# BOCA Story Architecture v2

Aturan naratif yang mengikat semua episode. Dokumen ini melengkapi
`SCENE_MOTION_SPEC.md` (teknis) dan `CHARACTER_SYSTEM.md` (cast).

> Prinsip induk: **penonton tidak boleh mendengar "penjelasan" — mereka harus menonton kejadian.**

---

## 1. Enam beat wajib

Setiap episode, apa pun durasinya, harus punya enam fungsi naratif ini:

| # | Beat | Fungsi | Yang harus terjadi |
|---|---|---|---|
| 1 | **HOOK** | klaim → celah → janji | penonton bertanya "kok bisa?" |
| 2 | **SETUP** | situasi konkret | ada tokoh yang **mengalami** masalahnya |
| 3 | **EXPLAIN** | analogi inti | konsep abstrak diterjemahkan ke benda sehari-hari |
| 4 | **TWIST** | perluasan / pengecualian | ada hal yang **tidak** sesuai dugaan awal |
| 5 | **PAYOFF** | kembali ke setup | situasi awal sekarang masuk akal |
| 6 | **CTA** | ajakan | pertanyaan yang bisa dijawab penonton dari pengalaman sendiri |

Kalau salah satu beat hilang, episode terasa seperti artikel yang dibacakan.

### Pemetaan waktu per tier

| Beat | 45 s | 60 s | 90 s |
|---|---|---|---|
| HOOK | 0–3 | 0–3 | 0–4 |
| SETUP | 3–9 | 3–10 | 4–14 |
| EXPLAIN | 9–20 | 10–26 | 14–40 |
| TWIST | 20–30 | 26–40 | 40–60 |
| PAYOFF | 30–40 | 40–52 | 60–78 |
| CTA | 40–45 | 52–60 | 78–90 |

---

## 2. Hook — wajib dibuka dengan pertanyaan ke penonton

**Aturan induk (D04 ke atas): kalimat pertama harus pertanyaan yang terasa
ditujukan ke penonton**, bukan pernyataan. Penonton harus merasa ditanya, bukan
diceramahi. Pernyataan baru boleh muncul di baris kedua (teaser), bukan pembuka.

| Kode | Sudut pertanyaan | Contoh |
|---|---|---|
| `H1` | sebab-akibat | "Kenapa air laut asin, padahal hujan tawar?" |
| `H2` | kontradiksi | "Kok Wi-Fi bisa tembus tembok kamar, ya?" |
| `H3` | hitungan / tebak | "Coba tebak, sehari harga saham berubah berapa kali?" |
| `H4` | eksperimen | "Apa yang terjadi kalau Bumi berhenti berputar?" |
| `H5` | pengalaman penonton | "Pernah nggak dua jam terasa cuma sepuluh menit?" |
| `H6` | pertanyaan yang beredar di kepala orang | "Internet itu sebenarnya tinggal di mana, sih?" |

Aturan hook:

- **Maksimal 3 detik** (4 detik untuk tier 90 s), maksimal **2 baris** dialog.
- Baris 1 = pertanyaan (Boca, ke penonton). Baris 2 = teaser singkat, bukan
  jawaban penuh.
- **Boca tidak menjawab pertanyaannya sendiri.** Teaser hanya menjanjikan arah
  jawaban; jawaban utuh baru di beat EXPLAIN.
- Tamu **tidak harus** bicara di hook — porsi 1–3 barisnya dipenuhi di shot lain.
- Kalimat pembuka = caption pertama. Harus jalan saat ditonton **mute**.
- Frame pertama sudah berisi konflik atau objek aneh — bukan wajah Boca tersenyum.
- Dilarang membuka dengan "Hai teman-teman" atau sapaan.
- Dilarang membuka dengan angka atau pernyataan ("Dua jam scroll HP terasa
  sepuluh menit.") — ubah jadi pertanyaan dulu.

---

## 3. Peran dialog

Setiap episode punya maksimal **3 suara**. Tidak lebih.

| Peran | Siapa | Porsi baris | Tugas |
|---|---|---|---|
| **EXPLAINER** | Boca | 55–70% | menjelaskan dengan analogi, memegang alur |
| **ASKER** | tamu (atau Lumi) | 15–30% | melontarkan pertanyaan polos yang mewakili penonton |
| **REACTOR** | Lumi | 10–20% | reaksi emosional, punchline kecil, tidak menjelaskan |

Aturan:

- **ASKER wajib ada** kalau episode butuh pertanyaan pembuka. Kalau tidak ada tamu,
  Lumi yang jadi ASKER — tapi maksimal 2 baris.
- Baris tamu maksimal **3 baris** per episode, masing-masing ≤ 12 kata.
- Boca tidak boleh menjawab pertanyaannya sendiri. Harus ada yang bertanya.
- Lumi **tidak boleh** menjelaskan fakta. Dia hanya bereaksi.

---

## 4. Aturan analogi (WAJIB)

Setiap episode punya **tepat satu analogi inti**, ditulis eksplisit di dokumen:

```json
"analogy": {
  "source": "warung Bu Ratna yang menaikkan harga pelan-pelan",
  "maps": [
    {"real": "harga naik terus", "analogy": "papan harga di warung diganti sedikit-sedikit"},
    {"real": "daya beli turun", "analogy": "uang jajan sama, tapi dapatnya lebih sedikit"}
  ],
  "line_shot": 3,
  "why_it_works": "Semua orang pernah melihat harga naik, jadi tidak perlu dijelaskan lagi."
}
```

### Standar kualitas analogi

| Kriteria | Gagal | Lulus |
|---|---|---|
| Konkret | "sistem ekonomi" | "warung yang naikkan harga" |
| Familiar | "server cloud" | "lemari arsip di kantor pos" |
| Bisa dipetakan | 1 kemiripan saja | ≥ 2 elemen yang jelas pasangannya |
| Tidak menyesatkan | analogi melanggar fakta | analogi menyederhanakan, bukan salah |
| Murah digambar | butuh 20 objek | bisa dibuat dari 3–5 bentuk |

**Tes cepat:** bisa kamu jelaskan analogi ini ke nenek dalam satu kalimat tanpa
memakai istilah teknis? Kalau tidak, ganti.

### Contoh analogi yang sudah terbukti

| Konsep | Analogi | Kenapa jalan |
|---|---|---|
| Inflasi | harga di warung naik pelan-pelan, uang jajan tetap | semua orang pernah mengalaminya |
| Bunga bank | menanam pohon, buahnya bertambah tiap musim | pertumbuhan terlihat |
| Saham | harga cabai di pasar: ramai pembeli, harga naik | naik-turun terasa wajar |
| Pajak | iuran kelas untuk beli sapu dan papan tulis | kepemilikan bersama |
| Utang negara | pinjam uang ke tetangga untuk perbaiki atap | kebutuhan vs kemampuan |
| Internet | jaringan jalan antar rumah | rute yang harus dilalui |
| Wi-Fi | suara yang menembus dinding tapi melemah | jarak melemahkan |
| AI | teman yang sudah membaca jutaan buku lalu menebak | pintar tapi bisa salah |
| Baterai | ember air yang bocor sedikit-sedikit | berkurang tanpa terlihat |
| Memori | lemari arsip dengan laci berlabel | penyimpanan & pengambilan |
| Tidur | shift malam: pekerja datang saat toko tutup | aktif saat tampak diam |
| Jantung | pompa air yang tidak pernah dimatikan | terus bekerja |
| Laut asin | sup yang kebanyakan garam | rasa yang dikenal |
| Pesawat terbang | tangan di luar jendela mobil ikut terangkat | angkat terasa |
| Es mengapung | pelampung di kolam | benda ringan mengapung |
| Hujan | jemuran basah lalu air naik ke awan | siklus yang terlihat |
| Waktu cepat | antrean vs main game | pengalaman subjektif |

---

## 5. Kapan membuat karakter tamu

Buat tamu **hanya kalau** memenuhi salah satu:

1. Ada pertanyaan yang lebih wajar diucapkan orang lain (Ardi: "Inflasi itu apa sih, Boca?").
2. Ada situasi yang butuh pemilik tempat (Bu Ratna di warung, Pak Darno di bengkel).
3. Ada otoritas yang masuk akal (Dokter Nia untuk topik tubuh).

**Jangan** membuat tamu kalau:

- hanya untuk mengulang pertanyaan yang bisa diucapkan Lumi;
- hanya muncul 1 shot lalu hilang tanpa alasan;
- menambah karakter ke-4 dalam satu episode.

Aturan tamu:

- Maksimal **1 tamu** per episode.
- Minimal muncul di **2 shot** (bukan cameo sekali lewat).
- Harus punya alasan berada di lokasi itu.
- Tidak boleh lebih pintar dari Boca — tamu bertanya, Boca menjelaskan.

---

## 6. Twist — beat yang paling sering dilupakan

Tanpa twist, episode terasa seperti definisi kamus. Twist yang dipakai:

| Tipe | Contoh |
|---|---|
| **Pengecualian** | "Tapi ada satu benda yang justru mengapung walau berat." |
| **Konsekuensi tak terduga** | "Karena itu, makin banyak uang dicetak, makin murah nilainya." |
| **Perbandingan** | "Di antrean 5 menit terasa 1 jam, main 1 jam terasa 5 menit." |
| **Balik arah** | "Ternyata bukan uangnya hilang, tapi pergi sedikit-sedikit." |

Twist harus **dipersiapkan** di setup (bukan kejutan tanpa dasar).

---

## 7. CTA

| Kode | Pola | Contoh |
|---|---|---|
| `C1` | pertanyaan pengalaman | "Kamu pernah kehilangan uang kecil ke mana?" |
| `C2` | tebakan | "Menurutmu, besok harganya naik lagi?" |
| `C3` | aksi kecil | "Coba lihat langit sore ini." |
| `C4` | simpan/bagikan | "Simpan buat tugas sekolah." |
| `C5` | lanjut seri | "Besok Boca masuk ke dalam HP." |

CTA **tidak boleh** meminta follow secara eksplisit di setiap episode (maksimal
1 dari 5 episode).

---

## 8. Bahasa

- Kalimat VO: **≤ 14 kata**. Caption besar: **≤ 9 kata**.
- Dilarang: "Adek", "dek", "adik", "kakak", "bunda", "sayang", "teman-teman".
- "kamu" maksimal **1×** per episode.
- Tidak ada istilah teknis tanpa analogi langsung di kalimat yang sama.
- Tidak meremehkan: hindari "gampang banget", "masa nggak tahu".

---

## 9. Contoh utuh: inflasi (60 s, tamu Bu Ratna)

| Beat | Shot | Scene | Isi |
|---|---|---|---|
| HOOK | 1 | `market` | Bu Ratna mengganti papan harga. "Harganya naik lagi, Boca." |
| SETUP | 2 | `market` | Ardi hitung uang jajan: "Uangku sama, tapi dapatnya lebih sedikit." |
| EXPLAIN | 3–5 | `market` → `kitchen` | Boca: "Bayangkan warung ini satu dunia kecil..." |
| TWIST | 6–7 | `city_street` | "Bukan cuma di warung ini. Semua harga ikut naik." |
| PAYOFF | 8 | `market` | Ardi paham: "Jadi uangku bukan hilang, tapi tenaganya mengecil." |
| CTA | 9 | `market` | "Barang apa yang harganya naik di tempatmu?" |

Perhatikan: pertanyaan tidak diucapkan Boca, tapi **dialami** Ardi.
Analogi tidak dijelaskan Boca sendirian — ada yang merespons.
