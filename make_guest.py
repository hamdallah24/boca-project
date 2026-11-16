#!/usr/bin/env python3
"""Guest character rigs — 6 recurring cast members.

Same flat-vector language as Boca/Lumi so guests sit naturally in the same
scene. Drawn at the same anchor as Boca: head center (540, 620), feet ~1560,
so the pipeline can crop with the identical box.

    python3 make_guest.py            # render contact sheet ke png/
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from make_boca import (BLUSH, INK, MOUTH, TONGUE, WHITE, circle, ellipse,  # noqa: E402
                       line, path, render_svg, svg_doc, text)

GUEST_SPECS = {
    "ardi": dict(name="Ardi", skin="#F2C9A0", hair="#171313", style="spiky",
                 shirt="#4C9BE8", pants="#3B4A63", shoes="#2B2B2B", acc=None,
                 edge="id-ID-ArdiNeural"),
    "bu_ratna": dict(name="Bu Ratna", skin="#E8B98A", hair="#2B1B14", style="hijab",
                     shirt="#D96C8A", pants="#7A4A6A", shoes="#5A3A4A", acc="earrings",
                     edge="id-ID-GadisNeural"),
    "pak_darno": dict(name="Pak Darno", skin="#D9A273", hair="#8A8A8A", style="short",
                      shirt="#6B8E5A", pants="#4A5A6A", shoes="#333333", acc="mustache",
                      edge="id-ID-ArdiNeural"),
    "sari": dict(name="Sari", skin="#F2C9A0", hair="#171313", style="pigtails",
                 shirt="#F2B84B", pants="#5A7FB8", shoes="#333333", acc=None,
                 edge="id-ID-GadisNeural"),
    "dokter_nia": dict(name="Dokter Nia", skin="#E8B98A", hair="#1F1A17", style="long",
                       shirt="#F2F6F7", pants="#2E6F8E", shoes="#333333", acc="stethoscope",
                       edge="id-ID-GadisNeural"),
    "kak_bima": dict(name="Kak Bima", skin="#D9A273", hair="#171313", style="cap",
                     shirt="#E86A3A", pants="#2F3B4A", shoes="#333333", acc="cap",
                     edge="id-ID-ArdiNeural"),
}


def _hair(spec: dict) -> str:
    c, style = spec["hair"], spec["style"]
    out: list[str] = []
    if style == "hijab":
        out.append(path(
            "M -262,-20 C -262,-310 262,-310 262,-20 L 262,330 L 190,330 "
            "L 190,-10 C 190,-150 -190,-150 -190,-10 L -190,330 L -262,330 Z", c, 12))
        out.append(path("M -150,-120 C -150,-250 150,-250 150,-120", "none", 8, "#FFFFFF", 'opacity="0.18"'))
        return "".join(out)
    if style == "cap":
        cap = "#2F3B4A"
        out.append(path("M -240,-60 C -240,-240 240,-240 240,-60 L 240,-40 "
                        "C 180,-100 -180,-100 -240,-40 Z", cap, 12))
        out.append(path("M -252,-86 C -140,-52 140,-52 252,-86 "
                        "C 240,-58 140,-34 0,-34 C -140,-34 -240,-58 -252,-86 Z",
                        cap, 12))
        out.append(circle(0, -236, 26, "#E86A3A", 8, WHITE))
        return "".join(out)
    # common hair bowl with a soft fringe
    out.append(path("M -250,-40 C -250,-268 250,-268 250,-40 "
                    "C 205,-96 170,-70 130,-92 C 85,-116 40,-92 0,-108 "
                    "C -40,-92 -85,-116 -130,-92 C -170,-70 -205,-96 -250,-40 Z", c, 12))
    if style == "spiky":
        for x in range(-210, 220, 62):
            out.append(path(f"M {x},-158 L {x + 34},-268 L {x + 68},-158 Z", c, 8))
    elif style == "bun":
        out.append(circle(0, -292, 74, c, 12))
        out.append(circle(0, -292, 46, c, 0, "none", 'opacity="0.55"'))
    elif style == "pigtails":
        out.append(circle(-278, -18, 62, c, 12))
        out.append(circle(278, -18, 62, c, 12))
        out.append(circle(-278, -18, 34, "#F2B84B", 8))
        out.append(circle(278, -18, 34, "#F2B84B", 8))
    elif style == "long":
        out.append(path("M -250,-60 C -250,-270 250,-270 250,-60 L 250,300 "
                        "L 176,300 L 176,-20 C 176,-150 -176,-150 -176,-20 "
                        "L -176,300 L -250,300 Z", c, 12))
    return "".join(out)


def _accessory(spec: dict, expr: str) -> str:
    out: list[str] = []
    acc = spec.get("acc")
    if acc == "mustache":
        out.append(ellipse(-52, 150, 46, 18, spec["hair"], 0, "none"))
        out.append(ellipse(52, 150, 46, 18, spec["hair"], 0, "none"))
    elif acc == "earrings":
        out.append(circle(-246, 78, 13, "#F4C542", 6))
        out.append(circle(246, 78, 13, "#F4C542", 6))
    elif acc == "stethoscope":
        out.append(path("M -120,300 C -120,430 120,430 120,300", "none", 12, "#2E6F8E"))
        out.append(circle(-128, 300, 18, "#2E6F8E", 8, "#C9D8DE"))
        out.append(circle(128, 300, 18, "#2E6F8E", 8, "#C9D8DE"))
        out.append(circle(0, 470, 30, "#C9D8DE", 10, "#2E6F8E"))
    return "".join(out)


def guest_head(expr: str, spec: dict, mouth: int = 0) -> str:
    out: list[str] = []
    skin = spec["skin"]
    out.append(circle(-250, 20, 32, skin, 12))
    out.append(circle(250, 20, 32, skin, 12))
    out.append(ellipse(0, 0, 250, 265, skin, 14))
    out.append(_hair(spec))
    out.append(ellipse(-90, 40, 72, 80, WHITE, 12))
    out.append(ellipse(90, 40, 72, 80, WHITE, 12))

    if expr == "happy":
        out.append(path("M -168,50 Q -90,-14 0,50", "none", 18))
        out.append(path("M 0,50 Q 90,-14 168,50", "none", 18))
        out.append(path("M -178,-68 Q -100,-90 -22,-68", "none", 15))
        out.append(path("M 22,-68 Q 100,-90 178,-68", "none", 15))
        out.append(path("M -78,160 Q 0,245 78,160 Q 0,202 -78,160 Z", MOUTH, 12))
        out.append(ellipse(0, 184, 24, 11, TONGUE, 0, "none"))
    elif expr == "shock":
        out.append(circle(-88, 60, 17, INK, 0, "none"))
        out.append(circle(92, 60, 17, INK, 0, "none"))
        out.append(circle(-80, 52, 6, WHITE, 0, "none"))
        out.append(circle(100, 52, 6, WHITE, 0, "none"))
        out.append(path("M -178,-84 Q -100,-112 -22,-84", "none", 15))
        out.append(path("M 22,-84 Q 100,-112 178,-84", "none", 15))
        out.append(ellipse(0, 192, 52, 48, MOUTH, 13))
        out.append(ellipse(0, 214, 18, 8, TONGUE, 0, "none"))
    elif expr == "confused":
        out.append(circle(-88, 70, 19, INK, 0, "none"))
        out.append(circle(92, 55, 19, INK, 0, "none"))
        out.append(circle(-80, 62, 6, WHITE, 0, "none"))
        out.append(circle(100, 52, 6, WHITE, 0, "none"))
        out.append(path("M -178,-58 Q -100,-98 -22,-72", "none", 15))
        out.append(path("M 22,-60 Q 100,-60 178,-60", "none", 15))
        out.append(path("M -58,188 Q -28,158 0,188 T 58,188", "none", 14))
    else:  # neutral
        out.append(circle(-88, 60, 18, INK, 0, "none"))
        out.append(circle(92, 60, 18, INK, 0, "none"))
        out.append(circle(-80, 52, 6, WHITE, 0, "none"))
        out.append(circle(100, 52, 6, WHITE, 0, "none"))
        out.append(path("M -178,-64 Q -100,-84 -22,-64", "none", 15))
        out.append(path("M 22,-64 Q 100,-84 178,-64", "none", 15))
        out.append(path("M -44,182 Q 0,218 44,182", "none", 12))

    out.append(ellipse(-164, 152, 36, 21, BLUSH, 0, "none", 'opacity="0.55"'))
    out.append(ellipse(164, 152, 36, 21, BLUSH, 0, "none", 'opacity="0.55"'))
    if mouth == 5:
        out.append(ellipse(0, 196, 112, 70, spec["skin"], 0, "none"))
    out.append(_accessory(spec, expr))
    return "".join(out)


def _arm(gesture: int, skin: str, sleeve: str) -> str:
    paths = {
        0: ("M -180,380 C -220,460 -240,540 -250,600", (-250, 600)),
        1: ("M -180,380 C -230,410 -225,450 -170,470", (-170, 470)),
        2: ("M -180,380 C -260,420 -320,470 -350,520", (-350, 520)),
        3: ("M -180,380 C -240,330 -280,250 -270,190", (-270, 190)),
        4: ("M -180,380 C -210,470 -230,560 -220,640", (-220, 640)),
    }
    d, (hx, hy) = paths[gesture]
    return (path(d, "none", 34, sleeve) + path(d, "none", 26, skin)
            + circle(hx, hy, 36, skin, 12))


def guest_body(pose: str, expr: str, arm: int, step: int, spec: dict) -> str:
    out: list[str] = []
    shirt, pants, shoes, skin = spec["shirt"], spec["pants"], spec["shoes"], spec["skin"]
    out.append(path("M 0,250 C 150,250 220,360 210,500 C 202,620 140,720 0,720 "
                    "C -140,720 -202,620 -210,500 C -220,360 -150,250 0,250 Z", shirt, 14))
    out.append(path("M -60,262 L 0,320 L 60,262", "none", 10))
    if spec.get("acc") == "stethoscope":
        out.append(path("M -120,300 C -120,430 120,430 120,300", "none", 12, "#2E6F8E"))
        out.append(circle(0, 452, 26, "#C9D8DE", 9, "#2E6F8E"))

    # legs
    if pose == "walk":
        if step % 2 == 0:
            legs = [(-64, 720, -132, 866), (64, 720, 46, 846)]
        else:
            legs = [(-64, 720, -46, 846), (64, 720, 132, 866)]
        for x1, y1, x2, y2 in legs:
            out.append(line(x1, y1, x2, y2, pants, 34))
            out.append(f'<path d="M {x2 - 54},{y2 + 18} Q {x2},{y2 - 16} {x2 + 54},{y2 + 18} '
                       f'L {x2 + 50},{y2 + 58} Q {x2},{y2 + 76} {x2 - 50},{y2 + 58} Z" '
                       f'fill="{shoes}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>')
    else:
        out.append(line(-70, 720, -82, 850, pants, 34))
        out.append(line(70, 720, 82, 850, pants, 34))
        out.append(f'<path d="M -166,850 Q -82,832 -18,860 L -22,916 Q -100,932 -172,908 Z" '
                   f'fill="{shoes}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>')
        out.append(f'<path d="M 18,860 Q 82,832 166,850 L 172,908 Q 100,932 22,916 Z" '
                   f'fill="{shoes}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>')

    out.append(_arm(arm, skin, shirt))
    if pose == "wave":
        out.append(path("M 180,380 C 250,320 300,250 315,180", "none", 34, shirt))
        out.append(path("M 180,380 C 250,320 300,250 315,180", "none", 26, skin))
        out.append(circle(315, 180, 38, skin, 12))
        out.append(path("M 350,140 L 380,110", "none", 8, INK))
        out.append(path("M 355,190 L 395,185", "none", 8, INK))
    elif pose == "point":
        out.append(path("M 180,380 C 260,360 330,350 390,360", "none", 34, shirt))
        out.append(path("M 180,380 C 260,360 330,350 390,360", "none", 26, skin))
        out.append(circle(390, 360, 38, skin, 12))
        out.append(path("M 425,340 L 470,330", "none", 8, INK))
        out.append(path("M 425,380 L 470,385", "none", 8, INK))
    else:
        out.append(path("M 180,380 C 235,470 255,565 248,645", "none", 34, shirt))
        out.append(path("M 180,380 C 235,470 255,565 248,645", "none", 26, skin))
        out.append(circle(248, 645, 36, skin, 12))
    return "".join(out)


def guest(gid: str, expr: str = "neutral", pose: str = "stand",
          x: float = 0, y: float = 0, scale: float = 1.0,
          arm_gesture: int = 0, step: int = 0, mouth: int = 0) -> str:
    spec = GUEST_SPECS[gid]
    parts = [guest_body(pose, expr, arm_gesture, step, spec),
             guest_head(expr, spec, mouth)]
    return f'<g transform="translate({x} {y}) scale({scale})">{"".join(parts)}</g>'


def main() -> None:
    png = ROOT / "png"
    png.mkdir(exist_ok=True)
    for gid in GUEST_SPECS:
        for expr, pose in [("neutral", "stand"), ("happy", "wave"), ("shock", "point")]:
            svg = svg_doc(1080, 1920, guest(gid, expr, pose, 540, 620, 1.0), None)
            sp = png / f"guest-{gid}-{expr}-{pose}.svg"
            sp.write_text(svg, encoding="utf-8")
            render_svg(sp, png / f"guest-{gid}-{expr}-{pose}.png", 1080, 1920, transparent=True)
    print(f"{len(GUEST_SPECS)} tamu dirender ke {png}")


if __name__ == "__main__":
    main()
