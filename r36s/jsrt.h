/* HoLua on the R36S: the browser test page of the game (scripts/build_evo_app.py -> preview/tien-hoa/) run as it
   is by QuickJS, with the few browser pieces it uses (a 2D canvas, images, a game pad, timers) done in C here
   and in js/shim.js. No SDL in here: js_sdl2.c shows it on the handheld, js_test.c runs it on a PC.
   Data: scripts/r36s_game.py. */
#ifndef HOLUA_JSRT_H
#define HOLUA_JSRT_H
#include <stdint.h>

#define JS_SCREEN_W 640
#define JS_SCREEN_H 480
#define JS_AUDIO_RATE 22050

/* game pad bits, as the page's standard pad indices: 0 A, 1 B, 2 X, 3 Y, 4 L1, 5 R1, 6 L2, 7 R2,
   8 SELECT, 9 START, 12 up, 13 down, 14 left, 15 right */
enum { PAD_A = 1 << 0, PAD_B = 1 << 1, PAD_X = 1 << 2, PAD_Y = 1 << 3, PAD_L1 = 1 << 4, PAD_R1 = 1 << 5,
       PAD_L2 = 1 << 6, PAD_R2 = 1 << 7, PAD_SELECT = 1 << 8, PAD_START = 1 << 9,
       PAD_UP = 1 << 12, PAD_DOWN = 1 << 13, PAD_LEFT = 1 << 14, PAD_RIGHT = 1 << 15 };

/* load the scripts and pictures under dir and start the page; 0 on failure (printed) */
int jsrt_init(const char *dir);
/* one frame at time now_ms with these pad bits held; the screen (JS_SCREEN_W x JS_SCREEN_H ARGB) is returned */
const uint32_t *jsrt_frame(double now_ms, unsigned pad);
/* sounds asked for during jsrt_frame start: call with the audio thread locked */
void jsrt_audio_commit(void);
void jsrt_audio(int16_t *out, int n);
/* the page's __quit() (the game saves there), before jsrt_shutdown */
void jsrt_quit(void);
void jsrt_shutdown(void);

#endif
