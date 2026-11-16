#!/data/data/com.termux/files/usr/bin/python3
"""Plan builder: Content Bible (md) -> episode plan JSON.

md adalah source of truth. Script ini membaca section "11. Kalender 30 Hari"
lalu menyusun plan episode (shot list, narasi, acting, caption) per hari.

Plan yang dihasilkan berstatus "draft" dan WAJIB ditinjau manusia sebelum
dipublikasikan (lihat daily_build.py). Plan final bisa disunting manual di
production/plans/DNN.json tanpa mengubah md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MD = Path("/sdcard/Download/BOCA_Rencana_Konten_30_Hari.md")
PLANS = ROOT / "production" / "plans"

SERIES_NAME = {
    "KYB": "Kenapa Ya, Boca?",
    "BMM": "Boca Masuk Mesin",
    "BMT": "Boca Menang Tempur",
    "BBU": "Boca Bikin URLah",
    "BLA": "Boca Lihat Asphalt",
}
HASHTAGS = {
    "KYB": ["#faktaunik", "#belajarseru", "#edukasicuma", "#ideinaja"],
    "BMM": ["#teknologi", "#faktaunik", "#edukasicuma", "#ideinaja"],
    "BMT": ["#teknologi", "#caramudah", "#belajarseru", "#ideinaja"],
    "BBU": ["#uang", "#faktaunik", "#keluargabocah", "#ideinaja"],
    "BLA": ["#bumi", "#sains", "#faktaunik", "#ideinaja"],
}


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_days(md_text: str) -> list[dict]:
    lines = md_text.split("\n")
    days = []
    cur = None
    buf_key = None
    for raw in lines:
        line = raw.rstrip()
        s = line.strip()
        m = re.match(r"^### Hari (\d+) --- (.+)$", s)
        if m:
            if cur:
                days.append(cur)
            cur = {"day": int(m.group(1)), "title": m.group(2).strip(),
                   "meta": "", "idea": "", "world": "", "story": ""}
            buf_key = None
            continue
        if cur is None:
            continue
        if s.startswith("**Meta:**"):
            cur["meta"] = s
            buf_key = None
        elif s.startswith("**Ide utama:**"):
            cur["idea"] = s.replace("**Ide utama:**", "").strip()
            buf_key = "idea"
        elif s.startswith("**Dunia visual:**"):
            cur["world"] = s.replace("**Dunia visual:**", "").strip()
            buf_key = "world"
        elif s.startswith("**Storyboard:**"):
            cur["story"] = s.replace("**Storyboard:**", "").strip()
            buf_key = "story"
        elif not s:
            buf_key = None
        elif buf_key:
            # lanjutan paragraf (wrap baris markdown)
            cur[buf_key] += " " + s
    if cur:
        days.append(cur)

    for d in days:
        meta = d["meta"]
        d["id"] = (re.search(r"`(BOCA-D\d+)`", meta) or [None, f"BOCA-D{d['day']:02d}"])[1]
        d["series"] = (re.search(r"Seri: `([A-Z]+)`", meta) or [None, "KYB"])[1]
        dur = (re.search(r"Durasi: `(\d+)s`", meta) or [None, "45"])[1]
        d["duration"] = int(dur)
        d["facts"] = (re.search(r"Fakta: `([a-z_]+)`", meta) or [None, "pending"])[1]
        d["cta"] = (re.search(r'CTA: "([^"]*)"', meta) or [None, "Tulis di komentar."])[1]
        d["beats"] = parse_beats(d["story"])
    return days


def parse_beats(story: str) -> list[dict]:
    """Pecah storyboard jadi beat: judul + narasi (kalimat yang diucapkan)."""
    beats = []
    parts = re.split(r"(?=\d\. \*\*[^*]+\*\*)", story)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        title_m = re.match(r"(\d)\. \*\*([^*]+)\*\*", part)
        if not title_m:
            continue
        n = int(title_m.group(1))
        name = title_m.group(2).strip()
        nar = re.findall(r'Narasi:\s*"([^"]+)"', part)
        narration = normalise(nar[0]) if nar else ""
        if not narration:
            # fallback: kalimat pertama dalam beat
            sentences = re.findall(r'"([^"]+)"', part)
            narration = normalise(sentences[0]) if sentences else ""
        beats.append({"n": n, "name": name, "narration": narration, "raw": part})
    return beats


def pick_scene(text: str, index: int, total: int) -> str:
    t = (text or "").lower()
    if any(k in t for k in ["ruang angkasa", "bintang", "bulat", "planet", "antariksa",
                            "tata surya", "kosmos", "bumi dari", "satelit"]):
        return "space"
    if "prisma" in t or "pelangi" in t:
        return "prism"
    if any(k in t for k in ["atmosfer", "orbit", "iss", "sts", "roket"]):
        return "atmosphere"
    if any(k in t for k in ["senja", "sore", "terbenam", "sunset", "jingga", "malam"]):
        return "sunset"
    if any(k in t for k in ["langit", "awan", "pagi", "siang", "cerah"]):
        return "sky"
    if index == total - 1:
        return "park_evening"
    return "park"


def simple_caption(narration: str, max_words: int = 9) -> str:
    """Versi sederhana dari narasi: kalimat pertama, maksimal max_words."""
    if not narration:
        return ""
    first = re.split(r"(?<=[.!?])\s+", narration)[0].strip()
    words = first.split()
    if len(words) > max_words:
        first = " ".join(words[:max_words]).rstrip(",;")
    return first


# --------------------------------------------------------------- LLM drafter
LLM_MODELS = ["gemini-3.1-flash-lite-preview", "gemini-3.1-flash-preview",
              "gemini-3-flash-preview", "gemini-flash-latest"]
LLM_CACHE = ROOT / "production" / "cache" / "llm"

PROMPT = """Kamu penulis naskah untuk channel edukatif BOCA (karakter anak SD yang menjelaskan hal rumit dengan bahasa ringan).

Tulis SATU kalimat narasi (maks 14 kata) untuk beat adegan berikut.

Beat: {beat}
Visual: {visual}
Ide episode: {idea}

Aturan wajib:
- Bahasa Indonesia sehari-hari, ringan, hangat, seperti ngobrol ke teman.
- Pakai analogi konkret, tanpa istilah teknis.
- JANGAN menyapa penonton sebagai "Adek"/"dek"/"kamu".
- Satu kalimat = satu ide, maksimal 14 kata.
- Tidak boleh menyebut nomor, data, atau fakta khusus yang belum diverifikasi.

Balas HANYA kalimat narasi tersebut, tanpa penjelasan dan tanpa tanda kutip."""


def llm_draft(beat: str, visual: str, idea: str, key: str) -> str:
    """Panggil Gemini text model untuk draf narasi. Cache per prompt."""
    LLM_CACHE.mkdir(parents=True, exist_ok=True)
    digest = hashlib.md5(f"{beat}|{visual}|{idea}".encode("utf-8")).hexdigest()[:12]
    cached = LLM_CACHE / f"{digest}.txt"
    if cached.exists() and cached.stat().st_size > 10:
        return cached.read_text(encoding="utf-8").strip()
    if not key:
        return ""
    body = {
        "contents": [{"parts": [{"text": PROMPT.format(beat=beat, visual=visual, idea=idea)}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 120},
    }
    text = ""
    for model in LLM_MODELS:
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            data=json.dumps(body).encode("utf-8"),
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.load(r)
            text = data["candidates"][0]["content"]["parts"][0].get("text", "").strip()
        except Exception as e:  # noqa: BLE001
            print(f"    LLM draft {model} gagal: {e}")
            continue
        if text:
            break
    text = text.strip().strip('"').replace("\n", " ").strip()
    if text:
        cached.write_text(text, encoding="utf-8")
    return text


def acting_keys(kind: str, ground: int, h: int) -> list[dict]:
    """Template acting generik per jenis shot."""
    if kind == "hook":
        return [
            dict(t=0.00, expr="shock", pose="walk", arms=[0], x=-300, ground=ground, h=h - 20),
            dict(t=0.95, expr="shock", pose="walk", arms=[0], x=170, ground=ground, h=h - 10),
            dict(t=1.30, expr="shock", pose="stand", arms=[0, 3, 2], period=0.70, x=290, ground=ground, h=h),
            dict(t=2.30, expr="shock", pose="point", arms=[2], x=312, ground=ground, h=h),
            dict(t=3.40, expr="neutral", pose="stand", arms=[3, 2, 1], period=0.75, x=300, ground=ground, h=h),
        ]
    if kind == "close":
        return [
            dict(t=0.00, expr="focus", pose="stand", arms=[0, 2], period=0.80, x=250, ground=ground, h=h),
            dict(t=1.20, expr="neutral", pose="point", arms=[2], x=265, ground=ground, h=h),
            dict(t=2.40, expr="happy", pose="celebrate", arms=[0], x=258, ground=ground, h=h),
        ]
    if kind == "cta":
        return [
            dict(t=0.00, expr="happy", pose="walk", arms=[0], x=-240, ground=ground, h=h),
            dict(t=0.70, expr="happy", pose="stand", arms=[0, 1], period=0.70, x=295, ground=ground, h=h),
            dict(t=1.55, expr="happy", pose="wave", arms=[1, 3], period=0.75, x=315, ground=ground, h=h),
        ]
    return [
        dict(t=0.00, expr="focus", pose="stand", arms=[0, 3], period=0.75, x=250, ground=ground, h=h),
        dict(t=1.60, expr="focus", pose="point", arms=[2], x=268, ground=ground, h=h),
        dict(t=2.90, expr="neutral", pose="stand", arms=[3, 2], period=0.85, x=255, ground=ground, h=h),
    ]


LUMI_KEYS = {
    "float": [dict(t=0.00, expr="happy", pose="float", x=860, y=1230, h=230),
              dict(t=2.00, expr="happy", pose="float", x=800, y=1180, h=235)],
    "cheer": [dict(t=0.00, expr="happy", pose="float", x=860, y=1230, h=230),
              dict(t=1.80, expr="happy", pose="cheer", x=790, y=1150, h=245)],
    "wave": [dict(t=0.00, expr="happy", pose="float", x=860, y=1230, h=230),
             dict(t=1.40, expr="happy", pose="wave", x=800, y=1160, h=240)],
    "point": [dict(t=0.00, expr="happy", pose="float", x=860, y=1230, h=230),
              dict(t=1.60, expr="happy", pose="point", x=790, y=1160, h=240)],
}

SFX_BY_KIND = {
    "hook": [(0.05, "pop", 1.0), (2.60, "whoosh", 0.45)],
    "middle": [(0.05, "whoosh", 0.7)],
    "close": [(0.05, "sparkle", 0.9)],
    "cta": [(0.05, "sparkle", 1.0), (1.45, "pop", 0.8)],
}


def build_plan(day: dict, ground: int = 1400, h: int = 620, key: str = "",
               use_llm: bool = True) -> dict:
    beats = day["beats"]
    shots = []
    n = 1
    total_beats = len(beats)
    drafted = 0
    for i, b in enumerate(beats):
        kind = "hook" if i == 0 else ("close" if i == total_beats - 1 else "middle")
        scene = pick_scene(b["name"] + " " + b["narration"] + " " + day["world"], i, total_beats)
        narration = b["narration"]
        if not narration and use_llm and key:
            visual = normalise(b["raw"])[:400]
            narration = llm_draft(b["name"], visual, day["idea"], key)
            if narration:
                drafted += 1
        if not narration:
            narration = f"[TODO narasi beat {b['n']}] {b['name']}"
        shots.append({
            "n": n,
            "scene": scene,
            "dialogue": [{
                "who": "boca",
                "text": narration,
                "caption": simple_caption(narration),
                "caption_adult": narration,
            }],
            "keys": acting_keys(kind, ground, h),
            "lumi": LUMI_KEYS["cheer"] if kind in ("close",) else LUMI_KEYS["float"],
            "sfx": [list(x) for x in SFX_BY_KIND[kind]],
            "cam": {"fx": [0.30, 0.68], "fy": [0.35, 0.62]},
        })
        n += 1

    # shot CTA
    shots.append({
        "n": n,
        "scene": "park_evening",
        "dialogue": [{
            "who": "boca",
            "text": day["cta"],
            "caption": day["cta"],
            "caption_adult": "Tulis di komentar.",
        }],
        "keys": acting_keys("cta", ground, h),
        "lumi": LUMI_KEYS["wave"],
        "sfx": [list(x) for x in SFX_BY_KIND["cta"]],
        "cam": {"fx": [0.30, 0.62], "fy": [0.45, 0.62]},
    })

    return {
        "id": day["id"],
        "day": day["day"],
        "title": day["title"],
        "series": day["series"],
        "duration_target": day["duration"],
        "facts_status": day["facts"],
        "cta": day["cta"],
        "status": "draft",
        "needs_review": True,
        "llm_drafted_lines": drafted,
        "notes": "Auto-draft dari Content Bible. Tinjau narasi, caption, scene, dan acting sebelum publish.",
        "publish": {
            "title": f"{day['title']}",
            "description": (f"{day['idea']}\n\n{day['world']}\n\n"
                             f"{day['cta']}\n\n"
                             + " ".join(HASHTAGS.get(day["series"], HASHTAGS["KYB"]))),
            "hashtags": HASHTAGS.get(day["series"], HASHTAGS["KYB"]),
            "category": "Education",
        },
        "shots": shots,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=str(MD))
    ap.add_argument("--day", type=int, help="nomor hari 1..30 (kosong = semua)")
    ap.add_argument("--out", default=str(PLANS))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-llm", action="store_true", help="jangan pakai LLM untuk draf narasi")
    args = ap.parse_args()

    key = ""
    if not args.no_llm:
        try:
            import os
            sys.path.insert(0, str(ROOT))
            from boca_pipeline import gemini_key
            key = gemini_key()
        except Exception:
            key = ""

    md_text = Path(args.md).read_text(encoding="utf-8")
    days = parse_days(md_text)
    print(f"parsed {len(days)} hari dari md" + ("  (LLM drafter aktif)" if key else ""))
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    targets = [d for d in days if args.day in (None, d["day"])]
    for d in targets:
        plan = build_plan(d, key=key, use_llm=bool(key))
        path = outdir / f"{d['id']}.json"
        if path.exists() and not args.force:
            print(f"skip {path.name} (sudah ada)")
            continue
        path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {path.name}  shots={len(plan['shots'])}  drafted={plan['llm_drafted_lines']}  status={plan['status']}")


if __name__ == "__main__":
    main()
