"""Dormant, exact-media release gate for newly produced History Shorts.

The policy file is deliberately absent from the repository. A certificate records what the
studio checked; every release rechecks its inputs and the hosted bytes before Buffer is touched.
This is a mechanical provenance and rights gate, not an independent historical fact check.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

from . import publish
from .research import site
from .spec import ShortSpec

ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = ROOT / "status" / "autonomous_release_policy.json"
CERTIFICATE = "release_certificate.json"
FILES = ("short.yaml", "script.json", "research.json", "review.json", "work/manifest.json")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_EPISODE = re.compile(r"ep(\d{3,})\Z")
_CC_BY = re.compile(r"CC BY (?:2\.0|2\.5|3\.0|4\.0)(?: [a-z]{2})?\Z", re.I)
_OPEN = {"CC0", "Public domain", "Pexels License", "Pixabay Content License"}
_ORIGINAL = {"designed card", "AI generated"}
FIRST_ELIGIBLE_EPISODE = 63  # ep062 and earlier existed when this gate was designed.
FIRST_ELIGIBLE_START = datetime(2026, 10, 5, tzinfo=timezone.utc)
MIN_POST_LEAD = timedelta(minutes=30)
MAX_POST_HORIZON = timedelta(days=30)
MAX_INSTAGRAM_RETRY = timedelta(days=7)


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path.name} must be an object")
    return value


def _hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise RuntimeError("release cutoff must have a UTC offset")
    return parsed


def policy() -> dict | None:
    """An absent or disabled policy does nothing; a malformed enabled policy stops release."""
    if not POLICY_PATH.exists():
        return None
    config = _json(POLICY_PATH)
    if config.get("enabled") is not True:
        return None
    if os.environ.get("YTC_AUTONOMOUS_RELEASE") != "1":
        return None
    minimum = _EPISODE.fullmatch(str(config.get("min_episode_id", "")))
    if config.get("version") != 1 or not minimum or int(minimum.group(1)) < FIRST_ELIGIBLE_EPISODE:
        raise RuntimeError("autonomous release policy has no valid version or episode floor")
    cutoff = _utc(config["started_after_utc"])
    if cutoff < FIRST_ELIGIBLE_START:
        raise RuntimeError("autonomous release cutoff predates the new-draft boundary")
    if cutoff > datetime.now(timezone.utc) + timedelta(days=366):
        raise RuntimeError("autonomous release cutoff is implausibly far in the future")
    if not config.get("require_instagram") is True:
        raise RuntimeError("autonomous release must require Instagram")
    return config


def _new_draft(folder: Path, config: dict) -> None:
    number = _EPISODE.fullmatch(folder.name)
    floor = _EPISODE.fullmatch(config["min_episode_id"])
    if not number or not floor or int(number.group(1)) < int(floor.group(1)):
        raise RuntimeError(f"{folder.name} predates the autonomous release episode floor")
    # topic.started_at can use the studio's IST timezone. Compare instants, not strings.
    started = datetime.fromisoformat(_json(folder / "topic.json")["started_at"])
    if started.tzinfo is None or started.astimezone(timezone.utc) < _utc(config["started_after_utc"]):
        raise RuntimeError(f"{folder.name} predates the autonomous release time cutoff")


def _sources_and_rights(folder: Path) -> tuple[list[dict], list[dict]]:
    research, script = _json(folder / "research.json"), _json(folder / "script.json")
    manifest = _json(folder / "work" / "manifest.json")
    spec = ShortSpec.load(folder / "short.yaml")
    if manifest.get("id") != folder.name or manifest.get("video_sha256") is None:
        raise RuntimeError("manifest identity or rendered media hash is missing")
    sources = {s["label"]: s for s in research["sources"]}
    if not research.get("viable") or not sources or not script.get("beats"):
        raise RuntimeError("research is incomplete")
    if [b.text for b in spec.beats] != [b["text"] for b in script["beats"]] or len(manifest["beats"]) != len(spec.beats):
        raise RuntimeError("script, spec, and rendered beats disagree")
    claims = research["claims"]
    cited: set[int] = set()
    for beat in script["beats"]:
        numbers = beat.get("claims")
        if not isinstance(numbers, list) or not numbers:
            raise RuntimeError("a narrated beat has no research citation")
        for number in numbers:
            if not isinstance(number, int) or not 1 <= number <= len(claims):
                raise RuntimeError("a narrated beat cites a missing claim")
            cited.add(number)
    certified_claims = []
    for number in sorted(cited):
        claim = claims[number - 1]
        evidence = claim.get("evidence") or []
        labels = {item.get("source") for item in evidence if isinstance(item, dict) and
                  len(str(item.get("quote", "")).split()) >= 4 and len(str(item.get("quote", ""))) >= 20}
        labels &= set(claim.get("sources") or [])
        if len({site(sources[label]["url"]) for label in labels if label in sources}) < 2:
            raise RuntimeError(f"claim {number} lacks two independently quoted source sites")
        for label in labels:
            if label not in sources or urlparse(sources[label]["url"]).scheme not in ("http", "https"):
                raise RuntimeError(f"claim {number} has an invalid source URL")
        certified_claims.append({"number": number, "source_labels": sorted(labels)})
    assets = []
    for number, beat in enumerate(manifest["beats"], 1):
        if beat["text"] != spec.beats[number - 1].text:
            raise RuntimeError("rendered narration differs from the script")
        asset = beat["asset"]
        kind, license_name = asset.get("source"), asset.get("license")
        if kind in _ORIGINAL:
            if kind == "AI generated" and not spec.synthetic_media:
                raise RuntimeError("AI imagery has no synthetic-media disclosure")
        elif license_name not in _OPEN and not (isinstance(license_name, str) and _CC_BY.fullmatch(license_name)):
            raise RuntimeError(f"beat {number} has unapproved or missing image rights: {license_name}")
        if kind not in _ORIGINAL and (not asset.get("url") or not asset.get("credit")):
            raise RuntimeError(f"beat {number} lacks image provenance or credit")
        assets.append({"beat": number, "source": kind, "license": license_name, "url": asset.get("url")})
    return certified_claims, assets


def _review(folder: Path, media_sha256: str) -> dict:
    review = _json(folder / "review.json")
    rounds = review["rounds"]
    kept = review.get("kept_round", len(rounds))
    if not isinstance(kept, int) or not 1 <= kept <= len(rounds):
        raise RuntimeError("review has no kept round")
    round_ = rounds[kept - 1]
    check = round_["check"]
    from .studio import GATE, PASS_SCORE
    if (round_.get("media_sha256") != media_sha256 or round_.get("passed") is not True or
        check.get("warnings") != [] or check.get("speech_differences") != [] or check.get("speech_error") or
        round_.get("frames") != [] or round_.get("speech") != [] or
        any(round_["scores"].get(name, 0) < PASS_SCORE for name in GATE)):
        raise RuntimeError("the exact rendered MP4 has no clean final-media review")
    return {"round": kept, "scores": round_["scores"], "speech_differences": [], "warnings": []}


def certify(folder: Path) -> dict:
    """Save a certificate after a new draft has passed review and its MP4 has been hosted."""
    folder = folder.resolve()
    match = _EPISODE.fullmatch(folder.name)
    if not match or int(match.group(1)) < FIRST_ELIGIBLE_EPISODE:
        raise RuntimeError("legacy drafts cannot receive an autonomous release certificate")
    held = _json(folder / "hold.json")
    spec = ShortSpec.load(folder / "short.yaml")
    if spec.id != folder.name or held.get("id") != spec.id:
        raise RuntimeError("episode identity disagrees")
    media = folder / f"{spec.id}.mp4"
    media_sha256 = _hash(media)
    if _json(folder / "work" / "manifest.json").get("video_sha256") != media_sha256:
        raise RuntimeError("manifest render hash differs from the reviewed MP4")
    binding = publish.media_binding(folder / "short.yaml", spec.id)
    if binding["media_sha256"] != media_sha256 or any(held.get(k) != v for k, v in binding.items()):
        raise RuntimeError("hosted hold does not bind to the reviewed MP4")
    if not held.get("media_url") or not held.get("media_public_id"):
        raise RuntimeError("hosted media is missing")
    claims, assets = _sources_and_rights(folder)
    reviewed = _review(folder, media_sha256)
    certificate = {"version": 1, "id": spec.id, "issued_at_utc": datetime.now(timezone.utc).isoformat(),
                   "media_sha256": media_sha256, "media_url": held["media_url"],
                   "media_public_id": held["media_public_id"],
                   "files": {name: _hash(folder / name) for name in FILES},
                   "claims": claims, "assets": assets, "review": reviewed}
    (folder / CERTIFICATE).write_text(json.dumps(certificate, indent=2) + "\n", encoding="utf-8")
    return certificate


def validate(spec_path: Path, *, hosted: bool = False) -> dict:
    """Recheck the certificate, policy, episode age, and hosted record for either platform."""
    config = policy()
    if config is None:
        raise RuntimeError("autonomous release policy is inactive")
    folder = spec_path.resolve().parent
    if (folder / "editorial_hold.json").exists():
        raise RuntimeError(f"{folder.name} is on editorial hold")
    _new_draft(folder, config)
    certificate = _json(folder / CERTIFICATE)
    if certificate.get("version") != 1 or certificate.get("id") != folder.name:
        raise RuntimeError("release certificate identity is invalid")
    if any(not _HASH.fullmatch(str(value)) or _hash(folder / name) != value
           for name, value in certificate.get("files", {}).items()):
        raise RuntimeError("release certificate files changed")
    if set(certificate.get("files", {})) != set(FILES):
        raise RuntimeError("release certificate file list is incomplete")
    binding = publish.media_binding(spec_path, folder.name)
    if _json(folder / "work" / "manifest.json").get("video_sha256") != certificate.get("media_sha256"):
        raise RuntimeError("manifest render hash differs from the release certificate")
    if certificate.get("media_sha256") != binding["media_sha256"] or any(
        certificate["files"][name] != binding[field]
        for name, field in (("short.yaml", "spec_sha256"), ("work/manifest.json", "manifest_sha256"))
    ):
        raise RuntimeError("release certificate media binding changed")
    local = folder / f"{folder.name}.mp4"
    if local.exists() and _hash(local) != certificate["media_sha256"]:
        raise RuntimeError("local MP4 differs from the certified media")
    if _sources_and_rights(folder) != (certificate.get("claims"), certificate.get("assets")):
        raise RuntimeError("source or rights certificate changed")
    if _review(folder, certificate["media_sha256"]) != certificate.get("review"):
        raise RuntimeError("final-media review certificate changed")
    record_path = folder / ("publish.json" if (folder / "publish.json").exists() else "hold.json")
    record = _json(record_path)
    if record.get("media_url") != certificate.get("media_url") or record.get("media_public_id") != certificate.get("media_public_id"):
        raise RuntimeError("hosted record differs from the certified media")
    if any(record.get(key) != binding[key] for key in publish.MEDIA_BINDING_FIELDS):
        raise RuntimeError("hosted record has a stale media binding")
    if hosted:
        publish.verify_hosted_media(certificate["media_url"], certificate["media_sha256"])
    return certificate


def instagram_channel_id() -> str:
    wanted = os.environ.get("BUFFER_INSTAGRAM_CHANNEL_ID", "").strip()
    if not wanted:
        raise RuntimeError("BUFFER_INSTAGRAM_CHANNEL_ID is required for autonomous release")
    matched = next((item for item in publish.channels() if item.get("id") == wanted), None)
    if not matched or matched.get("service") != "instagram" or any(
        matched.get(flag) for flag in ("isDisconnected", "isLocked", "isQueuePaused")
    ):
        raise RuntimeError("configured Instagram channel is missing, disconnected, locked, or paused")
    return wanted


def _due(value: str | None, label: str) -> datetime:
    """A timezone-aware Buffer due time; never let a naive or malformed time enter a mutation."""
    try:
        parsed = datetime.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        parsed = None
    if parsed is None or parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeError(f"{label} has no valid timezone-aware due time")
    return parsed.astimezone(timezone.utc)


def _instagram_due(youtube_due: datetime, posts: list[dict], now: datetime) -> datetime:
    """Keep a future paired slot; after it passes, choose a fresh bounded Instagram slot."""
    if youtube_due > now + MIN_POST_LEAD:
        if youtube_due > now + MAX_POST_HORIZON:
            raise RuntimeError("paired YouTube slot is too far in the future")
        return youtube_due
    if youtube_due < now - MAX_INSTAGRAM_RETRY:
        raise RuntimeError("YouTube slot is too old for a fresh Instagram retry")
    from .publish import next_slots
    taken = {_due(p["dueAt"], "Instagram Buffer post") for p in posts if p.get("dueAt")}
    fresh = _due(next_slots(1, taken, start=now)[0].isoformat(), "fresh Instagram slot")
    if not now + MIN_POST_LEAD < fresh <= min(now + MAX_POST_HORIZON, youtube_due + MAX_INSTAGRAM_RETRY):
        raise RuntimeError("fresh Instagram slot is outside the safe scheduling window")
    return fresh


def schedule_waiting(run) -> None:
    """Under the channel hold, release only certified future drafts to YouTube and Instagram."""
    config = None
    with run.stage("autonomous release policy") as entry:
        config = policy()
        entry["detail"] = "active" if config else "disabled"
    if not run.stages[-1]["ok"] or config is None:
        run.notes.append("new scheduling on editorial hold; production continues")
        return
    from . import auto
    from .publish import AUDIENCE_TZ, BUFFER_QUEUE_LIMIT, caption, next_slots, posts

    instagram = None
    instagram_room = False
    with run.stage("autonomous release destinations") as entry:
        instagram = instagram_channel_id()
        youtube = publish.channel()
        if any(youtube.get(flag) for flag in ("isDisconnected", "isLocked", "isQueuePaused")):
            raise RuntimeError("configured YouTube channel is disconnected, locked, or paused")
        instagram_posts = posts(channel_id=instagram)
        instagram_room = len([p for p in instagram_posts if p["status"] not in ("sent", "error", "draft")]) < BUFFER_QUEUE_LIMIT
        entry["detail"] = "YouTube and Instagram connected"
    if not run.stages[-1]["ok"] or instagram is None:
        return
    eps = auto.episodes()
    missing = [e["id"] for e in eps if e["state"] == "waiting" and not (e["folder"] / CERTIFICATE).exists()]
    if missing:
        run.notes.append(f"uncertified waiting drafts remain held: {', '.join(missing)}")
    # Pair one YouTube post with its Instagram Reel per run, keeping queue capacity predictable.
    waiting = [e for e in eps if e["state"] == "waiting" and (e["folder"] / CERTIFICATE).exists()][:1]
    if not instagram_room and waiting:
        run.notes.append("Instagram Buffer queue is full; certified drafts remain held")
        waiting = []
    scheduled = [e for e in eps if e["state"] in ("scheduled", "live") and (e["folder"] / CERTIFICATE).exists()
                 and not ((e["record"].get("crossposts") or {}).get("instagram") or {}).get("id")]
    for e in waiting:
        with run.stage(f"release {e['id']} to YouTube") as entry:
            spec_path = e["folder"] / "short.yaml"
            validate(spec_path)
            youtube_posts = posts()
            when = next_slots(1, {_due(p["dueAt"], "YouTube Buffer post").astimezone(AUDIENCE_TZ)
                                  for p in youtube_posts if p.get("dueAt")})[0]
            record = publish.schedule(spec_path, when, autonomous_release=True)
            entry["detail"] = record["due_at"]
            run.published.append({"id": e["id"], "title": e["title"], "due_at": record["due_at"]})
            scheduled.append({**e, "state": "scheduled", "record": record})
    for e in scheduled:
        with run.stage(f"release {e['id']} to Instagram") as entry:
            spec_path = e["folder"] / "short.yaml"
            cert = validate(spec_path)
            record = _json(e["folder"] / "publish.json")
            existing = (record.get("crossposts") or {}).get("instagram")
            if existing and existing.get("id"):
                entry["detail"] = f"already recorded as {existing['id']}"
                continue
            spec = ShortSpec.load(spec_path)
            recent = posts(channel_id=instagram)
            exact = [p for p in recent if p.get("text") == caption(spec)]
            if len(exact) > 1:
                raise RuntimeError("multiple matching Instagram posts need inspection")
            if exact:
                post = exact[0]
                if post["status"] in ("error", "draft"):
                    raise RuntimeError(f"matching Instagram post {post['id']} is {post['status']}")
                youtube_due = _due(record.get("due_at"), "YouTube post")
                accepted_due = _due(post.get("dueAt"), "matching Instagram post")
                if not youtube_due <= accepted_due <= youtube_due + MAX_INSTAGRAM_RETRY:
                    raise RuntimeError(f"Instagram post {post['id']} has an unrelated due time")
                remote = publish.post(post["id"])
                if not remote or remote.get("video") != cert["media_url"] or remote.get("text") != caption(spec):
                    raise RuntimeError(f"Instagram post {post['id']} has unverified media or text")
                publish.verify_hosted_media(cert["media_url"], cert["media_sha256"])
                result = {"id": post["id"], "status": post["status"], "due_at": post.get("dueAt")}
            else:
                if len([p for p in recent if p["status"] not in ("sent", "error", "draft")]) >= BUFFER_QUEUE_LIMIT:
                    raise RuntimeError("Instagram Buffer queue is full")
                due = _instagram_due(_due(record.get("due_at"), "YouTube post"), recent,
                                     datetime.now(timezone.utc))
                result = publish.crosspost(spec_path, "instagram", instagram, cert["media_url"],
                                           due, autonomous_release=True)
            record.setdefault("crossposts", {})["instagram"] = result
            (e["folder"] / "publish.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            entry["detail"] = f"Instagram post {result['id']}"
