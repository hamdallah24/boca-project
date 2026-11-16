# Cast & suara

Sumber lengkap: `docs/CHARACTER_SYSTEM.md`. Ringkasan yang dipakai saat menulis.

## Tetap

| id | Peran | Suara Gemini | Fallback Edge |
|---|---|---|---|
| `boca` | EXPLAINER, host, desain LOCKED | `Puck` | `id-ID-ArdiNeural` |
| `lumi` | REACTOR, sidekick cahaya | `Aoede` | `id-ID-GadisNeural` |

## Tamu berulang

| id | Siapa | Fungsi | Episode | Suara |
|---|---|---|---|---|
| `ardi` | anak 10 th, tetangga | penanya polos | 03, 07, 19, 29 | `Fenrir` |
| `sari` | kakak SMA 16 th | analogi digital | 04, 08, 09, 11, 14 | `Leda` |
| `pak_darno` | montir 50-an | analogi mesin | 05, 10, 12 | `Charon` |
| `bu_ratna` | pemilik warung | analogi harga/pasar | 06, 13, 22, 26 | `Kore` |
| `dokter_nia` | dokter 30-an | analogi tubuh | 15, 16, 17, 18 | `Autonoe` |
| `kak_bima` | teller bank 25 th | analogi uang | 23, 24, 25, 27, 28 | `Orus` |

## Ciri visual pengenal

| id | Ciri yang harus disebut/digambar |
|---|---|
| `ardi` | kacamata bulat, kaus oranye |
| `sari` | hoodie ungu, headphone |
| `pak_darno` | overall biru, topi montir |
| `bu_ratna` | sanggul, kain batik |
| `dokter_nia` | jas putih, stetoskop merah |
| `kak_bima` | kemeja biru, dasi merah |

## Aturan

1. Maksimal 1 tamu per episode; maksimal 3 suara total.
2. Tamu bicara 1–3 baris, masing-masing ≤ 12 kata.
3. Tamu muncul di ≥ 2 shot dan punya alasan berada di lokasi.
4. Tamu tidak boleh lebih pintar dari Boca — dia bertanya, Boca menjelaskan.
5. Tamu tidak boleh memakai `prop: prism`.
6. Tanpa tamu: Lumi jadi ASKER (maksimal 2 baris bertanya).

## Catatan produksi

Fallback Edge hanya punya 2 suara Indonesia (Ardi/Gadis). Kalau kuota Gemini
habis, hindari episode bertamu supaya tidak ada dua karakter bersuara sama.
