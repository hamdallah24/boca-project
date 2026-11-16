#!/data/data/com.termux/files/usr/bin/python3
"""BOCA-D02 — reference episode untuk template v4 (LOCKED).

Pipeline produksi ada di boca_pipeline.py; file ini hanya mendefinisikan
episode D02 (naskah + acting) lalu memanggil pipeline yang sama dengan yang
dipakai cron harian.

Contoh ini juga menunjukkan dialog 2 arah: di shot 3 Lumi ikut bicara
(muncul chip "LUMI" dan mulutnya bergerak).

Jalankan:
    python3 make_animatic_d02.py            # render ke /sdcard/Download/Boca/animatic-d02-v4
    python3 make_animatic_d02.py --edge     # paksa fallback Edge TTS
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from boca_pipeline import Episode, qa_checks, qa_report, render_episode  # noqa: E402

OUT = Path("/sdcard/Download/Boca/animatic-d02-v4")
TMP = Path("/data/data/com.termux/files/usr/tmp/opencode/boca-d02-v4-build")

WALK_IN = [
    dict(t=0.00, expr="shock", pose="walk", arms=[0], x=-300, ground=1400, h=640),
    dict(t=0.95, expr="shock", pose="walk", arms=[0], x=170, ground=1400, h=655),
    dict(t=1.30, expr="shock", pose="stand", arms=[0, 3, 2], period=0.70, x=290, ground=1400, h=672),
    dict(t=1.50, expr="shock", pose="stand", arms=[3], x=295, ground=1400, h=706),
    dict(t=2.20, expr="shock", pose="point", arms=[2], x=312, ground=1400, h=676),
    dict(t=3.10, expr="neutral", pose="stand", arms=[3, 2, 1], period=0.75, x=300, ground=1400, h=672),
]


def build_episode() -> Episode:
    shots = [
        dict(n=1, scene="park", cam={"fx": [0.30, 0.68], "fy": [0.35, 0.62]},
             dialogue=[
                 dict(who="boca", text="Langit biru, tapi langitnya nggak ada catnya. Warnanya dari mana?",
                      caption="Langitnya nggak ada cat.",
                      caption_adult="Langit biru tanpa cat — dari mana warnanya?"),
             ],
             keys=WALK_IN,
             lumi=[dict(t=2.30, expr="shock", pose="float", x=745, y=1080, h=250),
                   dict(t=3.20, expr="happy", pose="float", x=730, y=1055, h=255)],
             sfx=[(0.05, "pop", 1.0), (2.25, "boing", 0.7), (3.05, "sparkle", 0.6)]),

        dict(n=2, scene="space", cam={"fx": [0.62, 0.40], "fy": [0.60, 0.42]},
             dialogue=[
                 dict(who="boca", text="Cahaya matahari putih, padahal isinya campur banyak warna.",
                      caption="Cahaya matahari campur warna.",
                      caption_adult="Cahaya matahari putih sebenarnya campuran semua warna."),
             ],
             keys=[dict(t=0.00, expr="neutral", pose="walk", arms=[0], x=-250, ground=1420, h=560),
                   dict(t=0.70, expr="neutral", pose="stand", arms=[0, 2], period=0.8, x=230, ground=1420, h=575),
                   dict(t=1.80, expr="focus", pose="point", arms=[2], x=255, ground=1420, h=578),
                   dict(t=3.00, expr="focus", pose="stand", arms=[2, 3], period=0.85, x=240, ground=1420, h=575)],
             lumi=[dict(t=0.00, expr="happy", pose="float", x=880, y=1200, h=235),
                   dict(t=2.20, expr="happy", pose="point", x=820, y=1130, h=240)],
             sfx=[(0.05, "whoosh", 0.85), (2.40, "pop", 0.5)]),

        # dialog 2 arah: Boca menjelaskan, Lumi merespons
        dict(n=3, scene="prism", cam={"fx": [0.35, 0.66], "fy": [0.40, 0.62]},
             dialogue=[
                 dict(who="boca", text="Lewat prisma, cahaya pecah jadi pelangi: merah, kuning, hijau, biru.",
                      caption="Prisma memecah cahaya.",
                      caption_adult="Prisma memecah cahaya putih menjadi pelangi."),
                 dict(who="lumi", text="Wah, jadi pelangi!",
                      caption="Jadi pelangi!",
                      caption_adult="Cahaya putih terurai menjadi deretan warna."),
             ],
             keys=[dict(t=0.00, expr="focus", pose="walk", arms=[0], x=-240, ground=1400, h=610),
                   dict(t=0.75, expr="focus", pose="stand", arms=[0, 3], period=0.75, x=230, ground=1400, h=620),
                   dict(t=1.80, expr="focus", pose="point", arms=[2], x=258, ground=1400, h=622, prop="prism"),
                   dict(t=3.10, expr="happy", pose="point", arms=[2], x=258, ground=1400, h=622, prop="prism"),
                   dict(t=4.50, expr="happy", pose="stand", arms=[1, 3], period=0.8, x=245, ground=1400, h=620, prop="prism")],
             lumi=[dict(t=0.00, expr="happy", pose="float", x=900, y=1260, h=225),
                   dict(t=2.10, expr="happy", pose="cheer", x=840, y=1150, h=240),
                   dict(t=4.20, expr="happy", pose="float", x=780, y=1090, h=230)],
             sfx=[(0.05, "sparkle", 0.8), (2.05, "sparkle", 1.0), (4.60, "pop", 0.7)]),

        dict(n=4, scene="atmosphere", cam={"fx": [0.25, 0.60], "fy": [0.22, 0.48]},
             dialogue=[
                 dict(who="boca", text="Di atas kita ada udara. Partikelnya lempar cahaya biru ke segala arah.",
                      caption="Udara lempar cahaya biru.",
                      caption_adult="Partikel udara menghamburkan cahaya biru paling kuat."),
             ],
             keys=[dict(t=0.00, expr="focus", pose="walk", arms=[0], x=-280, ground=790, h=440),
                   dict(t=0.80, expr="focus", pose="stand", arms=[0, 2], period=0.8, x=215, ground=780, h=455),
                   dict(t=1.90, expr="focus", pose="point", arms=[2], x=235, ground=775, h=458),
                   dict(t=3.30, expr="neutral", pose="stand", arms=[3, 2], period=0.85, x=225, ground=775, h=455)],
             lumi=[dict(t=0.00, expr="happy", pose="float", x=840, y=1080, h=230),
                   dict(t=1.60, expr="shock", pose="float", x=780, y=980, h=235),
                   dict(t=3.20, expr="happy", pose="cheer", x=720, y=900, h=240)],
             sfx=[(0.05, "whoosh", 0.6), (2.80, "pop", 0.5)]),

        dict(n=5, scene="sky", cam={"fx": [0.30, 0.66], "fy": [0.45, 0.68]},
             dialogue=[
                 dict(who="boca", text="Karena biru paling banyak terlempar, kita lihat langit biru dari segala arah.",
                      caption="Biru paling banyak dilempar.",
                      caption_adult="Cahaya biru melimpah dari segala arah, jadi kita lihat biru."),
             ],
             keys=[dict(t=0.00, expr="focus", pose="walk", arms=[0], x=-260, ground=1420, h=540),
                   dict(t=0.75, expr="focus", pose="stand", arms=[0, 3], period=0.75, x=235, ground=1420, h=555),
                   dict(t=1.80, expr="neutral", pose="point", arms=[2], x=255, ground=1420, h=558),
                   dict(t=2.80, expr="happy", pose="celebrate", arms=[0], x=248, ground=1420, h=562)],
             lumi=[dict(t=0.00, expr="happy", pose="float", x=880, y=1240, h=230),
                   dict(t=2.60, expr="happy", pose="cheer", x=780, y=1150, h=245)],
             sfx=[(0.05, "pop", 0.8), (2.75, "sparkle", 0.9)]),

        dict(n=6, scene="sunset", cam={"fx": [0.40, 0.66], "fy": [0.40, 0.62]},
             dialogue=[
                 dict(who="boca", text="Pas sore, cahayasnya lebih jauh. Biru habis, tinggal merah dan oranye.",
                      caption="Sore, biru habis, tinggal merah.",
                      caption_adult="Di sore hari, biru habis; merah dan oranye yang tersisa."),
             ],
             keys=[dict(t=0.00, expr="confused", pose="walk", arms=[0], x=-270, ground=1420, h=550),
                   dict(t=0.85, expr="confused", pose="stand", arms=[0, 1], period=0.85, x=245, ground=1420, h=565),
                   dict(t=2.20, expr="confused", pose="think", arms=[1], x=258, ground=1420, h=567),
                   dict(t=3.70, expr="happy", pose="point", arms=[2], x=250, ground=1420, h=565)],
             lumi=[dict(t=0.00, expr="shock", pose="float", x=870, y=1260, h=225),
                   dict(t=3.40, expr="happy", pose="wave", x=810, y=1180, h=235)],
             sfx=[(0.05, "whoosh", 0.7), (3.60, "chime", 0.9)]),

        dict(n=7, scene="park_sunleft", cam={"fx": [0.66, 0.32], "fy": [0.55, 0.66]},
             dialogue=[
                 dict(who="boca", text="Jadi langit nggak dicat. Yang mewarnainya cuma udara dan cahaya.",
                      caption="Yang mewarna itu udara.",
                      caption_adult="Langit biru karena hamburan cahaya, bukan cat."),
             ],
             keys=[dict(t=0.00, expr="focus", pose="walk", arms=[0], x=-260, ground=1400, h=650),
                   dict(t=0.75, expr="focus", pose="stand", arms=[0, 2], period=0.7, x=275, ground=1400, h=668),
                   dict(t=1.70, expr="happy", pose="point", arms=[2], x=295, ground=1400, h=670),
                   dict(t=2.80, expr="happy", pose="celebrate", arms=[0], x=285, ground=1400, h=674)],
             lumi=[dict(t=0.00, expr="happy", pose="float", x=870, y=1250, h=230),
                   dict(t=2.60, expr="happy", pose="point", x=790, y=1160, h=240)],
             sfx=[(0.05, "pop", 0.9), (2.70, "sparkle", 1.0)]),

        dict(n=8, scene="park_evening", cam={"fx": [0.30, 0.62], "fy": [0.45, 0.62]},
             dialogue=[
                 dict(who="boca", text="Coba lihat langit sore ini. Warnanya apa?",
                      caption="Langit sore ini warna apa?",
                      caption_adult="Tulis di komentar."),
             ],
             keys=[dict(t=0.00, expr="happy", pose="walk", arms=[0], x=-240, ground=1400, h=650),
                   dict(t=0.70, expr="happy", pose="stand", arms=[0, 1], period=0.7, x=295, ground=1400, h=668),
                   dict(t=1.55, expr="happy", pose="wave", arms=[1, 3], period=0.75, x=315, ground=1400, h=672),
                   dict(t=2.60, expr="happy", pose="wave", arms=[3, 2], period=0.7, x=310, ground=1400, h=672)],
             lumi=[dict(t=0.00, expr="happy", pose="float", x=880, y=1250, h=235),
                   dict(t=1.40, expr="happy", pose="wave", x=810, y=1160, h=245)],
             sfx=[(0.05, "sparkle", 1.0), (1.45, "pop", 0.8)]),
    ]

    ep = Episode.from_dict({
        "id": "BOCA-D02",
        "day": 2,
        "title": "Kenapa langit warnanya biru?",
        "series": "KYB",
        "duration_target": 45,
        "facts_status": "verified_basic",
        "cta": "Coba lihat langit sore ini, warnanya apa?",
        "publish": {
            "title": "Kenapa langit warnanya biru? #Shorts",
            "description": ("Langit itu biru, tapi langitnya nggak punya cat. "
                             "Cahaya matahari sebenarnya campur banyak warna, dan udara "
                             "yang lempar cahaya biru ke segala arah. "
                             "Coba lihat langit sore ini, warnanya apa? "
                             "#faktaunik #belajarseru #edukasicuma #boca #Shorts"),
            "hashtags": ["#faktaunik", "#belajarseru", "#edukasicuma", "#boca", "#Shorts"],
            "category": "Education",
        },
        "shots": shots,
    })
    return ep


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tts", choices=["auto", "edge", "gemini"], default="auto")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    ep = build_episode()
    outdir = Path(args.out)
    tmp = TMP
    manifest = render_episode(ep, outdir, tmp, tts_backend=args.tts)
    checks = qa_checks(ep, outdir, ep.duration_target)
    ok, report = qa_report(checks)
    (outdir / "qa.txt").write_text(report + "\n", encoding="utf-8")
    print(report)
    print("\nmanifest:", json.dumps({k: manifest[k] for k in ("id", "duration", "tts")}, ensure_ascii=False))
    if not ok:
        print("QA GAGAL - cek qa.txt")
    print("done:", outdir)


if __name__ == "__main__":
    import json
    main()
