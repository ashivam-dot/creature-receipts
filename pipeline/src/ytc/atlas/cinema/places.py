"""Real pictures of a country for a cinematic Atlas Short: its flag and photos of the country, its capital and its
largest cities, all from Wikimedia Commons through Wikidata's curated main images.

Only CC0, public-domain, CC BY and CC BY-SA files pass, each kept with its author and licence for the credits. Maps,
logos, flags passed off as photos and anything that suggests injury or grief are skipped: these pictures stand for a
place, so they show the place as its own photographers present it.
"""

from __future__ import annotations

import html
import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from ..data import get

log = logging.getLogger(__name__)

COMMONS = "https://commons.wikimedia.org/w/api.php"
WIKIDATA = "https://www.wikidata.org/w/api.php"
WIKIPEDIA = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "AtlasInNumbers/2.0 (https://github.com/ashivam-dot/creature-receipts)"}
FREE = re.compile(r"^(CC0|Public domain|PD\b|CC BY(-SA)? \d(\.\d)?( [a-z]{2,})?$|CC BY(-SA)?$)", re.I)
NOT_PHOTO = re.compile(r"(\.svg$|\.gif$|\.tiff?$|\blogo|signature|\bmap\b|locator|location|\bflag\b|coat of arms|"
                       r"\bicon\b|\bseal\b|emblem|chart|graph|diagram|insignia|\bplan\b|blank|collage|montage|"
                       r"satellite|from space|\biss\b|orthographic)", re.I)
GRAPHIC = re.compile(r"(corpse|bodies|\bbody\b|victim|blood|wound|injur|\bdead\b|killed|funeral|coffin|wreckage|"
                     r"debris|aftermath|refugee|riot|protest|soldier|army|military|war\b|bomb)", re.I)
MIN_SIDE = 700


@dataclass
class Picture:
    file: str
    url: str
    page: str
    width: int
    height: int
    author: str
    license: str
    description: str
    role: str  # "flag", "country", "capital" or "city"
    place: str  # what it shows, for the caption chip: "N'Djamena", "Chad"
    path: str = ""

    @property
    def credit(self) -> str:
        return f"Photo: {self.author} / {self.license} / Wikimedia Commons"


def _text(value: str | None, limit: int = 200) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()[:limit]


def _info(files: list[str], width: int = 2560) -> dict[str, dict]:
    out = {}
    for i in range(0, len(files), 40):
        d = get(COMMONS, params={"action": "query", "titles": "|".join(files[i:i + 40]), "prop": "imageinfo",
                                 "iiurlwidth": width, "iiprop": "url|size|mime|extmetadata", "format": "json",
                                 "formatversion": 2, "redirects": 1}, headers=HEADERS, timeout=60).json()
        for p in d["query"].get("pages", []):
            if not p.get("missing") and p.get("imageinfo"):
                out[p["title"]] = p["imageinfo"][0]
        for r in d["query"].get("normalized", []) + d["query"].get("redirects", []):
            if r["to"] in out:
                out[r["from"]] = out[r["to"]]
    return out


def _picture(file: str, info: dict, role: str, place: str) -> Picture | None:
    meta = info.get("extmetadata", {})
    lic = _text(meta.get("LicenseShortName", {}).get("value"), 60)
    desc = _text(meta.get("ImageDescription", {}).get("value"), 300)
    if not FREE.match(lic):
        return None
    if role != "flag":
        if NOT_PHOTO.search(file) or GRAPHIC.search(file + " " + desc):
            return None
        if min(info.get("width", 0), info.get("height", 0)) < MIN_SIDE or info.get("mime") != "image/jpeg":
            return None
    author = _text(meta.get("Artist", {}).get("value"), 80) or "Unknown author"
    return Picture(file=file, url=info.get("thumburl") or info["url"], page=info.get("descriptionurl", ""),
                   width=info.get("width", 0), height=info.get("height", 0), author=author, license=lic,
                   description=desc, role=role, place=place)


def _entities(ids: list[str]) -> dict:
    d = get(WIKIDATA, params={"action": "wbgetentities", "ids": "|".join(ids), "props": "claims|labels|sitelinks",
                              "languages": "en", "sitefilter": "enwiki", "format": "json"},
            headers=HEADERS, timeout=60).json()
    return d.get("entities", {})


def _claims(ent: dict, prop: str) -> list:
    """Current values only (no end time), preferred rank first: P36 also lists a country's former capitals."""
    out = []
    for c in ent.get("claims", {}).get(prop, []):
        if c.get("rank") == "deprecated" or "P582" in c.get("qualifiers", {}):
            continue
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if v is not None:
            out.append((c.get("rank") != "preferred", v["id"] if isinstance(v, dict) and "id" in v else v))
    return [v for _, v in sorted(out, key=lambda x: x[0])]


def _article_files(title: str) -> list[str]:
    d = get(WIKIPEDIA, params={"action": "parse", "page": title, "prop": "images", "redirects": 1, "format": "json",
                               "formatversion": 2}, headers=HEADERS, timeout=60).json()
    return ["File:" + f.replace("_", " ") for f in d.get("parse", {}).get("images", [])]


def lookup(iso3: str) -> dict:
    """The country's flag file and main image, its capital's image, and the photos of the capital's Wikipedia
    article, from Wikidata's entity API (its query service is too slow to rely on)."""
    hits = get(WIKIDATA, params={"action": "query", "list": "search", "srsearch": f"haswbstatement:P298={iso3}",
                                 "srlimit": 3, "format": "json"}, headers=HEADERS, timeout=60).json()
    out = {"iso3": iso3, "name": "", "flag": "", "country": [], "capital": [], "cities": []}
    qids = [h["title"] for h in hits.get("query", {}).get("search", [])]
    if not qids:
        return out
    ent = _entities(qids[:1])[qids[0]]
    out["name"] = ent.get("labels", {}).get("en", {}).get("value", "")
    flags = _claims(ent, "P41")
    out["flag"] = "File:" + flags[0] if flags else ""
    out["country"] = ["File:" + f for f in _claims(ent, "P18")[:2]]
    caps = _claims(ent, "P36")[:1]
    if caps:
        cap = _entities(caps)[caps[0]]
        name = cap.get("labels", {}).get("en", {}).get("value", "")
        out["capital"] = [(name, "File:" + f) for f in _claims(cap, "P18")[:1]]
        title = cap.get("sitelinks", {}).get("enwiki", {}).get("title")
        if title:
            try:
                out["cities"] = [(name, f) for f in _article_files(title)[:30]]
            except Exception as err:
                log.warning("no article images for %s: %s", title, err)
    return out


def _stem(file: str) -> str:
    """Commons keeps edited copies beside originals ("X (revised).jpg", "X 2.jpg"): one stem per photo."""
    name = re.sub(r"\.[a-z]+$", "", file.lower())
    return re.sub(r"\([^)]*\)|[\d\s_\-,.]+", "", name)


def gather(iso3: str, cache: Path, photos: int = 2) -> dict:
    """The flag and up to `photos` photos of the country, downloaded into cache/<iso3>/ (reused when present)."""
    folder = cache / iso3
    meta_path = folder / "places.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    folder.mkdir(parents=True, exist_ok=True)
    found = lookup(iso3)
    name = found["name"] or iso3
    wanted = [(found["flag"], "flag", name)] if found["flag"] else []
    wanted += [(f, "capital", place) for place, f in found["capital"]]
    wanted += [(f, "country", name) for f in found["country"]]
    wanted += [(f, "city", place) for place, f in found["cities"]]
    infos = _info([f for f, _, _ in wanted])
    flag_info = _info([found["flag"]], width=640) if found["flag"] else {}
    flag, chosen = None, []
    for f, role, place in wanted:
        info = (flag_info if role == "flag" else infos).get(f)
        if not info:
            continue
        pic = _picture(f, info, role, place)
        if pic is None:
            continue
        if role == "flag":
            flag = flag or pic
        elif len(chosen) < photos and _stem(pic.file) not in [_stem(c.file) for c in chosen]:
            chosen.append(pic)
    for i, pic in enumerate(([flag] if flag else []) + chosen):
        suffix = ".png" if pic.role == "flag" else ".jpg"
        path = folder / (f"flag{suffix}" if pic.role == "flag" else f"photo{i}{suffix}")
        path.write_bytes(get(pic.url, headers=HEADERS, timeout=120).content)
        pic.path = str(path)
    meta = {"iso3": iso3, "name": name, "flag": asdict(flag) if flag else None,
            "photos": [asdict(p) for p in chosen]}
    meta_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    return meta


def credit(pic: dict) -> str:
    return f"Photo: {pic['author']} / {pic['license']} / Wikimedia Commons"
