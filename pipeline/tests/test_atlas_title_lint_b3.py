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
