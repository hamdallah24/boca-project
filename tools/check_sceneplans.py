#!/usr/bin/env python3
"""Validator scene sheet BOCA (production/sceneplans/*.json).

Memaksa seluruh aturan di docs/SCENE_MOTION_SPEC.md dan docs/CODEX_PROMPT_SCENE_VO.md.
Dipakai Codex setelah setiap batch: wajib 0 error sebelum lanjut.

Pemakaian:
    python3 tools/check_sceneplans.py production/sceneplans/
    python3 tools/check_sceneplans.py production/sceneplans/ --strict   # scene wajib ada di kode
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------- kontrak
SCENES_V1 = ["park", "park_evening", "park_sunleft", "sky", "space", "prism",
             "atmosphere", "sunset"]
SCENES_V2 = [
    "bedroom", "bedroom_night", "kitchen", "classroom", "market", "city_top",
    "city_street", "beach", "underwater", "body_inside", "phone_inside", "data_center",
    "neuron_city", "airport", "bank", "money_print", "stock_board", "lake_ice",
    "rain_cloud", "galaxy", "garden", "dark_forest", "house_cutaway", "playground_clock",
]
SCENES_ALLOWED = set(SCENES_V1) | set(SCENES_V2)

EXPRS = {"shock", "neutral", "happy", "confused", "focus", "sleepy"}
POSES = {"stand", "walk", "point", "think", "read", "wave", "cheer", "celebrate", "run"}
LUMI_EXPRS = {"happy", "shock"}
LUMI_POSES = {"float", "wave", "point", "cheer"}
SFX = {"pop", "whoosh", "sparkle", "chime", "boing"}
BANNED = ["adek", "adik", "kakak", "bunda", "sayang", "dedek", "dik"]
MAX_TEXT_WORDS = 14
MAX_CAPTION_WORDS = 9
MAX_ADULT_WORDS = 14
WORDS_MIN, WORDS_MAX = 120, 150
SEC_MIN, SEC_MAX = 42.0, 50.0
WPS = 0.30          # detik per kata
LINE_GAP = 0.16


def words(s: str) -> int:
    return len(re.findall(r"[\w'’-]+", s or ""))


def norm_cam(cam: dict) -> tuple:
    return (tuple(cam.get("fx", ())), tuple(cam.get("fy", ())), tuple(cam.get("z", ())))


def check_episode(path: Path, strict: bool) -> tuple[list[str], dict]:
    errs: list[str] = []
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"JSON tidak bisa dibaca: {e}"], {}

    ep_id = path.stem
    if d.get("id") != ep_id:
        errs.append(f"id '{d.get('id')}' != nama file '{ep_id}'")
    if not d.get("title"):
        errs.append("title kosong")
    if d.get("facts_status") != "pending":
        errs.append(f"facts_status harus 'pending', bukan '{d.get('facts_status')}'")

    shots = d.get("shots") or []
    if not (5 <= len(shots) <= 6):
        errs.append(f"jumlah shot {len(shots)} (harus 5–6)")

    scenes, cams = [], []
    total_words = 0
    lumi_lines = 0
    sfx_total = 0
    prop_shots = 0
    you_count = 0

    for i, s in enumerate(shots, 1):
        tag = f"shot {i}"
        sc = s.get("scene")
        scenes.append(sc)
        if sc not in SCENES_ALLOWED:
            errs.append(f"{tag}: scene '{sc}' tidak dikenal")
        elif strict and sc in SCENES_V2:
            errs.append(f"{tag}: scene '{sc}' belum ada di make_cartoon.py")

        cam = s.get("cam")
        if not isinstance(cam, dict):
            errs.append(f"{tag}: cam wajib ada")
        else:
            for k in ("fx", "fy"):
                v = cam.get(k)
                if not (isinstance(v, (list, tuple)) and len(v) == 2):
                    errs.append(f"{tag}: cam.{k} harus [awal, akhir]")
                elif not all(0.0 <= float(x) <= 1.0 for x in v):
                    errs.append(f"{tag}: cam.{k} harus 0..1")
            z = cam.get("z", [1.0, 1.0])
            if not (isinstance(z, (list, tuple)) and len(z) == 2):
                errs.append(f"{tag}: cam.z harus [awal, akhir]")
            elif not all(1.0 <= float(x) <= 1.6 for x in z):
                errs.append(f"{tag}: cam.z harus 1.0..1.6 (di atas 1.6 blur)")
            cams.append(norm_cam(cam))

        keys = s.get("keys") or []
        if len(keys) < 2:
            errs.append(f"{tag}: minimal 2 key")
        ts = []
        for k in keys:
            if k.get("expr") not in EXPRS:
                errs.append(f"{tag}: expr '{k.get('expr')}' tidak valid")
            if k.get("pose") not in POSES:
                errs.append(f"{tag}: pose '{k.get('pose')}' tidak valid")
            arms = k.get("arms")
            if not isinstance(arms, list) or not arms:
                errs.append(f"{tag}: arms harus list, mis. [0] atau [0,3]")
            elif not all(isinstance(a, int) and 0 <= a <= 4 for a in arms):
                errs.append(f"{tag}: arms hanya 0–4")
            if k.get("prop") not in (None, "prism"):
                errs.append(f"{tag}: prop hanya 'prism'")
            ts.append(float(k.get("t", 0)))
        if ts != sorted(ts):
            errs.append(f"{tag}: key t harus naik")

        for sfx in s.get("sfx") or []:
            if not (isinstance(sfx, (list, tuple)) and len(sfx) == 3):
                errs.append(f"{tag}: sfx harus [offset, nama, gain]")
                continue
            if sfx[1] not in SFX:
                errs.append(f"{tag}: sfx '{sfx[1]}' tidak valid")
            if not (0.0 <= float(sfx[2]) <= 1.0):
                errs.append(f"{tag}: gain sfx harus 0..1")
            sfx_total += 1

        if any(k.get("prop") == "prism" for k in keys):
            prop_shots += 1

        for lk in s.get("lumi") or []:
            if lk.get("expr") not in LUMI_EXPRS:
                errs.append(f"{tag}: lumi expr '{lk.get('expr')}' tidak valid")
            if lk.get("pose") not in LUMI_POSES:
                errs.append(f"{tag}: lumi pose '{lk.get('pose')}' tidak valid")

        dlg = s.get("dialogue") or []
        if not (1 <= len(dlg) <= 2):
            errs.append(f"{tag}: dialogue harus 1–2 baris")
        for line in dlg:
            who = line.get("who")
            if who not in ("boca", "lumi"):
                errs.append(f"{tag}: who '{who}' tidak valid")
            if who == "lumi":
                lumi_lines += 1
            t = line.get("text", "")
            total_words += words(t)
            if words(t) > MAX_TEXT_WORDS:
                errs.append(f"{tag}: text {words(t)} kata (> {MAX_TEXT_WORDS})")
            cap = line.get("caption", "")
            if words(cap) > MAX_CAPTION_WORDS:
                errs.append(f"{tag}: caption {words(cap)} kata (> {MAX_CAPTION_WORDS})")
            if words(line.get("caption_adult", "")) > MAX_ADULT_WORDS:
                errs.append(f"{tag}: caption_adult terlalu panjang")
            low = f"{t} {cap}".lower()
            for b in BANNED:
                if re.search(rf"\b{b}\b", low):
                    errs.append(f"{tag}: kata terlarang '{b}'")
            you_count += len(re.findall(r"\bkamu\b", low))

    uniq = len(set(scenes))
    if uniq < 4:
        errs.append(f"scene unik {uniq} (< 4)")
    if len(set(cams)) < 3:
        errs.append(f"preset kamera unik {len(set(cams))} (< 3)")
    if lumi_lines < 1:
        errs.append("Lumi tidak bicara sama sekali")
    if sfx_total > 4:
        errs.append(f"SFX {sfx_total} (> 4)")
    if prop_shots > 1:
        errs.append(f"prop dipakai di {prop_shots} shot (> 1)")
    if you_count > 1:
        errs.append(f"'kamu' muncul {you_count}× (> 1)")
    if not (WORDS_MIN <= total_words <= WORDS_MAX):
        errs.append(f"total kata {total_words} (harus {WORDS_MIN}–{WORDS_MAX})")

    vo = d.get("vo") or {}
    beats = vo.get("beats") or []
    if len(beats) != len(shots):
        errs.append(f"vo.beats {len(beats)} != jumlah shot {len(shots)}")
    valid_fn = {"hook", "gap", "explain", "analogy", "twist", "payoff", "cta"}
    for b in beats:
        if b.get("function") not in valid_fn:
            errs.append(f"vo.beat function '{b.get('function')}' tidak valid")

    est = total_words * WPS + sum(len(s.get("dialogue") or []) for s in shots) * LINE_GAP
    if not (SEC_MIN <= est <= SEC_MAX):
        errs.append(f"estimasi durasi {est:.1f}s (harus {SEC_MIN:.0f}–{SEC_MAX:.0f}s)")
    if vo.get("total_words") not in (None, total_words):
        errs.append(f"vo.total_words {vo.get('total_words')} != hitungan {total_words}")

    info = {"id": ep_id, "scenes": scenes, "cams": cams, "words": total_words,
            "est": est, "lumi": lumi_lines, "motif": d.get("motion_motif")}
    return errs, info


def cross_checks(infos: dict[str, dict]) -> list[str]:
    errs: list[str] = []
    ids = sorted(infos)
    for a, b in zip(ids, ids[1:]):
        ia, ib = infos[a], infos[b]
        if ia["scenes"][0] == ib["scenes"][0]:
            errs.append(f"{a} & {b}: scene pembuka sama ('{ia['scenes'][0]}')")
        shared = len(set(ia["scenes"]) & set(ib["scenes"]))
        if shared > 2:
            errs.append(f"{a} & {b}: berbagi {shared} scene (> 2)")
        if ia.get("motif") and ia.get("motif") == ib.get("motif"):
            errs.append(f"{a} & {b}: motif sama ({ia['motif']})")

    for i, a in enumerate(ids):
        window = ids[i:i + 5]
        c = Counter(s for x in window for s in set(infos[x]["scenes"]))
        for s, n in c.items():
            if n > 3:
                errs.append(f"jendela {a}..{window[-1]}: scene '{s}' di {n} episode (> 3)")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", default="production/sceneplans")
    ap.add_argument("--strict", action="store_true",
                    help="gagal kalau memakai scene v2 yang belum ada di make_cartoon.py")
    args = ap.parse_args()

    folder = Path(args.folder)
    if not folder.is_absolute():
        folder = ROOT / folder
    files = sorted(folder.glob("BOCA-D*.json"))
    if not files:
        print(f"Tidak ada file di {folder}")
        return 1

    infos: dict[str, dict] = {}
    total_err = 0
    for f in files:
        errs, info = check_episode(f, args.strict)
        total_err += len(errs)
        status = "PASS" if not errs else f"FAIL ({len(errs)})"
        print(f"{status:12} {f.name}")
        for e in errs:
            print(f"             - {e}")
        if info:
            infos[info["id"]] = info

    cross = cross_checks(infos)
    if cross:
        print("\nCek antar-episode:")
        for e in cross:
            print(f"  - {e}")
        total_err += len(cross)

    print(f"\n{len(files)} episode | {total_err} error")
    if infos:
        ws = [i["words"] for i in infos.values()]
        es = [i["est"] for i in infos.values()]
        print(f"kata: min {min(ws)} / rata {sum(ws)/len(ws):.0f} / max {max(ws)}")
        print(f"durasi: min {min(es):.1f}s / rata {sum(es)/len(es):.1f}s / max {max(es):.1f}s")

    if total_err:
        print("\nHASIL: GAGAL — perbaiki dulu sebelum lanjut batch berikutnya.")
        return 1
    print("\nHASIL: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
