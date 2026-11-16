# MOTION SYSTEM — BOCA renderer

**Framework:** Python + Pillow (frame-by-frame) + ffmpeg. Tidak ada Remotion/GSAP;
semua "hook" di bawah adalah fungsi Python murni yang deterministik terhadap `t`,
di `motion.py`.

## 1. Lapisan (layer) — wajib terpisah

| # | Layer | Isi | Penggerak |
|---|---|---|---|
| 1 | Background | PNG scene 1350×2400 | pan `fx/fy` + zoom `z` + **kamera napas** (`use_camera_breath`) |
| 2 | Ambient | awan, glow, partikel, uang melayang | `use_ambient` (prosedural, parallax per elemen) |
| 3 | Midground prop | objek yang menempel di scene | ikut layer 1 (baked di PNG) |
| 4 | Main subject | Boca, Lumi, tamu | keyframe `keys` + **idle napas** (`use_breath`) + mouth + blink |
| 5 | UI/HUD | progress bar, chip seri, rolling hari | `use_hud` |
| 6 | Caption | subtitle karaoke | `Subtitle.draw` + `use_word_pop` |
| 7 | Transition | speed-line wipe | `use_speed_lines` (0.30 s tiap shot) |

## 2. Easing (tidak ada `linear` untuk entrance/exit)

| Hook | Kurva | Dipakai untuk |
|---|---|---|
| `use_ease_out_cubic` | 1-(1-u)³ | slide, settle |
| `use_ease_out_expo` | 1-2^(-10u) | counter, kamera |
| `use_spring_pop` | 0 → 1.08 → 1.0 | chip HUD, badge, pop-in |
| `use_word_pop` | 1 → 1.09 → 1.0 (160 ms) | kata caption yang sedang diucapkan |
| `use_ease_in_out` | smoothstep | loop ambient |

## 3. Living World — minimal 2 elemen ambient per scene

Profil otomatis dari nama scene (`_PROFILE` di `motion.py`):

| Profil | Scene | Ambient aktif |
|---|---|---|
| `sky` | sky, city_top, atmosphere, sunset | awan 2 lapis parallax + glow matahari berdenyut + partikel |
| `street` | city_street, park*, garden, market, airport, playground | awan + glow + debu/daun melayang |
| `night_sky` | space, galaxy | bintang berkelip (34 titik, fase acak) |
| `night` / `night_forest` | bedroom_night, dark_forest | kunang-kunang melayang + kedip |
| `rain` | rain_cloud | garis hujan diagonal 26 jalur |
| `water` | underwater | gelembung naik + goyang |
| `money` | bank, money_print, stock_board | koin melayang + kilau diagonal |
| `cold` | lake_ice | salju turun + awan |
| `interior` | classroom, kitchen, bank, data_center, body_inside, … | debu halus melayang |

Aturan:
- Semua gerak ambient memakai **sine/cosinus kontinu** dengan fase acak per scene,
  jadi tidak pernah sinkron dan tidak pernah berhenti.
- Kecepatan parallax awan 6–20 px/s, berlapis (lapisan belakang lebih lambat).
- Ambient digambar **di bawah karakter**, di atas background.

## 4. Karakter — micro-animation

| Gerak | Implementasi | Nilai |
|---|---|---|
| Napas / idle | `use_breath(seed, t)` | ±2,4 px vertikal, 1,35 rad/s, fase beda per aktor |
| Bicara | `draw_mouth` + envelope audio | amplitudo ikut LUFS per frame |
| Kedip | `draw_blink` | tiap ±4 s, 120 ms |
| Follow-through | keyframe `keys` (`arms`, `step`, `pose`) | rotasi sendi dari sprite rig |

## 5. HUD & UI

- **Progress bar** tipis 7 px di atas, lebar terinterpolasi `t/total`,
  warna merah → emas setelah 82% episode.
- **Chip seri** (`BOCA · KYB`) pop-in spring 0 → 1.08 → 1.0 dalam 450 ms.
- **Rolling counter** `HARI 04`: 0 → 04 dengan ease-out expo 700 ms (tidak pernah snap).

## 6. Transisi

- Bukan hard cut: `use_speed_lines` menggambar 16 garis kecepatan diagonal,
  arah bergantian per shot (kiri/kanan), memudar dalam **0.30 s**.
- Kamera tidak pernah diam: `use_camera_breath` memberi offset ±2–3 px sinusoidal.

## 7. Caption dinamis

- Kata aktif: skala spring 1 → 1.09 → 1.0 selama 160 ms, warna highlight,
  naik 4 px.
- Kata yang belum diucapkan tidak digambar (muncul tepat saat audio sampai).

## 8. Aturan pacing

- Setiap shot punya minimal 1 state change (ambient selalu bergerak).
- Visual hook tiap ≤3 s: keyframe pose/ekspresi atau pan kamera di tiap shot
  (storyboard sudah menjamin ≥4 scene & ≥3 preset kamera per episode).
- Durasi ambient tidak dipotong saat shot berganti — fase memakai `t` global,
  jadi gerak tidak "reset".

## 9. Anggaran performa

| Bagian | Biaya |
|---|---|
| crop + resize scene | ±8 ms/frame |
| `use_ambient` (setelah optimasi) | ±17 ms/frame |
| sprite + mouth + caption | ±40 ms/frame |
| **total** | ±250–300 ms/frame @1080×1920, 30 fps |

Render 90 s ≈ 2700 frame ≈ 12–14 menit di perangkat ini.

## 10. Hook pelengkap (opt-in)

| Hook | Fungsi | Status di BOCA |
|---|---|---|
| `use_loupe(im, t, pop_t, src, at, r, zoom)` | gelembung kaca pembesar: crop detail frame, spring pop 0→1.08→1.0, ring tebal + garis penghubung | tersedia; dipakai bila storyboard menandai field `loupe` |
| `use_rolling_value(t, dur, target)` | odometer 0→target ease-out expo | dipakai HUD `HARI nn` |
| `use_progress_bar(...)` | bar terinterpolasi + glow di ujung | dipakai HUD |

Catatan: format BOCA tidak memakai daftar angka berbaris (income/expense),
jadi aturan *staggered list* tidak relevan; bila nanti ada episode daftar,
pakai `stagger = 90 ms` + `use_ease_out_cubic` per baris.

## 11. Layer parallax (v4.1)

`make_cartoon.build_fx_layers(scene)` mengembalikan 2 layer transparan
(setengah resolusi 675×1200, di-upscale saat komposit):

| Layer | Isi | Faktor kamera |
|---|---|---|
| `atm` | awan lembut / bintang / gelembung / berkas cahaya | **0,45×** |
| `fg` | bokeh gelap sudut + tepi bawah (depth framing) | **1,30×** |
| background PNG | midground (bangunan, pohon, jalan) | 1,00× |

`layer_crop()` memotong tiap layer dengan offset `ox × faktor`, jadi saat kamera
pan, langit bergerak lebih pelan daripada tanah → parallax nyata.
Bila `atm` ada, `use_ambient(..., clouds=False)` supaya awan tidak dobel.

## 12. Schema `props` (visual storytelling)

```json
"props": [
  {"id": "clock", "t_in": 0.9, "t_out": 6.0, "x": 862, "y": 520, "h": 210,
   "anim": "pop_float", "badge": "2 jam?", "loupe_from": [540, 900]}
]
```

| Field | Arti |
|---|---|
| `id` | ikon di `props.py`: `clock, phone, coin_stack, wallet, money_note, hourglass, bulb, chart, calendar, heart, star, arrow, badge, dot` |
| `t_in` / `t_out` | waktu lokal shot (detik) |
| `x` / `y` / `h` | posisi pusat & tinggi di frame 1080×1920 |
| `anim` | `pop_float` (default), `tilt` |
| `badge` | label pil di bawah ikon |
| `loupe_from` | `[x, y]` titik detail yang diperbesar gelembung loupe |

Perilaku render:
- entrance: `use_spring_pop(..., 1.12)` (0 → 1.12 → 1.0, 420 ms)
- exit: `use_ease_out_expo` scale-down 300 ms terakhir
- idle: `sin(t*3 + seed) * 8px` + tilt ±2°
- `loupe_from` → `use_loupe()` mulai `t_in + 0,30 s`

## 13. Elastic actor & kamera

| Fitur | Implementasi |
|---|---|
| Squash & stretch | `use_squash(local, t_change)` → `scaleY 1 → 0.92 → 1.04 → 1`, `scaleX = 1/scaleY`, anchor di `ground` |
| Impuls otomatis | tiap key dengan `(expr, pose, arms)` berubah + awal shot |
| Lumi tilt | rotasi ±3° (`sin(local*1.9)`) saat tidak bicara |
| Kamera | `use_ease_out_cubic(prog)` untuk `fx/fy/z` (bukan linear) |
| Shake | `use_camera_shake(local, t_shock, 8)` — 0,42 s, decay eksponensial |

## 14. Caption & HUD safe-zone

- **Satu track caption** (`caption` besar). `caption_adult` tetap di data untuk
  SEO/aksesibilitas, **tidak digambar**.
- Blok caption berakhir di `CAPTION_BOTTOM = 1570`, maksimum 2 baris → aman di
  lower-third.
- HUD hanya di `y < 220`: progress bar 0–7 px, chip seri 34–72 px.
- `line_gap 0,16 s` + `lead_in 0,22 s` → tidak ada dead-air > 0,5 s.

## 15. Zoom & aktor

`z` kini menggerakkan kamera **dan** aktor:
`h_aktor = h_key × (1 + (z − 1) × 0,55)` (dikuantisasi ke grid 8 px agar cache
sprite tetap kecil). Preset yang disarankan:

| Preset | `z` | Pemakaian |
|---|---|---|
| Wide | 1,00–1,08 | establishing, jalan |
| Medium | 1,18–1,26 | penjelasan biasa |
| Reaction close-up | 1,34–1,45 | reaksi `shock`, kalimat punchline |

Batas aman: `h ≤ ground + 260` supaya kepala tidak keluar frame.

## 16. Layout per beat (v4.3)

`Shot.layouts` opsional; tiap rentang ≤ 3,8 s (target 2,5–3,5 s), menutup
seluruh durasi shot, dan dinormalkan otomatis ke durasi VO nyata.

| Mode | Efek |
|---|---|
| `WIDE_STAGE` | default |
| `INFOGRAPHIC_CARD` | aktor mengecil 0,52× ke kiri bawah, kartu 820 px pop-in spring |
| `CLOSEUP_EMPHASIS` | `z` 1,40–1,55 ease-out-expo, aktor fokus ke tengah, aktor lain digeser keluar |
| `SPOTLIGHT_EFFECT` | mask gelap 8 langkah + elips/cone di subjek, digambar sebelum aktor |

Kartu: `kind` = `compare` | `checklist` | `steps`; frame dibakar 12 fps di
`Art.build()` (runtime hanya buka PNG + paste). Urutan gambar:
`plate → clouds → ambient → spotlight → aktor → prop → kartu → fg → HUD → badge → subtitle`.

## 17. Prop SVG besar (v4.3)

`props_svg.py` menyediakan `clock`, `phone`, `hourglass`, `bulb`, `coin_stack`
(h 280–480, animasi scripted: jarum berputar, layar scroll, pasir + flip,
cahaya berdenyut, koin berputar). Prop beat wajib
`beat: true` dan `h 280–520`; letakkan di band atas `y 250–340` atau samping
`x ≤ 220` / `x ≥ 860`, bukan di depan wajah.

## 18. HUD 1,5× & badge kaki

Chip `BOCA · KYB` (font 33, tinggi 56, `#111827` 85%), `HARI nn` dengan pil
kontras, progress bar 10 px, semua `y < 190`. Badge pembicara berupa pil di
bawah kaki aktor (`ground + 18`, clamp `CAPTION_BOTTOM − 60`), bukan chip di
atas subtitle.
