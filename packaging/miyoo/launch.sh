#!/bin/sh
# Elemon launcher for the Miyoo Mini Plus (OnionOS, or the stock firmware): an app in App/Elemon, run by the menu.
# The menu starts it from another folder, so it moves to its own first.
cd "$(dirname "$0")" || exit 1
SDCARD=/mnt/SDCARD

# the save lives outside the app folder (as on the Brick: Saves/elemon), so a new version copied over never touches it
export HOLUA_SAVE_DIR="$SDCARD/Saves/elemon"
mkdir -p "$HOLUA_SAVE_DIR"
chmod +x ./elemon

# the sound: the firmware's audioserver owns the speaker; libpadsp.so turns /dev/dsp into a way to it (as Onion
# runs MainUI and RetroArch)
PADSP=""
for p in "$SDCARD/miyoo/lib/libpadsp.so" /customer/lib/libpadsp.so /config/lib/libpadsp.so; do
    [ -f "$p" ] && { PADSP="$p"; break; }
done

# the fastest clock while the game runs (Onion puts the menu's back when the app ends; the stock firmware: here)
GOV=/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
OLD_GOV="$(cat $GOV 2>/dev/null)"
[ -n "$OLD_GOV" ] && echo performance > $GOV 2>/dev/null
touch /tmp/stay_awake                       # Onion: no going to sleep in the middle of a match
{
    echo "cpu: $(cat $GOV 2>/dev/null) $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null) kHz"
    echo "sound: ${PADSP:-no libpadsp.so}"
    grep -E 'MemTotal|MemFree|MemAvailable|SwapFree' /proc/meminfo
} > log.txt

if [ -n "$PADSP" ]; then LD_PRELOAD="$PADSP" ./elemon >> log.txt 2>&1
else ./elemon >> log.txt 2>&1
fi

rm -f /tmp/stay_awake
[ -n "$OLD_GOV" ] && echo "$OLD_GOV" > $GOV 2>/dev/null
