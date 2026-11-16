#!/usr/bin/env python3
"""upgrade_storyboards_v43.py — isi `layouts`/`props` v4.3 untuk episode lama.

Aturan:
- shot >= 6 s wajib >= 2 layout, tiap rentang <= 3,8 s, menutup [0, est_seconds]
- kartu infografis hanya berisi langkah yang sudah ada di naskah
- prop beat h 280–480, diletakkan di band atas y 250–340
- menulis ke storyboard DAN plan (plan = sumber render daily_build)

Pemakaian:
    python3 tools/upgrade_storyboards_v43.py --dry-run
    python3 tools/upgrade_storyboards_v43.py --episodes BOCA-D05,BOCA-D06
    python3 tools/upgrade_storyboards_v43.py            # semua yang belum punya layout
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORY = ROOT / "production" / "storyboards"
PLANS = ROOT / "production" / "plans"

WIDE, CLOSE, SPOT, CARD = "WIDE_STAGE", "CLOSEUP_EMPHASIS", "SPOTLIGHT_EFFECT", "INFOGRAPHIC_CARD"

# pola per beat: (mode, durasi tetap) — entri terakhir menyerap sisa durasi
TEMPLATES = {
    "hook": [(WIDE, 1.8), (CLOSE, 2.0), (WIDE, None)],
    "setup": [(WIDE, 2.4), (CLOSE, 2.2), (WIDE, None)],
    "explain": [(WIDE, 2.2), (SPOT, 2.2), (WIDE, None)],
    "twist": [(WIDE, 1.6), (CLOSE, 2.0), (SPOT, None)],
    "payoff": [(WIDE, 2.0), (SPOT, 2.2), (WIDE, None)],
    "cta": [(WIDE, 2.2), (CLOSE, None)],
}

# kartu hanya untuk episode yang naskahnya berisi langkah proses
CARDS = {
    5: (3, {"kind": "steps", "title": "Bagaimana sayap mengangkat",
            "accent": "#1F6F78",
            "steps": ["Udara di atas lebih cepat", "Tekanan bawah lebih besar",
                      "Sayap terangkat"]}),
    6: (3, {"kind": "steps", "title": "Kenapa laut asin",
            "accent": "#1F6F78",
            "steps": ["Hujan membawa garam", "Air menguap", "Garam tertinggal"]}),
    7: (3, {"kind": "steps", "title": "Apa yang terjadi saat cegukan",
            "accent": "#D7263D",
            "steps": ["Diafragma berkontraksi", "Udara terhenti", "Cegukan muncul"]}),
    8: (3, {"kind": "steps", "title": "Perjalanan satu pesan",
            "accent": "#1F6F78",
            "steps": ["Data dipecah kecil", "Disimpan di server",
                      "Diambil saat dibuka"]}),
    9: (3, {"kind": "steps", "title": "Cara HP menemukan kita",
            "accent": "#D7263D",
            "steps": ["Satelit kirim waktu", "HP hitung jarak", "Titik ketemu"]}),
    10: (3, {"kind": "steps", "title": "Ke mana energi baterai pergi",
             "accent": "#1F6F78",
             "steps": ["Layar terang", "Notifikasi terus", "Aplikasi latar jalan"]}),
}

# prop beat: (shot, id, h, badge) — semua band atas y 300
PROPS = {
    5: [(3, "bulb", 300, "gaya angkat")],
    6: [(6, "hourglass", 320, "jutaan tahun")],
    7: [(6, "clock", 300, "beberapa menit")],
    8: [(1, "phone", 340, "data"), (4, "bulb", 280, "paket")],
    9: [(1, "phone", 340, "titik lokasi")],
    10: [(1, "phone", 340, "baterai"), (5, "hourglass", 300, "pemakaian")],
}


def _split(dur: float) -> list[float]:
    """Pecah durasi > 3,8 s jadi bagian sama rata."""
    if dur <= 3.8:
        return [dur]
    n = int(dur // 3.8) + 1
    return [dur / n] * n


def build_layouts(est: float, beat: str, card: dict | None = None) -> list[dict]:
    if card is not None:
        out = [{"mode": WIDE, "from": 0.0, "to": 1.8},
               {"mode": CARD, "from": 1.8, "to": 5.2, "card": card}]
        if est - 5.2 > 0.25:
            out.append({"mode": WIDE, "from": 5.2, "to": est})
        return out

    tmpl = list(TEMPLATES.get(beat, TEMPLATES["explain"]))
    fixed = sum(d for _, d in tmpl if d)
    # sisa terlalu kecil -> buang segmen variabel terakhir
    while len(tmpl) > 2 and est - fixed < 0.5:
        tmpl.pop()
        fixed = sum(d for _, d in tmpl if d)
    modes = [m for m, _ in tmpl]
    rest = max(0.6, est - fixed)
    durs = [d if d else rest for _, d in tmpl]

    # entri terakhir terlalu pendek -> gabung ke sebelumnya
    if len(durs) >= 2 and durs[-1] < 0.5:
        durs[-2] += durs[-1]
        modes.pop()
        durs.pop()

    # pecah segmen yang > 3,8 s
    final = []
    for m, d in zip(modes, durs):
        parts = _split(d)
        final += [(m, p) for p in parts]

    out, t = [], 0.0
    for mode, d in final:
        item = {"mode": mode, "from": round(t, 2), "to": round(t + d, 2)}
        if mode == CLOSE:
            item["z"] = 1.46
        elif mode == SPOT:
            item["focus"] = "boca"
            item["dim"] = 0.58
            item["cone"] = True
        out.append(item)
        t += d
    out[-1]["to"] = round(est, 2)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--episodes", help="daftar id dipisah koma")
    ap.add_argument("--force", action="store_true",
                    help="tulis ulang layout yang sudah ada (pakai bersama --episodes)")
    args = ap.parse_args()

    only = set(args.episodes.split(",")) if args.episodes else None
    changed = []
    for sb in sorted(STORY.glob("BOCA-D*.json")):
        ep_id = sb.stem
        if only and ep_id not in only:
            continue
        d = json.loads(sb.read_text(encoding="utf-8"))
        day = int(d.get("day") or ep_id.split("D")[-1])
        card_shot, card_spec = CARDS.get(day, (None, None))
        props_map = {s: (pid, h, badge) for s, pid, h, badge in PROPS.get(day, [])}
        touched = 0

        for s in d["shots"]:
            if not s.get("layouts") or args.force:
                est = float(s.get("est_seconds", 6.0))
                card = card_spec if s["n"] == card_shot else None
                s["layouts"] = build_layouts(est, s.get("beat", "explain"), card)
                touched += 1
            if not s.get("props") and s["n"] in props_map:
                pid, h, badge = props_map[s["n"]]
                est = float(s.get("est_seconds", 6.0))
                s["props"] = [{"id": pid, "t_in": 0.9,
                               "t_out": round(max(2.0, est - 0.3), 2),
                               "x": 540, "y": 300, "h": h, "beat": True,
                               "anim": "pop_float", "badge": badge}]

        if not touched and not props_map:
            continue
        changed.append((ep_id, touched))
        if args.dry_run:
            continue
        sb.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

        pp = PLANS / f"{ep_id}.json"
        if pp.exists():
            plan = json.loads(pp.read_text(encoding="utf-8"))
            by_n = {s["n"]: s for s in d["shots"]}
            for ps in plan.get("shots", []):
                src = by_n.get(ps.get("n"))
                if not src:
                    continue
                ps["layouts"] = json.loads(json.dumps(src.get("layouts", [])))
                ps["props"] = json.loads(json.dumps(src.get("props", [])))
            pp.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n",
                          encoding="utf-8")

    for ep_id, n in changed:
        print(f"{ep_id}: {n} shot dilengkapi")
    print(f"total {len(changed)} episode" + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
