#ifndef HOLUA_PLATFORM_H
#define HOLUA_PLATFORM_H

#include <stdint.h>

/* Screen, pictures and buttons. platform/sdl12.c is the PocketGo (SDL 1.2) version,
   platform/sim.c a headless PC stand-in that saves screenshots. */

#define SCREEN_W 320
#define SCREEN_H 240
#define PLATFORM_IMAGE_SLOTS 256

typedef enum {
    INPUT_NONE = 0,
    INPUT_LEFT, INPUT_RIGHT, INPUT_UP, INPUT_DOWN,
    INPUT_A, INPUT_B, INPUT_X, INPUT_Y, INPUT_L, INPUT_R,
    INPUT_START, INPUT_SELECT,
    INPUT_QUIT
} Input;

typedef struct Platform Platform;

Platform *platform_init(const char *title);
void platform_shutdown(Platform *p);

/* A 24-bit BMP into a slot; with keyed set, magenta (255,0,255) is see-through. */
int platform_load_image(Platform *p, int slot, const char *path, int keyed);
int platform_image_size(Platform *p, int slot, int *w, int *h);
void platform_draw_image(Platform *p, int slot, int x, int y);
void platform_draw_image_part(Platform *p, int slot, int x, int y, int sx, int sy, int w, int h);

void platform_clear(Platform *p, uint8_t r, uint8_t g, uint8_t b);
void platform_rect(Platform *p, int x, int y, int w, int h, uint8_t r, uint8_t g, uint8_t b);
void platform_present(Platform *p);

/* One pressed button per call; 0 when there is none left this frame. */
int platform_poll(Platform *p, Input *input);
int platform_held(Platform *p, Input input);

uint32_t platform_ticks(void);
void platform_delay(uint32_t ms);

#endif
