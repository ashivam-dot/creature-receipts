import time

from ytc import llm


def test_a_spent_daily_quota_is_asked_again_after_the_recheck(monkeypatch):
    monkeypatch.setattr(llm, "_key_refused", "")
    monkeypatch.setattr(llm, "_spent", set())
    now = time.monotonic()
    monkeypatch.setattr(llm, "_day_spent", {"gemini-3.8-flash": now + 60, "gemini-3.7-flash": now - 1})
    assert llm._out("gemini-3.8-flash")
    assert not llm._out("gemini-3.7-flash")
    assert not llm.gemini_spent()
    monkeypatch.setattr(llm, "_day_spent", {model: now + 60 for model in llm.FLASH})
    assert llm.gemini_spent()
