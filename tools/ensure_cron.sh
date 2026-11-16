#!/data/data/com.termux/files/usr/bin/sh
# Watchdog BOCA: pastikan daemon crond hidup + crontab BOCA terpasang.
# Dipanggil dari:
#   - ~/.bashrc  (setiap sesi Termux baru)
#   - crontab    (tiap 15 menit, untuk crond yang crash)
#   - ~/.termux/boot/start_boca_cron.sh (setelah reboot, butuh Termux:Boot)
#   - manual:    sh tools/ensure_cron.sh
#
# Catatan: `pgrep -x crond` TIDAK bisa dipakai di Termux karena argv[0] crond
# adalah path penuh ("/data/.../crond"), jadi exact-match selalu gagal.
# Pakai pidof (membaca /proc) + fallback pgrep -f.

LOG_DIR="$HOME/projects/boca-character/production/logs"
LOG="$LOG_DIR/watchdog.log"
STATE="$LOG_DIR/.watchdog_ok_at"
PREFIX=/data/data/com.termux/files/usr/bin
PIDFILE="$PREFIX/var/run/crond.pid"
CRONTAB_SRC="$HOME/projects/boca-character/production/boca.cron"

mkdir -p "$LOG_DIR"

say() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

crond_pid() {
    p=$(pidof crond 2>/dev/null | awk '{print $1}')
    if [ -z "$p" ]; then
        p=$(pgrep -f '/crond$' 2>/dev/null | awk '{print $1}')
    fi
    echo "$p"
}

# 1. pastikan crond hidup
pid=$(crond_pid)
if [ -z "$pid" ]; then
    # pid file sisa? hapus hanya kalau pid di dalamnya sudah tidak ada
    if [ -f "$PIDFILE" ]; then
        oldpid=$(cat "$PIDFILE" 2>/dev/null | tr -d ' \n')
        if [ -n "$oldpid" ] && [ ! -d "/proc/$oldpid" ]; then
            rm -f "$PIDFILE" 2>/dev/null
            say "pid file basi dibuang (pid $oldpid sudah mati)"
        fi
    fi
    "$PREFIX/crond" 2>>"$LOG"
    sleep 1
    pid=$(crond_pid)
    if [ -n "$pid" ]; then
        say "crond MATI -> dijalankan ulang (pid $pid)"
    else
        say "GAGAL menjalankan crond"
    fi
else
    # tick tiap trigger (untuk audit: crontab */15 memanggil script ini)
    say "tick: crond OK (pid $pid)"
fi

# 2. sinkronkan crontab dengan sumber (production/boca.cron).
#    Job harian ikut aturan PAUSE di file sumber; job lain milik sesi/agen lain
#    tetap dipertahankan supaya tidak hilang.
TMPDIR=/data/data/com.termux/files/usr/tmp
TMP="$TMPDIR/boca-watchdog-crontab.$$"
CUR="$TMP.cur"
CUR_JOBS="$TMP.jobs"
SRC_JOBS="$TMP.src"

crontab -l > "$CUR" 2>/dev/null || : > "$CUR"
grep -v '^[[:space:]]*#' "$CRONTAB_SRC" | grep -v '^[[:space:]]*$' > "$SRC_JOBS"
grep -v 'daily_build\.py' "$CUR" | grep -v 'ensure_cron\.sh' | grep -v '^PATH=' \
    | grep -v '^[[:space:]]*#' | grep -v '^[[:space:]]*$' > "$CUR_JOBS"

# sumber dipakai UTUH (termasuk komentar + baris "# PAUSED ...") supaya status
# pause ikut terbawa; job milik agen lain tetap dipertahankan.
cat "$CUR_JOBS" "$CRONTAB_SRC" > "$TMP"

if ! cmp -s "$TMP" "$CUR"; then
    if crontab "$TMP" 2>>"$LOG"; then
        if grep -q "^# PAUSED .*daily_build\.py" "$CRONTAB_SRC"; then
            say "crontab disinkronkan (job harian PAUSE sesuai boca.cron)"
        else
            say "crontab disinkronkan (job harian AKTIF sesuai boca.cron)"
        fi
    else
        say "GAGAL pasang crontab"
    fi
fi
rm -f "$TMP" "$CUR" "$CUR_JOBS" "$SRC_JOBS"
