"""The YAML contract for one Atlas Short: its dataset, colour scale, and beats, each with a camera shot."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

FORMATS = ("map_reveal", "rank_ladder", "versus", "odd_one_out", "then_now")


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
        return self.value_format.format(v=value)

    @classmethod
    def load(cls, path: Path) -> AtlasEpisode:
        return cls.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))

    def save(self, path: Path) -> None:
        path.write_text(yaml.safe_dump(self.model_dump(exclude_defaults=True), sort_keys=False, allow_unicode=True,
                                       width=110), encoding="utf-8")
