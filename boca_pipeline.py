#!/usr/bin/env python3
"""BOCA production pipeline (template v4 - LOCKED).

Episode-driven: satu plan JSON (atau objek Episode) -> satu video vertikal.
Dipakai oleh daily_build.py (cron harian) dan oleh make_animatic_d02.py.

Fitur template v4:
- gaya kartun flat vector (make_cartoon.py)
- Boca sebagai karakter utama (timeline acting), tanpa buku
- sidekick Lumi yang bisa jadipeaker (VO sendiri) untuk dialog 2 arah
- subtitle tanpa panel, outline, muncul kata-per-kata sinkron envelope suara
- musik + SFX original (make_music.py)
- narasi Gemini TTS (fallback chain multi-model + Edge TTS)
"""
from __future__ import annotations

import base64
import hashlib
import io
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
import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import motion
import props as prop_lib
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from make_boca import character, lumi, render_svg, svg_doc  # noqa: E402
from make_cartoon import build_scene, build_fx_layers  # noqa: E402
import layouts as layout_lib  # noqa: E402
import props_svg  # noqa: E402
from scene_svg import SCENE_SVG  # noqa: E402
from make_guest import GUEST_SPECS, guest as guest_svg  # noqa: E402
from make_music import build_music, mix as mix_audio, read_wav_mono, write_wav  # noqa: E402

W, H = 1080, 1920
FPS = 30
SCENE_SCALE = 1.25
SW, SH = int(W * SCENE_SCALE), int(H * SCENE_SCALE)

CAPTION_BOTTOM = 1570
SIZE_BABY = 56
SIZE_ADULT = 42

# Narasi TTS asli ~0.45-0.50 s/kata (Edge) dan ~0.35-0.40 (Gemini). Kalau
# hasil sintesis melewati tier, percepat maksimal 1.60x (Edge butuh ~1.6x,
# Gemini cukup ~1.25x); kalau lebih pendek, tambah jeda visual maksimal 22%
# saja supaya tidak jadi video senyap seperti D01.
MAX_TEMPO = 1.0          # tidak dipakai lagi: narasi tidak pernah dipercepat (atempo dihapus)


class NetworkUnavailable(RuntimeError):
    """Tidak ada koneksi internet - build tidak bisa lanjut, coba di run berikutnya."""


def is_network_error(e: BaseException) -> bool:
    """True kalau error-nya gara-gara jaringan (DNS/HTTP/socket), bukan kode API."""
    if isinstance(e, urllib.error.HTTPError):
        return False          # HTTP error = kode API (kuota, auth), bukan jaringan
    if isinstance(e, urllib.error.URLError):
        return True
    msg = f"{e!r}".lower()
    return any(k in msg for k in (
        "gaierror", "no address associated", "name or service not known",
        "temporary failure in name resolution", "connection refused",
        "connection reset", "timed out", "network is unreachable",
        "ssl", "certificate", "eof occurred",
    ))
TTS_SEC_PER_WORD = 0.4895  # Gemini Puck/Aoede (Edge fallback +0% setara)
MAX_PAD = 1.22

INK = (35, 24, 21)
WHITE = (255, 255, 255)
HILITE = (255, 226, 96)

FONT = "/system/fonts/Roboto-Regular.ttf"
EDGE = Path("/data/data/com.termux/files/home/projects/MoneyPrinterTurbo/.venv/bin/edge-tts")
MPT_CONFIG = Path("/data/data/com.termux/files/home/projects/MoneyPrinterTurbo/config.toml")

# TTS defaults
GEMINI_MODEL = "gemini-3.8-flash-tts"
GEMINI_STYLE = ("warm, friendly, light conversational Indonesian for a general audience, "
                "explaining with everyday analogies, no baby talk, natural pace")
GEMINI_VOICE_BOCA = "Puck"
GEMINI_VOICE_LUMI = "Aoede"
EDGE_VOICE = "id-ID-ArdiNeural"
GEMINI_VOICE_GUEST = {"ardi": "Fenrir", "bu_ratna": "Kore", "pak_darno": "Charon",
                      "sari": "Leda", "dokter_nia": "Autonoe", "kak_bima": "Orus"}
EDGE_VOICE_GUEST = {gid: spec["edge"] for gid, spec in GUEST_SPECS.items()}
# Edge = cadangan saat kuota Gemini habis. Pakai rate natural (+0%) supaya
# tempo-nya sama dengan Gemini (0.49 s/kata); tidak ada atempo di pipeline.
EDGE_RATE = "+0%"
EDGE_PITCH = "+0Hz"
# Backend default: auto -> Gemini (suara Puck/Aoede, tempo natural 0.49 s/kata).
# Edge hanya dipakai kalau kunci Gemini tidak ada atau kuota harian habis.
TTS_BACKEND = os.environ.get("BOCA_TTS", "auto")

SR_ENV = 200  # envelope rate untuk alignment kata


# ----------------------------------------------------------------- data model
@dataclass
class Line:
    who: str            # "boca" | "lumi"
    text: str           # narasi yang diucapkan
    caption: str        # baris sederhana (besar)
    caption_adult: str  # baris dewasa (kecil)


@dataclass
class Shot:
    n: int
    scene: str
    dialogue: list[Line]
    keys: list[dict] = field(default_factory=list)     # acting Boca
    lumi: list[dict] = field(default_factory=list)     # acting Lumi
    sfx: list[tuple] = field(default_factory=list)    # (offset_detik, nama, gain)
    guest: list[dict] = field(default_factory=list)   # acting tamu (opsional)
    props: list[dict] = field(default_factory=list)   # ikon/badge/loupe (opsional)
    layouts: list[dict] = field(default_factory=list)  # mode layout per beat
    cam: dict = field(default_factory=lambda: {"fx": (0.30, 0.70), "fy": (0.30, 0.70)})
    start: float = 0.0
    end: float = 0.0
    est: float = 6.0                                  # est_seconds dari JSON
    lines: list = field(default_factory=list)         # terisi saat render


@dataclass
class Episode:
    id: str
    day: int
    title: str
    series: str = "KYB"
    duration_target: float = 45.0
    facts_status: str = "pending"
    scene_family: str = ""
    motion_motif: str = ""
    cta: str = "Tulis di komentar."
    guest: str | None = None
    shots: list[Shot] = field(default_factory=list)
    publish: dict = field(default_factory=dict)
    lead_in: float = 0.22
    line_gap: float = 0.16
    tail: float = 0.20

    @staticmethod
    def from_dict(d: dict) -> "Episode":
        shots = []
        for s in d["shots"]:
            dialogue = [Line(**l) for l in s.get("dialogue", [])]
            shots.append(Shot(n=s["n"], scene=s["scene"], dialogue=dialogue,
                              keys=s.get("keys", []), lumi=s.get("lumi", []),
                              guest=s.get("guest", []),
                              props=s.get("props", []),
                              layouts=s.get("layouts", []),
                              sfx=[tuple(x) for x in s.get("sfx", [])],
                              est=float(s.get("est_seconds", 6.0)),
                              cam=s.get("cam", {"fx": (0.30, 0.70), "fy": (0.30, 0.70)})))
        return Episode(id=d["id"], day=d["day"], title=d["title"],
                       series=d.get("series", "KYB"),
                       scene_family=d.get("scene_family", ""),
                       motion_motif=d.get("motion_motif", ""),
                       duration_target=float(d.get("duration_target", 45)),
                       facts_status=d.get("facts_status", "pending"),
                       cta=d.get("cta", "Tulis di komentar."),
                       guest=(d.get("cast") or {}).get("guest"),
                       shots=shots, publish=d.get("publish", {}))

    def to_dict(self) -> dict:
        return {
            "id": self.id, "day": self.day, "title": self.title, "series": self.series,
            "scene_family": self.scene_family, "motion_motif": self.motion_motif,
            "duration_target": self.duration_target, "facts_status": self.facts_status,
            "cta": self.cta, "publish": self.publish,
            "shots": [{
                "n": s.n, "scene": s.scene,
                "dialogue": [l.__dict__ for l in s.dialogue],
                "keys": s.keys, "lumi": s.lumi, "guest": s.guest,
                "props": s.props,
                "layouts": s.layouts,
                "sfx": [list(x) for x in s.sfx],
            } for s in self.shots],
        }


# ------------------------------------------------------------------- helpers
def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kw)


def lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def layer_crop(layer: Image.Image, ox: int, oy: int, cw: int, ch: int,
               factor: float, W: int, H: int) -> Image.Image:
    """Crop layer parallax (setengah resolusi) lalu upscale ke frame."""
    lw, lh = layer.size
    sx = lw / SW
    lwc = max(2, int(cw * sx))
    lhc = max(2, int(ch * sx))
    lx = max(0, min(lw - lwc, int(ox * sx * factor)))
    ly = max(0, min(lh - lhc, int(oy * sx * factor)))
    return layer.crop((lx, ly, lx + lwc, ly + lhc)).resize((W, H), Image.Resampling.BILINEAR)


_BADGE_CACHE: dict[tuple, Image.Image] = {}


def badge_img(text: str, size: int) -> Image.Image:
    key = (text, size)
    if key in _BADGE_CACHE:
        return _BADGE_CACHE[key]
    font = ImageFont.truetype(FONT, size)
    w = int(font.getlength(text)) + int(size * 1.6)
    h = int(size * 1.9)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=(22, 18, 16, 228),
                        outline=(244, 185, 66, 255), width=max(2, size // 8))
    d.text((w // 2, h // 2 + 1), text, font=font, fill=(255, 255, 255, 255), anchor="mm")
    _BADGE_CACHE[key] = img
    return img


def smooth(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


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
    return m.group(1).strip()


def gemini_key() -> str:
    return (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            or read_mpt_gemini_key())


def normalize_audio(raw: bytes) -> bytes:
    """Pastikan payload TTS punya container yang bisa dibaca ffmpeg.

    Gemini TTS kadang mengembalikan PCM mentah (24 kHz, 16-bit, mono) tanpa
    header RIFF. ffmpeg menolaknya dengan "Invalid data found". Kita bungkus
    ulang jadi WAV supaya rantai render tidak putus.
    """
    if len(raw) < 2000:
        raise RuntimeError(f"audio terlalu pendek ({len(raw)} bytes)")
    if not any(raw[:4096]):
        raise RuntimeError("audio kosong (silence)")
    head = raw[:4]
    if (head == b"RIFF" or head == b"OggS" or head == b"fLaC"
            or raw[:3] == b"ID3" or raw[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
        return raw
    if len(raw) % 2:
        raw = raw[:-1]
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(raw)
    return buf.getvalue()


# ----------------------------------------------------------------------- TTS
class TTS:
    """Gemini TTS dengan fallback chain multi-model + Edge TTS."""

    MODELS = [
        ("gemini-3.8-flash-tts", True),
        ("gemini-3.8-flash-lite-tts", True),
        ("gemini-3.1-flash-tts-preview", False),
        ("gemini-2.5-pro-preview-tts", False),
    ]

    def __init__(self, backend: str = "auto", cache_dir: Path | None = None):
        self.backend = backend
        self.key = gemini_key()
        self.cache = cache_dir or (ROOT / "production" / "cache" / "tts")
        self.cache.mkdir(parents=True, exist_ok=True)
        if backend == "auto":
            backend = "gemini" if self.key else "edge"
        self.backend = backend
        self.used: list[str] = []

    # --- gemini
    def _request(self, text: str, model: str, voice: str, style: str, use_style: bool) -> bytes:
        content = {"type": "text", "text": text}
        if use_style:
            content["annotations"] = [{"type": "speech_metadata", "style": style}]
        body = {
            "model": model,
            "input": [{"type": "user_input", "content": [content]}],
            "response_format": {"type": "audio"},
            "generation_config": {"speech_config": [{"voice": voice}]},
        }
        req = urllib.request.Request(
            "https://generativelanguage.googleapis.com/v1beta/interactions",
            data=json.dumps(body).encode("utf-8"),
            headers={"x-goog-api-key": self.key, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.load(r)
        items = [c for s in data.get("steps", []) if s.get("type") == "model_output"
                 for c in s.get("content", []) if c.get("type") == "audio" and c.get("data")]
        if not items:
            raise RuntimeError("no audio in Gemini response")
        return base64.b64decode(items[-1]["data"])

    def _gemini(self, text: str, voice: str, style: str) -> bytes:
        chain = [(GEMINI_MODEL, True)] + [m for m in self.MODELS if m[0] != GEMINI_MODEL]
        errors: list[str] = []
        net_fail = 0
        for model, styled in chain:
            for attempt in range(3):
                try:
                    raw = normalize_audio(self._request(text, model, voice, style, styled))
                    self.used.append(model)
                    return raw
                except urllib.error.HTTPError as e:
                    body = e.read().decode(errors="ignore")
                    if e.code == 429 and ("per day" in body or "daily" in body.lower()):
                        errors.append(f"{model}: daily quota")
                        break
                    if e.code == 400 and ("annotation" in body.lower() or "metadata" in body.lower()):
                        break
                    if e.code in (429, 500, 502, 503, 504):
                        wait = min(15 * (attempt + 1), 45)
                        time.sleep(wait)
                        continue
                    errors.append(f"{model}: HTTP {e.code}")
                    break
                except Exception as e:  # noqa: BLE001
                    if is_network_error(e):
                        # koneksi putus (DNS/HTTP): coba lagi dengan jeda, jangan
                        # langsung lompat ke model berikutnya (buang waktu).
                        net_fail += 1
                        errors.append(f"{model}: jaringan: {e!r}")
                        wait = min(20 * (attempt + 1), 90)
                        print(f"    jaringan bermasalah ({e!r}) -> coba lagi dalam {wait}s", flush=True)
                        time.sleep(wait)
                        continue
                    errors.append(f"{model}: {e!r}")
                    time.sleep(5)
                    break
        if net_fail and net_fail == len(errors):
            raise NetworkUnavailable(
                "tidak ada koneksi internet saat synthesis TTS (DNS gagal) - "
                "episode akan dicoba lagi di run berikutnya")
        raise RuntimeError("; ".join(errors[-3:]) or "Gemini TTS failed")

    # --- edge
    def _edge(self, text: str, out_path: Path, voice: str = EDGE_VOICE) -> Path:
        last_err = ""
        for attempt in range(3):
            p = subprocess.run(
                [str(EDGE), "--voice", voice, f"--rate={EDGE_RATE}", f"--pitch={EDGE_PITCH}",
                 "--text", text, "--write-media", str(out_path)],
                capture_output=True, text=True,
            )
            if p.returncode == 0 and out_path.exists() and out_path.stat().st_size > 1000:
                return out_path
            last_err = (p.stderr or p.stdout or "").strip().splitlines()[-1:] or ["?"]
            last_err = last_err[0]
            if "network" in last_err.lower() or "resolve" in last_err.lower() \
                    or "connection" in last_err.lower() or "timed out" in last_err.lower():
                print(f"    edge-tts: jaringan bermasalah -> coba lagi ({last_err})", flush=True)
                time.sleep(20 * (attempt + 1))
                continue
            time.sleep(3)
        if any(k in last_err.lower() for k in ("network", "resolve", "connection", "timed out")):
            raise NetworkUnavailable(f"tidak ada koneksi internet (edge-tts): {last_err}")
        raise RuntimeError(f"edge-tts failed: {last_err}")

    # --- public
    def synth(self, text: str, who: str, out_path: Path) -> tuple[Path, str]:
        """Return (wav path, backend label)."""
        if who == "lumi":
            voice, edge_voice = GEMINI_VOICE_LUMI, EDGE_VOICE
        elif who == "boca":
            voice, edge_voice = GEMINI_VOICE_BOCA, EDGE_VOICE
        else:
            voice = GEMINI_VOICE_GUEST.get(who, GEMINI_VOICE_BOCA)
            edge_voice = EDGE_VOICE_GUEST.get(who, EDGE_VOICE)
        digest = hashlib.md5(f"{who}|{text}".encode("utf-8")).hexdigest()[:10]
        slug = re.sub(r"[^a-z0-9]+", "-", text.lower())[:36]
        cached = self.cache / f"{slug}-{digest}-{voice}.wav"
        # Cache HANYA untuk Gemini: audio Edge punya rate sendiri (EDGE_RATE),
        # jadi tidak boleh memakai ulang wav Gemini (bug: narasi jadi 1.47x lebih lambat).
        if self.backend == "gemini" and cached.exists() and cached.stat().st_size > 5000:
            try:
                raw = normalize_audio(cached.read_bytes())
            except RuntimeError:
                raw = b""
            if raw:
                if raw != cached.read_bytes():
                    cached.write_bytes(raw)
                out_path.write_bytes(raw)
                return out_path, "gemini"   # cache hanya berisi audio Gemini
        if self.backend == "gemini":
            try:
                raw = self._gemini(text, voice, GEMINI_STYLE)
                cached.write_bytes(raw)
                shutil.copy2(cached, out_path)
                return out_path, "gemini"
            except NetworkUnavailable:
                raise
            except Exception as e:  # noqa: BLE001
                print(f"    Gemini fallback -> Edge ({who}): {e}", flush=True)
        self._edge(text, out_path.with_suffix(".mp3"), edge_voice)
        return out_path.with_suffix(".mp3"), "edge"


def to_wav(src: Path, dst: Path) -> None:
    run(["ffmpeg", "-y", "-i", str(src), "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(dst)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path),
    ])
    return float(out.decode().strip())


# --------------------------------------------------- speech driven word timing
def count_syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 1
    return max(1, len(re.findall(r"[aeiouy]+", w)))


def speech_env(path: Path) -> np.ndarray:
    data, sr = read_wav_mono(path)
    hop = max(1, sr // SR_ENV)
    n = len(data) // hop
    if n < 3:
        return np.zeros(SR_ENV, dtype=np.float32)
    env = np.array([float(np.sqrt(np.mean(data[i * hop:(i + 1) * hop] ** 2))) for i in range(n)],
                   dtype=np.float32)
    peak = float(env.max())
    return env / peak if peak > 0 else env


def speech_peaks(env: np.ndarray) -> list[int]:
    n = len(env)
    peaks: list[int] = []
    min_dist = int(0.085 * SR_ENV)
    win = int(0.16 * SR_ENV)
    for i in range(1, n - 1):
        if env[i] < 0.20 or env[i] < env[i - 1] or env[i] <= env[i + 1]:
            continue
        lo, hi = max(0, i - win), min(n, i + win)
        if env[i] - float(env[lo:hi].min()) < 0.05:
            continue
        if not peaks or i - peaks[-1] >= min_dist:
            peaks.append(i)
        elif env[i] > env[peaks[-1]]:
            peaks[-1] = i
    return peaks


def speech_valleys(env: np.ndarray) -> list[int]:
    n = len(env)
    if n < 3:
        return []
    thr = float(env.max()) * 0.55
    out: list[int] = []
    for i in range(1, n - 1):
        if env[i] <= env[i - 1] and env[i] < env[i + 1] and env[i] < thr:
            if not out or i - out[-1] >= int(0.05 * SR_ENV):
                out.append(i)
            elif env[i] < env[out[-1]]:
                out[-1] = i
    return out


def align_words(words: list[str], audio: Path, line_dur: float) -> list[tuple[str, float, float]]:
    syl = [count_syllables(w) for w in words]
    total = sum(syl)
    env = speech_env(audio)
    peaks = speech_peaks(env)
    valleys = speech_valleys(env)
    if total == 0 or line_dur <= 0 or not peaks:
        step = line_dur / max(len(words), 1)
        return [(w, i * step, (i + 1) * step) for i, w in enumerate(words)]
    peak_t = [p / SR_ENV for p in peaks]
    syl_t = []
    for k in range(total):
        idx = k * (len(peak_t) - 1) / max(total - 1, 1)
        lo = int(math.floor(idx))
        hi = min(lo + 1, len(peak_t) - 1)
        frac = idx - lo
        syl_t.append(peak_t[lo] * (1 - frac) + peak_t[hi] * frac)
    val_t = [v / SR_ENV for v in valleys]
    bounds: list[float] = []
    cum = 0
    for s in syl[:-1]:
        cum += s
        exp = syl_t[min(cum, total - 1)]
        near = [v for v in val_t if abs(v - exp) <= 0.14]
        bounds.append(min(near, key=lambda v: abs(v - exp)) if near else exp)
    for i in range(1, len(bounds)):
        if bounds[i] < bounds[i - 1]:
            bounds[i] = bounds[i - 1]
    start = max(0.0, peak_t[0] - 0.09)
    end = min(line_dur, peak_t[-1] + 0.16)
    out: list[tuple[str, float, float]] = []
    prev = start
    for i, w in enumerate(words):
        stop = bounds[i] if i < len(bounds) else end
        stop = max(stop, prev + 0.07)
        out.append((w, prev, stop))
        prev = stop
    out[-1] = (out[-1][0], out[-1][1], max(end, out[-1][1] + 0.06))
    return out


def align_translation(words: list[str], audio: Path, line_dur: float) -> list[tuple[str, float, float]]:
    env = speech_env(audio)
    valleys = speech_valleys(env)
    peaks = speech_peaks(env)
    if not words:
        return []
    if not valleys and not peaks:
        step = line_dur / len(words)
        return [(w, i * step, (i + 1) * step) for i, w in enumerate(words)]
    marks = ([v / SR_ENV for v in valleys] if valleys else [p / SR_ENV for p in peaks])
    if len(marks) < 2:
        marks = [0.0, line_dur]
    syl = [count_syllables(w) for w in words]
    total = max(sum(syl), 1)
    idxs, cum = [], 0
    for s in syl:
        idxs.append(cum / total)
        cum += s
    idxs.append(1.0)
    times = [marks[min(len(marks) - 1, round(u * (len(marks) - 1)))] for u in idxs]
    out = []
    for i, w in enumerate(words):
        t0 = max(0.0, min(line_dur, times[i]))
        t1 = max(t0 + 0.06, min(line_dur, times[i + 1]))
        out.append((w, t0, t1))
    for i in range(1, len(out)):
        if out[i][1] < out[i - 1][1]:
            out[i] = (out[i][0], out[i - 1][1], max(out[i][2], out[i][1] + 0.06))
    return out


# ------------------------------------------------------------------- subtitle
class Subtitle:
    """Caption dual-layer tanpa panel; reveal kata-per-kata + highlight."""

    def __init__(self, baby_font, adult_font):
        self.bf = baby_font
        self.af = adult_font
        self.probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        self.lines: dict[int, list] = {}   # shot n -> list of line layouts
        self.glyph_cache: dict[tuple, Image.Image] = {}

    def _rows(self, entries, font, max_w):
        rows: list[list] = [[]]
        cur = 0.0
        space = self.probe.textlength(" ", font=font)
        for e in entries:
            w = self.probe.textlength(e[0], font=font)
            add = w if not rows[-1] else w + space
            if rows[-1] and cur + add > max_w:
                rows.append([e])
                cur = w
            else:
                rows[-1].append(e)
                cur += add
        out = []
        for row in rows:
            width = sum(self.probe.textlength(e[0], font=font) for e in row) + space * (len(row) - 1)
            out.append(dict(words=row, width=width))
        return out

    def build_line(self, shot_n: int, line_idx: int, who: str,
                   baby: list[tuple], adult: list[tuple]) -> None:
        # Satu track saja: caption besar. caption_adult tetap disimpan di data
        # (untuk SEO/aksesibilitas) tapi tidak pernah digambar menumpuk.
        baby_rows = self._rows(baby, self.bf, 940)
        lh1 = int(self.bf.size * 1.24)
        total = len(baby_rows) * lh1
        y = CAPTION_BOTTOM - total
        layout = {"baby": [], "adult": [], "who": who, "top": y}
        for row in baby_rows:
            x = W / 2 - row["width"] / 2
            for e in row["words"]:
                layout["baby"].append((e[0], e[1], e[2], x, y, self.bf))
                x += self.probe.textlength(e[0], font=self.bf) + self.probe.textlength(" ", font=self.bf)
            y += lh1
        self.lines.setdefault(shot_n, []).append(layout)

    def _glyph(self, word, font, fill, stroke, fatten, scale):
        key = (word, id(font), fill, stroke, fatten, round(scale, 2))
        g = self.glyph_cache.get(key)
        if g is not None:
            return g
        w = int(self.probe.textlength(word, font=font)) + stroke * 4
        h = int(font.size * 2.2)
        tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        td.text((stroke * 2, stroke * 2), word, font=font, fill=(*fill, 255),
                stroke_width=stroke, stroke_fill=(8, 6, 5, 255))
        if fatten:
            td.text((stroke * 2, stroke * 2), word, font=font, fill=(*fill, 255),
                    stroke_width=1, stroke_fill=(*fill, 255))
        bbox = tmp.getbbox()
        if bbox:
            tmp = tmp.crop(bbox)
        if scale != 1.0:
            tmp = tmp.resize((max(1, int(tmp.width * scale)), max(1, int(tmp.height * scale))),
                             Image.Resampling.LANCZOS)
        self.glyph_cache[key] = tmp
        return tmp

    def draw(self, im: Image.Image, shot_n: int, active_idx: int, t: float) -> None:
        layouts = self.lines.get(shot_n) or []
        if not layouts or active_idx < 0 or active_idx >= len(layouts):
            return
        layout = layouts[active_idx]
        for word, t0, t1, x, y, font in layout["baby"]:
            if t < t0:
                continue
            active = t0 <= t < t1
            fill = HILITE if active else WHITE
            g = self._glyph(word, font, fill, 6, True,
                            motion.use_word_pop(t0, t) if active else 1.0)
            im.paste(g, (int(x), int(y - (4 if active else 0))), g)



# -------------------------------------------------------------------- actors
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


def draw_speaker_badge(im: Image.Image, label: str, color, x: float, anchor_y: float,
                       font: ImageFont.FreeTypeFont | None = None) -> None:
    """Nama pembicara sebagai pil di bawah kaki aktor (bukan di tengah layar)."""
    f = font or ImageFont.truetype(FONT, 28)
    d = ImageDraw.Draw(im, "RGBA")
    tw = int(d.textlength(label, font=f))
    y = min(anchor_y + 18, CAPTION_BOTTOM - 60)
    d.rounded_rectangle((x - tw / 2 - 22, y, x + tw / 2 + 22, y + 46), 23,
                        fill=(17, 24, 39, 214))
    d.rounded_rectangle((x - tw / 2 - 12, y + 12, x - tw / 2 - 4, y + 30), 4,
                        fill=(*color, 255))
    d.text((x + 4, y + 23), label, font=f, fill=(*color, 255), anchor="mm")


def actor_state(keys: list[dict], local: float) -> dict:
    if not keys:
        return {}
    i = 0
    for idx, k in enumerate(keys):
        if local >= k["t"]:
            i = idx
    a = keys[i]
    b = keys[min(i + 1, len(keys) - 1)]
    span = max(b["t"] - a["t"], 1e-6)
    u = smooth((local - a["t"]) / span) if b is not a else 0.0
    state = dict(a)
    for field in ("x", "ground", "h", "y"):
        if field in a and field in b:
            state[field] = lerp(a[field], b[field], u)
    arms = a.get("arms")
    if arms:
        state["arm"] = arms[int(local / a.get("period", 0.8)) % len(arms)]
    else:
        state["arm"] = 0
    state["step"] = int(local / 0.24) % 2 if a.get("pose") == "walk" else 0
    return state


CARD_FPS = 12
SCENE_CACHE = ROOT / "production" / "cache" / "scenes"


def build_scene_layers(name: str, tmp: Path):
    """Scene SVG -> plate (sky+mid+ground) + layer awan terpisah (0.55x)."""
    fn = SCENE_SVG.get(name)
    if fn is None:                      # scene lama: fallback mulus
        return build_scene(name, (SW, SH)), None

    out = SCENE_CACHE / name
    out.mkdir(parents=True, exist_ok=True)
    pngs: dict[str, Image.Image] = {}
    for layer, svg in fn(SW, SH).items():
        png = out / f"{layer}.png"
        sp = out / f"{layer}.svg"          # simpan sumber untuk cek perubahan
        stale = True
        if png.exists() and sp.exists():
            stale = sp.read_text(encoding="utf-8") != svg
        if stale:
            sp.write_text(svg, encoding="utf-8")
            render_svg(sp, png, SW, SH, transparent=(layer != "sky"))
        pngs[layer] = Image.open(png).convert("RGBA")

    plate = pngs["sky"]
    for key in ("midground", "ground"):
        plate = Image.alpha_composite(plate, pngs[key])
    cloud = pngs["clouds"]
    return plate, (cloud if cloud.getbbox() else None)


def focus_state(ep: "Episode", shot: "Shot", who: str, local: float) -> dict:
    """State aktor yang jadi subjek layout (spotlight / close-up)."""
    if who == "lumi":
        return actor_state(shot.lumi, local)
    if ep.guest and who == ep.guest:
        return actor_state(shot.guest, local)
    return actor_state(shot.keys, local)


class Art:
    """Sprite & scene cache untuk satu episode."""

    def __init__(self, ep: Episode, tmp: Path):
        self.ep = ep
        self.tmp = tmp
        self.sprites: dict[tuple, Image.Image] = {}
        self.lumis: dict[tuple, Image.Image] = {}
        self.guests: dict[tuple, Image.Image] = {}
        self.plates: dict[str, Image.Image] = {}
        self.fx: dict[str, dict] = {}
        self.clouds: dict[str, Image.Image | None] = {}
        self.cards: dict[str, list[Path]] = {}
        self.spots: dict[str, list[Image.Image]] = {}
        self.prop_sprites: dict[tuple, props_svg.PropSprite] = {}
        self.prop_imgs: dict[tuple, Image.Image] = {}
        self.sprite_paths: dict[tuple, str] = {}
        self._tilt: dict[tuple, Image.Image] = {}
        self._card_open: dict[tuple, Image.Image] = {}

    # ------------------------------------------------------------- tilt bob
    def tilt(self, key: tuple, step: int) -> Image.Image:
        """Varian tilt -2/0/+2 derajat, dimuat lazy (LRU 24) saat bicara."""
        if step == 0:
            return self.sprites[key]
        ck = (key, step)
        img = self._tilt.get(ck)
        if img is None:
            name = self.sprite_paths.get(key)
            if name is None:
                return self.sprites[key]
            path = self.tmp / "sprites" / f"{name}-{'m' if step < 0 else 'p'}.png"
            if not path.exists():
                return self.sprites[key]
            img = Image.open(path).convert("RGBA")
            if len(self._tilt) >= 24:
                self._tilt.pop(next(iter(self._tilt)))
            self._tilt[ck] = img
        return img

    # ------------------------------------------------------------ card frame
    def card_frame(self, key: str, idx: int) -> Image.Image | None:
        frames = self.cards.get(key)
        if not frames:
            return None
        idx = max(0, min(len(frames) - 1, idx))
        ck = (key, idx)
        img = self._card_open.get(ck)
        if img is None:
            img = Image.open(frames[idx]).convert("RGBA")
            if len(self._card_open) >= 8:
                self._card_open.pop(next(iter(self._card_open)))
            self._card_open[ck] = img
        return img

    def build(self) -> None:
        out_dir = self.tmp / "sprites"
        out_dir.mkdir(parents=True, exist_ok=True)
        need_s, need_l = set(), set()
        for shot in self.ep.shots:
            for k in shot.keys:
                steps = (0, 1) if k["pose"] == "walk" else (0,)
                for arm in k.get("arms", [0]):
                    for st in steps:
                        need_s.add((k["expr"], k["pose"], arm, st, k.get("prop")))
            for k in shot.lumi:
                need_l.add((k["expr"], k["pose"]))
        for expr, pose, arm, step, prop in sorted(need_s, key=lambda t: (t[0], t[1], t[2], t[3], str(t[4]))):
            name = f"{expr}-{pose}-a{arm}-s{step}-{(prop or 'none')}"
            png = out_dir / f"{name}.png"
            if not png.exists():
                svg = svg_doc(1080, 1920,
                              character(expr, pose, 540, 620, 1.0, shadow=False,
                                        arm_gesture=arm, mouth=5, step=step, prop=prop, book=False),
                              None)
                sp = out_dir / f"{name}.svg"
                sp.write_text(svg, encoding="utf-8")
                render_svg(sp, png, 1080, 1920, transparent=True)
            key = (expr, pose, arm, step, prop)
            self.sprites[key] = Image.open(png).convert("RGBA").crop((140, 348, 940, 1548))
            self.sprite_paths[key] = name
            # varian bob: rotasi 2 derajat mengelilingi kaki (bukan per frame)
            for tag, ang in (("m", -2.0), ("p", 2.0)):
                tp = out_dir / f"{name}-{tag}.png"
                if not tp.exists():
                    self.sprites[key].rotate(
                        ang, resample=Image.Resampling.BICUBIC,
                        center=(400, 1150)).save(tp)
        for expr, pose in sorted(need_l):
            for mouth in (0, 5):
                name = f"lumi-{expr}-{pose}-m{mouth}"
                png = out_dir / f"{name}.png"
                if not png.exists():
                    svg = svg_doc(1080, 1920, lumi(expr, pose, 540, 620, 1.0, mouth=mouth), None)
                    sp = out_dir / f"{name}.svg"
                    sp.write_text(svg, encoding="utf-8")
                    render_svg(sp, png, 1080, 1920, transparent=True)
                self.lumis[(expr, pose, mouth)] = Image.open(png).convert("RGBA").crop((180, 390, 900, 860))
        need_g = set()
        if self.ep.guest:
            for shot in self.ep.shots:
                for k in shot.guest:
                    for arm in k.get("arms", [0]):
                        need_g.add((self.ep.guest, k["expr"], k["pose"], arm))
        for gid, expr, pose, arm in sorted(need_g):
            name = f"guest-{gid}-{expr}-{pose}-a{arm}"
            png = out_dir / f"{name}.png"
            if not png.exists():
                svg = svg_doc(1080, 1920,
                              guest_svg(gid, expr, pose, 540, 620, 1.0,
                                        arm_gesture=arm, mouth=5), None)
                sp = out_dir / f"{name}.svg"
                sp.write_text(svg, encoding="utf-8")
                render_svg(sp, png, 1080, 1920, transparent=True)
            self.guests[(gid, expr, pose, arm)] = (
                Image.open(png).convert("RGBA").crop((140, 348, 940, 1548)))

        # scene: plate + awan (SVG ber-outline, bukan PIL blur)
        for shot in self.ep.shots:
            if shot.scene not in self.plates:
                plate, cloud = build_scene_layers(shot.scene, self.tmp)
                self.plates[shot.scene] = plate
                self.clouds[shot.scene] = cloud
                if shot.scene not in SCENE_SVG:
                    self.fx[shot.scene] = build_fx_layers(shot.scene)
            for pr in shot.props:
                hh = int(pr.get("h", 220))
                if pr["id"] in props_svg.PROPS:
                    self.prop_sprites[(pr["id"], hh)] = props_svg.build(
                        pr["id"], hh, self.tmp / "props-svg")
                else:
                    self.prop_imgs[(pr["id"], hh)] = prop_lib.build(pr["id"], hh)

        # kartu infografis: 12 fps di-bake, runtime cuma buka + paste
        for shot in self.ep.shots:
            for i, ly in enumerate(shot.layouts or []):
                if ly.get("mode") != "INFOGRAPHIC_CARD":
                    continue
                spec = ly.get("card") or {}
                key = f"s{shot.n:02d}-l{i}"
                dur = float(ly.get("to", 0)) - float(ly.get("from", 0))
                frames = []
                for k in range(max(1, int(dur * CARD_FPS) + 1)):
                    img = layout_lib.draw_card(spec, k / CARD_FPS, k / CARD_FPS, 0.0)
                    p = self.tmp / "cards" / f"{key}-{k:03d}.png"
                    p.parent.mkdir(parents=True, exist_ok=True)
                    img.save(p)
                    frames.append(p)
                self.cards[key] = frames

        # spotlight: 8 langkah fade, mask L (blur hanya di mask)
        for shot in self.ep.shots:
            for i, ly in enumerate(shot.layouts or []):
                if ly.get("mode") != "SPOTLIGHT_EFFECT":
                    continue
                st = focus_state(self.ep, shot, ly.get("focus", "boca"),
                                 float(ly.get("from", 0)) + 0.6)
                if not st:
                    continue
                cx = float(st.get("x", W / 2))
                cy = float(st.get("ground", 1400)) - float(st.get("h", 640)) * 0.55
                if "y" in st and "x" in st and not st.get("ground"):
                    cy = float(st["y"])
                key = f"s{shot.n:02d}-l{i}"
                self.spots[key] = [
                    layout_lib.spot_mask((W, H), cx, cy, ly, step / 7.0)
                    for step in range(8)
                ]

# --------------------------------------------------------------------- audio
def parse_srt(path: Path) -> list[tuple[float, float]]:
    """Ambil (start, end) tiap cue SRT — dipakai untuk reuse VO tanpa TTS."""
    def to_s(t: str) -> float:
        hh, mm, rest = t.split(":")
        ss, ms = rest.replace(",", ".").split(".")
        return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / (10 ** len(ms))

    cues = []
    for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8", errors="ignore").strip()):
        m = re.search(r"(\d\d:\d\d:\d\d[,.]\d+)\s*-->\s*(\d\d:\d\d:\d\d[,.]\d+)", block)
        if m:
            cues.append((to_s(m.group(1)), to_s(m.group(2))))
    return cues


def proportional_words(text: str, dur: float) -> list[tuple[str, float, float]]:
    """Word timing proporsional (reuse VO: audio per baris tidak disimpan)."""
    words = text.split()
    if not words:
        return []
    weights = [max(2, len(w)) for w in words]
    total_w = float(sum(weights))
    out, t = [], 0.0
    for w, wt in zip(words, weights):
        d = dur * wt / total_w
        out.append((w, t, t + d))
        t += d
    return out


def load_vo_reuse(src: Path, ep: Episode):
    """Pakai voiceover.wav + SRT yang sudah ada: NOL panggilan TTS."""
    wav = src / "voiceover.wav"
    srt = sorted(src.glob("*.srt"))
    if not wav.exists() or not srt:
        raise SystemExit(f"reuse-vo: butuh voiceover.wav + .srt di {src}")
    cues = parse_srt(srt[0])
    lines = [(shot, i, ln) for shot in ep.shots for i, ln in enumerate(shot.dialogue)]
    if len(cues) != len(lines):
        raise SystemExit(f"reuse-vo: {len(cues)} cue != {len(lines)} baris dialog")

    lines_info = []
    t = 0.0
    idx = 0
    for shot in ep.shots:
        shot.start = t
        shot.lines = []
        cursor = t + ep.lead_in
        for i, ln in enumerate(shot.dialogue):
            start, end = cues[idx]
            idx += 1
            dur = max(0.4, end - start)
            item = dict(shot=shot, idx=i, who=ln.who, dur=dur,
                        wav=wav, data=None,
                        baby=proportional_words(ln.caption, dur),
                        adult=proportional_words(ln.caption_adult, dur),
                        text=ln.text, caption=ln.caption,
                        caption_adult=ln.caption_adult,
                        start=cursor, end=cursor + dur)
            shot.lines.append(item)
            lines_info.append(item)
            cursor += dur + ep.line_gap
        shot.end = cursor - ep.line_gap + ep.tail
        t = shot.end
    for shot in ep.shots:
        for l in shot.lines:
            l["shot_dur"] = shot.end - shot.start
    total = t
    return wav, lines_info, total


def build_voice_track(ep: Episode, tts: TTS, tmp: Path):
    """Generate semua baris, hitung timing absolut, dan susun track narasi."""
    SR = 48000
    vo_dir = tmp / "vo"
    vo_dir.mkdir(parents=True, exist_ok=True)

    # --- tahap 1: sintesis semua baris dulu, tanpa timing -------------------
    def synth_all(engine):
        items = []
        for shot in ep.shots:
            for i, line in enumerate(shot.dialogue):
                raw, backend = engine.synth(line.text, line.who,
                                            vo_dir / f"s{shot.n:02d}-l{i:02d}-raw.wav")
                wav = vo_dir / f"s{shot.n:02d}-l{i:02d}.wav"
                to_wav(raw, wav)
                items.append(dict(shot=shot, idx=i, line=line, wav=wav,
                                  dur=ffprobe_duration(wav), backend=backend))
        return items

    pending = synth_all(tts)
    # Kuota Gemini bisa habis di tengah episode. Jangan campur Puck + Ardi dalam
    # satu video: kalau ada baris yang jatuh ke Edge, ulang SEMUA baris dengan Edge.
    if tts.backend == "gemini" and any(p["backend"] == "edge" for p in pending):
        print("  ! Gemini gagal di sebagian baris (kuota) -> seluruh episode "
              "diulang dengan Edge agar suara konsisten", flush=True)
        tts = TTS("edge", cache_dir=tts.cache)
        pending = synth_all(tts)

    def raw_length(items) -> float:
        total = 0.0
        for shot in ep.shots:
            ls = [p for p in items if p["shot"] is shot]
            total += (ep.lead_in + sum(p["dur"] for p in ls)
                      + ep.line_gap * max(len(ls) - 1, 0) + ep.tail)
        return total

    def overhead_of(items) -> float:
        """Durasi tetap (lead_in + tail + line_gap) yang TIDAK ikut dipercepat."""
        total = 0.0
        for shot in ep.shots:
            ls = [p for p in items if p["shot"] is shot]
            total += (ep.lead_in + ep.line_gap * max(len(ls) - 1, 0) + ep.tail)
        return total

    # --- tahap 2: TIDAK ada percepatan buatan ------------------------------
    # Kecepatan sudah diatur di sumber suara (EDGE_RATE +47% -> 0.333 s/kata).
    # Kalau narasi tetap lebih panjang dari tier, video dibiarkan lebih panjang.
    # Tidak ada atempo: suara tidak pernah di-stretch.
    raw_len = raw_length(pending)
    if raw_len > ep.duration_target * 1.01:
        print(f"  narasi {raw_len:.1f}s > target {ep.duration_target:.0f}s "
              f"- dibiarkan lebih panjang (tanpa percepatan)")

    # --- tahap 3: alignment kata + durasi per shot --------------------------
    lines_info = []      # per line: dict(shot, idx, who, start, end, dur, baby[], adult[])
    shot_durs = []
    for shot in ep.shots:
        shot_lines = []
        for p in [x for x in pending if x["shot"] is shot]:
            data, sr = read_wav_mono(p["wav"])
            line = p["line"]
            baby = align_words(line.caption.split(), p["wav"], p["dur"])
            adult = align_translation(line.caption_adult.split(), p["wav"], p["dur"])
            shot_lines.append(dict(shot=shot, idx=p["idx"], who=line.who, dur=p["dur"],
                                   wav=p["wav"], data=data, baby=baby, adult=adult,
                                   text=line.text, caption=line.caption,
                                   caption_adult=line.caption_adult))
        need = ep.lead_in + sum(l["dur"] for l in shot_lines) + ep.line_gap * max(len(shot_lines) - 1, 0) + ep.tail
        shot_durs.append(need)
        for l in shot_lines:
            l["shot_dur"] = need
        lines_info.extend(shot_lines)

    total_raw = sum(shot_durs)
    # jangan pernah menambah lebih dari MAX_PAD: silence panjang = retensi mati
    total = max(total_raw, min(ep.duration_target, total_raw * MAX_PAD))
    extra = total - total_raw
    # distribute extra proportionally ke shot
    durs = [d + extra * (d / total_raw if total_raw else 0) for d in shot_durs]

    # absolute timeline
    t = 0.0
    for shot, d in zip(ep.shots, durs):
        shot.start = t
        shot.end = t + d
        t += d
    for shot in ep.shots:
        cursor = shot.start + ep.lead_in
        shot.lines = []
        for l in [x for x in lines_info if x["shot"] is shot]:
            l["start"] = cursor
            l["end"] = cursor + l["dur"]
            shot.lines.append(l)
            cursor += l["dur"] + ep.line_gap

    n_total = int(math.ceil(total * SR))
    track = np.zeros(n_total, dtype=np.float32)
    for l in lines_info:
        s = int(l["start"] * SR)
        data = l["data"]
        e = min(n_total, s + len(data))
        if e > s:
            track[s:e] += data[: e - s]
    vo_path = vo_dir / "voiceover.wav"
    write_wav(vo_path, np.stack([track, track], axis=1))
    (vo_dir / "timeline.json").write_text(json.dumps({
        "duration": total,
        "lines": [{"shot": l["shot"].n, "idx": l["idx"], "who": l["who"],
                   "start": l["start"], "end": l["end"], "dur": l["dur"],
                   "text": l["text"]} for l in lines_info],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    return vo_path, lines_info, total


def build_mix(ep: Episode, vo_path: Path, lines_info, total: float, tmp: Path) -> tuple[Path, list[dict]]:
    vo_dir = tmp / "vo"
    music = build_music(total)
    events = []
    for shot in ep.shots:
        for off, name, gain in shot.sfx:
            events.append({"time": shot.start + off, "name": name, "gain": gain})
    mixed = vo_dir / "mix.wav"
    mix_audio(vo_path, music, events, total, mixed, music_gain=0.52, sfx_gain=0.85)
    final = vo_dir / "audio.wav"
    run(["ffmpeg", "-y", "-i", str(mixed), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
         "-t", f"{total:.3f}", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(final)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return final, events


def audio_envelope(audio: Path, total: float) -> np.ndarray:
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(audio), "-f", "s16le",
                                   "-ac", "1", "-ar", "8000", "-"])
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    frames = int(math.ceil(total * FPS))
    spf = 8000.0 / FPS
    env = np.zeros(frames, dtype=np.float32)
    for i in range(frames):
        a, b = int(i * spf), int((i + 1) * spf)
        seg = samples[a:b]
        if len(seg):
            env[i] = float(np.sqrt(np.mean(seg * seg)))
    env = np.convolve(env, np.ones(5, dtype=np.float32) / 5.0, mode="same")
    p95 = float(np.percentile(env, 95)) if env.size else 1.0
    env = np.clip((env - 0.008) / max(p95 - 0.008, 1e-6), 0.0, 1.0)
    return env ** 0.65


# -------------------------------------------------------------------- render
SHADOW_BLOB: Image.Image | None = None


def shadow_blob() -> Image.Image:
    global SHADOW_BLOB
    if SHADOW_BLOB is None:
        blob = Image.new("RGBA", (480, 120), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blob)
        bd.ellipse((20, 20, 460, 100), fill=(0, 0, 0, 110))
        SHADOW_BLOB = blob.filter(ImageFilter.GaussianBlur(14))
    return SHADOW_BLOB


def scale_shot_timings(ep: Episode) -> None:
    """Skalakan timing JSON (est_seconds) ke durasi VO nyata.

    Keyframes, layout numerik, dan prop numerik ditulis saat storyboard masih
    memakai est_seconds (mis. 6.6s). VO asli bisa 11s. Tanpa fungsi ini, pose
    terakhir berhenti di tengah shot dan kartu muncul terlalu cepat.
    Blok ber-`on_line` tidak diskalakan karena langsung diikat ke baris dialog.
    """
    if getattr(ep, "_timings_scaled", False):
        return
    for shot in ep.shots:
        est = max(1.0, float(shot.est or 6.0))
        actual = max(0.1, shot.end - shot.start)
        ratio = max(0.35, min(3.0, actual / est))

        for actor in (shot.keys, shot.lumi, shot.guest):
            for k in actor or []:
                if "t" not in k:
                    continue
                try:
                    k["t"] = round(max(0.0, min(actual - 0.05,
                                                float(k["t"]) * ratio)), 3)
                except (TypeError, ValueError):
                    pass

        for ly in shot.layouts or []:
            if ly.get("on_line") is not None:
                continue
            try:
                f0 = float(ly.get("from", 0.0)) * ratio
                f1 = float(ly.get("to", 0.0)) * ratio
            except (TypeError, ValueError):
                continue
            f1 = min(f1, f0 + 3.8)          # kartu/layout tidak boleh >3.8s
            ly["from"] = round(max(0.0, min(actual, f0)), 3)
            ly["to"] = round(max(ly["from"] + 0.2, min(actual, f1)), 3)

        for pr in shot.props or []:
            if pr.get("on_line") is not None:
                continue
            for key in ("t_in", "t_out"):
                if key in pr:
                    try:
                        pr[key] = round(max(0.0, min(actual,
                                                    float(pr[key]) * ratio)), 3)
                    except (TypeError, ValueError):
                        pass

        # Jangan normalize di sini: layout ber-on_line belum punya from/to.
    ep._timings_scaled = True


def bind_line_motion(ep: Episode) -> None:
    """Terjemahkan `on_line` / `target` ke detik setelah timing VO diketahui.

    Rulebook motion: layout & prop tidak boleh pakai detik hardcoded; ikat ke
    baris dialog. `on_line` (dan `to_line`) dihitung dari shot.lines.
    """
    for shot in ep.shots:
        dur = max(0.1, shot.end - shot.start)
        base = shot.start
        lines = shot.lines or []

        def _line_span(a: int, b: int) -> tuple[float, float]:
            a = max(0, min(len(lines) - 1, int(a)))
            b = max(a, min(len(lines) - 1, int(b)))
            f = max(0.0, float(lines[a]["start"]) - base)
            t = min(dur, float(lines[b]["end"]) - base)
            return f, max(f + 0.4, t)

        for ly in shot.layouts or []:
            target = ly.get("target")
            if target and not ly.get("focus"):
                ly["focus"] = ep.guest if target == "guest" else target
            if ly.get("on_line") is not None and lines:
                f, t = _line_span(ly["on_line"], ly.get("to_line", ly["on_line"]))
                cap = float(ly.get("max_span", 3.7))
                ly["from"], ly["to"] = round(f, 3), round(min(t, f + cap), 3)
        for pr in shot.props or []:
            if pr.get("on_line") is None or not lines:
                continue
            f, t = _line_span(pr["on_line"], pr.get("to_line", pr["on_line"]))
            pr["t_in"] = round(f, 3)
            if pr.get("to_line") is not None:
                pr["t_out"] = round(max(f + 0.6, min(t, f + float(pr.get("max_span", 3.6)))), 3)
            elif "t_out" not in pr:
                pr["t_out"] = round(min(dur, f + 3.2), 3)
        if shot.layouts:
            shot.layouts = layout_lib.normalize(shot.layouts, dur)


def render_episode(ep: Episode, outdir: Path, tmp: Path, tts_backend: str | None = None,
                   verbose: bool = True, reuse_vo: Path | None = None) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)
    tts = TTS(tts_backend or TTS_BACKEND, cache_dir=tmp.parent / "cache" / "tts")

    if verbose:
        print(f"[{ep.id}] {ep.title}")
    if reuse_vo:
        vo_path, lines_info, total = load_vo_reuse(Path(reuse_vo), ep)
        if verbose:
            print(f"  reuse VO: {reuse_vo} (tanpa TTS)")
    else:
        vo_path, lines_info, total = build_voice_track(ep, tts, tmp)
    if verbose:
        for l in lines_info:
            print(f"  shot {l['shot'].n} line {l['idx']} ({l['who']}): {l['dur']:.2f}s  {l['text'][:46]}")
        print(f"  total {total:.2f}s")

    # timing JSON (est_seconds) diskalakan ke VO nyata, lalu blok on_line
    # diikat ke baris dialog dan layout dinormalkan ke durasi shot.
    scale_shot_timings(ep)
    bind_line_motion(ep)

    audio_path, events = build_mix(ep, vo_path, lines_info, total, tmp)
    env = audio_envelope(audio_path, total)

    art = Art(ep, tmp)
    art.build()

    impulses: dict[int, list[float]] = {}
    for _shot in ep.shots:
        _times = [0.0]
        _prev = None
        for _k in _shot.keys:
            _sig = (_k.get("expr"), _k.get("pose"), tuple(_k.get("arms") or ()))
            if _prev is not None and _sig != _prev:
                _times.append(float(_k["t"]))
            _prev = _sig
        impulses[_shot.n] = sorted(set(_times))

    subs = Subtitle(ImageFont.truetype(FONT, SIZE_BABY), ImageFont.truetype(FONT, SIZE_ADULT))
    for l in lines_info:
        baby = [(w, l["start"] + t0, l["start"] + t1) for w, t0, t1 in l["baby"]]
        adult = [(w, l["start"] + t0, l["start"] + t1) for w, t0, t1 in l["adult"]]
        subs.build_line(l["shot"].n, l["idx"], l["who"], baby, adult)

    from collections import OrderedDict
    scaled: "OrderedDict[tuple, Image.Image]" = OrderedDict()
    lumi_scaled: "OrderedDict[tuple, Image.Image]" = OrderedDict()
    blob = shadow_blob()

    def sprite_for(state, h, tilt=0):
        key = (state["expr"], state["pose"], state["arm"], state["step"],
               state.get("prop"), h, tilt)
        got = scaled.get(key)
        if got is None:
            skey = (state["expr"], state["pose"], state["arm"], state["step"], state.get("prop"))
            src = art.sprites[skey] if tilt == 0 else art.tilt(skey, tilt)
            w = max(1, int(round(800 * h / 1200)))
            got = src.resize((w, h), Image.Resampling.LANCZOS)
            scaled[key] = got
            if len(scaled) > 120:
                scaled.popitem(last=False)
        else:
            scaled.move_to_end(key)
        return got

    def lumi_for(state, h, mouth):
        key = (state["expr"], state["pose"], mouth, h)
        got = lumi_scaled.get(key)
        if got is None:
            src = art.lumis[(state["expr"], state["pose"], mouth)]
            w = max(1, int(round(720 * h / 470)))
            got = src.resize((w, h), Image.Resampling.LANCZOS)
            lumi_scaled[key] = got
            if len(lumi_scaled) > 40:
                lumi_scaled.popitem(last=False)
        else:
            lumi_scaled.move_to_end(key)
        return got

    # index baris aktif per frame
    line_bounds = [(l["start"], l["end"], l["shot"].n, l["idx"], l["who"]) for l in lines_info]

    out_mp4 = outdir / f"{ep.id.lower()}-v4.mp4"
    log = tmp / "ffmpeg-render.log"
    frames = int(math.ceil(total * FPS))
    _limit = int(os.environ.get("BOCA_FRAME_LIMIT", "0") or 0)
    if _limit:
        frames = min(frames, _limit)
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(audio_path),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out_mp4),
    ]
    t0 = time.time()
    with open(log, "wb") as err:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=err)
        assert proc.stdin is not None
        for f in range(frames):
            t = f / FPS
            shot = next((s for s in ep.shots if s.start <= t < s.end), ep.shots[-1])
            local = t - shot.start
            prog = local / max(shot.end - shot.start, 1e-6)

            # ---- mode layout per beat (WIDE / CARD / CLOSEUP / SPOTLIGHT)
            lys = shot.layouts or []
            lay = layout_lib.active(lys, local) if lys else {"mode": "WIDE_STAGE"}
            mode = lay.get("mode", "WIDE_STAGE")
            ly_key = f"s{shot.n:02d}-l{lys.index(lay) if lay in lys else 0}"
            card_u = 0.0
            if mode == "INFOGRAPHIC_CARD":
                card_u = motion.use_ease_out_cubic(
                    max(0.0, min(1.0, (local - float(lay.get("from", 0))) / 0.35)))
            card_active = mode == "INFOGRAPHIC_CARD" and card_u > 0.02

            active = next((lb for lb in line_bounds if lb[0] <= t < lb[1]), None)
            speaker = active[4] if active else None
            active_idx = active[3] if active else -1

            camd = shot.cam
            ec = motion.use_ease_out_cubic(prog)   # start snappy, settle halus
            fx = camd["fx"][0] + (camd["fx"][1] - camd["fx"][0]) * ec
            fy = camd["fy"][0] + (camd["fy"][1] - camd["fy"][0]) * ec
            zs = camd.get("z", (1.0, 1.0))
            z = max(1.0, zs[0] + (zs[1] - zs[0]) * ec)
            bst = actor_state(shot.keys, local)
            if mode == "CLOSEUP_EMPHASIS":
                st_f = focus_state(ep, shot, lay.get("focus", "boca"), local)
                if st_f:
                    fx, fy, z = layout_lib.closeup_camera(lay, local, st_f, W, H)
            elif mode == "INFOGRAPHIC_CARD":
                z = max(1.0, z * 0.94)
            imp_cam = None
            for kk in shot.keys:
                if kk.get("expr") == "shock" and local >= kk["t"]:
                    imp_cam = kk["t"]
            if local < 0.30 and any(e["name"] == "whoosh" for e in events
                                    if abs(e["time"] - shot.start) < 0.35):
                imp_cam = 0.0
            shx, shy = motion.use_camera_shake(local, imp_cam, 8.0) if imp_cam is not None else (0, 0)
            zscale = 1.0 + (z - 1.0) * 0.55      # push-in ikut mendekatkan aktor
            scene = art.plates[shot.scene]
            cw, ch = int(W / z), int(H / z)
            # kamera tidak pernah mati: offset mikro sinusoidal
            bx, by = motion.use_camera_breath(t)
            ox = int(fx * (scene.width - cw)) + bx + shx
            oy = int(fy * (scene.height - ch)) + by + shy
            ox = max(0, min(scene.width - cw, ox))
            oy = max(0, min(scene.height - ch, oy))
            base = scene.crop((ox, oy, ox + cw, oy + ch))
            if (cw, ch) != (W, H):
                base = base.resize((W, H), Image.Resampling.LANCZOS)
            base = base.convert("RGBA")
            cloud_layer = art.clouds.get(shot.scene)
            if cloud_layer is not None:
                fcl = 0.55
                cx0 = max(0, min(scene.width - cw, int(ox * fcl)))
                cy0 = max(0, min(scene.height - ch, int(oy * fcl)))
                crop = cloud_layer.crop((cx0, cy0, cx0 + cw, cy0 + ch))
                if crop.size != (W, H):
                    crop = crop.resize((W, H), Image.Resampling.LANCZOS)
                base.alpha_composite(crop.convert("RGBA"))
            fx_layers = art.fx.get(shot.scene) or {}
            atm = fx_layers.get("atm")
            if atm is not None:
                # parallax jauh: 0.45x kecepatan kamera
                base.alpha_composite(layer_crop(atm, ox, oy, cw, ch, 0.45, W, H))
            # Living World: glow/partikel (awan sudah di layer parallax)
            motion.use_ambient(base, shot.scene, t, seed=shot.n,
                               clouds=(cloud_layer is None and atm is None))

            if mode == "SPOTLIGHT_EFFECT":
                masks = art.spots.get(ly_key)
                if masks:
                    step = min(7, int(max(0.0, (local - float(lay.get("from", 0)))) / 0.45 * 7))
                    shade = Image.new("RGBA", (W, H), (8, 10, 14, 255))
                    shade.putalpha(masks[step])
                    base.alpha_composite(shade)

            lstate = actor_state(shot.lumi, local)
            if lstate and not (card_active and card_u > 0.55):
                lh = int(round(min(lstate.get("h", 236) * (0.85 + 0.15 * zscale), 900) / 8.0) * 8)
                mouth_flag = 5 if speaker == "lumi" else 0
                lumi = lumi_for(lstate, lh, mouth_flag)
                lx = int(lstate["x"])
                if mode == "CLOSEUP_EMPHASIS":
                    target_l = 540.0 if focus_who == "lumi" else 1240.0
                    lx = int(lstate["x"] + (target_l - lstate["x"]) * u_c)
                ly = int(lstate.get("y", 1100)) + int(math.sin(local * 2.2) * 14)
                if mouth_flag != 5:
                    tilt_l = math.sin(local * 1.9 + shot.n) * 3.0
                    if abs(tilt_l) > 0.4:
                        lumi = lumi.rotate(tilt_l, resample=Image.Resampling.BICUBIC, expand=True)
                base.paste(lumi, (lx - lumi.width // 2, ly - lumi.height // 2), lumi)
                if mouth_flag == 5:
                    amt = float(env[f]) if speaker == "lumi" else 0.0
                    draw_mouth(base, lx, ly + int(lh * 0.643), lh, amt, "smile")

            gx = gg = None
            gstate = actor_state(shot.guest, local)
            if gstate and ep.guest and not (card_active and card_u > 0.55):
                gh = int(round(min(gstate["h"] * zscale, gstate["ground"] + 240) / 8.0) * 8)
                gsrc = (art.guests.get((ep.guest, gstate["expr"], gstate["pose"], gstate["arm"]))
                        or art.guests.get((ep.guest, gstate["expr"], "stand", 0)))
                if gsrc is not None:
                    gw = max(1, int(round(800 * gh / 1200)))
                    gsprite = gsrc.resize((gw, gh), Image.Resampling.LANCZOS)
                    gimp = [float(k["t"]) for k in shot.guest if local >= k["t"]]
                    if gimp:
                        gsx, gsy = motion.use_squash(local, gimp[-1])
                        if abs(gsy - 1.0) > 0.004:
                            gsprite = gsprite.resize((max(1, int(gsprite.width * gsx)),
                                                      max(1, int(gh * gsy))),
                                                     Image.Resampling.LANCZOS)
                            gh = gsprite.height
                    gx = int(gstate["x"])
                    gg = int(gstate["ground"])
                    if mode == "CLOSEUP_EMPHASIS":
                        target_g = 540.0 if focus_who == ep.guest else 1240.0
                        gx = int(gstate["x"] + (target_g - gstate["x"]) * u_c)
                    gtop = gg - gh + motion.use_breath(shot.n * 29 + 7, local)
                    gsw = int(gsprite.width * 0.62)
                    gsh = blob.resize((max(8, gsw * 2), max(8, int(gsw * 0.5))),
                                      Image.Resampling.BILINEAR)
                    base.paste(gsh, (gx - gsw, gg - gsh.height // 2), gsh)
                    base.paste(gsprite, (gx - gsprite.width // 2, gtop), gsprite)
                    amt_g = float(env[f]) if speaker == ep.guest else 0.0
                    draw_mouth(base, gx, gtop + int(gh * 0.393333), gh, amt_g, "line")

            st = bst
            lscale, ldx = 1.0, 0.0
            lground = float(st["ground"])
            u_c = 1.0
            if mode == "CLOSEUP_EMPHASIS":
                u_c = motion.use_ease_out_cubic(
                    max(0.0, min(1.0, (local - float(lay.get("from", 0))) / 0.35)))
            focus_who = lay.get("focus", "boca") if mode == "CLOSEUP_EMPHASIS" else "boca"
            if card_active:
                lscale = 1.0 - 0.48 * card_u
                ldx = (150.0 - float(st["x"])) * card_u
                lground = float(st["ground"]) + (1810.0 - float(st["ground"])) * card_u
            elif mode == "CLOSEUP_EMPHASIS":
                target = 540.0 if focus_who == "boca" else -160.0
                ldx = (target - float(st["x"])) * u_c
            h = int(round(min(st["h"] * zscale * lscale, st["ground"] + 260) / 8.0) * 8)
            env_b = float(env[f]) if speaker == "boca" else 0.0
            tilt_step = 0
            if env_b > 0.08 and not card_active:
                ang_b = math.sin(local * 2 * math.pi * 1.7) * 2.0
                tilt_step = -1 if ang_b < -0.7 else (1 if ang_b > 0.7 else 0)
            sprite = sprite_for(st, h, tilt_step)
            x = int(st["x"] + ldx)
            ground = int(lground)
            imp_s = max([q for q in impulses.get(shot.n, [0.0]) if local >= q], default=None)
            sx_s, sy_s = motion.use_squash(local, imp_s) if imp_s is not None else (1.0, 1.0)
            if abs(sy_s - 1.0) > 0.004:
                sprite = sprite.resize((max(1, int(sprite.width * sx_s)),
                                        max(1, int(h * sy_s))), Image.Resampling.LANCZOS)
            h = sprite.height
            top = (ground - h + motion.use_breath(shot.n * 13, local)
                   + (int(math.sin(local * 4.1) * 3) if env_b > 0.15 else 0))

            sw = int(sprite.width * 0.62)
            sh = blob.resize((max(8, sw * 2), max(8, int(sw * 0.5))), Image.Resampling.BILINEAR)
            base.paste(sh, (x - sw, ground - sh.height // 2), sh)
            base.paste(sprite, (x - sprite.width // 2, top), sprite)

            mouth_y = top + int(h * 0.393333)
            amt = float(env[f]) if speaker == "boca" else 0.0
            draw_mouth(base, x, mouth_y, h, amt, "line")
            if ((local + (shot.n * 0.7) % 4.0) % 4.0) < 0.12:
                draw_blink(base, x, top, h)

            # ---- props / callouts / loupe (screen-space, di atas aktor)
            for pr in ([] if card_active else shot.props):
                p_in = float(pr.get("t_in", 0.0))
                p_out = float(pr.get("t_out", max(0.2, shot.end - shot.start)))
                if not (p_in <= local <= p_out):
                    continue
                ph = int(pr.get("h", 220))
                sprite_p = art.prop_sprites.get((pr["id"], ph))
                if sprite_p is not None:
                    pimg = sprite_p.frame(local - p_in)      # animasi scripted
                else:
                    pimg = art.prop_imgs.get((pr["id"], ph)) or prop_lib.build(pr["id"], ph)
                sc = motion.use_spring_pop((local - p_in) / 0.42, 1.12)
                if (p_out - local) < 0.30:
                    sc *= motion.use_ease_out_expo((p_out - local) / 0.30)
                anim_p = pr.get("anim", "pop_float")
                seed_p = int(hashlib.md5(pr["id"].encode()).hexdigest()[:4], 16) % 97
                dy_p = int(round(math.sin(local * 3.0 + seed_p) * 8)) if "float" in anim_p else 0
                tilt_p = math.sin(local * 2.1 + seed_p) * 2.0 if anim_p in ("tilt", "pop_float") else 0.0
                pw, phh = max(1, int(pimg.width * sc)), max(1, int(pimg.height * sc))
                if (pw, phh) != pimg.size:
                    pimg = pimg.resize((pw, phh), Image.Resampling.LANCZOS)
                if abs(tilt_p) > 0.3:
                    pimg = pimg.rotate(tilt_p, resample=Image.Resampling.BICUBIC, expand=True)
                px = int(pr.get("x", W // 2))
                py = int(pr.get("y", 900)) + dy_p
                base.paste(pimg, (px - pimg.width // 2, py - pimg.height // 2), pimg)
                if pr.get("badge"):
                    bimg = badge_img(str(pr["badge"]), max(20, int(ph * 0.12)))
                    base.paste(bimg, (px - bimg.width // 2, py + pimg.height // 2 + 8), bimg)
                lf = pr.get("loupe_from")
                if lf:
                    motion.use_loupe(base, local, p_in + 0.30, (int(lf[0]), int(lf[1])),
                                     (px, py - int(pimg.height * 0.1)),
                                     max(90, int(ph * 0.45)))

            # ---- kartu infografis (frame 12 fps dibuka dari cache)
            if card_active:
                card = art.card_frame(ly_key, int(max(0.0, local - float(lay.get("from", 0))) * CARD_FPS))
                if card is not None:
                    remain = float(lay.get("to", local + 9)) - local
                    pop = motion.use_spring_pop(
                        max(0.0, (local - float(lay.get("from", 0))) / 0.42), 1.10)
                    if remain < 0.30:
                        pop *= motion.use_ease_out_expo(remain / 0.30)
                    if abs(pop - 1.0) > 0.004:
                        card = card.resize((max(1, int(card.width * pop)),
                                            max(1, int(card.height * pop))),
                                           Image.Resampling.LANCZOS)
                    base.paste(card, (540 - card.width // 2, 760 - card.height // 2), card)

            fg_layer = fx_layers.get("fg")
            if fg_layer is not None:
                # foreground depth: 1.30x kecepatan kamera
                base.alpha_composite(layer_crop(fg_layer, ox, oy, cw, ch, 1.30, W, H))

            for ev in events:
                dt = t - ev["time"]
                if 0 <= dt < 0.9 and ev["name"] == "sparkle":
                    d = ImageDraw.Draw(base, "RGBA")
                    for k in range(14):
                        ang = k * 0.7 + dt * 2.2
                        rr = 120 + dt * 420
                        sx = W / 2 + math.cos(ang) * rr * 0.9
                        sy = 820 + math.sin(ang) * rr * 0.7
                        s = 10 * (1 - dt / 0.9) + 3
                        d.ellipse((sx - s, sy - s, sx + s, sy + s), fill=(255, 240, 190, 210))

            # transisi: wipe garis kecepatan 0.30s di awal tiap shot
            wipe = local / 0.30
            if wipe < 1.0:
                motion.use_speed_lines(base, wipe, shot.n, 1 if shot.n % 2 else -1)

            if speaker and not card_active:
                f_b = ImageFont.truetype(FONT, 28)
                if speaker == "boca":
                    draw_speaker_badge(base, "BOCA", (255, 138, 148), x, ground, f_b)
                elif speaker == "lumi" and lstate:
                    draw_speaker_badge(base, "LUMI", (255, 214, 102),
                                       lx, int(ly + lh * 0.42), f_b)
                elif gx is not None:
                    nm = GUEST_SPECS.get(speaker, {}).get("name", speaker).upper()
                    draw_speaker_badge(base, nm, (150, 214, 255), gx, gg, f_b)
            motion.use_hud(base, t, ep, t / max(total, 0.1),
                           ImageFont.truetype(FONT, 33))
            subs.draw(base, shot.n, active_idx, t)

            preview_t = shot.start + min(0.9, (shot.end - shot.start) * 0.35)
            if f == int(round(preview_t * FPS)):
                base.convert("RGB").save(tmp / f"preview-{shot.n:02d}.png")
            proc.stdin.write(base.convert("RGB").tobytes())
        proc.stdin.close()
        rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed, see {log}")

    # outputs
    shutil.copy2(vo_path, outdir / "voiceover.wav")
    shutil.copy2(audio_path, outdir / "audio-master.wav")
    write_srt(ep, outdir)
    make_contact_sheet(ep, tmp, outdir)
    make_poster(ep, art, outdir)
    write_readme(ep, outdir, total, tts, events)

    manifest = {
        "id": ep.id, "day": ep.day, "title": ep.title, "series": ep.series,
        "duration": round(total, 3), "resolution": f"{W}x{H}", "fps": FPS,
        "video": out_mp4.name, "facts_status": ep.facts_status,
        "publish": ep.publish,
        "shots": [{"n": s.n, "scene": s.scene,
                   "lines": [{"who": l.who, "text": l.text, "caption": l.caption} for l in s.dialogue]}
                  for s in ep.shots],
        "tts": sorted(set(tts.used)) or ["edge"],
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if verbose:
        print(f"  done -> {out_mp4}")
    return manifest


def write_srt(ep: Episode, outdir: Path) -> Path:
    lines = []
    idx = 0
    for shot in ep.shots:
        for l in shot.lines:
            idx += 1
            lines += [str(idx),
                      f"{fmt_srt(l['start'])} --> {fmt_srt(l['end'])}",
                      l["caption"], l["caption_adult"], ""]
    out = outdir / f"{ep.id.lower()}-v4.srt"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def fmt_srt(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def make_contact_sheet(ep: Episode, tmp: Path, outdir: Path) -> Path:
    sheet = Image.new("RGB", (W, H), (246, 241, 231))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT, 26)
    for i, shot in enumerate(ep.shots):
        p = tmp / f"preview-{shot.n:02d}.png"
        if not p.exists():
            continue
        im = Image.open(p).convert("RGB").resize((270, 480), Image.Resampling.LANCZOS)
        x = 20 + (i % 4) * 260
        y = 80 + (i // 4) * 760
        sheet.paste(im, (x, y))
        d.text((x, y + 490), f"SHOT {shot.n}", font=f, fill=INK)
        d.text((x, y + 524), f"{shot.start:.1f}-{shot.end:.1f}s", font=f, fill=(107, 91, 75))
    out = outdir / "contact-sheet.png"
    sheet.save(out)
    return out


def make_poster(ep: Episode, art: Art, outdir: Path) -> Path:
    shot = ep.shots[0]
    scene = art.plates[shot.scene]
    camd = shot.cam
    zs = camd.get("z", (1.0, 1.0))
    z = max(1.0, (zs[0] + zs[1]) / 2)
    cw, ch = int(W / z), int(H / z)
    ox = int(((camd["fx"][0] + camd["fx"][1]) / 2) * (scene.width - cw))
    oy = int(((camd["fy"][0] + camd["fy"][1]) / 2) * (scene.height - ch))
    base = scene.crop((ox, oy, ox + cw, oy + ch))
    if (cw, ch) != (W, H):
        base = base.resize((W, H), Image.Resampling.LANCZOS)
    base = base.convert("RGB")
    st = actor_state(shot.keys, 1.0)
    if st:
        h = int(round(st.get("h", 660) / 8.0) * 8)
        src = art.sprites.get((st["expr"], st["pose"], st.get("arm", 0), st.get("step", 0), st.get("prop")))
        if src is not None:
            w = int(round(800 * h / 1200))
            sprite = src.resize((w, h), Image.Resampling.LANCZOS)
            x, ground = 300, int(st.get("ground", 1390))
            sw = int(sprite.width * 0.62)
            sh = shadow_blob().resize((max(8, sw * 2), max(8, int(sw * 0.5))), Image.Resampling.BILINEAR)
            base.paste(sh, (x - sw, ground - sh.height // 2), sh)
            base.paste(sprite, (x - sprite.width // 2, ground - h), sprite)
            draw_mouth(base, x, ground - h + int(h * 0.393333), h, 0.0, "line")
    lumi_src = art.lumis.get(("shock", "float", 0)) or art.lumis.get(("happy", "float", 0))
    if lumi_src is not None:
        lh = 250
        lw = int(round(720 * lh / 470))
        li = lumi_src.resize((lw, lh), Image.Resampling.LANCZOS)
        base.paste(li, (740 - lw // 2, 1010 - lh // 2), li)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((60, 80, 1020, 360), 30, fill=(246, 241, 231), outline=INK, width=6)
    d.rectangle((90, 110, 990, 120), fill=(215, 38, 61))
    d.text((540, 150), "BOCA", font=ImageFont.truetype(FONT, 92), fill=INK, anchor="ma")
    d.text((540, 258), ep.title, font=ImageFont.truetype(FONT, 44), fill=INK, anchor="ma")
    # durasi asli mengikuti VO (tidak dipaksa ke tier)
    real_dur = ep.shots[-1].end if ep.shots else ep.duration_target
    d.text((540, 320), f"BOCA · {real_dur:.0f} detik",
           font=ImageFont.truetype(FONT, 24), fill=(107, 91, 75), anchor="ma")
    out = outdir / f"{ep.id.lower()}-v4-poster.png"
    base.save(out)
    return out


def write_readme(ep: Episode, outdir: Path, total: float, tts: TTS, events: list[dict]) -> Path:
    rows = "\n".join(
        f"| {s.n} | {s.start:.2f}-{s.end:.2f}s | {s.scene} | "
        f"{' / '.join(l.caption for l in s.dialogue)} |" for s in ep.shots)
    text = f"""# {ep.id} — {ep.title}

**Status:** {ep.facts_status}
**Durasi:** {total:.1f}s · {W}x{H} · {FPS}fps
**TTS:** {', '.join(sorted(set(tts.used))) or 'edge'}
**SFX event:** {len(events)}

| Shot | Waktu | Scene | Caption |
|---|---|---|---|
{rows}

Template: `boca_pipeline.py` (gaya kartun, Boca tanpa buku, sidekick Lumi,
subtitle tanpa panel + outline kata-per-kata sinkron suara, musik & SFX original).
"""
    out = outdir / "README.md"
    out.write_text(text, encoding="utf-8")
    return out


# ------------------------------------------------------------------------ QA
def qa_checks(ep: Episode, outdir: Path, target: float) -> list[dict]:
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str = ""):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    mp4 = outdir / f"{ep.id.lower()}-v4.mp4"
    add("file exists", mp4.exists(), mp4.name)
    if not mp4.exists():
        return checks
    dur = ffprobe_duration(mp4)
    add("duration >= target - 2.5", dur >= target - 2.5,
        f"{dur:.2f}s vs target {target:.0f}s (lebih panjang = boleh)")
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-of", "default=nw=1:nk=1", str(mp4)]).decode()
    add("resolution 1080x1920", "1080" in probe and "1920" in probe, probe.replace("\n", " "))
    add("size > 1MB", mp4.stat().st_size > 1_000_000, f"{mp4.stat().st_size // 1024}KB")
    loud = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp4), "-af", "loudnorm=print_format=summary",
                           "-f", "null", "-"], capture_output=True, text=True).stderr
    lufs = 0.0
    tp = 0.0
    for line in loud.splitlines():
        if "Input Integrated" in line:
            lufs = float(line.split(":")[1].strip().split()[0])
        if "Input True Peak" in line:
            tp = float(line.split(":")[1].strip().split()[0])
    add("loudness -16..-12 LUFS", -16.5 <= lufs <= -12.0, f"{lufs:.1f} LUFS")
    add("true peak <= -1.0 dBTP", tp <= -1.0, f"{tp:.1f} dBTP")
    # naskah
    bad = []
    for shot in ep.shots:
        for line in shot.dialogue:
            if re.search(r"\b(adek|Adek)\b", line.text):
                bad.append(line.text[:30])
    add("no 'Adek' in VO", not bad, "; ".join(bad))
    add("all shots have dialogue", all(s.dialogue for s in ep.shots))
    add("all lines have captions", all(l.caption and l.caption_adult for s in ep.shots for l in s.dialogue))
    add("caption bottom safe", CAPTION_BOTTOM <= 1600, f"{CAPTION_BOTTOM}px")
    add("srt written", (outdir / f"{ep.id.lower()}-v4.srt").exists())
    add("poster written", (outdir / f"{ep.id.lower()}-v4-poster.png").exists())
    return checks


def qa_report(checks: list[dict]) -> tuple[bool, str]:
    failed = [c for c in checks if not c["ok"]]
    lines = [f"{'PASS' if c['ok'] else 'FAIL'}  {c['name']}  {c['detail']}" for c in checks]
    return (not failed), "\n".join(lines)
