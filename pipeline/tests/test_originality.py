from ytc import writer


def test_structure_rotates_to_the_least_used():
    recent = [{"structure": "story"}, {"structure": "myth_vs_fact"}, {"structure": "story"}]
    assert writer.choose_structure(recent) == "countdown"
    assert writer.choose_structure([]) == "story"


def test_a_copied_script_is_flagged():
    beats = ["The mantis shrimp punches faster than a bullet leaves a gun.", "Its club hits with the force of a small bullet.",
             "The strike boils the water around it for an instant.", "Aquariums have lost glass tanks to a single punch."]
    other = {"id": "ep004", "beats": list(beats)}
    found = writer.sameness(beats, [other])
    assert any("ep004" in f and "wording" in f for f in found)


def test_a_template_opening_is_flagged_but_fresh_scripts_pass():
    mine = ["Scientists found a fish that walks on land.", "It lives in the mangroves of Asia."]
    template = {"id": "ep009", "beats": ["Scientists found a fish that glows in the dark.", "Nobody expected it."]}
    assert any("same words" in f for f in writer.sameness(mine, [template]))
    fresh = {"id": "ep010", "beats": ["An octopus escaped its tank at night.", "It returned before morning."]}
    assert writer.sameness(mine, [fresh]) == []
