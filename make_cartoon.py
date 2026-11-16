#!/usr/bin/env python3
"""Cartoon scene backgrounds for BOCA animatics.

Flat-vector illustration style (no photos) so the art matches the hand-drawn
BOCA character: bold flat shapes, soft gradients, no realism. Every scene is
drawn oversized so the camera can pan inside it.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def gradient(size: tuple[int, int], stops: list[tuple[float, tuple[int, int, int]]]) -> Image.Image:
    w, h = size
    ys = np.linspace(0.0, 1.0, h)
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for c in range(3):
        vals = np.zeros(h, dtype=np.float64)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            m = (ys >= p0) & (ys <= p1)
            if not m.any():
                continue
            loc = (ys[m] - p0) / max(p1 - p0, 1e-9)
            vals[m] = c0[c] + (c1[c] - c0[c]) * loc
        vals[ys < stops[0][0]] = stops[0][1][c]
        vals[ys > stops[-1][0]] = stops[-1][1][c]
        arr[:, :, c] = vals.astype(np.uint8)[:, None]
    return Image.fromarray(arr, "RGB")


def flat_cloud(d: ImageDraw.ImageDraw, x: float, y: float, s: float,
               top=(255, 255, 255), bottom=(214, 234, 255)) -> None:
    """Flat cartoon cloud made of overlapping ellipses."""
    puffs = [(-1.10, 0.10, 0.62, 0.36), (-0.35, -0.22, 0.80, 0.52),
             (0.48, -0.05, 0.66, 0.42), (1.05, 0.12, 0.50, 0.30)]
    for dx, dy, rx, ry in puffs:
        d.ellipse((x + dx * s - rx * s, y + dy * s - ry * s,
                   x + dx * s + rx * s, y + dy * s + ry * s), fill=bottom)
    for dx, dy, rx, ry in puffs:
        d.ellipse((x + dx * s - rx * s, y + dy * s - ry * s - s * 0.10,
                   x + dx * s + rx * s, y + dy * s + ry * s - s * 0.10), fill=top)


def cartoon_sun(d: ImageDraw.ImageDraw, x: float, y: float, r: float,
                color=(255, 214, 96), ray_color=(255, 232, 150), rays: int = 12,
                ray_len: float = 1.85) -> None:
    for i in range(rays):
        a = math.radians(i * 360 / rays)
        x1 = x + math.cos(a) * r * 1.18
        y1 = y + math.sin(a) * r * 1.18
        x2 = x + math.cos(a) * r * ray_len
        y2 = y + math.sin(a) * r * ray_len
        w = r * 0.16
        nx, ny = -math.sin(a) * w, math.cos(a) * w
        d.polygon([(x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x2, y2)], fill=ray_color)
    d.ellipse((x - r, y - r, x + r, y + r), fill=color)


def flat_stars(d: ImageDraw.ImageDraw, w: int, h: int, count: int, seed: int) -> None:
    rng = np.random.default_rng(seed)
    for _ in range(count):
        x = float(rng.integers(0, w))
        y = float(rng.integers(0, int(h * 0.8)))
        r = float(rng.integers(2, 6))
        a = int(rng.integers(140, 255))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, a))
    for _ in range(count // 14):
        x = float(rng.integers(0, w))
        y = float(rng.integers(0, int(h * 0.7)))
        r = float(rng.integers(10, 20))
        d.polygon([(x, y - r), (x + r * 0.28, y - r * 0.28), (x + r, y),
                   (x + r * 0.28, y + r * 0.28), (x, y + r), (x - r * 0.28, y + r * 0.28),
                   (x - r, y), (x - r * 0.28, y - r * 0.28)], fill=(255, 255, 255, 230))


def cartoon_earth(d: ImageDraw.ImageDraw, x: float, y: float, r: float) -> None:
    d.ellipse((x - r * 1.10, y - r * 1.10, x + r * 1.10, y + r * 1.10), fill=(120, 200, 255, 60))
    d.ellipse((x - r, y - r, x + r, y + r), fill=(46, 134, 222))
    d.ellipse((x - r * 0.62, y - r * 0.55, x + r * 0.05, y + r * 0.18), fill=(96, 196, 110))
    d.ellipse((x + r * 0.02, y - r * 0.05, x + r * 0.62, y + r * 0.62), fill=(78, 178, 96))
    d.ellipse((x - r * 0.45, y + r * 0.30, x + r * 0.12, y + r * 0.70), fill=(120, 206, 126))
    d.ellipse((x - r * 0.30, y - r * 0.86, x + r * 0.40, y - r * 0.52), fill=(236, 248, 255))
    d.ellipse((x - r * 0.86, y + r * 0.10, x - r * 0.34, y + r * 0.34), fill=(236, 248, 255))
    d.ellipse((x - r, y - r, x + r, y + r), outline=(214, 240, 255), width=max(3, int(r * 0.02)))


def cartoon_hill(d: ImageDraw.ImageDraw, w: int, h: int, color: tuple[int, int, int],
                 y_base: float, bumps: list[tuple[float, float, float]]) -> None:
    """Rolling flat hills: bumps = (center_x_ratio, height_ratio, half_width_ratio)."""
    pts: list[tuple[float, float]] = [(0, h), (0, y_base)]
    for cx, hh, hw in bumps:
        pts.append((cx * w, y_base - hh * h))
    pts.append((w, y_base))
    pts.append((w, h))
    d.polygon(pts, fill=color)


def cartoon_prism(d: ImageDraw.ImageDraw, x: float, y: float, s: float) -> None:
    """Glass prism with a white beam in and a flat rainbow fan out."""
    colors = [(255, 88, 88), (255, 166, 74), (255, 224, 96),
              (110, 220, 130), (78, 170, 255), (158, 110, 255)]
    # rainbow fan out to the right
    for i, c in enumerate(colors):
        a = math.radians(-16 + i * 8)
        x2 = x + math.cos(a) * s * 7.5
        y2 = y + math.sin(a) * s * 7.5 + s * 0.2
        d.line((x, y, x2, y2), fill=(*c, 70), width=int(s * 0.42))
        d.line((x, y, x2, y2), fill=(*c, 235), width=int(s * 0.16))
    # incoming white beam
    d.line((0, y - s * 1.5, x - s * 0.55, y - s * 0.25), fill=(255, 255, 255, 210), width=int(s * 0.34))
    d.line((0, y - s * 1.5, x - s * 0.55, y - s * 0.25), fill=(255, 255, 255, 255), width=int(s * 0.16))
    # glass triangle
    tri = [(x, y - s), (x - s * 0.88, y + s * 0.62), (x + s * 0.88, y + s * 0.62)]
    d.polygon(tri, fill=(196, 232, 255, 150))
    d.line([tri[0], tri[1]], fill=(120, 170, 210), width=int(s * 0.09))
    d.line([tri[1], tri[2]], fill=(120, 170, 210), width=int(s * 0.09))
    d.line([tri[2], tri[0]], fill=(120, 170, 210), width=int(s * 0.09))


def soft_glow(im: Image.Image, x: float, y: float, r: float, color, alpha: int = 40) -> None:
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse((x - r, y - r, x + r, y + r), fill=(*color, alpha))
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(r * 0.35)))


# --------------------------------------------------------------------- scenes
def scene_park(size: tuple[int, int], evening: bool = False, sun_left: bool = False) -> Image.Image:
    w, h = size
    cx, cy = w / 2, h / 2
    if evening:
        im = gradient(size, [(0.0, (92, 54, 120)), (0.45, (232, 120, 92)),
                              (0.75, (255, 186, 104)), (1.0, (255, 224, 168))]).convert("RGBA")
    else:
        im = gradient(size, [(0.0, (74, 168, 235)), (0.55, (150, 214, 248)),
                              (1.0, (214, 240, 252))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    sx = cx - w * 0.30 if sun_left else cx + w * 0.30
    sy = cy - h * 0.30
    soft_glow(im, sx, sy, 380, (255, 235, 160), 70)
    d = ImageDraw.Draw(im)
    cartoon_sun(d, sx, sy, 120 if not evening else 150)
    flat_cloud(d, cx - w * 0.24, cy - h * 0.36, 170)
    flat_cloud(d, cx + w * 0.20, cy - h * 0.22, 130)
    flat_cloud(d, cx + w * 0.02, cy - h * 0.05, 100)
    ground = cy + h * 0.18
    if evening:
        cartoon_hill(d, w, h, (62, 38, 70), ground, [(0.25, 0.10, 0.40), (0.75, 0.07, 0.45)])
        cartoon_hill(d, w, h, (44, 26, 52), ground + h * 0.06, [(0.60, 0.08, 0.50)])
    else:
        cartoon_hill(d, w, h, (124, 203, 106), ground, [(0.22, 0.09, 0.42), (0.72, 0.07, 0.48)])
        cartoon_hill(d, w, h, (96, 186, 92), ground + h * 0.07, [(0.55, 0.07, 0.50)])
        # grass tufts
        for i in range(26):
            gx = (i * 137) % w
            gy = ground + h * 0.03 + (i * 53) % int(h * 0.10)
            d.line((gx, gy, gx + 6, gy - 34), fill=(84, 170, 82), width=7)
    return im.convert("RGB")


def scene_sky(size: tuple[int, int]) -> Image.Image:
    w, h = size
    cx, cy = w / 2, h / 2
    im = gradient(size, [(0.0, (36, 132, 226)), (0.5, (96, 182, 240)),
                          (1.0, (196, 232, 252))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    cartoon_sun(d, cx + w * 0.30, cy - h * 0.32, 105, ray_color=(255, 240, 180))
    flat_cloud(d, cx - w * 0.26, cy - h * 0.22, 190)
    flat_cloud(d, cx + w * 0.14, cy - h * 0.34, 140)
    flat_cloud(d, cx - w * 0.05, cy + h * 0.06, 120)
    flat_cloud(d, cx + w * 0.30, cy + h * 0.12, 100)
    cartoon_hill(d, w, h, (118, 198, 104), cy + h * 0.30, [(0.30, 0.06, 0.45), (0.80, 0.05, 0.40)])
    return im.convert("RGB")


def scene_space(size: tuple[int, int]) -> Image.Image:
    w, h = size
    cx, cy = w / 2, h / 2
    im = gradient(size, [(0.0, (8, 12, 34)), (0.6, (16, 26, 60)), (1.0, (26, 44, 92))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    flat_stars(d, w, h, 150, 4)
    cartoon_sun(d, cx - w * 0.34, cy - h * 0.30, 110, ray_color=(255, 226, 140))
    # sun beam to earth
    ex, ey, er = cx + w * 0.22, cy + h * 0.14, 300
    d.line((cx - w * 0.34, cy - h * 0.30, ex, ey), fill=(255, 250, 220, 70), width=70)
    d.line((cx - w * 0.34, cy - h * 0.30, ex, ey), fill=(255, 255, 255, 220), width=18)
    soft_glow(im, ex, ey, er * 1.25, (120, 200, 255), 60)
    d = ImageDraw.Draw(im)
    cartoon_earth(d, ex, ey, er)
    return im.convert("RGB")


def scene_prism(size: tuple[int, int]) -> Image.Image:
    w, h = size
    cx, cy = w / 2, h / 2
    im = gradient(size, [(0.0, (250, 246, 238)), (1.0, (226, 216, 240))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    for i in range(5):
        d.ellipse((cx - w * 0.55 + i * 30, cy - h * 0.55 + i * 30,
                   cx + w * 0.55 - i * 30, cy + h * 0.55 - i * 30),
                  outline=(255, 255, 255, 90), width=26)
    cartoon_prism(d, cx + w * 0.18, cy - h * 0.02, 190)
    return im.convert("RGB")


def scene_atmosphere(size: tuple[int, int]) -> Image.Image:
    w, h = size
    cx, cy = w / 2, h / 2
    im = gradient(size, [(0.0, (4, 8, 22)), (0.55, (10, 22, 48)), (1.0, (16, 40, 78))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    flat_stars(d, w, h, 110, 9)
    # earth limb as a huge flat circle
    r = h * 0.86
    ey = cy + h * 0.72
    d.ellipse((cx - r, ey - r, cx + r, ey + r), fill=(30, 126, 200))
    d.ellipse((cx - r, ey - r - h * 0.055, cx + r, ey + r - h * 0.055), fill=(126, 214, 255))
    d.ellipse((cx - r, ey - r, cx + r, ey + r), fill=(30, 126, 200))
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((cx - r, ey - r - h * 0.075, cx + r, ey + r - h * 0.075), fill=(140, 220, 255, 150))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(im)
    # a few cartoon cloud arcs on the limb
    for i in range(5):
        flat_cloud(d, cx - w * 0.30 + i * w * 0.16, ey - r + h * 0.10 + (i % 2) * 30, 70)
    return im.convert("RGB")


def scene_sunset(size: tuple[int, int]) -> Image.Image:
    w, h = size
    cx, cy = w / 2, h / 2
    im = gradient(size, [(0.0, (58, 28, 86)), (0.35, (140, 58, 110)),
                          (0.62, (245, 108, 84)), (0.84, (255, 178, 96)),
                          (1.0, (255, 222, 156))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    sy = cy + h * 0.30
    soft_glow(im, cx, sy, 520, (255, 190, 110), 80)
    d = ImageDraw.Draw(im)
    cartoon_sun(d, cx, sy, 230, ray_color=(255, 214, 140), rays=14, ray_len=1.35)
    flat_cloud(d, cx - w * 0.26, cy - h * 0.26, 160, top=(255, 214, 190), bottom=(238, 150, 128))
    flat_cloud(d, cx + w * 0.22, cy - h * 0.10, 130, top=(255, 226, 200), bottom=(244, 168, 120))
    cartoon_hill(d, w, h, (52, 28, 60), cy + h * 0.40, [(0.30, 0.07, 0.45), (0.78, 0.05, 0.42)])
    return im.convert("RGB")


def _room_base(size, wall_top, wall_bottom, floor, horizon=0.58):
    w, h = size
    im = gradient(size, [(0.0, wall_top), (horizon, wall_bottom)]).convert("RGBA")
    d = ImageDraw.Draw(im)
    fy = int(h * horizon)
    d.rectangle((0, fy, w, h), fill=floor)
    d.line((0, fy, w, fy), fill=(255, 255, 255, 40), width=5)
    return im, d, fy


def _window(d, box, day=True):
    x0, y0, x1, y1 = box
    frame = (255, 255, 255)
    d.rounded_rectangle(box, radius=22, fill=frame)
    pad = 18
    d.rectangle((x0 + pad, y0 + pad, x1 - pad, y1 - pad),
                fill=(150, 210, 246) if day else (26, 32, 72))
    if day:
        d.ellipse((x1 - 150, y0 + 50, x1 - 70, y0 + 130), fill=(255, 232, 150))
        flat_cloud(d, x0 + (x1 - x0) * 0.40, y0 + (y1 - y0) * 0.55, 48)
    else:
        d.ellipse((x1 - 160, y0 + 60, x1 - 80, y0 + 140), fill=(246, 244, 214))
        for sx, sy in [(0.18, 0.20), (0.32, 0.42), (0.62, 0.18), (0.72, 0.50), (0.48, 0.66)]:
            d.ellipse((x0 + (x1 - x0) * sx, y0 + (y1 - y0) * sy,
                       x0 + (x1 - x0) * sx + 7, y0 + (y1 - y0) * sy + 7), fill=(255, 255, 255))
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    d.rectangle((mx - 7, y0 + pad, mx + 7, y1 - pad), fill=frame)
    d.rectangle((x0 + pad, my - 7, x1 - pad, my + 7), fill=frame)


def _shelf(d, x0, y0, x1, y1):
    d.rectangle((x0, y0, x1, y1), fill=(196, 150, 110))
    for i in range(2):
        y = y0 + (y1 - y0) * (0.5 + i * 0.5)
        d.rectangle((x0, y - 6, x1, y), fill=(160, 116, 84))
    colors = [(214, 90, 80), (90, 150, 200), (240, 190, 90), (110, 180, 120), (180, 120, 200)]
    for i in range(7):
        bx = x0 + 10 + i * ((x1 - x0) / 8)
        bh = (y1 - y0) * 0.30
        d.rectangle((bx, y0 + (y1 - y0) * 0.50 - bh, bx + 16,
                     y0 + (y1 - y0) * 0.50), fill=colors[i % 5])


def _plant(d, x, y, s=1.0):
    top = y - 70 * s
    d.polygon([(x - 42 * s, top), (x + 42 * s, top),
               (x + 30 * s, y), (x - 30 * s, y)], fill=(196, 110, 84))
    for dx, dy, r in [(-26, -110, 36), (2, -142, 46), (28, -108, 34), (-6, -78, 34)]:
        d.ellipse((x + dx * s - r * s, y + dy * s - r * s,
                   x + dx * s + r * s, y + dy * s + r * s), fill=(76, 166, 96))


def scene_bedroom(size, night=False):
    w, h = size
    if night:
        wall = ((48, 44, 88), (74, 66, 120))
        floor = (96, 70, 74)
    else:
        wall = ((252, 240, 222), (246, 224, 198))
        floor = (178, 136, 106)
    im, d, fy = _room_base(size, wall[0], wall[1], floor, 0.58)
    _window(d, (w * 0.52, h * 0.14, w * 0.86, h * 0.40), day=not night)
    d.rounded_rectangle((w * 0.09, h * 0.17, w * 0.29, h * 0.33), radius=8, fill=(255, 255, 255))
    d.rectangle((w * 0.11, h * 0.19, w * 0.27, h * 0.31),
                fill=(255, 206, 120) if not night else (120, 150, 220))
    d.ellipse((w * 0.14, h * 0.22, w * 0.24, h * 0.29),
              fill=(255, 120, 96) if not night else (250, 220, 120))
    _shelf(d, w * 0.60, h * 0.44, w * 0.90, h * 0.52)
    bx0, by0 = w * 0.02, h * 0.62
    d.rounded_rectangle((bx0, by0, bx0 + w * 0.34, by0 + h * 0.13), radius=26,
                        fill=(120, 150, 220) if night else (240, 120, 110))
    d.rounded_rectangle((bx0 + 10, by0 - h * 0.05, bx0 + w * 0.32, by0 + h * 0.04),
                        radius=18, fill=(255, 255, 255))
    d.rounded_rectangle((bx0 + w * 0.30, by0 - h * 0.10, bx0 + w * 0.36, by0 + h * 0.02),
                        radius=12, fill=(150, 110, 90))
    d.ellipse((w * 0.38, h * 0.80, w * 0.92, h * 0.92),
              fill=(246, 196, 120) if not night else (120, 96, 150))
    if night:
        soft_glow(im, w * 0.92, h * 0.52, 180, (255, 210, 120), 90)
        d = ImageDraw.Draw(im)
        d.polygon([(w * 0.90, h * 0.50), (w * 0.94, h * 0.50),
                   (w * 0.96, h * 0.55), (w * 0.88, h * 0.55)], fill=(255, 214, 130))
    else:
        _plant(d, w * 0.90, h * 0.92, 0.9)
    return im.convert("RGB")


def scene_kitchen(size):
    w, h = size
    im, d, fy = _room_base(size, (246, 244, 238), (232, 226, 214), (196, 168, 132), 0.58)
    d.rectangle((w * 0.04, h * 0.10, w * 0.44, h * 0.30), fill=(214, 150, 104))
    for i in range(3):
        x0 = w * 0.04 + i * (w * 0.40 / 3)
        d.rectangle((x0 + 8, h * 0.12, x0 + w * 0.40 / 3 - 8, h * 0.28), fill=(232, 176, 124))
        d.ellipse((x0 + w * 0.40 / 3 - 30, h * 0.19, x0 + w * 0.40 / 3 - 18, h * 0.21),
                  fill=(120, 80, 60))
    d.rounded_rectangle((w * 0.72, h * 0.30, w * 0.96, h * 0.62), radius=18, fill=(228, 236, 240))
    d.line((w * 0.72, h * 0.44, w * 0.96, h * 0.44), fill=(160, 176, 184), width=8)
    d.rectangle((w * 0.93, h * 0.36, w * 0.945, h * 0.42), fill=(150, 166, 174))
    d.rectangle((w * 0.02, h * 0.54, w * 0.70, h * 0.60), fill=(246, 246, 242))
    d.rectangle((w * 0.02, h * 0.60, w * 0.70, h * 0.66), fill=(196, 150, 110))
    for cx, cc in [(0.10, (255, 214, 120)), (0.18, (150, 210, 150)), (0.26, (240, 140, 120))]:
        x = w * cx
        d.rounded_rectangle((x, h * 0.46, x + 70, h * 0.54), radius=10, fill=cc)
    d.rounded_rectangle((w * 0.52, h * 0.45, w * 0.60, h * 0.54), radius=12, fill=(210, 230, 245))
    for i in range(6):
        d.ellipse((w * 0.53 + i * 8, h * 0.50, w * 0.535 + i * 8, h * 0.515), fill=(240, 190, 80))
    d.ellipse((w * 0.36, h * 0.74, w * 0.90, h * 0.84), fill=(232, 200, 160))
    d.rectangle((w * 0.60, h * 0.80, w * 0.64, h * 0.92), fill=(190, 150, 110))
    return im.convert("RGB")


def scene_classroom(size):
    w, h = size
    im, d, fy = _room_base(size, (250, 244, 226), (238, 228, 204), (186, 150, 112), 0.56)
    d.rounded_rectangle((w * 0.12, h * 0.10, w * 0.88, h * 0.42), radius=12, fill=(70, 110, 92))
    d.rounded_rectangle((w * 0.13, h * 0.11, w * 0.87, h * 0.41), radius=8, fill=(84, 128, 104))
    d.line((w * 0.20, h * 0.18, w * 0.42, h * 0.18), fill=(240, 246, 236), width=8)
    d.line((w * 0.20, h * 0.24, w * 0.52, h * 0.24), fill=(240, 246, 236), width=8)
    d.line((w * 0.20, h * 0.30, w * 0.36, h * 0.30), fill=(240, 246, 236), width=8)
    d.ellipse((w * 0.62, h * 0.16, w * 0.78, h * 0.34), outline=(240, 246, 236), width=8)
    _window(d, (w * 0.02, h * 0.46, w * 0.24, h * 0.64))
    for i in range(3):
        y = h * (0.66 + i * 0.10)
        d.rectangle((w * (0.06 + i * 0.06), y, w * (0.94 - i * 0.02), y + h * 0.05),
                    fill=(222, 178, 124))
        d.rectangle((w * (0.08 + i * 0.06), y + h * 0.05, w * (0.10 + i * 0.06), y + h * 0.11),
                    fill=(150, 110, 80))
    d.ellipse((w * 0.84, h * 0.50, w * 0.96, h * 0.62), fill=(110, 180, 220))
    d.ellipse((w * 0.87, h * 0.52, w * 0.93, h * 0.58), fill=(120, 200, 120))
    return im.convert("RGB")


def scene_market(size):
    w, h = size
    im = gradient(size, [(0.0, (250, 226, 170)), (0.55, (255, 240, 206)),
                         (1.0, (238, 214, 176))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    for i, cc in enumerate([(230, 90, 80), (80, 160, 140), (240, 170, 70)]):
        x0 = w * (0.02 + i * 0.32)
        x1 = x0 + w * 0.30
        d.polygon([(x0, h * 0.18), (x1, h * 0.18), (x1 - 40, h * 0.30), (x0 + 40, h * 0.30)], fill=cc)
        inner = (x1 - x0) * 0.76
        for k in range(3):
            sx = x0 + (x1 - x0) * 0.12 + k * (inner / 3)
            d.rectangle((sx, h * 0.18, sx + inner / 3, h * 0.24),
                        fill=(255, 255, 255, 70))
        d.rectangle((x0 + 30, h * 0.30, x0 + 40, h * 0.62), fill=(150, 110, 70))
        d.rectangle((x1 - 40, h * 0.30, x1 - 30, h * 0.62), fill=(150, 110, 70))
    d.rectangle((0, h * 0.56, w, h * 0.66), fill=(196, 150, 104))
    for i in range(6):
        cx = w * (0.08 + i * 0.16)
        d.ellipse((cx - 46, h * 0.50, cx + 46, h * 0.58), fill=(240, 180, 90))
        for k in range(4):
            d.ellipse((cx - 30 + k * 16, h * 0.51, cx - 16 + k * 16, h * 0.55), fill=(210, 80, 70))
    for i in range(3):
        x = w * (0.10 + i * 0.30)
        d.arc((x, h * 0.70, x + 120, h * 0.80), 180, 360, fill=(180, 130, 80), width=14)
        d.ellipse((x + 14, h * 0.68, x + 106, h * 0.74), fill=(120, 190, 110))
    for i in range(2):
        x = w * (0.22 + i * 0.44)
        d.rounded_rectangle((x, h * 0.34, x + 90, h * 0.44), radius=8, fill=(255, 255, 255))
        d.line((x + 14, h * 0.37, x + 76, h * 0.37), fill=(90, 90, 90), width=6)
        d.line((x + 14, h * 0.41, x + 60, h * 0.41), fill=(90, 90, 90), width=6)
    d.rectangle((0, h * 0.66, w, h), fill=(224, 196, 150))
    return im.convert("RGB")

def scene_city_top(size):
    w, h = size
    im = gradient(size, [(0.0, (120, 190, 240)), (0.45, (180, 220, 250)),
                         (1.0, (236, 246, 252))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    flat_cloud(d, w * 0.18, h * 0.10, 150)
    flat_cloud(d, w * 0.80, h * 0.16, 120)
    blocks = [(0.02, 0.44, 0.10, 0.22), (0.12, 0.38, 0.09, 0.30), (0.22, 0.46, 0.12, 0.20),
              (0.36, 0.36, 0.10, 0.32), (0.48, 0.42, 0.13, 0.24), (0.62, 0.34, 0.11, 0.34),
              (0.74, 0.44, 0.12, 0.22), (0.86, 0.38, 0.12, 0.30)]
    for x, y, bw, bh in blocks:
        d.rectangle((w * x, h * y, w * (x + bw), h * 0.66), fill=(150, 186, 214))
        for r in range(4):
            for c in range(3):
                if (r + c) % 2 == 0:
                    d.rectangle((w * x + 16 + c * 26, h * y + 20 + r * 34,
                                 w * x + 30 + c * 26, h * y + 40 + r * 34), fill=(236, 246, 255))
    d.rectangle((0, h * 0.66, w, h), fill=(110, 170, 120))
    d.polygon([(0, h * 0.66), (w, h * 0.66), (w * 0.70, h * 0.78), (w * 0.30, h * 0.78)],
              fill=(120, 124, 132))
    d.line((w * 0.50, h * 0.66, w * 0.50, h * 0.78), fill=(250, 230, 120), width=10)
    d.rectangle((0, h * 0.86, w, h), fill=(196, 150, 110))
    return im.convert("RGB")


def scene_city_street(size):
    w, h = size
    im = gradient(size, [(0.0, (140, 200, 244)), (0.5, (198, 228, 250)),
                         (1.0, (240, 248, 252))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    for x, bw, cc in [(0.02, 0.18, (214, 170, 140)), (0.22, 0.22, (180, 196, 214)),
                      (0.46, 0.16, (226, 196, 150)), (0.64, 0.20, (190, 210, 200)),
                      (0.86, 0.14, (210, 180, 170))]:
        d.rectangle((w * x, h * 0.20, w * (x + bw), h * 0.58), fill=cc)
        for r in range(3):
            for c in range(3):
                d.rectangle((w * x + 18 + c * (w * bw / 3.4), h * 0.24 + r * h * 0.09,
                             w * x + 52 + c * (w * bw / 3.4), h * 0.24 + r * h * 0.09 + 46),
                            fill=(236, 246, 255))
    d.rectangle((0, h * 0.58, w, h * 0.68), fill=(206, 206, 204))
    d.rectangle((0, h * 0.68, w, h), fill=(110, 114, 120))
    for i in range(6):
        d.rectangle((w * 0.05 + i * w * 0.17, h * 0.82, w * 0.13 + i * w * 0.17, h * 0.84),
                    fill=(250, 230, 140))
    for x in (0.12, 0.52, 0.88):
        d.rectangle((w * x, h * 0.30, w * x + 10, h * 0.58), fill=(90, 96, 104))
        d.ellipse((w * x - 26, h * 0.26, w * x + 36, h * 0.32), fill=(255, 224, 140))
    d.rectangle((w * 0.70, h * 0.44, w * 0.84, h * 0.50), fill=(70, 150, 160))
    d.rectangle((w * 0.71, h * 0.50, w * 0.715, h * 0.58), fill=(90, 96, 104))
    d.rectangle((w * 0.835, h * 0.50, w * 0.84, h * 0.58), fill=(90, 96, 104))
    return im.convert("RGB")


def scene_beach(size):
    w, h = size
    im = gradient(size, [(0.0, (92, 186, 240)), (0.42, (168, 222, 248)),
                         (0.56, (110, 200, 214)), (0.62, (238, 214, 160)),
                         (1.0, (246, 226, 180))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    cartoon_sun(d, w * 0.78, h * 0.14, 110)
    flat_cloud(d, w * 0.22, h * 0.14, 140)
    d.rectangle((0, h * 0.50, w, h * 0.60), fill=(64, 170, 200))
    for i in range(5):
        d.arc((w * (0.02 + i * 0.2), h * 0.50, w * (0.18 + i * 0.2), h * 0.56),
              200, 340, fill=(200, 240, 250), width=8)
    d.rectangle((0, h * 0.60, w, h), fill=(244, 222, 168))
    d.line((w * 0.14, h * 0.62, w * 0.18, h * 0.34), fill=(150, 110, 70), width=26)
    for a in (-150, -110, -70, -30):
        d.arc((w * 0.18 - 120, h * 0.30 - 80, w * 0.18 + 120, h * 0.30 + 80),
              a, a + 70, fill=(86, 168, 96), width=22)
    d.polygon([(w * 0.62, h * 0.44), (w * 0.84, h * 0.44), (w * 0.73, h * 0.38)],
              fill=(240, 110, 100))
    d.line((w * 0.73, h * 0.44, w * 0.73, h * 0.66), fill=(150, 110, 70), width=10)
    for i in range(6):
        x = w * (0.06 + i * 0.14)
        y = h * (0.80 + (i % 2) * 0.05)
        d.ellipse((x, y, x + 34, y + 22), fill=(255, 246, 236))
    return im.convert("RGB")


def scene_underwater(size):
    w, h = size
    im = gradient(size, [(0.0, (46, 150, 196)), (0.35, (26, 104, 160)),
                         (1.0, (10, 48, 96))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    for i in range(5):
        x = w * (0.06 + i * 0.22)
        d.polygon([(x, h * 0.02), (x + w * 0.10, h * 0.02),
                   (x + w * 0.22, h * 0.70), (x + w * 0.06, h * 0.70)],
                  fill=(200, 240, 255, 34))
    for i in range(16):
        x = w * (0.05 + ((i * 37) % 90) / 100)
        y = h * (0.10 + ((i * 53) % 80) / 100)
        r = 6 + ((i * 7) % 12)
        d.ellipse((x - r, y - r, x + r, y + r), outline=(220, 246, 255, 150), width=3)
    d.ellipse((-w * 0.2, h * 0.78, w * 1.2, h * 1.15), fill=(214, 190, 140))
    for x, cc in [(0.12, (240, 120, 130)), (0.30, (250, 170, 110)),
                  (0.72, (220, 130, 190)), (0.88, (250, 190, 120))]:
        bx = w * x
        d.rounded_rectangle((bx - 18, h * 0.72, bx + 18, h * 0.86), radius=16, fill=cc)
        d.rounded_rectangle((bx - 56, h * 0.68, bx - 14, h * 0.80), radius=16, fill=cc)
        d.rounded_rectangle((bx + 14, h * 0.66, bx + 56, h * 0.78), radius=16, fill=cc)
    for i in range(5):
        x = w * (0.05 + i * 0.22)
        for k in range(3):
            d.arc((x - 20, h * (0.70 + k * 0.05), x + 30, h * (0.78 + k * 0.05)),
                  200, 340, fill=(70, 170, 120), width=12)
    for i in range(4):
        x = w * (0.18 + i * 0.2)
        y = h * (0.24 + (i % 2) * 0.08)
        d.ellipse((x, y, x + 90, y + 44), fill=(250, 190, 90))
        d.polygon([(x, y + 22), (x - 34, y), (x - 34, y + 44)], fill=(250, 190, 90))
        d.ellipse((x + 66, y + 12, x + 74, y + 20), fill=(40, 40, 40))
    return im.convert("RGB")


def scene_body_inside(size):
    w, h = size
    im = gradient(size, [(0.0, (120, 40, 64)), (0.45, (168, 58, 80)),
                         (1.0, (214, 104, 110))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    for i in range(5):
        y = h * (0.12 + i * 0.16)
        d.line((0, y, w, y + 60), fill=(150, 40, 60), width=70)
        d.line((0, y, w, y + 60), fill=(226, 110, 120), width=34)
    for i in range(12):
        x = w * (0.04 + ((i * 29) % 92) / 100)
        y = h * (0.10 + ((i * 41) % 70) / 100)
        r = 36 + ((i * 11) % 22)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(250, 180, 190, 180))
        d.ellipse((x - r * 0.4, y - r * 0.4, x + r * 0.3, y + r * 0.3),
                  fill=(190, 70, 96, 180))
    for i in range(6):
        x = w * (0.1 + i * 0.15)
        d.line((x, h * 0.80, x + 30, h * 0.72, x + 60, h * 0.80),
               fill=(255, 232, 150), width=8)
    return im.convert("RGB")

def scene_phone_inside(size):
    w, h = size
    im = gradient(size, [(0.0, (14, 26, 32)), (1.0, (22, 42, 48))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    for i in range(9):
        y = h * (0.08 + i * 0.10)
        d.line((0, y, w, y), fill=(40, 140, 110), width=5)
        for j in range(7):
            x = w * (0.05 + j * 0.14)
            d.line((x, y, x, y + h * 0.05), fill=(40, 140, 110), width=5)
            d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(90, 210, 160))
    for x, y, cw, ch, cc in [(0.10, 0.30, 0.22, 0.16, (40, 60, 70)),
                             (0.42, 0.18, 0.20, 0.14, (48, 70, 82)),
                             (0.62, 0.46, 0.24, 0.18, (36, 56, 66))]:
        d.rounded_rectangle((w * x, h * y, w * (x + cw), h * (y + ch)), radius=10, fill=cc)
        for k in range(6):
            d.line((w * x + 12 + k * 18, h * y, w * x + 12 + k * 18, h * y - 14),
                   fill=(150, 170, 180), width=5)
    d.rounded_rectangle((w * 0.10, h * 0.62, w * 0.46, h * 0.74), radius=12, fill=(60, 80, 60))
    for k in range(4):
        d.rectangle((w * 0.12 + k * w * 0.085, h * 0.64,
                     w * 0.18 + k * w * 0.085, h * 0.72), fill=(140, 230, 120))
    for i, cc in enumerate([(240, 110, 110), (110, 190, 240), (250, 200, 110)]):
        d.rounded_rectangle((w * (0.62 + i * 0.11), h * 0.70,
                             w * (0.70 + i * 0.11), h * 0.78), radius=16, fill=cc)
    return im.convert("RGB")


def scene_data_center(size):
    w, h = size
    im = gradient(size, [(0.0, (10, 16, 26)), (1.0, (18, 30, 44))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    for i in range(8):
        d.line((0, h * 0.70 + i * h * 0.04, w, h * 0.70 + i * h * 0.04), fill=(40, 60, 80), width=3)
    for i in range(9):
        d.line((w * i / 8, h * 0.70, w * i / 8, h), fill=(40, 60, 80), width=3)
    for i in range(4):
        x = w * (0.04 + i * 0.24)
        d.rectangle((x, h * 0.16, x + w * 0.18, h * 0.70), fill=(28, 40, 54))
        for r in range(8):
            d.rectangle((x + 10, h * 0.18 + r * h * 0.06,
                         x + w * 0.18 - 10, h * 0.18 + r * h * 0.06 + h * 0.045),
                        fill=(38, 54, 70))
            for k in range(4):
                on = (r * 4 + k + i) % 3 == 0
                d.ellipse((x + 18 + k * 16, h * 0.19 + r * h * 0.06,
                           x + 26 + k * 16, h * 0.19 + r * h * 0.06 + 8),
                          fill=(120, 230, 170) if on else (60, 80, 96))
    for i in range(4):
        d.arc((w * (0.02 + i * 0.24), h * 0.04, w * (0.26 + i * 0.24), h * 0.20),
              0, 180, fill=(80, 110, 140), width=8)
    return im.convert("RGB")


def scene_neuron_city(size):
    w, h = size
    im = gradient(size, [(0.0, (10, 22, 34)), (0.6, (16, 40, 54)),
                         (1.0, (22, 60, 74))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    nodes = [(0.12, 0.22), (0.34, 0.14), (0.58, 0.26), (0.82, 0.16), (0.22, 0.48),
             (0.48, 0.42), (0.74, 0.50), (0.90, 0.40), (0.10, 0.72), (0.36, 0.70),
             (0.62, 0.74), (0.86, 0.66)]
    edges = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6), (6, 7),
             (4, 8), (8, 9), (9, 10), (10, 11), (5, 9), (2, 6)]
    for a, b in edges:
        x1, y1 = w * nodes[a][0], h * nodes[a][1]
        x2, y2 = w * nodes[b][0], h * nodes[b][1]
        d.line((x1, y1, x2, y2), fill=(60, 160, 180), width=14)
        d.line((x1, y1, x2, y2), fill=(120, 230, 240), width=5)
    for i, (x, y) in enumerate(nodes):
        r = 34 if i % 3 else 46
        soft_glow(im, w * x, h * y, r * 2.4, (120, 240, 250), 60)
        d = ImageDraw.Draw(im)
        d.ellipse((w * x - r, h * y - r, w * x + r, h * y + r), fill=(40, 110, 130))
        d.ellipse((w * x - r * 0.6, h * y - r * 0.6, w * x + r * 0.6, h * y + r * 0.6),
                  fill=(150, 240, 250))
    return im.convert("RGB")


def scene_airport(size):
    w, h = size
    im = gradient(size, [(0.0, (120, 186, 238)), (0.45, (184, 222, 250)),
                         (1.0, (240, 248, 252))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    flat_cloud(d, w * 0.20, h * 0.12, 150)
    flat_cloud(d, w * 0.74, h * 0.18, 120)
    d.rectangle((w * 0.72, h * 0.30, w * 0.78, h * 0.62), fill=(226, 230, 236))
    d.rectangle((w * 0.68, h * 0.26, w * 0.82, h * 0.32), fill=(120, 170, 200))
    d.rectangle((w * 0.70, h * 0.24, w * 0.80, h * 0.27), fill=(90, 120, 140))
    d.rectangle((0, h * 0.44, w * 0.60, h * 0.62), fill=(236, 240, 244))
    for i in range(6):
        d.rectangle((w * 0.03 + i * w * 0.095, h * 0.47,
                     w * 0.10 + i * w * 0.095, h * 0.56), fill=(150, 200, 230))
    d.rectangle((0, h * 0.62, w, h), fill=(120, 124, 130))
    for i in range(7):
        d.rectangle((w * 0.04 + i * w * 0.14, h * 0.80,
                     w * 0.11 + i * w * 0.14, h * 0.82), fill=(250, 240, 180))
    px, py = w * 0.14, h * 0.70
    d.ellipse((px + 40, py + 86, px + 360, py + 118), fill=(96, 100, 106))
    d.ellipse((px, py, px + 320, py + 76), fill=(252, 252, 254))
    d.rectangle((px + 40, py + 34, px + 280, py + 48), fill=(70, 140, 200))
    d.polygon([(px + 128, py + 32), (px + 214, py - 54),
               (px + 244, py - 48), (px + 188, py + 36)], fill=(236, 242, 248))
    d.polygon([(px + 160, py + 44), (px + 96, py + 100),
               (px + 140, py + 104), (px + 210, py + 48)], fill=(226, 232, 240))
    d.polygon([(px + 320, py + 16), (px + 376, py + 34), (px + 320, py + 56)],
              fill=(214, 60, 70))
    for i in range(7):
        d.ellipse((px + 62 + i * 28, py + 24, px + 76 + i * 28, py + 38),
                  fill=(90, 150, 190))
    return im.convert("RGB")


def scene_bank(size):
    w, h = size
    im, d, fy = _room_base(size, (246, 240, 226), (232, 222, 200), (176, 150, 116), 0.58)
    for i in range(4):
        x = w * (0.06 + i * 0.24)
        d.rectangle((x, h * 0.12, x + 70, h * 0.56), fill=(238, 232, 218))
        d.rectangle((x - 14, h * 0.10, x + 84, h * 0.15), fill=(226, 218, 200))
        d.rectangle((x - 10, h * 0.54, x + 80, h * 0.58), fill=(226, 218, 200))
    d.rectangle((0, h * 0.56, w, h * 0.68), fill=(186, 140, 96))
    d.rectangle((0, h * 0.56, w, h * 0.60), fill=(214, 176, 128))
    d.ellipse((w * 0.68, h * 0.30, w * 0.96, h * 0.58), fill=(150, 158, 168))
    d.ellipse((w * 0.72, h * 0.34, w * 0.92, h * 0.54), fill=(120, 128, 140))
    d.ellipse((w * 0.80, h * 0.42, w * 0.84, h * 0.46), fill=(220, 226, 232))
    for a in range(0, 360, 45):
        d.line((w * 0.82, h * 0.44,
                w * 0.82 + 50 * math.cos(math.radians(a)),
                h * 0.44 + 50 * math.sin(math.radians(a))), fill=(190, 196, 204), width=6)
    return im.convert("RGB")


def scene_money_print(size):
    w, h = size
    im, d, fy = _room_base(size, (40, 52, 66), (28, 38, 50), (70, 80, 92), 0.60)
    for i in range(2):
        x = w * (0.06 + i * 0.46)
        d.rounded_rectangle((x, h * 0.28, x + w * 0.36, h * 0.62), radius=14, fill=(90, 104, 120))
        d.rectangle((x + 16, h * 0.32, x + w * 0.36 - 16, h * 0.44), fill=(50, 60, 72))
        d.rectangle((x + 16, h * 0.48, x + w * 0.36 - 16, h * 0.56), fill=(120, 180, 150))
        for k in range(5):
            d.ellipse((x + 28 + k * 22, h * 0.50, x + 38 + k * 22, h * 0.54),
                      fill=(220, 240, 220))
    for i in range(3):
        cx = w * (0.16 + i * 0.30)
        d.ellipse((cx - 60, h * 0.66, cx + 60, h * 0.76), fill=(230, 236, 240))
        d.ellipse((cx - 22, h * 0.68, cx + 22, h * 0.74), fill=(120, 140, 160))
    for i in range(4):
        x = w * (0.10 + i * 0.16)
        d.polygon([(x, h * 0.80), (x + 110, h * 0.80),
                   (x + 120, h * 0.88), (x + 10, h * 0.88)], fill=(190, 220, 190))
    return im.convert("RGB")

def scene_stock_board(size):
    w, h = size
    im = gradient(size, [(0.0, (18, 26, 40)), (1.0, (30, 44, 62))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((w * 0.05, h * 0.08, w * 0.95, h * 0.50), radius=14, fill=(12, 22, 34))
    for i in range(6):
        d.line((w * 0.07, h * (0.12 + i * 0.07), w * 0.93, h * (0.12 + i * 0.07)),
               fill=(34, 52, 70), width=3)
    pts = [(0.08, 0.42), (0.18, 0.34), (0.28, 0.38), (0.38, 0.26), (0.48, 0.30),
           (0.58, 0.18), (0.68, 0.24), (0.78, 0.14), (0.90, 0.20)]
    poly = [(w * x, h * y) for x, y in pts]
    d.line(poly, fill=(90, 230, 160), width=8, joint="curve")
    d.polygon(poly + [(w * 0.90, h * 0.48), (w * 0.08, h * 0.48)], fill=(90, 230, 160, 50))
    for x, y, up in [(0.20, 0.62, True), (0.50, 0.66, False), (0.78, 0.60, True)]:
        if up:
            d.polygon([(w * x, h * y), (w * x + 30, h * y - 40), (w * x + 30, h * y - 16),
                       (w * x + 70, h * y - 16), (w * x + 70, h * y + 16),
                       (w * x + 30, h * y + 16), (w * x + 30, h * y + 40)], fill=(90, 230, 160))
        else:
            d.polygon([(w * x, h * y - 20), (w * x + 30, h * y + 20), (w * x + 30, h * y - 4),
                       (w * x + 70, h * y - 4), (w * x + 70, h * y + 36),
                       (w * x + 30, h * y + 36), (w * x + 30, h * y + 12)], fill=(240, 110, 110))
    d.rectangle((0, h * 0.70, w, h), fill=(24, 34, 48))
    return im.convert("RGB")


def scene_lake_ice(size):
    w, h = size
    im = gradient(size, [(0.0, (36, 62, 96)), (0.4, (96, 136, 168)),
                         (0.62, (196, 222, 236)), (1.0, (232, 244, 250))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.polygon([(0, h * 0.60), (w * 0.22, h * 0.20), (w * 0.46, h * 0.60)], fill=(226, 238, 246))
    d.polygon([(w * 0.30, h * 0.60), (w * 0.58, h * 0.16), (w * 0.86, h * 0.60)], fill=(206, 224, 238))
    d.polygon([(w * 0.58, h * 0.60), (w * 0.80, h * 0.30), (w, h * 0.60)], fill=(216, 232, 242))
    d.polygon([(w * 0.22, h * 0.20), (w * 0.30, h * 0.34), (w * 0.16, h * 0.34)],
              fill=(255, 255, 255))
    d.rectangle((0, h * 0.58, w, h), fill=(28, 58, 88))
    for i in range(5):
        d.arc((w * (0.02 + i * 0.20), h * 0.62, w * (0.18 + i * 0.20), h * 0.68),
              200, 340, fill=(120, 180, 210), width=6)
    d.polygon([(w * 0.10, h * 0.78), (w * 0.22, h * 0.60), (w * 0.36, h * 0.78)],
              fill=(226, 242, 250))
    d.polygon([(w * 0.62, h * 0.82), (w * 0.76, h * 0.62), (w * 0.90, h * 0.82)],
              fill=(214, 236, 248))
    d.ellipse((-w * 0.2, h * 0.44, w * 1.2, h * 0.60), fill=(255, 255, 255, 40))
    return im.convert("RGB")


def scene_rain_cloud(size):
    w, h = size
    im = gradient(size, [(0.0, (90, 120, 150)), (0.5, (150, 178, 198)),
                         (1.0, (206, 220, 228))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    cartoon_sun(d, w * 0.82, h * 0.10, 90, ray_color=(255, 236, 170))
    flat_cloud(d, w * 0.30, h * 0.22, 260, top=(246, 248, 252), bottom=(168, 184, 198))
    flat_cloud(d, w * 0.62, h * 0.30, 200, top=(240, 244, 250), bottom=(158, 176, 192))
    for i in range(40):
        x = w * (0.04 + ((i * 23) % 92) / 100)
        y = h * (0.30 + ((i * 37) % 50) / 100)
        d.line((x, y, x - 12, y + 46), fill=(180, 214, 240, 190), width=5)
    d.ellipse((-w * 0.2, h * 0.74, w * 1.2, h * 1.1), fill=(120, 170, 120))
    d.ellipse((w * 0.30, h * 0.80, w * 0.70, h * 0.88), fill=(150, 200, 230))
    return im.convert("RGB")


def scene_galaxy(size):
    w, h = size
    im = gradient(size, [(0.0, (8, 8, 26)), (0.5, (24, 16, 56)),
                         (1.0, (44, 26, 80))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    flat_stars(d, w, h, 220, 11)
    for i in range(5):
        r = w * (0.22 + i * 0.06)
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.ellipse((w * 0.5 - r, h * 0.42 - r * 0.55,
                    w * 0.5 + r, h * 0.42 + r * 0.55),
                   outline=(150, 110, 220, 60), width=int(r * 0.22))
        im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(r * 0.10)))
    d = ImageDraw.Draw(im)
    soft_glow(im, w * 0.72, h * 0.66, 190, (120, 180, 255), 70)
    d = ImageDraw.Draw(im)
    cartoon_earth(d, w * 0.72, h * 0.66, 120)
    d.line((w * 0.10, h * 0.14, w * 0.26, h * 0.22), fill=(255, 240, 200, 180), width=10)
    d.ellipse((w * 0.255, h * 0.205, w * 0.275, h * 0.235), fill=(255, 250, 220))
    return im.convert("RGB")


def scene_garden(size):
    w, h = size
    im = gradient(size, [(0.0, (128, 196, 240)), (0.5, (190, 228, 248)),
                         (1.0, (238, 248, 246))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    cartoon_sun(d, w * 0.80, h * 0.12, 100)
    flat_cloud(d, w * 0.22, h * 0.12, 120)
    for i in range(3):
        y = h * (0.62 + i * 0.10)
        d.rounded_rectangle((w * 0.04, y, w * 0.96, y + h * 0.06), radius=18, fill=(146, 104, 74))
        d.rounded_rectangle((w * 0.04, y, w * 0.96, y + h * 0.02), radius=10, fill=(168, 122, 86))
    for i in range(6):
        x = w * (0.10 + i * 0.15)
        for k in range(3):
            y = h * (0.60 + k * 0.10)
            d.line((x, y, x, y - h * 0.05), fill=(86, 168, 96), width=8)
            d.ellipse((x - 18, y - h * 0.07, x + 18, y - h * 0.03), fill=(110, 190, 110))
    d.rounded_rectangle((w * 0.68, h * 0.80, w * 0.82, h * 0.88), radius=12, fill=(90, 160, 200))
    d.line((w * 0.68, h * 0.82, w * 0.62, h * 0.78), fill=(90, 160, 200), width=10)
    return im.convert("RGB")


def scene_dark_forest(size):
    w, h = size
    im = gradient(size, [(0.0, (16, 34, 30)), (0.55, (28, 58, 48)),
                         (1.0, (44, 80, 62))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    for i in range(4):
        x = w * (0.12 + i * 0.24)
        d.polygon([(x, h * 0.02), (x + w * 0.08, h * 0.02),
                   (x + w * 0.20, h * 0.78), (x + w * 0.06, h * 0.78)],
                  fill=(220, 240, 180, 26))
    for x, wd in [(0.06, 60), (0.24, 74), (0.46, 54), (0.68, 80), (0.88, 62)]:
        d.rectangle((w * x, h * 0.06, w * x + wd, h * 0.80), fill=(38, 52, 40))
        d.line((w * x + wd * 0.5, h * 0.06, w * x + wd * 0.5, h * 0.80),
               fill=(60, 78, 58), width=8)
    for i in range(6):
        d.ellipse((w * (0.0 + i * 0.18) - 60, h * 0.02,
                   w * (0.0 + i * 0.18) + 160, h * 0.16), fill=(30, 62, 48))
    for i in range(18):
        x = w * (0.05 + ((i * 31) % 92) / 100)
        y = h * (0.30 + ((i * 47) % 55) / 100)
        soft_glow(im, x, y, 18, (240, 240, 150), 120)
    d = ImageDraw.Draw(im)
    d.ellipse((-w * 0.2, h * 0.80, w * 1.2, h * 1.12), fill=(34, 62, 44))
    return im.convert("RGB")


def scene_house_cutaway(size):
    w, h = size
    im = gradient(size, [(0.0, (196, 226, 244)), (1.0, (232, 242, 248))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.polygon([(w * 0.06, h * 0.26), (w * 0.5, h * 0.06), (w * 0.94, h * 0.26)], fill=(200, 90, 80))
    d.rectangle((w * 0.08, h * 0.26, w * 0.92, h * 0.80), fill=(250, 244, 232))
    d.rectangle((w * 0.08, h * 0.26, w * 0.50, h * 0.52), fill=(226, 238, 248))
    d.rectangle((w * 0.50, h * 0.26, w * 0.92, h * 0.52), fill=(246, 236, 220))
    d.rectangle((w * 0.08, h * 0.52, w * 0.50, h * 0.80), fill=(240, 232, 214))
    d.rectangle((w * 0.50, h * 0.52, w * 0.92, h * 0.80), fill=(230, 240, 236))
    d.rectangle((w * 0.14, h * 0.58, w * 0.30, h * 0.66), fill=(190, 150, 110))
    d.rectangle((w * 0.58, h * 0.34, w * 0.72, h * 0.44), fill=(180, 200, 220))
    d.rectangle((w * 0.62, h * 0.60, w * 0.78, h * 0.66), fill=(200, 170, 130))
    d.rounded_rectangle((w * 0.74, h * 0.72, w * 0.82, h * 0.76), radius=8, fill=(80, 90, 100))
    for r in (30, 52, 74):
        d.arc((w * 0.78 - r, h * 0.74 - r, w * 0.78 + r, h * 0.74 + r),
              200, 340, fill=(90, 190, 230), width=5)
    return im.convert("RGB")


def scene_playground_clock(size):
    w, h = size
    im = gradient(size, [(0.0, (150, 206, 244)), (0.5, (198, 230, 250)),
                         (1.0, (240, 248, 252))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    flat_cloud(d, w * 0.18, h * 0.12, 130)
    flat_cloud(d, w * 0.78, h * 0.16, 110)
    cx, cy, r = w * 0.50, h * 0.30, w * 0.26
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(250, 250, 246))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(90, 100, 110), width=14)
    for i in range(12):
        a = math.radians(i * 30)
        d.line((cx + math.cos(a) * r * 0.82, cy + math.sin(a) * r * 0.82,
                cx + math.cos(a) * r * 0.92, cy + math.sin(a) * r * 0.92),
               fill=(70, 80, 90), width=8)
    d.line((cx, cy, cx + math.cos(math.radians(-60)) * r * 0.60,
            cy + math.sin(math.radians(-60)) * r * 0.60), fill=(60, 70, 80), width=14)
    d.line((cx, cy, cx + math.cos(math.radians(20)) * r * 0.78,
            cy + math.sin(math.radians(20)) * r * 0.78), fill=(220, 90, 80), width=10)
    d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=(60, 70, 80))
    d.ellipse((-w * 0.2, h * 0.62, w * 1.2, h * 1.05), fill=(240, 214, 160))
    d.line((w * 0.10, h * 0.52, w * 0.30, h * 0.52), fill=(120, 130, 140), width=12)
    d.line((w * 0.12, h * 0.52, w * 0.16, h * 0.70), fill=(150, 160, 170), width=6)
    d.line((w * 0.28, h * 0.52, w * 0.24, h * 0.70), fill=(150, 160, 170), width=6)
    d.rectangle((w * 0.14, h * 0.70, w * 0.26, h * 0.72), fill=(220, 110, 100))
    return im.convert("RGB")


SCENES = {
    "park": lambda size: scene_park(size),
    "park_evening": lambda size: scene_park(size, evening=True),
    "park_sunleft": lambda size: scene_park(size, sun_left=True),
    "sky": scene_sky,
    "space": scene_space,
    "prism": scene_prism,
    "atmosphere": scene_atmosphere,
    "sunset": scene_sunset,
    "bedroom": lambda size: scene_bedroom(size),
    "bedroom_night": lambda size: scene_bedroom(size, night=True),
    "kitchen": scene_kitchen,
    "classroom": scene_classroom,
    "market": scene_market,
    "city_top": scene_city_top,
    "city_street": scene_city_street,
    "beach": scene_beach,
    "underwater": scene_underwater,
    "body_inside": scene_body_inside,
    "phone_inside": scene_phone_inside,
    "data_center": scene_data_center,
    "neuron_city": scene_neuron_city,
    "airport": scene_airport,
    "bank": scene_bank,
    "money_print": scene_money_print,
    "stock_board": scene_stock_board,
    "lake_ice": scene_lake_ice,
    "rain_cloud": scene_rain_cloud,
    "galaxy": scene_galaxy,
    "garden": scene_garden,
    "dark_forest": scene_dark_forest,
    "house_cutaway": scene_house_cutaway,
    "playground_clock": scene_playground_clock,
}


def build_scene(name: str, size: tuple[int, int]) -> Image.Image:
    if name not in SCENES:
        raise ValueError(f"unknown cartoon scene: {name}")
    return SCENES[name](size)


# ---------------------------------------------------------- parallax fx layers
_FX_FAMILY = {
    "sky": "day", "atmosphere": "day", "sunset": "day", "city_top": "day",
    "city_street": "day", "park": "day", "park_evening": "day", "park_sunleft": "day",
    "playground_clock": "day", "garden": "day", "beach": "day", "market": "day",
    "airport": "day", "rain_cloud": "rain", "lake_ice": "ice",
    "space": "night", "galaxy": "night", "bedroom_night": "night", "dark_forest": "night",
    "underwater": "water",
}

_FX_CACHE: dict[tuple, dict] = {}


def build_fx_layers(name: str, size: tuple[int, int] = (675, 1200)) -> dict:
    """Layer parallax terpisah dari background: `atm` (jauh) dan `fg` (depan).

    Setengah resolusi (675×1200 mewakili kanvas 1350×2400) supaya hemat memori
    di Termux; di-upscale saat komposit. Background tetap 1 gambar (midground),
    `atm` bergerak 0,45× dan `fg` 1,35× kecepatan kamera -> kedalaman nyata.
    """
    key = (name, size)
    if key in _FX_CACHE:
        return _FX_CACHE[key]

    fam = _FX_FAMILY.get(name, "interior")
    W2, H2 = size
    atm = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    da = ImageDraw.Draw(atm)
    if fam in ("day", "ice", "rain"):
        for i, (cx, cy, rw, rh, a) in enumerate((
                (0.18, 0.14, 0.34, 0.050, 58), (0.55, 0.09, 0.42, 0.058, 46),
                (0.82, 0.20, 0.30, 0.042, 52), (0.36, 0.27, 0.26, 0.034, 38))):
            x, y = cx * W2, cy * H2
            da.ellipse((x - rw * W2 / 2, y - rh * H2 / 2,
                        x + rw * W2 / 2, y + rh * H2 / 2), fill=(255, 255, 255, a))
        atm = atm.filter(ImageFilter.GaussianBlur(7))
    elif fam == "night":
        for i in range(46):
            x = ((i * 137) % 100) / 100 * W2
            y = ((i * 271) % 100) / 100 * H2 * 0.7
            r = 1.2 + (i % 3) * 0.8
            da.ellipse((x - r, y - r, x + r, y + r), fill=(255, 252, 230, 150))
    elif fam == "water":
        for i in range(18):
            x = ((i * 173) % 100) / 100 * W2
            y = ((i * 97) % 100) / 100 * H2
            da.ellipse((x - 3, y - 3, x + 3, y + 3), outline=(255, 255, 255, 70), width=2)
        atm = atm.filter(ImageFilter.GaussianBlur(3))
    else:  # interior: berkas cahaya lembut dari atas
        da.polygon([(W2 * 0.18, 0), (W2 * 0.46, 0), (W2 * 0.62, H2), (W2 * 0.30, H2)],
                   fill=(255, 244, 220, 18))
        atm = atm.filter(ImageFilter.GaussianBlur(24))

    fg = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    df = ImageDraw.Draw(fg)
    for i, (cx, cy, rw, rh, a) in enumerate((
            (-0.05, 0.04, 0.26, 0.09, 92), (1.03, 0.08, 0.22, 0.08, 78),
            (-0.03, 0.97, 0.28, 0.10, 96), (1.04, 0.94, 0.24, 0.09, 84))):
        x, y = cx * W2, cy * H2
        df.ellipse((x - rw * W2 / 2, y - rh * H2 / 2,
                    x + rw * W2 / 2, y + rh * H2 / 2), fill=(14, 18, 16, a))
    fg = fg.filter(ImageFilter.GaussianBlur(30))

    out = {"atm": atm, "fg": fg}
    _FX_CACHE[key] = out
    return out
