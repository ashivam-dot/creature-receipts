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
import re
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from .. import publish as pub
from .data import Dataset
from .episode import AtlasEpisode

log = logging.getLogger(__name__)

# Channel 2's Buffer YouTube channel (CHANNEL.md); an id, not a key.
BUFFER_CHANNEL = "6abcba6dea19ca0bde30177e"
os.environ.setdefault("BUFFER_YOUTUBE_CHANNEL_ID", BUFFER_CHANNEL)

SLOTS = (time(12, 0), time(16, 0), time(19, 0))  # lunch, afternoon and evening ET; three a day (owner, 2026-10-27)
CATEGORY = "27"  # Education
TITLE_CHARS = 100
MIN_LEAD = timedelta(minutes=30)
# A slot with a post this close to it is taken.
SLOT_GAP = timedelta(minutes=60)
MAP_CREDIT = "Globe: NASA Blue Marble and Black Marble (public domain). Borders: Natural Earth (public domain)."
# How every Short is made, on every description (revenue-push plan, cross-channel: an editorial-process line beside
# the dataset citation). Each claim is one the code really enforces: writer.number_problems and
# quality.entity_value_errors check every number and country, quality.review is a second model's read against the
# official definition, and quality.media checks the encoded narration against the script.
EDITORIAL = ("How this Short is made: one published dataset (named above), the latest value for each place (not a "
             "trend). The script is written with AI; every number and country in it is checked in code against the "
             "data above, a second AI review reads it against the dataset's definition, and the finished narration "
             "is checked against the script before it is published. Narrated with a synthetic voice. Corrections "
             "welcome in the comments.")
# The producer's committed episodes. The publisher schedules from a temporary folder holding only the video, so the
# credits are read from here when that folder has none.
EPISODES = Path(__file__).resolve().parents[4] / "content" / "atlas"


def photo_credits(folder: Path | None, episode_id: str = "") -> str:
    """Every photo the Short shows, with its author, licence and Commons page (credits.json, written by the
    renderer); empty for a Short without photos."""
    path = folder / "credits.json" if folder else None
    if (not path or not path.exists()) and episode_id:
        path = EPISODES / episode_id / "credits.json"
    if not path or not path.exists():
        return ""
    rows = json.loads(path.read_text(encoding="utf-8"))
    lines = [f"- {r['place']}: {r['author']}, {r['license']}, {r['page']}" for r in rows]
    return "Photos from Wikimedia Commons:\n" + "\n".join(lines) if lines else ""


def _indicator(ds: Dataset) -> str:
    """The World Bank indicator code, so anyone can look the series up ("Indicator SH.MED.PHYS.ZS."); nothing for
    an Our World in Data slug, whose URL already names it."""
    code = ds.indicator or ""
    return f" Indicator {code}." if re.fullmatch(r"[A-Z][A-Z0-9]*(?:\.[A-Z0-9]+)+", code) else ""


def title_problems(ep: AtlasEpisode, ds: Dataset) -> list[str]:
    """The last title check before Buffer (writer.episode_title_lint); the publisher calls it too."""
    from .writer import episode_title_lint
    return episode_title_lint(ep, ds)


def search_line(ds: Dataset) -> str:
    """The words people search, high in the description: "Countries and territories ranked by <label> (<years>):
    highest <place>, lowest <place>." Names only, no values: every number lives in the checked script."""
    from . import geo

    world = geo.world()
    vals = {k: v for k, v in ds.values.items() if k in world}
    if not vals or not ds.label:
        return ""
    top, bottom = (ds.names.get(k, world[k].name) for k in (max(vals, key=vals.get), min(vals, key=vals.get)))
    label = ds.label if re.match(r"[A-Z]{2}", ds.label) else ds.label[:1].lower() + ds.label[1:]
    return f"Countries and territories ranked by {label} ({ds.year_label}): highest {top}, lowest {bottom}."


def description(ep: AtlasEpisode, ds: Dataset, folder: Path | None = None) -> str:
    sources = "\n".join(ep.sources) if ep.sources else ds.url
    blocks = [
        ep.description,
        search_line(ds),
        f"Data: {ds.label}, {ds.source}, {ds.year_label} ({ds.license}).{_indicator(ds)}\n{sources}\n{MAP_CREDIT}",
        photo_credits(folder, ep.id),
        EDITORIAL,
        f"Atlas episode: {ep.id}",
        " ".join(ep.hashtags[:3]),
    ]
    return pub._youtube_text("\n\n".join(b for b in blocks if b))


# A Short parked this long goes out next whatever its score, so a low score can't keep one waiting forever.
STALE = timedelta(hours=72)


def order(folders: list[Path], last: Path | None = None, now: datetime | None = None) -> list[Path]:
    """Waiting Shorts in the order the publisher schedules them: any parked over STALE first (oldest first), then
    the highest ready.json "score" (pipeline.score), never two of one family in a row while another family waits;
    the folder name breaks ties, so Shorts parked before scores existed keep their old order. `last` is the folder
    of the post scheduled before them, whose family the first must not repeat."""
    now = now or datetime.now(pub.AUDIENCE_TZ)

    def ready(folder: Path | None) -> dict:
        try:
            return json.loads((folder / "ready.json").read_text(encoding="utf-8")) if folder else {}
        except (OSError, ValueError):
            return {}

    def age(record: dict) -> timedelta:
        try:
            return now - datetime.fromisoformat(record["rendered_at"])
        except (KeyError, TypeError, ValueError):
            return timedelta(0)

    records = {f: ready(f) for f in folders}
    left = sorted(folders, key=lambda f: (-(records[f].get("score") or 0), f.name))
    previous, look, out = ready(last).get("family"), ready(last).get("look"), []
    while left:
        stale = sorted((f for f in left if age(records[f]) > STALE), key=lambda f: -age(records[f]))
        other = [f for f in left if not previous or records[f].get("family") != previous]
        # Nor two of one look in a row (cinema/looks.py), while another look waits.
        fresh = [f for f in other if not look or records[f].get("look") != look]
        chosen = (stale or fresh or other or left)[0]
        out.append(chosen)
        left.remove(chosen)
        previous, look = records[chosen].get("family"), records[chosen].get("look")
    return out


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
    if bad := title_problems(ep, ds):
        raise ValueError(f"{ep.id}: title held, {'; '.join(bad)}")
    text = description(ep, ds, folder)
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


# Uploading, listing and unscheduling (videos.update, which youtube.upload doesn't allow).
SCOPE = "https://www.googleapis.com/auth/youtube"
# The sign-in for @atlasinnumbers: JSON with client_id, client_secret and refresh_token, only in the Modal secret
# atlas-youtube that cloud.atlas_upload alone mounts.
OAUTH_ENV = "ATLAS_YOUTUBE_OAUTH"
CHANNEL_ID = "UC6e6OB3iw3yp8JnnBYxLItA"


def youtube_client():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    info = json.loads(os.environ[OAUTH_ENV])
    creds = Credentials(None, refresh_token=info["refresh_token"], client_id=info["client_id"],
                        client_secret=info["client_secret"], token_uri="https://oauth2.googleapis.com/token",
                        scopes=[SCOPE])
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def recent_uploads(yt, limit: int = 50) -> list[dict]:
    """The channel's latest uploads (id, title, description, status), newest first; 2-3 quota units."""
    me = yt.channels().list(part="id,contentDetails", mine=True).execute()["items"][0]
    if me["id"] != CHANNEL_ID:
        raise RuntimeError("the YouTube sign-in is not @atlasinnumbers")
    uploads = me["contentDetails"]["relatedPlaylists"]["uploads"]
    items = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=limit).execute()["items"]
    ids = [i["contentDetails"]["videoId"] for i in items]
    if not ids:
        return []
    return yt.videos().list(part="snippet,status", id=",".join(ids)).execute()["items"]


def upload(ep: AtlasEpisode, folder: Path, ds: Dataset, video: Path, taken: list[datetime], yt=None,
           existing: list[dict] | None = None) -> dict:
    """Upload a Short straight to YouTube, private until its slot (publishAt). A video already carrying this
    episode's line is recorded instead of uploaded again."""
    record_path = folder / "publish.json"
    if record_path.exists():
        return json.loads(record_path.read_text(encoding="utf-8"))
    if bad := title_problems(ep, ds):
        raise ValueError(f"{ep.id}: title held, {'; '.join(bad)}")
    yt = yt or youtube_client()
    text = description(ep, ds, folder)
    title = pub._youtube_text(ep.title)[:TITLE_CHARS]
    lead = f"Atlas episode: {ep.id}"
    existing = recent_uploads(yt) if existing is None else existing
    twin = next((v for v in existing if lead in v["snippet"].get("description", "").splitlines()), None)
    if twin:
        when = twin["status"].get("publishAt")
        if not when and twin["status"].get("privacyStatus") != "public":
            raise RuntimeError(f"{ep.id} is already YouTube video {twin['id']}, private with no schedule: "
                               "publish or delete it in Studio")
        log.warning("%s is already YouTube video %s; recording it", ep.id, twin["id"])
        return _direct_record(record_path, ep, twin["id"], when or twin["snippet"].get("publishedAt"), uploaded=False)
    # A run that uploaded and then lost its record still holds its slot on the channel.
    taken = taken + [datetime.fromisoformat(v["status"]["publishAt"].replace("Z", "+00:00"))
                     for v in existing if v["status"].get("publishAt")]
    when = next_slot(taken)
    from googleapiclient.http import MediaFileUpload

    body = {"snippet": {"title": title, "description": text, "categoryId": CATEGORY, "defaultLanguage": "en",
                        "defaultAudioLanguage": "en", "tags": youtube_tags(ep)},
            "status": {"privacyStatus": "private", "publishAt": when.astimezone(timezone.utc).isoformat().replace(
                "+00:00", "Z"), "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True,
                "embeddable": True, "license": "youtube"}}
    request = yt.videos().insert(part="snippet,status", body=body, notifySubscribers=True,
                                 media_body=MediaFileUpload(str(video), mimetype="video/mp4", resumable=True,
                                                            chunksize=8 * 1024 * 1024))
    response = None
    while response is None:
        _, response = request.next_chunk()
    log.info("uploaded %s as %s for %s", ep.id, response["id"], when.isoformat())
    return _direct_record(record_path, ep, response["id"], when.isoformat())


def youtube_tags(ep: AtlasEpisode, limit: int = 450) -> list[str]:
    """The episode's tags then its hashtags' words, within YouTube's 500 characters (a tag with a space counts its
    quotes)."""
    out, used = [], 0
    for tag in dict.fromkeys([*ep.tags, *(h.lstrip("#") for h in ep.hashtags), "atlas in numbers"]):
        cost = len(tag) + (2 if " " in tag else 0) + 1
        if tag and used + cost <= limit:
            out.append(tag)
            used += cost
    return out


def withdraw(video_ids: list[str], yt=None) -> list[str]:
    """Unschedule direct uploads of @atlasinnumbers: still private, no publishAt (an update that omits publishAt
    keeps the schedule). Videos already public are left alone. Returns the ids withdrawn."""
    yt = yt or youtube_client()
    done = []
    for i in range(0, len(video_ids), 50):
        for v in yt.videos().list(part="status,snippet", id=",".join(video_ids[i:i + 50])).execute()["items"]:
            if v["snippet"].get("channelId") != CHANNEL_ID or v["status"].get("privacyStatus") == "public":
                continue
            status = {k: v["status"][k] for k in ("embeddable", "license", "publicStatsViewable",
                                                  "selfDeclaredMadeForKids", "containsSyntheticMedia")
                      if k in v["status"]}
            yt.videos().update(part="status", body={"id": v["id"], "status": status | {
                "privacyStatus": "private", "publishAt": None}}).execute()
            done.append(v["id"])
    return done


def _direct_record(path: Path, ep: AtlasEpisode, video_id: str, when: str, uploaded: bool = True) -> dict:
    record = {"id": ep.id, "title": ep.title, "route": "youtube", "youtube_video_id": video_id, "due_at": when,
              "status": "scheduled", "youtube_url": f"https://www.youtube.com/shorts/{video_id}"}
    if uploaded:  # counts against the publisher's daily uploads
        record["uploaded_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


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
    title, text = pub._youtube_text(ep.title)[:TITLE_CHARS], description(ep, ds, folder)
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
