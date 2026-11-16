# BOCA Art Upgrade v4.3 — Desain Teknis

Status: **desain + modul baru sudah jadi & sudah diuji render**, belum di-wire ke
`boca_pipeline.py`. Dokumen ini adalah kontrak implementasi.

Tujuan: menyatukan gaya visual (SVG bergaris), memecah shot statis 8 detik jadi
4 mode layout, memperbesar prop jadi centerpiece, memperbaiki elastisitas aktor,
dan membuat HUD + badge speaker benar-benar terbaca di 9:16.

File baru:

| File | Isi |
|---|---|
| `scene_svg.py` | 4 layer SVG per scene (`sky/clouds/midground/ground`), `city_street` + `classroom` |
| `props_svg.py` | `clock`, `phone`, `hourglass` — prop besar + animasi scripted |
| `layouts.py` | resolver layout, kartu infografis, spotlight mask, kamera close-up |

Hasil uji (sudah dilihat, bukan asumsi):

- `city_street-flat2.png` — langit bergradien halus + awan & gedung ber-outline 9 px.
- `classroom-flat3.png` — papan, jendela, jam, rak, 4 meja ber-outline; tanpa blur.
- `props-big.png` — jam 380 px, HP 420 px, hourglass 420 px (satu sheet).
- `card-test2.png` — kartu 820 px (compare bars + badge VS) di atas scene.

---

## 0. Ringkasan pemetaan 5 aturan → implementasi

| Aturan | Implementasi |
|---|---|
| 1. SVG bergaris, bukan PIL blur | `scene_svg.py` + `props_svg.py`, raster Chromium di `Art.build()`, cache disk `production/cache/scenes/<scene>/<layer>.png` |
| 2. 4 mode layout | `layouts.py` + field `layouts[]` per shot; resolver per frame; kartu 820 px; spotlight mask |
| 3. Prop 280–480 px + animasi | `props_svg.ClockProp/PhoneProp/HourglassProp`; validator `h >= 280` untuk prop beat |
| 4. Elastic 200 ms + bob | `use_squash(dur=0.20)` dipicu pose **dan** expr/arms; tilt 3 varian di-bake, LRU 16 |
| 5. HUD 1,5× + badge di kaki | `motion.use_hud` skala baru; `draw_speaker_badge()` setelah aktor, chip lama dihapus |

---

## 1. Scene sebagai layer SVG

### 1.1 Kontrak layer

`scene_svg.build_layers(name, size)` → `dict[str, str]`:

```python
{"sky": "<svg…>", "clouds": "<svg…>",
 "midground": "<svg…>", "ground": "<svg…>"}
```

- Kanvas = `(SW, SH)` = 1350×2400 (sama dengan `build_scene` lama, jadi matematika
  kamera tidak berubah).
- Semua bentuk punya `stroke="#231815" stroke-width="9"` (≈7 px di frame 1080 —
  sebanding dengan outline karakter 14 px di kanvas 1080).
- `sky` opaque; tiga layer lain transparan.
- Tidak ada `GaussianBlur`, tidak ada gradien raster; bayangan = poligon flat
  alpha `#00000018`.

### 1.2 Kenapa 3 layer di-bake, 1 layer live

Meng-composite 4 layer penuh per frame terukur **55 ms/frame** (1080×1920) —
terlalu mahal. Jadi:

- `sky + midground + ground` di-bake jadi satu **plate** (midground 1,0×).
  Ketiganya memang berbagi kecepatan kamera yang sama.
- `clouds` disimpan terpisah dan di-composite live dengan faktor **0,55×** →
  satu-satunya biaya tambahan, terukur **17,6 ms/frame** (termasuk copy frame).
- Scene interior (classroom) menghasilkan layer `clouds` kosong → `None` →
  nol biaya.

Ini tetap parallax berlapis nyata (awan bergerak lebih lambat dari gedung),
tetapi ramah Termux.

### 1.3 Integrasi `Art.build()`

```python
# boca_pipeline.py
from scene_svg import SCENE_SVG
import props_svg

SCENE_CACHE = ROOT / "production" / "cache" / "scenes"


def build_scene_layers(name: str, tmp: Path):
    """Plate (sky+mid+ground) + layer awan terpisah. Cache disk per scene."""
    fn = SCENE_SVG.get(name)
    if fn is None:                       # scene lama: fallback mulus
        return build_scene(name, (SW, SH)), None

    out = SCENE_CACHE / name
    out.mkdir(parents=True, exist_ok=True)
    pngs: dict[str, Image.Image] = {}
    for layer, svg in fn(SW, SH).items():
        png = out / f"{layer}.png"
        if not png.exists():
            sp = tmp / f"scene-{name}-{layer}.svg"
            sp.write_text(svg, encoding="utf-8")
            render_svg(sp, png, SW, SH, transparent=(layer != "sky"))
        pngs[layer] = Image.open(png).convert("RGBA")

    plate = pngs["sky"]
    for key in ("midground", "ground"):
        plate = Image.alpha_composite(plate, pngs[key])
    cloud = pngs["clouds"]
    return plate, (cloud if cloud.getbbox() else None)
```

Di `Art`:

```python
self.plates: dict[str, Image.Image] = {}
self.clouds: dict[str, Image.Image | None] = {}

# di dalam build():
for shot in self.ep.shots:
    if shot.scene not in self.plates:
        plate, cloud = build_scene_layers(shot.scene, self.tmp)
        self.plates[shot.scene] = plate
        self.clouds[shot.scene] = cloud
```

### 1.4 Integrasi loop render

```python
scene = art.plates[shot.scene]           # ganti art.scenes[...]
...
base = scene.crop((ox, oy, ox + cw, oy + ch))
if (cw, ch) != (W, H):
    base = base.resize((W, H), Image.Resampling.LANCZOS)
base = base.convert("RGBA")

cloud_layer = art.clouds.get(shot.scene)
if cloud_layer is not None:
    f = 0.55
    cx0 = int(ox * f) % max(1, scene.width - cw)
    cy0 = int(oy * f) % max(1, scene.height - ch)
    crop = cloud_layer.crop((cx0, cy0, cx0 + cw, cy0 + ch))
    if crop.size != (W, H):
        crop = crop.resize((W, H), Image.Resampling.LANCZOS)
    base.alpha_composite(crop)
```

`motion.use_ambient(..., clouds=False)` sekarang selalu dipakai untuk scene SVG
(awan sudah punya layer sendiri). Scene lama tetap `clouds=True`.

### 1.5 Biaya

| Tahap | Waktu | Frekuensi |
|---|---|---|
| Raster 4 layer @1350×2400 | ±18 s | sekali per scene (cache disk) |
| Composite awan live | 17,6 ms/frame | tiap frame |
| Composite kartu | 3,3 ms/frame | saat layout kartu |
| Composite spotlight | 19,6 ms/frame | saat layout spotlight |

---

## 2. Prop SVG besar + animasi

### 2.1 API

```python
import props_svg

sprite = props_svg.build("clock", 380, tmp / "props-svg")  # cached per (id,h)
frame = sprite.frame(local - t_in)                         # RGBA
```

| Prop | Tinggi | Animasi | Biaya runtime |
|---|---|---|---|
| `clock` | 320–460 | jarum menit 240°/s, jam 20°/s; body+2 jarum PNG diputar PIL | rotate 2× (±4 ms) |
| `phone` | 340–480 | strip chat 9 baris digeser di dalam layar, loop mulus | crop + paste (±3 ms) |
| `hourglass` | 320–440 | 8 state pasir di-bake; flip 180° 0,35 s tiap 3 s | pilih PNG + rotate saat flip |

Semua bagian statis di-raster sekali lewat Chromium; animasi hanya crop/rotate
sprite kecil → tidak ada rasterisasi SVG per frame.

### 2.2 Ukuran & penempatan

- Prop beat: `h 280–480`; prop badge kecil boleh 180–240.
- Band aman lama `y 400–650` diganti: prop besar diletakkan **samping aktor**
  (`x ≤ 240` atau `x ≥ 840`) dan `y` antara `420–760`, supaya tidak menutup
  wajah (pelajaran dari D04).
- Validator (`tools/check_storyboards.py`):

```python
h = int(pr.get("h", 0))
if pr.get("beat") and not (280 <= h <= 520):
    errs.append(f"{sid} shot {shot['n']}: prop '{pr['id']}' h={h} "
                f"(beat prop harus 280–520)")
if not (0 <= float(pr.get("t_in", -1)) < float(pr.get("t_out", -1))):
    errs.append(...)
```

### 2.3 Integrasi `Art`

```python
self.prop_sprites: dict[tuple, props_svg.PropSprite] = {}

for pr in shot.props:
    hh = int(pr.get("h", 320))
    self.prop_sprites[(pr["id"], hh)] = props_svg.build(
        pr["id"], hh, self.tmp / "props-svg")
```

Di loop, ganti `pimg = art.prop_imgs[...]` dengan:

```python
sprite = art.prop_sprites.get((pr["id"], ph))
if sprite is not None:
    pimg = sprite.frame(local - p_in)       # animasi scripted
else:
    pimg = art.prop_imgs.get((pr["id"], ph)) or prop_lib.build(pr["id"], ph)
```

`anim` tetap mengatur pop/float/tilt pembungkus; animasi internal tidak
bergantung pada `anim`.

---

## 3. Empat mode layout

### 3.1 Skema per shot

```json
"layouts": [
  {"mode": "WIDE_STAGE", "from": 0.0, "to": 2.6},
  {"mode": "INFOGRAPHIC_CARD", "from": 2.6, "to": 6.1,
   "card": {"kind": "compare", "title": "2 jam vs 10 menit",
            "unit": "menit", "accent": "#D7263D",
            "left":  {"label": "SCROLL", "value": 120, "max": 120},
            "right": {"label": "FOKUS",  "value": 10,  "max": 120}}},
  {"mode": "CLOSEUP_EMPHASIS", "from": 6.1, "to": 8.4, "z": 1.48},
  {"mode": "SPOTLIGHT_EFFECT", "from": 8.4, "to": 11.0,
   "focus": "boca", "dim": 0.62, "cone": true}
]
```

Aturan waktu (divalidasi):

- `layouts` opsional; tanpa itu = `WIDE_STAGE` sepanjang shot.
- Rentang harus menutup `[0, dur]` tanpa celah; `layouts.normalize()` mengisi
  celah otomatis dengan `WIDE_STAGE`.
- Setiap rentang ≤ **3,8 s** (target 2,5–3,5 s). Validator error bila lebih.
- Shot ≥ 6 s wajib punya ≥ 2 layout.

Kartu mendukung tiga `kind`:

```json
{"kind": "compare",   "left": {"label": "...", "value": 120, "max": 120}, "right": {...}, "unit": "menit"}
{"kind": "checklist", "items": [{"text": "HP disimpan", "ok": true}, {"text": "Notifikasi mati", "ok": true}]}
{"kind": "steps",     "steps": ["Simpan HP", "Matikan notifikasi", "Satu tugas"]}
```

### 3.2 Resolver

```python
# boca_pipeline.py (di dalam loop, setelah `local` dihitung)
lys = shot.layouts or layouts_mod.normalize(None, shot.end - shot.start)
ly = layouts_mod.active(lys, local)
mode = ly.get("mode", "WIDE_STAGE")
```

`Shot` mendapat field baru:

```python
layouts: list[dict] = field(default_factory=list)   # opsional
# from_dict:  layouts=d.get("layouts") or []
# to_dict:    ("layouts", self.layouts) bila non-empty
```

### 3.3 Kamera per mode

```python
if mode == "CLOSEUP_EMPHASIS":
    focus = ly.get("focus", "boca")
    st = actor_state_for(focus, shot, local)      # x, ground, h
    fx, fy, z = layouts_mod.closeup_camera(ly, local, st, W, H)
elif mode == "INFOGRAPHIC_CARD":
    fx, fy, z = 0.5, 0.5, max(1.0, z * 0.94)      # kamera bernapas, tidak panik
elif mode == "SPOTLIGHT_EFFECT":
    fx, fy, z = camd["fx"][1], camd["fy"][1], max(1.0, z)
else:
    fx, fy, z = <rumus lama>
```

`closeup_camera` mengembalikan `z` 1,40–1,55 dengan `use_ease_out_expo` 0,55 s.

### 3.4 INFOGRAPHIC_CARD

Alur per frame:

1. Aktor aktif mengecil `1,0 → 0,52` dan bergeser ke `(150, 1810)` dengan
   `use_ease_out_cubic` 0,35 s. Aktor lain fade-out (`alpha 0` di akhir 0,25 s).
   Skala ini **dilipat ke tinggi sprite** (`h = h_key * zscale * layout_scale`),
   jadi tidak ada resize kedua.
2. Prop disembunyikan selama kartu (menghindari tabrakan).
3. Kartu digambar di `(540, 760)`.
4. Badge speaker diganti label kecil di dalam kartu (opsional).

Kartu di-`build()` sekali per layout:

```python
# Art.build
self.cards: dict[str, list[Path]] = {}
for shot in self.ep.shots:
    for i, ly in enumerate(shot.layouts):
        if ly.get("mode") == "INFOGRAPHIC_CARD":
            spec = ly["card"]
            key = f"{ep.id}-s{shot.n:02d}-l{i}"
            frames = []
            dur = ly["to"] - ly["from"]
            for k in range(int(dur * CARD_FPS) + 1):          # CARD_FPS = 12
                t_loc = k / CARD_FPS
                img = layouts_mod.draw_card(spec, t_loc, t_loc, 0.0)
                p = self.tmp / "cards" / f"{key}-{k:03d}.png"
                p.parent.mkdir(parents=True, exist_ok=True)
                img.save(p)
                frames.append(p)
            self.cards[key] = frames
```

Runtime:

```python
frames = art.cards[key]
idx = min(len(frames) - 1, int((local - ly["from"]) * CARD_FPS))
card = Image.open(frames[idx]).convert("RGBA")   # LRU 8 frame
pop = motion.use_spring_pop((local - ly["from"]) / 0.42, 1.10)
if abs(pop - 1.0) > 0.004:
    card = card.resize((int(card.width * pop), int(card.height * pop)),
                       Image.Resampling.LANCZOS)
base.paste(card, (540 - card.width // 2, 760 - card.height // 2), card)
```

Biaya: buka PNG ±4 ms + paste 3,3 ms. Tidak ada rasterisasi kartu per frame.

### 3.5 SPOTLIGHT_EFFECT

Mask di-bake 8 langkah fade per layout (L, 1080×1920, blur 60 px):

```python
self.spots: dict[str, list[Image.Image]] = {}
for ly in shot.layouts:
    if ly.get("mode") == "SPOTLIGHT_EFFECT":
        self.spots[key] = [
            layouts_mod.spot_mask((W, H), cx, cy, ly, step / 7)
            for step in range(8)
        ]
```

Runtime (sebelum aktor digambar, sesudah parallax):

```python
masks = art.spots.get(key)
if masks:
    st = actor_state_for(ly.get("focus", "boca"), shot, local)
    step = min(7, int((local - ly["from"]) / 0.45 * 8))
    shade = Image.new("RGBA", (W, H), (8, 10, 14, 255))
    shade.putalpha(masks[step])
    base.alpha_composite(shade)      # 19,6 ms
```

Karena aktor digambar setelahnya, subjek tetap terang; aktor lain:

```python
if mode == "SPOTLIGHT_EFFECT" and who != ly.get("focus"):
    sprite = Image.eval(sprite, lambda v: int(v * 0.62))   # hanya RGB
```

(opsional, biaya ±3 ms; bisa dimatikan untuk menghemat.)

### 3.6 CLOSEUP_EMPHASIS

- `z = 1.40–1.55` (di dalam batas validator 1,0–1,6).
- Aktor digeser ke tengah (`char_dx = 540 - x`) dengan ease-out-cubic 0,35 s.
- Dipakai untuk hook, reaksi `shock`, dan punchline — bukan untuk dialog
  informatif (kartu lebih baik).

### 3.7 Urutan gambar (final)

```
plate → clouds (0,55×) → ambient → spotlight → aktor → prop → kartu →
fg layer (1,30×) → speed-lines → HUD → badge speaker → subtitle
```

---

## 4. Elastisitas & bob

### 4.1 Squash 200 ms

`motion.use_squash(..., dur=0.20)` (default lama 0,26). Impuls dipicu untuk
**setiap** perubahan `pose`, `expr`, atau `arms`, bukan hanya pose:

```python
impulses = []
prev_key = None
for k in shot.keys:
    sig = (k["pose"], k["expr"], tuple(k.get("arms", [0])))
    if prev_key is not None and sig != prev_key:
        impulses.append(float(k["t"]))
    prev_key = sig
```

Kurva tetap `scaleY: 1,0 → 0,92 → 1,05 → 1,0` (volume terjaga `sx = 1/sy`).

### 4.2 Bob ±2° saat bicara

Rotasi sprite penuh terukur **172 ms/frame** → tidak mungkin runtime. Solusi:
bake 3 varian tilt (`-2°, 0°, +2°`) per sprite, muat lazy:

```python
# Art.build: simpan hanya varian 0 di RAM
self.sprites[(expr, pose, arm, step, prop)] = open(png0)

# runtime, hanya aktor yang sedang bicara:
ang = math.sin(local * 2 * math.pi * 1.7) * 2.0
step = 0 if ang < -0.7 else (2 if ang > 0.7 else 1)
sprite = art.tilt(expr, pose, arm, step, prop, step)   # LRU 16
```

`art.tilt()` membuka `sprites/tilt{step}/...png`; bila tidak ada (aktor diam),
pakai varian 0. Memori maksimum ±16 sprite ≈ 60 MB.

Tambahan bob vertikal murah (tanpa rotate): `top += int(sin(t*4.1)*3)`.

### 4.3 Mata tidak "setengah tidur"

`make_boca.head()`: untuk `expr in ("neutral","talk","happy")` pupil digambar
penuh (`ry` 0,9 dari kelopak); hanya `expr="tired"` yang memakai kelopak 55%.
Ini perubahan kecil di SVG, bukan renderer.

---

## 5. HUD 1,5× & badge speaker

### 5.1 HUD (`motion.use_hud`)

| Elemen | Lama | Baru |
|---|---|---|
| font chip | 22 | 33 |
| tinggi chip | 38 | 56 |
| posisi chip | (40, 34) | (36, 26) |
| pill `HARI nn` | tinggi 38, alpha 150 | tinggi 56, `#111827` α 0,85 |
| progress bar | 7 px | 10 px |
| safe zone | y < 220 | y < 190 |

```python
chip_h = 56
font = ImageFont.truetype(FONT, 33)
label = f"BOCA · {ep.series}"
...
cd.rounded_rectangle((0, 0, cw - 1, chip_h - 1), chip_h // 2,
                     fill=(17, 24, 39, 217))          # #111827 @ 85%
cd.rounded_rectangle((10, 10, 24, chip_h - 10), 7, fill=(*hot, 255))
cd.text((36, chip_h // 2 + 1), label, font=font, fill=(255, 255, 255, 255), anchor="lm")

day_txt = f"HARI {use_rolling_value(t - 0.15, 0.7, ep.day):02d}"
d.rounded_rectangle((W - 36 - tw - 22, 26, W - 18, 26 + chip_h), chip_h // 2,
                    fill=(17, 24, 39, 217))
d.text((W - 36, 26 + chip_h // 2 + 1), day_txt, font=font,
       fill=(255, 236, 120, 255), anchor="rm")
```

### 5.2 Badge speaker di kaki

Hapus chip di atas subtitle (`Subtitle.draw`), ganti:

```python
def draw_speaker_badge(im, label, color, x, ground, font):
    d = ImageDraw.Draw(im, "RGBA")
    tw = int(d.textlength(label, font=font))
    y = min(ground + 14, CAPTION_TOP - 58)
    d.rounded_rectangle((x - tw / 2 - 20, y, x + tw / 2 + 20, y + 44), 22,
                        fill=(17, 24, 39, 210))
    d.text((x, y + 22), label, font=font, fill=color, anchor="mm")
```

- Warna: BOCA merah, LUMI emas, tamu biru muda.
- Posisi: `x` aktor, `ground + 14` (di bawah kaki), clamp agar tidak menabrak
  subtitle (1570).
- Disembunyikan saat `INFOGRAPHIC_CARD` (aktor sudah kecil) dan saat
  `SPOTLIGHT_EFFECT` untuk aktor yang tidak disorot.

---

## 6. VO: pakai audio yang sudah ada (tanpa Gemini)

Tidak ada panggilan TTS baru untuk uji ulang D04. Dua jalur:

1. **Build normal** (produksi harian): TTS cache seperti sekarang; bila cache
   hit, tidak ada request ke Gemini.
2. **`--reuse-vo <dir>`** (uji visual D04): pakai `voiceover.wav` +
   `boca-*.srt` yang sudah ada untuk merekonstruksi timing per baris.

```python
def load_vo_reuse(dir_: Path, ep: Episode):
    wav = dir_ / "voiceover.wav"
    cues = parse_srt(next(dir_.glob("*.srt")))        # [(start, end), ...]
    lines = [ln for shot in ep.shots for ln in shot.dialogue]
    if len(cues) != len(lines):
        raise SystemExit(f"reuse-vo: {len(cues)} cue != {len(lines)} baris")
    bounds, t = [], 0.0
    for i, (ln, (s, e)) in enumerate(zip(lines, cues)):
        bounds.append((s, e, ln.who, i, ln.who))
    return wav, bounds, np.zeros(0)   # env dibaca dari wav oleh speech_env
```

SRT D04 punya 14 cue = 14 baris dialog (sudah dicek), jadi rekonstruksi eksak
(start/end per baris). Word-timing subtitle dihitung proporsional dari durasi cue — sama
dengan cara lama yang memakai durasi wav per baris.

Ke depannya `build_voice_track` menulis `vo/timeline.json`:

```json
{"lines": [{"shot": 1, "idx": 0, "who": "boca", "start": 0.22, "end": 4.66,
            "text": "…", "wav": "s01-l00.wav"}], "duration": 64.86}
```

supaya reuse berikutnya tidak perlu parsing SRT.

---

## 7. Anggaran performa

| Komponen | ms/frame |
|---|---|
| baseline lama (scene+aktor+prop+HUD+subs) | 250–300 |
| + cloud parallax | +11 (composite) |
| + kartu (layout kartu saja) | +4 |
| + spotlight (layout spotlight saja) | +20 |
| total worst case | ±320 |

90 detik @30 fps → 2700 frame → ±15 menit render. Masih dalam jendela cron
(06:00, publish 06:15). Tidak ada tambahan raster SVG per frame.

Optimasi bila perlu: turunkan `CARD_FPS` ke 10, matikan dim aktor lain, atau
render cloud layer di 675×1200.

## 8. Rencana wiring (urutan commit)

1. `Shot.layouts` + validator (`check_storyboards`) + migrasi D04 (prop h ≥ 280).
2. `Art.build`: `build_scene_layers`, `prop_sprites`, `cards`, `spots`.
3. Loop render: plate/clouds, resolver layout, kamera, transform aktor, kartu,
   spotlight, prop sprite.
4. `motion.use_hud` 1,5× + `draw_speaker_badge`; hapus chip subtitle.
5. `--reuse-vo` + `vo/timeline.json`.
6. `make_boca.head()`: mata neutral penuh; tilt varian di-bake.
7. Uji: render 1 shot per mode (contact sheet), lalu D04 penuh dengan
   `--reuse-vo`, QA gate seperti biasa.

---

## 9. Status implementasi (setelah wiring)

Sudah terpasang dan dirender:

- `Shot.layouts`, normalisasi ke durasi VO nyata, validator layout + prop beat.
- `Art.build()`: plate/clouds dari `scene_svg`, prop sprite SVG, kartu 12 fps,
  spotlight 8 langkah, sprite tilt ±2° (lazy, LRU 24).
- Loop render: cloud parallax 0,55×, spotlight sebelum aktor, transform aktor
  (kartu 0,52× ke kiri bawah; close-up ke tengah + aktor lain digeser keluar),
  kartu 820 px, prop animasi, badge speaker di kaki.
- HUD 1,5× (font 33, pill `#111827`, bar 10 px) + squash 200 ms + bob ±2°/±3 px.
- `--reuse-vo`: SRT + voiceover.wav yang sudah ada, nol panggilan Gemini.

Belum:

- Sudah 9 scene SVG: `city_street`, `classroom`, `mountain_sunset`,
  `park_evening`, `city_top`, `data_center`, `market`, `phone_inside`,
  `bedroom`. Scene lain (`beach`, `kitchen`, `underwater`, `atmosphere`,
  `house_cutaway`, `around`/`body_inside`, `space`, `sunset`, dll.) masih
  `make_cartoon` (PIL).
- Prop `heart`, `star`, `arrow`, dll. masih ikon PIL; prop beranimasi SVG baru:
  clock, phone, hourglass, bulb, coin_stack.
- Layout sudah terisi di 29 episode (D04 authored, D05–D10 + kartu/prop,
  D11–D30 template per beat).

## Cara meng-upgrade episode lain

```bash
# isi layout per beat untuk episode yang belum punya (tanpa menimpa D04)
python3 tools/upgrade_storyboards_v43.py --episodes BOCA-D11,BOCA-D12

# tulis ulang layout satu episode (hati-hati: kartu/prop authored ikut hilang)
python3 tools/upgrade_storyboards_v43.py --episodes BOCA-D03 --force

python3 tools/check_storyboards.py     # wajib PASS 0 error
```

Tool menulis ke `production/storyboards/` **dan** `production/plans/` karena
`daily_build.py` merender dari plan. Pola per beat: hook WIDE→CLOSEUP→WIDE,
explain WIDE→CARD→WIDE, twist/payoff WIDE→SPOTLIGHT, cta WIDE→CLOSEUP.

Kartu/prop hanya ditambahkan manual untuk episode yang naskahnya sudah berisi
langkah proses (D05–D10). Untuk episode lain, tambahkan `card`/`props` saat
storyboard-nya ditulis ulang — jangan mengarang angka atau fakta baru.
