#!/usr/bin/env python3
"""Build BOCA-D02 animatic v1 (previz, not final production).

Outputs 1080x1920 / 30fps / 45s MP4 with burned-in dual-layer captions,
VO from edge-tts, a poster, SRT, contact sheet, and a review README.

This is an animatic: simple backgrounds + Boca sprites + motion accents.
It is intentionally not the final Stickman Kino/Remotion render.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path("/data/data/com.termux/files/home/projects/boca-character")
sys.path.insert(0, str(ROOT))
from make_boca import character, render_svg, svg_doc  # noqa: E402

W, H = 1080, 1920
FPS = 30
TOTAL = 45.0
TOTAL_FRAMES = int(round(TOTAL * FPS))

OUT = Path("/sdcard/Download/Boca/animatic-d02")
TMP = Path("/data/data/com.termux/files/usr/tmp/opencode/boca-d02-build")
EDGE = Path("/data/data/com.termux/files/home/projects/MoneyPrinterTurbo/.venv/bin/edge-tts")
FONT = "/system/fonts/Roboto-Regular.ttf"

CREAM = (246, 241, 231)
INK = (35, 24, 21)
RED = (215, 38, 61)
TEAL = (31, 111, 120)
YELLOW = (244, 185, 66)
WHITE = (255, 255, 255)

# Timings are tuned to the measured VO durations (total VO ~35.95s).
SHOTS = [
    dict(
        n=1, start=0.0, end=3.4, bg="park", sprite="shock",
        size=1100, top=120, x=540, phase=0.0, bob=6,
        vo="Adek, siapa yang ngecat langit jadi biru?",
        baby="Siapa yang ngecat langit?",
        adult="Kenapa langit tampak biru?",
    ),
    dict(
        n=2, start=3.4, end=8.4, bg="space", sprite="focus",
        size=850, top=330, x=540, phase=0.8, bob=5,
        vo="Cahaya matahari itu sebenarnya campuran banyak warna.",
        baby="Matahari kirim banyak warna.",
        adult="Cahaya Matahari terdiri dari banyak warna.",
    ),
    dict(
        n=3, start=8.4, end=14.9, bg="prism", sprite="focus",
        size=820, top=360, x=300, phase=1.6, bob=5,
        vo="Kalau lewat prisma, warnanya pisah: merah, kuning, hijau, biru.",
        baby="Merah, kuning, hijau, biru!",
        adult="Prisma memisahkan spektrum cahaya.",
    ),
    dict(
        n=4, start=14.9, end=22.2, bg="atmosphere", sprite="focus",
        size=850, top=330, x=300, phase=2.4, bob=5,
        vo="Di langit, udara kecil-kecil main lempar warna biru ke mana-mana.",
        baby="Udara lempar warna biru.",
        adult="Molekul udara menghamburkan biru lebih kuat.",
    ),
    dict(
        n=5, start=22.2, end=29.5, bg="sky", sprite="happy",
        size=950, top=260, x=540, phase=3.2, bob=6,
        vo="Karena biru paling banyak dilempar, mata kita lihat langit biru.",
        baby="Jadi langit biru!",
        adult="Cahaya biru sampai ke mata dari segala arah.",
    ),
    dict(
        n=6, start=29.5, end=36.8, bg="sunset", sprite="confused",
        size=850, top=330, x=540, phase=4.0, bob=5,
        vo="Tapi sore, cahayanya jalan lebih jauh. Biru habis dilempar, tinggal merah.",
        baby="Sore, biru habis. Tinggal merah.",
        adult="Saat sunset, biru tersebar habis; merah/oranye tersisa.",
    ),
    dict(
        n=7, start=36.8, end=41.65, bg="sky", sprite="happy",
        size=1150, top=100, x=540, phase=4.8, bob=9,
        vo="Jadi bukan cat, Adek. Udara yang main warna!",
        baby="Bukan cat, tapi udara!",
        adult="Langit biru karena hamburan cahaya, bukan cat.",
        sunglasses=True,
    ),
    dict(
        n=8, start=41.65, end=45.0, bg="sky", sprite="happy-wave",
        size=900, top=300, x=540, phase=5.6, bob=7,
        vo="Coba lihat langit sore ini, warnanya apa?",
        baby="Langit sore ini warna apa?",
        adult="Tulis di komentar.",
        cta=True,
    ),
]

SPRITE_SPECS = {
    "neutral": ("neutral", "stand"),
    "shock": ("shock", "stand"),
    "happy": ("happy", "stand"),
    "confused": ("confused", "stand"),
    "focus": ("focus", "stand"),
    "happy-wave": ("happy", "wave"),
    "confused-think": ("confused", "think"),
    "focus-read": ("focus", "read"),
}


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kwargs)


def gradient(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for i in range(3):
        arr[:, :, i] = np.linspace(top[i], bottom[i], H).astype(np.uint8)[:, None]
    return Image.fromarray(arr, "RGB")


def gradient_multi(stops: list[tuple[float, tuple[int, int, int]]]) -> Image.Image:
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    ys = np.linspace(0.0, 1.0, H)
    for i in range(3):
        vals = np.zeros(H, dtype=np.float64)
        for j in range(len(stops) - 1):
            p0, c0 = stops[j]
            p1, c1 = stops[j + 1]
            m = (ys >= p0) & (ys <= p1)
            if not m.any():
                continue
            local = (ys[m] - p0) / max(p1 - p0, 1e-9)
            vals[m] = c0[i] + (c1[i] - c0[i]) * local
        vals[ys < stops[0][0]] = stops[0][1][i]
        vals[ys > stops[-1][0]] = stops[-1][1][i]
        arr[:, :, i] = vals.astype(np.uint8)[:, None]
    return Image.fromarray(arr, "RGB")


def layer() -> Image.Image:
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def vignette() -> Image.Image:
    y, x = np.ogrid[:H, :W]
    cx, cy = W / 2, H / 2
    r = np.sqrt(((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2)
    a = np.clip((r - 0.55) * 95, 0, 95).astype(np.uint8)
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[:, :, 3] = a
    return Image.fromarray(arr, "RGBA")


VIGNETTE = vignette()


def finish_bg(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    im.alpha_composite(VIGNETTE)
    return im.convert("RGB")


def draw_sun(im: Image.Image, x: int, y: int, r: int, color: tuple[int, int, int]) -> None:
    glow = layer()
    gd = ImageDraw.Draw(glow)
    for i in range(6, 0, -1):
        rr = r + i * 26
        gd.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(*color, 16))
    glow = glow.filter(ImageFilter.GaussianBlur(30))
    im.alpha_composite(glow)
    d = ImageDraw.Draw(im)
    d.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=(255, 255, 255, 230), width=6)


def draw_cloud(d: ImageDraw.ImageDraw, x: int, y: int, s: float, alpha: int = 210) -> None:
    color = (255, 255, 255, alpha)
    for dx, dy, rx, ry in [
        (-1.15, 0.05, 0.70, 0.42),
        (-0.35, -0.30, 0.82, 0.55),
        (0.55, -0.12, 0.70, 0.48),
        (1.15, 0.08, 0.55, 0.36),
    ]:
        d.ellipse(
            (x + dx * s - rx * s, y + dy * s - ry * s,
             x + dx * s + rx * s, y + dy * s + ry * s),
            fill=color,
        )


def draw_stars(d: ImageDraw.ImageDraw, count: int, seed: int) -> None:
    rng = np.random.default_rng(seed)
    for _ in range(count):
        x = int(rng.integers(0, W))
        y = int(rng.integers(0, int(H * 0.78)))
        r = int(rng.integers(1, 4))
        a = int(rng.integers(120, 255))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, a))


def draw_earth(d: ImageDraw.ImageDraw, x: int, y: int, r: int) -> None:
    d.ellipse((x - r, y - r, x + r, y + r), fill=(38, 105, 180, 255), outline=(190, 235, 255, 255), width=6)
    # stylized land
    d.ellipse((x - r * 0.55, y - r * 0.55, x + r * 0.10, y + r * 0.15), fill=(80, 170, 105, 255))
    d.ellipse((x - r * 0.10, y + r * 0.05, x + r * 0.55, y + r * 0.60), fill=(70, 155, 95, 255))
    d.ellipse((x - r * 0.25, y - r * 0.85, x + r * 0.45, y - r * 0.45), fill=(235, 250, 255, 180))
    d.ellipse((x - r * 0.75, y + r * 0.15, x - r * 0.10, y + r * 0.35), fill=(235, 250, 255, 160))


def draw_prism(d: ImageDraw.ImageDraw, cx: int, cy: int, s: int) -> None:
    # incoming white beam
    d.line((0, cy - 120, cx - s * 0.55, cy - 20), fill=(255, 255, 255, 210), width=34)
    # glass triangle
    tri = [(cx, cy - s), (cx - s * 0.92, cy + s * 0.72), (cx + s * 0.92, cy + s * 0.72)]
    d.polygon(tri, fill=(170, 225, 255, 95), outline=(255, 255, 255, 235))
    d.line((cx, cy - s, cx - s * 0.55, cy + s * 0.42), fill=(255, 255, 255, 130), width=5)
    # rainbow fan
    colors = [
        (255, 70, 70), (255, 145, 55), (255, 220, 70),
        (85, 210, 110), (65, 160, 255), (145, 100, 255),
    ]
    for i, c in enumerate(colors):
        ang = math.radians(-36 + i * 14)
        x2 = cx + math.cos(ang) * 760
        y2 = cy + 20 + math.sin(ang) * 540
        d.line((cx + s * 0.12, cy + 15, x2, y2), fill=(*c, 55), width=34)
        d.line((cx + s * 0.12, cy + 15, x2, y2), fill=(*c, 235), width=15)


def draw_particles(d: ImageDraw.ImageDraw, seed: int) -> None:
    rng = np.random.default_rng(seed)
    for _ in range(34):
        x = int(rng.integers(80, W - 80))
        y = int(rng.integers(140, 1250))
        r = int(rng.integers(5, 16))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(225, 245, 255, 150), outline=(255, 255, 255, 210), width=2)
        if rng.random() < 0.55:
            dx = int(rng.integers(-60, 60))
            dy = int(rng.integers(-40, 40))
            d.line((x, y, x + dx, y + dy), fill=(120, 210, 255, 170), width=3)
            d.ellipse((x + dx - 4, y + dy - 4, x + dx + 4, y + dy + 4), fill=(120, 210, 255, 200))


def draw_question_bubble(d: ImageDraw.ImageDraw) -> None:
    d.rounded_rectangle((760, 180, 1000, 380), 40, fill=(255, 255, 255, 235), outline=INK, width=6)
    d.polygon([(820, 370), (790, 440), (870, 382)], fill=(255, 255, 255, 235), outline=INK)
    f = ImageFont.truetype(FONT, 120)
    d.text((880, 280), "?", font=f, fill=RED, anchor="mm")


def make_bg(name: str) -> Image.Image:
    if name == "park":
        im = gradient((75, 168, 235), (218, 244, 255)).convert("RGBA")
        draw_sun(im, 850, 280, 105, (255, 210, 90))
        d = ImageDraw.Draw(im)
        draw_cloud(d, 210, 320, 90)
        draw_cloud(d, 760, 540, 70, 190)
        d.rectangle((0, 1540, W, H), fill=(105, 190, 105, 255))
        d.rectangle((0, 1540, W, 1585), fill=(78, 160, 82, 255))
        return finish_bg(im)

    if name == "space":
        im = gradient((5, 14, 34), (12, 42, 78)).convert("RGBA")
        d = ImageDraw.Draw(im)
        draw_stars(d, 150, 7)
        draw_sun(im, 150, 350, 95, (255, 220, 120))
        d = ImageDraw.Draw(im)
        # beam from sun to Earth
        d.polygon([(235, 330), (760, 700), (790, 900), (220, 390)], fill=(255, 245, 190, 28))
        d.polygon([(240, 350), (700, 720), (720, 840), (225, 385)], fill=(255, 250, 220, 22))
        draw_earth(d, 850, 900, 175)
        d.arc((620, 690, 1080, 1120), 200, 340, fill=(140, 210, 255, 100), width=4)
        return finish_bg(im)

    if name == "prism":
        im = gradient((8, 14, 28), (26, 36, 54)).convert("RGBA")
        d = ImageDraw.Draw(im)
        draw_stars(d, 55, 11)
        draw_prism(d, 760, 850, 210)
        return finish_bg(im)

    if name == "atmosphere":
        im = gradient((40, 110, 190), (170, 220, 255)).convert("RGBA")
        d = ImageDraw.Draw(im)
        # curved horizon
        d.ellipse((-420, 1420, W + 420, 2300), fill=(28, 78, 135, 255))
        d.arc((-420, 1420, W + 420, 2300), 200, 340, fill=(190, 235, 255, 180), width=8)
        draw_particles(d, 13)
        # big scattering wave
        for i in range(4):
            y = 1020 + i * 70
            d.arc((80 - i * 30, y - 120, W - 80 + i * 30, y + 120), 200, 340, fill=(210, 240, 255, 70 - i * 12), width=10)
        return finish_bg(im)

    if name == "sky":
        im = gradient((55, 150, 225), (210, 242, 255)).convert("RGBA")
        draw_sun(im, 840, 300, 95, (255, 215, 95))
        d = ImageDraw.Draw(im)
        draw_cloud(d, 200, 360, 85)
        draw_cloud(d, 760, 610, 65, 190)
        draw_cloud(d, 360, 900, 55, 150)
        return finish_bg(im)

    if name == "sunset":
        im = gradient_multi([
            (0.0, (38, 24, 74)),
            (0.42, (126, 55, 105)),
            (0.68, (245, 100, 80)),
            (0.82, (255, 178, 92)),
            (1.0, (255, 222, 150)),
        ]).convert("RGBA")
        draw_sun(im, 540, 1370, 130, (255, 190, 80))
        d = ImageDraw.Draw(im)
        draw_cloud(d, 240, 470, 80, 150)
        draw_cloud(d, 820, 700, 65, 130)
        d.rectangle((0, 1500, W, H), fill=(58, 36, 52, 255))
        d.rectangle((0, 1500, W, 1530), fill=(255, 170, 90, 160))
        # long light path
        d.polygon([(500, 1500), (580, 1500), (760, H), (320, H)], fill=(255, 210, 120, 30))
        return finish_bg(im)

    raise ValueError(name)


def wrap_text(d: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        test = (cur + " " + word).strip()
        if d.textlength(test, font=font) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def make_overlay(shot: dict) -> Image.Image:
    ov = layer()
    d = ImageDraw.Draw(ov)

    baby_font = ImageFont.truetype(FONT, 56)
    adult_font = ImageFont.truetype(FONT, 30)
    baby_lines = wrap_text(d, shot["baby"], baby_font, 900)
    adult_lines = wrap_text(d, shot["adult"], adult_font, 900)
    baby_h = len(baby_lines) * 64
    adult_h = len(adult_lines) * 38
    panel_top = 1280
    panel_bottom = 1305 + baby_h + 16 + adult_h + 20
    panel_bottom = min(panel_bottom, 1600)

    d.rounded_rectangle((50, panel_top, 1030, panel_bottom), 24, fill=(0, 0, 0, 172))
    d.rounded_rectangle((80, panel_top, 1000, panel_top + 6), 3, fill=(*RED, 255))

    y = 1305
    for line in baby_lines:
        d.text((540, y), line, font=baby_font, fill=(255, 255, 255, 255),
               anchor="ma", stroke_width=3, stroke_fill=(0, 0, 0, 230))
        y += 64
    y += 16
    for line in adult_lines:
        d.text((540, y), line, font=adult_font, fill=(255, 224, 130, 255),
               anchor="ma", stroke_width=1, stroke_fill=(0, 0, 0, 230))
        y += 38

    # review labels (animatic only)
    label_font = ImageFont.truetype(FONT, 22)
    brand_font = ImageFont.truetype(FONT, 20)
    d.rounded_rectangle((30, 30, 430, 82), 12, fill=(0, 0, 0, 120))
    d.text((48, 42), f"SHOT {shot['n']}/8  ·  {shot['start']:.2f}–{shot['end']:.2f}s",
           font=label_font, fill=(255, 255, 255, 230))
    d.text((W - 36, 42), "BOCA · D02 ANIMATIC v1", font=brand_font,
           fill=(255, 255, 255, 185), anchor="ra")

    if shot.get("cta"):
        d.rounded_rectangle((300, 1160, 780, 1230), 24, fill=(255, 255, 255, 220), outline=INK, width=4)
        cta_font = ImageFont.truetype(FONT, 34)
        d.text((540, 1195), "KOMENTAR DI BAWAH", font=cta_font, fill=INK, anchor="mm")

    return ov


def make_sprites() -> dict[str, Image.Image]:
    sprite_dir = TMP / "sprites"
    sprite_dir.mkdir(parents=True, exist_ok=True)
    sprites: dict[str, Image.Image] = {}
    for name, (expr, pose) in SPRITE_SPECS.items():
        svg = svg_doc(1080, 1920, character(expr, pose, 540, 620, 1.0, shadow=False), None)
        svg_path = sprite_dir / f"{name}.svg"
        png_path = sprite_dir / f"{name}.png"
        svg_path.write_text(svg, encoding="utf-8")
        render_svg(svg_path, png_path, 1080, 1920, transparent=True)
        im = Image.open(png_path).convert("RGBA")
        # Fixed crop centered on the character, not on the alpha bbox.
        im = im.crop((140, 348, 940, 1548))
        sprites[name] = im
        im.save(sprite_dir / f"{name}-crop.png")
    return sprites


def make_shadow(x: int, top: int, size: int, width: int) -> Image.Image:
    sh = layer()
    d = ImageDraw.Draw(sh)
    cy = top + size - 35
    d.ellipse((x - width * 0.44, cy - 35, x + width * 0.44, cy + 35), fill=(0, 0, 0, 90))
    return sh.filter(ImageFilter.GaussianBlur(18))


def draw_sunglasses(im: Image.Image, x: int, top: int, size: int) -> None:
    d = ImageDraw.Draw(im)
    eye_y = top + int(size * 0.26)
    eye_dx = int(size * 0.075)
    w = int(size * 0.155)
    h = int(size * 0.052)
    for sx in (-1, 1):
        cx = x + sx * eye_dx
        d.rounded_rectangle((cx - w // 2, eye_y - h // 2, cx + w // 2, eye_y + h // 2),
                            12, fill=(20, 20, 25), outline=(5, 5, 8), width=4)
        d.line((cx - w // 3, eye_y - h // 5, cx + w // 4, eye_y - h // 5),
               fill=(255, 255, 255), width=4)
        # arm to the side
        d.line((cx + sx * w // 2, eye_y, x + sx * int(size * 0.18), eye_y - 8),
               fill=(20, 20, 25), width=6)
    d.line((x - eye_dx + w // 2, eye_y, x + eye_dx - w // 2, eye_y), fill=(20, 20, 25), width=6)


def make_audio() -> Path:
    vo_dir = TMP / "vo"
    vo_dir.mkdir(parents=True, exist_ok=True)
    seg_paths: list[Path] = []
    for shot in SHOTS:
        mp3 = vo_dir / f"vo-{shot['n']:02d}.mp3"
        last_err = ""
        for attempt in range(3):
            p = subprocess.run(
                [str(EDGE), "--voice", "id-ID-ArdiNeural", "--rate=+4%", "--pitch=-2Hz",
                 "--text", shot["vo"], "--write-media", str(mp3)],
                capture_output=True, text=True,
            )
            if p.returncode == 0 and mp3.exists() and mp3.stat().st_size > 1000:
                break
            last_err = (p.stderr or p.stdout or "").strip()
            time.sleep(2)
        else:
            raise RuntimeError(f"edge-tts failed for shot {shot['n']}: {last_err}")

        dur = shot["end"] - shot["start"]
        seg = vo_dir / f"seg-{shot['n']:02d}.wav"
        run([
            "ffmpeg", "-y", "-i", str(mp3),
            "-af", f"apad=whole_dur={dur:.3f}",
            "-t", f"{dur:.3f}", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(seg),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        seg_paths.append(seg)

    concat = vo_dir / "concat.txt"
    concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in seg_paths), encoding="utf-8")
    raw = vo_dir / "voiceover-raw.wav"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(raw)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    norm = vo_dir / "voiceover.wav"
    run([
        "ffmpeg", "-y", "-i", str(raw),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-t", f"{TOTAL:.3f}", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
        str(norm),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return norm


def render_video(audio: Path, sprites: dict[str, Image.Image]) -> Path:
    bg_cache = {s["n"]: make_bg(s["bg"]) for s in SHOTS}
    ov_cache = {s["n"]: make_overlay(s) for s in SHOTS}

    sprite_cache: dict[int, Image.Image] = {}
    shadow_cache: dict[int, Image.Image] = {}
    for s in SHOTS:
        target_h = s["size"]
        target_w = int(round(800 * target_h / 1200))
        sprite_cache[s["n"]] = sprites[s["sprite"]].resize((target_w, target_h), Image.Resampling.LANCZOS)
        shadow_cache[s["n"]] = make_shadow(s["x"], s["top"], target_h, target_w)

    out = OUT / "boca-d02-animatic-v1.mp4"
    log = TMP / "ffmpeg-render.log"
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(audio),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
        str(out),
    ]
    with open(log, "wb") as err:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=err)
        assert proc.stdin is not None
        previews: dict[int, Path] = {}
        for f in range(TOTAL_FRAMES):
            t = f / FPS
            shot = next((s for s in SHOTS if s["start"] <= t < s["end"]), SHOTS[-1])
            n = shot["n"]
            local = t - shot["start"]
            base = bg_cache[n].copy()
            base.paste(shadow_cache[n], (0, 0), shadow_cache[n])
            target_w = sprite_cache[n].width
            bob = math.sin(2 * math.pi * 0.8 * local + shot["phase"]) * shot["bob"]
            dx = math.sin(2 * math.pi * 0.5 * local + shot["phase"]) * 3
            pos = (shot["x"] - target_w // 2 + int(dx), shot["top"] + int(bob))
            base.paste(sprite_cache[n], pos, sprite_cache[n])
            if shot.get("sunglasses"):
                draw_sunglasses(base, shot["x"] + int(dx), shot["top"] + int(bob), shot["size"])
            base.paste(ov_cache[n], (0, 0), ov_cache[n])
            d = ImageDraw.Draw(base)
            d.rectangle((0, H - 16, W, H), fill=(20, 20, 30))
            d.rectangle((0, H - 16, int(W * t / TOTAL), H), fill=RED)

            mid = int(round(((shot["start"] + shot["end"]) / 2) * FPS))
            if f == mid:
                pp = TMP / f"preview-{n:02d}.png"
                base.save(pp)
                previews[n] = pp
            proc.stdin.write(base.tobytes())
        proc.stdin.close()
        rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg render failed (see {log})")
    return out


def make_poster(sprites: dict[str, Image.Image]) -> Path:
    shot = SHOTS[0]
    base = make_bg("sky").copy()
    poster_top = 430
    target_h = 950
    target_w = int(round(800 * target_h / 1200))
    sprite = sprites[shot["sprite"]].resize((target_w, target_h), Image.Resampling.LANCZOS)
    shadow = make_shadow(shot["x"], poster_top, target_h, target_w)
    base.paste(shadow, (0, 0), shadow)
    base.paste(sprite, (shot["x"] - target_w // 2, poster_top), sprite)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((60, 80, 1020, 380), 30, fill=(246, 241, 231), outline=INK, width=6)
    d.rectangle((90, 110, 990, 120), fill=RED)
    f1 = ImageFont.truetype(FONT, 92)
    f2 = ImageFont.truetype(FONT, 46)
    f3 = ImageFont.truetype(FONT, 24)
    d.text((540, 155), "BOCA", font=f1, fill=INK, anchor="ma")
    d.text((540, 265), "Kenapa langit biru?", font=f2, fill=INK, anchor="ma")
    d.text((540, 330), "ANIMATIC v1 · 45 detik", font=f3, fill=(107, 91, 75), anchor="ma")
    out = OUT / "boca-d02-animatic-v1-poster.png"
    base.save(out)
    return out


def make_contact_sheet() -> Path:
    sheet = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT, 28)
    for i, shot in enumerate(SHOTS):
        p = TMP / f"preview-{shot['n']:02d}.png"
        if not p.exists():
            continue
        im = Image.open(p).convert("RGB").resize((270, 480), Image.Resampling.LANCZOS)
        x = 20 + (i % 4) * 260
        y = 80 + (i // 4) * 760
        sheet.paste(im, (x, y))
        d.text((x, y + 490), f"SHOT {shot['n']}", font=f, fill=INK)
        d.text((x, y + 525), f"{shot['start']:.1f}–{shot['end']:.1f}s", font=f, fill=(107, 91, 75))
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
        lines.append(str(i))
        lines.append(f"{fmt_srt(shot['start'])} --> {fmt_srt(shot['end'])}")
        lines.append(shot["baby"])
        lines.append(shot["adult"])
        lines.append("")
    out = OUT / "boca-d02-animatic-v1.srt"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def write_readme(video: Path, audio: Path) -> Path:
    rows = "\n".join(
        f"| {s['n']} | {s['start']:.2f}–{s['end']:.2f}s | {s['baby']} | {s['adult']} |"
        for s in SHOTS
    )
    text = f"""# BOCA-D02 — Animatic v1

**Status:** previz / animatic. Bukan render final.  
**File:** `{video.name}`  
**Durasi:** {TOTAL:.1f}s · 1080×1920 · 30fps  
**Audio:** `{audio.name}` — edge-tts `id-ID-ArdiNeural`, rate +4%, pitch -2Hz, loudnorm -16 LUFS.

## Shot & caption

| Shot | Waktu | Caption bayi | Caption dewasa |
|---|---|---|---|
{rows}

## File

- `{video.name}` — animatic MP4
- `boca-d02-animatic-v1.srt` — caption SRT
- `boca-d02-animatic-v1-poster.png` — poster
- `contact-sheet.png` — 8-shot contact sheet

## Catatan review

- Animatic ini menguji timing VO, caption dual-layer, ukuran Boca, dan alur 8 shot.
- Background masih stilasi sederhana; belum ada animasi rig penuh.
- Shot label di kiri atas dan progress bar adalah penanda review, bukan final.
- Sumber fakta: NASA Science + NOAA NESDIS (lihat Content Bible v2.2).
- Kalau VO terasa cepat/lambat, revisi di script sebelum render final.

## Next

1. Review animatic.
2. Kunci timing + caption.
3. Baru masuk produksi rig/Remotion untuk versi final.
"""
    out = OUT / "README.md"
    out.write_text(text, encoding="utf-8")
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)

    print("1/5 sprites")
    sprites = make_sprites()
    print("2/5 audio")
    audio = make_audio()
    print("3/5 video")
    video = render_video(audio, sprites)
    print("4/5 poster + contact sheet")
    make_poster(sprites)
    make_contact_sheet()
    print("5/5 srt + readme")
    write_srt()
    write_readme(video, audio)

    # copy clean audio for review
    shutil.copy2(audio, OUT / "voiceover.wav")
    print("done:", video)
    print("size:", video.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
