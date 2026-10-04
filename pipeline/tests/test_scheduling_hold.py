from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from ytc import auto, cloud, publish, release, youtube


def test_channel_hold_stops_automatic_scheduling_without_buffer_call(tmp_path, monkeypatch):
    marker = tmp_path / "scheduling_hold.json"
    marker.write_text('{"reason": "editorial review"}')
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", marker)
    monkeypatch.setattr(auto, "episodes", lambda: pytest.fail("inventory should not be queried"))
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer should not be called"))

    run = auto.Run("test")
    auto.publish_waiting(run)
    assert "automatic production pauses" in run.notes[-1]


@pytest.mark.parametrize("has_hold,policy_active,requested,trigger,expected", [
    (True, False, None, "schedule", None),
    (True, False, 2, "manual", 2),
    (True, False, 2, "schedule", None),
    (True, True, None, "schedule", 4),
    (False, False, None, "schedule", 4),
])
def test_automatic_production_pause_keeps_run_services_and_manual_trials(
        tmp_path, monkeypatch, has_hold, policy_active, requested, trigger, expected):
    marker = tmp_path / "scheduling_hold.json"
    if has_hold:
        marker.write_text('{"reason":"editorial review"}')
    config = tmp_path / "autonomous_release_policy.json"
    config.write_text(json.dumps({"version": 1, "enabled": policy_active, "min_episode_id": "ep063",
                                  "started_after_utc": "2026-10-05T00:00:00+00:00", "require_instagram": True}))
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", marker)
    monkeypatch.setattr(release, "POLICY_PATH", config)
    monkeypatch.setenv("YTC_AUTONOMOUS_RELEASE", "1" if policy_active else "0")
    monkeypatch.setattr(auto, "STATUS", tmp_path / "status")
    monkeypatch.setattr(auto, "EPISODES", tmp_path / "episodes")
    monkeypatch.setattr(auto, "ON_MODAL", False)
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    calls = []
    run_seen = []
    monkeypatch.setattr(publish, "sync", lambda folder: calls.append("sync") or [])
    monkeypatch.setattr(publish, "buffer_busy", lambda: None)
    monkeypatch.setattr(youtube, "file_into_playlists", lambda folder: [])
    monkeypatch.setattr(youtube, "fix_languages", lambda folder: [])
    monkeypatch.setattr(youtube, "check_live", lambda folder: [])
    monkeypatch.setattr(auto, "review_shorts", lambda run: [])
    monkeypatch.setattr(auto, "inventory", lambda eps=None: {"target": 12, "total": 0, "remote": ["ep090"], "making": []})
    monkeypatch.setattr(auto, "episodes", lambda: [])
    monkeypatch.setattr(auto, "calendar_topics", lambda today=None: [])
    monkeypatch.setattr(auto, "collect", lambda run: calls.append("collect") or "collected")
    monkeypatch.setattr(auto, "daily", lambda run, state: calls.append("daily"))
    monkeypatch.setattr(auto, "check_channel", lambda run: True)
    monkeypatch.setattr(auto, "repair_posts", lambda run, requeue=True: calls.append("repair"))
    monkeypatch.setattr(auto, "preflight_posts", lambda run: calls.append("preflight"))
    monkeypatch.setattr(auto, "release_anniversaries", lambda run: calls.append("release anniversaries"))
    monkeypatch.setattr(auto, "publish_waiting", lambda run: calls.append("publish waiting"))
    monkeypatch.setattr(auto, "crosspost_scheduled", lambda run: calls.append("crosspost"))
    monkeypatch.setattr(auto, "produce", lambda run, count: calls.append(("produce", count)))
    monkeypatch.setattr(auto, "_session_note", lambda run, inv: calls.append("session note"))
    monkeypatch.setattr(auto, "write_status", lambda run, result: run_seen.append(run) or {})

    assert auto.main(requested, daily_mode="yes", trigger=trigger) == 0
    assert {"sync", "collect", "daily", "repair", "preflight", "publish waiting", "crosspost", "session note"} <= set(calls)
    assert [call for call in calls if isinstance(call, tuple)] == ([ ("produce", expected) ] if expected else [])
    if has_hold and not policy_active and (requested is None or trigger == "schedule"):
        assert any("automatic production paused" in note for note in run_seen[0].notes)


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


def test_exact_media_release_only_opens_one_direct_schedule(tmp_path, monkeypatch):
    marker = tmp_path / "scheduling_hold.json"
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", marker)
    episode = tmp_path / "ep054"
    (episode / "work").mkdir(parents=True)
    spec = episode / "short.yaml"
    spec.write_text("id: ep054\n")
    video = episode / "ep054.mp4"
    video.write_bytes(b"reviewed media")
    (episode / "work" / "manifest.json").write_text(json.dumps(
        {"id": "ep054", "video_sha256": publish._sha256(video)}))
    monkeypatch.setattr(publish.ShortSpec, "load", lambda path: SimpleNamespace(id="ep054"))
    binding = publish.media_binding(spec, "ep054")
    allowed = {"episode_id": "ep054", **binding,
               "expires_at_utc": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()}
    marker.write_text(json.dumps({"reason": "Editorial review", "block_existing_queue": True,
                                  "release_allowlist": allowed}))

    publish._require_scheduling_open(spec, exact_media_release=True)
    (episode / "hold.json").write_text(json.dumps({**binding, "media_url": "https://cdn.example/ep054.mp4",
                                                   "media_public_id": "creaturereceipts/ep054"}))
    monkeypatch.setattr(publish, "description", lambda *args: "test description")
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("direct schedule reached Buffer read"))
    monkeypatch.setattr(publish, "verify_hosted_media", lambda url, digest: None)
    with pytest.raises(RuntimeError, match="New scheduling is on editorial hold"):
        publish.schedule(spec)
    with pytest.raises(pytest.fail.Exception, match="direct schedule reached Buffer read"):
        publish.schedule(spec, reviewed_release=True)
    monkeypatch.setattr(auto, "episodes", lambda: pytest.fail("auto inventory should not be queried"))
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert "automatic production pauses" in run.notes[-1]
    with pytest.raises(RuntimeError, match="New scheduling is on editorial hold"):
        publish._require_scheduling_open(spec)
    with pytest.raises(RuntimeError, match="New scheduling is on editorial hold"):
        publish._require_scheduling_open()

    for field in publish.MEDIA_BINDING_FIELDS:
        changed = dict(allowed, **{field: "0" * 64})
        marker.write_text(json.dumps({"release_allowlist": changed}))
        with pytest.raises(RuntimeError, match="New scheduling is on editorial hold"):
            publish._require_scheduling_open(spec, exact_media_release=True)
    marker.write_text(json.dumps({"release_allowlist": allowed}))
    (episode / "ep054.mp4").write_bytes(b"changed media")
    with pytest.raises(RuntimeError, match="New scheduling is on editorial hold"):
        publish._require_scheduling_open(spec, exact_media_release=True)
    (episode / "ep054.mp4").unlink()
    with pytest.raises(RuntimeError, match="New scheduling is on editorial hold"):
        publish._require_scheduling_open(spec, exact_media_release=True)


def test_exact_media_release_requires_expiry_and_respects_episode_hold(tmp_path, monkeypatch):
    marker = tmp_path / "scheduling_hold.json"
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", marker)
    episode = tmp_path / "ep054"
    (episode / "work").mkdir(parents=True)
    spec = episode / "short.yaml"
    spec.write_text("id: ep054\n")
    (episode / "ep054.mp4").write_bytes(b"reviewed media")
    (episode / "work" / "manifest.json").write_text('{"id":"ep054"}')
    monkeypatch.setattr(publish.ShortSpec, "load", lambda path: SimpleNamespace(id="ep054"))
    binding = publish.media_binding(spec, "ep054")
    for expiry in ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
                   datetime.now(timezone.utc).replace(tzinfo=None).isoformat(), "invalid"):
        marker.write_text(json.dumps({"release_allowlist": {"episode_id": "ep054", **binding,
                                                           "expires_at_utc": expiry}}))
        with pytest.raises(RuntimeError, match="New scheduling is on editorial hold"):
            publish._require_scheduling_open(spec, exact_media_release=True)
    marker.write_text(json.dumps({"release_allowlist": {"episode_id": "ep054", **binding,
                                                       "expires_at_utc": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()}}))
    (episode / "editorial_hold.json").write_text('{}')
    with pytest.raises(RuntimeError, match="ep054 is on editorial hold"):
        publish._require_scheduling_open(spec, exact_media_release=True)


def test_hosted_bytes_are_checked_before_reviewed_release_reads_buffer(tmp_path, monkeypatch):
    marker = tmp_path / "scheduling_hold.json"
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", marker)
    episode = tmp_path / "ep054"
    (episode / "work").mkdir(parents=True)
    spec = episode / "short.yaml"
    spec.write_text("id: ep054\n")
    video = episode / "ep054.mp4"
    video.write_bytes(b"reviewed media")
    (episode / "work" / "manifest.json").write_text(json.dumps(
        {"id": "ep054", "video_sha256": publish._sha256(video)}))
    monkeypatch.setattr(publish.ShortSpec, "load", lambda path: SimpleNamespace(id="ep054"))
    binding = publish.media_binding(spec, "ep054")
    marker.write_text(json.dumps({"release_allowlist": {"episode_id": "ep054", **binding,
                         "expires_at_utc": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()}}))
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer must not be read"))
    monkeypatch.setattr(publish, "host_video", lambda *args: pytest.fail("Must not host in-line"))
    with pytest.raises(RuntimeError, match="pre-hosted"):
        publish.schedule(spec, reviewed_release=True)
    (episode / "hold.json").write_text(json.dumps({**binding, "media_url": "https://cdn.example/ep054.mp4",
                                                   "media_public_id": "creaturereceipts/ep054"}))
    monkeypatch.setattr(publish, "verify_hosted_media", lambda url, digest: (_ for _ in ()).throw(
        RuntimeError("Hosted video differs from the reviewed media hash")))
    with pytest.raises(RuntimeError, match="Hosted video differs"):
        publish.schedule(spec, reviewed_release=True)


def test_verify_hosted_media_hashes_downloaded_bytes(monkeypatch):
    class Response:
        headers = {"content-type": "video/mp4", "content-length": "14"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def raise_for_status(self):
            pass

        def iter_content(self, size):
            return iter((b"reviewed ", b"media"))

    monkeypatch.setattr(publish.requests, "get", lambda *args, **kwargs: Response())
    digest = hashlib.sha256(b"reviewed media").hexdigest()
    publish.verify_hosted_media("https://cdn.example/ep054.mp4", digest)
    with pytest.raises(RuntimeError, match="differs from the reviewed media hash"):
        publish.verify_hosted_media("https://cdn.example/ep054.mp4", "0" * 64)


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
