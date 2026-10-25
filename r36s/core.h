/* HoLua viewer for the R36S: one room and one pet from the packed R36S set, drawn into a 640x480
   XRGB8888 frame and mixed into 22050 Hz mono 16-bit sound. No SDL in here, so the same code runs in
   the PC test (test_main.c) and on the handheld (sdl2_main.c). Data: scripts/r36s_app.py. */
#ifndef HOLUA_CORE_H
#define HOLUA_CORE_H
#include <stdint.h>

#define SCREEN_W 640
#define SCREEN_H 480
#define AUDIO_RATE 22050
#define FRAME_MS 33

enum { BTN_LEFT, BTN_RIGHT, BTN_UP, BTN_DOWN, BTN_ACT, BTN_RUN, BTN_PREV_PET, BTN_NEXT_PET,
       BTN_PREV_ROOM, BTN_NEXT_ROOM, BTN_NIGHT, BTN_MUSIC, BTN_COUNT };

/* load everything under data_dir; 0 on failure (the reason is printed) */
int core_init(const char *data_dir);
/* one step of FRAME_MS with these buttons held, drawn into frame (SCREEN_W * SCREEN_H pixels) */
void core_frame(const int held[BTN_COUNT], uint32_t *frame);
/* sounds asked for by core_frame start playing: call with the audio thread locked */
void core_audio_commit(void);
/* mix n samples (audio thread) */
void core_audio(int16_t *out, int n);
/* SELECT + START pressed together */
int core_wants_quit(void);
void core_shutdown(void);

#endif
