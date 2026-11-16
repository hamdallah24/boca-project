#!/usr/bin/env python3
"""Generate the Boca character sheet as SVG/PNG assets."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SVG_DIR = ROOT / "svg"
PNG_DIR = ROOT / "png"
SVG_DIR.mkdir(parents=True, exist_ok=True)
PNG_DIR.mkdir(parents=True, exist_ok=True)

# Palette
CREAM = "#F6F1E7"
INK = "#231815"
SKIN = "#F2C9A0"
SKIN_SHADOW = "#E7B58B"
HAIR = "#171313"
RED = "#D7263D"
RED_DARK = "#A8172A"
WHITE = "#FFFFFF"
TEAL = "#1F6F78"
TEAL_DARK = "#15545B"
YELLOW = "#F4B942"
BROWN = "#8B5A2B"
PAGE = "#F8E8C8"
BLUSH = "#E89A8A"
MOUTH = "#7A1F2B"
TONGUE = "#E86A7A"
LUMI_GOLD = "#FFD24A"
PENCIL_ERASER = "#F08A9B"

SW = 14  # main outline


def path(d: str, fill: str, sw: int = SW, stroke: str = INK, extra: str = "") -> str:
    return (
        f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
        f'stroke-linejoin="round" stroke-linecap="round" {extra}/>'
    )


def ellipse(cx: float, cy: float, rx: float, ry: float, fill: str, sw: int = 12,
            stroke: str = INK, extra: str = "") -> str:
    return (
        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{sw}" {extra}/>'
    )


def circle(cx: float, cy: float, r: float, fill: str, sw: int = 12,
           stroke: str = INK, extra: str = "") -> str:
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{sw}" {extra}/>'
    )


def line(x1: float, y1: float, x2: float, y2: float, color: str = INK,
         sw: int = 26, extra: str = "") -> str:
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
        f'stroke-width="{sw}" stroke-linecap="round" {extra}/>'
    )


def text(x: float, y: float, s: str, size: int, fill: str = INK,
         weight: str = "700", anchor: str = "middle", family: str = "Arial, Helvetica, sans-serif",
         extra: str = "") -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{s}</text>'
    )


def head(expr: str = "shock") -> str:
    """Head in local coordinates: center (0,0), r=250."""
    out: list[str] = []

    # Ears
    out.append(circle(-250, 20, 32, SKIN, 12))
    out.append(circle(250, 20, 32, SKIN, 12))
    out.append(circle(-250, 20, 14, SKIN_SHADOW, 0, "none"))
    out.append(circle(250, 20, 14, SKIN_SHADOW, 0, "none"))

    # Head
    out.append(ellipse(0, 0, 250, 265, SKIN, 14))

    # Pencil tucked behind the right ear (viewer right)
    out.append(
        '<g transform="rotate(22 245 55)">'
        + f'<rect x="235" y="-40" width="20" height="150" rx="9" fill="{YELLOW}" stroke="{INK}" stroke-width="8"/>'
        + f'<rect x="235" y="-48" width="20" height="26" rx="8" fill="{PENCIL_ERASER}" stroke="{INK}" stroke-width="8"/>'
        + f'<path d="M235,110 L245,145 L255,110 Z" fill="{INK}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
        + "</g>"
    )

    # Hair: bowl cut with wavy fringe
    hair_d = (
        "M -250,-90 "
        "C -250,-280 250,-280 250,-90 "
        "L 250,-60 "
        "C 212,-100 182,-80 152,-110 "
        "C 122,-130 92,-100 62,-120 "
        "C 32,-140 2,-105 -28,-120 "
        "C -58,-140 -88,-100 -118,-118 "
        "C -148,-130 -180,-105 -212,-60 "
        "L -250,-90 Z"
    )
    out.append(path(hair_d, HAIR, 14))

    # Cap: crown + white front panel + brim + badge
    cap = []
    cap.append(path("M -212,-132 C -212,-304 212,-304 212,-132 L 212,-104 L -212,-104 Z", RED, 14))
    cap.append(path("M -152,-132 C -152,-244 152,-244 152,-132 L 152,-104 L -152,-104 Z", WHITE, 12))
    # Brim (thin visor)
    cap.append(path(
        "M -224,-142 C -124,-112 124,-112 224,-142 "
        "C 214,-116 124,-92 0,-92 C -124,-92 -214,-116 -224,-142 Z",
        RED, 14,
    ))
    # Badge
    cap.append(circle(0, -186, 38, RED, 9, WHITE))
    cap.append(text(0, -175, "SD", 27, WHITE, "800"))
    out.append(f'<g transform="rotate(-6 0 -175)">{"".join(cap)}</g>')

    # Eyes
    out.append(ellipse(-90, 40, 72, 80, WHITE, 12))
    out.append(ellipse(90, 40, 72, 80, WHITE, 12))

    # Pupils / brows / mouth per expression
    if expr == "neutral":
        out.append(circle(-88, 60, 18, INK, 0, "none"))
        out.append(circle(92, 60, 18, INK, 0, "none"))
        out.append(circle(-80, 52, 6, WHITE, 0, "none"))
        out.append(circle(100, 52, 6, WHITE, 0, "none"))
        out.append(path("M -178,-64 Q -100,-84 -22,-64", "none", 15))
        out.append(path("M 22,-64 Q 100,-84 178,-64", "none", 15))
        out.append(ellipse(0, 192, 38, 38, MOUTH, 12))
    elif expr == "shock":
        out.append(circle(-88, 60, 17, INK, 0, "none"))
        out.append(circle(92, 60, 17, INK, 0, "none"))
        out.append(circle(-80, 52, 6, WHITE, 0, "none"))
        out.append(circle(100, 52, 6, WHITE, 0, "none"))
        out.append(path("M -178,-84 Q -100,-112 -22,-84", "none", 15))
        out.append(path("M 22,-84 Q 100,-112 178,-84", "none", 15))
        out.append(ellipse(0, 192, 52, 48, MOUTH, 13))
        out.append(ellipse(0, 214, 18, 8, TONGUE, 0, "none"))
    elif expr == "happy":
        out.append(path("M -168,50 Q -90,-14 0,50", "none", 18))
        out.append(path("M 0,50 Q 90,-14 168,50", "none", 18))
        out.append(path("M -178,-68 Q -100,-90 -22,-68", "none", 15))
        out.append(path("M 22,-68 Q 100,-90 178,-68", "none", 15))
        out.append(path("M -78,160 Q 0,245 78,160 Q 0,202 -78,160 Z", MOUTH, 12))
        out.append(ellipse(0, 184, 24, 11, TONGUE, 0, "none"))
    elif expr == "confused":
        out.append(circle(-88, 70, 19, INK, 0, "none"))
        out.append(circle(92, 55, 19, INK, 0, "none"))
        out.append(circle(-80, 62, 6, WHITE, 0, "none"))
        out.append(circle(100, 52, 6, WHITE, 0, "none"))
        out.append(path("M -178,-58 Q -100,-98 -22,-72", "none", 15))
        out.append(path("M 22,-60 Q 100,-60 178,-60", "none", 15))
        out.append(path("M -58,188 Q -28,158 0,188 T 58,188", "none", 14))
    elif expr == "sleepy":
        out.append(path("M -168,52 Q -90,18 0,52", "none", 18))
        out.append(path("M 0,52 Q 90,18 168,52", "none", 18))
        out.append(path("M -178,-50 Q -100,-68 -22,-54", "none", 15))
        out.append(path("M 22,-54 Q 100,-68 178,-50", "none", 15))
        out.append(ellipse(0, 190, 30, 22, MOUTH, 12))
        out.append(text(205, -150, "z", 52, INK, "800"))
        out.append(text(245, -198, "z", 36, INK, "800"))
    elif expr == "focus":
        out.append(circle(-88, 72, 19, INK, 0, "none"))
        out.append(circle(92, 72, 19, INK, 0, "none"))
        out.append(circle(-80, 64, 6, WHITE, 0, "none"))
        out.append(circle(100, 64, 6, WHITE, 0, "none"))
        out.append(path("M -178,-46 Q -100,-72 -22,-50", "none", 16))
        out.append(path("M 22,-50 Q 100,-72 178,-46", "none", 16))
        out.append(path("M -40,188 L 40,188", "none", 14))
    else:
        raise ValueError(expr)

    # Blush
    out.append(ellipse(-164, 152, 36, 21, BLUSH, 0, "none", 'opacity="0.55"'))
    out.append(ellipse(164, 152, 36, 21, BLUSH, 0, "none", 'opacity="0.55"'))

    return "".join(out)


def left_arm(gesture: int = 0) -> str:
    """Left arm (viewer left) with optional gesture.

    Gesture 0 is the original standing arm, so existing assets stay unchanged.
    """
    if gesture == 0:
        d = "M -180,380 C -220,460 -240,540 -250,600"
        hx, hy = -250, 600
    elif gesture == 1:
        d = "M -180,380 C -230,410 -225,450 -170,470"
        hx, hy = -170, 470
    elif gesture == 2:
        d = "M -180,380 C -260,420 -320,470 -350,520"
        hx, hy = -350, 520
    elif gesture == 3:
        d = "M -180,380 C -240,330 -280,250 -270,190"
        hx, hy = -270, 190
    elif gesture == 4:
        d = "M -180,380 C -210,470 -230,560 -220,640"
        hx, hy = -220, 640
    else:
        raise ValueError(f"unknown arm gesture: {gesture}")
    return path(d, "none", 26) + circle(hx, hy, 36, SKIN, 12)


def mouth_overlay(state: int = 0) -> str:
    """Optional talking-mouth overlay.

    state 0: leave the expression mouth untouched.
    state 1: small open mouth.
    state 2: wide open mouth.
    state 3: closed neutral line.
    state 4: closed smile.
    state 5: blank skin patch (for runtime mouth drawing).
    """
    if state == 0:
        return ""
    out = [ellipse(0, 200, 100, 62, SKIN, 0, "none")]
    if state == 1:
        out.append(ellipse(0, 196, 26, 20, MOUTH, 8))
        out.append(ellipse(0, 204, 14, 7, TONGUE, 0, "none"))
    elif state == 2:
        out.append(ellipse(0, 198, 46, 36, MOUTH, 8))
        out.append(ellipse(0, 210, 26, 11, TONGUE, 0, "none"))
    elif state == 3:
        out.append(path("M -40,192 L 40,192", "none", 10))
    elif state == 4:
        out.append(path("M -48,188 Q 0,228 48,188", "none", 10))
    elif state == 5:
        pass
    else:
        raise ValueError(f"unknown mouth state: {state}")
    return "".join(out)


def body(pose: str = "stand", expr: str = "neutral", arm_gesture: int = 0,
         step: int = 0, book: bool = True) -> str:
    """Body in local coordinates, head center at (0,0). Body top y=250."""
    out: list[str] = []

    # Backpack behind body
    out.append(f'<rect x="-265" y="300" width="105" height="300" rx="48" fill="{TEAL}" stroke="{INK}" stroke-width="14"/>')
    out.append(f'<rect x="-245" y="330" width="38" height="110" rx="18" fill="{TEAL_DARK}" stroke="{INK}" stroke-width="6"/>')

    # Bean body / shirt
    body_d = (
        "M 0,250 "
        "C 160,250 232,370 222,510 "
        "C 214,630 142,730 0,730 "
        "C -142,730 -214,630 -222,510 "
        "C -232,370 -160,250 0,250 Z"
    )
    out.append(path(body_d, WHITE, 14))

    # Shorts
    shorts_d = (
        "M -202,560 "
        "C -120,592 120,592 202,560 "
        "L 192,640 "
        "C 182,720 102,730 0,730 "
        "C -102,730 -182,720 -192,640 Z"
    )
    out.append(path(shorts_d, RED, 14))
    out.append(line(0, 594, 0, 722, INK, 8))

    # Backpack strap
    out.append(path("M -160,258 C -174,330 -174,430 -160,520", "none", 30, TEAL_DARK))
    out.append(path("M -160,258 C -174,330 -174,430 -160,520", "none", 20, TEAL))

    # Tie (slightly crooked)
    tie = []
    tie.append(path("M 0,258 L 30,290 L 0,322 L -30,290 Z", RED, 10))
    tie.append(path("M -21,312 L 21,312 L 42,492 L 0,532 L -42,492 Z", RED, 10))
    tie.append(path("M -12,330 L 12,330 L 24,470 L 0,496 L -24,470 Z", RED_DARK, 0, "none", 'opacity="0.55"'))
    out.append(f'<g transform="rotate(3 0 400)">{"".join(tie)}</g>')

    # Name tag
    out.append(f'<rect x="-158" y="392" width="104" height="54" rx="12" fill="{WHITE}" stroke="{INK}" stroke-width="8"/>')
    out.append(text(-106, 429, "BOCA", 21, INK, "800"))

    # Legs / shoes
    if pose == "run":
        out.append(line(-64, 720, -150, 900, INK, 28))
        out.append(line(64, 720, 150, 880, INK, 28))
        out.append(line(-150, 900, -205, 940, INK, 26))
        out.append(line(150, 880, 210, 930, INK, 26))
        out.append(f'<path d="M -260,930 Q -205,900 -150,940 L -160,990 Q -215,1000 -265,970 Z" fill="{INK}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>')
        out.append(f'<path d="M 160,920 Q 215,890 270,930 L 265,980 Q 210,995 160,965 Z" fill="{INK}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>')
    elif pose == "walk":
        # step 0: viewer-left leg forward, step 1: viewer-right leg forward
        if step % 2 == 0:
            lf, rf = (-132, 866), (46, 846)
            out.append(line(-64, 720, lf[0], lf[1], INK, 28))
            out.append(line(64, 720, rf[0], rf[1], INK, 28))
        else:
            lf, rf = (-46, 846), (132, 866)
            out.append(line(-64, 720, lf[0], lf[1], INK, 28))
            out.append(line(64, 720, rf[0], rf[1], INK, 28))
        for fx, fy in (lf, rf):
            out.append(
                f'<path d="M {fx-54},{fy+18} Q {fx},{fy-16} {fx+54},{fy+18} '
                f'L {fx+50},{fy+58} Q {fx},{fy+76} {fx-50},{fy+58} Z" '
                f'fill="{INK}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
            )
    else:
        out.append(line(-70, 720, -82, 850, INK, 28))
        out.append(line(70, 720, 82, 850, INK, 28))
        # socks
        out.append(f'<rect x="-108" y="808" width="52" height="52" rx="18" fill="{WHITE}" stroke="{INK}" stroke-width="8"/>')
        out.append(f'<rect x="56" y="808" width="52" height="52" rx="18" fill="{WHITE}" stroke="{INK}" stroke-width="8"/>')
        # shoes
        out.append(f'<path d="M -166,850 Q -82,832 -18,860 L -22,916 Q -100,932 -172,908 Z" fill="{INK}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>')
        out.append(f'<path d="M 18,860 Q 82,832 166,850 L 172,908 Q 100,932 22,916 Z" fill="{INK}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>')
        out.append(f'<path d="M -162,906 Q -100,924 -26,910" fill="none" stroke="{WHITE}" stroke-width="7" stroke-linecap="round"/>')
        out.append(f'<path d="M 26,910 Q 100,924 162,906" fill="none" stroke="{WHITE}" stroke-width="7" stroke-linecap="round"/>')

    # Arms + book per pose
    if pose == "wave":
        out.append(left_arm(arm_gesture))
        out.append(path("M 180,380 C 250,320 300,250 315,180", "none", 26))
        out.append(circle(315, 180, 38, SKIN, 12))
        # little motion lines
        out.append(path("M 350,140 L 380,110", "none", 8, INK))
        out.append(path("M 355,190 L 395,185", "none", 8, INK))
    elif pose == "think":
        out.append(left_arm(arm_gesture))
        out.append(path("M 180,380 C 230,350 190,300 130,285", "none", 26))
    elif pose == "read":
        out.append(path("M -180,380 C -160,480 -130,590 -100,665", "none", 26))
        out.append(path("M 180,380 C 180,480 170,590 160,665", "none", 26))
    elif pose == "point":
        out.append(left_arm(arm_gesture))
        out.append(path("M 180,380 C 260,360 330,350 390,360", "none", 26))
        out.append(circle(390, 360, 38, SKIN, 12))
        out.append(path("M 425,340 L 470,330", "none", 8, INK))
        out.append(path("M 425,380 L 470,385", "none", 8, INK))
    elif pose == "walk":
        out.append(left_arm(arm_gesture))
        if step % 2 == 0:
            out.append(path("M 180,380 C 235,430 255,510 240,585", "none", 26))
            out.append(circle(240, 585, 36, SKIN, 12))
        else:
            out.append(path("M 180,380 C 235,340 285,320 325,335", "none", 26))
            out.append(circle(325, 335, 36, SKIN, 12))
    elif pose == "celebrate":
        out.append(path("M -180,380 C -250,320 -300,250 -315,180", "none", 26))
        out.append(circle(-315, 180, 38, SKIN, 12))
        out.append(path("M 180,380 C 250,320 300,250 315,180", "none", 26))
        out.append(circle(315, 180, 38, SKIN, 12))
        out.append(path("M -350,140 L -380,110", "none", 8, INK))
        out.append(path("M 350,140 L 380,110", "none", 8, INK))
    else:  # stand
        out.append(left_arm(arm_gesture))
        if book:
            out.append(path("M 180,380 C 240,480 285,590 310,665", "none", 26))
        else:
            out.append(path("M 180,380 C 235,470 255,565 248,645", "none", 26))
            out.append(circle(248, 645, 36, SKIN, 12))

    # Book (right-hand carry for stand, centered two-hand hold for read)
    if book and pose in ("stand", "read"):
        if pose == "read":
            bx0, bx1, bmid = -120, 180, 30
        else:
            bx0, bx1, bmid = 185, 435, 310
        book = []
        book.append(f'<path d="M {bx0},455 L {bx1},455 L {bx1},665 L {bx0},665 Z" fill="{BROWN}" stroke="{INK}" stroke-width="14" stroke-linejoin="round"/>')
        book.append(f'<path d="M {bx0+15},471 L {bmid},471 L {bmid},649 L {bx0+15},649 Z" fill="{PAGE}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>')
        book.append(f'<path d="M {bmid},471 L {bx1-15},471 L {bx1-15},649 L {bmid},649 Z" fill="{PAGE}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>')
        book.append(line(bmid, 471, bmid, 649, INK, 10))
        for yy in (500, 528, 556, 584):
            book.append(line(bx0+33, yy, bmid-18, yy, "#B99B7A", 6))
            book.append(line(bmid+18, yy, bx1-33, yy, "#B99B7A", 6))
        out.append("".join(book))
        # hands over the book edge
        if pose == "stand":
            out.append(circle(310, 675, 36, SKIN, 12))
        else:
            out.append(circle(-100, 675, 36, SKIN, 12))
            out.append(circle(160, 675, 36, SKIN, 12))

    return "".join(out)


def prop_sprite(prop: str | None = None) -> str:
    """Optional handheld prop drawn in front of the character."""
    if not prop:
        return ""
    if prop == "prism":
        # small glass prism held up near the pointing hand
        cx, cy, s = 330, 290, 70
        return "".join([
            path(f"M {cx},{cy - s} L {cx - s * 0.86},{cy + s * 0.62} L {cx + s * 0.86},{cy + s * 0.62} Z",
                 "#CDEBFF", 11, INK, 'fill-opacity="0.5"'),
            path(f"M {cx},{cy - s} L {cx - s * 0.86},{cy + s * 0.62}", "none", 5, INK, 'opacity="0.4"'),
            path(f"M {cx - 16},{cy - s + 26} L {cx + 10},{cy - s + 44}", "none", 5, WHITE, 'opacity="0.9"'),
        ])
    raise ValueError(f"unknown prop: {prop}")


def lumi(expr: str = "happy", pose: str = "float", x: float = 0, y: float = 0,
         scale: float = 1.0, glow: bool = True, mouth: int = 0) -> str:
    """Sidekick character Lumi - a small bouncing light blob that helps tell the story.

    Local coordinates: body centre at (0,0), feet around y=210.
    mouth: 0 = default smile, 5 = blank patch so the mouth can be drawn at runtime.
    """
    r = 170
    out: list[str] = []
    if glow:
        for i, a in enumerate([0.11, 0.07, 0.045]):
            rr = r * (1.16 + i * 0.15)
            out.append(circle(0, 0, rr, LUMI_GOLD, 0, "none", f'opacity="{a}"'))
    out.append(circle(0, 0, r, LUMI_GOLD, 14, INK))
    out.append(ellipse(-74, 198, 46, 26, INK, 0, "none"))
    out.append(ellipse(74, 198, 46, 26, INK, 0, "none"))

    if pose == "wave":
        out.append(path("M -150,40 C -200,85 -215,140 -205,192", "none", 22))
        out.append(circle(-205, 192, 30, LUMI_GOLD, 10, INK))
        out.append(path("M 150,15 C 212,-40 248,-100 256,-148", "none", 22))
        out.append(circle(256, -148, 32, LUMI_GOLD, 10, INK))
    elif pose == "point":
        out.append(path("M -150,40 C -200,90 -205,150 -195,196", "none", 22))
        out.append(circle(-195, 196, 30, LUMI_GOLD, 10, INK))
        out.append(path("M 150,18 C 215,8 265,-2 312,-12", "none", 22))
        out.append(circle(312, -12, 32, LUMI_GOLD, 10, INK))
    elif pose == "cheer":
        out.append(path("M -150,18 C -200,-52 -215,-112 -205,-158", "none", 22))
        out.append(circle(-205, -158, 32, LUMI_GOLD, 10, INK))
        out.append(path("M 150,18 C 200,-52 215,-112 205,-158", "none", 22))
        out.append(circle(205, -158, 32, LUMI_GOLD, 10, INK))
    else:  # float
        out.append(path("M -150,28 C -205,60 -215,116 -205,158", "none", 22))
        out.append(circle(-205, 158, 30, LUMI_GOLD, 10, INK))
        out.append(path("M 150,28 C 205,60 215,116 205,158", "none", 22))
        out.append(circle(205, 158, 30, LUMI_GOLD, 10, INK))

    out.append(ellipse(-58, -42, 40, 46, WHITE, 10))
    out.append(ellipse(58, -42, 40, 46, WHITE, 10))
    if expr == "shock":
        out.append(circle(-56, -40, 19, INK, 0, "none"))
        out.append(circle(60, -40, 19, INK, 0, "none"))
    else:
        out.append(circle(-54, -38, 16, INK, 0, "none"))
        out.append(circle(62, -38, 16, INK, 0, "none"))
    if mouth == 5:
        out.append(ellipse(0, 72, 62, 52, LUMI_GOLD, 0, "none"))
    elif expr == "shock":
        out.append(ellipse(0, 72, 34, 40, MOUTH, 10))
    else:
        out.append(path("M -46,54 Q 0,100 46,54", "none", 11, INK))
    out.append(ellipse(-118, 24, 30, 18, BLUSH, 0, "none", 'opacity="0.5"'))
    out.append(ellipse(118, 24, 30, 18, BLUSH, 0, "none", 'opacity="0.5"'))
    return f'<g transform="translate({x} {y}) scale({scale})">{"".join(out)}</g>'


def character(expr: str = "shock", pose: str = "stand", x: float = 0, y: float = 0,
              scale: float = 1.0, shadow: bool = True, arm_gesture: int = 0,
              mouth: int = 0, step: int = 0, prop: str | None = None,
              book: bool = True) -> str:
    parts = []
    if shadow:
        parts.append(ellipse(0, 940, 270, 32, "#000000", 0, "none", 'opacity="0.10"'))
    parts.append(body(pose, expr, arm_gesture, step, book))
    parts.append(head(expr))
    if mouth:
        parts.append(mouth_overlay(mouth))
    if prop:
        parts.append(prop_sprite(prop))
    if pose == "think":
        parts.append(circle(130, 285, 36, SKIN, 12))
    return f'<g transform="translate({x} {y}) scale({scale})">{"".join(parts)}</g>'


def bust() -> str:
    """Simple shoulders bust for expression cards."""
    out: list[str] = []
    out.append(path("M -190,250 C -190,180 190,180 190,250 L 190,380 L -190,380 Z", WHITE, 14))
    out.append(path("M -80,250 L 0,320 L 80,250", "none", 10))
    out.append(path("M 0,270 L 26,296 L 0,322 L -26,296 Z", RED, 10))
    out.append(path("M -18,310 L 18,310 L 34,400 L 0,430 L -34,400 Z", RED, 10))
    out.append(path("M -150,260 C -160,300 -160,350 -150,390", "none", 28, TEAL_DARK))
    out.append(path("M -150,260 C -160,300 -160,350 -150,390", "none", 18, TEAL))
    return "".join(out)


def expression_sheet() -> str:
    w, h = 1080, 1920
    parts: list[str] = []
    parts.append(text(540, 55, "BOCA — EKSPRESI v1", 38, INK, "800"))
    parts.append(text(540, 90, "wajah dasar untuk animasi", 20, "#6B5B4B", "500"))
    exps = [
        ("neutral", "NETRAL", "mata tenang, mulut kecil"),
        ("shock", "KAGET", "mata besar, mulut terbuka"),
        ("happy", "SENANG", "mata melengkung, senyum"),
        ("confused", "BINGUNG", "pupil geser, alis asimetris"),
        ("sleepy", "NGANTUK", "mata setengah, mulut kecil"),
        ("focus", "FOKUS", "alis turun, mulut datar"),
    ]
    for i, (expr, label, desc) in enumerate(exps):
        col, row = i % 2, i // 2
        x, y = 30 + col * 520, 120 + row * 580
        parts.append(f'<rect x="{x}" y="{y}" width="500" height="560" rx="28" fill="#FFF9EE" stroke="#E7DCCB" stroke-width="3"/>')
        cx, cy = x + 250, y + 260
        parts.append(f'<g transform="translate({cx} {cy}) scale(0.55)">{bust()}{head(expr)}</g>')
        parts.append(text(cx, y + 520, label, 30, INK, "800"))
        parts.append(text(cx, y + 548, desc, 17, "#7A6A5A", "500"))
    return svg_doc(w, h, "".join(parts), CREAM)


def cover_sheet() -> str:
    w, h = 1080, 1920
    parts: list[str] = []
    parts.append(f'<rect x="0" y="0" width="1080" height="18" fill="{RED}"/>')
    parts.append(text(540, 130, "BOCA", 110, INK, "900"))
    parts.append(f'<rect x="420" y="150" width="240" height="8" rx="4" fill="{RED}"/>')
    parts.append(text(540, 195, "bocah SD • bahasa bayi • rasa ingin tahu", 26, "#6B5B4B", "600"))
    parts.append(character("happy", "wave", 540, 880, 0.82, shadow=True))
    swatches = [(CREAM, "KREM"), (INK, "TINTA"), (RED, "MERAH"), (TEAL, "TEAL"), (YELLOW, "KUNING")]
    for i, (color, label) in enumerate(swatches):
        x = 180 + i * 180
        parts.append(f'<rect x="{x-35}" y="1740" width="70" height="70" rx="18" fill="{color}" stroke="{INK}" stroke-width="4"/>')
        parts.append(text(x, 1840, label, 16, "#6B5B4B", "700"))
    parts.append(text(540, 1880, "v1 — untuk review • belum masuk engine", 18, "#7A6A5A", "500"))
    return svg_doc(w, h, "".join(parts), CREAM)


def pose_sheet() -> str:
    w, h = 1080, 1920
    parts: list[str] = []
    parts.append(text(540, 55, "BOCA — POSE v1", 38, INK, "800"))
    parts.append(text(540, 90, "tiga pose dasar untuk konten pendek", 20, "#6B5B4B", "500"))
    poses = [
        ("wave", "happy", "SAPA", "tangan melambai, ekspresi senang", "opening / hook", RED),
        ("think", "confused", "MIKIR", "tangan di dagu, ekspresi bingung", "pertanyaan / konflik", TEAL),
        ("read", "focus", "BACA", "memegang buku, ekspresi fokus", "edukasi / penjelasan", YELLOW),
    ]
    for i, (pose, expr, label, desc, use, accent) in enumerate(poses):
        y = 110 + i * 580
        parts.append(f'<rect x="40" y="{y}" width="1000" height="560" rx="28" fill="#FFF9EE" stroke="#E7DCCB" stroke-width="3"/>')
        parts.append(f'<rect x="560" y="{y+100}" width="60" height="8" rx="4" fill="{accent}"/>')
        parts.append(character(expr, pose, 280, y + 210, 0.36, shadow=True))
        parts.append(f'<line x1="520" y1="{y+45}" x2="520" y2="{y+515}" stroke="#E7DCCB" stroke-width="3"/>')
        parts.append(text(560, y + 170, label, 34, INK, "800", "start"))
        parts.append(text(560, y + 220, desc, 20, "#6B5B4B", "500", "start"))
        parts.append(text(560, y + 270, use, 16, "#7A6A5A", "500", "start"))
    return svg_doc(w, h, "".join(parts), CREAM)


def svg_doc(w: int, h: int, content: str, bg: str | None = CREAM) -> str:
    rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'{rect}{content}</svg>'
    )


def render_svg(svg_path: Path, png_path: Path, w: int, h: int, transparent: bool = False) -> None:
    url = svg_path.resolve().as_uri()
    cmd = [
        "chromium-browser", "--headless=new", "--no-sandbox", "--disable-gpu",
        "--hide-scrollbars", f"--screenshot={png_path}", f"--window-size={w},{h}",
    ]
    if transparent:
        cmd.append("--default-background-color=00000000")
    cmd.append(url)
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", png_path)


def main() -> None:
    # Front view: 1080x1920, character centered
    front = svg_doc(1080, 1920, character("shock", "stand", 540, 620, 1.0), CREAM)
    (SVG_DIR / "boca-front-v1.svg").write_text(front, encoding="utf-8")
    render_svg(SVG_DIR / "boca-front-v1.svg", PNG_DIR / "boca-front-v1.png", 1080, 1920)

    # Transparent front for compositing
    front_t = svg_doc(1080, 1920, character("shock", "stand", 540, 620, 1.0), None)
    (SVG_DIR / "boca-front-v1-transparent.svg").write_text(front_t, encoding="utf-8")
    render_svg(SVG_DIR / "boca-front-v1-transparent.svg", PNG_DIR / "boca-front-v1-transparent.png", 1080, 1920, transparent=True)

    # Neutral front for comparison
    neutral = svg_doc(1080, 1920, character("neutral", "stand", 540, 620, 1.0), CREAM)
    (SVG_DIR / "boca-front-neutral-v1.svg").write_text(neutral, encoding="utf-8")
    render_svg(SVG_DIR / "boca-front-neutral-v1.svg", PNG_DIR / "boca-front-neutral-v1.png", 1080, 1920)

    # Cover / hero sheet
    cover = cover_sheet()
    (SVG_DIR / "boca-cover-v1.svg").write_text(cover, encoding="utf-8")
    render_svg(SVG_DIR / "boca-cover-v1.svg", PNG_DIR / "boca-cover-v1.png", 1080, 1920)

    # Expression and pose sheets
    expr = expression_sheet()
    (SVG_DIR / "boca-expressions-v1.svg").write_text(expr, encoding="utf-8")
    render_svg(SVG_DIR / "boca-expressions-v1.svg", PNG_DIR / "boca-expressions-v1.png", 1080, 1920)

    poses = pose_sheet()
    (SVG_DIR / "boca-poses-v1.svg").write_text(poses, encoding="utf-8")
    render_svg(SVG_DIR / "boca-poses-v1.svg", PNG_DIR / "boca-poses-v1.png", 1080, 1920)


if __name__ == "__main__":
    main()
