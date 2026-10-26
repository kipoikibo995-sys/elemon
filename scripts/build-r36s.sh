#!/usr/bin/env bash
# build-r36s.ps1 for Linux / WSL / macOS: the two R36S programs for ARM64 Linux handhelds (ArkOS / dArkOS), SDL2.
#   viewer  r36s/core.c + sdl2_main.c                 -> dist/holua-r36s/holua/holua        (data: scripts/r36s_app.py)
#   game    r36s/jsrt.c + js_sdl2.c + r36s/quickjs/   -> dist/elemon/elemon/elemon        (data: scripts/r36s_game.py)
#
#   scripts/build-r36s.sh              # both
#   scripts/build-r36s.sh game         # only the game (or: viewer)
#
# Needs Python with the "ziglang" package (pip install ziglang) and the SDL2 headers: SDL_INC, default
# build/sdl2/SDL2-2.30.9/include (fetched from libsdl.org when missing). SDL2 itself is NOT linked: the handheld
# already has libSDL2-2.0.so.0.
set -euo pipefail
ONLY=${1:-both}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=$ROOT/build/r36s-arm64
TARGET=aarch64-linux-gnu.2.28          # glibc 2.28 runs on everything from ArkOS (Ubuntu 19.10) on
PY=${PYTHON:-python3}
ZIG=("$PY" -m ziglang cc -target "$TARGET")
SDL_VER=2.30.9
SDL_INC=${SDL_INC:-$ROOT/build/sdl2/SDL2-$SDL_VER/include}
mkdir -p "$OUT"

if [ ! -f "$SDL_INC/SDL.h" ]; then
    echo "fetching the SDL2 $SDL_VER headers into build/sdl2"
    mkdir -p "$ROOT/build/sdl2"
    curl -sSL "https://github.com/libsdl-org/SDL/releases/download/release-$SDL_VER/SDL2-$SDL_VER.tar.gz" |
        tar xz -C "$ROOT/build/sdl2" "SDL2-$SDL_VER/include"
fi

build() {   # name, dist dir, file the data must have, extra flags..., -- sources...
    local name=$1 dist=$2 need=$3; shift 3
    local flags=() objects=() src obj warn opt
    while [ "$1" != -- ]; do flags+=("$1"); shift; done; shift
    [ -f "$dist/$need" ] || { echo "$dist/$need is missing: make the data first (see the top of this file)." >&2; exit 1; }
    for src in "$@"; do
        obj=$OUT/$name-$(basename "${src%.c}").o
        # our own files with every warning, QuickJS as it comes; the pixel loops at -O3 (SIMD), QuickJS at -O2
        case $src in r36s/quickjs/*) warn=(-w); opt=-O2 ;; *) warn=(-Wall -Wextra); opt=-O3 ;; esac
        "${ZIG[@]}" -mcpu=cortex_a35 -std=gnu99 $opt -D_GNU_SOURCE "-I$SDL_INC" "${flags[@]}" "${warn[@]}" -c "$src" -o "$obj"
        objects+=("$obj")
    done
    # a stand-in libSDL2 with just the names the program uses: the binary records libSDL2-2.0.so.0 as a
    # dependency, the real library on the handheld takes its place when it starts
    "$PY" "$ROOT/scripts/sdl-symbols.py" "${objects[@]}" | sed 's/.*/int &(void) { return 0; }/' > "$OUT/$name-sdl2stub.c"
    mkdir -p "$OUT/$name-stub"
    "${ZIG[@]}" -shared -Wl,-soname,libSDL2-2.0.so.0 "$OUT/$name-sdl2stub.c" -o "$OUT/$name-stub/libSDL2-2.0.so.0"
    "${ZIG[@]}" -s -o "$OUT/$name" "${objects[@]}" "$OUT/$name-stub/libSDL2-2.0.so.0" -lm
    cp "$OUT/$name" "$dist/$name"
    echo "Built $dist/$name ($(( $(wc -c < "$OUT/$name") / 1024 )) KB)"
}

cd "$ROOT"
if [ "$ONLY" != game ]; then
    build holua "$ROOT/dist/holua-r36s/holua" data/list.txt -- r36s/core.c r36s/sdl2_main.c
fi
if [ "$ONLY" != viewer ]; then
    build elemon "$ROOT/dist/elemon/elemon" js/load.txt '-DCONFIG_VERSION="2026-06-04"' -- \
        r36s/jsrt.c r36s/js_sdl2.c r36s/quickjs/{quickjs,dtoa,libregexp,libunicode,cutils}.c
fi
