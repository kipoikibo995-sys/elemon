/* PC test of the page runtime, no SDL: plays a script of pad presses at 30 frames a second, writes every
   frame as out/NNNNN.ppm and the sound as out/am-thanh.wav, and the time each frame took.
   Usage: holua-game-test <game dir> <out dir> [every Nth frame to write, default 1] [script file]
   A script file is words: a number waits that many frames, a button name (A B X Y L1 R1 L2 R2 SELECT START UP DOWN
   LEFT RIGHT) taps it; # starts a comment to the end of the line. Without one, the built-in walk round the room. */
#include "jsrt.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* (frames, pad bits): taps are 3 frames down, then let go */
typedef struct { int frames; unsigned pad; } Step;
#define TAP(b) { 3, b }, { 12, 0 }
static const Step SCRIPT[] = {
    { 60, 0 },                                  /* the room; after 1.5 s the "ready to evolve" panel */
    TAP(PAD_B), { 40, 0 },                      /* later */
    TAP(PAD_A), { 20, 0 },                      /* Ăn: the bag opens */
    TAP(PAD_RIGHT), TAP(PAD_A), { 150, 0 },     /* feed: bite, chew, lick */
    TAP(PAD_R2), { 90, 0 },                     /* play */
    TAP(PAD_RIGHT), TAP(PAD_A), { 40, 0 },      /* Dọn: clean */
    TAP(PAD_RIGHT), TAP(PAD_RIGHT), TAP(PAD_A), { 50, 0 },   /* Ra ngoài: the map */
    TAP(PAD_RIGHT), { 50, 0 }, TAP(PAD_DOWN), { 50, 0 },
    TAP(PAD_B), { 40, 0 },                      /* home */
    TAP(PAD_SELECT), { 30, 0 }, TAP(PAD_R1), { 30, 0 }, TAP(PAD_R1), { 30, 0 }, TAP(PAD_B), { 20, 0 },  /* stats pages */
    TAP(PAD_LEFT), TAP(PAD_LEFT), TAP(PAD_LEFT), TAP(PAD_A), { 40, 0 },   /* the map again */
    { 1, 0 },
};

static const struct { const char *name; unsigned bit; } NAMES[] = {
    { "A", PAD_A }, { "B", PAD_B }, { "X", PAD_X }, { "Y", PAD_Y }, { "L1", PAD_L1 }, { "R1", PAD_R1 }, { "L2", PAD_L2 },
    { "R2", PAD_R2 }, { "SELECT", PAD_SELECT }, { "START", PAD_START }, { "UP", PAD_UP }, { "DOWN", PAD_DOWN },
    { "LEFT", PAD_LEFT }, { "RIGHT", PAD_RIGHT } };

/* the script file as steps (NULL if it cannot be read) */
static Step *read_script(const char *path, unsigned *count) {
    FILE *f = fopen(path, "r");
    char w[64];
    Step *out = 0;
    unsigned n = 0, cap = 0, i;
    int c;
    if (!f) return 0;
    while (fscanf(f, "%63s", w) == 1) {
        if (w[0] == '#') { while ((c = fgetc(f)) != EOF && c != '\n') {} continue; }
        if (n + 2 > cap) { cap = cap ? cap * 2 : 64; out = (Step *)realloc(out, cap * sizeof *out); }
        if (w[0] >= '0' && w[0] <= '9') { out[n].frames = atoi(w); out[n++].pad = 0; continue; }
        for (i = 0; i < sizeof NAMES / sizeof *NAMES; ++i)
            if (!strcmp(w, NAMES[i].name)) { out[n].frames = 3; out[n++].pad = NAMES[i].bit; out[n].frames = 12; out[n++].pad = 0; }
    }
    fclose(f);
    *count = n;
    return out;
}

static void put32(FILE *f, unsigned v) { fputc(v & 255, f); fputc(v >> 8 & 255, f); fputc(v >> 16 & 255, f); fputc(v >> 24 & 255, f); }

int main(int argc, char **argv) {
    static uint8_t rgb[JS_SCREEN_W * JS_SCREEN_H * 3];
    char path[1024];
    int n = 0, every = argc > 3 ? atoi(argv[3]) : 1, per = JS_AUDIO_RATE / 30;
    unsigned s, total = 0, i, steps = sizeof SCRIPT / sizeof *SCRIPT;
    const Step *script = SCRIPT;
    double t = 0, worst = 0, sum = 0;
    int16_t *pcm;
    FILE *wav;
    if (argc < 3) { fprintf(stderr, "usage: %s game out [every]\n", argv[0]); return 2; }
    if (every < 1) every = 1;
    if (argc > 4 && !(script = read_script(argv[4], &steps))) { fprintf(stderr, "no script %s\n", argv[4]); return 2; }
    if (!jsrt_init(argv[1])) return 1;
    snprintf(path, sizeof path, "%s/am-thanh.wav", argv[2]);
    wav = fopen(path, "wb");
    if (!wav) return 1;
    fwrite("RIFF\0\0\0\0WAVEfmt \x10\0\0\0\x01\0\x01\0", 1, 24, wav);
    put32(wav, JS_AUDIO_RATE); put32(wav, JS_AUDIO_RATE * 2);
    fwrite("\x02\0\x10\0data\0\0\0\0", 1, 12, wav);
    pcm = (int16_t *)malloc(sizeof(int16_t) * (size_t)per);
    for (s = 0; s < steps; ++s) {
        int k;
        for (k = 0; k < script[s].frames; ++k, ++n) {
            clock_t c0 = clock();
            const uint32_t *screen = jsrt_frame(t, script[s].pad);
            double ms = (clock() - c0) * 1000.0 / CLOCKS_PER_SEC;
            FILE *f;
            sum += ms; if (ms > worst && n > 5) worst = ms;
            t += 1000.0 / 30;
            jsrt_audio_commit();
            jsrt_audio(pcm, per);
            fwrite(pcm, 2, (size_t)per, wav);
            total += (unsigned)per;
            if (n % every) continue;
            for (i = 0; i < JS_SCREEN_W * JS_SCREEN_H; ++i) {
                rgb[3 * i] = screen[i] >> 16 & 255; rgb[3 * i + 1] = screen[i] >> 8 & 255; rgb[3 * i + 2] = screen[i] & 255;
            }
            snprintf(path, sizeof path, "%s/%05d.ppm", argv[2], n / every);
            f = fopen(path, "wb");
            if (!f) return 1;
            fprintf(f, "P6 %d %d 255\n", JS_SCREEN_W, JS_SCREEN_H);
            fwrite(rgb, 1, sizeof rgb, f);
            fclose(f);
        }
    }
    fseek(wav, 4, SEEK_SET); put32(wav, 36 + total * 2);
    fseek(wav, 40, SEEK_SET); put32(wav, total * 2);
    fclose(wav);
    free(pcm);
    printf("%d frames, %.2f ms a frame on average, %.2f ms at worst\n", n, sum / n, worst);
    jsrt_quit();
    jsrt_shutdown();
    return 0;
}
