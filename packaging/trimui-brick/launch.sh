#!/bin/sh
# Elemon launcher for TrimUI stock firmware (Brick / Smart Pro): an app in Apps/Elemon, run by the menu.
case "$0" in
    */*) cd "${0%/*}" || exit 1 ;;
esac
GAMEDIR="$(pwd)"
SDCARD="${SDCARD_PATH:-/mnt/SDCARD}"

# the firmware's own SDL2 (it knows the built-in pad) comes first
export LD_LIBRARY_PATH="/usr/trimui/lib:/usr/lib64:/usr/lib:/lib:$LD_LIBRARY_PATH"
export SDL_AUDIODRIVER=${SDL_AUDIODRIVER:-alsa}
# the save lives outside the app folder, so installing a new version never touches it
export HOLUA_SAVE_DIR="$SDCARD/Saves/elemon"
mkdir -p "$HOLUA_SAVE_DIR"
chmod +x ./elemon

GOV=/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
OLD_GOV="$(cat $GOV 2>/dev/null)"
[ -n "$OLD_GOV" ] && echo performance > $GOV 2>/dev/null
echo "cpu: $(cat $GOV 2>/dev/null) $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null) kHz" > log.txt

./elemon >> log.txt 2>&1

[ -n "$OLD_GOV" ] && echo "$OLD_GOV" > $GOV 2>/dev/null
