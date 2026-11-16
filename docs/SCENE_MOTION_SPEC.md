# BOCA Render Contract — Scene & Motion Spec v4.1

Dokumen ini adalah **kontrak teknis**. Apa pun yang tidak ada di sini **tidak bisa dirender**.
Semua nilai di bawah diambil langsung dari kode (`boca_pipeline.py`, `make_boca.py`, `make_cartoon.py`, `make_music.py`).

> Pemilik: pipeline `boca-character` · Terakhir diperbarui: 2026-11-14

---

## 1. Kanvas, kamera, dan safe area

| Item | Nilai |
|---|---|
| Output | 1080 × 1920 (9:16), 30 fps, H.264 + AAC |
| Kanvas scene | **1350 × 2400** (1.25× output) → ruang gerak kamera 270 × 480 px |
| Crop kamera | 1080 × 1920, lalu di-resize ke output |
| Caption | bawah, aman sampai **y = 1570 px** (QA akan gagal kalau lewat) |
| Durasi target | **45 / 60 / 90 detik** (ikut registry Content Bible, toleransi ±4 s) |
| Jumlah shot | 45 s → **5–7** · 60 s → **7–9** · 90 s → **9–12** |

### Skema `cam`

```json
"cam": { "fx": [0.30, 0.68], "fy": [0.35, 0.62], "z": [1.00, 1.25] }
```

- `fx`, `fy` = posisi titik crop, **0.0–1.0**, dari awal shot → akhir shot (pan).
- `z` = zoom, **1.0–1.6**. `1.0` = lebar penuh, `1.3` = 1.3× lebih dekat.
  Di atas `1.6` gambar mulai blur karena upscale.
- `cam` **wajib ada di setiap shot** dan **tidak boleh** semua shot memakai nilai yang sama.

**Preset kamera (pakai kode ini, jangan mengarang):**

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

---

## 2. Enum yang valid (HARAM mengarang nilai baru)

### 2.1 `scene` — Library v1 (sudah ada di kode, 8 buah)

| id | Isi | Cocok untuk |
|---|---|---|
| `park` | taman siang, matahari kanan, bukit, awan | pembuka/penutup netral |
| `park_evening` | taman senja, langit ungu-oranye | penutup refleksi |
| `park_sunleft` | taman, matahari kiri (komposisi beda) | variasi pembuka |
| `sky` | langit biru + awan tebal | konsep langit/cuaca |
| `space` | angkasa, bintang, Bumi mini | skala besar, kosmos |
| `prism` | prisma + spektrum cahaya | cahaya, warna, sains |
| `atmosphere` | lapisan atmosfer + orbit | ruang, satelit, lapisan udara |
| `sunset` | matahari terbenam, siluet | kesimpulan emosional |

### 2.2 `scene` — Library v2 (BELUM ada di kode, harus dibuat di `make_cartoon.py`)

Format: `id — nama | layer utama | props kunci | prioritas`

**P0 (wajib, 12):**
1. `bedroom` — kamar BOCA | dinding krem, jendela, ranjang, rak buku | lampu tidur, bantal, poster | P0
2. `bedroom_night` — kamar malam | dinding biru gelap, jendela + bulan + bintang | selimut, lampu tidur menyala | P0
3. `kitchen` — dapur | kabinet, kulkas, meja | toples, uang receh, piring | P0
4. `classroom` — kelas | papan tulis, meja murid, jendela | kapur, buku, globe | P0
5. `market` — pasar | lapak, tenda, keranjang | harga, buah, timbangan | P0
6. `city_top` — kota dari atas | blok gedung, jalan, taman kecil | awan, antena | P0
7. `city_street` — jalan kota | trotoar, lampu jalan, toko | rambu, bangku, halte | P0
8. `beach` — pantai | pasir, ombak, langit | kelapa, ember, kerang | P0
9. `underwater` — bawah laut | gradasi biru, gelembung, karang | ikan, rumput laut, cahaya atas | P0
10. `body_inside` — dalam tubuh | dinding organ lembut, pembuluh | sel, aliran darah, saraf | P0
11. `phone_inside` — dalam HP | papan sirkuit, chip, baterai | ikon, kabel, muatan | P0
12. `data_center` — pusat data | rak server, kabel, lantai | LED, kipas, paket data | P0

**P1 (8):**
13. `neuron_city` — kota neuron | jaringan saraf sebagai jalan | simpul, percikan sinyal | P1
14. `airport` — bandara | landasan, menara, pesawat | sayap, awan rendah | P1
15. `bank` — bank | gedung, loket, brankas | uang, buku tabungan, kunci | P1
16. `money_print` — percetakan uang | mesin cetak, gulungan | lembaran uang, tinta | P1
17. `stock_board` — bursa saham | papan grafik, lantai bursa | panah naik/turun, jam | P1
18. `lake_ice` — danau es | air gelap, gunung es, salju | bongkahan es, kabut | P1
19. `rain_cloud` — awan hujan | awan tebal, tetes air, matahari kecil | siklus air, angin | P1
20. `galaxy` — galaksi | nebula, bintang, pusaran | planet kecil, komet | P1

**P2 (4):**
21. `garden` — kebun | tanah, tanaman bertingkat | bibit, buah, air | P2
22. `dark_forest` — hutan gelap | pohon tinggi, kabut, cahaya celah | lentera, bayangan | P2
23. `house_cutaway` — rumah potongan melintang | ruang tamu, kamar, atap | router, kabel, sinyal | P2
24. `playground_clock` — taman jam raksasa | jam besar, ayunan, pasir | jarum jam, bola | P2

### 2.3 `expr` (Boca) — 6 nilai

`shock` · `neutral` · `happy` · `confused` · `focus` · `sleepy`

### 2.4 `pose` (Boca) — 9 nilai

`stand` · `walk` · `point` · `think` · `read` · `wave` · `cheer` · `celebrate` · `run`

### 2.5 `arms` (gestur tangan kiri) — 0–4

| nilai | arti |
|---|---|
| 0 | tangan turun (netral) |
| 1 | tangan ditekuk ke depan (memegang) |
| 2 | tangan menunjuk jauh |
| 3 | tangan terangkat (tanya/ide) |
| 4 | tangan ke bawah-depan (menunjuk bawah) |

`arms` **harus berupa list**, bukan angka tunggal. Contoh `"arms": [0, 3, 2]` = bergantian tiap `period` detik.
`period` default **0.8** detik.

### 2.6 `prop` — hanya `prism`

Selain itu tidak dirender. Maksimal **1 shot** per episode.

### 2.7 `sfx` — 5 nilai

`pop` · `whoosh` · `sparkle` · `chime` · `boing`

Format: `[offset_detik, "nama", gain_0.0-1.0]`. Maksimal **4 SFX** per episode.
`sparkle` otomatis memicu efek visual kilau di 0.9 detik pertama shot.

### 2.8 Lumi (`lumi`)

| Field | Nilai valid |
|---|---|
| `expr` | `happy` · `shock` |
| `pose` | `float` · `wave` · `point` · `cheer` |
| `x` | 700–950 (kanan frame), atau 150–380 kalau Boca pindah kanan |
| `y` | 1000–1300 |
| `h` | 220–260 |

Lumi **wajib bicara** minimal 1 baris per episode (`who: "lumi"`).

---

## 3. Skema `keys` (acting Boca)

```json
{ "t": 0.0, "expr": "shock", "pose": "walk", "arms": [0],
  "x": -300, "ground": 1400, "h": 640 }
```

| Field | Arti | Rentang |
|---|---|---|
| `t` | detik lokal dalam shot, **naik** | 0 → durasi shot |
| `x` | posisi horizontal (pusat tubuh) | -350 (luar kiri) … 950 (kanan) |
| `ground` | garis tanah (kaki) | 1330–1440 |
| `h` | tinggi badan | 520 (jauh) … 760 (dekat) |
| `arms` | list gestur | `[0]` … `[0,3,2]` |
| `period` | detik per gestur | 0.6–1.0 |
| `prop` | `"prism"` | opsional |

Interpolasi hanya untuk `x`, `ground`, `h`. **`expr`/`pose`/`arms` berganti mendadak** (cut), jadi:

- Jangan taruh dua key berurutan dengan `pose` sama tapi `expr` beda dalam < 0.25 s.
- `pose: "walk"` butuh minimal 2 key supaya langkahnya bergerak.
- Boca tidak boleh diam > **2.5 detik** tanpa key baru.

---

## 4. Skema `dialogue` (VO + caption)

```json
{ "who": "boca",
  "text": "Kalimat yang diucapkan.",
  "caption": "Baris besar di layar",
  "caption_adult": "baris kecil penjelas" }
```

| Aturan | Nilai |
|---|---|
| `who` | `boca` / `lumi` |
| `text` | **≤ 14 kata**, 1 ide, bahasa sehari-hari |
| `caption` | **≤ 9 kata**, tanpa tanda baca akhir |
| `caption_adult` | ≤ 14 kata, boleh lebih teknis |
| Dilarang | "Adek", "dek", "adik", "kakak", "bunda", "sayang" |
| Sapaan | "kamu" boleh, maksimal 1× per episode |

**Budget waktu:** ~**0.33 detik/kata** + jeda 0.16 s antar baris.

> **Catatan render (penting).** TTS asli (Gemini `Puck`/`Aoede` maupun Edge
> `id-ID-ArdiNeural` +0%) bicara ~**0.45–0.50 detik/kata**, bukan 0.30. Karena itu
> kecepatan dinaikkan **di sumbernya**: `EDGE_RATE = "+47%"` → 0.4895 / 1.47 =
> **0.333 s/kata**. **Tidak ada `atempo`** — suara tidak pernah di-stretch.
> Kalau narasi tetap lebih panjang dari tier, video **dibiarkan lebih panjang**
> (QA: `duration >= target - 2.5`, tanpa batas atas). Kalau narasi lebih pendek,
> jeda visual ditambah maksimal **22%** (`MAX_PAD`) supaya tidak ada video senyap
> panjang.
>
> Backend default = **Edge** (`BOCA_TTS=edge`). `BOCA_TTS=gemini` hanya untuk
> eksperimen: Gemini tidak punya kontrol rate, jadi narasi akan ~0.49 s/kata dan
> video jadi lebih panjang. Cache TTS Gemini **tidak** dipakai ulang oleh Edge
> (dulu ini bug: narasi Edge ikut memutar audio Gemini yang lebih lambat).

| Durasi | Total kata | Baris dialog |
|---|---|---|
| 45 s | 135–150 | 10–14 |
| 60 s | 180–200 | 14–20 |
| 90 s | 270–300 | 20–30 |

---

## 5. VO / TTS

| Item | Nilai |
|---|---|
| Mesin utama | Gemini TTS `gemini-3.8-flash-tts` |
| Suara Boca | `Puck` |
| Suara Lumi | `Aoede` |
| Fallback | Edge TTS `id-ID-ArdiNeural` |
| Gaya | hangat, santai, seperti ngobrol, tanpa baby talk |
| Kecepatan | natural, tanpa mempercepat |
| Cache | per-hash teks — **mengubah 1 kata = 1 baris dirender ulang** |

Karena kuota Gemini gratis 10 req/hari, **naskah harus final sebelum render**.

---

## 6. Motif gerak (acting) — 8 pola wajib bergilir

| Kode | Nama | Pola key (relatif durasi shot L) |
|---|---|---|
| M1 | walk-in reveal | `t0 x=-300 walk` → `0.35L x=250 stand` → `0.70L x=260 point` |
| M2 | point-explain | `t0 stand [0]` → `0.30L point [2]` → `0.65L stand [1,3]` |
| M3 | think→lightbulb | `t0 think [1]` → `0.45L confused [1]` → `0.70L focus [3]` → `0.85L happy [0,3]` |
| M4 | prop demo | `t0 stand [0] prop` → `0.30L point [2] prop` → `0.70L happy [1,3] prop` |
| M5 | run-chase | `t0 x=-320 run` → `0.40L x=250 run` → `0.60L x=270 stand [2]` |
| M6 | wave-greet | `t0 wave [3]` → `0.40L happy [0,1]` → `0.80L point [2]` |
| M7 | celebrate | `t0 happy [0]` → `0.50L cheer [3]` → `0.80L celebrate [1,3]` |
| M8 | sleepy→focus | `t0 sleepy [0]` → `0.50L focus [1]` → `0.80L happy [2]` |

---

## 7. Aturan variasi (dicek otomatis, tidak bisa dinegosiasi)

1. Satu episode minimal **4 `scene` id berbeda**.
2. **Dua episode berurutan tidak boleh** membuka dengan `scene` yang sama.
3. Dalam **5 episode berurutan**, satu `scene` id maksimal muncul di **3 episode**
   (klaster keuangan D22–D28 butuh `market`/`bank` berulang).
4. Setiap shot **wajib** punya `cam`; minimal **3 preset kamera berbeda** per episode.
5. Motif gerak utama episode **≠** motif episode sebelumnya.
6. Setiap shot minimal **2 key** (kecuali shot < 3 detik → 1 key cukup).
7. `prop` maksimal 1 shot; `sfx` maksimal 4 per episode.
8. Lumi bicara **≥ 1 baris** per episode.
9. Semua `caption` ≤ 9 kata, semua `text` ≤ 14 kata.
10. Total estimasi durasi **sesuai tier** (45/60/90 ± 4 s).
11. Maksimal **1 karakter tamu** per episode (lihat `CHARACTER_SYSTEM.md`).
12. Setiap episode wajib punya blok `analogy` (lihat `STORY_ARCHITECTURE.md` §4).
13. Porsi bicara: **Boca ≥ 50%** baris, **Lumi ≤ 30%**. Lumi bereaksi, bukan
    ikut menjelaskan fakta.

---

## 8. Validasi

```bash
python3 tools/check_sceneplans.py production/sceneplans/
```

Skrip ini mengecek seluruh aturan di atas dan memberi kode error per baris.
**Dokumen dinyatakan selesai hanya kalau validator keluar dengan `PASS` 0 error.**

---

## 9. Lapisan animasi wajib (motion.py)

Sejak v4.1 renderer memakai `motion.py`. Kontraknya:

| Lapisan | Hook | Wajib |
|---|---|---|
| Kamera | `use_camera_breath(t)` | ya, semua shot |
| Ambient bawah karakter | `use_ambient(im, scene, t, seed)` | ya, minimal 2 elemen aktif |
| Idle aktor | `use_breath(seed, t)` | ya, semua aktor |
| Pop kata caption | `use_word_pop(t0, t)` | ya |
| HUD atas | `use_hud(im, t, ep, prog, font)` | ya |
| Transisi shot | `use_speed_lines(im, p, seed, dir)` | ya, 0,30 s pertama tiap shot |

Larangan:
- `linear` untuk entrance/exit/UI.
- Angka yang snap (counter harus `use_rolling_value`).
- Frame dengan latar 100% statis (ambient + kamera napas menutup ini).

Detail lengkap: `docs/MOTION_SYSTEM.md`.

## 10. Field opsional `props` (v4.1)

```json
{"id": "coin_stack", "t_in": 1.2, "t_out": 4.0, "x": 760, "y": 980,
 "h": 220, "anim": "pop_float", "badge": "Rp10.000", "loupe_from": [250, 1200]}
```

Aturan validator (`tools/check_storyboards.py`):
- `id` harus ada di `props.ids()`.
- `0 ≤ t_in < t_out`, `180 ≤ h ≤ 520` (prop beat wajib `280 ≤ h` dengan
  `"beat": true`).
- Prop beat diletakkan di band atas `y 250–340` atau samping `x ≤ 220` /
  `x ≥ 860` supaya tidak menutup wajah aktor.
- `loupe_from` (jika ada) harus `[x, y]`.
- Setiap shot > 2,5 s disarankan punya minimal 1 prop/badge (belum error).
