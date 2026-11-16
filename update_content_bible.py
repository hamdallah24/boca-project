#!/usr/bin/env python3
"""Build BOCA Content Bible v2 from the existing 30-day plan.

Plan-only: this updates the planning/source-of-truth document.
It does not touch the renderer, engine, or cron job.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

SRC = Path("/sdcard/Download/BOCA_Rencana_Konten_30_Hari.md")
BACKUP = Path("/data/data/com.termux/files/home/projects/boca-character/archive/BOCA_Rencana_Konten_30_Hari.v1.md")

SERIES = {
    "KYB": "Kenapa Ya, Boca?",
    "BMM": "Boca Masuk Mesin",
    "BMT": "Boca Masuk Tubuh",
    "BBU": "Boca Bicara Uang",
    "BLA": "Boca ke Luar Angkasa",
}

DURATION = {
    1: 45, 2: 45, 3: 60, 4: 45, 5: 60, 6: 45, 7: 45,
    8: 60, 9: 60, 10: 45, 11: 90, 12: 45, 13: 60, 14: 45,
    15: 45, 16: 60, 17: 45, 18: 60, 19: 45, 20: 45, 21: 60,
    22: 60, 23: 90, 24: 60, 25: 60, 26: 60, 27: 60, 28: 60,
    29: 60, 30: 90,
}

COMPLEXITY = {
    1: "B", 2: "B", 3: "B", 4: "B", 5: "C", 6: "B", 7: "B",
    8: "C", 9: "B", 10: "B", 11: "C", 12: "B", 13: "B", 14: "B",
    15: "B", 16: "C", 17: "B", 18: "C", 19: "B", 20: "B", 21: "B",
    22: "B", 23: "C", 24: "B", 25: "B", 26: "B", 27: "C", 28: "B",
    29: "C", 30: "C",
}

FACT = {i: "pending" for i in range(1, 31)}
for i in (11, 23, 25, 26, 27, 29, 30):
    FACT[i] = "high-risk"

CTA = {
    1: "Kamu pernah kehilangan uang kecil ke mana?",
    2: "Coba lihat langit sore ini, warnanya apa?",
    3: "Kamu tidur jam berapa tadi?",
    4: "Waktu apa yang paling cepat buat kamu?",
    5: "Pernah naik pesawat? Ke mana?",
    6: "Kamu suka laut atau gunung?",
    7: "Coba tahan napas, masih cegukan?",
    8: "Menurutmu internet itu di mana?",
    9: "HP kamu pernah nyasar lokasi?",
    10: "Baterai HP kamu sekarang berapa persen?",
    11: "Pernah tanya AI? Jawabannya aneh nggak?",
    12: "Wi-Fi di kamar kamu kuat?",
    13: "Lebih suka cash atau QR?",
    14: "Pernah kehilangan foto penting?",
    15: "Coba hitung detak jantungmu.",
    16: "Mimpi aneh apa yang pernah kamu alami?",
    17: "Perut kamu bunyi kalau lapar?",
    18: "Ingatan masa kecil apa yang masih kamu simpan?",
    19: "Kamu takut apa?",
    20: "Es batu kamu mengapung?",
    21: "Hujan di kotamu gimana?",
    22: "Barang apa yang harganya naik?",
    23: "Menurutmu utang negara itu kayak apa?",
    24: "Pernah pinjam uang?",
    25: "Kamu punya aset produktif?",
    26: "Kalau bisa cetak uang, mau beli apa?",
    27: "Saham atau tabungan?",
    28: "Fasilitas umum apa yang paling kamu pakai?",
    29: "Kalau Bumi berhenti, kamu mau di mana?",
    30: "Menurutmu alam semesta ada ujungnya?",
}


def series_for(day: int) -> str:
    if day <= 7:
        return "KYB"
    if day <= 14:
        return "BMM"
    if day <= 21:
        return "BMT"
    if day <= 28:
        return "BBU"
    return "BLA"


def meta_line(day: int) -> str:
    code = series_for(day)
    return (
        f"**Meta:** `BOCA-D{day:02d}` · Seri: `{code}` — {SERIES[code]} · "
        f"Durasi: `{DURATION[day]}s` · Kompleksitas: `{COMPLEXITY[day]}` · "
        f"Fakta: `{FACT[day]}` · Status: `planned` · CTA: \"{CTA[day]}\""
    )


def registry_table(titles: dict[int, str]) -> str:
    rows = [
        "| ID | Hari | Judul | Seri | Durasi | Kompleksitas | Fakta | Status | CTA |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for day in range(1, 31):
        code = series_for(day)
        title = titles.get(day, f"Hari {day:02d}")
        rows.append(
            f"| `BOCA-D{day:02d}` | {day:02d} | {title} | `{code}` | {DURATION[day]}s | "
            f"{COMPLEXITY[day]} | {FACT[day]} | planned | {CTA[day]} |"
        )
    return "\n".join(rows)


def main() -> None:
    original = SRC.read_text(encoding="utf-8")
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        shutil.copy2(SRC, BACKUP)
        print("backup:", BACKUP)

    rules = original[original.index("# Aturan umum untuk agent"):original.index("# Kalender 30 hari")]
    rules = rules.replace("# Aturan umum untuk agent", "## Aturan umum untuk agent", 1).strip()

    calendar = original[original.index("# Kalender 30 hari"):]
    headings = re.findall(r"^### Hari (\d+) --- (.+)$", calendar, flags=re.M)
    titles = {int(day): title.strip() for day, title in headings}
    if len(titles) != 30:
        raise SystemExit(f"expected 30 day headings, got {len(titles)}")

    calendar = re.sub(
        r"^(### Hari (\d+) --- .+)$",
        lambda m: m.group(1) + "\n\n" + meta_line(int(m.group(2))),
        calendar,
        flags=re.M,
    )
    calendar = calendar.replace("# Kalender 30 hari", "# 11. Kalender 30 Hari & Storyboard", 1)
    calendar = calendar.replace("# Catatan konsistensi cerita", "# 12. Catatan Konsistensi Cerita", 1)

    header = """---
document: BOCA_CONTENT_BIBLE
version: 2.0
status: source_of_truth
updated: 2026-11-12
canonical_path: /sdcard/Download/BOCA_Rencana_Konten_30_Hari.md
audience: all_ages
character: boca_v1
language: id-ID
format:
  aspect_ratio: "9:16"
  resolution: "1080x1920"
  fps: 30
  duration_default_sec: 60
  duration_tiers_sec: [45, 60, 90]
  captions: dual_layer_burned_in
  safe_area: "top 250px / bottom 350px"
voice:
  engine: edge-tts
  voice_id: id-ID-ArdiNeural
  rate: "+4%"
  pitch: "-2Hz"
render:
  stack: [stickman_kino, remotion_overlay, ffmpeg]
  character_assets: /sdcard/Download/Boca
publishing:
  cadence: daily
  render_time: "03:00 WIB"
  publish_time: "18:00 WIB"
  platforms: [tiktok, instagram_reels, youtube_shorts, facebook_reels]
automation:
  mode: daily_cron
  source_of_truth: this_file
  require_fact_check: true
  require_qa: true
  require_character_lock: true
  auto_publish_if: "fact_check=verified AND qa=pass"
  output_root: /sdcard/Download/BOCA_DAILY
---

# BOCA — Content Bible & Rencana Produksi 30 Hari

**Status:** Source of Truth v2.0 · 12 November 2026  
**Karakter:** Boca v1 — **LOCKED**  
**Audiens:** semua umur  
**Format:** vertikal 9:16 · 45–90 detik · caption dual-layer  
**Mode dokumen:** plan only. Dokumen ini belum mengeksekusi render atau cron job.

## 0. Cara memakai dokumen ini

Dokumen ini adalah **single source of truth** untuk:

- ide dan urutan 30 episode;
- karakter dan identitas visual;
- format, durasi, caption, voice, dan QA;
- aturan fact-check;
- kontrak otomasi untuk cron job harian.

Jika ada konflik dengan file lain, **dokumen ini yang menang**. Automation tidak boleh mengarang topik baru, mengubah karakter, atau mempublikasikan fakta yang belum terverifikasi.

Status episode:

| Status | Arti |
|---|---|
| `planned` | Ide dan storyboard sudah ada, belum diproduksi |
| `scripted` | VO dan caption sudah ditulis |
| `rendered` | Video sudah dirender |
| `qa_passed` | Lolos QA teknis dan konten |
| `published` | Sudah dipublikasikan |
| `failed` | Gagal, perlu retry atau intervensi |

Status fakta:

| Status | Arti |
|---|---|
| `pending` | Belum diverifikasi, belum boleh publish |
| `verified` | Sudah dicek dengan sumber |
| `high-risk` | Wajib 2 sumber independen + review manusia |
| `blocked` | Ada klaim bermasalah, jangan diproduksi |

__RULES__

## 1. Audiens & positioning

**Audiens: semua umur.** Bukan channel balita, bukan channel dewasa. Tujuannya menjelaskan hal rumit dengan cara ringan, hangat, dan mudah dimengerti.

Cara satu episode melayani beberapa audiens:

| Audiens | Yang mereka dapat |
|---|---|
| Anak 6–12 | Analogi visual, tokoh Boca, bahasa pendek, humor ringan |
| Remaja / Gen Z | Hook cepat, relatable, punchline, visual yang bisa dibagikan |
| Orang tua / dewasa | Penjelasan inti yang benar, caption terjemahan, tidak menggurui |

**“Bahasa bayi”** berarti parentese-inspired: kalimat pendek, kata sederhana, sapaan “Adek”, nada hangat. Bukan babble tanpa arti, bukan informasi yang dikalahkan oleh gaya.

Contoh caption dual-layer:

> **Baris bayi (besar):** “Langit biru karena udara ikut main warna!”  
> **Terjemahan dewasa (kecil):** “Molekul udara menyebarkan cahaya biru lebih kuat daripada merah.”

Aturan bahasa:

- Maksimal 12–16 kata per kalimat VO.
- Satu kalimat = satu ide.
- Sapaan “Adek” maksimal 2–3 kali per episode.
- Istilah teknis boleh muncul, tapi harus langsung diberi analogi.
- Humor tidak boleh mengaburkan fakta utama.
- Jangan memakai kata “mudah banget” atau meremehkan penonton.

## 2. Karakter Boca v1 — LOCKED

Boca v1 adalah desain final untuk produksi. Jangan mengubah proporsi, pakaian, warna, atau ciri khas antar-scene.

**Ciri canonical:**

- kepala besar oval, sekitar 45% tinggi badan;
- badan bean, tangan-kaki stick;
- topi SD merah-putih dengan badge **SD**;
- rambut hitam, alis tebal, mata besar, pipi blush, tanpa hidung;
- kemeja putih, dasi merah, celana merah;
- tas teal, pensil di belakang telinga;
- name tag **BOCA**;
- sepatu hitam, kaus kaki putih;
- buku sebagai properti utama.

**Palet:**

| Warna | Hex | Pemakaian |
|---|---|---|
| Krem | `#F6F1E7` | background default |
| Tinta | `#231815` | outline, teks |
| Merah sekolah | `#D7263D` | topi, dasi, celana |
| Teal | `#1F6F78` | tas, aksen |
| Kuning | `#F4B942` | pensil, highlight |

**Ekspresi canonical:**

| Ekspresi | Kapan dipakai |
|---|---|
| `neutral` | penjelasan tenang, transisi |
| `shock` | hook, pertanyaan besar, reaksi |
| `happy` | punchline, sapaan, CTA |
| `confused` | analogi yang sengaja dibuat aneh |
| `sleepy` | topik tidur, waktu, rutinitas |
| `focus` | diagram, fakta inti, membaca |

**Pose canonical:**

| Pose | Kapan dipakai |
|---|---|
| `wave` | opening, sapaan, CTA |
| `think` | pertanyaan, konflik, tebakan |
| `read` | edukasi, buku, penjelasan |
| `stand` | default, membawa buku |

**Aset:**

- `/sdcard/Download/Boca/boca-cover-v1.png`
- `/sdcard/Download/Boca/boca-front-v1.png`
- `/sdcard/Download/Boca/boca-front-neutral-v1.png`
- `/sdcard/Download/Boca/boca-expressions-v1.png`
- `/sdcard/Download/Boca/boca-poses-v1.png`
- `/sdcard/Download/Boca/boca-front-v1-transparent.png`
- Source: `~/projects/boca-character/`

**Do / Don’t:**

- DO gunakan ekspresi dan pose yang sudah ada.
- DO ganti lingkungan dan properti sesuai topik.
- DO jaga name tag, dasi, topi, dan tas tetap terlihat.
- DON’T mengubah pakaian atau warna per episode.
- DON’T menambah sidekick permanen.
- DON’T menjadikan Boca guru formal di depan papan tulis sebagai default.
- Perubahan karakter harus lewat approval dan versi baru.

## 3. Format & platform spec

| Item | Spec |
|---|---|
| Aspect ratio | 9:16 |
| Resolution | 1080×1920 |
| FPS | 30 |
| Durasi | 45s / 60s / 90s |
| Caption | dual-layer, burned in |
| Safe area | top 250px, bottom 350px |
| Voice | `id-ID-ArdiNeural`, rate `+4%`, pitch `-2Hz` |
| Audio | -14 s.d. -16 LUFS, true peak ≤ -1.5 dBTP |
| Music | minimal, no lyrics, duck under VO |
| SFX | pop / whoosh / coin / hik, secukupnya |
| On-screen text | 3–7 kata per kartu, maksimal 2 elemen |
| Intro | 0–1 detik brand sting, tanpa intro panjang |
| Platform | TikTok, IG Reels, YouTube Shorts, FB Reels |

**Durasi per topik:**

- 45s: topik sederhana, satu analogi, satu properti.
- 60s: default, dua lapis penjelasan.
- 90s: topik padat (AI, utang negara, saham, alam semesta) atau dipecah 2 part.

**Caption:**

- Baris bayi: 56–72px, bold, max 2 baris.
- Terjemahan dewasa: 30–38px, max 2 baris.
- Posisi aman: jangan menutup mata/mulut Boca.
- Cek overlap antar-caption; toleransi maksimal 0.05s.
- Highlight kata kunci dengan warna kuning/merah, jangan pelangi.

**Voice & sound:**

- VO conversational, bukan pembaca berita.
- Jeda 150–250ms antar-beat.
- Musik turun 10–14 dB saat VO.
- SFX hanya untuk aksen, bukan setiap kalimat.

## 4. Series architecture & hook patterns

| Kode | Series | Fokus | Hari |
|---|---|---|---|
| `KYB` | Kenapa Ya, Boca? | sains sehari-hari | 1–7 |
| `BMM` | Boca Masuk Mesin | teknologi & digital | 8–14 |
| `BMT` | Boca Masuk Tubuh | tubuh & sains | 15–21 |
| `BBU` | Boca Bicara Uang | ekonomi & masyarakat | 22–28 |
| `BLA` | Boca ke Luar Angkasa | misteri & alam semesta | 29–30 |

**Struktur default:**

1. Hook 1–3 detik.
2. Dunia/analogi 3–15 detik.
3. Penjelasan inti 15–35 detik.
4. Pendalaman 35–50 detik.
5. Punchline + CTA 50–60 detik.

**Hook patterns (variasikan, jangan semua pertanyaan):**

- Pertanyaan langsung: “Kenapa uang bisa habis?”
- Kontradiksi visual: dompet kosong padahal tidak beli apa-apa.
- Hitungan: “Coba tebak, ada berapa warna di cahaya matahari?”
- Eksperimen mini: es dimasukkan ke air.
- Pengakuan: “Boca juga baru tahu.”

**CTA patterns:**

- Pertanyaan komentar: “Kamu pernah…?”
- Tebakan: “Menurutmu…?”
- Save/share: “Simpan buat tugas sekolah.”
- Follow seri: “Besok Boca masuk ke….”

## 5. Episode registry

Legenda: `KYB` = Kenapa Ya, Boca? · `BMM` = Boca Masuk Mesin · `BMT` = Boca Masuk Tubuh · `BBU` = Boca Bicara Uang · `BLA` = Boca ke Luar Angkasa.

**Penting:** semua episode masih `pending` untuk fact-check. Cron job tidak boleh publish sebelum status fakta `verified` dan QA `pass`.

__REGISTRY__

## 6. Storyboard template & contoh shot list

Storyboard 5-beat di bagian kalender adalah **narrative beat**, bukan shot list. Sebelum render, setiap episode harus dipecah menjadi shot list.

**Template shot list:**

| Shot | Waktu | Visual | Boca | Camera | Caption | SFX | Catatan |
|---|---|---|---|---|---|---|---|
| 1 | 0.0–2.5s | hook visual | `shock` | close-up | pertanyaan | pop | 1 ide |
| 2 | 2.5–6.0s | dunia/analogi | `confused` | medium | analogi | whoosh | |
| 3 | 6.0–15.0s | penjelasan awal | `focus` | medium | fakta 1 | | |
| 4 | 15.0–25.0s | diagram/properti | `focus` | close-up | fakta 2 | | |
| 5 | 25.0–35.0s | konsekuensi | `shock` | medium | “oh, jadi…” | | |
| 6 | 35.0–45.0s | punchline | `happy` | medium | punchline | pop | |
| 7 | 45.0–50.0s | CTA | `wave` | medium | pertanyaan | | |

**Contoh — `BOCA-D02` “Kenapa langit warnanya biru?” (45s):**

| Shot | Waktu | Visual | Boca | Camera | Caption | SFX |
|---|---|---|---|---|---|---|
| 1 | 0.0–3.0s | Boca mendongak ke langit biru | `shock` | low angle | “Siapa yang ngecat langit?” | pop |
| 2 | 3.0–8.0s | Matahari mengirim cahaya putih ke Bumi | `focus` | wide | “Cahaya matahari itu campuran warna.” | whoosh |
| 3 | 8.0–14.0s | Prisma memisahkan warna | `focus` | close-up | “Merah, kuning, hijau, biru…” | sparkle |
| 4 | 14.0–22.0s | Atmosfer, partikel menyebarkan biru | `focus` | macro | “Partikel udara menyebarkan biru.” | |
| 5 | 22.0–30.0s | Langit dari permukaan Bumi | `happy` | medium | “Jadi biru itu warna yang paling banyak tersebar.” | pop |
| 6 | 30.0–38.0s | Perbandingan sunset merah | `confused` | wide | “Saat sore, jalurnya lebih panjang.” | |
| 7 | 38.0–45.0s | Boca pakai kacamata hitam | `happy` | medium | “Bukan cat, tapi udara yang main warna.” | pop |

## 7. Fact-check protocol & high-risk ledger

Aturan:

- Tidak ada angka, kutipan, sejarah, atau klaim ilmiah tanpa sumber.
- Topik `high-risk` wajib 2 sumber independen.
- Sumber prioritas: lembaga resmi, jurnal, ensiklopedia tepercaya, dokumentasi resmi.
- Catat klaim, sumber, tanggal akses, status, dan catatan visual.
- Jangan memakai visual yang bertentangan dengan fakta.

**High-risk ledger (isi sebelum produksi):**

| ID | Klaim yang harus dicek | Sumber 1 | Sumber 2 | Status | Catatan visual |
|---|---|---|---|---|---|
| `BOCA-D11` | AI memprediksi token berikutnya | TODO | TODO | pending | jangan tampilkan AI sebagai manusia kecil |
| `BOCA-D23` | negara meminjam & membayar utang | TODO | TODO | pending | jangan menyamakan utang negara dengan utang pribadi |
| `BOCA-D25` | aset produktif & compounding | TODO | TODO | pending | wajib disclaimer risiko |
| `BOCA-D26` | pencetakan uang & inflasi | TODO | TODO | pending | inflasi banyak penyebab |
| `BOCA-D27` | harga saham naik-turun | TODO | TODO | pending | bukan prediksi |
| `BOCA-D29` | Bumi berhenti berputar | TODO | TODO | pending | skenario hipotetis |
| `BOCA-D30` | batas alam semesta teramati | TODO | TODO | pending | batas pengamatan ≠ dinding |

## 8. Visual complexity & asset reuse

| Tier | Arti | Contoh | Strategi |
|---|---|---|---|
| A | sederhana | satu ruangan, 1–2 properti | aman untuk harian |
| B | sedang | 2–3 lingkungan, diagram | default |
| C | kompleks | luar angkasa, bawah laut, dalam tubuh, bursa | batch + reuse |

Aturan:

- Maksimal 1 lingkungan baru + 2 properti baru per episode.
- Reuse: kamar, jalan kota, pasar mini, taman, terowongan tubuh, grid digital, luar angkasa.
- Hindari kerumunan; maksimal 2–3 siluet latar.
- Tier C sebaiknya dipecah 2 part atau dibuat diagram stilasi.
- Simpan aset lingkungan di folder reusable, bukan per episode.

## 9. Automation contract untuk cron job harian

**Ini spesifikasi, belum implementasi.** Cron job nanti membaca dokumen ini sebagai source of truth.

**Pipeline:**

1. `select_next_episode` — pilih episode `planned` berikutnya dengan fakta `verified`.
2. `validate_contract` — cek karakter, durasi, platform, aset, fact-check.
3. `generate_script` — ubah 5-beat storyboard jadi VO + caption dual-layer.
4. `generate_shot_list` — isi template shot list; jangan mengarang fakta.
5. `render` — Stickman Kino untuk karakter, Remotion untuk overlay, FFmpeg untuk komposit.
6. `qa` — cek teknis, konten, karakter, caption, audio.
7. `publish` — upload ke platform atau ekspor ke folder publish.
8. `log` — catat status, output, error, dan post ID.

**State machine:**

`planned → scripted → rendered → qa_passed → published`

Jika gagal: `failed` → retry 2× → fallback ke buffer → alert.

**Idempotency:**

- Kunci: `episode_id + tanggal`.
- Jangan render ulang jika output sudah ada dan QA pass.
- Jangan publish dua kali untuk episode yang sama.

**Jadwal:**

- 03:00 WIB — render episode untuk besok.
- 18:00 WIB — publish episode hari ini.
- Buffer minimal 7 hari; kalau buffer < 3, produksi tambahan.

**Output:**

```
/sdcard/Download/BOCA_DAILY/YYYY-MM-DD_BOCA-Dxx/
  video.mp4
  poster.png
  captions.srt
  script.md
  qa.json
  publish.json
```

**Gate:**

- `fact_check=verified` wajib sebelum render final.
- `qa=pass` wajib sebelum publish.
- `high-risk` wajib review manusia.
- Perubahan karakter, format, atau series wajib approval.

**Logging:**

- `production_log.jsonl` berisi timestamp, episode_id, stage, status, durasi, error.
- Jangan simpan credential di log.

## 10. QA checklist

**Teknis:**

- [ ] 1080×1920, 30fps.
- [ ] Durasi sesuai tier.
- [ ] Audio -14 s.d. -16 LUFS, true peak ≤ -1.5 dBTP.
- [ ] Caption burned in, tidak overlap >0.05s.
- [ ] Safe area atas/bawah aman.
- [ ] Tidak ada frame hitam/asset hilang.

**Konten:**

- [ ] Hook muncul dalam 1–3 detik.
- [ ] Satu ide utama per episode.
- [ ] Fakta sudah `verified`.
- [ ] Analogi tidak bertentangan dengan fakta.
- [ ] Punchline jelas.
- [ ] CTA singkat.

**Karakter:**

- [ ] Topi, dasi, name tag, tas, pensil sesuai Boca v1.
- [ ] Ekspresi dan pose sesuai beat.
- [ ] Proporsi dan warna tidak berubah.
- [ ] Tidak ada sidekick permanen.

**Platform:**

- [ ] Tidak ada watermark platform lain.
- [ ] Caption aman untuk TikTok/IG/Shorts/FB.
- [ ] Poster/thumbnail siap.
- [ ] Judul dan deskripsi tidak clickbait palsu.

---

"""

    header = header.replace("__RULES__", rules)
    header = header.replace("__REGISTRY__", registry_table(titles))

    changelog = """

---

# 13. Changelog

| Versi | Tanggal | Perubahan |
|---|---|---|
| 2.0 | 2026-11-12 | Audiens dikunci semua umur; Boca v1 dikunci; ditambah registry 30 episode, template shot list, fact-check ledger, visual complexity, automation contract, QA checklist |
| 1.0 | 2026-11-12 | Rencana konten 30 hari dan storyboard 5-beat |

**Catatan:** dokumen ini plan-only. Cron job, renderer, dan publishing belum diimplementasikan.
"""

    new_text = header + calendar.rstrip() + changelog
    SRC.write_text(new_text, encoding="utf-8")
    print("wrote:", SRC)
    print("lines:", len(new_text.splitlines()))
    print("bytes:", len(new_text.encode("utf-8")))


if __name__ == "__main__":
    main()
