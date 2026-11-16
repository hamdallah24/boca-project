> **SUPERSEDED** — pakai `docs/CODEX_PROMPT_MASTERPLAN.md`.
> File ini disimpan hanya sebagai referensi format shot lama.

# PROMPT UNTUK CODEX — Scene Sheet + Rencana VO (30 Episode BOCA)

> Cara pakai: buka repo `boca-character` di Codex, lalu tempel **seluruh isi file ini**
> sebagai instruksi. Jangan menambahkan episode di luar 30 hari.

---

## 1. Peran

Kamu adalah **storyboard artist + script supervisor** untuk channel edukasi vertikal
"BOCA". Kamu TIDAK menulis kode pipeline dan TIDAK merender video. Tugasmu hanya
menghasilkan **dokumen scene per scene + rencana VO** yang bisa langsung dirender
oleh `boca_pipeline.py`.

## 2. Tujuan

Untuk setiap hari (D03–D30), hasilkan:

1. **Scene sheet** (JSON) — urutan shot, background, kamera, gerak Boca, gerak Lumi, SFX.
2. **Storyboard** (Markdown) — versi manusia: tabel shot + naskah VO + catatan visual.

Tujuannya: **tidak ada dua video yang terlihat sama** — background, kamera, dan
gerak Boca harus berbeda antar episode.

## 3. Baca dulu (WAJIB, jangan dilewati)

| File | Untuk apa |
|---|---|
| `docs/SCENE_MOTION_SPEC.md` | kontrak render: enum, skema, aturan, preset kamera |
| `docs/VARIATION_MATRIX_30.md` | urutan scene, motif gerak, preset kamera per hari |
| `docs/variation_matrix.json` | versi mesin dari tabel di atas |
| `/sdcard/Download/BOCA_Rencana_Konten_30_Hari.md` | Content Bible v2.7: judul, beat, fakta, risiko |
| `production/plans/BOCA-D02.json` | contoh plan nyata yang sudah dirender & lolos QA |
| `make_boca.py` | daftar ekspresi/pose yang benar-benar ada |
| `make_cartoon.py` | daftar background yang benar-benar ada |
| `make_music.py` | daftar SFX yang benar-benar ada |

Kalau sebuah ide butuh sesuatu yang tidak ada di file-file itu → **jangan dipakai**.

## 4. Output

Buat folder `production/sceneplans/` lalu tulis, per episode:

```
production/sceneplans/BOCA-D03.json
production/sceneplans/BOCA-D03.md
production/sceneplans/BOCA-D04.json
production/sceneplans/BOCA-D04.md
...
production/sceneplans/BOCA-D30.json
production/sceneplans/BOCA-D30.md
```

**Jangan** menyentuh `production/plans/`, `boca_pipeline.py`, `daily_build.py`,
`publish.py`, atau `make_*.py`.

### 4.1 Skema JSON

```json
{
  "id": "BOCA-D03",
  "day": 3,
  "title": "Kenapa kita harus tidur?",
  "duration_target": 45,
  "facts_status": "pending",
  "scene_family": "kamar-malam → dalam tubuh",
  "palette_mood": "malam hangat",
  "motion_motif": "M3",
  "vo": {
    "voice_boca": "Puck",
    "voice_lumi": "Aoede",
    "style_note": "hangat, santai, tempo sedang, tanpa baby talk",
    "total_words": 138,
    "est_seconds": 44.6,
    "lumi_lines": 2,
    "beats": [
      { "shot": 1, "function": "hook", "emotion": "penasaran",
        "emphasis": ["tiba-tiba", "ngantuk"],
        "pause_before": 0.0, "pause_after": 0.25 }
    ]
  },
  "shots": [
    {
      "n": 1,
      "scene": "bedroom_night",
      "beat": "hook",
      "cam": { "fx": [0.46, 0.50], "fy": [0.44, 0.46], "z": [1.00, 1.25] },
      "keys": [
        { "t": 0.0, "expr": "sleepy", "pose": "walk", "arms": [0],
          "x": -300, "ground": 1400, "h": 640 },
        { "t": 1.4, "expr": "sleepy", "pose": "stand", "arms": [0, 3],
          "period": 0.8, "x": 250, "ground": 1400, "h": 660 }
      ],
      "lumi": [
        { "t": 0.4, "expr": "happy", "pose": "float", "x": 820, "y": 1180, "h": 240 }
      ],
      "sfx": [[0.05, "whoosh", 0.8]],
      "est_seconds": 6.2,
      "dialogue": [
        { "who": "boca",
          "text": "Setiap malam tubuh kita seperti mematikan lampu sendiri.",
          "caption": "tubuh mematikan lampu sendiri",
          "caption_adult": "tidur = mode pemeliharaan tubuh" }
      ]
    }
  ]
}
```

Field `vo.beats` **wajib satu entri per shot**, `function` salah satu dari:
`hook` · `gap` · `explain` · `analogy` · `twist` · `payoff` · `cta`.

### 4.2 Skema Markdown (storyboard)

```markdown
# BOCA-D03 — Kenapa kita harus tidur?

**Motif:** M3 think→lightbulb · **Mood:** malam hangat · **Durasi:** ~44.6 s
**Scene:** bedroom_night → bedroom → body_inside → neuron_city → bedroom_night

| # | Scene | Kamera | Gerak Boca | Lumi | SFX | Durasi |
|---|---|---|---|---|---|---|
| 1 | bedroom_night | C1 push-in | walk-in, sleepy | float kanan | whoosh | 6.2 s |

## Naskah VO

**Shot 1 — hook**
- BOCA: "Setiap malam tubuh kita seperti mematikan lampu sendiri."
  - caption: `tubuh mematikan lampu sendiri`
  - emosi: penasaran · jeda setelah: 0.25 s
- LUMI: "Lampu apa?"

## Catatan visual
- Shot 1: Boca masuk dari kiri, kamera push-in pelan.
```

## 5. Aturan keras (dicek validator, tidak bisa dinegosiasi)

1. **Scene** hanya dari `SCENE_MOTION_SPEC.md` §2.1–2.2. Ikuti `VARIATION_MATRIX_30.md`.
2. **Ekspresi** hanya: `shock`, `neutral`, `happy`, `confused`, `focus`, `sleepy`.
3. **Pose** hanya: `stand`, `walk`, `point`, `think`, `read`, `wave`, `cheer`, `celebrate`, `run`.
4. **`arms` harus list** (`[0]`, `[0,3,2]`), nilai 0–4. Bukan angka tunggal.
5. **`prop`** hanya `"prism"`, maksimal 1 shot per episode.
6. **`sfx`** hanya: `pop`, `whoosh`, `sparkle`, `chime`, `boing`. Maksimal 4 per episode.
7. Setiap shot **wajib** punya `cam` dengan `fx`, `fy`, `z`. Minimal **3 preset berbeda** per episode.
8. Minimal **4 scene id berbeda** per episode; **5 shot** per episode (kecuali butuh 6 untuk payoff).
9. `text` ≤ **14 kata**; `caption` ≤ **9 kata**; `caption_adult` ≤ 14 kata.
10. Total kata episode **120–150**; estimasi durasi **42–50 detik**.
11. **Lumi wajib bicara** minimal 1 baris per episode.
12. Dilarang memakai kata: **"Adek", "dek", "adik", "kakak", "bunda", "sayang"**.
    "kamu" maksimal 1× per episode.
13. Struktur narasi per episode: **hook → gap → penjelasan → analogi → payoff → ajakan**.
    Hook = klaim → celah → janji, dalam 3 detik pertama.
14. **Jangan mengarang fakta, angka, tahun, atau nama.** Kalau Content Bible tidak
    menyebutkannya, jangan tambahkan. `facts_status` **selalu** `"pending"` — verifikasi
    bukan tugasmu.
15. Judul episode **sama persis** dengan Content Bible. Jangan mengubah judul.
16. Bahasa Indonesia sehari-hari, tanpa istilah teknis tanpa penjelasan.
17. Boca tidak boleh diam > 2.5 detik tanpa key baru; minimal 2 key per shot.
18. Setiap shot punya tepat **satu** blok `dialogue` dengan 1–2 baris.

## 6. Cara kerja (batch, jangan sekali jalan)

Kerjakan **5 episode per batch**, berurutan:

```
Batch 1: D03–D07
Batch 2: D08–D12
Batch 3: D13–D17
Batch 4: D18–D22
Batch 5: D23–D27
Batch 6: D28–D30
```

Setelah **setiap batch**:

```bash
python3 tools/check_sceneplans.py production/sceneplans/
```

Kalau ada error → perbaiki → jalankan lagi. **Jangan lanjut batch berikutnya
sebelum batch sekarang 0 error.**

## 7. Cara memastikan tidak "ngasal"

Sebelum menulis shot, isi dulu tabel kecil ini untuk episode tersebut:

| Shot | Fungsi narasi | Scene (dari matriks) | Yang berubah dari shot sebelumnya |
|---|---|---|---|
| 1 | hook | … | — |
| 2 | gap | … | background / kamera / pose |

Aturan: **setiap shot harus mengubah minimal satu** dari: background, preset kamera,
pose Boca. Kalau tidak berubah, gabungkan shot-nya.

## 8. Larangan

- ❌ Menulis lebih dari 30 episode, atau membuat episode baru.
- ❌ Mengubah D01/D02 (sudah tayang/direkam).
- ❌ Mengubah isi `production/plans/`.
- ❌ Menambah scene/ekspresi/pose/SFX baru tanpa menambahkannya di kode lebih dulu.
- ❌ Menandai fakta sebagai `verified`.
- ❌ Memakai background `park` di lebih dari 1 episode per batch.
- ❌ Menyalin naskah dari episode lain.

## 9. Definition of done

- [ ] 28 file JSON + 28 file Markdown (D03–D30) ada di `production/sceneplans/`.
- [ ] `python3 tools/check_sceneplans.py production/sceneplans/` → **PASS, 0 error**.
- [ ] Tidak ada dua episode berurutan dengan scene pembuka sama.
- [ ] Setiap episode punya minimal 1 baris Lumi.
- [ ] Total kata tiap episode 120–150.
- [ ] Tidak ada file di luar `production/sceneplans/` yang berubah.

## 10. Laporan akhir yang harus kamu tulis

Setelah selesai, tulis `production/sceneplans/REPORT.md` berisi:

1. Tabel 28 baris: hari, judul, urutan scene, motif, jumlah kata, estimasi durasi.
2. Scene v2 yang **belum ada di kode** (dipakai tapi harus dibuat di `make_cartoon.py`),
   diurutkan berdasarkan frekuensi pemakaian.
3. Episode yang butuh perhatian khusus (fakta berisiko tinggi, narasi padat).
