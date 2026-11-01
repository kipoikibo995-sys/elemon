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

# an update downloaded in the game (Cài đặt -> Cập nhật, ota.sh) goes in before the game starts; "Cài ngay" quits the
# game with one ready, so it is put in and the game opened again (twice at most); a new version that never says it
# started is undone (ota.sh after)
chmod +x ./ota.sh 2>/dev/null
for run in 1 2 3; do
    sh ./ota.sh apply >> log.txt 2>&1
    ./elemon >> log.txt 2>&1
    sh ./ota.sh after >> log.txt 2>&1
    [ -f .ota/ready ] || [ -f .ota/rolled ] || break
    rm -f .ota/rolled
done

[ -n "$OLD_GOV" ] && echo "$OLD_GOV" > $GOV 2>/dev/null
