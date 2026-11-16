#!/usr/bin/env python3
"""Bangun storyboard BOCA dari data ringkas (biar tidak salah struktur).

Data ditulis di file Python lain sebagai list `EPISODES` berisi dict:
    {
      "id": "BOCA-D04", "day": 4, "title": "...", "duration": 45,
      "logline": "...", "guest": "sari" | None,
      "hook": ("H3", "claim", "gap", "promise"),
      "analogy": {"source": "...", "maps": [("real", "analogy"), ...],
                  "line_shot": 4, "why_it_works": "..."},
      "shots": [
        {"scene": "city_street", "beat": "hook",
         "cam": (0.30, 0.70, 0.35, 0.62, 1.0, 1.0),
         "keys": [(0.0, "neutral", "walk", [0], -300, 1400, 640), ...],
         "lumi": [(1.2, "happy", "float", 870, 1080, 235), ...],
         "guest": [(0.0, "neutral", "stand", 720, 1420, 610), ...],
         "sfx": [(0.05, "whoosh", 0.8)],
         "lines": [("boca", "teks", "caption", "caption dewasa"), ...]},
      ],
    }

Pemakaian:
    python3 tools/draft_storyboard.py production/_drafts/d04_d07.py --write
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "production" / "storyboards"
VOICE = {"boca": "Puck", "lumi": "Aoede",
         "ardi": "Fenrir", "bu_ratna": "Kore", "pak_darno": "Charon",
         "sari": "Leda", "dokter_nia": "Autonoe", "kak_bima": "Orus"}
GUEST_NAME = {"ardi": "Ardi", "bu_ratna": "Bu Ratna", "pak_darno": "Pak Darno",
              "sari": "Sari", "dokter_nia": "Dokter Nia", "kak_bima": "Kak Bima"}
EMO = {"hook": "penasaran", "setup": "menjelaskan", "explain": "menjelaskan",
       "twist": "menegaskan", "payoff": "hangat", "cta": "hangat"}


def _key(k: tuple) -> dict:
    t, expr, pose, arms, x, ground, h = k[:7]
    out = {"t": t, "expr": expr, "pose": pose, "arms": list(arms),
           "x": x, "ground": ground, "h": h}
    if len(k) > 7:
        extra = k[7]
        if "period" in extra:
            out["period"] = extra["period"]
        if "prop" in extra:
            out["prop"] = extra["prop"]
    return out


def build(ep: dict) -> dict:
    shots, structure, beats = [], [], []
    words = 0
    lumi_lines = 0
    for i, s in enumerate(ep["shots"], 1):
        fx0, fx1, fy0, fy1, z0, z1 = s["cam"]
        dlg = []
        for who, text, cap, adult in s["lines"]:
            dlg.append({"who": who, "text": text, "caption": cap, "caption_adult": adult})
            words += len(text.split())
            if who == "lumi":
                lumi_lines += 1
        shot = {
            "n": i, "scene": s["scene"], "beat": s["beat"],
            "cam": {"fx": [fx0, fx1], "fy": [fy0, fy1], "z": [z0, z1]},
            "keys": [_key(k) for k in s["keys"]],
            "lumi": [{"t": t, "expr": e, "pose": p, "x": x, "y": y, "h": h}
                     for t, e, p, x, y, h in s.get("lumi", [])],
            "sfx": [list(x) for x in s.get("sfx", [])],
            "est_seconds": 0.0,
            "dialogue": dlg,
        }
        if ep.get("guest"):
            shot["guest"] = [{"t": t, "expr": e, "pose": p, "x": x, "ground": g, "h": h}
                             for t, e, p, x, g, h in s.get("guest", [])]
        # estimasi kasar per shot, nanti dipakai untuk menaruh key kalau perlu
        shot["est_seconds"] = round(sum(len(l["text"].split()) for l in dlg) * 0.30
                                    + len(dlg) * 0.16, 1)
        shots.append(shot)
        structure.append({"beat": s["beat"], "shot": i})
        beats.append({"shot": i, "function": s["beat"], "emotion": EMO.get(s["beat"], "netral"),
                      "emphasis": s.get("emphasis", []), "pause_before": 0.0,
                      "pause_after": 0.2})

    hook = ep["hook"]
    an = ep["analogy"]
    lines_total = sum(len(s["lines"]) for s in ep["shots"])
    est = round(words * 0.30 + lines_total * 0.16, 1)
    scenes = []
    for s in shots:
        if s["scene"] not in scenes:
            scenes.append(s["scene"])
    needs = [{"type": "scene", "id": sc, "priority": "P0"} for sc in scenes]
    if ep.get("guest"):
        needs.append({"type": "character", "id": ep["guest"], "priority": "P0"})
    needs += [{"type": "voice", "id": VOICE["boca"], "priority": "P0"},
              {"type": "voice", "id": VOICE["lumi"], "priority": "P0"}]
    if ep.get("guest"):
        needs.append({"type": "voice", "id": VOICE[ep["guest"]], "priority": "P0"})

    return {
        "id": ep["id"], "day": ep["day"], "series": ep.get("series", "KYB"),
        "title": ep["title"], "duration_target": ep["duration"],
        "facts_status": "pending",
        "logline": ep["logline"],
        "hook": {"pattern": hook[0], "claim": hook[1], "gap": hook[2],
                 "promise": hook[3], "seconds": ep.get("hook_seconds", 3)},
        "cast": {"host": "boca", "sidekick": "lumi", "guest": ep.get("guest")},
        "analogy": {"source": an["source"],
                    "maps": [{"real": r, "analogy": a} for r, a in an["maps"]],
                    "line_shot": an["line_shot"], "why_it_works": an["why_it_works"]},
        "structure": structure,
        "vo": {"voice_boca": VOICE["boca"], "voice_lumi": VOICE["lumi"],
               "voice_guest": VOICE[ep["guest"]] if ep.get("guest") else None,
               "style_note": "hangat, santai, tempo sedang, tanpa baby talk",
               "total_words": words, "est_seconds": est, "lumi_lines": lumi_lines,
               "beats": beats},
        "shots": shots,
        "asset_needs": needs,
        "production_notes": ep.get("notes", ""),
    }


def load(path: Path):
    spec = importlib.util.spec_from_file_location("draft_data", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.EPISODES


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data", help="file python berisi EPISODES")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    eps = load(Path(args.data))
    OUT.mkdir(parents=True, exist_ok=True)
    for ep in eps:
        doc = build(ep)
        dst = OUT / f"{doc['id']}.json"
        if not args.write:
            print(f"{doc['id']}: {len(doc['shots'])} shot | {doc['vo']['total_words']} kata "
                  f"| est {doc['vo']['est_seconds']}s")
            continue
        dst.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{dst.name}: {len(doc['shots'])} shot | {doc['vo']['total_words']} kata "
              f"| est {doc['vo']['est_seconds']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
