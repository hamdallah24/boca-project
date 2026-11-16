#!/data/data/com.termux/files/usr/bin/python3
r"""BOCA daily build - 1 episode per hari dari Content Bible (md).

Dipakai cron termux:
    crontab: 0 6 * * * $HOME/projects/boca-character/daily_build.py --date $(date +\%F) >> $HOME/projects/boca-character/production/logs/cron.log 2>&1

Alur:
  1. Lock (anti run tumpang tindih)
  2. Petakan tanggal -> episode "Hari N" di Content Bible
  3. Ambil plan dari production/plans/ID.json (draf otomatis dari md bila belum ada)
  4. Render video (pipeline template v4)
  5. QA otomatis (durasi, LUFS, resolusi, naskah, caption)
  6. Siapkan payload upload untuk 4 platform
  7. Publish HANYA kalau: plan disetujui + facts verified + QA pass + kredensial ada

Tidak ada video yang dibuat ulang kalau episode sudah selesai (idempoten).
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from boca_pipeline import (  # noqa: E402
    Episode, NetworkUnavailable, qa_checks, qa_report, render_episode,
)
from plan_from_md import build_plan, parse_days  # noqa: E402

MD = Path("/sdcard/Download/BOCA_Rencana_Konten_30_Hari.md")
PROD = ROOT / "production"
PLANS = PROD / "plans"
OUTROOT = Path("/sdcard/Download/BOCA_DAILY")
TMPROOT = Path("/data/data/com.termux/files/usr/tmp/opencode/boca-daily")
STATE = PROD / "state.json"

# Fokus 1 platform dulu (YouTube Shorts). IG/FB/TikTok diparkir sampai kredensial siap.
# Ubah lewat env BOCA_PLATFORMS="youtube_shorts,tiktok" tanpa edit kode.
ACTIVE_PLATFORMS = [p.strip() for p in
                    os.environ.get("BOCA_PLATFORMS", "youtube_shorts").split(",") if p.strip()]
PUBLISH_PRIVACY = os.environ.get("BOCA_PRIVACY", "public")

# Parameter rendering (boca_pipeline.py). Gemini 0.4895 s/kata, tanpa atempo.
TTS_SEC_PER_WORD = 0.4895
LOCK = PROD / ".build.lock"
PAYLOADS = PROD / "payloads"
LOGS = PROD / "logs"

# Hari produksi pertama = plan "Hari 01". Tanggal bisa diganti lewat env
# BOCA_START_DATE (format YYYY-MM-DD).
START_DATE = date.fromisoformat(os.environ.get("BOCA_START_DATE", "2026-11-14"))


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def online(timeout: float = 8.0) -> bool:
    """Cek koneksi internet (DNS + HTTPS) sebelum render yang butuh TTS."""
    import socket
    import urllib.request
    for host, port in (("generativelanguage.googleapis.com", 443),
                       ("1.1.1.1", 53)):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    try:
        urllib.request.urlopen("https://generativelanguage.googleapis.com/", timeout=timeout)
        return True
    except Exception:  # noqa: BLE001
        return False


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"episodes": {}, "last_run": None}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def acquire_lock() -> bool:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            pid = int(LOCK.read_text().strip())
            os.kill(pid, 0)
            return False  # proses lain masih jalan
        except (ValueError, ProcessLookupError, PermissionError):
            LOCK.unlink(missing_ok=True)
    LOCK.write_text(str(os.getpid()), encoding="utf-8")
    return True


def release_lock() -> None:
    LOCK.unlink(missing_ok=True)


def episode_for(day_number: int) -> dict | None:
    days = parse_days(MD.read_text(encoding="utf-8"))
    for d in days:
        if d["day"] == day_number:
            return d
    return None


def ensure_plan(day: dict, state: dict) -> Path:
    PLANS.mkdir(parents=True, exist_ok=True)
    path = PLANS / f"{day['id']}.json"
    if path.exists():
        return path
    key = ""
    try:
        from boca_pipeline import gemini_key
        key = gemini_key()
    except Exception:
        pass
    plan = build_plan(day, key=key, use_llm=bool(key))
    path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"plan draf dibuat: {path.name} (status=draft, perlu review)")
    return path


def stage_payload(ep_id: str, manifest: dict, plan: dict) -> Path:
    PAYLOADS.mkdir(parents=True, exist_ok=True)
    pub = plan.get("publish", {})
    title = pub.get("title") or manifest["title"]
    if not title.startswith("BOCA"):
        title = f"BOCA — {title}"
    payload = {
        "id": ep_id,
        "title": title,
        "description": pub.get("description", ""),
        "hashtags": pub.get("hashtags", []),
        "category": pub.get("category", "Education"),
        "video": manifest["video"],
        "video_path": str(OUTROOT / ep_id / manifest["video"]),
        "thumbnail": f"boca-{ep_id.lower()}-v4-poster.png",
        "duration": manifest["duration"],
        "facts_status": manifest["facts_status"],
        "platforms": list(ACTIVE_PLATFORMS),
        "notes": "Publish hanya setelah plan disetujui + QA pass. Tiktok: app perlu audit; "
                 "IG/FB butuh media publik atau upload biner.",
    }
    out = PAYLOADS / f"{ep_id}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def run_publish(payload: Path) -> tuple[bool, dict]:
    """Jalankan publish.py, tampilkan outputnya, dan kembalikan (ok, uploads)."""
    cmd = [sys.executable, str(ROOT / "publish.py"), "--payload", str(payload), "--publish",
           "--only", ",".join(ACTIVE_PLATFORMS), "--privacy", PUBLISH_PRIVACY]
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    for line in out.splitlines():
        print(line, flush=True)
    uploads: dict = {}
    for line in out.splitlines():
        line = line.strip()
        if not line.startswith("-> "):
            continue
        try:
            d = ast.literal_eval(line[3:])
        except Exception:
            continue
        if isinstance(d, dict) and d.get("ok"):
            uploads[d.get("platform", "?")] = {k: d[k] for k in ("video_id", "url", "title") if k in d}
    return r.returncode == 0, uploads


def try_publish_built(ep_id: str, rec: dict, plan: dict, state: dict) -> bool:
    """Terbitkan episode yang sudah dirender (tanpa render ulang) bila semua gate lolos.

    Dipakai saat episode sudah `built` tapi saat itu plan-nya belum approved, lalu
    plan-nya disetujui belakangan. Return True kalau episode jadi published.
    """
    payload_path = PAYLOADS / f"{ep_id}.json"
    if not payload_path.exists():
        log(f"{ep_id}: payload belum ada, publish dilewati")
        return False
    gates = {
        "plan approved": plan.get("status") == "approved",
        "facts verified": plan.get("facts_status") == "verified",
        "qa pass": bool(rec.get("qa_pass")),
    }
    if not all(gates.values()):
        log(f"{ep_id} publish DITUNDA: {gates}")
        return False
    log(f"{ep_id} sudah dirender -> publish tanpa render ulang")
    published, uploads = run_publish(payload_path)
    if published:
        rec.update({
            "status": "published",
            "published": True,
            "published_at": datetime.now().isoformat(timespec="seconds"),
            "uploads": uploads,
        })
        state["episodes"][ep_id] = rec
        state["last_run"] = {"day": rec.get("day"), "id": ep_id,
                             "at": datetime.now().isoformat(timespec="seconds"),
                             "result": "published"}
        save_state(state)
        log(f"selesai: published {uploads}")
        return True
    log("publish gagal, episode tetap 'built'")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (default: hari ini)")
    ap.add_argument("--day", type=int, help="nomor hari plan 1..30 (menang atas --date)")
    ap.add_argument("--plan", help="episode id, mis. BOCA-D01")
    ap.add_argument("--no-render", action="store_true", help="hanya cek plan/state (dry run)")
    ap.add_argument("--publish", action="store_true", help="publikasikan kalau semua gate lolos")
    ap.add_argument("--force", action="store_true", help="render ulang walau sudah selesai")
    ap.add_argument("--catch-up", action="store_true",
                    help="terbitkan dulu episode yang sudah 'built' tapi belum terbit "
                         "(mis. plan-nya disetujui belakangan)")
    ap.add_argument("--catch-up-days", action="store_true",
                    help="bangun juga hari yang terlewat (episode yang belum pernah dibangun)")
    ap.add_argument("--approve", metavar="ID", help="tandai plan sebagai approved")
    args = ap.parse_args()

    PROD.mkdir(parents=True, exist_ok=True)
    (PROD / "cache").mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    if args.approve:
        path = PLANS / f"{args.approve}.json"
        plan = json.loads(path.read_text(encoding="utf-8"))
        plan["status"] = "approved"
        plan["needs_review"] = False
        plan["approved_at"] = datetime.now().isoformat(timespec="seconds")
        path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"plan {args.approve} disetujui")
        return 0

    if not acquire_lock():
        log("SKIP: ada build lain yang jalan (lock aktif)")
        return 0
    try:
        state = load_state()

        # --catch-up: episode yang sudah 'built' tapi belum terbit (plan disetujui belakangan)
        # dicoba terbitkan lebih dulu, tanpa render ulang.
        if args.catch_up:
            pending = sorted(
                ((r.get("day") or 0), ep_id, r)
                for ep_id, r in state["episodes"].items()
                if r.get("status") == "built" and r.get("qa_pass")
            )
            for _, pid, prec in pending:
                ppath = PLANS / f"{pid}.json"
                if not ppath.exists():
                    continue
                pplan = json.loads(ppath.read_text(encoding="utf-8"))
                if pplan.get("status") != "approved" or pplan.get("facts_status") != "verified":
                    continue
                log(f"catch-up: {pid} siap terbit (sudah dirender sebelumnya)")
                try_publish_built(pid, prec, pplan, state)
                return 0

        if args.plan:
            day_number = int(args.plan.split("D")[-1])
        elif args.day:
            day_number = args.day
        else:
            d = date.fromisoformat(args.date) if args.date else date.today()
            day_number = (d - START_DATE).days + 1

        # --catch-up-days: kalau ada hari yang terlewat (cron mati), bangun yang tertua dulu
        if args.catch_up_days:
            done_days = {r.get("day") for r in state["episodes"].values()
                         if r.get("status") in ("built", "published")}
            for d in range(1, day_number + 1):
                if d not in done_days:
                    if d != day_number:
                        log(f"catch-up: hari ke-{d} belum pernah dibangun ->prioritaskan")
                    day_number = d
                    break
        log(f"hari produksi ke-{day_number} (tanggal acuan {START_DATE})")

        day = episode_for(day_number)
        if day is None:
            log(f"TIDAK ADA episode untuk hari {day_number} (rencana 30 hari habis)")
            state["last_run"] = {"day": day_number, "at": datetime.now().isoformat(timespec="seconds"),
                                 "result": "no_episode"}
            save_state(state)
            return 0

        ep_id = day["id"]
        rec = state["episodes"].get(ep_id, {})
        if rec.get("status") == "published" and not args.force:
            log(f"SKIP: {ep_id} sudah published")
            return 0

        plan_path = ensure_plan(day, state)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        approved = plan.get("status") == "approved"
        log(f"{ep_id} '{day['title']}' | plan={plan_path.name} status={plan.get('status')} "
            f"| facts={plan.get('facts_status')}")

        # Sudah dirender tapi belum terbit (mis. gate belum lolos saat cron):
        # jangan render ulang, langsung coba publish.
        if rec.get("status") == "built" and args.publish and not args.force and rec.get("qa_pass"):
            if (PAYLOADS / f"{ep_id}.json").exists():
                try_publish_built(ep_id, rec, plan, state)
                return 0
            log(f"{ep_id}: payload hilang -> render ulang")

        # pre-check panjang narasi sebelum pakai kuota TTS.
        # Gemini 0.4895 s/kata; tidak ada atempo, video boleh lebih panjang.
        words = sum(len(l["text"].split()) for s in plan["shots"] for l in s["dialogue"])
        n_lines = sum(len(s["dialogue"]) for s in plan["shots"])
        n_shots = len(plan["shots"])
        target = float(plan.get("duration_target", 45))
        overhead = n_shots * (0.22 + 0.20) + max(n_lines - n_shots, 0) * 0.16
        speech = words * TTS_SEC_PER_WORD
        est = speech + overhead
        if est > target * 1.06:
            log(f"CATATAN: narasi ~{est:.0f}s > target {target:.0f}s ({words} kata) - "
                f"video dibiarkan lebih panjang, tanpa percepatan")
        else:
            log(f"perkiraan durasi narasi {est:.0f}s (target {target:.0f}s, {words} kata) - ok")

        if args.no_render:
            log("dry-run: tidak render")
            state["last_run"] = {"day": day_number, "id": ep_id, "at": datetime.now().isoformat(timespec="seconds"),
                                 "result": "dry_run", "plan_status": plan.get("status")}
            save_state(state)
            return 0

        ep = Episode.from_dict(plan)
        outdir = OUTROOT / ep_id
        tmp = TMPROOT / ep_id

        # pre-flight: TTS butuh internet. Kalau tidak ada koneksi, jangan crash
        # di tengah render - episodes dicoba lagi di run berikutnya (--catch-up).
        if not online():
            log("TIDAK ADA KONEKSI INTERNET - build ditunda, "
                "episode akan dicoba lagi di run berikutnya")
            return 3

        try:
            manifest = render_episode(ep, outdir, tmp)
        except NetworkUnavailable as e:
            log(f"NETWORK GAGAL: {e}")
            log("build dibatalkan tanpa merusak state; "
                "episode akan dicoba lagi di run berikutnya")
            return 3

        checks = qa_checks(ep, outdir, ep.duration_target)
        ok, report = qa_report(checks)
        (outdir / "qa.txt").write_text(report + "\n", encoding="utf-8")
        log(f"QA {'PASS' if ok else 'FAIL'}\n{report}")

        payload = stage_payload(ep_id, manifest, plan)
        log(f"payload upload siap: {payload}")

        status = "built"
        published = False
        uploads: dict = {}
        if args.publish:
            gates = {
                "plan approved": approved,
                "facts verified": plan.get("facts_status") == "verified",
                "qa pass": ok,
            }
            if all(gates.values()):
                log("gate publish lolos -> kirim ke publish.py")
                published, uploads = run_publish(payload)
                status = "published" if published else "publish_failed"
            else:
                log(f"publish DITUNDA: {gates}")

        rec = {
            "status": status,
            "title": ep.title,
            "day": day_number,
            "built_at": datetime.now().isoformat(timespec="seconds"),
            "duration": manifest["duration"],
            "qa_pass": ok,
            "qa": checks,
            "plan_status": plan.get("status"),
            "facts_status": plan.get("facts_status"),
            "output_dir": str(outdir),
            "payload": str(payload),
            "published": published,
            "published_at": (datetime.now().isoformat(timespec="seconds")
                             if published else None),
            "uploads": uploads,
        }
        state["episodes"][ep_id] = rec
        state["last_run"] = {"day": day_number, "id": ep_id,
                             "at": datetime.now().isoformat(timespec="seconds"), "result": status}
        save_state(state)
        log(f"selesai: status={status}")
        return 0 if ok else 1
    finally:
        release_lock()


if __name__ == "__main__":
    sys.exit(main())
