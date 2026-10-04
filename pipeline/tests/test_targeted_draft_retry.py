import pytest

from ytc import auto


def test_manual_draft_retry_routes_only_the_requested_episode(monkeypatch, tmp_path):
    monkeypatch.setattr(auto, "STATUS", tmp_path / "status")
    monkeypatch.setattr(auto, "ON_MODAL", False)
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.setattr(auto, "inventory", lambda: {"remote": [], "target": 5, "total": 4, "making": []})
    monkeypatch.setattr(auto, "_session_note", lambda *args: None)
    monkeypatch.setattr(auto, "write_status", lambda *args: None)
    called = []
    monkeypatch.setattr(auto, "produce", lambda run, count, *, cloud_only, episode_id:
                        called.append((count, cloud_only, episode_id)))

    assert auto.main(1, daily_mode="no", trigger="workflow_dispatch", draft_only=True,
                     target_episode="ep065") == 0
    assert called == [(1, True, "ep065")]


def test_targeted_retry_skips_older_unfinished_episodes(monkeypatch, tmp_path):
    episodes = [
        {"id": "ep055", "state": "making", "folder": tmp_path / "ep055",
         "topic": {"topic": "Older", "series": "Warnings Ignored", "spawns": 0}},
        {"id": "ep065", "state": "making", "folder": tmp_path / "ep065",
         "topic": {"topic": "Quebec Bridge", "series": "Warnings Ignored", "spawns": 1}},
    ]
    for episode in episodes:
        episode["folder"].mkdir()
    monkeypatch.setattr(auto, "episodes", lambda: episodes)
    monkeypatch.setattr(auto, "capacity", lambda: {"cloud": 1, "runner": 0, "runner_minutes": 0})
    monkeypatch.setattr(auto, "_jobs", lambda count: pytest.fail("general queue selected"))
    started = []
    monkeypatch.setattr(auto, "_spawn", lambda run, jobs: started.extend(jobs) or [])
    monkeypatch.setattr(auto, "_produce_here", lambda *args: None)

    auto.produce(auto.Run("workflow_dispatch"), 1, cloud_only=True, episode_id="ep065")
    assert [job["id"] for job in started] == ["ep065"]


def test_targeted_retry_fails_closed_for_hold_or_wrong_mode(monkeypatch, tmp_path):
    with pytest.raises(ValueError, match="draft-only manual"):
        auto.main(1, draft_only=False, target_episode="ep065")
    with pytest.raises(ValueError, match="draft-only manual"):
        auto.main(1, trigger="schedule", draft_only=True, target_episode="ep065")
    held = tmp_path / "ep065"
    held.mkdir()
    (held / "editorial_hold.json").write_text("{}")
    monkeypatch.setattr(auto, "episodes", lambda: [{"id": "ep065", "state": "making", "folder": held,
                                                     "topic": {"topic": "Quebec Bridge", "series": "Warnings Ignored"}}])
    monkeypatch.setattr(auto, "capacity", lambda: {"cloud": 1, "runner": 0, "runner_minutes": 0})
    with pytest.raises(RuntimeError, match="not an unheld unfinished episode"):
        auto.produce(auto.Run("workflow_dispatch"), 1, cloud_only=True, episode_id="ep065")
