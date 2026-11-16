---
name: boca-visual
description: Memilih scene, kamera C1–C9, motif gerak M1–M8, dan menyusun keys Boca/Lumi/tamu yang benar-benar bisa dirender pipeline BOCA. Gunakan saat menulis shot, shot terasa membosankan, kamera terlalu statis, atau render gagal karena nilai enum/keys tidak valid.
metadata:
  author: boca-character
  version: "1.0"
---

# BOCA Visual — scene, kamera, gerak

Dokumen ini adalah **kontrak render**. Nilai di luar daftar ini tidak dirender
atau bikin render gagal. Detail panjang ada di `docs/SCENE_MOTION_SPEC.md`.

## Kanvas & safe area

| Item | Nilai |
|---|---|
| Output | 1080 × 1920 (9:16), 30 fps, H.264 + AAC |
| Kanvas scene | 1350 × 2400 → ruang pan hanya 270 × 480 px |
| Caption | aman sampai **y = 1570 px** |
| Zoom berguna | `1.0–1.6`; di atas 1.6 gambar blur |

Karena ruang pan cuma 270 × 480 px, **zoom (`z`) yang membuat kamera terasa
hidup** — bukan pan.

## Scene

Hanya 8 yang benar-benar ada di kode:

`park` · `park_evening` · `park_sunleft` · `sky` · `space` · `prism` · `atmosphere` · `sunset`

24 scene lain (`bedroom`, `market`, `body_inside`, dst.) **belum diimplementasikan**.
Boleh ditulis di storyboard, tapi episode itu **belum bisa dirender** sampai
`make_cartoon.py` punya fungsinya. Lihat `references/scenes.md`.

Aturan variasi:

1. Minimal **4 scene id berbeda** per episode.
2. Dua episode berurutan **tidak boleh** membuka dengan scene sama.
3. Dalam 5 episode berurutan, satu scene maksimal di **3** episode
   (klaster keuangan D22–D28 butuh `market`/`bank` berulang).
4. Episode berurutan berbagi maksimal **2** scene.

## Kamera — pakai preset, jangan mengarang

```json
"cam": { "fx": [0.46, 0.50], "fy": [0.44, 0.46], "z": [1.00, 1.25] }
```

| Kode | Nama | fx | fy | z |
|---|---|---|---|---|
| C1 | push-in | `[0.46, 0.50]` | `[0.44, 0.46]` | `[1.00, 1.25]` |
| C2 | pull-out | `[0.50, 0.46]` | `[0.46, 0.42]` | `[1.30, 1.00]` |
| C3 | pan kiri | `[0.62, 0.32]` | `[0.45, 0.45]` | `[1.05, 1.05]` |
| C4 | pan kanan | `[0.32, 0.62]` | `[0.45, 0.45]` | `[1.05, 1.05]` |
| C5 | tilt up | `[0.45, 0.45]` | `[0.62, 0.30]` | `[1.00, 1.06]` |
| C6 | tilt down | `[0.45, 0.45]` | `[0.28, 0.60]` | `[1.06, 1.00]` |
| C7 | static wide | `[0.30, 0.70]` | `[0.35, 0.62]` | `[1.00, 1.00]` |
| C8 | push-in kuat | `[0.47, 0.50]` | `[0.45, 0.45]` | `[1.10, 1.45]` |
| C9 | drift diagonal | `[0.38, 0.56]` | `[0.38, 0.52]` | `[1.12, 1.12]` |

Minimal **3 preset berbeda** per episode. `cam` wajib di setiap shot.

## Enum valid

| Field | Nilai |
|---|---|
| `expr` Boca | `shock` `neutral` `happy` `confused` `focus` `sleepy` |
| `pose` Boca | `stand` `walk` `point` `think` `read` `wave` `cheer` `celebrate` `run` |
| `arms` | `0` turun · `1` tekuk depan · `2` menunjuk jauh · `3` terangkat · `4` menunjuk bawah |
| `prop` | hanya `prism`, maksimal 1 shot |
| `sfx` | `pop` `whoosh` `sparkle` `chime` `boing`, maksimal 4/episode |
| Lumi `expr` | `happy` `shock` |
| Lumi `pose` | `float` `wave` `point` `cheer` |
| Tamu `expr` | `neutral` `happy` `shock` `confused` |
| Tamu `pose` | `stand` `point` `wave` |

**Jebakan paling sering:** `arms` harus **list** (`"arms": [0, 3]`), bukan angka.
`"arm": 2` bikin sprite lookup gagal.

## Skema `keys` (Boca)

```json
{ "t": 0.0, "expr": "shock", "pose": "walk", "arms": [0],
  "x": -300, "ground": 1400, "h": 640 }
```

| Field | Rentang |
|---|---|
| `t` | 0 → durasi shot, harus naik |
| `x` | -350 (luar kiri) … 950 (kanan) |
| `ground` | 1330–1440 |
| `h` | 520 (jauh) … 760 (dekat) |
| `period` | 0.6–1.0 detik per gestur (default 0.8) |

Aturan:

- Minimal **2 key** per shot (shot < 3 s cukup 1).
- Interpolasi hanya `x`, `ground`, `h`. `expr`/`pose`/`arms` berganti mendadak.
- Jangan dua key berurutan dengan `pose` sama tapi `expr` beda dalam < 0.25 s.
- `pose: "walk"` butuh minimal 2 key.
- Boca tidak boleh diam > **2.5 detik** tanpa key baru.

## Lumi

| Field | Nilai |
|---|---|
| `x` | 700–950 (kanan), atau 150–380 kalau Boca pindah kanan |
| `y` | 1000–1300 |
| `h` | 220–260 |

Lumi tidak boleh menutupi wajah Boca, tamu, atau caption. Kalau ada tamu di
`x` 700–780, taruh Lumi di `y` 1000–1080 (atas).

## Tamu

```json
"guest": [
  { "t": 0.0, "expr": "neutral", "pose": "stand", "x": 740, "ground": 1420, "h": 615 }
]
```

- Field `guest` **wajib ada** (boleh `[]`) kalau `cast.guest` tidak null.
- Posisi tetap: Boca kiri (`x` 240–260), tamu kanan (`x` 720–745), `ground` 1420.
- Tamu muncul di ≥ 2 shot.

## Motif gerak (M1–M8) — bergilir, jangan sama dengan episode sebelumnya

| Kode | Nama | Pola |
|---|---|---|
| M1 | walk-in reveal | `0 walk x=-300` → `.35L stand x=250` → `.70L point x=260` |
| M2 | point-explain | `0 stand [0]` → `.30L point [2]` → `.65L stand [1,3]` |
| M3 | think→lightbulb | `0 think [1]` → `.45L confused [1]` → `.70L focus [3]` → `.85L happy [0,3]` |
| M4 | prop demo | `0 stand [0] prop` → `.30L point [2] prop` → `.70L happy [1,3] prop` |
| M5 | run-chase | `0 run x=-320` → `.40L run x=250` → `.60L stand [2] x=270` |
| M6 | wave-greet | `0 wave [3]` → `.40L happy [0,1]` → `.80L point [2]` |
| M7 | celebrate | `0 happy [0]` → `.50L cheer [3]` → `.80L celebrate [1,3]` |
| M8 | sleepy→focus | `0 sleepy [0]` → `.50L focus [1]` → `.80L happy [2]` |

`L` = durasi shot.

## Caption

- Satu baris dialog = satu caption. Jangan memecah caption dari `text`-nya.
- `caption` ≤ 9 kata, tanpa tanda baca akhir.
- `caption_adult` ≤ 14 kata, boleh lebih teknis — ini baris kecil penjelas.
- Teks tidak boleh masuk ke area bawah `y = 1570`.
- Jangan taruh Lumi atau tangan Boca di area caption.

Pelajaran dari skill komunitas (HyperFrames `embedded-captions`): kelompok caption
yang enak dibaca adalah **3–5 kata** untuk percakapan santai, dan **2–3 kata**
untuk energi tinggi. Kalau satu baris VO > 9 kata, pecah jadi dua baris dialog —
jangan pecah captionnya.

## Anti-pola (penyebab episode terasa membosankan)

| Gejala | Penyebab | Perbaikan |
|---|---|---|
| Semua shot terasa sama | `cam` sama / semua C7 | minimal 3 preset, ganti per beat |
| Background itu-itu saja | fallback ke `park` | pilih scene dari tabel, bukan kata kunci |
| Boca diam lama | 1 key untuk shot 6 s | tambah key di 0.4L dan 0.75L |
| Kamera goyang aneh | `z` > 1.6 | maksimal 1.45 |
| Tamu menutupi Boca | `x` tamu < 700 | Boca 250, tamu 740 |
| Caption terpotong | teks terlalu bawah | aman sampai y 1570 |

## Selesai kalau

- [ ] Minimal 4 scene unik, minimal 3 preset kamera unik
- [ ] Semua `arms` berupa list
- [ ] Semua `cam.z` di 1.0–1.6
- [ ] `guest` ada di setiap shot kalau ada tamu
- [ ] Lumi tidak menutupi wajah/caption

---

## Motion plan v4.5 — anti-template

```json
"layouts": [
  {"mode": "CLOSEUP_EMPHASIS", "on_line": 0, "target": "boca", "z": 1.46},
  {"mode": "SPOTLIGHT_EFFECT", "on_line": 1, "target": "lumi",
   "dim": 0.58, "cone": true},
  {"mode": "INFOGRAPHIC_CARD", "on_line": 2, "max_span": 3.7,
   "card": {"kind": "steps", "title": "...", "accent": "#1F6F78",
            "steps": ["...", "...", "..."]}}
]
```

- **Wajib `on_line`** (indeks dialog shot). Pipeline mengubahnya jadi detik
  setelah TTS tahu durasi asli (`bind_line_motion`). Jangan pakai `from`/`to`
  hardcoded untuk episode baru.
- `SPOTLIGHT_EFFECT` **maks 2/episode**, hanya fokus/rahasia/gelap/twist;
  dilarang di analogi outdoor terang.
- `CLOSEUP_EMPHASIS` hanya hook / shock / CTA; `target` = pembicara baris itu.
  Boleh `boca`, `lumi`, atau `guest`.
- `INFOGRAPHIC_CARD` hanya mekanisme/sebab-akibat/perbandingan; 2–3 langkah,
  fakta dari naskah. Kartu menutupi aktor; jangan taruh di hook.
- **WIDE + props = mode utama.** Shot tanpa layout sah kalau ada prop atau key
  beranimasi; jangan paksa efek.
- Dua layout bersebelahan tidak boleh mode sama.
- `keys` numerik diskalakan otomatis oleh `scale_shot_timings()` ke durasi VO
  nyata; `on_line` untuk layout/prop tetap lebih presisi.

Blocking:

| Situasi | Boca | Tamu | Prop |
|---|---|---|---|
| solo kiri | 340 | — | kanan 720 / atas 540 |
| solo kanan | 700 | — | kiri 240 / atas 540 |
| dialog | 300 | 640 (step 610) | atas 540 |

## Scene (v4.3)

Sudah SVG tajam (dipakai otomatis): `city_street`, `classroom`,
`mountain_sunset`, `park_evening`, `city_top`, `data_center`, `market`,
`phone_inside`, `bedroom`, `airport_svg`, `sky_flight`. Scene lain masih
`make_cartoon` (lebih lembut).

## Props (v4.3)

```json
"props": [{"id": "clock", "t_in": 0.9, "t_out": 6.0, "x": 540, "y": 300,
           "h": 320, "beat": true, "badge": "2 jam?"}]
```

- Prop beranimasi penuh: `clock` (jarum), `phone` (scroll), `hourglass`
  (pasir+flip), `bulb` (denyut), `coin_stack` (koin berputar).
- Prop penerbangan (v4.4): `airplane_jet`, `wing_airfoil`, `hand_wind`,
  `glider_plane`, `lift_vs_weight`.
- `beat: true` → `h 280–480`; non-beat `h 180–520`.
- Band aman: `y 250–340` (atas kepala) atau samping `x <= 220` / `x >= 860`.
  Jangan di `y 400–760` tengah — menutupi wajah.
- Prop tidak tampil saat `INFOGRAPHIC_CARD` aktif.

Aturan kamera zona aman: `z 1.0–1.08` wide, `1.18–1.26` medium,
  `1.34–1.45` reaction close-up (aktor ikut membesar 0,55× dari delta zoom).
