from ytc import writer


def _script(last: str) -> dict:
    beats = [{"text": "In 1938, a fisherman hauled up a living fossil.", "claims": [1], "emphasis": ["living fossil"],
              "queries": ["Coelacanth"], "sfx": "none"}]
    beats += [{"text": "It swam off South Africa.", "claims": [1], "emphasis": ["South Africa"], "queries": ["Latimeria chalumnae"], "sfx": "none"}] * 5
    beats.append({"text": last, "claims": [], "emphasis": [last.split()[0]], "queries": ["Coelacanth"], "sfx": "none"})
    return {"beats": beats, "title": "t", "hashtags": ["#animals", "#coelacanth", "#fossils"], "tags": ["a", "b", "c", "d"],
            "description": "One."}


def _loop_problems(last: str) -> list[str]:
    return [p for p in writer.problems(_script(last), {"claims": [{}]}) if "last beat" in p]


def test_dangling_loop_endings_are_rejected():
    for last in ("Scientists thought it vanished, which was because...", "And it all started when", "It lasted until"):
        assert _loop_problems(last), last


def test_complete_loop_sentence_passes():
    for last in ("It was supposed to be extinct for 66 million years.", "Nobody expected it to survive."):
        assert not _loop_problems(last), last
