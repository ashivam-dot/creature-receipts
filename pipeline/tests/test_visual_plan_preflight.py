from ytc import studio


def test_art_poor_seven_beat_plan_is_blocked_before_render():
    plan = [
        {"source": "url", "url": "https://archive.example/before.jpg"},
        {"reuse": 1},
        *({"source": "card"} for _ in range(4)),
        {"reuse": 1},
    ]
    assert studio._visual_plan_problem(plan) == "4 title cards exceed the two-card limit"


def test_hook_card_and_single_photo_reuse_are_blocked():
    assert studio._visual_plan_problem([{"source": "card"}, {"source": "url"}]) == "the hook has a title card"
    plan = [{"source": "url"}, {"reuse": 1}, {"source": "card"},
            {"source": "card"}, {"reuse": 1}, {"reuse": 1}]
    assert "only 1 original art beats" in studio._visual_plan_problem(plan)


def test_archival_images_and_authored_schematic_make_a_viable_plan():
    plan = [{"source": "url"}, {"source": "file"}, {"source": "card"},
            {"source": "url"}, {"source": "card"}, {"reuse": 1}]
    assert studio._visual_plan_problem(plan) is None
