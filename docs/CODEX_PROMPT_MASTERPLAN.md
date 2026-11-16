# PROMPT MASTER — BOCA Master Plan (Storyboard + VO + Karakter, Production Grade)

> **Cara pakai:** buka repo `boca-character`, tempel **seluruh isi file ini** ke agent
> (Codex/Claude/GPT). Jangan tambah instruksi lain sebelum batch 1 selesai.
> Prompt ini menggantikan `CODEX_PROMPT_SCENE_VO.md` versi lama.
>
> **Kalau kamu berjalan di OpenCode:** muat skill `boca-storyboard`,
> `boca-visual`, dan `boca-qa` lebih dulu — isinya sudah merangkum dokumen ini.

---

## 0. Peran & hasil akhir

Kamu adalah **showrunner + storyboard artist + script supervisor** untuk serial
edukasi vertikal **BOCA**. Kamu tidak merender video dan tidak menulis kode pipeline.

Hasil akhirmu adalah **Master Plan production-grade** untuk 30 episode:

| # | File | Isi |
|---|---|---|
| 1 | `docs/MASTER_PLAN.md` | peta musim: 30 logline, hook, analogi inti, tamu, durasi, seri |
| 2 | `docs/ANALOGY_LIBRARY.md` | ≥ 45 analogi kehidupan sehari-hari + pemetaan konsep |
| 3 | `docs/CHARACTER_BIBLE_V2.md` | cast lengkap: Boca, Lumi, 6 tamu + spec visual & suara |
| 4 | `production/characters/<id>.json` | 6 spec karakter tamu (machine-readable) |
| 5 | `production/storyboards/BOCA-Dxx.json` | 28 storyboard (D03–D30) |
| 6 | `production/storyboards/BOCA-Dxx.md` | 28 storyboard versi manusia |
| 7 | `docs/ASSET_BACKLOG.md` | daftar aset yang harus dibuat, berprioritas |
| 8 | `production/storyboards/REPORT.md` | ringkasan + hal yang perlu keputusan manusia |

---

## 1. Baca dulu (WAJIB, jangan dilewati)

| File | Untuk apa |
|---|---|
| `/sdcard/Download/BOCA_Rencana_Konten_30_Hari.md` | **source of truth**: judul, seri, durasi, beat, fakta, CTA |
| `docs/STORY_ARCHITECTURE.md` | 6 beat, 6 pola hook, aturan analogi, peran dialog, CTA |
| `docs/CHARACTER_SYSTEM.md` | cast, siapa muncul di episode mana, voice, aturan tamu |
| `docs/SCENE_MOTION_SPEC.md` | kontrak render: scene, ekspresi, pose, kamera, timing |
| `docs/VARIATION_MATRIX_30.md` | urutan scene & kamera per hari (anti-repetisi) |
| `production/plans/BOCA-D02.json` | contoh plan nyata yang sudah lolos QA |
| `production/sceneplans/BOCA-D03.json` | contoh format shot (lama, tetap berguna) |
| `make_boca.py`, `make_cartoon.py`, `make_music.py` | daftar aset yang benar-benar ada |

Kalau sebuah ide butuh sesuatu yang tidak ada di file-file itu → **catat di
`ASSET_BACKLOG.md`, jangan dipakai di shot**.

---

## 2. Aturan cerita (ringkasan yang mengikat)

1. **Enam beat wajib**: HOOK → SETUP → EXPLAIN → TWIST → PAYOFF → CTA.
2. **Analogi wajib** dan harus dari **kehidupan sehari-hari** (warung, angkot,
   dapur, antrean, kuota, jemuran, kasur, sekolah). Satu analogi inti per episode,
   dipetakan ke ≥ 2 elemen nyata.
3. **Jangan bergantung pada Boca sendirian.** Kalau episode butuh pertanyaan,
   ada **ASKER**: karakter tamu (atau Lumi kalau tanpa tamu).
4. Maksimal **3 suara** per episode: Boca (EXPLAINER), Lumi (REACTOR), 1 tamu (ASKER).
5. Tamu bicara **1–3 baris** (≤ 12 kata), muncul di **≥ 2 shot**, punya alasan
   berada di lokasi.
6. **Twist wajib** — pengecualian, konsekuensi tak terduga, atau perbandingan.
7. Hook **≤ 3 detik** (4 detik untuk tier 90 s), harus jalan saat mute.
8. Bahasa: ≤ 14 kata per kalimat VO, caption ≤ 9 kata, "kamu" maksimal 1×.
   Dilarang: "Adek", "dek", "adik", "kakak", "bunda", "sayang", "teman-teman".
9. Jangan mengarang fakta, angka, tahun, nama. `facts_status` **selalu** `"pending"`.
10. Judul **sama persis** dengan Content Bible.

### Teknik supaya cerita tidak generik

Pakai minimal **3 dari 5** ini di setiap episode:

- **Situasi konkret**: tamu sedang *melakukan* sesuatu saat Boca datang.
- **Keinginan kecil**: tamu ingin membeli sesuatu, ingin cepat sampai, ingin
  HP-nya awet — lalu keinginan itu bentrok dengan kenyataan.
- **Detail spesifik Indonesia**: uang kembalian receh, kuota habis, angkot
  berhenti sembarangan, warung yang naikkan harga, jemuran kehujanan.
- **Punchline kecil** di Lumi (bukan penjelasan).
- **Balik arah**: sesuatu yang tampak benar di awal ternyata salah.

---

## 3. Registry episode (WAJIB dipakai, jangan diubah)

| Hari | Seri | Durasi | Tamu | Status |
|---|---|---|---|---|
| 01 | KYB | 45 | — | **TERKUNCI, sudah tayang** |
| 02 | KYB | 45 | — | **TERKUNCI, sudah direkam** |
| 03 | KYB | 60 | `ardi` | kerjakan |
| 04 | KYB | 45 | `sari` | kerjakan |
| 05 | KYB | 60 | `pak_darno` | kerjakan |
| 06 | KYB | 45 | `bu_ratna` | kerjakan |
| 07 | KYB | 45 | `ardi` | kerjakan |
| 08 | BMM | 60 | `sari` | kerjakan |
| 09 | BMM | 60 | `sari` | kerjakan |
| 10 | BMM | 45 | `pak_darno` | kerjakan |
| 11 | BMM | 90 | `sari` | kerjakan |
| 12 | BMM | 45 | `pak_darno` | kerjakan |
| 13 | BMM | 60 | `bu_ratna` | kerjakan |
| 14 | BMM | 45 | `sari` | kerjakan |
| 15 | BMT | 45 | `dokter_nia` | kerjakan |
| 16 | BMT | 60 | `dokter_nia` | kerjakan |
| 17 | BMT | 45 | `dokter_nia` | kerjakan |
| 18 | BMT | 60 | `dokter_nia` | kerjakan |
| 19 | BMT | 45 | `ardi` | kerjakan |
| 20 | BMT | 45 | — (Lumi jadi ASKER) | kerjakan |
| 21 | BMT | 60 | — (Lumi jadi ASKER) | kerjakan |
| 22 | BBU | 60 | `bu_ratna` | kerjakan |
| 23 | BBU | 90 | `kak_bima` | kerjakan |
| 24 | BBU | 60 | `kak_bima` | kerjakan |
| 25 | BBU | 60 | `kak_bima` | kerjakan |
| 26 | BBU | 60 | `bu_ratna` | kerjakan |
| 27 | BBU | 60 | `kak_bima` | kerjakan |
| 28 | BBU | 60 | `kak_bima` | kerjakan |
| 29 | BLA | 60 | `ardi` | kerjakan |
| 30 | BLA | 90 | — (Lumi jadi ASKER) | kerjakan |

**Seri:** `KYB` sains sehari-hari · `BMM` teknologi · `BMT` tubuh · `BBU` ekonomi · `BLA` antariksa.

### Budget per tier

| Durasi | Shot | Total kata | Baris dialog |
|---|---|---|---|
| 45 s | 5–7 | 135–150 | 10–14 |
| 60 s | 7–9 | 180–200 | 14–20 |
| 90 s | 9–12 | 270–300 | 20–30 |

Estimasi: `0.33 detik/kata + 0.16 detik/baris` (Edge `+47%`, tanpa `atempo`).
Kalau narasi lebih panjang dari tier, video dibiarkan lebih panjang — durasi
tidak dipaksa.

---

## 4. Skema storyboard JSON

```json
{
  "id": "BOCA-D22",
  "day": 22,
  "series": "BBU",
  "title": "Kenapa harga barang bisa naik?",
  "duration_target": 60,
  "facts_status": "pending",
  "logline": "Ardi bingung uang jajannya sama tapi dapatnya lebih sedikit, lalu Bu Ratna menjelaskan harga yang naik pelan-pelan.",
  "hook": {
    "pattern": "H6",
    "claim": "Bu Ratna mengganti papan harga di warungnya.",
    "gap": "Padahal barangnya tidak berubah.",
    "promise": "Kenapa harganya ikut naik?",
    "seconds": 3
  },
  "cast": { "host": "boca", "sidekick": "lumi", "guest": "bu_ratna" },
  "analogy": {
    "source": "warung yang menaikkan harga pelan-pelan",
    "maps": [
      { "real": "harga naik terus", "analogy": "papan harga diganti sedikit-sedikit" },
      { "real": "daya beli turun", "analogy": "uang jajan sama, dapatnya lebih sedikit" }
    ],
    "line_shot": 4,
    "why_it_works": "Semua orang pernah melihat harga naik, jadi tidak perlu dijelaskan."
  },
  "structure": [
    { "beat": "hook", "shot": 1 },
    { "beat": "setup", "shot": 2 },
    { "beat": "explain", "shot": 3 },
    { "beat": "explain", "shot": 4 },
    { "beat": "twist", "shot": 5 },
    { "beat": "twist", "shot": 6 },
    { "beat": "payoff", "shot": 7 },
    { "beat": "cta", "shot": 8 }
  ],
  "vo": {
    "voice_boca": "Puck",
    "voice_lumi": "Aoede",
    "voice_guest": "Kore",
    "style_note": "hangat, santai, tempo sedang, tanpa baby talk",
    "total_words": 190,
    "est_seconds": 59.9,
    "lumi_lines": 3,
    "beats": [
      { "shot": 1, "function": "hook", "emotion": "penasaran",
        "emphasis": ["naik lagi"], "pause_before": 0.0, "pause_after": 0.25 }
    ]
  },
  "shots": [
    {
      "n": 1,
      "scene": "market",
      "beat": "hook",
      "cam": { "fx": [0.46, 0.50], "fy": [0.44, 0.46], "z": [1.00, 1.25] },
      "keys": [
        { "t": 0.0, "expr": "neutral", "pose": "walk", "arms": [0], "x": -300, "ground": 1400, "h": 640 },
        { "t": 1.5, "expr": "shock", "pose": "stand", "arms": [0, 3], "period": 0.8, "x": 250, "ground": 1400, "h": 660 }
      ],
      "lumi": [
        { "t": 0.8, "expr": "happy", "pose": "float", "x": 830, "y": 1180, "h": 240 }
      ],
      "guest": [
        { "t": 0.0, "expr": "neutral", "pose": "stand", "x": 700, "ground": 1420, "h": 620 }
      ],
      "sfx": [[0.05, "whoosh", 0.8]],
      "est_seconds": 7.2,
      "dialogue": [
        { "who": "bu_ratna", "text": "Harganya naik lagi, Boca. Mulai minggu ini.",
          "caption": "harganya naik lagi", "caption_adult": "kenaikan harga barang konsumsi" }
      ]
    }
  ],
  "asset_needs": [
    { "type": "scene", "id": "market", "priority": "P0" },
    { "type": "character", "id": "bu_ratna", "priority": "P0" },
    { "type": "voice", "id": "Kore", "priority": "P0" }
  ],
  "production_notes": "Bu Ratna berdiri di belakang lapak, Boca datang dari kiri."
}
```

### Field wajib per shot

`n`, `scene`, `beat`, `cam`, `keys`, `lumi`, `sfx`, `est_seconds`, `dialogue`.
Field `guest` **wajib ada** kalau `cast.guest` tidak null (boleh array kosong di shot
tempat tamu tidak terlihat).

### Field wajib per baris dialogue

`who` (`boca` | `lumi` | id tamu), `text` (≤ 14 kata), `caption` (≤ 9 kata),
`caption_adult` (≤ 14 kata).

---

## 5. Skema `docs/MASTER_PLAN.md`

Wajib memuat:

1. **Ringkasan musim** — 5 seri, jumlah episode, total durasi.
2. **Tabel 30 baris** dengan kolom: Hari · Seri · Durasi · Judul · Logline (1 kalimat) ·
   Pola hook · Analogi inti · Tamu · CTA.
3. **Peta karakter** — siapa muncul di episode mana, berapa kali.
4. **Peta analogi** — konsep → analogi → episode.
5. **Peta aset** — ringkasan dari `ASSET_BACKLOG.md`.
6. **Risiko produksi** — episode high-risk fakta, episode yang butuh aset baru paling banyak.

## 6. Skema `docs/ANALOGY_LIBRARY.md`

Tabel minimal 45 baris:

| Konsep | Analogi sehari-hari | Pemetaan | Episode | Kekuatan |
|---|---|---|---|---|
| Inflasi | harga warung naik pelan-pelan | harga↑ / uang sama | 22, 26 | sangat familiar |

Aturan: tidak boleh ada analogi yang sama dipakai di dua episode berbeda.

## 7. Skema `docs/CHARACTER_BIBLE_V2.md`

Untuk setiap karakter (Boca, Lumi, 6 tamu): id, nama, peran, siapa, ciri visual,
palet hex, ekspresi, pose, suara, kepribadian, cara bicara, kalimat khas,
episode kemunculan, do/don't, dan **satu paragraf "kenapa karakter ini ada"**.

## 8. Skema `docs/ASSET_BACKLOG.md`

| Prioritas | Tipe | id | Dipakai di episode | Estimasi usaha | Catatan |
|---|---|---|---|---|---|
| P0 | scene | `market` | 06, 13, 22, 26 | sedang | lapak + tenda + timbangan |
| P0 | character | `bu_ratna` | 06, 13, 22, 26 | besar | 12 sprite |
| P0 | voice | `Kore` | 06, 13, 22, 26 | kecil | cek kuota TTS |

Prioritas: **P0** = dipakai ≥ 3 episode · **P1** = 2 episode · **P2** = 1 episode.

---

## 9. Cara kerja (batch, wajib berurutan)

| Batch | Episode |
|---|---|
| 1 | D03–D07 |
| 2 | D08–D12 |
| 3 | D13–D17 |
| 4 | D18–D22 |
| 5 | D23–D27 |
| 6 | D28–D30 |

Sebelum batch 1: selesaikan dulu `MASTER_PLAN.md`, `ANALOGY_LIBRARY.md`,
`CHARACTER_BIBLE_V2.md`, `production/characters/*.json`.

Setelah **setiap** batch:

```bash
python3 tools/check_storyboards.py production/storyboards/
```

**Wajib 0 error sebelum lanjut batch berikutnya.** Kalau validator belum ada,
buat sendiri di `tools/check_storyboards.py` sesuai aturan di dokumen ini —
validator itu bagian dari hasil kerja.

---

## 10. Larangan

- ❌ Mengubah D01/D02.
- ❌ Mengubah isi `production/plans/` atau file pipeline (`*.py` selain `tools/`).
- ❌ Memakai scene/ekspresi/pose/SFX di luar `SCENE_MOTION_SPEC.md`.
- ❌ Membuat karakter ke-4 dalam satu episode.
- ❌ Membuat tamu yang hanya muncul sekali seumur musim.
- ❌ Menandai fakta `verified`.
- ❌ Memakai analogi yang sama di dua episode.
- ❌ Menyalin naskah antar episode.
- ❌ Membuka episode dengan sapaan ("Hai teman-teman").

---

## 11. Definition of done

- [ ] `docs/MASTER_PLAN.md` lengkap (30 baris, semua kolom terisi).
- [ ] `docs/ANALOGY_LIBRARY.md` ≥ 45 analogi unik.
- [ ] `docs/CHARACTER_BIBLE_V2.md` memuat 8 karakter.
- [ ] 6 file `production/characters/*.json` valid.
- [ ] 28 JSON + 28 MD di `production/storyboards/`.
- [ ] `python3 tools/check_storyboards.py production/storyboards/` → **PASS 0 error**.
- [ ] Setiap episode punya: hook 3 bagian, analogi dengan ≥ 2 mapping, twist,
      minimal 1 baris Lumi, dan tamu sesuai registry.
- [ ] `docs/ASSET_BACKLOG.md` mencantumkan semua scene/karakter/suara yang dipakai.
- [ ] `production/storyboards/REPORT.md` berisi ringkasan + keputusan yang
      butuh manusia (fakta high-risk, aset mahal, episode padat).

---

## 12. Kalimat pertama yang harus kamu balas

Sebelum menulis file apa pun, balas dengan:

1. Daftar file yang sudah kamu baca.
2. Ringkasan 6 beat dan 3 peran dialog dalam bahasamu sendiri (bukti kamu paham).
3. Rencana batch 1 (D03–D07): satu baris per episode berisi hook + analogi + tamu.

Setelah itu baru mulai menulis.
