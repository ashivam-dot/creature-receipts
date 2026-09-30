import pytest

from ytc import llm, research
from ytc.research import Source


def _sources():
    return [Source("S1", "https://en.wikipedia.org/wiki/Narwhal", "Narwhal", "x"),
            Source("S2", "https://www.nationalgeographic.com/animals/narwhal", "Narwhal", "x"),
            Source("S3", "https://oceana.org/marine-life/narwhal/", "Narwhal", "x")]


def _answer(cite):
    return {"viable": True, "reason": "ok", "story": "s", "angle": "a", "disputed": [], "visuals": [],
            "claims": [{"claim": f"fact {i}", "sources": cite, "confidence": "high"} for i in range(10)]}


def test_bracketed_and_annotated_labels_count(monkeypatch):
    monkeypatch.setattr(research, "gather", lambda topic: _sources())
    monkeypatch.setattr(llm, "generate", lambda *a, **k: _answer(["[S1]", "S2 (National Geographic)"]))
    found = research.research("Narwhal", "Deep Weird")
    assert found["viable"] and len(found["claims"]) == 10
    assert found["claims"][0]["sources"] == ["S1", "S2"]


def test_an_answer_citing_nothing_usable_is_asked_again(monkeypatch):
    monkeypatch.setattr(research, "gather", lambda topic: _sources())
    monkeypatch.setattr(llm, "generate", lambda *a, **k: _answer(["source one", "source two"]))
    with pytest.raises(RuntimeError, match="asking again"):
        research.research("Narwhal", "Deep Weird")
