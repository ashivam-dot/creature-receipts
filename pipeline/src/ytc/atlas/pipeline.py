"""The Atlas lane end to end: pick a topic, snapshot its data, write and check the script, render, schedule.

Each Short lives in content/atlas/<id>/ with atlas.yaml (the script), data.json (the exact numbers it was checked
against) and publish.json once Buffer has it. The catalogue is strategy/ATLAS-TOPICS.json.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from . import publish, render, writer
from .data import Dataset, fetch
from .episode import AtlasEpisode

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[4]
TOPICS = ROOT / "strategy" / "ATLAS-TOPICS.json"
EPISODES = ROOT / "content" / "atlas"
BULKY = ("short.mp4", "mix.wav", "mix_raw.wav", "narration.wav", "work")
# Without these a run still writes and renders the next Short, then waits for them before making another.
PUBLISH_KEYS = ("BUFFER_API_KEY", "CLOUDINARY_URL")


def _catalogue() -> dict:
    return json.loads(TOPICS.read_text(encoding="utf-8"))


def _mark(topic_id: str, status: str) -> None:
    cat = _catalogue()
    for t in cat["topics"]:
        if t["id"] == topic_id:
            t["status"] = status
    TOPICS.write_text(json.dumps(cat, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def next_id() -> str:
    numbers = [int(m.group(1)) for p in EPISODES.glob("atlas*") if (m := re.fullmatch(r"atlas(\d{3})", p.name))]
    return f"atlas{max(numbers, default=0) + 1:03d}"


def pick() -> dict | None:
    return next((t for t in _catalogue()["topics"] if t.get("status") == "open"), None)


def make(topic: dict, episode_id: str) -> tuple[AtlasEpisode, Path, Dataset, Path]:
    folder = EPISODES / episode_id
    folder.mkdir(parents=True, exist_ok=True)
    data_path = folder / "data.json"
    if data_path.exists():
        ds = Dataset.load(data_path)
    else:
        ds = fetch(topic["dataset"])
        ds.save(data_path)
    spec_path = folder / "atlas.yaml"
    if spec_path.exists():
        ep = AtlasEpisode.load(spec_path)
    else:
        ep = writer.write({**topic, "definition_text": writer.definition(topic["dataset"])}, ds, episode_id,
                          series=topic.get("series", ""))
        ep.save(spec_path)
    video = render.render(ep, folder)
    return ep, folder, ds, video


def _scheduled(now: datetime) -> list[dict]:
    found = []
    for path in EPISODES.glob("atlas*/publish.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("due_at") and datetime.fromisoformat(record["due_at"]) > now:
            found.append(record)
    return found


def _tidy(folder: Path) -> None:
    import shutil

    for name in BULKY:
        path = folder / name
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)


def run(publish_it: bool = True) -> dict:
    """One daily run: make and schedule the next Short unless one is already waiting in Buffer."""
    now = datetime.now(timezone.utc)
    if publish_it and (queued := _scheduled(now)):
        return {"outcome": "queued", "next": queued[0]["id"], "due_at": queued[0]["due_at"]}
    pending = next((p.parent for p in sorted(EPISODES.glob("atlas*/atlas.yaml"))
                    if re.fullmatch(r"atlas\d{3}", p.parent.name) and not (p.parent / "publish.json").exists()), None)
    missing = [k for k in PUBLISH_KEYS if not os.environ.get(k)]
    if publish_it and missing and pending:
        return {"outcome": "no_keys", "missing": missing, "waiting": pending.name}
    publish_it = publish_it and not missing
    if pending:
        episode_id = pending.name
        topic = next(t for t in _catalogue()["topics"] if t.get("status") == f"making:{episode_id}")
    else:
        topic = pick()
        if topic is None:
            return {"outcome": "no_topics"}
        episode_id = next_id()
        _mark(topic["id"], f"making:{episode_id}")
    try:
        ep, folder, ds, video = make(topic, episode_id)
    except Exception as err:
        log.exception("%s failed", episode_id)
        _mark(topic["id"], f"failed:{type(err).__name__}")
        failed = EPISODES / episode_id
        if failed.exists():
            _tidy(failed)
            (failed / "failed.json").write_text(json.dumps({"topic": topic["id"], "error": str(err)[:800]}), encoding="utf-8")
            failed.rename(failed.with_name(f"{episode_id}-failed-{now:%Y%m%d%H%M}"))
        return {"outcome": "failed", "id": episode_id, "topic": topic["id"], "error": str(err)[:400]}
    record = publish.schedule(ep, folder, ds, video) if publish_it else {}
    if publish_it:
        _mark(topic["id"], f"used:{episode_id}")
        _tidy(folder)
    return {"outcome": "scheduled" if publish_it else ("no_keys" if missing else "rendered"), "id": episode_id,
            "topic": topic["id"], "title": ep.title, "video": str(video),
            **({"due_at": record.get("due_at")} if record else {}), **({"missing": missing} if missing else {})}
