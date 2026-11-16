#!/usr/bin/env python3
"""props.py — ikon properti kartun prosedural untuk layer `props` BOCA.

Semua ikon digambar dengan PIL (flat + outline ink), di-cache per (id, tinggi).
Dipakai oleh boca_pipeline.Art.build() lalu ditempel di render_episode().

Skema pemakaian di plan JSON:

    "props": [
      {"id": "clock", "t_in": 0.8, "t_out": 4.2, "x": 800, "y": 980,
       "h": 240, "anim": "pop_float", "badge": "2 jam", "loupe_from": [640, 1120]}
    ]
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

INK = (26, 22, 20, 255)
WHITE = (255, 255, 255, 255)
RED = (215, 38, 61, 255)
RED_D = (150, 24, 40, 255)
TEAL = (32, 150, 146, 255)
TEAL_D = (18, 96, 96, 255)
GOLD = (244, 185, 66, 255)
GOLD_D = (196, 132, 26, 255)
CREAM = (247, 238, 219, 255)
BLUE = (108, 178, 235, 255)
BLUE_D = (52, 112, 170, 255)
GREEN = (86, 168, 104, 255)

S = 480          # kanvas kerja (nanti di-downscale ke tinggi target)
SW = 7           # tebal outline


def _c(d, box, fill, w=SW):
    d.rounded_rectangle(box, radius=int(min(box[2] - box[0], box[3] - box[1]) * 0.28),
                        fill=fill, outline=INK, width=w)


# --------------------------------------------------------------------- ikon
def _clock(d):
    d.ellipse((100, 100, 380, 380), fill=CREAM, outline=INK, width=SW)
    d.ellipse((124, 124, 356, 356), outline=RED, width=SW)
    for i in range(12):
        a = i * math.pi / 6
        x0, y0 = 240 + math.sin(a) * 92, 240 - math.cos(a) * 92
        x1, y1 = 240 + math.sin(a) * 106, 240 - math.cos(a) * 106
        d.line((x0, y0, x1, y1), fill=INK, width=6)
    d.line((240, 240, 240, 168), fill=INK, width=12)          # jarum jam
    d.line((240, 240, 300, 262), fill=RED, width=9)           # jarum menit
    d.ellipse((228, 228, 252, 252), fill=RED, outline=INK, width=4)


def _phone(d):
    _c(d, (146, 74, 334, 406), (40, 44, 52, 255), 8)
    d.rounded_rectangle((164, 108, 316, 372), radius=8, fill=BLUE)
    d.rounded_rectangle((182, 126, 298, 210), radius=6, fill=WHITE)
    d.rounded_rectangle((182, 222, 298, 250), radius=6, fill=(230, 236, 244, 255))
    d.rounded_rectangle((182, 262, 298, 290), radius=6, fill=(230, 236, 244, 255))
    d.ellipse((228, 88, 252, 100), fill=(90, 96, 104, 255))
    d.ellipse((232, 382, 248, 396), fill=(120, 126, 134, 255))


def _coin_stack(d):
    for i, y in enumerate((300, 340, 380)):
        d.ellipse((126, y - 44, 354, y + 44), fill=GOLD, outline=INK, width=SW)
        d.ellipse((150, y - 26, 330, y + 26), outline=GOLD_D, width=6)
        d.line((206, y, 274, y), fill=GOLD_D, width=8)
        d.line((240, y - 22, 240, y + 22), fill=GOLD_D, width=8)
    d.ellipse((150, 120, 330, 208), fill=GOLD, outline=INK, width=SW)
    d.ellipse((186, 142, 294, 186), outline=GOLD_D, width=6)


def _wallet(d):
    _c(d, (96, 150, 384, 366), TEAL, 8)
    d.rounded_rectangle((120, 176, 360, 330), radius=18, fill=TEAL_D)
    d.rounded_rectangle((250, 218, 410, 300), radius=16, fill=GOLD, outline=INK, width=SW)
    d.ellipse((300, 244, 340, 284), fill=CREAM, outline=INK, width=5)
    d.line((120, 198, 300, 198), fill=TEAL_D, width=8)


def _money_note(d):
    _c(d, (70, 150, 410, 350), (236, 226, 190, 255), 8)
    d.rounded_rectangle((96, 176, 384, 324), radius=10, outline=GOLD_D, width=6)
    d.ellipse((180, 200, 300, 300), outline=GOLD_D, width=6)
    d.line((214, 232, 266, 232), fill=INK, width=9)
    d.line((240, 214, 240, 286), fill=INK, width=9)
    for x in (120, 340):
        d.ellipse((x - 12, 190, x + 12, 214), fill=GOLD_D)
        d.ellipse((x - 12, 286, x + 12, 310), fill=GOLD_D)


def _hourglass(d):
    d.line((140, 92, 340, 92), fill=INK, width=16)
    d.line((140, 388, 340, 388), fill=INK, width=16)
    d.polygon([(168, 108), (312, 108), (240, 240)], fill=CREAM, outline=INK)
    d.polygon([(168, 372), (312, 372), (240, 240)], fill=CREAM, outline=INK)
    d.polygon([(196, 126), (284, 126), (240, 214)], fill=GOLD)
    d.polygon([(214, 356), (266, 356), (240, 306)], fill=GOLD)
    d.polygon([(208, 370), (272, 370), (240, 392)], fill=GOLD)


def _bulb(d):
    d.ellipse((160, 80, 320, 250), fill=GOLD, outline=INK, width=SW)
    d.line((236, 250, 236, 120), fill=GOLD_D, width=10)
    d.rounded_rectangle((196, 250, 284, 300), radius=12, fill=(226, 226, 226, 255), outline=INK, width=SW)
    d.rounded_rectangle((196, 302, 284, 340), radius=10, fill=(200, 200, 200, 255), outline=INK, width=6)
    for a in (-50, -20, 20, 50):
        rad = math.radians(a - 90)
        x0, y0 = 240 + math.cos(rad) * 96, 165 + math.sin(rad) * 96
        x1, y1 = 240 + math.cos(rad) * 132, 165 + math.sin(rad) * 132
        d.line((x0, y0, x1, y1), fill=GOLD_D, width=9)


def _chart(d):
    d.line((96, 380, 400, 380), fill=INK, width=8)
    d.line((96, 380, 96, 100), fill=INK, width=8)
    for i, h in enumerate((70, 120, 96, 180)):
        x = 128 + i * 68
        d.rounded_rectangle((x, 380 - h, x + 46, 372), radius=8, fill=(RED if i == 3 else TEAL),
                            outline=INK, width=6)
    d.line((120, 250, 190, 200, 260, 220, 340, 132), fill=RED, width=10)
    d.polygon([(340, 132), (300, 140), (330, 168)], fill=RED)


def _calendar(d):
    _c(d, (96, 116, 384, 396), WHITE, 8)
    d.rounded_rectangle((96, 116, 384, 186), radius=16, fill=RED)
    d.rectangle((96, 160, 384, 186), fill=RED)
    for x in (168, 312):
        d.line((x, 92, x, 140), fill=INK, width=12)
    for r in range(3):
        for c in range(4):
            d.rounded_rectangle((128 + c * 64, 214 + r * 58, 172 + c * 64, 252 + r * 58),
                                radius=6, fill=(230, 226, 216, 255), outline=INK, width=4)


def _heart(d):
    pts = []
    for i in range(72):
        a = i / 72 * math.tau
        hx = 16 * math.sin(a) ** 3
        hy = -(13 * math.cos(a) - 5 * math.cos(2 * a)
               - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((240 + hx * 9.6, 236 + hy * 9.6))
    d.polygon(pts, fill=RED, outline=INK, width=9)
    d.arc((160, 148, 236, 216), 200, 320, fill=(255, 158, 168, 255), width=9)


def _star(d):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = 170 if i % 2 == 0 else 74
        pts.append((240 + math.cos(a) * r, 240 + math.sin(a) * r))
    d.polygon(pts, fill=GOLD, outline=INK)


def _arrow(d):
    d.polygon([(70, 190), (240, 190), (240, 120), (410, 250), (240, 380), (240, 310), (70, 310)],
              fill=RED, outline=INK)


def _badge(d):
    _c(d, (70, 170, 410, 330), WHITE, 8)
    d.rounded_rectangle((92, 192, 388, 308), radius=20, outline=RED, width=6)
    d.rounded_rectangle((232, 208, 248, 268), radius=6, fill=RED)
    d.ellipse((230, 276, 250, 296), fill=RED)


def _dot(d):
    d.ellipse((140, 140, 340, 340), fill=RED, outline=INK, width=SW)


PROPS: dict[str, callable] = {
    "clock": _clock, "phone": _phone, "coin_stack": _coin_stack, "wallet": _wallet,
    "money_note": _money_note, "hourglass": _hourglass, "bulb": _bulb, "chart": _chart,
    "calendar": _calendar, "heart": _heart, "star": _star, "arrow": _arrow,
    "badge": _badge, "dot": _dot,
}

_CACHE: dict[tuple, Image.Image] = {}


def build(pid: str, h: int = 220) -> Image.Image:
    """Buat (atau ambil dari cache) sprite properti setinggi h px."""
    key = (pid, h)
    if key in _CACHE:
        return _CACHE[key]
    fn = PROPS.get(pid) or _dot
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    fn(d)
    w = max(1, int(round(h * canvas.width / canvas.height)))
    img = canvas.resize((w, h), Image.Resampling.LANCZOS)
    _CACHE[key] = img
    return img


def ids() -> list[str]:
    return sorted(PROPS)
