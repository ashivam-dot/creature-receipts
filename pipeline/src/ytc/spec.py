"""The YAML contract for one Short: narration beats, visuals, voice, captions, and metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Motion = Literal["zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down", "none"]
# "url" is a picture chosen by eye and fetched as is (credit included); "card" is a designed title card.
Source = Literal["commons", "met", "aic", "nasa", "pexels", "pixabay", "ai", "file", "color", "url", "card"]


class _Model(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True, extra="forbid")


class Card(_Model):
    """A designed title card for a line no picture can show: a date and place, a number, or a quote."""

    kind: Literal["dateline", "fact", "quote"] = "fact"
    big: str
    small: str = ""


class Visual(_Model):
    source: Source = "color"
    fallbacks: list[Source] = []
    query: str | None = None
    prompt: str | None = None
    path: str | None = None
    url: str | None = None
    # For a "url" picture: source, title, credit (the author), license, and url (the picture's page).
    credit: dict[str, str | None] = {}
    # Short, visible provenance note for a reconstruction, later artwork, or illustrative image.
    label: str = ""
    card: Card | None = None
    color: str = "#101820"
    motion: Motion = "zoom_in"
    # Which part of the image the vertical crop keeps: 0 is the left or top edge, 1 the right or bottom.
    focus_x: float = Field(0.5, ge=0, le=1)
    focus_y: float = Field(0.5, ge=0, le=1)
    # The part of the picture that shows exactly what the line names (left, top, right, bottom, each 0 to 1):
    # a long beat cuts to it for a second, closer shot.
    box: list[float] = []
    # The only part of the picture to use (left, top, right, bottom, each 0 to 1), e.g. one tall scene from a wide
    # painting so it fills the screen; focus and box then refer to this part.
    crop: list[float] = []
    # Show an earlier beat's image again (1 is the first beat), e.g. for the loop line.
    reuse: int | None = None

    @model_validator(mode="after")
    def _box_is_a_box(self) -> Visual:
        for name in ("box", "crop"):
            b = getattr(self, name)
            if b and not (len(b) == 4 and 0 <= b[0] < b[2] <= 1 and 0 <= b[1] < b[3] <= 1):
                raise ValueError(f"visual.{name} must be [left, top, right, bottom] within 0 to 1, got {b}")
        return self


class Beat(_Model):
    text: str
    visual: Visual = Field(default_factory=Visual)
    emphasis: list[str] = []
    sfx: Literal["whoosh", "pop", "riser", "none"] = "none"
    pause_after: float = 0.12
    # Where this line's captions sit (0 is the top of the frame, 1 the bottom), for a picture with a face where
    # they would otherwise go; empty keeps the caption style's height.
    caption_y: float | None = Field(None, ge=0.15, le=0.85)


class Voice(_Model):
    engine: Literal["kokoro", "gemini"] = "kokoro"
    # A Kokoro voice, or a Gemini TTS voice name such as "Algenib".
    voice: str = "af_heart"
    speed: float = 1.0
    # Kokoro's language code; "h" is Hindi.
    lang_code: str = "a"
    # Gemini only: the TTS model (empty: the newest that answers), and performance notes in English, which it
    # follows without reading them out.
    model: str = ""
    direction: str = ""
    # Seconds before the first word. A Reel needs enough for its cover frame to show the hook before any caption.
    lead_in: float = Field(0.08, ge=0, le=1)


class Music(_Model):
    # A file beside the spec, or "tanpura" for the drone the pipeline synthesizes (drone.py).
    path: str | None = None
    gain_db: float = -24.0


class CaptionStyle(_Model):
    font: str = "Montserrat Black"
    font_file: str = "Montserrat-Black.ttf"
    size: int = 128
    # Clear of the Shorts player's like and comment buttons down the right edge.
    max_width: float = 0.74
    primary: str = "#FFFFFF"
    highlight: str = "#FFD400"
    accent: str = "#00E5FF"
    outline: int = 9
    words_per_line: int = 3
    uppercase: bool = True
    y: float = 0.60
    # The on-screen hook's font; Anton has no Devanagari, so Hindi Reels name one that does.
    hook_font: str = "Anton"
    hook_font_file: str = "Anton-Regular.ttf"
    hook_size: int = 112
    # The top of the hook's box, as a fraction of the height: lower it when the first picture has a face near the top.
    hook_y: float = Field(0.15, ge=0.08, le=0.5)


class ShortSpec(_Model):
    id: str
    title: str
    series: str | None = None
    description: str = ""
    # A few words on screen over the first beat, a teaser that adds to the spoken hook.
    hook_text: str = ""
    sources: list[str] = []
    hashtags: list[str] = []
    tags: list[str] = []
    category_id: str = "27"
    synthetic_media: bool = False
    # Pictures that fill the screen move in depth (depth.py), near parts against far ones. Needs torch and
    # transformers, which the YouTube studio's image doesn't have.
    depth_motion: bool = False
    voice: Voice = Field(default_factory=Voice)
    music: Music = Field(default_factory=Music)
    captions: CaptionStyle = Field(default_factory=CaptionStyle)
    beats: list[Beat]

    @model_validator(mode="after")
    def _reuse_points_back(self) -> ShortSpec:
        for number, beat in enumerate(self.beats, start=1):
            reuse = beat.visual.reuse
            if reuse is not None and not 1 <= reuse < number:
                raise ValueError(f"beat {number}: visual.reuse must name an earlier beat (1 to {number - 1})")
        return self

    @classmethod
    def load(cls, path: Path) -> ShortSpec:
        return cls.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))
