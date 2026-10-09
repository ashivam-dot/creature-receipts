from datetime import datetime
from zoneinfo import ZoneInfo

from ytc.atlas import publish, writer
from ytc.atlas.data import Dataset

ET = ZoneInfo("America/New_York")


def _dataset() -> Dataset:
    values = {"IND": 0.9, "CHN": -0.2, "MDA": -1.8, "USA": 0.5, "JPN": -0.5, "BRA": 0.4, "DEU": -0.01, "MAF": -4.7}
    return Dataset(label="Population growth", unit="%", source="World Bank", license="CC BY 4.0", url="",
                   values=values, years={k: 2025 for k in values}, names={}, fetched="")


def test_country_values_belong_to_their_country():
    summary, allowed, owners = writer.facts(_dataset(), {"kind": "threshold", "at": 0}, "{v:.1f}%")
    assert writer.number_problems("Moldova is shrinking by 1.8%.", allowed, owners, ["MDA"]) == []
    assert writer.number_problems("Lithuania is shrinking by 1.8%.", allowed, owners, ["LTU"])
    assert writer.number_problems("India grows 0.9% a year.", allowed, owners, [])
    assert writer.number_problems("It grows 7.7% a year.", allowed, owners, ["IND"])


def test_tiny_places_stay_off_the_tour_and_superlatives_are_guarded():
    summary, _, owners = writer.facts(_dataset(), {"kind": "threshold", "at": 0}, "{v:.1f}%")
    assert "MAF" not in summary.split("Notable")[0].split("Year")[1]
    assert "too small to show" in summary
    assert not any("MAF" in isos for isos in owners.values())


def test_negative_zero_and_minus_signs():
    assert writer._say(-0.01, "{v:.1f}%") == "0.0%"
    draft = {"title": "t", "beats": [{"text": "Red shows Moldova at -1.8%.", "shot": "world", "isos": ["MDA"]}]}
    found = " ".join(writer.problems(draft, set(), {"1.8": {"MDA"}}, {"MDA": -1.8}))
    assert "'Red' describes the map" in found and "minus sign" in found


def test_no_filler_and_ratios_are_offered_and_bound_to_both_countries():
    ds = Dataset(label="Density", unit="per km²", source="World Bank", license="CC BY 4.0", url="",
                 values={"BGD": 1333.4, "AUS": 3.54, "IND": 488.0, "USA": 37.2, "JPN": 340.1, "NLD": 534.4},
                 years={k: 2023 for k in ("BGD", "AUS", "IND", "USA", "JPN", "NLD")}, names={}, fetched="")
    summary, allowed, owners = writer.facts(ds, {"kind": "bins"}, "{v:,.0f}")
    # Australia shows as "4", far from 3.54, so no ratio against it is offered; India to the USA is.
    assert "Australia's value" not in summary and "13 times" in summary
    assert owners["13"] == {"IND", "USA"}
    assert writer.number_problems("India has 13 times the USA's density.", allowed, owners, ["IND"]) == []
    assert writer.number_problems("Japan has 13 times that.", allowed, owners, ["JPN"])
    draft = {"title": "t", "beats": [{"text": "Bangladesh reaches 1,333 among these countries.", "shot": "world",
                                      "isos": ["BGD"]}]}
    found = " ".join(writer.problems(draft, allowed, owners, writer.visible(writer.drawable(ds))))
    assert "filler" in found


def test_quality_checks_every_ratio_against_the_data():
    from ytc.atlas import quality
    from ytc.atlas.episode import AtlasEpisode

    ds = Dataset(label="Density", unit="per km²", source="World Bank", license="CC BY 4.0", url="",
                 values={"BGD": 1333.4, "AUS": 3.54, "IND": 488.0, "USA": 37.2},
                 years={k: 2023 for k in ("BGD", "AUS", "IND", "USA")},
                 names={"BGD": "Bangladesh", "AUS": "Australia", "IND": "India", "USA": "United States"}, fetched="")
    ep = AtlasEpisode.model_validate({"id": "atlas999", "title": "t", "value_format": "{v:,.0f}",
                                      "dataset": {"kind": "worldbank", "label": "l", "source": "s"},
                                      "beats": [{"text": "x"}]})
    assert quality.ratio_errors("India has 13 times the density of the United States.", ep, ds) == []
    assert quality.ratio_errors("Bangladesh has 377 times Australia's density.", ep, ds) == []
    assert quality.ratio_errors("India has 20 times the density of the United States.", ep, ds)
    assert quality.ratio_errors("That's 13 times more.", ep, ds)
    assert quality.ratio_errors("13X THE PEOPLE", ep, ds, ["IND", "USA"]) == []
    assert quality.entity_value_errors("India has 13 times the density of the United States.", ep, ds) == []


def test_three_slots_a_day():
    now = datetime(2026, 10, 8, 10, 0, tzinfo=ET)
    assert publish.next_slot([], now) == datetime(2026, 10, 8, 12, 0, tzinfo=ET)
    taken = [datetime(2026, 10, 8, 12, 0, tzinfo=ET), datetime(2026, 10, 8, 16, 20, tzinfo=ET)]
    assert publish.next_slot(taken, now) == datetime(2026, 10, 8, 19, 0, tzinfo=ET)
    late = datetime(2026, 10, 8, 18, 45, tzinfo=ET)
    assert publish.next_slot([], late) == datetime(2026, 10, 9, 12, 0, tzinfo=ET)


def test_rank_title_only_when_true():
    from ytc.atlas import draw, render
    from ytc.atlas.episode import AtlasEpisode

    ds = _dataset()
    ep = AtlasEpisode.model_validate({"id": "atlas999", "title": "t", "value_format": "{v:.1f}%",
                                      "dataset": {"kind": "worldbank", "label": "l", "source": "s"},
                                      "beats": [{"text": "x", "shot": {"kind": "rank", "isos": ["IND", "USA", "BRA"]}}]})
    scale = draw.Scale("threshold", at=0)
    title, rows = render.rank_rows(["USA", "IND", "BRA"], ds, ep, scale, {})
    assert title == "Top 3" and [r[1] for r in rows] == ["0.9%", "0.5%", "0.4%"]
    title, _ = render.rank_rows(["USA", "IND", "JPN"], ds, ep, scale, {})
    assert title == ""


def test_sync_frees_the_video_only_once_sent(tmp_path, monkeypatch):
    import json

    from ytc.atlas import pipeline

    episodes, box = tmp_path / "atlas", tmp_path / "outbox"
    (episodes / "atlas001").mkdir(parents=True)
    (box / "atlas").mkdir(parents=True)
    video = box / "atlas" / "atlas001-ab.mp4"
    video.write_bytes(b"x")
    (episodes / "atlas001" / "ready.json").write_text(json.dumps({"modal_path": "atlas/atlas001-ab.mp4"}))
    topics = tmp_path / "topics.json"
    topics.write_text(json.dumps({"topics": [{"id": "t001", "status": "ready:atlas001"}]}))
    monkeypatch.setattr(pipeline, "EPISODES", episodes)
    monkeypatch.setattr(pipeline, "TOPICS", topics)
    monkeypatch.setenv("ATLAS_OUTBOX", str(box))
    record = {"id": "atlas001", "status": "scheduled", "due_at": "2026-10-08T12:00:00-04:00"}
    assert pipeline.sync({"atlas001": record}) == ["atlas001"]
    assert video.exists() and json.loads(topics.read_text())["topics"][0]["status"] == "used:atlas001"
    assert pipeline.sync({"atlas001": record}) == []
    assert pipeline.sync({"atlas001": record | {"status": "sent"}}) == ["atlas001"]
    assert not video.exists()


def test_topic_scales_are_checked_against_the_data():
    from ytc.atlas import topics

    vals = [float(v) for v in range(1, 101)]
    good = {"label": "Share", "value_format": "{v:.0f}%", "scale": {"kind": "bins", "edges": [10, 30, 50, 70],
                                                                    "labels": ["a", "b", "c", "d", "e"]}}
    assert topics.check(good, vals) == []
    outside = good | {"scale": {"kind": "bins", "edges": [0, 30, 50, 200], "labels": ["a", "b", "c", "d", "e"]}}
    assert "inside" in " ".join(topics.check(outside, vals))
    edge = good | {"scale": {"kind": "threshold", "at": 99.5, "labels": ["x", "y"]}}
    assert "percentile" in " ".join(topics.check(edge, vals))
    assert topics.NO_GO.search("Armed forces personnel (% of total labor force)")
    assert topics.RATIO.search("Individuals using the Internet (% of population)")


def test_scoreboard_is_rewritten_in_place(tmp_path):
    from ytc.atlas import stats

    path = tmp_path / "LEARNINGS.md"
    path.write_text("# x\n\n## Scoreboard\n\nold\n\n## Log\n\n- kept\n")
    stats._scoreboard(path, [{"id": "atlas001", "title": "T", "format": "map_reveal",
                              "published": "2026-10-08T16:00:05+00:00", "views": 120, "likes": 3,
                              "views_per_hour": 12.0}])
    text = path.read_text()
    assert "| atlas001 T | map_reveal | 2026-10-08 16:00 UTC | 120 | 3 | 12.0 |" in text
    assert "old" not in text and "- kept" in text
