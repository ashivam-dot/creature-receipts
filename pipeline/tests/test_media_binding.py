"""A hosted hold can only schedule the local render and copy that created it."""

import hashlib
import json
from datetime import datetime, timedelta

import pytest

from ytc import auto, publish


@pytest.fixture
def episode(tmp_path, monkeypatch):
    folder = tmp_path / "ep026"
    (folder / "work").mkdir(parents=True)
    spec = folder / "short.yaml"
    spec.write_text("id: ep026\ntitle: Original title\nseries: The Last Hours\nbeats:\n  - text: A true story.\n")
    (folder / "ep026.mp4").write_bytes(b"original rendered video")
    (folder / "work" / "manifest.json").write_text(json.dumps({"beats": [{"asset": {"source": "generated gradient"}}]}))
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", tmp_path / "no-channel-hold.json")
    monkeypatch.setattr(publish, "host_video", lambda path, public_id: f"https://cdn.example/{public_id}.mp4")
    return folder


def _hosted(episode):
    return publish.hold(episode / "short.yaml", {"scores": {"hook": 8}})


def test_hold_binds_exact_local_media_spec_and_manifest(episode):
    held = _hosted(episode)
    assert json.loads((episode / "work" / "manifest.json").read_text())["video_sha256"] == held["media_sha256"]
    for field, path in (("media_sha256", episode / "ep026.mp4"), ("spec_sha256", episode / "short.yaml"),
                        ("manifest_sha256", episode / "work" / "manifest.json")):
        assert held[field] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert held["media_public_id"].endswith(held["media_sha256"][:8])
    assert json.loads((episode / "hold.json").read_text()) == held


@pytest.mark.parametrize("file,change", [
    ("ep026.mp4", b"repaired rendered video"),
    ("short.yaml", b"id: ep026\ntitle: Repaired title\nseries: The Last Hours\nbeats:\n  - text: A true story.\n"),
    ("work/manifest.json", b'{"beats": [{"asset": {"source": "designed card"}}]}'),
])
def test_changed_local_file_cannot_schedule_old_hosted_video(episode, monkeypatch, file, change):
    _hosted(episode)
    (episode / file).write_bytes(change)
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer was contacted"))
    with pytest.raises(RuntimeError, match="hosted video is stale"):
        publish.schedule(episode / "short.yaml")
    assert (episode / "hold.json").exists() and not (episode / "publish.json").exists()


def test_legacy_unbound_hold_is_rejected_before_buffer(episode, monkeypatch):
    (episode / "hold.json").write_text(json.dumps({"media_public_id": "old", "media_url": "https://cdn.example/old.mp4"}))
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer was contacted"))
    with pytest.raises(RuntimeError, match="unbound hosted video"):
        publish.schedule(episode / "short.yaml")


def test_superseded_hold_is_out_of_inventory_and_cannot_schedule(episode, monkeypatch):
    held = _hosted(episode)
    held["superseded"] = True
    (episode / "hold.json").write_text(json.dumps(held))
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer was contacted"))
    found = auto.episodes()[0]
    assert found["state"] == "superseded"
    assert auto.inventory()["total"] == auto.inventory()["waiting"] == 0
    auto.publish_waiting(auto.Run("test"))
    with pytest.raises(RuntimeError, match="superseded hosted video"):
        publish.schedule(episode / "short.yaml")


def test_scheduling_bound_hold_carries_binding_to_publish_record(episode, monkeypatch):
    held = _hosted(episode)
    # Worker handoff keeps the manifest and hold, but deliberately omits the MP4.
    (episode / "ep026.mp4").unlink()
    monkeypatch.setattr(publish, "posts", lambda **kwargs: [])
    monkeypatch.setattr(publish, "youtube_channel_id", lambda: "youtube")
    monkeypatch.setattr(publish, "_buffer", lambda query, variables: {"createPost": {
        "__typename": "PostActionSuccess", "post": {"id": "p1", "status": "scheduled"}}})
    when = datetime.now(publish.AUDIENCE_TZ) + timedelta(days=1)
    record = publish.schedule(episode / "short.yaml", when)
    assert record["media_url"] == held["media_url"]
    assert {k: record[k] for k in publish.MEDIA_BINDING_FIELDS} == {k: held[k] for k in publish.MEDIA_BINDING_FIELDS}
    assert not (episode / "hold.json").exists()
    assert json.loads((episode / "publish.json").read_text()) == record


def test_manifest_render_hash_change_blocks_hold_without_local_video(episode, monkeypatch):
    _hosted(episode)
    (episode / "ep026.mp4").unlink()
    path = episode / "work" / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["video_sha256"] = "0" * 64
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer was contacted"))
    with pytest.raises(RuntimeError, match="hosted video is stale"):
        publish.schedule(episode / "short.yaml")


def test_failed_post_requeue_preserves_binding(episode, monkeypatch):
    held = _hosted(episode)
    (episode / "hold.json").unlink()
    record = {**held, "status": "error", "buffer_post_id": "p1", "error": "Buffer failed"}
    (episode / "publish.json").write_text(json.dumps(record))
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.setattr(publish, "shrink_hosted", lambda *args: pytest.fail("bound media must not be re-encoded"))
    monkeypatch.setattr(publish, "hosted_bytes", lambda url: 123)
    monkeypatch.setattr(publish, "delete_post", lambda post_id: None)
    auto.repair_posts(auto.Run("test"))
    requeued = json.loads((episode / "hold.json").read_text())
    assert {k: requeued[k] for k in publish.MEDIA_BINDING_FIELDS} == {k: held[k] for k in publish.MEDIA_BINDING_FIELDS}
    assert not (episode / "publish.json").exists()


@pytest.mark.parametrize("state", ["waiting", "scheduled"])
def test_oversize_bound_media_is_not_shrunk(episode, monkeypatch, state):
    held = _hosted(episode)
    if state == "scheduled":
        (episode / "hold.json").unlink()
        record = {**held, "status": "scheduled", "buffer_post_id": "p1"}
        path = episode / "publish.json"
    else:
        record = held
        path = episode / "hold.json"
    path.write_text(json.dumps(record))
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.setattr(publish, "hosted_bytes", lambda url: 41_000_000)
    monkeypatch.setattr(publish, "shrink_hosted", lambda *args: pytest.fail("bound media must not be re-encoded"))
    monkeypatch.setattr(publish, "edit_post", lambda *args: pytest.fail("Buffer must not be edited"))
    monkeypatch.setattr(publish, "unhost_video", lambda *args: pytest.fail("hosted media must not be removed"))
    run = auto.Run("test")
    auto.repair_posts(run)
    assert "automatic shrink would change bound media" in run.errors[0]
    assert json.loads(path.read_text()) == record


def test_oversize_failed_bound_post_is_not_requeued_or_shrunk(episode, monkeypatch):
    held = _hosted(episode)
    (episode / "hold.json").unlink()
    record = {**held, "status": "error", "buffer_post_id": "p1", "error": "Buffer failed"}
    path = episode / "publish.json"
    path.write_text(json.dumps(record))
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.setattr(publish, "hosted_bytes", lambda url: 41_000_000)
    monkeypatch.setattr(publish, "shrink_hosted", lambda *args: pytest.fail("bound media must not be re-encoded"))
    monkeypatch.setattr(publish, "delete_post", lambda *args: pytest.fail("Buffer post must not be deleted"))
    run = auto.Run("test")
    auto.repair_posts(run)
    assert "requeue would require shrinking bound media" in run.errors[0]
    assert json.loads(path.read_text()) == record
    assert not (episode / "hold.json").exists()


def test_missing_buffer_post_returns_bound_hold(episode, monkeypatch):
    held = _hosted(episode)
    (episode / "hold.json").unlink()
    due = datetime.now(publish.AUDIENCE_TZ) + timedelta(hours=1)
    record = {**held, "status": "scheduled", "buffer_post_id": "p1", "due_at": due.isoformat()}
    (episode / "publish.json").write_text(json.dumps(record))
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.setattr(publish, "buffer_busy", lambda: None)
    monkeypatch.setattr(publish, "post", lambda post_id: None)
    auto.preflight_posts(auto.Run("test"))
    requeued = json.loads((episode / "hold.json").read_text())
    assert {k: requeued[k] for k in publish.MEDIA_BINDING_FIELDS} == {k: held[k] for k in publish.MEDIA_BINDING_FIELDS}


def test_anniversary_release_preserves_binding(episode, monkeypatch):
    held = _hosted(episode)
    (episode / "hold.json").unlink()
    day = (datetime.now(publish.AUDIENCE_TZ) + timedelta(days=4)).date()
    due = datetime.combine(day, publish.SLOTS[0], publish.AUDIENCE_TZ)
    record = {**held, "status": "scheduled", "buffer_post_id": "p1", "due_at": due.isoformat()}
    (episode / "publish.json").write_text(json.dumps(record))
    (episode / "topic.json").write_text(json.dumps({"at": day.isoformat()}))
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.setattr(auto, "slots_per_day", lambda today=None: 3)
    monkeypatch.setattr(publish, "delete_post", lambda post_id: None)
    auto.release_anniversaries(auto.Run("test"))
    requeued = json.loads((episode / "hold.json").read_text())
    assert {k: requeued[k] for k in publish.MEDIA_BINDING_FIELDS} == {k: held[k] for k in publish.MEDIA_BINDING_FIELDS}
