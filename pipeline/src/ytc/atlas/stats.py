"""How each published Atlas Short is doing, from the channel's public feed (no key needed), kept in
analytics/atlas.json and in the scoreboard of strategy/LEARNINGS.md.

The feed lists the channel's latest 15 videos with their view and like counts. A Short is matched to its episode
through the YouTube link Buffer reported when it went out (publish.json `youtube_url`), or else by title.
"""

from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests

log = logging.getLogger(__name__)

CHANNEL_ID = "UC6e6OB3iw3yp8JnnBYxLItA"
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
      "media": "http://search.yahoo.com/mrss/"}
BOARD_HEAD = ("| Short | Topic | Published | Views | Likes | Views per hour |\n"
              "|---|---|---|---|---|---|")


def feed() -> list[dict]:
    root = ET.fromstring(requests.get(FEED, timeout=30).content)
    out = []
    for e in root.findall("a:entry", NS):
        stats = e.find("media:group/media:community/media:statistics", NS)
        rating = e.find("media:group/media:community/media:starRating", NS)
        out.append({"video_id": e.findtext("yt:videoId", namespaces=NS), "title": e.findtext("a:title", namespaces=NS),
                    "published": e.findtext("a:published", namespaces=NS),
                    "views": int(stats.get("views")) if stats is not None else None,
                    "likes": int(rating.get("count")) if rating is not None else None})
    return out


def _video_id(url: str | None) -> str | None:
    m = re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", url or "")
    return m.group(1) if m else None


def update(episodes: Path, root: Path) -> list[dict]:
    """Refresh analytics/atlas.json and the LEARNINGS.md scoreboard; returns one row per matched Short."""
    try:
        videos = feed()
    except Exception as err:
        log.warning("couldn't read the channel feed: %s", err)
        return []
    by_id = {v["video_id"]: v for v in videos}
    by_title = {v["title"].strip().lower(): v for v in videos}
    now = datetime.now(timezone.utc)
    rows = []
    for path in sorted(episodes.glob("atlas*/publish.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        video = by_id.get(_video_id(record.get("youtube_url"))) or by_title.get((record.get("title") or "").strip().lower())
        if not video:
            continue
        hours = max((now - datetime.fromisoformat(video["published"])).total_seconds() / 3600, 0.1)
        topic = ""
        spec = path.parent / "atlas.yaml"
        if spec.exists():
            m = re.search(r"^format: (\S+)", spec.read_text(encoding="utf-8"), re.M)
            topic = m.group(1) if m else ""
        rows.append({"id": path.parent.name, "title": record.get("title"), "video_id": video["video_id"],
                     "published": video["published"], "views": video["views"], "likes": video["likes"],
                     "format": topic or "map_reveal", "hours": round(hours, 1),
                     "views_per_hour": round((video["views"] or 0) / hours, 1)})
    out = root / "analytics" / "atlas.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"read_at": now.isoformat(timespec="seconds"), "shorts": rows}, indent=1) + "\n",
                   encoding="utf-8")
    _scoreboard(root / "strategy" / "LEARNINGS.md", rows)
    return rows


def _scoreboard(path: Path, rows: list[dict]) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    start = text.find("## Scoreboard")
    end = text.find("\n## ", start + 1)
    if start < 0 or end < 0:
        return
    lines = [f"| {r['id']} {r['title']} | {r['format']} | {r['published'][:16].replace('T', ' ')} UTC | {r['views']} | "
             f"{r['likes'] if r['likes'] is not None else '–'} | {r['views_per_hour']} |" for r in rows]
    body = ("## Scoreboard\n\nRefreshed by every producer run (`atlas.stats`) from the channel's public feed. Views per "
            "hour is over the Short's whole life so far, so compare Shorts of similar age.\n\n" + BOARD_HEAD + "\n"
            + "\n".join(lines) + "\n")
    path.write_text(text[:start] + body + text[end:], encoding="utf-8")
