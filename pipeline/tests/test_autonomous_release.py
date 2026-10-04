"""The disabled-by-default release path binds new drafts to exact media and retries safely."""

import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ytc import auto, publish, release
from ytc.spec import ShortSpec


@pytest.fixture
def draft(tmp_path, monkeypatch):
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
    (folder / "visuals.json").write_text(json.dumps([{"source": "url",
        "url": "https://commons.example/image", "credit": {"license": "Public domain"}}]))
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
    monkeypatch.setattr(publish, "verify_hosted_media", lambda url, digest: None)
    return folder


def _sign_independent_review(folder, monkeypatch):
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    key_path = folder.parent / "independent-review.pub"
    key_path.write_text(base64.b64encode(public).decode("ascii"))
    monkeypatch.setattr(release, "REVIEW_PUBLIC_KEY_PATH", key_path)
    held = json.loads((folder / "hold.json").read_text())
    files = {name: release._hash(folder / name) for name in release.FILES}
    subject = release._review_subject(folder, held, held["media_sha256"], files)
    review = {"version": 1, "subject": subject,
              "reviewer_key_sha256": hashlib.sha256(public).hexdigest(),
              "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
              "decision": "approved", "checks": {name: True for name in release.REVIEW_CHECKS}}
    message = json.dumps(review, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    review["signature"] = base64.b64encode(private.sign(release.REVIEW_SIGNING_CONTEXT + message)).decode("ascii")
    (folder / release.INDEPENDENT_REVIEW).write_text(json.dumps(review))
    return review


@pytest.fixture
def episode(draft, monkeypatch):
    _sign_independent_review(draft, monkeypatch)
    release.certify(draft)
    return draft


def _optional_instagram_policy():
    config = release.POLICY_PATH
    data = json.loads(config.read_text())
    data["require_instagram"] = False
    config.write_text(json.dumps(data))


def _capture_buffer_creates(monkeypatch):
    payloads = []

    def create(query, variables):
        payloads.append(variables["input"])
        return {"createPost": {"__typename": "PostActionSuccess",
                               "post": {"id": f"post-{len(payloads)}", "status": "scheduled"}}}

    monkeypatch.setattr(publish, "posts", lambda **kwargs: [])
    monkeypatch.setattr(publish, "_buffer", create)
    monkeypatch.setattr(publish, "next_slots", lambda count, taken, **kwargs:
                        [datetime.now(publish.AUDIENCE_TZ) + timedelta(days=1)])
    return payloads


def test_unsigned_producer_draft_stays_held(draft, monkeypatch):
    _optional_instagram_policy()
    monkeypatch.setattr(auto, "EPISODES", draft.parent)
    monkeypatch.delenv("BUFFER_INSTAGRAM_CHANNEL_ID")
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer posts were queried"))
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("a post was created"))
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert run.errors == []
    assert any("uncertified waiting drafts remain held: ep063" in note for note in run.notes)
    assert not (draft / release.CERTIFICATE).exists()
    assert not (draft / "publish.json").exists()


def test_certify_requires_a_signed_independent_review(draft, monkeypatch):
    _sign_independent_review(draft, monkeypatch)
    (draft / release.INDEPENDENT_REVIEW).unlink()
    with pytest.raises(RuntimeError, match="signed independent review is missing"):
        release.certify(draft)
    assert not (draft / release.CERTIFICATE).exists()


def test_changed_or_untrusted_independent_signature_blocks_certification(draft, monkeypatch):
    review = _sign_independent_review(draft, monkeypatch)
    review["reviewed_at_utc"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    (draft / release.INDEPENDENT_REVIEW).write_text(json.dumps(review))
    with pytest.raises(RuntimeError, match="signature is invalid"):
        release.certify(draft)
    (draft.parent / "independent-review.pub").unlink()
    with pytest.raises(RuntimeError, match="trusted independent reviewer public key"):
        release.certify(draft)
    assert not (draft / release.CERTIFICATE).exists()


@pytest.mark.parametrize("file,change", [
    ("topic.json", {"started_at": "2026-10-06T00:00:00+00:00"}),
    ("visuals.json", [{"source": "card", "card": {"kind": "fact", "big": "Changed image"}}]),
])
def test_independent_review_binds_topic_and_visual_selection(draft, monkeypatch, file, change):
    _sign_independent_review(draft, monkeypatch)
    (draft / file).write_text(json.dumps(change))
    with pytest.raises(RuntimeError, match="does not approve this exact candidate"):
        release.certify(draft)
    assert not (draft / release.CERTIFICATE).exists()


def test_signed_cloud_handoff_certifies_hosted_bytes_without_local_mp4(draft, monkeypatch):
    _optional_instagram_policy()
    _sign_independent_review(draft, monkeypatch)
    (draft / "ep063.mp4").unlink()
    monkeypatch.setattr(auto, "EPISODES", draft.parent)
    monkeypatch.delenv("BUFFER_INSTAGRAM_CHANNEL_ID")
    verified = []
    monkeypatch.setattr(publish, "verify_hosted_media", lambda url, digest: verified.append((url, digest)))
    payloads = _capture_buffer_creates(monkeypatch)
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert run.errors == []
    assert [payload["channelId"] for payload in payloads] == ["yt"]
    certificate = json.loads((draft / release.CERTIFICATE).read_text())
    assert certificate["version"] == release.CERTIFICATE_VERSION == 2
    assert certificate["independent_review"]["reviewer_key_sha256"]
    assert verified and all(url == "https://cdn.example/ep063.mp4" and
                            digest == certificate["media_sha256"] for url, digest in verified)


def test_old_producer_certificate_cannot_authorize_release(episode):
    certificate_path = episode / release.CERTIFICATE
    certificate = json.loads(certificate_path.read_text())
    certificate["version"] = 1
    certificate_path.write_text(json.dumps(certificate))
    with pytest.raises(RuntimeError, match="release certificate identity is invalid"):
        release.validate(episode / "short.yaml")


def test_release_rechecks_the_signed_review_and_trusted_key(episode):
    review_path = episode / release.INDEPENDENT_REVIEW
    original = review_path.read_text()
    review = json.loads(original)
    review["checks"]["full_video_audio"] = False
    review_path.write_text(json.dumps(review))
    with pytest.raises(RuntimeError, match="signed independent review differs"):
        release.validate(episode / "short.yaml")
    review_path.write_text(original)
    release.REVIEW_PUBLIC_KEY_PATH.unlink()
    with pytest.raises(RuntimeError, match="trusted independent reviewer public key"):
        release.validate(episode / "short.yaml")


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


@pytest.mark.parametrize("value", [None, "false", 0, 1])
def test_policy_requires_an_explicit_boolean_instagram_choice(episode, value):
    config = release.POLICY_PATH
    data = json.loads(config.read_text())
    data["require_instagram"] = value
    config.write_text(json.dumps(data))
    with pytest.raises(RuntimeError, match="explicitly choose"):
        release.policy()


def test_policy_rejects_an_omitted_instagram_choice(episode):
    config = release.POLICY_PATH
    data = json.loads(config.read_text())
    del data["require_instagram"]
    config.write_text(json.dumps(data))
    with pytest.raises(RuntimeError, match="explicitly choose"):
        release.policy()


def test_optional_policy_keeps_episode_floor_and_start_cutoff(episode):
    _optional_instagram_policy()
    config = release.POLICY_PATH
    data = json.loads(config.read_text())
    data["min_episode_id"] = "ep050"
    config.write_text(json.dumps(data))
    with pytest.raises(RuntimeError, match="episode floor"):
        release.validate(episode / "short.yaml")
    data["min_episode_id"] = "ep063"
    config.write_text(json.dumps(data))
    data["started_after_utc"] = "2026-10-04T05:00:00+00:00"
    config.write_text(json.dumps(data))
    (episode / "topic.json").write_text(json.dumps({"started_at": "2026-10-04T04:59:59+00:00"}))
    with pytest.raises(RuntimeError, match="time cutoff"):
        release.validate(episode / "short.yaml")


def test_optional_youtube_release_is_idempotent_without_an_instagram_id(episode, monkeypatch):
    _optional_instagram_policy()
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.delenv("BUFFER_INSTAGRAM_CHANNEL_ID")
    # An unrelated account in the organization's channel list is never selected by discovery.
    monkeypatch.setattr(publish, "channels", lambda: [
        {"id": "yt", "service": "youtube", "isDisconnected": False},
        {"id": "mool-ig", "service": "instagram", "isDisconnected": False},
    ])
    payloads = _capture_buffer_creates(monkeypatch)
    verified = []
    monkeypatch.setattr(publish, "verify_hosted_media", lambda url, digest: verified.append((url, digest)))
    first = auto.Run("test")
    auto.publish_waiting(first)
    second = auto.Run("test")
    auto.publish_waiting(second)
    assert first.errors == second.errors == []
    assert [p["channelId"] for p in payloads] == ["yt"]
    assert verified and all(url == "https://cdn.example/ep063.mp4" and
                            digest == release._hash(episode / "ep063.mp4") for url, digest in verified)
    record = json.loads((episode / "publish.json").read_text())
    assert record["buffer_post_id"] == "post-1"
    assert not record.get("crossposts")


def test_optional_youtube_release_repairs_instagram_after_correct_account_connects(episode, monkeypatch):
    _optional_instagram_policy()
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.delenv("BUFFER_INSTAGRAM_CHANNEL_ID")
    payloads = _capture_buffer_creates(monkeypatch)
    youtube_only = auto.Run("test")
    auto.publish_waiting(youtube_only)
    assert youtube_only.errors == []
    monkeypatch.setenv("BUFFER_INSTAGRAM_CHANNEL_ID", "history-ig")
    monkeypatch.setattr(publish, "channels", lambda: [
        {"id": "yt", "service": "youtube", "isDisconnected": False},
        {"id": "mool-ig", "service": "instagram", "isDisconnected": False},
        {"id": "history-ig", "service": "instagram", "isDisconnected": False},
    ])
    repair = auto.Run("test")
    auto.publish_waiting(repair)
    repeated = auto.Run("test")
    auto.publish_waiting(repeated)
    assert repair.errors == repeated.errors == []
    assert [p["channelId"] for p in payloads] == ["yt", "history-ig"]
    assert payloads[1]["assets"] == [{"video": {"url": "https://cdn.example/ep063.mp4"}}]
    record = json.loads((episode / "publish.json").read_text())
    assert record["crossposts"]["instagram"]["id"] == "post-2"


def test_wrong_optional_instagram_id_does_not_block_youtube_or_use_mool(episode, monkeypatch):
    _optional_instagram_policy()
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.setenv("BUFFER_INSTAGRAM_CHANNEL_ID", "mool-ig")
    monkeypatch.setattr(publish, "channels", lambda: [{"id": "yt", "service": "youtube"}])
    payloads = _capture_buffer_creates(monkeypatch)
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert any("configured Instagram channel is missing" in error for error in run.errors)
    assert [p["channelId"] for p in payloads] == ["yt"]


def test_optional_policy_still_requires_the_exact_youtube_destination(episode, monkeypatch):
    _optional_instagram_policy()
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.setenv("BUFFER_YOUTUBE_CHANNEL_ID", "mool-yt")
    monkeypatch.delenv("BUFFER_INSTAGRAM_CHANNEL_ID")
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer posts were queried"))
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("a post was created"))
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert any("Configured Buffer YouTube channel is missing" in error for error in run.errors)
    assert not (episode / "publish.json").exists()


def test_optional_policy_waits_for_a_verified_youtube_destination_when_buffer_is_busy(episode, monkeypatch):
    _optional_instagram_policy()
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    monkeypatch.delenv("BUFFER_INSTAGRAM_CHANNEL_ID")

    def busy():
        raise publish.BufferBusy(datetime.now(timezone.utc) + timedelta(minutes=15))

    monkeypatch.setattr(publish, "channel", busy)
    monkeypatch.setattr(publish, "posts", lambda **kwargs: pytest.fail("Buffer posts were queried"))
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("a post was created"))
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert run.errors == []
    assert not (episode / "publish.json").exists()


@pytest.mark.parametrize("file,change", [
    ("ep063.mp4", b"another video"),
    ("topic.json", b'{"started_at":"2026-10-06T00:00:00+00:00"}'),
    ("short.yaml", b"id: ep063\ntitle: Rewritten\nbeats:\n  - text: The ship was lost.\n"),
    ("research.json", b"{}"),
    ("visuals.json", b'[{"source":"card","card":{"kind":"fact","big":"Changed image"}}]'),
    ("review.json", b"{}"),
])
@pytest.mark.parametrize("require_instagram", [True, False])
def test_changed_certified_input_blocks_buffer(episode, monkeypatch, file, change, require_instagram):
    if not require_instagram:
        _optional_instagram_policy()
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


def _youtube_record(episode, due):
    held = json.loads((episode / "hold.json").read_text())
    (episode / "hold.json").unlink()
    record = {**held, "buffer_post_id": "yt-post", "status": "sent", "due_at": due.isoformat(),
              "sent_at": due.isoformat()}
    (episode / "publish.json").write_text(json.dumps(record))
    return record


def test_optional_instagram_skips_a_new_reel_after_the_retry_window(episode, monkeypatch):
    _optional_instagram_policy()
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    _youtube_record(episode, datetime.now(publish.AUDIENCE_TZ) - timedelta(days=8))
    monkeypatch.setattr(publish, "posts", lambda **kwargs: [])
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("an old Reel was created"))
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert run.errors == []
    assert any("retry window elapsed" in stage["detail"] for stage in run.stages)
    assert "instagram" not in json.loads((episode / "publish.json").read_text()).get("crossposts", {})


def test_optional_instagram_can_adopt_an_old_accepted_reel(episode, monkeypatch):
    _optional_instagram_policy()
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    original = datetime.now(publish.AUDIENCE_TZ) - timedelta(days=8)
    _youtube_record(episode, original)
    caption = publish.caption(ShortSpec.load(episode / "short.yaml"))
    remote = {"id": "ig-accepted", "status": "sent", "text": caption, "dueAt": original.isoformat()}
    monkeypatch.setattr(publish, "posts", lambda **kwargs: [remote] if kwargs.get("channel_id") == "ig" else [])
    monkeypatch.setattr(publish, "post", lambda post_id: {**remote, "video": "https://cdn.example/ep063.mp4"})
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("a duplicate Reel was created"))
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert run.errors == []
    assert json.loads((episode / "publish.json").read_text())["crossposts"]["instagram"]["id"] == "ig-accepted"


@pytest.mark.parametrize("require_instagram", [True, False])
def test_live_youtube_post_retries_instagram_at_fresh_safe_slot(episode, monkeypatch, require_instagram):
    if not require_instagram:
        _optional_instagram_policy()
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    original = datetime.now(publish.AUDIENCE_TZ) - timedelta(hours=2)
    _youtube_record(episode, original)
    searches = []
    monkeypatch.setattr(publish, "posts", lambda **kwargs: searches.append(kwargs) or [])
    payloads = []

    def create(query, variables):
        payloads.append(variables["input"])
        return {"createPost": {"__typename": "PostActionSuccess",
                               "post": {"id": "ig-new", "status": "scheduled"}}}

    monkeypatch.setattr(publish, "_buffer", create)
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert run.errors == []
    assert len(payloads) == 1 and payloads[0]["channelId"] == "ig"
    fresh = datetime.fromisoformat(payloads[0]["dueAt"])
    now = datetime.now(publish.AUDIENCE_TZ)
    assert now + timedelta(minutes=29) < fresh <= now + timedelta(days=30)
    record = json.loads((episode / "publish.json").read_text())
    assert record["due_at"] == original.isoformat()
    assert record["crossposts"]["instagram"]["due_at"] == payloads[0]["dueAt"]
    assert searches and all("since" not in search for search in searches)


def test_live_youtube_post_adopts_accepted_instagram_post_after_due(episode, monkeypatch):
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    original = datetime.now(publish.AUDIENCE_TZ) - timedelta(hours=2)
    _youtube_record(episode, original)
    text = publish.caption(ShortSpec.load(episode / "short.yaml"))
    remote = {"id": "ig-accepted", "status": "sent", "text": text, "dueAt": original.isoformat()}
    monkeypatch.setattr(publish, "posts", lambda **kwargs: [remote] if kwargs.get("channel_id") == "ig" else [])
    monkeypatch.setattr(publish, "post", lambda post_id: {**remote, "video": "https://cdn.example/ep063.mp4"})
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("a duplicate was created"))
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert run.errors == []
    assert json.loads((episode / "publish.json").read_text())["crossposts"]["instagram"]["id"] == "ig-accepted"


def test_matching_instagram_post_with_unrelated_due_is_not_adopted(episode, monkeypatch):
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    original = datetime.now(publish.AUDIENCE_TZ) - timedelta(hours=2)
    _youtube_record(episode, original)
    text = publish.caption(ShortSpec.load(episode / "short.yaml"))
    remote = {"id": "ig-other", "status": "sent", "text": text,
              "dueAt": (original - timedelta(days=1)).isoformat()}
    monkeypatch.setattr(publish, "posts", lambda **kwargs: [remote] if kwargs.get("channel_id") == "ig" else [])
    monkeypatch.setattr(publish, "post", lambda post_id: {**remote, "video": "https://cdn.example/ep063.mp4"})
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("a duplicate was created"))
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert any("unrelated due time" in error for error in run.errors)
    assert "instagram" not in json.loads((episode / "publish.json").read_text()).get("crossposts", {})


@pytest.mark.parametrize("due", [
    (datetime.now(publish.AUDIENCE_TZ) - timedelta(days=8)).isoformat(),
    (datetime.now(publish.AUDIENCE_TZ) + timedelta(days=31)).isoformat(),
    "2026-10-06T12:00:00",
])
def test_instagram_retry_rejects_unbounded_or_naive_due(episode, monkeypatch, due):
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    _youtube_record(episode, datetime.now(publish.AUDIENCE_TZ))
    record_path = episode / "publish.json"
    record = json.loads(record_path.read_text())
    record["due_at"] = due
    record_path.write_text(json.dumps(record))
    monkeypatch.setattr(publish, "posts", lambda **kwargs: [])
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("an unsafe slot was scheduled"))
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert run.errors and "Instagram" in run.errors[-1]
    assert "instagram" not in json.loads(record_path.read_text()).get("crossposts", {})


def test_sync_keeps_certified_media_while_instagram_retry_is_pending(episode, monkeypatch):
    _youtube_record(episode, datetime.now(publish.AUDIENCE_TZ) - timedelta(days=3))
    monkeypatch.setattr(publish, "posts", lambda **kwargs: [])
    monkeypatch.setattr(publish, "unhost_video", lambda *args: pytest.fail("certified media was unhosted"))
    monkeypatch.setattr(publish, "_free_local", lambda *args: pytest.fail("certified media was removed"))
    records = publish.sync(episode.parent)
    assert records[0]["media_url"] == "https://cdn.example/ep063.mp4"


def test_direct_instagram_release_rejects_unsafe_due(episode, monkeypatch):
    original = datetime.now(publish.AUDIENCE_TZ) - timedelta(hours=1)
    _youtube_record(episode, original)
    monkeypatch.setattr(publish, "_buffer", lambda *args: pytest.fail("an unsafe slot was scheduled"))
    for target in (datetime.now(publish.AUDIENCE_TZ) - timedelta(minutes=1),
                   datetime.now(publish.AUDIENCE_TZ) + timedelta(days=31),
                   datetime.now(publish.AUDIENCE_TZ).replace(tzinfo=None)):
        with pytest.raises(RuntimeError, match="due time|safe scheduling window"):
            publish.crosspost(episode / "short.yaml", "instagram", "ig", "https://cdn.example/ep063.mp4",
                              target, autonomous_release=True)


def test_recorded_instagram_post_is_skipped_after_media_cleanup(episode, monkeypatch):
    monkeypatch.setattr(auto, "EPISODES", episode.parent)
    old = datetime.now(publish.AUDIENCE_TZ) - timedelta(days=3)
    record = _youtube_record(episode, old)
    record["crossposts"] = {"instagram": {"id": "ig-sent", "status": "sent", "due_at": old.isoformat()}}
    (episode / "publish.json").write_text(json.dumps(record))
    monkeypatch.setattr(publish, "posts", lambda **kwargs: [])
    monkeypatch.setattr(publish, "unhost_video", lambda *args: None)
    monkeypatch.setattr(publish, "_free_local", lambda *args: None)
    publish.sync(episode.parent)
    assert json.loads((episode / "publish.json").read_text())["media_url"] is None
    run = auto.Run("test")
    auto.publish_waiting(run)
    assert run.errors == []
