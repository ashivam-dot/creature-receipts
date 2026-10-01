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

ABYSS = (14, 11, 9)
TEAL = (78, 34, 18)
LIME = (222, 172, 84)
WHITE = (255, 255, 255)
MIST = (226, 206, 170)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = f"HistorysLastHoursBrand/1.0 ({os.environ.get('YTC_CONTACT') or 'aksha.shivam18@gmail.com'})"
# Commons licenses that allow commercial reuse without share-alike or NonCommercial terms.
OPEN_LICENSES = re.compile(r"^(public domain|pd\b.*|cc0.*|cc by \d(\.\d)?|no restrictions)$", re.I)

# name: (Commons file title, download width, display title, author as the source credits it)
PICTURES = {
    "pompeii": ("File:Karl Brullov - The Last Day of Pompeii - Google Art Project.jpg", 3072,
                "The Last Day of Pompeii, Karl Bryullov (1830-1833)", "Karl Bryullov"),
    "titanic": ("File:Stöwer Titanic.jpg", 2400, "Der Untergang der Titanic, Willy Stöwer (1912)", "Willy Stöwer"),
    "hindenburg": ("File:Hindenburg burning.jpg", 2400, "The Hindenburg burning at Lakehurst, New Jersey (1937)",
                   "U.S. Navy"),
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


def _mark(size: int) -> Image.Image:
    """The mark on a transparent square: an hourglass in gold with almost all of its sand run out."""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    cx, cy = size / 2, size / 2
    w, h = size * 0.46, size * 0.64
    top, bottom = cy - h / 2, cy + h / 2
    bar_h, neck, wall = size * 0.05, size * 0.07, size * 0.03
    for y in (top, bottom - bar_h):
        draw.rounded_rectangle([cx - w * 0.62, y, cx + w * 0.62, y + bar_h], radius=bar_h / 2, fill=LIME)
    glass_top, glass_bottom = top + bar_h, bottom - bar_h
    half = w / 2
    outer = [(cx - half, glass_top), (cx + half, glass_top), (cx + neck, cy), (cx + half, glass_bottom),
             (cx - half, glass_bottom), (cx - neck, cy)]
    draw.polygon(outer, fill=LIME)
    inner_half = half - wall
    inner = [(cx - inner_half, glass_top + wall * 0.6), (cx + inner_half, glass_top + wall * 0.6), (cx + neck * 0.3, cy),
             (cx + inner_half, glass_bottom - wall * 0.6), (cx - inner_half, glass_bottom - wall * 0.6),
             (cx - neck * 0.3, cy)]
    draw.polygon(inner, fill=ABYSS)
    # The last of the sand in the top bulb, a thin falling stream, and the pile below.
    chamber = cy - (glass_top + wall * 0.6)
    sand_top = cy - chamber * 0.3
    sand_half = (inner_half - neck * 0.3) * 0.3 + neck * 0.3
    draw.polygon([(cx - sand_half, sand_top), (cx + sand_half, sand_top), (cx + neck * 0.3, cy), (cx - neck * 0.3, cy)],
                 fill=WHITE)
    pile_base = glass_bottom - wall * 0.6
    pile_top = pile_base - chamber * 0.5
    draw.rectangle([cx - size * 0.007, cy, cx + size * 0.007, pile_top + 2], fill=WHITE)
    pile_half = inner_half * 0.9
    draw.polygon([(cx - pile_half, pile_base), (cx + pile_half, pile_base), (cx, pile_top)], fill=WHITE)
    return layer


def _badge(size: int, tilt: float = 0) -> Image.Image:
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

    center = _cover(pictures["pompeii"][0], w, h, (0.5, 0.42))
    arr = np.asarray(center, np.float32)
    # Shift the painting toward ember and sepia so the whole banner shares one palette.
    lum = arr @ np.array([0.30, 0.50, 0.20], np.float32)
    ember = np.array([170, 96, 48], np.float32) * (lum[..., None] / 120)
    arr = arr * 0.35 + ember * 0.65
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # Darken toward the middle so the name reads, keeping the painting visible at the edges.
    focus = np.exp(-(((xx - w / 2) / (safe_w * 0.62)) ** 2 + ((yy - h / 2) / (safe_h * 0.95)) ** 2))
    shade = 0.78 - 0.50 * focus
    abyss = np.array(ABYSS, np.float32)
    arr = arr * shade[..., None] + abyss * (1 - shade[..., None])
    banner = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    # The side pictures stop just outside the mobile crop, so phones see only the name on the painting.
    side_w = (w - safe_w) // 2 - 10
    panels = {
        "left": _band(pictures["titanic"][0], side_w, h, (0.5, 0.5), 1000, ABYSS, band_top=300),
        "right": _band(pictures["hindenburg"][0], side_w, h, (0.5, 0.45), 1000, ABYSS, band_top=300),
    }
    for side, panel in panels.items():
        mask = _torn_mask(side_w, h, side)
        x = 0 if side == "left" else w - side_w
        edge = mask.filter(ImageFilter.MaxFilter(15))
        banner.paste(Image.new("RGB", (side_w, h), LIME), (x, 0), edge)
        banner.paste(panel, (x, 0), mask)

    draw = ImageDraw.Draw(banner)
    title_font = ImageFont.truetype(str(ANTON), 168)
    tag_font = ImageFont.truetype(str(MONTSERRAT_BLACK), 56)
    small_font = ImageFont.truetype(str(MONTSERRAT_XB), 30)
    words = [("HISTORY'S", WHITE), ("LAST HOURS", LIME)]
    tagline = "THE FINAL MOMENTS OF HISTORY'S TRAGEDIES"
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
             "(no share-alike, no NonCommercial). The Titanic painting and Hindenburg photo were cropped; the Pompeii "
             "painting was cropped, tinted, and darkened. The avatar and watermark are original drawings.", ""]
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
