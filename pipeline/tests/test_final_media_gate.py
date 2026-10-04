"""Objective checks must inspect the encoded video that will be hosted."""

import importlib
import json
from subprocess import CompletedProcess


checker = importlib.import_module("ytc.check")


def _episode(tmp_path, monkeypatch, *, decode_code=0):
    video = tmp_path / "ep059.mp4"
    video.write_bytes(b"encoded video")
    work = tmp_path / "work"
    work.mkdir()
    beats = [{"start": 0, "end": 25, "text": "The exact spoken line.",
              "asset": {"source": "archival image", "title": "Archive", "license": "Public domain"}}]
    (work / "manifest.json").write_text(json.dumps({"beats": beats, "words": []}))
    (work / "speech.json").write_text(json.dumps({"heard": "A stale narration check.", "differences": []}))
    (work / "narration.wav").write_bytes(b"not the finished mix")
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        if "-af" in args:
            return CompletedProcess(args, decode_code, stderr="Summary:\nI: -14.0 LUFS\nPeak: -2.0 dBFS\n")
        return CompletedProcess(args, 1, stderr="Stream #0:0 Video: h264\nStream #0:1 Audio: aac\n")

    monkeypatch.setattr(checker.subprocess, "run", run)
    monkeypatch.setattr(checker.ff, "exe", lambda: "ffmpeg")
    monkeypatch.setattr(checker.ff, "run", lambda *args: None)
    monkeypatch.setattr(checker.ff, "duration", lambda path: 25)
    heard = []
    monkeypatch.setattr(checker, "speech", lambda path, transcript: heard.append((path, transcript)) or
                        {"heard": "The exact spoken line.", "differences": []})
    return video, beats, calls, heard


def test_check_recognizes_the_finished_mp4_even_with_a_cached_narration_check(tmp_path, monkeypatch):
    video, beats, calls, heard = _episode(tmp_path, monkeypatch)
    result = checker.check(video)
    assert heard == [(video.resolve(), beats)]
    assert result["warnings"] == []
    assert "-xerror" in next(args for args in calls if "-af" in args)


def test_decode_error_blocks_a_short_even_if_loudness_summary_exists(tmp_path, monkeypatch):
    video, _, _, _ = _episode(tmp_path, monkeypatch, decode_code=1)
    assert "full audio/video decode failed (ffmpeg exit 1)" in checker.check(video)["warnings"]
