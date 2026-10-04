"""Dormant, exact-media release gate for independently reviewed History Shorts.

The tracked policy is disabled. A signed review from outside production and a certificate
bind the reviewed media and inputs; every release rechecks them before Buffer is touched.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from . import publish
from .research import site
from .spec import ShortSpec

ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = ROOT / "status" / "autonomous_release_policy.json"
REVIEW_PUBLIC_KEY_PATH = ROOT / "kit" / "independent-review.pub"
INDEPENDENT_REVIEW = "independent_review.json"
REVIEW_SIGNING_CONTEXT = b"history-last-hours-independent-review-v1\0"
CERTIFICATE = "release_certificate.json"
CERTIFICATE_VERSION = 2
FILES = ("topic.json", "short.yaml", "script.json", "research.json", "visuals.json",
         "review.json", "work/manifest.json")
REVIEW_CHECKS = ("claim_sources", "visual_identity_rights", "full_video_audio")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_EPISODE = re.compile(r"ep(\d{3,})\Z")
_CC_BY = re.compile(r"CC BY (?:2\.0|2\.5|3\.0|4\.0)(?: [a-z]{2})?\Z", re.I)
_OPEN = {"CC0", "Public domain", "Pexels License", "Pixabay Content License"}
_ORIGINAL = {"designed card", "AI generated"}
FIRST_ELIGIBLE_EPISODE = 63  # ep062 and earlier existed when this gate was designed.
# ep063 does not exist yet. Allow new drafts made after this rollout on October 4
# so a successful bounded trial can be released without an unnecessary day of delay.
FIRST_ELIGIBLE_START = datetime(2026, 10, 4, 5, tzinfo=timezone.utc)
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


def _utc(value: str, label: str = "release cutoff") -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise RuntimeError(f"{label} must have a UTC offset")
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
    if type(config.get("require_instagram")) is not bool:
        raise RuntimeError("autonomous release must explicitly choose whether Instagram is required")
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
    from .check import speech_verified
    from .studio import GATE, PASS_SCORE
    if (round_.get("media_sha256") != media_sha256 or round_.get("passed") is not True or
        check.get("warnings") != [] or check.get("speech_differences") != [] or check.get("speech_error") or
        round_.get("frames") != [] or round_.get("speech") != [] or
        any(round_["scores"].get(name, 0) < PASS_SCORE for name in GATE)):
        raise RuntimeError("the exact rendered MP4 has no clean final-media review")
    if "speech_verification" in check:
        beats = _json(folder / "work" / "manifest.json")["beats"]
        if not speech_verified(check["speech_verification"], media_sha256, beats):
            raise RuntimeError("the exact rendered MP4 has no clean final-media review")
    return {"round": kept, "scores": round_["scores"], "speech_differences": [], "warnings": []}


def _review_subject(folder: Path, record: dict, media_sha256: str, files: dict[str, str]) -> dict:
    return {"id": folder.name, "media_sha256": media_sha256,
            "media_url": record["media_url"], "media_public_id": record["media_public_id"],
            "files": files}


def _independent_review(folder: Path, subject: dict) -> dict:
    """Verify a separate reviewer's signed approval of this exact media and its source files."""
    try:
        key_bytes = base64.b64decode(REVIEW_PUBLIC_KEY_PATH.read_text(encoding="utf-8").strip(), validate=True)
        if len(key_bytes) != 32:
            raise ValueError("Ed25519 public keys contain 32 bytes")
        key = Ed25519PublicKey.from_public_bytes(key_bytes)
    except (OSError, ValueError, binascii.Error) as exc:
        raise RuntimeError("trusted independent reviewer public key is missing or invalid") from exc
    try:
        review = _json(folder / INDEPENDENT_REVIEW)
    except FileNotFoundError as exc:
        raise RuntimeError("signed independent review is missing") from exc
    if set(review) != {"version", "subject", "reviewer_key_sha256", "reviewed_at_utc", "decision", "checks", "signature"}:
        raise RuntimeError("independent review fields are incomplete or unexpected")
    fingerprint = hashlib.sha256(key_bytes).hexdigest()
    if (type(review["version"]) is not int or review["version"] != 1 or review["subject"] != subject or
        review["reviewer_key_sha256"] != fingerprint or review["decision"] != "approved" or
        not isinstance(review["checks"], dict) or set(review["checks"]) != set(REVIEW_CHECKS) or
        any(review["checks"][name] is not True for name in REVIEW_CHECKS)):
        raise RuntimeError("independent review does not approve this exact candidate")
    try:
        reviewed_at = _utc(review["reviewed_at_utc"], "independent review time")
    except (TypeError, ValueError) as exc:
        raise RuntimeError("independent review time is invalid") from exc
    if reviewed_at > datetime.now(timezone.utc) + timedelta(minutes=5):
        raise RuntimeError("independent review time is in the future")
    try:
        signature = base64.b64decode(review["signature"], validate=True)
        signed = {name: value for name, value in review.items() if name != "signature"}
        message = json.dumps(signed, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                             allow_nan=False).encode("utf-8")
        key.verify(signature, REVIEW_SIGNING_CONTEXT + message)
    except (TypeError, ValueError, binascii.Error, InvalidSignature) as exc:
        raise RuntimeError("independent review signature is invalid") from exc
    return {"reviewer_key_sha256": fingerprint, "reviewed_at_utc": review["reviewed_at_utc"]}


def certify(folder: Path) -> dict:
    """Save a certificate only after separate signed QA of the exact hosted MP4."""
    folder = folder.resolve()
    match = _EPISODE.fullmatch(folder.name)
    if not match or int(match.group(1)) < FIRST_ELIGIBLE_EPISODE:
        raise RuntimeError("legacy drafts cannot receive an autonomous release certificate")
    held = _json(folder / "hold.json")
    spec = ShortSpec.load(folder / "short.yaml")
    if spec.id != folder.name or held.get("id") != spec.id:
        raise RuntimeError("episode identity disagrees")
    if held.get("superseded"):
        raise RuntimeError("superseded hosted media cannot receive a release certificate")
    media = folder / f"{spec.id}.mp4"
    binding = publish.media_binding(folder / "short.yaml", spec.id)
    media_sha256 = binding["media_sha256"]
    if not _HASH.fullmatch(str(media_sha256)):
        raise RuntimeError("rendered MP4 hash is invalid")
    if media.exists() and _hash(media) != media_sha256:
        raise RuntimeError("local MP4 differs from the hosted media binding")
    if _json(folder / "work" / "manifest.json").get("video_sha256") != media_sha256:
        raise RuntimeError("manifest render hash differs from the reviewed MP4")
    if binding["media_sha256"] != media_sha256 or any(held.get(k) != v for k, v in binding.items()):
        raise RuntimeError("hosted hold does not bind to the reviewed MP4")
    if not held.get("media_url") or not held.get("media_public_id"):
        raise RuntimeError("hosted media is missing")
    claims, assets = _sources_and_rights(folder)
    reviewed = _review(folder, media_sha256)
    files = {name: _hash(folder / name) for name in FILES}
    independent = _independent_review(folder, _review_subject(folder, held, media_sha256, files))
    publish.verify_hosted_media(held["media_url"], media_sha256)
    certificate = {"version": CERTIFICATE_VERSION, "id": spec.id, "issued_at_utc": datetime.now(timezone.utc).isoformat(),
                   "media_sha256": media_sha256, "media_url": held["media_url"],
                   "media_public_id": held["media_public_id"],
                   "files": files, "claims": claims, "assets": assets, "review": reviewed,
                   "independent_review_sha256": _hash(folder / INDEPENDENT_REVIEW),
                   "independent_review": independent}
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
    if certificate.get("version") != CERTIFICATE_VERSION or certificate.get("id") != folder.name:
        raise RuntimeError("release certificate identity is invalid")
    files = certificate.get("files")
    if not isinstance(files, dict) or set(files) != set(FILES):
        raise RuntimeError("release certificate file list is incomplete")
    if any(not _HASH.fullmatch(str(files[name])) or _hash(folder / name) != files[name] for name in FILES):
        raise RuntimeError("release certificate files changed")
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
    if record.get("superseded"):
        raise RuntimeError("superseded hosted media cannot be released")
    if record.get("media_url") != certificate.get("media_url") or record.get("media_public_id") != certificate.get("media_public_id"):
        raise RuntimeError("hosted record differs from the certified media")
    if any(record.get(key) != binding[key] for key in publish.MEDIA_BINDING_FIELDS):
        raise RuntimeError("hosted record has a stale media binding")
    review_path = folder / INDEPENDENT_REVIEW
    if not review_path.exists() or certificate.get("independent_review_sha256") != _hash(review_path):
        raise RuntimeError("signed independent review differs from the release certificate")
    independent = _independent_review(folder, _review_subject(folder, certificate, certificate["media_sha256"], files))
    if independent != certificate.get("independent_review"):
        raise RuntimeError("independent review certificate changed")
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
    """Under the channel hold, release certified future drafts to YouTube and configured Instagram."""
    config = None
    with run.stage("autonomous release policy") as entry:
        config = policy()
        entry["detail"] = "active" if config else "disabled"
    if not run.stages[-1]["ok"] or config is None:
        run.notes.append("new scheduling on editorial hold; automatic production pauses while release is inactive")
        return
    from . import auto
    from .publish import AUDIENCE_TZ, BUFFER_QUEUE_LIMIT, caption, next_slots, posts

    youtube_ready = False
    instagram = None
    instagram_room = False
    with run.stage("autonomous release destinations") as entry:
        youtube = publish.channel()
        if any(youtube.get(flag) for flag in ("isDisconnected", "isLocked", "isQueuePaused")):
            raise RuntimeError("configured YouTube channel is disconnected, locked, or paused")
        youtube_ready = True
        if config["require_instagram"]:
            candidate = instagram_channel_id()
            instagram_posts = posts(channel_id=candidate)
            instagram_room = len([p for p in instagram_posts if p["status"] not in ("sent", "error", "draft")]) < BUFFER_QUEUE_LIMIT
            instagram = candidate
        entry["detail"] = "YouTube and Instagram connected" if instagram else "YouTube connected"
    if not run.stages[-1]["ok"] or not youtube_ready or (config["require_instagram"] and instagram is None):
        return
    if not config["require_instagram"] and os.environ.get("BUFFER_INSTAGRAM_CHANNEL_ID", "").strip():
        # A future Instagram connection must be named explicitly and found in this Buffer organization.
        # A bad optional destination is reported but cannot hold a certified YouTube release.
        with run.stage("optional Instagram destination") as entry:
            instagram = instagram_channel_id()
            entry["detail"] = "Instagram connected"
        if not run.stages[-1]["ok"]:
            instagram = None
    eps = auto.episodes()
    for episode in eps:
        folder = episode["folder"]
        if episode["state"] == "waiting" and (folder / INDEPENDENT_REVIEW).exists() and not (folder / CERTIFICATE).exists():
            with run.stage(f"certify independent review of {episode['id']}") as entry:
                cert = certify(folder)
                entry["detail"] = cert["media_sha256"]
    missing = [e["id"] for e in eps if e["state"] == "waiting" and not (e["folder"] / CERTIFICATE).exists()]
    if missing:
        run.notes.append(f"uncertified waiting drafts remain held: {', '.join(missing)}")
    # Release one YouTube post per run, pairing its Reel when Instagram is required and has room.
    waiting = [e for e in eps if e["state"] == "waiting" and (e["folder"] / CERTIFICATE).exists()][:1]
    if config["require_instagram"] and not instagram_room and waiting:
        run.notes.append("Instagram Buffer queue is full; certified drafts remain held")
        waiting = []
    scheduled = []
    if instagram:
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
            if instagram:
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
            youtube_due = _due(record.get("due_at"), "YouTube post")
            if exact:
                post = exact[0]
                if post["status"] in ("error", "draft"):
                    raise RuntimeError(f"matching Instagram post {post['id']} is {post['status']}")
                accepted_due = _due(post.get("dueAt"), "matching Instagram post")
                if not youtube_due <= accepted_due <= youtube_due + MAX_INSTAGRAM_RETRY:
                    raise RuntimeError(f"Instagram post {post['id']} has an unrelated due time")
                remote = publish.post(post["id"])
                if not remote or remote.get("video") != cert["media_url"] or remote.get("text") != caption(spec):
                    raise RuntimeError(f"Instagram post {post['id']} has unverified media or text")
                publish.verify_hosted_media(cert["media_url"], cert["media_sha256"])
                result = {"id": post["id"], "status": post["status"], "due_at": post.get("dueAt")}
            else:
                if not config["require_instagram"] and youtube_due < datetime.now(timezone.utc) - MAX_INSTAGRAM_RETRY:
                    entry["detail"] = "Instagram retry window elapsed; no Reel created"
                    continue
                if len([p for p in recent if p["status"] not in ("sent", "error", "draft")]) >= BUFFER_QUEUE_LIMIT:
                    raise RuntimeError("Instagram Buffer queue is full")
                due = _instagram_due(youtube_due, recent, datetime.now(timezone.utc))
                result = publish.crosspost(spec_path, "instagram", instagram, cert["media_url"],
                                           due, autonomous_release=True)
            record.setdefault("crossposts", {})["instagram"] = result
            (e["folder"] / "publish.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            entry["detail"] = f"Instagram post {result['id']}"
