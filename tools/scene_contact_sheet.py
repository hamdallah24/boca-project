#!/usr/bin/env python3
"""Render semua scene ke satu contact sheet supaya gampang dicek visual.

    python3 tools/scene_contact_sheet.py            # 540x960 per tile
    python3 tools/scene_contact_sheet.py --size 270
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from make_cartoon import SCENES, build_scene  # noqa: E402

OUT = Path("/sdcard/Download/BOCA_DAILY/_assets")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=540, help="tinggi tile (default 540)")
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--out", default=str(OUT / "scenes_contact.png"))
    args = ap.parse_args()

    names = sorted(SCENES)
    th = args.size
    tw = int(th * 9 / 16)
    cols = args.cols
    rows = (len(names) + cols - 1) // cols
    pad = 10
    label_h = 34
    sheet = Image.new("RGB", (cols * (tw + pad) + pad,
                              rows * (th + label_h + pad) + pad), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except Exception:
        font = ImageFont.load_default()

    for i, name in enumerate(names):
        im = build_scene(name, (1350, 2400)).resize((tw, th), Image.Resampling.LANCZOS)
        x = pad + (i % cols) * (tw + pad)
        y = pad + (i // cols) * (th + label_h + pad)
        sheet.paste(im, (x, y))
        d.text((x + 4, y + th + 4), name, fill=(240, 240, 240), font=font)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"{len(names)} scene -> {out} ({sheet.width}x{sheet.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
