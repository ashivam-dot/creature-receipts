from ytc import pick, studio


def _choice(key):
    return {"key": key, "title": f"{key}.jpg", "origin": "inaturalist", "original": f"https://x/{key}.jpg",
            "width": 2048, "height": 2048, "license": "Public domain", "artist": "a", "page": "https://x",
            "source_name": "Wikimedia Commons"}


def _picture(key, alternates=()):
    return {"source": "url", "motion": "zoom_in", "_choice": _choice(key),
            "_alternates": [_choice(k) for k in alternates]}


def _card():
    return {"source": "card", "card": {"kind": "fact", "big": "x", "small": ""}}


def test_reuse_beat_takes_a_spare_alternate_so_an_art_poor_plan_renders():
    beats = [{"text": f"Beat {n}."} for n in range(1, 7)]
    visuals = [_picture("a", ["a2", "a3"]), _picture("b"), {"reuse": 2, "motion": "zoom_out"},
               {"reuse": 1, "motion": "zoom_in"}, _card(), {"reuse": 1, "motion": "zoom_out"}]
    assert studio._visual_plan_problem(visuals) == "only 2 original art beats; 3 are needed for 6 beats"
    pick._spares_for_reuse(beats, visuals, loop=True)
    assert visuals[2]["_choice"]["key"] == "a2"
    assert visuals[3]["_choice"]["key"] == "a3"
    assert visuals[5] == {"reuse": 1, "motion": "zoom_out"}
    assert studio._visual_plan_problem(visuals) is None


def test_reuse_beat_never_takes_a_picture_already_shown_or_rejected():
    beats = [{"text": "One."}, {"text": "Two."}, {"text": "Three."}]
    visuals = [_picture("a", ["b", "x"]), _picture("b"), {"reuse": 1, "motion": "zoom_out", "_rejected": ["x"]}]
    pick._spares_for_reuse(beats, visuals, loop=False)
    assert visuals[2] == {"reuse": 1, "motion": "zoom_out", "_rejected": ["x"]}
