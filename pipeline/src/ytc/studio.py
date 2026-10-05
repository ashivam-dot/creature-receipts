"""Make a Short with no one at the keyboard: research, script, pictures, render, checks, a look at the result
with fixes, and a hosted copy that waits for a Buffer slot.

Each stage saves its result in the episode folder, so a run that stops (out of quota, out of time) picks the
episode up where it left off.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from PIL import Image

from . import llm, pick, writer
from .research import research as do_research

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
EPISODES = ROOT / "content" / "episodes"
REJECTED = ROOT / "content" / "rejected"
# Episodes from the channel's first niche (animals, until 2026-10-01): kept for their numbers, never published.
SHELVED = ROOT / "content" / "shelved"
IST = ZoneInfo("Asia/Kolkata")
# Kokoro am_fenrir scored 4.51 and 4.49 predicted naturalness (UTMOS22) on two scripts, against 3.80 for the
# Gemini Charon "fast and urgent" read (245 words a minute) and 4.2-4.3 for the best warm Gemini voices
# (voice-samples/, 2026-10-02). It also has no daily quota and never reads its direction aloud.
VOICE = {"engine": "kokoro", "voice": "am_fenrir", "speed": 1.15}
GATE = ["hook", "clarity", "payoff", "visuals", "loop", "accuracy"]
PASS_SCORE = 4
# The recognizer drops or swaps a short word on clean narration; a judge who heard no error settles that many.
MINOR_ASR_DIFFERENCES = 2
FIX_ROUNDS = 2
MAX_ATTEMPTS = 3
# Set per job (auto.LAST_RESORT_BELOW) when so few Shorts are ready that the channel would soon post nothing.
LAST_RESORT = False

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {"type": "object", "properties": {k: {"type": "integer"} for k in GATE}, "required": GATE},
        "notes": {"type": "object", "properties": {k: {"type": "string"} for k in GATE}, "required": GATE},
        "frames": {"type": "array", "items": {"type": "object", "properties": {
            "beat": {"type": "integer"}, "problem": {"type": "string"}}, "required": ["beat", "problem"]}},
        "speech": {"type": "array", "items": {"type": "object", "properties": {
            "beat": {"type": "integer"}, "word": {"type": "string"}, "respelling": {"type": "string"}},
            "required": ["beat", "word", "respelling"]}},
        "rewrite": {"type": "array", "items": {"type": "string"}},
        "better_than_last": {"type": "string"},
    },
    "required": ["scores", "notes", "frames", "speech", "rewrite", "better_than_last"],
}

REVIEW_PROMPT = """You are the quality gate for History's Last Hours, a YouTube Shorts channel of true, sourced
stories of history's tragedies (lost cities, doomed voyages and expeditions, fallen empires, ignored warnings, and
the few who survived), each told through the people in it, gravely and without gore, in 17 to 35 seconds. Judge
this rendered Short as a demanding editor would. Below are the script with each beat's timing,
one frame from the middle of each shot (what viewers see, captions included; a long beat can cut to a close-up,
so it has two), and the automatic checks.

Score 1 to 5 (5 excellent, 4 good enough to publish, 3 or lower must be fixed), with a one-line note each:
- hook: would a stranger stop swiping within the first 2 seconds?
- clarity: can someone who knows nothing about it follow on one listen? One idea per beat.
- payoff: is there a real surprise or twist near the end that pays off the hook?
- visuals: is every frame on-topic, clear at phone size, and striking?
- loop: does the last line run straight into the first, so a replay feels seamless?
- accuracy: check the title, the on-screen text, and every spoken line against the research claims and the
  disputed points listed below. Score 3 or lower if anything says more than the claims support: a number,
  date, or count that differs; a cause, motive, or outcome stated as settled when the claims hedge it or the
  disputed points list it; a word that changes the meaning (an on-screen "52 YEARS OF DARKNESS" for a
  ceremony held every 52 years, "ground zero" for 3 km away, "accidentally" when the source says deliberate);
  a "many believe" strawman no claim supports; two events merged into one; or a picture presented as the
  event's own when its title says it is another. Score 5 only when every line is backed as worded.

Also:
- frames: each beat whose frame has a problem (off-topic, anachronistic, the wrong ship, city, or person, corpses or gore, nudity, a big watermark,
  mostly text, the subject cropped out, blurry, the same picture as another beat, or a print too small to read at phone size), with the problem.
  Use the image title and date listed beside each beat to check what the image actually depicts. A modern photo of
  another historical event is not an archive photo of this event; flag it when the narration presents it as such.
  Leave out beats that are fine. {loop_note}
- speech: the recognizer's differences are listed. For each real mispronunciation (not another spelling of
  a correctly spoken name, not a skipped short word), give the beat, the word exactly as written in the
  beat, and a respelling in plain lowercase words that a text-to-speech voice would read correctly
  (Formosus: "for moe sus").
- rewrite: if hook, clarity, payoff, loop, or accuracy is under 4, or the duration is outside 17-35 s, up to 4
  concrete changes (which beat or the on-screen text, what to say instead), using only facts in the research
  claims, worded no more certainly than they are. Otherwise empty.
- better_than_last: one sentence on what this Short does better than the recent ones listed, or "" if nothing.

Recent Shorts and their scores:
{recent}
"""


def _write(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def next_id() -> str:
    numbers = [int(p.name[2:]) for folder in (EPISODES, REJECTED, SHELVED) if folder.exists()
               for p in folder.glob("ep[0-9][0-9][0-9]") if p.is_dir()]
    return f"ep{max(numbers, default=0) + 1:03d}"


def _clean(visual: dict) -> dict:
    return {k: v for k, v in visual.items() if not k.startswith("_")}


def spec_from(script: dict, visuals: list[dict], research: dict, episode_id: str) -> dict:
    cited = [c for beat in script["beats"] for c in beat.get("claims", [])]
    labels = [s for n in dict.fromkeys(cited) if 1 <= n <= len(research["claims"]) for s in research["claims"][n - 1]["sources"]]
    by_label = {s["label"]: s["url"] for s in research["sources"]}
    beats = []
    for beat, visual in zip(script["beats"], visuals):
        item = {"text": beat["text"], "emphasis": beat["emphasis"]}
        if beat.get("sfx", "none") != "none":
            item["sfx"] = beat["sfx"]
        if abs(beat.get("pause_after", 0.12) - 0.12) > 0.001:
            item["pause_after"] = beat["pause_after"]
        item["visual"] = _clean(visual)
        beats.append(item)
    spec = {
        "id": episode_id,
        "title": script["title"],
        "series": research["series"],
        "description": script["description"],
        "sources": list(dict.fromkeys(by_label[l] for l in labels if l in by_label)),
        "hashtags": script["hashtags"],
        "tags": script["tags"],
        "voice": VOICE,
        "beats": beats,
        "depth_motion": True,
    }
    if script.get("hook_text"):
        spec["hook_text"] = script["hook_text"]
    return spec


def _save_spec(folder: Path, spec: dict) -> Path:
    path = folder / "short.yaml"
    path.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    return path


def contact_sheet(folder: Path, frames: list[Path]) -> Path:
    width, per_row = 180, 6
    tiles = [Image.open(f).convert("RGB") for f in frames if f.exists()]
    tiles = [t.resize((width, round(t.height * width / t.width))) for t in tiles]
    height = max((t.height for t in tiles), default=320)
    rows = (len(tiles) + per_row - 1) // per_row or 1
    sheet = Image.new("RGB", (width * min(per_row, max(len(tiles), 1)), height * rows), "black")
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % per_row) * width, (i // per_row) * height))
    path = folder / "sheet.jpg"
    sheet.save(path, quality=78)
    return path


def recent_scores(count: int = 3, exclude: str = "") -> str:
    lines = []
    for folder in sorted(EPISODES.glob("ep[0-9][0-9][0-9]"), reverse=True):
        if folder.name == exclude or not ((folder / "publish.json").exists() or (folder / "hold.json").exists()):
            continue
        spec = yaml.safe_load((folder / "short.yaml").read_text(encoding="utf-8"))
        text = (folder / "research.md").read_text(encoding="utf-8") if (folder / "research.md").exists() else ""
        match = re.search(r"\| Hook \| Clarity \| Payoff \| Visuals \| Loop [^\n]*\|\n\|[-| ]+\|\n\|([^\n]+)\|", text)
        scores = match.group(1).replace(" ", "") if match else "unscored"
        lines.append(f"- {folder.name} \"{spec['title']}\": hook|clarity|payoff|visuals|loop = {scores}; "
                     f"beat 1: \"{spec['beats'][0]['text']}\"")
        if len(lines) == count:
            break
    return "\n".join(lines) or "- none yet"


def _loop_reuse(script: dict, visuals: list[dict]) -> bool:
    return bool(script.get("loop")) and len(visuals) > 1 and visuals[-1].get("reuse") == 1


def review(folder: Path, script: dict, result: dict, episode_id: str, visuals: list[dict]) -> dict:
    manifest = _read(folder / "work" / "manifest.json")
    last = len(script["beats"])
    loop = _loop_reuse(script, visuals)
    reuse_notes = []
    for n, visual in enumerate(visuals, start=1):
        if loop and n == last:
            reuse_notes.append(f"Beat {n} deliberately shows beat 1's picture again so the replay is seamless: "
                               f"never flag beat {n}'s frame.")
        elif visual.get("reuse"):
            reuse_notes.append(f"Beat {n} deliberately shows beat {visual['reuse']}'s picture again, framed differently, "
                               f"because no better picture was found: flag it only if the picture doesn't fit what beat {n} says.")
        elif visual.get("source") == "card":
            reuse_notes.append(f"Beat {n} is a designed title card (a date, number, or quote on a dark background), chosen "
                               f"on purpose: flag it only if it is hard to read or doesn't fit what beat {n} says.")
    parts: list = [REVIEW_PROMPT.format(recent=recent_scores(exclude=episode_id), loop_note=" ".join(reuse_notes))]
    if research := _read(folder / "research.json"):
        claims = []
        for n, claim in enumerate(research.get("claims", []), start=1):
            quotes = " | ".join(f"{e.get('source')}: \"{e.get('quote', '')[:240]}\"" for e in claim.get("evidence", [])[:2])
            claims.append(f"{n}. [{claim.get('confidence', '?')}] {claim['claim']}" + (f" (quotes: {quotes})" if quotes else ""))
        disputed = [f"- {d}" for d in research.get("disputed", [])]
        parts.append("\nResearch claims (each beat lists the numbers it cites):\n" + "\n".join(claims)
                     + ("\nDisputed or left out:\n" + "\n".join(disputed) if disputed else ""))
    parts.append(f"\nTitle: {script['title']}\nDescription: {script['description']}")
    if script.get("hook_text"):
        parts.append(f"On-screen text over beat 1: \"{script['hook_text']}\"")
    for i, (beat, frame) in enumerate(zip(manifest["beats"], result["beats"]), start=1):
        cites = script["beats"][i - 1].get("claims", []) if i <= len(script["beats"]) else []
        parts.append(f"\nBeat {i} ({beat['start']:.1f}-{beat['end']:.1f} s, cites claims {cites or 'none'}): \"{beat['text']}\"")
        visual = visuals[i - 1]
        if choice := visual.get("_choice"):
            parts.append(f"Image: {choice.get('title', 'untitled')}; recorded date: {choice.get('date') or 'unknown'}; "
                         f"fit: {visual.get('_fit', 'unrated')}; actually shows: {visual.get('_shows') or 'not recorded'}")
        parts += [Path(f) for f in frame.get("frames", [frame["frame"]]) if Path(f).exists()]
    speech = result.get("speech", {})
    parts.append(
        "\nChecks: duration {d} s, {w} words, loudness {l} LUFS, true peak {p} dBFS; warnings: {warn}; "
        "speech recognizer differences: {diff}".format(
            d=result["duration"], w=result["words"], l=result["integrated_lufs"], p=result["true_peak_dbfs"],
            warn="; ".join(result["warnings"]) or "none",
            diff="; ".join(speech.get("differences", [])) or ("check failed: " + speech["error"] if speech.get("error") else "none"),
        )
    )
    # The gate is a Flash model while plenty of Shorts are ready: drafts from the fallback models are judged to the
    # same standard, and the Short waits for Gemini's reset rather than being passed by a weaker judge. When few are
    # ready (llm.CURSOR_FALLBACK), a strong backup model (llm.JUDGES) or Cursor judges, and a backup passes only a
    # Short it finds nothing to fix in (_passes). Only when the channel is about to run out of Shorts (LAST_RESORT)
    # does Gemma judge instead of nobody.
    judges = llm.FLASH + (llm.JUDGES if llm.CURSOR_FALLBACK else ())
    try:
        verdict = llm.generate(parts, schema=REVIEW_SCHEMA, models=judges, purpose=f"{episode_id} review")
    except (llm.OutOfQuota, llm.Overloaded):
        if not LAST_RESORT:
            raise
        verdict = llm.generate(parts, schema=REVIEW_SCHEMA, models=("gemma-4-31b-it",),
                               purpose=f"{episode_id} review (last resort)")
    verdict["judge"] = llm.answered_by()
    if loop:
        verdict["frames"] = [f for f in verdict["frames"] if f.get("beat") != last]
    return verdict


def _minor_asr_dispute(result: dict, verdict: dict) -> bool:
    speech = result.get("speech") or {}
    differences = speech.get("differences")
    return (not speech.get("error") and isinstance(differences, list)
            and 0 < len(differences) <= MINOR_ASR_DIFFERENCES and not verdict["speech"])


def _passes(result: dict, verdict: dict, final: bool) -> bool:
    if result["warnings"] or any(verdict["scores"].get(k, 0) < PASS_SCORE for k in GATE):
        return False
    from .check import speech_verified

    if (not speech_verified(result.get("speech"), result.get("media_sha256"), result.get("beats"))
            and not _minor_asr_dispute(result, verdict)):
        # A judge may suggest a pronunciation fix, but cannot clear a failed or
        # unresolved recognition of the exact encoded video being hosted.
        return False
    # A final-round score cannot waive an identified wrong image or pronunciation.
    # If a source-matched picture is unavailable, the editor can use a clearly
    # labelled card; the issue must be resolved before hosting the episode.
    return not verdict["frames"] and not verdict["speech"]


# A round's files, kept while it is the best so far: a fix can make a Short worse, and the final round then
# falls back to the best one if that one would pass.
BEST = "best"
_BEST_FILES = ("script.json", "visuals.json", "short.yaml", "sheet.jpg", "work/manifest.json", "work/speech.json",
               "work/captions.srt", "work/captions.ass")


def _standing(round_: dict) -> tuple:
    """How good a reviewed round is: passing by the final rule first, then its lowest score, total, and frames."""
    scores = round_["scores"]
    check = round_["check"]
    speech = check.get("speech_verification") or {
        "differences": check.get("speech_differences"), "error": check.get("speech_error")}
    passes = _passes({"warnings": check["warnings"], "speech": speech,
                      "media_sha256": round_.get("media_sha256")}, round_, final=True)
    return (passes, min(scores.values()), sum(scores.values()), -len(round_["frames"]), -len(round_["speech"]))


def _keep_best(folder: Path) -> None:
    best = folder / BEST
    shutil.rmtree(best, ignore_errors=True)
    for name in (*_BEST_FILES, f"{folder.name}.mp4"):
        if (folder / name).exists():
            (best / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(folder / name, best / name)


def _restore_best(folder: Path) -> None:
    best = folder / BEST
    for path in sorted(best.rglob("*")):
        if path.is_file():
            target = folder / path.relative_to(best)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    shutil.rmtree(best)


def _override(text: str, word: str, respelling: str) -> str:
    from .tts import phonemes

    if f"[{word}](" in text:
        return text
    sounds = phonemes(respelling.lower()).replace(" ", "")
    return re.sub(rf"(?<![\w\[]){re.escape(word)}(?!\w)", lambda _: f"[{word}](/{sounds}/)", text, count=1)


renders: list[str] = []
# Shorts made side by side (auto.LANES) render and check one at a time: those share the CPU and the voice and
# speech models.
CPU_LOCK = threading.Lock()


def record_draft(spec_path: Path, episode_id: str, title: str, series: str, scores: dict, anniversary: str | None) -> dict:
    """Bind the reviewed render without giving the producer a publishing destination."""
    from .publish import _stamp_manifest_media, media_binding

    folder = spec_path.parent
    _stamp_manifest_media(folder, episode_id)
    binding = media_binding(spec_path, episode_id)
    draft = {"id": episode_id, "title": title, "series": series, "scores": scores,
             "anniversary": anniversary, **binding, "modal_volume": "creature-receipts-outbox",
             "modal_path": f"drafts/{episode_id}-{binding['media_sha256']}.mp4"}
    _write(folder / "draft.json", draft)
    (folder / "hold.json").unlink(missing_ok=True)
    (folder / "release_certificate.json").unlink(missing_ok=True)
    (folder / "independent_review.json").unlink(missing_ok=True)
    return draft


def _render(spec_path: Path) -> Path:
    """On Modal when it's set up and working (or when this is a Modal worker), otherwise on this machine."""
    if (os.environ.get("MODAL_TOKEN_ID") or os.environ.get("YTC_ON_MODAL")) and os.environ.get("YTC_RENDER_HERE") != "1":
        try:
            from .cloud import render

            video = render(spec_path)
            renders.append("modal")
            return video
        except Exception as err:  # quota, network, image build
            if os.environ.get("YTC_ON_MODAL"):
                # A studio worker is sized for waiting on Gemini, not for rendering.
                raise
            log.warning("Modal render failed (%s); rendering on this machine", err)
    from .render import make_short

    video = make_short(spec_path)
    renders.append("runner")
    return video


def _summary(result: dict) -> dict:
    summary = {k: result.get(k) for k in ("duration", "words", "integrated_lufs", "true_peak_dbfs", "warnings")} | {
        "speech_differences": result.get("speech", {}).get("differences"),
        "speech_error": result.get("speech", {}).get("error"),
        "sources": [b["source"] for b in result["beats"]],
    }
    if isinstance(result.get("speech"), dict):
        summary["speech_verification"] = result["speech"]
    return summary


def _speech_only_block(result: dict, verdict: dict) -> bool:
    from .check import speech_verified

    return (not speech_verified(result.get("speech"), result.get("media_sha256"), result.get("beats"))
            and not result["warnings"] and not verdict["frames"]
            and all(verdict["scores"].get(name, 0) >= PASS_SCORE for name in GATE))


def _reject_speech(folder: Path, meta: dict, result: dict) -> dict:
    speech = result.get("speech") or {}
    reason = "speech: " + ("; ".join(speech.get("differences") or []) or speech.get("error") or "recognizer disagreed")
    reject(folder, reason[:400])
    return {"id": folder.name, "outcome": "rejected", "topic": meta["topic"], "reason": reason[:400]}


def reject(folder: Path, reason: str) -> Path:
    REJECTED.mkdir(parents=True, exist_ok=True)
    notes = _read(folder / "review.json") or {}
    _write(folder / "review.json", notes | {"verdict": "rejected", "reason": reason,
                                            "rejected_at": datetime.now(IST).isoformat(timespec="seconds")})
    for bulky in (folder / f"{folder.name}.mp4", folder / "work"):
        if bulky.is_dir():
            shutil.rmtree(bulky)
        else:
            bulky.unlink(missing_ok=True)
    target = REJECTED / folder.name
    if target.exists():
        shutil.rmtree(target)
    shutil.move(str(folder), target)
    log.warning("%s rejected: %s", folder.name, reason)
    return target


def _visual_plan_problem(visuals: list[dict]) -> str | None:
    """Stop an art-poor plan before paying to render a Short it cannot pass."""
    cards = [n for n, visual in enumerate(visuals, 1) if visual.get("source") == "card"]
    if 1 in cards:
        return "the hook has a title card"
    if len(cards) > 2:
        return f"{len(cards)} title cards exceed the two-card limit"
    original_art = sum(bool(visual.get("source") and visual.get("source") not in {"card", "color"}
                            and not visual.get("reuse")) for visual in visuals)
    minimum = 3 if len(visuals) >= 6 else 2 if len(visuals) >= 4 else 1
    if original_art < minimum:
        return f"only {original_art} original art beats; {minimum} are needed for {len(visuals)} beats"
    return None


def _reject_visual_plan(folder: Path, meta: dict, visuals: list[dict]) -> dict | None:
    problem = _visual_plan_problem(visuals)
    # A researched episode may pin its dated/licensed art. Review rewrites can still ask the
    # picker for replacements; reject an unreviewed URL before spending another render on it.
    if not problem and (approved := meta.get("approved_art_sha256")):
        for number, visual in enumerate(visuals, 1):
            if visual.get("reuse") or visual.get("source") == "card":
                continue
            path = visual.get("path") if visual.get("source") == "file" else None
            if path not in approved:
                problem = f"beat {number} uses art outside the approved source set"
                break
            asset = folder / path
            if not asset.is_file() or hashlib.sha256(asset.read_bytes()).hexdigest() != approved[path]:
                problem = f"beat {number} approved art hash changed or is missing"
                break
    if problem:
        reason = f"visual plan: {problem}"
        reject(folder, reason)
        return {"id": folder.name, "outcome": "rejected", "topic": meta["topic"], "reason": reason}
    return None


def _pinned_rewrite_problem(before: dict, after: dict) -> str | None:
    """A story rewrite may keep curated pictures only when each beat still names its old event."""
    old, new = before.get("beats", []), after.get("beats", [])
    if len(old) != len(new):
        return "changed the beat count of the approved visual plan"
    for number, (was, now) in enumerate(zip(old, new), 1):
        if not set(was.get("claims", [])) & set(now.get("claims", [])):
            return f"beat {number} no longer cites an original visual claim"
        if was.get("year") != now.get("year"):
            return f"beat {number} changed the approved visual year"
        original = set(was.get("subjects", []))
        revised = set(now.get("subjects", []))
        if original and revised and not original & revised:
            return f"beat {number} changed the approved visual subject"
    return None


def produce(topic: str, series: str, episode_id: str | None = None, *, at: str | None = None) -> dict:
    """Make one Short (or finish a half-made one) and host it. Returns what happened, for the run's status."""
    from .check import DURATION, check
    from .publish import hold

    episode_id = episode_id or next_id()
    folder = EPISODES / episode_id
    if (folder / "editorial_hold.json").exists():
        raise RuntimeError(f"{episode_id} is on editorial hold; remove editorial_hold.json after repair and review")
    folder.mkdir(parents=True, exist_ok=True)
    meta = _read(folder / "topic.json") or {"topic": topic, "series": series, "at": at,
                                              "started_at": datetime.now(IST).isoformat(timespec="seconds"), "attempts": 0}
    if (folder / "hold.json").exists() or (folder / "publish.json").exists():
        return {"id": episode_id, "outcome": "ready", "topic": meta["topic"]}
    meta["attempts"] += 1
    _write(folder / "topic.json", meta)
    if meta["attempts"] > MAX_ATTEMPTS:
        reject(folder, f"still unfinished after {MAX_ATTEMPTS} runs")
        return {"id": episode_id, "outcome": "rejected", "topic": meta["topic"], "reason": "too many attempts"}

    research = _read(folder / "research.json")
    source_plan = meta.get("research_sources")
    if research is None:
        if source_plan:
            research = do_research(meta["topic"], meta["series"],
                                   source_plan=source_plan, cautions=meta.get("research_cautions"))
        else:
            research = do_research(meta["topic"], meta["series"])
        _write(folder / "research.json", research)
    if not research.get("viable"):
        reason = f"research: {research.get('reason')}"
        reject(folder, reason)
        return {"id": episode_id, "outcome": "rejected", "topic": meta["topic"], "reason": reason}

    script = _read(folder / "script.json")
    if script is None:
        script = writer.write_script(research, episode_id)
        _write(folder / "script.json", script)
    visuals = _read(folder / "visuals.json")
    if visuals is None:
        visuals = pick.pick(script, research, episode_id)
        _write(folder / "visuals.json", visuals)
    if blocked := _reject_visual_plan(folder, meta, visuals):
        return blocked

    notes = _read(folder / "review.json") or {"rounds": []}
    spec_path = _save_spec(folder, spec_from(script, visuals, research, episode_id))
    video = folder / f"{episode_id}.mp4"
    while True:
        with CPU_LOCK:
            if not video.exists() or video.stat().st_mtime < spec_path.stat().st_mtime:
                video = _render(spec_path)
            result = check(video)
            frames = [Path(f) for b in result["beats"] for f in b.get("frames", [b["frame"]])]
            contact_sheet(folder, frames)
        verdict = review(folder, script, result, episode_id, visuals)
        final = len(notes["rounds"]) >= FIX_ROUNDS
        with video.open("rb") as rendered:
            media_sha256 = hashlib.file_digest(rendered, "sha256").hexdigest()
        result["media_sha256"] = media_sha256
        passed = _passes(result, verdict, final)
        previous = notes["rounds"][-1]["check"] if notes["rounds"] else None
        repeated_speech = (previous is not None
                           and previous.get("speech_differences") == result.get("speech", {}).get("differences")
                           and previous.get("speech_error") == result.get("speech", {}).get("error"))
        notes["rounds"].append({"at": datetime.now(IST).isoformat(timespec="seconds"), "check": _summary(result),
                                "media_sha256": media_sha256, **verdict,
                                "passed": passed})
        best = notes.get("best_round")
        if best is None or not (folder / BEST).exists() or _standing(notes["rounds"][-1]) > _standing(notes["rounds"][best - 1]):
            _keep_best(folder)
            notes["best_round"] = len(notes["rounds"])
        _write(folder / "review.json", notes)
        log.info("%s review %d: %s%s", episode_id, len(notes["rounds"]), verdict["scores"], " (passed)" if passed else "")
        if passed:
            break
        if _speech_only_block(result, verdict) and (not verdict["speech"] or repeated_speech):
            shutil.rmtree(folder / BEST, ignore_errors=True)
            return _reject_speech(folder, meta, result)
        if final:
            best = notes["best_round"]
            if best != len(notes["rounds"]) and _standing(notes["rounds"][best - 1])[0]:
                log.info("%s: round %d was better and passes; keeping it", episode_id, best)
                _restore_best(folder)
                notes["rounds"][best - 1]["passed"] = True
                notes["kept_round"] = best
                _write(folder / "review.json", notes)
                script, visuals = _read(folder / "script.json"), _read(folder / "visuals.json")
                spec_path = folder / "short.yaml"
                break
            low = [k for k in GATE if verdict["scores"][k] < PASS_SCORE]
            reason = "; ".join(filter(None, [
                f"low scores: {', '.join(low)}" if low else "", "; ".join(result["warnings"]),
                f"{len(verdict['frames'])} frame problems" if verdict["frames"] else "",
                f"{len(verdict['speech'])} speech problems" if verdict["speech"] else ""]))
            shutil.rmtree(folder / BEST, ignore_errors=True)
            reject(folder, reason or "failed the quality gate")
            return {"id": episode_id, "outcome": "rejected", "topic": meta["topic"], "reason": reason}

        story = ("hook", "clarity", "payoff", "loop", "accuracy")
        rewrite = verdict["rewrite"] or [f"{k}: {verdict['notes'][k]}" for k in story if verdict["scores"][k] < PASS_SCORE]
        low, high = DURATION
        if any(verdict["scores"][k] < PASS_SCORE for k in story) or not low <= result["duration"] <= high:
            if not low <= result["duration"] <= high:
                rewrite.append(f"The render ran {result['duration']} s; it must be {low}-{high} s.")
            if meta.get("approved_art_sha256"):
                rewrite.append("Keep the exact beat count, original claims, visual subjects, and years in their numbered beats; "
                               "only revise the wording. These dated images are already approved and cannot be replaced.")
            old_script, script = script, writer.write_script(research, episode_id, feedback=rewrite, draft=script)
            if meta.get("approved_art_sha256"):
                if problem := _pinned_rewrite_problem(old_script, script):
                    reason = f"pinned script revision needs editorial review: {problem}"
                    notes["revision_hold"] = reason
                    _write(folder / "review.json", notes)
                    return {"id": episode_id, "outcome": "unfinished", "topic": meta["topic"], "reason": reason}
                # The visual event mapping survived. Keep its dated and hash-pinned art.
            else:
                # Beats the rewrite left alone keep their pictures, unless the reviewer flagged them.
                kept = pick.unchanged(old_script, visuals, script, skip={f["beat"] for f in verdict["frames"]})
                visuals = pick.pick(script, research, episode_id, keep=kept)
        else:
            before_script = json.dumps(script, sort_keys=True)
            bad = sorted({f["beat"] for f in verdict["frames"] if 1 <= f["beat"] <= len(script["beats"])})
            bad += [n for n, b in enumerate(result["beats"], 1) if b["source"] == "generated gradient" and n not in bad]
            if bad:
                if meta.get("approved_art_sha256"):
                    reason = f"pinned visual plan needs editorial review: beat(s) {', '.join(map(str, bad))}"
                    notes["revision_hold"] = reason
                    _write(folder / "review.json", notes)
                    return {"id": episode_id, "outcome": "unfinished", "topic": meta["topic"], "reason": reason}
                why = "Avoid: " + "; ".join(f"beat {f['beat']}: {f['problem']}" for f in verdict["frames"])
                visuals = pick.replace(script, research, episode_id, visuals, bad, why)
            for fix in verdict["speech"][:3]:
                n = fix["beat"]
                if 1 <= n <= len(script["beats"]):
                    beat = script["beats"][n - 1]
                    beat["text"] = _override(beat["text"], fix["word"], fix["respelling"])
            if _speech_only_block(result, verdict) and json.dumps(script, sort_keys=True) == before_script:
                shutil.rmtree(folder / BEST, ignore_errors=True)
                return _reject_speech(folder, meta, result)
        _write(folder / "script.json", script)
        _write(folder / "visuals.json", visuals)
        if blocked := _reject_visual_plan(folder, meta, visuals):
            return blocked
        spec_path = _save_spec(folder, spec_from(script, visuals, research, episode_id))

    shutil.rmtree(folder / BEST, ignore_errors=True)
    verdict = notes["rounds"][notes.get("kept_round", len(notes["rounds"])) - 1]
    write_research_md(folder, research, script, visuals, notes, episode_id)
    if os.environ.get("YTC_DRAFT_ONLY") == "1":
        draft = record_draft(spec_path, episode_id, script["title"], meta["series"], verdict["scores"], meta.get("at"))
        log.info("%s reviewed draft retained for independent handoff", episode_id)
        return {"id": episode_id, "outcome": "ready", "topic": meta["topic"], "title": script["title"],
                "scores": verdict["scores"], "draft": draft["modal_path"], "renders": len(notes["rounds"])}
    held = hold(spec_path, {"scores": verdict["scores"], "anniversary": meta.get("at")})
    if int(episode_id.removeprefix("ep")) >= 63:
        # A producing run cannot approve its own render. Any earlier approval covered older bytes.
        (folder / "release_certificate.json").unlink(missing_ok=True)
        (folder / "independent_review.json").unlink(missing_ok=True)
        log.info("%s hosted and held for independent exact-media review", episode_id)
    return {"id": episode_id, "outcome": "ready", "topic": meta["topic"], "title": script["title"],
            "scores": verdict["scores"], "media_url": held["media_url"], "renders": len(notes["rounds"])}


def write_research_md(folder: Path, research: dict, script: dict, visuals: list[dict], notes: dict, episode_id: str) -> None:
    today = datetime.now(IST).date().isoformat()
    final = notes["rounds"][notes.get("kept_round", len(notes["rounds"])) - 1]
    beats_for_claim: dict[int, list[int]] = {}
    for b, beat in enumerate(script["beats"], start=1):
        for c in beat.get("claims", []):
            beats_for_claim.setdefault(c, []).append(b)
    models = sorted({c["model"] for c in llm.calls})
    lines = [
        f"# {episode_id} research: {script['title']} ({research['series']})",
        "",
        f"Researched {today} by the cloud studio ({', '.join(models) or 'Gemini'}) from the sources below, read in "
        "full by the studio. Only claims backed by two or more independent sites were allowed into the script.",
        "",
        f"Story: {research.get('story', '')}",
        "",
        "## Sources",
        "",
        "| Key | Source | URL |",
        "|---|---|---|",
        *[f"| {s['label']} | {s['title']} ({s['site']}) | {s['url']} |" for s in research["sources"]],
        "",
        "## Claims table",
        "",
        "| # | Beats | Claim | Sources | Confidence |",
        "|---|---|---|---|---|",
        *[f"| {n} | {', '.join(map(str, beats_for_claim.get(n, []))) or '-'} | {c['claim']} | {', '.join(c['sources'])} | {c['confidence']} |"
          for n, c in enumerate(research["claims"], start=1)],
        "",
        "## Disputed or left out",
        "",
        *([f"- {d}" for d in research.get("disputed", [])] or ["- nothing"]),
        "",
        "## Images",
        "",
    ]
    for n, visual in enumerate(visuals, start=1):
        if visual.get("reuse"):
            why = "for the loop" if n == len(visuals) and script.get("loop") else "no better picture was found"
            lines.append(f"- Beat {n}: beat {visual['reuse']}'s picture again, {why}.")
        elif visual.get("source") == "card":
            card = visual["card"]
            lines.append(f"- Beat {n}: a designed {card['kind']} card, \"{card['big']}\"" + (f" / \"{card['small']}\"" if card.get("small") else ""))
        elif visual.get("_choice"):
            c = visual["_choice"]
            fit = f", judged {visual['_fit']}" if visual.get("_fit") else ""
            lines.append(f"- Beat {n}: {c['title'].removeprefix('File:')} ({c['license']}{fit}), {c.get('page')}")
        else:
            lines.append(f"- Beat {n}: searched `{visual.get('query')}` (not checked by eye)")
    lines += ["", "## Render log", ""]
    for i, r in enumerate(notes["rounds"], start=1):
        ch = r["check"]
        lines.append(
            f"- Render {i}: {ch['duration']} s, {ch['words']} words, {ch['integrated_lufs']} LUFS, "
            f"{ch['true_peak_dbfs']} dBFS true peak, warnings: {'; '.join(ch['warnings']) or 'none'}; speech differences: "
            f"{'; '.join(ch['speech_differences'] or []) or ch.get('speech_error') or 'none'}. Scores "
            + ", ".join(f"{k} {r['scores'].get(k, '-')}" for k in GATE)
            + (f". Fixes asked: {'; '.join(r['rewrite'] + [f['problem'] for f in r['frames']] + [s['word'] for s in r['speech']])}"
               if not r["passed"] else ". Passed.")
        )
    if kept := notes.get("kept_round"):
        lines.append(f"- Published render {kept}: the fixes after it scored lower.")
    lines += [
        "",
        f"## Quality gate (cloud studio, {today})",
        "",
        "| " + " | ".join(k.capitalize() for k in GATE) + " |",
        "|" + "---|" * len(GATE),
        "| " + " | ".join(str(final["scores"].get(k, "-")) for k in GATE) + " |",
        "",
        *[f"- {k.capitalize()}: {final['notes'].get(k, '')}" for k in GATE],
        "",
        f"Better than the last: {final.get('better_than_last') or script.get('better_than_last', '')}",
        "",
    ]
    (folder / "research.md").write_text("\n".join(lines), encoding="utf-8")
