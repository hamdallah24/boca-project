#!/usr/bin/env python3
"""Build BOCA-D02 animatic v3 — story-driven character, real backgrounds,
word-by-word subtitles, original music + SFX.

Differences vs v2
-----------------
- Boca is an actor in the scene: he walks in, reacts, points, holds the prism
  and changes expression per beat (keyframed acting timeline).
- Backgrounds are real public-domain / CC0 photos (Wikimedia Commons) with a
  slow camera move (Ken Burns) and per-shot colour grading.
- Subtitles have no background box: outlined text only, revealed word by word
  in sync with the narration.
- Original BGM + SFX are synthesised by make_music.py (no copyright risk).
- Voice over uses Gemini 3.8 Flash TTS (cached, with backoff) and falls back
  to Edge TTS.

Output: 1080x1920 / 30fps / ~45s MP4 + SRT + poster + contact sheet + README.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path("/data/data/com.termux/files/home/projects/boca-character")
sys.path.insert(0, str(ROOT))
from make_boca import character, render_svg, svg_doc  # noqa: E402
from make_music import build_music, mix as mix_audio, read_wav_mono, write_wav  # noqa: E402

W, H = 1080, 1920
FPS = 30
TARGET_TOTAL = 45.0
TOTAL = TARGET_TOTAL
TOTAL_FRAMES = int(round(TOTAL * FPS))

OUT = Path("/sdcard/Download/Boca/animatic-d02-v3")
TMP = Path("/data/data/com.termux/files/usr/tmp/opencode/boca-d02-v3-build")
BG_DIR = ROOT / "assets" / "bg"
EDGE = Path("/data/data/com.termux/files/home/projects/MoneyPrinterTurbo/.venv/bin/edge-tts")
MPT_CONFIG = Path("/data/data/com.termux/files/home/projects/MoneyPrinterTurbo/config.toml")
FONT = "/system/fonts/Roboto-Regular.ttf"
FONT_BOLD = "/system/fonts/Roboto-Bold.ttf"

INK = (35, 24, 21)
WHITE = (255, 255, 255)
HILITE = (255, 226, 96)
SUN = (255, 214, 120)
BLUE = (120, 196, 255)

# ---------------------------------------------------------------- TTS config
TTS_BACKEND = "auto"
EDGE_VOICE = "id-ID-ArdiNeural"
EDGE_RATE = "+0%"
EDGE_PITCH = "+0Hz"
GEMINI_VOICE = "Puck"
GEMINI_MODEL = "gemini-3.8-flash-tts"
GEMINI_STYLE = "friendly, clear, playful, natural pace, talking with children in Indonesian"
GEMINI_KEY = ""

# ------------------------------------------------------------------- the story
# keys: acting keyframes -> (t, expr, pose, arms, period, x, ground, h, prop)
#   x      : horizontal centre of Boca
#   ground : y of his feet
#   h      : character height in px
SHOTS = [
    dict(
        n=1, bg="sky_ground",
        vo="Adek, siapa yang ngecat langit jadi biru?",
        baby="Siapa yang ngecat langit?",
        adult="Kenapa langit tampak biru?",
        grade=dict(tint=(1.02, 1.03, 1.05), bright=1.02, contrast=1.06, sat=1.12, warm=0.25),
        cam=dict(zoom=(1.05, 1.14), fx=(0.46, 0.52), fy=(0.52, 0.44)),
        keys=[
            dict(t=0.00, expr="shock", pose="walk", arms=[0], x=-300, ground=1430, h=690),
            dict(t=1.05, expr="shock", pose="walk", arms=[0], x=180, ground=1430, h=715),
            dict(t=1.45, expr="shock", pose="stand", arms=[0, 3, 2], period=0.70, x=300, ground=1430, h=735),
            dict(t=2.35, expr="shock", pose="point", arms=[2], x=320, ground=1430, h=735),
            dict(t=3.10, expr="shock", pose="stand", arms=[3, 2, 1], period=0.75, x=300, ground=1430, h=735),
        ],
        sfx=[(0.05, "pop", 1.0), (2.30, "whoosh", 0.45)],
        fx=dict(rays=(880, 250, 0.55), dust=(0, 0, 0)),
    ),
    dict(
        n=2, bg="earthrise",
        vo="Cahaya matahari itu sebenarnya campuran banyak warna.",
        baby="Matahari kirim banyak warna.",
        adult="Cahaya Matahari terdiri dari banyak warna.",
        grade=dict(tint=(0.96, 0.99, 1.06), bright=1.04, contrast=1.10, sat=1.05, warm=-0.10),
        cam=dict(zoom=(1.10, 1.20), fx=(0.38, 0.30), fy=(0.42, 0.38)),
        keys=[
            dict(t=0.00, expr="neutral", pose="walk", arms=[0], x=-260, ground=1520, h=620),
            dict(t=0.75, expr="neutral", pose="stand", arms=[0, 2], period=0.8, x=250, ground=1520, h=640),
            dict(t=1.90, expr="focus", pose="point", arms=[2], x=270, ground=1520, h=640),
            dict(t=3.10, expr="focus", pose="stand", arms=[2, 3], period=0.85, x=255, ground=1520, h=640),
        ],
        sfx=[(0.05, "whoosh", 0.85), (2.60, "pop", 0.5)],
        fx=dict(rays=(240, 320, 0.75), beam=True, dust=(0, 0, 0)),
    ),
    dict(
        n=3, bg="prism",
        vo="Kalau lewat prisma, warnanya pisah: merah, kuning, hijau, biru.",
        baby="Merah, kuning, hijau, biru!",
        adult="Prisma memisahkan spektrum cahaya.",
        grade=dict(tint=(1.02, 1.00, 1.03), bright=1.00, contrast=1.08, sat=1.18, warm=0.0),
        cam=dict(zoom=(1.04, 1.13), fx=(0.58, 0.62), fy=(0.50, 0.46)),
        keys=[
            dict(t=0.00, expr="focus", pose="walk", arms=[0], x=-240, ground=1500, h=650),
            dict(t=0.80, expr="focus", pose="stand", arms=[0, 3], period=0.75, x=250, ground=1500, h=665),
            dict(t=1.90, expr="focus", pose="point", arms=[2], x=280, ground=1500, h=665, prop="prism"),
            dict(t=3.20, expr="happy", pose="point", arms=[2], x=280, ground=1500, h=665, prop="prism"),
            dict(t=4.60, expr="happy", pose="stand", arms=[1, 3], period=0.8, x=260, ground=1500, h=665, prop="prism"),
        ],
        sfx=[(0.05, "sparkle", 0.8), (2.10, "sparkle", 1.0), (4.70, "pop", 0.7)],
        fx=dict(rays=(0, 0, 0), beam=True, dust=(0, 0, 0)),
    ),
    dict(
        n=4, bg="atmosphere",
        vo="Di langit, udara kecil-kecil main lempar warna biru ke mana-mana.",
        baby="Udara lempar warna biru.",
        adult="Molekul udara menghamburkan biru lebih kuat.",
        grade=dict(tint=(0.92, 0.97, 1.08), bright=1.05, contrast=1.10, sat=1.12, warm=-0.15),
        cam=dict(zoom=(1.12, 1.22), fx=(0.50, 0.56), fy=(0.40, 0.34)),
        keys=[
            dict(t=0.00, expr="focus", pose="walk", arms=[0], x=-280, ground=1560, h=560),
            dict(t=0.85, expr="focus", pose="stand", arms=[0, 2], period=0.8, x=230, ground=1560, h=580),
            dict(t=2.00, expr="focus", pose="point", arms=[2], x=250, ground=1560, h=580),
            dict(t=3.40, expr="neutral", pose="stand", arms=[3, 2], period=0.85, x=235, ground=1560, h=580),
        ],
        sfx=[(0.05, "whoosh", 0.6), (2.90, "pop", 0.5)],
        fx=dict(rays=(0, 0, 0), dust=(BLUE, 46, 1500)),
    ),
    dict(
        n=5, bg="sky_open",
        vo="Karena biru paling banyak dilempar, mata kita lihat langit biru.",
        baby="Jadi langit biru!",
        adult="Cahaya biru sampai ke mata dari segala arah.",
        grade=dict(tint=(0.90, 0.98, 1.12), bright=1.06, contrast=1.08, sat=1.22, warm=-0.20),
        cam=dict(zoom=(1.06, 1.16), fx=(0.42, 0.48), fy=(0.44, 0.38)),
        keys=[
            dict(t=0.00, expr="focus", pose="walk", arms=[0], x=-260, ground=1480, h=600),
            dict(t=0.80, expr="focus", pose="stand", arms=[0, 3], period=0.75, x=240, ground=1480, h=620),
            dict(t=1.90, expr="neutral", pose="point", arms=[2], x=260, ground=1480, h=620),
            dict(t=2.90, expr="happy", pose="celebrate", arms=[0], x=250, ground=1480, h=625),
        ],
        sfx=[(0.05, "pop", 0.8), (2.85, "sparkle", 0.9)],
        fx=dict(rays=(760, 320, 0.45), dust=(BLUE, 40, 1400)),
    ),
    dict(
        n=6, bg="sunset",
        vo="Tapi sore, cahayanya jalan lebih jauh. Biru habis dilempar, tinggal merah.",
        baby="Sore, biru habis. Tinggal merah.",
        adult="Saat sunset, biru tersebar habis; merah/oranye tersisa.",
        grade=dict(tint=(1.10, 0.94, 0.86), bright=1.02, contrast=1.10, sat=1.20, warm=0.45),
        cam=dict(zoom=(1.08, 1.18), fx=(0.52, 0.44), fy=(0.46, 0.40)),
        keys=[
            dict(t=0.00, expr="confused", pose="walk", arms=[0], x=-270, ground=1540, h=600),
            dict(t=0.90, expr="confused", pose="stand", arms=[0, 1], period=0.85, x=250, ground=1540, h=620),
            dict(t=2.30, expr="confused", pose="think", arms=[1], x=265, ground=1540, h=620),
            dict(t=3.80, expr="happy", pose="point", arms=[2], x=255, ground=1540, h=620),
        ],
        sfx=[(0.05, "whoosh", 0.7), (3.70, "chime", 0.9)],
        fx=dict(rays=(520, 1150, 0.60), dust=((255, 190, 120), 34, 1250)),
    ),
    dict(
        n=7, bg="sky_ground",
        vo="Jadi bukan cat, Adek. Udara yang main warna!",
        baby="Bukan cat, tapi udara!",
        adult="Langit biru karena hamburan cahaya, bukan cat.",
        grade=dict(tint=(1.00, 1.02, 1.08), bright=1.04, contrast=1.08, sat=1.15, warm=0.18),
        cam=dict(zoom=(1.10, 1.20), fx=(0.56, 0.50), fy=(0.50, 0.44)),
        keys=[
            dict(t=0.00, expr="focus", pose="walk", arms=[0], x=-260, ground=1440, h=700),
            dict(t=0.80, expr="focus", pose="stand", arms=[0, 2], period=0.7, x=280, ground=1440, h=720),
            dict(t=1.80, expr="happy", pose="point", arms=[2], x=300, ground=1440, h=720),
            dict(t=2.90, expr="happy", pose="celebrate", arms=[0], x=290, ground=1440, h=725),
        ],
        sfx=[(0.05, "pop", 0.9), (2.85, "sparkle", 1.0)],
        fx=dict(rays=(900, 260, 0.5), dust=(0, 0, 0)),
        sunglasses=True,
    ),
    dict(
        n=8, bg="sky_ground",
        vo="Coba lihat langit sore ini, warnanya apa?",
        baby="Langit sore ini warna apa?",
        adult="Tulis di komentar.",
        grade=dict(tint=(1.10, 0.97, 0.88), bright=1.03, contrast=1.08, sat=1.18, warm=0.40),
        cam=dict(zoom=(1.06, 1.15), fx=(0.44, 0.50), fy=(0.50, 0.44)),
        keys=[
            dict(t=0.00, expr="happy", pose="walk", arms=[0], x=-240, ground=1430, h=700),
            dict(t=0.75, expr="happy", pose="stand", arms=[0, 1], period=0.7, x=300, ground=1430, h=720),
            dict(t=1.60, expr="happy", pose="wave", arms=[1, 3], period=0.75, x=320, ground=1430, h=725),
            dict(t=2.70, expr="happy", pose="wave", arms=[3, 2], period=0.7, x=315, ground=1430, h=725),
        ],
        sfx=[(0.05, "sparkle", 1.0), (1.55, "pop", 0.8)],
        fx=dict(rays=(860, 280, 0.7), dust=(0, 0, 0)),
        cta=True,
    ),
]


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kw)


# --------------------------------------------------------------------- voices
def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and v:
            os.environ.setdefault(k, v)


def read_mpt_gemini_key() -> str:
    if not MPT_CONFIG.exists():
        return ""
    txt = MPT_CONFIG.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'^\s*gemini_api_key\s*=\s*["\']([^"\']+)["\']', txt, re.M)
    return m.group(1).strip() if m else ""


def _gemini_audio(text: str, model: str, voice: str, style: str) -> bytes:
    body = {
        "model": model,
        "input": [{"type": "user_input", "content": [{
            "type": "text", "text": text,
            "annotations": [{"type": "speech_metadata", "style": style}],
        }]}],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": voice}]},
    }
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        data=json.dumps(body).encode("utf-8"),
        headers={"x-goog-api-key": GEMINI_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    last = None
    for attempt in range(7):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
            items = [c for s in data.get("steps", []) if s.get("type") == "model_output"
                     for c in s.get("content", []) if c.get("type") == "audio" and c.get("data")]
            if not items:
                raise RuntimeError("no audio in Gemini response")
            return base64.b64decode(items[-1]["data"])
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                wait = min(20 * (attempt + 1), 120)
                print(f"    Gemini {e.code}, retry in {wait}s", flush=True)
                time.sleep(wait)
                last = e
                continue
            raise
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(10)
    raise RuntimeError(f"Gemini TTS failed: {last!r}")


def gemini_tts(text: str, out_path: Path) -> Path:
    cache = TMP / "cache" / "tts"
    cache.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())[:48]
    cached = cache / f"{slug}-{GEMINI_VOICE}.wav"
    if cached.exists() and cached.stat().st_size > 5000:
        shutil.copy2(cached, out_path)
        return out_path
    raw = _gemini_audio(text, GEMINI_MODEL, GEMINI_VOICE, GEMINI_STYLE)
    cached.write_bytes(raw)
    shutil.copy2(cached, out_path)
    return out_path


def edge_tts(text: str, out_path: Path) -> Path:
    for attempt in range(3):
        p = subprocess.run(
            [str(EDGE), "--voice", EDGE_VOICE, f"--rate={EDGE_RATE}", f"--pitch={EDGE_PITCH}",
             "--text", text, "--write-media", str(out_path)],
            capture_output=True, text=True,
        )
        if p.returncode == 0 and out_path.exists() and out_path.stat().st_size > 1000:
            return out_path
        time.sleep(3)
    raise RuntimeError("edge-tts failed")


def generate_tts(text: str, out_path: Path) -> Path:
    backend = TTS_BACKEND
    if backend == "auto":
        backend = "gemini" if GEMINI_KEY else "edge"
    if backend == "gemini":
        try:
            return gemini_tts(text, out_path)
        except Exception as e:  # noqa: BLE001
            print(f"    Gemini fallback -> Edge: {e}")
            return edge_tts(text, out_path.with_suffix(".mp3"))
    return edge_tts(text, out_path.with_suffix(".mp3"))


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path),
    ])
    return float(out.decode().strip())


def to_wav(src: Path, dst: Path) -> None:
    run(["ffmpeg", "-y", "-i", str(src), "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(dst)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ------------------------------------------------------------- word alignment
def count_syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 1
    return max(1, len(re.findall(r"[aeiouy]+", w)))


def speech_peaks(path: Path) -> list[float]:
    data, sr = read_wav_mono(path)
    hop = sr // 100
    n = len(data) // hop
    if n < 3:
        return []
    env = np.array([float(np.sqrt(np.mean(data[i * hop:(i + 1) * hop] ** 2))) for i in range(n)])
    peak = float(env.max())
    if peak <= 0:
        return []
    env = env / peak
    peaks: list[int] = []
    for i in range(1, n - 1):
        if env[i] >= 0.28 and env[i] >= env[i - 1] and env[i] > env[i + 1]:
            if not peaks or i - peaks[-1] >= 8:
                peaks.append(i)
            elif env[i] > env[peaks[-1]]:
                peaks[-1] = i
    return [p / 100.0 for p in peaks]


def align_words(words: list[str], audio: Path, line_dur: float) -> list[tuple[str, float, float]]:
    """Word-by-word timing inside one narration line."""
    syl = [count_syllables(w) for w in words]
    total = sum(syl)
    if total == 0 or line_dur <= 0:
        step = line_dur / max(len(words), 1)
        return [(w, i * step, (i + 1) * step) for i, w in enumerate(words)]

    peaks = speech_peaks(audio)
    if len(peaks) >= 2:
        # stretch the detected speech rhythm over the expected syllable count
        syl_times = []
        for k in range(total):
            idx = k * (len(peaks) - 1) / max(total - 1, 1)
            lo = int(math.floor(idx))
            hi = min(lo + 1, len(peaks) - 1)
            frac = idx - lo
            syl_times.append(peaks[lo] * (1 - frac) + peaks[hi] * frac)
    else:
        syl_times = [line_dur * (k / total) for k in range(total)]

    out: list[tuple[str, float, float]] = []
    cursor = 0
    for i, w in enumerate(words):
        n = syl[i]
        t0 = max(0.0, syl_times[cursor])
        t1 = max(t0 + 0.06, syl_times[min(cursor + n - 1, total - 1)] + 0.11)
        cursor += n
        out.append((w, t0, min(t1, line_dur)))
    # last word ends with the line
    if out:
        out[-1] = (out[-1][0], out[-1][1], max(out[-1][2], min(line_dur, out[-1][1] + 0.3)))
    # enforce monotonic
    for i in range(1, len(out)):
        if out[i][1] < out[i - 1][1]:
            out[i] = (out[i][0], out[i - 1][1], max(out[i][2], out[i][1] + 0.06))
    return out


def distribute_words(words: list[str], t0: float, t1: float) -> list[tuple[str, float, float]]:
    if not words:
        return []
    syl = [count_syllables(w) for w in words]
    total = sum(syl)
    out = []
    cur = t0
    span = max(t1 - t0, 0.2)
    for w, s in zip(words, syl):
        d = span * (s / total)
        out.append((w, cur, cur + d))
        cur += d
    return out


# ---------------------------------------------------------------- backgrounds
def load_photo(key: str) -> Image.Image:
    p = BG_DIR / f"{key}.jpg"
    if not p.exists():
        raise FileNotFoundError(f"missing background {p} - run fetch_backgrounds.py")
    img = Image.open(p).convert("RGB")
    work_h = int(H * 1.55)
    work_w = int(img.width * work_h / img.height)
    return img.resize((work_w, work_h), Image.Resampling.LANCZOS)


def lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def smoothstep(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def bg_frame(photo: Image.Image, shot: dict, prog: float) -> Image.Image:
    cam = shot["cam"]
    zoom = lerp(cam["zoom"][0], cam["zoom"][1], prog)
    fx = lerp(cam["fx"][0], cam["fx"][1], prog)
    fy = lerp(cam["fy"][0], cam["fy"][1], prog)
    cw = W / zoom
    ch = H / zoom
    cx = fx * photo.width
    cy = fy * photo.height
    x0 = max(0.0, min(photo.width - cw, cx - cw / 2))
    y0 = max(0.0, min(photo.height - ch, cy - ch / 2))
    crop = photo.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.Resampling.LANCZOS)
    return grade(crop, shot["grade"])


def grade(img: Image.Image, g: dict) -> Image.Image:
    arr = np.asarray(img).astype(np.float32) / 255.0
    arr *= np.array(g["tint"], dtype=np.float32) * g["bright"]
    arr = (arr - 0.5) * g["contrast"] + 0.5
    gray = arr.mean(axis=2, keepdims=True)
    arr = gray + (arr - gray) * g["sat"]
    warm = g.get("warm", 0.0)
    arr[:, :, 0] += warm * 0.06
    arr[:, :, 2] -= warm * 0.06
    arr = np.clip(arr, 0, 1)
    out = Image.fromarray((arr * 255).astype(np.uint8), "RGB")

    # soft vignette
    y, x = np.ogrid[:H, :W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    a = np.clip((r - 0.62) * 120, 0, 90).astype(np.uint8)
    vign = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), a]), "RGBA")
    out = out.convert("RGBA")
    out.alpha_composite(vign)
    return out.convert("RGB")


def draw_fx(base: Image.Image, shot: dict, local: float) -> Image.Image:
    fx = shot.get("fx") or {}
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    rays = fx.get("rays")
    if rays and rays[2] > 0:
        rx, ry, strength = rays
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        for i in range(7, 0, -1):
            r = 60 + i * 34
            gd.ellipse((rx - r, ry - r, rx + r, ry + r), fill=(255, 240, 200, int(10 * strength)))
        glow = glow.filter(ImageFilter.GaussianBlur(40))
        layer.alpha_composite(glow)
        d = ImageDraw.Draw(layer)
        for i in range(7):
            ang = math.radians(-160 + i * 16 + math.sin(local * 0.4 + i) * 2)
            x2 = rx + math.cos(ang) * 1400
            y2 = ry + math.sin(ang) * 1400
            d.line((rx, ry, x2, y2), fill=(255, 238, 190, int(16 * strength)), width=26 + i * 3)

    if fx.get("beam"):
        x2, y2 = 980, 560
        colors = [(255, 80, 80), (255, 160, 70), (255, 225, 90), (110, 220, 130), (80, 170, 255), (160, 110, 255)]
        for i, c in enumerate(colors):
            d.line((0, 360 + i * 16, x2, y2 + (i - 2.5) * 90), fill=(*c, 46), width=22)
            d.line((0, 360 + i * 16, x2, y2 + (i - 2.5) * 90), fill=(*c, 190), width=9)

    dust = fx.get("dust")
    if dust and dust[1]:
        color, count, ymax = dust
        rng = np.random.default_rng(23)
        for _ in range(count):
            px = int(rng.integers(0, W))
            py = int(rng.integers(120, ymax))
            drift = math.sin(local * 0.7 + px) * 26
            r = int(rng.integers(4, 13))
            a = int(rng.integers(60, 170))
            d.ellipse((px + drift - r, py - r, px + drift + r, py + r), fill=(*color, a))
    base = base.convert("RGBA")
    base.alpha_composite(layer)
    return base.convert("RGB")


# --------------------------------------------------------------------- actors
SPRITE_CACHE: dict[tuple, Image.Image] = {}


def needed_sprites() -> set[tuple]:
    need = set()
    for shot in SHOTS:
        for k in shot["keys"]:
            steps = (0, 1) if k["pose"] == "walk" else (0,)
            for arm in k.get("arms", [0]):
                for st in steps:
                    need.add((k["expr"], k["pose"], arm, st, k.get("prop")))
    return need


def build_sprites() -> dict[tuple, Image.Image]:
    out_dir = TMP / "sprites"
    out_dir.mkdir(parents=True, exist_ok=True)
    for expr, pose, arm, step, prop in sorted(needed_sprites(), key=lambda t: (t[0], t[1], t[2], t[3], str(t[4]))):
        key = (expr, pose, arm, step, prop)
        svg = svg_doc(1080, 1920,
                      character(expr, pose, 540, 620, 1.0, shadow=False,
                                arm_gesture=arm, mouth=5, step=step, prop=prop),
                      None)
        name = f"{expr}-{pose}-a{arm}-s{step}-{(prop or 'none')}"
        sp = out_dir / f"{name}.svg"
        png = out_dir / f"{name}.png"
        sp.write_text(svg, encoding="utf-8")
        render_svg(sp, png, 1080, 1920, transparent=True)
        SPRITE_CACHE[key] = Image.open(png).convert("RGBA").crop((140, 348, 940, 1548))
    return SPRITE_CACHE


def actor_state(shot: dict, local: float) -> dict:
    keys = shot["keys"]
    i = 0
    for idx, k in enumerate(keys):
        if local >= k["t"]:
            i = idx
    a = keys[i]
    b = keys[min(i + 1, len(keys) - 1)]
    span = max(b["t"] - a["t"], 1e-6)
    u = smoothstep((local - a["t"]) / span) if b is not a else 0.0
    arms = a.get("arms", [0])
    period = a.get("period", 0.8)
    arm = arms[int(local / period) % len(arms)] if arms else 0
    step = int(local / 0.24) % 2 if a["pose"] == "walk" else 0
    return dict(
        expr=a["expr"], pose=a["pose"], arm=arm, step=step, prop=a.get("prop"),
        x=lerp(a["x"], b["x"], u), ground=lerp(a["ground"], b["ground"], u),
        h=lerp(a["h"], b["h"], u),
    )


def draw_mouth(im: Image.Image, cx: int, cy: int, size: int, open_amt: float, closed: str) -> None:
    d = ImageDraw.Draw(im)
    ink_w = max(2, int(size * 0.008))
    if open_amt < 0.10:
        if closed == "smile":
            w, h = int(size * 0.050), int(size * 0.030)
            d.arc((cx - w, cy - h, cx + w, cy + h), 20, 160, fill=INK, width=ink_w)
        else:
            w = int(size * 0.055)
            d.line((cx - w, cy, cx + w, cy), fill=INK, width=ink_w)
        return
    w = int(size * (0.032 + 0.043 * open_amt))
    h = int(size * (0.014 + 0.034 * open_amt))
    d.ellipse((cx - w, cy - h, cx + w, cy + h), fill=(122, 31, 43), outline=INK, width=ink_w)
    if open_amt > 0.35:
        tw, th = int(w * 0.55), int(h * 0.35)
        d.ellipse((cx - tw, cy + int(h * 0.25) - th, cx + tw, cy + int(h * 0.25) + th), fill=(232, 106, 122))


def draw_blink(im: Image.Image, x: int, top: int, size: int) -> None:
    d = ImageDraw.Draw(im)
    eye_y = top + int(size * 0.26)
    eye_dx = int(size * 0.075)
    ew, eh = int(size * 0.080), int(size * 0.070)
    for sx in (-1, 1):
        cx = x + sx * eye_dx
        d.ellipse((cx - ew, eye_y - eh, cx + ew, eye_y + eh), fill=(242, 201, 160))
        d.arc((cx - ew, eye_y - eh, cx + ew, eye_y + eh), 200, 340, fill=INK, width=max(2, int(size * 0.008)))


def draw_sunglasses(im: Image.Image, x: int, top: int, size: int) -> None:
    d = ImageDraw.Draw(im)
    eye_y = top + int(size * 0.26)
    eye_dx = int(size * 0.075)
    w, h = int(size * 0.130), int(size * 0.046)
    for sx in (-1, 1):
        cx = x + sx * eye_dx
        d.rounded_rectangle((cx - w // 2, eye_y - h // 2, cx + w // 2, eye_y + h // 2), 12,
                            fill=(20, 20, 25), outline=(5, 5, 8), width=4)
        d.line((cx - w // 3, eye_y - h // 5, cx + w // 4, eye_y - h // 5), fill=(255, 255, 255), width=4)
        d.line((cx + sx * w // 2, eye_y, x + sx * int(size * 0.18), eye_y - 8), fill=(20, 20, 25), width=6)
    d.line((x - eye_dx + w // 2, eye_y, x + eye_dx - w // 2, eye_y), fill=(20, 20, 25), width=6)


# ------------------------------------------------------------------ subtitles
class Subtitle:
    """Word-by-word caption with outline only (no background box)."""

    def __init__(self, baby_font: ImageFont.FreeTypeFont, adult_font: ImageFont.FreeTypeFont):
        self.bf = baby_font
        self.af = adult_font
        self.probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        self.rows: dict[int, list] = {}

    def _rows(self, entries: list[tuple[str, float, float]], font, max_w: int) -> list[dict]:
        rows: list[list] = [[]]
        cur_w = 0.0
        space = self.probe.textlength(" ", font=font)
        for e in entries:
            w = self.probe.textlength(e[0], font=font)
            add = w if not rows[-1] else w + space
            if rows[-1] and cur_w + add > max_w:
                rows.append([e])
                cur_w = w
            else:
                rows[-1].append(e)
                cur_w += add
        out = []
        for row in rows:
            width = sum(self.probe.textlength(e[0], font=font) for e in row) + space * (len(row) - 1)
            out.append(dict(words=row, width=width))
        return out

    def build(self, shot: dict, baby_words, adult_words) -> None:
        baby_rows = self._rows(baby_words, self.bf, 940)
        adult_rows = self._rows(adult_words, self.af, 960)
        lh1 = int(self.bf.size * 1.26)
        lh2 = int(self.af.size * 1.34)
        gap = 14
        total = len(baby_rows) * lh1 + gap + len(adult_rows) * lh2
        bottom = 1548
        y = bottom - total
        layout = {"baby": [], "adult": []}
        for row in baby_rows:
            x = W / 2 - row["width"] / 2
            for e in row["words"]:
                layout["baby"].append((e[0], e[1], e[2], x, y, self.bf))
                x += self.probe.textlength(e[0], font=self.bf) + self.probe.textlength(" ", font=self.bf)
            y += lh1
        y += gap
        for row in adult_rows:
            x = W / 2 - row["width"] / 2
            for e in row["words"]:
                layout["adult"].append((e[0], e[1], e[2], x, y, self.af))
                x += self.probe.textlength(e[0], font=self.af) + self.probe.textlength(" ", font=self.af)
            y += lh2
        self.rows[shot["n"]] = layout

    def draw(self, im: Image.Image, shot: dict, t: float) -> None:
        layout = self.rows.get(shot["n"])
        if not layout:
            return
        for group, is_baby in (("baby", True), ("adult", False)):
            for word, t0, t1, x, y, font in layout[group]:
                if t < t0:
                    continue
                active = t0 <= t < t1
                fill = HILITE if (active and is_baby) else (WHITE if is_baby else (238, 240, 245))
                stroke = 6 if is_baby else 4
                self._paste(im, word, x, y, font, fill, stroke, 1.0 if not active else 1.07,
                            -4 if active else 0)

    @staticmethod
    def _paste(im: Image.Image, word: str, x: float, y: float, font, fill, stroke: int,
               scale: float, dy: int) -> None:
        probe = ImageDraw.Draw(Image.new("RGB", (4, 4)))
        w = int(probe.textlength(word, font=font)) + stroke * 4
        h = int(font.size * 2.2)
        tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        td.text((stroke * 2, stroke * 2), word, font=font, fill=(*fill, 255),
                stroke_width=stroke, stroke_fill=(8, 6, 5, 255))
        bbox = tmp.getbbox()
        if bbox:
            tmp = tmp.crop(bbox)
        if scale != 1.0:
            tmp = tmp.resize((max(1, int(tmp.width * scale)), max(1, int(tmp.height * scale))),
                             Image.Resampling.LANCZOS)
        im.paste(tmp, (int(x + (w - tmp.width) / 2), int(y + dy)), tmp)


# -------------------------------------------------------------------- audio
def make_audio() -> tuple[Path, Path, list[dict]]:
    """Build narration (Gemini/Edge), music and SFX; returns vo path, mix path, events."""
    vo_dir = TMP / "vo"
    vo_dir.mkdir(parents=True, exist_ok=True)

    vo_wavs: list[Path] = []
    vo_durs: list[float] = []
    for shot in SHOTS:
        raw = generate_tts(shot["vo"], vo_dir / f"vo-{shot['n']:02d}.wav")
        wav = vo_dir / f"vo-{shot['n']:02d}.wav"
        to_wav(raw, wav)
        dur = ffprobe_duration(wav)
        vo_wavs.append(wav)
        vo_durs.append(dur)
        print(f"  VO {shot['n']}: {dur:.2f}s  {shot['vo'][:42]}")

    min_durs = [d + 0.26 for d in vo_durs]
    base = sum(min_durs)
    global TOTAL, TOTAL_FRAMES
    TOTAL = max(TARGET_TOTAL, base)
    extra = TOTAL - base
    durs = [m + (extra * m / base if base > 0 else 0.0) for m in min_durs]
    t = 0.0
    for shot, dur in zip(SHOTS, durs):
        shot["start"] = round(t, 3)
        t += dur
        shot["end"] = round(t, 3)
    SHOTS[-1]["end"] = round(TOTAL, 3)
    TOTAL_FRAMES = int(round(TOTAL * FPS))
    print(f"  fitted total {TOTAL:.2f}s / {TOTAL_FRAMES} frames")

    # pad each line into its slot
    segs = []
    for shot, wav in zip(SHOTS, vo_wavs):
        dur = shot["end"] - shot["start"]
        seg = vo_dir / f"seg-{shot['n']:02d}.wav"
        run(["ffmpeg", "-y", "-i", str(wav), "-af", f"apad=whole_dur={dur:.3f}",
             "-t", f"{dur:.3f}", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(seg)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        segs.append(seg)

    concat = vo_dir / "concat.txt"
    concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in segs), encoding="utf-8")
    raw_all = vo_dir / "voiceover-raw.wav"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(raw_all)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    vo = vo_dir / "voiceover.wav"
    run(["ffmpeg", "-y", "-i", str(raw_all), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
         "-t", f"{TOTAL:.3f}", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(vo)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # word timings
    for shot, wav, dur in zip(SHOTS, vo_wavs, vo_durs):
        baby_words = shot["baby"].split()
        adult_words = shot["adult"].split()
        shot["_baby_t"] = align_words(baby_words, wav, dur)
        shot["_adult_t"] = distribute_words(adult_words, 0.05, max(dur - 0.05, 0.2))

    # music + sfx
    print("  building music + sfx")
    music = build_music(TOTAL)
    events = []
    for shot in SHOTS:
        for off, name, gain in shot.get("sfx", []):
            events.append({"time": shot["start"] + off, "name": name, "gain": gain})
    mixed = vo_dir / "mix.wav"
    mix_audio(vo, music, events, TOTAL, mixed, music_gain=0.34, sfx_gain=0.6)
    final = vo_dir / "audio.wav"
    run(["ffmpeg", "-y", "-i", str(mixed), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
         "-t", f"{TOTAL:.3f}", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(final)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return vo, final, events


def audio_envelope(audio: Path) -> np.ndarray:
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(audio), "-f", "s16le",
                                   "-ac", "1", "-ar", "8000", "-"])
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    spf = 8000.0 / FPS
    env = np.zeros(TOTAL_FRAMES, dtype=np.float32)
    for i in range(TOTAL_FRAMES):
        a, b = int(i * spf), int((i + 1) * spf)
        seg = samples[a:b]
        if len(seg):
            env[i] = float(np.sqrt(np.mean(seg * seg)))
    env = np.convolve(env, np.ones(5, dtype=np.float32) / 5.0, mode="same")
    p95 = float(np.percentile(env, 95)) if env.size else 1.0
    env = np.clip((env - 0.008) / max(p95 - 0.008, 1e-6), 0.0, 1.0)
    return env ** 0.65


# ------------------------------------------------------------------- render
def render_video(audio: Path, vo: Path, subs: Subtitle, events: list[dict]) -> Path:
    photos = {s["bg"]: load_photo(s["bg"]) for s in SHOTS}
    env = audio_envelope(vo)
    sprites = build_sprites()

    scaled: dict[tuple, Image.Image] = {}

    def sprite_for(state: dict, h: int) -> Image.Image:
        key = (state["expr"], state["pose"], state["arm"], state["step"], state["prop"], int(h))
        if key not in scaled:
            src = sprites[(state["expr"], state["pose"], state["arm"], state["step"], state["prop"])]
            w = max(1, int(round(800 * h / 1200)))
            scaled[key] = src.resize((w, h), Image.Resampling.LANCZOS)
        return scaled[key]

    out = OUT / "boca-d02-animatic-v3.mp4"
    log = TMP / "ffmpeg-render.log"
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(audio),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out),
    ]
    with open(log, "wb") as err:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=err)
        assert proc.stdin is not None
        for f in range(TOTAL_FRAMES):
            t = f / FPS
            shot = next((s for s in SHOTS if s["start"] <= t < s["end"]), SHOTS[-1])
            local = t - shot["start"]
            prog = local / max(shot["end"] - shot["start"], 1e-6)

            base = bg_frame(photos[shot["bg"]], shot, prog)
            base = draw_fx(base, shot, local)

            st = actor_state(shot, local)
            h = int(st["h"])
            sprite = sprite_for(st, h)
            x = int(st["x"])
            ground = int(st["ground"])
            top = ground - h

            # ground shadow
            shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(shadow)
            sw = int(sprite.width * 0.42)
            sd.ellipse((x - sw, ground - 26, x + sw, ground + 26), fill=(0, 0, 0, 96))
            shadow = shadow.filter(ImageFilter.GaussianBlur(16))
            base = base.convert("RGBA")
            base.alpha_composite(shadow)
            base = base.convert("RGB")

            base.paste(sprite, (x - sprite.width // 2, top), sprite)

            mouth_y = top + int(h * 0.393333)
            draw_mouth(base, x, mouth_y, h, float(env[f]), "smile" if shot["n"] in (5, 8) else "line")
            if not shot.get("sunglasses"):
                if ((local + (shot["n"] * 0.7) % 4.0) % 4.0) < 0.12:
                    draw_blink(base, x, top, h)
            if shot.get("sunglasses"):
                draw_sunglasses(base, x, top, h)

            # sfx accents
            for ev in events:
                dt = t - ev["time"]
                if 0 <= dt < 0.9:
                    if ev["name"] == "sparkle":
                        d = ImageDraw.Draw(base, "RGBA")
                        for k in range(14):
                            ang = k * 0.7 + dt * 2.2
                            rr = 120 + dt * 420
                            sx = W / 2 + math.cos(ang) * rr * 0.9
                            sy = 820 + math.sin(ang) * rr * 0.7
                            s = 10 * (1 - dt / 0.9) + 3
                            d.ellipse((sx - s, sy - s, sx + s, sy + s), fill=(255, 240, 190, 210))
                    elif ev["name"] == "pop" and dt < 0.45:
                        d = ImageDraw.Draw(base, "RGBA")
                        rr = 40 + dt * 420
                        d.ellipse((x - rr, top + 120 - rr, x + rr, top + 120 + rr),
                                  outline=(255, 236, 170, int(190 * (1 - dt / 0.45))), width=7)

            subs.draw(base, shot, t)

            preview_t = shot["start"] + min(0.9, (shot["end"] - shot["start"]) * 0.35)
            if f == int(round(preview_t * FPS)):
                base.save(TMP / f"preview-{shot['n']:02d}.png")
            proc.stdin.write(base.tobytes())
        proc.stdin.close()
        rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed, see {log}")
    return out


# ------------------------------------------------------------------ outputs
def make_poster(subs: Subtitle) -> Path:
    shot = SHOTS[-1]
    base = bg_frame(load_photo(shot["bg"]), shot, 0.25).convert("RGBA")
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((60, 80, 1020, 360), 30, fill=(246, 241, 231, 240), outline=INK, width=6)
    d.rectangle((90, 110, 990, 120), fill=(215, 38, 61))
    f1 = ImageFont.truetype(FONT_BOLD if Path(FONT_BOLD).exists() else FONT, 92)
    f2 = ImageFont.truetype(FONT, 46)
    f3 = ImageFont.truetype(FONT, 24)
    d.text((540, 150), "BOCA", font=f1, fill=INK, anchor="ma")
    d.text((540, 258), "Kenapa langit biru?", font=f2, fill=INK, anchor="ma")
    d.text((540, 320), "ANIMATIC v3 · 45 detik", font=f3, fill=(107, 91, 75), anchor="ma")
    d.rounded_rectangle((760, 520, 1000, 720), 40, fill=(255, 255, 255, 240), outline=INK, width=6)
    d.polygon([(820, 710), (790, 780), (870, 722)], fill=(255, 255, 255, 240), outline=INK)
    d.text((880, 620), "?", font=ImageFont.truetype(FONT, 120), fill=(215, 38, 61), anchor="mm")
    out = OUT / "boca-d02-animatic-v3-poster.png"
    base.convert("RGB").save(out)
    return out


def make_contact_sheet() -> Path:
    sheet = Image.new("RGB", (W, H), (246, 241, 231))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT, 26)
    for i, shot in enumerate(SHOTS):
        p = TMP / f"preview-{shot['n']:02d}.png"
        if not p.exists():
            continue
        im = Image.open(p).convert("RGB").resize((270, 480), Image.Resampling.LANCZOS)
        x = 20 + (i % 4) * 260
        y = 80 + (i // 4) * 760
        sheet.paste(im, (x, y))
        d.text((x, y + 490), f"SHOT {shot['n']}", font=f, fill=INK)
        d.text((x, y + 524), f"{shot['start']:.1f}-{shot['end']:.1f}s", font=f, fill=(107, 91, 75))
    out = OUT / "contact-sheet.png"
    sheet.save(out)
    return out


def fmt_srt(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt() -> Path:
    lines = []
    for i, shot in enumerate(SHOTS, 1):
        lines += [str(i), f"{fmt_srt(shot['start'])} --> {fmt_srt(shot['end'])}",
                  shot["baby"], shot["adult"], ""]
    out = OUT / "boca-d02-animatic-v3.srt"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def write_readme(video: Path, vo: Path, backend: str, events: list[dict]) -> Path:
    rows = "\n".join(f"| {s['n']} | {s['start']:.2f}-{s['end']:.2f}s | {s['bg']} | {s['baby']} | {s['adult']} |"
                     for s in SHOTS)
    tts_line = (f"Gemini `{GEMINI_MODEL}` / voice `{GEMINI_VOICE}` / style: {GEMINI_STYLE}"
                if backend == "gemini" else f"Edge `{EDGE_VOICE}` rate {EDGE_RATE}")
    bg_lines = []
    cred = BG_DIR / "credits.json"
    if cred.exists():
        for r in json.loads(cred.read_text(encoding="utf-8")):
            bg_lines.append(f"| `{r['file']}` | {r['title'].replace('File:','')} | {r['license']} | {r['page']} |")
    credits_table = "\n".join(bg_lines)
    text = f"""# BOCA-D02 — Animatic v3

**Status:** previz / animatic. Bukan render final.
**File:** `{video.name}`
**Durasi:** {TOTAL:.1f}s · 1080x1920 · 30fps
**Audio:** `{vo.name}` · narasi {tts_line} · musik + SFX original (self-made) · loudnorm -14 LUFS

## Perubahan v3

- **Boca jadi karakter utama.** Ada timeline acting per shot: dia masuk scene
  (jalan), berhenti, bereaksi, menunjuk, memegang prisma, merayakan.
  Ekspresi berubah mengikuti beat cerita, bukan berdiri diam.
- **Background asli** (Public Domain / CC0, Wikimedia Commons) dengan camera
  move pelan (Ken Burns) dan colour grading per shot.
- **Subtitle tanpa kotak background**: hanya huruf + outline, ukuran sedang
  (bayi 52px / dewasa 38px), dan **muncul kata per kata** sinkron dengan
  narasi (align dari ritme suara).
- **Musik + SFX**: bed original (pad, bass, marimba, shaker) plus SFX per beat
  (pop / whoosh / sparkle / chime). Semua disintesis sendiri, nol hak cipta.
- Narasi pakai Gemini 3.8 Flash TTS (cached, retry 429).

## Shot list

| Shot | Waktu | BG | Caption bayi | Caption dewasa |
|---|---|---|---|---|
{rows}

## Background (lisensi bebas)

| File | Judul | Lisensi | Sumber |
|---|---|---|---|
{credits_table}

Detail: `assets/bg/CREDITS.md`.

## File

- `{video.name}` — animatic v3
- `boca-d02-animatic-v3.srt` — caption SRT (per shot, 2 baris)
- `boca-d02-animatic-v3-poster.png` — poster
- `contact-sheet.png` — 8-shot contact sheet
- `voiceover.wav` — narasi saja (tanpa musik)
- `audio-master.wav` — narasi + musik + SFX

## Catatan

- SFX event: {len(events)} kejadian.
- Sumber fakta: NASA Science + NOAA NESDIS (Content Bible v2.3).
- Belum final render, belum cron, belum publish.
"""
    out = OUT / "README.md"
    out.write_text(text, encoding="utf-8")
    return out


def main() -> None:
    global TTS_BACKEND, EDGE_VOICE, EDGE_RATE, EDGE_PITCH, GEMINI_VOICE, GEMINI_MODEL, GEMINI_STYLE
    global GEMINI_KEY, OUT

    ap = argparse.ArgumentParser()
    ap.add_argument("--tts", choices=["auto", "edge", "gemini"], default="auto")
    ap.add_argument("--edge-voice", default=EDGE_VOICE)
    ap.add_argument("--edge-rate", default=EDGE_RATE)
    ap.add_argument("--gemini-voice", default=GEMINI_VOICE)
    ap.add_argument("--gemini-model", default=GEMINI_MODEL)
    ap.add_argument("--gemini-style", default=GEMINI_STYLE)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    TTS_BACKEND = args.tts
    EDGE_VOICE, EDGE_RATE = args.edge_voice, args.edge_rate
    GEMINI_VOICE, GEMINI_MODEL, GEMINI_STYLE = args.gemini_voice, args.gemini_model, args.gemini_style
    OUT = Path(args.out)

    load_dotenv(ROOT / ".env")
    load_dotenv(Path.home() / ".config" / "boca" / ".env")
    GEMINI_KEY = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
                  or read_mpt_gemini_key())

    backend = TTS_BACKEND
    if backend == "auto":
        backend = "gemini" if GEMINI_KEY else "edge"
    print(f"TTS backend: {backend}" + ("" if GEMINI_KEY or backend == "edge" else " (no key)"))

    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    (TMP / "cache").mkdir(parents=True, exist_ok=True)

    print("1/5 audio (VO + music + sfx)")
    vo, audio, events = make_audio()

    print("2/5 subtitle layout")
    subs = Subtitle(ImageFont.truetype(FONT_BOLD if Path(FONT_BOLD).exists() else FONT, 52),
                    ImageFont.truetype(FONT, 38))
    for shot in SHOTS:
        baby = [(w, shot["start"] + t0, shot["start"] + t1) for w, t0, t1 in shot["_baby_t"]]
        adult = [(w, shot["start"] + t0, shot["start"] + t1) for w, t0, t1 in shot["_adult_t"]]
        subs.build(shot, baby, adult)

    print("3/5 sprites")
    build_sprites()

    print("4/5 video")
    video = render_video(audio, vo, subs, events)

    print("5/5 outputs")
    make_poster(subs)
    make_contact_sheet()
    write_srt()
    write_readme(video, vo, backend, events)
    shutil.copy2(vo, OUT / "voiceover.wav")
    shutil.copy2(audio, OUT / "audio-master.wav")
    print("done:", video, video.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
