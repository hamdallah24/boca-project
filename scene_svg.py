#!/usr/bin/env python3
"""scene_svg.py — scene BOCA sebagai layer SVG bergaris tebal (bukan PIL blur).

Kontrak
-------
`build_layers(name, size)` -> dict {"sky", "clouds", "midground", "ground"}:
  * setiap nilai adalah string SVG siap di-rasterisasi Chromium headless
    (`make_boca.render_svg`) dengan latar transparan;
  * semua bentuk punya outline `INK` (#231815) setebal `SW_SCENE` (9 px di
    kanvas 1350×2400 ≈ 7 px di frame 1080 — sebanding dengan outline karakter);
  * tidak ada GaussianBlur, tidak ada gradien raster: bayangan = bidang datar.

Kenapa per layer:
  sky      0.35× kecepatan kamera
  clouds   0.55×
  midground 1.00×
  ground   1.15×
sehingga parallax terasa saat kamera pan/zoom.
"""
from __future__ import annotations

INK = "#231815"
SKY_TOP = "#8CC8F4"
SKY_BOT = "#D8ECFB"
CREAM = "#F6F1E7"
WALL_TOP = "#FAF3E2"
WALL_BOT = "#EDE2C8"
FLOOR = "#C89A6B"
FLOOR_D = "#A97A4E"
TEAL = "#1F6F78"
TEAL_D = "#15545B"
RED = "#D7263D"
YELLOW = "#F4B942"
WHITE = "#FFFFFF"
GLASS = "#CFE8F7"
ROAD = "#6E7278"
SIDEWALK = "#C9C7C2"
CURB = "#A8A6A1"
BUILDINGS = ["#D6AA8C", "#B4C4D6", "#E2C496", "#BED2C8", "#D2B4AA"]

SW_SCENE = 9


# --------------------------------------------------------------------- helper
def _r(x, y, w, h, fill, rx=0, sw=SW_SCENE, extra=""):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="{rx}" fill="{fill}" stroke="{INK}" stroke-width="{sw}" {extra}/>')


def _c(cx, cy, r, fill, sw=SW_SCENE, extra=""):
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" '
            f'stroke="{INK}" stroke-width="{sw}" {extra}/>')


def _p(d, fill, sw=SW_SCENE, extra=""):
    return (f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="{sw}" '
            f'stroke-linejoin="round" {extra}/>')


def _l(x1, y1, x2, y2, color=INK, w=SW_SCENE, extra=""):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{w}" stroke-linecap="round" {extra}/>')


def _cloud(cx, cy, s, fill=WHITE):
    """Awan satu path (outline hanya di tepi luar)."""
    return _p(
        f"M {cx-2.0*s:.1f},{cy:.1f} "
        f"C {cx-2.1*s:.1f},{cy-0.75*s:.1f} {cx-1.35*s:.1f},{cy-1.20*s:.1f} {cx-0.70*s:.1f},{cy-0.95*s:.1f} "
        f"C {cx-0.45*s:.1f},{cy-1.75*s:.1f} {cx+0.70*s:.1f},{cy-1.80*s:.1f} {cx+0.95*s:.1f},{cy-0.95*s:.1f} "
        f"C {cx+1.75*s:.1f},{cy-1.05*s:.1f} {cx+2.15*s:.1f},{cy+0.10*s:.1f} {cx+1.55*s:.1f},{cy+0.45*s:.1f} "
        f"L {cx-1.55*s:.1f},{cy+0.45*s:.1f} Z", fill)


def _svg(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">'
            f"<defs>{defs}</defs>{body}</svg>")


def _sky_defs(w, h, top=SKY_TOP, bot=SKY_BOT):
    return (f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{top}"/>'
            f'<stop offset="1" stop-color="{bot}"/></linearGradient>')


# ------------------------------------------------------------- city_street
def city_street_layers(w=1350, h=2400) -> dict:
    # --- sky
    sun = (_c(w * 0.80, h * 0.13, 92, YELLOW)
           + "".join(_l(w * 0.80 + 118 * __import__("math").cos(a),
                        h * 0.13 + 118 * __import__("math").sin(a),
                        w * 0.80 + 156 * __import__("math").cos(a),
                        h * 0.13 + 156 * __import__("math").sin(a),
                        YELLOW, 12)
                     for a in [i * 0.785 for i in range(8)]))
    sky = _svg(w, h,
               f'<rect width="{w}" height="{h}" fill="url(#sky)"/>'
               f'<rect y="{h*0.52:.0f}" width="{w}" height="{h*0.48:.0f}" fill="#EAF4FD"/>'
               + sun,
               _sky_defs(w, h))

    # --- clouds (outline, parallax 0.55)
    clouds = _svg(w, h,
                  _cloud(w * 0.13, h * 0.15, 40)
                  + _cloud(w * 0.44, h * 0.12, 50)
                  + _cloud(w * 0.62, h * 0.20, 30)
                  + _cloud(w * 0.31, h * 0.26, 24))

    # --- midground: gedung, jendela, lampu, toko
    parts = []
    for i, (x, bw, col) in enumerate(zip((0.02, 0.22, 0.46, 0.64, 0.86),
                                         (0.18, 0.22, 0.16, 0.20, 0.14),
                                         BUILDINGS)):
        bx, bwid = w * x, w * bw
        top = h * (0.24 + 0.02 * (i % 3))
        parts.append(_r(bx, top, bwid, h * 0.34, col, rx=6))
        parts.append(_r(bx - 14, top - 18, bwid + 28, 26, col, rx=6))
        for row in range(3):
            for col_i in range(3):
                wx = bx + 26 + col_i * (bwid - 52) / 3
                wy = top + 34 + row * h * 0.095
                parts.append(_r(wx, wy, (bwid - 52) / 3 - 14, h * 0.052, GLASS, rx=4, sw=5))
    # toko + kanopi
    parts.append(_r(w * 0.70, h * 0.44, w * 0.15, h * 0.10, "#F3E3C2", rx=4))
    parts.append(_r(w * 0.695, h * 0.425, w * 0.16, h * 0.035, TEAL, rx=4))
    parts.append(_l(w * 0.775, h * 0.46, w * 0.775, h * 0.54, INK, 7))
    # tiang lampu
    for x in (0.12, 0.52, 0.88):
        parts.append(_r(w * x, h * 0.34, 12, h * 0.24, "#5A6068", sw=6))
        parts.append(_c(w * x + 6, h * 0.335, 34, "#FFE08C", sw=6))
    mid = _svg(w, h, "".join(parts))

    # --- ground: trotoar, jalan, marka, bayangan
    g = []
    g.append(_r(0, h * 0.58, w, h * 0.07, SIDEWALK, sw=0))
    g.append(_l(0, h * 0.58, w, h * 0.58, INK, 10))
    g.append(_l(0, h * 0.65, w, h * 0.65, CURB, 8))
    g.append(_r(0, h * 0.65, w, h * 0.35, ROAD, sw=0))
    for i in range(6):
        g.append(_r(w * 0.05 + i * w * 0.17, h * 0.82, w * 0.08, h * 0.018,
                    "#FAE68C", rx=6, sw=5))
    # retak halus + bayangan gedung (flat, tanpa blur)
    for i in range(9):
        g.append(_l(w * i / 8.0, h * 0.585, w * i / 8.0, h * 0.648, CURB, 3))
    g.append(_p(f"M 0,{h*0.585:.0f} L {w:.0f},{h*0.585:.0f} "
                f"L {w:.0f},{h*0.597:.0f} L 0,{h*0.597:.0f} Z", "#00000018", sw=0))
    ground = _svg(w, h, "".join(g))

    return {"sky": sky, "clouds": clouds, "midground": mid, "ground": ground}


# --------------------------------------------------------------- classroom
def classroom_layers(w=1350, h=2400) -> dict:
    wall = _svg(w, h,
                f'<rect width="{w}" height="{h*0.72:.0f}" fill="url(#wall)"/>'
                f'<rect y="{h*0.72:.0f}" width="{w}" height="{h*0.28:.0f}" fill="{WALL_BOT}"/>',
                f'<linearGradient id="wall" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{WALL_TOP}"/>'
                f'<stop offset="1" stop-color="{WALL_BOT}"/></linearGradient>')

    # interior: tidak ada awan di dinding. Layer tetap ada (kosong) agar
    # kontrak 4-layer seragam dan renderer tidak perlu cabang khusus.
    clouds = _svg(w, h, "")

    parts = []
    # papan tulis
    parts.append(_r(w * 0.10, h * 0.08, w * 0.66, h * 0.26, TEAL, rx=8))
    parts.append(_r(w * 0.115, h * 0.095, w * 0.63, h * 0.23, "#548068", rx=6, sw=6))
    for i, (x0, x1) in enumerate(((0.16, 0.34), (0.16, 0.42), (0.16, 0.28))):
        parts.append(_l(w * x0, h * (0.14 + i * 0.045), w * x1, h * (0.14 + i * 0.045),
                        "#F0F6EC", 9))
    parts.append(_r(w * 0.10, h * 0.34, w * 0.66, h * 0.02, "#8A6B4B", rx=4, sw=6))
    # jendela
    parts.append(_r(w * 0.80, h * 0.10, w * 0.17, h * 0.30, "#F7FBFF", rx=8))
    parts.append(_r(w * 0.815, h * 0.115, w * 0.14, h * 0.27, GLASS, rx=4, sw=6))
    parts.append(_l(w * 0.885, h * 0.115, w * 0.885, h * 0.385, INK, 7))
    parts.append(_l(w * 0.815, h * 0.25, w * 0.955, h * 0.25, INK, 7))
    # jam dinding
    parts.append(_c(w * 0.735, h * 0.425, 48, "#FFFDF4"))
    parts.append(_c(w * 0.735, h * 0.425, 43, WHITE, sw=5))
    parts.append(_l(w * 0.735, h * 0.425, w * 0.735, h * 0.390, INK, 6))
    parts.append(_l(w * 0.735, h * 0.425, w * 0.760, h * 0.438, RED, 5))
    # rak buku
    parts.append(_r(w * 0.03, h * 0.38, w * 0.16, h * 0.12, "#C9A227", rx=4))
    for i in range(4):
        parts.append(_r(w * 0.045 + i * w * 0.033, h * 0.395, w * 0.024, h * 0.09,
                        [RED, TEAL, YELLOW, "#4C7DD6"][i], rx=3, sw=5))
    mid = _svg(w, h, "".join(parts))

    g = []
    g.append(_r(0, h * 0.70, w, h * 0.30, FLOOR, sw=0))
    g.append(_l(0, h * 0.70, w, h * 0.70, INK, 10))
    for i in range(7):
        g.append(_l(w * (i / 6.0), h * 0.70, w * (i / 5.2), h, FLOOR_D, 4))
    for row, (y, sc, shift) in enumerate(((0.745, 0.92, 0.0), (0.845, 1.0, 0.13))):
        for i in range(2):
            cx = w * (0.22 + shift + i * 0.30)
            dw = w * 0.22 * sc
            top_y = h * y
            # bidang meja (perspektif ringan)
            g.append(_p(f"M {cx-dw*0.5:.1f},{top_y:.1f} L {cx+dw*0.5:.1f},{top_y:.1f} "
                        f"L {cx+dw*0.43:.1f},{h*(y+0.022):.1f} L {cx-dw*0.43:.1f},{h*(y+0.022):.1f} Z",
                        "#E8C08A", sw=6))
            # bibir depan
            g.append(_r(cx - dw * 0.43, h * (y + 0.022), dw * 0.86, h * 0.016,
                        "#C79A68", rx=5, sw=5))
            # kaki
            g.append(_l(cx - dw * 0.36, h * (y + 0.038), cx - dw * 0.38, h * (y + 0.10), INK, 7))
            g.append(_l(cx + dw * 0.36, h * (y + 0.038), cx + dw * 0.38, h * (y + 0.10), INK, 7))

    ground = _svg(w, h, "".join(g))

    return {"sky": wall, "clouds": clouds, "midground": mid, "ground": ground}




# ---------------------------------------------------------- mountain_sunset
def mountain_sunset_layers(w=1350, h=2400) -> dict:
    """Senja di lembah: langit hangat, gunung berlapis, sawah + gubuk."""
    sky = _svg(
        w, h,
        f'<rect width="{w}" height="{h}" fill="url(#dusk)"/>'
        f'<rect y="{h*0.545:.0f}" width="{w}" height="{h*0.455:.0f}" fill="#F6D9A8"/>'
        + _c(w * 0.70, h * 0.285, 122, "#FFE9A3", sw=7)
        + _c(w * 0.70, h * 0.285, 92, YELLOW, sw=6),
        '<linearGradient id="dusk" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#6C5B9E"/>'
        '<stop offset="0.46" stop-color="#E76F51"/>'
        '<stop offset="0.78" stop-color="#F4A261"/>'
        '<stop offset="1" stop-color="#F7D08A"/></linearGradient>')

    clouds = _svg(w, h,
                  _cloud(w * 0.16, h * 0.17, 38, "#FBE3C8")
                  + _cloud(w * 0.47, h * 0.13, 46, "#FBE3C8")
                  + _cloud(w * 0.78, h * 0.22, 28, "#FBE3C8"))

    parts = []
    # gunung jauh
    parts.append(_p(f"M -40,{h*0.545:.1f} L {w*0.20:.1f},{h*0.255:.1f} "
                    f"L {w*0.47:.1f},{h*0.545:.1f} Z", "#8E7BB5"))
    parts.append(_p(f"M {w*0.30:.1f},{h*0.545:.1f} L {w*0.56:.1f},{h*0.215:.1f} "
                    f"L {w*0.92:.1f},{h*0.545:.1f} Z", "#6E5E9B"))
    parts.append(_p(f"M {w*0.68:.1f},{h*0.545:.1f} L {w*0.90:.1f},{h*0.30:.1f} "
                    f"L {w*1.05:.1f},{h*0.545:.1f} Z", "#55488A"))
    # puncak bersalju
    parts.append(_p(f"M {w*0.545:.1f},{h*0.245:.1f} L {w*0.56:.1f},{h*0.215:.1f} "
                    f"L {w*0.585:.1f},{h*0.255:.1f} L {w*0.57:.1f},{h*0.247:.1f} "
                    f"L {w*0.555:.1f},{h*0.262:.1f} Z", "#F6F1E7", sw=5))
    # sawah
    parts.append(_r(-10, h * 0.505, w + 20, h * 0.055, "#7DB36F", sw=0))
    parts.append(_l(-10, h * 0.505, w + 10, h * 0.505, INK, 9))
    for i in range(5):
        parts.append(_l(w * (0.05 + i * 0.22), h * 0.505, w * (0.02 + i * 0.22),
                        h * 0.56, "#5C9152", 4))
    # gubuk
    hx = w * 0.12
    parts.append(_r(hx, h * 0.455, w * 0.10, h * 0.052, "#B45309", rx=3))
    parts.append(_p(f"M {hx-18:.1f},{h*0.455:.1f} L {hx+w*0.05:.1f},{h*0.408:.1f} "
                    f"L {hx+w*0.10+18:.1f},{h*0.455:.1f} Z", "#D97706"))
    parts.append(_r(hx + w * 0.055, h * 0.474, w * 0.018, h * 0.033, "#7A4A22", rx=2, sw=5))
    # pohon
    for tx, ty, sc in ((0.86, 0.485, 1.0), (0.30, 0.495, 0.7)):
        parts.append(_r(w * tx - 8, h * ty - h * 0.02, 16, h * 0.075, "#7A4A22", sw=5))
        parts.append(_c(w * tx, h * ty - h * 0.045, 52 * sc, "#3F7D4E"))
        parts.append(_c(w * tx - 34 * sc, h * ty - h * 0.020, 34 * sc, "#57A05F"))
    mid = _svg(w, h, "".join(parts))

    g = []
    g.append(_r(-10, h * 0.56, w + 20, h * 0.44, "#C08A5A", sw=0))
    g.append(_l(-10, h * 0.56, w + 10, h * 0.56, INK, 10))
    g.append(_r(-10, h * 0.56, w + 20, h * 0.028, "#7DB36F", sw=6))
    g.append(_r(-10, h * 0.588, w + 20, h * 0.030, "#8F5F35", sw=0))
    g.append(_l(-10, h * 0.588, w + 10, h * 0.588, INK, 8))
    for i in range(6):
        g.append(_l(w * (0.05 + i * 0.185), h * 0.62, w * (0.02 + i * 0.19), h,
                    "#B07A45", 4))
    ground = _svg(w, h, "".join(g))

    return {"sky": sky, "clouds": clouds, "midground": mid, "ground": ground}



# --------------------------------------------------------------- park_evening
def park_evening_layers(w=1350, h=2400) -> dict:
    sky = _svg(
        w, h,
        f'<rect width="{w}" height="{h}" fill="url(#dusk2)"/>'
        + _c(w * 0.24, h * 0.30, 116, "#FFE9A3", sw=7)
        + _c(w * 0.24, h * 0.30, 86, "#F7B267", sw=6),
        '<linearGradient id="dusk2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#7A8FB5"/>'
        '<stop offset="0.55" stop-color="#F2A65A"/>'
        '<stop offset="1" stop-color="#FBD6A0"/></linearGradient>')
    clouds = _svg(w, h,
                  _cloud(w * 0.16, h * 0.14, 40, "#FFE8CC")
                  + _cloud(w * 0.56, h * 0.10, 48, "#FFE8CC")
                  + _cloud(w * 0.80, h * 0.20, 30, "#FFE8CC"))
    parts = []
    # bukit jauh
    parts.append(_p(f"M -20,{h*0.548:.0f} Q {w*0.28:.0f},{h*0.43:.0f} {w*0.60:.0f},{h*0.548:.0f} "
                    f"L {w+20:.0f},{h*0.548:.0f} L {w+20:.0f},{h*0.60:.0f} L -20,{h*0.60:.0f} Z",
                    "#8FAE7E", sw=6))
    # pohon
    for tx, sc in ((0.12, 1.0), (0.87, 1.15), (0.68, 0.72)):
        parts.append(_r(w * tx - 12 * sc, h * 0.44, 24 * sc, h * 0.115, "#7A4A22", sw=6))
        parts.append(_c(w * tx, h * 0.405, 96 * sc, "#3F7D4E"))
        parts.append(_c(w * tx - 52 * sc, h * 0.445, 58 * sc, "#57A05F"))
    # semak tepi
    for bx, by, br, col in ((0.03, 0.545, 58, "#4C8A55"), (0.27, 0.556, 40, "#57A05F"),
                            (0.96, 0.548, 50, "#4C8A55")):
        parts.append(_c(w * bx, h * by, br, col))
    # bangku
    bx = w * 0.40
    parts.append(_r(bx, h * 0.505, w * 0.20, h * 0.022, "#B4713C", rx=5))
    parts.append(_r(bx, h * 0.485, w * 0.20, h * 0.018, "#C98A4E", rx=5))
    parts.append(_l(bx + 16, h * 0.527, bx + 16, h * 0.567, INK, 8))
    parts.append(_l(bx + w * 0.20 - 16, h * 0.527, bx + w * 0.20 - 16, h * 0.567, INK, 8))
    # tiang lampu taman
    parts.append(_r(w * 0.52, h * 0.34, 12, h * 0.245, "#4A5058", sw=6))
    parts.append(_c(w * 0.526, h * 0.328, 34, "#FFE08C", sw=6))
    mid = _svg(w, h, "".join(parts))

    g = []
    g.append(_r(-10, h * 0.548, w + 20, h * 0.452, "#6FA96A", sw=0))
    g.append(_l(-10, h * 0.548, w + 10, h * 0.548, INK, 9))
    # jalan setapak melengkung ke bawah
    g.append(_p(f"M {w*0.40:.0f},{h*0.60:.0f} L {w*0.60:.0f},{h*0.60:.0f} "
                f"L {w*0.84:.0f},{h:.0f} L {w*0.10:.0f},{h:.0f} Z", "#D9C39A", sw=7))
    g.append(_p(f"M {w*0.455:.0f},{h*0.60:.0f} L {w*0.545:.0f},{h*0.60:.0f} "
                f"L {w*0.73:.0f},{h:.0f} L {w*0.29:.0f},{h:.0f} Z", "#CBB07F", sw=0))
    # rumput tepi jalan
    for i in range(12):
        gx = w * (i + 0.5) / 12.0
        if 0.24 < gx / w < 0.76:
            continue
        g.append(_l(gx, h * 0.72, gx - 10, h * 0.685, "#4C8A55", 4))
    ground = _svg(w, h, "".join(g))
    return {"sky": sky, "clouds": clouds, "midground": mid, "ground": ground}


# ------------------------------------------------------------------ city_top
def city_top_layers(w=1350, h=2400) -> dict:
    sky = _svg(w, h,
               f'<rect width="{w}" height="{h}" fill="url(#sky)"/>'
               + _c(w * 0.78, h * 0.14, 78, YELLOW, sw=7),
               _sky_defs(w, h, "#9ACBF2", "#DDEFFB"))
    clouds = _svg(w, h,
                  _cloud(w * 0.18, h * 0.16, 42)
                  + _cloud(w * 0.50, h * 0.11, 52)
                  + _cloud(w * 0.86, h * 0.18, 32))
    parts = []
    # skyline jauh + jendela
    for x, bw, bh in ((0.0, 0.14, 0.24), (0.15, 0.10, 0.30), (0.27, 0.16, 0.20),
                      (0.45, 0.12, 0.27), (0.60, 0.18, 0.22), (0.80, 0.10, 0.30),
                      (0.92, 0.12, 0.24)):
        top = h * (0.50 - bh)
        parts.append(_r(w * x, top, w * bw, h * (bh + 0.06), "#A9C4DB", rx=4))
        rows = max(2, int(bh / 0.045))
        for ci in range(3):
            wx = w * x + w * bw * (0.18 + 0.26 * ci)
            for ri in range(rows):
                wy = top + h * 0.030 + (h * bh * 0.72 / rows) * ri
                parts.append(_r(wx, wy, w * bw * 0.14, h * 0.016,
                                "#E8F4FD", rx=2, sw=2))
    # tangki air + AC di atap
    parts.append(_r(w * 0.06, h * 0.43, w * 0.10, h * 0.09, "#C7D3DD", rx=8))
    parts.append(_p(f"M {w*0.06:.0f},{h*0.43:.0f} L {w*0.11:.0f},{h*0.385:.0f} "
                    f"L {w*0.16:.0f},{h*0.43:.0f} Z", "#8FA3B5"))
    parts.append(_l(w * 0.08, h * 0.52, w * 0.08, h * 0.56, INK, 7))
    parts.append(_l(w * 0.14, h * 0.52, w * 0.14, h * 0.56, INK, 7))
    parts.append(_r(w * 0.34, h * 0.485, w * 0.12, h * 0.055, "#B9C6D2", rx=6))
    for i in range(4):
        parts.append(_l(w * 0.35 + i * w * 0.027, h * 0.495, w * 0.35 + i * w * 0.027,
                        h * 0.525, "#7E8C99", 4))
    # pipa ventilasi
    parts.append(_r(w * 0.235, h * 0.445, w * 0.022, h * 0.10, "#9AA8B6", rx=4, sw=5))
    parts.append(_r(w * 0.225, h * 0.437, w * 0.042, h * 0.016, "#7E8C99", rx=4, sw=5))
    # pagar atap
    parts.append(_r(-10, h * 0.505, w + 20, h * 0.014, "#8FA3B5", sw=6))
    for i in range(13):
        parts.append(_l(w * i / 12.0, h * 0.505, w * i / 12.0, h * 0.552, "#8FA3B5", 6))
    parts.append(_l(-10, h * 0.552, w + 10, h * 0.552, INK, 8))
    mid = _svg(w, h, "".join(parts))

    g = []
    g.append(_r(-10, h * 0.55, w + 20, h * 0.45, "#BEB7AC", sw=0))
    g.append(_l(-10, h * 0.55, w + 10, h * 0.55, INK, 10))
    g.append(_r(-10, h * 0.55, w + 20, h * 0.028, "#A8A198", sw=0))
    for i in range(4):
        g.append(_l(-10, h * (0.62 + i * 0.09), w + 10, h * (0.62 + i * 0.09), "#A49D93", 4))
    for i in range(6):
        g.append(_l(w * i / 5.0, h * 0.578, w * (i / 5.0 * 1.16 - 0.08), h, "#A49D93", 3))
    ground = _svg(w, h, "".join(g))
    return {"sky": sky, "clouds": clouds, "midground": mid, "ground": ground}


# ---------------------------------------------------------------- data_center
def data_center_layers(w=1350, h=2400) -> dict:
    wall = _svg(w, h,
                f'<rect width="{w}" height="{h}" fill="#1B2430"/>'
                f'<rect y="{h*0.60:.0f}" width="{w}" height="{h*0.40:.0f}" fill="#202A37"/>'
                + "".join(_l(0, h * (0.05 + i * 0.085), w, h * (0.05 + i * 0.085),
                             "#263241", 3) for i in range(7)))
    clouds = _svg(w, h, "")
    parts = []
    # rak server besar
    for k in range(4):
        x = w * (0.025 + k * 0.247)
        rw, top, rh = w * 0.215, h * 0.205, h * 0.395
        parts.append(_r(x, top, rw, rh, "#2E3B4E", rx=7, sw=6))
        for r in range(10):
            ry = top + h * 0.016 + r * (rh * 0.089)
            parts.append(_r(x + 12, ry, rw - 24, h * 0.026, "#3B4A5E", rx=3, sw=4))
            parts.append(_c(x + rw * 0.13, ry + h * 0.013, 5, "#3DDC97", sw=0))
            parts.append(_c(x + rw * 0.20, ry + h * 0.013, 5, "#F4B942", sw=0))
        # ventilasi atas
        for v in range(3):
            parts.append(_l(x + rw * (0.3 + v * 0.2), top + 8,
                            x + rw * (0.3 + v * 0.2), top + 26, "#4A5A70", 4))
    # lampu plafon
    for k in range(3):
        parts.append(_r(w * (0.10 + k * 0.31), h * 0.055, w * 0.16, h * 0.018,
                        "#F2F6FA", rx=6, sw=5))
    # kabel tray
    parts.append(_r(w * 0.02, h * 0.148, w * 0.96, h * 0.014, "#4A5A70", rx=5, sw=4))
    mid = _svg(w, h, "".join(parts))

    g = []
    g.append(_r(-10, h * 0.59, w + 20, h * 0.41, "#39485C", sw=0))
    g.append(_l(-10, h * 0.59, w + 10, h * 0.59, INK, 10))
    # lorong dingin: garis cahaya
    g.append(_r(w * 0.28, h * 0.595, w * 0.44, h * 0.012, "#5FA8D3", rx=6, sw=0))
    for i in range(5):
        g.append(_l(-10, h * (0.66 + i * 0.07), w + 10, h * (0.66 + i * 0.07), "#2C3848", 4))
    for i in range(6):
        g.append(_l(w * i / 5.0, h * 0.59, w * (i / 5.0 * 1.2 - 0.10), h, "#2C3848", 3))
    ground = _svg(w, h, "".join(g))
    return {"sky": wall, "clouds": clouds, "midground": mid, "ground": ground}


# --------------------------------------------------------------------- market
def market_layers(w=1350, h=2400) -> dict:
    sky = _svg(w, h,
               f'<rect width="{w}" height="{h}" fill="url(#sky)"/>'
               + _c(w * 0.82, h * 0.13, 74, YELLOW, sw=7),
               _sky_defs(w, h, "#BFE3F7", "#EAF6FD"))
    clouds = _svg(w, h, _cloud(w * 0.16, h * 0.14, 38) + _cloud(w * 0.50, h * 0.10, 46))
    parts = []
    # tiga warung dengan kanopi bergaris
    for k, (x, col) in enumerate(((0.005, RED), (0.345, TEAL), (0.685, "#4C7DD6"))):
        ww = w * 0.30
        px = w * x
        parts.append(_r(px, h * 0.38, ww, h * 0.205, "#F3E3C2", rx=4, sw=6))
        parts.append(_p(f"M {px-16:.0f},{h*0.385:.0f} L {px+ww+16:.0f},{h*0.385:.0f} "
                        f"L {px+ww-6:.0f},{h*0.315:.0f} L {px+6:.0f},{h*0.315:.0f} Z", col))
        for i in range(5):
            sx = px + ww * i / 5.0
            parts.append(_l(sx, h * 0.315, sx + 7, h * 0.385, "#FFFFFF", 5))
        # meja, peti, dan barang dagangan
        parts.append(_r(px + 10, h * 0.49, ww - 20, h * 0.024, "#B4713C", rx=4, sw=5))
        for i in range(4):
            parts.append(_c(px + ww * (0.17 + i * 0.22), h * 0.472, 20,
                            [RED, YELLOW, "#57A05F", "#E07A5F"][i], sw=5))
        parts.append(_r(px + ww * 0.14, h * 0.515, ww * 0.30, h * 0.045,
                        "#C98A4E", rx=4, sw=5))
        parts.append(_r(px + ww * 0.56, h * 0.515, ww * 0.30, h * 0.045,
                        "#C98A4E", rx=4, sw=5))
        # lampu gantung
        parts.append(_l(px + ww * 0.5, h * 0.315, px + ww * 0.5, h * 0.352, INK, 4))
        parts.append(_c(px + ww * 0.5, h * 0.362, 22, "#FFE08C", sw=5))
    # pot tanaman di ujung
    parts.append(_r(w * 0.955, h * 0.53, w * 0.035, h * 0.05, "#C98A4E", rx=4, sw=5))
    parts.append(_c(w * 0.972, h * 0.505, 34, "#4C8A55"))
    mid = _svg(w, h, "".join(parts))

    g = []
    g.append(_r(-10, h * 0.585, w + 20, h * 0.415, "#B9A88F", sw=0))
    g.append(_l(-10, h * 0.585, w + 10, h * 0.585, INK, 10))
    for i in range(4):
        g.append(_l(-10, h * (0.64 + i * 0.09), w + 10, h * (0.64 + i * 0.09), "#A6947C", 4))
    for i in range(6):
        g.append(_l(w * i / 5.0, h * 0.60, w * (i / 5.0 * 1.18 - 0.09), h, "#A6947C", 3))
    # tikar di tengah
    g.append(_r(w * 0.26, h * 0.70, w * 0.48, h * 0.10, "#8FAE7E", rx=14, sw=5))
    g.append(_r(w * 0.29, h * 0.715, w * 0.42, h * 0.07, "#A8C79A", rx=10, sw=3))
    ground = _svg(w, h, "".join(g))
    return {"sky": sky, "clouds": clouds, "midground": mid, "ground": ground}


# --------------------------------------------------------------- phone_inside
def phone_inside_layers(w=1350, h=2400) -> dict:
    wall = _svg(w, h,
                f'<rect width="{w}" height="{h}" fill="#10151C"/>'
                f'<rect y="{h*0.115:.0f}" width="{w}" height="{h*0.03:.0f}" fill="#1B2330"/>'
                f'<rect y="{h*0.82:.0f}" width="{w}" height="{h*0.18:.0f}" fill="#0C1015"/>'
                + "".join(_l(0, h * (0.20 + i * 0.10), w, h * (0.20 + i * 0.10),
                             "#161D27", 3) for i in range(6)))
    clouds = _svg(w, h, "")
    parts = []
    # status bar + judul
    parts.append(_r(w * 0.06, h * 0.155, w * 0.16, h * 0.012, "#6B7A8C", rx=6, sw=0))
    parts.append(_r(w * 0.78, h * 0.155, w * 0.16, h * 0.012, "#3B4757", rx=6, sw=0))
    # bubble chat kiri/kanan (di tepi, tengah tetap kosong)
    rows = [(0.24, 0.42, "#1F6F78", 0.02), (0.31, 0.30, "#243447", 0.52),
            (0.38, 0.36, "#243447", 0.02), (0.45, 0.26, "#1F6F78", 0.58),
            (0.66, 0.34, "#243447", 0.02), (0.73, 0.28, "#1F6F78", 0.56)]
    for y, bw, col, x in rows:
        parts.append(_r(w * x, h * y, w * bw, h * 0.048, col, rx=22, sw=5))
        parts.append(_r(w * (x + 0.03), h * (y + 0.014), w * (bw - 0.09), h * 0.012,
                        "#FFFFFF55", rx=6, sw=0))
    # ikon aplikasi di bawah
    for i in range(4):
        parts.append(_r(w * (0.10 + i * 0.21), h * 0.86, w * 0.10, h * 0.055,
                        ["#EF4444", "#22C55E", "#3B82F6", "#F59E0B"][i], rx=18, sw=5))
    mid = _svg(w, h, "".join(parts))
    ground = _svg(w, h, "")
    return {"sky": wall, "clouds": clouds, "midground": mid, "ground": ground}


# -------------------------------------------------------------------- bedroom
def bedroom_layers(w=1350, h=2400) -> dict:
    wall = _svg(w, h,
                f'<rect width="{w}" height="{h}" fill="url(#wall2)"/>'
                f'<rect y="{h*0.60:.0f}" width="{w}" height="{h*0.40:.0f}" fill="#F0E2CC"/>',
                '<linearGradient id="wall2" x1="0" y1="0" x2="0" y2="1">'
                '<stop offset="0" stop-color="#FBEFD8"/>'
                '<stop offset="1" stop-color="#F3E2C6"/></linearGradient>')
    clouds = _svg(w, h, "")
    parts = []
    # jendela
    parts.append(_r(w * 0.60, h * 0.09, w * 0.28, h * 0.25, "#FFFFFF", rx=10))
    parts.append(_r(w * 0.617, h * 0.105, w * 0.246, h * 0.22, "#BFE3F7", rx=6, sw=6))
    parts.append(_c(w * 0.795, h * 0.16, 30, YELLOW, sw=5))
    parts.append(_l(w * 0.74, h * 0.105, w * 0.74, h * 0.325, INK, 6))
    parts.append(_l(w * 0.617, h * 0.215, w * 0.863, h * 0.215, INK, 6))
    # tempat tidur
    bx = w * 0.05
    bw_ = w * 0.36
    parts.append(_r(bx - w * 0.015, h * 0.355, w * 0.035, h * 0.235,
                    "#8F6A44", rx=8, sw=6))          # headboard
    parts.append(_r(bx, h * 0.395, bw_, h * 0.155, "#B4713C", rx=10, sw=6))
    parts.append(_r(bx + 12, h * 0.408, bw_ - 24, h * 0.052, "#FFFFFF", rx=8, sw=5))
    parts.append(_r(bx + 22, h * 0.418, w * 0.10, h * 0.030, "#F7F9FC", rx=8, sw=4))
    parts.append(_r(bx + w * 0.14, h * 0.418, w * 0.10, h * 0.030, "#F7F9FC", rx=8, sw=4))
    parts.append(_r(bx + 12, h * 0.458, bw_ - 24, h * 0.092, "#5AA9E6", rx=8, sw=5))
    parts.append(_r(bx + 12, h * 0.497, bw_ - 24, h * 0.012, "#3F8FCC", rx=4, sw=0))
    parts.append(_l(bx + 18, h * 0.55, bx + 18, h * 0.60, INK, 7))
    parts.append(_l(bx + bw_ - 18, h * 0.55, bx + bw_ - 18, h * 0.60, INK, 7))
    # nakas + lampu
    parts.append(_r(w * 0.445, h * 0.50, w * 0.105, h * 0.10, "#C98A4E", rx=6, sw=5))
    parts.append(_r(w * 0.465, h * 0.462, w * 0.052, h * 0.040, "#F4B942", rx=6, sw=5))
    parts.append(_l(w * 0.491, h * 0.50, w * 0.491, h * 0.462, INK, 6))
    # lemari
    parts.append(_r(w * 0.87, h * 0.28, w * 0.10, h * 0.32, "#C98A4E", rx=6, sw=6))
    parts.append(_l(w * 0.92, h * 0.29, w * 0.92, h * 0.59, INK, 6))
    parts.append(_c(w * 0.905, h * 0.44, 7, INK, 0))
    parts.append(_c(w * 0.935, h * 0.44, 7, INK, 0))
    # hiasan dinding
    parts.append(_r(w * 0.455, h * 0.13, w * 0.10, h * 0.09, "#FFFFFF", rx=6, sw=5))
    parts.append(_p(f"M {w*0.465:.0f},{h*0.205:.0f} L {w*0.49:.0f},{h*0.155:.0f} "
                    f"L {w*0.515:.0f},{h*0.19:.0f} L {w*0.54:.0f},{h*0.15:.0f} "
                    f"L {w*0.545:.0f},{h*0.205:.0f} Z", "#8FAE7E", sw=3))
    mid = _svg(w, h, "".join(parts))

    g = []
    g.append(_r(-10, h * 0.59, w + 20, h * 0.41, "#C89A6B", sw=0))
    g.append(_l(-10, h * 0.59, w + 10, h * 0.59, INK, 10))
    for i in range(8):
        g.append(_l(w * i / 7.0, h * 0.59, w * (i / 7.0 * 1.25 - 0.12), h, "#B0835A", 3))
    g.append(_r(w * 0.32, h * 0.70, w * 0.40, h * 0.13, "#D77A6A", rx=26, sw=6))
    g.append(_r(w * 0.36, h * 0.72, w * 0.32, h * 0.09, "#E8988A", rx=20, sw=4))
    ground = _svg(w, h, "".join(g))
    return {"sky": wall, "clouds": clouds, "midground": mid, "ground": ground}


# --------------------------------------------------------------- airport_svg
def _raw_airport_svg() -> dict:
    sky = """
    <defs>
      <linearGradient id="airSky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#38BDF8"/>
        <stop offset="68%" stop-color="#BAE6FD"/>
        <stop offset="100%" stop-color="#E0F2FE"/>
      </linearGradient>
    </defs>
    <rect width="1350" height="2400" fill="url(#airSky)"/>
    <circle cx="180" cy="290" r="130" fill="#FEF08A" opacity="0.4"/>
    <circle cx="180" cy="290" r="85" fill="#FACC15" stroke="#1E293B" stroke-width="5"/>
    """
    clouds = """
    <g stroke="#1E293B" stroke-width="5" stroke-linejoin="round" fill="#FFFFFF">
      <path d="M260,350 Q260,300 310,300 Q335,255 395,260 Q450,265 465,310 Q510,315 510,350 Z"/>
      <path d="M740,240 Q740,190 790,190 Q815,145 875,150 Q930,155 945,200 Q995,205 995,240 Z"/>
    </g>
    """
    midground = """
    <g stroke="#1E293B" stroke-width="5" stroke-linejoin="round">
      <rect x="30" y="920" width="760" height="445" rx="14" fill="#F1F5F9"/>
      <path d="M10,925 L410,855 L810,925 Z" fill="#0284C7"/>
      <rect x="260" y="885" width="300" height="46" rx="10" fill="#FACC15"/>
      <g fill="#7DD3FC" stroke-width="4">
        <rect x="75" y="975" width="95" height="240" rx="6"/>
        <rect x="195" y="975" width="95" height="240" rx="6"/>
        <rect x="315" y="975" width="95" height="240" rx="6"/>
        <rect x="435" y="975" width="95" height="240" rx="6"/>
        <rect x="555" y="975" width="95" height="240" rx="6"/>
        <rect x="675" y="975" width="85" height="240" rx="6"/>
      </g>
      <rect x="1035" y="650" width="95" height="715" fill="#CBD5E1"/>
      <polygon points="980,655 1185,655 1215,520 950,520" fill="#E2E8F0"/>
      <polygon points="968,615 1197,615 1208,545 957,545" fill="#38BDF8"/>
      <rect x="945" y="492" width="275" height="34" rx="10" fill="#EF4444"/>
      <line x1="1082" y1="492" x2="1082" y2="415" stroke-width="6"/>
      <circle cx="1082" cy="408" r="14" fill="#FACC15"/>
      <g transform="translate(360, 990) scale(0.92)">
        <ellipse cx="320" cy="242" rx="280" ry="22" fill="#0F172A" opacity="0.25" stroke="none"/>
        <polygon points="55,140 15,35 95,35 155,140" fill="#EF4444"/>
        <path d="M55,140 L485,140 Q610,140 625,185 Q610,222 485,222 L75,212 Q40,205 55,140 Z" fill="#FFFFFF"/>
        <path d="M535,148 L595,168 L545,175 Z" fill="#1E293B"/>
        <g fill="#38BDF8" stroke-width="3">
          <circle cx="195" cy="175" r="10"/><circle cx="235" cy="175" r="10"/>
          <circle cx="275" cy="175" r="10"/><circle cx="315" cy="175" r="10"/>
          <circle cx="355" cy="175" r="10"/><circle cx="395" cy="175" r="10"/>
          <circle cx="435" cy="175" r="10"/><circle cx="475" cy="175" r="10"/>
        </g>
        <polygon points="270,192 430,192 220,248 165,248" fill="#CBD5E1"/>
        <rect x="275" y="218" width="68" height="32" rx="12" fill="#64748B"/>
      </g>
    </g>
    """
    ground = """
    <g stroke="#1E293B" stroke-width="5" stroke-linejoin="round">
      <rect x="-10" y="1335" width="1370" height="45" fill="#4ADE80"/>
      <rect x="-10" y="1375" width="1370" height="1025" fill="#475569"/>
      <rect x="-10" y="1405" width="1370" height="18" fill="#FFFFFF" stroke="none"/>
      <g fill="#FACC15" stroke-width="4">
        <rect x="55" y="1685" width="160" height="28" rx="6"/>
        <rect x="335" y="1685" width="160" height="28" rx="6"/>
        <rect x="615" y="1685" width="160" height="28" rx="6"/>
        <rect x="895" y="1685" width="160" height="28" rx="6"/>
        <rect x="1175" y="1685" width="160" height="28" rx="6"/>
      </g>
    </g>
    """
    return {"sky": sky, "clouds": clouds, "midground": midground, "ground": ground}


def airport_svg_layers(w=1350, h=2400) -> dict:
    return {k: _svg(w, h, v) for k, v in _raw_airport_svg().items()}


# --------------------------------------------------------------- sky_flight
def _raw_sky_flight() -> dict:
    sky = """
    <defs>
      <linearGradient id="flightSky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#0284C7"/>
        <stop offset="55%" stop-color="#38BDF8"/>
        <stop offset="100%" stop-color="#BAE6FD"/>
      </linearGradient>
    </defs>
    <rect width="1350" height="2400" fill="url(#flightSky)"/>
    <circle cx="1070" cy="300" r="145" fill="#FEF08A" opacity="0.38"/>
    <circle cx="1070" cy="300" r="95" fill="#FACC15" stroke="#1E293B" stroke-width="5"/>
    """
    clouds = """
    <g stroke="#1E293B" stroke-width="5" stroke-linejoin="round" fill="#FFFFFF">
      <path d="M90,390 Q90,335 145,335 Q175,285 245,290 Q305,295 320,345 Q375,350 375,390 Z"/>
      <path d="M530,245 Q530,195 580,195 Q608,145 675,150 Q730,155 745,205 Q795,210 795,245 Z"/>
      <path d="M880,550 Q880,505 925,505 Q950,460 1010,465 Q1060,470 1075,510 Q1120,515 1120,550 Z"/>
    </g>
    """
    midground = """
    <g stroke="#FFFFFF" stroke-width="8" stroke-linecap="round" opacity="0.45">
      <line x1="90" y1="680" x2="350" y2="680"/>
      <line x1="780" y1="810" x2="1150" y2="810"/>
      <line x1="220" y1="980" x2="540" y2="980"/>
      <line x1="880" y1="1120" x2="1240" y2="1120"/>
    </g>
    """
    ground = """
    <g stroke="#1E293B" stroke-width="5" stroke-linejoin="round">
      <path d="M-20,1385 Q90,1320 220,1370 Q360,1300 520,1365 Q680,1295 850,1365 Q1020,1305 1180,1365 Q1290,1330 1380,1380 L1380,2410 L-20,2410 Z" fill="#F8FAFC"/>
      <path d="M-20,1495 Q320,1455 680,1495 Q1030,1455 1380,1495 L1380,2410 L-20,2410 Z" fill="#E0F2FE" stroke="none"/>
    </g>
    """
    return {"sky": sky, "clouds": clouds, "midground": midground, "ground": ground}


def sky_flight_layers(w=1350, h=2400) -> dict:
    return {k: _svg(w, h, v) for k, v in _raw_sky_flight().items()}

SCENE_SVG = {
    "city_street": city_street_layers,
    "classroom": classroom_layers,
    "mountain_sunset": mountain_sunset_layers,
    "park_evening": park_evening_layers,
    "city_top": city_top_layers,
    "data_center": data_center_layers,
    "market": market_layers,
    "phone_inside": phone_inside_layers,
    "bedroom": bedroom_layers,
    "airport_svg": airport_svg_layers,
    "sky_flight": sky_flight_layers,
}
