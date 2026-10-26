"""Batch 3 of the revenue push (2026-10-22): the title lint (gap audit #9) and the description's dataset citation
and editorial-process line. The bad titles are the real ones that went out on Atlas Shorts."""

import pytest

from ytc.atlas import geo, pipeline, publish, quality, writer
from ytc.atlas.data import Dataset
from ytc.atlas.episode import AtlasEpisode


def _dataset(label="Physicians (per 1,000 people)", indicator="SH.MED.PHYS.ZS", values=None, unit="per 1,000") -> Dataset:
    world = geo.world()
    vals = values or {iso: float(i + 1) for i, iso in enumerate(sorted(world))}
    return Dataset(label, unit, "WHO via World Bank", "CC BY 4.0", f"https://data.worldbank.org/indicator/{indicator}",
                   vals, {k: 2023 for k in vals}, {k: world[k].name for k in vals if k in world},
                   definition="Physicians include generalist and specialist medical practitioners.",
                   indicator=indicator)


def _ep(title: str, ds: Dataset, episode_id: str = "atlas900") -> AtlasEpisode:
    return AtlasEpisode.model_validate({
        "id": episode_id, "title": title, "description": "Where doctors are.", "hashtags": ["#maps"],
        "dataset": {"kind": "worldbank", "indicator": ds.indicator, "label": ds.label, "unit": ds.unit,
                    "source": ds.source}, "beats": [{"text": "Doctors are spread unevenly."}]})


def _kind(**over):
    return {"zero_ok": False, "falls": set(), "quoted": "", "gross": False, "growth": False} | over


# (published id, the exact title, its dataset label, its indicator, what the lint must say)
BAD = [
    ("atlas053", "Why Greece Has 165.1% College Enrollment", "School enrollment, tertiary (% gross)",
     "SE.TER.ENRR", "over 100%"),
    ("atlas021", "Cuba has 9.5 doctors while Niger has 0.0", "Physicians (per 1,000 people)", "SH.MED.PHYS.ZS",
     "reads as nothing"),
    ("atlas056", "Where More Boys Are Born: 1.01 to 1.11 Worldwide", "Sex ratio at birth (male births per female births)",
     "SP.POP.BRTH.MF", "over-precise"),
    ("atlas075", "Bulgaria Has 93.8 Bank Branches to DR Congo 0.6", "Bank branches per 100,000 adults",
     "FB.CBK.BRCH.P5", "table row"),
    ("atlas054", "Household Goods Cost 130 in Iceland but 100 in USA", "Price level index (US = 100)",
     "PA.NUS.PRVT.PLI", "index"),
]
LOWERCASE = [  # all six shipped with a lowercase "places"
    ("atlas030", "places Where One City Holds 92% of City Dwellers"),
    ("atlas028", "61 places Still Have Most People Outside Cities"),
    ("atlas019", "The Emptiest and Most Crowded places"),
    ("atlas017", "The Youngest and Oldest places on Earth"),
    ("atlas002", "45 places with Falling Populations"),
    ("atlas004", "47 places Where Life Expectancy Reaches 80"),
]


@pytest.mark.parametrize("episode_id,title,label,indicator,expected", BAD, ids=[b[0] for b in BAD])
def test_the_published_bad_titles_are_held(episode_id, title, label, indicator, expected):
    kind = _kind(**writer.measure_kind(label, indicator))
    problems = writer.title_lint(writer.fix_title(title), label=label, indicator=indicator, kind=kind)
    assert any(expected in p for p in problems), problems


@pytest.mark.parametrize("episode_id,title", LOWERCASE, ids=[t[0] for t in LOWERCASE])
def test_lowercase_titles_are_held_raw_and_repaired_for_free(episode_id, title):
    assert any("Title Case" in p for p in writer.title_lint(title))
    fixed = writer.fix_title(title)
    assert not fixed.split()[0][:1].islower() and " places" not in fixed and "Places" in fixed
    assert writer.title_lint(fixed, kind=_kind()) == []


@pytest.mark.parametrize("title", [
    "Is YOUR Country One of the Most Crowded?",
    "47 Places Where Life Expectancy Reaches 80",
    "Happiness Out of 10: Who Scores Highest?",
    "Cuba Has 9.5 Doctors per 1,000. Does YOUR Country?",
    "The Top 10 Places for Doctors",
    "Where a Coffee Costs $4.50",
    "Places Where Under 0.25 Doctors Serve 1,000 People",
])
def test_ordinary_titles_pass(title):
    assert writer.title_lint(title, label="Physicians (per 1,000 people)", indicator="SH.MED.PHYS.ZS",
                             kind=_kind()) == []


def test_decimals_codes_brackets_and_labels():
    assert any("over-precise" in p for p in writer.title_lint("Places With 0.123 Doctors"))
    assert any("indicator code" in p for p in writer.title_lint("Where SH.MED.PHYS.ZS Is Highest"))
    assert any("indicator code" in p for p in writer.title_lint("Where SE.TER.ENRR Is Highest",
                                                                 indicator="SE.TER.ENRR"))
    assert any("column header" in p for p in writer.title_lint("Doctors (per 1,000 People) Around the World"))
    label = "Population, total"
    assert any("copies the dataset label" in p for p in writer.title_lint("Population, Total: Who Leads?", label=label))


def test_over_100_percent_passes_only_when_it_is_legitimate():
    title = "Where Prices Rose 512% in a Year"
    assert any("over 100%" in p for p in writer.title_lint(title, kind=_kind()))
    assert writer.title_lint(title, kind=_kind(growth=True)) == []  # a growth rate (.ZG)
    assert writer.title_lint("Where Money Fell -512% in Value", kind=_kind()) == []  # signed
    gross = _kind(**writer.measure_kind("School enrollment, tertiary (% gross)", "SE.TER.ENRR"))
    assert writer.title_lint("Greece's Gross Enrollment Ratio Is 165%", kind=gross) == []
    assert any("over 100%" in p for p in writer.title_lint("Greece Has 165% College Enrollment", kind=gross))


def test_a_real_zero_may_be_said_but_never_as_0_point_0():
    assert writer.title_lint("Places With 0 Volcanoes", kind=_kind(zero_ok=True)) == []
    assert any("reads as nothing" in p for p in writer.title_lint("Places With 0 Volcanoes", kind=_kind()))
    assert any("reads as nothing" in p for p in writer.title_lint("Places With 0.0 Volcanoes", kind=_kind(zero_ok=True)))


def test_the_writers_hard_check_runs_the_title_lint():
    draft = {"title": "Bulgaria Has 93.8 Bank Branches to DR Congo 0.6", "hook_text": "BANKS", "description": "d",
             "card_lines": [], "opening_options": [], "beats": [{"text": "Banks.", "shot": "world", "isos": []}]}
    problems = writer.problems(draft, {"93.8", "0.6"}, {}, {}, label="Bank branches per 100,000 adults",
                               indicator="FB.CBK.BRCH.P5")
    assert any(p.startswith("title:") and "table row" in p for p in problems)


def test_the_review_holds_a_bad_title_before_any_model_call(tmp_path, monkeypatch):
    monkeypatch.setattr(quality.llm, "generate", lambda *a, **k: pytest.fail("model called for a held title"))
    ds = _dataset()
    with pytest.raises(ValueError, match="title: the title isn't in Title Case"):
        quality.review(_ep("Where the doctors are", ds), ds, tmp_path)


def test_schedule_holds_a_bad_title_before_hosting_or_buffer(tmp_path, monkeypatch):
    for name in ("posts", "host_video", "fetch_video", "_buffer"):
        monkeypatch.setattr(publish.pub, name, lambda *a, _n=name, **k: pytest.fail(f"{_n} called for a held title"))
    ds = _dataset()
    with pytest.raises(ValueError, match="atlas900: title held.*reads as nothing"):
        publish.schedule(_ep("Cuba Has 9.5 Doctors While Niger Has 0.0", ds), tmp_path, ds, tmp_path / "v.mp4")


def test_a_parked_short_with_a_held_title_is_not_reserve(tmp_path):
    ds = _dataset()
    ds.save(tmp_path / "data.json")
    _ep("Cuba Has 9.5 Doctors While Niger Has 0.0", ds).save(tmp_path / "atlas.yaml")
    assert any("reads as nothing" in p for p in pipeline.title_held(tmp_path))
    assert pipeline._accepted(tmp_path) is False
    _ep("Cuba Has 9.5 Doctors per 1,000. Does YOUR Country?", ds).save(tmp_path / "atlas.yaml")
    assert pipeline.title_held(tmp_path) == []
    assert pipeline.title_held(tmp_path / "missing") == []  # unreadable: left to the receipt checks


def test_description_cites_dataset_indicator_year_and_the_editorial_process():
    ds = _dataset()
    text = publish.description(_ep("T", ds), ds)
    assert "Data: Physicians (per 1,000 people), WHO via World Bank, 2023 (CC BY 4.0). Indicator SH.MED.PHYS.ZS." in text
    assert publish.EDITORIAL in text and text.count("How this Short is made") == 1
    assert "synthetic voice" in text and "checked in code against the data" in text
    owid = _dataset(indicator="share-of-population-urban")
    assert "Indicator" not in publish.description(_ep("T", owid), owid).split("\n\n")[1]


def _upgrade_run(monkeypatch, tmp_path, records):
    """run() with one waiting Short (atlas075) that isn't accepted, as on main: its title fails the bare-value rule
    and its publish.json isn't synced yet. Returns the ids make() was asked to re-make."""
    from ytc.atlas import pipeline, stats, topics
    folder = tmp_path / "atlas075"
    folder.mkdir()
    remade = []
    for name, value in (("sync", lambda: []), ("retire_withdrawn", lambda: []), ("_waiting", lambda: [folder]),
                        ("_accepted", lambda f: False), ("_topic_of", lambda i: {"id": "t053", "status": "ready:" + i}),
                        ("_records", lambda *a: records), ("ready", lambda: [folder] * 9),
                        ("_catalogue", lambda: {"topics": []}),
                        ("_mark", lambda *a, **k: (_ for _ in ()).throw(AssertionError("topic reopened"))),
                        ("make", lambda topic, episode_id: remade.append(episode_id) or (_ for _ in ()).throw(
                            RuntimeError("re-make")))):
        monkeypatch.setattr(pipeline, name, value)
    monkeypatch.setattr(pipeline, "HOLD", tmp_path / "no-hold.json")
    monkeypatch.setattr(stats, "update", lambda *a: {})
    monkeypatch.setattr(topics, "refill", lambda *a: [])
    pipeline.run(reserve=0)
    return remade, folder


def test_a_short_the_publisher_already_sent_is_never_remade_or_reopened(monkeypatch, tmp_path):
    remade, folder = _upgrade_run(monkeypatch, tmp_path, {"atlas075": {"status": "sent"}})
    assert remade == [] and folder.is_dir()


def test_no_upgrade_when_the_publishers_records_cannot_be_read(monkeypatch, tmp_path):
    remade, folder = _upgrade_run(monkeypatch, tmp_path, None)
    assert remade == [] and folder.is_dir()


def test_an_unpublished_held_short_is_still_upgraded(monkeypatch, tmp_path):
    from ytc.atlas import pipeline
    monkeypatch.setattr(pipeline, "_tidy", lambda f: None)
    with pytest.raises(AssertionError, match="topic reopened"):
        _upgrade_run(monkeypatch, tmp_path, {})


class _Call:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result

    def next_chunk(self):
        return None, self.result


class _YouTube:
    def __init__(self, channel=publish.CHANNEL_ID):
        self.channel, self.inserted = channel, []

    def channels(self):
        return self

    def playlistItems(self):
        return self

    def videos(self):
        return self

    def list(self, **params):
        if "mine" in params:
            return _Call({"items": [{"id": self.channel, "contentDetails": {"relatedPlaylists": {"uploads": "UU"}}}]})
        if "playlistId" in params:
            return _Call({"items": [{"contentDetails": {"videoId": "old1"}}]})
        return _Call({"items": [{"id": "old1", "snippet": {"description": "Atlas episode: atlas800"},
                                 "status": {"publishAt": "2026-10-28T16:00:00Z"}}]})

    def insert(self, **params):
        self.inserted.append(params)
        return _Call({"id": "new1"})


def test_direct_upload_is_private_until_its_slot_and_never_uploads_an_episode_twice(tmp_path):
    from datetime import datetime, timezone

    ds = _dataset()
    yt = _YouTube()
    video = tmp_path / "v.mp4"
    video.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    existing = publish.recent_uploads(yt)
    taken = [datetime(2026, 10, 28, 16, tzinfo=timezone.utc)]
    record = publish.upload(_ep("Is YOUR Country Short of Doctors?", ds), tmp_path, ds, video, taken, yt=yt,
                            existing=existing)
    body = yt.inserted[0]["body"]
    assert record["route"] == "youtube" and record["youtube_video_id"] == "new1"
    assert body["status"]["privacyStatus"] == "private" and body["status"]["publishAt"].endswith("Z")
    assert body["status"]["containsSyntheticMedia"] and "Atlas episode: atlas900" in body["snippet"]["description"]
    again = tmp_path / "again"
    again.mkdir()
    twin = publish.upload(_ep("Is YOUR Country Short of Doctors?", ds, "atlas800"), again, ds, video, taken, yt=yt,
                          existing=existing)
    assert twin["youtube_video_id"] == "old1" and len(yt.inserted) == 1
    with pytest.raises(RuntimeError, match="not @atlasinnumbers"):
        publish.recent_uploads(_YouTube(channel="UCother"))
    # The slot of an upload whose record was lost is still taken.
    first = publish.next_slot([])
    lost = [{"id": "x", "snippet": {"description": ""},
             "status": {"publishAt": first.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")}}]
    third = tmp_path / "third"
    third.mkdir()
    record = publish.upload(_ep("Is YOUR Country Short of Doctors?", ds, "atlas901"), third, ds, video, [], yt=yt,
                            existing=lost)
    assert datetime.fromisoformat(record["due_at"]) > first
    stuck = [{"id": "y", "snippet": {"description": "Atlas episode: atlas902"}, "status": {"privacyStatus": "private"}}]
    fourth = tmp_path / "fourth"
    fourth.mkdir()
    with pytest.raises(RuntimeError, match="private with no schedule"):
        publish.upload(_ep("Is YOUR Country Short of Doctors?", ds, "atlas902"), fourth, ds, video, [], yt=yt,
                       existing=stuck)


def test_withdraw_keeps_uploads_private_and_clears_their_schedule():
    class _Videos(_YouTube):
        def __init__(self):
            super().__init__()
            self.updates = []

        def list(self, **params):
            return _Call({"items": [
                {"id": "a", "snippet": {"channelId": publish.CHANNEL_ID},
                 "status": {"privacyStatus": "private", "publishAt": "2026-11-02T17:00:00Z", "embeddable": True}},
                {"id": "b", "snippet": {"channelId": publish.CHANNEL_ID}, "status": {"privacyStatus": "public"}},
                {"id": "c", "snippet": {"channelId": "UCother"}, "status": {"privacyStatus": "private"}}]})

        def update(self, **params):
            self.updates.append(params["body"])
            return _Call({})

    yt = _Videos()
    assert publish.withdraw(["a", "b", "c"], yt=yt) == ["a"]
    assert yt.updates == [{"id": "a", "status": {"embeddable": True, "privacyStatus": "private", "publishAt": None}}]


def test_three_slots_a_day():
    from datetime import datetime

    taken = []
    for _ in range(6):
        taken.append(publish.next_slot(taken, datetime(2026, 11, 2, 6, tzinfo=publish.pub.AUDIENCE_TZ)))
    assert [t.hour for t in taken] == [12, 16, 19, 12, 16, 19] and taken[3].day == 3


def test_order_never_puts_two_of_one_look_in_a_row(tmp_path):
    from datetime import datetime, timezone

    now = datetime(2026, 10, 27, 12, tzinfo=timezone.utc)
    at = now.isoformat()
    last = _parked_ready(tmp_path, "atlas300", family="health", look="versus", score=10, rendered_at=at)
    a = _parked_ready(tmp_path, "atlas301", family="wealth", look="versus", score=30, rendered_at=at)
    b = _parked_ready(tmp_path, "atlas302", family="energy", look="spotlight", score=20, rendered_at=at)
    assert publish.order([a, b], last, now) == [b, a]


def _parked_ready(root, name, **record):
    import json

    folder = root / name
    folder.mkdir()
    (folder / "ready.json").write_text(json.dumps({"id": name, **record}))
    return folder
