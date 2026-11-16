# BOCA Skills — cara pakai

Tiga skill OpenCode yang membuat agent mana pun (Codex, Claude, Gemini, model
gratis di OpenCode) langsung patuh pada aturan produksi BOCA tanpa perlu
menempel prompt panjang.

## Isi

| Skill | Kapan aktif | Isi |
|---|---|---|
| `boca-storyboard` | user minta episode, naskah, VO, hook, analogi | 6 beat, registry 30 hari, budget kata, aturan cast, hard rules |
| `boca-visual` | menulis shot, kamera statis, render gagal | scene library, kamera C1–C9, motif M1–M8, skema `keys`, anti-pola |
| `boca-qa` | sebelum render, validator gagal, mau publish | validator, konversi plan, gate publish, katalog error |

## Agent khusus: `boca`

`.opencode/agents/boca.md` — agent primary yang menangani seluruh produksi.

```bash
cd ~/projects/boca-character
opencode --agent boca
```

Yang dikunci di agent:

| Aspek | Nilai |
|---|---|
| Model | `opencode/deepseek-v4.1-flash-free#high` |
| Mode | primary |
| Max steps | 80 |
| Warna | `#2DD4BF` |

Guard yang dipasang:

| Aksi | Efek |
|---|---|
| edit `production/*/BOCA-D01.json` dan `D02` | **deny** |
| `shell` berisi `rm -rf` | **deny** |
| `shell` berisi `--publish` | **ask** |
| `shell` berisi `git push` | **ask** |
| sisanya | allow |

Ganti model cukup satu baris di frontmatter:

```yaml
model: opencode/<model>#<variant>
```

## Struktur file

```
.opencode/
├── agents/
│   └── boca.md
└── skills/
    ├── boca-storyboard/
    │   ├── SKILL.md
    │   └── references/cast.md
    ├── boca-visual/
    │   ├── SKILL.md
    │   └── references/scenes.md
    └── boca-qa/
        ├── SKILL.md
        └── references/publish.md
```

OpenCode menemukan skill dari `.opencode/skills/<id>/SKILL.md`. ID = nama
direktori, `name` di frontmatter hanya label tampilan.

## Instalasi

Sudah terpasang di dua tempat:

1. **Project** — otomatis saat OpenCode dijalankan di dalam repo ini.
2. **Global** — `~/.config/opencode/opencode.json` berisi:

```jsonc
{
  "skills": ["~/projects/boca-character/.opencode/skills"]
}
```

Dengan begitu skill tetap tersedia walau OpenCode dibuka dari direktori lain.

## Cara memakai

Cukup minta seperti biasa — skill dipilih otomatis dari `description`:

```
buat episode D05
```

```
D07 gagal validasi, perbaiki
```

```
render D03 lalu cek QA
```

Kalau ingin memaksa, sebut namanya:

```
pakai boca-visual, shot D03 terlalu statis
```

## Prinsip pemeliharaan

- **`docs/` adalah sumber kebenaran.** Skill adalah prosedur ringkas.
- Kalau aturan berubah (misal budget kata), ubah `docs/` **dan** `SKILL.md`
  dalam satu commit. Jangan biarkan berbeda.
- Detail panjang masuk `references/`, bukan `SKILL.md`. Batas praktis:
  `SKILL.md` ≤ 500 baris.
- `description` menentukan skill terpanggil atau tidak. Sertakan kata yang
  benar-benar diucapkan user ("buat episode", "validator", "publish").

## Validasi

```bash
python3 tools/check_skills.py
```

Cek frontmatter, kecocokan `name` dengan direktori, panjang `description`,
dan referensi file yang hilang.

## Hubungan dengan dokumen lain

| Dokumen | Peran |
|---|---|
| `docs/STORY_ARCHITECTURE.md` | aturan cerita lengkap |
| `docs/CHARACTER_SYSTEM.md` | cast & suara |
| `docs/SCENE_MOTION_SPEC.md` | kontrak render |
| `docs/CODEX_PROMPT_MASTERPLAN.md` | prompt untuk agent di luar OpenCode |
| `.opencode/skills/*` | prosedur yang dipakai agent di dalam OpenCode |
