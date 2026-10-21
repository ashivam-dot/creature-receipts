"""The YAML contract for one Atlas Short: its dataset, colour scale, and beats, each with a camera shot."""

from __future__ import annotations

import re
import string
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

FORMATS = ("map_reveal", "rank_ladder", "versus", "odd_one_out", "then_now")
_DIGITS = re.compile(r"\d[\d,]*(?:\.\d+)?")
# Decimals a value keeps: 3 significant figures, and 1 decimal for a percentage. Whisper writes "5.0%" as "5%" and
# "70.5202%" as "70.520%", so the narrator must never be asked to say more than a person would (2026-10-21).
SIGNIFICANT = 3
PERCENT_DECIMALS = 1
# Decimals a value may grow to so that it never reads as 0 or as a full 100%.
MAX_DECIMALS = 10


def _field(fmt: str) -> tuple[str, str, str] | None:
    """(text before, format spec, text after) of fmt's single {v} field, or None for any other shape."""
    try:
        parts = list(string.Formatter().parse(fmt))
    except ValueError:
        return None
    fields = [i for i, p in enumerate(parts) if p[1] is not None]
    if len(fields) != 1 or parts[fields[0]][1] != "v" or parts[fields[0]][3] or "{" in (parts[fields[0]][2] or ""):
        return None
    i = fields[0]
    head = "".join(p[0] for p in parts[:i + 1])
    tail = "".join(p[0] for p in parts[i + 1:])
    return head, parts[i][2] or "", tail


def say_value(value: float, fmt: str) -> str:
    """fmt's text for value, as a person says it on screen and aloud: no trailing zeros ("5.0%" is "5%", "0.80%"
    is "0.8%"), at most 3 significant figures in the decimals and 1 decimal for a percentage. A nonzero value keeps
    the decimals it needs to show its first figure, and its sign ("0.01%", "-0.04%"), and a share short of 100
    the decimals that keep it short of 100 ("99.99%"): never "0.0", "0.000" or a rounded-up "100%", and never a
    word such as "under" that the number checks can't see. Whole digits are never rounded away ("3,947" stays).
    Only the {v} field is rewritten, never a digit in the unit ("CO2 5.3 t", "per 100,000")."""
    text = fmt.format(v=value)
    field = _field(fmt)
    if field is None or not isinstance(value, (int, float)) or field[1].endswith("%"):
        return text
    head, spec, tail = field
    number = format(value, spec)
    m = _DIGITS.search(number)
    if not m:
        return text
    head, tail = head + number[:m.start()], number[m.end():] + tail
    shown = len(m.group(0).partition(".")[2])
    magnitude = abs(value)
    whole = len(str(int(magnitude))) if magnitude >= 1 else 0
    if whole:
        decimals = max(0, SIGNIFICANT - whole)
    else:
        # 0.0143 keeps 0.0143: the zeros after the point, then 3 figures.
        lead = len(f"{magnitude:.12f}".partition(".")[2]) - len(f"{magnitude:.12f}".partition(".")[2].lstrip("0"))
        decimals = lead + SIGNIFICANT
    percent = "%" in text
    if percent:
        decimals = min(decimals, PERCENT_DECIMALS)
    decimals = min(decimals, shown)
    group = "," if "," in spec else ""

    def said(d: int) -> str:
        out = f"{magnitude:{group}.{d}f}"
        return out.rstrip("0").rstrip(".") if "." in out else out

    while decimals < MAX_DECIMALS and (
            (value and not re.search(r"[1-9]", said(decimals)))
            or (percent and 0 < value < 100 and float(said(decimals).replace(",", "")) >= 100)):
        decimals += 1
    return f"{head}{said(decimals)}{tail}"


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DatasetSpec(_Model):
    kind: Literal["worldbank", "owid"]
    indicator: str = ""  # World Bank
    slug: str = ""  # OWID grapher chart
    column: str = ""
    label: str  # shown in the chip, e.g. "Mobile subscriptions per 100 people"
    unit: str = ""
    source: str  # shown on screen, e.g. "ITU via World Bank"
    min_year: int = 2018


class ScaleSpec(_Model):
    kind: Literal["threshold", "bins"] = "bins"
    at: float = 0.0
    edges: list[float] = []
    labels: list[str] = []

    @model_validator(mode="after")
    def _valid_scale(self):
        import math
        if not math.isfinite(self.at) or any(not math.isfinite(v) for v in self.edges):
            raise ValueError("scale contains non-finite limits")
        if self.kind == "bins" and (self.edges != sorted(set(self.edges)) or
                                   self.labels and len(self.labels) != len(self.edges) + 1):
            raise ValueError("bin limits must be unique/ascending with one label per bin")
        if self.kind == "threshold" and self.labels and len(self.labels) != 2:
            raise ValueError("a threshold has exactly two labels")
        return self


class Shot(_Model):
    kind: Literal["world", "country", "group", "region", "rank", "card"] = "world"
    iso: str = ""
    isos: list[str] = []
    box: list[float] = []  # lon0, lat0, lon1, lat1 for a region
    callouts: list[str] = []  # countries labelled with their value; defaults to the shot's countries
    lines: list[str] = []  # for a card: big line first, then smaller ones
    pad: float = 0.0  # extra framing room; 0 uses the default


class AtlasBeat(_Model):
    text: str
    shot: Shot = Field(default_factory=Shot)
    pause_after: float = 0.15


class AtlasEpisode(_Model):
    id: str
    title: str
    format: Literal[FORMATS] = "map_reveal"  # type: ignore[valid-type]
    series: str = ""
    hook_text: str = ""
    description: str = ""
    hashtags: list[str] = []
    sources: list[str] = []
    dataset: DatasetSpec
    scale: ScaleSpec = Field(default_factory=ScaleSpec)
    value_format: str = "{v:,.0f}"
    beats: list[AtlasBeat]

    @model_validator(mode="after")
    def _shots_name_countries(self) -> AtlasEpisode:
        for n, beat in enumerate(self.beats, start=1):
            s = beat.shot
            if s.kind == "country" and not s.iso:
                raise ValueError(f"beat {n}: a country shot needs iso")
            if s.kind == "group" and not s.isos:
                raise ValueError(f"beat {n}: a group shot needs isos")
            if s.kind == "rank" and not 3 <= len(s.isos) <= 6:
                raise ValueError(f"beat {n}: a rank shot needs 3-6 isos")
            if s.kind == "region" and len(s.box) != 4:
                raise ValueError(f"beat {n}: a region shot needs box [lon0, lat0, lon1, lat1]")
        return self

    def value_text(self, value: float) -> str:
        return say_value(value, self.value_format)

    @classmethod
    def load(cls, path: Path) -> AtlasEpisode:
        return cls.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))

    def save(self, path: Path) -> None:
        path.write_text(yaml.safe_dump(self.model_dump(exclude_defaults=True), sort_keys=False, allow_unicode=True,
                                       width=110), encoding="utf-8")
