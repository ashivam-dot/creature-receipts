import pytest

from ytc import llm, research
from ytc.research import Source


def _sources():
    return [Source("S1", "https://en.wikipedia.org/wiki/Narwhal", "Narwhal",
                   "Narwhals live in Arctic seas and eat fish."),
            Source("S2", "https://www.nationalgeographic.com/animals/narwhal", "Narwhal",
                   "The narwhal lives in Arctic waters and eats fish."),
            Source("S3", "https://oceana.org/marine-life/narwhal/", "Narwhal",
                   "Narwhals are marine mammals found in the Arctic.")]


def _answer(cite, quotes=None):
    quotes = quotes if quotes is not None else [
        {"source": "[S1]", "quote": "Narwhals live in Arctic seas and eat fish."},
        {"source": "S2", "quote": "The narwhal lives in Arctic waters and eats fish."},
    ]
    return {"viable": True, "reason": "ok", "story": "s", "angle": "a", "disputed": [], "visuals": [],
            "claims": [{"claim": f"fact {'abcdefghij'[i]}", "sources": cite, "evidence": quotes, "confidence": "high"}
                       for i in range(10)]}


def test_bracketed_and_annotated_labels_count(monkeypatch):
    monkeypatch.setattr(research, "gather", lambda topic: _sources())
    monkeypatch.setattr(llm, "generate", lambda *a, **k: _answer(["[S1]", "S2 (National Geographic)"]))
    found = research.research("Narwhal", "Deep Weird")
    assert found["viable"] and len(found["claims"]) == 10
    assert found["claims"][0]["sources"] == ["S1", "S2"]
    assert len(found["claims"][0]["evidence"]) == 2


def test_invented_or_mismatched_quotes_do_not_count(monkeypatch):
    monkeypatch.setattr(research, "gather", lambda topic: _sources())
    fake = [{"source": "S1", "quote": "Narwhals were discovered in the Pacific Ocean."},
            {"source": "S2", "quote": "The narwhal lives in Arctic waters and eats fish."}]
    monkeypatch.setattr(llm, "generate", lambda *a, **k: _answer(["S1", "S2"], fake))
    with pytest.raises(RuntimeError, match="asking again"):
        research.research("Narwhal", "Deep Weird")


def test_an_answer_citing_nothing_usable_is_asked_again(monkeypatch):
    monkeypatch.setattr(research, "gather", lambda topic: _sources())
    monkeypatch.setattr(llm, "generate", lambda *a, **k: _answer(["source one", "source two"]))
    with pytest.raises(RuntimeError, match="asking again"):
        research.research("Narwhal", "Deep Weird")
