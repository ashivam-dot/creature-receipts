"""Country shapes from Natural Earth's India point-of-view layer, in the Equal Earth projection.

India's law requires its official boundaries on any map shown in India, so every map uses the
`ne_10m_admin_0_countries_ind` layer (public domain). `build_asset` simplifies it once into the compact file
the renderer loads.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np

ASSET = Path(__file__).resolve().parents[3] / "assets" / "atlas" / "countries_ind.json"
SOURCE_URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
              "ne_10m_admin_0_countries_ind.geojson")

# Equal Earth (Šavrič, Patterson, Jenny 2018).
_A1, _A2, _A3, _A4 = 1.340264, -0.081106, 0.000893, 0.003796
_M = math.sqrt(3) / 2


def project(lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    lam, phi = np.radians(lon), np.radians(lat)
    theta = np.arcsin(_M * np.sin(phi))
    t2 = theta * theta
    t6 = t2 * t2 * t2
    x = 2 * math.sqrt(3) * lam * np.cos(theta) / (3 * (9 * _A4 * t6 * t2 + 7 * _A3 * t6 + 3 * _A2 * t2 + _A1))
    y = theta * (_A1 + _A2 * t2 + t6 * (_A3 + _A4 * t2))
    return x, y


# The projected world's extent: x in ±XMAX, y in ±YMAX.
XMAX = float(project(np.array([180.0]), np.array([0.0]))[0][0])
YMAX = float(project(np.array([0.0]), np.array([90.0]))[1][0])


@dataclass
class Country:
    iso3: str
    name: str
    rings: list[np.ndarray]  # projected outer rings and holes, each an (n, 2) array; y points up
    lon: float  # label point
    lat: float
    continent: str

    @property
    def point(self) -> tuple[float, float]:
        x, y = project(np.array([self.lon]), np.array([self.lat]))
        return float(x[0]), float(y[0])

    def bbox(self, main_only: bool = True) -> tuple[float, float, float, float]:
        """The projected box around the country; with `main_only`, around the ring that holds its label point,
        so France frames France rather than France plus French Guiana."""
        rings = self.rings
        if main_only:
            px, py = self.point
            near = min(rings, key=lambda r: 0 if _inside(px, py, r) else 1 + math.dist((px, py), r.mean(axis=0)))
            big = max(rings, key=_area)
            rings = [near] if _area(near) > 0.05 * _area(big) else [big]
        xs = np.concatenate([r[:, 0] for r in rings])
        ys = np.concatenate([r[:, 1] for r in rings])
        return float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())


def _area(ring: np.ndarray) -> float:
    x, y = ring[:, 0], ring[:, 1]
    return abs(float(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))) / 2


def _inside(px: float, py: float, ring: np.ndarray) -> bool:
    x, y = ring[:, 0], ring[:, 1]
    x2, y2 = np.roll(x, -1), np.roll(y, -1)
    cross = ((y > py) != (y2 > py)) & (px < (x2 - x) * (py - y) / np.where(y2 == y, 1e-12, y2 - y) + x)
    return bool(np.count_nonzero(cross) % 2)


def _code(props: dict) -> str:
    """ISO 3166 alpha-3 where Natural Earth has one; it leaves France, Norway and Kosovo at -99."""
    for key in ("ISO_A3", "ISO_A3_EH", "ADM0_A3"):
        value = props.get(key) or ""
        if value and value != "-99":
            return {"KOS": "XKX", "SDS": "SSD"}.get(value, value)
    return props["ADM0_A3"]


def build_asset(source: Path, tolerance: float = 0.03) -> Path:
    """Simplify the 10 m layer to about 2 MB of rings, rounded to 0.01 degree."""
    from shapely.geometry import shape

    data = json.loads(source.read_text(encoding="utf-8"))
    out = []
    for feature in data["features"]:
        props = feature["properties"]
        geom = shape(feature["geometry"]).simplify(tolerance, preserve_topology=True)
        polys = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
        rings = []
        for poly in polys:
            if poly.area < 0.002:
                continue
            for ring in [poly.exterior, *poly.interiors]:
                rings.append([[round(x, 2), round(y, 2)] for x, y in ring.coords])
        if not rings:
            continue
        out.append({"iso3": _code(props), "name": props.get("NAME_EN") or props["NAME"],
                    "continent": props.get("CONTINENT", ""),
                    "lon": props.get("LABEL_X"), "lat": props.get("LABEL_Y"), "rings": rings})
    ASSET.parent.mkdir(parents=True, exist_ok=True)
    ASSET.write_text(json.dumps({"source": SOURCE_URL, "license": "Public domain (Natural Earth)",
                                 "countries": out}, separators=(",", ":")), encoding="utf-8")
    return ASSET


@cache
def world() -> dict[str, Country]:
    data = json.loads(ASSET.read_text(encoding="utf-8"))
    countries: dict[str, Country] = {}
    for c in data["countries"]:
        rings = []
        for ring in c["rings"]:
            arr = np.asarray(ring, dtype=float)
            x, y = project(arr[:, 0], arr[:, 1])
            rings.append(np.column_stack([x, y]))
        if c["iso3"] in countries:
            countries[c["iso3"]].rings.extend(rings)
            continue
        countries[c["iso3"]] = Country(c["iso3"], c["name"], rings, c["lon"], c["lat"], c["continent"])
    return countries
