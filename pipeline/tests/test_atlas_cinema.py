import json

from ytc.atlas import publish
from ytc.atlas.cinema import film, globe, places
from ytc.atlas.episode import AtlasEpisode


def _episode() -> AtlasEpisode:
    return AtlasEpisode.model_validate({
        "id": "atlas999", "title": "t", "dataset": {"kind": "worldbank", "label": "l", "source": "s"},
        "beats": [{"text": "hook", "shot": {"callouts": ["BGD"]}},
                  {"text": "dive", "shot": {"kind": "country", "iso": "BGD"}},
                  {"text": "short", "shot": {"kind": "country", "iso": "AUS"}},
                  {"text": "pair", "shot": {"kind": "group", "isos": ["IND", "CHN"]}},
                  {"text": "end", "shot": {"kind": "card", "lines": ["Yours?"]}}]})


def test_country_beats_dive_on_the_globe_then_cut_to_photos():
    photo = {"path": "p.jpg"}
    pics = {"BGD": {"photos": [photo, photo]}, "AUS": {"photos": [photo]}, "IND": {"photos": [photo]},
            "CHN": {"photos": [photo]}}
    spans = [(0.25, 4.0), (4.0, 12.0), (12.0, 15.0), (15.0, 21.0), (21.0, 23.0)]
    segs = film.segments(_episode(), spans, 23.6, pics)
    kinds = [(s["kind"], s["beat"]) for s in segs]
    # An 8 s country beat: globe dive, then two photos; a 3 s one is too short for a photo and stays on the globe.
    assert kinds == [("globe", 0), ("globe", 1), ("photo", 1), ("photo", 1), ("globe", 2), ("globe", 3),
                     ("split", 3), ("globe", 4)]
    assert segs[2]["t0"] - 4.0 >= film.DIVE and segs[-1]["t1"] == 23.6 and segs[0]["t0"] == 0.0


def test_claims_skip_former_values_and_prefer_the_preferred_rank():
    entity = {"claims": {"P36": [
        {"rank": "normal", "mainsnak": {"datavalue": {"value": {"id": "Q_OLD"}}}, "qualifiers": {"P582": []}},
        {"rank": "normal", "mainsnak": {"datavalue": {"value": {"id": "Q_ALSO"}}}},
        {"rank": "preferred", "mainsnak": {"datavalue": {"value": {"id": "Q_TOKYO"}}}},
        {"rank": "deprecated", "mainsnak": {"datavalue": {"value": {"id": "Q_BAD"}}}}]}}
    assert places._claims(entity, "P36") == ["Q_TOKYO", "Q_ALSO"]


def test_edited_copies_of_one_photo_count_once():
    assert places._stem("File:Skyscrapers of Shinjuku 2009 January (revised).jpg") == \
        places._stem("File:Skyscrapers of Shinjuku 2009 January.jpg")
    assert places._stem("File:Forecourt, Rashtrapati Bhavan - 1.jpg") != places._stem("File:Supreme Court of India 01.jpg")


def test_licences_and_pictures_that_are_not_photos_are_filtered():
    info = {"width": 2000, "height": 1300, "mime": "image/jpeg", "url": "u", "descriptionurl": "d",
            "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 4.0"}, "Artist": {"value": "<a>Jo</a>"}}}
    assert places._picture("File:Dhaka skyline.jpg", info, "capital", "Dhaka").author == "Jo"
    assert places._picture("File:Dhaka map.jpg", info, "capital", "Dhaka") is None
    assert places._picture("File:Dhaka protest.jpg", info, "capital", "Dhaka") is None
    nc = {**info, "extmetadata": {"LicenseShortName": {"value": "CC BY-NC 2.0"}}}
    assert places._picture("File:Dhaka skyline.jpg", nc, "capital", "Dhaka") is None


def test_highlight_covers_only_its_countries(tmp_path):
    box = globe.highlight_texture(["BGD"], (255, 209, 102), tmp_path / "hi.png")
    u0, v0, u1, v1 = box
    # Bangladesh spans about 88-93°E, 20-27°N, plus padding.
    assert 0.72 < u0 < u1 < 0.78 and 0.58 < v0 < v1 < 0.68 and u1 - u0 < 0.04


def test_description_credits_every_photo(tmp_path):
    (tmp_path / "credits.json").write_text(json.dumps([{"file": "File:A.jpg", "page": "https://c/A", "author": "Jo",
                                                       "license": "CC BY 2.0", "place": "Dhaka"}]))
    text = publish.photo_credits(tmp_path)
    assert "Dhaka: Jo, CC BY 2.0, https://c/A" in text
    assert publish.photo_credits(None) == ""
