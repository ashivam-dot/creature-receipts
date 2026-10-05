from ytc import writer


def _script(hook: str, hook_text: str = "18 MINUTES TO SINK", title: str = "Why Did the Titanic Sink So Fast?") -> dict:
    beats = [{"text": hook, "claims": [1], "emphasis": [hook.split()[0]], "queries": ["Titanic"], "sfx": "none"}]
    beats += [{"text": "The ship struck ice at night.", "claims": [1], "emphasis": ["ice"], "queries": ["Titanic"], "sfx": "none"}] * 6
    return {"beats": beats, "title": title, "hook_text": hook_text, "description": "One.",
            "hashtags": ["#history", "#titanic", "#shipwreck"], "tags": ["a", "b", "c", "d"]}


def _hook_problems(script: dict) -> list[str]:
    return [p for p in writer.problems(script, {"claims": [{}]})
            if any(rule in p for rule in ("open inside the story", "Give hook_text", "graphic"))]


def test_slow_or_strawman_openers_are_rejected():
    for hook in ("You might think a tsunami destroys everything.", "Imagine a city under ash.",
                 "Many believe the ship was unsinkable.", "What if the warning had been heard?"):
        assert any("open inside the story" in p for p in _hook_problems(_script(hook))), hook


def test_concrete_opening_passes():
    assert not _hook_problems(_script("The lookouts on the Titanic had no binoculars."))


def test_missing_on_screen_hook_must_be_rewritten():
    script = writer.normalize(_script("The lookouts on the Titanic had no binoculars.",
                                      hook_text="THE LOOKOUTS ON THE TITANIC HAD NO BINOCULARS"))
    assert script["hook_text"] == ""
    assert any(p.startswith("Give hook_text") for p in _hook_problems(script))


def test_graphic_hook_text_or_title_is_rejected():
    script = _script("Jean de Valette fired the heads of prisoners from his cannons.",
                     hook_text="CANNONS LOADED WITH HEADS", title="Why Was Blood Running in Malta's Streets?")
    graphic = [p for p in _hook_problems(script) if "graphic" in p]
    assert graphic and all(part in graphic[0] for part in ("hook", "title"))


def test_pompeii_without_bodies_is_not_graphic():
    script = _script("Akrotiri is the Pompeii where nobody died.", hook_text="THE POMPEII WITHOUT BODIES")
    assert not [p for p in _hook_problems(script) if "graphic" in p]


def test_title_whitespace_is_collapsed():
    script = writer.normalize(_script("The lookouts on the Titanic had no binoculars.",
                                      title="How Did Alexander's Men Scale a Mountain?  "))
    assert script["title"] == "How Did Alexander's Men Scale a Mountain?"
