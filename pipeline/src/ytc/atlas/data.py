"""Open datasets an Atlas Short is drawn from, fetched once and kept beside the episode as its receipt."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import requests

WB_API = "https://api.worldbank.org/v2"
OWID_GRAPHER = "https://ourworldindata.org/grapher"
TIMEOUT = 60


@dataclass
class Dataset:
    """One value per country (ISO 3166 alpha-3), with the year each value is for."""

    label: str
    unit: str
    source: str  # who publishes it, as shown on screen
    license: str
    url: str
    values: dict[str, float]
    years: dict[str, int]
    names: dict[str, str] = field(default_factory=dict)
    fetched: str = ""

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.__dict__, indent=1, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> Dataset:
        return cls(**json.loads(path.read_text(encoding="utf-8")))

    def ranked(self, reverse: bool = True) -> list[tuple[str, float]]:
        return sorted(self.values.items(), key=lambda kv: kv[1], reverse=reverse)

    @property
    def year(self) -> int:
        """The year most values are for."""
        counts: dict[int, int] = {}
        for y in self.years.values():
            counts[y] = counts.get(y, 0) + 1
        return max(counts, key=counts.get) if counts else 0


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _wb_countries() -> dict[str, str]:
    rows = requests.get(f"{WB_API}/country", params={"format": "json", "per_page": 400}, timeout=TIMEOUT).json()[1]
    return {r["id"]: r["name"] for r in rows if r["region"]["id"] != "NA"}


def worldbank(indicator: str, label: str, unit: str, source: str, min_year: int) -> Dataset:
    """The latest value since `min_year` for every country (aggregates such as "World" are dropped)."""
    names = _wb_countries()
    resp = requests.get(f"{WB_API}/country/all/indicator/{indicator}",
                        params={"format": "json", "per_page": 20000, "mrnev": 1}, timeout=TIMEOUT)
    resp.raise_for_status()
    values, years = {}, {}
    for row in resp.json()[1] or []:
        iso, value = row["countryiso3code"], row["value"]
        if iso in names and value is not None and int(row["date"]) >= min_year:
            values[iso], years[iso] = float(value), int(row["date"])
    return Dataset(label, unit, source, "CC BY 4.0", f"https://data.worldbank.org/indicator/{indicator}",
                   values, years, {k: names[k] for k in values}, _now())


def owid(slug: str, column: str, label: str, unit: str, source: str, min_year: int) -> Dataset:
    """The latest value since `min_year` per country from an Our World in Data chart."""
    url = f"{OWID_GRAPHER}/{slug}.csv"
    resp = requests.get(url, params={"v": 1, "csvType": "full", "useColumnShortNames": "true"},
                        headers={"User-Agent": "atlas-in-numbers/1.0"}, timeout=TIMEOUT)
    resp.raise_for_status()
    values, years, names = {}, {}, {}
    for row in csv.DictReader(io.StringIO(resp.text)):
        code, year, value = row.get("code") or row.get("Code") or "", row.get("year") or row.get("Year"), row.get(column)
        if len(code) != 3 or not value or int(year) < min_year:
            continue
        if code not in years or int(year) > years[code]:
            values[code], years[code], names[code] = float(value), int(year), row.get("entity") or row.get("Entity")
    return Dataset(label, unit, source, "CC BY 4.0", f"https://ourworldindata.org/grapher/{slug}",
                   values, years, names, _now())


def fetch(spec: dict) -> Dataset:
    kind = spec["kind"]
    common = dict(label=spec["label"], unit=spec.get("unit", ""), source=spec["source"],
                  min_year=int(spec.get("min_year", 2018)))
    if kind == "worldbank":
        return worldbank(spec["indicator"], **common)
    if kind == "owid":
        return owid(spec["slug"], spec["column"], **common)
    raise ValueError(f"unknown dataset kind: {kind}")
