"""Offline checks of the timely calendar, breakout follow-ups, timely scheduling, and cross-posting in auto.py and
publish.py. Everything runs in a temporary folder with the network and language models faked."""

import json
from datetime import date, datetime, timedelta, timezone

import pytest
import yaml

from ytc import auto, growth, publish, research
from ytc.spec import ShortSpec

NOW = datetime(2026, 10, 20, 15, 0, tzinfo=auto.IST)
CALENDAR = """# Content calendar

Intro.

## Anniversaries (publish on the date, 8 p.m. Eastern)

| Date | Story | Series |
|---|---|---|
| Oct 25 | Coelacanth (1938): a fish known only from fossils turned up alive | Back From Extinction |

## Backlog

### Deep Sea Files

- Vampire squid (1903): it turns itself inside out instead of fleeing

### Nature's Record Breakers

- Peacock mantis shrimp: a punch as fast as a bullet
"""


@pytest.fixture
def studio(tmp_path, monkeypatch):
    (tmp_path / "strategy").mkdir()
    calendar = tmp_path / "strategy" / "CALENDAR.md"
    calendar.write_text(CALENDAR, encoding="utf-8")
    for name, path in (("CALENDAR", calendar), ("STATUS", tmp_path / "status"), ("ANALYTICS", tmp_path / "analytics"),
                       ("EPISODES", tmp_path / "content" / "episodes"), ("REJECTED", tmp_path / "content" / "rejected"),
                       ("DEMAND", tmp_path / "status" / "demand.json")):
        monkeypatch.setattr(auto, name, path)
    (tmp_path / "status").mkdir()
    (tmp_path / "analytics").mkdir()
    (tmp_path / "content" / "episodes").mkdir(parents=True)
    monkeypatch.setattr(auto, "_now", lambda: NOW)
    monkeypatch.setattr(auto, "demand", lambda topics: {})
    monkeypatch.setattr(research, "_existing", lambda titles: [{"giant squid": "Giant squid"}.get(t, t) for t in titles
                                                               if t != "Made Up Article"])
    return tmp_path


def _rows(n=1, why="Nature news: hydrothermal vents"):
    return [{"topic": f"Hydrothermal vent (1977): story number {i} about life without sunlight", "series": "Deep Sea Files", "why": why}
            for i in range(n)]


def test_insert_timely_creates_the_section_at_the_top(studio):
    lines = auto.insert_timely(CALENDAR.splitlines(), _rows(), date(2026, 10, 20))
    text = "\n".join(lines)
    assert text.index("## Timely") < text.index("## Anniversaries")
    assert "| 2026-10-20 | Hydrothermal vent (1977): story number 0 about life without sunlight | Deep Sea Files | Nature news: hydrothermal vents |" in lines
    # A second insert goes into the same table, after the first row.
    again = auto.insert_timely(lines, [{"topic": "A | piped topic", "series": "Nature's Record Breakers", "why": "x"}], date(2026, 10, 21))
    assert sum(line.startswith("## Timely") for line in again) == 1
    assert again.index("| 2026-10-21 | A / piped topic | Nature's Record Breakers | x |") == lines.index(
        next(line for line in lines if line.startswith("| 2026-10-20"))) + 1


def test_timely_topics_are_parsed_marked_and_chosen_first(studio):
    auto.CALENDAR.write_text("\n".join(auto.insert_timely(CALENDAR.splitlines(), _rows(), date(2026, 10, 19))) + "\n")
    stale = auto.insert_timely(auto.CALENDAR.read_text().splitlines(),
                               [{"topic": "Axolotl (1864): the salamander that never grows up", "series": "Evolution Got Weird", "why": "old news"}],
                               date(2026, 10, 10))
    auto.CALENDAR.write_text("\n".join(stale) + "\n")
    topics = auto.calendar_topics(NOW.date())
    timely = [t for t in topics if t["kind"] == "timely"]
    assert [t["date"] for t in timely] == [date(2026, 10, 19), date(2026, 10, 10)]
    assert [t["topic"][:6] for t in auto.urgent(topics, NOW.date())] == ["Hydrot"]

    chosen = auto.choose_topics(5, [])
    assert [t["kind"] for t in chosen[:2]] == ["timely", "anniversary"]
    # The stale timely topic waits in line with the backlog.
    assert any(t["topic"].startswith("Axolotl") for t in chosen[2:])

    auto.mark_topic(timely[0], "making", "ep012")
    marked = next(t for t in auto.calendar_topics(NOW.date()) if t["kind"] == "timely" and t["topic"].startswith("Hydrothermal"))
    assert (marked["status"], marked["episode"], marked["why"]) == ("making", "ep012", "Nature news: hydrothermal vents")
    assert not auto.urgent([t for t in auto.calendar_topics(NOW.date()) if auto._available(t, NOW.date())], NOW.date())


def test_verified_needs_a_series_a_real_article_and_something_new(studio):
    known = [auto._key_words("Vampire squid (1903): it turns itself inside out instead of fleeing")]
    items = [
        {"topic": "Vampire squid (1903): it turns itself inside out instead of fleeing, again", "series": "Deep Sea Files",
         "wikipedia": "Vampire squid"},
        {"topic": "Something (2026): with no article", "series": "Deep Sea Files", "wikipedia": "Made Up Article"},
        {"topic": "Moon (2026): a series that doesn't exist", "series": "Cooking", "wikipedia": "Moon"},
        {"topic": "It was filmed alive for the first time in 2012, 630 meters down", "series": "Deep Sea Files",
         "wikipedia": "giant squid", "why": "Nature news"},
        {"topic": "Tardigrade (1702): dried out for decades, then alive again", "series": "Built Different", "wikipedia": "Tardigrade"},
    ]
    rows = auto._verified(items, known, limit=5)
    assert [r["topic"] for r in rows] == ["Giant squid: It was filmed alive for the first time in 2012, 630 meters down",
                                         "Tardigrade (1702): dried out for decades, then alive again"]
    assert len(auto._verified(items, [], limit=1)) == 1


def test_add_timely_caps_topics_a_day(studio, monkeypatch):
    monkeypatch.setattr(growth, "trending_animals", lambda: [{"title": "Tardigrade", "views": 90_000,
                                                              "description": "Phylum of microscopic animals"}])
    monkeypatch.setattr(growth, "fetch_nature_news", lambda: [])
    asked = []

    def pick(trending, news, known, limit):
        asked.append(limit)
        return [{"topic": t, "series": "Built Different", "wikipedia": w, "why": "trending"} for t, w in (
            ("Tardigrade (1702): dried out for decades, then alive again", "Tardigrade"),
            ("Pistol shrimp (2001): a snap that flashes light", "Alpheidae"),
            ("Wood frog (1982): it freezes solid every winter", "Wood frog"))]

    monkeypatch.setattr(growth, "pick_timely", pick)
    assert len(auto.add_timely(auto.Run("test"))) == auto.TREND_PER_DAY
    assert auto.add_timely(auto.Run("test")) == [] and asked == [auto.TREND_PER_DAY]


def _episode(root, episode_id, video, series="Built Different", state="sent", extra=None):
    folder = root / "content" / "episodes" / episode_id
    folder.mkdir(parents=True)
    (folder / "short.yaml").write_text(yaml.safe_dump({"id": episode_id, "title": f"Title of {episode_id}", "series": series,
                                                       "beats": [{"text": "A shrimp punched through aquarium glass."}]}))
    (folder / "topic.json").write_text(json.dumps({"topic": "Peacock mantis shrimp (2004): the fastest punch", "series": series}))
    record = {"id": episode_id, "title": f"Title of {episode_id}", "buffer_post_id": f"post-{episode_id}", "status": state,
              "youtube_url": f"https://youtube.com/shorts/{video}", **(extra or {})}
    (folder / "publish.json").write_text(json.dumps(record))
    return folder


def test_breakout_queues_follow_ups_once(studio, monkeypatch):
    _episode(studio, "ep007", "hitVIDEO001")
    taken = datetime(2026, 10, 20, 9, tzinfo=timezone.utc)
    for n in range(6):
        day = taken - timedelta(days=6 - n)
        (studio / "analytics" / f"{day.date()}.json").write_text(json.dumps({"date": str(day.date()), "taken_at": day.isoformat(), "videos": [
            {"id": f"peerVIDEO0{n}", "title": "peer", "published": (day - timedelta(hours=30)).isoformat(), "views": 800}]}))
    (studio / "analytics" / "2026-10-20.json").write_text(json.dumps({"date": "2026-10-20", "taken_at": taken.isoformat(), "videos": [
        {"id": "hitVIDEO001", "title": "Title of ep007", "published": (taken - timedelta(hours=18)).isoformat(), "views": 9000}]}))
    calls = []

    def propose(short, known, count):
        calls.append(short)
        return [{"topic": "Odontomachus (2006): jaws that snap shut in a fraction of a millisecond", "wikipedia": "Odontomachus"},
                {"topic": "Flea (1967): a jump powered by a rubbery protein", "wikipedia": "Flea"},
                {"topic": "Elateridae (2020): the beetle that flips without legs", "wikipedia": "Elateridae"}]

    monkeypatch.setattr(growth, "propose_followups", propose)
    state = {}
    lines = auto.breakout_topics(auto.Run("test"), state)
    assert len(lines) == 1 and "ep007" in lines[0] and "11.2x" in lines[0]
    assert calls[0]["series"] == "Built Different" and calls[0]["hook"] == "A shrimp punched through aquarium glass."
    follow = [t for t in auto.calendar_topics(NOW.date()) if t["kind"] == "timely"]
    assert len(follow) == auto.FOLLOW_UPS and all(t["series"] == "Built Different" and t["why"].startswith("Follow-up to ep007")
                                                  for t in follow)
    assert json.loads((studio / "status" / "state.json").read_text())["breakouts"]["hitVIDEO001"]["added"] == 2
    # The same Short doesn't trigger again, and follow-ups don't count against the day's trending topics.
    assert auto.breakout_topics(auto.Run("test"), state) == [] and len(calls) == 1
    assert sum(1 for t in auto.calendar_topics(NOW.date()) if t["kind"] == "timely" and not t["why"].startswith("Follow-up")) == 0


def test_timely_short_is_scheduled_first_with_an_extra_slot(monkeypatch):
    queued_at = publish.next_slots(9, set(), per_day=3)
    monkeypatch.setattr(publish, "posts", lambda since=None, channel_id=None: [
        {"id": f"q{i}", "status": "scheduled", "dueAt": when.isoformat()} for i, when in enumerate(queued_at)])
    scheduled = []
    monkeypatch.setattr(publish, "schedule", lambda path, when: scheduled.append((path.parent.name, when)) or {"due_at": when.isoformat()})
    monkeypatch.setattr(auto, "slots_per_day", lambda today=None: 3)

    def ep(episode_id, timely, score):
        return {"id": episode_id, "folder": auto.EPISODES / episode_id, "state": "waiting", "title": episode_id, "series": "Nature's Record Breakers",
                "record": None, "held": {"scores": {"hook": score}}, "topic": {"timely": True} if timely else {}, "remote": None}

    monkeypatch.setattr(auto, "episodes", lambda: [ep("ep001", False, 9), ep("ep002", True, 1), ep("ep003", False, 8)])
    run = auto.Run("test")
    auto.publish_waiting(run)
    # Buffer holds 10, so one goes in: the timely Short, before the last of the queue rather than after it.
    assert [name for name, _ in scheduled] == ["ep002"]
    assert scheduled[0][1] < max(queued_at)


def _record_ep(episode_id, due, **extra):
    record = {"id": episode_id, "media_url": f"https://cdn/{episode_id}.mp4", "due_at": due.isoformat(), "media_bytes": 20_000_000,
              "status": "scheduled", **extra}
    return {"id": episode_id, "state": "scheduled", "record": record}


def test_crosspost_due_filters_and_orders():
    now = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)
    eps = [
        _record_ep("late", now + timedelta(days=2)),
        _record_ep("soon", now + timedelta(hours=3)),
        _record_ep("too-soon", now + timedelta(minutes=10)),
        _record_ep("done", now + timedelta(hours=5), crossposts={"tiktok": {"id": "x"}}),
        _record_ep("failed", now + timedelta(hours=5), crossposts={"tiktok": {"error": "no"}}),
        _record_ep("unmeasured", now + timedelta(hours=5), media_bytes=None),
        _record_ep("huge", now + timedelta(hours=5), media_bytes=90_000_000),
        {**_record_ep("waiting", now + timedelta(hours=5)), "state": "waiting"},
    ]
    assert [e["id"] for e in auto.crosspost_due(eps, "tiktok", now, 10, 40_000_000)] == ["soon", "late"]
    assert [e["id"] for e in auto.crosspost_due(eps, "tiktok", now, 1, 40_000_000)] == ["soon"]
    assert [e["id"] for e in auto.crosspost_due(eps, "instagram", now, 10, 40_000_000)] == ["soon", "done", "failed", "late"]


def test_caption_and_metadata():
    spec = ShortSpec.model_construct(id="ep001", title="The Fish That Was Supposed to Be Extinct", description="Why? See https://nhm.ac.uk/x now. " * 200,
                                     sources=["https://www.nhm.ac.uk/a", "https://www.nhm.ac.uk/b", "https://www.amnh.org/c"],
                                     hashtags=["#animals", "#Shorts", "#coelacanth", "#fossils"], synthetic_media=True)
    text = publish.caption(spec)
    assert len(text) <= publish.CAPTION_CHARS and text.startswith("The Fish That Was Supposed to Be Extinct\n\n")
    assert "#Shorts" not in text and "https://" not in text and text.endswith("#animals #coelacanth #fossils")
    short = publish.caption(ShortSpec.model_construct(id="e", title="T", description="D", sources=["https://www.nhm.ac.uk/a"],
                                                      hashtags=["#animals"], synthetic_media=False))
    assert "Sources: nhm.ac.uk" in short and "synthetic voice" in short
    assert publish._crosspost_metadata("instagram", spec) == {"instagram": {"type": "reel", "shouldShareToFeed": True, "isAiGenerated": True}}
    assert publish._crosspost_metadata("tiktok", spec) == {"tiktok": {"isAiGenerated": True}}


def test_crosspost_is_off_by_default_and_never_fails_the_run(studio, monkeypatch):
    monkeypatch.delenv("BUFFER_TIKTOK_CHANNEL_ID", raising=False)
    monkeypatch.delenv("BUFFER_INSTAGRAM_CHANNEL_ID", raising=False)
    assert publish.crosspost_channels() == {}
    due = (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()
    for episode_id in ("ep001", "ep002"):
        _episode(studio, episode_id, f"vid{episode_id}0000"[:11], state="scheduled",
                 extra={"due_at": due, "media_url": f"https://cdn/{episode_id}.mp4", "media_bytes": 1000})
    monkeypatch.setattr(auto, "_now", lambda: datetime.now(auto.IST))
    requests_made = []
    monkeypatch.setattr(publish, "posts", lambda since=None, channel_id=None: requests_made.append(channel_id) or [])
    run = auto.Run("test")
    auto.crosspost_scheduled(run)
    assert run.stages == [] and requests_made == []

    monkeypatch.setenv("BUFFER_TIKTOK_CHANNEL_ID", "tiktok-channel")

    def fake_crosspost(spec_path, service, channel_id, media_url, when):
        if spec_path.parent.name == "ep001":
            raise RuntimeError("Buffer rejected the tiktok post of ep001: bad field")
        return {"id": "tt-2", "status": "scheduled", "due_at": when.isoformat()}

    monkeypatch.setattr(publish, "crosspost", fake_crosspost)
    auto.crosspost_scheduled(run)
    assert run.errors == [] and run.stages[0]["ok"] and "scheduled ep002" in run.stages[0]["detail"]
    assert requests_made == ["tiktok-channel"]
    records = {p.parent.name: json.loads(p.read_text()) for p in (studio / "content" / "episodes").glob("*/publish.json")}
    assert records["ep002"]["crossposts"]["tiktok"]["id"] == "tt-2"
    assert "bad field" in records["ep001"]["crossposts"]["tiktok"]["error"]
    # Nothing left to do: no request at all.
    auto.crosspost_scheduled(run)
    assert requests_made == ["tiktok-channel"]
