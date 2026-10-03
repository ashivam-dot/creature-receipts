import pytest

from ytc import auto, publish


def test_channel_hold_stops_automatic_scheduling_without_buffer_call(tmp_path, monkeypatch):
    marker = tmp_path / "scheduling_hold.json"
    marker.write_text('{"reason": "editorial review"}')
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", marker)
    monkeypatch.setattr(auto, "episodes", lambda: pytest.fail("inventory should not be queried"))
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer should not be called"))

    run = auto.Run("test")
    auto.publish_waiting(run)
    assert "production continues" in run.notes[-1]


def test_channel_hold_blocks_direct_schedule_before_external_calls(tmp_path, monkeypatch):
    marker = tmp_path / "scheduling_hold.json"
    marker.write_text('{}')
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", marker)
    with pytest.raises(RuntimeError, match="New scheduling is on editorial hold"):
        publish.schedule(tmp_path / "short.yaml")
