# BOCA-D03 — Kenapa kita harus tidur?

**Motif:** M3 think→lightbulb · **Mood:** malam hangat · **Durasi:** ~45.4 s
**Scene:** `bedroom_night` → `bedroom` → `body_inside` → `neuron_city` → `body_inside` → `bedroom_night`
**Kata:** 145 · **Baris Lumi:** 2

| # | Scene | Kamera | Gerak Boca | Lumi | SFX | Durasi |
|---|---|---|---|---|---|---|
| 1 | `bedroom_night` | C7 static wide | walk-in → sleepy → think → focus | float kanan, kaget | whoosh | 7.5 s |
| 2 | `bedroom` | C1 push-in | stand → point → gesture | float kanan | — | 7.5 s |
| 3 | `body_inside` | C4 pan kanan | walk-in → kaget → point | float + point | sparkle | 7.5 s |
| 4 | `neuron_city` | C7 static wide | stand → point → gesture | float kanan | pop | 7.5 s |
| 5 | `body_inside` | C1 push-in | think → bingung → fokus → senang | kaget | — | 7.8 s |
| 6 | `bedroom_night` | C8 push-in kuat | senang → wave → cheer | cheer + wave | chime | 7.5 s |

## Naskah VO

**Shot 1 — hook**
- **BOCA:** "Setiap malam, tubuh kita seperti mematikan lampu sendiri tanpa kita pernah sadari."
  - caption: `tubuh mematikan lampu sendiri`
  - emosi: penasaran · jeda setelah: 0.25 s
- **LUMI:** "Lampu apa yang dimatikan? Aku nggak melihat ada saklar di rumah ini."
  - caption: `lampu apa yang dimatikan`
  - emosi: heran

**Shot 2 — gap**
- **BOCA:** "Padahal tidur bukan cuma berhenti bergerak, ada pekerjaan besar di dalam tubuh."
  - caption: `tidur bukan sekadar berhenti bergerak`
- **BOCA:** "Kita merasa hanya memejamkan mata, tapi organ kita sedang berganti shift kerja."
  - caption: `organ kita berganti shift kerja`
  - jeda setelah: 0.2 s

**Shot 3 — explain**
- **BOCA:** "Saat tidur, otak merapikan ingatan hari ini seperti memilah foto ke album."
  - caption: `otak merapikan ingatan hari ini`
- **LUMI:** "Jadi ingatan yang penting dipindah ke album yang lebih aman, ya, Boca?"
  - caption: `dipindah ke album lebih aman`
  - emosi: senang

**Shot 4 — analogy**
- **BOCA:** "Ingatan yang sering dipakai dirapikan, yang jarang dipakai disingkirkan pelan-pelan sekali."
  - caption: `yang sering dipakai dirapikan`
- **BOCA:** "Jaringan otak yang baru dipakai akan dirapikan supaya besok lebih mudah dipanggil."
  - caption: `jaringan otak dirapikan`

**Shot 5 — twist**
- **BOCA:** "Tubuh juga memperbaiki sel yang rusak dan mengisi ulang tenaga untuk besok pagi."
  - caption: `tubuh memperbaiki sel dan tenaga`
- **BOCA:** "Karena itu kurang tidur bikin kita lambat berpikir dan gampang kesal sekali."
  - caption: `kurang tidur bikin lambat berpikir`
  - jeda setelah: 0.25 s

**Shot 6 — cta**
- **BOCA:** "Jadi tidur bukan buang waktu, tapi shift malam yang dijalankan oleh tubuh kita."
  - caption: `tidur itu shift malam tubuh`
- **BOCA:** "Coba ingat, pelajaran apa yang paling nempel setelah kamu tidur cukup semalam?"
  - caption: `pelajaran apa yang paling nempel`
  - emosi: hangat · jeda setelah: 0.3 s

## Catatan visual

- **Shot 1:** Boca masuk dari kiri dalam keadaan setengah mengantuk, kamera diam lebar
  supaya kamar malam terlihat utuh. Lumi muncul belakangan supaya tidak ramai di frame pertama.
- **Shot 2:** push-in pelan ke wajah Boca saat kalimat "pekerjaan besar" — penekanan ada di ekspresi.
- **Shot 3:** pan kanan mengikuti Boca yang "masuk" ke dalam tubuh. Sparkle di awal shot
  menandai perpindahan dunia.
- **Shot 4:** kamera lebar supaya jaringan neuron terasa seperti kota.
- **Shot 5:** push-in lagi, tapi Boca berpindah pose think → fokus supaya tidak mengulang shot 2.
- **Shot 6:** push-in kuat + cheer, penutup hangat. Lumi ikut melambai di kanan.

## Catatan produksi

- `bedroom_night`, `body_inside`, dan `neuron_city` **belum ada di `make_cartoon.py`** —
  harus dibuat sebelum episode ini bisa dirender.
- `facts_status` masih `pending`: klaim tidur–memori–mood perlu diverifikasi sebelum publish.
