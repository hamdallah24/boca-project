# Publish & operasi harian

## Platform

| Key | Status | Env |
|---|---|---|
| `youtube_shorts` | aktif (default) | — |
| `tiktok` | parkir | `BOCA_PLATFORMS=youtube_shorts,tiktok` |
| `instagram_reels` | parkir | idem |
| `facebook_reels` | parkir | idem |

Default privacy YouTube: `public`. Ubah dengan `PUBLISH_PRIVACY`.

## Kredensial

- `production/credentials.json` (jangan commit; sudah di `.gitignore`)
- Template: `production/credentials.example.json`
- YouTube OAuth: scope `youtube.upload`
- Cek cepat: `python3 publish.py --payload <file> --only youtube_shorts` (dry-run)

## Cron

```
0 6 * * * cd ~/projects/boca-character && python3 daily_build.py --publish --date $(date +\%F)
```

- `crond` dijalankan oleh `cronie`; boot script `~/.termux/boot/start_boca_cron.sh`
- Log: `production/logs/cron.log`
- `BOCA_START_DATE` default `2026-11-14` (Day 01)
- Satu episode per hari — jangan render 30 sekaligus

## Urutan aman publish manual

1. `python3 tools/check_storyboards.py production/storyboards/`
2. `python3 tools/sceneplan_to_plan.py BOCA-Dxx --write`
3. `python3 daily_build.py --approve BOCA-Dxx`
4. Pastikan `facts_status` sudah `verified` di plan
5. `python3 daily_build.py --plan BOCA-Dxx --publish`
6. Catat URL ke `production/state.json`

## Larangan

- Publish kalau `facts_status` masih `pending` atau `verified_basic`
- Publish tanpa `qa_pass: true`
- Menandai `published` sebelum dapat URL
- Mengubah D01/D02 yang sudah tayang
- Menimpa patch Termux di AutoClip (`frontend/package.json`,
  `frontend/package-lock.json`, `scripts/local_services.py`,
  `scripts/runtime/start.sh`, `data/`, `frontend/scripts/termux-lightningcss-shim.cjs`)
