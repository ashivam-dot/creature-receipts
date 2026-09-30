import json

from ytc import auto


def _event(tmp_path, monkeypatch, private):
    path = tmp_path / "event.json"
    path.write_text(json.dumps({"repository": {"private": private}}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))


def test_public_repo_has_no_minutes_budget(tmp_path, monkeypatch):
    _event(tmp_path, monkeypatch, private=False)
    assert auto.minutes_budget() is None
    assert auto.runner_minutes_allowed() == auto.PRODUCE_MINUTES


def test_private_repo_keeps_the_budget(tmp_path, monkeypatch):
    _event(tmp_path, monkeypatch, private=True)
    assert auto.minutes_budget() == auto.MONTH_MINUTES


def test_unknown_visibility_counts_as_private(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_EVENT_PATH", "/nonexistent")
    monkeypatch.setattr(auto.requests, "get", lambda *a, **k: (_ for _ in ()).throw(auto.requests.ConnectionError()))
    assert auto.minutes_budget() == auto.MONTH_MINUTES
