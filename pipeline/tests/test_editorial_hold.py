import json
from pathlib import Path

import pytest

from ytc import auto, cloud, publish, studio


def test_editorial_hold_excludes_waiting_episode_from_inventory_and_scheduling(tmp_path, monkeypatch):
    folder = tmp_path / "ep026"
    folder.mkdir()
    (folder / "hold.json").write_text(json.dumps({"id": "ep026", "media_url": "https://cdn/example.mp4"}))
    (folder / "editorial_hold.json").write_text(json.dumps({"reason": "claim needs review"}))
    monkeypatch.setattr(auto, "EPISODES", tmp_path)
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer should not be called"))

    episode = auto.episodes()[0]
    assert episode["state"] == "editorial_hold"
    assert auto.inventory([episode])["total"] == 0
    auto.publish_waiting(auto.Run("test"))


def test_editorial_hold_blocks_direct_schedule_before_external_calls(tmp_path, monkeypatch):
    folder = tmp_path / "ep026"
    folder.mkdir()
    spec = folder / "short.yaml"
    (folder / "editorial_hold.json").write_text("{}")
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", tmp_path / "no-channel-hold.json")
    with pytest.raises(RuntimeError, match="editorial hold"):
        publish.schedule(spec)


def test_editorial_hold_overrides_stale_scheduled_record(tmp_path, monkeypatch):
    folder = tmp_path / "ep026"
    folder.mkdir()
    (folder / "publish.json").write_text(json.dumps({"status": "scheduled", "buffer_post_id": "example"}))
    (folder / "editorial_hold.json").write_text(json.dumps({"reason": "claim needs review"}))
    monkeypatch.setattr(auto, "EPISODES", tmp_path)
    assert auto.episodes()[0]["state"] == "editorial_hold"


def test_editorial_hold_skips_unfinished_retry_without_stopping_other_jobs(tmp_path, monkeypatch):
    held = tmp_path / "ep056"
    ordinary = tmp_path / "ep057"
    for folder in (held, ordinary):
        folder.mkdir()
        (folder / "topic.json").write_text(json.dumps({"topic": folder.name, "series": "The Last Hours",
                                                        "attempts": 0}))
    # Presence is the lock, even if its explanation cannot be parsed.
    (held / "editorial_hold.json").write_text("{invalid")
    monkeypatch.setattr(auto, "EPISODES", tmp_path)
    monkeypatch.setattr(auto, "choose_topics", lambda count, eps: [])
    monkeypatch.setattr(studio, "reject", lambda *args: pytest.fail("held episode must not be rejected"))

    jobs = auto._jobs(2)

    assert [job["id"] for job in jobs] == ["ep057"]
    assert auto.episodes()[0]["state"] == "editorial_hold"
    assert json.loads((held / "topic.json").read_text())["attempts"] == 0


def test_editorial_hold_blocks_direct_production_before_attempt_changes(tmp_path, monkeypatch):
    folder = tmp_path / "ep056"
    folder.mkdir()
    topic = folder / "topic.json"
    topic.write_text(json.dumps({"topic": "story", "series": "The Last Hours", "attempts": 1}))
    (folder / "editorial_hold.json").write_text("{}")
    monkeypatch.setattr(studio, "EPISODES", tmp_path)

    with pytest.raises(RuntimeError, match="editorial hold"):
        studio.produce("story", "The Last Hours", "ep056")

    assert json.loads(topic.read_text())["attempts"] == 1
    assert not (folder / "research.json").exists()


def test_editorial_hold_added_after_job_selection_stops_worker_spawn(tmp_path, monkeypatch):
    held = tmp_path / "ep056"
    ordinary = tmp_path / "ep057"
    for folder in (held, ordinary):
        folder.mkdir()
        (folder / "topic.json").write_text(json.dumps({"topic": folder.name, "series": "The Last Hours"}))
    (held / "editorial_hold.json").write_text("{}")
    monkeypatch.setattr(auto, "EPISODES", tmp_path)
    started = []
    monkeypatch.setattr(cloud, "spawn", lambda root, job: started.append(job["id"]) or "worker-1")
    run = auto.Run("test")
    run.stages.append({"name": "deploy", "ok": True})
    jobs = [{"id": folder.name, "topic": folder.name, "series": "The Last Hours", "at": None}
            for folder in (held, ordinary)]

    auto._spawn(run, jobs)

    assert started == ["ep057"]
    assert not (held / "remote.json").exists()
    assert (ordinary / "remote.json").exists()


def test_editorial_hold_keeps_running_worker_collectable(tmp_path, monkeypatch):
    folder = tmp_path / "ep056"
    folder.mkdir()
    (folder / "topic.json").write_text(json.dumps({"topic": "story", "series": "The Last Hours"}))
    (folder / "remote.json").write_text(json.dumps({"call_id": "worker-1", "key": "worker-1",
                                                    "spawned_at": auto._now().isoformat(), "topic": "story"}))
    (folder / "editorial_hold.json").write_text("{}")
    monkeypatch.setattr(auto, "EPISODES", tmp_path)
    collected = []

    def receive(root, episode_id, call_id, key):
        collected.append((episode_id, call_id, key))
        (folder / "hold.json").write_text(json.dumps({"id": episode_id, "media_url": "https://cdn/example.mp4"}))
        return {"id": episode_id, "outcome": "ready", "topic": "story"}

    monkeypatch.setattr(cloud, "collect", receive)
    monkeypatch.setattr(cloud, "sweep", lambda waiting: 0)
    monkeypatch.setattr(auto, "_finish_topic", lambda *args: None)

    assert auto.episodes()[0]["state"] == "remote"
    auto.collect(auto.Run("test"))

    assert collected == [("ep056", "worker-1", "worker-1")]
    assert not (folder / "remote.json").exists()
    assert auto.episodes()[0]["state"] == "editorial_hold"
