import re

import pytest

from ytc.atlas import writer


@pytest.mark.parametrize("title,want", [
    ("countries Where One City Holds 92% of City Dwellers", "Places Where One City Holds 92% of City Dwellers"),
    ("61 Countries Still Have Most People Outside Cities", "61 Places Still Have Most People Outside Cities"),
    ("The Emptiest and Most Crowded countries", "The Emptiest and Most Crowded places"),
])
def test_title_terminology_keeps_title_case(title, want):
    fixed = re.sub(r"\bcountries\b", writer._places, title, flags=re.I)
    assert fixed[:1].upper() + fixed[1:] == want


@pytest.mark.parametrize("fmt,values,want", [
    ("{v:.1f}", [9.5, 0.04, 3.2], "{v:.2f}"),
    ("{v:,.0f}", [131592, 0.3], "{v:,.1f}"),
    ("{v:.0f}%", [83, 5], "{v:.0f}%"),
    ("{v:.1f}", [0.0, 2.5], "{v:.1f}"),
    ("{v:,}", [0.04], "{v:,}"),
])
def test_no_nonzero_value_reads_as_zero(fmt, values, want):
    assert writer.precise(fmt, values) == want
