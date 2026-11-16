#!/usr/bin/env python3
"""motion.py — primitif animasi reusable untuk renderer BOCA (Pillow + ffmpeg).

Semua fungsi di sini murni deterministik terhadap (t) sehingga frame bisa
dirender ulang identik.

Hook yang tersedia
------------------
use_ease_out_cubic(u) / use_ease_out_expo(u) / use_spring_pop(u, overshoot)
use_ambient(im, scene, t, seed)        -> lapisan ambient parallax (Living World)
use_camera_breath(t)                   -> offset kamera mikro (tidak ada frame mati)
use_speed_lines(im, p, seed, dir)      -> transisi wipe saat ganti shot
use_hud(im, t, ep, shot_prog)          -> HUD atas + progress bar + rolling counter
use_breath(seed, t)                    -> offset vertikal idle (nafas) aktor
use_word_pop(t0, t)                    -> skala pop kata caption aktif
"""
from __future__ import annotations

import hashlib
import math
import random

from PIL import Image, ImageDraw

# --------------------------------------------------------------------- easing
def clamp01(u: float) -> float:
    return 0.0 if u < 0 else (1.0 if u > 1 else u)


def use_ease_out_cubic(u: float) -> float:
    """Snappy di awal, mendarat halus. Untuk slide/pan."""
    u = clamp01(u)
    return 1 - (1 - u) ** 3


def use_ease_out_expo(u: float) -> float:
    """Untuk kamera & counter: start instan, settle lembut."""
    u = clamp01(u)
    return 1.0 if u >= 1 else 1 - 2 ** (-10 * u)


def use_ease_in_out(u: float) -> float:
    u = clamp01(u)
    return 3 * u * u - 2 * u * u * u


def use_spring_pop(u: float, overshoot: float = 1.08) -> float:
    """Scale 0 -> overshoot -> 1.0 (spring, bukan linear)."""
    u = clamp01(u)
    if u >= 1:
        return 1.0
    # fase naik 0..0.62 (cubic-out), lalu settle 0.62..1 dengan decay
    if u < 0.62:
        k = u / 0.62
        return (1 - (1 - k) ** 3) * overshoot
    k = (u - 0.62) / 0.38
    return overshoot + (1.0 - overshoot) * use_ease_out_cubic(k)


def use_word_pop(t0: float, t: float, dur: float = 0.16) -> float:
    """Pop halus untuk kata yang sedang diucapkan (1.0 -> 1.09 -> 1.0)."""
    dt = t - t0
    if dt < 0 or dt > dur:
        return 1.0
    return 1.0 + 0.09 * use_spring_pop(dt / dur, 1.0)


def use_breath(seed: int, t: float) -> int:
    """Idle napas: offset vertikal 0-4 px, fase berbeda per aktor."""
    ph = (seed % 100) / 100 * math.tau
    return int(round(math.sin(t * 1.35 + ph) * 2.4))


# ------------------------------------------------------------------ ambient
# Profil per scene: elemen apa yang hidup di latar.
_PROFILE = {
    "sky": "sky", "atmosphere": "sky", "sunset": "sky", "galaxy": "night_sky",
    "space": "night_sky", "city_top": "sky", "city_street": "street",
    "park": "street", "park_evening": "street", "park_sunleft": "street",
    "playground_clock": "street", "garden": "street", "beach": "beach",
    "lake_ice": "cold", "market": "street", "airport": "street",
    "rain_cloud": "rain", "dark_forest": "night_forest", "bedroom_night": "night",
    "underwater": "water", "classroom": "interior", "kitchen": "interior",
    "bedroom": "interior", "bank": "money", "money_print": "money",
    "stock_board": "money", "data_center": "interior", "phone_inside": "interior",
    "body_inside": "interior", "neuron_city": "interior",
    "house_cutaway": "interior", "prism": "interior",
}

_CACHE: dict[tuple, dict] = {}


def _seed_of(scene: str, seed: int) -> int:
    h = hashlib.md5(f"{scene}|{seed}".encode()).hexdigest()[:8]
    return int(h, 16)


def _specks(scene: str, prof: str, W: int, H: int, n: int, seed: int) -> list[dict]:
    key = (scene, prof, W, H, n, seed)
    if key in _CACHE:
        return _CACHE[key]["specks"]
    rng = random.Random(_seed_of(scene, seed))
    out = []
    for _ in range(n):
        out.append(dict(
            x=rng.uniform(0, W), y=rng.uniform(120, H * 0.78),
            r=rng.uniform(2.0, 5.5), sp=rng.uniform(0.15, 0.55),
            amp=rng.uniform(0.3, 1.0), ph=rng.uniform(0, math.tau),
            drift=rng.uniform(-14, 14),
        ))
    _CACHE[key] = {"specks": out}
    return out


def _clouds(scene: str, W: int, H: int, seed: int) -> list[dict]:
    key = (scene, "clouds", W, H, seed)
    if key in _CACHE:
        return _CACHE[key]["clouds"]
    rng = random.Random(_seed_of(scene, seed) ^ 0x9E37)
    out = []
    for i in range(6):
        out.append(dict(
            x=rng.uniform(-200, W + 100), y=rng.uniform(140, H * 0.42),
            w=rng.uniform(220, 460), h=rng.uniform(70, 150),
            sp=rng.uniform(6, 20) * (0.5 + 0.18 * i),   # parallax berlapis
            a=rng.randint(26, 52),
        ))
    _CACHE[key] = {"clouds": out}
    return out


def _glow_sprite(r: int, color: tuple[int, int, int]) -> Image.Image:
    key = ("glow", r, color)
    if key in _CACHE:
        return _CACHE[key]["img"]
    size = r * 2
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    steps = 12
    for i in range(steps, 0, -1):
        rr = int(r * i / steps)
        a = int(46 * (1 - i / steps) ** 1.4) + 4
        d.ellipse((r - rr, r - rr, r + rr, r + rr), fill=(*color, a))
    img = img.filter(__import__("PIL.ImageFilter", fromlist=["GaussianBlur"]).GaussianBlur(r * 0.18))
    _CACHE[key] = {"img": img}
    return img


def use_camera_breath(t: float) -> tuple[int, int]:
    """Kamera tidak pernah benar-benar diam: offset 1-3 px."""
    return (int(round(math.sin(t * 0.85) * 2.6)),
            int(round(math.sin(t * 0.63 + 1.1) * 2.0)))


def use_ambient(im: Image.Image, scene: str, t: float, seed: int = 0,
                clouds: bool = True) -> None:
    """Gambar ambient di atas background, di bawah karakter.

    Minimal 2 elemen aktif per scene (aturan Living World).
    """
    prof = _PROFILE.get(scene, "interior")
    W, H = im.size
    # gambar langsung ke frame (ImageDraw "RGBA" memblend alpha) -> hemat ~30ms/frame
    d = ImageDraw.Draw(im, "RGBA")

    # 1) awan / kabut bergerak (parallax berlapis)
    if clouds and prof in ("sky", "night_sky", "rain", "street", "beach", "cold"):
        for c in _clouds(scene, W, H, seed):
            span = W + c["w"] + 260
            x = (c["x"] + t * c["sp"]) % span - c["w"] - 130
            y = c["y"] + math.sin(t * 0.32 + c["x"] * 0.01) * 9
            box = (x, y, x + c["w"], y + c["h"])
            d.ellipse(box, fill=(255, 255, 255, c["a"]))
            d.ellipse((x + c["w"] * 0.18, y - c["h"] * 0.22,
                       x + c["w"] * 0.70, y + c["h"] * 0.55),
                      fill=(255, 255, 255, int(c["a"] * 0.8)))

    # 2) glow matahari / bulan berdenyut
    if prof in ("sky", "street", "beach", "cold"):
        gx, gy = int(W * 0.74), int(H * 0.20)
        pulse = 0.5 + 0.5 * math.sin(t * 1.1)
        r = int(180 * (0.94 + 0.08 * pulse))
        g = _glow_sprite(r, (255, 226, 150))
        im.alpha_composite(g, (gx - r, gy - r))

    # 3) partikel sesuai suasana
    if prof == "night_sky":
        pts = _specks(scene, prof, W, H, 34, seed)
        for s in pts:
            tw = 0.35 + 0.65 * abs(math.sin(t * (0.7 + s["amp"]) + s["ph"]))
            a = int(200 * tw)
            r = s["r"] * 0.8
            d.ellipse((s["x"] - r, s["y"] - r, s["x"] + r, s["y"] + r),
                      fill=(255, 250, 220, a))
    elif prof in ("night", "night_forest"):
        for s in _specks(scene, prof, W, H, 16, seed):
            tw = 0.25 + 0.75 * (0.5 + 0.5 * math.sin(t * 1.5 + s["ph"]))
            x = s["x"] + math.sin(t * 0.5 + s["ph"]) * 22
            y = s["y"] + math.cos(t * 0.42 + s["ph"]) * 14
            r = s["r"] * 1.3
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 236, 140, int(150 * tw)))
    elif prof == "water":
        for s in _specks(scene, prof, W, H, 18, seed):
            y = (s["y"] - t * (18 + s["sp"] * 40)) % (H * 0.8) + H * 0.1
            x = s["x"] + math.sin(t * 0.8 + s["ph"]) * 12
            r = s["r"] * 1.6
            d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 255, 255, 90), width=2)
    elif prof == "rain":
        for i in range(26):
            sx = (i * 137 + int(t * 900)) % (W + 200) - 100
            sy = (i * 211 + int(t * 1500)) % H
            d.line((sx, sy, sx - 12, sy + 46), fill=(220, 235, 255, 70), width=2)
    elif prof == "money":
        for s in _specks(scene, prof, W, H, 10, seed):
            y = (s["y"] + t * (14 + s["sp"] * 18)) % (H * 0.7) + H * 0.12
            x = s["x"] + math.sin(t * 0.6 + s["ph"]) * 26
            r = s["r"] * 2.0
            d.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7),
                      fill=(255, 205, 90, 120), outline=(190, 140, 40, 150), width=2)
    elif prof == "cold":
        for s in _specks(scene, prof, W, H, 20, seed):
            y = (s["y"] + t * (10 + s["sp"] * 12)) % (H * 0.8)
            x = s["x"] + math.sin(t * 0.7 + s["ph"]) * 18
            r = s["r"] * 0.9
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 120))
    else:  # interior: debu halus melayang
        for s in _specks(scene, prof, W, H, 14, seed):
            y = (s["y"] - t * (6 + s["sp"] * 8)) % (H * 0.75) + H * 0.1
            x = s["x"] + math.sin(t * 0.5 + s["ph"]) * 16
            r = s["r"] * 0.7
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 250, 235, 70))

    # 4) kilau diagonal (floating highlights) untuk scene uang
    if prof == "money":
        for i in range(4):
            p = (t * 0.35 + i * 0.25) % 1.0
            x = W * (0.1 + p * 0.8)
            y = H * (0.75 - p * 0.45)
            a = int(90 * math.sin(math.pi * p))
            d.line((x - 18, y + 18, x + 18, y - 18), fill=(255, 240, 180, a), width=3)



# ------------------------------------------------------------------- HUD / UI
def _digit_strip(font) -> dict:
    key = ("digits", id(font), font.size)
    if key in _CACHE:
        return _CACHE[key]["map"]
    m = {}
    for ch in "0123456789":
        m[ch] = font.getbbox(ch)
    _CACHE[key] = {"map": m}
    return m


def use_rolling_value(t: float, dur: float, target: int) -> int:
    """Counter odometer: 0 -> target dengan ease-out expo (tidak snap)."""
    u = clamp01(t / dur)
    return int(round(use_ease_out_expo(u) * target))


def use_progress_bar(d: ImageDraw.ImageDraw, x0: int, y0: int, w: int, h: int,
                     prog: float, color: tuple[int, int, int]) -> None:
    prog = clamp01(prog)
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), h // 2, fill=(0, 0, 0, 70))
    if prog > 0.002:
        d.rounded_rectangle((x0, y0, x0 + max(h, int(w * prog)), y0 + h), h // 2,
                            fill=(*color, 235))
        glow = (x0 + int(w * prog), y0 + h // 2)
        d.ellipse((glow[0] - 7, glow[1] - 7, glow[0] + 7, glow[1] + 7),
                  fill=(255, 255, 255, 150))


def use_hud(im: Image.Image, t: float, ep, prog: float, font) -> None:
    """HUD persisten 1,5x: chip seri, HARI, progress bar — semua y < 190."""
    W, _ = im.size
    layer = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    chip_h = 56

    # progress bar tebal (warna berubah di akhir episode)
    hot = (215, 38, 61) if prog < 0.82 else (244, 185, 66)
    use_progress_bar(d, 0, 0, W, 10, prog, hot)

    # chip seri: pop-in spring, pill #111827 @ 85%
    label = f"BOCA · {ep.series}"
    sp = use_spring_pop(t / 0.45)
    cw = int(font.getlength(label)) + 128
    chip = Image.new("RGBA", (cw, chip_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(chip)
    cd.rounded_rectangle((0, 0, cw - 1, chip_h - 1), chip_h // 2, fill=(17, 24, 39, 217))
    cd.rounded_rectangle((11, 11, 25, chip_h - 11), 7, fill=(*hot, 255))
    cd.text((38, chip_h // 2 + 1), label, font=font, fill=(255, 255, 255, 255), anchor="lm")
    if abs(sp - 1.0) > 0.005:
        chip = chip.resize((max(1, int(cw * sp)), max(1, int(chip_h * sp))),
                           Image.Resampling.LANCZOS)
    im.alpha_composite(chip, (28, 26))

    # nomor hari: rolling counter + pill kontras
    day_txt = f"HARI {use_rolling_value(t - 0.15, 0.7, ep.day):02d}"
    tw = int(font.getlength(day_txt))
    d.rounded_rectangle((W - 30 - tw - 26, 26, W - 18, 26 + chip_h), chip_h // 2,
                        fill=(17, 24, 39, 217))
    d.text((W - 34, 26 + chip_h // 2 + 1), day_txt, font=font,
           fill=(255, 236, 120, 255), anchor="rm")

    im.alpha_composite(layer)


# --------------------------------------------------------------- transitions
def use_speed_lines(im: Image.Image, p: float, seed: int, direction: int = 1) -> None:
    """Wipe garis kecepatan saat ganti shot (bukan hard cut).

    p = 0 -> paling kuat, p = 1 -> hilang.
    """
    if p >= 1.0:
        return
    k = 1.0 - clamp01(p)
    W, H = im.size
    layer = Image.new("RGBA", (W, H), (255, 255, 255, int(26 * k)))
    d = ImageDraw.Draw(layer)
    rng = random.Random((seed * 7919) ^ int(p * 1000))
    for i in range(16):
        y = rng.uniform(0, H)
        ln = rng.uniform(180, 620) * k
        x = rng.uniform(-200, W)
        a = int(rng.uniform(60, 170) * k)
        w = int(rng.uniform(2, 6))
        d.line((x, y, x + direction * ln, y - ln * 0.34), fill=(255, 255, 255, a), width=w)

    im.alpha_composite(layer)


# ------------------------------------------------------------- callout loupe
def use_loupe(im: Image.Image, t: float, pop_t: float,
              src: tuple[int, int], at: tuple[int, int], r: int,
              zoom: float = 1.8, ring: tuple[int, int, int] = (255, 255, 255)) -> None:
    """Zoom-in magnifier bubble (opt-in lewat field `loupe` di storyboard).

    src  = titik detail yang diperbesar di frame (koordinat 1080x1920)
    at   = pusat gelembung
    r    = radius akhir gelembung
    """
    p = use_spring_pop((t - pop_t) / 0.38)
    if p <= 0.02:
        return
    rr = max(8, int(r * p))
    half = int(rr / zoom)
    sx, sy = src
    box = (max(0, sx - half), max(0, sy - half),
           min(im.width, sx + half), min(im.height, sy + half))
    if box[2] - box[0] < 8 or box[3] - box[1] < 8:
        return
    crop = im.crop(box).resize((rr * 2, rr * 2), Image.Resampling.LANCZOS)
    mask = Image.new("L", (rr * 2, rr * 2), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, rr * 2 - 1, rr * 2 - 1), fill=255)
    bx, by = at
    # garis penghubung dulu (di bawah gelembung)
    d = ImageDraw.Draw(im, "RGBA")
    d.line((sx, sy, bx, by), fill=(255, 255, 255, int(190 * p)), width=max(3, int(6 * p)))
    d.ellipse((sx - 6, sy - 6, sx + 6, sy + 6), outline=(255, 255, 255, 220), width=3)
    im.paste(crop, (bx - rr, by - rr), mask)
    d.ellipse((bx - rr, by - rr, bx + rr, by + rr), outline=(*ring, 255), width=max(4, int(9 * p)))
    d.ellipse((bx - rr - 5, by - rr - 5, bx + rr + 5, by + rr + 5),
              outline=(20, 16, 15, int(200 * p)), width=3)


# --------------------------------------------------------------- elastic body
def use_squash(t: float, impulse_t: float, dur: float = 0.20) -> tuple[float, float]:
    """Squash & stretch saat pose/ekspresi berganti (0 -> 0.92 -> 1.04 -> 1.0).

    Mengembalikan (scaleX, scaleY); selalu menjaga volume kasar (sx = 1/sy).
    """
    dt = t - impulse_t
    if dt < 0 or dt > dur:
        return (1.0, 1.0)
    u = clamp01(dt / dur)
    sy = 1.0 - 0.08 * math.sin(math.pi * u) + 0.045 * math.sin(2 * math.pi * u) * (1 - u)
    sy = max(0.9, min(1.05, sy))
    return (1.0 / sy, sy)


def use_camera_shake(t: float, impact_t: float, intensity: float = 9.0) -> tuple[int, int]:
    """Guncangan kamera singkat (shock / benda jatuh / whoosh)."""
    dt = t - impact_t
    if dt < 0 or dt > 0.42:
        return (0, 0)
    decay = math.exp(-7.5 * dt)
    return (int(round(math.sin(46 * dt) * intensity * decay)),
            int(round(math.cos(39 * dt) * intensity * 0.65 * decay)))


def use_parallax_offset(base: int, factor: float, limit: int) -> int:
    """Offset layer depth: 0.35 = jauh (lambat), 1.25 = depan (cepat)."""
    return max(0, min(limit, int(round(base * factor))))
