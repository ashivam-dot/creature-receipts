"""The cinematic Atlas Short. The globe flies to every country the narration names, then real photos of that country
take over with a slow depth-parallax camera; a comparison splits the screen between its countries, a ranking rises as
a panel of flags and bars, and the last beat lands on an end card. Kokoro narration, an original score and
synthesized effects are mixed to -14 LUFS."""

from __future__ import annotations

import json
import logging
import math
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ... import depth, ff, sfx, tts
from ...captions import write_srt
from ...spec import Beat, CaptionStyle, ShortSpec, Voice
from .. import geo
from ..draw import Scale, short_name
from ..episode import AtlasEpisode
from ..render import dataset, rank_rows
from . import globe, places, score

log = logging.getLogger(__name__)

W, H, FPS = 1080, 1920, 30
FONTS = Path(__file__).resolve().parents[4] / "assets" / "fonts"
ACCENT = (255, 209, 102)
VOICE = Voice(engine="kokoro", voice="am_fenrir", speed=1.1, lang_code="a", lead_in=0.25)
TARGET = (30.0, 44.0)  # seconds of narration
TAIL = 0.6  # the end card holds this long after the last word
CAPTION_Y = 0.715
CAPTION_W = 0.78  # clear of the Shorts player's buttons down the right edge
# A country beat dives on the globe first; its photos take over once the pin has been on screen a moment.
DIVE = 2.3
MIN_PHOTO = 1.6
CROSS = 9  # frames
HOOK_HOLD = 2.2  # seconds the hook title stays before it fades for the opening pins
DISCLOSURE = "Photos: Wikimedia Commons · Narration: AI voice"
MOTIONS = [
    {"z": (1.00, 1.09), "dz": (0.00, 0.07), "pan": (0, 0, 0, -20), "par": (0, 0)},  # push in
    {"z": (1.05, 1.07), "dz": (0.02, 0.03), "pan": (-45, 45, 0, 0), "par": (34, 0)},  # drift right
    {"z": (1.10, 1.02), "dz": (0.07, 0.01), "pan": (0, 0, 10, -10), "par": (0, 0)},  # pull back
    {"z": (1.05, 1.08), "dz": (0.02, 0.04), "pan": (40, -40, 0, 0), "par": (-34, 0)},  # drift left
    {"z": (1.04, 1.08), "dz": (0.02, 0.05), "pan": (0, 0, 40, -40), "par": (0, 26)},  # rise
]
MARGIN = 1.16


def _font(name: str, size: int, weight: str | None = None) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONTS / name), size)
    if weight:
        font.set_variation_by_name(weight)
    return font


def _anton(size: int) -> ImageFont.FreeTypeFont:
    return _font("Anton-Regular.ttf", size)


def _sans(size: int, weight: str = "ExtraBold") -> ImageFont.FreeTypeFont:
    return _font("Montserrat-Variable.ttf", size, weight)


def _ease(u: float) -> float:
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def _rgba(img: Image.Image) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(img.convert("RGBA"), dtype=np.float32)
    return a[..., :3], a[..., 3:4] / 255.0


def _blit(frame: np.ndarray, layer: tuple[np.ndarray, np.ndarray], x: int, y: int, alpha: float = 1.0) -> None:
    rgb, a = layer
    h, w = a.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0 or alpha <= 0:
        return
    sub = frame[y0:y1, x0:x1].astype(np.float32)
    la = a[y0 - y:y1 - y, x0 - x:x1 - x] * alpha
    frame[y0:y1, x0:x1] = (sub * (1 - la) + rgb[y0 - y:y1 - y, x0 - x:x1 - x] * la).astype(np.uint8)


def _wrap(text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and font.getlength(trial) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + ([cur] if cur else [])


def _lines_layer(lines: list[tuple[str, ImageFont.FreeTypeFont, tuple]], stroke: int = 6, gap: int = 12,
                 align: str = "center") -> Image.Image:
    boxes = [f.getbbox(t, stroke_width=stroke) for t, f, _ in lines]
    w = max(b[2] - b[0] for b in boxes) + 8
    h = sum(b[3] - b[1] for b in boxes) + gap * (len(lines) - 1) + 8
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = 4
    for (t, f, color), b in zip(lines, boxes):
        x = 4 + ((w - 8 - (b[2] - b[0])) // 2 if align == "center" else 0)
        d.text((x - b[0], y - b[1]), t, font=f, fill=color, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        y += b[3] - b[1] + gap
    return img


def _shadowed(img: Image.Image, radius: int = 18, strength: int = 150) -> Image.Image:
    pad = radius * 2
    out = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    alpha = Image.new("L", out.size, 0)
    alpha.paste(img.getchannel("A").point(lambda v: min(255, v * strength // 255)), (pad, pad + 8))
    out.putalpha(alpha.filter(ImageFilter.GaussianBlur(radius)))
    out.alpha_composite(img, (pad, pad))
    return out


def _flag(path: str | None, height: int) -> Image.Image | None:
    if not path or not Path(path).exists():
        return None
    img = Image.open(path).convert("RGBA")
    img = img.resize((max(1, round(img.width * height / img.height)), height), Image.LANCZOS)
    framed = Image.new("RGBA", (img.width + 6, img.height + 6), (255, 255, 255, 235))
    framed.alpha_composite(img, (3, 3))
    return framed


# -- photos ---------------------------------------------------------------------------------------------------------

class Plate:
    """One photo prepared for camera moves: RGB and nearness at plate size, full bleed when the photo has the pixels
    for it, otherwise framed over a blurred copy of itself."""

    def __init__(self, path: str, box: tuple[int, int] = (W, H)):
        img = Image.open(path).convert("RGB")
        cache = Path(path).with_suffix(".depth.npy")
        if cache.exists():
            near = np.load(cache)
        else:
            small = img.copy()
            small.thumbnail((1024, 1024))
            near = cv2.resize(depth.nearness(small), img.size, interpolation=cv2.INTER_LINEAR)
            np.save(cache, near)
        bw, bh = box
        pw, ph = round(bw * MARGIN), round(bh * MARGIN)
        iw, ih = img.size
        ratio = pw / ph
        if (ih >= 0.58 * ph and iw / ih <= 2.0) or iw / ih <= ratio * 1.25 or bh < H:
            cw, ch = (ih * ratio, ih) if iw / ih > ratio else (iw, iw / ratio)
            x0, y0 = (iw - cw) / 2, (ih - ch) * 0.45
            box_ = (round(x0), round(y0), round(x0 + cw), round(y0 + ch))
            rgb = img.crop(box_).resize((pw, ph), Image.LANCZOS)
            d = cv2.resize(near[box_[1]:box_[3], box_[0]:box_[2]], (pw, ph), interpolation=cv2.INTER_LINEAR)
        else:
            scale = max(pw / iw, ph / ih)
            bg = img.resize((round(iw * scale), round(ih * scale)), Image.LANCZOS)
            left, top = (bg.width - pw) // 2, (bg.height - ph) // 2
            bg = bg.crop((left, top, left + pw, top + ph)).filter(ImageFilter.GaussianBlur(38))
            bg = Image.eval(bg, lambda v: int(v * 0.45))
            fw = round(pw * 0.94)
            fh = round(ih * fw / iw)
            fg = img.resize((fw, fh), Image.LANCZOS)
            ox, oy = (pw - fw) // 2, round(ph * 0.45 - fh / 2)
            shadow = Image.new("L", (pw, ph), 0)
            ImageDraw.Draw(shadow).rectangle((ox + 6, oy + 14, ox + fw + 6, oy + fh + 14), fill=170)
            bg.paste(Image.new("RGB", (pw, ph), (0, 0, 0)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(22)))
            bg.paste(fg, (ox, oy))
            rgb = bg
            d = np.zeros((ph, pw), np.float32)
            d[oy:oy + fh, ox:ox + fw] = 0.35 + 0.65 * cv2.resize(near, (fw, fh), interpolation=cv2.INTER_LINEAR)
        self.rgb = np.asarray(rgb, dtype=np.uint8)
        self.depth = cv2.GaussianBlur(d.astype(np.float32), (0, 0), 3) - 0.5
        self.pw, self.ph, self.bw, self.bh = pw, ph, bw, bh


class Camera:
    def __init__(self, box: tuple[int, int] = (W, H)):
        bw, bh = box
        gx, gy = np.meshgrid(np.arange(bw, dtype=np.float32) - bw / 2, np.arange(bh, dtype=np.float32) - bh / 2)
        self.gx, self.gy = gx, gy

    def shoot(self, plate: Plate, u: float, motion: dict, punch: float = 0.0) -> np.ndarray:
        e = _ease(u)
        z = (motion["z"][0] + (motion["z"][1] - motion["z"][0]) * e) * (1 + punch)
        dz = motion["dz"][0] + (motion["dz"][1] - motion["dz"][0]) * e
        px0, px1, py0, py1 = motion["pan"]
        k = plate.bh / H
        cx = plate.pw / 2 + (px0 + (px1 - px0) * e) * k
        cy = plate.ph / 2 + (py0 + (py1 - py0) * e) * k
        parx, pary = motion["par"][0] * (e - 0.5) * k, motion["par"][1] * (e - 0.5) * k
        d = cv2.remap(plate.depth, cx + self.gx / z, cy + self.gy / z, cv2.INTER_LINEAR,
                      borderMode=cv2.BORDER_REPLICATE)
        zz = 1 + dz * d * 2
        mx = cx + self.gx / (z * zz) - parx * d * 2
        my = cy + self.gy / (z * zz) - pary * d * 2
        return cv2.remap(plate.rgb, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def _photo_grade(frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
    f = frame.astype(np.float32)
    gray = f.mean(axis=2, keepdims=True)
    f = gray + (f - gray) * 0.96
    f = (f - 128) * 1.05 + 128
    return np.clip(f * mask, 0, 255).astype(np.uint8)


def _masks() -> tuple[np.ndarray, np.ndarray]:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.7)) ** 2)
    vignette = np.clip(1.08 - 0.55 * r ** 2.2, 0.35, 1.0)
    # Darken behind the captions and the top cards so white text always reads.
    band = 1 - 0.34 * np.exp(-((yy - H * CAPTION_Y) / (H * 0.08)) ** 2) - 0.3 * np.exp(-((yy - H * 0.14) / (H * 0.1)) ** 2)
    photo = (vignette * band)[..., None].astype(np.float32)
    caption = (1 - 0.22 * np.exp(-((yy - H * CAPTION_Y) / (H * 0.07)) ** 2))[..., None].astype(np.float32)
    return photo, caption


# -- overlays -------------------------------------------------------------------------------------------------------

class Captions:
    """Karaoke captions: short phrases, the word being spoken in the accent colour, a small pop as each phrase lands."""

    def __init__(self, words: list[dict]):
        self.font = _anton(96)
        self.groups = []
        cur: list[dict] = []
        chunks = []
        for w in words:
            cur.append(w)
            if len(cur) >= 3 or len(" ".join(x["text"] for x in cur)) >= 15 or w["text"][-1:] in ".,;:!?—":
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        for chunk in chunks:
            texts = [w["text"].upper() for w in chunk]
            self.groups.append({"start": chunk[0]["start"], "end": chunk[-1]["end"], "words": chunk,
                                "variants": [self._render(texts, k) for k in range(len(chunk))]})

    def _render(self, texts: list[str], active: int) -> tuple[np.ndarray, np.ndarray]:
        space = self.font.getlength(" ")
        widths = [self.font.getbbox(t, stroke_width=9)[2] for t in texts]
        img = Image.new("RGBA", (int(sum(widths) + space * (len(texts) - 1)) + 24, 150), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        x = 12
        for i, (t, w) in enumerate(zip(texts, widths)):
            color = ACCENT + (255,) if i == active else (255, 255, 255, 255)
            d.text((x, 10), t, font=self.font, fill=color, stroke_width=9, stroke_fill=(0, 0, 0, 255))
            x += w + space
        limit = round(W * CAPTION_W)
        if img.width > limit:
            img = img.resize((limit, round(img.height * limit / img.width)), Image.LANCZOS)
        return _rgba(img)

    def draw(self, frame: np.ndarray, t: float) -> None:
        for g in self.groups:
            if g["start"] - 0.05 <= t < g["end"] + 0.12:
                k = max([i for i, w in enumerate(g["words"]) if w["start"] <= t + 0.03] or [0])
                rgb, a = g["variants"][k]
                h, w = a.shape[:2]
                pop = min(1.0, (t - g["start"] + 0.05) / 0.09)
                if pop < 1:
                    s = 0.9 + 0.1 * pop
                    size = (max(1, round(w * s)), max(1, round(h * s)))
                    rgb, a = cv2.resize(rgb, size), cv2.resize(a, size)[..., None]
                    h, w = a.shape[:2]
                _blit(frame, (rgb, a), (W - w) // 2, round(H * CAPTION_Y - h / 2))
                return


def _hook_layer(text: str, label: str) -> tuple[np.ndarray, np.ndarray]:
    big = _anton(124)
    lines = _wrap(text.upper(), big, W - 140)
    while len(lines) > 2 and big.size > 80:
        big = _anton(big.size - 8)
        lines = _wrap(text.upper(), big, W - 140)
    rows = [(line, big, (255, 255, 255, 255)) for line in lines]
    if label:
        rows.append((label.upper(), _sans(40, "Black"), ACCENT + (255,)))
    return _rgba(_shadowed(_lines_layer(rows, stroke=7, gap=14)))


def _chip_layer(label: str, source: str) -> tuple[np.ndarray, np.ndarray]:
    title, sub = _sans(34, "Black"), _sans(26, "SemiBold")
    tw = max(title.getlength(label.upper()), sub.getlength(source))
    img = Image.new("RGBA", (int(tw) + 70, 104), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=18, fill=(8, 12, 22, 170))
    d.rounded_rectangle((16, 18, 23, img.height - 18), radius=3, fill=ACCENT + (255,))
    d.text((40, 16), label.upper(), font=title, fill=(255, 255, 255, 255))
    d.text((40, 60), source, font=sub, fill=(255, 255, 255, 200))
    return _rgba(img)


def _country_layer(name: str, value: str, unit: str, flag: str | None) -> tuple[np.ndarray, np.ndarray]:
    """The country's flag, its name, and its value in the accent colour with the unit beside it."""
    big = _anton(112)
    while big.getlength(name.upper()) > W - 330 and big.size > 64:
        big = _anton(big.size - 6)
    num, small = _sans(84, "Black"), _sans(38, "Bold")
    fl = _flag(flag, 96)
    name_w = big.getbbox(name.upper(), stroke_width=6)[2]
    unit_lines = _wrap(unit, small, 420)[:2]
    value_w = num.getbbox(value, stroke_width=5)[2] + 22 + max([int(small.getlength(u)) for u in unit_lines] or [0])
    left = (fl.width + 28) if fl else 0
    w = left + max(name_w, value_w) + 20
    img = Image.new("RGBA", (w, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if fl:
        img.alpha_composite(fl, (0, 22))
    nb = big.getbbox(name.upper(), stroke_width=6)
    d.text((left - nb[0], 10 - nb[1]), name.upper(), font=big, fill=(255, 255, 255, 255), stroke_width=6,
           stroke_fill=(0, 0, 0, 255))
    y = 10 + nb[3] - nb[1] + 14
    vb = num.getbbox(value, stroke_width=5)
    d.text((left - vb[0], y - vb[1]), value, font=num, fill=ACCENT + (255,), stroke_width=5, stroke_fill=(0, 0, 0, 255))
    ux, uy = left + vb[2] - vb[0] + 22, y + (vb[3] - vb[1]) // 2 - 24 * len(unit_lines)
    for line in unit_lines:
        d.text((ux, uy), line, font=small, fill=(255, 255, 255, 240), stroke_width=4, stroke_fill=(0, 0, 0, 255))
        uy += 46
    return _rgba(_shadowed(img.crop(img.getbbox() or (0, 0, w, 260))))


def _place_layer(place: str, credit: str) -> tuple[np.ndarray, np.ndarray]:
    rows = []
    if place:
        rows.append((place.upper(), _sans(32, "Black"), ACCENT + (255,)))
    font = _sans(22, "Medium")
    while font.getlength(credit) > W - 120 and len(credit) > 20:
        credit = credit[:-4] + "…"
    rows.append((credit, font, (255, 255, 255, 180)))
    return _rgba(_lines_layer(rows, stroke=3, gap=10, align="left"))


class RankPanel:
    """A ranked list rising from the bottom: rank, flag, name, value, and a bar that grows to the value."""

    def __init__(self, title: str, label: str, rows: list[tuple[str, str, float, str | None]]):
        self.rows = rows
        self.width, self.row_h = W - 120, 112
        self.head = _rgba(_lines_layer([(title, _sans(34, "Black"), ACCENT + (255,))], stroke=4, align="left")) \
            if title else None
        top = max(abs(v) for _, _, v, _ in rows) or 1.0
        self.fracs = [max(0.04, abs(v) / top) for _, _, v, _ in rows]
        self.static = []
        for i, (name, value, _, flag) in enumerate(rows):
            img = Image.new("RGBA", (self.width, self.row_h), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.rounded_rectangle((0, 0, self.width - 1, self.row_h - 10), radius=16, fill=(8, 12, 22, 185))
            d.text((22, 14), str(i + 1), font=_anton(60), fill=(255, 255, 255, 150))
            fl = _flag(flag, 46)
            x = 82
            if fl:
                img.alpha_composite(fl, (x, 16))
                x += fl.width + 18
            d.text((x, 14), name, font=_sans(40, "ExtraBold"), fill=(255, 255, 255, 255))
            vf = _sans(42, "Black")
            d.text((self.width - 24 - vf.getlength(value), 12), value, font=vf, fill=ACCENT + (255,))
            self.static.append(img)

    def draw(self, frame: np.ndarray, local: float, y0: int) -> None:
        if self.head:
            _blit(frame, self.head, 60, y0 - 58, min(1.0, local / 0.3))
        n = len(self.rows)
        for i, img in enumerate(self.static):
            at = 0.15 + 0.22 * (n - 1 - i)
            u = _ease((local - at) / 0.35)
            if u <= 0:
                continue
            row = img.copy()
            bar = _ease((local - at - 0.15) / 0.6) * self.fracs[i]
            if bar > 0:
                d = ImageDraw.Draw(row)
                x1 = 82 + max(8, round((self.width - 110) * bar))
                d.rounded_rectangle((82, 74, x1, 90), radius=8, fill=ACCENT + (255,) if i == 0 else (255, 255, 255, 210))
            _blit(frame, _rgba(row), 60, y0 + i * self.row_h + round(30 * (1 - u)), u)


def _end_layers(question: str, source: str) -> dict:
    logo = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(logo)
    a, b = _anton(120), _anton(120)
    aw, bw = a.getlength("ATLAS "), b.getlength("IN NUMBERS")
    x = (W - aw - bw) / 2
    d.text((x, 20), "ATLAS ", font=a, fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0, 255))
    d.text((x + aw, 20), "IN NUMBERS", font=b, fill=ACCENT + (255,), stroke_width=4, stroke_fill=(0, 0, 0, 255))
    big = _anton(110)
    q = _lines_layer([(line, big, (255, 255, 255, 255)) for line in _wrap(question.upper(), big, round(W * CAPTION_W))],
                     stroke=7, gap=10)
    meta = _lines_layer([(source, _sans(30, "SemiBold"), (255, 255, 255, 220)),
                         (DISCLOSURE, _sans(24, "Medium"), (255, 255, 255, 170))], stroke=3, gap=12)
    return {"logo": _rgba(_shadowed(logo.crop(logo.getbbox()))), "question": _rgba(_shadowed(q)), "meta": _rgba(meta)}


# -- timeline -------------------------------------------------------------------------------------------------------

def segments(ep: AtlasEpisode, spans: list[tuple[float, float]], total: float, pics: dict) -> list[dict]:
    """What fills the frame when: the globe, one country's photo, or a split between a group's countries."""
    out = []
    used: dict[str, int] = {}
    for i, (beat, (s, e)) in enumerate(zip(ep.beats, spans)):
        s, e = (0.0 if i == 0 else s), (total if i == len(spans) - 1 else e)
        shot = beat.shot
        cut = s + max(DIVE, 0.42 * (e - s))
        if shot.kind == "country" and pics.get(shot.iso, {}).get("photos") and e - cut >= MIN_PHOTO:
            photos = pics[shot.iso]["photos"]
            out.append({"kind": "globe", "t0": s, "t1": cut, "beat": i})
            n = 2 if e - cut >= 4.4 and len(photos) > 1 else 1
            for k in range(n):
                idx = (used.get(shot.iso, 0) + k) % len(photos)
                out.append({"kind": "photo", "t0": cut + (e - cut) * k / n, "t1": cut + (e - cut) * (k + 1) / n,
                            "beat": i, "iso": shot.iso, "photo": photos[idx]})
            used[shot.iso] = used.get(shot.iso, 0) + n
        elif shot.kind == "group" and 2 <= len(shot.isos) <= 3 and all(pics.get(x, {}).get("photos") for x in shot.isos) \
                and e - cut >= MIN_PHOTO:
            out.append({"kind": "globe", "t0": s, "t1": cut, "beat": i})
            out.append({"kind": "split", "t0": cut, "t1": e, "beat": i, "isos": list(shot.isos),
                        "photos": [pics[x]["photos"][used.get(x, 0) % len(pics[x]["photos"])] for x in shot.isos]})
            for x in shot.isos:
                used[x] = used.get(x, 0) + 1
        else:
            out.append({"kind": "globe", "t0": s, "t1": e, "beat": i})
    for k, seg in enumerate(out):
        seg["motion"] = MOTIONS[k % len(MOTIONS)]
    return out


def narrate(ep: AtlasEpisode, folder: Path) -> tts.Narration:
    spec = ShortSpec(id=ep.id, title=ep.title, hook_text=ep.hook_text, voice=VOICE, captions=CaptionStyle(),
                     beats=[Beat(text=b.text, pause_after=b.pause_after) for b in ep.beats])
    narr = tts.synthesize(spec, folder)
    if not TARGET[0] <= narr.duration <= TARGET[1]:
        speed = min(1.18, max(0.98, VOICE.speed * narr.duration / sum(TARGET) * 2))
        spec = spec.model_copy(update={"voice": VOICE.model_copy(update={"speed": speed})})
        narr = tts.synthesize(spec, folder)
    return narr


def _effects(ep: AtlasEpisode, scene: dict, segs: list[dict], total: float, cache: Path) -> np.ndarray:
    n = int(total * sfx.SAMPLE_RATE)
    track = np.zeros(n, np.float32)

    def add(name: str, at: float, db: float) -> None:
        clip, _ = sf.read(sfx.ensure(name, cache), dtype="float32")
        if clip.ndim > 1:
            clip = clip.mean(axis=1)
        a = int(max(at, 0) * sfx.SAMPLE_RATE)
        b = min(a + len(clip), n)
        if a < n:
            track[a:b] += clip[:b - a] * 10 ** (db / 20)

    shots = scene["shots"]
    for i in range(1, len(shots)):
        s, p = shots[i], shots[i - 1]
        if s["focus"] != p["focus"] or s["alt"] != p["alt"]:
            add("whoosh", s["t0"] - 0.12, -19)
        if s["isos"] and s["kind"] in ("country", "group", "world"):
            add("pop", s["t0"] + min(1.25, 0.42 * (s["t1"] - s["t0"])) + 0.05, -23)
        if s["kind"] == "rank":
            for k in range(len(s["isos"])):
                add("pop", s["t0"] + 0.15 + 0.22 * k, -26)
    for seg in segs:
        if seg["kind"] in ("photo", "split") and seg["t0"] > 0.5:
            add("whoosh", seg["t0"] - 0.2, -24)
    return track


def _mix(narration: Path, music: np.ndarray, effects: np.ndarray, total: float, folder: Path) -> Path:
    sf.write(folder / "music.wav", music, score.SR)
    sf.write(folder / "effects.wav", effects, sfx.SAMPLE_RATE)
    out = folder / "mix.wav"
    graph = ("[0:a]aresample=48000,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,asplit=2[v][key];"
             "[1:a]aresample=48000,volume=0.32[m];"
             "[m][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];"
             "[2:a]aresample=48000,volume=1.0[fx];"
             "[v][duck][fx]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.8,"
             f"loudnorm=I=-14:TP=-1.5:LRA=9,apad,atrim=0:{total:.3f}[out]")
    subprocess.run([ff.exe(), "-y", "-loglevel", "error", "-i", str(narration), "-i", str(folder / "music.wav"),
                    "-i", str(folder / "effects.wav"), "-filter_complex", graph, "-map", "[out]", "-ar", "48000",
                    "-ac", "2", str(out)], check=True)
    (folder / "music.wav").unlink()
    (folder / "effects.wav").unlink()
    return out


def _globe_frames(video: Path):
    proc = subprocess.Popen([ff.exe(), "-loglevel", "error", "-i", str(video), "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-"], stdout=subprocess.PIPE)
    size = W * H * 3
    last = None
    try:
        while True:
            buf = proc.stdout.read(size)
            if len(buf) < size:
                break
            last = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            yield last
        while last is not None:
            yield last
    finally:
        proc.kill()
        proc.wait()


def render(ep: AtlasEpisode, folder: Path, cache: Path) -> Path:
    """short.mp4 (1080x1920, 30 fps, H.264 + AAC), stills, captions.srt, timing.json and credits.json in folder;
    country pictures are kept in cache across episodes."""
    folder.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    ds = dataset(ep, folder)
    scale = Scale(ep.scale.kind, at=ep.scale.at, edges=ep.scale.edges, labels=ep.scale.labels)
    world = geo.world()
    names = {iso: short_name(c.name) for iso, c in world.items()}

    narr = narrate(ep, folder)
    total = narr.duration + TAIL
    spans = narr.beat_spans
    words = [{"text": w.text, "start": w.start, "end": w.end, "beat": w.beat} for w in narr.words]
    (folder / "timing.json").write_text(json.dumps({"duration": total, "beats": [
        {"start": a, "end": b, "text": ep.beats[i].text} for i, (a, b) in enumerate(spans)]}, indent=2))
    write_srt(narr.words, folder / "captions.srt")

    featured = []
    for b in ep.beats:
        for iso in ([b.shot.iso] if b.shot.iso else []) + list(b.shot.isos):
            if iso in world and iso not in featured:
                featured.append(iso)
    pics = {}
    for iso in featured:
        try:
            pics[iso] = places.gather(iso, cache)
        except Exception as err:  # a country without pictures stays on the globe
            log.warning("%s: no pictures for %s: %s", ep.id, iso, err)
    segs = segments(ep, spans, total, pics)

    stage = folder / ".stage"
    scene = globe.bake(ep, ds, scale, spans, total, stage, ACCENT, first_pins=HOOK_HOLD + 0.35)
    globe_mp4 = folder / "globe.mp4"
    needed = set()
    for k, seg in enumerate(segs):
        a, b = round(seg["t0"] * FPS), math.ceil(seg["t1"] * FPS)
        if seg["kind"] == "globe":
            needed.update(range(a, b + 1))
        elif k and segs[k - 1]["kind"] == "globe":
            needed.update(range(a, a + CROSS + 1))
    stats = globe.capture(stage, total, globe_mp4, needed)
    log.info("%s: globe captured %s", ep.id, stats)

    unit = ep.dataset.unit or ep.dataset.label
    source = f"Data: {ds.source}, {ds.year_label}"
    chip = _chip_layer(ep.dataset.label, f"{ds.source} · {ds.year_label}")
    hook = _hook_layer(ep.hook_text or ep.title, ep.dataset.label)
    captions = Captions([w for w in words if ep.beats[w["beat"]].shot.kind != "card"])
    card_beat = next((i for i, b in enumerate(ep.beats) if b.shot.kind == "card"), None)
    question = ep.beats[card_beat].shot.lines[0] if card_beat is not None and ep.beats[card_beat].shot.lines else \
        (ep.beats[card_beat].text if card_beat is not None else "")
    end = _end_layers(question, source)
    photo_mask, caption_mask = _masks()
    plates: dict[str, Plate] = {}
    split_plates: dict[str, Plate] = {}
    cam, cams = Camera(), {}
    country_cards, place_cards, credits_used = {}, {}, []

    def value_of(iso: str) -> str:
        return ep.value_text(ds.values[iso]) if iso in ds.values else ""

    def country_card(iso: str):
        if iso not in country_cards:
            flag = (pics.get(iso, {}).get("flag") or {}).get("path")
            country_cards[iso] = _country_layer(names.get(iso, iso), value_of(iso), unit, flag)
        return country_cards[iso]

    def photo_frame(seg: dict, t: float) -> np.ndarray:
        u = (t - seg["t0"]) / max(seg["t1"] - seg["t0"], 0.1)
        if seg["kind"] == "photo":
            p = seg["photo"]
            plate = plates.setdefault(p["path"], Plate(p["path"]))
            return cam.shoot(plate, u, seg["motion"])
        n = len(seg["photos"])
        bh = H // n
        frame = np.zeros((H, W, 3), np.uint8)
        for k, p in enumerate(seg["photos"]):
            key = f"{p['path']}:{n}"
            plate = split_plates.setdefault(key, Plate(p["path"], (W, bh)))
            c = cams.setdefault(n, Camera((W, bh)))
            frame[k * bh:(k + 1) * bh] = c.shoot(plate, u, MOTIONS[(k * 2) % len(MOTIONS)])
        for k in range(1, n):
            frame[k * bh - 3:k * bh + 3] = 255
        return frame

    rank_panels: dict[int, RankPanel] = {}
    for i, b in enumerate(ep.beats):
        if b.shot.kind == "rank":
            title, rows = rank_rows(b.shot.isos, ds, ep, scale, names)
            by_name = {names.get(x, x): x for x in b.shot.isos}
            said = [v for v in (ds.values.get(x) for x in b.shot.isos) if v is not None]
            if len(said) == len(rows) and said == sorted(said):
                # The narration lists them from the bottom up ("the emptiest: ..."), so the panel does too.
                rows = sorted(rows, key=lambda r: r[2])
            rank_panels[i] = RankPanel(title.upper(), ep.dataset.label, [
                (name, value, v, (pics.get(by_name.get(name, ""), {}).get("flag") or {}).get("path"))
                for name, value, v, _ in rows])

    mixed = _mix(narr.wav_path, score.score(total, ep.id), _effects(ep, scene, segs, total, folder / ".sfx"), total,
                 folder)
    out = folder / "short.mp4"
    stills = folder / "stills"
    stills.mkdir(exist_ok=True)
    enc = subprocess.Popen(
        [ff.exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-i", str(mixed), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    n = int(math.ceil(total * FPS))
    still_at = {round(s["t0"] * FPS + (s["t1"] - s["t0"]) * FPS * 0.6) for s in segs} | {0}
    frames = _globe_frames(globe_mp4)
    try:
        for f in range(n):
            t = f / FPS
            g = next(frames)
            k = next(j for j, s in enumerate(segs) if t < s["t1"] or j == len(segs) - 1)
            seg = segs[k]
            beat = ep.beats[seg["beat"]]
            local = t - spans[seg["beat"]][0] if seg["beat"] else t
            if seg["kind"] == "globe":
                frame = (g.astype(np.float32) * caption_mask).astype(np.uint8)
            else:
                frame = _photo_grade(photo_frame(seg, t), photo_mask)
                p = seg["photo"] if seg["kind"] == "photo" else None
                if p and p not in credits_used:
                    credits_used.append(p)
                for q in seg.get("photos", []):
                    if q not in credits_used:
                        credits_used.append(q)
            into = (t - seg["t0"]) * FPS
            if k and into < CROSS:
                prev = segs[k - 1]
                a = into / CROSS
                if prev["kind"] == "globe":
                    # Through the globe into the photo: the globe frame swells as it fades.
                    z = 1 + 0.25 * a
                    big = cv2.resize(g, None, fx=z, fy=z, interpolation=cv2.INTER_LINEAR)
                    y0, x0 = (big.shape[0] - H) // 2, (big.shape[1] - W) // 2
                    before = big[y0:y0 + H, x0:x0 + W]
                else:
                    before = _photo_grade(photo_frame(prev, t), photo_mask)
                if seg["kind"] != "globe" or prev["kind"] != "globe":
                    frame = cv2.addWeighted(frame, a, before, 1 - a, 0)
            frame = np.ascontiguousarray(frame)
            if beat.shot.kind == "card":
                fade = min(1.0, local / 0.5)
                dark = (frame.astype(np.float32) * (1 - 0.45 * fade)).astype(np.uint8)
                frame = dark
                _blit(frame, end["logo"], (W - end["logo"][1].shape[1]) // 2, round(H * 0.08), fade)
                qh = end["question"][1].shape[0]
                _blit(frame, end["question"], (W - end["question"][1].shape[1]) // 2, round(H * CAPTION_Y - qh / 2),
                      min(1.0, local / 0.25))
                _blit(frame, end["meta"], (W - end["meta"][1].shape[1]) // 2, round(H * 0.80), fade)
            elif seg["beat"] == 0 and seg["kind"] == "globe" and t < HOOK_HOLD + 0.35:
                # Fully visible from the first frame (YouTube may use it as the cover), gone before the pins land.
                _blit(frame, hook, (W - hook[1].shape[1]) // 2, round(H * 0.06), min(1.0, (HOOK_HOLD + 0.35 - t) / 0.35))
                captions.draw(frame, t)
            else:
                if seg["kind"] == "photo":
                    card = country_card(seg["iso"])
                    a = min(1.0, (t - seg["t0"]) / 0.3)
                    _blit(frame, card, 40, round(H * 0.075) + round(20 * (1 - a)), a)
                    p = seg["photo"]
                    key = p["path"]
                    if key not in place_cards:
                        here = p["place"] if p["place"] != names.get(seg["iso"]) else ""
                        place_cards[key] = _place_layer(here, places.credit(p))
                    _blit(frame, place_cards[key], 44, round(H * 0.79), min(1.0, (t - seg["t0"]) / 0.4))
                elif seg["kind"] == "split":
                    m = len(seg["isos"])
                    bh = H // m
                    for j, iso in enumerate(seg["isos"]):
                        card = country_card(iso)
                        scale_k = min(1.0, (bh * 0.42) / card[1].shape[0])
                        if scale_k < 1:
                            size = (round(card[1].shape[1] * scale_k), round(card[1].shape[0] * scale_k))
                            card = (cv2.resize(card[0], size), cv2.resize(card[1], size)[..., None])
                        a = min(1.0, (t - seg["t0"] - 0.12 * j) / 0.3)
                        _blit(frame, card, 40, j * bh + 30, max(0.0, a))
                    credit = " | ".join(f"{q['author']} / {q['license']}" for q in seg["photos"])
                    key = "split:" + credit
                    if key not in place_cards:
                        place_cards[key] = _place_layer("", "Photos: " + credit + " / Wikimedia Commons")
                    _blit(frame, place_cards[key], 44, round(H * 0.80), 1.0)
                else:
                    since = t - HOOK_HOLD - 0.35 if seg["beat"] == 0 else local if seg["beat"] == 1 else 1.0
                    _blit(frame, chip, 40, round(H * 0.045), min(1.0, since / 0.3))
                    if beat.shot.kind == "rank" and seg["beat"] in rank_panels:
                        rank_panels[seg["beat"]].draw(frame, local, round(H * 0.17))
                captions.draw(frame, t)
            enc.stdin.write(frame.tobytes())
            if f in still_at:
                Image.fromarray(frame).save(stills / f"f{f:04d}.jpg", quality=88)
    finally:
        frames.close()
        enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("ffmpeg failed to encode the Short")
    (folder / "credits.json").write_text(json.dumps([{
        "file": p["file"], "page": p["page"], "author": p["author"], "license": p["license"], "place": p["place"]}
        for p in credits_used], indent=1, ensure_ascii=False), encoding="utf-8")
    log.info("%s: %.1f s Short rendered in %.0f s", ep.id, total, time.monotonic() - started)
    return out
