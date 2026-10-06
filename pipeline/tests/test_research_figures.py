from ytc import research
from ytc.research import Source

S1 = Source("S1", "https://www.ffi.no/report", "Oppau reassessment",
            "On the morning of 21 September 1921, hundreds of tons of fertilizer decomposed explosively. "
            "The event killed more than five hundred people and destroyed a large part of the factory site "
            "and surrounding residential area.")
S2 = Source("S2", "https://www.aria.developpement-durable.gouv.fr/fiche/14373/", "ARIA 14373",
            "N° 14373 - 21/09/1921 - ALLEMAGNE - 00 - OPPAU. Une explosion forme un cratère de 90 m de large "
            "et 20 m de profondeur. Le bilan de la catastrophe est très lourd : 561 morts, 1 952 blessés.")
BY_LABEL = {"S1": S1, "S2": S2}


def _claim(text, q1, q2):
    return {"claim": text, "sources": ["S1", "S2"],
            "evidence": [{"source": "S1", "quote": q1}, {"source": "S2", "quote": q2}]}


def test_a_quote_without_the_claims_figure_does_not_count():
    crater = _claim("The explosion left a crater 90 meters wide and 20 meters deep.",
                    "destroyed a large part of the factory site and surrounding residential area",
                    "Une explosion forme un cratère de 90 m de large et 20 m de profondeur")
    assert [e["source"] for e in research._matched_evidence(crater, BY_LABEL)] == ["S2"]


def test_each_site_stating_the_date_or_a_figureless_toll_counts():
    date = _claim("The explosion happened on 21 September 1921.",
                  "On the morning of 21 September 1921, hundreds of tons of fertilizer",
                  "N° 14373 - 21/09/1921 - ALLEMAGNE - 00 - OPPAU")
    toll = _claim("The explosion killed more than five hundred people.",
                  "The event killed more than five hundred people",
                  "Le bilan de la catastrophe est très lourd : 561 morts")
    assert len(research._matched_evidence(date, BY_LABEL)) == 2
    assert len(research._matched_evidence(toll, BY_LABEL)) == 2
    assert research._figures("1,952 injured and 1 952 blessés on 21/09/1921") == {"1952", "21", "9", "1921"}
