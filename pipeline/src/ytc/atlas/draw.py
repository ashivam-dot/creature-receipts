"""Vector map frames for a vertical Short: a camera over the Equal Earth world, coloured by one dataset."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import geo

W, H = 1080, 1920
SS = 2  # supersampling; PIL polygons have no antialiasing
MAP_Y = 0.47  # where the camera's centre sits on screen, as a fraction of the height
FONTS = Path(__file__).resolve().parents[3] / "assets" / "fonts"

OCEAN = (9, 18, 36)
OCEAN_GLOW = (17, 34, 64)
NO_DATA = (52, 60, 78)
BORDER = (9, 18, 36)
HIGHLIGHT = (255, 212, 0)
INK = (255, 255, 255)
MUTED = (170, 182, 204)

# Colour-blind-safe sequential ramp (cividis-like, brightened for a dark background).
RAMP = [(38, 62, 120), (64, 92, 136), (102, 116, 128), (150, 142, 112), (204, 172, 82), (253, 210, 52)]


@cache
def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def lerp_color(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


@dataclass
class Scale:
    """How a value becomes a colour: a threshold split into two colours, or bins along the ramp."""

    kind: str = "bins"  # "threshold" or "bins"
    at: float = 0.0
    above: tuple = (253, 197, 49)
    below: tuple = (47, 75, 124)
    edges: list[float] = field(default_factory=list)  # bin edges for "bins", ascending
    labels: list[str] = field(default_factory=list)

    def color(self, value: float | None) -> tuple:
        if value is None:
            return NO_DATA
        if self.kind == "threshold":
            return self.above if value >= self.at else self.below
        idx = sum(1 for e in self.edges if value >= e)
        return RAMP[round(idx * (len(RAMP) - 1) / max(len(self.edges), 1))]

    def swatches(self) -> list[tuple[tuple, str]]:
        if self.kind == "threshold":
            return [(self.above, self.labels[0] if self.labels else f">= {self.at:g}"),
                    (self.below, self.labels[1] if len(self.labels) > 1 else f"< {self.at:g}")]
        colors = [self.color(self.edges[0] - 1)] + [self.color(e) for e in self.edges]
        return list(zip(colors, self.labels or [""] * len(colors)))


@dataclass
class Camera:
    cx: float  # projected centre
    cy: float
    hw: float  # half the visible width, in projected units

    def mix(self, other: Camera, t: float) -> Camera:
        """Fly between two views; zoom moves in log space so its speed feels even."""
        hw = math.exp(math.log(self.hw) + (math.log(other.hw) - math.log(self.hw)) * t)
        return Camera(self.cx + (other.cx - self.cx) * t, self.cy + (other.cy - self.cy) * t, hw)

    def zoomed(self, factor: float) -> Camera:
        return Camera(self.cx, self.cy, self.hw / factor)


# Slightly cropped at the far Pacific edges so the world reads bigger on a phone.
WORLD = Camera(0.12, 0.22, geo.XMAX * 0.9)


def fit(box: tuple[float, float, float, float], pad: float = 1.7, min_hw: float = 0.18) -> Camera:
    """A view that shows the box, padded, inside the map band between the legend and the captions."""
    x0, y0, x1, y1 = box
    usable_h = H * 0.30
    hw = max((x1 - x0) / 2 * pad, (y1 - y0) / 2 * pad * W / usable_h, min_hw)
    return Camera((x0 + x1) / 2, (y0 + y1) / 2, min(hw, WORLD.hw))


def country_camera(iso3: str, pad: float = 1.7) -> Camera:
    return fit(geo.world()[iso3].bbox(), pad)


def group_camera(isos: list[str], pad: float = 1.25) -> Camera:
    boxes = [geo.world()[i].bbox() for i in isos]
    return fit((min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes),
                max(b[3] for b in boxes)), pad)


def region_camera(lon0: float, lat0: float, lon1: float, lat1: float) -> Camera:
    xs, ys = geo.project(np.array([lon0, lon1, lon0, lon1]), np.array([lat0, lat0, lat1, lat1]))
    return fit((xs.min(), ys.min(), xs.max(), ys.max()), pad=1.0)


def ease(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


@cache
def _ring_boxes() -> list[tuple[str, int, tuple[float, float, float, float]]]:
    out = []
    for iso, c in geo.world().items():
        if iso == "ATA":
            continue
        for i, r in enumerate(c.rings):
            out.append((iso, i, (r[:, 0].min(), r[:, 1].min(), r[:, 0].max(), r[:, 1].max())))
    return out


def _to_px(cam: Camera, pts: np.ndarray, ss: int = SS) -> np.ndarray:
    scale = W * ss / (2 * cam.hw)
    px = (pts[:, 0] - cam.cx) * scale + W * ss / 2
    py = H * ss * MAP_Y - (pts[:, 1] - cam.cy) * scale
    return np.column_stack([px, py])


def screen_point(cam: Camera, iso3: str) -> tuple[float, float]:
    x, y = geo.world()[iso3].point
    p = _to_px(cam, np.array([[x, y]]), 1)[0]
    return float(p[0]), float(p[1])


@cache
def _background() -> Image.Image:
    img = Image.new("RGB", (W * SS, H * SS), OCEAN)
    glow = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(glow).ellipse([-W * SS * 0.3, H * SS * 0.2, W * SS * 1.3, H * SS * 0.74], fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(W * SS * 0.16))
    return Image.composite(Image.new("RGB", img.size, OCEAN_GLOW), img, glow)


def map_layer(cam: Camera, colors: dict[str, tuple], highlight: set[str], dim: float = 0.0) -> Image.Image:
    """The map at supersampled size: countries filled, thin ocean-coloured borders, highlighted ones outlined.
    `dim` fades every country that isn't highlighted towards the ocean."""
    img = _background().copy()
    d = ImageDraw.Draw(img)
    view = (cam.cx - cam.hw, cam.cy - cam.hw * H / W, cam.cx + cam.hw, cam.cy + cam.hw * H / W)
    world = geo.world()
    border = max(1, int(SS * min(2.5, 0.9 * WORLD.hw / cam.hw)))
    outlines = []
    for iso, i, (x0, y0, x1, y1) in _ring_boxes():
        if x1 < view[0] or x0 > view[2] or y1 < view[1] or y0 > view[3]:
            continue
        flat = [tuple(p) for p in _to_px(cam, world[iso].rings[i])]
        if len(flat) < 3:
            continue
        fill = colors.get(iso, NO_DATA)
        if dim and iso not in highlight:
            fill = lerp_color(fill, OCEAN, dim)
        d.polygon(flat, fill=fill, outline=BORDER, width=border)
        if iso in highlight:
            outlines.append(flat)
    for flat in outlines:
        d.line(flat + [flat[0]], fill=HIGHLIGHT, width=SS * 4, joint="curve")
    return img


def text_center(d: ImageDraw.ImageDraw, xy: tuple, text: str, f: ImageFont.FreeTypeFont, fill=INK) -> None:
    d.text(xy, text, font=f, fill=fill, anchor="mm")


def overlay(img: Image.Image, *, chip: str, swatches: list[tuple[tuple, str]], source: str,
            callouts: list[tuple[float, float, str, str]], chip_alpha: float = 1.0,
            callout_alpha: float = 1.0) -> Image.Image:
    """Everything drawn at screen size over the map: the metric chip and legend, the source line, and the
    labelled callouts (screen x, screen y, name, value)."""
    base = img.resize((W, H), Image.LANCZOS).convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(255 * chip_alpha)
    if chip and a:
        f = font("Montserrat-ExtraBold.ttf", 38)
        tw = d.textlength(chip.upper(), font=f)
        y = int(H * 0.268)
        d.rounded_rectangle((W / 2 - tw / 2 - 28, y - 34, W / 2 + tw / 2 + 28, y + 34), radius=34,
                            fill=(28, 40, 66, int(a * 0.95)))
        text_center(d, (W / 2, y), chip.upper(), f, fill=(255, 255, 255, a))
        fs = font("Montserrat-ExtraBold.ttf", 30)
        items = [(c, label.upper()) for c, label in swatches if label]
        total = sum(40 + d.textlength(t, font=fs) for _, t in items) + 34 * max(len(items) - 1, 0)
        x = W / 2 - total / 2
        if items:
            d.rounded_rectangle((x - 22, y + 52, x + total + 22, y + 100), radius=24, fill=(9, 18, 36, int(a * 0.85)))
        for color, label in items:
            d.rounded_rectangle((x, y + 62, x + 28, y + 90), radius=6, fill=(*color, a))
            d.text((x + 40, y + 76), label, font=fs, fill=(*MUTED, a), anchor="lm")
            x += 40 + d.textlength(label, font=fs) + 34
    if source:
        fs = font("Montserrat-ExtraBold.ttf", 26)
        tw, y = d.textlength(source.upper(), font=fs), int(H * 0.655)
        d.rounded_rectangle((W / 2 - tw / 2 - 20, y - 22, W / 2 + tw / 2 + 20, y + 22), radius=22,
                            fill=(9, 18, 36, 200))
        text_center(d, (W / 2, y), source.upper(), fs, fill=(*MUTED, 235))
    ca = int(255 * callout_alpha)
    for x, y, name, value, bx, by, bw, bh in _layout(d, callouts) if ca else []:
        fn, fv = font("Montserrat-Black.ttf", 38), font("Anton-Regular.ttf", 66)
        anchor_y = by + bh if by + bh <= y else by
        d.line((x, y, bx + bw / 2, anchor_y), fill=(*HIGHLIGHT, ca), width=4)
        d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(*HIGHLIGHT, ca), outline=(0, 0, 0, ca), width=3)
        d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=20, fill=(10, 16, 30, int(ca * 0.92)),
                            outline=(*HIGHLIGHT, ca), width=4)
        text_center(d, (bx + bw / 2, by + 36), name.upper(), fn, fill=(*MUTED, ca))
        text_center(d, (bx + bw / 2, by + 94), value, fv, fill=(*HIGHLIGHT, ca))
    return Image.alpha_composite(base, layer).convert("RGB")


TOP, BOTTOM = H * 0.335, H * 0.625  # the band callouts stay inside, clear of the legend and captions


def _layout(d: ImageDraw.ImageDraw, callouts: list[tuple[float, float, str, str]]) -> list[tuple]:
    """Place each callout's box above its point (below when there's no room), then push overlapping boxes
    apart vertically, keeping them inside the map band."""
    fn, fv = font("Montserrat-Black.ttf", 38), font("Anton-Regular.ttf", 66)
    placed = []
    for x, y, name, value in callouts:
        bw = max(d.textlength(name.upper(), font=fn), d.textlength(value, font=fv)) + 52
        bh = 134
        bx = min(max(x - bw / 2, 24), W - bw - 24)
        by = y - bh - 80 if y - bh - 80 >= TOP else y + 80
        placed.append([x, y, name, value, bx, min(max(by, TOP), BOTTOM - bh), bw, bh])
    placed.sort(key=lambda p: p[5])
    for i in range(1, len(placed)):
        prev, cur = placed[i - 1], placed[i]
        overlap_x = cur[4] < prev[4] + prev[6] + 12 and prev[4] < cur[4] + cur[6] + 12
        if overlap_x and cur[5] < prev[5] + prev[7] + 14:
            cur[5] = prev[5] + prev[7] + 14
    if placed and placed[-1][5] + placed[-1][7] > BOTTOM:
        shift = placed[-1][5] + placed[-1][7] - BOTTOM
        for p in placed:
            p[5] = max(TOP, p[5] - shift)
    return [tuple(p) for p in placed]


SHORT_NAMES = {"United Arab Emirates": "UAE", "People's Republic of China": "China",
               "United States of America": "USA", "United Kingdom": "UK", "Russian Federation": "Russia",
               "Democratic Republic of the Congo": "DR Congo", "Republic of the Congo": "Congo",
               "Central African Republic": "C. African Rep.", "Bosnia and Herzegovina": "Bosnia",
               "Dominican Republic": "Dominican Rep.", "Papua New Guinea": "Papua N. Guinea",
               "Trinidad and Tobago": "Trinidad & Tobago", "Saint Vincent and the Grenadines": "St Vincent",
               "Republic of China": "Taiwan", "South Korea": "South Korea", "North Korea": "North Korea"}


def short_name(name: str) -> str:
    return SHORT_NAMES.get(name, name)


def card(lines: list[tuple[str, int, tuple]], under: Image.Image | None = None, shade: int = 215) -> Image.Image:
    """A full-screen text card (text, font size, colour per line), over a darkened frame if one is given."""
    img = (under.resize((W, H)) if under is not None else Image.new("RGB", (W, H), OCEAN)).convert("RGBA")
    img = Image.alpha_composite(img, Image.new("RGBA", (W, H), (*OCEAN, shade)))
    d = ImageDraw.Draw(img)
    total = sum(int(size * 1.4) for _, size, _ in lines)
    y = H * 0.40 - total / 2
    for text, size, color in lines:
        name = "Montserrat-Black.ttf" if size >= 48 else "Montserrat-ExtraBold.ttf"
        f = font(name, size)
        while size > 24 and d.textlength(text, font=f) > W * 0.86:
            size -= 4
            f = font(name, size)
        y += size * 1.4 / 2
        text_center(d, (W / 2, y), text, f, fill=color)
        y += size * 1.4 / 2
    return img.convert("RGB")
