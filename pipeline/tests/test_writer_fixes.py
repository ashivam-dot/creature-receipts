import pytest

from ytc import writer

RESEARCH = {"series": "Deep Sea Files", "topic": "Giant squid (2004): first photographed alive", "claims": [],
            "visuals": []}


@pytest.fixture
def drafts(monkeypatch):
    sent = []

    def run(replies, issues_of):
        replies = list(replies)
        monkeypatch.setattr(writer, "normalize", lambda script, research: dict(script))
        monkeypatch.setattr(writer, "problems", lambda script, research: issues_of[script["n"]])
        monkeypatch.setattr(writer, "recent_scripts", lambda topic: [])
        monkeypatch.setattr(writer, "_learnings", lambda: "")
        monkeypatch.setattr(writer, "exemplars", lambda: "")
        monkeypatch.setattr(writer.llm, "generate", lambda prompt, **k: sent.append(prompt) or replies.pop(0))
        return sent

    return run


def test_fixes_start_from_the_best_draft(drafts):
    issues = {1: ["a"], 2: ["a", "b", "c"], 3: []}
    sent = drafts([{"n": 1}, {"n": 2}, {"n": 3}], issues)
    assert writer.write_script(RESEARCH, "ep001")["n"] == 3
    assert '"n": 1' in sent[2]


def test_gives_up_after_the_fix_rounds_with_the_best_problems(drafts):
    issues = {1: ["short by 2 words"], 2: ["x", "y"]}
    sent = drafts([{"n": 1}] + [{"n": 2}] * writer.FIX_ROUNDS, issues)
    with pytest.raises(RuntimeError, match="short by 2 words"):
        writer.write_script(RESEARCH, "ep001")
    assert len(sent) == writer.FIX_ROUNDS + 1


def test_word_count_problem_says_how_many_words_to_add(monkeypatch):
    monkeypatch.setattr(writer, "recent_scripts", lambda topic: [])
    beats = [{"text": " ".join(["word"] * 10)} for _ in range(6)]
    found = writer.problems({"beats": beats}, RESEARCH)
    assert any("add at least 45 words" in f and "beat 6: 10" in f for f in found)
