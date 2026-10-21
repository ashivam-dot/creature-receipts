"""Atlas speech-check yield (2026-10-21): 9 of the 18 drafts lost on 2026-10-17..21 failed the encoded speech check
on numbers the writer was allowed to say ("5.0%", "70.5202%", "0.000%") and on the stock card "Where does your
country land?". These tests replay the real failed.json findings and scripts in content/atlas/*-failed-*/, and
check that the fixes are made at the source while the polarity and country guards stay as strict as before."""
import inspect
import json
import re
from pathlib import Path

import pytest

from ytc import check
from ytc.atlas import pipeline, quality, receipt, writer
from ytc.atlas.data import Dataset
from ytc.atlas.episode import AtlasEpisode, say_value

CONTENT = Path(__file__).resolve().parents[2] / "content" / "atlas"
FAILED = sorted(CONTENT.glob("atlas*-failed-*"))
PREFIX = "encoded speech material mismatch: "


def _findings() -> list[tuple[Path, str]]:
    out = []
    for folder in FAILED:
        error = json.loads((folder / "failed.json").read_text())["error"]
        if error.startswith(PREFIX):
            out += [(folder, f) for f in error[len(PREFIX):].split("; ")]
    return out


def _folder(episode: str) -> Path:
    return next(f for f in FAILED if f.name.startswith(episode + "-"))


@pytest.mark.parametrize("value,fmt,want", [
    (5.0, "{v:.1f}%", "5%"),              # atlas064: heard as "5%"
    (14.0, "{v:.1f}%", "14%"),            # atlas066
    (9.0, "{v:.1f}%", "9%"),              # atlas077
    (0.8, "{v:.2f}%", "0.8%"),            # atlas060: "0.80%" heard as "0.8%"
    (70.5202, "{v:.4f}%", "70.5%"),       # atlas062: "70.5202%" heard as "70.520%"
    (58.5532, "{v:.4f}%", "58.6%"),
    (5.801, "{v:.3f}%", "5.8%"),          # atlas051
    (0.0, "{v:.3f}%", "0%"),              # atlas051: Saudi Arabia's hydropower is exactly 0
    (0.0143, "{v:.2f}%", "under 0.1%"),   # atlas060: Guinea, never "0.0%" or "0.01%"
    (99.992, "{v:.3f}%", "over 99.9%"),   # atlas051: Bhutan, never rounded up to a full 100%
    (100.0, "{v:.1f}%", "100%"),
    (0.02, "{v:.1f}", "under 0.1"),       # atlas021: "Niger has 0.0" doctors
    (0.02, "{v:.2f}", "0.02"),            # small non-percentages keep up to 3 significant figures
    (0.01234, "{v:.4f}", "0.0123"),
    (9.5, "{v:.2f}", "9.5"),
    (1333.4, "{v:,.0f}", "1,333"),        # whole digits are never rounded away
    (1333.4, "{v:,.1f}", "1,333"),
    (0.3, "{v:,.0f}", "under 1"),
    (0.4, "${v:,.0f}", "under $1"),
    (-1.8, "{v:.1f}%", "-1.8%"),
    (-0.01, "{v:.1f}%", "under 0.1%"),
    (16.0, "{v:.0f} years", "16 years"),
    (93.8, "{v:.1f}", "93.8"),
])
def test_values_are_said_the_way_a_person_says_them(value, fmt, want):
    assert say_value(value, fmt) == want


def test_the_episode_writer_and_review_share_one_formatter():
    ep = AtlasEpisode.model_validate({"id": "atlas999", "title": "t", "value_format": "{v:.1f}%",
        "dataset": {"kind": "worldbank", "label": "Youth NEET", "source": "WB"}, "beats": [{"text": "t"}]})
    assert ep.value_text(5.0) == writer._say(5.0, "{v:.1f}%") == "5%"
    ds = Dataset("Youth NEET", "%", "WB", "CC BY", "", {"SWE": 5.0}, {"SWE": 2024}, names={"SWE": "Sweden"})
    assert quality.entity_value_errors("Sweden has 5%.", ep, ds) == []
    # The writer may no longer say the trailing zero the narrator drops.
    assert quality.entity_value_errors("Sweden has 5.0%.", ep, ds)


def test_replayed_findings_relax_only_the_same_number_spelled_another_way():
    findings = _findings()
    assert len(findings) >= 20, "the failed.json fixtures are missing"
    for folder, finding in findings:
        ds = Dataset.load(folder / "data.json")
        match = check._FINDING.match(finding)
        before = bool(match) and _old_minor(finding, ds)
        now = quality.minor_speech_difference(finding, ds)
        if now and not before:
            # The only new tolerance: every word pairs up and each changed word is the same number.
            assert quality.same_number(match[2], match[4]), finding
            assert not re.search(r"[a-z]", re.sub(r"\d|[.,%$]", "", match[2] + match[4]), re.I), finding


def _old_minor(finding: str, ds: Dataset) -> bool:
    original = quality.same_number
    try:
        quality.same_number = lambda wrote, heard: False
        return quality.minor_speech_difference(finding, ds)
    finally:
        quality.same_number = original


@pytest.mark.parametrize("episode,finding,minor", [
    ("atlas064", "'5.0%' heard as '5%' after '6.2% sweden has'", True),
    ("atlas064", "base.en: '5.0%' heard as '5%' after '6.2% sweden has'", True),
    ("atlas066", "'14.0%' heard as '14%' after 'uk which uses'", True),
    ("atlas051", "'0.000%' heard as '0%' after 'saudi arabia generates'", True),
    # Still material: an extra word, a country, a changed value, the stock card, a misheard name or letter.
    ("atlas066", "base.en: '14.0% the' heard as '14%' after 'uk which uses'", False),
    ("atlas060", "'0.80% guinea' heard as '0.8% ini' after 'foreign visitors at'", False),
    ("atlas062", "base.en: '70.5202%' heard as '70.520%' after 'asia indonesia generates'", False),
    ("atlas077", "'9.0% where does' heard as '9% what is' after 'the usa has'", False),
    ("atlas063", "'where does' heard as 'what is' after 'that with 38.7%'", False),
    ("atlas073", "base.en: 'laos' heard as 'locks' after 'mali 2 one'", False),
    ("atlas041", "'c' heard as 'see' after 'spain counts 6'", False),
    ("atlas077", "base.en: '(nothing)' heard as '7%' after 'brazil has 40.7%'", False),
])
def test_replayed_findings(episode, finding, minor):
    folder = _folder(episode)
    assert finding in json.loads((folder / "failed.json").read_text())["error"]
    assert quality.minor_speech_difference(finding, Dataset.load(folder / "data.json")) is minor


def test_atlas064_would_now_pass_its_speech_gate():
    """atlas064's only differences were Sweden's "5.0%" said as "5%"; the gate's own arithmetic now passes it."""
    folder = _folder("atlas064")
    differences = json.loads((folder / "failed.json").read_text())["error"][len(PREFIX):].split("; ")
    ds = Dataset.load(folder / "data.json")
    material = [d for d in differences if not quality.minor_speech_difference(d, ds)]
    assert differences and not material and len(differences) <= 4


@pytest.mark.parametrize("episode,iso,said", [
    ("atlas064", "SWE", "5%"), ("atlas066", "GBR", "14%"), ("atlas077", "USA", "9%"),
    ("atlas060", "NGA", "0.8%"), ("atlas060", "GIN", "under 0.1%"), ("atlas062", "IDN", "70.5%"),
    ("atlas062", "CHN", "58.6%"), ("atlas051", "SAU", "0%"), ("atlas051", "USA", "5.8%"),
])
def test_replayed_scripts_now_say_what_the_recognizer_writes(episode, iso, said):
    folder = _folder(episode)
    ep = AtlasEpisode.load(folder / "atlas.yaml")
    ds = Dataset.load(folder / "data.json")
    old = ep.value_format.format(v=ds.values[iso])
    assert old in " ".join(b.text for b in ep.beats)  # the value that failed was said in the script
    assert ep.value_text(ds.values[iso]) == said


def test_replayed_stock_cards_are_rejected_and_a_topic_question_passes():
    cards = []
    for folder in FAILED:
        if (folder / "atlas.yaml").exists():
            ep = AtlasEpisode.load(folder / "atlas.yaml")
            cards += [b.text for b in ep.beats if b.shot.kind == "card" and re.match(r"where\b", b.text, re.I)]
    assert len(cards) >= 8
    for text in cards:
        assert writer.card_problems(text), text
    coal = writer.topic_words("Coal power", "Coal share in electricity production")
    assert writer.card_problems("How does your country compare?", coal)
    assert writer.card_problems("How much of your power comes from coal", coal)
    assert writer.card_problems("So where do you think your electricity comes from?", coal)
    assert not writer.card_problems("How much of your power comes from coal?", coal)
    assert not writer.card_problems("Is your electricity cleaner than China's?", coal)


def test_units_and_abbreviated_names_are_said_as_words():
    # atlas041: "C. African Rep." was said "C" and heard as "see".
    assert writer.spoken("C. African Rep. is the world's highest at 46.") == \
        "Central African Republic is the world's highest at 46."
    assert writer.spoken("Bangladesh has 1,333 people per km².") == "Bangladesh has 1,333 people per square kilometer."
    assert writer.spoken("Qatar: 108 µg/m³.") == "Qatar: 108 micrograms per cubic meter."
    assert writer.spoken("Iceland uses 50,000 kWh, Chad 20 kg/ha.") == \
        "Iceland uses 50,000 kilowatt hours, Chad 20 kilograms per hectare."
    assert writer.spoken("Trinidad & Tobago and Papua N. Guinea") == "Trinidad and Tobago and Papua New Guinea"
    assert writer.spoken("PM2.5 in Kampala, the Okm brand") == "PM2.5 in Kampala, the Okm brand"
    assert writer.spoken_name("Central African Republic") == "Central African Republic"
    assert writer.spoken_name("United States of America") == "USA"


def test_misleading_numbers_are_rejected():
    assert writer.misleading_numbers("Cuba has 9.5 doctors. Niger has 0.0.")
    assert writer.misleading_numbers("Saudi Arabia generates 0.000%.", zero_ok=True)
    assert writer.misleading_numbers("Saudi Arabia generates 0%.")
    assert writer.misleading_numbers("Saudi Arabia generates 0%.", zero_ok=True) == []
    assert writer.misleading_numbers("Guinea has under 0.1%, Chad 10, Peru 2020, and 1,000 or 0.05.") == []
    assert writer.misleading_numbers("Why Greece Has 165.1% College Enrollment", gross=True)
    assert writer.misleading_numbers("Greece: 165%.", gross=False, explained=True)
    assert writer.misleading_numbers("Greece has a gross enrollment ratio of 165%.", gross=True, explained=True) == []
    assert writer.misleading_numbers("Prices in Argentina rose 211%.", growth=True) == []
    assert writer.misleading_numbers("Bhutan generates 100%.") == []
    assert writer.measure_kind("Gross tertiary enrollment ratio", "SE.TER.ENRR") == {"gross": True, "growth": False}
    assert writer.measure_kind("Inflation, consumer prices", "FP.CPI.TOTL.ZG") == {"gross": False, "growth": True}


def _draft(card: str = "How many doctors does your country have?", extra: str = "") -> dict:
    beats = [{"shot": "world", "isos": ["CUB", "NER"], "text": "Cuba has 9.5 doctors for every 1,000 people. In Niger, under 0.1."},
             {"shot": "country", "isos": ["CUB"], "text": "Cuba trains doctors for half the world."},
             {"shot": "country", "isos": ["NER"], "text": "In Niger, a whole town can share one clinic and one nurse." + extra},
             {"shot": "country", "isos": ["IND"], "text": "India has 0.7 for every 1,000 people, below the median."},
             {"shot": "country", "isos": ["USA"], "text": "The USA has 3.6, well above the median."},
             {"shot": "card", "text": card}]
    return {"title": "Cuba has 9.5 doctors per 1,000. Niger, under 0.1", "hook_text": "DOCTOR DIVIDE", "beats": beats}


def _check(draft: dict, **kwargs) -> list[str]:
    vals = {"CUB": 9.5, "NER": 0.02, "IND": 0.7, "USA": 3.6}
    allowed = {"1,000", "1000", "0.1", "9.5", "0.7", "3.6"}
    return writer.problems(draft, allowed, {}, vals, **kwargs)


def test_writer_word_floor_is_50_with_a_spoken_floor_and_the_same_max():
    assert writer.WORDS == (50, 110)
    found = _check(_draft(), topic=writer.topic_words("Doctors per 1,000 people"))
    words = sum(len(b["text"].split()) for b in _draft()["beats"])
    assert 50 <= words < 60
    assert not [p for p in found if "words" in p], found
    short = _draft()
    short["beats"] = short["beats"][:2] + short["beats"][-1:] + short["beats"][-1:]
    assert any("as spoken; the Short needs" in p for p in writer.problems(short, set(), {}, {}))


def test_writer_rejects_misleading_numbers_and_stock_cards():
    topic = writer.topic_words("Doctors per 1,000 people")
    assert not _check(_draft(), topic=topic)
    zero = _draft()
    zero["title"] = "Cuba has 9.5 doctors while Niger has 0.0"
    assert any("title: '0.0' reads as nothing" in p for p in _check(zero, topic=topic))
    assert any("card question" in p for p in _check(_draft("Where does your country land?"), topic=topic))
    assert any("subject" in p for p in _check(_draft("How does your nation compare?"), topic=topic))


def test_review_rejects_published_misleading_numbers_before_any_model_call(tmp_path, monkeypatch):
    """atlas053 'Why Greece Has 165.1% College Enrollment' (a gross ratio its title never called gross) and
    atlas021 'Cuba has 9.5 doctors while Niger has 0.0' are stopped by the deterministic gate."""
    monkeypatch.setattr(quality.llm, "generate", lambda *a, **k: pytest.fail("reached the model review"))
    for episode, want in (("atlas053", "over 100%"), ("atlas021", "'0.0' reads as nothing")):
        ep = AtlasEpisode.load(CONTENT / episode / "atlas.yaml")
        ds = Dataset.load(CONTENT / episode / "data.json")
        with pytest.raises(ValueError, match=re.escape(want)):
            quality.review(ep, ds, tmp_path)


def test_producer_runs_four_times_a_day_and_spends_up_to_four_failures():
    from ytc import cloud
    assert cloud.ATLAS_SCHEDULE == "10 1,7,13,19 * * *"
    assert inspect.signature(pipeline.run).parameters["max_failures"].default == pipeline.MAX_FAILURES == 4


def test_queued_ready_shorts_stay_accepted():
    """Nothing here changes what a parked Short claims: its numbers were checked against its own value_format and
    still are. Bumping writer.STYLE or receipt.FORMAT would re-script or skip every waiting Short while the
    publisher needs every one it has."""
    assert receipt.FORMAT == pipeline.FORMAT == "cinema-v2.2"
    assert writer.STYLE == "story-v2"
