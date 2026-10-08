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
    assert "no Red" in found and "minus sign" in found


def test_one_post_a_day_at_the_evening_slot():
    now = datetime(2026, 10, 8, 10, 0, tzinfo=ET)
    assert publish.next_slot([], now) == datetime(2026, 10, 8, 19, 0, tzinfo=ET)
    taken = [datetime(2026, 10, 8, 19, 0, tzinfo=ET)]
    assert publish.next_slot(taken, now) == datetime(2026, 10, 9, 19, 0, tzinfo=ET)
    late = datetime(2026, 10, 8, 18, 30, tzinfo=ET)
    assert publish.next_slot([], late) == datetime(2026, 10, 9, 19, 0, tzinfo=ET)
