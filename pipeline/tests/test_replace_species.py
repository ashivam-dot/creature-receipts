from ytc import pick


def _choice(key, title):
    return {"key": key, "title": title, "origin": "inaturalist", "original": f"https://x/{key}.jpg",
            "width": 2048, "height": 2048, "license": "CC BY 4.0", "artist": "a", "page": "https://x", "source_name": "iNaturalist"}


def test_species_reads_binomials():
    assert pick._species("Mallard (Anas platyrhynchos)") == {"anas platyrhynchos"}
    assert pick._species("File:Anas platyrhynchos (mixed pair) (32428014687).jpg") == {"anas platyrhynchos"}
    assert pick._species("Proceedings of the Zoological Society of London") == set()


def test_replace_skips_alternates_of_the_rejected_species():
    script = {"beats": [{"text": "A platypus."}, {"text": "A duck's bill on a beaver's body."}, {"text": "Done."}]}
    visuals = [
        {"source": "card", "card": {"kind": "fact", "big": "x", "small": ""}},
        {"source": "url", "_choice": _choice("inat:1", "Mallard (Anas platyrhynchos)"),
         "_alternates": [_choice("commons:2", "Anas platyrhynchos (mixed pair).jpg"),
                         _choice("commons:3", "Ornithorhynchus anatinus swimming.jpg")]},
        {"source": "card", "card": {"kind": "fact", "big": "y", "small": ""}},
    ]
    out = pick.replace(script, {}, "ep", visuals, [2])
    assert out[1]["_choice"]["key"] == "commons:3"
    assert "inat:1" in out[1]["_rejected"]
