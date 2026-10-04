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


def test_final_review_cannot_host_flagged_picture_or_speech():
    verdict = {"scores": {key: 5 for key in studio.GATE}, "judge": "gemini",
               "frames": [{"beat": 3, "problem": "2021 fire photo used for an 1871 event"}],
               "speech": []}
    exact = {"warnings": [], "speech": {"differences": []}}
    assert not studio._passes(exact, verdict, final=True)
    verdict["frames"] = []
    verdict["speech"] = [{"beat": 3, "word": "Peshtigo", "respelling": "pesh tee go"}]
    assert not studio._passes(exact, verdict, final=True)
    verdict["speech"] = []
    assert studio._passes(exact, verdict, final=True)
    assert not studio._passes({"warnings": []}, verdict, final=True)
    assert not studio._passes({"warnings": [], "speech": {"error": "ASR failed"}}, verdict, final=True)
    assert not studio._passes({"warnings": [], "speech": {"differences": ["missing word"]}}, verdict, final=True)


def test_best_round_cannot_restore_a_failed_final_media_speech_check():
    round_ = {"scores": {key: 5 for key in studio.GATE}, "frames": [], "speech": [],
              "check": {"warnings": [], "speech_differences": ["missing word"], "speech_error": None}}
    assert not studio._standing(round_)[0]
    round_["check"]["speech_differences"] = []
    assert studio._standing(round_)[0]
