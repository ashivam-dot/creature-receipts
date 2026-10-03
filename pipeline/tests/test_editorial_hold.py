import json
from pathlib import Path

import pytest

from ytc import auto, publish


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
