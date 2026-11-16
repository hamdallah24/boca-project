#!/data/data/com.termux/files/usr/bin/sh
# Toggle job harian BOCA (06:00 + slot cadangan).
#
#   sh tools/cron_toggle.sh on    -> aktifkan build harian
#   sh tools/cron_toggle.sh off   -> pause build harian
#   sh tools/cron_toggle.sh       -> status
#
# Job watchdog (*/15 ensure_cron.sh) TIDAK ikut dipause, supaya crond tetap
# hidup dan tinggal aktifkan lagi kapan saja.

SRC="$HOME/projects/boca-character/production/boca.cron"
MARK="# PAUSED "

[ -f "$SRC" ] || { echo "WARN: $SRC tidak ada"; exit 1; }

mode="${1:-status}"

paused() { grep -q "^$MARK.*daily_build\.py" "$SRC"; }
active() { grep -q '^[^#].*daily_build\.py' "$SRC"; }

case "$mode" in
  on)
    if paused; then
        sed -i '/^# PAUSED .*daily_build\.py/ s|^# PAUSED ||' "$SRC"
    fi
    crontab "$SRC" && echo "cron harian: AKTIF"
    ;;
  off)
    if active; then
        sed -i '/^[^#].*daily_build\.py/ s|^|# PAUSED |' "$SRC"
    fi
    crontab "$SRC" && echo "cron harian: PAUSE"
    ;;
  *)
    if paused; then echo "cron harian: PAUSE"; else echo "cron harian: AKTIF"; fi
    ;;
esac

echo "--- crontab sekarang ---"
crontab -l | grep -v '^[[:space:]]*#' | grep -v '^[[:space:]]*$'
