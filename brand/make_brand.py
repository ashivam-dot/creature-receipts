"""Build the History's Last Hours brand kit: avatar, banner, watermark, and the banner credits.

Run from the pipeline project so its dependencies are available:
    cd pipeline && uv run --no-sync python ../brand/make_brand.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BRAND = Path(__file__).resolve().parent
PIPELINE = BRAND.parent / "pipeline"
FONTS = PIPELINE / "assets/fonts"
ANTON = FONTS / "Anton-Regular.ttf"
MONTSERRAT_XB = FONTS / "Montserrat-ExtraBold.ttf"
MONTSERRAT_BLACK = FONTS / "Montserrat-Black.ttf"

ABYSS = (5, 24, 36)
TEAL = (0, 96, 108)
LIME = (190, 255, 60)
WHITE = (255, 255, 255)
MIST = (168, 222, 214)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = f"HistorysLastHoursBrand/1.0 ({os.environ.get('YTC_CONTACT') or 'aksha.shivam18@gmail.com'})"
# Commons licenses that allow commercial reuse without share-alike or NonCommercial terms.
OPEN_LICENSES = re.compile(r"^(public domain|pd\b.*|cc0.*|cc by \d(\.\d)?|no restrictions)$", re.I)

# name: (Commons file title, download width, display title, author as the source credits it)
PICTURES = {
    "humpback": ("File:Humpback Whale Underwater (37209287981).jpg", 3072,
                 "Humpback whale underwater, Hawaiian Islands Humpback Whale National Marine Sanctuary (2010)",
                 "NOAA National Marine Sanctuaries"),
    "mantis": ("File:Mantis shrimp (Odontodactylus scyllarus).jpg", 2400,
               "Peacock mantis shrimp (Odontodactylus scyllarus)", "prilfish from Vienna, Austria"),
    "dumbo": ("File:Dumbo-hires.jpg", 1920, "Dumbo octopus (Grimpoteuthis), NOAA Okeanos Explorer",
              "NOAA Okeanos Explorer Program"),
}


def _plain(html) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(html or ""))).strip()


def _fetch_picture(name: str, title: str, width: int, cache: Path) -> tuple[Image.Image, dict]:
    """Download a Commons picture once, refusing anything not public domain, CC0, or CC BY."""
    cache.mkdir(parents=True, exist_ok=True)
    path, meta_path = cache / f"{name}.jpg", cache / f"{name}.json"
    if not meta_path.exists():
        query = urllib.parse.urlencode({"action": "query", "prop": "imageinfo", "iiprop": "extmetadata|url",
                                        "iiurlwidth": width, "titles": title, "format": "json"})
        request = urllib.request.Request(f"{COMMONS_API}?{query}", headers={"User-Agent": USER_AGENT})
        page = next(iter(json.load(urllib.request.urlopen(request, timeout=60))["query"]["pages"].values()))
        info = page["imageinfo"][0]
        meta = {k: _plain(v.get("value", "")) for k, v in info["extmetadata"].items()}
        license_name = meta.get("LicenseShortName", "")
        if not OPEN_LICENSES.match(license_name):
            raise RuntimeError(f"{title}: license {license_name!r} isn't public domain, CC0, or CC BY")
        credit = {"title": page["title"].removeprefix("File:"), "author": meta.get("Artist", ""),
                  "credit": meta.get("Credit", ""), "license": license_name,
                  "license_url": meta.get("LicenseUrl", ""),
                  "url": info["descriptionurl"], "download": info.get("thumburl") or info["url"]}
        subprocess.run(["curl", "-sSfL", "-A", USER_AGENT, "-o", str(path), credit["download"]], check=True)
        meta_path.write_text(json.dumps(credit, indent=2, ensure_ascii=False), encoding="utf-8")
    return Image.open(path).convert("RGB"), json.loads(meta_path.read_text(encoding="utf-8"))


def _zigzag(x0: float, x1: float, y: float, tooth: float, down: bool = True) -> list[tuple[float, float]]:
    """Points of a torn-paper zigzag running from x1 back to x0 along y."""
    count = max(2, round((x1 - x0) / tooth))
    step = (x1 - x0) / count
    depth = step * 0.55 * (1 if down else -1)
    points = []
    for i in range(count, -1, -1):
        points.append((x0 + i * step, y))
        if i:
            points.append((x0 + (i - 0.5) * step, y + depth))
    return points


def _bezier(p0, p1, p2, p3, n: int = 24) -> list[tuple[float, float]]:
    t = np.linspace(0, 1, n)[:, None]
    pts = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
    return [tuple(p) for p in pts]


def _fluke(cx: float, cy: float, half_w: float) -> list[tuple[float, float]]:
    """Outline of a whale's tail fluke rising out of the water, centered on (cx, cy)."""
    P = lambda x, y: np.array([x, y], float)  # noqa: E731  unit coordinates, y down
    right = [P(0.26, 1.0)]
    right += _bezier(P(0.26, 1.0), P(0.17, 0.80), P(0.14, 0.60), P(0.15, 0.42))
    right += _bezier(P(0.15, 0.42), P(0.50, 0.42), P(0.92, 0.20), P(1.0, -0.36))
    right += _bezier(P(1.0, -0.36), P(0.78, -0.40), P(0.30, -0.28), P(0.0, -0.02))
    left = [P(-x, y) for x, y in reversed(right)]
    return [(cx + x * half_w, cy + y * half_w) for x, y in [*right, *left]]


def _mark(size: int) -> Image.Image:
    """The receipt mark on a transparent square: a white receipt with a torn bottom holding a whale's tail."""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    cx = size / 2
    w, h = size * 0.54, size * 0.68
    left, right, top = cx - w / 2, cx + w / 2, size * 0.5 - h / 2 - size * 0.015
    bottom = top + h
    tooth = w / 7
    corner = size * 0.045
    outline = [(left, bottom), (left, top + corner)]
    outline += [(left + corner * (1 - np.cos(a)), top + corner * (1 - np.sin(a))) for a in np.linspace(0, np.pi / 2, 12)]
    outline += [(right - corner * (1 - np.cos(a)), top + corner * (1 - np.sin(a))) for a in np.linspace(np.pi / 2, 0, 12)]
    outline += [(right, bottom)]
    outline += _zigzag(left, right, bottom, tooth)
    draw.polygon(outline, fill=WHITE)

    fluke_w = w * 0.40
    fluke_cy = top + h * 0.36
    draw.polygon(_fluke(cx, fluke_cy, fluke_w), fill=ABYSS)
    # A wave for the tail to dive into, with a white gap so the two shapes stay separate when tiny.
    bar_h = size * 0.042
    water_y = fluke_cy + fluke_w * 0.98
    wave_x = np.linspace(cx - w * 0.38, cx + w * 0.38, 80)
    crest = water_y + np.sin((wave_x - cx) / (w * 0.76) * 4 * np.pi) * size * 0.012
    gap = size * 0.02
    halo = [*zip(wave_x, crest - gap), *zip(wave_x[::-1], crest[::-1] + bar_h + gap)]
    draw.polygon(halo, fill=WHITE)
    draw.polygon([*zip(wave_x, crest), *zip(wave_x[::-1], crest[::-1] + bar_h)], fill=ABYSS)
    for end in (0, -1):
        draw.ellipse([wave_x[end] - bar_h / 2, crest[end], wave_x[end] + bar_h / 2, crest[end] + bar_h], fill=ABYSS)
    y = water_y + bar_h + size * 0.05
    lime_w = w * 0.44
    draw.rounded_rectangle([cx - lime_w / 2, y, cx + lime_w / 2, y + bar_h], radius=bar_h / 2, fill=LIME)
    return layer


def _badge(size: int, tilt: float = -8) -> Image.Image:
    """The circular badge used for the avatar and watermark, drawn 4x and scaled down for clean edges."""
    big = size * 4
    yy, xx = np.mgrid[0:big, 0:big].astype(np.float32)
    dist = np.hypot(xx - big / 2, (yy - big * 0.42)) / (big / 2)
    glow = np.clip(1 - dist, 0, 1)[..., None] ** 1.2
    bg = np.array(ABYSS, np.float32) + (np.array(TEAL, np.float32) - np.array(ABYSS, np.float32)) * glow
    badge = Image.fromarray(bg.astype(np.uint8), "RGB").convert("RGBA")
    mark = _mark(big).rotate(tilt, resample=Image.BICUBIC)
    shadow = Image.new("RGBA", mark.size, (0, 0, 0, 0))
    shadow.putalpha(mark.getchannel("A").point(lambda a: a * 0.55))
    shadow = shadow.filter(ImageFilter.GaussianBlur(big * 0.02))
    badge.alpha_composite(shadow, (0, int(big * 0.015)))
    badge.alpha_composite(mark)
    return badge.resize((size, size), Image.LANCZOS)


def make_avatar(out: Path, size: int = 800) -> Image.Image:
    avatar = _badge(size).convert("RGB")
    avatar.save(out)
    return avatar


def make_watermark(out: Path, size: int = 150) -> None:
    badge = _badge(size * 4)
    mask = Image.new("L", badge.size, 0)
    ImageDraw.Draw(mask).ellipse([0, 0, badge.width - 1, badge.height - 1], fill=255)
    badge.putalpha(mask)
    badge.resize((size, size), Image.LANCZOS).save(out)


def _cover(image: Image.Image, w: int, h: int, focus: tuple[float, float], zoom: float = 1.0) -> Image.Image:
    """Crop to w x h around the focus point (fractions of the picture), zoom times tighter than a plain cover."""
    scale = max(w / image.width, h / image.height) * zoom
    crop_w, crop_h = w / scale, h / scale
    left = min(max(focus[0] * image.width - crop_w / 2, 0), image.width - crop_w)
    top = min(max(focus[1] * image.height - crop_h / 2, 0), image.height - crop_h)
    return image.resize((w, h), Image.LANCZOS, box=(left, top, left + crop_w, top + crop_h))


def _band(image: Image.Image, w: int, h: int, focus: tuple[float, float], band_h: int, fill: tuple,
          band_top: int | None = None) -> Image.Image:
    """A w x h panel of `fill` holding a band_h-tall crop of a dark-background picture, feathered top and bottom."""
    crop = _cover(image, w, band_h, focus)
    panel = Image.new("RGB", (w, h), fill)
    ramp = np.clip(np.minimum(np.arange(band_h), band_h - 1 - np.arange(band_h)) / (band_h * 0.18), 0, 1) ** 1.5
    mask = Image.fromarray((np.tile(ramp[:, None], (1, w)) * 255).astype(np.uint8), "L")
    panel.paste(crop, (0, (h - band_h) // 2 if band_top is None else band_top), mask)
    return panel


def _torn_mask(w: int, h: int, side: str, tooth: int = 36) -> Image.Image:
    """Mask for a side panel whose inner edge is torn like a receipt."""
    mask = Image.new("L", (w, h), 0)
    step = h / max(2, round(h / tooth))
    depth = step * 0.55
    edge = []
    for i in range(round(h / step) + 1):
        edge.append((w - depth if side == "left" else depth, i * step))
        edge.append((w if side == "left" else 0, i * step + step / 2))
    edge = [(x, min(y, h)) for x, y in edge]
    polygon = [(0, 0), *edge, (0, h)] if side == "left" else [(w, 0), *edge, (w, h)]
    ImageDraw.Draw(mask).polygon(polygon, fill=255)
    return mask


def make_banner(out: Path, cache: Path) -> list[dict]:
    w, h = 2560, 1440
    safe_w, safe_h = 1546, 423
    pictures = {name: _fetch_picture(name, title, width, cache) for name, (title, width, *_) in PICTURES.items()}
    for name, (*_, label, author) in PICTURES.items():
        pictures[name][1].update(label=label, author=author)

    center = _cover(pictures["humpback"][0], w, h, (0.5, 0.5))
    arr = np.asarray(center, np.float32)
    # Shift the tropical blue toward deep teal so the whole banner shares one ocean palette.
    lum = arr @ np.array([0.30, 0.50, 0.20], np.float32)
    teal = np.array([20, 150, 160], np.float32) * (lum[..., None] / 120)
    arr = arr * 0.35 + teal * 0.65
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # Darken toward the middle so the name reads, keeping the whale visible at the edges.
    focus = np.exp(-(((xx - w / 2) / (safe_w * 0.62)) ** 2 + ((yy - h / 2) / (safe_h * 0.95)) ** 2))
    shade = 0.78 - 0.50 * focus
    abyss = np.array(ABYSS, np.float32)
    arr = arr * shade[..., None] + abyss * (1 - shade[..., None])
    banner = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    # The side pictures stop just outside the mobile crop, so phones see only the name on the ocean.
    side_w = (w - safe_w) // 2 - 10
    panels = {
        "left": _band(pictures["mantis"][0], side_w, h, (0.465, 0.5), 1000, (12, 9, 7), band_top=460),
        "right": _band(pictures["dumbo"][0], side_w, h, (0.765, 0.48), 700, (3, 5, 9)),
    }
    for side, panel in panels.items():
        mask = _torn_mask(side_w, h, side)
        x = 0 if side == "left" else w - side_w
        edge = mask.filter(ImageFilter.MaxFilter(15))
        banner.paste(Image.new("RGB", (side_w, h), LIME), (x, 0), edge)
        banner.paste(panel, (x, 0), mask)

    draw = ImageDraw.Draw(banner)
    title_font = ImageFont.truetype(str(ANTON), 188)
    tag_font = ImageFont.truetype(str(MONTSERRAT_BLACK), 56)
    small_font = ImageFont.truetype(str(MONTSERRAT_XB), 30)
    words = [("CREATURE", WHITE), ("RECEIPTS", LIME)]
    tagline = "ANIMAL STORIES. WITH RECEIPTS."
    small = "NEW SHORTS EVERY DAY  ·  EVERY CLAIM SOURCED"

    word_gap = 38
    widths = [draw.textlength(word, font=title_font) for word, _ in words]
    _, t_top, _, t_bottom = draw.textbbox((0, 0), "HISTORY'S LAST HOURS", font=title_font)
    _, g_top, _, g_bottom = draw.textbbox((0, 0), tagline, font=tag_font)
    _, s_top, _, s_bottom = draw.textbbox((0, 0), small, font=small_font)
    gap_title, gap_tag = 34, 30
    block = (t_bottom - t_top) + gap_title + (g_bottom - g_top) + gap_tag + (s_bottom - s_top)
    # Keep everything inside the 1546x423 area that every device shows (centered at y=720).
    assert block <= safe_h - 40 and sum(widths) + word_gap <= safe_w - 80, (block, sum(widths) + word_gap)
    top = h / 2 - block / 2

    x = (w - (sum(widths) + word_gap)) / 2
    for (word, color), word_w in zip(words, widths):
        draw.text((x, top - t_top), word, font=title_font, fill=color)
        x += word_w + word_gap

    tag_y = top + (t_bottom - t_top) + gap_title - g_top
    tag_w = draw.textlength(tagline, font=tag_font)
    draw.text(((w - tag_w) / 2, tag_y), tagline, font=tag_font, fill=WHITE)
    small_y = tag_y + g_bottom + gap_tag - s_top
    small_w = draw.textlength(small, font=small_font)
    draw.text(((w - small_w) / 2, small_y), small, font=small_font, fill=MIST)
    banner.save(out, quality=92)
    return [credit for _, credit in pictures.values()]


def write_credits(credits: list[dict]) -> str:
    lines = ["# Banner image credits", "",
             "Pictures from Wikimedia Commons, checked through the Commons API to be public domain, CC0, or CC BY "
             "(no share-alike, no NonCommercial). The mantis shrimp and octopus photos were cropped; the whale photo "
             "was cropped, tinted, and darkened. The avatar and watermark are original drawings.", ""]
    for c in credits:
        license_text = f"[{c['license']}]({c['license_url']})" if c.get("license_url") else c["license"]
        lines += [f"- **{c['label']}**", f"  - File: {c['title']}", f"  - Author: {c['author']}",
                  f"  - License: {license_text}", f"  - Link: {c['url']}"]
    text = "\n".join(lines) + "\n"
    (BRAND / "CREDITS.md").write_text(text, encoding="utf-8")
    return text


def main() -> None:
    out = BRAND / "out"
    out.mkdir(exist_ok=True)
    make_avatar(out / "avatar-800.png")
    make_watermark(out / "watermark-150.png")
    credits = make_banner(out / "banner-2560x1440.jpg", BRAND / "src")
    print(write_credits(credits))


if __name__ == "__main__":
    main()
