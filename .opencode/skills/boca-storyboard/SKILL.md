---
name: boca-storyboard
description: Menulis dan memperbaiki storyboard episode BOCA D01–D30 — hook, enam beat, analogi kehidupan sehari-hari, naskah VO, cast tamu, dan JSON production-grade. Gunakan saat user minta "buat episode", "naskah BOCA", "storyboard D07", "VO", "hook", "analogi", atau saat sebuah episode gagal validasi karena masalah cerita.
metadata:
  author: boca-character
  version: "1.0"
---

# BOCA Storyboard

Satu episode = satu hari = satu file. **Jangan** membuat lebih dari satu episode
dalam satu permintaan kecuali user meminta batch secara eksplisit.

> Prinsip induk: penonton tidak boleh mendengar "penjelasan" — mereka harus
> **menonton kejadian**. Setiap konsep abstrak wajib punya analogi konkret.

## Peta file

| Peran | Path |
|---|---|
| Source of truth (judul, CTA, fakta) | `/sdcard/Download/BOCA_Rencana_Konten_30_Hari.md` |
| Output utama | `production/storyboards/BOCA-Dxx.json` |
| Output manusia | `production/storyboards/BOCA-Dxx.md` — **generate**, jangan tulis tangan |
| Plan untuk render | `production/plans/BOCA-Dxx.json` (hasil converter) |
| Aturan cerita lengkap | `docs/STORY_ARCHITECTURE.md` |
| Cast & suara | `docs/CHARACTER_SYSTEM.md` |
| Kontrak render | `docs/SCENE_MOTION_SPEC.md` |

## Alur kerja (urutan wajib)

1. **Ambil hari.** Dari permintaan user (`D07`) atau tanggal. Baca bagian hari itu
   di Content Bible. **Judul disalin persis** — jangan diperbaiki gayanya.
2. **Cek registry** di bawah: seri, durasi, tamu. Jangan mengubah.
3. **Tulis hook** — baris pertama **wajib pertanyaan ke penonton** (diakhiri
   `?`, diucapkan `boca`), baru `gap` → `promise` sebagai teaser. Maksimal
   3 detik (4 detik untuk tier 90 s), maksimal 2 baris dialog. D04 ke atas
   tidak boleh dibuka dengan pernyataan/angka.
4. **Susun 6 beat** ke jumlah shot sesuai tier.
5. **Tulis analogi** di blok `analogy` (minimal 2 pemetaan).
6. **Tulis VO** sampai masuk budget kata.
7. **Susun shot** — muat skill `boca-visual` untuk scene, kamera, `keys`,
   `layouts`, dan `props` (v4.3: layout wajib untuk shot >= 6 s).
8. **Layout/prop v4.3** — jalankan
   `python3 tools/upgrade_storyboards_v43.py --episodes BOCA-Dxx` bila shot
   belum punya `layouts`; tambahkan `card` hanya dari fakta naskah.
9. **Validasi** — muat skill `boca-qa`. Wajib `PASS` 0 error.
10. **Generate MD**: `python3 tools/storyboard_to_md.py BOCA-Dxx`.

## Registry 30 hari (JANGAN diubah)

| Hari | Seri | Durasi | Tamu |
|---|---|---|---|
| 01 | KYB | 45 | — (sudah tayang, JANGAN disentuh) |
| 02 | KYB | 45 | — (sudah direkam, JANGAN disentuh) |
| 03 | KYB | 60 | `ardi` |
| 04 | KYB | 45 | `sari` |
| 05 | KYB | 60 | `pak_darno` |
| 06 | KYB | 45 | `bu_ratna` |
| 07 | KYB | 45 | `ardi` |
| 08 | BMM | 60 | `sari` |
| 09 | BMM | 60 | `sari` |
| 10 | BMM | 45 | `pak_darno` |
| 11 | BMM | 90 | `sari` |
| 12 | BMM | 45 | `pak_darno` |
| 13 | BMM | 60 | `bu_ratna` |
| 14 | BMM | 45 | `sari` |
| 15 | BMT | 45 | `dokter_nia` |
| 16 | BMT | 60 | `dokter_nia` |
| 17 | BMT | 45 | `dokter_nia` |
| 18 | BMT | 60 | `dokter_nia` |
| 19 | BMT | 45 | `ardi` |
| 20 | BMT | 45 | — (Lumi jadi ASKER) |
| 21 | BMT | 60 | — (Lumi jadi ASKER) |
| 22 | BBU | 60 | `bu_ratna` |
| 23 | BBU | 90 | `kak_bima` |
| 24 | BBU | 60 | `kak_bima` |
| 25 | BBU | 60 | `kak_bima` |
| 26 | BBU | 60 | `bu_ratna` |
| 27 | BBU | 60 | `kak_bima` |
| 28 | BBU | 60 | `kak_bima` |
| 29 | BLA | 60 | `ardi` |
| 30 | BLA | 90 | — (Lumi jadi ASKER) |

Seri: `KYB` sains sehari-hari · `BMM` teknologi · `BMT` tubuh · `BBU` ekonomi · `BLA` antariksa.

## Budget per tier

| Durasi | Shot | Total kata | Baris dialog |
|---|---|---|---|
| 45 s | 5–7 | 135–150 | 10–14 |
| 60 s | 7–9 | 180–200 | 14–20 |
| 90 s | 9–12 | 270–300 | 20–30 |

Estimasi: `0.30 detik/kata + 0.16 detik/baris`.

## Enam beat (wajib lengkap)

| # | Beat | Fungsi | Yang harus terjadi |
|---|---|---|---|
| 1 | HOOK | klaim → celah → janji | penonton bertanya "kok bisa?" |
| 2 | SETUP | situasi konkret | ada tokoh yang **mengalami** masalahnya |
| 3 | EXPLAIN | analogi inti | konsep abstrak jadi benda sehari-hari |
| 4 | TWIST | perluasan / pengecualian | ada hal yang **tidak** sesuai dugaan |
| 5 | PAYOFF | kembali ke setup | situasi awal sekarang masuk akal |
| 6 | CTA | ajakan | pertanyaan dari pengalaman penonton |

Kalau satu beat hilang, episode terasa seperti artikel yang dibacakan.

## Tiga peran dialog (maksimal 3 suara)

| Peran | Siapa | Porsi baris | Tugas |
|---|---|---|---|
| EXPLAINER | `boca` | 55–70% | menjelaskan dengan analogi, memegang alur |
| ASKER | tamu, atau `lumi` kalau tanpa tamu | 15–30% | pertanyaan polos mewakili penonton |
| REACTOR | `lumi` | 10–20% | reaksi emosional, punchline — **tidak** menjelaskan fakta |

- Boca **tidak boleh** menjawab pertanyaannya sendiri.
- Tamu bicara **1–3 baris** (≤ 12 kata), muncul di **≥ 2 shot**.
- Tanpa tamu: Lumi jadi ASKER, maksimal 2 baris.

## Hard rules

1. Enam beat lengkap, `structure` berisi satu entri per shot.
2. Blok `analogy` wajib: `source`, `maps` ≥ 2, `line_shot`, `why_it_works`.
3. Maksimal 1 tamu per episode, sesuai registry.
4. `facts_status` **selalu** `"pending"` — jangan pernah menandai `verified`.
5. Judul sama persis dengan Content Bible.
6. `text` ≤ 14 kata · `caption` ≤ 9 kata · `caption_adult` ≤ 14 kata.
7. Dilarang: "Adek", "dek", "adik", "kakak", "bunda", "sayang", "teman-teman".
8. "kamu" maksimal 1× per episode.
9. Tidak mengarang angka, tahun, nama, atau sumber.
10. Jangan menyalin naskah antar episode.
11. Jangan membuka dengan sapaan ("Hai teman-teman").
12. Satu episode punya **satu** analogi inti — tidak boleh dipakai episode lain.

## Motion plan (v4.5 — anti-template, wajib)

Jangan menyalin timing/koordinat D04. Setiap shot diturunkan dari makna dialog,
pembicara, dan fungsi beat.

1. **Tema episode dulu** — isi `scene_family` dan `motion_motif` (tidak boleh
   kosong). Contoh: D05 `aviation_sky` / `upward_lift_and_airflow`.
2. **Layout diikat ke baris dialog**, bukan detik tebakan:

   ```json
   "layouts": [
     {"mode": "CLOSEUP_EMPHASIS", "on_line": 0, "target": "boca", "z": 1.46},
     {"mode": "INFOGRAPHIC_CARD", "on_line": 1, "max_span": 3.7,
      "card": {"kind": "steps", "title": "Syarat terbang", "accent": "#1F6F78",
               "steps": ["...", "...", "..."]}}
   ]
   ```

   `from`/`to` numerik hanya untuk episode lama D01–D04.
3. **`SPOTLIGHT_EFFECT` maksimal 2 per episode** dan hanya saat naskah memang
   menyoroti fokus, rahasia, gelap, jebakan, atau twist. Jangan di analogi
   outdoor terang.
4. **`CLOSEUP_EMPHASIS` hanya** di hook, shock/Aha, atau CTA. `target` wajib
   `boca`/`lumi`/`guest` dan **harus sama** dengan pembicara baris `on_line`.
5. **`INFOGRAPHIC_CARD` hanya** untuk mekanisme, sebab-akibat, atau
   perbandingan; 2–3 langkah dari naskah, jangan mengarang angka.
6. **WIDE + props adalah mode utama.** Jangan memaksa efek kalau dialog tidak
   meminta. Shot tanpa layout sah selama ada prop/key beranimasi.
7. **Blocking bervariasi**: solo Boca `x` 340/700 bergantian; dialog Boca 300,
   tamu 640. Prop di sisi seberang atau band atas, jangan menutupi wajah.
8. **Dua layout bersebelahan tidak boleh mode sama.**

`on_line`/`to_line` dihitung pipeline dari timing VO nyata. Keyframe numerik
juga otomatis diskalakan `scale_shot_timings()` dari `est_seconds` ke durasi
suara asli — jadi jangan menulis key berhenti di tengah shot.

Regenerasi massal: `python3 tools/plan_motion_v45.py`, lalu
`python3 tools/check_storyboards.py` sampai `HASIL: PASS`.

## Teknik anti-generik (pakai minimal 3 dari 5)

- **Situasi konkret**: tamu sedang *melakukan* sesuatu saat Boca datang.
- **Keinginan kecil**: ingin beli sesuatu, ingin cepat sampai, ingin HP awet —
  lalu bentrok dengan kenyataan.
- **Detail Indonesia**: uang kembalian receh, kuota habis, angkot berhenti
  sembarangan, warung naikkan harga, jemuran kehujanan.
- **Punchline Lumi** (reaksi, bukan penjelasan).
- **Balik arah**: sesuatu yang tampak benar di awal ternyata salah.

## Bentuk blok yang sering salah

```json
"analogy": {
  "source": "HP yang dipakai seharian lalu di-charge semalam",
  "maps": [
    { "real": "tenaga pulih saat tidur", "analogy": "baterai terisi" },
    { "real": "sampah sel dibersihkan", "analogy": "aplikasi latar ditutup" }
  ],
  "line_shot": 3,
  "why_it_works": "Semua orang punya HP dan pernah kehabisan baterai."
}
```

## Contoh emas

`production/storyboards/BOCA-D03.json` — 60 s, 9 shot, 181 kata, tamu `ardi`,
hook H6, analogi HP. Baca file itu sebelum menulis episode baru; tiru
**strukturnya**, jangan isinya.

## Selesai kalau

- [ ] `python3 tools/check_storyboards.py production/storyboards/` → PASS 0 error
- [ ] `python3 tools/storyboard_to_md.py BOCA-Dxx` sudah dijalankan
- [ ] Judul, durasi, dan tamu sesuai registry
- [ ] Ada minimal 1 baris `lumi`
- [ ] Ada twist yang dipersiapkan sejak setup
