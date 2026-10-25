/* PC test of the viewer core, no SDL: plays a script of button presses, writes every frame as
   out/NNNNN.ppm and all the sound as out/am-thanh.wav (scripts/test-r36s.sh makes a video of them).
   Usage: holua-test <data dir> <out dir> */
#include "core.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* (frames, buttons held) */
typedef struct { int frames; int b[4]; } Step;
#define NONE -1
static const Step SCRIPT[] = {
    { 45, { NONE } },
    { 75, { BTN_RIGHT, NONE } },                 /* walk right */
    { 50, { BTN_LEFT, BTN_RUN, NONE } },         /* run left */
    { 20, { NONE } },
    { 2, { BTN_DOWN, NONE } }, { 8, { NONE } },  /* choose the next move */
    { 2, { BTN_ACT, NONE } }, { 60, { NONE } },
    { 2, { BTN_DOWN, NONE } }, { 8, { NONE } },
    { 2, { BTN_DOWN, NONE } }, { 8, { NONE } },
    { 2, { BTN_ACT, NONE } }, { 70, { NONE } },
    { 2, { BTN_NEXT_PET, NONE } }, { 30, { NONE } },
    { 60, { BTN_RIGHT, NONE } },
    { 2, { BTN_NEXT_ROOM, NONE } }, { 30, { NONE } },
    { 2, { BTN_NIGHT, NONE } }, { 50, { NONE } },          /* night */
    { 60, { BTN_LEFT, NONE } },
    { 2, { BTN_UP, NONE } }, { 8, { NONE } },
    { 2, { BTN_ACT, NONE } }, { 60, { NONE } },
    { 2, { BTN_NIGHT, NONE } }, { 40, { NONE } },          /* day again */
    { 2, { BTN_NIGHT, BTN_MUSIC, NONE } },                 /* quit */
};

static void put32(FILE *f, unsigned v) { fputc(v & 255, f); fputc(v >> 8 & 255, f); fputc(v >> 16 & 255, f); fputc(v >> 24 & 255, f); }

int main(int argc, char **argv) {
    static uint32_t frame[SCREEN_W * SCREEN_H];
    static uint8_t rgb[SCREEN_W * SCREEN_H * 3];
    char path[1024];
    int held[BTN_COUNT], n = 0, per = AUDIO_RATE * FRAME_MS / 1000;
    unsigned s, total = 0, i;
    int16_t *pcm;
    FILE *wav;
    if (argc < 3) { fprintf(stderr, "usage: %s data out\n", argv[0]); return 2; }
    if (!core_init(argv[1])) return 1;
    snprintf(path, sizeof path, "%s/am-thanh.wav", argv[2]);
    wav = fopen(path, "wb");
    if (!wav) return 1;
    fwrite("RIFF\0\0\0\0WAVEfmt \x10\0\0\0\x01\0\x01\0", 1, 24, wav);
    put32(wav, AUDIO_RATE); put32(wav, AUDIO_RATE * 2);
    fwrite("\x02\0\x10\0data\0\0\0\0", 1, 12, wav);
    pcm = (int16_t *)malloc(sizeof(int16_t) * (size_t)per);
    for (s = 0; s < sizeof SCRIPT / sizeof *SCRIPT && !core_wants_quit(); ++s) {
        int k;
        for (k = 0; k < SCRIPT[s].frames && !core_wants_quit(); ++k) {
            int j;
            FILE *f;
            memset(held, 0, sizeof held);
            for (j = 0; j < 4 && SCRIPT[s].b[j] != NONE; ++j) held[SCRIPT[s].b[j]] = 1;
            core_frame(held, frame);
            core_audio_commit();
            core_audio(pcm, per);
            fwrite(pcm, 2, (size_t)per, wav);
            total += (unsigned)per;
            for (i = 0; i < SCREEN_W * SCREEN_H; ++i) {
                rgb[3 * i] = frame[i] >> 16 & 255; rgb[3 * i + 1] = frame[i] >> 8 & 255; rgb[3 * i + 2] = frame[i] & 255;
            }
            snprintf(path, sizeof path, "%s/%05d.ppm", argv[2], n++);
            f = fopen(path, "wb");
            if (!f) return 1;
            fprintf(f, "P6 %d %d 255\n", SCREEN_W, SCREEN_H);
            fwrite(rgb, 1, sizeof rgb, f);
            fclose(f);
        }
    }
    fseek(wav, 4, SEEK_SET); put32(wav, 36 + total * 2);
    fseek(wav, 40, SEEK_SET); put32(wav, total * 2);
    fclose(wav);
    free(pcm);
    printf("%d frames, %.1f s of sound, quit=%d\n", n, total / (double)AUDIO_RATE, core_wants_quit());
    core_shutdown();
    return 0;
}
