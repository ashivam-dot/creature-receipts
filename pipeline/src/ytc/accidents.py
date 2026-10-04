"""A small, checked accident research queue, independent of Wikipedia readership.

The pool contains leads, not approved scripts. Each lead has an original report or
technical study and a separately published account. Source pages are read again
when research starts; an unreachable page makes that draft nonviable.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from urllib.parse import urlsplit

from .research import site
from .studio import ROOT

log = logging.getLogger(__name__)

CANDIDATES = ROOT / "strategy" / "ACCIDENT-CANDIDATES.json"
SELECTION_POLICY = ROOT / "status" / "accident_selection_policy.json"
SERIES = {"The Last Hours", "Warnings Ignored"}
ROLES = {"primary", "independent"}
DISALLOWED_SITES = {"wikipedia.org", "wikimedia.org", "wikidata.org"}


def _words(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _mentions(text: str, alias: str) -> bool:
    return f" {_words(alias)} " in f" {_words(text)} "


def _valid(row: dict, today: date) -> bool:
    if not isinstance(row, dict) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(row.get("id", ""))):
        return False
    if type(row.get("year")) is not int or row["year"] > today.year - 75:
        return False
    if type(row.get("order")) is not int or row["order"] < 1 or row.get("series") not in SERIES:
        return False
    topic = row.get("topic")
    aliases = row.get("aliases")
    if not isinstance(topic, str) or not topic.strip() or "\n" in topic or "|" in topic:
        return False
    if not isinstance(aliases, list) or not aliases or not all(isinstance(a, str) and _words(a) for a in aliases):
        return False
    if not any(_mentions(topic, alias) for alias in aliases):
        return False
    try:
        checked = date.fromisoformat(row["checked_at"])
    except (KeyError, TypeError, ValueError):
        return False
    if checked > today:
        return False
    if not isinstance(row.get("cautions"), list) or not all(isinstance(c, str) and c.strip() for c in row["cautions"]):
        return False
    sources = row.get("sources")
    if not isinstance(sources, list) or len(sources) < 2:
        return False
    seen_roles, seen_sites = set(), set()
    for source in sources:
        if not isinstance(source, dict) or source.get("role") not in ROLES or not source.get("institution"):
            return False
        url = source.get("url")
        if not isinstance(url, str):
            return False
        try:
            parsed = urlsplit(url)
        except ValueError:
            return False
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return False
        host = site(url)
        if host in DISALLOWED_SITES or host in seen_sites:
            return False
        focus = source.get("focus", [])
        if not isinstance(focus, list) or not all(isinstance(f, str) and f.strip() for f in focus):
            return False
        seen_roles.add(source["role"])
        seen_sites.add(host)
    return seen_roles == ROLES


def load(today: date | None = None) -> list[dict]:
    """Only well-formed leads with two distinct, named source origins are eligible."""
    today = today or date.today()
    try:
        rows = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        log.warning("accident candidate pool unavailable: %s", err)
        return []
    if not isinstance(rows, list):
        log.warning("accident candidate pool must be a list")
        return []
    out, ids, topics = [], set(), set()
    for row in rows:
        if not _valid(row, today):
            label = row.get("id") if isinstance(row, dict) else row
            log.warning("skipping accident candidate with invalid source metadata: %r", label)
            continue
        if row["id"] in ids or row["topic"] in topics:
            log.warning("skipping duplicate accident candidate: %s", row["id"])
            continue
        out.append(row)
        ids.add(row["id"])
        topics.add(row["topic"])
    return sorted(out, key=lambda row: (row["order"], row["id"]))


def next_candidate(known_topics: list[str], used_ids: set[str], today: date | None = None) -> dict | None:
    """Pick one unused subject, even if an existing topic tells a different angle."""
    for row in load(today):
        if row["id"] not in used_ids and not any(_mentions(topic, alias) for topic in known_topics for alias in row["aliases"]):
            return row
    return None


def by_topic(topic: str, today: date | None = None) -> dict | None:
    """Find only an exact pool topic when binding sources to an episode."""
    return next((row for row in load(today) if row["topic"] == topic), None)


def selection_allowed(candidate_id: str) -> bool:
    """Keep candidate leads out of producer jobs until separately approved."""
    try:
        value = json.loads(SELECTION_POLICY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return (isinstance(value, dict) and value.get("version") == 1 and
            value.get("enabled") is True and
            isinstance(value.get("approved_candidate_ids"), list) and
            candidate_id in value["approved_candidate_ids"])
