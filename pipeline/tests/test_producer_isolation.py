"""The scheduled producer can make drafts without receiving publisher credentials."""

import hashlib
import importlib.util
import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from ytc import auto, cloud, publish, release, studio


ROOT = Path(__file__).resolve().parents[2]


def test_publisher_credentials_are_absent_from_producer_mappings():
    paths = (".github/workflows/studio.yml", ".github/workflows/watchdog.yml",
             "pipeline/modal_secret.py", "pipeline/deploy.py")
    for relative in paths:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "secrets.BUFFER_" not in text
        assert "secrets.CLOUDINARY_URL" not in text
        assert "secrets.YTC_GOOGLE_" not in text
    assert not set(cloud.STUDIO_ENV) & set(cloud.PUBLISHER_ENV)
    assert "--draft-only" in (ROOT / ".github/workflows/studio.yml").read_text()
    assert "schedule=modal.Cron(WATCH_SCHEDULE" not in (ROOT / "pipeline/src/ytc/cloud.py").read_text()
    push = _load(ROOT / "kit" / "push_secrets.py", "producer_secret_seeding_test")
    verify = _load(ROOT / "kit" / "verify.py", "producer_setup_gate_test")
    assert not set(push.FROM_ENV) & set(cloud.PUBLISHER_ENV)
    assert not set(verify.REQUIRED_ENV) & set(cloud.PUBLISHER_ENV)


@pytest.mark.parametrize("workspace_name", ["akshshivam5", None, cloud.DEPLOY_WORKSPACE])
def test_modal_deploy_requires_pinned_producer_workspace(monkeypatch, workspace_name):
    deployed = []

    def workspace():
        if workspace_name is None:
            raise RuntimeError("workspace context unavailable")
        return SimpleNamespace(hydrate=lambda: SimpleNamespace(name=workspace_name))

    monkeypatch.setattr(cloud.modal.Workspace, "from_context", workspace)
    monkeypatch.setattr(cloud.modal, "enable_output", nullcontext)
    monkeypatch.setattr(cloud, "app", SimpleNamespace(deploy=lambda *, name: deployed.append(name)))
    if workspace_name == cloud.DEPLOY_WORKSPACE:
        cloud.deploy()
        assert deployed == [cloud.APP_NAME]
    else:
        with pytest.raises(RuntimeError, match="Modal deploy workspace"):
            cloud.deploy()
        assert deployed == []


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_draft_run_scrubs_inherited_publisher_keys_and_never_calls_publisher(monkeypatch, tmp_path):
    monkeypatch.setattr(auto, "STATUS", tmp_path / "status")
    monkeypatch.setattr(auto, "ON_MODAL", False)
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    for key in cloud.PUBLISHER_ENV:
        monkeypatch.setenv(key, "publisher-value")
    monkeypatch.setattr(auto, "inventory", lambda: {"remote": [], "target": 5, "total": 0, "making": []})
    monkeypatch.setattr(auto, "_session_note", lambda *args: None)
    monkeypatch.setattr(auto, "write_status", lambda *args: None)
    monkeypatch.setattr(publish, "sync", lambda *args: pytest.fail("Buffer sync called"))
    monkeypatch.setattr(auto, "check_channel", lambda *args: pytest.fail("Buffer channel called"))
    monkeypatch.setattr(auto, "publish_waiting", lambda *args: pytest.fail("publish called"))
    assert auto.main(0, daily_mode="no", draft_only=True) == 0
    assert all(key not in auto.os.environ for key in cloud.PUBLISHER_ENV)
    assert auto.os.environ["YTC_DRAFT_ONLY"] == "1"


@pytest.mark.parametrize("requested,trigger,held,expected", [
    (None, "schedule", True, None),
    (2, "schedule", True, None),
    (None, "manual", True, None),
    (2, "manual", True, 2),
    (2, "schedule", False, 2),
])
def test_draft_runner_preserves_editorial_pause_and_manual_trial(
        monkeypatch, tmp_path, requested, trigger, held, expected):
    marker = tmp_path / "scheduling_hold.json"
    if held:
        marker.write_text('{"reason":"editorial review"}')
    monkeypatch.setattr(publish, "SCHEDULING_HOLD", marker)
    policy_path = tmp_path / "autonomous_release_policy.json"
    policy_path.write_text('{"version":1,"enabled":false}')
    monkeypatch.setattr(release, "POLICY_PATH", policy_path)
    monkeypatch.setenv("YTC_AUTONOMOUS_RELEASE", "1")
    monkeypatch.setattr(auto, "STATUS", tmp_path / "status")
    monkeypatch.setattr(auto, "ON_MODAL", False)
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.setattr(auto, "inventory", lambda: {"remote": ["ep090"], "target": 5, "total": 0, "making": []})
    calls = []
    seen = []
    monkeypatch.setattr(auto, "collect", lambda run: calls.append("collect") or "collected")
    monkeypatch.setattr(auto, "daily", lambda run, state, *, draft_only: calls.append(("daily", draft_only)))
    monkeypatch.setattr(auto, "produce", lambda run, count, *, cloud_only: calls.append(("produce", count, cloud_only)))
    monkeypatch.setattr(auto, "_session_note", lambda run, inv: calls.append("session note"))
    monkeypatch.setattr(auto, "write_status", lambda run, result: seen.append(run))
    assert auto.main(requested, daily_mode="yes", trigger=trigger, draft_only=True) == 0
    assert "collect" in calls and ("daily", True) in calls and "session note" in calls
    assert [entry for entry in calls if isinstance(entry, tuple) and entry[0] == "produce"] == (
        [("produce", expected, True)] if expected else [])
    if held and expected is None:
        assert any("automatic production paused" in note for note in seen[0].notes)


def test_draft_runner_cannot_spend_runner_minutes_when_modal_credit_is_exhausted(monkeypatch):
    monkeypatch.setenv("MODAL_TOKEN_ID", "test-modal-token")
    monkeypatch.setattr(auto, "ON_MODAL", False)
    monkeypatch.setattr(auto, "_modal_cost", lambda: {"metered": auto.MODAL_CREDIT})
    monkeypatch.setattr(auto, "inventory", lambda: {"remote": []})
    monkeypatch.setattr(auto, "runner_minutes_allowed", lambda: 100)
    room = auto.capacity()
    assert room["cloud"] == 0 and room["runner"] > 0
    monkeypatch.setattr(auto, "capacity", lambda: room)
    requested = []
    monkeypatch.setattr(auto, "_jobs", lambda count: requested.append(count) or [])
    monkeypatch.setattr(auto, "_produce_here", lambda run, jobs, minutes: (
        jobs == [] and minutes == 0) or pytest.fail("local draft production"))
    auto.produce(auto.Run("schedule"), 3, cloud_only=True)
    assert requested == [0]


def test_modal_secret_rebuild_is_explicit_and_excludes_publisher_keys(monkeypatch, tmp_path):
    helper = _load(ROOT / "pipeline" / "modal_secret.py", "producer_modal_secret_test")
    called = []
    monkeypatch.setattr(helper, "deploy_key", lambda: called.append("deploy key"))
    monkeypatch.setattr(helper, "ntfy_topic", lambda: called.append("ntfy"))
    monkeypatch.setattr(helper, "modal_secret", lambda: called.append("rebuild"))
    with pytest.raises(SystemExit, match="usage"):
        helper.main([])
    assert called == []
    helper.main(["setup"])
    assert called == ["deploy key", "ntfy"]
    helper.main(["modal"])
    assert called[-1] == "rebuild"

    env_file = tmp_path / ".env"
    env_file.write_text("YTC_CONTACT=contact@example.com\nBUFFER_API_KEY=fake-buffer\n"
                        "CLOUDINARY_URL=cloudinary://fake\nYTC_GOOGLE_TOKEN=fake-google\n")
    key = tmp_path / "deploy_key"
    key.write_text("fake-deploy-key")
    monkeypatch.setattr(helper, "ENV", env_file)
    monkeypatch.setattr(helper, "KEY", key)
    monkeypatch.setenv("BUFFER_API_KEY", "fake-buffer")
    monkeypatch.setenv("CLOUDINARY_URL", "cloudinary://fake")
    captured = {}

    def capture(*args, **kwargs):
        captured["payload"] = json.loads(Path(args[args.index("--from-json") + 1]).read_text())
        captured["env"] = kwargs["env"]
        return ""

    # Reload to use the actual builder after checking command dispatch.
    actual = _load(ROOT / "pipeline" / "modal_secret.py", "producer_modal_secret_payload_test")
    monkeypatch.setattr(actual, "ENV", env_file)
    monkeypatch.setattr(actual, "KEY", key)
    monkeypatch.setattr(actual, "run", capture)
    actual.modal_secret()
    assert set(captured["payload"]) == {"YTC_CONTACT", "YTC_MODAL_CREDIT", "YTC_DEPLOY_KEY"}
    assert not set(captured["env"]) & set(cloud.PUBLISHER_ENV)


def test_push_secrets_cannot_reseed_publisher_credentials(monkeypatch, capsys):
    helper = _load(ROOT / "kit" / "push_secrets.py", "producer_push_secrets_test")
    monkeypatch.setattr(helper, "env_values", lambda: {
        "YTC_CONTACT": "contact@example.com", "BUFFER_API_KEY": "old-buffer",
        "CLOUDINARY_URL": "cloudinary://old", "YTC_GOOGLE_TOKEN": "old-google",
    })
    called = []
    monkeypatch.setattr(helper.subprocess, "run", lambda args, **kwargs: (
        called.append(args) or SimpleNamespace(returncode=0, stderr="")))
    monkeypatch.setattr(helper.sys, "argv", ["push_secrets.py", "--repo", "owner/producer"])
    helper.main()
    names = [command[3] for command in called if command[:3] == ["gh", "secret", "set"]]
    assert names == ["YTC_CONTACT"]
    assert not set(names) & set(cloud.PUBLISHER_ENV)
    output = capsys.readouterr().out
    assert "BUFFER_API_KEY" not in output and "CLOUDINARY_URL" not in output and "YTC_GOOGLE_TOKEN" not in output


def test_reviewed_draft_binding_has_no_hosted_destination(tmp_path, monkeypatch):
    folder = tmp_path / "ep063"
    (folder / "work").mkdir(parents=True)
    media = b"reviewed draft bytes"
    (folder / "ep063.mp4").write_bytes(media)
    spec = folder / "short.yaml"
    spec.write_text("id: ep063\n")
    (folder / "work" / "manifest.json").write_text(json.dumps({"id": "ep063", "beats": []}))
    (folder / "hold.json").write_text("{}")
    (folder / "release_certificate.json").write_text("{}")
    monkeypatch.setattr(publish, "host_video", lambda *args: pytest.fail("Cloudinary upload called"))
    draft = studio.record_draft(spec, "ep063", "Test title", "Tragedy", {"hook": 4}, None)
    digest = hashlib.sha256(media).hexdigest()
    assert draft["media_sha256"] == digest
    assert draft["modal_path"] == f"drafts/ep063-{digest}.mp4"
    assert "media_url" not in draft and "media_public_id" not in draft
    assert json.loads((folder / "draft.json").read_text()) == draft
    assert not (folder / "hold.json").exists()
    assert not (folder / "release_certificate.json").exists()


def test_draft_counts_toward_production_inventory(tmp_path, monkeypatch):
    folder = tmp_path / "ep063"
    folder.mkdir()
    (folder / "topic.json").write_text('{"topic":"A story","series":"History"}')
    (folder / "draft.json").write_text('{"id":"ep063"}')
    monkeypatch.setattr(auto, "EPISODES", tmp_path)
    found = auto.episodes()
    assert found[0]["state"] == "draft"
    inv = auto.inventory(found)
    assert inv["drafts"] == inv["total"] == 1
    assert inv["in_buffer"] == inv["waiting"] == 0


def test_public_monitor_skips_publisher_checks_and_alerts_on_feed_failure(monkeypatch):
    path = ROOT / "monitor" / "monitor.py"
    spec = importlib.util.spec_from_file_location("history_public_monitor_test", path)
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    monkeypatch.setenv("YTC_PUBLIC_MONITOR_ONLY", "1")
    monkeypatch.setattr(monitor, "_env", lambda: pytest.fail("publisher environment read"))
    monkeypatch.setattr(monitor, "buffer", lambda env: pytest.fail("Buffer read"))
    monkeypatch.setattr(monitor, "cloudinary", lambda env: pytest.fail("Cloudinary read"))
    monkeypatch.setattr(monitor, "github", lambda: {
        "status": {"inventory": {"total": 5, "drafts": 5}, "modal_credit": 1}, "runs": [],
        "workflow_state": "active", "history": [], "minutes": 0, "scheduling_hold": None,
    })
    monkeypatch.setattr(monitor, "youtube_feed", lambda: (_ for _ in ()).throw(RuntimeError("feed unavailable")))
    data = monitor.collect()
    assert data["buffer"]["unavailable"] and data["cloudinary"]["unavailable"]
    assert data["feed"]["error"] == "RuntimeError: feed unavailable"
    problems = monitor.assess(data)
    assert any(level == "alert" and "Can't verify the channel's public feed" in message
               for level, message in problems)
    assert any(level == "alert" and "Only 0 Shorts are ready" in message for level, message in problems)
