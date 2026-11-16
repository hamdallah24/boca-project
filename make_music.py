#!/usr/bin/env python3
"""Original BOCA music + SFX engine (100% self-made, no copyright risk).

Everything here is synthesised from scratch with numpy:
- a warm looping bed (pad + bass + marimba arp + shaker) that follows the
  story beats of the episode
- short SFX one-shots (pop, whoosh, sparkle, chime, boing)
- final mix with voice ducking so the narration always sits on top

Output is 48 kHz stereo PCM WAV.
"""
from __future__ import annotations

import json
import math
import wave
from pathlib import Path

import numpy as np

SR = 48000
BPM = 92
BEAT = 60.0 / BPM
BAR = 4 * BEAT

# I - vi - IV - V in C, warm and curious
CHORDS = [
    (130.81, [261.63, 329.63, 392.00], [523.25, 659.25, 783.99, 1046.50]),
    (110.00, [220.00, 261.63, 329.63], [440.00, 523.25, 659.25, 880.00]),
    (87.31, [174.61, 220.00, 261.63], [349.23, 440.00, 523.25, 698.46]),
    (98.00, [196.00, 246.94, 293.66], [392.00, 493.88, 587.33, 783.99]),
]


def _env_ar(n: int, attack: float, release: float) -> np.ndarray:
    a = max(1, int(attack * SR))
    r = max(1, int(release * SR))
    e = np.ones(n, dtype=np.float32)
    a = min(a, n)
    e[:a] = np.linspace(0.0, 1.0, a) ** 1.6
    r = min(r, n)
    e[-r:] = np.linspace(1.0, 0.0, r) ** 1.8
    return e


def _pad(freqs: list[float], dur: float, amp: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sig = np.zeros(n, dtype=np.float32)
    for i, f in enumerate(freqs):
        sig += np.sin(2 * math.pi * f * t + i * 0.9).astype(np.float32)
        sig += 0.45 * np.sin(2 * math.pi * f * 1.004 * t + i * 1.3).astype(np.float32)
        sig += 0.18 * np.sin(2 * math.pi * f * 2.01 * t).astype(np.float32)
    sig /= len(freqs)
    return sig * _env_ar(n, 0.45, 0.55) * amp


def _pluck(freq: float, dur: float, amp: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = np.exp(-t * 7.0).astype(np.float32)
    sig = (np.sin(2 * math.pi * freq * t)
           + 0.32 * np.sin(2 * math.pi * freq * 2.0 * t)
           + 0.10 * np.sin(2 * math.pi * freq * 3.0 * t)).astype(np.float32)
    return sig * env * amp


def _bass(freq: float, dur: float, amp: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = (1 - np.exp(-t * 14.0)).astype(np.float32) * np.exp(-t * 1.6).astype(np.float32)
    sig = (np.sin(2 * math.pi * freq * t) + 0.22 * np.sin(2 * math.pi * freq * 2 * t)).astype(np.float32)
    return sig * env * amp


def _shaker(amp: float) -> np.ndarray:
    n = int(0.075 * SR)
    rng = np.random.default_rng(7)
    noise = rng.standard_normal(n).astype(np.float32)
    # crude high-pass: difference filter
    noise = noise - np.concatenate([np.zeros(1, np.float32), noise[:-1]])
    env = np.exp(-np.arange(n, dtype=np.float32) / SR * 55.0)
    return noise * env * amp


def build_music(total: float, intensity: float = 1.0) -> np.ndarray:
    """Return (n, 2) float32 stereo music bed for `total` seconds."""
    n_total = int(total * SR)
    left = np.zeros(n_total, dtype=np.float32)
    right = np.zeros(n_total, dtype=np.float32)
    rng = np.random.default_rng(11)

    n_chords = int(math.ceil(total / (BAR * 2))) + 1
    for ci in range(n_chords):
        root, padf, arpf = CHORDS[ci % len(CHORDS)]
        start = ci * BAR * 2
        if start >= total:
            break
        dur = min(BAR * 2, total - start)
        # section energy: soft intro, full middle, gentle outro
        prog = start / max(total, 1e-6)
        if prog < 0.10:
            energy = 0.45 + 0.55 * (prog / 0.10)
        elif prog < 0.78:
            energy = 1.0
        else:
            energy = max(0.25, 1.0 - (prog - 0.78) / 0.22 * 0.75)
        energy *= intensity

        # pad
        pad = _pad(padf, dur, 0.16 * energy)
        s = int(start * SR)
        e = min(n_total, s + len(pad))
        if e > s:
            seg = pad[: e - s]
            left[s:e] += seg * 0.92
            right[s:e] += seg * 1.0

        # bass (root, two bars)
        bass = _bass(root, dur, 0.17 * energy)
        e = min(n_total, s + len(bass))
        if e > s:
            seg = bass[: e - s]
            left[s:e] += seg
            right[s:e] += seg

        # marimba arpeggio on 8ths
        step = BEAT / 2
        idx = 0
        t = 0.0
        while t < dur:
            note = arpf[idx % len(arpf)]
            if (idx // len(arpf)) % 2 == 1:
                note *= 1.5
            amp = 0.085 * energy * (0.75 + 0.25 * rng.random())
            pl = _pluck(note, 0.42, amp)
            ps = int((start + t) * SR)
            pe = min(n_total, ps + len(pl))
            if pe > ps:
                seg = pl[: pe - ps]
                pan = 0.35 if idx % 2 == 0 else -0.35
                left[ps:pe] += seg * (1 - max(0.0, pan))
                right[ps:pe] += seg * (1 + min(0.0, pan))
            t += step
            idx += 1

        # shaker on offbeats, only in the fuller part
        if 0.12 < prog < 0.9:
            t = BEAT
            while t < dur:
                sh = _shaker(0.035 * energy)
                ps = int((start + t) * SR)
                pe = min(n_total, ps + len(sh))
                if pe > ps:
                    seg = sh[: pe - ps]
                    left[ps:pe] += seg * 0.8
                    right[ps:pe] += seg
                t += BEAT

    # gentle stereo widening on the pad
    width = 0.06
    mid = (left + right) * 0.5
    side = (left - right) * width
    left = mid + side
    right = mid - side

    # soft limiter
    peak = float(np.max(np.abs(left))) if n_total else 0.0
    if peak > 0.98:
        left *= 0.98 / peak
        right *= 0.98 / peak
    return np.stack([left, right], axis=1)


def _pop(sr: int = SR) -> np.ndarray:
    n = int(0.22 * sr)
    t = np.arange(n) / sr
    f = 520 + 480 * (t / (n / sr))
    sig = np.sin(2 * math.pi * np.cumsum(f) / sr)
    env = np.exp(-t * 16.0)
    rng = np.random.default_rng(3)
    click = rng.standard_normal(n) * np.exp(-t * 180.0) * 0.25
    return ((sig * env) + click).astype(np.float32) * 0.8


def _whoosh(sr: int = SR) -> np.ndarray:
    n = int(0.75 * sr)
    rng = np.random.default_rng(5)
    noise = rng.standard_normal(n).astype(np.float32)
    # sweeping low-pass -> band-pass feel
    k = 40
    kernel = np.ones(k, dtype=np.float32) / k
    out = np.convolve(noise, kernel, mode="same")
    out = out / (np.max(np.abs(out)) + 1e-6)
    t = np.arange(n) / sr
    env = np.sin(np.pi * np.clip(t / (n / sr), 0, 1)) ** 2
    return (out * env).astype(np.float32) * 0.55


def _sparkle(sr: int = SR) -> np.ndarray:
    parts = []
    for i, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
        n = int(0.30 * sr)
        t = np.arange(n) / sr
        env = np.exp(-t * 11.0)
        sig = (np.sin(2 * math.pi * f * t) + 0.3 * np.sin(2 * math.pi * f * 2 * t)).astype(np.float32)
        seg = sig * env * 0.32
        parts.append((i * 0.075, seg))
    total = int(0.75 * sr)
    out = np.zeros(total, dtype=np.float32)
    for off, seg in parts:
        s = int(off * sr)
        e = min(total, s + len(seg))
        if e > s:
            out[s:e] += seg[: e - s]
    return out


def _chime(sr: int = SR) -> np.ndarray:
    n = int(1.6 * sr)
    t = np.arange(n) / sr
    sig = np.zeros(n, dtype=np.float32)
    for f, a, d in [(523.25, 1.0, 1.6), (784.0, 0.55, 2.1), (1046.5, 0.3, 2.8)]:
        sig += (a * np.sin(2 * math.pi * f * t) * np.exp(-t * d)).astype(np.float32)
    return sig * 0.45


def _boing(sr: int = SR) -> np.ndarray:
    n = int(0.45 * sr)
    t = np.arange(n) / sr
    dur = n / sr
    f = 420 * np.exp(-t * 4.2) + 150
    sig = np.sin(2 * math.pi * np.cumsum(f) / sr + np.sin(2 * math.pi * 18 * t) * 0.4)
    env = np.exp(-t * 5.5)
    return (sig * env).astype(np.float32) * 0.5


SFX = {
    "pop": _pop,
    "whoosh": _whoosh,
    "sparkle": _sparkle,
    "chime": _chime,
    "boing": _boing,
}


def build_sfx(name: str) -> np.ndarray:
    if name not in SFX:
        raise ValueError(f"unknown sfx: {name}")
    return SFX[name]().astype(np.float32)


def read_wav_mono(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        n_ch = w.getnchannels()
        sw = w.getsampwidth()
        sr = w.getframerate()
        raw = w.readframes(w.getnframes())
    if sw == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sw == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        data = np.frombuffer(raw, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0
    if n_ch > 1:
        data = data.reshape(-1, n_ch).mean(axis=1)
    return data, sr


def write_wav(path: Path, stereo: np.ndarray, sr: int = SR) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.clip(stereo, -1.0, 1.0)
    pcm = (data * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(stereo.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def duck(music: np.ndarray, vo: np.ndarray, amount: float = 0.55) -> np.ndarray:
    """Sidechain-style ducking of the music under the voice."""
    n = min(len(music), len(vo))
    env = np.abs(vo[:n])
    k = int(0.18 * SR)
    env = np.convolve(env, np.ones(k, dtype=np.float32) / k, mode="same")
    peak = float(np.max(env)) if n else 0.0
    if peak > 0:
        env = env / peak
    gain = (1.0 - amount * env).astype(np.float32)
    out = music.copy()
    out[:n] *= gain[:, None]
    return out


def mix(vo_path: Path, music: np.ndarray, events: list[dict], total: float,
        out_path: Path, music_gain: float = 0.30, sfx_gain: float = 0.55) -> None:
    """events: [{'time': float, 'name': str, 'gain': float}]"""
    n_total = int(total * SR)
    vo, _ = read_wav_mono(vo_path)
    mixbuf = np.zeros((n_total, 2), dtype=np.float32)
    m = music[:n_total]
    if len(m) < n_total:
        m = np.pad(m, ((0, n_total - len(m)), (0, 0)))
    # single ducked music bed (voice pushes the music down)
    mixbuf += duck(m, vo, 0.45) * music_gain

    for ev in events:
        sfx = build_sfx(ev["name"])
        s = int(ev["time"] * SR)
        e = min(n_total, s + len(sfx))
        if e <= s:
            continue
        seg = sfx[: e - s] * ev.get("gain", 1.0) * sfx_gain
        mixbuf[s:e, 0] += seg
        mixbuf[s:e, 1] += seg

    v = np.zeros(n_total, dtype=np.float32)
    m2 = min(len(vo), n_total)
    v[:m2] = vo[:m2]
    mixbuf[:, 0] += v
    mixbuf[:, 1] += v

    peak = float(np.max(np.abs(mixbuf))) if n_total else 0.0
    if peak > 0.98:
        mixbuf *= 0.98 / peak
    write_wav(out_path, mixbuf)


def main() -> None:
    """Render a standalone preview of the music + SFX so it can be checked."""
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/data/data/com.termux/files/usr/tmp/opencode/music-preview")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    total = 45.0
    music = build_music(total)
    events = [
        {"time": 0.0, "name": "pop", "gain": 1.0},
        {"time": 4.3, "name": "whoosh", "gain": 0.9},
        {"time": 9.0, "name": "sparkle", "gain": 0.9},
        {"time": 16.5, "name": "whoosh", "gain": 0.6},
        {"time": 22.0, "name": "pop", "gain": 0.9},
        {"time": 27.3, "name": "chime", "gain": 1.0},
        {"time": 35.0, "name": "pop", "gain": 0.9},
        {"time": 40.9, "name": "sparkle", "gain": 1.0},
    ]
    # silent voice track for preview
    vo_path = out / "silence.wav"
    write_wav(vo_path, np.zeros((int(total * SR), 2), dtype=np.float32))
    mix(vo_path, music, events, total, out / "music-preview.wav")
    print("wrote", out / "music-preview.wav")
    print(json.dumps({"events": len(events), "total": total}))


if __name__ == "__main__":
    main()
