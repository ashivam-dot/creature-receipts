from datetime import datetime
from pathlib import Path
import subprocess

import pytest

from ytc import auto, cloud, publish


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


def test_channel_hold_blocks_queued_post_edits_and_automatic_repairs(tmp_path, monkeypatch):
    marker = tmp_path / "scheduling_hold.json"
    marker.write_text('{"reason":"editorial review"}')
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", marker)
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("Buffer should not be mutated"))
    monkeypatch.setattr(auto, "episodes", lambda: pytest.fail("inventory should not be queried"))

    with pytest.raises(RuntimeError, match="New scheduling is on editorial hold"):
        publish.edit_post("queued-post", None, "https://cdn/video.mp4")
    run = auto.Run("test")
    auto.repair_posts(run)
    auto.preflight_posts(run)


def test_channel_hold_stops_watchdog_resends_before_buffer_read(tmp_path, monkeypatch):
    marker = tmp_path / "scheduling_hold.json"
    marker.write_text('{}')
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", marker)
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer should not be read"))
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("Buffer should not be mutated"))

    assert publish.resend_failed() == []
    with pytest.raises(RuntimeError, match="New scheduling is on editorial hold"):
        publish.resend({"id": "failed-post"}, datetime.now(publish.AUDIENCE_TZ))


def test_channel_hold_stops_crossposts_before_buffer_calls(tmp_path, monkeypatch):
    marker = tmp_path / "scheduling_hold.json"
    marker.write_text('{}')
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", marker)
    monkeypatch.setattr(publish, "crosspost_channels", lambda: pytest.fail("channels should not be read"))
    monkeypatch.setattr(auto, "episodes", lambda: pytest.fail("inventory should not be read"))
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("Buffer should not be mutated"))

    auto.crosspost_scheduled(auto.Run("test"))
    with pytest.raises(RuntimeError, match="New scheduling is on editorial hold"):
        publish.crosspost(tmp_path / "short.yaml", "tiktok", "channel", "https://cdn/video.mp4",
                          datetime.now(publish.AUDIENCE_TZ))


def test_episode_hold_blocks_direct_crosspost_before_buffer_call(tmp_path, monkeypatch):
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", tmp_path / "no-channel-hold.json")
    episode = tmp_path / "ep026"
    episode.mkdir()
    (episode / "editorial_hold.json").write_text('{}')
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("Buffer should not be mutated"))

    with pytest.raises(RuntimeError, match="ep026 is on editorial hold"):
        publish.crosspost(episode / "short.yaml", "tiktok", "channel", "https://cdn/video.mp4",
                          datetime.now(publish.AUDIENCE_TZ))


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def hold_repo(tmp_path, monkeypatch):
    repo = tmp_path / "source"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True, capture_output=True)
    _git(repo, "config", "user.name", "History test")
    _git(repo, "config", "user.email", "history-test@example.invalid")
    (repo / "README").write_text("test repository")
    _git(repo, "add", "README")
    _git(repo, "commit", "-q", "-m", "initial")
    monkeypatch.setenv("YTC_DEPLOY_KEY", "test-only-key")
    monkeypatch.setattr(cloud, "REPO_URL", str(repo))
    marker = tmp_path / "slot" / "status" / "scheduling_hold.json"
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", marker)
    return repo, marker


def test_slot_watcher_reads_repo_hold_into_local_lock(hold_repo, monkeypatch):
    repo, marker = hold_repo
    (repo / "status").mkdir()
    (repo / "status" / "scheduling_hold.json").write_text('{"reason":"Independent review pending"}')
    _git(repo, "add", "status/scheduling_hold.json")
    _git(repo, "commit", "-q", "-m", "place hold")
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer should not be read"))

    assert cloud._refresh_slot_hold()
    assert marker.exists()
    assert publish.resend_failed() == []


def test_slot_watcher_clears_lock_only_after_successful_clone_with_no_hold(hold_repo):
    _, marker = hold_repo
    marker.parent.mkdir(parents=True)
    marker.write_text('{"reason":"review pending"}')

    assert not cloud._refresh_slot_hold()
    assert not marker.exists()


def test_slot_watcher_keeps_resends_paused_when_clone_fails(hold_repo, monkeypatch, tmp_path):
    _, marker = hold_repo
    monkeypatch.setattr(cloud, "REPO_URL", str(tmp_path / "missing-private-repo"))
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer should not be read"))

    with pytest.raises(RuntimeError, match="resends remain paused"):
        cloud._refresh_slot_hold()
    assert marker.exists()
    assert publish.resend_failed() == []


def test_slot_watcher_keeps_resends_paused_when_hold_json_is_invalid(hold_repo, monkeypatch):
    repo, marker = hold_repo
    (repo / "status").mkdir()
    (repo / "status" / "scheduling_hold.json").write_text('{"reason":')
    _git(repo, "add", "status/scheduling_hold.json")
    _git(repo, "commit", "-q", "-m", "invalid hold")
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer should not be read"))

    with pytest.raises(RuntimeError, match="resends remain paused"):
        cloud._refresh_slot_hold()
    assert marker.exists()
    assert publish.resend_failed() == []
