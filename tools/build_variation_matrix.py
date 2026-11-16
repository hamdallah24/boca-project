#!/usr/bin/env python3
"""Bangun matriks variasi scene 30 episode (constraint solver).

Aturan yang dipaksa:
  1. minimal 4 scene berbeda per episode
  2. pembuka episode N != pembuka episode N-1
  3. dalam 5 episode berurutan, satu scene maksimal muncul di 3 episode
  4. dua episode berurutan maksimal berbagi 2 scene id
  5. motif gerak episode N != episode N-1
  6. minimal 3 preset kamera berbeda per episode
  7. minimal 3 scene tematik per episode

Output:
  docs/variation_matrix.json   (machine readable, dipakai Codex)
  docs/VARIATION_MATRIX_30.md  (tabel manusia)
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "docs" / "variation_matrix.json"
OUT_MD = ROOT / "docs" / "VARIATION_MATRIX_30.md"

SHOTS = 5

LOCKED = {
    1: {"title": "Kenapa uang bisa habis padahal nggak beli apa-apa?",
        "scenes": ["park", "park", "park", "park", "park_evening", "park_evening"],
        "motif": "M1", "cameras": ["C7"] * 6, "note": "SUDAH TAYANG - jangan diubah"},
    2: {"title": "Kenapa langit warnanya biru?",
        "scenes": ["park", "space", "prism", "atmosphere", "sky", "sunset",
                   "park_sunleft", "park_evening"],
        "motif": "M1", "cameras": ["C7"] * 8, "note": "SUDAH DIREKAM - jangan diubah"},
}

# scene tematik (urutan = prioritas; elemen pertama = pembuka pilihan)
THEMES: dict[int, list[str]] = {
    3: ["bedroom_night", "bedroom", "body_inside", "neuron_city"],
    4: ["playground_clock", "sky", "sunset", "park_evening"],
    5: ["airport", "sky", "atmosphere", "sunset"],
    6: ["beach", "underwater", "market", "sunset"],
    7: ["body_inside", "kitchen", "park", "park_evening"],
    8: ["data_center", "house_cutaway", "underwater", "bedroom"],
    9: ["city_top", "phone_inside", "space", "data_center"],
    10: ["phone_inside", "data_center", "city_street", "body_inside"],
    11: ["neuron_city", "classroom", "data_center", "city_top"],
    12: ["house_cutaway", "classroom", "data_center", "city_street"],
    13: ["market", "phone_inside", "bank", "city_street"],
    14: ["phone_inside", "data_center", "bedroom", "city_street"],
    15: ["body_inside", "neuron_city", "park", "sunset"],
    16: ["bedroom_night", "neuron_city", "galaxy", "bedroom"],
    17: ["body_inside", "kitchen", "market", "park"],
    18: ["neuron_city", "classroom", "city_top", "body_inside"],
    19: ["dark_forest", "body_inside", "park_sunleft", "sunset"],
    20: ["lake_ice", "underwater", "sky", "sunset"],
    21: ["rain_cloud", "underwater", "sky", "beach"],
    22: ["market", "city_street", "bank", "kitchen"],
    23: ["city_top", "city_street", "bank", "money_print"],
    24: ["bank", "phone_inside", "market", "city_top"],
    25: ["garden", "bank", "market", "sunset"],
    26: ["money_print", "bank", "market", "city_street", "stock_board"],
    27: ["stock_board", "data_center", "city_top", "phone_inside"],
    28: ["city_street", "city_top", "classroom", "sunset"],
    29: ["space", "galaxy", "city_top", "park"],
    30: ["galaxy", "space", "park_evening", "sky"],
}

ACCENTS = ["park", "park_sunleft", "park_evening", "sky", "sunset",
           "classroom", "city_top", "space", "market", "city_street"]

TITLES = {
    3: "Kenapa kita harus tidur?",
    4: "Kenapa waktu terasa cepat kalau sedang senang?",
    5: "Kenapa pesawat yang berat bisa terbang?",
    6: "Kenapa laut rasanya asin?",
    7: "Kenapa kita bisa cegukan?",
    8: "Internet itu sebenarnya tinggal di mana?",
    9: "Bagaimana HP bisa tahu lokasi kita?",
    10: "Kenapa baterai HP bisa habis?",
    11: "Bagaimana AI bisa menjawab pertanyaan manusia?",
    12: "Kenapa Wi-Fi bisa menembus tembok?",
    13: "Bagaimana uang digital berpindah?",
    14: "Apa yang terjadi ketika kita menghapus foto?",
    15: "Kenapa jantung nggak pernah berhenti bekerja?",
    16: "Kenapa kita bisa bermimpi?",
    17: "Kenapa perut berbunyi saat lapar?",
    18: "Bagaimana otak menyimpan ingatan?",
    19: "Kenapa kita bisa merasa takut?",
    20: "Kenapa es bisa mengapung di air?",
    21: "Bagaimana hujan bisa turun dari langit?",
    22: "Kenapa harga barang bisa naik?",
    23: "Kenapa negara bisa punya utang?",
    24: "Kenapa bank mau meminjamkan uang?",
    25: "Kenapa orang kaya bisa semakin kaya?",
    26: "Kenapa uang harus dicetak oleh negara?",
    27: "Apa yang membuat harga saham naik turun?",
    28: "Kenapa kita harus membayar pajak?",
    29: "Apa yang terjadi kalau Bumi tiba-tiba berhenti berputar?",
    30: "Apakah alam semesta punya ujung?",
}

MOTIFS = {
    "M1": "walk-in reveal", "M2": "point-explain", "M3": "think→lightbulb",
    "M4": "prop demo", "M5": "run-chase", "M6": "wave-greet",
    "M7": "celebrate", "M8": "sleepy→focus",
}
CAM_PRESETS = {
    "C1": "push-in", "C2": "pull-out", "C3": "pan kiri", "C4": "pan kanan",
    "C5": "tilt up", "C6": "tilt down", "C7": "static wide", "C8": "push-in kuat",
    "C9": "drift diagonal",
}


def window_count(s: str, day: int, assigned: dict[int, list[str]]) -> int:
    """Berapa episode di jendela 5-hari (berakhir di `day`) yang memakai scene s."""
    return sum(1 for d in range(max(3, day - 4), day) if s in set(assigned.get(d, [])))


def blocked(s: str, day: int, assigned: dict[int, list[str]], chosen: list[str]) -> bool:
    if window_count(s, day, assigned) >= 3:          # aturan 3
        return True
    shared = len(set(chosen) & set(assigned.get(day - 1, [])))
    if s in assigned.get(day - 1, []) and shared >= 2:  # aturan 4
        return True
    return False


def pick_scenes(day: int, assigned: dict[int, list[str]]) -> list[str]:
    themes = THEMES[day]
    prev_open = (assigned.get(day - 1) or [None])[0]
    chosen: list[str] = []

    # 1. pembuka: scene tematik pertama yang boleh
    for s in themes:
        if s == prev_open or blocked(s, day, assigned, chosen):
            continue
        chosen.append(s)
        break
    if not chosen:
        for s in ACCENTS:
            if s != prev_open and not blocked(s, day, assigned, chosen):
                chosen.append(s)
                break
    if not chosen:
        chosen.append(themes[0])

    # 2. isi scene tematik unik (target 4 unik, minimal 3 tematik)
    for s in themes:
        if len(set(chosen)) >= 4:
            break
        if s in chosen or blocked(s, day, assigned, chosen):
            continue
        chosen.append(s)

    # 3. aksen kalau masih kurang unik
    for s in ACCENTS:
        if len(set(chosen)) >= 4:
            break
        if s in chosen or blocked(s, day, assigned, chosen):
            continue
        chosen.append(s)

    # 4. lengkapi jumlah shot (boleh ulang scene, jangan sampai kurang)
    pool = themes + [s for s in ACCENTS if s not in themes]
    for s in pool:
        if len(chosen) >= SHOTS:
            break
        if blocked(s, day, assigned, chosen):
            continue
        if chosen.count(s) >= 2:
            continue
        chosen.append(s)
    for s in pool:
        if len(chosen) >= SHOTS:
            break
        chosen.append(s)

    return chosen[:SHOTS]


def pick_cameras(day: int, n: int) -> list[str]:
    keys = list(CAM_PRESETS)
    out = [keys[(day * 2 + i * 3) % len(keys)] for i in range(n)]
    i = 0
    while len(set(out)) < 3:
        out[i % n] = keys[(i * 5 + day) % len(keys)]
        i += 1
    return out


def pick_motif(day: int, prev: str | None) -> str:
    keys = list(MOTIFS)
    idx = (day - 1) % len(keys)
    m = keys[idx]
    if m == prev:
        m = keys[(idx + 1) % len(keys)]
    return m


def validate(matrix: dict[str, dict]) -> list[str]:
    errs: list[str] = []
    by_day = {int(k): v for k, v in matrix.items()}
    days = sorted(by_day)

    for d in days:
        if d in LOCKED:
            continue
        e = by_day[d]
        if len(set(e["scenes"])) < 4:
            errs.append(f"D{d:02d}: scene unik {len(set(e['scenes']))} < 4")
        if len(set(e["cameras"])) < 3:
            errs.append(f"D{d:02d}: preset kamera unik {len(set(e['cameras']))} < 3")
        thematic = len(set(e["scenes"]) & set(THEMES[d]))
        if thematic < 3:
            errs.append(f"D{d:02d}: scene tematik {thematic} < 3")
        if d - 1 in by_day:
            if e["scenes"][0] == by_day[d - 1]["scenes"][0]:
                errs.append(f"D{d:02d}: pembuka sama dengan D{d-1:02d}")
            if e["motif"] == by_day[d - 1]["motif"]:
                errs.append(f"D{d:02d}: motif sama dengan D{d-1:02d}")
            shared = len(set(e["scenes"]) & set(by_day[d - 1]["scenes"]))
            if shared > 2:
                errs.append(f"D{d:02d}: berbagi {shared} scene dengan D{d-1:02d} (>2)")

    for d in days:
        window = [by_day[x] for x in range(d, min(d + 5, 31)) if x in by_day and x not in LOCKED]
        c = Counter(s for e in window for s in set(e["scenes"]))
        for s, n in c.items():
            if n > 3:
                errs.append(f"jendela D{d:02d}-D{min(d+4,30):02d}: scene '{s}' di {n} episode (>3)")
    return errs


def main() -> int:
    matrix: dict[str, dict] = {}
    assigned: dict[int, list[str]] = {}
    prev_motif: str | None = None

    for d in range(1, 31):
        if d in LOCKED:
            e = dict(LOCKED[d])
            matrix[f"{d:02d}"] = e
            assigned[d] = e["scenes"]
            prev_motif = e["motif"]
            continue

        scenes = pick_scenes(d, assigned)
        motif = pick_motif(d, prev_motif)
        matrix[f"{d:02d}"] = {"title": TITLES[d], "scenes": scenes, "motif": motif,
                              "cameras": pick_cameras(d, len(scenes))}
        assigned[d] = scenes
        prev_motif = motif

    errs = validate(matrix)
    OUT_JSON.write_text(json.dumps(matrix, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Matriks Variasi 30 Episode",
        "",
        "Dokumen ini **wajib dipatuhi** saat menulis scene sheet. Kalau sebuah ide butuh",
        "scene di luar urutan ini, boleh — tapi aturan variasi di `SCENE_MOTION_SPEC.md`",
        "tetap harus lulus validator.",
        "",
        "| Hari | Judul | Urutan scene | Motif gerak | Kamera |",
        "|---|---|---|---|---|",
    ]
    for d in range(1, 31):
        e = matrix[f"{d:02d}"]
        seq = " → ".join(f"`{s}`" for s in e["scenes"])
        motif = f"{e['motif']} {MOTIFS[e['motif']]}"
        cams = " · ".join(e["cameras"])
        note = " *(terkunci)*" if d in LOCKED else ""
        lines.append(f"| {d:02d} | {e['title']}{note} | {seq} | {motif} | {cams} |")

    lines += ["", "## Legenda kamera", "",
              "| Kode | Nama | fx | fy | z |", "|---|---|---|---|---|"]
    cam_vals = {
        "C1": ("[0.46, 0.50]", "[0.44, 0.46]", "[1.00, 1.25]"),
        "C2": ("[0.50, 0.46]", "[0.46, 0.42]", "[1.30, 1.00]"),
        "C3": ("[0.62, 0.32]", "[0.45, 0.45]", "[1.05, 1.05]"),
        "C4": ("[0.32, 0.62]", "[0.45, 0.45]", "[1.05, 1.05]"),
        "C5": ("[0.45, 0.45]", "[0.62, 0.30]", "[1.00, 1.06]"),
        "C6": ("[0.45, 0.45]", "[0.28, 0.60]", "[1.06, 1.00]"),
        "C7": ("[0.30, 0.70]", "[0.35, 0.62]", "[1.00, 1.00]"),
        "C8": ("[0.47, 0.50]", "[0.45, 0.45]", "[1.10, 1.45]"),
        "C9": ("[0.38, 0.56]", "[0.38, 0.52]", "[1.12, 1.12]"),
    }
    for k, v in cam_vals.items():
        lines.append(f"| {k} | {CAM_PRESETS[k]} | `{v[0]}` | `{v[1]}` | `{v[2]}` |")

    lines += ["", "## Legenda motif", "", "| Kode | Pola |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in MOTIFS.items()]
    lines.append("")
    if errs:
        lines += ["> ⚠️ **PELANGGARAN:**", ""] + [f"> - {e}" for e in errs]
    else:
        lines.append("> ✅ Semua aturan variasi terpenuhi (0 pelanggaran).")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"matrix -> {OUT_JSON}")
    print(f"tabel  -> {OUT_MD}")
    print(f"pelanggaran: {len(errs)}")
    for e in errs[:20]:
        print("  -", e)
    return 0 if not errs else 1


if __name__ == "__main__":
    raise SystemExit(main())
