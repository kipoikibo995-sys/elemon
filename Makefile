# Hổ Lửa for the original PocketGo / MiyooCFW (ARM, shared uClibc, SDL 1.2).
# In WSL with the MiyooCFW SDK at /opt/miyoo:
#   make            build build/pocketgo/holua
#   make package    dist/holua ready to copy to the SD card (apps/holua)
#   make sim        headless PC build + screenshots in build/sim/shots (needs only host gcc)

TOOLCHAIN ?= /opt/miyoo
CROSS_COMPILE ?= $(TOOLCHAIN)/bin/arm-linux-

BUILD := build/pocketgo
DIST := dist/holua
TARGET := $(BUILD)/holua
SOURCES := src/main.c platform/sdl12.c
HEADERS := src/anim_data.h platform/platform.h
WARN := -std=c99 -Wall -Wextra -Werror -pedantic -I.

NEEDS_TARGET := $(if $(MAKECMDGOALS),$(filter-out sim clean,$(MAKECMDGOALS)),all)
ifneq ($(NEEDS_TARGET),)
CC := $(CROSS_COMPILE)gcc
STRIP := $(CROSS_COMPILE)strip
SYSROOT := $(shell $(CC) --print-sysroot)
SDL_CONFIG ?= $(SYSROOT)/usr/bin/sdl-config
CFLAGS := $(WARN) -Os -mcpu=arm926ej-s -marm -fno-pie -fno-PIC $(shell $(SDL_CONFIG) --cflags)
LDFLAGS := -no-pie $(shell $(SDL_CONFIG) --libs)
endif

.PHONY: all package sim clean

all: $(TARGET)

$(TARGET): $(SOURCES) $(HEADERS)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -o $@ $(SOURCES) $(LDFLAGS)
	$(STRIP) $@

package: $(TARGET)
	@rm -rf $(DIST)
	@mkdir -p $(DIST)/assets/frames $(DIST)/assets/frames-flash $(DIST)/saves
	cp $(TARGET) $(DIST)/holua
	cp assets/creatures/hoa/hoa-ho/adult/bmp/*.bmp $(DIST)/assets/frames/
	cp assets/creatures/hoa/hoa-ho/adult/bmp-flash/*.bmp $(DIST)/assets/frames-flash/
	cp packaging/holua.gmenu $(DIST)/holua.gmenu
	@echo "Packaged $(DIST): copy it to the SD card as apps/holua (see README)."

# Headless run: plays every move by script and saves a screenshot every 100 ms.
HOST_CC ?= gcc
SIM := build/sim
sim: $(HEADERS) src/main.c platform/sim.c
	@rm -rf $(SIM) && mkdir -p $(SIM)/shots $(SIM)/run/assets/frames $(SIM)/run/assets/frames-flash
	$(HOST_CC) $(WARN) -O2 -o $(SIM)/run/holua-sim src/main.c platform/sim.c
	cp assets/creatures/hoa/hoa-ho/adult/bmp/*.bmp $(SIM)/run/assets/frames/
	cp assets/creatures/hoa/hoa-ho/adult/bmp-flash/*.bmp $(SIM)/run/assets/frames-flash/
	cd $(SIM)/run && SIM_SCRIPT=../../../tests/sim-all-moves.txt SIM_SHOTS=../shots SIM_EVERY=100 SIM_END=40000 ./holua-sim
	@ls $(SIM)/shots | wc -l

clean:
	rm -rf build dist
