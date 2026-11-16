# BOCA Character System v2

Cast, aturan kemunculan, dan kontrak produksi karakter. Melengkapi
`STORY_ARCHITECTURE.md` (naratif) dan `SCENE_MOTION_SPEC.md` (render).

---

## 1. Prinsip

1. **Boca** = host tetap, desain **LOCKED** (Content Bible §2). Tidak berubah.
2. **Lumi** = sidekick tetap. Boleh bicara, tapi tidak boleh menjelaskan fakta.
3. **Karakter tamu** = boleh dibuat, **maksimal 1 per episode**, dan hanya kalau
   cerita memang butuh lawan bicara atau pemilik situasi.
4. Maksimal **3 suara** per episode. Tidak pernah lebih.
5. Karakter tamu **tidak boleh** lebih pintar dari Boca. Tugasnya bertanya.

> "Jangan menambah sidekick permanen" (Content Bible) tetap berlaku.
> Tamu bersifat **berulang**, bukan sidekick baru yang ikut di semua episode.

---

## 2. Cast tetap

### 2.1 Boca — host

| Aspek | Nilai |
|---|---|
| id | `boca` |
| Visual | sesuai Content Bible §2 (LOCKED) |
| Ekspresi | `shock` `neutral` `happy` `confused` `focus` `sleepy` |
| Pose | `stand` `walk` `point` `think` `read` `wave` `cheer` `celebrate` `run` |
| Suara | Gemini TTS `Puck` · fallback Edge `id-ID-ArdiNeural` |
| Peran | EXPLAINER (55–70% baris) |

### 2.2 Lumi — sidekick

| Aspek | Nilai |
|---|---|
| id | `lumi` |
| Visual | blob cahaya emas `#FFD24A`, outline tinta, tinggi 25–30% Boca |
| Ekspresi | `happy` `shock` |
| Pose | `float` `wave` `point` `cheer` |
| Suara | Gemini TTS `Aoede` · fallback Edge `id-ID-GadisNeural` |
| Peran | REACTOR (10–20% baris) — **tidak boleh** menjelaskan fakta |

---

## 3. Cast tamu (6 karakter berulang)

Setiap tamu punya **rig terbatas**: 4 ekspresi × 3 pose = 12 sprite.
Ini menjaga biaya produksi tetap wajar.

| id | Nama | Siapa | Fungsi cerita | Episode | Suara (Gemini) |
|---|---|---|---|---|---|
| `ardi` | Ardi | anak 10 th, tetangga Boca | penanya polos (proxy penonton) | 03, 07, 19, 29 | `Fenrir` |
| `bu_ratna` | Bu Ratna | pemilik warung, 40-an | pemilik situasi pasar/harga | 06, 13, 22, 26 | `Kore` |
| `pak_darno` | Pak Darno | montir, 50-an | analogi mesin & sistem | 05, 10, 12 | `Charon` |
| `sari` | Sari | kakak SMA, 16 th | analogi dunia digital | 04, 08, 09, 11, 14 | `Leda` |
| `dokter_nia` | Dokter Nia | dokter, 30-an | analogi tubuh | 15, 16, 17, 18 | `Autonoe` |
| `kak_bima` | Kak Bima | teller bank, 25 th | analogi uang & bank | 23, 24, 25, 27, 28 | `Orus` |

Episode tanpa tamu (Lumi jadi ASKER): **20, 21, 30**.

### 3.1 Spesifikasi visual

| id | Kulit | Rambut | Pakaian | Aksesori | Ciri pengenal |
|---|---|---|---|---|---|
| `ardi` | `#E8B48A` | pendek, `#1B1B1B` | kaus `#F08A3C`, celana `#2B4C7E` | kacamata bulat `#231815` | kacamata + kaus oranye |
| `bu_ratna` | `#D9A066` | sanggul, `#2A1B12` | kebaya `#8B5A2B`, kain `#C46A3A` | anting emas | sanggul + kain batik |
| `pak_darno` | `#C98F63` | pendek + kumis, `#3A2A20` | overall `#2B4C7E` | topi montir `#F4B942` | overall + kunci pas |
| `sari` | `#E8B48A` | kuncir, `#1B1B1B` | hoodie `#6C5CE7` | headphone `#231815` | hoodie ungu + headphone |
| `dokter_nia` | `#E3B491` | pendek, `#1B1B1B` | jas putih `#FFFFFF` | stetoskop `#D7263D` | jas + stetoskop |
| `kak_bima` | `#E0AC80` | rapi, `#231815` | kemeja `#4A90D9`, dasi `#D7263D` | name tag | kemeja biru + dasi |

Semua memakai **outline tinta `#231815`** dan gaya flat-vector yang sama dengan Boca.
Proporsi: kepala ± 40% tinggi badan (Boca 45% — tamu dibuat sedikit lebih realistis).

### 3.2 Ekspresi & pose tamu

| Aspek | Nilai |
|---|---|
| Ekspresi | `neutral` `happy` `shock` `confused` |
| Pose | `stand` `point` `wave` |
| Tinggi render | 600–680 px (Boca 640–700) |

### 3.3 Aturan kemunculan

1. Maksimal **1 tamu** per episode.
2. Tamu muncul di **≥ 2 shot** — bukan cameo sekali lewat.
3. Tamu bicara **1–3 baris**, masing-masing ≤ 12 kata.
4. Tamu harus punya **alasan berada di lokasi** (pemilik warung, montir, dokter).
5. Tamu tidak boleh muncul di CTA kecuali ikut menutup cerita.
6. Tamu **tidak** boleh memakai `prop: prism` (itu properti Boca).

---

## 4. Kontrak render karakter (untuk implementasi)

Karakter tamu **tidak** dibuat sebagai fungsi Python terpisah. Dibuat dari spec JSON:

```json
{
  "id": "ardi",
  "name": "Ardi",
  "role": "asker",
  "height": 620,
  "head_ratio": 0.40,
  "skin": "#E8B48A",
  "hair": {"style": "pendek", "color": "#1B1B1B"},
  "face": {"glasses": "bulat", "brows": "tebal"},
  "outfit": {"top": "#F08A3C", "bottom": "#2B4C7E", "shoes": "#231815"},
  "accessory": "kacamata_bulat",
  "expressions": ["neutral", "happy", "shock", "confused"],
  "poses": ["stand", "point", "wave"],
  "voice": {"gemini": "Fenrir", "edge": "id-ID-ArdiNeural"}
}
```

File: `production/characters/<id>.json`.
Renderer: `make_guest.py` (belum ada — masuk backlog aset).

Sampai renderer itu ada, scene sheet boleh **menyebut** tamu di `cast.guest`,
tetapi episode **tidak boleh dirender**. Validator akan menandainya.

---

## 5. Pemetaan suara

| Karakter | Gemini | Edge fallback |
|---|---|---|
| Boca | `Puck` | `id-ID-ArdiNeural` |
| Lumi | `Aoede` | `id-ID-GadisNeural` |
| Ardi | `Fenrir` | `id-ID-ArdiNeural` |
| Bu Ratna | `Kore` | `id-ID-GadisNeural` |
| Pak Darno | `Charon` | `id-ID-ArdiNeural` |
| Sari | `Leda` | `id-ID-GadisNeural` |
| Dokter Nia | `Autonoe` | `id-ID-GadisNeural` |
| Kak Bima | `Orus` | `id-ID-ArdiNeural` |

Catatan: fallback Edge hanya punya 2 suara Indonesia. Kalau kuota Gemini habis,
**tamu sebaiknya dihindari** supaya tidak ada dua karakter bersuara sama.

---

## 6. Biaya aset

| Item | Jumlah | Status |
|---|---|---|
| Rig Boca | 6 expr × 9 pose | ✅ ada |
| Rig Lumi | 2 expr × 4 pose | ✅ ada |
| Rig tamu | 4 expr × 3 pose = 12 sprite | ❌ belum |
| 6 tamu | 72 sprite + 6 spec JSON | ❌ belum |
| Scene v2 | 24 background | ❌ belum |

---

## 7. Do / Don't

**DO**
- Buat tamu kalau ada pertanyaan yang lebih wajar diucapkan orang lain.
- Beri tamu satu ciri visual yang langsung dikenali (kacamata, sanggul, stetoskop).
- Pakai tamu berulang supaya penonton mengenalinya.

**DON'T**
- Menambah karakter ke-4 dalam satu episode.
- Membuat tamu yang hanya muncul sekali lalu tidak pernah kembali.
- Membuat tamu yang menjelaskan lebih banyak dari Boca.
- Mengubah desain Boca.
