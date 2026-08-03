"""Soft sound effects generated as WAVs and played via QSoundEffect."""
from __future__ import annotations

import math
import os
import struct
import wave

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

from app.config import DATA_DIR

SOUNDS_DIR = os.path.join(DATA_DIR, "sounds")
SOUNDS_VERSION = 2

_TONES = {
    # name: (frequency Hz, duration ms, amplitude) blips played in sequence
    "move": ((740, 55, 0.16),),
    "opponent": ((560, 55, 0.16),),
    "good": ((1046, 80, 0.13), (1318, 110, 0.13)),
    "bad": ((150, 150, 0.18),),
}


def _write_wav(path: str, blips: tuple[tuple[int, int, float], ...]) -> None:
    rate = 22050
    total_ms = sum(ms for _, ms, _ in blips)
    total = int(rate * total_ms / 1000)
    samples = [0.0] * total
    pos = 0
    for freq, ms, amp in blips:
        n = int(rate * ms / 1000)
        fade = int(rate * 0.006)
        for i in range(n):
            env = min(1.0, i / fade) if fade else 1.0
            env *= math.exp(-4.5 * i / n)
            t = i / rate
            samples[pos + i] += amp * env * (
                math.sin(2 * math.pi * freq * t)
                + 0.2 * math.sin(2 * math.pi * 2 * freq * t))
        pos += n
    peak = max(1e-9, max(abs(s) for s in samples))
    scale = min(1.0, 0.9 / peak)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        for s in samples:
            w.writeframes(struct.pack("<h", int(s * scale * 32767)))


def _ensure_sounds() -> None:
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    version_file = os.path.join(SOUNDS_DIR, ".version")
    try:
        with open(version_file) as fh:
            current = int(fh.read().strip())
    except (OSError, ValueError):
        current = 0
    if current == SOUNDS_VERSION:
        return
    for name, blips in _TONES.items():
        _write_wav(os.path.join(SOUNDS_DIR, f"{name}.wav"), blips)
    with open(version_file, "w") as fh:
        fh.write(str(SOUNDS_VERSION))


class SoundPlayer:
    """Lazy-loaded QSoundEffect instances for the game events."""

    def __init__(self):
        self.enabled = True
        self._effects: dict[str, QSoundEffect] = {}

    def _effect(self, name: str) -> QSoundEffect | None:
        if name not in self._effects:
            path = os.path.join(SOUNDS_DIR, f"{name}.wav")
            if not os.path.exists(path):
                return None
            eff = QSoundEffect()
            eff.setSource(QUrl.fromLocalFile(path))
            eff.setVolume(0.6)
            self._effects[name] = eff
        return self._effects[name]

    def play(self, name: str) -> None:
        if not self.enabled:
            return
        eff = self._effect(name)
        if eff is not None:
            eff.play()


def init() -> SoundPlayer:
    _ensure_sounds()
    return SoundPlayer()
