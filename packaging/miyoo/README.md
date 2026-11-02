# Elemon on the Miyoo Mini Plus

The machine: SigmaStar SSD202D, two Cortex-A7 at about 1.2 GHz (32-bit ARMv7, hard float, NEON-VFPv4), 128 MB
memory, a 640x480 screen, 2.4 GHz wifi. OnionOS or the stock firmware; both have glibc 2.28.

## Build and pack

    powershell -File scripts\build-miyoo.ps1          -> build\miyoo-armv7\elemon
    python scripts\pack_miyoo.py v1.4.1               -> build\release\Elemon_v1.4.1_MiyooMiniPlus.zip (App/Elemon/)

The game's data is dist\elemon\elemon, the same as the Brick's and the R36S's (game/build_game.py,
scripts/r36s_game.py); only the program differs. `#version` in files.txt is the same as theirs, so wifi rooms find
each other. There is no ota.sh: an update fetches a version's files from its tag, and those are the ARM64 build's.

## The program

- `r36s/js_miyoo.c` in place of js_sdl2.c, no SDL:
  - screen: `/dev/fb0` mmapped, two pages (yres_virtual 960, FBIOPAN_DISPLAY), the picture written back to front
    because the panel is mounted upside down (`HOLUA_TURN=0` in launch.sh if a firmware turns it already);
  - buttons: `/dev/input/event0` key codes (Onion's keymap_hw.h); `buttons-miyoo.txt` ("A=57" lines) can change them;
    MENU held one second quits, as SELECT + START held half a second does;
  - sound: OSS `/dev/dsp`, 44100 Hz stereo (the mixer's 22050 Hz mono, each sample four times), through the
    firmware's `libpadsp.so` (LD_PRELOAD in launch.sh, as Onion runs MainUI), which hands it to the audioserver;
  - SIGTERM (Onion's power button) saves and quits.
- `r36s/jsrt.c` built with `-DJSRT_LAZY`: a picture's pixels are read from the card the first time it is drawn, and
  given back between frames when the pictures read in take more than 40 MB (`HOLUA_PIC_MB`), the one drawn longest ago
  first. Without it the game holds 135 MB of pictures as soon as it starts (187 MB after a while). Off in the ARM64
  build, whose binary stays byte for byte the same.

## Tests on a PC (WSL)

`scripts\build-miyoo.ps1 -Test` also builds `r36s/js_test.c` for ARMv7 (`holua-game-test-armv7`, JSRT_LAZY) and
ARM64 (`holua-game-test-arm64`, as the Brick). They run under qemu-user with a real glibc for each:
`apt-get download qemu-user libc6-armhf-cross libc6-arm64-cross` and `dpkg -x` them into a folder (no root needed),
then `qemu-arm -L <folder>/usr/arm-linux-gnueabihf build/miyoo-armv7/holua-game-test-armv7 <game> <out> ...`.

## Not yet checked on the machine

- the screen's turn and pixel format (the log's first line: "screen 640x480, 32 bits (red at 16), 2 pages ...");
- the sound through libpadsp.so at 44100 Hz (log: "sound: ...");
- the free memory (launch.sh writes MemAvailable into log.txt; the game logs its own every 30 s);
- the speed (the log: "t=..s  .. fps  game .. ms  screen .. ms" every 5 s);
- wifi broadcast between Miyoo and Brick/R36S (UDP 47777).
