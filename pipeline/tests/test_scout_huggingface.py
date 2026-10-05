"""The scout reports trending Hugging Face models only when their licence allows a monetized channel."""

import importlib.util
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _scout():
    spec = importlib.util.spec_from_file_location("scout_hf_test", ROOT / "monitor" / "scout.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _model(model_id, *, tags=(), card=None, likes=10):
    return {"id": model_id, "likes": likes, "tags": list(tags), "cardData": card or {}}


def test_trending_keeps_commercial_licences_and_drops_the_rest(monkeypatch):
    scout = _scout()
    pages = {
        "text-to-speech": [
            _model("ok/apache-tts", tags=["license:apache-2.0"], likes=1234),
            _model("no/nc-tts", tags=["license:cc-by-nc-4.0"]),
            _model("no/research-tts", tags=["license:other"], card={"license": "other",
                                                                   "license_name": "fish-audio-research-license"}),
            _model("no/unlicensed-tts"),
            _model("no/xtts", tags=["license:other"], card={"license_name": "coqui-public-model-license"}),
            _model("no/unnamed-other", tags=["license:other"], card={"license": "other"}),
        ],
        "image-to-video": [
            _model("ok/custom-i2v", tags=["license:other"], card={"license": "other",
                                                                 "license_name": "ltx-2-community-license"}),
            _model("no/mistral", tags=["license:mrl"]),
        ],
        "text-to-image": [
            _model("no/flux-dev", tags=["license:other"], card={"license_name": "flux-1-dev-non-commercial-license"}),
            _model("no/apache-gguf", tags=["license:apache-2.0"], card={"base_model_relation": "quantized"}),
            _model("ok/mit-image", card={"license": ["mit"]}),
        ],
    }
    seen = []

    def fake_get(url, headers=None):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        seen.append(query)
        assert url.startswith("https://huggingface.co/api/models?")
        return pages[query["pipeline_tag"][0]]

    monkeypatch.setattr(scout, "_get", fake_get)
    found = scout.hf_trending()

    assert sorted(found) == ["hf:ok/apache-tts", "hf:ok/custom-i2v", "hf:ok/mit-image"]
    assert found["hf:ok/apache-tts"] == ("Trending on Hugging Face (text-to-speech): ok/apache-tts, 1,234 likes, "
                                         "licence apache-2.0. https://huggingface.co/ok/apache-tts")
    assert "licence other / ltx-2-community-license" in found["hf:ok/custom-i2v"]
    assert [q["pipeline_tag"] for q in seen] == [["text-to-speech"], ["image-to-video"], ["text-to-image"]]
    assert all(q["sort"] == ["trendingScore"] and "cardData" in q["expand[]"] for q in seen)


def test_huggingface_finds_are_new_only_after_the_first_run(monkeypatch, tmp_path):
    scout = _scout()
    monkeypatch.setattr(scout, "OUT", tmp_path)
    monkeypatch.setattr(scout, "STATE", tmp_path / "scout.json")
    monkeypatch.delenv("YTC_NTFY_TOPIC", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    finds = [{"hf:a/one": "one"}, {"hf:a/one": "one", "hf:b/two": "two"}]
    monkeypatch.setattr(scout, "CHECKS", {"huggingface": lambda: finds.pop(0)})
    printed = []
    monkeypatch.setattr("builtins.print", lambda text: printed.append(text))

    scout.main()
    scout.main()

    assert "- Nothing new today." in printed[0]
    assert "- two" in printed[1] and "- one" not in printed[1]
