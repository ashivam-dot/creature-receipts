"""An original score written in code for each Short (no samples, so no licence or Content ID claim): a warm pad, a
plucked arpeggio and a soft pulse, curious rather than dramatic. The key and tempo come from the episode id, so
consecutive Shorts don't sound identical."""

from __future__ import annotations

import hashlib

import numpy as np

SR = 48000
# i - VI - III - VII in a minor key, and I - V - vi - IV in a major one.
PROGRESSIONS = [[(57, "m"), (53, "M"), (48, "M"), (55, "M")], [(48, "M"), (55, "M"), (57, "m"), (53, "M")]]


def _hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def _chord(root: int, kind: str) -> list[int]:
    return [root, root + (3 if kind == "m" else 4), root + 7]


def _pluck(f: float, dur: float, vel: float) -> np.ndarray:
    t = np.arange(int(dur * SR)) / SR
    tone = sum((1 / n ** 1.6) * np.sin(2 * np.pi * f * n * t) * np.exp(-t * (3.0 + 2.2 * n)) for n in range(1, 7))
    return (vel * tone * np.minimum(1, t / 0.004)).astype(np.float32)


def _pad(freqs: list[float], dur: float) -> np.ndarray:
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for f in freqs:
        for detune in (-0.1, 0.0, 0.1):
            g = f * 2 ** (detune / 12)
            out += sum((0.6 / n) * np.sin(2 * np.pi * g * n * t + n) for n in range(1, 4))
    env = np.minimum(1, t / 1.0) * np.minimum(1, (dur - t) / 1.0).clip(0, 1)
    return (out * env / (len(freqs) * 3)).astype(np.float32)


def _kick(vel: float) -> np.ndarray:
    t = np.arange(int(0.35 * SR)) / SR
    f = 48 + 90 * np.exp(-t * 30)
    return (vel * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)).astype(np.float32)


def _reverb(x: np.ndarray, seed: int, seconds: float = 2.2, wet: float = 0.3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = rng.standard_normal(n).astype(np.float32) * np.exp(-np.arange(n) / SR * 3.6).astype(np.float32)
    ir /= np.sqrt((ir ** 2).sum())
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[:len(x)].astype(np.float32)
    return (1 - wet) * x + wet * y


def score(seconds: float, seed_text: str) -> np.ndarray:
    """Stereo float32 [n, 2] at 48 kHz, peak at -6 dBFS, with fades."""
    seed = int(hashlib.sha1(seed_text.encode()).hexdigest()[:8], 16)
    shift = [0, 2, -2, 3, -3, 5][seed % 6]
    prog = PROGRESSIONS[(seed >> 4) % 2]
    beat = 60 / (88 + (seed >> 8) % 12)
    bar = 4 * beat
    total = int((seconds + bar + 4) * SR)
    left, right = np.zeros(total, np.float32), np.zeros(total, np.float32)
    rng = np.random.default_rng(seed)

    def add(sig: np.ndarray, at: float, pan: float = 0.5) -> None:
        s = int(at * SR)
        e = min(total, s + len(sig))
        if s < total:
            left[s:e] += (1 - pan) * sig[:e - s]
            right[s:e] += pan * sig[:e - s]

    t0, k = 0.0, 0
    while t0 < seconds + 1:
        root, kind = prog[k % len(prog)]
        notes = [n + shift for n in _chord(root, kind)]
        add(0.55 * _pad([_hz(n - 12) for n in notes], bar + 1.0), t0)
        add(0.5 * _pad([_hz(notes[0] - 24)], bar + 0.5), t0)
        # The arpeggio and pulse come in after the first bar, so the hook lands on a quiet bed.
        if k:
            pattern = [notes[0], notes[2], notes[1] + 12, notes[2], notes[0] + 12, notes[2], notes[1] + 12, notes[2]]
            for i, n in enumerate(pattern):
                add(_pluck(_hz(n + 12), 1.2, 0.16 + 0.05 * rng.random()), t0 + i * beat / 2, 0.5 + 0.3 * np.sin(i))
            for i in range(4):
                add(_kick(0.35 if i % 2 == 0 else 0.2), t0 + i * beat)
        t0 += bar
        k += 1
    left, right = _reverb(left, seed), _reverb(right, seed + 1)
    mix = np.stack([left, right], axis=1)[: int(seconds * SR)]
    fade_in, fade_out = int(0.6 * SR), int(1.5 * SR)
    mix[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    mix[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]
    return (mix / max(np.abs(mix).max(), 1e-6) * 0.5).astype(np.float32)
