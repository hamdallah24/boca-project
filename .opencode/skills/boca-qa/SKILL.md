---
name: boca-qa
description: Menjalankan validator storyboard, membaca arti setiap error, merender episode, memeriksa QA video, dan memutuskan boleh-tidaknya publish ke YouTube. Gunakan sebelum render, saat validator gagal, saat QA video gagal, atau saat user minta upload/publish episode BOCA.
metadata:
  author: boca-character
  version: "1.0"
---

# BOCA QA — validasi, render, publish

Urutannya tidak boleh dibalik: **validasi → konversi → render → QA → publish**.
Publish tanpa gate adalah kesalahan paling mahal di pipeline ini.

## 1. Validasi storyboard

```bash
python3 tools/check_storyboards.py production/storyboards/
```

Harus `PASS` dan `0 error` sebelum lanjut. Jangan menambal error dengan
menghapus aturan — perbaiki ceritanya.

`--strict` menambah satu cek: scene v2 yang belum ada di `make_cartoon.py`
dianggap error. Pakai `--strict` hanya kalau episode memang harus bisa dirender
sekarang.

## 2. Konversi ke plan

```bash
python3 tools/sceneplan_to_plan.py BOCA-Dxx            # dry-run, lihat ringkasan
python3 tools/sceneplan_to_plan.py BOCA-Dxx --write    # tulis production/plans/
```

Converter memperingatkan kalau ada scene yang belum ada di kode. Itu **bukan**
error validasi — tapi artinya episode belum bisa dirender.

## 3. Render

```bash
python3 daily_build.py --plan BOCA-Dxx --no-render   # cek gate tanpa render
python3 daily_build.py --plan BOCA-Dxx               # render + QA
python3 daily_build.py --plan BOCA-Dxx --force       # render ulang
```

## 3b. Error layout/prop v4.5 (rulebook motion)

- `scene_family / motion_motif wajib diisi` → isi tema visual + motif gerak
  episode sebelum menyusun shot.
- `layout ... wajib on_line` → layout masih pakai detik tebakan; ikat ke indeks
  dialog (`on_line`/`to_line`).
- `on_line di luar dialog` / `to_line < on_line` → indeks baris salah.
- `spotlight N (> 2/episode)` → buang efek; pilih hanya momen fokus/twist.
- `spotlight target bukan cast` / `closeup target bukan cast` → `target` harus
  `boca`, `lumi`, atau `guest`.
- `closeup target 'x' != speaker 'y' baris N` → close-up harus pada pembicara
  baris yang diikat.
- `layout ... mode sama berurutan` → ganti salah satu mode.
- `closeup wajib target` → tambahkan `target`.
- `shot Xs butuh >= 2 layout atau prop/key beranimasi` → beri prop bermakna,
  bukan memaksa layout.
- `layout ... > 3.8s` (episode lama) → pecah jadi 2–3,5 s.
- `card.kind` hanya `compare` / `checklist` / `steps`; `card.left/right.value`
  harus angka.
- Scene `mountain_sunset` valid (SVG), bukan error.

Kalau motion terasa tidak sinkron dengan suara, cek `scale_shot_timings()` dan
`bind_line_motion()` di `boca_pipeline.py`: `est_seconds` ≠ durasi VO nyata.

## 4. Gate publish (keempatnya wajib)

| Gate | Syarat | Cara memenuhi |
|---|---|---|
| Plan approved | `status == "approved"` | `python3 daily_build.py --approve BOCA-Dxx` |
| Fakta | `facts_status == "verified"` (bukan `verified_basic`) | riset + 2 sumber untuk topik high-risk |
| QA video | semua 11 cek lolos | lihat tabel di bawah |
| Kredensial | token platform valid | cek `production/credentials.json` |

Kalau satu gate gagal, **jangan** pakai `--force` untuk melewatinya.

### 11 cek QA otomatis

| Cek | Ambang |
|---|---|
| file exists | mp4 ada |
| duration ~ target | ±2.5 s |
| resolution 1080x1920 | persis |
| size > 1MB | ya |
| loudness | -16.5 … -12.0 LUFS |
| true peak | ≤ -1.0 dBTP |
| no "Adek" in VO | tidak ada |
| all shots have dialogue | ya |
| all lines have captions | ya |
| caption bottom safe | ≤ 1600 px |
| srt + poster | tertulis |

## 5. Publish

```bash
python3 daily_build.py --plan BOCA-Dxx --publish
```

atau manual:

```bash
python3 publish.py --payload production/payloads/BOCA-Dxx.json \
  --only youtube_shorts --privacy public --publish
```

Default platform: **YouTube Shorts saja**. Platform lain diaktifkan lewat env
`BOCA_PLATFORMS`. Detail di `references/publish.md`.

## 6. Katalog error validator

| Pesan | Arti | Perbaikan |
|---|---|---|
| `total kata 175 (tier 60s: 180–200)` | naskah kurang/lebih | tambah 1 kalimat pendek, jangan tambah kata di tengah kalimat |
| `estimasi 55.1s (tier 60s: 56–64s)` | durasi meleset | ikut budget kata, bukan perasaan |
| `jumlah shot 6 (tier 60s: 7–9)` | shot kurang | pecah satu shot panjang jadi dua |
| `scene unik 3 (< 4)` | background monoton | ganti satu scene dari library |
| `preset kamera unik 2 (< 3)` | kamera statis | pakai C1/C4/C7 bergilir |
| `Lumi tidak bicara` | tidak ada `who: "lumi"` | beri 1 reaksi pendek |
| `tamu 'ardi' muncul di 1 shot (< 2)` | cameo | tambah keyframe tamu di shot lain |
| `tamu bicara 4 baris (harus 1–3)` | tamu terlalu banyak | pindahkan satu baris ke Lumi |
| `beat 'twist' tidak ada` | cerita datar | tambah pengecualian/konsekuensi |
| `who 'sari' tidak ada di cast` | tamu tidak dideklarasikan | isi `cast.guest` |
| `arms harus list` | `"arm": 2` | ubah jadi `"arms": [2]` |
| `cam.z harus 1.0..1.6` | zoom berlebihan | maksimal 1.45 |
| `kata terlarang 'kakak'` | sapaan | ganti dengan nama atau "kamu" |
| `'kamu' muncul 2× (> 1)` | sapaan berulang | ganti salah satunya |
| `pembuka sama ('market')` | dua episode berurutan | ganti pembuka salah satu |
| `berbagi 3 scene (> 2)` | episode terlalu mirip | tukar satu scene |
| `pola hook sama (H2)` | hook berulang | ganti pola H1–H6 |
| `analogi sama dengan BOCA-D22` | analogi dipakai ulang | cari analogi baru |

Error antar-episode muncul di bagian **"Cek antar-episode"** setelah daftar file.

## 7. Kalau render gagal (bukan validator)

| Gejala | Penyebab | Perbaikan |
|---|---|---|
| `KeyError: 'bedroom'` | scene v2 belum ada | ganti ke scene v1, atau implementasikan dulu |
| `KeyError` di sprite | `arms` angka / pose salah | cek enum |
| video tanpa suara | TTS gagal / kuota habis | cek log, fallback Edge |
| durasi jauh dari target | cache TTS lama | hapus cache baris itu, render ulang |
| caption menutupi wajah | posisi Boca terlalu rendah | naikkan `ground` |

Kuota Gemini TTS gratis **10 request/hari**. Naskah harus final sebelum render;
mengubah satu baris hanya merender ulang baris itu (cache per-hash).

## 8. Setelah publish

Catat di `production/state.json`: `status: published`, `uploads.youtube_shorts`,
`built_at`, `qa_pass`. Jangan menandai `published` sebelum upload benar-benar
mengembalikan URL.

## Selesai kalau

- [ ] Validator PASS 0 error
- [ ] `qa_pass: true` dengan 11 cek
- [ ] `facts_status: verified`
- [ ] `status: approved` sebelum render
- [ ] URL upload tercatat di `state.json`
