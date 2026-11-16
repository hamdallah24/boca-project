# Rulebook Motion v4.5 — story-driven, anti-template

Berlaku untuk **D05–D30**. D01–D04 adalah arsip historis (sudah tayang /
referensi render) dan tidak dipaksa mengikuti aturan baru.

## 1. Tema episode dulu

Setiap storyboard & plan wajib punya:

```json
"scene_family": "aviation_sky",
"motion_motif": "upward_lift_and_airflow"
```

Tema ditentukan sebelum shot, bukan sesudah. Contoh motif:
`clock_tick_and_focus`, `coin_count_and_compare`, `packet_journey_and_pulse`.

## 2. Layout hanya kalau dialog meminta

| Mode | Kapan | Batas |
|---|---|---|
| `WIDE_STAGE` | default, terutama analogi + props | bebas |
| `CLOSEUP_EMPHASIS` | hook, shock/Aha, CTA | `target` = pembicara baris; `z` 1.3–1.6 |
| `INFOGRAPHIC_CARD` | mekanisme, sebab-akibat, perbandingan | 2–3 langkah; fakta naskah |
| `SPOTLIGHT_EFFECT` | fokus, rahasia, gelap, jebakan, twist | **maks 2/episode**; bukan analogi outdoor terang |

Dua layout bersebelahan tidak boleh mode sama. Jangan memaksa efek.

## 3. Ikat ke baris dialog, bukan detik tebakan

```json
{"mode": "CLOSEUP_EMPHASIS", "on_line": 0, "target": "boca", "z": 1.46}
{"mode": "INFOGRAPHIC_CARD", "on_line": 1, "max_span": 3.7, "card": {}}
{"id": "wing_airfoil", "on_line": 0, "max_span": 3.2, "x": 540, "y": 300}
```

Pipeline:

1. `build_voice_track()` / `load_vo_reuse()` menghasilkan `line.start/end`.
2. `scale_shot_timings()` menskalakan key/layout/prop numerik dari
   `est_seconds` ke durasi VO nyata.
3. `bind_line_motion()` mengubah `on_line`/`to_line` menjadi detik shot,
   menaruh `target` ke `focus`, dan menormalkan layout (celah jadi WIDE).

Tidak ada lagi `to: 6.6` yang berhenti di tengah shot 11 detik.

## 4. Blocking bervariasi

| Situasi | Boca | Tamu | Prop |
|---|---|---|---|
| solo kiri | 340 | — | kanan 720 / atas 540 |
| solo kanan | 700 | — | kiri 240 / atas 540 |
| dialog | 300 | 640 → 610 | atas 540 |

Pose/ekspresi mengikuti emosi baris (`vo.beats`), bukan pola D04. Key minimal
2 per shot; key terakhir tidak boleh berhenti sebelum 60% durasi shot.

## 5. Validator

`python3 tools/check_storyboards.py` menolak:

- `scene_family`/`motion_motif` kosong (D05+)
- layout tanpa `on_line` (D05+)
- spotlight > 2/episode
- closeup tanpa `target`, atau target ≠ pembicara baris
- dua layout mode sama berurutan
- shot ≥ 6 s tanpa layout **dan** tanpa prop/key beranimasi

Regenerasi massal: `python3 tools/plan_motion_v45.py`.

## 6. Skala waktu

`scale_shot_timings()` memakai `shot.est_seconds` sebagai basis. Kalau naskah
memanjang 93 s padahal target 60 s, key dan layout numerik ikut melar; blok
`on_line` tetap presisi ke kalimat. Tidak ada `atempo`.
