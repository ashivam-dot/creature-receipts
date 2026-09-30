import pytest

from ytc import llm


class _Response:
    status_code = 403
    content = b"x"
    text = ""

    def json(self):
        return {"error": {"code": 403, "status": "PERMISSION_DENIED", "message": "Your project has been denied access."}}


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.setenv("YTC_GEMINI_API_KEY", "test")
    monkeypatch.setattr(llm, "_key_refused", "")
    monkeypatch.setattr(llm, "_spent", set())
    monkeypatch.setattr(llm, "_resting", {})
    monkeypatch.setattr(llm, "CURSOR_FALLBACK", False)
    monkeypatch.setattr(llm, "_pace", lambda *a, **k: None)
    monkeypatch.setattr(llm.requests, "post", lambda *a, **k: _Response())


def test_refused_key_falls_through_to_a_backup(monkeypatch):
    asked = []
    monkeypatch.setattr(llm, "_ask_backup", lambda model, *a: asked.append(model) or "from the backup")
    answer = llm.generate("hi", models=("gemini-3.8-flash", "gemini-3.7-flash", "ovh:Qwen3.8-27B"))
    assert answer == "from the backup"
    assert asked == ["ovh:Qwen3.8-27B"]
    assert llm.gemini_spent()


def test_refused_key_with_no_backup_names_the_key():
    with pytest.raises(llm.OutOfQuota, match="Gemini refused the key: 403"):
        llm.generate("hi", models=("gemini-3.8-flash",))
