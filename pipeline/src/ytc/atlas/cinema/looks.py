"""One look per story format, so consecutive Shorts don't look alike (owner, 2026-10-27: "in every video show
different style"). A look sets the accent, caption face and height, hook position, photo grade, narrator and score."""
from __future__ import annotations

from dataclasses import dataclass

from ...spec import Voice


@dataclass(frozen=True, eq=False)
class Look:
    name: str
    accent: tuple[int, int, int]
    caption_font: str  # "anton", "sans" (Montserrat Black) or "serif" (DM Serif Display)
    caption_y: float  # caption centre as a share of the frame height
    hook_y: float  # top of the hook title as a share of the frame height
    grade: tuple[float, float, tuple[float, float, float]]  # saturation, contrast, per-channel tint
    voice: Voice
    progression: int  # score.PROGRESSIONS index
    tempo: float  # score pulse in beats per minute


LOOKS = {
    "map_reveal": Look("gold globe", (255, 209, 102), "anton", 0.715, 0.06, (0.96, 1.05, (1.0, 1.0, 1.0)),
                       Voice(engine="kokoro", voice="am_fenrir", speed=1.1, lang_code="a", lead_in=0.25), 0, 96),
    "rank_ladder": Look("red countdown", (255, 84, 92), "sans", 0.66, 0.05, (1.08, 1.1, (1.04, 0.98, 0.96)),
                        Voice(engine="kokoro", voice="am_michael", speed=1.1, lang_code="a", lead_in=0.2), 1, 112),
    "versus": Look("cyan versus", (64, 224, 230), "sans", 0.74, 0.07, (0.9, 1.12, (0.95, 1.0, 1.06)),
                   Voice(engine="kokoro", voice="bm_george", speed=1.08, lang_code="b", lead_in=0.25), 1, 104),
    "odd_one_out": Look("green quiz", (130, 236, 120), "anton", 0.6, 0.1, (1.05, 1.04, (0.98, 1.03, 0.98)),
                        Voice(engine="kokoro", voice="af_heart", speed=1.08, lang_code="a", lead_in=0.25), 0, 120),
    "spotlight": Look("violet spotlight", (190, 150, 255), "serif", 0.72, 0.08, (0.85, 1.02, (1.02, 0.98, 1.05)),
                      Voice(engine="kokoro", voice="bf_emma", speed=1.06, lang_code="b", lead_in=0.3), 0, 84),
}
DEFAULT = LOOKS["map_reveal"]


def look(fmt: str | None) -> Look:
    return LOOKS.get(fmt or "", DEFAULT)
