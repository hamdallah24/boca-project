# BOCA — Character Pack v1

Status: **review only, belum masuk engine Stickman Kino / Remotion.**

**Content Bible / source of truth:** `/sdcard/Download/BOCA_Rencana_Konten_30_Hari.md`

## File

- `boca-cover-v1.png` — cover / hero sheet, pose melambai.
- `boca-front-v1.png` — front view, ekspresi kaget.
- `boca-front-neutral-v1.png` — front view, ekspresi netral.
- `boca-expressions-v1.png` — 6 ekspresi: netral, kaget, senang, bingung, ngantuk, fokus.
- `boca-poses-v1.png` — 3 pose: sapa, mikir, baca.
- `boca-front-v1-transparent.png` — front view transparan untuk komposit.

SVG sumber ada di folder `svg/`. Generator: `make_boca.py`.

## Konsep

Boca adalah anak SD yang menjelaskan hal-hal rumit dengan gaya **bahasa bayi** yang tetap jelas (parentese, bukan babble tanpa arti). Target: anak-anak, orang tua, dan Gen Z yang suka humor edukatif.

Ciri utama:

- kepala besar bulat/oval, badan bean, tangan-kaki stick;
- topi SD merah-putih dengan badge **SD**;
- kemeja putih, dasi merah, celana merah;
- tas teal sebagai aksen;
- pensil di belakang telinga;
- name tag **BOCA**;
- buku sebagai properti utama;
- alis tebal, mata besar, mulut ekspresif, tanpa hidung.

## Palet

- Krem `#F6F1E7`
- Tinta `#231815`
- Merah sekolah `#D7263D`
- Teal `#1F6F78`
- Kuning `#F4B942`

## Yang perlu direview

1. Proporsi kepala vs badan.
2. Bentuk topi SD dan posisi badge.
3. Alis, mata, dan mulut (terutama ekspresi netral).
4. Seragam: kemeja putih, dasi merah, celana merah.
5. Buku dan cara tangan memegang.
6. Tas teal dan strap-nya.
7. Nama **Boca** dan tagline.

## Catatan produksi

- Semua aset dibuat vector SVG, dirender 1080×1920.
- Belum ada side view / turnaround. Itu dibuat setelah desain depan disetujui.
- Rig animasi belum diubah. Setelah desain lock, baru dibuat rig big-head bean dengan kontrol mata, alis, mulut, dan pose.
- Caption final akan memakai dual-layer: baris bayi + terjemahan dewasa.

## Template produksi v4 — LOCKED (pipeline harian)

| File | Fungsi |
|---|---|
| `boca_pipeline.py` | pipeline episode → video (render, audio, subtitle, QA) |
| `make_animatic_d02.py` | episode referensi D02 (kunci template, demo dialog Lumi) |
| `make_boca.py` | karakter Boca + `lumi()` (sidekick), opsi `book=False` |
| `make_cartoon.py` | scene kartun flat vector (park, sky, space, prism, atmosphere, sunset) |
| `make_music.py` | BGM + SFX original (sintesis numpy, nol hak cipta) |
| `plan_from_md.py` | Content Bible (md) → plan JSON 30 hari (+ draf LLM) |
| `daily_build.py` | **cron harian**: plan → render → QA → payload → publish |
| `publish.py` | uploader 4 platform (default dry-run), detail di `publish/README.md` |

### Cron (sudah terpasang)

```
0 6 * * *  $HOME/projects/boca-character/daily_build.py --publish --catch-up --date $(date +\%F) >> $HOME/projects/boca-character/production/logs/cron.log 2>&1
*/15 * * * * sh $HOME/projects/boca-character/tools/ensure_cron.sh
```

- Daemon: `cronie` (`crond`); source crontab: `production/boca.cron`.
- **Anti-mati**: Android bisa membunuh `crond` (doze / app dibunuh). Pengaman:
  - `tools/ensure_cron.sh` — menyalakan `crond` lagi + pasang ulang crontab
    (dipanggil dari `~/.bashrc`, dari crontab tiap 15 menit, dan dari
    `~/.termux/boot/start_boca_cron.sh`).
  - `termux-wake-lock` di `~/.bashrc` supaya Termux tidak di-doze.
  - `~/.termux/boot/start_boca_cron.sh` berjalan otomatis **setelah Termux:Boot
    terpasang** (F-Droid). Tanpa itu, jalankan `sh tools/ensure_cron.sh` manual
    setelah reboot.
  - Log: `production/logs/watchdog.log`.
- `--catch-up`: episode yang sudah dirender tapi belum terbit (plan-nya disetujui
  belakangan) otomatis diterbitkan di run berikutnya tanpa render ulang.
  `--catch-up-days` juga membangun hari yang terlewat.
- Tanggal acuan hari produksi: env `BOCA_START_DATE` (default 2026-11-14 = Hari 01).
- Output: `/sdcard/Download/BOCA_DAILY/BOCA-DNN/`; state: `production/state.json`.
- Gate publish: plan approved + facts `verified` + QA pass + kredensial ada.

### Perintah umum

```bash
python3 plan_from_md.py --day 3          # draf plan hari ke-3
python3 daily_build.py --day 3 --no-render  # cek plan tanpa render
python3 daily_build.py --day 3            # render + QA + payload
python3 daily_build.py --approve BOCA-D03  # setujui plan
python3 publish.py --payload production/payloads/BOCA-D03.json        # dry-run
python3 publish.py --payload production/payloads/BOCA-D03.json --publish
```

Gemini: key dari `MoneyPrinterTurbo/config.toml` (`gemini_api_key`) atau env
`GEMINI_API_KEY`. Free tier 10 request/hari per model TTS → ada fallback chain
(3.8-flash → 3.8-lite → 3.1-preview → 2.5-pro → Edge) + cache TTS berbasis hash teks.

Aturan v4: gaya kartun (bukan foto), Boca tanpa buku, sidekick Lumi (punya VO
kalau ada dialog 2 arah), subtitle tanpa panel + outline kata-per-kata sinkron
envelope suara, VO bahasa ringan tanpa "Adek", hook klaim→celah→janji.
