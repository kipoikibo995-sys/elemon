#!/bin/bash
# HoLua (bản xem thử) launcher for ArkOS / PortMaster style handhelds (R36S, RG351MP ...).
# Copy this file and the "holua" folder into the ports folder of the card (the EASYROMS partition: ports/).

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

GAMEDIR="$(cd "$(dirname "$0")" && pwd)/holua"
cd "$GAMEDIR" || exit 1
chmod +x ./holua

# the pad is mapped to an SDL game controller by PortMaster (sdl_controllerconfig); buttons.txt can remap
[ -n "$sdl_controllerconfig" ] && export SDL_GAMECONTROLLERCONFIG="$sdl_controllerconfig"
export SDL_AUDIODRIVER=${SDL_AUDIODRIVER:-alsa}

./holua > log.txt 2>&1

[ -n "$(type -t pm_finish)" ] && pm_finish
printf "\033c" > /dev/tty1 2>/dev/null
