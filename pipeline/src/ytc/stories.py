"""Find story leads from Wikipedia lists, readers, and a separate checked accident pool.

The general pool still asks a model to score the most-read leads. The small
accident pool can outrank readership after its source pair has been checked.
"""

from __future__ import annotations

import json
import logging
import math
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import requests

from . import llm
from .studio import ROOT

log = logging.getLogger(__name__)

STORIES = ROOT / "status" / "stories.json"
WIKI = "https://en.wikipedia.org/w/api.php"
WIKIDATA = "https://www.wikidata.org/w/api.php"
# Wikipedia lists whose links are mostly single events (or the ships, places, and people at their heart).
SOURCES = (
    "List of maritime disasters", "List of maritime disasters in the 18th century",
    "List of maritime disasters in the 19th century", "List of maritime disasters in the 20th century",
    "List of missing ships", "List of people who disappeared mysteriously at sea", "List of volcanic eruptions by death toll",
    "List of natural disasters by death toll", "List of accidents and disasters by death toll", "List of fires",
    "List of building or structure fires", "List of airship accidents", "List of rail accidents (before 1880)",
    "List of rail accidents (1880–1889)", "List of rail accidents (1900–1909)", "List of rail accidents (1940–1949)",
    "List of famines", "List of historical earthquakes", "Dam failure", "List of Antarctic expeditions",
    "List of Arctic expeditions", "List of polar explorers", "List of industrial disasters", "Mining accident",
    "List of fatal crowd crushes", "List of explosions", "List of floods", "List of tsunamis",
    "List of avalanches by death toll", "Lost city", "List of last stands", "List of sieges", "List of military disasters",
    "List of epidemics and pandemics", "List of destroyed heritage",
)
# Wikidata dates that place an event (or a ship's end) in time: point in time, start, end, service retirement.
# Dates of death and dissolution are left out: they filled the pool with people and countries.
DATE_PROPS = ("P585", "P580", "P582", "P730")
LATEST_YEAR = date.today().year - 75
# Readers are Wikipedia's page views over the last READ_DAYS (the most its bulk query gives). The pool is
# harvested again after FRESH_DAYS; candidates found again keep their score.
READ_DAYS = 60
FRESH_DAYS = 30
# Whole wars, revolutions, eras, and civilizations are too big for one Short; their battles and disasters stay.
BROAD = re.compile(r"\b(War|Wars|Revolution|Civili[sz]ation|period|Age|Era|Crusade|Reconquista|dynasty|history|"
                   r"Empire|Commonwealth|Unification of \w+|War of Independence)( [IVX]+)?$", re.I)
# How many of the most-read unscored candidates one scoring prompt judges, and the score a story needs to be added.
SCORE_BATCH = 40
KEEP_SCORE = 7
# Scoring prompts a day, so the most-read part of the pool is judged within weeks.
DAILY_BATCHES = 3
# A backlog topic nobody has scored counts as this.
DEFAULT_SCORE = 6


def _session() -> requests.Session:
    from .visuals import _user_agent

    session = requests.Session()
    session.headers["User-Agent"] = _user_agent()
    return session


def _load() -> dict:
    try:
        return json.loads(STORIES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"candidates": {}, "topics": {}}


def _save(data: dict) -> None:
    STORIES.parent.mkdir(parents=True, exist_ok=True)
    STORIES.write_text(json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def linked_articles(session: requests.Session, page: str) -> list[str]:
    """Article titles a page links to, redirects followed."""
    titles, params = [], {"action": "query", "titles": page, "generator": "links", "gplnamespace": 0, "gpllimit": "max",
                           "redirects": 1, "format": "json", "formatversion": 2}
    while True:
        body = session.get(WIKI, params=params, timeout=30).json()
        titles += [p["title"] for p in body.get("query", {}).get("pages", []) if not p.get("missing")]
        if "continue" not in body:
            return titles
        params.update(body["continue"])


def _year(claim: dict) -> int | None:
    value = (claim.get("mainsnak", {}).get("datavalue") or {}).get("value") or {}
    match = re.match(r"([+-])(\d+)-", str(value.get("time", "")))
    return (int(match[2]) * (-1 if match[1] == "-" else 1)) if match else None


def _chunk(session: requests.Session, chunk: list[str]) -> dict[str, tuple[int, int]]:
    """(earliest Wikidata date in DATE_PROPS, readers in the last READ_DAYS) for each title that has a date."""
    try:
        pages = session.get(WIKI, timeout=30, params={
            "action": "query", "titles": "|".join(chunk), "prop": "pageprops|pageviews", "ppprop": "wikibase_item",
            "pvipdays": READ_DAYS, "format": "json", "formatversion": 2}).json()
        found = {p["pageprops"]["wikibase_item"]: (p["title"], sum(v or 0 for v in (p.get("pageviews") or {}).values()))
                 for p in pages.get("query", {}).get("pages", []) if p.get("pageprops", {}).get("wikibase_item")}
        if not found:
            return {}
        entities = session.get(WIKIDATA, timeout=30, params={"action": "wbgetentities", "ids": "|".join(found),
                                                             "props": "claims", "format": "json"}).json().get("entities", {})
    except (requests.RequestException, ValueError) as err:
        log.info("no dates or readers for %d titles: %s", len(chunk), err)
        return {}
    result = {}
    for qid, entity in entities.items():
        years = [y for prop in DATE_PROPS for c in entity.get("claims", {}).get(prop, []) if (y := _year(c)) is not None]
        if years and qid in found:
            title, readers = found[qid]
            result[title] = (min(years), readers)
    return result


def dated_readers(session: requests.Session, titles: list[str]) -> dict[str, tuple[int, int]]:
    """(year, readers in the last READ_DAYS) for every title with a Wikidata date, 50 titles a request."""
    result: dict[str, tuple[int, int]] = {}
    with ThreadPoolExecutor(4) as pool:
        for found in pool.map(lambda i: _chunk(session, titles[i:i + 50]), range(0, len(titles), 50)):
            result.update(found)
    return result


def harvest(data: dict, today: date | None = None) -> int:
    """Refresh the candidate pool: events from SOURCES dated LATEST_YEAR or earlier, with their recent readers.
    A candidate keeps its score from earlier harvests."""
    today = today or date.today()
    session = _session()
    titles: set[str] = set()
    for page in SOURCES:
        try:
            titles.update(linked_articles(session, page))
        except (requests.RequestException, ValueError) as err:
            log.info("couldn't read %s: %s", page, err)
    titles = {t for t in titles if not t.startswith(("List of", "Lists of", "Timeline of", "Index of"))}
    log.info("story pool: %d articles linked from %d lists; reading their dates and readers", len(titles), len(SOURCES))
    found = dated_readers(session, sorted(titles))
    candidates = data.setdefault("candidates", {})
    old = 0
    for title, (year, readers) in found.items():
        if year <= LATEST_YEAR and not BROAD.search(title):
            old += 1
            candidates[title] = {**candidates.get(title, {}), "year": year, "readers": readers, "at": today.isoformat()}
    log.info("story pool: %d dated, %d from %d or earlier", len(found), old, LATEST_YEAR)
    return old


SCORE_SCHEMA = {
    "type": "object",
    "properties": {"stories": {"type": "array", "items": {"type": "object", "properties": {
        "wikipedia": {"type": "string"}, "score": {"type": "integer"}, "series": {"type": "string"},
        "topic": {"type": "string"}, "why": {"type": "string"}}, "required": ["wikipedia", "score", "series", "topic", "why"]}}},
    "required": ["stories"],
}


def score_prompt(batch: list[dict], series: list[str], known: list[str]) -> str:
    lines = "\n".join(f"- {c['title']} ({c['year']}; {c['readers']:,} readers in 60 days)" for c in batch)
    return (
        "You choose stories for History's Last Hours, a YouTube Shorts channel that tells the final moments of "
        "history's tragedies in 17 to 35 seconds, for a US audience scrolling the Shorts feed. Out of millions of "
        "tragedies, only the ones with an extraordinary story get watched to the end and shared.\n\n"
        "Score each Wikipedia article below from 1 to 10 for story power as a Short:\n"
        "- 9-10: one jaw-dropping, true detail a viewer will repeat to a friend (an irony, an ignored warning, an "
        "absurd cause, a single decision that doomed everyone, an impossible survival), a human face to follow, "
        "and a setting people already half-know (Titanic, Pompeii) or can picture in one second.\n"
        "- 7-8: a strong twist and clear stakes, but less known or harder to show.\n"
        "- 4-6: a sad event without a twist; the facts alone don't make a story.\n"
        "- 1-3: not a single event (a country, a concept, a list), not a tragedy, told only for gore, or less than "
        "75 years ago.\n"
        "Readers show how many people already care; weigh it, but a little-known event with an "
        "extraordinary twist can beat a famous one with none.\n\n"
        "For each article with a score of 7 or more, write the topic as one line naming the story, the year, and "
        "the twist that makes it extraordinary, like: \"Sinking of the Titanic (1912): the lookouts had no "
        "binoculars, because the key to their locker left the ship\". Only claims you are sure reputable sources "
        "support: no famous quotes historians doubt, no legends told as fact; if a story's best-known twist is "
        "disputed, build the topic on a documented one or score it 5 or less. Pick its series from: " + "; ".join(series) + ". In `why`, say in a few words what makes it "
        "extraordinary (or why not). Give `wikipedia` exactly as listed.\n\n"
        "Skip any story already covered by these topics:\n" + "\n".join(f"- {k}" for k in known[-150:]) +
        "\n\nArticles:\n" + lines
    )


def score(data: dict, series: list[str], known: list[str]) -> list[dict]:
    """Score the most-read candidates not scored yet; return the new stories at KEEP_SCORE or more."""
    candidates = data.get("candidates", {})
    unscored = sorted(({"title": t, **c} for t, c in candidates.items() if "score" not in c and c.get("readers")),
                      key=lambda c: -c["readers"])[:SCORE_BATCH]
    if not unscored:
        return []
    answer = llm.generate(score_prompt(unscored, series, known), schema=SCORE_SCHEMA, models=llm.BROAD,
                          purpose="story scores")
    by_title = {c["title"]: c for c in unscored}
    kept = []
    for story in answer.get("stories", []):
        entry = candidates.get(story.get("wikipedia", ""))
        if entry is None:
            continue
        entry.update(score=int(story["score"]), why=story.get("why", "")[:200])
        if story["score"] >= KEEP_SCORE and story.get("series") in series and story.get("topic"):
            kept.append({**story, "readers": by_title[story["wikipedia"]]["readers"]})
    # A candidate the answer skipped counts as judged too, so the next batch moves down the list.
    for title in by_title:
        candidates[title].setdefault("score", 0)
    return kept


def priority(topic: str, data: dict, readers: int = 0) -> float:
    """Backlog order from story score and readership, or a checked editorial lead."""
    known = data.get("topics", {}).get(topic, {})
    demand = known.get("score", DEFAULT_SCORE) * math.log10(max(known.get("readers", readers), 0) + 10)
    # An editor checked these accident leads against an original study/report and
    # an independent account. Their low Wikipedia readership must not bury them.
    if known.get("candidate_id") and len(known.get("source_urls", [])) >= 2:
        return max(demand, known.get("editorial_priority", 0))
    return demand


def topic_scores() -> dict:
    return _load()
