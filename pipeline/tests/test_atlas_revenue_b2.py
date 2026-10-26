"""Batch 2 of the revenue push (2026-10-22): curiosity titles, the grounded why-the-gap beat, topic families,
tags and hashtags, two slots a day and score-ordered publishing."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from ytc.atlas import geo, pipeline, publish, topics, writer
from ytc.atlas.data import Dataset
from ytc.atlas.episode import AtlasEpisode

@pytest.fixture(autouse=True)
def _fresh_run(monkeypatch):
    monkeypatch.setattr(pipeline, "TRIED", [])


DEFINITION = ("International migrant stock is the number of people born in a country other than that in which they "
              "live. It also includes refugees.")


def _dataset() -> Dataset:
    world = geo.world()
    vals = {iso: float(i + 1) for i, iso in enumerate(sorted(world))}
    return Dataset("Share of people born abroad", "%", "UN DESA via World Bank", "CC BY 4.0",
                   "https://data.worldbank.org/indicator/SM.POP.TOTL.ZS", vals, {k: 2024 for k in vals},
                   {k: world[k].name for k in vals}, definition=DEFINITION, indicator="SM.POP.TOTL.ZS")


TOPIC = {"id": "t900", "topic": "Migrants: the share born abroad", "format": "map_reveal",
         "dataset": {"kind": "worldbank", "indicator": "SM.POP.TOTL.ZS", "label": "Share of people born abroad",
                     "unit": "%", "source": "UN DESA via World Bank"},
         "hashtags": ["#maps','#geography','#migrants"], "definition_text": DEFINITION}


def _draft(title: str, basis: str = "", why: str = "It counts people born in another country.") -> dict:
    return {"title": title, "hook_text": "BORN ELSEWHERE", "description": "Who was born abroad.",
            "card_lines": ["Born abroad?", "Share born abroad"], "opening_options": [],
            "beats": [{"text": "Half of Qatar was born somewhere else.", "shot": "world", "isos": []},
                      {"text": why, "shot": "world", "isos": [], **({"basis": basis} if basis else {})},
                      {"text": "How many of your neighbours were born abroad?", "shot": "card"}]}


# --- titles -------------------------------------------------------------------------------------------------------

def test_curiosity_titles_pass_and_flat_or_overclaimed_titles_are_noted():
    assert writer.title_problems("Is YOUR Country One of the Most Crowded?") == []
    assert writer.title_problems("The Countries Where Almost Everyone Is Online") == []
    assert writer.title_problems("Countries Where Banks Basically Don't Exist") == []
    assert writer.title_problems("Countries Ranked by How Crowded They Are", ranked_ok=True) == []
    assert any("flatly" in p for p in writer.title_problems("Bangladesh Has 1,333 People per Square Kilometre"))
    assert any("flatly" in p for p in writer.title_problems("Places Where 1,333 Beats 4"))
    assert any("don't exist" in p.lower() for p in writer.title_problems("The Countries Where Banks Don't Exist"))
    assert any("nobody" in p.lower() for p in writer.title_problems("The Countries Where Nobody Drives"))
    # A definition says what is counted, never why, so every "Why" title is noted.
    assert any("'Why'" in p for p in writer.title_problems("Why Japan Is Less Crowded Than You Think"))
    assert "Never start with\n  \"Why\"" in writer.PROMPT and "WAY\n  Less Crowded" not in writer.PROMPT
    assert any("rank shot" in p for p in writer.title_problems("Countries Ranked by Crowds"))
    assert any("capitals" in p for p in writer.title_problems("Is YOUR Country WAY More Crowded?"))
    assert writer.title_problems("Is the USA More Crowded Than YOUR Country?") == []
    assert any("'!'" in p for p in writer.title_problems("Is YOUR Country Crowded!"))


def test_a_number_in_the_title_must_still_be_a_checked_value():
    # The hard rule is unchanged: a title number not in the data summary stops the draft.
    draft = _draft("Is YOUR Country One of the 7 Most Crowded?")
    assert any("title: the number 7" in p for p in writer.problems(draft, {"92"}, {}, {}))


# --- why the gap --------------------------------------------------------------------------------------------------

def test_basis_must_be_copied_from_the_definition_and_about_the_beat():
    assert writer.grounded("people born in a country other than that in which they live",
                           "It counts people born in another country.", DEFINITION)
    assert not writer.grounded("people who moved for jobs in oil", "It counts people born abroad.", DEFINITION)
    assert not writer.grounded("It also includes", "It also includes refugees.", DEFINITION)  # under 4 words
    assert not writer.grounded("also includes refugees too", "Refugees count.", DEFINITION)
    assert writer.grounded("It also includes refugees.", "Refugees are in the count too.", DEFINITION)


def test_unsourced_causes_and_bad_bases_are_style_notes_and_a_grounded_why_clears_them():
    loose = _draft("Why Qatar Is Mostly Born Abroad", why="Qatar is born abroad because of oil jobs.")
    notes = " ".join(writer.style_problems(loose, DEFINITION))
    assert "'because' gives a cause" in notes and "'Why'" in notes
    bad = _draft("Is YOUR Country Born Abroad?", basis="workers drawn by oil money")
    assert "basis must copy" in " ".join(writer.style_problems(bad, DEFINITION))
    good = _draft("Is YOUR Country Mostly Born Abroad?", basis="people born in a country other than that in which they live")
    assert writer.style_problems(good, DEFINITION) == []
    two = _draft("Is YOUR Country Born Abroad?", basis="It also includes refugees.", why="Refugees count too.")
    two["beats"].insert(1, {"text": "It counts people born in another country.", "shot": "world",
                            "basis": "people born in a country other than that in which they live"})
    assert "at most one why-the-gap" in " ".join(writer.style_problems(two, DEFINITION))


def _write(monkeypatch, drafts, hard=lambda draft: []):
    calls = []
    monkeypatch.setattr(writer.llm, "generate", lambda prompt, **k: calls.append(prompt) or drafts[min(len(calls), len(drafts)) - 1])
    monkeypatch.setattr(writer, "problems", lambda draft, *a, **k: hard(draft))
    return writer.write(dict(TOPIC), _dataset(), "atlas900"), calls


def test_style_rules_get_one_rewrite_then_are_advisory(monkeypatch):
    # A draft that passes every hard check gets one rewrite for style, not TRIES: each is a model call and minutes.
    flat = _draft("Qatar Has 77 Percent Born Abroad")
    ep, calls = _write(monkeypatch, [flat])
    assert len(calls) == 2 and ep.title == "Qatar Has 77 Percent Born Abroad"
    assert "frame it as curiosity" in calls[1]
    ep, calls = _write(monkeypatch, [flat, _draft("Is YOUR Country Born Abroad?")])
    assert len(calls) == 2 and ep.title == "Is YOUR Country Born Abroad?"


def test_style_notes_never_join_a_hard_failures_feedback(monkeypatch):
    flat = _draft("Qatar Has 77 Percent Born Abroad")
    fixed = _draft("Qatar Has 77 Percent Born Abroad", why="It counts people born in another country, refugees too.")
    ep, calls = _write(monkeypatch, [flat, fixed, fixed], hard=lambda d: ["beat 2: boom"] if d is flat else [])
    assert "beat 2: boom" in calls[1] and "frame it as curiosity" not in calls[1].split("Last draft:")[0]
    # Once the hard rules pass, the style note gets its one rewrite.
    assert "frame it as curiosity" in calls[2] and len(calls) == 3


def test_a_style_rewrite_that_breaks_a_hard_rule_never_costs_the_story(monkeypatch):
    first = _draft("Qatar Has 77 Percent Born Abroad")
    worse = _draft("Is YOUR Country Born Abroad?")
    ep, calls = _write(monkeypatch, [first, worse], hard=lambda d: ["boom"] if d["title"].startswith("Is") else [])
    assert ep.title == "Qatar Has 77 Percent Born Abroad" and len(calls) == 2


def test_hard_rules_still_stop_a_story(monkeypatch):
    with pytest.raises(RuntimeError, match="no draft passed"):
        _write(monkeypatch, [_draft("Is YOUR Country Born Abroad?")], hard=lambda d: ["the number 7 isn't in the data"])


def test_episode_keeps_only_a_grounded_basis_and_records_tags_and_clean_hashtags(monkeypatch):
    good = _draft("is YOUR country mostly born abroad?", basis="people born in a country other than that in which they live")
    ep, calls = _write(monkeypatch, [good])
    assert len(calls) == 1 and ep.title == "Is YOUR Country Mostly Born Abroad?"
    assert ep.beats[1].basis == "people born in a country other than that in which they live"
    assert ep.hashtags == ["#migration", "#migrants", "#maps"]
    assert ep.tags[:2] == ["migration", "share of people born abroad"] and ep.tags[-2:] == ["world map", "data"]
    assert len(ep.tags) == 6  # family, label, the top and bottom places, world map, data
    ungrounded = _draft("Is YOUR Country Born Abroad?", basis="workers drawn by oil money")
    ep, _ = _write(monkeypatch, [ungrounded])
    assert all(not b.basis for b in ep.beats)
    # Old records without tags or bases still load, and new ones round-trip.
    AtlasEpisode.model_validate(ep.model_dump(exclude_defaults=True))


def test_hashtags_drop_mangled_refill_output():
    assert writer.hashtags({"topic": "Global Consumer Price Inflation Rates", "hashtags": ["#maps改革", "#economics"]}) == \
        ["#economy", "#economics", "#maps"]
    assert writer.hashtags({"topic": "Where Food Dominates Manufacturing", "hashtags": []}) == \
        ["#data", "#maps", "#geography"]


def test_why_brief_keeps_never_invent_causes():
    assert "Never invent causes" in writer.PROMPT and '"basis"' in writer.PROMPT
    assert "basis" in writer.SCHEMA["properties"]["beats"]["items"]["properties"]


# --- topics -------------------------------------------------------------------------------------------------------

def test_families_rank_high_pull_topics_over_the_obscure_tail():
    t = lambda topic, ind, label="": {"topic": topic, "dataset": {"indicator": ind, "label": label}}  # noqa: E731
    assert (topics.family(t("Economic output per person", "NY.GDP.PCAP.CD")), topics.pull(t("x", "NY.GDP.PCAP.CD"))) == ("wealth", 3)
    assert topics.family(t("Migrants: the share born abroad", "SM.POP.TOTL.ZS")) == "migration"
    assert topics.family(t("The emptiest and most crowded countries", "EN.POP.DNST")) == "population"
    assert topics.family(t("Where people live past 80", "SP.DYN.LE00.IN")) == "health"
    assert topics.family(t("Lights on: access to electricity", "EG.ELC.ACCS.ZS")) == "energy"  # not "city"
    assert topics.pull(t("How Much of Imports Is Food", "TM.VAL.FOOD.ZS.UN")) == 0
    assert topics.pull(t("Global Container Shipping Connectivity", "IS.SHP.GCNW.XQ")) == 0
    # A catalogue family FAMILIES doesn't know is the one its keywords match, so "food" after "health" is a repeat.
    assert topics.family({"family": "food", "topic": "Calories on the plate", "dataset": {}}) == "health"
    assert topics.pull({"family": "food", "topic": "Calories on the plate", "dataset": {}}) == 3
    assert topics.family({"family": "people", "topic": "How good people say their life is",
                          "dataset": {"label": "Life rating (Cantril ladder)"}}) == "happiness"
    assert topics.family({"family": "population", "topic": "Calories", "dataset": {}}) == "population"
    assert topics.family({"family": "seas", "topic": "Something unmatched", "dataset": {}}) == "seas"
    # The decorum gate is untouched: no military family, and NO_GO still bars it.
    assert "military" not in {f[0] for f in topics.FAMILIES} and topics.NO_GO.search("Military expenditure")


def _catalogue(tmp_path, monkeypatch, rows):
    path = tmp_path / "topics.json"
    path.write_text(json.dumps({"topics": rows}))
    monkeypatch.setattr(pipeline, "TOPICS", path)


def test_pick_prefers_pull_never_repeats_the_last_family_and_swaps_a_repeated_format(tmp_path, monkeypatch):
    ds = lambda ind, label: {"indicator": ind, "label": label}  # noqa: E731
    _catalogue(tmp_path, monkeypatch, [
        {"id": "t1", "topic": "Economic output per person", "dataset": ds("NY.GDP.PCAP.CD", "GDP per person"),
         "format": "map_reveal", "status": "used:atlas010"},
        {"id": "t2", "topic": "Income inequality", "dataset": ds("SI.POV.GINI", "Gini index"), "format": "rank_ladder",
         "status": "open"},
        {"id": "t3", "topic": "Container shipping", "dataset": ds("IS.SHP.GCNW.XQ", "Liner shipping connectivity"),
         "format": "rank_ladder", "status": "open"},
        {"id": "t4", "topic": "Share born abroad", "dataset": ds("SM.POP.TOTL.ZS", "Share of people born abroad"),
         "format": "map_reveal", "status": "open"}])
    chosen = pipeline.pick()
    # Not t2 (wealth again), not t3 (obscure); the format rotates on from the last Short's map reveal.
    assert chosen["id"] == "t4" and chosen["format"] == "versus"
    saved = json.loads(pipeline.TOPICS.read_text())["topics"][3]
    assert saved["format"] == "map_reveal"  # pick() itself changes nothing on disk
    pipeline._mark("t4", "making:atlas011", format=chosen["format"])
    saved = json.loads(pipeline.TOPICS.read_text())["topics"][3]
    assert (saved["status"], saved["format"]) == ("making:atlas011", "versus")


def test_formats_rotate_so_no_two_shorts_in_a_row_share_a_look():
    assert pipeline.next_format([]) == "map_reveal"
    assert pipeline.next_format(["map_reveal"]) == "versus"
    assert pipeline.next_format(["versus", "map_reveal"]) == "rank_ladder"
    # Older Shorts made before the rotation were all map reveals and ladders: the unused formats come first.
    assert pipeline.next_format(["rank_ladder", "map_reveal", "rank_ladder", "map_reveal"]) == "versus"
    made, recent = [], []
    for _ in range(10):
        made.append(pipeline.next_format(recent))
        recent = made[::-1][:4]
    assert all(a != b for a, b in zip(made, made[1:])) and set(made[:5]) == set(pipeline.ROTATION)


def test_a_format_whose_drafts_fail_does_not_take_every_try_of_a_run(tmp_path, monkeypatch):
    ds = lambda ind, label: {"indicator": ind, "label": label}  # noqa: E731
    _catalogue(tmp_path, monkeypatch, [
        {"id": "t1", "topic": "Economic output per person", "dataset": ds("NY.GDP.PCAP.CD", "GDP per person"),
         "format": "map_reveal", "status": "used:atlas010"},
        *({"id": f"t{i}", "topic": f"Topic {i}", "dataset": ds(f"X.Y{i}.Z", f"Label {i}"), "status": "open"}
          for i in range(2, 6))])
    formats = []
    for _ in range(4):
        chosen = pipeline.pick()
        formats.append(chosen["format"])
        pipeline._mark(chosen["id"], "failed:ValueError")
    assert len(set(formats)) == 4 and "map_reveal" not in formats


def test_format_note_title_examples_pass_the_title_rules():
    for title in ("Which Country Has the MOST Doctors?", "Is INDIA Near the Top for Renewable Power?",
                  "How Does the USA Compare on Savings?", "India vs China: Who Saves More?",
                  "Countries Ranked by How Crowded They Are"):
        assert writer.title_problems(title, ranked_ok=True) == [], title
    for title in ("Which Country Has the MOST Doctors?", "Is INDIA Near the Top for Renewable Power?"):
        assert writer.title_problems(title) == [], title


def test_each_format_has_its_own_look():
    from ytc.atlas.cinema import film, looks
    seen = [looks.look(f) for f in pipeline.ROTATION]
    assert len({lk.name for lk in seen}) == len(seen) and len({lk.accent for lk in seen}) == len(seen)
    assert len({lk.voice.voice for lk in seen}) == len(seen)
    film.apply_look("versus")
    assert film.ACCENT == looks.LOOKS["versus"].accent and film.VOICE.voice == "bm_george"
    film.apply_look(None)
    assert film.LOOK is looks.DEFAULT


def test_refill_does_not_count_the_obscure_tail_as_stock(monkeypatch):
    obscure = [{"id": f"t{i}", "topic": "Food share of imports", "status": "open",
                "dataset": {"indicator": f"TM.VAL.{i}"}} for i in range(topics.MIN_OPEN)]
    asked = []
    monkeypatch.setattr(topics, "indicators", lambda: [{"id": "IS.SHP.GCNW.XQ", "name": "Liner shipping connectivity index", "note": ""},
                                                       {"id": "NY.GNP.PCAP.CD", "name": "GNI per capita (current US$)", "note": ""}])
    monkeypatch.setattr(topics.llm, "generate", lambda prompt, **k: asked.append(prompt) or {"ids": []})
    assert topics.refill({"topics": obscure}) == []
    assert asked and "NY.GNP.PCAP.CD" in asked[0] and "IS.SHP.GCNW.XQ" not in asked[0]
    good = [{"id": f"g{i}", "topic": "Life expectancy", "status": "open", "dataset": {"indicator": "SP.DYN.LE00.IN"}}
            for i in range(topics.MIN_OPEN)]
    monkeypatch.setattr(topics, "indicators", lambda: pytest.fail("refilled a stocked catalogue"))
    assert topics.refill({"topics": good}) == []


def test_ready_record_scores_by_pull_less_media_warnings(tmp_path, monkeypatch):
    _catalogue(tmp_path, monkeypatch, [{"id": "t1", "topic": "Share born abroad", "status": "making:atlas011",
                                        "dataset": {"indicator": "SM.POP.TOTL.ZS"}}])
    (tmp_path / "qa.json").write_text(json.dumps({"warnings": ["beat 2 heard differently"]}))
    assert pipeline.score(tmp_path, "t1") == {"family": "migration", "pull": 3, "score": 29}


# --- publishing ---------------------------------------------------------------------------------------------------

def _parked(root, name, **record):
    folder = root / name
    folder.mkdir()
    (folder / "ready.json").write_text(json.dumps({"id": name, **record}))
    return folder


def test_order_puts_the_best_first_without_repeating_a_family_and_never_lets_one_go_stale(tmp_path):
    now = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)
    fresh = (now - timedelta(hours=5)).isoformat()
    last = _parked(tmp_path, "atlas080", family="wealth", score=30, rendered_at=fresh)
    a = _parked(tmp_path, "atlas081", family="wealth", score=30, rendered_at=fresh)
    b = _parked(tmp_path, "atlas082", family="health", score=29, rendered_at=fresh)
    c = _parked(tmp_path, "atlas083", family="health", score=0, rendered_at=fresh)
    d = _parked(tmp_path, "atlas084", family="energy", score=10, rendered_at=fresh)
    assert publish.order([a, b, c, d], last, now) == [b, a, d, c]
    old = _parked(tmp_path, "atlas079", family="energy", score=0, rendered_at=(now - timedelta(hours=80)).isoformat())
    assert publish.order([a, b, old], None, now)[0] == old
    # Records from before scores existed keep folder-name order.
    legacy = [_parked(tmp_path, n) for n in ("atlas070", "atlas069")]
    assert publish.order(sorted(legacy), None, now) == sorted(legacy)


def test_description_cites_the_dataset_source_and_year_and_three_hashtags():
    ds = _dataset()
    ep = AtlasEpisode.model_validate({"id": "atlas900", "title": "T", "description": "Who was born abroad.",
                                      "hashtags": ["#migration", "#migrants", "#maps"],
                                      "dataset": TOPIC["dataset"], "beats": [{"text": "x"}]})
    text = publish.description(ep, ds)
    assert "Data: Share of people born abroad, UN DESA via World Bank, 2024 (CC BY 4.0)." in text
    assert text.rstrip().endswith("#migration #migrants #maps")


def test_semantic_review_treats_an_ungrounded_why_as_an_unsourced_cause():
    import inspect
    from ytc.atlas import quality
    source = inspect.getsource(quality.review)
    assert "must rest on the definition in EVIDENCE" in source and "unsourced causes" in source


# --- review fixes (2026-10-22) ------------------------------------------------------------------------------------

def test_title_case_keeps_unit_symbols_as_written():
    assert writer.title_case("people per km² in the most crowded places") == \
        "People per km² in the Most Crowded Places"
    assert writer.title_case("where 3,000 mm a year falls") == "Where 3,000 mm a Year Falls"
    assert writer.title_case("is your country 5 m above the sea?") == "Is Your Country 5 m Above the Sea?"
    assert writer.title_case("the mm and km of it") == "The Mm and Km of It"  # not after a number: ordinary words


def test_framing_after_a_colon_or_vs_and_two_letter_codes():
    assert writer.title_problems("Japan vs. the World: Who Is Older?") == []
    assert writer.title_problems("DR Congo and the PM2.5 Map: Is YOUR Air Cleaner?") == []
    assert any("capitals" in p for p in writer.title_problems("Is YOUR Air WAY Cleaner?"))


def test_comparatives_and_why_titles_are_factual_in_the_semantic_review():
    import inspect
    from ytc.atlas import quality
    source = " ".join(inspect.getsource(quality.review).split())
    assert '"than you think"' not in source
    assert 'its comparisons ("less crowded than", "twice as")' in source
    assert 'A "Why" title claims a cause' in source


def test_tags_drop_the_obscure_family_and_hashtags_keep_one_specific_then_maps():
    ds = _dataset()
    obscure = {"topic": "Container shipping", "dataset": {"indicator": "IS.SHP.GCNW.XQ", "label": "Shipping"}}
    assert "obscure" not in writer.tags(obscure, ds, {"QAT": 1.0, "JPN": 2.0})
    assert writer.hashtags({"topic": "Share born abroad", "dataset": {"indicator": "SM.POP.TOTL.ZS"},
                            "hashtags": ["#migrants", "#diaspora"]}) == ["#migration", "#migrants", "#maps"]
    assert writer.hashtags({"topic": "Share born abroad", "dataset": {"indicator": "SM.POP.TOTL.ZS"},
                            "hashtags": ["#migration", "#diaspora"]}) == ["#migration", "#diaspora", "#maps"]


def test_refill_runs_at_most_once_a_day_and_the_pipeline_saves_when_it_ran(tmp_path, monkeypatch):
    now = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)
    asked = []
    monkeypatch.setattr(topics, "indicators", lambda: asked.append(1) or [])
    monkeypatch.setattr(topics.llm, "generate", lambda prompt, **k: {"ids": []})
    cat = {"topics": []}
    assert topics.refill(cat, now=now) == [] and len(asked) == 1
    assert cat["refilled_at"] == "2026-10-22T12:00:00+00:00"
    assert topics.refill(cat, now=now + timedelta(hours=8)) == [] and len(asked) == 1
    assert topics.refill(cat, now=now + timedelta(hours=21)) == [] and len(asked) == 2
    cat["refilled_at"] = "garbage"
    topics.refill(cat, now=now)
    assert len(asked) == 3


def test_a_pulling_family_repeat_beats_the_obscure_tail_only_when_nothing_else_pulls(tmp_path, monkeypatch):
    ds = lambda ind, label: {"indicator": ind, "label": label}  # noqa: E731
    rows = [{"id": "t1", "topic": "Economic output per person", "dataset": ds("NY.GDP.PCAP.CD", "GDP per person"),
             "status": "used:atlas075"},  # no "format": a map reveal
            {"id": "t2", "topic": "Inflation", "dataset": ds("FP.CPI.TOTL.ZG", "Inflation"), "format": "map_reveal",
             "status": "open"},
            {"id": "t3", "topic": "Global Container Shipping Connectivity",
             "dataset": ds("IS.SHP.GCNW.XQ", "Liner shipping connectivity"), "format": "rank_ladder", "status": "open"}]
    _catalogue(tmp_path, monkeypatch, rows)
    chosen = pipeline.pick()
    assert chosen["id"] == "t2" and chosen["format"] == "versus"  # last had no format: a map reveal
    rows.append({"id": "t4", "topic": "Share using the internet", "dataset": ds("IT.NET.USER.ZS", "Internet users"),
                 "format": "map_reveal", "status": "open"})
    _catalogue(tmp_path, monkeypatch, rows)
    assert pipeline.pick()["id"] == "t4"


def test_order_puts_a_stale_record_without_a_score_first(tmp_path):
    now = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)
    best = _parked(tmp_path, "atlas090", family="wealth", score=30, rendered_at=(now - timedelta(hours=2)).isoformat())
    legacy = _parked(tmp_path, "atlas060", rendered_at=(now - timedelta(hours=90)).isoformat())
    assert publish.order([best, legacy], best, now) == [legacy, best]
