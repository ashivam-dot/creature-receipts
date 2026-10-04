"""Inspect a rendered Short: stream facts, full decode, loudness, per-beat assets, review frames, and what the
finished video's audio track sounds like to a speech recognizer."""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import subprocess
from pathlib import Path

from . import ff

_LUFS = re.compile(r"I:\s+(-?[\d.]+) LUFS")
_PEAK = re.compile(r"Peak:\s+(-?[\d.]+) dBFS")
# Kokoro's pronunciation override, [Formosus](/fɔɹmˈOsəs/), is spoken and captioned as the bracketed word.
_OVERRIDE = re.compile(r"\[([^\]]+)\]\(/[^)]*/\)")
# Single letters are left alone: "X-ray", "V-2".
_ROMAN = re.compile(r"\b[IVX]{2,}\b")
_WAR = re.compile(r"\bWar (I{1,2})\b")
# Whisper may spell the same spoken word in British English, and it often
# writes Henry the Fifth as Henry V. Keep these equivalences exact: a changed
# number, person, or other content word must still hold the final video.
_HENRY_FIFTH = re.compile(r"\bHenry\s+V\b(?![-\w])", re.I)
_SPELLING_VARIANT = re.compile(r"\b(?:armoured|ploughed)\b", re.I)
_SAME_SPOKEN_WORD = {"armoured": "armored", "ploughed": "plowed"}
ASR_MODEL = "small.en"
# A different English Whisper checkpoint checks only disputed final MP4 audio. It is
# small enough for the studio worker; neither checkpoint alone can waive a changed
# name, source, number, or other content word.
CORROBORATING_ASR_MODEL = "base.en"
_MINOR_WORDS = frozenset({"a", "an", "the", "and", "in"})
_CLOCK_TIME = re.compile(r"\b(\d{1,2}):(\d{2})\s*[ap]\.?m\.?(?!\w)", re.I)
# Seconds a finished Short may run (writer.WORDS sets the script length that lands inside it).
DURATION = (17, 35)


def check(video: Path) -> dict:
    video = video.resolve()
    work = video.parent / "work"
    frames = work / "frames"
    frames.mkdir(parents=True, exist_ok=True)

    info = subprocess.run([ff.exe(), "-hide_banner", "-i", str(video)], capture_output=True, text=True).stderr
    streams = [line.strip() for line in info.splitlines() if "Stream #" in line]
    decoded = subprocess.run(
        [ff.exe(), "-hide_banner", "-nostats", "-xerror", "-i", str(video), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    loud = decoded.stderr
    summary = loud[loud.rfind("Summary:") :]
    lufs, peak = _LUFS.search(summary), _PEAK.search(summary)

    manifest = json.loads((work / "manifest.json").read_text(encoding="utf-8"))
    beats = []
    for i, beat in enumerate(manifest["beats"]):
        # One frame from the middle of each shot: a long beat can cut from the whole picture to a close-up.
        paths = []
        for k, shot in enumerate(beat.get("shots") or [{"start": beat["start"], "end": beat["end"]}]):
            frame = frames / (f"frame{i:02d}.jpg" if k == 0 else f"frame{i:02d}_{k}.jpg")
            ff.run("-ss", f"{(shot['start'] + shot['end']) / 2:.2f}", "-i", video, "-frames:v", "1", "-vf", "scale=540:-1", frame)
            paths.append(str(frame))
        asset = beat["asset"]
        beats.append(
            {
                "beat": i,
                "seconds": round(beat["end"] - beat["start"], 2),
                "text": beat["text"],
                "source": asset.get("source"),
                "title": asset.get("title"),
                "license": asset.get("license"),
                "frame": paths[0],
                "frames": paths,
            }
        )
    duration = round(ff.duration(video), 2)
    integrated = float(lufs.group(1)) if lufs else None
    true_peak = float(peak.group(1)) if peak else None
    warnings = _warnings(duration, integrated, true_peak, beats)
    if decoded.returncode:
        warnings.append(f"full audio/video decode failed (ffmpeg exit {decoded.returncode})")
    return {
        "video": str(video),
        "duration": duration,
        "words": len(manifest["words"]),
        "streams": streams,
        "integrated_lufs": integrated,
        "true_peak_dbfs": true_peak,
        "warnings": warnings,
        # The mixed, encoded file is what Buffer receives. A clean narration WAV cannot
        # prove that its final AAC track is complete or intelligible under the music.
        "speech": speech(video, manifest["beats"]),
        "beats": beats,
    }


def write_speech(work: Path) -> None:
    """Save the speech check next to the narration, so a cloud render brings it back with the Short."""
    beats = json.loads((work / "manifest.json").read_text(encoding="utf-8"))["beats"]
    (work / "speech.json").write_text(json.dumps(speech(work / "narration.wav", beats), indent=2), encoding="utf-8")


def speech(media: Path, beats: list[dict]) -> dict:
    """Check the encoded final audio; corroborate only minor disputed words.

    A second model must hear the scripted span before a minor primary finding is
    cleared. Content words, names, source terms, and changed numbers stay blocked
    even if the second model disagrees with the first.
    """
    try:
        from transformers.models.whisper.english_normalizer import EnglishTextNormalizer

        with media.open("rb") as source:
            media_sha256 = hashlib.file_digest(source, "sha256").hexdigest()
        heard_text = _transcribe(media, ASR_MODEL)
    except Exception as error:  # the rest of the check is still worth having
        return {"error": f"{type(error).__name__}: {error}"}
    # Whisper's own normalizer, so "four million" in the script matches "4 million" in the transcript.
    normalize = EnglishTextNormalizer({})
    script, clock_spans = _script_context(beats, normalize)
    heard = _words(normalize(_numerals(_speech_equivalents(heard_text))))
    primary = _differences(script, heard)
    result = {"heard": heard_text, "model": ASR_MODEL, "media_sha256": media_sha256,
              "primary_differences": [issue["message"] for issue in primary],
              "differences": [issue["message"] for issue in primary]}
    if not primary or media.suffix.lower() != ".mp4":
        return result
    try:
        second_text = _transcribe(media, CORROBORATING_ASR_MODEL)
    except Exception as error:
        result["corroboration"] = {"model": CORROBORATING_ASR_MODEL,
                                   "error": f"{type(error).__name__}: {error}", "resolved": []}
        return result
    second = _differences(script, _words(normalize(_numerals(_speech_equivalents(second_text)))))
    resolved, unresolved = _reconcile(primary, second, len(script), clock_spans)
    result["corroboration"] = {"model": CORROBORATING_ASR_MODEL, "heard": second_text,
                               "differences": [issue["message"] for issue in second], "resolved": resolved}
    result["differences"] = unresolved
    return result


def _transcribe(media: Path, model_name: str) -> str:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(media), language="en", temperature=0.0,
                                   condition_on_previous_text=False)
    return " ".join(segment.text.strip() for segment in segments)


def _differences(script: list[str], heard: list[str]) -> list[dict]:
    findings = []
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(a=script, b=heard, autojunk=False).get_opcodes():
        wrote, said = script[a1:a2], heard[b1:b2]
        if op == "equal" or "".join(wrote) == "".join(said):
            continue
        before = " ".join(script[max(a1 - 3, 0):a1])
        message = f"{' '.join(wrote) or '(nothing)'!r} heard as {' '.join(said) or '(nothing)'!r}"
        findings.append({"start": a1, "end": a2, "wrote": wrote, "heard": said,
                         "message": message + (f" after {before!r}" if before else "")})
    return findings


def _script_context(beats: list[dict], normalize) -> tuple[list[str], set[tuple[int, int]]]:
    scripted_text = " ".join(_OVERRIDE.sub(r"\1", beat["text"]) for beat in beats)
    script = _words(normalize(_speech_equivalents(scripted_text)))
    clock_spans = set()
    for match in _CLOCK_TIME.finditer(scripted_text):
        start = len(_words(normalize(_speech_equivalents(scripted_text[:match.start()]))))
        if script[start:start + 2] == [match.group(1), match.group(2)]:
            clock_spans.add((start, start + 2))
    return script, clock_spans


def _reconcile(primary: list[dict], second: list[dict], script_length: int,
               clock_spans: set[tuple[int, int]]) -> tuple[list[str], list[str]]:
    resolved, unresolved = [], []
    for issue in primary:
        if _minor_difference(issue, script_length, clock_spans) and _second_supports(issue, second, script_length):
            resolved.append(issue["message"])
        else:
            unresolved.append(issue["message"])
    # The second model can expose a source, number, or content-word fault that
    # small.en missed. Its independent minor noise does not veto an exact match.
    for issue in second:
        if not _minor_difference(issue, script_length, clock_spans):
            finding = f"{CORROBORATING_ASR_MODEL}: {issue['message']}"
            if finding not in unresolved:
                unresolved.append(finding)
    return resolved, unresolved


def _minor_difference(issue: dict, script_length: int, clock_spans: set[tuple[int, int]]) -> bool:
    wrote, heard = issue["wrote"], issue["heard"]
    if (len(wrote) == 2 and len(heard) == 1 and (issue["start"], issue["end"]) in clock_spans
            and heard[0] == f"{wrote[0]}.{wrote[1]}"):
        # Whisper sometimes prints a clock time with a decimal separator. A
        # second model must still hear the scripted time tokens to clear it.
        return True
    if not wrote and heard == ["you"]:
        return issue["start"] == script_length  # an alleged stray after the ending only
    # One short word can be a recognition artifact. A run of missing or added
    # words, and a changed connective such as "and"/"or", needs human review.
    return (len(wrote) <= 1 and len(heard) <= 1 and bool(wrote or heard)
            and all(word in _MINOR_WORDS for word in [*wrote, *heard]))


def _second_supports(issue: dict, second: list[dict], script_length: int) -> bool:
    start, end = issue["start"], issue["end"]
    for other in second:
        lo, hi = other["start"], other["end"]
        if lo == hi:
            if start <= lo <= end:
                return False
        elif start == end:
            if lo <= max(0, start - 1) < hi or lo <= min(start, script_length - 1) < hi:
                return False
        elif lo < end and hi > start:
            return False
    return True


def speech_verified(speech_result: dict | None, media_sha256: str | None = None,
                    beats: list[dict] | None = None) -> bool:
    """Whether transcripts prove a clean result for the exact reviewed media.

    Older review summaries have only ``differences`` and ``error``. Their clean
    results remain usable until a full verification record is present. With
    beats, recompute every claimed finding from both retained transcripts.
    """
    if (not isinstance(speech_result, dict) or speech_result.get("error")
            or speech_result.get("differences") != []):
        return False
    if beats is None and "primary_differences" not in speech_result:
        return True  # a clean legacy summary, without a retained verification record
    if media_sha256 is not None and speech_result.get("media_sha256") != media_sha256:
        return False
    primary = speech_result.get("primary_differences")
    if (speech_result.get("model") != ASR_MODEL or not isinstance(speech_result.get("heard"), str)
            or not _messages(primary) or not re.fullmatch(r"[0-9a-f]{64}", str(speech_result.get("media_sha256")))):
        return False
    if primary:
        corroboration = speech_result.get("corroboration")
        if (not isinstance(corroboration, dict) or corroboration.get("model") != CORROBORATING_ASR_MODEL
                or not isinstance(corroboration.get("heard"), str) or not _messages(corroboration.get("differences"))
                or not _messages(corroboration.get("resolved")) or corroboration["resolved"] != primary
                or "error" in corroboration):
            return False
    elif "corroboration" in speech_result:
        return False
    if beats is None:
        return True
    try:
        from transformers.models.whisper.english_normalizer import EnglishTextNormalizer

        normalize = EnglishTextNormalizer({})
        script, clock_spans = _script_context(beats, normalize)
        actual_primary = _differences(script, _words(normalize(_numerals(_speech_equivalents(speech_result["heard"])))))
        if primary != [issue["message"] for issue in actual_primary]:
            return False
        if not primary:
            return True
        actual_second = _differences(script, _words(normalize(_numerals(_speech_equivalents(corroboration["heard"])))))
        resolved, unresolved = _reconcile(actual_primary, actual_second, len(script), clock_spans)
        return (corroboration["differences"] == [issue["message"] for issue in actual_second]
                and corroboration["resolved"] == resolved and speech_result["differences"] == unresolved)
    except (AttributeError, ImportError, KeyError, TypeError, ValueError):
        return False


def _messages(items) -> bool:
    return isinstance(items, list) and all(isinstance(item, str) and bool(item) for item in items)


def _words(text: str) -> list[str]:
    return [word for word in text.split() if any(char.isalnum() for char in word)]


def _speech_equivalents(text: str) -> str:
    """Canonicalize only known ways ASR writes the same spoken ep064 words."""
    text = _HENRY_FIFTH.sub("Henry the Fifth", text)
    return _SPELLING_VARIANT.sub(lambda match: _SAME_SPOKEN_WORD[match.group().casefold()], text)


def _numerals(text: str) -> str:
    """Whisper writes "World War One" as "World War I" and "Stephen the Sixth" as "Stephen VI"."""
    return _ROMAN.sub(_ordinal, _WAR.sub(lambda war: f"War {len(war.group(1))}", text))


def _ordinal(numeral: re.Match) -> str:
    values = [{"I": 1, "V": 5, "X": 10}[letter] for letter in numeral.group()]
    n = sum(-v if i + 1 < len(values) and v < values[i + 1] else v for i, v in enumerate(values))
    return f"the {n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _warnings(duration: float, integrated: float | None, true_peak: float | None, beats: list[dict]) -> list[str]:
    """The quality gate's measurable rules (PLAYBOOK.md step 6), plus beats that fell back to a placeholder."""
    found = []
    if not DURATION[0] <= duration <= DURATION[1]:
        found.append(f"duration {duration} s is outside {DURATION[0]}-{DURATION[1]} s")
    if integrated is None or abs(integrated + 14) > 1:
        found.append(f"loudness {integrated} LUFS is outside -14 +/- 1")
    if true_peak is None or true_peak > -1:
        found.append(f"true peak {true_peak} dBFS is above -1")
    for beat in beats:
        where = f"beat {beat['beat'] + 1} ({Path(beat['frame']).name})"
        if beat["source"] == "generated gradient":
            found.append(f"{where} is a plain gradient: every image source failed")
        elif beat["source"] == "AI generated":
            found.append(f"{where} is AI-generated: set synthetic_media if it looks real")
    return found
