#!/usr/bin/env python3
"""layouts.py — mode layout per beat: WIDE_STAGE, INFOGRAPHIC_CARD,
CLOSEUP_EMPHASIS, SPOTLIGHT_EFFECT.

Skema di shot (opsional; kalau tidak ada → WIDE_STAGE sepanjang shot):

    "layouts": [
      {"mode": "WIDE_STAGE", "from": 0.0, "to": 2.6},
      {"mode": "INFOGRAPHIC_CARD", "from": 2.6, "to": 6.0,
       "card": {"kind": "compare", "title": "Waktu vs Perhatian",
                "unit": "menit", "accent": "#D7263D",
                "left":  {"label": "2 JAM",   "value": 120, "max": 120},
                "right": {"label": "10 MENIT", "value": 10,  "max": 120}}},
      {"mode": "SPOTLIGHT_EFFECT", "from": 6.0, "to": 8.2,
       "focus": "boca", "dim": 0.62, "cone": true}
    ]

Semua kartu digambar di permukaan 2× lalu di-downscale → tepi tajam tanpa blur
scene. Spotlight memakai mask (boleh blur di mask, bukan di artwork).
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import motion

INK = (30, 30, 30)
WHITE = (255, 255, 255)
CREAM = (246, 241, 231)
RED = (215, 38, 61)
GOLD = (244, 185, 66)
TEAL = (31, 111, 120)
MUTED = (122, 116, 110)

CARD_W = 820
CARD_PAD = 44
HEADER_H = 96
RADIUS = 36
BORDER = 8

FONT_BOLD = Path("/system/fonts/DroidSans-Bold.ttf")
FONT_REG = Path("/system/fonts/Roboto-Regular.ttf")


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    p = FONT_BOLD if bold and FONT_BOLD.exists() else FONT_REG
    return ImageFont.truetype(str(p), size)


# ------------------------------------------------------------------ resolve
DEFAULT = {"mode": "WIDE_STAGE", "from": 0.0, "to": 1e9}


def normalize(layouts: list[dict] | None, dur: float) -> list[dict]:
    """Rapikan layout: urut, tanpa celah, menutup seluruh durasi shot."""
    if not layouts:
        return [{"mode": "WIDE_STAGE", "from": 0.0, "to": dur}]
    out = []
    cur = 0.0
    for ly in sorted(layouts, key=lambda x: float(x.get("from", 0))):
        f = max(cur, float(ly.get("from", cur)))
        t = min(dur, float(ly.get("to", dur)))
        if t <= f:
            continue
        if f > cur:
            out.append({"mode": "WIDE_STAGE", "from": cur, "to": f})
        item = dict(ly)
        item["from"], item["to"] = f, t
        out.append(item)
        cur = t
    if cur < dur:
        out.append({"mode": "WIDE_STAGE", "from": cur, "to": dur})
    return out


def active(layouts: list[dict], local: float) -> dict:
    for ly in layouts:
        if ly["from"] <= local < ly["to"]:
            return ly
    return layouts[-1] if layouts else DEFAULT


def layout_progress(ly: dict, local: float) -> float:
    span = max(1e-6, ly["to"] - ly["from"])
    return max(0.0, min(1.0, (local - ly["from"]) / span))


# ------------------------------------------------------- character transform
def character_transform(ly: dict, local: float, state: dict) -> dict:
    """Kembalikan offset & skala karakter sesuai mode layout.

    INFOGRAPHIC_CARD: karakter mengecil 0,52× dan bergeser ke kiri bawah
    (x = 150, ground = 1810) dengan ease-out-cubic 0,35 s.
    CLOSEUP_EMPHASIS: karakter digeser ke tengah (x = 540) — kamera yang zoom.
    """
    mode = ly.get("mode", "WIDE_STAGE")
    u = motion.use_ease_out_cubic(layout_progress(ly, local) / 0.35 if ly else 1.0)
    tr = {"scale": 1.0, "dx": 0.0, "ground": None, "dim_char": 0.0}
    if mode == "INFOGRAPHIC_CARD":
        tr["scale"] = 1.0 + (0.52 - 1.0) * u
        tr["dx"] = (150 - float(state.get("x", 540))) * u
        tr["ground"] = float(state.get("ground", 1400)) + (1810 - float(state.get("ground", 1400))) * u
        tr["dim_char"] = 0.25 * u
    elif mode == "CLOSEUP_EMPHASIS":
        tr["dx"] = (540 - float(state.get("x", 540))) * u
    return tr


# ------------------------------------------------------------------ card UI
def card_height(spec: dict) -> int:
    """Tinggi kartu 1x (kanvas digambar 2x)."""
    kind = spec.get("kind", "compare")
    if kind == "compare":
        return HEADER_H + 344
    if kind == "checklist":
        n = len(spec.get("items") or [])
        return HEADER_H + 75 + max(1, n) * 92
    if kind == "steps":
        n = len(spec.get("steps") or [])
        return HEADER_H + 70 + max(1, n) * 96
    return HEADER_H + 340


def _panel(h: int) -> Image.Image:
    im = Image.new("RGBA", (CARD_W * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((BORDER, BORDER, CARD_W * 2 - BORDER, h * 2 - BORDER),
                        RADIUS * 2, fill=(*WHITE, 255), outline=(*INK, 255), width=BORDER * 2)
    return im


def _header(d: ImageDraw.ImageDraw, spec: dict, accent) -> None:
    d.rounded_rectangle((BORDER * 2, BORDER * 2, CARD_W * 2 - BORDER * 2,
                         (HEADER_H - 4) * 2),
                        RADIUS, fill=accent)
    d.line((BORDER * 2, (HEADER_H - 4) * 2, CARD_W * 2 - BORDER * 2, (HEADER_H - 4) * 2),
           fill=INK, width=BORDER * 2)
    d.text((CARD_PAD * 2, (HEADER_H - 4)), spec.get("title", ""), font=_font(40 * 2),
           fill=(255, 255, 255, 255), anchor="lm")


def draw_card(spec: dict, t: float, local: float, t_in: float) -> Image.Image:
    """Kartu infografis 820×H pada permukaan 2x, lalu downscale LANCZOS."""
    h = card_height(spec)
    im = _panel(h)
    d = ImageDraw.Draw(im)
    accent_hex = spec.get("accent", "#D7263D")
    accent = (int(accent_hex[1:3], 16), int(accent_hex[3:5], 16), int(accent_hex[5:7], 16))
    _header(d, spec, accent)

    kind = spec.get("kind", "compare")
    u = max(0.0, min(1.0, (local - t_in) / 0.45))
    ease = motion.use_ease_out_cubic(u)

    if kind == "compare":
        unit = spec.get("unit", "")
        left, right = spec.get("left", {}), spec.get("right", {})
        gap = 40
        colw = (CARD_W * 2 - CARD_PAD * 4 - gap) // 2
        box_h = 300 * 2
        for i, side in enumerate((left, right)):
            x0 = CARD_PAD * 2 + i * (colw + gap)
            y0 = (HEADER_H + 22) * 2
            d.rounded_rectangle((x0, y0, x0 + colw, y0 + box_h),
                                28, fill=(*CREAM, 255), outline=(*INK, 255), width=BORDER * 2)
            d.text((x0 + 30, y0 + 34), side.get("label", ""), font=_font(24 * 2),
                   fill=(*MUTED, 255), anchor="lt")
            val = int(round(motion.use_rolling_value((local - t_in) - 0.15 - i * 0.12, 0.8,
                                                     int(side.get("value", 0)))))
            d.text((x0 + 30, y0 + 150), f"{val}", font=_font(92 * 2),
                   fill=(*INK, 255), anchor="lt")
            if unit:
                d.text((x0 + 30, y0 + 300), unit, font=_font(24 * 2),
                       fill=(*MUTED, 255), anchor="lt")
            mx = max(1, int(side.get("max", 100)))
            track_w = colw - 60
            bar_y = y0 + box_h - 96
            d.rounded_rectangle((x0 + 30, bar_y, x0 + 30 + track_w, bar_y + 34),
                                17, fill=(232, 226, 214, 255))
            frac = min(1.0, int(side.get("value", 0)) / mx) * ease
            if frac > 0.01:
                d.rounded_rectangle((x0 + 30, bar_y, x0 + 30 + int(track_w * frac), bar_y + 34),
                                    17, fill=accent if i == 0 else (*TEAL, 255))
        vs_cx, vs_cy = CARD_W, (HEADER_H + 22 + box_h // 2 - 72)
        rr = int(38 * ease)
        if rr > 4:
            d.ellipse((vs_cx - rr, vs_cy - rr, vs_cx + rr, vs_cy + rr),
                      fill=(*INK, 255), outline=(*WHITE, 255), width=6)
            d.text((vs_cx, vs_cy), "VS", font=_font(28 * 2), fill=(*WHITE, 255), anchor="mm")

    elif kind == "checklist":
        items = spec.get("items") or []
        for i, it in enumerate(items):
            k = max(0.0, min(1.0, (local - t_in - 0.25 - i * 0.10) / 0.30))
            if k <= 0:
                continue
            e = motion.use_spring_pop(k, 1.08)
            cy = (HEADER_H + 35 + i * 92 + 40) * 2
            ok = bool(it.get("ok", True))
            r = int(24 * 2 * e)
            cx = CARD_PAD * 2 + 28
            d.ellipse((cx - r, cy - r, cx + r, cy + r),
                      fill=(*TEAL, 255) if ok else (*WHITE, 255),
                      outline=(*INK, 255) if not ok else (*TEAL, 255), width=6)
            if ok:
                d.line((cx - 16, cy, cx - 4, cy + 14), fill=(255, 255, 255, 255), width=9)
                d.line((cx - 4, cy + 14, cx + 20, cy - 12), fill=(255, 255, 255, 255), width=9)
            d.text((cx + 60, cy), str(it.get("text", "")), font=_font(30 * 2),
                   fill=(*INK, 255), anchor="lm")

    elif kind == "steps":
        steps = spec.get("steps") or []
        for i, st in enumerate(steps):
            k = max(0.0, min(1.0, (local - t_in - 0.20 - i * 0.10) / 0.28))
            if k <= 0:
                continue
            e = motion.use_spring_pop(k, 1.10)
            y = (HEADER_H + 30 + i * 96) * 2
            d.rounded_rectangle((CARD_PAD * 2, y, CARD_W * 2 - CARD_PAD * 2, y + 78 * 2),
                                20, fill=(*CREAM, 255), outline=(*INK, 255), width=5 * 2)
            rr = int(30 * 2 * e)
            cx, cy = CARD_PAD * 2 + 50, y + 78
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(*accent, 255))
            d.text((cx, cy), str(i + 1), font=_font(30 * 2), fill=(255, 255, 255, 255),
                   anchor="mm")
            d.text((cx + 70, cy), str(st), font=_font(30 * 2), fill=(*INK, 255), anchor="lm")

    return im.resize((CARD_W, h), Image.Resampling.LANCZOS)


def paste_card(base: Image.Image, spec: dict, t: float, local: float,
               t_in: float, cx: int = 540, cy: int = 760) -> tuple[int, int, int]:
    """Tempel kartu dengan pop-in spring; return (x, y, h) untuk hit-test."""
    card = draw_card(spec, t, local, t_in)
    pop = motion.use_spring_pop(max(0.0, (local - t_in) / 0.42), 1.10)
    out_span = float(spec.get("_out_span", 0.30))
    remain = float(spec.get("_remain", 9.0))
    if remain < out_span:
        pop *= motion.use_ease_out_expo(remain / out_span)
    if abs(pop - 1.0) > 0.004:
        card = card.resize((max(1, int(card.width * pop)), max(1, int(card.height * pop))),
                           Image.Resampling.LANCZOS)
    x = cx - card.width // 2
    y = cy - card.height // 2
    base.paste(card, (x, y), card)
    return x, y, card.height


# ----------------------------------------------------------------- spotlight
def spot_mask(size: tuple[int, int], cx: float, cy: float,
              spec: dict, k: float = 1.0) -> Image.Image:
    """Mask L: gelap `dim` dengan lubang elips + cone, blur di mask saja."""
    W, H = size
    dim = float(spec.get("dim", 0.62)) * motion.use_ease_out_cubic(max(0.0, min(1.0, k)))
    rx = int(spec.get("rx", 320))
    ry = int(spec.get("ry", 420))
    mask = Image.new("L", (W, H), int(255 * dim))
    d = ImageDraw.Draw(mask)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=0)
    if spec.get("cone"):
        top_w = int(spec.get("cone_top", 240))
        d.polygon([(cx - top_w // 2, 0), (cx + top_w // 2, 0),
                   (cx + rx, cy + ry), (cx - rx, cy + ry)], fill=0)
    return mask.filter(ImageFilter.GaussianBlur(60))


def draw_spotlight(im: Image.Image, spec: dict, cx: float, cy: float,
                   t: float, t_in: float) -> None:
    """Versi langsung (dipakai test/manual); pipeline memakai spot_mask cache."""
    k = max(0.0, min(1.0, (t - t_in) / 0.45))
    if float(spec.get("dim", 0.62)) * k <= 0.01:
        return
    shade = Image.new("RGBA", im.size, (8, 10, 14, 255))
    shade.putalpha(spot_mask(im.size, cx, cy, spec, k))
    im.alpha_composite(shade)


# ---------------------------------------------------------------- close-up
def closeup_camera(ly: dict, local: float, state: dict, W: int, H: int) -> tuple[float, float, float]:
    """Kamera mendekat ke wajah aktor dengan ease-out-expo.

    fx/fy adalah koordinat ternormalisasi 0..1 pada scene; z 1.40–1.55.
    """
    u = max(0.0, min(1.0, (local - ly["from"]) / 0.55))
    e = motion.use_ease_out_expo(u)
    z_target = float(ly.get("z", 1.45))
    hx = float(state.get("x", W / 2)) / W
    hy = max(0.0, (float(state.get("ground", 1400)) - float(state.get("h", 640)) * 0.72) / H)
    return (hx, hy, 1.0 + (z_target - 1.0) * e)
