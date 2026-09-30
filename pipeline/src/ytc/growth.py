"""Timely topics for the calendar (auto.add_timely): the animal and biology articles English Wikipedia's readers
flocked to in the last two days, nature and biology news, and follow-ups to a Short that broke out.

The fetchers are keyless public feeds; the pure functions under them take what the feeds return, so they can be
checked offline.
"""

from __future__ import annotations

import json
import logging
import re
import statistics
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import requests

from . import llm
from .writer import SERIES

log = logging.getLogger(__name__)

WIKI_TOP = "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{day:%Y/%m/%d}"
WIKI_API = "https://en.wikipedia.org/w/api.php"
# Free, keyless nature and biology news feeds, checked 2026-09-30 (all 200 RSS 2.0, updated daily). NOAA Ocean
# Exploration and National Geographic publish no working RSS feed.
NATURE_FEEDS = (
    "https://www.sciencedaily.com/rss/plants_animals.xml",
    "https://www.sciencedaily.com/rss/plants_animals/marine_biology.xml",
    "https://phys.org/rss-feed/biology-news/zoology/",
    "https://www.livescience.com/feeds/tag/animals",
    "https://www.sciencenews.org/topic/animals/feed",
)
NEWS_KEEP = 40
# A cheap first pass over Wikipedia's short descriptions ("Species of cephalopod", "Genus of lobe-finned fish",
# "American marine biologist"); the language model makes the real call on what's left.
ANIMAL_WORDS = re.compile(
    r"\b(species|subspecies|genus|genera|family of|order of|class of|phylum|taxon|animals?|mammals?|birds?|fish|"
    r"fishes|sharks?|rays?|whales?|dolphins?|porpoises?|cetaceans?|seals?|reptiles?|snakes?|lizards?|turtles?|"
    r"tortoises?|crocodil\w*|amphibians?|frogs?|toads?|salamanders?|insects?|beetles?|butterfl\w+|moths?|bees?|"
    r"wasps?|ants?|spiders?|arachnids?|scorpions?|crustaceans?|crabs?|shrimps?|lobsters?|molluscs?|mollusks?|"
    r"cephalopods?|octop\w+|squids?|snails?|slugs?|jellyfish|cnidarians?|corals?|sponges?|worms?|tardigrades?|"
    r"primates?|apes?|monkeys?|lemurs?|bats?|rodents?|marsupials?|parrots?|owls?|penguins?|dinosaurs?|"
    r"pterosaurs?|fossils?|extinct|zoolog\w*|biolog\w*|naturalists?|entomolog\w*|ornitholog\w*|herpetolog\w*|"
    r"ichthyolog\w*|primatolog\w*|paleontolog\w*|palaeontolog\w*|evolution\w*|wildlife|deep[- ]sea|"
    r"marine (?:animal|biolog\w*|life|mammal|species|invertebrate)s?)\b", re.I)
# Articles that are never a story: the front page, search, and project pages.
NOT_ARTICLES = re.compile(r"^(Main Page|-|Undefined)$|^(Special|Wikipedia|File|Portal|Help|Template|Category|Talk|User):")
TRENDING_KEEP = 15

# A Short breaks out when, within BREAKOUT_HOURS of going live, it has BREAKOUT_RATIO times the median views its
# peers had at the same age (and at least BREAKOUT_MIN_VIEWS, so 3x a handful of views on Day 2 isn't a breakout),
# or BREAKOUT_VIEWS outright (strategy/PLAN-100.md). Peers need MIN_PEERS Shorts measured that young.
BREAKOUT_RATIO = 3.0
BREAKOUT_HOURS = 48
BREAKOUT_MIN_VIEWS = 1000
BREAKOUT_VIEWS = 100_000
MIN_PEERS = 5


def _headers() -> dict:
    from .visuals import _user_agent

    return {"User-Agent": _user_agent()}


# --- trending on Wikipedia ------------------------------------------------------------------------------------


def top_articles(days: int = 2, today: date | None = None) -> dict[str, int]:
    """English Wikipedia's most-read articles on each of the last `days` full days (UTC): title -> the most views
    it had on one of them. A day Wikimedia hasn't published yet is skipped."""
    today = today or datetime.now(timezone.utc).date()
    views: dict[str, int] = {}
    for back in range(1, days + 1):
        response = requests.get(WIKI_TOP.format(day=today - timedelta(days=back)), headers=_headers(), timeout=20)
        if response.status_code == 404:
            continue
        response.raise_for_status()
        views = merge_top(views, response.json())
    return views


def merge_top(views: dict[str, int], body: dict) -> dict[str, int]:
    """Add one day of Wikimedia's "top" answer to `views`, keeping each article's best day and leaving out pages
    that aren't articles."""
    out = dict(views)
    for item in body.get("items", []):
        for article in item.get("articles", []):
            title = article["article"].replace("_", " ")
            if not NOT_ARTICLES.search(title):
                out[title] = max(out.get(title, 0), int(article["views"]))
    return out


def descriptions(titles: list[str]) -> dict[str, str]:
    """Wikipedia's short description of each title (after redirects), 50 titles a request."""
    found: dict[str, str] = {}
    for start in range(0, len(titles), 50):
        batch = titles[start:start + 50]
        body = requests.get(WIKI_API, headers=_headers(), timeout=20, params={
            "action": "query", "prop": "description", "titles": "|".join(batch), "redirects": 1,
            "format": "json", "formatversion": 2}).json()["query"]
        renamed = {r["from"]: r["to"] for r in body.get("normalized", []) + body.get("redirects", [])}
        described = {p["title"]: p.get("description", "") for p in body.get("pages", []) if not p.get("missing")}
        for title in batch:
            target = title
            for _ in range(3):
                target = renamed.get(target, target)
            if target in described:
                found[title] = described[target]
    return found


def animal_articles(views: dict[str, int], described: dict[str, str], keep: int = TRENDING_KEEP) -> list[dict]:
    """The trending articles whose short description sounds like animals or biology, most read first."""
    hits = [{"title": t, "views": v, "description": described[t]} for t, v in views.items()
            if ANIMAL_WORDS.search(described.get(t, ""))]
    return sorted(hits, key=lambda h: -h["views"])[:keep]


def trending_animals(days: int = 2, pool: int = 300) -> list[dict]:
    """Animal and biology articles among the `pool` most-read English Wikipedia articles of the last `days` days."""
    views = top_articles(days)
    titles = [t for t, _ in sorted(views.items(), key=lambda kv: -kv[1])[:pool]]
    return animal_articles({t: views[t] for t in titles}, descriptions(titles))


# --- nature news ------------------------------------------------------------------------------------------------


def nature_news(xml_text: str, now: datetime, hours: int = 48) -> list[dict]:
    """The items of one RSS feed published within `hours` before `now`: {"title", "link", "published",
    "summary"}, newest first."""
    items = []
    for item in ElementTree.fromstring(xml_text).iter("item"):
        try:
            published = parsedate_to_datetime(item.findtext("pubDate") or "")
        except (TypeError, ValueError):
            continue
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        if not timedelta(0) <= now - published <= timedelta(hours=hours):
            continue
        summary = re.sub(r"\s+", " ", re.sub(r"<[^>]+>|\[&#8230;\]|\[…\]", " ", item.findtext("description") or "")).strip()
        items.append({"title": (item.findtext("title") or "").strip(), "link": (item.findtext("link") or "").strip(),
                      "published": published.astimezone(timezone.utc).isoformat(), "summary": summary[:400]})
    return sorted(items, key=lambda i: i["published"], reverse=True)


def fetch_nature_news(hours: int = 48) -> list[dict]:
    """The recent items of every NATURE_FEEDS feed that answers, newest first, without repeated titles; raises
    only when no feed answers."""
    now, items, failures = datetime.now(timezone.utc), [], []
    for url in NATURE_FEEDS:
        try:
            response = requests.get(url, headers=_headers(), timeout=20)
            response.raise_for_status()
            items += nature_news(response.text, now, hours)
        except (requests.RequestException, ElementTree.ParseError) as err:
            log.info("nature feed %s failed: %s", url, err)
            failures.append(err)
    if len(failures) == len(NATURE_FEEDS):
        raise failures[-1]
    unique = {i["title"].lower(): i for i in sorted(items, key=lambda i: i["published"])}
    return sorted(unique.values(), key=lambda i: i["published"], reverse=True)[:NEWS_KEEP]


# --- choosing timely topics ------------------------------------------------------------------------------------

TOPICS_SCHEMA = {
    "type": "object",
    "properties": {"topics": {"type": "array", "items": {"type": "object", "properties": {
        "topic": {"type": "string"}, "series": {"type": "string", "enum": list(SERIES)}, "wikipedia": {"type": "string"},
        "why": {"type": "string"}}, "required": ["topic", "series", "wikipedia", "why"]}}},
    "required": ["topics"],
}

_CHANNEL = ("Creature Receipts is a YouTube Shorts channel of true, surprising stories of strange animals, extreme "
            "biology, and deep-sea life for a US audience (under a minute each, told with openly licensed photos, "
            "every claim backed by two reputable sources). Series: " + "; ".join(SERIES) + ".")
_RULES = ("Each must be a real story (a discovery, an experiment, a record, a scientist's surprise; not a facts list) "
          "with a genuinely surprising, well-documented fact, and name the exact title of an existing English "
          "Wikipedia article about its subject (the species, scientist, or event itself, not a news story). Start "
          "the topic line with that exact title, then the year and the twist, like: \"Coelacanth (1938): a fish "
          "known only from fossils turned up in a fishing net\". No hoaxes, cryptids, or speculation presented as "
          "fact, no gore, predation, dead-animal, or animal-cruelty stories, no health advice, no living private "
          "people, and nothing already listed below or a close variant.")


def pick_timely(trending: list[dict], news: list[dict], known: list[str], limit: int) -> list[dict]:
    """Up to `limit` topics a US viewer would care about today, from trending articles and nature news; each
    {"topic", "series", "wikipedia", "why"}. An empty list when nothing fits."""
    if not (trending or news) or limit <= 0:
        return []
    prompt = (
        f"{_CHANNEL}\n\nThese animal and biology subjects are in the news or trending on Wikipedia in the last two days. Pick at "
        f"most {limit} that make a strong Short right now: people are already curious about the subject, and it has "
        "a documented story worth a minute. Skip routine items (personnel news, event notices, photo captions) and "
        "anything whose facts are still unconfirmed; tell the documented background, not guesses about the news. "
        f"{_RULES} why: one short line saying what makes it timely (the trend or the news item). Return an empty "
        "list if nothing fits.\n\nTrending on English Wikipedia (views in a day):\n"
        + "\n".join(f"- {t['title']} ({t['views']:,}): {t['description']}" for t in trending)
        + "\n\nNature and biology news:\n" + "\n".join(f"- {n['title']} ({n['published'][:10]}): {n['summary'][:240]}" for n in news)
        + "\n\nAlready listed or made:\n" + "\n".join(f"- {k}" for k in known)
    )
    answer = llm.generate(prompt, schema=TOPICS_SCHEMA, models=llm.BROAD, purpose="timely topics")
    return answer.get("topics", [])[: limit * 2]


# --- breakouts --------------------------------------------------------------------------------------------------


def _taken_at(snapshot: dict) -> datetime:
    """When a stats snapshot was taken: its taken_at, or for older ones the morning (UTC) of its date, when the
    daily routine runs (after 14:00 IST)."""
    if snapshot.get("taken_at"):
        return datetime.fromisoformat(snapshot["taken_at"])
    return datetime.fromisoformat(f"{snapshot['date']}T09:00:00+00:00")


def early_views(snapshots: list[dict], hours: int = BREAKOUT_HOURS) -> dict[str, dict]:
    """Each video's views in the last snapshot taken within `hours` of it going live: video id -> {"views",
    "hours", "title", "taken_at"}."""
    best: dict[str, dict] = {}
    for snapshot in snapshots:
        taken = _taken_at(snapshot)
        for video in snapshot.get("videos", []):
            published = datetime.fromisoformat(video["published"].replace("Z", "+00:00"))
            age = (taken - published).total_seconds() / 3600
            if 0 <= age <= hours and (video["id"] not in best or age > best[video["id"]]["hours"]):
                best[video["id"]] = {"views": int(video.get("views", 0)), "hours": round(age, 1),
                                     "title": video.get("title", ""), "taken_at": taken.isoformat()}
    return best


def breakouts(snapshots: list[dict], done: set[str] | frozenset = frozenset()) -> list[dict]:
    """Shorts in the newest snapshot, still within BREAKOUT_HOURS of going live, that broke out against their
    peers' views at the same age: {"video", "title", "views", "median", "ratio", "hours"}, biggest ratio first.
    Videos in `done` were already acted on."""
    if not snapshots:
        return []
    snapshots = sorted(snapshots, key=_taken_at)
    early = early_views(snapshots)
    newest = _taken_at(snapshots[-1]).isoformat()
    found = []
    for video, seen in early.items():
        if seen["taken_at"] != newest or video in done:
            continue
        peers = [v["views"] for other, v in early.items() if other != video]
        if len(peers) < MIN_PEERS:
            continue
        median = statistics.median(peers)
        ratio = seen["views"] / median if median else float("inf")
        if (ratio >= BREAKOUT_RATIO and seen["views"] >= BREAKOUT_MIN_VIEWS) or seen["views"] >= BREAKOUT_VIEWS:
            found.append({"video": video, "title": seen["title"], "views": seen["views"], "median": median,
                          "ratio": round(ratio, 1) if ratio != float("inf") else None, "hours": seen["hours"]})
    return sorted(found, key=lambda b: -(b["ratio"] or 1e9))


FOLLOW_SCHEMA = {
    "type": "object",
    "properties": {"topics": {"type": "array", "items": {"type": "object", "properties": {
        "topic": {"type": "string"}, "wikipedia": {"type": "string"}}, "required": ["topic", "wikipedia"]}}},
    "required": ["topics"],
}


def propose_followups(short: dict, known: list[str], count: int = 2) -> list[dict]:
    """Follow-ups to a Short that broke out ({"title", "topic", "series", "hook"}), in its series and
    neighbourhood: each {"topic", "wikipedia"}."""
    prompt = (
        f"{_CHANNEL}\n\nThis Short in the series \"{short['series']}\" is breaking out, far above the channel's usual "
        f"views:\n{json.dumps({k: short.get(k) for k in ('title', 'topic', 'hook')}, ensure_ascii=False)}\n\n"
        f"Suggest {count + 2} follow-up topics for the same series that the same viewers will want next: the same "
        "subject from a different angle, a related species or discovery, or the rest of the story. Each must stand on "
        f"its own as a Short. {_RULES}\n\nAlready listed or made:\n" + "\n".join(f"- {k}" for k in known)
    )
    answer = llm.generate(prompt, schema=FOLLOW_SCHEMA, models=llm.BROAD, purpose="breakout follow-ups")
    return answer.get("topics", [])
