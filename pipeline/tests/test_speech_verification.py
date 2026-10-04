"""Final speech findings need independent evidence and an exact-media review path."""

import copy
import hashlib
import importlib
import json

import pytest

from ytc import auto, cloud, publish, release, studio


checker = importlib.import_module("ytc.check")


@pytest.fixture
def video(tmp_path):
    path = tmp_path / "ep063.mp4"
    path.write_bytes(b"the exact encoded final video")
    return path


def _speech(video, beats, small, base, monkeypatch):
    def transcribe(media, model):
        assert media == video
        if model == checker.ASR_MODEL:
            return small
        assert model == checker.CORROBORATING_ASR_MODEL
        if isinstance(base, Exception):
            raise base
        return base

    monkeypatch.setattr(checker, "_transcribe", transcribe)
    return checker.speech(video, beats)


def test_ep063_style_minor_findings_clear_only_with_matching_second_model(video, monkeypatch):
    beats = [{"text": line} for line in (
        "A dock fire destroyed the municipal fire department.",
        "In 1947, responders watched the ship.",
        "At 9:12 A.M., the cargo exploded, obliterating the docks and every fire truck.",
        "Fertilizer could detonate a port.",
    )]
    scripted = " ".join(beat["text"] for beat in beats)
    small = (scripted.replace("department. In", "department.")
             .replace("9:12", "9.12").replace("docks and", "docks in") + " You")

    result = _speech(video, beats, small, scripted, monkeypatch)

    assert len(result["primary_differences"]) == 4
    assert "'in' heard as '(nothing)'" in result["primary_differences"][0]
    assert "'9 12' heard as '9.12'" in result["primary_differences"][1]
    assert "'and' heard as 'in'" in result["primary_differences"][2]
    assert "'(nothing)' heard as 'you'" in result["primary_differences"][3]
    assert result["corroboration"]["resolved"] == result["primary_differences"]
    assert result["differences"] == []
    digest = hashlib.sha256(video.read_bytes()).hexdigest()
    assert result["media_sha256"] == digest
    assert checker.speech_verified(result, digest, beats)
    assert not checker.speech_verified(result, "0" * 64, beats)


def test_clean_primary_audio_does_not_load_second_model(video, monkeypatch):
    beats = [{"text": "The ship sailed in 1947."}]
    called = []

    def transcribe(media, model):
        called.append(model)
        assert model == checker.ASR_MODEL
        return beats[0]["text"]

    monkeypatch.setattr(checker, "_transcribe", transcribe)
    result = checker.speech(video, beats)
    assert called == [checker.ASR_MODEL]
    assert checker.speech_verified(result, result["media_sha256"], beats)


@pytest.mark.parametrize("scripted,small", [
    ("The SS Grandcamp exploded.", "The SS Grandchamp exploded."),
    ("The ammonium nitrate burned.", "The ammonium nitrite burned."),
    ("In 1947, 12 people sailed.", "In 1948, 12 people sailed."),
    ("The ship did not sail.", "The ship did sail."),
    ("9 12 crates were moved. At 9:12 A.M., the ship exploded.",
     "9.12 crates were moved. At 9:12 A.M., the ship exploded."),
    ("At 9:12 A.M., the ship exploded.", "At 9.13 A.M., the ship exploded."),
    ("The ship carried coal and iron.", "The ship carried coal or iron."),
    ("The crew stayed in the port.", "The crew stayed port."),
    ("The crew stayed in port.", "The crew stayed in port you all."),
])
def test_names_sources_numbers_and_negation_stay_blocked_even_when_base_matches(
        video, monkeypatch, scripted, small):
    beats = [{"text": scripted}]
    result = _speech(video, beats, small, scripted, monkeypatch)
    assert result["primary_differences"]
    assert result["differences"]
    assert not checker.speech_verified(result, result["media_sha256"], beats)


@pytest.mark.parametrize("base", ["The ship sailed 1947.", OSError("base model unavailable")])
def test_second_model_disagreement_or_failure_keeps_finding(video, monkeypatch, base):
    beats = [{"text": "The ship sailed in 1947."}]
    result = _speech(video, beats, "The ship sailed 1947.", base, monkeypatch)
    assert result["differences"] == result["primary_differences"]
    assert not checker.speech_verified(result, result["media_sha256"], beats)
    if isinstance(base, Exception):
        assert "base model unavailable" in result["corroboration"]["error"]


def test_release_recomputes_claimed_corroboration_and_accepts_clean_legacy_review(video, tmp_path, monkeypatch):
    beats = [{"text": "The ship sailed in 1947."}]
    small = "The ship sailed 1947."
    result = _speech(video, beats, small, beats[0]["text"], monkeypatch)
    assert result["differences"] == []
    folder = tmp_path / "ep063"
    (folder / "work").mkdir(parents=True)
    (folder / "work" / "manifest.json").write_text(json.dumps({"beats": beats}))
    review = {"rounds": [{"media_sha256": result["media_sha256"], "passed": True,
                          "check": {"warnings": [], "speech_differences": [], "speech_error": None,
                                    "speech_verification": result},
                          "scores": {name: 4 for name in studio.GATE}, "frames": [], "speech": []}]}
    path = folder / "review.json"
    path.write_text(json.dumps(review))
    assert release._review(folder, result["media_sha256"])["round"] == 1

    for change in ("missing second transcript", "false second transcript", "false differences",
                   "false resolution", "wrong media hash", "missing primary findings"):
        bad = copy.deepcopy(review)
        verification = bad["rounds"][0]["check"]["speech_verification"]
        if change == "missing second transcript":
            verification["corroboration"].pop("heard")
        elif change == "false second transcript":
            verification["corroboration"]["heard"] = small
        elif change == "false differences":
            verification["corroboration"]["differences"] = ["invented"]
        elif change == "false resolution":
            verification["corroboration"]["resolved"] = []
        elif change == "wrong media hash":
            verification["media_sha256"] = "0" * 64
        else:
            verification["primary_differences"] = []
        path.write_text(json.dumps(bad))
        with pytest.raises(RuntimeError, match="clean final-media review"):
            release._review(folder, result["media_sha256"])

    legacy = copy.deepcopy(review)
    legacy["rounds"][0]["check"].pop("speech_verification")
    path.write_text(json.dumps(legacy))
    assert release._review(folder, result["media_sha256"])["round"] == 1


@pytest.mark.parametrize("prior_review, reviewer_fix", [(False, False), (True, True)])
def test_speech_only_review_stops_after_one_render_and_keeps_exact_video(
        tmp_path, monkeypatch, prior_review, reviewer_fix):
    episodes = tmp_path / "episodes"
    folder = episodes / "ep064"
    folder.mkdir(parents=True)
    research = {"viable": True, "series": "History", "claims": [], "sources": []}
    script = {"title": "The ship", "description": "A sourced story.", "hashtags": [], "tags": [],
              "beats": [{"text": "The ship sailed in 1947.", "emphasis": [], "claims": []}]}
    (folder / "research.json").write_text(json.dumps(research))
    (folder / "script.json").write_text(json.dumps(script))
    (folder / "visuals.json").write_text(json.dumps([{"source": "designed card"}]))
    monkeypatch.setattr(studio, "EPISODES", episodes)
    monkeypatch.setattr(studio, "REJECTED", tmp_path / "rejected")
    monkeypatch.setattr(studio, "contact_sheet", lambda folder, frames: folder / "sheet.jpg")
    monkeypatch.setattr(publish, "hold", lambda *args: pytest.fail("speech hold must not host media"))
    rendered = []
    media_bytes = b"encoded audio with unresolved speech"

    def render(spec):
        rendered.append(spec)
        media = spec.parent / "ep064.mp4"
        media.write_bytes(media_bytes)
        return media

    def inspect(media):
        beats = [{"text": script["beats"][0]["text"], "source": "designed card",
                  "frame": str(folder / "frame.jpg")}]
        return {"duration": 25, "words": 6, "integrated_lufs": -14.0, "true_peak_dbfs": -2.0,
                "warnings": [], "beats": beats,
                "speech": checker.speech(media, beats)}

    monkeypatch.setattr(studio, "_render", render)
    monkeypatch.setattr(checker, "check", inspect)
    monkeypatch.setattr(checker, "_transcribe", lambda media, model: "The ship sailed 1947.")
    if prior_review:
        earlier_media = tmp_path / "earlier.mp4"
        earlier_media.write_bytes(b"earlier render")
        finding = checker.speech(earlier_media, [{"text": script["beats"][0]["text"]}])["differences"]
        (folder / "review.json").write_text(json.dumps({"rounds": [{
            "check": {"warnings": [], "speech_differences": finding, "speech_error": None},
            "media_sha256": hashlib.sha256(b"earlier render").hexdigest(),
            "scores": {name: 4 for name in studio.GATE}, "frames": [], "speech": [],
        }]}))
    monkeypatch.setattr(studio, "review", lambda *args: {
        "scores": {name: 4 for name in studio.GATE}, "notes": {name: "good" for name in studio.GATE},
        "frames": [], "speech": [{"beat": 1, "word": "ship", "respelling": "ship"}] if reviewer_fix else [],
        "rewrite": [], "better_than_last": "", "judge": "test",
    })

    outcome = studio.produce("Ship story", "History", "ep064")
    digest = hashlib.sha256(media_bytes).hexdigest()
    hold = json.loads((folder / "editorial_hold.json").read_text())
    review = json.loads((folder / "review.json").read_text())
    assert outcome["outcome"] == "unfinished" and outcome["speech_review"] is True
    assert outcome["media_sha256"] == hold["media_sha256"] == digest
    assert (folder / "ep064.mp4").read_bytes() == media_bytes
    assert len(rendered) == 1
    assert len(review["rounds"]) == (2 if prior_review else 1)
    assert not (folder / "draft.json").exists() and not (folder / "hold.json").exists()
    attempts = json.loads((folder / "topic.json").read_text())["attempts"]
    with pytest.raises(RuntimeError, match="editorial hold"):
        studio.produce("Ship story", "History", "ep064")
    assert json.loads((folder / "topic.json").read_text())["attempts"] == attempts
    assert len(rendered) == 1


def test_cloud_keeps_held_media_byte_for_byte_in_private_outbox_and_collects_hold(tmp_path):
    root = tmp_path / "worker"
    folder = root / "content" / "episodes" / "ep064"
    folder.mkdir(parents=True)
    media_bytes = b"exact held encoded video bytes"
    (folder / "ep064.mp4").write_bytes(media_bytes)
    digest = hashlib.sha256(media_bytes).hexdigest()
    hold = {"schema": "ytc.final-audio-speech-hold/v1", "episode_id": "ep064",
            "media_sha256": digest, "media_file": "ep064.mp4", "speech_differences": ["a finding"]}
    (folder / "editorial_hold.json").write_text(json.dumps(hold))
    outcome = {"id": "ep064", "outcome": "unfinished", "speech_review": True, "media_sha256": digest}
    private_outbox = tmp_path / "outbox"

    cloud._retain_speech_review(folder, outcome, private_outbox)

    expected_path = f"drafts/speech-review/ep064-{digest}.mp4"
    assert outcome["speech_review_path"] == expected_path
    assert (private_outbox / expected_path).read_bytes() == media_bytes
    saved_hold = json.loads((folder / "editorial_hold.json").read_text())
    assert saved_hold["modal_volume"] == cloud.OUTBOX_VOLUME
    assert saved_hold["modal_path"] == expected_path
    (private_outbox / expected_path).write_bytes(b"interrupted earlier copy")
    cloud._retain_speech_review(folder, outcome, private_outbox)
    assert (private_outbox / expected_path).read_bytes() == media_bytes
    names = cloud._episode_files(root, folder)
    assert "content/episodes/ep064/editorial_hold.json" in names
    assert "content/episodes/ep064/ep064.mp4" not in names
    collected = tmp_path / "collected"
    cloud._unpack(cloud._pack(root, names), collected)
    assert json.loads((collected / "content/episodes/ep064/editorial_hold.json").read_text()) == saved_hold
    assert not (collected / "content/episodes/ep064/ep064.mp4").exists()

    (folder / "ep064.mp4").write_bytes(b"different media")
    with pytest.raises(RuntimeError, match="local media differs"):
        cloud._retain_speech_review(folder, outcome, private_outbox)


def test_speech_hold_owner_action_remains_visible_on_later_status_runs(tmp_path, monkeypatch):
    episodes = tmp_path / "episodes"
    folder = episodes / "ep064"
    folder.mkdir(parents=True)
    digest = "a" * 64
    held_path = f"drafts/speech-review/ep064-{digest}.mp4"
    (folder / "editorial_hold.json").write_text(json.dumps({
        "schema": "ytc.final-audio-speech-hold/v1", "episode_id": "ep064", "media_sha256": digest,
        "modal_volume": cloud.OUTBOX_VOLUME, "modal_path": held_path,
    }))
    monkeypatch.setattr(auto, "EPISODES", episodes)
    monkeypatch.setattr(auto, "STATUS", tmp_path / "status")
    monkeypatch.setattr(auto, "calendar_topics", lambda: [])
    monkeypatch.setattr(auto, "month_minutes", lambda: 0)
    monkeypatch.setattr(auto, "minutes_budget", lambda: 0)
    monkeypatch.setattr(auto, "_modal_cost", lambda: None)

    for _ in range(2):
        status = auto.write_status(auto.Run("test"), "held")
        assert len(status["owner_action"]) == 1
        assert "ep064 final speech review" in status["owner_action"][0]
        assert held_path in status["owner_action"][0]
        assert status["inventory"]["total"] == 0
