import json

from ytc import studio


def test_review_receives_image_date_and_actual_subject(tmp_path, monkeypatch):
    work = tmp_path / "work"
    work.mkdir()
    (work / "manifest.json").write_text(json.dumps({"beats": [{"start": 0, "end": 3,
                                                           "text": "The 1871 fire spread."}]}))
    seen = []
    monkeypatch.setattr(studio, "recent_scores", lambda **kwargs: "none")
    monkeypatch.setattr(studio.llm, "generate", lambda parts, **kwargs: seen.extend(parts) or
                        {"scores": {key: 5 for key in studio.GATE}, "notes": {key: "ok" for key in studio.GATE},
                         "frames": [], "speech": [], "rewrite": [], "better_than_last": ""})
    monkeypatch.setattr(studio.llm, "answered_by", lambda: "test")
    script = {"title": "Fire", "description": "Fire.", "beats": [{"text": "The 1871 fire spread."}]}
    result = {"beats": [{"frame": str(tmp_path / "absent.jpg")}], "duration": 3, "words": 5,
              "integrated_lufs": -14, "true_peak_dbfs": -2, "warnings": []}
    visuals = [{"_choice": {"title": "Lick Fire, Umatilla Forest", "date": "2021-07-16"},
                "_fit": "close", "_shows": "A modern wildfire"}]

    studio.review(tmp_path, script, result, "test", visuals)
    prompt = "\n".join(str(part) for part in seen)
    assert "2021-07-16" in prompt
    assert "A modern wildfire" in prompt
    assert "A modern photo of" in prompt and "historical event" in prompt
