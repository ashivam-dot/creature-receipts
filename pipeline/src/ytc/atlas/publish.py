"""Schedule an Atlas Short on YouTube through Buffer, with its video hosted on Cloudinary.

One post a day at SLOT in the audience's time. A post is matched by its description before a new one is made, so a
run that stopped after Buffer took a post doesn't post it twice.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, time, timedelta
from pathlib import Path

from .. import publish as pub
from .data import Dataset
from .episode import AtlasEpisode

log = logging.getLogger(__name__)

# Channel 2's Buffer YouTube channel (CHANNEL.md); an id, not a key.
BUFFER_CHANNEL = "6abcba6dea19ca0bde30177e"
os.environ.setdefault("BUFFER_YOUTUBE_CHANNEL_ID", BUFFER_CHANNEL)

SLOT = time(19, 0)
CATEGORY = "27"  # Education
TITLE_CHARS = 100
MIN_LEAD = timedelta(minutes=45)
MAP_CREDIT = "Map: Natural Earth (public domain)."


def description(ep: AtlasEpisode, ds: Dataset) -> str:
    sources = "\n".join(ep.sources) if ep.sources else ds.url
    blocks = [
        ep.description,
        f"Data: {ds.label}, {ds.source}, {ds.year} ({ds.license}).\n{sources}\n{MAP_CREDIT}",
        "Script written with AI and checked number by number against the data. Narrated with a synthetic voice.",
        " ".join(ep.hashtags[:3]),
    ]
    return pub._youtube_text("\n\n".join(b for b in blocks if b))


def next_slot(taken: list[datetime], now: datetime | None = None) -> datetime:
    """The first SLOT on a day with no Atlas post, at least MIN_LEAD from now."""
    now = (now or datetime.now(pub.AUDIENCE_TZ)).astimezone(pub.AUDIENCE_TZ)
    days = {t.astimezone(pub.AUDIENCE_TZ).date() for t in taken}
    day = now.date()
    while True:
        when = datetime.combine(day, SLOT, pub.AUDIENCE_TZ)
        if when >= now + MIN_LEAD and day not in days:
            return when
        day += timedelta(days=1)


def schedule(ep: AtlasEpisode, folder: Path, ds: Dataset, video: Path) -> dict:
    record_path = folder / "publish.json"
    if record_path.exists():
        return json.loads(record_path.read_text(encoding="utf-8"))
    text = description(ep, ds)
    title = pub._youtube_text(ep.title)[:TITLE_CHARS]
    recent = pub.posts(since=datetime.now(pub.AUDIENCE_TZ) - timedelta(days=30))
    lead = text.split("\n\n", 1)[0]
    twin = next((p for p in recent if (p.get("text") or "").split("\n\n", 1)[0] == lead
                 and p["status"] not in ("error", "draft")), None)
    public_id = f"atlasinnumbers/{ep.id}"
    if twin:
        log.warning("%s is already Buffer post %s; recording it", ep.id, twin["id"])
        return _record(record_path, ep, twin, public_id, None)
    taken = [datetime.fromisoformat(p["dueAt"]) for p in recent
             if p.get("dueAt") and p["status"] not in ("error", "draft")]
    when = next_slot(taken)
    media_url = pub.host_video(video, public_id)
    pub.fetch_video(media_url)
    mutation = """
    mutation Create($input: CreatePostInput!) {
      createPost(input: $input) {
        __typename
        ... on PostActionSuccess { post { id status dueAt } }
        ... on MutationError { message }
      }
    }"""
    payload = {
        "channelId": pub.youtube_channel_id(),
        "text": text,
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": when.isoformat(),
        "assets": [{"video": {"url": media_url}}],
        "metadata": {"youtube": {"title": title, "categoryId": CATEGORY, "privacy": "public", "madeForKids": False,
                                 "notifySubscribers": True, "isAiGenerated": True, "embeddable": True}},
    }
    result = pub._buffer(mutation, {"input": payload})["createPost"]
    if result["__typename"] != "PostActionSuccess":
        pub.unhost_video(public_id)
        raise RuntimeError(f"Buffer rejected {ep.id}: {result.get('message')}")
    log.info("scheduled %s for %s", ep.id, when.isoformat())
    return _record(record_path, ep, result["post"] | {"dueAt": when.isoformat()}, public_id, media_url)


def _record(path: Path, ep: AtlasEpisode, post: dict, public_id: str, media_url: str | None) -> dict:
    record = {"id": ep.id, "title": ep.title, "buffer_post_id": post["id"], "due_at": post.get("dueAt"),
              "status": post["status"], "media_public_id": public_id, "media_url": media_url,
              "youtube_url": post.get("externalLink")}
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record
