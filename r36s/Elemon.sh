#!/bin/bash
# Elemon launcher for ArkOS / PortMaster style handhelds (R36S, RG351MP ...): the game run by r36s/js_sdl2.c.
# Copy this file and the "elemon" folder into the ports folder of the card (EASYROMS: ports/).

if [ -d "/opt/system/Tools/PortMaster/" ]; then
  controlfolder="/opt/system/Tools/PortMaster"
elif [ -d "/opt/tools/PortMaster/" ]; then
  controlfolder="/opt/tools/PortMaster"
elif [ -d "$XDG_DATA_HOME/PortMaster/" ]; then
  controlfolder="$XDG_DATA_HOME/PortMaster"
else
  controlfolder="/roms/ports/PortMaster"
fi

[ -f "$controlfolder/control.txt" ] && source "$controlfolder/control.txt"
[ -n "$(type -t get_controls)" ] && get_controls

PORTS="$(cd "$(dirname "$0")" && pwd)"
GAMEDIR="$PORTS/elemon"
cd "$GAMEDIR" || exit 1
chmod +x ./elemon

[ -n "$sdl_controllerconfig" ] && export SDL_GAMECONTROLLERCONFIG="$sdl_controllerconfig"
export SDL_AUDIODRIVER=${SDL_AUDIODRIVER:-alsa}
# the save lives next to the game folder, so installing a new version never touches it
# (a save from when the game was called HoLua moves over once)
[ -d "$PORTS/holua-save" ] && [ ! -d "$PORTS/elemon-save" ] && mv "$PORTS/holua-save" "$PORTS/elemon-save"
export HOLUA_SAVE_DIR="$PORTS/elemon-save"
mkdir -p "$HOLUA_SAVE_DIR"

# the CPU at full speed while the game runs (the handheld's own perfmax when it has one), back as it was after;
# without a password-free sudo this does nothing and the game runs as before
GOV=/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
OLD_GOV="$(cat $GOV 2>/dev/null)"
if command -v perfmax >/dev/null 2>&1; then sudo -n perfmax >/dev/null 2>&1
elif [ -n "$OLD_GOV" ]; then echo performance | sudo -n tee $GOV >/dev/null 2>&1; fi
echo "cpu: $(cat $GOV 2>/dev/null) $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null) kHz" > log.txt

./elemon >> log.txt 2>&1

if command -v perfnorm >/dev/null 2>&1; then sudo -n perfnorm >/dev/null 2>&1
elif [ -n "$OLD_GOV" ]; then echo "$OLD_GOV" | sudo -n tee $GOV >/dev/null 2>&1; fi

[ -n "$(type -t pm_finish)" ] && pm_finish
printf "\033c" > /dev/tty1 2>/dev/null
