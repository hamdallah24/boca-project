import math
import os
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920


# ==============================================================================
# 1. EASING & BOUNDED COMPOSITING
# ==============================================================================

def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def ease_out_cubic(p: float) -> float:
    p = clamp01(p)
    return 1.0 - (1.0 - p) ** 3


def ease_out_expo(p: float) -> float:
    p = clamp01(p)
    return 1.0 if p >= 1.0 else 1.0 - (2.0 ** (-10.0 * p))


def spring_pop(p: float, overshoot: float = 1.70158) -> float:
    """Overshoot cubic back-out: 0 -> ~1.10 -> 1.0."""
    p = clamp01(p)
    t = p - 1.0
    return 1.0 + t * t * ((overshoot + 1.0) * t + overshoot)


def load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = [
        "/system/fonts/Roboto-Bold.ttf" if bold else "/system/fonts/Roboto-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def safe_alpha_composite(bg: Image.Image, fg: Image.Image, x: int, y: int) -> None:
    """Fast bounded alpha composite supporting negative/out-of-frame coordinates."""
    bw, bh = bg.size
    fw, fh = fg.size
    if x >= bw or y >= bh or x + fw <= 0 or y + fh <= 0:
        return
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(fw, bw - x), min(fh, bh - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    crop = fg if (sx0 == 0 and sy0 == 0 and sx1 == fw and sy1 == fh) else fg.crop((sx0, sy0, sx1, sy1))
    bg.alpha_composite(crop, dest=(max(0, x), max(0, y)))


# ==============================================================================
# 2. TRUE PARALLAX CAMERA + DRIFTING CLOUDS + CAMERA SHAKE
# ==============================================================================

def camera_shake(t: float, impact_times: List[float], duration: float = 0.28, amp: float = 14.0) -> Tuple[int, int]:
    sx, sy = 0.0, 0.0
    for t0 in impact_times:
        dt = t - t0
        if 0.0 <= dt < duration:
            decay = (1.0 - dt / duration) ** 2
            sx += math.sin(dt * 85.0) * amp * decay
            sy += math.cos(dt * 110.0) * amp * 0.6 * decay
    return int(round(sx)), int(round(sy))


def compose_parallax_scene(
    layers: Dict[str, Optional[Image.Image]],
    cam: dict,
    shot_prog: float,
    t_global: float,
    impact_times: Optional[List[float]] = None,
) -> Image.Image:
    """Render true multi-layer parallax camera with eased pan/zoom and moving clouds."""
    p = ease_out_cubic(shot_prog)
    fx0, fx1 = cam.get("fx", [0.5, 0.5])
    fy0, fy1 = cam.get("fy", [0.5, 0.5])
    z0, z1 = cam.get("z", [1.0, 1.0])

    fx = fx0 + (fx1 - fx0) * p
    fy = fy0 + (fy1 - fy0) * p
    z = max(1.0, z0 + (z1 - z0) * p)

    # Subtle breathing + optional shake
    bx = int(round(math.sin(t_global * 1.4) * 3.0))
    by = int(round(math.cos(t_global * 1.1) * 2.5))
    sx, sy = camera_shake(t_global, impact_times or [])

    base_canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    parallax_weights = [("sky", 0.15), ("clouds", 0.30), ("midground", 0.60), ("ground", 1.00)]

    for name, weight in parallax_weights:
        layer = layers.get(name)
        if layer is None:
            continue
        lw, lh = layer.size
        cw, ch = int(W / z), int(H / z)

        # Interpolate pan centered around 0.5 weighted by parallax depth
        eff_fx = 0.5 + (fx - 0.5) * weight
        eff_fy = 0.5 + (fy - 0.5) * weight

        ox = int(eff_fx * (lw - cw)) + int(bx * weight) + sx
        oy = int(eff_fy * (lh - ch)) + int(by * weight) + sy
        ox = max(0, min(lw - cw, ox))
        oy = max(0, min(lh - ch, oy))

        if name == "clouds":
            # Seamless horizontal drift wrap-around for clouds
            drift = int((t_global * 26.0) % lw)
            shifted = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
            shifted.paste(layer, (-drift, 0))
            if drift > 0:
                shifted.paste(layer, (lw - drift, 0))
            cropped = shifted.crop((ox, oy, ox + cw, oy + ch))
        else:
            cropped = layer.crop((ox, oy, ox + cw, oy + ch))

        if (cw, ch) != (W, H):
            cropped = cropped.resize((W, H), Image.Resampling.BILINEAR)

        if name == "sky":
            base_canvas = cropped
        else:
            base_canvas.alpha_composite(cropped)

    return base_canvas


# ==============================================================================
# 3. ELASTIC SQUASH & STRETCH FOR CHARACTER STATE CHANGES
# ==============================================================================

def apply_squash_stretch(
    sprite: Image.Image,
    x_center: int,
    ground_y: int,
    t_local: float,
    state_change_times: List[float],
    tilt_deg: float = 0.0,
) -> Tuple[Image.Image, int, int]:
    """
    Applies a 220ms elastic bounce whenever pose/expr/arm changes, anchored to ground_y.
    Returns (transformed_sprite, top_left_x, top_left_y).
    """
    sx, sy = 1.0, 1.0
    for tc in state_change_times:
        dt = t_local - tc
        if 0.0 <= dt < 0.24:
            # Damped bounce: squash -> stretch -> settle
            phase = dt / 0.24
            wave = math.sin(phase * math.pi * 2.0) * (1.0 - phase)
            sy += 0.09 * wave
            sx -= 0.07 * wave

    sw, sh = sprite.size
    nw = max(8, int(round(sw * sx)))
    nh = max(8, int(round(sh * sy)))
    out = sprite if (nw, nh) == (sw, sh) else sprite.resize((nw, nh), Image.Resampling.BILINEAR)

    if abs(tilt_deg) > 0.2:
        out = out.rotate(tilt_deg, resample=Image.Resampling.BILINEAR, expand=True)
        nw, nh = out.size

    return out, int(x_center - nw // 2), int(ground_y - nh)


# ==============================================================================
# 4. SPOTLIGHT / DIMMING LAYER
# ==============================================================================

def apply_spotlight(
    canvas: Image.Image,
    focus_xy: Tuple[int, int],
    radius: int = 340,
    darkness_alpha: int = 165,
    fade_p: float = 1.0,
) -> None:
    """Dims scene around a focused character or prop with a crisp radial spotlight."""
    alpha = int(darkness_alpha * ease_out_cubic(fade_p))
    if alpha <= 2:
        return
    overlay = Image.new("RGBA", (W, H), (10, 15, 30, alpha))
    draw = ImageDraw.Draw(overlay)
    fx, fy = focus_xy
    # Soft stepped concentric cutout (fast without GaussianBlur)
    steps = [(1.25, int(alpha * 0.65)), (1.10, int(alpha * 0.30)), (1.00, 0)]
    for mult, step_a in steps:
        r = int(radius * mult)
        draw.ellipse((fx - r, fy - r, fx + r, fy + r), fill=(10, 15, 30, step_a))
    canvas.alpha_composite(overlay)


# ==============================================================================
# 5. DYNAMIC PROPS & INFOGRAPHIC CARDS (HAFZYNASH STYLE)
# ==============================================================================

def draw_prop_dynamic(
    canvas: Image.Image,
    prop_sprites: Dict[str, Image.Image],
    prop_spec: dict,
    t_shot: float,
    font_bold: ImageFont.FreeTypeFont,
) -> None:
    """Renders large outlined SVG prop with spring pop-in, float, and micro-animation."""
    t_in = prop_spec.get("t_in", 0.0)
    t_out = prop_spec.get("t_out", 999.0)
    if t_shot < t_in or t_shot > t_out:
        return

    dt_in = t_shot - t_in
    dt_out = t_out - t_shot
    if dt_in < 0.32:
        scale = max(0.05, spring_pop(dt_in / 0.32))
    elif dt_out < 0.20:
        scale = max(0.05, ease_out_expo(dt_out / 0.20))
    else:
        scale = 1.0

    name = prop_spec["id"]
    base = prop_sprites.get(name)
    if base is None:
        return

    target_h = int(prop_spec.get("h", 340) * scale)
    if target_h < 12:
        return

    spr = base.resize((target_h, target_h), Image.Resampling.BILINEAR).copy()
    draw = ImageDraw.Draw(spr)

    # Procedural sub-animations inside props
    if name == "clock_face":
        cx, cy = target_h // 2, target_h // 2
        ang_min = t_shot * 6.5  # rapid time-lapse spin
        ang_hr = t_shot * 0.8
        r_min = int(target_h * 0.28)
        r_hr = int(target_h * 0.19)
        w_line = max(3, target_h // 55)
        draw.line((cx, cy, cx + int(math.sin(ang_min) * r_min), cy - int(math.cos(ang_min) * r_min)), fill=(30, 41, 59, 255), width=w_line)
        draw.line((cx, cy, cx + int(math.sin(ang_hr) * r_hr), cy - int(math.cos(ang_hr) * r_hr)), fill=(239, 68, 68, 255), width=w_line + 1)
        draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(30, 41, 59, 255))

    elif name == "phone_scroll":
        # Animated scrolling feed bars inside screen
        sx0, sx1 = int(target_h * 0.32), int(target_h * 0.68)
        sy0, sy1 = int(target_h * 0.18), int(target_h * 0.80)
        offset = int((t_shot * 140) % 75)
        colors = [(59, 130, 246, 255), (244, 63, 94, 255), (16, 185, 129, 255), (245, 158, 11, 255)]
        for i in range(4):
            by0 = sy0 + i * 75 - offset
            by1 = by0 + 52
            if by1 > sy0 and by0 < sy1:
                draw.rounded_rectangle(
                    (sx0, max(sy0, by0), sx1, min(sy1, by1)),
                    radius=max(3, target_h // 60),
                    fill=colors[i % len(colors)],
                    outline=(30, 41, 59, 255),
                    width=max(2, target_h // 110),
                )

    # Idle hover
    bob_y = int(math.sin(t_shot * 3.2 + prop_spec.get("x", 0) * 0.01) * 9.0)
    px = int(prop_spec.get("x", W // 2) - target_h // 2)
    py = int(prop_spec.get("y", 720) - target_h // 2 + bob_y)
    safe_alpha_composite(canvas, spr, px, py)

    # Optional pill badge under prop
    badge = prop_spec.get("badge")
    if badge and scale > 0.7:
        d_canv = ImageDraw.Draw(canvas)
        bbox = d_canv.textbbox((0, 0), badge, font=font_bold)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        bx = int(prop_spec.get("x", W // 2))
        by = py + target_h + 8
        pad_x, pad_y = 22, 10
        d_canv.rounded_rectangle(
            (bx - tw // 2 - pad_x, by, bx + tw // 2 + pad_x, by + th + pad_y * 2),
            radius=24,
            fill=(17, 24, 39, 240),
            outline=(250, 204, 21, 255),
            width=4,
        )
        d_canv.text((bx - tw // 2, by + pad_y - 2), badge, font=font_bold, fill=(255, 255, 255, 255))


def draw_info_card(
    canvas: Image.Image,
    card_spec: dict,
    t_shot: float,
    font_title: ImageFont.FreeTypeFont,
    font_row: ImageFont.FreeTypeFont,
) -> None:
    """
    Renders a crisp @hafzynash-style centered infographic card with staggered rows.
    card_spec example:
    {
      "t_in": 0.4, "t_out": 4.2, "title": "KENAPA TERASA CEPAT?", "y": 310,
      "items": [
        {"label": "Scroll HP", "val": "2 JAM", "color": [239, 68, 68], "fill": 0.92},
        {"label": "Terasa",    "val": "10 MENIT", "color": [34, 197, 94], "fill": 0.15}
      ]
    }
    """
    t_in = card_spec.get("t_in", 0.0)
    t_out = card_spec.get("t_out", 999.0)
    if t_shot < t_in or t_shot > t_out:
        return

    dt_in = t_shot - t_in
    dt_out = t_out - t_shot
    if dt_in < 0.30:
        s = max(0.05, spring_pop(dt_in / 0.30))
    elif dt_out < 0.20:
        s = max(0.05, ease_out_expo(dt_out / 0.20))
    else:
        s = 1.0

    cw = 880
    items = card_spec.get("items", [])
    ch = 150 + len(items) * 125
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)

    # Drop shadow + main rounded white card
    d.rounded_rectangle((10, 14, cw - 2, ch - 2), radius=34, fill=(15, 23, 42, 95))
    d.rounded_rectangle((0, 0, cw - 12, ch - 14), radius=34, fill=(255, 255, 255, 252), outline=(30, 41, 59, 255), width=6)

    # Header bar
    d.rounded_rectangle((0, 0, cw - 12, 96), radius=34, fill=(30, 41, 59, 255))
    d.rectangle((0, 56, cw - 12, 96), fill=(30, 41, 59, 255))
    title = card_spec.get("title", "")
    tb = d.textbbox((0, 0), title, font=font_title)
    d.text(((cw - 12 - (tb[2] - tb[0])) // 2, 26), title, font=font_title, fill=(250, 204, 21, 255))

    # Staggered item bars
    for idx, item in enumerate(items):
        row_dt = dt_in - (0.12 + idx * 0.14)
        if row_dt <= 0:
            continue
        rp = ease_out_cubic(min(1.0, row_dt / 0.35))
        ry = 132 + idx * 120
        d.text((48, ry), item["label"], font=font_row, fill=(30, 41, 59, 255))
        val_txt = item.get("val", "")
        vb = d.textbbox((0, 0), val_txt, font=font_title)
        d.text((cw - 60 - (vb[2] - vb[0]), ry - 4), val_txt, font=font_title, fill=tuple(item["color"]) + (255,))

        # Progress bar track & animated fill
        bar_y = ry + 50
        bar_w = cw - 108
        d.rounded_rectangle((48, bar_y, 48 + bar_w, bar_y + 32), radius=14, fill=(226, 232, 240, 255), outline=(30, 41, 59, 255), width=3)
        fill_w = max(24, int(bar_w * item.get("fill", 0.5) * rp))
        d.rounded_rectangle((48, bar_y, 48 + fill_w, bar_y + 32), radius=14, fill=tuple(item["color"]) + (255,), outline=(30, 41, 59, 255), width=3)

    if abs(s - 1.0) > 0.01:
        nw, nh = max(16, int(cw * s)), max(16, int(ch * s))
        card = card.resize((nw, nh), Image.Resampling.BILINEAR)

    cy = int(card_spec.get("y", 300))
    safe_alpha_composite(canvas, card, (W - card.width) // 2, cy + (ch - card.height) // 2)


# ==============================================================================
# 6. HIGH-CONTRAST READABLE HUD (TOP SAFE ZONE)
# ==============================================================================

def draw_hud_v2(
    canvas: Image.Image,
    series_label: str,
    day_num: int,
    ep_progress: float,
    t_global: float,
    font_bold: ImageFont.FreeTypeFont,
) -> None:
    """Crated crisp top HUD inside y=68..150, highly legible on mobile."""
    d = ImageDraw.Draw(canvas)
    s = spring_pop(min(1.0, t_global / 0.35)) if t_global < 0.35 else 1.0

    # Left pill: BOCA · KYB
    pad_x = 24
    tb = d.textbbox((0, 0), series_label, font=font_bold)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    pw = int((tw + pad_x * 2 + 24) * min(1.08, s))
    d.rounded_rectangle((48, 72, 48 + pw, 72 + th + 26), radius=28, fill=(17, 24, 39, 225), outline=(255, 255, 255, 210), width=3)
    d.ellipse((68, 72 + (th + 26) // 2 - 8, 84, 72 + (th + 26) // 2 + 8), fill=(239, 68, 68, 255))
    d.text((96, 72 + 11), series_label, font=font_bold, fill=(255, 255, 255, 255))

    # Right pill: HARI XX
    day_txt = f"HARI {day_num:02d}"
    db = d.textbbox((0, 0), day_txt, font=font_bold)
    dw = db[2] - db[0]
    rx0 = W - 48 - dw - 44
    d.rounded_rectangle((rx0, 72, W - 48, 72 + th + 26), radius=28, fill=(17, 24, 39, 225), outline=(250, 204, 21, 255), width=3)
    d.text((rx0 + 22, 72 + 11), day_txt, font=font_bold, fill=(250, 204, 21, 255))

    # Smooth episode progress bar across very top
    bar_w = int((W - 96) * clamp01(ep_progress))
    d.rounded_rectangle((48, 42, W - 48, 56), radius=7, fill=(15, 23, 42, 120))
    if bar_w > 12:
        d.rounded_rectangle((48, 42, 48 + bar_w, 56), radius=7, fill=(250, 204, 21, 255))