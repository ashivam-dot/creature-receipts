"""The globe layer of a cinematic Atlas Short: bake the scene (NASA Earth, the dataset draped over the countries, a
column per country, camera targets per beat) and capture it frame by frame in headless Chromium (three.js)."""

from __future__ import annotations

import asyncio
import base64
import functools
import json
import math
import os
import shutil
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from ... import ff
from .. import geo
from ..draw import Scale, short_name

WEB = Path(__file__).resolve().parent / "web"
EARTH = Path(__file__).resolve().parents[4] / "assets" / "atlas" / "earth"
FPS = 30
TEX_W, TEX_H = 4096, 2048
# Altitudes above the surface, in Earth radii.
ALT_WORLD, ALT_CARD, ALT_RANK = 4.4, 5.6, 4.6
# Two countries named in one world shot further apart than this (radians from their midpoint) can't share the
# narrow 9:16 view: the camera starts on the first and pans to the second over PAN (fractions of the beat).
PAN_SPREAD = math.radians(40)
PAN = (0.35, 0.75)
# Software GL works on any Linux host; on a Mac the GPU is used unless ATLAS_SOFTWARE_GL=1.
SOFTWARE_GL = ["--use-angle=swiftshader", "--use-gl=angle", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]


def _hex(rgb: tuple) -> str:
    return "#%02x%02x%02x" % tuple(int(v) for v in rgb[:3])


def _px(ring: list) -> list[tuple[float, float]]:
    return [((lon + 180) / 360 * TEX_W, (90 - lat) / 180 * TEX_H) for lon, lat in ring]


@functools.cache
def _rings() -> dict[str, list[list]]:
    data = json.loads(geo.ASSET.read_text(encoding="utf-8"))
    out: dict[str, list[list]] = {}
    for c in data["countries"]:
        out.setdefault(c["iso3"], []).extend(c["rings"])
    return out


def _lonlat_box(iso: str) -> tuple[float, float, float, float]:
    """The lon/lat box of the ring holding the label point (France, not France plus Guiana)."""
    c = geo.world()[iso]
    rings = _rings()[iso]
    best = None
    for ring in rings:
        arr = np.asarray(ring)
        lo0, la0, lo1, la1 = arr[:, 0].min(), arr[:, 1].min(), arr[:, 0].max(), arr[:, 1].max()
        inside = lo0 <= c.lon <= lo1 and la0 <= c.lat <= la1
        area = (lo1 - lo0) * (la1 - la0)
        key = (inside, area)
        if best is None or key > best[0]:
            best = (key, (lo0, la0, lo1, la1))
    return best[1]


def data_texture(colors: dict[str, tuple], path: Path) -> Path:
    img = Image.new("RGBA", (TEX_W, TEX_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rings = _rings()
    for iso, rgb in colors.items():
        for ring in rings.get(iso, []):
            d.polygon(_px(ring), fill=tuple(int(v) for v in rgb[:3]) + (215,))
    for iso, country_rings in rings.items():
        for ring in country_rings:
            d.line(_px(ring), fill=(255, 255, 255, 110), width=2)
    img.save(path)
    return path


def highlight_texture(isos: list[str], accent: tuple, path: Path, side: int = 2048) -> list[float]:
    """The countries' fill and outline over just their padded lon/lat box, at `side` pixels on its long edge, and that
    box in texture coordinates [u0, v0, u1, v1]. A box across the antimeridian falls back to the whole world."""
    boxes = [_lonlat_box(i) for i in isos]
    lo0, la0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
    lo1, la1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
    pad = 0.3 * max(lo1 - lo0, la1 - la0) + 1.0
    lo0, la0, lo1, la1 = max(-180, lo0 - pad), max(-90, la0 - pad), min(180, lo1 + pad), min(90, la1 + pad)
    if lo1 - lo0 > 180:
        lo0, la0, lo1, la1 = -180.0, -90.0, 180.0, 90.0
    k = side / max(lo1 - lo0, la1 - la0)
    w, h = max(8, round((lo1 - lo0) * k)), max(8, round((la1 - la0) * k))

    def px(ring: list) -> list[tuple[float, float]]:
        return [((lon - lo0) * k, (la1 - lat) * k) for lon, lat in ring]

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rings = _rings()
    line = max(3, round(max(w, h) * 0.0035))
    for iso in isos:
        for ring in rings.get(iso, []):
            d.polygon(px(ring), fill=tuple(accent[:3]) + (70,))
    for iso in isos:
        for ring in rings.get(iso, []):
            d.line(px(ring) + px(ring)[:1], fill=(255, 255, 255, 255), width=line, joint="curve")
    img.save(path)
    return [(lo0 + 180) / 360, (la0 + 90) / 180, (lo1 + 180) / 360, (la1 + 90) / 180]


def _unit(lat: float, lon: float) -> np.ndarray:
    la, lo = math.radians(lat), math.radians(lon)
    return np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])


def _latlon(v: np.ndarray) -> tuple[float, float]:
    v = v / np.linalg.norm(v)
    return math.degrees(math.asin(max(-1.0, min(1.0, v[2])))), math.degrees(math.atan2(v[1], v[0]))


def _center(isos: list[str]) -> tuple[float, float, float]:
    """Mean direction of the countries' label points and the widest angle (radians) from it."""
    world = geo.world()
    pts = [_unit(world[i].lat, world[i].lon) for i in isos if i in world]
    if not pts:
        return 15.0, 10.0, 0.0
    m = np.mean(pts, axis=0)
    lat, lon = _latlon(m)
    c = _unit(lat, lon)
    spread = max(math.acos(max(-1.0, min(1.0, float(p @ c)))) for p in pts)
    return lat, lon, spread


def _clamp_lat(lat: float) -> float:
    return max(-58.0, min(62.0, lat))


def shots(ep, spans: list[tuple[float, float]], duration: float) -> list[dict]:
    """Camera targets for each beat."""
    out = []
    world = geo.world()
    last = (20.0, 15.0)
    for i, (beat, (t0, t1)) in enumerate(zip(ep.beats, spans)):
        shot = beat.shot
        kind = shot.kind
        isos = [x for x in ([shot.iso] if shot.iso else []) + list(shot.isos) if x in world]
        extra = {}
        if kind == "world":
            callouts = [x for x in shot.callouts if x in world]
            lat, lon, spread = _center(callouts) if callouts else (18.0, last[1], 0.0)
            focus, alt, isos = (_clamp_lat(lat * 0.6 + 8), lon), ALT_WORLD, callouts[:2]
            if len(isos) == 2 and spread > PAN_SPREAD:
                a, b = world[isos[0]], world[isos[1]]
                focus = (_clamp_lat(a.lat * 0.6 + 8), a.lon)
                extra = {"focus2": [round(_clamp_lat(b.lat * 0.6 + 8), 3), round(b.lon, 3)], "pan": list(PAN)}
        elif kind in ("group", "region") and len(isos) > 1 and _center(isos)[2] > PAN_SPREAD:
            # Too far apart to share a view: dive to the first, as a country shot would, and light only it.
            lo0, la0, lo1, la1 = _lonlat_box(isos[0])
            c = world[isos[0]]
            span = math.radians(max((lo1 - lo0) * math.cos(math.radians(c.lat)), la1 - la0))
            focus, alt, extra = (_clamp_lat(c.lat), c.lon), max(1.2, min(2.4, span / 0.2)), {"hi_isos": isos[:1]}
        elif kind == "country" and isos:
            lo0, la0, lo1, la1 = _lonlat_box(isos[0])
            c = world[isos[0]]
            span = math.radians(max((lo1 - lo0) * math.cos(math.radians(c.lat)), la1 - la0))
            focus, alt = (_clamp_lat(c.lat), c.lon), max(0.8, min(2.4, span / 0.2))
        elif kind in ("group", "region") and isos:
            lat, lon, spread = _center(isos)
            focus, alt = (_clamp_lat(lat), lon), max(0.9, min(3.6, spread * 2 / 0.25 + 0.4))
        elif kind == "rank" and isos:
            lat, lon, _ = _center(isos)
            focus, alt = (_clamp_lat(lat * 0.5 + 5), lon), ALT_RANK
        else:
            focus, alt, isos = (18.0, last[1] + 35), ALT_CARD, []
        last = focus
        out.append({"kind": kind, "t0": 0.0 if i == 0 else t0, "t1": duration if i == len(spans) - 1 else t1,
                    "isos": isos, "focus": [round(focus[0], 3), round(focus[1], 3)], "alt": round(alt, 3), **extra})
    return out


def ranks(vals: dict[str, float]) -> dict[str, int]:
    """Each place's position from the highest value down; tied values share the better position."""
    return {k: 1 + sum(1 for x in vals.values() if x > v) for k, v in vals.items()}


def bake(ep, ds, scale: Scale, spans: list[tuple[float, float]], duration: float, stage: Path,
         accent: tuple = (255, 209, 102), first_pins: float = 0.0) -> dict:
    """The stage folder for capture(); the opening shot's pins wait `first_pins` seconds (for the hook title)."""
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(WEB, stage)
    out = stage / "scene"
    out.mkdir()
    shutil.copy(EARTH / "day.jpg", out / "day.jpg")
    shutil.copy(EARTH / "night.jpg", out / "night.jpg")
    world = geo.world()
    vals = {k: v for k, v in ds.values.items() if k in world}
    colors = {k: scale.color(v) for k, v in vals.items()}
    data_texture(colors, out / "data.png")
    order = sorted(vals, key=lambda k: vals[k])
    # Height follows the value, so the extremes stand out; a few outliers above the 98th percentile are capped.
    lo = vals[order[0]]
    hi = float(np.percentile([vals[k] for k in order], 98))
    rank = {k: max(0.0, min(1.0, (vals[k] - lo) / max(hi - lo, 1e-9))) ** 0.8 for k in order}
    places = ranks(vals)
    countries = []
    for k in order:
        c = world[k]
        lo0, la0, lo1, la1 = _lonlat_box(k)
        size = math.sqrt(max((lo1 - lo0) * (la1 - la0), 0.01))
        countries.append({"iso": k, "lat": round(c.lat, 3), "lon": round(c.lon, 3), "h": round(rank[k], 4),
                          "c": _hex(colors[k]), "name": short_name(c.name), "value": ep.value_text(vals[k]),
                          "rank": places[k], "of": len(vals),
                          "w": round(min(0.016, max(0.0065, 0.0011 * size)), 5)})
    plan = shots(ep, spans, duration)
    if first_pins:
        plan[0]["pin_at"] = first_pins
    for i, s in enumerate(plan):
        if s["kind"] in ("country", "group") and s["isos"]:
            name = f"hi_{i}.png"
            s["hibox"] = [round(v, 6) for v in highlight_texture(s.get("hi_isos", s["isos"]), accent, out / name)]
            s["hi"] = name
    scene = {"countries": countries, "shots": plan, "grow": [0.0, 1.6], "duration": duration}
    (out / "scene.json").write_text(json.dumps(scene), encoding="utf-8")
    return scene


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


async def _capture(stage: Path, duration: float, video: Path, needed: set[int] | None = None) -> dict:
    from playwright.async_api import async_playwright

    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(stage)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    frames = math.ceil(duration * FPS)
    ffmpeg = subprocess.Popen([ff.exe(), "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate",
                               str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "14",
                               "-pix_fmt", "yuv420p", "-r", str(FPS), str(video)], stdin=subprocess.PIPE)
    errors: list[str] = []
    started = time.time()
    software = os.environ.get("ATLAS_SOFTWARE_GL", "1" if os.uname().sysname != "Darwin" else "0") == "1"
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=SOFTWARE_GL if software else ["--ignore-gpu-blocklist"])
            page = await browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            await page.goto(f"http://127.0.0.1:{server.server_port}/globe.html")
            try:
                await page.wait_for_function("window.ready === true", timeout=240000)
            except Exception as exc:
                raise RuntimeError(f"globe stage did not load: {errors[:5]}") from exc
            cdp = await page.context.new_cdp_session(page)
            last = b""
            for i in range(frames):
                # Frames under a photo are never seen; repeating the last one keeps the video's timing.
                if not last or needed is None or i in needed:
                    await page.evaluate(f"window.renderAt({i / FPS})")
                    shot = await cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 94,
                                                                     "optimizeForSpeed": True})
                    last = base64.b64decode(shot["data"])
                ffmpeg.stdin.write(last)
            await browser.close()
    finally:
        ffmpeg.stdin.close()
        ffmpeg.wait()
        server.shutdown()
    if errors:
        raise RuntimeError(f"globe stage errors: {errors[:5]}")
    drawn = frames if needed is None else len(needed & set(range(frames)))
    return {"frames": frames, "drawn": drawn, "seconds": round(time.time() - started, 1),
            "s_per_frame": round((time.time() - started) / max(drawn, 1), 3)}


def capture(stage: Path, duration: float, video: Path, needed: set[int] | None = None) -> dict:
    """The globe as an MP4 of `duration`; only frames in `needed` (all when None) are rendered."""
    return asyncio.run(_capture(stage, duration, video, needed))


def still(stage: Path, t: float, png: Path) -> Path:
    """One frame at time t, for checks and the cover."""
    async def run() -> None:
        from playwright.async_api import async_playwright
        server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(stage)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True, args=["--ignore-gpu-blocklist"])
                page = await browser.new_page(viewport={"width": 1080, "height": 1920})
                await page.goto(f"http://127.0.0.1:{server.server_port}/globe.html")
                await page.wait_for_function("window.ready === true", timeout=240000)
                await page.evaluate(f"window.renderAt({t})")
                await page.screenshot(path=str(png))
                await browser.close()
        finally:
            server.shutdown()
    asyncio.run(run())
    return png
