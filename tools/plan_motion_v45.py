#!/usr/bin/env python3
"""plan_motion_v45.py — motion plan story-driven (rulebook anti-template).

- scene_family + motion_motif wajib per episode
- layout diikat ke baris dialog (`on_line`), bukan detik hardcoded
- CLOSEUP hanya hook / twist / CTA, target = pembicara baris itu
- SPOTLIGHT maksimal 2/episode (D05 hanya 1, di twist)
- blocking bervariasi: solo 340/700, dialog 300/640
- satu prop tema per episode (D05 memakai prop penerbangan yang sudah ada)

Pemakaian:
    python3 tools/plan_motion_v45.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORY = ROOT / "production" / "storyboards"
PLANS = ROOT / "production" / "plans"

# day -> (scene_family, motion_motif, prop_id)
THEME = {
    1: ("money_city", "coin_count_and_compare", "coin_stack"),
    2: ("sky_light", "light_prism_and_scatter", "bulb"),
    3: ("night_room", "clock_tick_and_rest", "hourglass"),
    4: ("city_time", "clock_tick_and_focus", "clock"),
    5: ("aviation_sky", "upward_lift_and_airflow", "wing_airfoil"),
    6: ("ocean_shore", "salt_cycle_and_evaporation", "hourglass"),
    7: ("body_home", "diaphragm_pulse_and_breath", "clock"),
    8: ("data_city", "packet_journey_and_pulse", "phone"),
    9: ("city_signal", "signal_triangulation", "phone"),
    10: ("phone_life", "energy_drain_and_charge", "phone"),
    11: ("neural_net", "neuron_pulse_and_pattern", "bulb"),
    12: ("home_signal", "wave_penetration", "phone"),
    13: ("money_flow", "coin_transfer_and_ledger", "coin_stack"),
    14: ("data_storage", "data_erase_and_residue", "phone"),
    15: ("body_circulation", "heartbeat_pulse", "clock"),
    16: ("night_brain", "dream_float_and_memory", "bulb"),
    17: ("hunger_kitchen", "stomach_growl_and_timer", "clock"),
    18: ("brain_map", "memory_path_and_recall", "bulb"),
    19: ("fear_forest", "threat_pulse_and_freeze", "bulb"),
    20: ("water_lake", "density_float_and_layers", "bulb"),
    21: ("rain_cycle", "evaporation_cycle", "hourglass"),
    22: ("market_money", "supply_demand_balance", "coin_stack"),
    23: ("money_state", "debt_stack_and_interest", "coin_stack"),
    24: ("bank_money", "loan_cycle_and_interest", "coin_stack"),
    25: ("money_growth", "compound_growth_stack", "coin_stack"),
    26: ("money_print", "printing_press_and_supply", "coin_stack"),
    27: ("market_chart", "chart_rise_and_fall", "coin_stack"),
    28: ("state_budget", "tax_flow_and_services", "coin_stack"),
    29: ("earth_space", "rotation_stop_and_inertia", "clock"),
    30: ("cosmos_edge", "expansion_and_horizon", "bulb"),
}

# blocking: boca solo kiri/kanan bergantian, prop di sisi seberang
SOLO_X = [340, 700]


def line_speaker(shot: dict, idx: int) -> str:
    dlg = shot.get("dialogue") or []
    if not dlg:
        return "boca"
    return dlg[max(0, min(len(dlg) - 1, idx))].get("who", "boca")


def reblock(shot: dict, idx: int) -> None:
    guest = bool(shot.get("guest"))
    boca = 300 if guest else SOLO_X[idx % 2]
    keys = shot.get("keys") or []
    for j, k in enumerate(keys):
        if j == 0 and float(k.get("x", 0)) < 0:
            continue                       # biarkan walk-in dari luar frame
        k["x"] = boca + (35 if j % 2 else 0)
    for j, g in enumerate(shot.get("guest") or []):
        g["x"] = 640 - (30 if j else 0)    # melangkah mendekat ke Boca


def prop_shot_index(shots: list[dict]) -> int | None:
    def has_card(s):
        return any(l.get("mode") == "INFOGRAPHIC_CARD" for l in s.get("layouts") or [])
    for i, s in enumerate(shots):
        if s.get("beat") == "explain" and not s.get("guest") and not has_card(s):
            return i
    for i, s in enumerate(shots):
        if s.get("beat") in ("explain", "payoff") and not has_card(s):
            return i
    return None


def theme_prop(pid: str, x: int) -> dict:
    # band atas: di atas kepala, tidak menutupi Boca/tamu/caption
    return {"id": pid, "on_line": 0, "max_span": 3.2,
            "x": x, "y": 300, "h": 300, "beat": True,
            "anim": "pop_float"}


def d05_bespoke(d: dict) -> None:
    """D05: scene & prop sudah direvisi user; hanya motion-nya di-rule-kan."""
    shots = {s["n"]: s for s in d["shots"]}
    for s in d["shots"]:
        n = s["n"]
        s.pop("layouts", None)
        for pr in s.get("props") or []:
            pr["on_line"] = 0
            pr["max_span"] = 3.2
            pr.pop("t_in", None)
            pr.pop("t_out", None)

    # hook: closeup pertanyaan pembuka
    shots[1]["layouts"] = [{"mode": "CLOSEUP_EMPHASIS", "on_line": 0,
                            "target": line_speaker(shots[1], 0), "z": 1.46,
                            "max_span": 3.7}]
    # kartu mekanisme sayap (baris 1), prop sayap di baris 2
    shots[3]["layouts"] = [{"mode": "INFOGRAPHIC_CARD", "on_line": 0,
                            "max_span": 3.7,
                            "card": {"kind": "steps",
                                     "title": "Bagaimana sayap mengangkat",
                                     "accent": "#1F6F78",
                                     "steps": ["Bentuk sayap melengkung",
                                               "Udara atas & bawah beda",
                                               "Udara bawah mendorong naik"]}}]
    shots[3]["props"] = [p for p in shots[3]["props"] if p["id"] != "bulb"]
    if shots[3]["props"]:
        shots[3]["props"][0]["on_line"] = 1        # wing_airfoil setelah kartu
    # twist mesin mati: 1 spotlight (maks 2) + kartu
    shots[6]["layouts"] = [
        {"mode": "SPOTLIGHT_EFFECT", "on_line": 0, "target": "boca",
         "dim": 0.58, "cone": True, "max_span": 3.7},
        {"mode": "INFOGRAPHIC_CARD", "on_line": 1, "max_span": 3.7,
         "card": {"kind": "steps", "title": "Kalau mesin mati?",
                  "accent": "#D7263D",
                  "steps": ["Tidak langsung jatuh", "Meluncur pelan dulu",
                            "Gaya angkat masih bekerja"]}},
    ]
    # syarat terbang (payoff) = mekanisme
    shots[7]["layouts"] = [{"mode": "INFOGRAPHIC_CARD", "on_line": 1,
                            "max_span": 3.7,
                            "card": {"kind": "steps",
                                     "title": "Syarat pesawat terbang",
                                     "accent": "#1F6F78",
                                     "steps": ["Berat pesawat tidak hilang",
                                               "Gaya angkat dari udara bertambah",
                                               "Butuh udara & kecepatan tinggi"]}}]
    # CTA: closeup pertanyaan penutup (baris terakhir)
    last = len(shots[8]["dialogue"]) - 1
    shots[8]["layouts"] = [{"mode": "CLOSEUP_EMPHASIS", "on_line": last,
                            "target": line_speaker(shots[8], last), "z": 1.46,
                            "max_span": 3.7}]

    # blocking + prop di sisi seberang
    for i, s in enumerate(d["shots"]):
        reblock(s, i)
        guest = bool(s.get("guest"))
        base = 300 if guest else SOLO_X[i % 2]
        px = 720 if base < 540 else 240
        props = s.get("props") or []
        for j, pr in enumerate(props):
            pr["x"] = 360 + j * 360 if len(props) > 1 else 540
            pr["y"] = 300
            pr["h"] = 300


def generic(d: dict, pid: str) -> None:
    shots = d["shots"]
    # kartu lama (D06–D10) dipertahankan, diikat ke baris mekanisme
    for s in shots:
        cards = [l for l in (s.get("layouts") or [])
                 if l.get("mode") == "INFOGRAPHIC_CARD"]
        lays = []
        if cards:
            card = cards[0]
            card.pop("from", None)
            card.pop("to", None)
            card["on_line"] = 0
            card["max_span"] = 3.7
            lays.append(card)
        if lays:
            s["layouts"] = lays
        else:
            s.pop("layouts", None)

    # hook & CTA
    shots[0]["layouts"] = [{"mode": "CLOSEUP_EMPHASIS", "on_line": 0,
                            "target": line_speaker(shots[0], 0), "z": 1.46,
                            "max_span": 3.7}]
    last = len(shots[-1]["dialogue"]) - 1
    shots[-1]["layouts"] = [{"mode": "CLOSEUP_EMPHASIS", "on_line": last,
                             "target": line_speaker(shots[-1], last), "z": 1.46,
                             "max_span": 3.7}]

    # satu prop tema pada beat explain/payoff
    pi = prop_shot_index(shots)
    for i, s in enumerate(shots):
        reblock(s, i)
        if i != pi:
            s["props"] = []
            continue
        guest = bool(s.get("guest"))
        base = 300 if guest else SOLO_X[i % 2]
        s["props"] = [theme_prop(pid, 540)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    changed = 0
    for sb in sorted(STORY.glob("BOCA-D*.json")):
        d = json.loads(sb.read_text(encoding="utf-8"))
        day = int(d["day"])
        fam, motif, pid = THEME[day]
        d["scene_family"], d["motion_motif"] = fam, motif
        if day == 5:
            d05_bespoke(d)
        elif day > 5:
            generic(d, pid)
        # D01–D04: motion historis (sudah tayang / referensi), field tema saja
        if not args.dry_run:
            sb.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n",
                          encoding="utf-8")
            pp = PLANS / f"{sb.stem}.json"
            if pp.exists():
                plan = json.loads(pp.read_text(encoding="utf-8"))
                plan["scene_family"], plan["motion_motif"] = fam, motif
                by_n = {s["n"]: s for s in d["shots"]}
                for ps in plan.get("shots", []):
                    src = by_n.get(ps.get("n"))
                    if src:
                        for k in ("layouts", "props", "keys", "guest"):
                            ps[k] = json.loads(json.dumps(src.get(k, [])))
                        if "est_seconds" in src:
                            ps["est_seconds"] = src["est_seconds"]
                pp.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8")
        changed += 1
    print(f"{changed} episode diproses" + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
