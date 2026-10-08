"""Schedule an Atlas Short on YouTube through Buffer, with its video hosted on Cloudinary.

Posts go out at SLOTS in the audience's time. A post is matched by its description before a new one is made, so a
run that stopped after Buffer took a post doesn't post it twice.

The keys live only with the publisher (the control repo's history-publisher environment, `control/atlas.py`); the
producer on Modal renders and parks each Short without them.
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

SLOTS = (time(12, 0), time(16, 0), time(19, 0))
CATEGORY = "27"  # Education
TITLE_CHARS = 100
MIN_LEAD = timedelta(minutes=30)
# A slot with a post this close to it is taken.
SLOT_GAP = timedelta(minutes=60)
MAP_CREDIT = "Map: Natural Earth (public domain)."


def description(ep: AtlasEpisode, ds: Dataset) -> str:
    sources = "\n".join(ep.sources) if ep.sources else ds.url
    blocks = [
        ep.description,
        f"Data: {ds.label}, {ds.source}, {ds.year_label} ({ds.license}).\n{sources}\n{MAP_CREDIT}",
        "Script written with AI and checked number by number against the data. Narrated with a synthetic voice.",
        f"Atlas episode: {ep.id}",
        " ".join(ep.hashtags[:3]),
    ]
    return pub._youtube_text("\n\n".join(b for b in blocks if b))


def next_slot(taken: list[datetime], now: datetime | None = None) -> datetime:
    """The first of SLOTS with no post within SLOT_GAP of it, at least MIN_LEAD from now."""
    now = (now or datetime.now(pub.AUDIENCE_TZ)).astimezone(pub.AUDIENCE_TZ)
    day = now.date()
    while True:
        for slot in SLOTS:
            when = datetime.combine(day, slot, pub.AUDIENCE_TZ)
            if when >= now + MIN_LEAD and all(abs(when - t) >= SLOT_GAP for t in taken):
                return when
        day += timedelta(days=1)


def schedule(ep: AtlasEpisode, folder: Path, ds: Dataset, video: Path) -> dict:
    record_path = folder / "publish.json"
    if record_path.exists():
        return json.loads(record_path.read_text(encoding="utf-8"))
    text = description(ep, ds)
    title = pub._youtube_text(ep.title)[:TITLE_CHARS]
    recent = pub.posts(since=datetime.now(pub.AUDIENCE_TZ) - timedelta(days=30))
    lead = f"Atlas episode: {ep.id}"
    twin = next((p for p in recent if lead in (p.get("text") or "").splitlines()
                 and p["status"] not in ("error", "draft")), None)
    public_id = f"atlasinnumbers/{ep.id}"
    if twin:
        log.warning("%s is already Buffer post %s; recording it", ep.id, twin["id"])
        return _record(record_path, ep, twin, public_id, None)
    taken = [datetime.fromisoformat(p["dueAt"]) for p in recent
             if p.get("dueAt") and p["status"] not in ("error", "draft")]
    when = next_slot(taken)
    media_url = pub.host_video(video, public_id)
    from .receipt import digest
    pub.fetch_video(media_url, expected_sha256=digest(video))
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


def replace_queued(ep: AtlasEpisode, folder: Path, ds: Dataset, video: Path, record: dict) -> dict:
    """Replace an exact queued legacy post only after checking its identity, slot and accepted media.

    The new asset has a content-specific public ID. Repeating an interrupted edit recovers the same post.
    """
    from .receipt import digest
    post_id = record["buffer_post_id"]
    before = pub.post(post_id)
    if before is None or before["status"] not in ("scheduled", "pending"):
        raise RuntimeError("legacy replacement requires an existing queued post")
    due = datetime.fromisoformat(before["dueAt"])
    if due != datetime.fromisoformat(record["due_at"]):
        raise RuntimeError("legacy post's scheduled slot changed")
    title, text = pub._youtube_text(ep.title)[:TITLE_CHARS], description(ep, ds)
    sha = digest(video)
    public_id = f"atlasinnumbers/{ep.id}-qa-{sha[:12]}"
    existing_url = before.get("video") or ""
    recovered = (existing_url.startswith("https://res.cloudinary.com/") and
                 existing_url.endswith(f"/{public_id}.mp4") and
                 before.get("title") == title and before.get("text") == text)
    media_url = existing_url if recovered else pub.host_video(video, public_id)
    pub.fetch_video(media_url, expected_sha256=sha)
    already = before.get("video") == media_url and before.get("title") == title and before.get("text") == text
    if not already:
        if due < datetime.now(pub.AUDIENCE_TZ) + MIN_LEAD:
            raise RuntimeError("legacy post is too close to publication to edit safely")
        if before.get("title") != record["title"] or before.get("video") != record.get("media_url"):
            raise RuntimeError("legacy post's title/media identity changed")
        mutation = """mutation Edit($input: EditPostInput!) {
          editPost(input: $input) { __typename ... on MutationError { message } }
        }"""
        payload = {"id": post_id, "assets": [{"video": {"url": media_url}}], "text": text,
                   "metadata": {"youtube": {"title": title, "categoryId": CATEGORY, "privacy": "public",
                       "madeForKids": False, "notifySubscribers": True, "isAiGenerated": True, "embeddable": True}}}
        result = pub._buffer(mutation, {"input": payload})["editPost"]
        if result["__typename"] != "PostActionSuccess":
            raise RuntimeError(f"Buffer rejected checked replacement: {result.get('message')}")
    after = pub.post(post_id)
    if (after is None or after.get("video") != media_url or after.get("title") != title or
            after.get("text") != text or after.get("privacy") != "public" or
            datetime.fromisoformat(after["dueAt"]) != due):
        raise RuntimeError("checked replacement could not be confirmed at its original slot")
    return _record(folder / "publish.json", ep, after, public_id, media_url)
