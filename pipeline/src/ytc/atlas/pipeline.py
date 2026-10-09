"""The Atlas lane's producer: pick a topic, snapshot its data, write and check the script, render, and park the
video for the publisher.

Each Short lives in content/atlas/<id>/ with atlas.yaml (the script), data.json (the exact numbers it was checked
against), ready.json once its video is parked in the Modal outbox, and publish.json once the publisher has
scheduled it. The catalogue is strategy/ATLAS-TOPICS.json.

The producer never holds the Buffer or Cloudinary keys. The publisher (`control/atlas.py` in
ashivam-dot/history-last-hours-control) reads ready.json from this repo, fetches the parked video, schedules it, and
records the post in its own atlas/published.json, which `sync` copies back here.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from . import quality, topics, writer
from .cinema import film
from .data import Dataset, fetch
from .episode import AtlasEpisode

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[4]
TOPICS = ROOT / "strategy" / "ATLAS-TOPICS.json"
EPISODES = ROOT / "content" / "atlas"
BULKY = ("short.mp4", "mix.wav", "mix_raw.wav", "mix_tamed.wav", "narration.wav", "work", ".sfx", "globe.mp4",
         ".stage", "stills")
OUTBOX_VOLUME = "creature-receipts-outbox"
# Rendered Shorts kept waiting for the publisher: more than a day of SLOTS, so a failed run costs no post.
RESERVE = 4
PUBLISHED_URL = ("https://raw.githubusercontent.com/ashivam-dot/history-last-hours-control/main/"
                 "atlas/published.json")
EPISODE_ID = re.compile(r"atlas\d{3,}")
# While this file ({"reason": ...}) exists the producer only syncs and refreshes numbers; it renders nothing.
HOLD = ROOT / "status" / "atlas_hold.json"


def outbox() -> Path:
    return Path(os.environ.get("ATLAS_OUTBOX", "/outbox"))


def places_cache() -> Path:
    """Country flags and photos, shared by every Short: on the Modal cache volume, or the repo's .cache on a Mac."""
    if found := os.environ.get("ATLAS_PLACES"):
        return Path(found)
    return Path("/cache/atlas-places") if Path("/cache").is_dir() else ROOT / ".cache" / "atlas-places"


def _catalogue() -> dict:
    return json.loads(TOPICS.read_text(encoding="utf-8"))


def _mark(topic_id: str, status: str) -> None:
    cat = _catalogue()
    for t in cat["topics"]:
        if t["id"] == topic_id:
            t["status"] = status
    TOPICS.write_text(json.dumps(cat, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def _topic_of(episode_id: str) -> dict | None:
    return next((t for t in _catalogue()["topics"]
                 if t.get("status", "").split(":", 1)[-1] == episode_id), None)


def next_id() -> str:
    numbers = [int(m.group(1)) for p in EPISODES.glob("atlas*") if (m := re.match(r"atlas(\d{3,})(?:-|$)", p.name))]
    return f"atlas{max(numbers, default=0) + 1:03d}"


class Implausible(Exception):
    """The independent audit found values in a dataset that are very likely wrong."""


def family(topic: dict) -> str:
    if topic.get("family"):
        return topic["family"]
    indicator = topic["dataset"].get("indicator", "")
    prefix = indicator.split(".")[0]
    return {"SP": "population", "SH": "health", "IT": "technology", "AG": "nature", "EN": "nature",
            "EG": "infrastructure", "ER": "nature", "SL": "work", "SE": "education"}.get(prefix, "economy")


def pick() -> dict | None:
    catalogue = _catalogue()["topics"]
    candidates = [t for t in catalogue if t.get("status") == "open"]
    if not candidates:
        return None
    recent = sorted((t for t in catalogue if re.search(r"atlas\d{3,}$", t.get("status", ""))),
                    key=lambda t: int(t["status"].split("atlas")[-1]), reverse=True)[:3]
    # Balance topic families (editorial variety, not a claim of algorithmic advantage); within that, topics marked
    # with a higher priority (everyday-life stories) go first.
    return min(candidates, key=lambda t: (sum(family(old) == family(t) for old in recent), -t.get("priority", 0)))


def make(topic: dict, episode_id: str) -> tuple[AtlasEpisode, Path, Dataset, Path]:
    folder = EPISODES / episode_id
    folder.mkdir(parents=True, exist_ok=True)
    data_path = folder / "data.json"
    if data_path.exists():
        ds = Dataset.load(data_path)
        if not ds.source_response_sha256:
            # Legacy snapshots did not retain response provenance. Fetch it, don't fabricate a hash.
            ds = fetch(topic["dataset"])
            ds.save(data_path)
    else:
        ds = fetch(topic["dataset"])
        suspect = topics.audit_dataset(ds, topic["dataset"].get("label", topic["topic"]),
                                       ds.definition or writer.definition(topic["dataset"]))
        quality.save(folder / "dataset-audit.json", {"warnings": suspect,
                     "policy": "model memory is advisory; unsupported suspicions cannot overrule official data"})
        ds.save(data_path)
    spec_path = folder / "atlas.yaml"
    if spec_path.exists():
        ep = AtlasEpisode.load(spec_path)
    else:
        ep = writer.write({**topic, "definition_text": ds.definition or writer.definition(topic["dataset"])}, ds, episode_id,
                          series=topic.get("series", ""))
        ep.save(spec_path)
    for media_attempt in range(2):
        # Reused and speech-repaired scripts must pass the full factual gate too.
        for attempt in range(3):
            try:
                quality.review(ep, ds, folder)
                break
            except ValueError as error:
                if attempt == 2:
                    raise
                fixed_topic = {**topic, "angle": topic.get("angle", "") +
                               "\nMandatory factual corrections from the reviewer: " + str(error),
                               "definition_text": ds.definition or writer.definition(topic["dataset"])}
                ep = writer.write(fixed_topic, ds, episode_id, series=topic.get("series", ""))
                ep.save(spec_path)
        video = film.render(ep, folder, places_cache())
        try:
            quality.media(ep, folder, video)
        except ValueError as error:
            if media_attempt or not str(error).startswith("encoded speech material mismatch:"):
                raise
            quality.save(folder / "speech-repair.json", {"error": str(error),
                         "rejected_script_sha256": quality.digest(spec_path),
                         "rejected_media_sha256": quality.digest(video)})
            fixed_topic = {**topic, "angle": topic.get("angle", "") +
                "\nThe encoded narration failed speech recognition: " + str(error) +
                "\nUse simpler, clearly spoken wording. Replace a confusing country example with another "
                "country from the supplied data supporting the same insight. Avoid the misheard name entirely; "
                "do not invent phonetic spellings or change units, years or factual meaning.",
                "definition_text": ds.definition or writer.definition(topic["dataset"])}
            ep = writer.write(fixed_topic, ds, episode_id, series=topic.get("series", ""))
            ep.save(spec_path)
            continue
        return ep, folder, ds, video


def _tidy(folder: Path) -> None:
    for name in BULKY:
        path = folder / name
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)


def park(ep: AtlasEpisode, folder: Path, video: Path, topic_id: str) -> dict:
    """Copy the video into the outbox under its hash and record where it is in ready.json."""
    with video.open("rb") as fh:
        sha = hashlib.file_digest(fh, "sha256").hexdigest()
    rel = f"atlas/{ep.id}-{sha}.mp4"
    target = outbox() / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(video, target)
    with target.open("rb") as fh:
        if hashlib.file_digest(fh, "sha256").hexdigest() != sha:
            raise RuntimeError(f"{ep.id}: the parked copy differs from the render")
    quality.verify(folder, sha)
    record = {"qa_sha256": quality.digest(folder / "qa.json"), "id": ep.id, "title": ep.title, "topic": topic_id, "media_sha256": sha, "bytes": target.stat().st_size,
              "modal_volume": OUTBOX_VOLUME, "modal_path": rel,
              "rendered_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (folder / "ready.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    _tidy(folder)
    return record


def _waiting() -> list[Path]:
    return sorted(p.parent for p in EPISODES.glob("atlas*/ready.json")
                  if EPISODE_ID.fullmatch(p.parent.name) and not (p.parent / "publish.json").exists())


def _accepted(folder: Path) -> bool:
    try:
        record = json.loads((folder / "ready.json").read_text())
        if record["id"] != folder.name or record["modal_volume"] != OUTBOX_VOLUME:
            return False
        if record.get("qa_sha256") != quality.digest(folder / "qa.json"):
            return False
        quality.verify(folder, record["media_sha256"])
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False


def ready() -> list[Path]:
    """Only accepted inventory counts toward the reserve; legacy markers cannot hide starvation."""
    return [folder for folder in _waiting() if _accepted(folder)]


def published() -> dict:
    try:
        response = requests.get(PUBLISHED_URL, timeout=30)
        if response.status_code == 404:
            return {}
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as err:
        log.warning("couldn't read the publisher's records: %s", err)
        return {}


def sync(records: dict | None = None) -> list[str]:
    """Mirror each post the publisher made into its Short's publish.json and mark the topic used. The parked video
    is freed only once the post has gone out, so the publisher can still retry a post Buffer failed to send."""
    changed = []
    for episode_id, record in (records if records is not None else published()).items():
        folder = EPISODES / episode_id
        if not EPISODE_ID.fullmatch(episode_id) or not folder.is_dir():
            continue
        path = folder / "publish.json"
        text = json.dumps(record, indent=2) + "\n"
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            changed.append(episode_id)
        if (topic := _topic_of(episode_id)) and topic["status"] != f"used:{episode_id}":
            _mark(topic["id"], f"used:{episode_id}")
        parked = folder / "ready.json"
        if record.get("status") == "sent" and parked.exists():
            (outbox() / json.loads(parked.read_text(encoding="utf-8"))["modal_path"]).unlink(missing_ok=True)
    return changed


def _pending() -> tuple[str, dict] | None:
    """A Short that was started (topic marked making:<id>) but never parked."""
    for t in _catalogue()["topics"]:
        status = t.get("status", "")
        if status.startswith(("making:", "retry:")):
            episode_id = status.split(":", 1)[1]
            if not (EPISODES / episode_id / "ready.json").exists():
                return episode_id, t
    return None


def make_next() -> dict:
    if found := _pending():
        episode_id, topic = found
    else:
        topic = pick()
        if topic is None:
            return {"outcome": "no_topics"}
        episode_id = next_id()
        _mark(topic["id"], f"making:{episode_id}")
    now = datetime.now(timezone.utc)
    try:
        ep, folder, _, video = make(topic, episode_id)
        record = park(ep, folder, video, topic["id"])
    except Implausible as err:
        log.warning("%s: skipping topic %s, its data looks wrong: %s", episode_id, topic["id"], err)
        _mark(topic["id"], "skipped:implausible")
        shutil.rmtree(EPISODES / episode_id, ignore_errors=True)
        return {"outcome": "skipped", "id": episode_id, "topic": topic["id"], "error": str(err)[:400]}
    except Exception as err:
        log.exception("%s failed", episode_id)
        if isinstance(err, requests.RequestException):
            cat = _catalogue()
            saved_topic = next(t for t in cat["topics"] if t["id"] == topic["id"])
            count = saved_topic.get("source_retries", 0) + 1
            saved_topic.update(source_retries=count, status=f"retry:{episode_id}" if count < 3 else "failed:source")
            TOPICS.write_text(json.dumps(cat, indent=1) + "\n")
            if count < 3:
                return {"outcome": "failed", "id": episode_id, "topic": topic["id"], "error": "transient source failure; retry retained"}
        _mark(topic["id"], f"failed:{type(err).__name__}")
        failed = EPISODES / episode_id
        if failed.exists():
            _tidy(failed)
            (failed / "failed.json").write_text(json.dumps({"topic": topic["id"], "error": str(err)[:800]}),
                                                encoding="utf-8")
            failed.rename(failed.with_name(f"{episode_id}-failed-{now:%Y%m%d%H%M}"))
        return {"outcome": "failed", "id": episode_id, "topic": topic["id"], "error": str(err)[:400]}
    _mark(topic["id"], f"ready:{episode_id}")
    return {"outcome": "ready", "id": episode_id, "topic": topic["id"], "title": ep.title, "bytes": record["bytes"]}


def run(reserve: int = RESERVE, minutes: float = 40, max_failures: int = 2) -> dict:
    """One producer run: sync the publisher's posts, refresh their numbers, top up the topics, then render until
    `reserve` Shorts are waiting."""
    from . import stats

    started = time.monotonic()
    synced = sync()
    if HOLD.exists():
        reason = json.loads(HOLD.read_text(encoding="utf-8")).get("reason") or "held"
        numbers = stats.update(EPISODES, ROOT)
        return {"outcome": "held", "reason": reason, "synced": synced, "tracked": len(numbers)}
    # Upgrade old waiting videos through the same checks instead of grandfathering unverified media.
    for folder in _waiting():
        if _accepted(folder):
            continue
        topic = _topic_of(folder.name)
        if topic is None:
            continue
        try:
            ep, upgraded, _, video = make(topic, folder.name)
            park(ep, upgraded, video, topic["id"])
        except Exception as error:
            log.exception("legacy upgrade rejected %s", folder.name)
            _mark(topic["id"], "open")
            legacy_ready = folder / "ready.json"
            if legacy_ready.exists():
                (outbox() / json.loads(legacy_ready.read_text())["modal_path"]).unlink(missing_ok=True)
                legacy_ready.unlink()
            _tidy(folder)
            folder.rename(folder.with_name(f"{folder.name}-retired-{datetime.now(timezone.utc):%Y%m%d%H%M%S}"))
        if time.monotonic() - started > minutes * 30:
            break
    numbers = stats.update(EPISODES, ROOT)
    added = []
    try:
        cat = _catalogue()
        if added := topics.refill(cat, numbers):
            TOPICS.write_text(json.dumps(cat, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as err:  # a failed refill mustn't stop today's renders
        log.exception("topic refill failed: %s", err)
    made, failed, skipped = [], [], []
    while len(ready()) < reserve and time.monotonic() - started < minutes * 60 and len(failed) < max_failures:
        result = make_next()
        if result["outcome"] == "no_topics":
            break
        {"ready": made, "skipped": skipped}.get(result["outcome"], failed).append(result)
    waiting = [p.name for p in ready()]
    outcome = "failed" if failed and not waiting else ("no_topics" if not waiting else "ok")
    return {"outcome": outcome, "synced": synced, "made": made, "failed": failed, "skipped": skipped, "waiting": waiting,
            "new_topics": [t["id"] for t in added], "tracked": len(numbers),
            "open_topics": sum(t.get("status") == "open" for t in _catalogue()["topics"])}
