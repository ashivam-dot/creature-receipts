"""The scheduled producer can make drafts without receiving publisher credentials."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from ytc import auto, cloud, publish, studio


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
