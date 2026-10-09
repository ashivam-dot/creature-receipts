"""Evidence-bound acceptance checks for Atlas scripts and encoded media."""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .. import ff, llm
from . import writer
from .data import Dataset
from .episode import AtlasEpisode
from .receipt import digest, verify

VERSION = 1
SPEECH_POLICY = "material-hard-entity-polarity-strict-minor-spelling-warning"


def minor_speech_difference(finding: str, ds: Dataset) -> bool:
    """Fuzzy spelling tolerance must never excuse a direction reversal or a changed country name."""
    from .. import check
    match = check._FINDING.match(finding)
    if not match:
        return False
    wrote, heard = match[2], match[4]
    polarity = r"\b(?:not|no|never|above|below|over|under|more|less|positive|negative|highest|lowest|higher|lower|most|least|increase[ds]?|increasing|decrease[ds]?|decreasing|grow(?:s|ing|th)?|grew|grown|shrink(?:s|ing)?|shrunk|rises?|rising|rose|fall(?:s|ing|en)?|fell)\b"
    if re.search(polarity, wrote + " " + heard, re.I):
        return False
    from . import geo
    from .draw import short_name
    aliases = {n for name in [*ds.names.values(), *(c.name for c in geo.world().values())] if isinstance(name, str)
               for n in (name, short_name(name)) if len(n) >= 3}
    aliases.update({"USA", "UK", "UAE"})
    if any(re.search(r"\b" + re.escape(alias) + r"\b", wrote + " " + heard, re.I) for alias in aliases):
        return False
    return check._asr_noise(finding)


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def evidence(ep: AtlasEpisode, ds: Dataset) -> dict:
    vals = writer.drawable(ds)
    if not vals or any(not math.isfinite(v) for v in vals.values()):
        raise ValueError("empty or non-finite mapped dataset")
    if any(k not in ds.years for k in vals):
        raise ValueError("a mapped value has no reporting year")
    rows = {k: {"name": ds.names.get(k, k), "value": v, "display": ep.value_text(v),
                "year": ds.years[k], "unit": ds.unit, "rank": 1 + sum(x > v for x in vals.values())} for k, v in vals.items()}
    return {"version": VERSION, "indicator": ep.dataset.indicator or ep.dataset.slug,
            "definition": ds.definition or writer.definition(ep.dataset.model_dump()), "source": ds.url,
            "source_response_sha256": ds.source_response_sha256, "source_organization": ds.source_organization,
            "year_label": ds.year_label, "universe": "mapped countries and territories with data",
            "count": len(vals), "threshold": ep.scale.at if ep.scale.kind == "threshold" else None,
            "at_or_above": sum(v >= ep.scale.at for v in vals.values()) if ep.scale.kind == "threshold" else None,
            "entities": rows}


def entity_value_errors(text: str, ep: AtlasEpisode, ds: Dataset) -> list[str]:
    """Check explicit name→value clauses before any probabilistic review.

    Shared-subject or implicit clauses remain the semantic reviewer's responsibility.
    Denominators, reporting years and explicitly labelled ranks are not entity values.
    """
    from .draw import short_name
    from . import geo
    world = geo.world()
    aliases = {}
    for iso, name in ds.names.items():
        alternatives = {name, short_name(name)}
        if iso in world:
            alternatives.update({world[iso].name, short_name(world[iso].name)})
        for alias in alternatives:
            if len(alias) >= 3:
                aliases[alias] = iso
    aliases.update({"United States": "USA", "USA": "USA", "UAE": "ARE",
                    "United Arab Emirates": "ARE", "UK": "GBR"})
    if not aliases:
        return []
    pattern = re.compile(r"\b(" + "|".join(re.escape(n) for n in sorted(aliases, key=len, reverse=True)) + r")\b", re.I)
    canonical = {k.lower(): v for k, v in aliases.items()}
    matches = list(pattern.finditer(text))
    errors = []
    for i, match in enumerate(matches):
        iso = canonical[match.group().lower()]
        if iso not in ds.values:
            continue
        whole = text[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        # A sentence boundary ends the named subject's scope.
        clause = re.split(r"[.!?](?:\s|$)", whole)[0]
        following = canonical[matches[i + 1].group().lower()] if i + 1 < len(matches) and clause == whole else None
        for number in writer._NUMBER.finditer(clause):
            subject = iso
            # "... to 3,947 in the USA": a number just before "in <the next country>" is that country's.
            if following and re.fullmatch(r"\s*(?:[^\W\d]+\s+){0,3}?(?:in|for)(?: the)?\s*", clause[number.end():], re.I):
                if following not in ds.values:
                    continue
                subject = following
            # Digits inside a measure's name (PM2.5, CO2) are not the country's value.
            if number.start() and clause[number.start() - 1].isalpha():
                continue
            context = clause[:number.start()].lower()
            token = number.group().replace(",", "").rstrip(".")
            if re.search(r"(?:per|every|each|in|year|rank|#|top)\s*$", context):
                continue
            # Counts and scale limits ("highest of all 146", "146 countries", "out of 10") aren't values either.
            if re.search(r"(?:of all|out of|among(?: the)?)\s*$", context) or re.match(
                    r"\s*(?:countries|places|nations|territories)\b", clause[number.end():], re.I):
                continue
            # "377 times" compares two countries; ratio_errors checks it.
            if RATIO.match(clause[number.end():]):
                continue
            displayed = writer._NUMBER.search(ep.value_text(ds.values[subject]))
            # Unit denominators such as "per 100" are not this country's measured value.
            expected = writer._forms(displayed.group()) if displayed else set()
            if token not in expected:
                name = match.group() if subject == iso else matches[i + 1].group()
                errors.append(f"{name} value {token} does not match {ep.value_text(ds.values[subject])}")
            if subject == iso:
                break
    return errors


RATIO = re.compile(r"\s*(?:times\b|x\b|×)", re.I)


def ratio_errors(text: str, ep: AtlasEpisode, ds: Dataset, context: list[str] = ()) -> list[str]:
    """Each "N times" must be the ratio of two countries' values as displayed: the two its sentence names, else the
    ones its shot shows (`context`; a 3-word hook can't name both). The writer rounds as writer.ratio_text does,
    so 5% slack covers rounding only."""
    from .draw import short_name
    from . import geo
    world = geo.world()
    aliases = {}
    for iso, name in ds.names.items():
        for alias in {name, short_name(name), *((world[iso].name, short_name(world[iso].name)) if iso in world else ())}:
            if len(alias) >= 3:
                aliases[alias.lower()] = iso
    aliases.update({"united states": "USA", "usa": "USA", "uk": "GBR", "uae": "ARE"})
    pattern = re.compile(r"\b(" + "|".join(re.escape(n) for n in sorted(aliases, key=len, reverse=True)) + r")\b", re.I)
    errors = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        isos = list(dict.fromkeys(aliases[m.group().lower()] for m in pattern.finditer(sentence)))
        isos = [i for i in isos if i in ds.values]
        if len(isos) < 2:
            isos += [i for i in context if i in ds.values and i not in isos]
        for m in writer._NUMBER.finditer(sentence):
            if not RATIO.match(sentence[m.end():]):
                continue
            said = float(m.group().replace(",", "").rstrip("."))
            if len(isos) < 2:
                errors.append(f"'{m.group()} times' needs both countries it compares named in the same sentence")
                continue
            shown = []
            for iso in isos[:2]:
                d = writer._NUMBER.search(ep.value_text(ds.values[iso]))
                shown.append(float(d.group().replace(",", "")) if d else 0.0)
            true = sorted(abs(ds.values[i]) for i in isos[:2])
            fits = [r for r in ((max(shown) / min(shown)) if min(shown) > 0 else None,
                                (true[1] / true[0]) if true[0] > 0 else None) if r]
            if not fits or all(abs(said - r) > 0.05 * r + 0.05 for r in fits):
                errors.append(f"'{m.group()} times' is not the ratio of {isos[0]} and {isos[1]} "
                              f"({ep.value_text(ds.values[isos[0]])} vs {ep.value_text(ds.values[isos[1]])})")
    return errors


SCHEMA = {"type": "object", "properties": {
    "errors": {"type": "array", "items": {"type": "object", "properties": {
        "surface": {"type": "string"}, "claim": {"type": "string"}, "reason": {"type": "string"},
        "severity": {"type": "string", "enum": ["factual", "style", "info"]}},
        "required": ["surface", "claim", "reason", "severity"]}},
    "claims": {"type": "array", "items": {"type": "object", "properties": {
        "surface": {"type": "string"}, "text": {"type": "string"},
        "isos": {"type": "array", "items": {"type": "string"}},
        "support": {"type": "string"}}, "required": ["surface", "text", "isos", "support"]}}},
    "required": ["errors", "claims"]}


def review(ep: AtlasEpisode, ds: Dataset, folder: Path) -> dict:
    """Review every textual surface against exact entity/year/metric evidence; keep the verdict."""
    facts = evidence(ep, ds)
    surfaces = {"title": ep.title, "hook": ep.hook_text, "description": ep.description,
                **{f"beat_{i}": b.text for i, b in enumerate(ep.beats)},
                **{f"card_{i}": b.shot.lines for i, b in enumerate(ep.beats) if b.shot.kind == "card"}}
    deterministic = []
    for surface, text in surfaces.items():
        value = " ".join(text) if isinstance(text, list) else text
        deterministic.extend(f"{surface}: {error}" for error in entity_value_errors(value, ep, ds))
        shot = ep.beats[int(surface[5:])].shot if surface.startswith("beat_") else ep.beats[0].shot
        context = list(dict.fromkeys(([shot.iso] if shot.iso else []) + shot.isos + shot.callouts))
        deterministic.extend(f"{surface}: {error}" for error in ratio_errors(value, ep, ds, context))
    if deterministic:
        raise ValueError("entity binding: " + "; ".join(deterministic))
    shots = {f"beat_{i}": b.shot.model_dump() for i, b in enumerate(ep.beats)}
    prompt = f"""Audit every factual statement below against the supplied evidence, not your memory.
Only factual contradictions/unsupported claims have severity factual. Correct claims belong in surface_checks;
never list a correct claim as a factual error. Style preferences and informational notes are severity style/info.
Return errors for swapped countries, unsupported numbers, reversed growth/decline, wrong units or denominators,
unsourced causes, false superlatives, misleading metric names, and a single year claimed for mixed-year values.
World Bank entities include territories: don't call them all sovereign countries. Most countries is not most people.
Do not infer never-used from current internet non-use; broadband subscriptions do not measure speed;
basic water is not necessarily safe; labour force includes unemployed; age dependency is not workers/retirees;
GDP is not wages; renewable final energy is not renewable electricity. 2.1 fertility is an approximate benchmark,
not proof of immediate population decline. Definitions may explain a measurement, not invent causal history.
For every material claim return its surface, text, entity ISOs (empty for aggregate/definition), and exact support.
Also return surface_checks for EVERY supplied surface, including cards, description, and repeated units/years:
supported (boolean), reason (source-based), and isos (empty for definitions/counts).
A stylistic headline may simplify wording only if it does not change the metric. Do not reject rounding that
matches display values. A positive-growth country is a valid contrast in a shrinking-populations video if
explicitly described as growing; do not reject the presence of a contrast example alone. Do not reject ordinary color/loop questions. Verify ranks among the stated universe.
EVIDENCE: {json.dumps(facts, ensure_ascii=False)}
Each country shot must show the country described in its narration; group/rank shots must include the
countries being compared. World shots show the whole mapped universe, so existential value comparisons
need not name a specific country. Reject a wrong country shot or a bar list that contradicts the narration.
VISUAL PLANS: {json.dumps(shots)}
SURFACES: {json.dumps(surfaces, ensure_ascii=False)}"""
    schema = json.loads(json.dumps(SCHEMA))
    schema["properties"]["claims"]["items"]["properties"]["surface"]["enum"] = list(surfaces)
    schema["properties"]["surface_checks"] = {"type": "object", "properties": {
        key: {"type": "object", "properties": {"supported": {"type": "boolean"},
               "reason": {"type": "string"}, "isos": {"type": "array", "items": {"type": "string"}}},
              "required": ["supported", "reason", "isos"]} for key in surfaces}, "required": list(surfaces)}
    schema["required"].append("surface_checks")
    result = llm.generate(prompt, schema=schema, temperature=0.0,
                          models=(*llm.FLASH_LITE, *llm.BACKUP_STRONG, *llm.FLASH),
                          purpose=f"atlas semantic review {ep.id}")
    save(folder / "semantic-review.json", result)
    result["warnings"] = [e for e in result["errors"] if e["severity"] != "factual"]
    result["errors"] = [e for e in result["errors"] if e["severity"] == "factual"]
    claims = result.get("claims", [])
    for surface, verdict in result["surface_checks"].items():
        if not verdict["supported"]:
            result["errors"].append({"surface": surface, "claim": str(surfaces[surface]), "reason": verdict["reason"], "severity": "factual"})
        claims.append({"surface": surface, "text": surfaces[surface], "isos": verdict["isos"],
                       "support": verdict["reason"], "method": "complete-surface-check"})
    for claim in claims:
        if claim["surface"] not in surfaces or any(k not in facts["entities"] for k in claim["isos"]):
            raise ValueError(f"review references an unknown surface or entity: {claim['surface']} {claim['isos']}")
        claim["evidence"] = {k: facts["entities"][k] for k in claim["isos"]}
    covered = {claim["surface"] for claim in claims}
    missing = [surface for surface, text in surfaces.items()
               if re.search(r"\d", " ".join(text) if isinstance(text, list) else text) and surface not in covered]
    if missing:
        raise ValueError("review omitted numeric surfaces: " + ", ".join(missing))
    record = {"version": VERSION, "evidence": facts, "review": result,
              "script_sha256": digest(folder / "atlas.yaml"), "data_sha256": digest(folder / "data.json"),
              "reviewer_model": llm.calls[-1]["model"] if llm.calls else "unreported"}
    save(folder / "claims.json", record)
    if result["errors"]:
        raise ValueError("semantic review: " + "; ".join(f"{e['surface']}: {e['reason']}" for e in result["errors"])[:1800])
    return record


def media(ep: AtlasEpisode, folder: Path, video: Path) -> dict:
    """Decode the exact MP4 and independently inspect its encoded audio."""
    from .. import check
    duration = ff.duration(video)
    run = subprocess.run([ff.exe(), "-hide_banner", "-nostats", "-xerror", "-i", str(video),
                          "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True, timeout=180)
    if run.returncode:
        raise ValueError("final MP4 failed full decode")
    if not 25 <= duration <= 55:
        raise ValueError(f"final duration {duration:.1f}s outside 25–55s acceptance range")
    if not re.search(r"Video:.*1080x1920", run.stderr) or "Audio:" not in run.stderr:
        raise ValueError("final MP4 must contain 1080x1920 video and audio")
    summary = run.stderr[run.stderr.rfind("Summary:"):]
    loud, peak = check._LUFS.search(summary), check._PEAK.search(summary)
    if not loud or not peak:
        raise ValueError("final loudness measurement unavailable")
    integrated, true_peak = float(loud.group(1)), float(peak.group(1))
    if not -18 <= integrated <= -11 or true_peak > -0.5:
        raise ValueError(f"final audio outside limits: {integrated} LUFS, {true_peak} dBTP")
    speech = check.speech(video, [{"text": b.text} for b in ep.beats])
    if speech.get("error"):
        raise ValueError("final speech verification unavailable: " + speech["error"][:300])
    # Only small spelling/function-word recognizer noise can be retained as a visible warning.
    save(folder / "media-review.json", {"duration": duration, "integrated_lufs": integrated,
                                        "true_peak_dbfs": true_peak, "speech": speech})
    differences = speech.get("differences", [])
    ds = Dataset.load(folder / "data.json")
    material = [d for d in differences if not minor_speech_difference(d, ds)]
    if material or len(differences) > 4:
        raise ValueError("encoded speech material mismatch: " + "; ".join(material or differences)[:500])
    warnings = list(differences)
    if not 30 <= duration <= 45:
        warnings.append(f"duration {duration:.1f}s outside editorial 30–45s target")
    # Keep the actual encoded frames as a compact visual audit artifact after bulky renders are removed.
    from PIL import Image
    timing = json.loads((folder / "timing.json").read_text())
    frames = []
    frame_dir = folder / "review-frames"
    frame_dir.mkdir(exist_ok=True)
    for i, beat in enumerate(timing["beats"]):
        path = frame_dir / f"{i:02d}.jpg"
        at = (beat["start"] + beat["end"]) / 2
        ff.run("-ss", str(at), "-i", video, "-frames:v", "1", "-vf", "scale=270:480", path)
        with Image.open(path) as im:
            frames.append(im.copy())
    contact = Image.new("RGB", (270 * 4, 480 * math.ceil(len(frames) / 4)))
    for i, frame in enumerate(frames):
        contact.paste(frame, ((i % 4) * 270, (i // 4) * 480))
    contact.save(folder / "contact.jpg", quality=85)
    import shutil
    shutil.rmtree(frame_dir)
    result = {"version": VERSION, "passed": True, "checked_at": datetime.now(timezone.utc).isoformat(),
              "quality_module_sha256": digest(Path(__file__)), "media_sha256": digest(video), "script_sha256": digest(folder / "atlas.yaml"),
              "data_sha256": digest(folder / "data.json"), "claims_sha256": digest(folder / "claims.json"),
              "contact_sha256": digest(folder / "contact.jpg"), "duration": round(duration, 3), "integrated_lufs": integrated, "true_peak_dbfs": true_peak,
              "speech": speech, "warnings": warnings, "speech_policy": SPEECH_POLICY}
    save(folder / "qa.json", result)
    return result
