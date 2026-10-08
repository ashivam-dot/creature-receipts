"""Turn an Atlas episode into a finished vertical Short: narration, camera moves over the map, callouts,
captions, a soft pad and sound effects, mixed to -14 LUFS."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image

from .. import ff, sfx, tts
from ..captions import write_ass, write_srt
from ..spec import Beat, CaptionStyle, ShortSpec, Voice
from . import draw, geo, music
from .data import Dataset, fetch
from .episode import AtlasEpisode, Shot

log = logging.getLogger(__name__)

FPS = 30
FLY = 0.8  # seconds a camera move between beats takes
PUSH = 0.05  # how much each shot slowly zooms in over its beat
CALLOUT_IN = 0.25
VOICE = Voice(engine="kokoro", voice="am_fenrir", speed=1.08, lang_code="a", lead_in=0.25)
CAPTIONS = CaptionStyle(size=96, y=0.745, words_per_line=3, hook_size=124, hook_y=0.1, max_width=0.8)
FONTS = Path(__file__).resolve().parents[3] / "assets" / "fonts"
MIX_RATE = 48000


@dataclass
class Plan:
    camera: draw.Camera
    highlight: set[str]
    callouts: list[str]
    card: list[str]
    dim: float
    rank: list[str] = field(default_factory=list)


def dataset(ep: AtlasEpisode, folder: Path) -> Dataset:
    """The episode's data snapshot; fetched on first use and kept as the Short's receipt."""
    path = folder / "data.json"
    if path.exists():
        return Dataset.load(path)
    ds = fetch(ep.dataset.model_dump())
    ds.save(path)
    return ds


def _plan(shot: Shot) -> Plan:
    world = geo.world()
    if shot.kind == "country":
        cam = draw.country_camera(shot.iso, shot.pad or 1.9)
        return Plan(cam, {shot.iso}, shot.callouts or [shot.iso], [], 0.35)
    if shot.kind == "group":
        isos = [i for i in shot.isos if i in world]
        cam = draw.group_camera(isos, shot.pad or 1.3)
        return Plan(cam, set(isos), shot.callouts or isos[:3], [], 0.35)
    if shot.kind == "region":
        cam = draw.region_camera(*shot.box)
        return Plan(cam, set(shot.callouts), shot.callouts, [], 0.0)
    if shot.kind == "card":
        return Plan(draw.WORLD, set(), [], shot.lines, 0.0)
    if shot.kind == "rank":
        isos = [i for i in shot.isos if i in world]
        return Plan(draw.WORLD, set(), [], [], 0.7, isos)
    return Plan(draw.WORLD, set(shot.callouts), shot.callouts, [], 0.0)


def rank_rows(isos: list[str], ds: Dataset, ep: AtlasEpisode, scale: draw.Scale,
              names: dict[str, str]) -> tuple[str, list[tuple[str, str, float, tuple]]]:
    """The bars for a rank shot, in order, and a "Top N"/"Lowest N" title only when that's exactly what they are
    among every mapped country with data."""
    world = geo.world()
    mapped = sorted(((k, v) for k, v in ds.values.items() if k in world), key=lambda kv: kv[1], reverse=True)
    picked = [i for i in isos if i in ds.values]
    n = len(picked)
    top, bottom = [k for k, _ in mapped[:n]], [k for k, _ in mapped[-n:]]
    bottom_unique = n == len(mapped) or (n > 0 and mapped[-n-1][1] > mapped[-n][1])
    top_unique = n == len(mapped) or (n > 0 and mapped[n-1][1] > mapped[n][1])
    if set(picked) == set(bottom) and set(picked) != set(top):
        order, title = sorted(picked, key=lambda k: ds.values[k]), f"Lowest {n}" if bottom_unique else ""
    else:
        order = sorted(picked, key=lambda k: ds.values[k], reverse=True)
        title = f"Top {n}" if set(picked) == set(top) and top_unique else ""
    rows = [(names.get(k, ds.names.get(k, k)), ep.value_text(ds.values[k]), ds.values[k], scale.color(ds.values[k]))
            for k in order]
    return title, rows


def _short_spec(ep: AtlasEpisode) -> ShortSpec:
    return ShortSpec(id=ep.id, title=ep.title, hook_text=ep.hook_text, voice=VOICE, captions=CAPTIONS,
                     beats=[Beat(text=b.text, pause_after=b.pause_after) for b in ep.beats])


def _source_line(ds: Dataset) -> str:
    return f"Data: {ds.source}, {ds.year_label} · {ds.license}"


def _mix(narration: Path, total: float, cues: list[tuple[float, str]], out: Path, cache_dir: Path) -> None:
    voice, rate = sf.read(narration, dtype="float32")
    if voice.ndim > 1:
        voice = voice.mean(axis=1)
    n = int(total * MIX_RATE)
    src_t = np.arange(len(voice)) / rate
    voice48 = np.interp(np.arange(n) / MIX_RATE, src_t, voice, right=0.0).astype(np.float32)
    bed = music.pad(total) * 10 ** (-27 / 20)
    fade = np.minimum(1.0, (n - np.arange(n)) / (0.8 * MIX_RATE)).astype(np.float32)
    mix = voice48 + bed[:n] * fade
    for at, name in cues:
        clip, _ = sf.read(sfx.ensure(name, cache_dir), dtype="float32")
        gain = 10 ** ((-20 if name == "whoosh" else -24) / 20)
        a = int(at * MIX_RATE)
        b = min(a + len(clip), n)
        if a < n:
            mix[a:b] += clip[: b - a] * gain
    sf.write(out, np.clip(mix, -1, 1), MIX_RATE)


def render(ep: AtlasEpisode, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    ds = dataset(ep, folder)
    scale = draw.Scale(ep.scale.kind, at=ep.scale.at, edges=ep.scale.edges, labels=ep.scale.labels)
    colors = {iso: scale.color(v) for iso, v in ds.values.items()}
    names = {iso: draw.short_name(c.name) for iso, c in geo.world().items()}
    if len(set(ds.years.values())) > 1:
        names = {iso: f"{name} · {ds.years[iso]}" if iso in ds.years else name for iso, name in names.items()}

    import torch
    torch.set_num_threads(4)
    speech_spec = _short_spec(ep)
    narr = tts.synthesize(speech_spec, folder)
    if not 30 <= narr.duration + 0.35 <= 45:
        speed = min(1.22, max(0.95, VOICE.speed * narr.duration / 38))
        speech_spec = speech_spec.model_copy(update={"voice": VOICE.model_copy(update={"speed": speed})})
        narr = tts.synthesize(speech_spec, folder)
    total = narr.duration + 0.35
    plans = [_plan(b.shot) for b in ep.beats]
    spans = narr.beat_spans
    import json
    (folder / "timing.json").write_text(json.dumps({"duration": total, "beats": [
        {"start": a, "end": b, "text": ep.beats[i].text} for i, (a, b) in enumerate(spans)]}, indent=2))

    def beat_at(t: float) -> int:
        for i, (_, end) in enumerate(spans):
            if t < end:
                return i
        return len(spans) - 1

    cues: list[tuple[float, str]] = []
    for i in range(1, len(plans)):
        moved = plans[i].camera != plans[i - 1].camera
        if moved and not plans[i].card:
            cues.append((spans[i][0] - 0.15, "whoosh"))
        if plans[i].callouts and not plans[i].card:
            cues.append((spans[i][0] + (FLY if moved else 0.1), "pop"))
        if plans[i].rank:
            cues.append((spans[i][0] + 0.2, "pop"))

    words = narr.words
    emphasis = {i: set() for i in range(len(ep.beats))}
    ass = folder / "captions.ass"
    write_ass(words, CAPTIONS, ass, total, emphasis, FONTS, hook=(ep.hook_text, spans[0][1]))
    write_srt(words, folder / "captions.srt")
    raw = folder / "mix_raw.wav"
    _mix(narr.wav_path, total, cues, raw, folder / ".sfx")
    # Kokoro's peaks sit ~14 dB over its average, so linear loudnorm can't reach -14 LUFS under the peak ceiling
    # without the peaks first being tamed.
    tamed = folder / "mix_tamed.wav"
    ff.run("-i", raw, "-af", "acompressor=threshold=0.1:ratio=3:attack=5:release=120:makeup=2,alimiter=limit=0.7",
           tamed)
    target = "loudnorm=I=-14:TP=-1.5:LRA=11"
    m = ff.loudnorm_stats(tamed, target)
    mix = folder / "mix.wav"
    ff.run("-i", tamed, "-af", f"{target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
           f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
           "linear=true", "-ar", str(MIX_RATE), mix)
    raw.unlink()
    tamed.unlink()

    out = folder / "short.mp4"
    cmd = [ff.exe(), "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{draw.W}x{draw.H}", "-r", str(FPS), "-i", "pipe:",
           "-i", str(mix),
           "-vf", f"ass={ff.filter_path(ass)}:fontsdir={ff.filter_path(FONTS)}",
           "-threads", "4", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart", "-shortest", str(out)]
    import tempfile
    import time
    encoder_errors = tempfile.TemporaryFile()
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=encoder_errors)
    rendering_started = time.monotonic()
    source = _source_line(ds)
    swatches = [*scale.swatches(), (draw.NO_DATA, "No data")]
    last_card = None
    ranks: dict[int, tuple] = {}
    settled_layers: dict[int, Image.Image] = {}
    frames = int(total * FPS)
    try:
        for f in range(frames):
            if f and f % (FPS * 10) == 0:
                log.info("%s: rendered %s/%s frames in %.0fs", ep.id, f, frames, time.monotonic() - rendering_started)
            t = f / FPS
            i = beat_at(t)
            start, end = spans[i]
            plan, prev = plans[i], plans[i - 1] if i else plans[0]
            local = t - start
            if plan.card:
                if last_card is None:
                    under = draw.overlay(draw.map_layer(prev.camera, colors, prev.highlight, prev.dim),
                                         chip="", swatches=[], source="", callouts=[])
                    big, *small = plan.card
                    credit = f"{ds.source} · {ds.year_label} · {ds.license}"
                    small = [s for s in small if not (ds.source.lower() in s.lower() and ds.year_label in s)]
                    if len(small) < 2:
                        small.append(credit)
                    lines = [(big, 92, draw.HIGHLIGHT), ("", 30, draw.INK)] + [(s, 44, draw.INK) for s in small]
                    last_card = (under, draw.card(lines, under))
                under, full = last_card
                a = min(local / 0.35, 1.0)
                frame = full if a >= 1 else Image.blend(under, full, a)
            else:
                fly = min(FLY, max(0.15, (end - start) * 0.2))
                arrive = draw.ease(local / fly) if i and plan.camera != prev.camera else 1.0
                cam = prev.camera.mix(plan.camera, arrive) if arrive < 1 else plan.camera
                push = 1 + PUSH * min(local / max(end - start, 0.1), 1.0)
                cam = cam.zoomed(push)
                dim = plan.dim * arrive
                if arrive >= 1:
                    # Rasterize settled geography once per shot; the subtle push is an affine camera transform.
                    # Full vector drawing is retained during flights and for every new country view.
                    if i not in settled_layers:
                        settled_layers[i] = draw.map_layer(plan.camera, colors, plan.highlight, plan.dim).resize(
                            (draw.W, draw.H), Image.LANCZOS)
                    layer = draw.push_layer(settled_layers[i], push)
                else:
                    layer = draw.map_layer(cam, colors, plan.highlight if arrive > 0.6 else set(), dim)
                callouts = []
                ready = local - (fly if arrive < 1 or (i and plan.camera != prev.camera) else 0.1)
                if plan.callouts and ready > 0:
                    for iso in plan.callouts:
                        if iso in ds.values:
                            x, y = draw.screen_point(cam, iso)
                            callouts.append((x, y, names.get(iso, ds.names.get(iso, iso)), ep.value_text(ds.values[iso])))
                frame = draw.overlay(layer, chip=ep.dataset.label, swatches=swatches, source=source, callouts=callouts,
                                     callout_alpha=min(ready / CALLOUT_IN, 1.0) if callouts else 0.0)
                if plan.rank:
                    if i not in ranks:
                        ranks[i] = rank_rows(plan.rank, ds, ep, scale, names)
                    frame = draw.rank_panel(frame, *ranks[i], local)
            proc.stdin.write(frame.tobytes())
    except Exception:
        proc.kill()
        proc.wait()
        encoder_errors.close()
        raise
    proc.stdin.close()
    try:
        result = proc.wait(timeout=180)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        encoder_errors.close()
        raise RuntimeError("ffmpeg did not finish within 180 seconds after rendering")
    encoder_errors.seek(0)
    err = encoder_errors.read().decode(errors="replace")
    encoder_errors.close()
    if result != 0:
        raise RuntimeError(f"ffmpeg failed: {err[-2000:]}")
    log.info("%s: %.1f s rendered to %s", ep.id, total, out)
    return out
