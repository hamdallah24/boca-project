#!/usr/bin/env python3
"""Validator storyboard BOCA (production/storyboards/BOCA-D*.json).

Memaksa aturan:
  docs/SCENE_MOTION_SPEC.md      (kontrak render)
  docs/STORY_ARCHITECTURE.md     (6 beat, hook, analogi, peran dialog)
  docs/CHARACTER_SYSTEM.md       (cast, tamu, suara)

Pemakaian:
    python3 tools/check_storyboards.py production/storyboards/
    python3 tools/check_storyboards.py production/storyboards/ --strict
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

SCENES_V1 = ["park", "park_evening", "park_sunleft", "sky", "space", "prism",
             "atmosphere", "sunset"]
SCENES_V2 = [
    "bedroom", "bedroom_night", "kitchen", "classroom", "market", "city_top",
    "city_street", "beach", "underwater", "body_inside", "phone_inside", "data_center",
    "neuron_city", "airport", "bank", "money_print", "stock_board", "lake_ice",
    "rain_cloud", "galaxy", "garden", "dark_forest", "house_cutaway", "playground_clock",
    "mountain_sunset", "airport_svg", "sky_flight",
]
SCENES_ALLOWED = set(SCENES_V1) | set(SCENES_V2)


def implemented_scenes() -> set | None:
    """Scene yang benar-benar ada di make_cartoon.py (registry SCENES)."""
    try:
        sys.path.insert(0, str(ROOT))
        from make_cartoon import SCENES  # noqa: PLC0415
        from scene_svg import SCENE_SVG  # noqa: PLC0415
        return set(SCENES.keys()) | set(SCENE_SVG.keys())
    except Exception:  # noqa: BLE001
        return None


EXPRS = {"shock", "neutral", "happy", "confused", "focus", "sleepy"}
POSES = {"stand", "walk", "point", "think", "read", "wave", "cheer", "celebrate", "run"}
GUEST_EXPRS = {"neutral", "happy", "shock", "confused"}
GUEST_POSES = {"stand", "point", "wave"}
LUMI_EXPRS = {"happy", "shock"}
LUMI_POSES = {"float", "wave", "point", "cheer"}
SFX = {"pop", "whoosh", "sparkle", "chime", "boing"}
GUESTS = {"ardi", "bu_ratna", "pak_darno", "sari", "dokter_nia", "kak_bima"}
HOOKS = {"H1", "H2", "H3", "H4", "H5", "H6"}
BEATS = ["hook", "setup", "explain", "twist", "payoff", "cta"]
BANNED = ["adek", "adik", "kakak", "bunda", "sayang", "dedek", "dik", "teman-teman"]

TIERS = {
    45: {"shots": (5, 7), "words": (135, 150), "sec": (41, 49)},
    60: {"shots": (7, 9), "words": (180, 200), "sec": (56, 64)},
    90: {"shots": (9, 12), "words": (270, 300), "sec": (86, 94)},
}

MAX_TEXT, MAX_CAP, MAX_ADULT = 14, 9, 14
WPS, LINE_GAP = 0.30, 0.16

# Parameter rendering pipeline (boca_pipeline.py)
LEAD_IN, TAIL = 0.22, 0.20
TTS_SEC_PER_WORD = 0.4895   # Gemini Puck/Aoede; tanpa atempo


def words(s: str) -> int:
    return len(re.findall(r"[\w'’-]+", s or ""))


def norm_cam(c: dict) -> tuple:
    return (tuple(c.get("fx", ())), tuple(c.get("fy", ())), tuple(c.get("z", ())))


def check(path: Path, strict: bool) -> tuple[list[str], dict]:
    errs: list[str] = []
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"JSON rusak: {e}"], {}

    ep = path.stem
    if d.get("id") != ep:
        errs.append(f"id '{d.get('id')}' != '{ep}'")
    for f in ("title", "series", "logline", "production_notes"):
        if not d.get(f):
            errs.append(f"{f} kosong")
    if d.get("facts_status") != "pending":
        errs.append(f"facts_status harus 'pending' (sekarang '{d.get('facts_status')}')")

    dur = d.get("duration_target")
    if dur not in TIERS:
        return errs + [f"duration_target {dur} bukan 45/60/90"], {}
    tier = TIERS[dur]

    if int(d.get("day", 1)) >= 5:
        for f in ("scene_family", "motion_motif"):
            if not str(d.get(f) or "").strip():
                errs.append(f"{f} wajib diisi (rulebook motion)")

    # ---------------- hook
    hook = d.get("hook") or {}
    if hook.get("pattern") not in HOOKS:
        errs.append(f"hook.pattern '{hook.get('pattern')}' tidak valid (H1–H6)")
    for f in ("claim", "gap", "promise"):
        if not hook.get(f):
            errs.append(f"hook.{f} kosong")
    if float(hook.get("seconds", 99)) > (4 if dur == 90 else 3):
        errs.append(f"hook {hook.get('seconds')}s terlalu panjang untuk tier {dur}s")
    # D04 ke atas: hook wajib dibuka pertanyaan ke penonton, bukan pernyataan.
    if int(d.get("day", 1)) >= 4:
        first = ((d.get("shots") or [{}])[0].get("dialogue") or [{}])[0]
        if not str(first.get("text", "")).strip().endswith("?"):
            errs.append("hook: kalimat pertama harus pertanyaan (diakhiri '?')")
        if first.get("who") != "boca":
            errs.append("hook: pertanyaan pembuka harus diucapkan boca")

    # ---------------- cast
    cast = d.get("cast") or {}
    guest = cast.get("guest")
    if cast.get("host") != "boca":
        errs.append("cast.host harus 'boca'")
    if cast.get("sidekick") != "lumi":
        errs.append("cast.sidekick harus 'lumi'")
    if guest is not None and guest not in GUESTS:
        errs.append(f"cast.guest '{guest}' tidak dikenal (lihat CHARACTER_SYSTEM.md)")
    speakers = {"boca", "lumi"} | ({guest} if guest else set())

    # ---------------- analogi
    an = d.get("analogy") or {}
    if not an.get("source"):
        errs.append("analogy.source kosong")
    maps = an.get("maps") or []
    if len(maps) < 2:
        errs.append(f"analogy.maps {len(maps)} (< 2 pemetaan)")
    for m in maps:
        if not m.get("real") or not m.get("analogy"):
            errs.append("analogy.maps ada entri kosong")
    if not an.get("why_it_works"):
        errs.append("analogy.why_it_works kosong")

    # ---------------- shots
    shots = d.get("shots") or []
    lo, hi = tier["shots"]
    if not (lo <= len(shots) <= hi):
        errs.append(f"jumlah shot {len(shots)} (tier {dur}s: {lo}–{hi})")
    if an.get("line_shot") and not (1 <= int(an["line_shot"]) <= len(shots)):
        errs.append(f"analogy.line_shot {an['line_shot']} di luar 1..{len(shots)}")

    scenes, cams = [], []
    total_words = lumi_lines = boca_lines = total_lines = sfx_total = prop_shots = you_count = 0
    spotlight_total = 0
    guest_shots = guest_lines = 0
    seen_beats: list[str] = []

    for i, s in enumerate(shots, 1):
        tag = f"shot {i}"
        sc = s.get("scene")
        scenes.append(sc)
        if sc not in SCENES_ALLOWED:
            errs.append(f"{tag}: scene '{sc}' tidak dikenal")
        elif strict:
            impl = implemented_scenes()
            if impl is not None and sc not in impl:
                errs.append(f"{tag}: scene '{sc}' belum ada di make_cartoon.py")

        beat = s.get("beat")
        if beat not in BEATS:
            errs.append(f"{tag}: beat '{beat}' tidak valid")
        else:
            seen_beats.append(beat)

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
                errs.append(f"{tag}: cam.z harus 1.0..1.6")
            cams.append(norm_cam(cam))

        keys = s.get("keys") or []
        if len(keys) < 2:
            errs.append(f"{tag}: minimal 2 key")
        ts = [float(k.get("t", 0)) for k in keys]
        if ts != sorted(ts):
            errs.append(f"{tag}: key t harus naik")
        for k in keys:
            if k.get("expr") not in EXPRS:
                errs.append(f"{tag}: expr '{k.get('expr')}' tidak valid")
            if k.get("pose") not in POSES:
                errs.append(f"{tag}: pose '{k.get('pose')}' tidak valid")
            arms = k.get("arms")
            if not isinstance(arms, list) or not arms:
                errs.append(f"{tag}: arms harus list")
            elif not all(isinstance(a, int) and 0 <= a <= 4 for a in arms):
                errs.append(f"{tag}: arms hanya 0–4")
            if k.get("prop") not in (None, "prism"):
                errs.append(f"{tag}: prop hanya 'prism'")
        if any(k.get("prop") == "prism" for k in keys):
            prop_shots += 1

        for lk in s.get("lumi") or []:
            if lk.get("expr") not in LUMI_EXPRS:
                errs.append(f"{tag}: lumi expr '{lk.get('expr')}' tidak valid")
            if lk.get("pose") not in LUMI_POSES:
                errs.append(f"{tag}: lumi pose '{lk.get('pose')}' tidak valid")

        gkeys = s.get("guest")
        if guest:
            if not isinstance(gkeys, list):
                errs.append(f"{tag}: field 'guest' wajib ada (boleh [])")
            elif gkeys:
                guest_shots += 1
                for gk in gkeys:
                    if gk.get("expr") not in GUEST_EXPRS:
                        errs.append(f"{tag}: guest expr '{gk.get('expr')}' tidak valid")
                    if gk.get("pose") not in GUEST_POSES:
                        errs.append(f"{tag}: guest pose '{gk.get('pose')}' tidak valid")
        elif gkeys:
            errs.append(f"{tag}: ada keyframe guest padahal cast.guest null")

        # ---- props / callouts (opsional, schema v4.1)
        for pr in s.get("props") or []:
            if not isinstance(pr, dict):
                errs.append(f"{tag}: props harus objek")
                continue
            try:
                from props import ids as prop_ids  # noqa: PLC0415
                from props_svg import PROPS as svg_props  # noqa: PLC0415
                valid_ids = set(prop_ids()) | set(svg_props)
            except Exception:  # noqa: BLE001
                valid_ids = []
            if valid_ids and pr.get("id") not in valid_ids:
                errs.append(f"{tag}: prop id '{pr.get('id')}' tidak dikenal")
            if not (0.0 <= float(pr.get("t_in", 0)) < float(pr.get("t_out", 1))):
                errs.append(f"{tag}: prop t_in harus < t_out")
            ph = int(pr.get("h", 220))
            if not (180 <= ph <= 520):
                errs.append(f"{tag}: prop h 180–520 px")
            elif pr.get("beat") and not (280 <= ph <= 520):
                errs.append(f"{tag}: prop beat h 280–520 px")
            if pr.get("loupe_from") is not None:
                lf = pr["loupe_from"]
                if not (isinstance(lf, (list, tuple)) and len(lf) == 2):
                    errs.append(f"{tag}: loupe_from harus [x, y]")

        # ---- layouts per beat (schema v4.3)
        lys = s.get("layouts")
        if lys is not None:
            if not isinstance(lys, list) or not lys:
                errs.append(f"{tag}: layouts harus list tidak kosong")
            else:
                est = float(s.get("est_seconds", 6.0))
                modes = {"WIDE_STAGE", "INFOGRAPHIC_CARD", "CLOSEUP_EMPHASIS",
                         "SPOTLIGHT_EFFECT"}
                dlg = s.get("dialogue") or []
                strict = int(d.get("day", 1)) >= 5
                prev_end = 0.0
                prev_mode = None
                any_on_line = False
                for i, ly in enumerate(lys):
                    if not isinstance(ly, dict):
                        errs.append(f"{tag}: layout[{i}] harus objek")
                        continue
                    mode = ly.get("mode")
                    if mode not in modes:
                        errs.append(f"{tag}: layout[{i}] mode '{mode}' tidak valid")
                    if mode == prev_mode:
                        errs.append(f"{tag}: layout[{i}] {mode} berurutan "
                                    f"(dilarang rulebook motion)")
                    prev_mode = mode

                    on_line = ly.get("on_line")
                    if on_line is not None:
                        any_on_line = True
                        if not isinstance(on_line, int) or not (0 <= on_line < len(dlg)):
                            errs.append(f"{tag}: layout[{i}] on_line di luar dialog")
                        to_line = ly.get("to_line", on_line)
                        if isinstance(on_line, int) and isinstance(to_line, int) and to_line < on_line:
                            errs.append(f"{tag}: layout[{i}] to_line < on_line")
                        if strict and not ly.get("to_line") and mode != "CLOSEUP_EMPHASIS":
                            pass  # satu baris sah; durasi di-cap renderer
                    elif strict:
                        errs.append(f"{tag}: layout[{i}] wajib on_line (rulebook motion)")
                    else:
                        try:
                            f0, f1 = float(ly.get("from", -1)), float(ly.get("to", -1))
                        except (TypeError, ValueError):
                            errs.append(f"{tag}: layout[{i}] from/to harus angka")
                            continue
                        if f0 < -0.01 or f1 <= f0:
                            errs.append(f"{tag}: layout[{i}] rentang tidak valid")
                        if abs(f0 - prev_end) > 0.05:
                            errs.append(f"{tag}: layout[{i}] mulai {f0:.2f}s, "
                                        f"celah/overlap dari {prev_end:.2f}s")
                        if f1 - f0 > 3.8:
                            errs.append(f"{tag}: layout[{i}] {f1 - f0:.1f}s > 3.8s")
                        prev_end = f1

                    if mode == "INFOGRAPHIC_CARD":
                        card = ly.get("card")
                        if not isinstance(card, dict):
                            errs.append(f"{tag}: layout[{i}] card wajib objek")
                        elif card.get("kind") not in ("compare", "checklist", "steps"):
                            errs.append(f"{tag}: card.kind harus compare/checklist/steps")
                        elif card.get("kind") == "compare":
                            for side in ("left", "right"):
                                sd = card.get(side)
                                if not isinstance(sd, dict):
                                    errs.append(f"{tag}: card.{side} wajib objek")
                                elif not isinstance(sd.get("value"), (int, float)):
                                    errs.append(f"{tag}: card.{side}.value harus angka")

                    tgt = ly.get("target") or ly.get("focus")
                    if tgt == "guest":
                        tgt = guest
                    if mode == "SPOTLIGHT_EFFECT":
                        spotlight_total += 1
                        dim = float(ly.get("dim", 0.62))
                        if not (0.0 <= dim <= 0.9):
                            errs.append(f"{tag}: spotlight dim 0..0.9")
                        if tgt not in speakers:
                            errs.append(f"{tag}: spotlight target bukan cast")
                    if mode == "CLOSEUP_EMPHASIS":
                        z = float(ly.get("z", 1.45))
                        if not (1.3 <= z <= 1.6):
                            errs.append(f"{tag}: closeup z 1.3–1.6")
                        if strict:
                            if not (ly.get("target") or ly.get("focus")):
                                errs.append(f"{tag}: closeup wajib target "
                                            f"(boca/lumi/guest)")
                            elif tgt not in speakers:
                                errs.append(f"{tag}: closeup target bukan cast")
                            if isinstance(on_line, int) and 0 <= on_line < len(dlg):
                                who = dlg[on_line].get("who")
                                if tgt != who:
                                    errs.append(f"{tag}: closeup target '{tgt}' != "
                                                f"speaker '{who}' baris {on_line}")

                if not any_on_line and abs(prev_end - est) > 0.25:
                    errs.append(f"{tag}: layout berakhir {prev_end:.2f}s "
                                f"!= shot {est:.2f}s")
                has_props = bool(s.get("props"))
                has_keys = len(s.get("keys") or []) >= 2
                if est >= 6.0 and len(lys) < 2 and not (has_props or has_keys):
                    errs.append(f"{tag}: shot {est:.1f}s butuh >= 2 layout "
                                f"atau prop/key beranimasi")

        for sfx in s.get("sfx") or []:
            if not (isinstance(sfx, (list, tuple)) and len(sfx) == 3):
                errs.append(f"{tag}: sfx harus [offset, nama, gain]")
                continue
            if sfx[1] not in SFX:
                errs.append(f"{tag}: sfx '{sfx[1]}' tidak valid")
            if not (0.0 <= float(sfx[2]) <= 1.0):
                errs.append(f"{tag}: gain sfx 0..1")
            sfx_total += 1

        dlg = s.get("dialogue") or []
        if not (1 <= len(dlg) <= 2):
            errs.append(f"{tag}: dialogue harus 1–2 baris")
        for line in dlg:
            who = line.get("who")
            if who not in speakers:
                errs.append(f"{tag}: who '{who}' tidak ada di cast")
            total_lines += 1
            if who == "lumi":
                lumi_lines += 1
            elif who == "boca":
                boca_lines += 1
            if guest and who == guest:
                guest_lines += 1
            t = line.get("text", "")
            total_words += words(t)
            if words(t) > MAX_TEXT:
                errs.append(f"{tag}: text {words(t)} kata (> {MAX_TEXT})")
            if words(line.get("caption", "")) > MAX_CAP:
                errs.append(f"{tag}: caption {words(line.get('caption',''))} kata (> {MAX_CAP})")
            if words(line.get("caption_adult", "")) > MAX_ADULT:
                errs.append(f"{tag}: caption_adult terlalu panjang")
            low = f"{t} {line.get('caption','')}".lower()
            for b in BANNED:
                if re.search(rf"\b{re.escape(b)}\b", low):
                    errs.append(f"{tag}: kata terlarang '{b}'")
            you_count += len(re.findall(r"\bkamu\b", low))

    uniq = len(set(scenes))
    if uniq < 4:
        errs.append(f"scene unik {uniq} (< 4)")
    if len(set(cams)) < 3:
        errs.append(f"preset kamera unik {len(set(cams))} (< 3)")
    if lumi_lines < 1:
        errs.append("Lumi tidak bicara")
    if total_lines:
        bshare = boca_lines / total_lines
        lshare = lumi_lines / total_lines
        if bshare < 0.50:
            errs.append(f"porsi Boca {bshare:.0%} (< 50%) — Boca harus memegang alur")
        if lshare > 0.30:
            errs.append(f"porsi Lumi {lshare:.0%} (> 30%) — Lumi bereaksi, bukan menjelaskan")
    if sfx_total > 4:
        errs.append(f"SFX {sfx_total} (> 4)")
    if prop_shots > 1:
        errs.append(f"prop dipakai {prop_shots} shot (> 1)")
    if you_count > 1:
        errs.append(f"'kamu' muncul {you_count}× (> 1)")

    if guest:
        if guest_shots < 2:
            errs.append(f"tamu '{guest}' muncul di {guest_shots} shot (< 2)")
        if not (1 <= guest_lines <= 3):
            errs.append(f"tamu bicara {guest_lines} baris (harus 1–3)")

    for b in BEATS:
        if b not in seen_beats:
            errs.append(f"beat '{b}' tidak ada di shot mana pun")

    structure = d.get("structure") or []
    if len(structure) != len(shots):
        errs.append(f"structure {len(structure)} entri != {len(shots)} shot")
    for st in structure:
        if st.get("beat") not in BEATS:
            errs.append(f"structure beat '{st.get('beat')}' tidak valid")
        if not (1 <= int(st.get("shot", 0)) <= len(shots)):
            errs.append(f"structure shot {st.get('shot')} di luar rentang")

    wlo, whi = tier["words"]
    if int(d.get("day", 1)) >= 5 and spotlight_total > 2:
        errs.append(f"spotlight {spotlight_total} (> 2/episode, rulebook motion)")

    if not (wlo <= total_words <= whi):
        errs.append(f"total kata {total_words} (tier {dur}s: {wlo}–{whi})")

    est = total_words * WPS + sum(len(s.get("dialogue") or []) for s in shots) * LINE_GAP
    slo, shi = tier["sec"]
    if not (slo <= est <= shi):
        errs.append(f"estimasi {est:.1f}s (tier {dur}s: {slo}–{shi}s)")

    vo = d.get("vo") or {}
    if vo.get("total_words") not in (None, total_words):
        errs.append(f"vo.total_words {vo.get('total_words')} != {total_words}")
    beats = vo.get("beats") or []
    if len(beats) != len(shots):
        errs.append(f"vo.beats {len(beats)} != {len(shots)} shot")
    vo_funcs = set(BEATS) | {"gap", "analogy"}
    for b in beats:
        if b.get("function") not in vo_funcs:
            errs.append(f"vo.beat function '{b.get('function')}' tidak valid")

    needs = d.get("asset_needs") or []
    if not needs:
        errs.append("asset_needs kosong")
    for n in needs:
        if n.get("type") not in ("scene", "character", "voice"):
            errs.append(f"asset_needs type '{n.get('type')}' tidak valid")
        if n.get("type") == "scene" and n.get("id") not in SCENES_ALLOWED:
            errs.append(f"asset_needs scene '{n.get('id')}' tidak dikenal")
        if n.get("type") == "character" and n.get("id") not in ({"boca", "lumi"} | GUESTS):
            errs.append(f"asset_needs character '{n.get('id')}' tidak dikenal")

    # --- realism: panjang naskah vs rate TTS nyata -------------------------
    # Edge dinaikkan di sumbernya (EDGE_RATE +47%) = 0.4895 / 1.47 = 0.333 s/kata.
    # Tidak ada atempo: kalau narasi lebih panjang dari tier, video dibiarkan
    # lebih panjang. Jadi ini catatan informasi, bukan error.
    sec_per_word = TTS_SEC_PER_WORD
    n_lines = sum(len(s.get("dialogue") or []) for s in shots)
    overhead = len(shots) * (LEAD_IN + TAIL) + max(n_lines - len(shots), 0) * LINE_GAP
    speech = total_words * sec_per_word
    final_dur = speech + overhead
    tempo = 1.0
    tempo_note = ""
    if final_dur > dur + 2.5:
        tempo_note = (f"naskah {total_words} kata -> narasi ~{final_dur:.0f}s "
                      f"(target {dur}s, video dibiarkan lebih panjang)")

    info = {"id": ep, "scenes": scenes, "cams": cams, "words": total_words,
            "est": est, "guest": guest, "hook": hook.get("pattern"),
            "analogy": an.get("source", ""), "dur": dur,
            "tempo": tempo, "final_dur": final_dur, "tempo_note": tempo_note}
    return errs, info


def cross(infos: dict[str, dict]) -> list[str]:
    errs: list[str] = []
    ids = sorted(infos)
    for a, b in zip(ids, ids[1:]):
        ia, ib = infos[a], infos[b]
        if ia["scenes"][0] == ib["scenes"][0]:
            errs.append(f"{a} & {b}: pembuka sama ('{ia['scenes'][0]}')")
        shared = len(set(ia["scenes"]) & set(ib["scenes"]))
        if shared > 2:
            errs.append(f"{a} & {b}: berbagi {shared} scene (> 2)")
        if ia["hook"] and ia["hook"] == ib["hook"]:
            errs.append(f"{a} & {b}: pola hook sama ({ia['hook']})")

    for i, a in enumerate(ids):
        w = ids[i:i + 5]
        c = Counter(s for x in w for s in set(infos[x]["scenes"]))
        for s, n in c.items():
            if n > 3:
                errs.append(f"jendela {a}..{w[-1]}: scene '{s}' di {n} episode (> 3)")

    seen: dict[str, str] = {}
    for x in ids:
        src = (infos[x].get("analogy") or "").strip().lower()
        if not src:
            continue
        if src in seen:
            errs.append(f"{x}: analogi sama dengan {seen[src]} ('{src[:40]}')")
        else:
            seen[src] = x
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", default="production/storyboards")
    ap.add_argument("--strict", action="store_true",
                    help="gagal kalau scene v2 belum ada di make_cartoon.py")
    args = ap.parse_args()

    folder = Path(args.folder)
    if not folder.is_absolute():
        folder = ROOT / folder
    files = sorted(folder.glob("BOCA-D*.json"))
    if not files:
        print(f"Tidak ada storyboard di {folder}")
        return 1

    infos: dict[str, dict] = {}
    total = 0
    for f in files:
        errs, info = check(f, args.strict)
        total += len(errs)
        print(f"{'PASS' if not errs else f'FAIL ({len(errs)})':12} {f.name}")
        for e in errs:
            print(f"             - {e}")
        if info:
            infos[info["id"]] = info

    xerr = cross(infos)
    if xerr:
        print("\nCek antar-episode:")
        for e in xerr:
            print(f"  - {e}")
        total += len(xerr)

    notes = [(i, infos[i]["tempo_note"]) for i in sorted(infos) if infos[i].get("tempo_note")]
    if notes:
        print("\nCatatan tempo (naskah panjang -> suara dipercepat saat render):")
        for i, n in notes:
            print(f"  - {i}: {n}")

    print(f"\n{len(files)} episode | {total} error")
    if infos:
        ws = [i["words"] for i in infos.values()]
        es = [i["est"] for i in infos.values()]
        print(f"kata: min {min(ws)} / rata {sum(ws)/len(ws):.0f} / max {max(ws)}")
        print(f"durasi: min {min(es):.1f}s / rata {sum(es)/len(es):.1f}s / max {max(es):.1f}s")
    print("\nHASIL: " + ("PASS" if not total else "GAGAL"))
    return 0 if not total else 1


if __name__ == "__main__":
    raise SystemExit(main())
