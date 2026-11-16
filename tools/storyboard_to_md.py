#!/usr/bin/env python3
"""Render storyboard JSON -> Markdown yang enak dibaca.

    python3 tools/storyboard_to_md.py BOCA-D03
    python3 tools/storyboard_to_md.py --all
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SB = ROOT / "production" / "storyboards"

CAM_NAMES = {
    ((0.46, 0.50), (0.44, 0.46), (1.00, 1.25)): "C1 push-in",
    ((0.50, 0.46), (0.46, 0.42), (1.30, 1.00)): "C2 pull-out",
    ((0.62, 0.32), (0.45, 0.45), (1.05, 1.05)): "C3 pan kiri",
    ((0.32, 0.62), (0.45, 0.45), (1.05, 1.05)): "C4 pan kanan",
    ((0.45, 0.45), (0.62, 0.30), (1.00, 1.06)): "C5 tilt up",
    ((0.45, 0.45), (0.28, 0.60), (1.06, 1.00)): "C6 tilt down",
    ((0.30, 0.70), (0.35, 0.62), (1.00, 1.00)): "C7 static wide",
    ((0.47, 0.50), (0.45, 0.45), (1.10, 1.45)): "C8 push-in kuat",
    ((0.38, 0.56), (0.38, 0.52), (1.12, 1.12)): "C9 drift diagonal",
}

SPEAKER = {"boca": "BOCA", "lumi": "LUMI"}


def cam_name(cam: dict) -> str:
    key = (tuple(cam.get("fx", ())), tuple(cam.get("fy", ())), tuple(cam.get("z", (1, 1))))
    return CAM_NAMES.get(key, f"fx{cam.get('fx')} fy{cam.get('fy')} z{cam.get('z')}")


def build(d: dict) -> str:
    ep = d["id"]
    cast = d.get("cast", {})
    guest = cast.get("guest")
    an = d.get("analogy", {})
    vo = d.get("vo", {})
    shots = d["shots"]
    dur = d.get("duration_target")
    total_lines = sum(len(s.get("dialogue", [])) for s in shots)

    L: list[str] = []
    L.append(f"# {ep} — {d['title']}")
    L.append("")
    L.append(f"**Seri:** `{d['series']}` · **Durasi:** {dur}s · "
             f"**Kata:** {vo.get('total_words', '?')} · **Baris:** {total_lines} · "
             f"**Shot:** {len(shots)}")
    L.append("")
    L.append(f"**Logline:** {d.get('logline', '-')}")
    L.append("")
    h = d.get("hook", {})
    L.append("## Hook")
    L.append("")
    L.append(f"| Pola | Klaim | Celah | Janji |")
    L.append("|---|---|---|---|")
    L.append(f"| `{h.get('pattern','-')}` | {h.get('claim','-')} | {h.get('gap','-')} | {h.get('promise','-')} |")
    L.append("")
    L.append("## Cast")
    L.append("")
    L.append(f"- **Host:** `boca` — suara `{vo.get('voice_boca','Puck')}`")
    L.append(f"- **Sidekick:** `lumi` — suara `{vo.get('voice_lumi','Aoede')}`")
    if guest:
        L.append(f"- **Tamu:** `{guest}` — suara `{vo.get('voice_guest','-')}`")
    else:
        L.append("- **Tamu:** — (Lumi jadi ASKER)")
    L.append("")
    L.append("## Analogi inti")
    L.append("")
    L.append(f"> {an.get('source','-')}")
    L.append("")
    if an.get("maps"):
        L.append("| Konsep nyata | Padanan analogi |")
        L.append("|---|---|")
        for m in an["maps"]:
            L.append(f"| {m.get('real','-')} | {m.get('analogy','-')} |")
        L.append("")
    if an.get("why_it_works"):
        L.append(f"**Kenapa jalan:** {an['why_it_works']}")
        L.append("")
    if an.get("line_shot"):
        L.append(f"**Diucapkan di shot:** {an['line_shot']}")
        L.append("")

    L.append("## Shot list")
    L.append("")
    L.append("| # | Beat | Scene | Kamera | Durasi | Dialog |")
    L.append("|---|---|---|---|---|---|")
    for s in shots:
        who = ", ".join(l.get("who", "?") for l in s.get("dialogue", []))
        L.append(f"| {s['n']} | {s.get('beat','-')} | `{s.get('scene','-')}` | "
                 f"{cam_name(s.get('cam', {}))} | {s.get('est_seconds','?')}s | {who} |")
    L.append("")

    L.append("## Naskah VO")
    L.append("")
    beats = {b.get("shot"): b for b in vo.get("beats", [])}
    for s in shots:
        b = beats.get(s["n"], {})
        L.append(f"### Shot {s['n']} — {s.get('beat','-')}"
                 + (f" ({b.get('function','')})" if b.get("function") else ""))
        L.append("")
        if b.get("emotion") or b.get("emphasis"):
            extra = []
            if b.get("emotion"):
                extra.append(f"emosi: {b['emotion']}")
            if b.get("emphasis"):
                extra.append("tekanan: " + ", ".join(f"**{e}**" for e in b["emphasis"]))
            if b.get("pause_after"):
                extra.append(f"jeda setelah: {b['pause_after']}s")
            L.append("_" + " · ".join(extra) + "_")
            L.append("")
        for line in s.get("dialogue", []):
            who = SPEAKER.get(line.get("who"), str(line.get("who")).upper())
            L.append(f"- **{who}:** \"{line.get('text','')}\"")
            L.append(f"  - caption: `{line.get('caption','')}`")
            L.append(f"  - dewasa: _{line.get('caption_adult','')}_")
        L.append("")

    L.append("## Aset yang dibutuhkan")
    L.append("")
    L.append("| Prioritas | Tipe | id |")
    L.append("|---|---|---|")
    for n in d.get("asset_needs", []):
        L.append(f"| {n.get('priority','-')} | {n.get('type','-')} | `{n.get('id','-')}` |")
    L.append("")
    if d.get("production_notes"):
        L.append("## Catatan produksi")
        L.append("")
        L.append(d["production_notes"])
        L.append("")
    return "\n".join(L)


def convert(ep_id: str) -> int:
    src = SB / f"{ep_id}.json"
    if not src.exists():
        print(f"tidak ada: {src}")
        return 1
    d = json.loads(src.read_text(encoding="utf-8"))
    out = SB / f"{ep_id}.md"
    out.write_text(build(d), encoding="utf-8")
    print(f"{ep_id} -> {out.name}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    if args.all:
        rc = 0
        for f in sorted(SB.glob("BOCA-D*.json")):
            rc |= convert(f.stem)
        return rc
    if not args.ids:
        print("pakai: storyboard_to_md.py BOCA-D03 | --all")
        return 1
    rc = 0
    for i in args.ids:
        rc |= convert(i)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
