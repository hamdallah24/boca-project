# Audit engine dari folder Download

Tanggal: 2026-11-15 18:20
Sumber: `/sdcard/Download/engine_motion..py`, `/sdcard/Download/engine_svg.py` (18:14)
MD terbaru: `/sdcard/Download/BOCA_Ringkasan_Teknis_Animasi.md` (15:06)

## Temuan

1. MD terbaru **tidak menyebut** `engine_motion` / `engine_svg`. Bagian
   "Referensi file" masih menunjuk modul project (`boca_pipeline.py`,
   `motion.py`, `make_boca.py`, `make_cartoon.py`).
2. Dua file engine baru ada di Download, bukan project. Sudah disalin ke
   project dengan nama bersih dan lolos `py_compile`:
   - `engine_motion.py` (dari `engine_motion..py`)
   - `engine_svg.py`
3. Isi engine tumpang tindih dengan stack v4.3 yang sudah jalan:

| Engine Download | Padanan project | Catatan |
|---|---|---|
| `build_parallax_scene()` + `compose_parallax_scene()` | `boca_pipeline.build_scene_layers()` + crop plate/clouds | engine: parallax 4 layer asli (0,15/0,30/0,60/1,00) |
| `apply_squash_stretch()` | `motion.use_squash()` + sprite tilt bake | engine: `rotate(expand=True)` tiap frame |
| `apply_spotlight()` | `layouts.spot_mask()` + cache 8 langkah | engine: stepped ellipse, tanpa blur |
| `draw_prop_dynamic()` | `props_svg.build()` + frame scripted | engine: 5 prop 512 px, statis + sub-animasi garis |
| `draw_info_card()` | `layouts.draw_card()` | engine: kartu 880 px, hanya baris progress |
| `draw_hud_v2()` | `motion.use_hud()` | setara, HUD v4.3 sudah 1,5× |
| `SCENE_BUILDERS` (3 scene) | `scene_svg.SCENE_SVG` (2 scene) | engine punya `mountain_sunset`; project punya detail lebih rapat |

## Hasil ukur di perangkat (Pillow, 1080×1920)

| Operasi | Waktu |
|---|---|
| `engine_svg.build_parallax_scene()` kota / kelas / gunung | 15,1 s / 8,6 s / 12,3 s (cache disk) |
| `engine_svg.build_prop_sprites()` 5 prop | 13,8 s |
| `engine_motion.compose_parallax_scene()` z=1,00 | **93 ms/frame** |
| `compose_parallax_scene()` z=1,10 | **373 ms/frame** |
| `compose_parallax_scene()` z=1,30 | **341 ms/frame** |

Batas anggaran render ±250–300 ms/frame **total** (aktor, kartu, caption, HUD,
encode). Parallax engine saja sudah 93–373 ms → tidak bisa dipakai apa adanya.
Stack v4.3 memakai plate statis + cloud 0,55× (crop ringan ±18 ms/frame).

## Kualitas

- Scene engine: bersih, outline tebal, tapi lebih datar/sederhana (gedung blok,
  tanpa detail storefront), palet tidak disamakan dengan karakter.
- Prop engine: rapi, tetapi statis (tidak ada animasi jarum/pasir/scroll
  ber-frame seperti `props_svg`).
- Kartu engine: tidak mendukung `compare` dua kolom / checklist / VS badge.

## Rekomendasi

Pertahankan stack v4.3. Engine Download disimpan sebagai referensi. Aset yang
sudah diadopsi (18:35): scene `mountain_sunset` di `scene_svg.py` dan prop
`bulb` + `coin_stack` di `props_svg.py`, dikonversi ke palet/outline BOCA dan
animasi scripted (bukan versi statis engine).
