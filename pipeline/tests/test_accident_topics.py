"""The checked accident lane adds one lead once and carries its sources into research."""

import copy
import json
from datetime import date, datetime

import pytest

from ytc import accidents, auto, llm, research, stories, studio
from ytc.research import Source


CALENDAR = """# Content calendar

## Backlog

### The Last Hours

- An unrelated historical event

### Warnings Ignored

- Another unrelated historical event
"""
TODAY = date(2026, 10, 4)


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    strategy = tmp_path / "strategy"
    strategy.mkdir()
    calendar = strategy / "CALENDAR.md"
    calendar.write_text(CALENDAR, encoding="utf-8")
    candidates = strategy / "ACCIDENT-CANDIDATES.json"
    candidates.write_text(accidents.CANDIDATES.read_text(encoding="utf-8"), encoding="utf-8")
    status = tmp_path / "status"
    status.mkdir()
    episodes = tmp_path / "content" / "episodes"
    rejected = tmp_path / "content" / "rejected"
    shelved = tmp_path / "content" / "shelved"
    for folder in (episodes, rejected, shelved):
        folder.mkdir(parents=True)
    monkeypatch.setattr(accidents, "CANDIDATES", candidates)
    monkeypatch.setattr(auto, "CALENDAR", calendar)
    monkeypatch.setattr(auto, "EPISODES", episodes)
    monkeypatch.setattr(auto, "REJECTED", rejected)
    monkeypatch.setattr(auto, "ROOT", tmp_path)
    monkeypatch.setattr(auto, "_now", lambda: datetime(2026, 10, 4, 12, tzinfo=auto.IST))
    monkeypatch.setattr(auto, "demand", lambda topics: {})
    monkeypatch.setattr(stories, "STORIES", status / "stories.json")
    monkeypatch.setattr(studio, "EPISODES", episodes)
    monkeypatch.setattr(studio, "REJECTED", rejected)
    monkeypatch.setattr(studio, "SHELVED", shelved)
    return tmp_path


def test_accident_pool_needs_primary_and_independent_origins(isolated):
    rows = accidents.load(TODAY)
    assert [row["id"] for row in rows] == ["texas-city-1947", "quebec-bridge-1907", "oppau-1921", "mann-gulch-1949"]
    broken = copy.deepcopy(rows[0])
    broken["sources"][0]["url"] = "https://en.wikipedia.org/wiki/Texas_City_disaster"
    accidents.CANDIDATES.write_text(json.dumps([broken]), encoding="utf-8")
    before = auto.CALENDAR.read_text(encoding="utf-8")
    assert auto.add_accident_topics(auto.Run("test")) == []
    assert auto.CALENDAR.read_text(encoding="utf-8") == before
    assert not stories.STORIES.exists()


def test_accident_lead_is_repeat_safe_across_calendar_and_episode_history(isolated):
    run = auto.Run("test")
    assert "Texas City" in auto.add_accident_topics(run)[0]
    assert auto.add_accident_topics(run) == []
    assert auto.CALENDAR.read_text().count("Texas City disaster (1947)") == 1
    topic = next(t for t in auto.calendar_topics(TODAY) if t["topic"].startswith("Texas City"))
    auto.mark_topic(topic, "done", "ep100")
    # A rejected episode can be absent from the calendar yet still consume its subject.
    old = auto.REJECTED / "ep099"
    old.mkdir()
    (old / "topic.json").write_text(json.dumps({"topic": "Oppau disaster (1921): another angle"}))
    old = auto.REJECTED / "ep098"
    old.mkdir()
    (old / "topic.json").write_text(json.dumps({"topic": "Quebec Bridge (1907): a different collapse angle"}))
    assert "Mann Gulch" in auto.add_accident_topics(run)[0]
    assert auto.add_accident_topics(run) == []
    records = stories._load()["topics"]
    assert {r["candidate_id"] for r in records.values()} == {"texas-city-1947", "mann-gulch-1949"}


def test_parked_accident_does_not_block_next_checked_lead(isolated):
    run = auto.Run("test")
    assert "Texas City" in auto.add_accident_topics(run)[0]
    first = next(t for t in auto.calendar_topics(TODAY) if t["topic"].startswith("Texas City"))
    auto.mark_topic(first, "parked", "ep063")
    assert "Quebec Bridge" in auto.add_accident_topics(run)[0]
    assert auto.add_accident_topics(run) == []
    records = stories._load()["topics"]
    assert records[accidents.load(TODAY)[1]["topic"]]["candidate_id"] == "quebec-bridge-1907"


def test_episode_receives_exact_checked_sources_and_studio_passes_them(isolated, monkeypatch):
    candidate = accidents.load(TODAY)[0]
    auto.add_accident_topics(auto.Run("test"))
    jobs = auto._jobs(1)
    assert len(jobs) == 1 and jobs[0]["topic"] == candidate["topic"]
    meta = json.loads((auto.EPISODES / jobs[0]["id"] / "topic.json").read_text())
    assert meta["candidate_id"] == candidate["id"]
    assert meta["research_sources"] == candidate["sources"]
    seen = {}

    def researched(topic, series, *, source_plan, cautions):
        seen.update(topic=topic, series=series, source_plan=source_plan, cautions=cautions)
        return {"viable": False, "reason": "test stops before rendering", "claims": [], "sources": []}

    monkeypatch.setattr(studio, "do_research", researched)
    result = studio.produce(candidate["topic"], candidate["series"], jobs[0]["id"])
    assert result["outcome"] == "rejected"
    assert seen == {"topic": candidate["topic"], "series": candidate["series"],
                    "source_plan": candidate["sources"], "cautions": candidate["cautions"]}


def test_episode_cannot_resume_without_its_checked_source_plan(isolated):
    candidate = accidents.load(TODAY)[0]
    folder = studio.EPISODES / "ep001"
    folder.mkdir()
    meta = {"topic": candidate["topic"], "series": candidate["series"], "candidate_id": candidate["id"], "attempts": 0}
    (folder / "topic.json").write_text(json.dumps(meta))
    with pytest.raises(RuntimeError, match="without its source plan"):
        studio.produce(candidate["topic"], candidate["series"], "ep001")
    meta["research_sources"] = candidate["sources"]
    meta["attempts"] = 0
    (folder / "topic.json").write_text(json.dumps(meta))
    (folder / "research.json").write_text(json.dumps({"sources": [{"url": "https://unrelated.example/report"}]}))
    with pytest.raises(RuntimeError, match="different source plan"):
        studio.produce(candidate["topic"], candidate["series"], "ep001")


def test_curated_research_reads_only_checked_pages_and_keeps_quote_gate(monkeypatch):
    urls = ["https://primary.example.org/report.txt", "https://history.example.net/account"]
    plan = [{"url": urls[0], "focus": ["lower chord"]}, {"url": urls[1]}]
    first = [f"At Quebec Bridge, report entry {i} described a lower chord bend." for i in range(9)]
    second = [f"At Quebec Bridge, account entry {i} described a lower chord bend." for i in range(9)]
    texts = {urls[0]: ("Original report", "\n".join(first) + " evidence" * 300),
             urls[1]: ("Independent account", "\n".join(second) + " evidence" * 300)}
    reads = []
    monkeypatch.setattr(research, "_read", lambda url: reads.append(url) or texts[url])
    monkeypatch.setattr(research, "_search", lambda *args: pytest.fail("curated research searched outside its source pair"))
    claims = [{"claim": f"fact {i}", "sources": ["S1", "S2"], "evidence": [
        {"source": "S1", "quote": first[i]}, {"source": "S2", "quote": second[i]}], "confidence": "high"}
        for i in range(9)]
    claims.append({"claim": "invented", "sources": ["S1", "S2"], "evidence": [
        {"source": "S1", "quote": "The bridge was made of paper and vanished overnight."},
        {"source": "S2", "quote": second[0]}], "confidence": "high"})
    prompts = []

    def answer(prompt, **kwargs):
        prompts.append(prompt)
        return {"viable": True, "reason": "ok", "story": "s", "angle": "a", "disputed": [], "visuals": [], "claims": claims}

    monkeypatch.setattr(llm, "generate", answer)
    found = research.research("Quebec Bridge (1907): lower chord", "The Last Hours", plan,
                              ["Do not invent a preventable collapse."])
    assert reads == urls
    assert [s["url"] for s in found["sources"]] == urls
    assert found["viable"] and len(found["claims"]) == 9
    assert "Do not invent a preventable collapse." in prompts[0]


def test_plain_text_report_is_read_as_source_text(monkeypatch):
    class Raw:
        def read(self, limit, decode_content=False):
            assert limit == 3_000_000 and decode_content
            return b"Royal Commission on Quebec Bridge Inquiry\nThe lower chord bent."

    class Response:
        status_code = 200
        headers = {"content-type": "text/plain; charset=utf-8"}
        encoding = "utf-8"
        raw = Raw()

    monkeypatch.setattr(research.requests, "get", lambda *args, **kwargs: Response())
    assert research._read("https://archive.org/download/report/report.txt") == (
        "report.txt", "Royal Commission on Quebec Bridge Inquiry\nThe lower chord bent.")


def test_quotes_cannot_span_two_distant_ocr_excerpts():
    source = Source("S1", "https://archive.org/download/report/report.txt", "Report",
                    "Engineers measured a lower chord bend.\n[...]\nThe bridge fell at Quebec.",
                    full_text="Engineers measured a lower chord bend. Many pages separated these facts. "
                              "The bridge fell at Quebec.")
    claim = {"sources": ["S1"], "evidence": [
        {"source": "S1", "quote": "Engineers measured a lower chord bend. The bridge fell at Quebec."}]}
    assert research._matched_evidence(claim, {"S1": source}) == []


def test_missing_checked_source_stops_research_without_substitution(monkeypatch):
    urls = ["https://primary.example.org/report.txt", "https://history.example.net/account"]
    plan = [{"url": url} for url in urls]
    monkeypatch.setattr(research, "_read", lambda url: ("Report", "Quebec Bridge " + "evidence " * 300) if url == urls[0] else None)
    monkeypatch.setattr(research, "_search", lambda *args: pytest.fail("unexpected web search"))
    monkeypatch.setattr(llm, "generate", lambda *args, **kwargs: pytest.fail("research continued without the checked pair"))
    with pytest.raises(RuntimeError, match="cannot substitute"):
        research.research("Quebec Bridge (1907): lower chord", "The Last Hours", plan)
