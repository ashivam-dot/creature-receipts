"""One unattended run of the cloud studio. GitHub Actions starts it several times a day.

A run syncs Buffer, files live Shorts into playlists, does the daily routine once a day (analytics, learnings,
report, new topics), makes Shorts when fewer than a week's worth are waiting, schedules finished Shorts into
Buffer's free slots, and writes `status/status.json` for the monitor on the owner's Mac.
"""

from __future__ import annotations

import calendar
import json
import logging
import os
import re
import secrets
import shutil
import statistics
import threading
import time
import traceback
from contextlib import contextmanager
from datetime import date, datetime, time as clock, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import yaml

from . import llm

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
EPISODES = ROOT / "content" / "episodes"
REJECTED = ROOT / "content" / "rejected"
STATUS = ROOT / "status"
CALENDAR = ROOT / "strategy" / "CALENDAR.md"
LEARNINGS = ROOT / "strategy" / "LEARNINGS.md"
REPORTS = ROOT / "reports"
ANALYTICS = ROOT / "analytics"
IST = ZoneInfo("Asia/Kolkata")
ET = ZoneInfo("America/New_York")
DAY_ZERO = date(2026, 10, 1)
# Two weeks at 3 a day, so the channel keeps publishing through two weeks without any language model. Shorts
# made further ahead would miss what the newest analytics teach.
INVENTORY_DAYS = 14
# Drafts the control repo can still release: it takes three a day, so a few days' worth keeps it fed.
DRAFT_BUFFER_DAYS = 3
# Episodes below this predate the control repo's release floor (its policy.json) and can never be released.
RELEASE_FLOOR = 63
BATCH = 4
# After Gemini's free quotas reset (00:05 Pacific: 12:35 IST in summer time, 13:35 in winter), so the routine's
# learnings and new topics come before production uses the day's quota; the first run after is 17:05 IST.
DAILY_FROM_HOUR = 14
# Source-checked accident leads waiting in the calendar at once.
ACCIDENT_LEADS_ACTIVE = 2
# Open calendar topics that cover 20 days at 3 Shorts a day; the backlog generators skip a day above it.
OPEN_TOPICS_ENOUGH = 60
# Modal's Starter plan includes $1 of compute a month, or $30 once a card is on file (set the YTC_MODAL_CREDIT
# Actions variable to match). A Short made there costs about $0.10: a worker waiting on Gemini, and up to three renders.
MODAL_CREDIT = float(os.environ.get("YTC_MODAL_CREDIT") or 1)
MODAL_PER_SHORT = 0.12
# With a card on file the studio's own runs are on Modal too (cloud.studio_run, about $1 a month), and with the
# spend limit at $0 Modal stops everything, those runs included, once the credit is gone.
MODAL_RESERVE = 2.0 if MODAL_CREDIT >= 10 else 0.0
# Set in Modal's containers: this run is cloud.studio_run, which starts workers but makes no Short itself.
ON_MODAL = bool(os.environ.get("YTC_ON_MODAL"))
# GitHub's free plan gives private repositories 2,000 Actions minutes a month; public ones aren't metered
# (minutes_budget). The reserve keeps the runs that only sync, collect and publish (about 2 minutes each) going
# to the end of the month.
MONTH_MINUTES = 2000
MINUTES_RESERVE = 250
# About what one Short made on the runner takes: research, image picks, and reviews waiting on the language model
# (3 to 5 minutes a prompt through Cursor), and three renders of about 3 minutes each (39 and 49 on 2026-09-26).
RUNNER_MINUTES_PER_SHORT = 45
# Shorts made at once on the runner. Most of a Short's time is waiting on the language model, so the lanes overlap
# those waits, while rendering and checking take turns (studio.CPU_LOCK).
LANES = 3
# Once Gemini's Flash quota is spent, production goes on with the backup models (llm.BACKUPS), but only while fewer
# than this many are ready (where posting slows; see per_day) does a backup model or Cursor judge a finished Short;
# otherwise it waits for a Flash review after the reset (_jobs). Cursor's Shorts took about three times the runner's
# minutes and passed the gate 2 times in 17 (0 of 3 when also given the month's spare minutes on 2026-09-27).
CURSOR_BELOW = 9
# Below this many ready (about a day of posting), production goes on without Gemini's Flash models or Cursor, and
# Gemma 4 31B reviews the Shorts they can't (studio.LAST_RESORT): a Short judged by Gemma beats posting nothing.
LAST_RESORT_BELOW = 3
# A post Buffer couldn't publish goes back in the queue this many times; after that it's left for the owner.
RETRIES = 2
# How far ahead of its slot a post is first checked (preflight_posts); every run until it goes out checks it again.
PREFLIGHT_HOURS = 36
# Never start a Short on the runner this far into a run; the workflow stops the step at 170.
PRODUCE_MINUTES = 120
# A Modal worker has a 4-hour timeout, after which Modal reports it failed. One Modal still calls running
# this long after it started (runs are 6 hours apart) is stuck in a queue, and is stopped and retried.
STALE_HOURS = 8
MAX_SPAWNS = 3
# A topic whose Short is rejected for anything but its research (the pictures, the review, a worker that kept
# stopping) is parked and comes back once after this many days; a second rejection drops it.
PARK_DAYS = 14
SERIES = [
    "The Last Hours",
    "Lost Cities",
    "Doomed Expeditions",
    "Fallen Empires",
    "Warnings Ignored",
    "Sole Survivors",
]
MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}
STATUS_MARK = re.compile(r"\s+—\s+(making|done|dropped|parked)\s+\((ep\d{3})\)\s*$")
# Wikipedia readership per topic (choose_topics), read again after DEMAND_DAYS.
DEMAND = STATUS / "demand.json"
DEMAND_DAYS = 14
# Timely topics (news, what's trending on Wikipedia, follow-ups to a breakout) are made and posted first while
# this many days old; after that they wait in line with the backlog. Trending and news add at most TREND_PER_DAY a
# day, and each breakout FOLLOW_UPS.
TIMELY_DAYS = 3
TREND_PER_DAY = 2
FOLLOW_UPS = 2
TIMELY_HEADING = "## Timely (news, trending, and breakout follow-ups: made and posted first)"


def _now() -> datetime:
    return datetime.now(IST)


def day_number(today: date | None = None) -> int:
    return ((today or _now().date()) - DAY_ZERO).days


def _json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


class Run:
    """What this run did, stage by stage, for status.json and the day's report."""

    def __init__(self, trigger: str):
        self.started = _now()
        self.clock = time.monotonic()
        self.trigger = trigger
        self.stages: list[dict] = []
        self.errors: list[str] = []
        self.owner_action: list[str] = []
        self.made: list[dict] = []
        self.spawned: list[dict] = []
        self.started_here = 0
        self.capacity: dict | None = None
        self.worker_calls: list[dict] = []
        self.quota_until: datetime | None = None
        self.published: list[dict] = []
        self.notes: list[str] = []
        self.renders: dict[str, int] = {"modal": 0, "runner": 0}
        self.not_live: list[dict] = []

    def minutes(self) -> float:
        return (time.monotonic() - self.clock) / 60

    @contextmanager
    def stage(self, name: str):
        started = time.monotonic()
        entry = {"name": name, "ok": True, "detail": ""}
        self.stages.append(entry)
        log.info("== %s", name)
        try:
            yield entry
        except Exception as err:
            from .publish import BufferBusy

            if isinstance(err, BufferBusy):
                entry["detail"] = f"skipped: {err}"
                log.warning("%s skipped: %s", name, err)
                return
            entry["ok"] = False
            entry["error"] = f"{type(err).__name__}: {err}"[:600]
            self.errors.append(f"{name}: {entry['error']}")
            log.error("%s failed: %s\n%s", name, err, traceback.format_exc())
            if isinstance(err, llm.OutOfQuota):
                entry["quota"] = True
                self.quota_until = _next_quota_reset()
            _owner_action_for(self, err)
        finally:
            entry["seconds"] = round(time.monotonic() - started, 1)


def _owner_action_for(run: Run, err: Exception) -> None:
    text = str(err)
    if "invalid_grant" in text or "Not signed in" in text:
        run.owner_action.append("YouTube sign-in expired: on the Mac run `uv run --no-sync ytc auth` in pipeline/, "
                                "then update the YTC_GOOGLE_TOKEN secret (see OWNER-CHECKLIST.md).")
    elif "API key not valid" in text or "API_KEY_INVALID" in text or "Gemini refused the key" in text:
        run.owner_action.append("The Gemini API key was rejected: make a new key in AI Studio (akshshivam5@gmail.com, project creature-receipts) "
                                "and update the YTC_GEMINI_API_KEY secret.")
    elif "Unauthorized" in text and "buffer" in text.lower():
        run.owner_action.append("Buffer rejected the API key: make a new one and update the BUFFER_API_KEY secret.")


# --- inventory ---------------------------------------------------------------------------------------------


def episodes() -> list[dict]:
    """Every episode folder with what stage it's at."""
    out = []
    for folder in sorted(EPISODES.glob("ep[0-9][0-9][0-9]")):
        record, held, topic = _json(folder / "publish.json"), _json(folder / "hold.json"), _json(folder / "topic.json")
        draft = _json(folder / "draft.json")
        editorial_hold_path = folder / "editorial_hold.json"
        editorial_hold = _json(editorial_hold_path)
        withdrawal = _json(folder / "withdrawal.json")
        remote = _json(folder / "remote.json")
        spec = yaml.safe_load((folder / "short.yaml").read_text(encoding="utf-8")) if (folder / "short.yaml").exists() else {}
        if withdrawal is not None and record and record.get("status") == "sent":
            state = "withdrawn"
        elif remote and not record:
            # A hold added while a worker is running must not hide its result from collect().
            state = "remote"
        elif editorial_hold_path.exists() and (not record or record.get("status") != "sent"):
            # A queued Buffer post must be removed separately; this lock keeps the studio from scheduling it again.
            state = "editorial_hold"
        elif record:
            state = "live" if record["status"] == "sent" else "error" if record["status"] == "error" else "scheduled"
        elif held and held.get("superseded"):
            state = "superseded"
        elif held:
            state = "waiting"
        elif draft:
            state = "draft"
        elif topic:
            state = "making"
        else:
            state = "unfinished"
        out.append({"id": folder.name, "folder": folder, "state": state, "title": spec.get("title"),
                    "series": spec.get("series") or (topic or {}).get("series"), "record": record, "held": held, "topic": topic,
                    "remote": remote, "editorial_hold": editorial_hold, "withdrawal": withdrawal})
    return out


def _fresh_draft(episode: dict, now: datetime | None = None) -> bool:
    """The control repo releases drafts without telling the producer, so only recent drafts count as unposted."""
    started = (episode.get("topic") or {}).get("started_at")
    try:
        when = datetime.fromisoformat(started)
    except (TypeError, ValueError):
        return True
    return (now or datetime.now(IST)) - when <= timedelta(days=DRAFT_BUFFER_DAYS)


def inventory(eps: list[dict] | None = None) -> dict:
    eps = eps if eps is not None else episodes()
    scheduled = [e for e in eps if e["state"] == "scheduled"]
    waiting = [e for e in eps if e["state"] == "waiting" and int(e["id"][2:]) >= RELEASE_FLOOR]
    drafts = [e for e in eps if e["state"] == "draft" and _fresh_draft(e)]
    days = DRAFT_BUFFER_DAYS if os.environ.get("YTC_DRAFT_ONLY") == "1" else INVENTORY_DAYS
    return {"total": len(scheduled) + len(waiting) + len(drafts), "in_buffer": len(scheduled), "waiting": len(waiting),
            "drafts": len(drafts),
            "target": days * slots_per_day(), "making": [e["id"] for e in eps if e["state"] == "making"],
            "remote": [e["id"] for e in eps if e["state"] == "remote"]}


# --- calendar ----------------------------------------------------------------------------------------------


def _next_date(label: str, today: date) -> date | None:
    match = re.match(r"([A-Z][a-z]{2})\w*\s+(\d{1,2})", label)
    if not match or match.group(1) not in MONTHS:
        return None
    for year in (today.year, today.year + 1):
        try:
            when = date(year, MONTHS[match.group(1)], int(match.group(2)))
        except ValueError:
            return None
        if when >= today:
            return when
    return None


def _iso_date(text: str) -> date | None:
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def calendar_topics(today: date | None = None) -> list[dict]:
    today = today or _now().date()
    topics, section, series = [], None, None
    for number, line in enumerate(CALENDAR.read_text(encoding="utf-8").splitlines()):
        if line.startswith("## "):
            section, series = line[3:].strip(), None
        elif line.startswith("### "):
            series = line[4:].strip()
        elif section and section.startswith(("Anniversaries", "Timely")) and line.startswith("| ") \
                and not line.startswith(("| Date", "| Added", "|---")):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3:
                mark = STATUS_MARK.search(cells[1])
                timely = section.startswith("Timely")
                topics.append({"kind": "timely" if timely else "anniversary", "line": number, "label": cells[0],
                               "date": _iso_date(cells[0]) if timely else _next_date(cells[0], today),
                               "topic": STATUS_MARK.sub("", cells[1]), "series": cells[2], "status": mark.group(1) if mark else None,
                               "episode": mark.group(2) if mark else None, "why": cells[3] if len(cells) > 3 else ""})
        elif section == "Backlog" and series and line.startswith("- "):
            mark = STATUS_MARK.search(line)
            topics.append({"kind": "backlog", "line": number, "topic": STATUS_MARK.sub("", line[2:]).strip(),
                           "series": series, "status": mark.group(1) if mark else None, "episode": mark.group(2) if mark else None})
    return topics


def mark_topic(topic: dict, status: str, episode_id: str) -> None:
    lines = CALENDAR.read_text(encoding="utf-8").splitlines()
    line = lines[topic["line"]]
    if topic["kind"] in ("anniversary", "timely"):
        cells = line.strip().strip("|").split("|")
        cells[1] = f" {STATUS_MARK.sub('', cells[1].strip())} — {status} ({episode_id}) "
        lines[topic["line"]] = "|" + "|".join(cells) + "|"
    else:
        lines[topic["line"]] = STATUS_MARK.sub("", line) + f" — {status} ({episode_id})"
    CALENDAR.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _available(topic: dict, today: date) -> bool:
    """Not started yet, or parked for PARK_DAYS since its Short was rejected."""
    if topic["status"] != "parked":
        return not topic["status"]
    rejected_on = str((_json(REJECTED / topic["episode"] / "review.json") or {}).get("rejected_at", ""))[:10]
    return not rejected_on or (today - date.fromisoformat(rejected_on)).days >= PARK_DAYS


def demand(topics: list[dict]) -> dict[str, int]:
    """How many people read the English Wikipedia article that best matches each topic in the last 30 days: how
    widely known its subject is. Cached in status/demand.json for DEMAND_DAYS; 0 when Wikipedia doesn't answer."""
    from urllib.parse import quote

    from .visuals import _user_agent

    cache = _json(DEMAND, {})
    today = _now().date()
    end = today - timedelta(days=1)
    start = end - timedelta(days=29)
    headers = {"User-Agent": _user_agent()}

    def stems(text: str) -> set[str]:
        return {w.rstrip("s")[:5] for w in _key_words(text)}

    def article_for(text: str) -> str:
        # The first search hit whose title (or the redirect it matched) is at least a third the topic's own words:
        # full-text search alone matched "Tulip mania wasn't as manic as we think" to a list of people.
        words = stems(text)

        def fit(title: str) -> float:
            own = stems(title)
            return len(own & words) / len(own) if own else 0.0

        query = re.sub(r"\([^)]*\)", "", text).split(":")[0].strip()
        for attempt in dict.fromkeys((query, re.split(r",| and | was | were | is ", query)[0])):
            found = requests.get("https://en.wikipedia.org/w/api.php", headers=headers, timeout=15, params={
                "action": "query", "list": "search", "srsearch": attempt, "srlimit": 5, "srprop": "redirecttitle",
                "format": "json"}).json()["query"]["search"]
            for hit in found:
                if max(fit(hit["title"]), fit(hit.get("redirecttitle", ""))) >= 1 / 3:
                    return hit["title"]
        return ""

    for topic in topics:
        text = topic["topic"]
        if (kept := cache.get(text)) and (today - date.fromisoformat(kept["at"])).days < DEMAND_DAYS:
            continue
        try:
            title = article_for(text)
            views = 0
            if title:
                article = quote(title.replace(" ", "_"), safe="")
                response = requests.get(
                    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/"
                    f"{article}/daily/{start:%Y%m%d}/{end:%Y%m%d}", headers=headers, timeout=15)
                if response.ok:
                    views = sum(item["views"] for item in response.json().get("items", []))
            cache[text] = {"article": title, "views": views, "at": today.isoformat()}
        except (requests.RequestException, ValueError, KeyError) as err:
            log.info("no Wikipedia readership for %r: %s", text, err)
    _write_json(DEMAND, cache)
    return {text: entry["views"] for text, entry in cache.items()}


def urgent(topics: list[dict], today: date) -> list[dict]:
    """Timely topics still within TIMELY_DAYS of being added, oldest first."""
    return sorted((t for t in topics if t["kind"] == "timely" and t["date"] and 0 <= (today - t["date"]).days <= TIMELY_DAYS),
                  key=lambda t: t["date"])


def choose_topics(count: int, eps: list[dict]) -> list[dict]:
    """Fresh timely topics first, then anniversaries within a week, then the backlog (with timely topics past
    TIMELY_DAYS). Rank the backlog by story score/readers or checked editorial priority, never two of one series
    in a row."""
    from . import stories

    today = _now().date()
    open_topics = [t for t in calendar_topics(today) if _available(t, today)]
    fresh = urgent(open_topics, today)
    chosen = fresh[:count]
    chosen += sorted((t for t in open_topics if t["kind"] == "anniversary" and t["date"] and (t["date"] - today).days <= 7),
                     key=lambda t: t["date"])[:count - len(chosen)]
    recent = [e["series"] for e in sorted(eps, key=lambda e: e["id"], reverse=True) if e["series"]]
    backlog = [t for t in open_topics if t["kind"] == "backlog" or (t["kind"] == "timely" and t not in fresh)]
    readers = demand(backlog) if len(chosen) < count and backlog else {}
    scores = stories.topic_scores()
    while len(chosen) < count and backlog:
        used = [t["series"] for t in reversed(chosen)] + recent
        last = used[0] if used else None
        best = max(backlog, key=lambda t: (t["series"] != last,
                                           stories.priority(t["topic"], scores, readers.get(t["topic"], 0))))
        chosen.append(best)
        backlog.remove(best)
    return chosen


TOPICS_SCHEMA = {
    "type": "object",
    "properties": {
        "backlog": {"type": "array", "items": {"type": "object", "properties": {
            "topic": {"type": "string"}, "series": {"type": "string", "enum": SERIES}, "wikipedia": {"type": "string"}},
            "required": ["topic", "series", "wikipedia"]}},
        "anniversaries": {"type": "array", "items": {"type": "object", "properties": {
            "date": {"type": "string"}, "topic": {"type": "string"}, "series": {"type": "string", "enum": SERIES},
            "wikipedia": {"type": "string"}}, "required": ["date", "topic", "series", "wikipedia"]}},
    },
    "required": ["backlog", "anniversaries"],
}


def _key_words(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'-]{3,}", text)} - {"that", "with", "from", "were", "their", "which", "into", "after"}


def _repeats(topic: str, known_words: list[set[str]]) -> bool:
    """Whether a topic has no words to go on, or shares half its words (at least 2) with one already known."""
    words = _key_words(topic)
    return not words or any(len(words & k) >= max(2, len(words) // 2) for k in known_words)


def add_topics(run: Run, backlog_count: int = 4) -> list[str]:
    """Fresh, well-documented topics for the backlog, plus an anniversary 3 to 8 weeks out."""
    from .research import _existing

    topics = calendar_topics()
    known = [t["topic"] for t in topics] + [e["title"] or "" for e in episodes()]
    today = _now().date()
    series_counts = {s: sum(1 for t in topics if t["kind"] == "backlog" and t["series"] == s and not t["status"]) for s in SERIES}
    prompt = (
        "You find topics for History's Last Hours, a YouTube Shorts channel of true, sourced stories of history's "
        "tragedies (lost cities, doomed voyages and expeditions, fallen empires, ignored warnings, and the few who "
        "survived) for a US audience (17 to 35 seconds each, told with period pictures, every claim sourced). "
        "Series: " + "; ".join(SERIES) + ".\n\n"
        f"Suggest {backlog_count + 3} new backlog topics and 2 anniversaries dated between "
        f"{(today + timedelta(days=21)).strftime('%b %d')} and {(today + timedelta(days=56)).strftime('%b %d')}. Each must be a "
        "real event at least 75 years old with a human story and a genuinely surprising detail, well documented by "
        "reputable sources, with an English Wikipedia article (give its exact title), and with period pictures "
        "likely on Wikimedia Commons (photographs, paintings, engravings, newspaper pages, ruins). No legends "
        "presented as true, nothing told for its gore, no living private people, no topics already listed below "
        "or close variants. "
        "Favor series with few open topics. Write each topic as a short line naming the story, the year, and the "
        "twist, like: \"Sinking of the Titanic (1912): the lookouts had no binoculars, because the key to their "
        "locker left the ship\". Dates look like "
        "\"Oct 7\".\n\n"
        f"Open topics per series: {json.dumps(series_counts)}\n\nAlready listed or made:\n" + "\n".join(f"- {k}" for k in known)
    )
    # Without new topics the calendar runs dry in weeks, so this falls back to the light models' separate quota.
    answer = llm.generate(prompt, schema=TOPICS_SCHEMA, models=llm.BROAD, purpose="new topics")
    added = []
    known_words = [_key_words(k) for k in known]

    def fresh(item) -> bool:
        return not _repeats(item["topic"], known_words) and bool(_existing([item["wikipedia"]]))

    lines = CALENDAR.read_text(encoding="utf-8").splitlines()
    for item in [i for i in answer.get("backlog", []) if fresh(i)][:backlog_count]:
        if not insert_backlog(lines, item["series"], item["topic"]):
            continue
        known_words.append(_key_words(item["topic"]))
        added.append(f"{item['topic']} ({item['series']})")
    for item in [i for i in answer.get("anniversaries", []) if fresh(i) and _next_date(i["date"], today)][:1]:
        header = next(i for i, l in enumerate(lines) if l.startswith("## Anniversaries"))
        end = next(i for i in range(header + 1, len(lines)) if lines[i].startswith("## "))
        while not lines[end - 1].startswith("|"):
            end -= 1
        when = _next_date(item["date"], today)
        rows = list(range(header + 1, end))
        position = end
        for i in rows:
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            other = _next_date(cells[0], today) if cells and cells[0] not in ("Date",) and not cells[0].startswith("---") else None
            if other and other > when:
                position = i
                break
        lines.insert(position, f"| {item['date']} | {item['topic']} | {item['series']} |")
        added.append(f"{item['date']}: {item['topic']} (anniversary)")
    CALENDAR.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return added


def insert_backlog(lines: list[str], series: str, topic: str) -> bool:
    """Add a topic line at the end of its series' backlog section; False when the calendar has no such section."""
    heading = f"### {series}"
    if heading not in lines:
        return False
    start = lines.index(heading)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("#")), len(lines))
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    lines.insert(end, f"- {topic}")
    return True


def add_accident_topics(run: Run) -> list[str]:
    """Add one checked accident lead at a time, with its original and independent sources.

    A lead remains an ordinary unapproved draft topic: research must read its
    listed pages and still find two matched quotes for each factual claim.
    """
    from . import accidents, stories

    today = _now().date()
    data = stories._load()
    topics = calendar_topics(today)
    records = data.setdefault("topics", {})
    # A parked lead cannot be retried for two weeks. Keep the source-checked
    # accident lane moving while that earlier draft waits for its retry date.
    pool_topics = {row["topic"] for row in accidents.load(today)}
    active = sum(t["topic"] in pool_topics and t["status"] not in ("done", "dropped", "parked") for t in topics)
    if active >= ACCIDENT_LEADS_ACTIVE:
        return []
    known = [t["topic"] for t in topics] + list(records)
    for base in (EPISODES, REJECTED, ROOT / "content" / "shelved"):
        for path in base.glob("ep[0-9][0-9][0-9]/topic.json"):
            meta = _json(path, {})
            if meta.get("topic"):
                known.append(meta["topic"])
    used_ids = {record["candidate_id"] for record in records.values() if record.get("candidate_id")}
    lines = CALENDAR.read_text(encoding="utf-8").splitlines()
    added = []
    while active + len(added) < ACCIDENT_LEADS_ACTIVE:
        candidate = accidents.next_candidate(known, used_ids, today)
        if not candidate or not insert_backlog(lines, candidate["series"], candidate["topic"]):
            break
        records[candidate["topic"]] = {
            "candidate_id": candidate["id"], "score": 8, "readers": 0, "editorial_priority": 36,
            "source_urls": [source["url"] for source in candidate["sources"]],
            "checked_at": candidate["checked_at"], "why": "Source-checked accident research lead",
        }
        known.append(candidate["topic"])
        used_ids.add(candidate["id"])
        added.append(f"{candidate['topic']} ({candidate['series']}, source-checked research lead)")
    if added:
        CALENDAR.write_text("\n".join(lines) + "\n", encoding="utf-8")
        stories._save(data)
    return added


def add_stories(run: Run, today: date | None = None) -> list[str]:
    """The strongest stories in the pool of real tragedies (stories.py): the pool is harvested again every
    stories.FRESH_DAYS, and each day the most-read unscored candidates are scored and the best added."""
    from . import stories

    today = today or _now().date()
    data = stories._load()
    harvested = data.get("harvested", "1970-01-01")
    if (today - date.fromisoformat(harvested)).days >= stories.FRESH_DAYS:
        stories.harvest(data, today)
        data["harvested"] = today.isoformat()
        stories._save(data)
    topics = calendar_topics(today)
    known = [t["topic"] for t in topics] + [e["title"] or "" for e in episodes()]
    kept = []
    for _ in range(stories.DAILY_BATCHES):
        batch = stories.score(data, SERIES, known + [s["topic"] for s in kept])
        if not batch and not any("score" not in c and c.get("readers") for c in data.get("candidates", {}).values()):
            break
        kept += batch
    known_words = [_key_words(k) for k in known]
    lines = CALENDAR.read_text(encoding="utf-8").splitlines()
    added = []
    for story in sorted(kept, key=lambda s: -s["score"]):
        if _repeats(story["topic"], known_words) or not insert_backlog(lines, story["series"], story["topic"]):
            continue
        known_words.append(_key_words(story["topic"]))
        data.setdefault("topics", {})[story["topic"]] = {
            "score": story["score"], "readers": story["readers"], "wikipedia": story["wikipedia"], "why": story["why"]}
        added.append(f"{story['topic']} ({story['series']}, story {story['score']}/10, "
                     f"{story['readers']:,} readers in {stories.READ_DAYS} days)")
    CALENDAR.write_text("\n".join(lines) + "\n", encoding="utf-8")
    stories._save(data)
    return added


def insert_timely(lines: list[str], rows: list[dict], today: date) -> list[str]:
    """CALENDAR.md's lines with `rows` ({"topic", "series", "why"}) added to the Timely table, which is put at the
    top of the calendar when it isn't there yet."""
    lines = list(lines)
    if not any(line.startswith("## Timely") for line in lines):
        at = next((i for i, line in enumerate(lines) if line.startswith("## ")), len(lines))
        lines[at:at] = [TIMELY_HEADING, "", "| Added | Story | Series | Why |", "|---|---|---|---|", ""]
    header = next(i for i, line in enumerate(lines) if line.startswith("## Timely"))
    end = next((i for i in range(header + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    while not lines[end - 1].startswith("|"):
        end -= 1

    def cell(text) -> str:
        return " ".join(str(text).replace("|", "/").split())

    lines[end:end] = [f"| {today.isoformat()} | {cell(r['topic'])} | {r['series']} | {cell(r['why'])} |" for r in rows]
    return lines


def _verified(items: list[dict], known_words: list[set[str]], limit: int) -> list[dict]:
    """Up to `limit` of the proposed topics that are in a series, aren't close to a known one, and name a real
    English Wikipedia article, each starting with that article's title as the calendar's topics do."""
    from .research import _existing

    rows = []
    for item in items:
        if len(rows) >= limit:
            break
        wiki, topic = (item.get("wikipedia") or "").strip(), (item.get("topic") or "").strip()
        if item.get("series") not in SERIES or not wiki or _repeats(topic, known_words):
            continue
        title = next(iter(_existing([wiki])), None)
        if not title:
            continue
        if not topic.lower().startswith((title.lower(), wiki.lower())):
            topic = f"{title}: {topic}"
        rows.append({"topic": topic, "series": item["series"], "why": item.get("why", "")})
        known_words.append(_key_words(topic))
    return rows


def _write_timely(rows: list[dict]) -> None:
    if rows:
        lines = insert_timely(CALENDAR.read_text(encoding="utf-8").splitlines(), rows, _now().date())
        CALENDAR.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _known_topics(topics: list[dict], eps: list[dict]) -> list[str]:
    return [t["topic"] for t in topics] + [e["title"] or "" for e in eps]


def add_timely(run: Run) -> list[str]:
    """Up to TREND_PER_DAY topics a day that are timely now: history and disaster articles trending on English
    Wikipedia and archaeology news, picked by the language model and checked like any other topic."""
    from xml.etree.ElementTree import ParseError

    from . import growth

    today = _now().date()
    topics = calendar_topics(today)
    room = TREND_PER_DAY - sum(1 for t in topics if t["kind"] == "timely" and t["date"] == today
                               and not t.get("why", "").startswith("Follow-up"))
    if room <= 0:
        return []
    trending, news = [], []
    try:
        trending = growth.trending_history()
    except (requests.RequestException, ValueError, KeyError) as err:
        log.warning("couldn't read Wikipedia's most-read articles: %s", err)
    try:
        news = growth.fetch_history_news()
    except (requests.RequestException, ParseError) as err:
        log.warning("couldn't read the history news feeds: %s", err)
    known = _known_topics(topics, episodes())
    picks = growth.pick_timely(trending, news, known, room)
    rows = _verified(picks, [_key_words(k) for k in known], room)
    _write_timely(rows)
    log.info("timely topics: %d trending history articles, %d history news items, %d added", len(trending), len(news), len(rows))
    return [f"{r['topic']} ({r['series']}; timely: {r['why']})" for r in rows]


def _by_video(eps: list[dict]) -> dict[str, dict]:
    """Episodes by the YouTube video id Buffer posted them as."""
    found = {}
    for e in eps:
        if match := re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", (e["record"] or {}).get("youtube_url") or ""):
            found[match.group(1)] = e
    return found


def breakout_topics(run: Run, state: dict) -> list[str]:
    """For each Short that broke out (growth.breakouts) and wasn't acted on before, queue FOLLOW_UPS follow-ups in
    its series at the top of the calendar. Acted-on Shorts are kept in state.json's "breakouts" so a Short
    triggers once. Returns a line per breakout for the day's report."""
    from . import growth

    snapshots = [s for p in sorted(ANALYTICS.glob("*.json"))[-10:] if (s := _json(p))]
    done = state.setdefault("breakouts", {})
    eps = episodes()
    by_video = _by_video(eps)
    today = _now().date().isoformat()
    lines = []
    for hit in growth.breakouts(snapshots, set(done))[:2]:
        e = by_video.get(hit["video"])
        if not e or e["series"] not in SERIES:
            done[hit["video"]] = {"on": today, "short": None, "added": 0}
            continue
        spec = yaml.safe_load((e["folder"] / "short.yaml").read_text(encoding="utf-8")) if (e["folder"] / "short.yaml").exists() else {}
        short = {"title": e["title"], "topic": (e["topic"] or {}).get("topic"), "series": e["series"],
                 "hook": ((spec.get("beats") or [{}])[0]).get("text", "")}
        known = _known_topics(calendar_topics(), episodes())
        ratio = f"{hit['ratio']}x" if hit["ratio"] else "far above"
        why = f"Follow-up to {e['id']}, which broke out ({hit['views']:,} views in {hit['hours']:.0f} h, {ratio} the median)"
        items = [dict(i, series=e["series"], why=why) for i in growth.propose_followups(short, known, FOLLOW_UPS)]
        rows = _verified(items, [_key_words(k) for k in known], FOLLOW_UPS)
        _write_timely(rows)
        done[hit["video"]] = {"on": today, "short": e["id"], "views": hit["views"], "ratio": hit["ratio"], "added": len(rows)}
        _write_json(STATUS / "state.json", state)
        lines.append(f"{e['id']} \"{e['title']}\" broke out: {hit['views']:,} views {hit['hours']:.0f} hours after going live, "
                     f"{ratio} the median of its peers at that age ({hit['median']:,.0f}); queued "
                     + ("; ".join(r["topic"] for r in rows) or "no follow-up that passed the checks"))
    _write_json(STATUS / "state.json", state)
    return lines


# --- producing and publishing ----------------------------------------------------------------------------


def month_minutes() -> float:
    """Actions minutes this calendar month (UTC), from the run history; each job is billed in whole minutes."""
    month = _now().astimezone(timezone.utc).strftime("%Y-%m")
    total = 0.0
    for line in (STATUS / "history.jsonl").read_text(encoding="utf-8").splitlines() if (STATUS / "history.jsonl").exists() else []:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("host") == "github-actions" and str(entry.get("started_at_utc", "")).startswith(month):
            total += int(entry.get("seconds", 0) // 60) + 2
    return total


def repo_is_public() -> bool:
    """Whether this runner's repository is public, where GitHub doesn't meter standard runners. Unknown counts
    as private, so the monthly budget stays on."""
    if not (repo := os.environ.get("GITHUB_REPOSITORY")):
        return False
    try:
        event = json.loads(Path(os.environ.get("GITHUB_EVENT_PATH", "")).read_text(encoding="utf-8"))
        if isinstance(private := (event.get("repository") or {}).get("private"), bool):
            return not private
    except (OSError, ValueError):
        pass
    try:
        response = requests.get(f"https://api.github.com/repos/{repo}", timeout=15)
        return response.ok and response.json().get("private") is False
    except (requests.RequestException, ValueError):
        return False


def minutes_budget() -> int | None:
    """The month's Actions minutes, or None when they're free."""
    return None if os.environ.get("GITHUB_ACTIONS") and repo_is_public() else MONTH_MINUTES


def runner_minutes_allowed() -> float:
    """Minutes this run may spend making Shorts on the runner: the month's use follows a straight line to the
    budget, so making Shorts here can't use up the minutes in the first week and stop the channel for the rest."""
    if minutes_budget() is None:
        return float(PRODUCE_MINUTES)
    now = _now().astimezone(timezone.utc)
    elapsed = (now.day - 1 + (now.hour + now.minute / 60) / 24) / calendar.monthrange(now.year, now.month)[1]
    line = (MONTH_MINUTES - MINUTES_RESERVE) * elapsed + RUNNER_MINUTES_PER_SHORT
    return max(0.0, min(PRODUCE_MINUTES, line - month_minutes()))


def capacity() -> dict:
    """How many Shorts this run can start: on Modal while this month's credit lasts, then on this runner."""
    cloud, credit_left = 0, None
    if (os.environ.get("MODAL_TOKEN_ID") or ON_MODAL) and os.environ.get("YTC_STUDIO_HERE") != "1":
        if (cost := _modal_cost()) is not None:
            # Workers still going haven't been billed in full.
            credit_left = MODAL_CREDIT - MODAL_RESERVE - cost["metered"] - len(inventory()["remote"]) * MODAL_PER_SHORT
            cloud = max(0, int(credit_left // MODAL_PER_SHORT))
    minutes = runner_minutes_allowed() if os.environ.get("GITHUB_ACTIONS") else 0 if ON_MODAL else PRODUCE_MINUTES
    return {"cloud": cloud, "runner": int(minutes // RUNNER_MINUTES_PER_SHORT) * LANES, "runner_minutes": round(minutes),
            "modal_credit_left": None if credit_left is None else round(credit_left, 2)}


def _next_quota_reset(after: datetime | None = None) -> datetime:
    """The first reset of Gemini's free daily quotas (midnight Pacific time) after `after`, or from now."""
    pacific = after.astimezone(ZoneInfo("America/Los_Angeles")) if after else datetime.now(ZoneInfo("America/Los_Angeles"))
    return datetime.combine(pacific.date() + timedelta(days=1), clock(0, 5), pacific.tzinfo).astimezone(IST)


def _refund_attempt(folder: Path, spawned: bool, quota: bool = False, stopped: datetime | None = None) -> None:
    """An episode stopped by Gemini's quota or an overload keeps the attempt it didn't get to use. One stopped by
    the quota (which with the backup models only the review runs out of) waits for the first reset after it
    stopped (_jobs): a worker that ran out before a reset and is collected after it can go on at once."""
    meta = _json(folder / "topic.json")
    if meta:
        meta["attempts"] = max(0, meta.get("attempts", 1) - 1)
        if spawned:
            meta["spawns"] = max(0, meta.get("spawns", 0) - 1)
        if quota:
            meta["waits_until"] = _next_quota_reset(stopped).isoformat(timespec="minutes")
        _write_json(folder / "topic.json", meta)


def _waiting(meta: dict) -> bool:
    """The episode stopped for a review Gemini's Flash models had no quota left for, and they haven't reset yet."""
    return bool(meta.get("waits_until")) and _now() < datetime.fromisoformat(meta["waits_until"])


def _finish_topic(episode_id: str, outcome: str) -> None:
    if outcome not in ("ready", "rejected"):
        return
    if topic := next((t for t in calendar_topics() if t["episode"] == episode_id), None):
        mark_topic(topic, "done" if outcome == "ready" else _rejected_mark(episode_id), episode_id)


def _rejected_mark(episode_id: str) -> str:
    """Parked (tried again after PARK_DAYS) unless the research found too little to go on or this was the retry."""
    folder = REJECTED / episode_id
    reason = str((_json(folder / "review.json") or {}).get("reason", ""))
    retry = (_json(folder / "topic.json") or {}).get("retry_of")
    return "dropped" if reason.startswith("research:") or retry else "parked"


def _resumable(eps: list[dict]) -> list[dict]:
    """Half-made episodes that can go on now. One waiting for Flash's review is left until the reset, unless so few
    are ready that a backup model judges it (studio.review)."""
    few_ready = inventory(eps)["total"] < CURSOR_BELOW
    return [e for e in eps if e["state"] == "making" and not (e["folder"] / "editorial_hold.json").exists()
            and (few_ready or not _waiting(e["topic"]))]


def _jobs(count: int) -> list[dict]:
    """Half-made episodes first (_resumable), then new topics from the calendar, each with its folder and topic.json."""
    from . import accidents, stories, studio

    eps = episodes()
    resumable = {e["id"] for e in _resumable(eps)}
    half_made = []
    for e in [e for e in eps if e["state"] == "making"]:
        candidate_id = (e["topic"].get("candidate_id") or
                        accidents.held_candidate_id(e["topic"].get("topic", "")))
        if candidate_id:
            candidate = accidents.by_topic(e["topic"].get("topic", ""))
            if not candidate or candidate["id"] != candidate_id:
                log.info("checked accident draft %s lost its exact source plan", candidate_id)
                continue
        if candidate_id and not accidents.selection_allowed(candidate_id):
            log.info("held checked accident draft %s cannot resume", candidate_id)
            continue
        if (e["folder"] / "editorial_hold.json").exists():
            continue
        if e["topic"].get("spawns", 0) >= MAX_SPAWNS:
            studio.reject(e["folder"], f"its cloud worker stopped {MAX_SPAWNS} times without finishing")
            _finish_topic(e["id"], "rejected")
        elif e["id"] in resumable:
            half_made.append(e)
    jobs = [{"id": e["id"], "topic": e["topic"]["topic"], "series": e["topic"]["series"], "at": e["topic"].get("at")}
            for e in half_made[:count]]
    today = _now().date()
    tracked = stories._load().get("topics", {})
    tracked = tracked if isinstance(tracked, dict) else {}
    for topic in choose_topics(count - len(jobs), eps):
        candidate = accidents.by_topic(topic["topic"], today)
        record = tracked.get(topic["topic"], {})
        tracked_id = record.get("candidate_id") if isinstance(record, dict) else None
        held_id = accidents.held_candidate_id(topic["topic"])
        if (tracked_id and (not candidate or candidate["id"] != tracked_id)) or \
                (held_id and (not candidate or candidate["id"] != held_id)):
            log.info("checked accident lead %s has no matching source plan", tracked_id or held_id)
            continue
        candidate_id = tracked_id or held_id or (candidate["id"] if candidate else None)
        if candidate_id and not accidents.selection_allowed(candidate_id):
            log.info("checked accident lead %s is held before producer selection", candidate_id)
            continue
        episode_id = studio.next_id()
        at = topic["date"].isoformat() if topic["kind"] == "anniversary" and topic.get("date") else None
        meta = {"topic": topic["topic"], "series": topic["series"], "at": at,
                "started_at": _now().isoformat(timespec="seconds"), "attempts": 0}
        if candidate:
            meta["candidate_id"] = candidate["id"]
            meta["research_sources"] = candidate["sources"]
            meta["research_cautions"] = candidate["cautions"]
        if topic in urgent([topic], today):
            meta["timely"] = True
        if topic["status"] == "parked":
            meta["retry_of"] = topic["episode"]
        _write_json(EPISODES / episode_id / "topic.json", meta)
        mark_topic(topic, "making", episode_id)
        jobs.append({"id": episode_id, "topic": topic["topic"], "series": topic["series"], "at": at})
    return jobs


def _spawn(run: Run, jobs: list[dict]) -> list[dict]:
    """Start a Modal worker per episode. Returns the jobs this runner has to make itself."""
    from . import cloud

    if not any(s["name"] == "deploy" for s in run.stages):
        with run.stage("deploy"):
            cloud.deploy()
    # A run on Modal is inside the deployed app, so its workers can still start on the version already there.
    if not any(s["name"] == "deploy" and s["ok"] for s in run.stages) and not ON_MODAL:
        return jobs
    ready = inventory()["total"]
    cursor, last_resort = ready < CURSOR_BELOW, ready < LAST_RESORT_BELOW
    for job in jobs:
        folder = EPISODES / job["id"]
        if (folder / "editorial_hold.json").exists():
            run.notes.append(f"{job['id']} is on editorial hold; no worker started")
            continue
        with run.stage(f"start {job['id']}") as entry:
            entry["detail"] = job["topic"]
            meta = _json(folder / "topic.json", {})
            meta["spawns"] = meta.get("spawns", 0) + 1
            _write_json(folder / "topic.json", meta)
            key = f"{job['id']}-{secrets.token_hex(4)}"
            call_id = cloud.spawn(ROOT, {**job, "key": key, "cursor": cursor, "last_resort": last_resort})
            _write_json(folder / "remote.json", {"call_id": call_id, "key": key, "spawned_at": _now().isoformat(timespec="seconds"),
                                                 "topic": job["topic"]})
            run.spawned.append({"id": job["id"], "topic": job["topic"], "call_id": call_id})
        # A failed start may still have started a worker, so the episode waits for the next run rather than
        # being made here as well.
    return []


def _produce_here(run: Run, jobs: list[dict], minutes: float) -> None:
    """Make Shorts on this machine, LANES at a time, starting each only while `minutes` more can pay for it."""
    from . import llm, studio

    if not jobs:
        return
    # Modal's credit is for its workers; and minutes spent waiting out an overloaded Gemini are billed here.
    os.environ["YTC_RENDER_HERE"] = "1"
    llm.OVERLOAD_WAIT = 300
    # As with workers (_spawn): Cursor finishes a Short only while few are ready, the only time it starts one.
    llm.CURSOR_FALLBACK = inventory()["total"] < CURSOR_BELOW
    studio.LAST_RESORT = inventory()["total"] < LAST_RESORT_BELOW
    deadline = run.minutes() + minutes
    waiting = list(jobs)
    # Also guards CALENDAR.md, which finishing a topic rewrites.
    lock = threading.Lock()
    stop, resting = threading.Event(), threading.Event()

    def next_job() -> dict | None:
        with lock:
            if stop.is_set() or not waiting or run.minutes() + RUNNER_MINUTES_PER_SHORT > deadline + 1:
                return None
            if llm.gemini_spent() and inventory()["total"] >= CURSOR_BELOW:
                resting.set()
                stop.set()
                return None
            run.started_here += 1
            return waiting.pop(0)

    def lane() -> None:
        while job := next_job():
            with run.stage(f"make {job['id']}") as entry:
                entry["detail"] = job["topic"]
                result = studio.produce(job["topic"], job["series"], job["id"], at=job["at"])
                run.made.append(result)
                entry["detail"] = f"{job['topic']}: {result['outcome']}" + (f" ({result.get('reason')})" if result.get("reason") else "")
                with lock:
                    _finish_topic(job["id"], result["outcome"])
            if entry.get("quota") or "Overloaded" in entry.get("error", ""):
                with lock:
                    _refund_attempt(EPISODES / job["id"], spawned=False, quota=bool(entry.get("quota")))
                if entry.get("quota"):
                    run.quota_until = _next_quota_reset()
                stop.set()

    lanes = [threading.Thread(target=lane, name=f"lane-{n + 1}") for n in range(min(LANES, len(jobs)))]
    for thread in lanes:
        thread.start()
    for thread in lanes:
        thread.join()
    if llm.gemini_spent():
        run.quota_until = _next_quota_reset()
    if resting.is_set():
        run.notes.append(f"Gemini's free quota is spent and {inventory()['total']} Shorts are ready; "
                         "the rest waits for its reset instead of going to Cursor")
    elif stop.is_set():
        run.notes.append("Gemini is out of free quota or overloaded; the rest waits for the next run")
    elif waiting:
        run.notes.append(f"{len(waiting)} Shorts wait for a later run's share of the Actions minutes")
    run.renders["modal"] += studio.renders.count("modal")
    run.renders["runner"] += studio.renders.count("runner")
    studio.renders.clear()


def produce(run: Run, count: int, *, cloud_only: bool = False, episode_id: str | None = None) -> None:
    """Start up to `count` Shorts: Modal workers while this month's credit lasts, then on this runner."""
    room = run.capacity = capacity()
    if cloud_only:
        room = run.capacity = {**room, "runner": 0, "runner_minutes": 0}
    if episode_id:
        if room["cloud"] < 1:
            raise RuntimeError(f"targeted draft {episode_id} has no cloud capacity")
        episode = next((e for e in episodes() if e["id"] == episode_id), None)
        if (not episode or episode["state"] != "making" or
                (episode["folder"] / "editorial_hold.json").exists()):
            raise RuntimeError(f"targeted draft {episode_id} is not an unheld unfinished episode")
        if episode["topic"].get("spawns", 0) >= MAX_SPAWNS:
            raise RuntimeError(f"targeted draft {episode_id} has reached the worker limit")
        jobs = [{"id": episode_id, "topic": episode["topic"]["topic"],
                 "series": episode["topic"]["series"], "at": episode["topic"].get("at")}]
    else:
        jobs = _jobs(min(count, room["cloud"] + room["runner"]))
    if len(jobs) < count:
        run.notes.append(f"room for {len(jobs)} of the {count} Shorts wanted: Modal's credit covers {room['cloud']}, "
                         f"this run's share of the Actions minutes {room['runner']}")
    cloud, here = jobs[:room["cloud"]], jobs[room["cloud"]:]
    if cloud:
        not_started = _spawn(run, cloud)
        if not_started:
            run.notes.append("Modal couldn't be deployed; making the Shorts on this runner")
            here = not_started + here
    _produce_here(run, here, room["runner_minutes"])


def collect(run: Run) -> str:
    """Bring in what finished Modal workers made. A worker that outlives its timeout is stopped and retried."""
    from . import cloud

    done = []
    for e in [e for e in episodes() if e["state"] == "remote"]:
        remote = e["remote"]
        outcome = cloud.collect(ROOT, e["id"], remote["call_id"], remote.get("key"))
        if outcome is None:
            hours = (_now() - datetime.fromisoformat(remote["spawned_at"])).total_seconds() / 3600
            if hours < STALE_HOURS:
                done.append(f"{e['id']} still working ({hours:.1f} h)")
                continue
            cloud.cancel(remote["call_id"])
            outcome = {"id": e["id"], "outcome": "unfinished", "reason": f"the worker ran over {STALE_HOURS} hours and was stopped"}
        (e["folder"] / "remote.json").unlink(missing_ok=True)
        if outcome["outcome"] == "rejected" and (ROOT / "content" / "rejected" / e["id"]).exists():
            shutil.rmtree(e["folder"])
        outcome.setdefault("topic", remote.get("topic"))
        renders = outcome.pop("renders", [])
        run.renders["modal"] += renders.count("modal")
        run.renders["runner"] += renders.count("runner")
        for call in outcome.pop("llm_calls", []):
            run.worker_calls.append(call)
        stopped = datetime.fromisoformat(outcome.pop("stopped_at", None) or remote["spawned_at"])
        run.made.append(outcome)
        _finish_topic(e["id"], outcome["outcome"])
        gemini = outcome.get("quota") or outcome.get("overloaded")
        if gemini or (outcome["outcome"] == "unfinished" and _modal_credit_spent()):
            _refund_attempt(e["folder"], spawned=True, quota=bool(outcome.get("quota")), stopped=stopped)
            why = ("Gemini's free quota" if outcome.get("quota") else "Gemini's free tier being overloaded") if gemini \
                else "Modal's monthly credit running out"
            run.notes.append(f"{e['id']} stopped on {why}; it resumes in a later run")
        if outcome.get("quota") and (reset := _next_quota_reset(stopped)) > _now():
            run.quota_until = reset
        done.append(f"{e['id']} {outcome['outcome']}" + (f" ({outcome.get('reason')})" if outcome.get("reason") else ""))
    waiting = {e["remote"].get("key") or e["id"] for e in episodes() if e["state"] == "remote"}
    try:
        if removed := cloud.sweep(waiting):
            done.append(f"cleared {removed} files no episode was waiting for")
    except Exception as err:
        log.warning("couldn't clear old worker files: %s", err)
    return "; ".join(done)[:600] or "nothing in the cloud"


def _scores(e: dict) -> int:
    held = e.get("held") or {}
    if held.get("scores"):
        return sum(held["scores"].values())
    text = (e["folder"] / "research.md").read_text(encoding="utf-8") if (e["folder"] / "research.md").exists() else ""
    match = re.search(r"\| Hook \| Clarity \| Payoff \| Visuals \| Loop \|\n\|[-| ]+\|\n\|([^\n]+)\|", text)
    return sum(int(x) for x in re.findall(r"\d", match.group(1))) if match else 0


def check_channel(run: Run) -> bool:
    """Whether Buffer can post to the YouTube channel. Disconnected, locked, or paused, it fails every queued Short,
    and only the owner can fix it."""
    from .publish import channel

    with run.stage("buffer channel") as entry:
        found = channel()
        wrong = [name for flag, name in (("isDisconnected", "disconnected"), ("isLocked", "locked"),
                                          ("isQueuePaused", "paused")) if found.get(flag)]
        entry["detail"] = " and ".join(wrong) or "connected"
        if wrong:
            run.owner_action.append(
                f"Buffer's YouTube channel is {entry['detail']}, so no Short goes out until it's fixed: in Chrome's "
                "aksha.shivam18@gmail.com profile open https://publish.buffer.com, go to Settings > Channels, and "
                "reconnect or unpause History's Last Hours.")
            return False
    return True


def _resending(record: dict) -> bool:
    """Whether cloud.slot_watch may still send a failed post again: its due time, which each try moves, is within
    publish.RESEND_WINDOW."""
    from .publish import RESEND_WINDOW

    return bool(record.get("due_at")) and timedelta(0) <= _now() - datetime.fromisoformat(record["due_at"]) <= RESEND_WINDOW


def repair_posts(run: Run, requeue: bool = True) -> None:
    """Keep every Short's hosted video within render.MAX_UPLOAD_MB (Buffer fetches it when the post goes out), and
    send a post Buffer couldn't publish back to waiting, up to RETRIES times (not while `requeue` is off: a post
    that failed on a disconnected channel would only fail again), once cloud.slot_watch has stopped sending it
    again."""
    from .publish import MEDIA_BINDING_FIELDS, SCHEDULING_HOLD, delete_post, edit_post, hosted_bytes, shrink_hosted, unhost_video
    from .render import MAX_UPLOAD_MB
    from .spec import ShortSpec

    if SCHEDULING_HOLD.exists():
        return
    for e in episodes():
        name = "publish.json" if e["record"] else "hold.json"
        record = e["record"] or e["held"] or {}
        path = e["folder"] / name
        bound = any(record.get(field) for field in MEDIA_BINDING_FIELDS)
        if e["state"] in ("scheduled", "waiting") and record.get("media_url") and "media_bytes" not in record:
            try:
                record["media_bytes"] = hosted_bytes(record["media_url"])
            except requests.RequestException as err:
                log.warning("couldn't size %s's video: %s", e["id"], err)
                continue
            if record["media_bytes"] > MAX_UPLOAD_MB * 1_000_000:
                with run.stage(f"shrink {e['id']}'s video") as entry:
                    if bound:
                        raise RuntimeError("automatic shrink would change bound media; render a smaller video, "
                                           "review it, and rehost")
                    old = record["media_public_id"]
                    record["media_public_id"], record["media_url"] = shrink_hosted(old, record["media_url"])
                    if e["state"] == "scheduled":
                        edit_post(record["buffer_post_id"], ShortSpec.load(e["folder"] / "short.yaml"), record["media_url"])
                    entry["detail"] = f"{record['media_bytes'] / 1e6:.0f} MB -> "
                    record["media_bytes"] = hosted_bytes(record["media_url"])
                    entry["detail"] += f"{record['media_bytes'] / 1e6:.0f} MB"
                    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
                    unhost_video(old)
                continue
            path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        elif e["state"] == "error" and requeue and record.get("retries", 0) < RETRIES and not _resending(record):
            with run.stage(f"requeue {e['id']}") as entry:
                if bound:
                    size = hosted_bytes(record["media_url"])
                    if size > MAX_UPLOAD_MB * 1_000_000:
                        raise RuntimeError("requeue would require shrinking bound media; render a smaller video, "
                                           "review it, and rehost")
                record["retries"] = record.get("retries", 0) + 1
                path.write_text(json.dumps(record, indent=2), encoding="utf-8")
                old = record["media_public_id"]
                smaller = None if bound else shrink_hosted(old, record["media_url"])
                public_id, url = smaller or (old, record["media_url"])
                held = {"id": e["id"], "title": record["title"], "series": e["series"], "media_public_id": public_id,
                        "media_url": url, "media_bytes": hosted_bytes(url), "hosted_at": _now().isoformat(timespec="seconds"),
                        "retries": record["retries"], "failed": record.get("error"),
                        **({"crossposts": record["crossposts"]} if record.get("crossposts") else {}),
                        **{k: record[k] for k in MEDIA_BINDING_FIELDS if k in record}}
                (e["folder"] / "hold.json").write_text(json.dumps(held, indent=2), encoding="utf-8")
                delete_post(record["buffer_post_id"])
                path.unlink()
                if smaller:
                    unhost_video(old)
                entry["detail"] = f"back to waiting after Buffer failed it ({record.get('error') or 'no reason given'})"[:300]


def preflight_posts(run: Run) -> None:
    """Check each post due within PREFLIGHT_HOURS as it will go out: Buffer still has it, scheduled and public, with
    a title and description YouTube takes and the video its record hosts, and that video downloads whole. What a
    run can fix it fixes; anything else fails the stage, which the monitor raises as an alert."""
    from .publish import MEDIA_BINDING_FIELDS, SCHEDULING_HOLD, buffer_busy, description, edit_post, fetch_video, hosted_bytes, post, youtube_problems
    from .spec import ShortSpec

    if SCHEDULING_HOLD.exists():
        return
    soon = _now() + timedelta(hours=PREFLIGHT_HOURS)
    for e in episodes():
        if buffer_busy():
            return
        record = e["record"]
        if e["state"] != "scheduled" or not record.get("due_at") or datetime.fromisoformat(record["due_at"]) > soon:
            continue
        with run.stage(f"preflight {e['id']}") as entry:
            path = e["folder"] / "publish.json"
            found = post(record["buffer_post_id"])
            if found is None:
                keep = ("media_public_id", "media_url", "media_bytes", "hosted_at", "retries", "crossposts") + MEDIA_BINDING_FIELDS
                held = {"id": e["id"], "title": record["title"], "series": e["series"],
                        **{k: record[k] for k in keep if k in record}}
                (e["folder"] / "hold.json").write_text(json.dumps(held, indent=2), encoding="utf-8")
                path.unlink()
                entry["detail"] = "Buffer no longer has its post, so it's back to waiting"
                continue
            if found["status"] in ("sending", "sent", "error"):
                entry["detail"] = f"Buffer has it as {found['status']}"
                continue
            if found["status"] != "scheduled":
                raise RuntimeError(f"Buffer has the post due {record['due_at']} as {found['status']}, so it won't go out")
            url = record.get("media_url") or found["video"]
            fixed = youtube_problems(found["title"], found["text"] or "")
            if found["privacy"] != "public":
                fixed.append(f"privacy {found['privacy']}")
            if found["video"] != url:
                fixed.append("video link")
            if fixed:
                spec = ShortSpec.load(e["folder"] / "short.yaml")
                manifest = json.loads((e["folder"] / "work" / "manifest.json").read_text(encoding="utf-8"))
                edit_post(record["buffer_post_id"], spec, url, description(spec, manifest))
            if record.get("fetched_url") == url:
                hosted_bytes(url)
                checked = "video still hosted"
            else:
                fetched = fetch_video(url)
                record.update(media_bytes=fetched["bytes"], fetched_url=url)
                path.write_text(json.dumps(record, indent=2), encoding="utf-8")
                checked = f"video downloads whole ({fetched['bytes'] / 1e6:.0f} MB in {fetched['seconds']:.0f} s)"
            entry["detail"] = (f"fixed {', '.join(fixed)}; " if fixed else "") + checked


def per_day(stock: int, slots: int) -> int:
    """Shorts a day to schedule: as many as leaves three days of posting in the made-but-unposted stock, but at least
    one, so a slow stretch of making thins the posting out instead of leaving days with nothing."""
    return max(1, min(slots, stock // 3))


# The first relaunch batch is a quality and format test. New slots are earned from at least 20 comparable Shorts
# with enough engaged views to distinguish a trend from a handful of channel-page visits. See strategy/STRATEGY.md.
PACE = ((1, 3),)
BASE_PACE = 3
CAUTION_PACE = 2
PACE_MIN_ENGAGED = 100
# The last 10 Shorts falling this far below the 10 before them in engaged views per Short drops back to BASE_PACE.
PACE_DROP = 0.7


def _pace_numbers() -> tuple[list[float], list[float]]:
    """Engaged views and engaged share of the Shorts 48 hours old or more, oldest first."""
    latest = max(ANALYTICS.glob("*.json"), default=None)
    rows = [r for r in _video_rows(_json(latest, {}), episodes()) if r["hours"] >= 48
            and isinstance(r["engaged_share"], (int, float))] if latest else []
    return [r["views"] * r["engaged_share"] for r in rows], [r["engaged_share"] for r in rows]


def slots_per_day(today: date | None = None) -> int:
    """How many of publish.SLOTS a day uses (PACE), held back while the per-Short numbers don't earn more."""
    from .publish import SLOTS

    planned = max(n for day, n in PACE if day_number(today) >= day) if day_number(today) >= PACE[0][0] else BASE_PACE
    if planned <= BASE_PACE:
        return min(len(SLOTS), planned)
    # Scheduling runs through here, so a stats file it can't read costs the extra slots, not the posting.
    try:
        engaged, share = _pace_numbers()
    except Exception as err:
        log.warning("couldn't read engagement for the posting pace (%s); posting %d a day", err, BASE_PACE)
        return BASE_PACE
    if len(engaged) < 20:
        return BASE_PACE
    recent, before = _median(engaged[-10:]), _median(engaged[-20:-10])
    recent_share, before_share = _median(share[-10:]), _median(share[-20:-10])
    if before < PACE_MIN_ENGAGED or recent < PACE_MIN_ENGAGED or recent < PACE_DROP * before:
        return BASE_PACE
    if recent >= 0.9 * before and recent_share and before_share and recent_share >= 0.9 * before_share:
        return min(len(SLOTS), planned)
    return min(len(SLOTS), planned, CAUTION_PACE)


def _worth_holding(day: date, supply: int, slots: int, today: date) -> bool:
    """Whether a Short waits for its anniversary: only while the other Shorts made fill every slot until then, as an
    empty day costs a young channel more than missing the date."""
    return supply - 1 >= (day - today).days * slots


def release_anniversaries(run: Run) -> None:
    """Back to waiting with each Short booked on its anniversary that is no longer worth holding for, so this run's
    publish puts it in the next free slot. Once moved off its date it isn't touched again."""
    from .publish import AUDIENCE_TZ, MEDIA_BINDING_FIELDS, delete_post

    eps = episodes()
    today = datetime.now(AUDIENCE_TZ)
    supply = sum(1 for e in eps if e["state"] in ("scheduled", "waiting"))
    slots = slots_per_day()
    for e in eps:
        record, at = e["record"], (e["topic"] or {}).get("at")
        if e["state"] != "scheduled" or not at or not record.get("due_at"):
            continue
        due = datetime.fromisoformat(record["due_at"]).astimezone(AUDIENCE_TZ)
        day = date.fromisoformat(at)
        if due.date() != day or due - today < timedelta(days=1) or _worth_holding(day, supply, slots, today.date()):
            continue
        with run.stage(f"release {e['id']}") as entry:
            keep = ("media_public_id", "media_url", "media_bytes", "hosted_at", "retries", "crossposts") + MEDIA_BINDING_FIELDS
            held = {"id": e["id"], "title": record["title"], "series": e["series"], **{k: record[k] for k in keep if k in record}}
            delete_post(record["buffer_post_id"])
            (e["folder"] / "hold.json").write_text(json.dumps(held, indent=2), encoding="utf-8")
            (e["folder"] / "publish.json").unlink()
            entry["detail"] = f"off its {day:%b %d} anniversary slot: too few other Shorts to fill the days before it"


def publish_waiting(run: Run) -> None:
    from .publish import AUDIENCE_TZ, BUFFER_QUEUE_LIMIT, SCHEDULING_HOLD, SLOTS, next_slots, posts, schedule

    if SCHEDULING_HOLD.exists():
        from .release import schedule_waiting
        schedule_waiting(run)
        return

    eps = episodes()
    waiting = [e for e in eps if e["state"] == "waiting"]
    if not waiting:
        return
    # Three days back covers every day a new post can land on; all of Buffer's history would cost a request per 50 posts.
    everything = [p for p in posts(since=datetime.now(AUDIENCE_TZ) - timedelta(days=3)) if p["status"] not in ("error", "draft")]
    queued = [p for p in everything if p["status"] != "sent"]
    free = BUFFER_QUEUE_LIMIT - len(queued)
    if free <= 0:
        run.notes.append(f"Buffer is full ({len(queued)} queued); {len(waiting)} waiting")
        return
    slots = slots_per_day()
    pace = per_day(len(queued) + len(waiting), slots)
    if pace < slots:
        run.notes.append(f"only {len(queued) + len(waiting)} Shorts made and unposted; scheduling {pace} a day")
    # Sent posts count toward their day's number.
    taken = {datetime.fromisoformat(p["dueAt"]).astimezone(AUDIENCE_TZ) for p in everything if p.get("dueAt")}
    by_post = {e["record"]["buffer_post_id"]: e for e in eps if e["record"]}
    last = max(queued, key=lambda p: p.get("dueAt") or "", default=None)
    last_series = by_post.get(last["id"], {}).get("series") if last else None
    today = datetime.now(AUDIENCE_TZ)

    supply = len(queued) + len(waiting)

    def anniversary(e):
        at = (e.get("held") or {}).get("anniversary") or (e.get("topic") or {}).get("at")
        day = date.fromisoformat(at) if at else None
        return day if day and _worth_holding(day, supply, slots, today.date()) else None

    def timely(e):
        return bool((e.get("topic") or {}).get("timely"))

    # Timely Shorts go right after anniversaries, while the news or trend they ride is fresh. A Short whose post
    # Buffer failed already lost one slot, so it takes the next one after those.
    ordered = sorted(waiting, key=lambda e: (anniversary(e) is None, anniversary(e) or date.max, not timely(e),
                                             not (e.get("held") or {}).get("retries"), -_scores(e), e["id"]))
    for _ in range(min(free, len(ordered))):
        pick = next((e for e in ordered if anniversary(e) or timely(e) or e["series"] != last_series), ordered[0])
        ordered.remove(pick)
        when = None
        if day := anniversary(pick):
            for slot in SLOTS[:3]:
                candidate = datetime.combine(day, slot, AUDIENCE_TZ)
                if candidate > today + timedelta(minutes=30) and candidate not in taken:
                    when = candidate
                    break
        # One slot a day more than the pace, so a timely Short goes out within a day instead of after the queue.
        when = when or next_slots(1, taken, per_day=min(len(SLOTS), pace + 1) if timely(pick) else pace)[0]
        with run.stage(f"schedule {pick['id']}") as entry:
            record = schedule(pick["folder"] / "short.yaml", when)
            taken.add(datetime.fromisoformat(record["due_at"]).astimezone(AUDIENCE_TZ))
            run.published.append({"id": pick["id"], "title": pick["title"], "due_at": record["due_at"]})
            entry["detail"] = record["due_at"]
            last_series = pick["series"]
        if not run.stages[-1]["ok"]:
            break


def crosspost_due(eps: list[dict], service: str, now: datetime, room: int, max_bytes: int) -> list[dict]:
    """Shorts scheduled on YouTube and not yet cross-posted to `service` (a failed try counts: it isn't sent
    again), due over 30 minutes from `now`, whose hosted video is measured and under `max_bytes`; soonest first,
    at most `room`."""
    due = [e for e in eps if e["state"] == "scheduled" and service not in (e["record"].get("crossposts") or {})
           and e["record"].get("media_url") and e["record"].get("due_at")
           and datetime.fromisoformat(e["record"]["due_at"]) > now + timedelta(minutes=30)
           and 0 < (e["record"].get("media_bytes") or 0) <= max_bytes]
    return sorted(due, key=lambda e: datetime.fromisoformat(e["record"]["due_at"]))[:max(0, room)]


def crosspost_scheduled(run: Run) -> None:
    """Schedule each Short that's scheduled on YouTube on the TikTok and Instagram channels switched on
    (publish.CROSSPOST_ENV) too, due at the same time, as far as each channel's Buffer queue has room. Off by
    default. What goes wrong is logged in the stage's detail and the Short's publish.json; it never fails the run.
    About 1 request per channel per run plus one per post, well within Buffer's 250 a day."""
    from .publish import AUDIENCE_TZ, BUFFER_QUEUE_LIMIT, SCHEDULING_HOLD, BufferBusy, caption, crosspost, crosspost_channels, posts
    from .render import MAX_UPLOAD_MB
    from .spec import ShortSpec

    if SCHEDULING_HOLD.exists():
        return
    limit = MAX_UPLOAD_MB * 1_000_000
    for service, channel_id in crosspost_channels().items():
        if not crosspost_due(episodes(), service, _now(), 1, limit):
            continue
        with run.stage(f"cross-post {service}") as entry:
            try:
                recent = posts(since=datetime.now(AUDIENCE_TZ) - timedelta(days=3), channel_id=channel_id)
            except BufferBusy:
                raise
            except (RuntimeError, requests.RequestException) as err:
                entry["detail"] = f"skipped: couldn't read the channel's Buffer queue ({err})"[:300]
                log.warning("cross-post %s: %s", service, err)
                continue
            live = [p for p in recent if p["status"] not in ("error", "draft")]
            queued = [p for p in live if p["status"] != "sent"]
            # A run that stopped after Buffer took a post, before its record was saved, would otherwise post it twice.
            by_lead = {(p.get("text") or "").split("\n\n", 1)[0]: p for p in live}
            done, failed = [], []
            todo = crosspost_due(episodes(), service, _now(), BUFFER_QUEUE_LIMIT - len(queued), limit)
            for e in todo:
                record = e["record"]
                try:
                    spec_path = e["folder"] / "short.yaml"
                    if twin := by_lead.get(caption(ShortSpec.load(spec_path)).split("\n\n", 1)[0]):
                        result = {"id": twin["id"], "status": twin["status"], "due_at": twin.get("dueAt")}
                    else:
                        result = crosspost(spec_path, service, channel_id, record["media_url"],
                                           datetime.fromisoformat(record["due_at"]))
                    done.append(e["id"])
                except BufferBusy:
                    raise
                except Exception as err:
                    result = {"error": f"{type(err).__name__}: {err}"[:300], "at": _now().isoformat(timespec="seconds")}
                    failed.append(f"{e['id']} ({result['error']})")
                    log.warning("cross-post %s of %s failed: %s", service, e["id"], err)
                record.setdefault("crossposts", {})[service] = result
                (e["folder"] / "publish.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
            waiting = len(crosspost_due(episodes(), service, _now(), BUFFER_QUEUE_LIMIT, limit))
            entry["detail"] = (f"scheduled {', '.join(done) or 'nothing'}" + (f"; failed {'; '.join(failed)}" if failed else "")
                               + (f"; {waiting} wait for room in its Buffer queue" if waiting else ""))[:600]


# --- daily routine ---------------------------------------------------------------------------------------


# A Short joins the learning log's scoreboard after this long: a day gives the first verdict on a Short, and at two
# a day, waiting longer means the lesson reaches Shorts made days later.
LEARN_FROM_HOURS = 24
# Fewer views than this cannot support a useful comparison of hooks, pictures,
# or retention; the first few channel-page visits are especially misleading.
LEARN_MIN_VIEWS = 100
LEARN_MIN_SHORTS = 3
# This many Shorts in a row not shown at 24 hours is a hold on the channel, not on any one Short.
NOT_SHOWN_STREAK = 3


def review_shorts(run: Run) -> list[str]:
    """Take each live Short's due checkpoint (review.CHECKPOINTS), tell the owner how it's doing, and feed any
    diagnosis into strategy/LEARNINGS.md so the next scripts apply it."""
    from . import review
    from .youtube import save_stats, short_numbers

    eps = episodes()
    live = _by_video([e for e in eps if e["state"] == "live"])
    now = _now()
    todo = []
    for video_id, e in live.items():
        sent = e["record"].get("sent_at") or e["record"].get("due_at")
        perf = _json(e["folder"] / "performance.json", {})
        if sent and (checkpoint := review.due(datetime.fromisoformat(sent), now, set(perf))):
            todo.append((video_id, e, checkpoint, perf))
    if not todo:
        return []
    numbers = short_numbers([t[0] for t in todo])
    channel = _json(ROOT / "kit" / "channel.json", {}).get("name", "the channel")
    topic = os.environ.get("YTC_NTFY_TOPIC")
    done, diagnosed = [], False
    for video_id, e, checkpoint, perf in todo:
        if video_id not in numbers:
            continue
        hours = (now - datetime.fromisoformat(numbers[video_id]["published"])).total_seconds() / 3600
        s = review.summary(numbers[video_id], hours)
        peers = [p[str(checkpoint)]["numbers"] for other in eps if other["id"] != e["id"]
                 and (p := _json(other["folder"] / "performance.json", {})) and str(checkpoint) in p]
        entry = {"taken_at": now.isoformat(timespec="seconds"), "numbers": s,
                 "verdict": review.verdict(s, [p["views"] for p in peers])}
        if checkpoint >= 24 and s["views"] >= review.DIAGNOSE_VIEWS:
            try:
                entry["diagnosis"] = review.diagnose(channel, e["id"], review.script_text(e["folder"]), s, peers[-10:])
                diagnosed = True
            except Exception as err:
                log.warning("couldn't diagnose %s: %s", e["id"], err)
        perf[str(checkpoint)] = entry
        _write_json(e["folder"] / "performance.json", perf)
        if topic:
            review.push(topic, f"{channel}: {e['id']} at {checkpoint} hours",
                        review.message(channel, e["id"], e["title"] or "", checkpoint, entry))
        done.append(f"{e['id']} at {checkpoint} h: {entry['verdict']}")
    day_old = [p["24"] for e in sorted(eps, key=lambda e: e["id"]) if (p := _json(e["folder"] / "performance.json", {})) and "24" in p]
    if len(day_old) >= NOT_SHOWN_STREAK and all(d["verdict"].startswith("not shown") for d in day_old[-NOT_SHOWN_STREAK:]):
        run.owner_action.append(
            f"YouTube hasn't shown the last {NOT_SHOWN_STREAK} Shorts in the Shorts feed after a day each, so the hold is on "
            "the channel, not the scripts. Verify the channel's phone number at youtube.com/verify (the one trust step "
            "it lacks), and check YouTube Studio for any notice.")
    if diagnosed:
        learned = update_learnings(run, _json(save_stats(ANALYTICS), {}))
        done.append(f"learnings: {learned['log']}")
    return done


def _reviews(eps: list[dict], count: int = 10) -> list[dict]:
    """The latest diagnosis of each of the newest reviewed Shorts, for the learning log."""
    out = []
    for e in sorted(eps, key=lambda e: e["id"]):
        perf = _json(e["folder"] / "performance.json", {})
        if latest := [perf[c] for c in sorted(perf, key=int) if perf[c].get("diagnosis")]:
            out.append({"short": e["id"], "title": e["title"], "verdict": latest[-1]["verdict"], **latest[-1]["diagnosis"]})
    return out[-count:]


def _sister_rules() -> str:
    """The other channel's proven rules, from its public repo: the same studio on another niche, so its rules are
    hypotheses here, not rules."""
    repo = _json(ROOT / "kit" / "channel.json", {}).get("sister_repo")
    if not repo:
        return ""
    try:
        response = requests.get(f"https://raw.githubusercontent.com/{repo}/main/strategy/LEARNINGS.md", timeout=20)
        response.raise_for_status()
        return _section(response.text, "## Rules we've proven")
    except (requests.RequestException, ValueError):
        return ""


def _video_rows(analytics: dict, eps: list[dict]) -> list[dict]:
    by_video = _by_video(eps)
    rows = []
    now = datetime.now(IST)
    for video in analytics.get("videos", []):
        e = by_video.get(video["id"])
        # The channel's two pre-rebrand animal Shorts and any unknown/private
        # uploads are retained in platform totals, not used to teach this niche.
        if e is None or e["state"] != "live":
            continue
        published = datetime.fromisoformat(video["published"].replace("Z", "+00:00"))
        a = video.get("analytics") or {}
        at10 = min(video.get("retention") or [], key=lambda p: abs(p["at"] - 0.1), default=None)
        script = _json(e["folder"] / "script.json", {}) if e else {}
        rows.append({
            "short": e["id"] if e else video["id"], "series": (e or {}).get("series") or "?",
            "hook_style": f"{script.get('hook_style', '–')}, {script.get('structure', 'story')}", "title": video["title"],
            "views": video["views"],
            "likes": video["likes"], "comments": video["comments"], "hours": round((now - published).total_seconds() / 3600),
            "engaged_share": a.get("engaged_share"), "avg_viewed": a.get("averageViewPercentage"),
            "at10": at10["watching"] if at10 else None, "subs": a.get("subscribersGained"),
            "hook": (yaml.safe_load((e["folder"] / "short.yaml").read_text(encoding="utf-8"))["beats"][0]["text"] if e else ""),
        })
    return sorted(rows, key=lambda r: r["short"])


def _median(values) -> float | None:
    values = [v for v in values if isinstance(v, (int, float))]
    return round(statistics.median(values), 3) if values else None


LEARN_SCHEMA = {
    "type": "object",
    "properties": {
        "reasons": {"type": "array", "items": {"type": "object", "properties": {
            "short": {"type": "string"}, "reason": {"type": "string"}}, "required": ["short", "reason"]}},
        "rules": {"type": "array", "items": {"type": "string"}},
        "hypotheses": {"type": "array", "items": {"type": "string"}},
        "log": {"type": "string"},
        "summary": {"type": "string"},
    },
    "required": ["reasons", "rules", "hypotheses", "log", "summary"],
}


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n## ", start + len(heading))
    return text[start: end if end != -1 else len(text)]


def update_learnings(run: Run, analytics: dict) -> dict:
    eps = episodes()
    rows = [r for r in _video_rows(analytics, eps)
            if r["hours"] >= LEARN_FROM_HOURS and r["views"] >= LEARN_MIN_VIEWS]
    if len(rows) < LEARN_MIN_SHORTS:
        message = (f"Only {len(rows)} live history Shorts have {LEARN_FROM_HOURS}+ hours and "
                   f"{LEARN_MIN_VIEWS}+ views; keep the current hypotheses pending.")
        return {"rows": rows, "medians": {}, "summary": message, "log": message}
    reviews = _reviews(eps)
    sister = _sister_rules()
    text = LEARNINGS.read_text(encoding="utf-8")
    recent = rows[-10:]
    medians = {"engaged_share": _median(r["engaged_share"] for r in recent), "avg_viewed": _median(r["avg_viewed"] for r in recent),
               "at10": _median(r["at10"] for r in recent),
               "subs_per_1000": _median((r["subs"] or 0) * 1000 / r["views"] for r in recent if r["views"]),
               "likes_per_100": _median(r["likes"] * 100 / r["views"] for r in recent if r["views"])}
    answer = llm.generate(
        "You keep the learning log of History's Last Hours, a Shorts channel of true, sourced stories of history's "
        "tragedies. From the numbers "
        "below, explain each Short's result in a few words (hook, topic, pacing, visuals, loop), judged against the "
        "channel medians. Promote a hypothesis to a rule only when 2 or more Shorts show the same effect, and cite "
        "them; drop hypotheses the data contradicts; keep the rest. Rules and hypotheses must be concrete enough "
        "for a scriptwriter to apply. log: one line on what changed today and why. summary: 2 sentences on what the "
        "numbers say for tomorrow's scripts.\n\nCurrent file:\n" + text.split("## Scoreboard")[0]
        + f"\n\nShorts with {LEARN_FROM_HOURS}+ hours of data:\n" + json.dumps(rows, indent=1) + "\n\nMedians of the last 10: " + json.dumps(medians)
        + "\n\nEach reviewed Short's diagnosis (review.py). Turn each change_next into a hypothesis unless a rule or "
        "hypothesis already covers it, and count a review as evidence for or against the ones it touches:\n"
        + (json.dumps(reviews, indent=1) if reviews else "none yet")
        + ("\n\nRules the sister channel (the same studio on another niche) has proven. Keep any that would carry "
           "over as hypotheses here until this channel's numbers show them:\n" + sister if sister else ""),
        schema=LEARN_SCHEMA, purpose="learnings",
    )
    reasons = {r["short"]: r["reason"] for r in answer["reasons"]}

    def pct(v):
        return "–" if v is None else f"{v * 100:.0f}%"

    def share(v):
        return "–" if v is None else f"{v:.1f}%"

    board = [
        "| Short | Series | Hook style | Views | Engaged share | Avg % viewed | Watching at 10% | Subs gained | Likely reason |",
        "|---|---|---|---|---|---|---|---|---|",
    ] + [
        f"| {r['short']} | {r['series']} | {r['hook_style']} | {r['views']} | {pct(r['engaged_share'])} | {share(r['avg_viewed'])} | "
        f"{pct(r['at10'])} | {r['subs'] if r['subs'] is not None else '–'} | {reasons.get(r['short'], '–')} |"
        for r in rows
    ]
    what = _section(text, "## What to beat")
    for label, key, fmt in (("Engaged share", "engaged_share", pct), ("Average percentage viewed", "avg_viewed", share),
                            ("Still watching at 10%", "at10", pct), ("Subscribers per 1,000 views", "subs_per_1000", lambda v: "–" if v is None else f"{v:.1f}"),
                            ("Likes per 100 views", "likes_per_100", lambda v: "–" if v is None else f"{v:.1f}")):
        value = medians[key]
        what = re.sub(rf"(\| {re.escape(label)}[^|]*\|[^|]*\| )([^|]*)( \|)", lambda m: m.group(1) + (fmt(value) if value is not None else "not enough data yet") + m.group(3), what, count=1)
    head = text.split("## What to beat")[0]
    rules_intro = _section(text, "## Rules we've proven").split("\n- ")[0].rstrip()
    hyp_intro = _section(text, "## Hypotheses to test").split("\n- ")[0].rstrip()
    board_intro = _section(text, "## Scoreboard").split("\n| Short")[0].rstrip()
    log_section = _section(text, "## Log").rstrip()
    new = "".join([
        head, what.rstrip(), "\n\n",
        rules_intro, "\n\n", "\n".join(f"- {r}" for r in answer["rules"]) or "- None yet.", "\n\n",
        hyp_intro, "\n\n", "\n".join(f"- {h}" for h in answer["hypotheses"]), "\n\n",
        board_intro, "\n\n", "\n".join(board), "\n\n",
        log_section, f"\n- {_now().date().isoformat()}: {answer['log']}\n",
    ])
    for heading in ("## What to beat", "## Rules we've proven", "## Hypotheses to test", "## Scoreboard", "## Log"):
        if heading not in new:
            raise RuntimeError(f"rebuilt LEARNINGS.md lost {heading}; left unchanged")
    LEARNINGS.write_text(new, encoding="utf-8")
    return {"rows": rows, "medians": medians, "summary": answer["summary"], "log": answer["log"]}


def _report_path(day: int) -> Path:
    return REPORTS / f"day-{day:03d}.md"


def _sessions_section(path: Path) -> str:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return text[text.index("## Production sessions"):].rstrip() + "\n" if "## Production sessions" in text else "## Production sessions\n"


def write_report(run: Run, analytics: dict, learned: dict | None, topics_added: list[str],
                 breakouts: list[str] | None = None) -> Path:
    today = _now().date()
    day = day_number(today)
    path = _report_path(day)
    eps = episodes()
    rows = {r["short"]: r for r in _video_rows(analytics, eps)} if analytics else {}
    since = datetime.now(IST) - timedelta(hours=24)
    went_live = [e for e in eps if e["state"] == "live" and e["record"].get("sent_at")
                 and datetime.fromisoformat(e["record"]["sent_at"]) >= since]
    queue = sorted((e for e in eps if e["state"] == "scheduled"), key=lambda e: e["record"]["due_at"])
    waiting = [e for e in eps if e["state"] == "waiting"]
    channel = analytics.get("channel", {}) if analytics else {}
    week_views = sum(d.get("views", 0) for d in (analytics.get("daily") or [])[-7:]) if analytics else None
    engaged90 = (analytics.get("last_90_days") or {}).get("engagedViews") if analytics else None
    made = [e for e in eps if e["state"] == "waiting" and e["held"].get("hosted_at")
            and datetime.fromisoformat(e["held"]["hosted_at"]) >= since]
    rejected = [p for p in (ROOT / "content" / "rejected").glob("ep*/review.json")
                if (_json(p) or {}).get("rejected_at", "") >= since.isoformat()]

    def when(iso: str) -> str:
        t = datetime.fromisoformat(iso)
        return f"{t.astimezone(ET):%a %b %d %H:%M} ET ({t.astimezone(IST):%a %H:%M} IST)"

    lines = [f"# Day {day}: {today.isoformat()}", "", "## Summary", ""]
    summary = [f"{len(went_live)} Short(s) went live in the last 24 hours; {len(queue)} are scheduled in Buffer and "
               f"{len(waiting)} wait for a slot (target {inventory(eps)['target']})."]
    if channel:
        summary.append(f"The channel has {channel.get('subscribers', 0)} subscribers and {channel.get('views', 0)} views.")
    if learned:
        summary.append(learned["summary"])
    lines += [" ".join(summary), "", "## Published", "", "| Id | Title | Published | Link | Views | Likes | Comments |", "|---|---|---|---|---|---|---|"]
    for e in went_live:
        r = rows.get(e["id"], {})
        lines.append(f"| {e['id']} | {e['title']} | {when(e['record']['sent_at'])} | <{e['record'].get('youtube_url') or ''}> | "
                     f"{r.get('views', (e['record'].get('metrics') or {}).get('views', '–'))} | {r.get('likes', '–')} | {r.get('comments', '–')} |")
    if not went_live:
        lines.append("| – | nothing went live | | | | | |")
    lines += ["", "## Totals", ""]
    if channel:
        lines.append(f"{channel.get('subscribers', 0)} subscribers, {week_views if week_views is not None else '–'} views in the last 7 days, "
                     f"{engaged90 if engaged90 is not None else '–'} engaged views in the last 90 days (the Partner Program needs 10 million).")
    else:
        lines.append("Analytics weren't available today (see the stages below).")
    lines += ["", "## Queue", "", "| Id | Publishes | Title |", "|---|---|---|"]
    lines += [f"| {e['id']} | {when(e['record']['due_at'])} | {e['title']} |" for e in queue] or ["| – | empty | |"]
    if waiting:
        lines += ["", "Waiting for a Buffer slot: " + ", ".join(f"{e['id']} ({e['title']})" for e in waiting) + "."]
    lines += ["", "## Learned", "", (learned or {}).get("log", "Not enough data yet.") if learned else "Skipped today.", ""]
    lines += ["## Better today", ""]
    for e in made:
        md = (e["folder"] / "research.md").read_text(encoding="utf-8") if (e["folder"] / "research.md").exists() else ""
        better = re.search(r"^Better than the last: (.*)$", md, re.M)
        scores = (e["held"] or {}).get("scores") or {}
        lines.append(f"- {e['id']} \"{e['title']}\" ({e['series']}): scores " + ", ".join(f"{k} {v}" for k, v in scores.items())
                     + (f". {better.group(1)}" if better else ""))
    for p in rejected:
        lines.append(f"- {p.parent.name} was rejected: {(_json(p) or {}).get('reason')}")
    if not made and not rejected:
        lines.append("- No new Shorts in the last 24 hours.")
    if breakouts:
        lines += ["", "## Breakouts", ""] + [f"- {b}" for b in breakouts]
    lines += ["", "## Decisions", ""]
    lines += [f"- Added topic: {t}" for t in topics_added] or ["- None."]
    lines += ["", "## Owner action needed", ""]
    lines += [f"- {a}" for a in dict.fromkeys(run.owner_action)] or ["- None."]
    lines += ["", _sessions_section(path)]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    if run.owner_action:
        blockers = REPORTS / "BLOCKERS.md"
        existing = blockers.read_text(encoding="utf-8") if blockers.exists() else "# Blockers\n"
        for action in dict.fromkeys(run.owner_action):
            if action not in existing:
                existing = existing.rstrip() + f"\n- {today.isoformat()}: {action}\n"
        blockers.write_text(existing, encoding="utf-8")
    return path


def weekly_review(run: Run, analytics: dict, learned: dict | None) -> Path:
    day = day_number()
    week = day // 7 + 1
    path = REPORTS / f"week-{week:02d}.md"
    rows = _video_rows(analytics, episodes()) if analytics else []
    text = llm.generate(
        f"Write the week {week} review for History's Last Hours, a Shorts channel of true, sourced stories of history's "
        "tragedies, in plain "
        "Markdown with these sections: Trend (views and subscribers), Top 3 and bottom 3 Shorts and why, What "
        "we learned, Next week's single experiment (one change, how we'll measure it). Be specific and brief. "
        "Use only these numbers:\n" + json.dumps({"rows": rows, "channel": analytics.get("channel"), "daily": analytics.get("daily"),
                                                  "learnings": learned}, indent=1, default=str),
        models=llm.STRONG, purpose="weekly review",
    )
    path.write_text(f"# Week {week} review ({_now().date().isoformat()})\n\n{text.strip()}\n", encoding="utf-8")
    return path


def daily(run: Run, state: dict | None = None, *, draft_only: bool = False) -> None:
    state = state if state is not None else _json(STATUS / "state.json", {})
    analytics, learned, added, broke = {}, None, [], []
    if not draft_only:
        from .youtube import save_stats

        with run.stage("analytics") as entry:
            path = save_stats(ANALYTICS)
            analytics = _json(path, {})
            entry["detail"] = f"{analytics.get('channel', {}).get('subscribers')} subscribers"
    if analytics:
        with run.stage("learnings") as entry:
            learned = update_learnings(run, analytics)
            entry["detail"] = learned["log"][:200]
        with run.stage("breakouts") as entry:
            broke = breakout_topics(run, state)
            entry["detail"] = "; ".join(broke)[:300] or "none"
    with run.stage("timely topics") as entry:
        timely = add_timely(run)
        added += timely
        entry["detail"] = f"{len(timely)} added"
    with run.stage("sourced accident topics") as entry:
        accidents = add_accident_topics(run)
        added += accidents
        entry["detail"] = f"{len(accidents)} added"
    # Both backlog stages spend Flash requests that drafts need to finish, so they rest while the backlog is deep.
    open_count = sum(1 for t in calendar_topics() if not t["status"])
    for name, add in (("strongest stories", add_stories), ("new topics", add_topics)):
        with run.stage(name) as entry:
            if open_count >= OPEN_TOPICS_ENOUGH:
                entry["detail"] = f"skipped: {open_count} open topics"
                continue
            found = add(run)
            added += found
            entry["detail"] = f"{len(found)} added"
    if _now().weekday() == 6 and analytics:
        with run.stage("weekly review") as entry:
            entry["detail"] = weekly_review(run, analytics, learned).name
    with run.stage("report") as entry:
        entry["detail"] = write_report(run, analytics, learned, added, broke).name


# --- the run -------------------------------------------------------------------------------------------------


def _session_note(run: Run, inv: dict) -> None:
    path = _report_path(day_number())
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Day {day_number()}: {_now().date().isoformat()}\n\n## Production sessions\n", encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    if "## Production sessions" not in text:
        text = text.rstrip() + "\n\n## Production sessions\n"
    made = ", ".join(f"{m['id']} {m['outcome']}" + (f" ({m.get('reason')})" if m.get("reason") else "") for m in run.made) or "nothing"
    if run.spawned:
        made += "; started in the cloud " + ", ".join(f"{s['id']} ({s['topic']})" for s in run.spawned)
    published = ", ".join(f"{p['id']} for {datetime.fromisoformat(p['due_at']).astimezone(ET):%b %d %H:%M} ET" for p in run.published) or "nothing"
    failed = [s["name"] for s in run.stages if not s["ok"]]
    where = f"run {os.environ['GITHUB_RUN_NUMBER']} on GitHub" if os.environ.get("GITHUB_RUN_NUMBER") else f"{_host()} run"
    note = (f"- {run.started:%H:%M} IST, {where} ({run.minutes():.0f} min): "
            f"made {made}; scheduled {published}; inventory {inv['total']} ({inv['in_buffer']} in Buffer, {inv['waiting']} waiting"
            + (f", {len(inv['remote'])} being made in the cloud" if inv["remote"] else "") + ")"
            + (f"; failed: {', '.join(failed)}" if failed else "") + (f"; {'; '.join(run.notes)}" if run.notes else "") + ".")
    path.write_text(text.rstrip() + "\n" + note + "\n", encoding="utf-8")


def _host() -> str:
    return "github-actions" if os.environ.get("GITHUB_ACTIONS") else "modal" if ON_MODAL else "local"


def _modal_cost() -> dict | None:
    if not (os.environ.get("MODAL_TOKEN_ID") or ON_MODAL):
        return None
    try:
        from .cloud import month_cost

        return month_cost()
    except Exception as err:
        log.warning("couldn't read Modal's billing: %s", err)
        return None


def _modal_credit_spent() -> bool:
    """Whether Modal has stopped running things because this month's credit is used up."""
    cost = _modal_cost()
    return bool(cost) and cost["metered"] >= MODAL_CREDIT - MODAL_PER_SHORT / 2


def write_status(run: Run, result: str) -> dict:
    eps = episodes()
    inv = inventory(eps)
    for episode in eps:
        hold = episode.get("editorial_hold")
        if not isinstance(hold, dict) or hold.get("schema") != "ytc.final-audio-speech-hold/v1":
            continue
        location = (f"Modal volume {hold['modal_volume']}:{hold['modal_path']}"
                    if hold.get("modal_volume") and hold.get("modal_path") else
                    f"content/episodes/{episode['id']}/{hold.get('media_file', episode['id'] + '.mp4')}")
        run.owner_action.append(
            f"{episode['id']} final speech review: listen to {location} against script.json and review.json "
            f"(SHA-256 {hold.get('media_sha256', 'unknown')}); repair any error and rerun final-media checks "
            "before clearing editorial_hold.json.")
    by_model: dict[str, int] = {}
    for call in llm.calls + run.worker_calls:
        by_model[call["model"]] = by_model.get(call["model"], 0) + 1
    state = _json(STATUS / "state.json", {})
    status = {
        "updated_at": _now().isoformat(timespec="seconds"),
        "day": day_number(),
        "result": result,
        "run": {
            "host": _host(),
            "id": os.environ.get("GITHUB_RUN_ID") or os.environ.get("MODAL_TASK_ID"), "number": os.environ.get("GITHUB_RUN_NUMBER"),
            "trigger": run.trigger,
            "started_at": run.started.isoformat(timespec="seconds"),
            "started_at_utc": run.started.astimezone(ZoneInfo("UTC")).isoformat(timespec="seconds"),
            "seconds": round(run.minutes() * 60),
        },
        "stages": run.stages,
        "errors": run.errors,
        "owner_action": list(dict.fromkeys(run.owner_action)),
        "notes": run.notes,
        "inventory": inv,
        "queue": [{"id": e["id"], "title": e["title"], "due_at": e["record"]["due_at"]}
                  for e in sorted((e for e in eps if e["state"] == "scheduled"), key=lambda e: e["record"]["due_at"])],
        "waiting": [{"id": e["id"], "title": e["title"], "series": e["series"], "score": _scores(e)} for e in eps if e["state"] == "waiting"],
        "made": run.made,
        "spawned": run.spawned,
        "in_cloud": [{"id": e["id"], "topic": e["remote"]["topic"], "spawned_at": e["remote"]["spawned_at"]}
                     for e in eps if e["state"] == "remote"],
        "published": run.published,
        "live": sum(1 for e in eps if e["state"] == "live"),
        "failed_posts": [{"id": e["id"], "error": e["record"].get("error")} for e in eps
                         if e["state"] == "error" and not _resending(e["record"])],
        "not_live": run.not_live,
        "llm": {"calls": len(llm.calls) + len(run.worker_calls), "by_model": by_model, "out_of_quota": sorted(llm._spent)},
        "renders": run.renders,
        "daily_done": state.get("daily_done"),
        "minutes_this_month": month_minutes() + (run.minutes() + 2 if os.environ.get("GITHUB_ACTIONS") else 0),
        "minutes_budget": minutes_budget(),
        "modal_cost": _modal_cost(),
        "modal_credit": MODAL_CREDIT,
        "capacity": run.capacity,
        "made_here": run.started_here,
        "open_topics": sum(1 for t in calendar_topics() if not t["status"]),
        "parked_topics": sum(1 for t in calendar_topics() if t["status"] == "parked"),
    }
    _write_json(STATUS / "status.json", status)
    with (STATUS / "history.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"started_at_utc": status["run"]["started_at_utc"], "host": status["run"]["host"],
                             "number": status["run"]["number"], "trigger": run.trigger, "seconds": status["run"]["seconds"],
                             "result": result, "made": [f"{m['id']}:{m['outcome']}" for m in run.made],
                             "spawned": [s["id"] for s in run.spawned], "made_here": run.started_here,
                             "published": [p["id"] for p in run.published], "inventory": inv["total"],
                             "errors": run.errors[:5], "llm_calls": len(llm.calls)}, default=str) + "\n")
    return status


def _automatic_production_paused(run: Run) -> bool:
    """A channel hold also pauses drafting until the full release policy is active."""
    from .publish import SCHEDULING_HOLD

    if not SCHEDULING_HOLD.exists():
        return False
    from .release import policy

    try:
        active = policy() is not None
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as err:
        run.notes.append(f"automatic production paused: autonomous release policy could not be validated ({err})")
        return True
    if not active:
        run.notes.append("automatic production paused: channel scheduling hold is active and autonomous release is disabled")
    return not active


def _draft_main(produce_count: int | None, daily_mode: str, trigger: str, target_episode: str | None = None) -> int:
    """Scheduled producer run with no publisher credentials or publishing calls."""
    from .cloud import PUBLISHER_ENV

    for key in PUBLISHER_ENV:
        os.environ.pop(key, None)
    os.environ["YTC_DRAFT_ONLY"] = "1"
    run = Run(trigger)
    STATUS.mkdir(parents=True, exist_ok=True)
    state = _json(STATUS / "state.json", {})
    if ON_MODAL:
        from . import cloud

        with run.stage("deploy"):
            cloud.deploy()
    if inventory()["remote"] or os.environ.get("MODAL_TOKEN_ID") or ON_MODAL:
        with run.stage("collect") as entry:
            entry["detail"] = collect(run)
    today = _now().date().isoformat()
    due = state.get("daily_done") != today and _now().hour >= DAILY_FROM_HOUR
    if daily_mode == "yes" or (daily_mode == "auto" and due):
        daily(run, state, draft_only=True)
        if all(s["ok"] for s in run.stages if s["name"] == "report"):
            state["daily_done"] = today
            _write_json(STATUS / "state.json", state)
    inv = inventory()
    # Match the main runner's editorial pause. A scheduled run cannot bypass it
    # with --produce; an explicit manual trial keeps its existing narrow exception.
    if (produce_count is None or trigger == "schedule") and _automatic_production_paused(run):
        produce_count = 0
    elif produce_count is None:
        want = inv["target"] - inv["total"] - len(inv["remote"])
        batch = max(BATCH, len(_resumable(episodes())))
        produce_count = min(batch, want) if want > 0 and (want >= BATCH or inv["making"]) else 0
        today_date = _now().date()
        timely = len(urgent([t for t in calendar_topics(today_date) if _available(t, today_date)], today_date))
        if timely:
            produce_count = max(produce_count, len(_resumable(episodes())) + timely)
        stored = datetime.fromisoformat(state["gemini_quota_until"]) if state.get("gemini_quota_until") else None
        quota_until = run.quota_until or (stored if stored and _now() < stored else None)
        if produce_count and quota_until and inv["total"] >= CURSOR_BELOW:
            run.notes.append(f"Gemini's Flash quota is spent until {quota_until:%H:%M} IST: new Shorts are drafted on the "
                             "backup models, and each waits for a Flash review after the reset")
    if produce_count > 0:
        if target_episode:
            produce(run, produce_count, cloud_only=True, episode_id=target_episode)
        else:
            produce(run, produce_count, cloud_only=True)
    run.notes.append("draft-only producer: no Buffer, Cloudinary, or Google publisher access")
    inv = inventory()
    _session_note(run, inv)
    failed = [stage for stage in run.stages if not stage["ok"]]
    result = "failed" if len(failed) >= 3 else "degraded" if failed else "ok"
    write_status(run, result)
    return 1 if result == "failed" else 0


def main(produce_count: int | None = None, publish: bool = True, daily_mode: str = "auto", trigger: str = "manual",
         *, draft_only: bool = False, target_episode: str | None = None) -> int:
    if target_episode and (not re.fullmatch(r"ep\d{3}", target_episode) or not draft_only
                           or produce_count != 1 or trigger == "schedule"):
        raise ValueError("--episode requires a draft-only manual run with --produce 1 and an epNNN id")
    if draft_only:
        return _draft_main(produce_count, daily_mode, trigger, target_episode)
    from .publish import buffer_busy, sync

    run = Run(trigger)
    STATUS.mkdir(parents=True, exist_ok=True)
    state = _json(STATUS / "state.json", {})
    if ON_MODAL:
        # The app's worker code runs the version last deployed, not this clone's.
        from . import cloud

        with run.stage("deploy"):
            cloud.deploy()
    with run.stage("sync") as entry:
        records = sync(EPISODES)
        entry["detail"] = f"{len(records)} posts"
    with run.stage("playlists") as entry:
        from .youtube import file_into_playlists

        entry["detail"] = "; ".join(file_into_playlists(EPISODES))[:300] or "nothing new"
    with run.stage("languages") as entry:
        from .youtube import fix_languages

        entry["detail"] = "; ".join(fix_languages(EPISODES))[:300] or "every live Short is in English"
    with run.stage("on youtube") as entry:
        from .youtube import check_live

        run.not_live = check_live(EPISODES)
        entry["detail"] = "; ".join(f"{p['id']}: {p['problem']}" for p in run.not_live)[:300] or "every Short sent is public"
    with run.stage("short reviews") as entry:
        entry["detail"] = "; ".join(review_shorts(run))[:600] or "no checkpoint due"
    if inventory()["remote"] or os.environ.get("MODAL_TOKEN_ID") or ON_MODAL:
        with run.stage("collect") as entry:
            entry["detail"] = collect(run)
    today = _now().date().isoformat()
    due = state.get("daily_done") != today and _now().hour >= DAILY_FROM_HOUR
    if daily_mode == "yes" or (daily_mode == "auto" and due):
        daily(run, state)
        if all(s["ok"] for s in run.stages if s["name"] in ("report",)):
            state["daily_done"] = today
            _write_json(STATUS / "state.json", state)
    can_post = False
    if publish and not buffer_busy():
        can_post = check_channel(run)
    if publish and not buffer_busy():
        if not can_post:
            run.notes.append("scheduled nothing new: Buffer can't post to the YouTube channel")
        repair_posts(run, requeue=can_post)
        preflight_posts(run)
    if can_post and not buffer_busy():
        release_anniversaries(run)
        with run.stage("publish"):
            publish_waiting(run)
    inv = inventory()
    # An explicit manual --produce trial is bounded by its requested count. Scheduled
    # runs, including one accidentally given --produce, honor the editorial pause.
    if (produce_count is None or trigger == "schedule") and _automatic_production_paused(run):
        produce_count = 0
    elif produce_count is None:
        # Shorts still being made in the cloud count as made, or every run would start another batch.
        want = inv["target"] - inv["total"] - len(inv["remote"])
        # Every half-made Short that can go on does, not just a batch: after Gemini's reset most only need the review
        # they waited for, and the day's Flash quota covers far more reviews than a batch.
        batch = max(BATCH, len(_resumable(episodes())))
        produce_count = min(batch, want) if want > 0 and (want >= BATCH or inv["making"]) else 0
        # A fresh timely topic is started even with the inventory full: it's worth most while its news is new.
        today_date = _now().date()
        if waiting_timely := len(urgent([t for t in calendar_topics(today_date) if _available(t, today_date)], today_date)):
            produce_count = max(produce_count, len(_resumable(episodes())) + waiting_timely)
        stored = datetime.fromisoformat(state["gemini_quota_until"]) if state.get("gemini_quota_until") else None
        quota_until = run.quota_until or (stored if stored and _now() < stored else None)
        if produce_count and quota_until and inv["total"] >= CURSOR_BELOW:
            run.notes.append(f"Gemini's Flash quota is spent until {quota_until:%H:%M} IST: new Shorts are drafted on the "
                             "backup models, and each waits for a Flash review after the reset")
    if produce_count > 0:
        produce(run, produce_count)
        if can_post and not buffer_busy():
            with run.stage("publish"):
                publish_waiting(run)
    if can_post and not buffer_busy():
        crosspost_scheduled(run)
    if until := buffer_busy():
        run.notes.append(f"Buffer's API limit is used up until {until.astimezone(IST):%H:%M} IST, so this run left Buffer "
                         "alone; the Shorts it already has still go out, and a later run schedules the waiting ones")
    if run.quota_until:
        state["gemini_quota_until"] = run.quota_until.isoformat(timespec="minutes")
        _write_json(STATUS / "state.json", state)
    inv = inventory()
    _session_note(run, inv)
    failed = [s for s in run.stages if not s["ok"]]
    quota = any(s.get("quota") or "Overloaded" in s.get("error", "") for s in failed)
    # Rejected Shorts are the quality gate working; a run fails when the Shorts it started all broke.
    made_nothing = run.started_here > 0 and not run.spawned and not any(m["outcome"] in ("ready", "rejected") for m in run.made)
    if not failed:
        result = "ok"
    elif (made_nothing and not quota) or len(failed) >= 3:
        result = "failed"
    else:
        result = "degraded"
    write_status(run, result)
    log.info("run %s in %.0f min: made %s, scheduled %s, inventory %s", result, run.minutes(), run.made, run.published, inv)
    return 0 if result != "failed" else 1
