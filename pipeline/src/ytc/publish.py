"""Schedule rendered Shorts on YouTube through Buffer, with the video file hosted on Cloudinary.

Buffer publishes through its own audited YouTube API client, so scheduled Shorts go public. Buffer takes
media only as a public URL and fetches it at publish time, so the file stays on Cloudinary until the post
has gone out.
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import os
import re
import shutil
import tempfile
import time
import urllib.parse
from datetime import datetime, time as clock, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from . import ff
from .spec import ShortSpec

log = logging.getLogger(__name__)

BUFFER_API = "https://api.buffer.com"
SCHEDULING_HOLD = Path(__file__).resolve().parents[3] / "status" / "scheduling_hold.json"
AUDIENCE_TZ = ZoneInfo("America/New_York")
# Best first: a day that posts fewer Shorts than there are slots keeps the first ones (auto.slots_per_day). Buffer's
# 2026 data (1.8M videos) puts Shorts' peak at 6-11 p.m. and the weekday 12-5 p.m. stretch lowest, so the first two
# are evening slots 2.5 hours apart (research/growth-playbook-2026.md, upgrade 5).
SLOTS = (clock(19, 0), clock(21, 30), clock(12, 30), clock(16, 30), clock(22, 30))
BUFFER_QUEUE_LIMIT = 10
# A live Short's copy is on YouTube, and a remake fetches the same images again.
BULKY = ("{id}.mp4", "work/assets", "work/frames", "work/narration.wav", "work/contact.jpg")
# YouTube refuses an upload whose title has < or > or runs past 100 characters, or whose description has < or >
# or runs past 5,000 bytes, and Buffer only finds out when the post goes out.
TITLE_CHARS, DESCRIPTION_BYTES = 100, 5000
# Buffer doesn't retry a post it failed. cloud.slot_watch sends one again this long after each of its checks, as long
# as the post's due time (which each try moves) is within RESEND_WINDOW; older failures wait for a studio run.
RESEND_DELAY = timedelta(minutes=5)
RESEND_WINDOW = timedelta(hours=1)
# Optional native cross-posts of each Short (auto.crosspost_scheduled), off unless the channel's Buffer id is set.
# Buffer's free plan has 3 channels, each with its own queue of BUFFER_QUEUE_LIMIT.
CROSSPOST_ENV = {"tiktok": "BUFFER_TIKTOK_CHANNEL_ID", "instagram": "BUFFER_INSTAGRAM_CHANNEL_ID"}
# Both TikTok and Instagram cut captions at 2,200 characters; Instagram allows 30 hashtags, TikTok's discovery
# works best with a few relevant ones.
CAPTION_CHARS = 2200
CAPTION_HASHTAGS = 5
MEDIA_BINDING_FIELDS = ("media_sha256", "spec_sha256", "manifest_sha256")


class NotFound(RuntimeError):
    pass


def _env(name: str) -> str:
    if value := os.environ.get(name):
        return value
    raise RuntimeError(f"{name} is not set in pipeline/.env (see kit/ACCOUNTS.md)")


def _require_scheduling_open(spec_path: Path | None = None, *, exact_media_release: bool = False) -> None:
    """Apply editorial locks before any Buffer mutation that creates a due post.

    A channel hold may authorize one direct YouTube schedule by exact local media binding. The
    automatic scheduler, crossposts, queued edits, and resends never use this exception.
    """
    if exact_media_release and not SCHEDULING_HOLD.exists():
        raise RuntimeError("Exact-media release requires the active channel scheduling hold")
    if spec_path is not None and (spec_path.parent / "editorial_hold.json").exists():
        raise RuntimeError(f"{spec_path.parent.name} is on editorial hold; remove editorial_hold.json after repair and review")
    if SCHEDULING_HOLD.exists():
        blocked = "New scheduling is on editorial hold; remove status/scheduling_hold.json only after review"
        if not exact_media_release or spec_path is None:
            raise RuntimeError(blocked)
        try:
            hold = json.loads(SCHEDULING_HOLD.read_text(encoding="utf-8"))
            allowed = hold.get("release_allowlist") if isinstance(hold, dict) else None
            if not isinstance(allowed, dict):
                raise ValueError("missing release allowlist")
            expiry = datetime.fromisoformat(allowed["expires_at_utc"])
            if expiry.tzinfo is None or expiry.utcoffset() != timedelta(0) or datetime.now(timezone.utc) >= expiry:
                raise ValueError("release allowlist expired or is not UTC")
            episode_id = spec_path.parent.name
            if allowed.get("episode_id") != episode_id or ShortSpec.load(spec_path).id != episode_id:
                raise ValueError("episode ID mismatch")
            manifest = json.loads((spec_path.parent / "work" / "manifest.json").read_text(encoding="utf-8"))
            if manifest.get("id") != episode_id:
                raise ValueError("manifest ID mismatch")
            if not (spec_path.parent / f"{episode_id}.mp4").is_file():
                raise ValueError("reviewed media file is missing")
            binding = media_binding(spec_path, episode_id)
            if any(not re.fullmatch(r"[0-9a-f]{64}", str(allowed.get(field, "")))
                   or allowed[field] != binding[field] for field in MEDIA_BINDING_FIELDS):
                raise ValueError("media binding mismatch")
        except (KeyError, ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(blocked) from exc


class BufferBusy(RuntimeError):
    """Buffer refused a request for its API limit: 100 requests in 15 minutes and 250 a day, for everything that
    uses the key (the studio's runs and both monitors)."""

    def __init__(self, until: datetime):
        super().__init__(f"Buffer's API limit is used up until {until:%H:%M} UTC")
        self.until = until


_busy_until: datetime | None = None


def buffer_busy() -> datetime | None:
    """When Buffer takes requests again, once it has refused one from this process for its limit."""
    return _busy_until if _busy_until and datetime.now(timezone.utc) < _busy_until else None


def _buffer(query: str, variables: dict | None = None) -> dict:
    global _busy_until
    if until := buffer_busy():
        raise BufferBusy(until)
    for attempt in range(2):
        response = requests.post(
            BUFFER_API,
            json={"query": query, "variables": variables or {}},
            headers={"Authorization": f"Bearer {_env('BUFFER_API_KEY')}"},
            timeout=60,
        )
        if response.status_code != 429:
            break
        retry_after = response.headers.get("Retry-After", "")
        wait = int(retry_after) if retry_after.isdigit() else 900
        if attempt or wait > 90:
            _busy_until = datetime.now(timezone.utc) + timedelta(seconds=wait)
            raise BufferBusy(_busy_until)
        time.sleep(wait)
    response.raise_for_status()
    body = response.json()
    if errors := body.get("errors"):
        missing = all((e.get("extensions") or {}).get("code") == "NOT_FOUND" for e in errors)
        raise (NotFound if missing else RuntimeError)(f"Buffer API error: {errors}")
    return body["data"]


@functools.cache
def organization_id() -> str:
    if org := os.environ.get("BUFFER_ORG_ID"):
        return org
    orgs = _buffer("query { account { organizations { id name } } }")["account"]["organizations"]
    return orgs[0]["id"]


def channels() -> list[dict]:
    query = """
    query Channels($input: ChannelsInput!) {
      channels(input: $input) { id name displayName service isDisconnected isLocked isQueuePaused timezone }
    }"""
    return _buffer(query, {"input": {"organizationId": organization_id()}})["channels"]


def youtube_channel_id() -> str:
    if channel := os.environ.get("BUFFER_YOUTUBE_CHANNEL_ID"):
        return channel
    for channel in channels():
        if channel["service"] == "youtube" and not channel["isDisconnected"]:
            return channel["id"]
    raise RuntimeError("No connected YouTube channel in Buffer")


def channel() -> dict:
    """The YouTube channel as Buffer has it. Disconnected, locked, or a paused queue each stop every post."""
    found = channels()
    wanted = os.environ.get("BUFFER_YOUTUBE_CHANNEL_ID")
    return next((c for c in found if c["id"] == wanted), None) or next(c for c in found if c["service"] == "youtube")


def posts(since: datetime | None = None, channel_id: str | None = None) -> list[dict]:
    query = """
    query Posts($input: PostsInput!, $after: String) {
      posts(input: $input, first: 50, after: $after) {
        edges {
          node {
            id status dueAt sentAt externalLink text channelService error { message }
            metrics { type value } metricsUpdatedAt
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }"""
    filters: dict = {"channelIds": [channel_id or youtube_channel_id()]}
    if since:
        # Buffer returns no posts for a startDate without an endDate.
        filters["startDate"] = since.isoformat()
        filters["endDate"] = (datetime.now(AUDIENCE_TZ) + timedelta(days=365)).isoformat()
    variables = {"input": {"organizationId": organization_id(), "filter": filters}, "after": None}
    found = []
    while True:
        page = _buffer(query, variables)["posts"]
        found += [edge["node"] for edge in page["edges"]]
        if not page["pageInfo"]["hasNextPage"]:
            return found
        variables["after"] = page["pageInfo"]["endCursor"]


def _cloudinary() -> tuple[str, str, str]:
    url = urllib.parse.urlparse(_env("CLOUDINARY_URL"))
    return url.hostname, urllib.parse.unquote(url.username), urllib.parse.unquote(url.password)


def _signed(params: dict, secret: str) -> dict:
    payload = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return {**params, "signature": hashlib.sha1((payload + secret).encode()).hexdigest()}


def host_video(path: Path, public_id: str) -> str:
    cloud, key, secret = _cloudinary()
    params = _signed({"public_id": public_id, "overwrite": "true", "timestamp": int(time.time())}, secret)
    with path.open("rb") as fh:
        response = requests.post(
            f"https://api.cloudinary.com/v1_1/{cloud}/video/upload",
            data={**params, "api_key": key},
            files={"file": fh},
            timeout=600,
        )
    response.raise_for_status()
    url = response.json()["secure_url"]
    head = requests.head(url, timeout=60, allow_redirects=True)
    if head.status_code != 200 or not head.headers.get("content-type", "").startswith("video/"):
        raise RuntimeError(f"Hosted video is not publicly reachable as video: {url} ({head.status_code})")
    return url


def unhost_video(public_id: str) -> None:
    cloud, key, secret = _cloudinary()
    params = _signed({"public_id": public_id, "invalidate": "true", "timestamp": int(time.time())}, secret)
    response = requests.post(
        f"https://api.cloudinary.com/v1_1/{cloud}/video/destroy", data={**params, "api_key": key}, timeout=60
    )
    response.raise_for_status()


def hosted_bytes(media_url: str) -> int:
    head = requests.head(media_url, timeout=60, allow_redirects=True)
    head.raise_for_status()
    return int(head.headers.get("content-length", 0))


def fetch_video(media_url: str, tries: int = 2) -> dict:
    """Download a hosted video whole, as Buffer will when the post goes out: {"bytes", "seconds"}. Raises when it
    doesn't come back complete as a video."""
    for attempt in range(1, tries + 1):
        started = time.monotonic()
        try:
            with requests.get(media_url, stream=True, timeout=(15, 60)) as response:
                response.raise_for_status()
                kind = response.headers.get("content-type", "")
                expected = int(response.headers.get("content-length") or 0)
                got = sum(len(chunk) for chunk in response.iter_content(1 << 20))
            if not kind.startswith("video/") or not got or (expected and got != expected):
                raise RuntimeError(f"came back as {kind or 'no type'}, {got} of {expected} bytes")
            return {"bytes": got, "seconds": round(time.monotonic() - started, 1)}
        except (requests.RequestException, RuntimeError) as err:
            if attempt == tries:
                raise RuntimeError(f"couldn't download {media_url}: {err}") from err
            time.sleep(30)


def shrink_hosted(public_id: str, media_url: str) -> tuple[str, str] | None:
    """Re-encode a hosted video larger than render.MAX_UPLOAD_MB to fit and host the copy: (public_id, url), or
    None when it already fits."""
    from .render import BT709, MAX_UPLOAD_MB

    if hosted_bytes(media_url) <= MAX_UPLOAD_MB * 1_000_000:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        source, small = Path(tmp) / "source.mp4", Path(tmp) / "small.mp4"
        with requests.get(media_url, stream=True, timeout=300) as response:
            response.raise_for_status()
            with source.open("wb") as fh:
                for chunk in response.iter_content(1 << 20):
                    fh.write(chunk)
        # Aims 10% under the limit, which leaves room for the audio and for the encoder overshooting.
        kbps = int(MAX_UPLOAD_MB * 8000 * 0.9 / ff.duration(source)) - 192
        ff.run(
            "-i", source, "-map", "0:v:0", "-map", "0:a:0",
            "-c:v", "libx264", "-preset", "medium", "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{2 * kbps}k",
            "-pix_fmt", "yuv420p", *BT709, "-c:a", "copy", "-movflags", "+faststart", small,
        )
        copy_id = f"{public_id}-{kbps}k"
        return copy_id, host_video(small, copy_id)


def _youtube_text(text: str) -> str:
    return text.replace("<", "‹").replace(">", "›")


def youtube_problems(title: str, text: str) -> list[str]:
    """What YouTube would refuse in a post's title and description."""
    problems = [f"{name} has {c}" for name, value in (("title", title), ("description", text)) for c in "<>" if c in value]
    if not title.strip():
        problems.append("no title")
    if len(title) > TITLE_CHARS:
        problems.append(f"title is {len(title)} characters")
    if len(text.encode()) > DESCRIPTION_BYTES:
        problems.append(f"description is {len(text.encode())} bytes")
    return problems


def _metadata(spec: ShortSpec) -> dict:
    return {
        "youtube": {
            "title": _youtube_text(spec.title)[:TITLE_CHARS],
            "categoryId": spec.category_id,
            "privacy": "public",
            "madeForKids": False,
            "notifySubscribers": True,
            "isAiGenerated": spec.synthetic_media,
            "embeddable": True,
        }
    }


def post(post_id: str) -> dict | None:
    """A post as Buffer has it, with its YouTube title and privacy, the video URL it will fetch, and "youtube": its
    YouTube details as an edit takes them; None when Buffer doesn't have it."""
    query = """
    query Post($id: PostId!) {
      post(input: {id: $id}) {
        id status dueAt text error { message }
        assets { ... on VideoAsset { source } }
        metadata {
          ... on YoutubePostMetadata {
            title privacy category { categoryId } madeForKids notifySubscribers isAiGenerated embeddable
          }
        }
      }
    }"""
    try:
        found = _buffer(query, {"id": post_id})["post"]
    except NotFound:
        return None
    meta = found.pop("metadata") or {}
    videos = [a["source"] for a in found.pop("assets") or [] if a.get("source")]
    youtube = {"title": meta.get("title"), "categoryId": (meta.get("category") or {}).get("categoryId"),
               **{k: meta.get(k) for k in ("privacy", "madeForKids", "notifySubscribers", "isAiGenerated", "embeddable")}}
    return found | {"title": meta.get("title") or "", "privacy": meta.get("privacy"), "video": videos[0] if videos else None,
                    "youtube": {k: v for k, v in youtube.items() if v is not None}}


def edit_post(post_id: str, spec: ShortSpec, media_url: str, text: str | None = None) -> None:
    """Point a queued Buffer post at media_url, and at text when given. Buffer wants the YouTube details with any
    edit."""
    _require_scheduling_open()
    mutation = """
    mutation Edit($input: EditPostInput!) {
      editPost(input: $input) {
        __typename
        ... on MutationError { message }
      }
    }"""
    edit = {"id": post_id, "assets": [{"video": {"url": media_url}}], "metadata": _metadata(spec)}
    if text is not None:
        edit["text"] = text
    result = _buffer(mutation, {"input": edit})["editPost"]
    if result["__typename"] != "PostActionSuccess":
        raise RuntimeError(f"Buffer wouldn't edit post {post_id}: {result.get('message')}")


def delete_post(post_id: str) -> None:
    mutation = """
    mutation Delete($input: DeletePostInput!) {
      deletePost(input: $input) {
        __typename
        ... on VoidMutationError { message }
      }
    }"""
    result = _buffer(mutation, {"input": {"id": post_id}})["deletePost"]
    if result["__typename"] != "DeletePostSuccess":
        raise RuntimeError(f"Buffer wouldn't delete post {post_id}: {result.get('message')}")


def failures(found: list[dict], now: datetime) -> list[dict]:
    """The posts in `found` that Buffer failed and that were due within RESEND_WINDOW before `now`."""
    return [p for p in found if p["status"] == "error" and p.get("dueAt")
            and timedelta(0) <= now - datetime.fromisoformat(p["dueAt"]) <= RESEND_WINDOW]


def resend(found: dict, when: datetime) -> dict:
    """Put a post Buffer failed (as post() returns it) back in the queue under the same id, due `when`. Buffer
    checks an edit as a whole post, so it repeats the video and YouTube details Buffer already has."""
    _require_scheduling_open()
    mutation = """
    mutation Resend($input: EditPostInput!) {
      editPost(input: $input) {
        __typename
        ... on PostActionSuccess { post { id status dueAt } }
        ... on MutationError { message }
      }
    }"""
    edit = {"id": found["id"], "dueAt": when.isoformat(), "mode": "customScheduled", "schedulingType": "automatic",
            "assets": [{"video": {"url": found["video"]}}], "metadata": {"youtube": found["youtube"]}}
    result = _buffer(mutation, {"input": edit})["editPost"]
    if result["__typename"] != "PostActionSuccess":
        raise RuntimeError(f"Buffer wouldn't queue post {found['id']} again: {result.get('message')}")
    return result["post"]


def resend_failed(now: datetime | None = None) -> list[dict]:
    """Send each post Buffer failed within RESEND_WINDOW again, RESEND_DELAY from now (cloud.slot_watch). Its video
    is downloaded first: a link that doesn't download would only fail again, and the download leaves the file in
    the CDN's cache just before Buffer fetches it. One {"id", "title", "sent", "note"} per failed post."""
    if SCHEDULING_HOLD.exists():
        return []
    now = now or datetime.now(timezone.utc)
    failed = failures(posts(since=now - RESEND_WINDOW), now)
    if not failed:
        return []
    found = channel()
    if wrong := [name for flag, name in (("isDisconnected", "disconnected"), ("isLocked", "locked"),
                                         ("isQueuePaused", "paused")) if found.get(flag)]:
        return [{"id": p["id"], "title": p["id"], "sent": False,
                 "note": f"Buffer's YouTube channel is {' and '.join(wrong)}"} for p in failed]
    results = []
    for failure in failed:
        full = post(failure["id"])
        if not full or full["status"] != "error":
            continue
        result = {"id": full["id"], "title": full["title"] or full["id"], "sent": False}
        results.append(result)
        if not full["video"] or not full["youtube"].get("categoryId"):
            result["note"] = "Buffer has no video or YouTube category for it"
            continue
        try:
            fetched = fetch_video(full["video"], tries=1)
            when = now + RESEND_DELAY
            resend(full, when)
        except BufferBusy:
            raise
        except (RuntimeError, requests.RequestException) as err:
            result["note"] = str(err)[:400]
            continue
        why = (full.get("error") or {}).get("message") or "no reason given"
        result.update(sent=True, note=f"due again {when:%H:%M} UTC after Buffer failed it ({why}); its video downloads "
                                      f"whole ({fetched['bytes'] / 1e6:.0f} MB in {fetched['seconds']:.0f} s)")
    return results


def _links_allowed() -> bool:
    return os.environ.get("YTC_DESCRIPTION_LINKS", "1") != "0"


def _domain(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.removeprefix("www.")


def _clean_credit(text: str | None) -> str | None:
    """Commons' Artist HTML carries hidden fallback text ("Unknown authorUnknown author or not provided",
    "AnonymousUnknown author"), broken templates ("{unknown"), Google Art Project biographies, and line
    breaks, which would split one credit over several lines of the description."""
    if not text:
        return text
    text = re.sub(r"(?<=:)\s*\n\s*", " ", text.strip())
    text = re.sub(r"\s*\n\s*", "; ", text)
    text = re.sub(r"\s+,", ",", " ".join(text.split()))
    if re.fullmatch(r"\{*\s*unknown\s*\}*", text, flags=re.I):
        return "Unknown author"
    if text.endswith("Details on Google Art Project"):
        text = re.split(r"\s+\(|\s+[–-]\s+", text)[0]
    text = re.sub(r"Unknown author\s*Unknown author(?: or not provided)?", "Unknown author", text)
    half = len(text) // 2
    if len(text) % 2 == 0 and text[:half] == text[half:]:
        return text[:half]
    return re.sub(r"(?<=[a-z])Unknown author$", "", text)


def _image_credits(manifest: dict, links: bool) -> list[str]:
    lines, seen = [], set()
    for beat in manifest["beats"]:
        asset = beat["asset"]
        if asset.get("source") in (None, "generated gradient", "local file", "designed card") or asset.get("url") in seen:
            continue
        seen.add(asset.get("url"))
        title = re.sub(r"\.(jpe?g|png|tiff?|gif|webp)$", "", asset.get("title") or "Untitled", flags=re.I)
        title = title.replace('"', "'")
        source = asset["source"].removesuffix(" (CC0)")
        rights = asset.get("license") or ("CC0" if "CC0" in asset["source"] else "public domain")
        cc_by = re.fullmatch(r"CC BY (\d(?:\.\d)?)", rights, flags=re.I)
        license_url = f"https://creativecommons.org/licenses/by/{cc_by.group(1)}/" if cc_by and links else None
        parts = [f'"{title}"', _clean_credit(asset.get("credit")), rights, license_url,
                 source, asset.get("url") if links else None]
        lines.append("- " + ", ".join(p for p in parts if p))
    return lines


def description(spec: ShortSpec, manifest: dict) -> str:
    text = _description(spec, manifest, _links_allowed())
    if len(text.encode()) > DESCRIPTION_BYTES:
        # Every source and credit still fits without its link.
        text = _description(spec, manifest, links=False)
    return text.encode()[:DESCRIPTION_BYTES].decode(errors="ignore")


def _description(spec: ShortSpec, manifest: dict, links: bool) -> str:
    blocks = [spec.description.strip()]
    if spec.sources:
        sources = spec.sources if links else list(dict.fromkeys(_domain(s) for s in spec.sources))
        blocks.append("Sources:\n" + "\n".join(f"- {s}" for s in sources))
    if credits := _image_credits(manifest, links):
        blocks.append("Images:\n" + "\n".join(credits))
    blocks.append("Researched and written by History's Last Hours. Narrated with a synthetic voice.")
    blocks.append(" ".join(spec.hashtags[:3]))
    return _youtube_text("\n\n".join(b for b in blocks if b))


def next_slots(count: int, taken: set[datetime], start: datetime | None = None, per_day: int = 3) -> list[datetime]:
    now = (start or datetime.now(AUDIENCE_TZ)).astimezone(AUDIENCE_TZ) + timedelta(minutes=30)
    day, found = now.date(), []
    while len(found) < count:
        for slot in sorted(SLOTS[:per_day]):
            when = datetime.combine(day, slot, AUDIENCE_TZ)
            booked = sum(t.astimezone(AUDIENCE_TZ).date() == day for t in taken | set(found))
            if when > now and when not in taken and booked < per_day:
                found.append(when)
                if len(found) == count:
                    break
        day += timedelta(days=1)
    return found


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stamp_manifest_media(folder: Path, episode_id: str) -> None:
    """Save the rendered file's digest in the manifest that survives worker handoff."""
    path = folder / "work" / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    digest = _sha256(folder / f"{episode_id}.mp4")
    if manifest.get("video_sha256") != digest:
        manifest["video_sha256"] = digest
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def media_binding(spec_path: Path, episode_id: str) -> dict[str, str]:
    """The rendered video, spec, and manifest digests, including after worker handoff omits the MP4."""
    folder = spec_path.parent
    video = folder / f"{episode_id}.mp4"
    manifest_path = folder / "work" / "manifest.json"
    if video.exists():
        media_hash = _sha256(video)
    else:
        media_hash = json.loads(manifest_path.read_text(encoding="utf-8")).get("video_sha256")
    if not media_hash:
        raise RuntimeError(f"{episode_id} has no local video or render hash in its manifest; cannot verify hosted media")
    return {"media_sha256": media_hash, "spec_sha256": _sha256(spec_path),
            "manifest_sha256": _sha256(manifest_path)}


def verify_hosted_media(media_url: str, expected_sha256: str) -> None:
    """Read the public asset Buffer will fetch and compare every byte to the reviewed render."""
    digest = hashlib.sha256()
    with requests.get(media_url, stream=True, timeout=(15, 60)) as response:
        response.raise_for_status()
        kind = response.headers.get("content-type", "")
        expected_bytes = int(response.headers.get("content-length") or 0)
        got = 0
        for chunk in response.iter_content(1 << 20):
            got += len(chunk)
            digest.update(chunk)
    if not kind.startswith("video/") or not got or (expected_bytes and got != expected_bytes):
        raise RuntimeError(f"Hosted video is incomplete or not video: {kind}, {got} of {expected_bytes} bytes")
    if digest.hexdigest() != expected_sha256:
        raise RuntimeError("Hosted video differs from the reviewed media hash; Buffer scheduling blocked")


def _validate_hold(held: dict, episode_id: str, binding: dict[str, str] | None = None) -> None:
    if held.get("superseded"):
        raise RuntimeError(f"{episode_id} has a superseded hosted video; host the repaired render before scheduling")
    if any(not held.get(field) for field in MEDIA_BINDING_FIELDS):
        raise RuntimeError(f"{episode_id} has an unbound hosted video; host the current render before scheduling")
    if binding is not None and any(held[field] != binding[field] for field in MEDIA_BINDING_FIELDS):
        raise RuntimeError(f"{episode_id} hosted video is stale relative to its local media, spec, or manifest; "
                           "host the repaired render before scheduling")


def schedule(spec_path: Path, when: datetime | None = None, *, reviewed_release: bool = False) -> dict:
    spec_path = spec_path.resolve()
    _require_scheduling_open(spec_path, exact_media_release=reviewed_release)
    spec = ShortSpec.load(spec_path)
    folder = spec_path.parent
    record_path = folder / "publish.json"
    if record_path.exists():
        existing = json.loads(record_path.read_text(encoding="utf-8"))
        raise RuntimeError(f"{spec.id} is already scheduled as Buffer post {existing['buffer_post_id']}")
    video = folder / f"{spec.id}.mp4"
    held_path = folder / "hold.json"
    held = json.loads(held_path.read_text(encoding="utf-8")) if held_path.exists() else None
    if reviewed_release and (not held or not held.get("media_url") or not held.get("media_public_id")):
        raise RuntimeError(f"{spec.id} reviewed release requires a pre-hosted, bound hold.json")
    if held is not None:
        _validate_hold(held, spec.id)
    if held is None:
        _stamp_manifest_media(folder, spec.id)
    binding = media_binding(spec_path, spec.id)
    _require_scheduling_open(spec_path, exact_media_release=reviewed_release)
    if held is not None:
        _validate_hold(held, spec.id, binding)
    if reviewed_release:
        verify_hosted_media(held["media_url"], binding["media_sha256"])
        _require_scheduling_open(spec_path, exact_media_release=True)
    manifest = json.loads((folder / "work" / "manifest.json").read_text(encoding="utf-8"))

    text = description(spec, manifest)
    recent = posts(since=datetime.now(AUDIENCE_TZ) - timedelta(days=30))
    # A run that stopped after Buffer took the post, before its record was saved, would otherwise post it twice.
    # Matched on the Short's own description, which leads the text: the credits after it are laid out by whichever
    # version of this code posted it.
    lead = text.split("\n\n", 1)[0]
    if twin := next((p for p in recent if (p.get("text") or "").split("\n\n", 1)[0] == lead
                     and p["status"] not in ("error", "draft")), None):
        if reviewed_release:
            raise RuntimeError(f"Existing Buffer post {twin['id']} matches {spec.id}; inspect it before a reviewed release")
        log.warning("%s is already Buffer post %s; recording it instead of posting it again", spec.id, twin["id"])
        return _record(folder, spec, twin, held["media_public_id"] if held else f"creaturereceipts/{spec.id}",
                       held["media_url"] if held else None, binding)
    queued = [p for p in recent if p["status"] not in ("sent", "error", "draft")]
    if len(queued) >= BUFFER_QUEUE_LIMIT:
        raise RuntimeError(f"Buffer queue is full ({len(queued)} scheduled)")
    if when is None:
        taken = {datetime.fromisoformat(p["dueAt"]).astimezone(AUDIENCE_TZ) for p in queued if p.get("dueAt")}
        when = next_slots(1, taken)[0]

    public_id = held["media_public_id"] if held else f"creaturereceipts/{spec.id}"
    media_url = held["media_url"] if held else host_video(video, public_id)
    mutation = """
    mutation Create($input: CreatePostInput!) {
      createPost(input: $input) {
        __typename
        ... on PostActionSuccess { post { id status dueAt } }
        ... on MutationError { message }
      }
    }"""
    payload = {
        "channelId": youtube_channel_id(),
        "text": text,
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": when.isoformat(),
        "assets": [{"video": {"url": media_url}}],
        "metadata": _metadata(spec),
    }
    result = _buffer(mutation, {"input": payload})["createPost"]
    if result["__typename"] != "PostActionSuccess":
        if not held:
            unhost_video(public_id)
        raise RuntimeError(f"Buffer rejected {spec.id}: {result.get('message')}")
    record = _record(folder, spec, result["post"] | {"dueAt": when.isoformat()}, public_id, media_url,
                     {**binding, **{k: held[k] for k in ("media_bytes", "retries", "crossposts") if k in (held or {})}})
    log.info("scheduled %s for %s", spec.id, when.isoformat())
    return record


def _record(folder: Path, spec: ShortSpec, post: dict, public_id: str, media_url: str | None,
            extra: dict | None = None) -> dict:
    record = {
        "id": spec.id,
        "title": spec.title,
        "buffer_post_id": post["id"],
        "due_at": post.get("dueAt"),
        "media_public_id": public_id,
        "media_url": media_url,
        "status": post["status"],
        "youtube_url": post.get("externalLink"),
        **(extra or {}),
    }
    (folder / "publish.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    (folder / "hold.json").unlink(missing_ok=True)
    return record


def crosspost_channels() -> dict[str, str]:
    """The cross-post channels switched on: service -> Buffer channel id."""
    return {service: value for service, name in CROSSPOST_ENV.items() if (value := os.environ.get(name, "").strip())}


def caption(spec: ShortSpec) -> str:
    """A TikTok or Instagram caption for a Short: its title, description, and sources by site (links aren't
    clickable there), the voice disclosure, and a few hashtags without YouTube's own."""
    tags = [t for t in spec.hashtags if t.lower().lstrip("#") not in ("shorts", "youtubeshorts", "ytshorts")][:CAPTION_HASHTAGS]
    blocks = [spec.title.strip(), re.sub(r"https?://\S+", "", spec.description).strip()]
    if spec.sources:
        blocks.append("Sources: " + ", ".join(dict.fromkeys(_domain(s) for s in spec.sources)))
    blocks.append("Researched and written by History's Last Hours. Narrated with a synthetic voice.")
    tail = " ".join(tags)
    text = "\n\n".join(b for b in blocks if b)
    return text[: CAPTION_CHARS - len(tail) - 2].rstrip() + ("\n\n" + tail if tail else "")


def _crosspost_metadata(service: str, spec: ShortSpec) -> dict:
    if service == "instagram":
        return {"instagram": {"type": "reel", "shouldShareToFeed": True, "isAiGenerated": spec.synthetic_media}}
    if service == "tiktok":
        return {"tiktok": {"isAiGenerated": spec.synthetic_media}}
    raise ValueError(f"no cross-posting to {service}")


def crosspost(spec_path: Path, service: str, channel_id: str, media_url: str, when: datetime) -> dict:
    """Schedule a Short natively on a TikTok or Instagram channel in Buffer, the same video file as its YouTube
    post (no watermark), due `when`: {"id", "status", "due_at"}."""
    spec_path = spec_path.resolve()
    _require_scheduling_open(spec_path)
    spec = ShortSpec.load(spec_path)
    mutation = """
    mutation Create($input: CreatePostInput!) {
      createPost(input: $input) {
        __typename
        ... on PostActionSuccess { post { id status dueAt } }
        ... on MutationError { message }
      }
    }"""
    payload = {
        "channelId": channel_id,
        "text": caption(spec),
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": when.isoformat(),
        "assets": [{"video": {"url": media_url}}],
        "metadata": _crosspost_metadata(service, spec),
    }
    result = _buffer(mutation, {"input": payload})["createPost"]
    if result["__typename"] != "PostActionSuccess":
        raise RuntimeError(f"Buffer rejected the {service} post of {spec.id}: {result.get('message')}")
    return {"id": result["post"]["id"], "status": result["post"]["status"], "due_at": when.isoformat()}


def hold(spec_path: Path, extra: dict | None = None) -> dict:
    """Host a finished Short so it can wait for a Buffer slot and be scheduled from any machine."""
    spec_path = spec_path.resolve()
    spec = ShortSpec.load(spec_path)
    video = spec_path.parent / f"{spec.id}.mp4"
    _stamp_manifest_media(spec_path.parent, spec.id)
    binding = media_binding(spec_path, spec.id)
    # Named after the file, so a second render of the same episode can't replace the video a record points to.
    public_id = f"creaturereceipts/{spec.id}-{binding['media_sha256'][:8]}"
    record = {
        "id": spec.id,
        "title": spec.title,
        "series": spec.series,
        "media_public_id": public_id,
        "media_url": host_video(video, public_id),
        "hosted_at": datetime.now(AUDIENCE_TZ).isoformat(timespec="seconds"),
        **(extra or {}),
        **binding,
    }
    if media_binding(spec_path, spec.id) != binding:
        raise RuntimeError(f"{spec.id} changed while its video was being hosted; hold was not saved")
    (spec_path.parent / "hold.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def sync(content_dir: Path) -> list[dict]:
    """Refresh publish.json files from Buffer, and free the hosted and local copies of Shorts two days after
    they go live."""
    by_id = {p["id"]: p for p in posts(since=datetime.now(AUDIENCE_TZ) - timedelta(days=30))}
    records = []
    for record_path in sorted(content_dir.glob("*/publish.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        post = by_id.get(record["buffer_post_id"])
        if post:
            record["status"] = post["status"]
            # A post sent again after a failure is due later than it was scheduled for.
            if post.get("dueAt"):
                record["due_at"] = datetime.fromisoformat(post["dueAt"]).astimezone(AUDIENCE_TZ).isoformat()
            record["youtube_url"] = post.get("externalLink") or record.get("youtube_url")
            record["sent_at"] = post.get("sentAt")
            record["error"] = (post.get("error") or {}).get("message")
            record["metrics"] = {m["type"]: m["value"] for m in post.get("metrics") or []}
            record["metrics_updated_at"] = post.get("metricsUpdatedAt")
        sent_at = record.get("sent_at")
        if record["status"] == "sent" and sent_at:
            if datetime.fromisoformat(sent_at) < datetime.now(AUDIENCE_TZ) - timedelta(days=2):
                if record.get("media_url"):
                    unhost_video(record["media_public_id"])
                    record["media_url"] = None
                _free_local(record_path.parent, record["id"])
        record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        records.append(record)
    return records


def _free_local(folder: Path, short_id: str) -> None:
    """Delete a live Short's video, images, and audio; keep its spec, research, captions, and manifest."""
    for name in BULKY:
        path = folder / name.format(id=short_id)
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
