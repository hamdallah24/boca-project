#!/usr/bin/env python3
"""props_svg.py — prop besar ber-outline SVG + animasi scripted.

Ukuran minimum yang disarankan: 280–480 px (bukan ikon 100 px di langit).

Prop yang tersedia:
  clock       : jarum jam berputar (jam + menit), case SVG
  phone       : layar scroll tak berujung (strip chat digeser di dalam mask)
  hourglass   : pasir turun + flip 180° tiap siklus

Semua bagian statis di-render sekali lewat Chromium (`make_boca.render_svg`),
animasi hanya crop/rotate/komposit PIL → tidak ada rasterisasi per frame.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

INK = "#231815"
WHITE = "#FFFFFF"
CREAM = "#F6F1E7"
RED = "#D7263D"
RED_D = "#A8172A"
TEAL = "#1F6F78"
GOLD = "#F4B942"
GOLD_D = "#C48A1E"
BLUE = "#5AA9E6"
SW = 10


def _svg(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}"><defs>{defs}</defs>{body}</svg>')


def _r(x, y, w, h, fill, rx=0, sw=SW, extra=""):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
            f'fill="{fill}" stroke="{INK}" stroke-width="{sw}" {extra}/>')


def _c(cx, cy, r, fill, sw=SW, extra=""):
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" '
            f'stroke="{INK}" stroke-width="{sw}" {extra}/>')


def _l(x1, y1, x2, y2, color=INK, w=SW):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>')


def _p(d, fill, sw=SW, extra=""):
    return (f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="{sw}" '
            f'stroke-linejoin="round" {extra}/>')


# ------------------------------------------------------------------- builder
class PropSprite:
    """Base class: semua prop punya tinggi akhir `h` dan frame(t)."""

    def __init__(self, h: int, cache: Path):
        self.h = h
        self.cache = cache
        self.cache.mkdir(parents=True, exist_ok=True)

    def _render(self, name: str, svg: str, w: int, h: int) -> Image.Image:
        from make_boca import render_svg  # import lokal: hindari siklus
        sp = self.cache / f"{name}.svg"
        png = self.cache / f"{name}.png"
        need = (not png.exists()) or (not sp.exists()) or (sp.stat().st_mtime > png.stat().st_mtime)
        if need:
            sp.write_text(svg, encoding="utf-8")
            render_svg(sp, png, w, h, transparent=True)
        return Image.open(png).convert("RGBA")

    def frame(self, t: float) -> Image.Image:  # pragma: no cover - abstract
        raise NotImplementedError


class ClockProp(PropSprite):
    """Jarum jam berputar scripted: menit 240°/s, jam 20°/s (spin dramatis)."""

    def __init__(self, h: int, cache: Path, hands_speed: float = 1.0):
        super().__init__(h, cache)
        self.speed = hands_speed
        r = h * 0.40
        body = (
            _c(h / 2, h / 2, r, CREAM)
            + _c(h / 2, h / 2, r * 0.90, WHITE, sw=6)
            + "".join(_l(h / 2 + math.sin(a) * r * 0.70, h / 2 - math.cos(a) * r * 0.70,
                         h / 2 + math.sin(a) * r * 0.82, h / 2 - math.cos(a) * r * 0.82,
                         INK, max(3, int(h * 0.018)))
                      for a in [i * math.pi / 6 for i in range(12)])
            + _c(h / 2, h / 2, r * 0.06, RED, sw=4)
        )
        self.body = self._render(f"clock-body-{h}", _svg(h, h, body), h, h)
        # jarum digambar menghadap atas, pivot di tengah kanvas
        hs = int(h * 0.9)
        c = hs / 2
        hour = (f'<rect x="{c-h*0.035:.1f}" y="{c-h*0.26:.1f}" width="{h*0.07:.1f}" '
                f'height="{h*0.26:.1f}" rx="{h*0.03:.1f}" fill="{INK}" stroke="{INK}" '
                f'stroke-width="6"/>'
                f'<circle cx="{c}" cy="{c}" r="{h*0.055:.1f}" fill="{RED}" stroke="{INK}" stroke-width="5"/>')
        minute = (f'<rect x="{c-h*0.025:.1f}" y="{c-h*0.40:.1f}" width="{h*0.05:.1f}" '
                  f'height="{h*0.40:.1f}" rx="{h*0.025:.1f}" fill="{RED}" stroke="{INK}" '
                  f'stroke-width="6"/>')
        self.hour = self._render(f"clock-hour-{h}", _svg(hs, hs, hour), hs, hs)
        self.minute = self._render(f"clock-minute-{h}", _svg(hs, hs, minute), hs, hs)
        self.hs = hs

    def frame(self, t: float) -> Image.Image:
        out = self.body.copy()
        off = (self.h - self.hs) // 2
        ang_h = -(t * 20.0 * self.speed) % 360
        ang_m = -(t * 240.0 * self.speed) % 360
        hh = self.hour.rotate(ang_h, resample=Image.Resampling.BICUBIC)
        mm = self.minute.rotate(ang_m, resample=Image.Resampling.BICUBIC)
        out.alpha_composite(hh, (off, off))
        out.alpha_composite(mm, (off, off))
        return out


class PhoneProp(PropSprite):
    """Layar HP scroll horizontal strip vertikal tanpa henti."""

    ROWS = 9

    def __init__(self, h: int, cache: Path):
        super().__init__(h, cache)
        w = int(h * 0.52)
        self.w = w
        body_col = "#2B2F36"
        self.body = self._render(
            f"phone-body-{h}",
            _svg(w, h,
                 _r(w * 0.02, h * 0.02, w * 0.96, h * 0.96, body_col, rx=int(w * 0.16))
                 + _r(w * 0.09, h * 0.06, w * 0.82, h * 0.80, "#0E1116", rx=int(w * 0.10), sw=6)
                 + _c(w * 0.5, h * 0.925, w * 0.055, "#3B4048", sw=5)
                 + _r(w * 0.36, h * 0.035, w * 0.28, h * 0.012, "#3B4048", rx=6, sw=0)),
            w, h)
        # area layar (di dalam mask body)
        self.box = (int(w * 0.09), int(h * 0.06), int(w * 0.82), int(h * 0.80))
        rows = []
        colors = [RED, TEAL, GOLD, BLUE, RED_D, TEAL, GOLD, BLUE, RED]
        row_h = int(h * 0.115)
        strip_h = row_h * self.ROWS
        for i in range(self.ROWS):
            y = i * row_h + row_h * 0.12
            right = i % 2 == 0
            bw = w * (0.52 if right else 0.64)
            bx = w * (0.40 if right else 0.10)
            rows.append(_r(bx, y, bw, row_h * 0.62, colors[i % len(colors)],
                           rx=int(row_h * 0.18), sw=6))
            rows.append(_r(bx + w * 0.06, y + row_h * 0.16, bw * 0.62, row_h * 0.10,
                           "#FFFFFF88", rx=4, sw=0))
        self.strip = self._render(f"phone-strip-{h}",
                                  _svg(self.box[2], strip_h, "".join(rows)),
                                  self.box[2], strip_h)
        self.strip_h = strip_h

    def frame(self, t: float) -> Image.Image:
        out = self.body.copy()
        bx, by, bw, bh = self.box
        span = max(1, self.strip_h - bh)
        off = int((t * self.h * 0.22) % span)
        crop = self.strip.crop((0, off, bw, off + bh))
        out.paste(crop, (bx, by), crop)
        # notch ditaruh di atas layar agar tetap terbaca
        notch = Image.new("RGBA", (bw, int(self.h * 0.045)), (0, 0, 0, 0))
        from PIL import ImageDraw
        ImageDraw.Draw(notch).rounded_rectangle(
            (bw * 0.34, 0, bw * 0.66, notch.height * 0.8),
            radius=int(notch.height * 0.4), fill=(14, 17, 22, 255))
        out.alpha_composite(notch, (bx, by))
        return out


class HourglassProp(PropSprite):
    """8 state pasir + flip 180° tiap 3 detik (rotasi PIL, bukan raster baru)."""

    STATES = 8

    def __init__(self, h: int, cache: Path):
        super().__init__(h, cache)
        w = int(h * 0.62)
        self.w = w
        self.states = []
        for k in range(self.STATES):
            frac = k / (self.STATES - 1)
            top = 0.36 * (1 - frac)
            bot = 0.36 * frac
            cx = w / 2
            body = (
                _r(w * 0.12, h * 0.02, w * 0.76, h * 0.045, GOLD_D, rx=8)
                + _r(w * 0.12, h * 0.935, w * 0.76, h * 0.045, GOLD_D, rx=8)
                + _l(w * 0.16, h * 0.065, w * 0.84, h * 0.065, INK, 7)
                + _l(w * 0.16, h * 0.935, w * 0.84, h * 0.935, INK, 7)
                # kaca
                + f'<path d="M {w*0.22:.1f},{h*0.06:.1f} L {w*0.78:.1f},{h*0.06:.1f} '
                  f'L {cx:.1f},{h*0.50:.1f} Z" fill="{CREAM}" stroke="{INK}" stroke-width="8"/>'
                + f'<path d="M {w*0.22:.1f},{h*0.94:.1f} L {w*0.78:.1f},{h*0.94:.1f} '
                  f'L {cx:.1f},{h*0.50:.1f} Z" fill="{CREAM}" stroke="{INK}" stroke-width="8"/>'
                # pasir atas (mengecil)
                + f'<path d="M {w*0.28:.1f},{h*0.09:.1f} L {w*0.72:.1f},{h*0.09:.1f} '
                  f'L {cx:.1f},{h*(0.09+top):.1f} Z" fill="{GOLD}" stroke="{GOLD_D}" stroke-width="5"/>'
                # pasir bawah (membesar)
                + f'<path d="M {w*0.28:.1f},{h*0.91:.1f} L {w*0.72:.1f},{h*0.91:.1f} '
                  f'L {cx:.1f},{h*(0.91-bot):.1f} Z" fill="{GOLD}" stroke="{GOLD_D}" stroke-width="5"/>'
                # aliran
                + _l(cx, h * (0.09 + top), cx, h * (0.91 - bot), GOLD_D, 6)
            )
            self.states.append(self._render(f"hour-{h}-s{k}", _svg(w, h, body), w, h))

    def frame(self, t: float) -> Image.Image:
        cyc = t % 3.0
        idx = min(self.STATES - 1, int(cyc / 3.0 * self.STATES))
        img = self.states[idx].copy()
        # flip cepat 0,35 s di akhir siklus
        if cyc > 2.65:
            ang = (cyc - 2.65) / 0.35 * 180.0
            img = img.rotate(ang, resample=Image.Resampling.BICUBIC, expand=False)
        return img




class BulbProp(PropSprite):
    """Bohlam besar: cahaya berdenyut (4 state pra-render, bukan blur)."""

    STATES = 4

    def __init__(self, h: int, cache: Path):
        super().__init__(h, cache)
        cx = h / 2
        r = h * 0.225
        gy = h * 0.40
        self.frames_img = []
        for k, ray in enumerate((0.070, 0.092, 0.112, 0.092)):
            body = [
                _c(cx, gy, r * 1.48, "#FFE9A3", sw=0, extra='fill-opacity="0.45"'),
            ]
            for i in range(8):
                a = i * math.pi / 4
                r0 = r * 1.26
                r1 = r0 + h * ray
                body.append(_l(cx + math.cos(a) * r0, gy + math.sin(a) * r0,
                               cx + math.cos(a) * r1, gy + math.sin(a) * r1,
                               GOLD, max(6, int(h * 0.028))))
            body.append(_p(
                f"M {cx-r:.1f},{gy+r*0.55:.1f} "
                f"A {r:.1f},{r:.1f} 0 1 1 {cx+r:.1f},{gy+r*0.55:.1f} Z", "#FDE68A"))
            # ulir lampu
            body.append(_p(f"M {cx-r*0.34:.1f},{gy:.1f} L {cx-r*0.12:.1f},{gy-r*0.46:.1f} "
                           f"L {cx+r*0.10:.1f},{gy-r*0.12:.1f} L {cx+r*0.30:.1f},{gy-r*0.50:.1f}",
                           "none", sw=5))
            body.append(_r(cx - h * 0.105, gy + r * 0.52, h * 0.21, h * 0.075, "#B9C2CC", rx=6))
            body.append(_r(cx - h * 0.090, gy + r * 0.52 + h * 0.062, h * 0.18, h * 0.045,
                           "#8E99A6", rx=5))
            body.append(_p(f"M {cx-h*0.070:.1f},{gy+r*0.52+h*0.105:.1f} "
                           f"L {cx+h*0.070:.1f},{gy+r*0.52+h*0.105:.1f} "
                           f"L {cx+h*0.036:.1f},{gy+r*0.52+h*0.150:.1f} "
                           f"L {cx-h*0.036:.1f},{gy+r*0.52+h*0.150:.1f} Z", "#5B6672", sw=5))
            self.frames_img.append(
                self._render(f"bulb-{h}-s{k}", _svg(h, h, "".join(body)), h, h))

    def frame(self, t: float) -> Image.Image:
        return self.frames_img[int(t * 6.0) % self.STATES].copy()


class CoinProp(PropSprite):
    """Tumpukan koin + satu koin berputar di atasnya (12 frame pra-render)."""

    FRAMES = 12

    def __init__(self, h: int, cache: Path):
        super().__init__(h, cache)
        cx = h / 2
        rx = h * 0.30
        ry = h * 0.088
        self.frames_img = []
        for i in range(self.FRAMES):
            phase = i / self.FRAMES
            rise = math.sin(phase * math.pi) * h * 0.11
            spin = phase * 2.0 * math.pi * 2.0
            spin_rx = max(h * 0.035, rx * abs(math.cos(spin)))
            spin_cy = h * 0.50 - rise
            body = []
            # tumpukan 4 koin (puck + sisi)
            for j in range(4):
                cy = h * 0.68 + j * h * 0.055
                body.append(_r(cx - rx, cy - ry * 0.55, rx * 2, ry * 1.10,
                               GOLD_D, rx=ry * 0.5, sw=7))
                body.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
                            f'fill="{GOLD}" stroke="{INK}" stroke-width="7"/>')
                body.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx*0.74:.1f}" '
                            f'ry="{ry*0.66:.1f}" fill="#FFE08C" stroke="none"/>')
            # koin berputar
            body.append(f'<ellipse cx="{cx:.1f}" cy="{spin_cy:.1f}" rx="{spin_rx:.1f}" '
                        f'ry="{ry:.1f}" fill="{GOLD}" stroke="{INK}" stroke-width="8"/>')
            body.append(f'<ellipse cx="{cx:.1f}" cy="{spin_cy:.1f}" rx="{spin_rx*0.70:.1f}" '
                        f'ry="{ry*0.62:.1f}" fill="#FFE08C" stroke="none"/>')
            self.frames_img.append(
                self._render(f"coin-{h}-s{i}", _svg(h, h, "".join(body)), h, h))

    def frame(self, t: float) -> Image.Image:
        return self.frames_img[int(t * 8.0) % self.FRAMES].copy()



# ---------------------------------------------------------- prop penerbangan
AVIATION_PROPS = {
    "airplane_jet": """
    <g stroke="#1E293B" stroke-width="10" stroke-linejoin="round">
      <polygon points="80,235 45,145 115,145 165,235" fill="#EF4444"/>
      <path d="M75,235 L385,235 Q475,235 486,272 Q475,305 385,305 L95,296 Q60,290 75,235 Z" fill="#FFFFFF"/>
      <path d="M415,244 L465,260 L422,268 Z" fill="#38BDF8"/>
      <g fill="#38BDF8" stroke-width="5">
        <circle cx="185" cy="264" r="9"/><circle cx="220" cy="264" r="9"/>
        <circle cx="255" cy="264" r="9"/><circle cx="290" cy="264" r="9"/>
        <circle cx="325" cy="264" r="9"/><circle cx="360" cy="264" r="9"/>
      </g>
      <polygon points="225,280 355,280 185,345 140,345" fill="#CBD5E1"/>
      <rect x="235" y="308" width="60" height="28" rx="10" fill="#64748B"/>
    </g>
    """,
    "wing_airfoil": """
    <g stroke-linejoin="round" stroke-linecap="round">
      <path d="M60,185 Q240,120 450,185" fill="none" stroke="#38BDF8" stroke-width="14"/>
      <polygon points="455,186 425,165 422,202" fill="#38BDF8"/>
      <path d="M85,256 C105,175 290,175 430,256 C305,270 155,270 85,256 Z" fill="#F1F5F9" stroke="#1E293B" stroke-width="11"/>
      <g fill="#22C55E" stroke="#1E293B" stroke-width="8">
        <polygon points="180,390 212,390 212,325 234,325 196,275 158,325 180,325"/>
        <polygon points="300,390 332,390 332,325 354,325 316,275 278,325 300,325"/>
      </g>
    </g>
    """,
    "hand_wind": """
    <g stroke="#1E293B" stroke-width="10" stroke-linejoin="round" stroke-linecap="round">
      <path d="M55,340 L195,300" stroke="#38BDF8" stroke-width="14"/>
      <path d="M85,390 L225,350" stroke="#38BDF8" stroke-width="14"/>
      <g transform="translate(265, 250) rotate(-25)">
        <rect x="-110" y="-22" width="160" height="44" rx="22" fill="#FCD5B5"/>
        <rect x="25" y="-26" width="85" height="40" rx="18" fill="#FCD5B5"/>
        <rect x="-25" y="-52" width="52" height="30" rx="14" fill="#FCD5B5"/>
      </g>
      <polygon points="240,175 272,175 272,120 296,120 256,70 216,120 240,120" fill="#22C55E"/>
    </g>
    """,
    "glider_plane": """
    <g stroke="#1E293B" stroke-width="10" stroke-linejoin="round">
      <g transform="translate(256, 225) rotate(12)">
        <polygon points="-145,-10 -175,-75 -115,-75 -85,-10" fill="#38BDF8"/>
        <path d="M-150,-10 L135,-10 Q195,-10 205,18 Q195,42 135,42 L-135,34 Z" fill="#FFFFFF"/>
        <polygon points="-35,24 85,24 -45,76 -85,76" fill="#BAE6FD"/>
      </g>
      <polygon points="240,420 272,420 272,355 296,355 256,305 216,355 240,355" fill="#FACC15"/>
    </g>
    """,
    "lift_vs_weight": """
    <g stroke="#1E293B" stroke-width="10" stroke-linejoin="round">
      <polygon points="150,400 198,400 198,210 236,210 174,105 112,210 150,210" fill="#22C55E"/>
      <rect x="285" y="210" width="135" height="120" rx="18" fill="#EF4444"/>
      <circle cx="352" cy="188" r="24" fill="none" stroke-width="12"/>
      <text x="352" y="288" font-family="Arial Black, sans-serif" font-weight="900" font-size="38" fill="#FFFFFF" stroke="none" text-anchor="middle">KG</text>
    </g>
    """,
}


class AviationProp(PropSprite):
    """Prop SVG statis (pesawat, sayap, tangan) — animasi pop/float dari pipeline."""

    def __init__(self, pid: str, h: int, cache: Path):
        super().__init__(h, cache)
        scale = h / 512.0
        body = AVIATION_PROPS[pid]
        svg = _svg(h, h, f'<g transform="scale({scale:.5f})">{body}</g>')
        self.img = self._render(f"{pid}-{h}", svg, h, h)

    def frame(self, t: float) -> Image.Image:
        return self.img.copy()


PROPS = {"clock": ClockProp, "phone": PhoneProp, "hourglass": HourglassProp,
         "bulb": BulbProp, "coin_stack": CoinProp}
for _pid in AVIATION_PROPS:
    PROPS[_pid] = (lambda h, cache, _n=_pid: AviationProp(_n, h, cache))

_CACHE: dict[tuple, PropSprite] = {}


def build(pid: str, h: int, cache: Path) -> PropSprite:
    key = (pid, h, str(cache))
    if key not in _CACHE:
        _CACHE[key] = PROPS.get(pid, ClockProp)(h, cache)
    return _CACHE[key]
