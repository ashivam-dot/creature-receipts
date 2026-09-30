from ytc import pick, sources


def _picture(motion="zoom_in"):
    return {"_choice": {"key": "commons:File:x.jpg"}, "motion": motion}


def test_a_picture_is_shown_again_at_most_once():
    visuals = [_picture(), None, None, None]
    first = pick._reuse_of(visuals, 2)
    assert first and first["reuse"] == 1
    visuals[1] = first
    assert pick._reuse_of(visuals, 3) is None


def test_reuse_skips_to_an_earlier_picture_not_yet_shown_twice():
    visuals = [_picture(), _picture("pan_left"), {"reuse": 2, "motion": "zoom_out"}, None]
    again = pick._reuse_of(visuals, 4)
    assert again and again["reuse"] == 1


def test_inaturalist_keeps_only_cc0_and_cc_by():
    base = {"id": 1, "url": "https://inaturalist-open-data.s3.amazonaws.com/photos/1/square.jpg",
            "original_dimensions": {"width": 2048, "height": 1536}, "attribution": "(c) someone, some rights reserved (CC BY)"}
    ok = sources._inat_photo({**base, "license_code": "cc-by"}, "Vampire Squid", "https://www.inaturalist.org/photos/1", "taxon")
    assert ok and ok["license"] == "CC BY 4.0" and ok["original"].endswith("/original.jpg")
    for code in ("cc-by-sa", "cc-by-nc", None):
        assert sources._inat_photo({**base, "license_code": code}, "x", "p", "taxon") is None
    small = {**base, "license_code": "cc0", "original_dimensions": {"width": 500, "height": 400}}
    assert sources._inat_photo(small, "x", "p", "taxon") is None
