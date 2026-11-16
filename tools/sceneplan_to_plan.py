#!/usr/bin/env python3
"""Konversi scene sheet (production/sceneplans) menjadi plan pipeline (production/plans).

Contoh:
    python3 tools/sceneplan_to_plan.py BOCA-D03            # dry-run, tampilkan ringkasan
    python3 tools/sceneplan_to_plan.py BOCA-D03 --write    # tulis production/plans/BOCA-D03.json

Plan yang sudah `approved` TIDAK ditimpa kecuali pakai --force.
Metadata publish (judul, deskripsi, hashtag) diambil dari plan lama kalau ada.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORYBOARDS = ROOT / "production" / "storyboards"
SCENEPLANS = ROOT / "production" / "sceneplans"
PLANS = ROOT / "production" / "plans"

SHOT_FIELDS = ("n", "scene", "cam", "keys", "lumi", "guest", "sfx", "dialogue",
               "props", "layouts", "est_seconds")


def convert(ep_id: str, force: bool, write: bool, keep_status: bool = False) -> int:
    src = STORYBOARDS / f"{ep_id}.json"
    if not src.exists():
        src = SCENEPLANS / f"{ep_id}.json"
    if not src.exists():
        print(f"tidak ada: {src}")
        return 1
    sp = json.loads(src.read_text(encoding="utf-8"))

    dst = PLANS / f"{ep_id}.json"
    old = json.loads(dst.read_text(encoding="utf-8")) if dst.exists() else {}
    if old.get("status") == "approved" and not force:
        print(f"{ep_id}: plan sudah approved — pakai --force kalau memang mau menimpa")
        return 2

    shots = []
    for s in sp["shots"]:
        shot = {k: s[k] for k in SHOT_FIELDS if k in s}
        shot.setdefault("keys", [])
        shot.setdefault("lumi", [])
        shot.setdefault("sfx", [])
        shots.append(shot)

    plan = {
        "id": sp["id"],
        "day": sp["day"],
        "title": sp["title"],
        "series": old.get("series", "KYB"),
        "duration_target": sp.get("duration_target", 45),
        "facts_status": old.get("facts_status", "pending") if keep_status else "pending",
        "cta": old.get("cta", "Tulis di komentar."),
        "status": old.get("status", "draft") if keep_status else "draft",
        "needs_review": old.get("needs_review", True) if keep_status else True,
        "scene_family": sp.get("scene_family", ""),
        "motion_motif": sp.get("motion_motif", ""),
        "vo": sp.get("vo", {}),
        "cast": sp.get("cast", {}),
        "analogy": sp.get("analogy", {}),
        "publish": old.get("publish", {}),
        "shots": shots,
    }
    if keep_status:
        for k in ("facts_verified_at", "facts_note", "approved_at"):
            if k in old:
                plan[k] = old[k]

    print(f"{ep_id}: {len(shots)} shot | scene: {' → '.join(s['scene'] for s in shots)}")
    print(f"  kata {plan['vo'].get('total_words', '?')} | est {plan['vo'].get('est_seconds', '?')}s"
          f" | motif {plan['motion_motif'] or '-'}")
    missing = [s["scene"] for s in shots if s["scene"] not in _code_scenes()]
    if missing:
        print(f"  ⚠ scene belum ada di make_cartoon.py: {', '.join(sorted(set(missing)))}")

    if not write:
        print("  (dry-run — tambahkan --write untuk menyimpan)")
        return 0

    dst.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  -> {dst}")
    return 0


def _code_scenes() -> set[str]:
    try:
        import sys
        sys.path.insert(0, str(ROOT))
        from make_cartoon import SCENES  # noqa: PLC0415
        return set(SCENES)
    except Exception:
        return set()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+", help="mis. BOCA-D03 BOCA-D04")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--keep-status", action="store_true",
                    help="pertahankan facts_status/status/approval dari plan lama")
    args = ap.parse_args()

    rc = 0
    for ep_id in args.ids:
        rc |= convert(ep_id, args.force, args.write, args.keep_status)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
