# Scene library

Sumber lengkap: `docs/SCENE_MOTION_SPEC.md` §2. Registry: `make_cartoon.SCENES`
dan `scene_svg.SCENE_SVG` (SVG dipakai otomatis bila id-nya ada di keduanya).

## Scene SVG tajam (9) — jalur utama v4.3

| id | Isi | Cocok untuk |
|---|---|---|
| `city_street` | trotoar, toko, lampu jalan | pembuka kota, analogi sehari-hari |
| `classroom` | papan tulis, meja, jendela | sekolah, belajar, penjelasan |
| `mountain_sunset` | gunung berlapis + matahari | skala besar, refleksi |
| `park_evening` | taman senja, jalan setapak | penutup tenang |
| `city_top` | atap gedung + skyline | twist, sudut pandang luas |
| `data_center` | rak server, lorong dingin | internet, data, AI |
| `market` | tiga warung + kanopi | jual beli, harga, makanan |
| `phone_inside` | layar HP, bubble chat | notifikasi, aplikasi |
| `bedroom` | kasur, jendela, lemari | rumah, malam, istirahat |

Semuanya di-cache di `production/cache/scenes/<id>/` (sky/clouds/midground/
ground). Cache otomatis basi kalau teks SVG berubah.

## Scene `make_cartoon` (masih dipakai, lebih lembut)

`park`, `park_sunleft`, `sky`, `space`, `prism`, `atmosphere`, `sunset`,
`kitchen`, `bedroom_night`, `beach`, `underwater`, `body_inside`,
`house_cutaway`, `airport`, `bank`, `garden`, `playground`, `neuron_city`,
`rain_cloud`, `lake_ice`, `mountains`, dll. — cek `SCENES` di
`make_cartoon.py` sebelum memakai id baru.

Scene yang **belum ada** jangan dipakai di storyboard; validator strict akan
menolak. Prioritaskan 9 scene SVG untuk hook dan payoff supaya kontrasnya
tajam.

## Cara memilih (bukan dari kata kunci)

| Beat | Kebutuhan visual |
|---|---|
| HOOK | objek aneh / konflik terlihat, bukan wajah tersenyum |
| SETUP | tempat kejadian milik tamu (warung, bengkel, kelas) |
| EXPLAIN | tempat analogi terjadi (dapur, HP, jalan) |
| TWIST | skala berbeda (kota, langit, dalam tubuh) |
| PAYOFF | kembali ke tempat setup |
| CTA | tempat yang tenang, ruang untuk caption |

Jangan memilih scene dari kata kunci judul — itu penyebab 152 dari 182 shot
lama jatuh ke `park`. Minimal 4 scene unik dan 3 preset kamera per episode.
