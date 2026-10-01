"""How each live Short is doing, at 6, 24 and 72 hours after it went up (auto.review_shorts).

A checkpoint records the numbers, a verdict, and, once enough people have seen the Short, a diagnosis with one
change for the next scripts. The verdict separates a Short YouTube hasn't shown yet (a reach problem the script
can't fix) from one that was shown and lost its viewers (a script problem the next Short can).
"""

from __future__ import annotations

import json
import logging
import statistics
import urllib.request
from datetime import datetime
from pathlib import Path

import yaml

from . import llm

log = logging.getLogger(__name__)

CHECKPOINTS = (6, 24, 72)
# Past this, a Short's checkpoints are history, not news.
MAX_HOURS = 7 * 24
# Fewer views than this after 6 hours means YouTube hasn't put the Short in front of the Shorts feed.
NOT_SHOWN_VIEWS = 10
# Below this, a diagnosis would read noise.
DIAGNOSE_VIEWS = 30
MIN_PEERS = 3
FEED = "SHORTS"

DIAGNOSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "worked": {"type": "array", "items": {"type": "string"}},
        "hurt": {"type": "array", "items": {"type": "string"}},
        "change_next": {"type": "string"},
    },
    "required": ["worked", "hurt", "change_next"],
}


def due(published: datetime, now: datetime, done: set[str]) -> int | None:
    """The checkpoint to take now: the latest one passed and not yet taken, or None. A Short first seen late
    skips the checkpoints it missed rather than reporting stale ones."""
    hours = (now - published).total_seconds() / 3600
    if hours > MAX_HOURS:
        return None
    passed = [c for c in CHECKPOINTS if hours >= c]
    return passed[-1] if passed and str(passed[-1]) not in done else None


def feed_share(numbers: dict) -> float | None:
    sources = numbers.get("sources") or {}
    total = sum(sources.values())
    return round(sources.get(FEED, 0) / total, 3) if total else None


def _watching(numbers: dict, at: float) -> float | None:
    point = min(numbers.get("retention") or [], key=lambda p: abs(p["at"] - at), default=None)
    return point["watching"] if point and abs(point["at"] - at) <= 0.05 else None


def summary(numbers: dict, hours: float) -> dict:
    a = numbers.get("analytics") or {}
    views = numbers["views"]
    return {
        "hours": round(hours, 1), "views": views, "likes": numbers["likes"], "comments": numbers["comments"],
        "views_per_hour": round(views / hours, 1) if hours else None,
        "likes_per_100": round(numbers["likes"] * 100 / views, 1) if views else None,
        "avg_viewed": a.get("averageViewPercentage"), "engaged_share": round(a["engagedViews"] / a["views"], 3)
        if a.get("views") and "engagedViews" in a else None,
        "subs": a.get("subscribersGained"), "shares": a.get("shares"),
        "watching_at_5": _watching(numbers, 0.05), "watching_at_50": _watching(numbers, 0.5),
        "watching_at_end": _watching(numbers, 1.0), "feed_share": feed_share(numbers),
        "sources": numbers.get("sources") or {},
    }


def verdict(s: dict, peer_views: list[int]) -> str:
    if s["views"] < NOT_SHOWN_VIEWS:
        where = ", ".join(f"{k.lower().replace('_', ' ')} {v}" for k, v in s["sources"].items()) or "no source data yet"
        return (f"not shown yet: {s['views']} views in {s['hours']:.0f} hours ({where}). YouTube hasn't tested it in "
                "the Shorts feed, so this says nothing about the script")
    if len(peer_views) >= MIN_PEERS:
        median = statistics.median(peer_views)
        ratio = s["views"] / median if median else float("inf")
        side = "ahead of" if ratio >= 1.2 else "behind" if ratio <= 0.8 else "level with"
        return f"{side} the channel's earlier Shorts at this age: {s['views']} views against a median of {median:.0f} ({ratio:.1f}x)"
    return f"shown: {s['views']} views in {s['hours']:.0f} hours, {s['likes_per_100'] or 0:.1f} likes per 100 views"


def script_text(folder: Path) -> dict:
    spec = yaml.safe_load((folder / "short.yaml").read_text(encoding="utf-8"))
    script = json.loads((folder / "script.json").read_text(encoding="utf-8")) if (folder / "script.json").exists() else {}
    return {"title": spec.get("title"), "hook_text": spec.get("hook_text"), "series": spec.get("series"),
            "structure": script.get("structure"), "hook_style": script.get("hook_style"),
            "beats": [b.get("text") for b in spec.get("beats", [])]}


def diagnose(channel: str, short_id: str, script: dict, s: dict, peers: list[dict]) -> dict:
    return llm.generate(
        f"You review Shorts for {channel}. One of them has been live {s['hours']:.0f} hours. From its script and "
        "numbers, and the channel's earlier Shorts at the same age, say what worked and what hurt, each tied to a "
        "number (watching at 5% is the first second or two, where viewers swipe; watching at the end above 1 means "
        "rewatches; feed share is the part of views from the Shorts feed). Then give change_next: one concrete "
        "change the next scripts should make, specific enough for a scriptwriter (the hook's first words, the "
        "pacing of a beat, the ending), or keep what worked if nothing hurt. Don't blame the topic for a reach "
        "problem the numbers don't show.\n\n"
        f"Short {short_id}:\n{json.dumps(script, indent=1)}\n\nIts numbers:\n{json.dumps(s, indent=1)}\n\n"
        f"Earlier Shorts at this age:\n{json.dumps(peers, indent=1) if peers else 'none yet'}",
        schema=DIAGNOSIS_SCHEMA, purpose=f"{short_id} review",
    )


def message(channel: str, short_id: str, title: str, checkpoint: int, entry: dict) -> str:
    s = entry["numbers"]
    lines = [f"{short_id} \"{title}\" at {checkpoint} h: {s['views']} views, {s['likes']} likes, {s['comments']} comments.",
             entry["verdict"] + "."]
    if s.get("avg_viewed") is not None:
        lines.append(f"Watched {s['avg_viewed']:.0f}% on average" + (f"; {s['watching_at_5'] * 100:.0f}% still there after the first second or two"
                                                                    if s.get("watching_at_5") is not None else "") + ".")
    if d := entry.get("diagnosis"):
        if d["worked"]:
            lines.append("Worked: " + "; ".join(d["worked"]))
        if d["hurt"]:
            lines.append("Hurt: " + "; ".join(d["hurt"]))
        lines.append("Next Shorts: " + d["change_next"])
    return "\n".join(lines)


def push(topic: str, title: str, text: str) -> None:
    body = {"topic": topic, "title": title, "message": text[:3900], "priority": 3, "tags": ["bar_chart"]}
    request = urllib.request.Request("https://ntfy.sh/", data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(request, timeout=30).read()
    except Exception as err:
        log.warning("ntfy push failed: %s", err)
