/* Headless PC stand-in for sdl12.c: no window, a simulated clock, scripted buttons and screenshots.

   SIM_SCRIPT  file of "<ms> <button>" lines (button names: left right up down a b x y l r start select quit)
   SIM_SHOTS   folder that receives shot-<ms>.ppm
   SIM_EVERY   ms between screenshots (default 500)
   SIM_END     ms after which the game is told to quit (default 10000) */
#include "platform.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { int w, h, keyed; uint32_t *px; } Image;

struct Platform {
    uint32_t fb[SCREEN_W * SCREEN_H];
    Image image[PLATFORM_IMAGE_SLOTS];
};

static uint32_t g_now;
static uint32_t g_next_shot, g_every = 500, g_end = 10000;
static const char *g_shots;
static struct { uint32_t at; Input in; } g_script[256];
static int g_count, g_next;

static Input input_named(const char *s) {
    static const char *const names[] = {"none", "left", "right", "up", "down", "a", "b", "x", "y",
                                        "l", "r", "start", "select", "quit"};
    int i;
    for (i = 0; i <= INPUT_QUIT; ++i) if (strcmp(s, names[i]) == 0) return (Input)i;
    return INPUT_NONE;
}

Platform *platform_init(const char *title) {
    const char *v;
    FILE *f;
    (void)title;
    if ((v = getenv("SIM_EVERY"))) g_every = (uint32_t)atoi(v);
    if ((v = getenv("SIM_END"))) g_end = (uint32_t)atoi(v);
    g_shots = getenv("SIM_SHOTS");
    if ((v = getenv("SIM_SCRIPT")) && (f = fopen(v, "r"))) {
        unsigned at;
        char name[16];
        while (g_count < 256 && fscanf(f, "%u %15s", &at, name) == 2) {
            g_script[g_count].at = at;
            g_script[g_count].in = input_named(name);
            ++g_count;
        }
        fclose(f);
    }
    return (Platform *)calloc(1, sizeof(Platform));
}

void platform_shutdown(Platform *p) {
    int i;
    if (p) for (i = 0; i < PLATFORM_IMAGE_SLOTS; ++i) free(p->image[i].px);
    free(p);
}

static unsigned rd16(const unsigned char *b) { return b[0] | b[1] << 8; }
static unsigned long rd32(const unsigned char *b) {
    return (unsigned long)b[0] | (unsigned long)b[1] << 8 | (unsigned long)b[2] << 16 | (unsigned long)b[3] << 24;
}

int platform_load_image(Platform *p, int slot, const char *path, int keyed) {
    unsigned char head[54];
    FILE *f;
    long w, h, y, x, stride;
    unsigned char *row;
    Image *im;
    if (!p || slot < 0 || slot >= PLATFORM_IMAGE_SLOTS || !(f = fopen(path, "rb"))) return 0;
    if (fread(head, 1, 54, f) != 54 || head[0] != 'B' || head[1] != 'M' || rd16(head + 28) != 24) {
        fclose(f);
        return 0;
    }
    w = (long)rd32(head + 18);
    h = (long)rd32(head + 22);
    stride = (w * 3 + 3) & ~3L;
    im = &p->image[slot];
    free(im->px);
    im->w = (int)w; im->h = (int)(h < 0 ? -h : h); im->keyed = keyed;
    im->px = (uint32_t *)malloc(sizeof(uint32_t) * (size_t)(w * im->h));
    row = (unsigned char *)malloc((size_t)stride);
    fseek(f, (long)rd32(head + 10), SEEK_SET);
    for (y = 0; y < im->h; ++y) {
        long dy = h > 0 ? im->h - 1 - y : y;
        if (fread(row, 1, (size_t)stride, f) != (size_t)stride) break;
        for (x = 0; x < w; ++x)
            im->px[dy * w + x] = (uint32_t)row[x * 3 + 2] << 16 | (uint32_t)row[x * 3 + 1] << 8 | row[x * 3];
    }
    free(row);
    fclose(f);
    return 1;
}

int platform_image_size(Platform *p, int slot, int *w, int *h) {
    if (!p || slot < 0 || slot >= PLATFORM_IMAGE_SLOTS || !p->image[slot].px) return 0;
    *w = p->image[slot].w;
    *h = p->image[slot].h;
    return 1;
}

void platform_draw_image_part(Platform *p, int slot, int x, int y, int sx, int sy, int w, int h) {
    Image *im;
    int i, j;
    if (!p || slot < 0 || slot >= PLATFORM_IMAGE_SLOTS || !(im = &p->image[slot])->px) return;
    for (j = 0; j < h; ++j) for (i = 0; i < w; ++i) {
        int u = sx + i, v = sy + j, X = x + i, Y = y + j;
        uint32_t c;
        if (u < 0 || v < 0 || u >= im->w || v >= im->h || X < 0 || Y < 0 || X >= SCREEN_W || Y >= SCREEN_H) continue;
        c = im->px[v * im->w + u];
        if (im->keyed && c == 0xFF00FFu) continue;
        p->fb[Y * SCREEN_W + X] = c;
    }
}

void platform_draw_image(Platform *p, int slot, int x, int y) {
    if (!p || slot < 0 || slot >= PLATFORM_IMAGE_SLOTS || !p->image[slot].px) return;
    platform_draw_image_part(p, slot, x, y, 0, 0, p->image[slot].w, p->image[slot].h);
}

void platform_rect(Platform *p, int x, int y, int w, int h, uint8_t r, uint8_t g, uint8_t b) {
    int i, j;
    for (j = y < 0 ? 0 : y; j < y + h && j < SCREEN_H; ++j)
        for (i = x < 0 ? 0 : x; i < x + w && i < SCREEN_W; ++i)
            p->fb[j * SCREEN_W + i] = (uint32_t)r << 16 | (uint32_t)g << 8 | b;
}

void platform_clear(Platform *p, uint8_t r, uint8_t g, uint8_t b) {
    platform_rect(p, 0, 0, SCREEN_W, SCREEN_H, r, g, b);
}

void platform_present(Platform *p) {
    char path[512];
    FILE *f;
    int i;
    if (!g_shots || g_now < g_next_shot) return;
    g_next_shot = g_now + g_every;
    snprintf(path, sizeof(path), "%s/shot-%06u.ppm", g_shots, (unsigned)g_now);
    if (!(f = fopen(path, "wb"))) return;
    fprintf(f, "P6\n%d %d\n255\n", SCREEN_W, SCREEN_H);
    for (i = 0; i < SCREEN_W * SCREEN_H; ++i) {
        fputc((int)(p->fb[i] >> 16 & 255), f);
        fputc((int)(p->fb[i] >> 8 & 255), f);
        fputc((int)(p->fb[i] & 255), f);
    }
    fclose(f);
}

int platform_poll(Platform *p, Input *input) {
    (void)p;
    static uint32_t quit_sent_at = (uint32_t)-1;
    if (g_now >= g_end && quit_sent_at != g_now) { quit_sent_at = g_now; *input = INPUT_QUIT; return 1; }
    if (g_next < g_count && g_script[g_next].at <= g_now) { *input = g_script[g_next++].in; return 1; }
    return 0;
}

int platform_held(Platform *p, Input input) { (void)p; (void)input; return 0; }
uint32_t platform_ticks(void) { return g_now; }
void platform_delay(uint32_t ms) { g_now += ms; }
