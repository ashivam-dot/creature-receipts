"""The disabled-by-default release path binds new drafts to exact media and retries safely."""

import hashlib
import json
from datetime import datetime, timedelta

import pytest

from ytc import auto, publish, release
from ytc.spec import ShortSpec


@pytest.fixture
def episode(tmp_path, monkeypatch):
    folder = tmp_path / "ep063"
    (folder / "work").mkdir(parents=True)
    marker = tmp_path / "scheduling_hold.json"
    marker.write_text('{"reason":"editorial review"}')
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", marker)
    config = tmp_path / "autonomous_release_policy.json"
    config.write_text(json.dumps({"version": 1, "enabled": True, "min_episode_id": "ep063",
                                  "started_after_utc": "2026-10-05T00:00:00+00:00", "require_instagram": True}))
    monkeypatch.setattr(release, "POLICY_PATH", config)
    monkeypatch.setenv("YTC_AUTONOMOUS_RELEASE", "1")
    monkeypatch.setenv("BUFFER_YOUTUBE_CHANNEL_ID", "yt")
    monkeypatch.setenv("BUFFER_INSTAGRAM_CHANNEL_ID", "ig")
    monkeypatch.setattr(publish, "channels", lambda: [
        {"id": "yt", "service": "youtube", "isDisconnected": False},
        {"id": "ig", "service": "instagram", "isDisconnected": False},
    ])
    (folder / "topic.json").write_text(json.dumps({"started_at": "2026-10-05T00:00:00+00:00"}))
    (folder / "short.yaml").write_text("id: ep063\ntitle: The Last Voyage\ndescription: A true story.\n"
                                      "beats:\n  - text: The ship was lost.\n")
    (folder / "script.json").write_text(json.dumps({"beats": [{"text": "The ship was lost.", "claims": [1]}]}))
    (folder / "research.json").write_text(json.dumps({"viable": True,
        "sources": [{"label": "S1", "url": "https://museum.example/story"},
                    {"label": "S2", "url": "https://archive.example/story"}],
        "claims": [{"claim": "The ship was lost.", "sources": ["S1", "S2"],
                    "evidence": [{"source": "S1", "quote": "The ship was lost during the long voyage."},
                                 {"source": "S2", "quote": "The ship was lost while crossing the ocean."}]}]}))
    video = folder / "ep063.mp4"
    video.write_bytes(b"a complete reviewed MP4")
    media_hash = hashlib.sha256(video.read_bytes()).hexdigest()
    (folder / "work" / "manifest.json").write_text(json.dumps({"id": "ep063", "video_sha256": media_hash,
        "beats": [{"text": "The ship was lost.", "asset": {"source": "Wikimedia Commons",
                    "license": "Public domain", "url": "https://commons.example/image", "credit": "Archive"}}]}))
    (folder / "review.json").write_text(json.dumps({"rounds": [{"media_sha256": media_hash, "passed": True,
        "check": {"warnings": [], "speech_differences": [], "speech_error": None},
        "scores": {name: 4 for name in ("hook", "clarity", "payoff", "visuals", "loop")},
        "frames": [], "speech": []}]}))
    binding = publish.media_binding(folder / "short.yaml", "ep063")
    (folder / "hold.json").write_text(json.dumps({"id": "ep063", "title": "The Last Voyage",
        "media_url": "https://cdn.example/ep063.mp4", "media_public_id": "history/ep063", **binding}))
    release.certify(folder)
    monkeypatch.setattr(publish, "verify_hosted_media", lambda url, digest: None)
    return folder


def test_policy_is_dormant_without_both_switches(episode, monkeypatch):
    monkeypatch.delenv("YTC_AUTONOMOUS_RELEASE")
    assert release.policy() is None
    with pytest.raises(RuntimeError, match="inactive"):
        release.validate(episode / "short.yaml")
    monkeypatch.setenv("YTC_AUTONOMOUS_RELEASE", "1")
    config = release.POLICY_PATH
    data = json.loads(config.read_text())
    data["enabled"] = False
    config.write_text(json.dumps(data))
    assert release.policy() is None


@pytest.mark.parametrize("file,change", [
    ("ep063.mp4", b"another video"),
    ("short.yaml", b"id: ep063\ntitle: Rewritten\nbeats:\n  - text: The ship was lost.\n"),
    ("research.json", b"{}"),
    ("review.json", b"{}"),
])
def test_changed_certified_input_blocks_buffer(episode, monkeypatch, file, change):
    (episode / file).write_bytes(change)
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer was contacted"))
    with pytest.raises(RuntimeError):
        publish.schedule(episode / "short.yaml", autonomous_release=True)


def test_source_rights_and_exact_mp4_review_are_required(episode):
    assert release.validate(episode / "short.yaml")["media_sha256"]
    manifest = episode / "work" / "manifest.json"
    data = json.loads(manifest.read_text())
    data["beats"][0]["asset"]["license"] = "CC BY-NC 4.0"
    manifest.write_text(json.dumps(data))
    with pytest.raises(RuntimeError, match="unapproved or missing image rights"):
        release._sources_and_rights(episode)
    data["beats"][0]["asset"]["license"] = "Public domain"
    manifest.write_text(json.dumps(data))
    review = episode / "review.json"
    data = json.loads(review.read_text())
    data["rounds"][0]["check"]["speech_differences"] = ["missing word"]
    review.write_text(json.dumps(data))
    with pytest.raises(RuntimeError, match="clean final-media review"):
        release._review(episode, hashlib.sha256((episode / "ep063.mp4").read_bytes()).hexdigest())


def test_old_drafts_stay_out_even_if_policy_floor_is_lower(episode):
    config = release.POLICY_PATH
    data = json.loads(config.read_text())
    data["min_episode_id"] = "ep050"
    config.write_text(json.dumps(data))
    with pytest.raises(RuntimeError, match="episode floor"):
        release.validate(episode / "short.yaml")


def test_missing_instagram_channel_blocks_youtube(episode, monkeypatch):
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.delenv("BUFFER_INSTAGRAM_CHANNEL_ID")
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer was contacted"))
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert not (episode / "publish.json").exists()
    assert any("BUFFER_INSTAGRAM_CHANNEL_ID" in error for error in run.errors)


def test_youtube_and_instagram_schedule_once_on_repeated_run(episode, monkeypatch):
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.setattr(publish, "posts", lambda **kwargs: [])
    calls = []

    def create(query, variables):
        calls.append(variables["input"]["channelId"])
        return {"createPost": {"__typename": "PostActionSuccess",
                               "post": {"id": f"post-{len(calls)}", "status": "scheduled"}}}

    monkeypatch.setattr(publish, "_buffer", create)
    monkeypatch.setattr(publish, "next_slots", lambda count, taken, **kwargs:
                        [datetime.now(publish.AUDIENCE_TZ) + timedelta(days=1)])
    first = auto.Run("test")
    auto.publish_waiting(first)
    assert first.errors == []
    assert calls == ["yt", "ig"]
    second = auto.Run("test")
    auto.publish_waiting(second)
    assert second.errors == []
    assert calls == ["yt", "ig"]
    record = json.loads((episode / "publish.json").read_text())
    assert record["crossposts"]["instagram"]["id"] == "post-2"


def test_interrupted_youtube_schedule_adopts_only_the_certified_remote_media(episode, monkeypatch):
    spec = ShortSpec.load(episode / "short.yaml")
    manifest = json.loads((episode / "work" / "manifest.json").read_text())
    text = publish.description(spec, manifest)
    remote = {"id": "already-created", "status": "scheduled", "dueAt":
              (datetime.now(publish.AUDIENCE_TZ) + timedelta(days=1)).isoformat(), "text": text}
    monkeypatch.setattr(publish, "posts", lambda **kwargs: [remote])
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("a duplicate was created"))
    monkeypatch.setattr(publish, "post", lambda post_id: {**remote, "video": "https://cdn.example/wrong.mp4"})
    with pytest.raises(RuntimeError, match="unverified media"):
        publish.schedule(episode / "short.yaml", autonomous_release=True)
    assert not (episode / "publish.json").exists()
    monkeypatch.setattr(publish, "post", lambda post_id: {**remote, "video": "https://cdn.example/ep063.mp4"})
    record = publish.schedule(episode / "short.yaml", autonomous_release=True)
    assert record["buffer_post_id"] == "already-created"
    assert not (episode / "hold.json").exists()


def test_interrupted_instagram_schedule_adopts_only_the_certified_remote_media(episode, monkeypatch):
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.setattr(publish, "posts", lambda **kwargs: [])
    monkeypatch.setattr(publish, "_buffer", lambda query, variables: {"createPost": {
        "__typename": "PostActionSuccess", "post": {"id": "yt-post", "status": "scheduled"}}})
    due = datetime.now(publish.AUDIENCE_TZ) + timedelta(days=1)
    publish.schedule(episode / "short.yaml", due, autonomous_release=True)
    text = publish.caption(ShortSpec.load(episode / "short.yaml"))
    remote = {"id": "ig-post", "status": "scheduled", "text": text, "dueAt": due.isoformat()}
    monkeypatch.setattr(publish, "posts", lambda **kwargs: [remote] if kwargs.get("channel_id") == "ig" else [])
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("a duplicate was created"))
    monkeypatch.setattr(publish, "post", lambda post_id: {**remote, "video": "https://cdn.example/wrong.mp4"})
    first = auto.Run("test")
    auto.publish_waiting(first)
    assert any("unverified media" in error for error in first.errors)
    assert "instagram" not in json.loads((episode / "publish.json").read_text()).get("crossposts", {})
    monkeypatch.setattr(publish, "post", lambda post_id: {**remote, "video": "https://cdn.example/ep063.mp4"})
    second = auto.Run("test")
    auto.publish_waiting(second)
    assert second.errors == []
    assert json.loads((episode / "publish.json").read_text())["crossposts"]["instagram"]["id"] == "ig-post"
