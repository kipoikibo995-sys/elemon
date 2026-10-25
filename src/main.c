/* Hổ Lửa - stage 1: the animation viewer.
   Plays every move of the fire tiger exactly as the game will (assets/frames/anims.json):
   Left/Right picks a move, A plays it again, B quits. */
#define _POSIX_C_SOURCE 200112L

#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "platform/platform.h"
#include "src/anim_data.h"

#define FLASH_SLOT 64
#define FLOOR_Y 186
#define TICK_MS 33
/* rows above this line move when the tiger breathes */
#define WAIST_Y (FRAME_AY - 46)

/* ---- text: 5x7 capitals, digits and a few signs ---- */

static const unsigned char k_font[44][7] = {
    {14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{14,17,16,16,16,17,14},
    {30,17,17,17,17,17,30},{31,16,16,30,16,16,31},{31,16,16,30,16,16,16},
    {14,17,16,23,17,17,15},{17,17,17,31,17,17,17},{31,4,4,4,4,4,31},
    {7,2,2,2,18,18,12},{17,18,20,24,20,18,17},{16,16,16,16,16,16,31},
    {17,27,21,21,17,17,17},{17,25,21,19,17,17,17},{14,17,17,17,17,17,14},
    {30,17,17,30,16,16,16},{14,17,17,17,21,18,13},{30,17,17,30,20,18,17},
    {15,16,16,14,1,1,30},{31,4,4,4,4,4,4},{17,17,17,17,17,17,14},
    {17,17,17,17,17,10,4},{17,17,17,21,21,21,10},{17,17,10,4,10,17,17},
    {17,17,10,4,4,4,4},{31,1,2,4,8,16,31},
    {14,17,19,21,25,17,14},{4,12,4,4,4,4,14},{14,17,1,2,4,8,31},
    {30,1,1,14,1,1,30},{2,6,10,18,31,2,2},{31,16,16,30,1,1,30},
    {14,16,16,30,17,17,14},{31,1,2,4,8,8,8},{14,17,17,14,17,17,14},
    {14,17,17,15,1,1,14},{0,0,0,0,0,0,0},{0,4,0,0,4,0,0},
    {1,2,4,8,16,0,0},{0,0,0,31,0,0,0},{2,4,8,16,8,4,2},{8,4,2,1,2,4,8},
    {0,0,0,0,0,0,4},{4,4,4,4,4,0,4}
};

static int glyph(char c) {
    if (c >= 'a' && c <= 'z') c = (char)(c - 'a' + 'A');
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= '0' && c <= '9') return 26 + c - '0';
    switch (c) {
    case ':': return 37; case '/': return 38; case '-': return 39;
    case '<': return 40; case '>': return 41; case '.': return 42; case '!': return 43;
    default: return 36;
    }
}

static int text_width(const char *s, int scale) { return (int)strlen(s) * 6 * scale - scale; }

static void text(Platform *p, int x, int y, const char *s, int scale, uint8_t r, uint8_t g, uint8_t b) {
    int row, col;
    for (; *s; ++s, x += 6 * scale) {
        const unsigned char *gl = k_font[glyph(*s)];
        for (row = 0; row < 7; ++row) for (col = 0; col < 5; ++col)
            if (gl[row] & (1U << (4 - col))) platform_rect(p, x + col * scale, y + row * scale, scale, scale, r, g, b);
    }
}

static void text_shadow(Platform *p, int x, int y, const char *s, int scale, uint8_t r, uint8_t g, uint8_t b) {
    text(p, x + scale, y + scale, s, scale, 20, 10, 8);
    text(p, x, y, s, scale, r, g, b);
}

/* ---- animation player ---- */

typedef struct {
    int anim, key;
    uint32_t elapsed;            /* ms into the current key */
    int x, y, br;                /* where the previous key ended, 1/256 px */
    int done;
} Player;

static uint32_t g_seed = 12345U;
static int rnd(int lo, int hi) {
    g_seed = g_seed * 1103515245U + 12345U;
    return lo + (int)((g_seed >> 16) % (uint32_t)(hi - lo + 1));
}

static const AnimKey *player_key(const Player *pl) {
    return &k_anim_keys[k_anims[pl->anim].first + pl->key];
}

static void player_goal(const Player *pl, const AnimKey *k, int *gx, int *gy, int *gbr) {
    *gx = k->keep_x ? pl->x : k->x * 256;
    *gy = k->keep_y ? pl->y : k->y * 256;
    *gbr = k->br * 256;
}

static void player_start(Player *pl, int anim) {
    memset(pl, 0, sizeof(*pl));
    pl->anim = anim;
}

static void player_update(Player *pl, uint32_t dt) {
    if (pl->done) return;
    pl->elapsed += dt;
    while (!pl->done && pl->elapsed >= player_key(pl)->ms) {
        const AnimKey *k = player_key(pl);
        pl->elapsed -= k->ms;
        player_goal(pl, k, &pl->x, &pl->y, &pl->br);
        if (++pl->key >= k_anims[pl->anim].count) {
            if (k_anims[pl->anim].loop) pl->key = 0;
            else { pl->key = k_anims[pl->anim].count - 1; pl->done = 1; pl->elapsed = k->ms; }
        }
    }
}

/* smoothstep in 1/256 steps */
static int ease(int t) { return t * t * (768 - 2 * t) / 65536; }

static void player_sample(const Player *pl, int *frame, int *x, int *y, int *br, int *shake, int *flash) {
    const AnimKey *k = player_key(pl);
    int gx, gy, gbr, t, e;
    player_goal(pl, k, &gx, &gy, &gbr);
    t = pl->done ? 256 : (int)(pl->elapsed * 256U / k->ms);
    e = ease(t > 256 ? 256 : t);
    *frame = k->frame;
    *x = (pl->done ? gx : pl->x + (gx - pl->x) * e / 256) / 256;
    *y = (pl->done ? gy : pl->y + (gy - pl->y) * e / 256) / 256;
    *br = ((pl->done ? gbr : pl->br + (gbr - pl->br) * e / 256) + (gbr >= 0 ? 128 : -128)) / 256;
    *shake = pl->done ? 0 : k->shake;
    *flash = !pl->done && k->flash && pl->elapsed < TICK_MS + 4;
}

/* ---- drawing ---- */

static void draw_room(Platform *p) {
    int i;
    /* placeholder room until the real background art arrives */
    for (i = 0; i < 14; ++i)
        platform_rect(p, 0, 18 + i * 12, SCREEN_W, 12, (uint8_t)(46 + i * 3), (uint8_t)(30 + i * 2), (uint8_t)(34 + i));
    platform_rect(p, 0, FLOOR_Y, SCREEN_W, 34, 104, 64, 42);
    for (i = 0; i < 4; ++i) platform_rect(p, 0, FLOOR_Y + 2 + i * 8, SCREEN_W, 1, 84, 50, 34);
    platform_rect(p, 0, FLOOR_Y, SCREEN_W, 2, 140, 92, 58);
}

static void draw_shadow(Platform *p, int cx, int lift) {
    int half = 40 - lift * 6 / 10, row;
    static const int k_row_w[5] = {60, 90, 100, 90, 60};
    for (row = 0; row < 5; ++row) {
        int w = half * k_row_w[row] / 100;
        platform_rect(p, cx - w, FLOOR_Y - 3 + row, w * 2, 1, 70, 42, 30);
    }
}

/* The frame with its upper body lifted by br px (lowered when negative). */
static void draw_tiger(Platform *p, int frame, int x, int y, int br, int flash) {
    int slot = frame + (flash ? FLASH_SLOT : 0);
    int i;
    platform_draw_image_part(p, slot, x, y + WAIST_Y, 0, WAIST_Y, FRAME_W, FRAME_H - WAIST_Y);
    if (br > 0)
        for (i = 0; i <= br; ++i)
            platform_draw_image_part(p, slot, x, y + WAIST_Y - 1 - i, 0, WAIST_Y - 1, FRAME_W, 1);
    platform_draw_image_part(p, slot, x, y - br, 0, 0, FRAME_W, WAIST_Y);
}

static void draw(Platform *p, const Player *pl) {
    int frame, x, y, br, shake, flash, jx = 0, jy = 0;
    char line[64];
    const Anim *a = &k_anims[pl->anim];
    player_sample(pl, &frame, &x, &y, &br, &shake, &flash);
    if (shake) { jx = rnd(-shake, shake); jy = rnd(-shake, shake) / 2; }
    draw_room(p);
    draw_shadow(p, SCREEN_W / 2 + x, y < 0 ? -y : 0);
    draw_tiger(p, frame, SCREEN_W / 2 - FRAME_AX + k_frame_align[frame] + x + jx, FLOOR_Y - FRAME_AY + y + jy, br, flash);

    platform_rect(p, 0, 0, SCREEN_W, 18, 30, 16, 14);
    platform_rect(p, 0, 18, SCREEN_W, 1, 200, 120, 40);
    text_shadow(p, 6, 6, "HO LUA - XEM DONG TAC", 1, 255, 200, 90);
    snprintf(line, sizeof(line), "%d/%d", pl->anim + 1, ANIM_COUNT);
    text(p, SCREEN_W - 6 - text_width(line, 1), 6, line, 1, 200, 160, 120);

    platform_rect(p, 0, 220, SCREEN_W, 20, 30, 16, 14);
    snprintf(line, sizeof(line), "< %s >", a->label);
    text_shadow(p, (SCREEN_W - text_width(line, 2)) / 2, 196, line, 2, 255, 236, 180);
    text(p, 8, 227, "TRAI/PHAI: CHON   A: CHOI LAI   B: THOAT", 1, 220, 190, 150);
}

/* gmenu2x may start us from anywhere: work from the folder the program is in. */
static void enter_program_folder(const char *argv0) {
    char dir[512];
    char *slash;
    if (!argv0 || strlen(argv0) >= sizeof(dir)) return;
    strcpy(dir, argv0);
    slash = strrchr(dir, '/');
    if (!slash) return;
    *slash = 0;
    if (dir[0] && chdir(dir) != 0) fprintf(stderr, "chdir %s failed\n", dir);
}

int main(int argc, char **argv) {
    Platform *p;
    Player pl;
    char path[128];
    int i, running = 1, idle = 0;
    uint32_t last;
    (void)argc;
    enter_program_folder(argv[0]);
    p = platform_init("Ho Lua");
    if (!p) { fprintf(stderr, "platform_init failed\n"); return 1; }
    for (i = 0; i < FRAME_COUNT; ++i) {
        snprintf(path, sizeof(path), "assets/frames/%s.bmp", k_frame_file[i]);
        if (!platform_load_image(p, i, path, 1)) fprintf(stderr, "missing %s\n", path);
        snprintf(path, sizeof(path), "assets/frames-flash/%s.bmp", k_frame_file[i]);
        if (!platform_load_image(p, FLASH_SLOT + i, path, 1)) fprintf(stderr, "missing %s\n", path);
    }
    for (i = 0; i < ANIM_COUNT; ++i) if (strcmp(k_anims[i].id, "idle") == 0) idle = i;
    player_start(&pl, idle);
    last = platform_ticks();
    while (running) {
        Input in;
        uint32_t now, dt;
        while (platform_poll(p, &in)) {
            switch (in) {
            case INPUT_LEFT: case INPUT_UP: player_start(&pl, (pl.anim + ANIM_COUNT - 1) % ANIM_COUNT); break;
            case INPUT_RIGHT: case INPUT_DOWN: player_start(&pl, (pl.anim + 1) % ANIM_COUNT); break;
            case INPUT_A: player_start(&pl, pl.anim); break;
            case INPUT_B: case INPUT_QUIT: running = 0; break;
            default: break;
            }
        }
        now = platform_ticks();
        dt = now - last;
        last = now;
        player_update(&pl, dt > 100 ? 100 : dt);
        draw(p, &pl);
        platform_present(p);
        now = platform_ticks() - now;
        if (now < TICK_MS) platform_delay(TICK_MS - now);
    }
    platform_shutdown(p);
    return 0;
}
