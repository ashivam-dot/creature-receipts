"""A soft synthesized pad under the narration, so no music licence or Content ID claim can arise."""

from __future__ import annotations

import numpy as np

SAMPLE_RATE = 48000
# A minor, F, C, G: calm and slightly curious. Each chord is root, third, fifth, an octave up.
CHORDS = [(220.0, 261.63, 329.63, 440.0), (174.61, 220.0, 261.63, 349.23),
          (196.0, 261.63, 329.63, 392.0), (196.0, 246.94, 293.66, 392.0)]


def pad(seconds: float, bar: float = 4.0, seed: int = 5) -> np.ndarray:
    n = int(seconds * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    out = np.zeros(n, dtype=np.float64)
    rng = np.random.default_rng(seed)
    starts = np.arange(0.0, seconds, bar)
    for i, start in enumerate(starts):
        chord = CHORDS[i % len(CHORDS)]
        a, b = int(start * SAMPLE_RATE), min(int((start + bar * 1.5) * SAMPLE_RATE), n)
        tt = t[a:b] - start
        env = np.minimum(tt / 1.2, 1.0) * np.clip((bar * 1.5 - tt) / 1.6, 0.0, 1.0)
        for f in chord:
            detune = 1 + rng.uniform(-0.002, 0.002)
            out[a:b] += env * (np.sin(2 * np.pi * f * detune * tt) + 0.25 * np.sin(4 * np.pi * f * detune * tt))
    shimmer = 0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t)
    out *= shimmer
    peak = np.abs(out).max() or 1.0
    return (out / peak).astype(np.float32)
