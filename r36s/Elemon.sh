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

./elemon > log.txt 2>&1

[ -n "$(type -t pm_finish)" ] && pm_finish
printf "\033c" > /dev/tty1 2>/dev/null
