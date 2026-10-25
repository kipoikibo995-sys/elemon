/* HoLua viewer core: see core.h. Everything is drawn by the CPU into one 640x480 frame (alpha
   blending, white flash and night tint as on the PocketGo set), so the handheld only shows it. */
#include "core.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ROOMS 32
#define MAX_PETS 256
#define MAX_ITEMS 32
#define MAX_FRAMES 64
#define MAX_MOVES 24
#define MAX_SOUNDS 48
#define CHANNELS 8
#define MAX_GLYPHS 512

typedef struct { int w, h, ncol; uint8_t *idx; uint8_t *rgb; uint32_t pal[256]; uint32_t *px; } Image;
typedef struct { char name[24]; int ax, ay, w, h, ox, oy, dx; } Frame;
typedef struct { int f; float x, y; int shake, flash; } Sample;
typedef struct { char name[16]; int loop, n; Sample *s; } Move;
typedef struct { char name[48]; int ax, ay, w, h, sx, sy, floor; } Item;
typedef struct { char name[32], label[96]; int feet, lo, hi; } RoomInfo;
typedef struct { char cid[32], stage[12], label[96]; } PetInfo;
typedef struct { char name[24]; int16_t *data; int len; } Sound;
typedef struct { const int16_t *d; int len, pos, vol, loop; } Channel;

static char data_dir[512];
static RoomInfo rooms[MAX_ROOMS];
static PetInfo pets[MAX_PETS];
static int n_rooms, n_pets, room_i, pet_i;

static struct { Image bg, deco; Item it[MAX_ITEMS]; int n, order[MAX_ITEMS]; } room;
static struct { Image atlas; int cw, ch, ax, ay, nfr, nmv; Frame fr[MAX_FRAMES]; Move mv[MAX_MOVES]; } pet;

static Image font;
static int glyph_of[0x3000], n_glyphs, line_h, ascent;
static struct { int x, y, w, h, l, adv, top; } glyph[MAX_GLYPHS];
#define MAX_STRINGS 48
static char strings[MAX_STRINGS][160], string_key[MAX_STRINGS][24];
static int n_strings;

static Sound sounds[MAX_SOUNDS];
static int n_sounds;
static Channel chan[CHANNELS];
static struct { int sound, vol; } pending[16];
static int n_pending, music_change = -1;   /* -1 nothing, -2 stop, else the sound to loop on channel 0 */

static int night, music_on = 1, quit, combo, sel, cur, tick, walk_prev = -1, step_parity, left_facing;
static int prev[BTN_COUNT];
static float feet_x;
static uint32_t seed = 12345;

/* ---------------------------------------------------------------- files */

static char *path_of(const char *rel) {
    static char p[1024];
    snprintf(p, sizeof p, "%s/%s", data_dir, rel);
    return p;
}

static uint8_t *read_file(const char *path, long *len) {
    FILE *f = fopen(path, "rb");
    uint8_t *b;
    long n;
    if (!f) return 0;
    fseek(f, 0, SEEK_END);
    n = ftell(f);
    fseek(f, 0, SEEK_SET);
    b = (uint8_t *)malloc((size_t)n + 1);
    if (b && fread(b, 1, (size_t)n, f) != (size_t)n) { free(b); b = 0; }
    fclose(f);
    if (b) { b[n] = 0; if (len) *len = n; }
    return b;
}

/* ---------------------------------------------------------------- pictures (.hli, see r36s_app.py) */

static uint32_t argb(uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
    return ((uint32_t)a << 24) | ((uint32_t)r << 16) | ((uint32_t)g << 8) | b;
}

static float clampf(float v) { return v < 0 ? 0 : v > 255 ? 255 : v; }

/* pocketgo_pak.NIGHT: darker and bluer, bright strongly coloured light (fire, lamps) keeps its colour */
static uint32_t night_colour(uint32_t c) {
    float r = (float)((c >> 16) & 255), g = (float)((c >> 8) & 255), b = (float)(c & 255);
    float dr = r * 0.464f - 6.4f, dg = g * 0.549f - 5.6f, db = b * 0.675f + 16.8f;
    float hi = r > g ? (r > b ? r : b) : (g > b ? g : b), lo = r < g ? (r < b ? r : b) : (g < b ? g : b);
    float k1 = (hi - 215.0f) / 40.0f, k2 = (hi - lo - 90.0f) / 60.0f, keep;
    k1 = k1 < 0 ? 0 : k1 > 1 ? 1 : k1;
    k2 = k2 < 0 ? 0 : k2 > 1 ? 1 : k2;
    keep = k1 * k2;
    return (c & 0xFF000000u) | ((uint32_t)clampf(dr + (r - dr) * keep) << 16) |
           ((uint32_t)clampf(dg + (g - dg) * keep) << 8) | (uint32_t)clampf(db + (b - db) * keep);
}

/* (re)build the ARGB pixels, by day or by night */
static void image_colour(Image *im, int at_night) {
    int i, n = im->w * im->h;
    if (im->idx) {
        uint32_t pal[256];
        for (i = 0; i < 256; ++i) pal[i] = at_night ? night_colour(im->pal[i]) : im->pal[i];
        for (i = 0; i < n; ++i) im->px[i] = pal[im->idx[i]];
    } else if (im->rgb) {
        for (i = 0; i < n; ++i) {
            uint32_t c = argb(im->rgb[3 * i], im->rgb[3 * i + 1], im->rgb[3 * i + 2], 255);
            im->px[i] = at_night ? night_colour(c) : c;
        }
    }
}

static void image_free(Image *im) {
    free(im->idx); free(im->rgb); free(im->px);
    memset(im, 0, sizeof *im);
}

static int image_load(Image *im, const char *rel) {
    long len, p = 10;
    uint8_t *b = read_file(path_of(rel), &len);
    int i, n;
    memset(im, 0, sizeof *im);
    if (!b || len < 10 || memcmp(b, "HLI1", 4)) { printf("cannot read %s\n", rel); free(b); return 0; }
    im->w = b[4] | b[5] << 8;
    im->h = b[6] | b[7] << 8;
    im->ncol = b[8] | b[9] << 8;
    n = im->w * im->h;
    im->px = (uint32_t *)malloc((size_t)n * 4);
    if (im->ncol >= 1 && im->ncol <= 256) {
        int k = 0;
        for (i = 0; i < im->ncol; ++i, p += 4) im->pal[i] = argb(b[p], b[p + 1], b[p + 2], b[p + 3]);
        im->idx = (uint8_t *)malloc((size_t)n);
        while (k < n && p < len) {
            int c = b[p++];
            if (c < 0x80) { int m = c + 1; if (k + m > n) m = n - k; memcpy(im->idx + k, b + p, (size_t)m); p += c + 1; k += m; }
            else { int m = c - 0x7E; if (k + m > n) m = n - k; memset(im->idx + k, b[p++], (size_t)m); k += m; }
        }
    } else if (im->ncol == 0xFFFF) {
        im->rgb = (uint8_t *)malloc((size_t)n * 3);
        memcpy(im->rgb, b + p, (size_t)n * 3);
    } else {
        for (i = 0; i < n; ++i, p += 4) im->px[i] = argb(b[p], b[p + 1], b[p + 2], b[p + 3]);
    }
    free(b);
    image_colour(im, 0);
    return 1;
}

/* ---------------------------------------------------------------- drawing */

static uint32_t *fb;

static void blend(uint32_t *d, uint32_t s) {
    uint32_t a = s >> 24, ia, r, g, b;
    if (a == 255) { *d = s & 0xFFFFFF; return; }
    if (!a) return;
    ia = 255 - a;
    r = (((s >> 16) & 255) * a + ((*d >> 16) & 255) * ia + 128) * 257 >> 16;
    g = (((s >> 8) & 255) * a + ((*d >> 8) & 255) * ia + 128) * 257 >> 16;
    b = ((s & 255) * a + (*d & 255) * ia + 128) * 257 >> 16;
    *d = r << 16 | g << 8 | b;
}

static uint32_t flash_of(uint32_t c) {
    uint32_t r = (c >> 16) & 255, g = (c >> 8) & 255, b = c & 255;
    r += (255 - r) * 3 >> 2; g += (255 - g) * 3 >> 2; b += (255 - b) * 3 >> 2;
    return (c & 0xFF000000u) | r << 16 | g << 8 | b;
}

/* a rect (ax, ay, w, h) of an atlas onto the frame at (x, y) */
static void blit(const Image *im, int ax, int ay, int w, int h, int x, int y, int flip, int flash) {
    int i, j;
    for (j = 0; j < h; ++j) {
        int sy = y + j;
        const uint32_t *row = im->px + (ay + j) * im->w + ax;
        if (sy < 0 || sy >= SCREEN_H) continue;
        for (i = 0; i < w; ++i) {
            int sx = x + i;
            uint32_t c;
            if (sx < 0 || sx >= SCREEN_W) continue;
            c = row[flip ? w - 1 - i : i];
            if (!(c >> 24)) continue;
            blend(fb + sy * SCREEN_W + sx, flash ? flash_of(c) : c);
        }
    }
}

static void shade(int x, int y, int w, int h, uint32_t a) {
    int i, j;
    for (j = y; j < y + h; ++j)
        for (i = x; i < x + w; ++i)
            if (i >= 0 && j >= 0 && i < SCREEN_W && j < SCREEN_H) blend(fb + j * SCREEN_W + i, a << 24);
}

static int utf8(const char **s) {
    const unsigned char *p = (const unsigned char *)*s;
    int c = *p++;
    if (c >= 0xF0) { c = (c & 7) << 18 | (p[0] & 63) << 12 | (p[1] & 63) << 6 | (p[2] & 63); p += 3; }
    else if (c >= 0xE0) { c = (c & 15) << 12 | (p[0] & 63) << 6 | (p[1] & 63); p += 2; }
    else if (c >= 0xC0) { c = (c & 31) << 6 | (p[0] & 63); p += 1; }
    *s = (const char *)p;
    return c;
}

static int text_w(const char *s) {
    int w = 0;
    while (*s) {
        int c = utf8(&s), g = c < 0x3000 ? glyph_of[c] - 1 : -1;
        if (g >= 0) w += glyph[g].adv;
    }
    return w;
}

static void text_one(int x, int y, const char *s, uint32_t colour) {
    while (*s) {
        int c = utf8(&s), g = c < 0x3000 ? glyph_of[c] - 1 : -1, i, j;
        if (g < 0) continue;
        for (j = 0; j < glyph[g].h; ++j)
            for (i = 0; i < glyph[g].w; ++i) {
                uint32_t a = font.px[(glyph[g].y + j) * font.w + glyph[g].x + i] >> 24;
                int sx = x + glyph[g].l + i, sy = y + glyph[g].top + j;
                if (a && sx >= 0 && sy >= 0 && sx < SCREEN_W && sy < SCREEN_H)
                    blend(fb + sy * SCREEN_W + sx, a << 24 | (colour & 0xFFFFFF));
            }
        x += glyph[g].adv;
    }
}

static void text(int x, int y, const char *s, uint32_t colour) {
    text_one(x + 1, y + 1, s, 0x000000);
    text_one(x, y, s, colour);
}

static const char *str(const char *key) {
    int i;
    for (i = 0; i < n_strings; ++i) if (!strcmp(string_key[i], key)) return strings[i];
    return key;
}

/* ---------------------------------------------------------------- sound */

static int sound_of(const char *name) {
    int i;
    for (i = 0; i < n_sounds; ++i) if (!strcmp(sounds[i].name, name)) return i;
    return -1;
}

static void load_sound(const char *dir, const char *name) {
    char rel[96];
    long len, p = 12;
    uint8_t *b;
    if (n_sounds >= MAX_SOUNDS) return;
    snprintf(rel, sizeof rel, "%s/%s.wav", dir, name);
    b = read_file(path_of(rel), &len);
    if (!b || len < 44 || memcmp(b, "RIFF", 4) || memcmp(b + 8, "WAVE", 4)) { printf("no sound %s\n", rel); free(b); return; }
    while (p + 8 <= len) {
        long size = b[p + 4] | b[p + 5] << 8 | b[p + 6] << 16 | (long)b[p + 7] << 24;
        if (!memcmp(b + p, "data", 4)) {
            Sound *s = &sounds[n_sounds++];
            if (size > len - p - 8) size = len - p - 8;
            snprintf(s->name, sizeof s->name, "%s", name);
            s->len = (int)(size / 2);
            s->data = (int16_t *)malloc((size_t)size);
            memcpy(s->data, b + p + 8, (size_t)size);   /* 22050 Hz mono 16-bit little-endian (make_sfx_8bit.py) */
            break;
        }
        p += 8 + size + (size & 1);
    }
    free(b);
}

static void play(const char *name, int vol) {
    int s = sound_of(name);
    if (s >= 0 && n_pending < 16) { pending[n_pending].sound = s; pending[n_pending].vol = vol; n_pending++; }
}

void core_audio_commit(void) {
    int i, k;
    if (music_change == -2) chan[0].d = 0;
    else if (music_change >= 0) {
        chan[0].d = sounds[music_change].data; chan[0].len = sounds[music_change].len;
        chan[0].pos = 0; chan[0].vol = 150; chan[0].loop = 1;
    }
    music_change = -1;
    for (i = 0; i < n_pending; ++i) {
        int best = 1;
        for (k = 1; k < CHANNELS; ++k)              /* a free channel, or the one nearest its end */
            if (!chan[k].d) { best = k; break; } else if (chan[k].len - chan[k].pos < chan[best].len - chan[best].pos) best = k;
        chan[best].d = sounds[pending[i].sound].data; chan[best].len = sounds[pending[i].sound].len;
        chan[best].pos = 0; chan[best].vol = pending[i].vol; chan[best].loop = 0;
    }
    n_pending = 0;
}

void core_audio(int16_t *out, int n) {
    int i, k;
    for (i = 0; i < n; ++i) {
        int32_t v = 0;
        for (k = 0; k < CHANNELS; ++k) {
            Channel *c = &chan[k];
            if (!c->d) continue;
            v += c->d[c->pos] * c->vol >> 8;
            if (++c->pos >= c->len) { if (c->loop) c->pos = 0; else c->d = 0; }
        }
        out[i] = (int16_t)(v > 32767 ? 32767 : v < -32768 ? -32768 : v);
    }
}

static void music_update(void) {
    music_change = music_on ? sound_of(night ? "nhac-dem" : "nhac-ngay") : -2;
    if (music_change == -1) music_change = -2;
}

/* ---------------------------------------------------------------- pets and rooms */

static float ease(float t) { return 0.5f - 0.5f * cosf(3.14159265f * t); }

static int frame_of(const char *name) {
    int i;
    for (i = 0; i < pet.nfr; ++i) if (!strcmp(pet.fr[i].name, name)) return i;
    return 0;
}

static int move_of(const char *name) {
    int i;
    for (i = 0; i < pet.nmv; ++i) if (!strcmp(pet.mv[i].name, name)) return i;
    return -1;
}

static void pet_free(void) {
    int i;
    image_free(&pet.atlas);
    for (i = 0; i < pet.nmv; ++i) free(pet.mv[i].s);
    memset(&pet, 0, sizeof pet);
}

/* the moves of one .anim file, sampled every FRAME_MS as preview_anims.samples does */
static void load_moves(const char *rel) {
    char *text = (char *)read_file(path_of(rel), 0), *line, *save = 0;
    Move *m = 0;
    float px = 0, py = 0;
    if (!text) return;
    for (line = strtok_r(text, "\n", &save); line; line = strtok_r(0, "\n", &save)) {
        char a[16], b[32], c[16], d[16];
        int ms, shake, flash, loop, steps, i;
        float br;
        if (sscanf(line, "move %15s %d", a, &loop) == 2 && pet.nmv < MAX_MOVES) {
            m = &pet.mv[pet.nmv++];
            snprintf(m->name, sizeof m->name, "%s", a);
            m->loop = loop;
            px = py = 0;
        } else if (m && sscanf(line, "key %31s %d %15s %15s %f %d %d", b, &ms, c, d, &br, &shake, &flash) == 7) {
            float gx = !strcmp(c, "-") ? px : (float)atof(c), gy = !strcmp(d, "-") ? py : (float)atof(d);
            steps = (int)floorf(ms / (float)FRAME_MS + 0.5f);
            if (steps < 1) steps = 1;
            m->s = (Sample *)realloc(m->s, sizeof(Sample) * (size_t)(m->n + steps));
            for (i = 0; i < steps; ++i) {
                float t = ease((i + 1) / (float)steps);
                Sample *s = &m->s[m->n++];
                s->f = frame_of(b);
                s->x = px + (gx - px) * t;
                s->y = py + (gy - py) * t;
                s->shake = shake;
                s->flash = i == 0 ? flash : 0;
            }
            px = gx; py = gy;
        }
    }
    free(text);
}

static int load_pet(int i) {
    char rel[128], *text, *line, *save = 0;
    pet_free();
    snprintf(rel, sizeof rel, "pet/%s_%s.hli", pets[i].cid, pets[i].stage);
    if (!image_load(&pet.atlas, rel)) return 0;
    snprintf(rel, sizeof rel, "pet/%s_%s.txt", pets[i].cid, pets[i].stage);
    text = (char *)read_file(path_of(rel), 0);
    if (!text) return 0;
    for (line = strtok_r(text, "\n", &save); line; line = strtok_r(0, "\n", &save)) {
        Frame *f = &pet.fr[pet.nfr];
        if (sscanf(line, "canvas %d %d anchor %d %d", &pet.cw, &pet.ch, &pet.ax, &pet.ay) == 4) continue;
        if (pet.nfr < MAX_FRAMES &&
            sscanf(line, "frame %23s %d %d %d %d %d %d %d", f->name, &f->ax, &f->ay, &f->w, &f->h, &f->ox, &f->oy, &f->dx) == 8)
            pet.nfr++;
    }
    free(text);
    snprintf(rel, sizeof rel, "pet/%s_%s.anim", pets[i].cid, pets[i].stage);
    load_moves(rel);
    if (night) image_colour(&pet.atlas, 1);
    pet_i = i;
    cur = move_of("idle") >= 0 ? move_of("idle") : 0;
    sel = cur;
    tick = 0;
    printf("pet %s/%s: %d frames, %d moves\n", pets[i].cid, pets[i].stage, pet.nfr, pet.nmv);
    return 1;
}

static int load_room(int i) {
    char rel[128], *text, *line, *save = 0;
    int a, b;
    image_free(&room.bg); image_free(&room.deco);
    room.n = 0;
    snprintf(rel, sizeof rel, "bg/%s.hli", rooms[i].name);
    if (!image_load(&room.bg, rel)) return 0;
    snprintf(rel, sizeof rel, "phong/%s_do.hli", rooms[i].name);
    if (!image_load(&room.deco, rel)) return 0;
    snprintf(rel, sizeof rel, "phong/%s_do.txt", rooms[i].name);
    text = (char *)read_file(path_of(rel), 0);
    if (!text) return 0;
    for (line = strtok_r(text, "\n", &save); line; line = strtok_r(0, "\n", &save)) {
        Item *it = &room.it[room.n];
        if (room.n < MAX_ITEMS &&
            sscanf(line, "item %47s %d %d %d %d %d %d %d", it->name, &it->ax, &it->ay, &it->w, &it->h, &it->sx, &it->sy, &it->floor) == 8)
            room.n++;
    }
    free(text);
    /* draw order: by floor line, ties in file order (a stable sort, like the previews) */
    for (a = 0; a < room.n; ++a) room.order[a] = a;
    for (a = 1; a < room.n; ++a)
        for (b = a; b > 0 && room.it[room.order[b - 1]].floor > room.it[room.order[b]].floor; --b) {
            int t = room.order[b]; room.order[b] = room.order[b - 1]; room.order[b - 1] = t;
        }
    if (night) { image_colour(&room.bg, 1); image_colour(&room.deco, 1); }
    room_i = i;
    feet_x = (rooms[i].lo + rooms[i].hi) / 2.0f;
    printf("room %s: %d items\n", rooms[i].name, room.n);
    return 1;
}

/* how far the body reaches from the feet, either way, over the frames of one move */
static int reach(const char *base) {
    int i, r = 0, any = 0, n = (int)strlen(base);
    for (i = 0; i < pet.nfr; ++i)
        if (!strncmp(pet.fr[i].name, base, (size_t)n) && pet.fr[i].name[n] == '-') any = 1;
    for (i = 0; i < pet.nfr; ++i) {
        const Frame *f = &pet.fr[i];
        int a = pet.ax - f->dx - f->ox, b = f->ox + f->w - pet.ax + f->dx;
        if (any && !(!strncmp(f->name, base, (size_t)n) && f->name[n] == '-')) continue;
        if (a > r) r = a;
        if (b > r) r = b;
    }
    return r;
}

/* ---------------------------------------------------------------- the app */

static void load_list(void) {
    char *text = (char *)read_file(path_of("list.txt"), 0), *line, *save = 0;
    if (!text) return;
    for (line = strtok_r(text, "\n", &save); line; line = strtok_r(0, "\n", &save)) {
        int k = 0;
        if (!strncmp(line, "room ", 5) && n_rooms < MAX_ROOMS) {
            RoomInfo *r = &rooms[n_rooms];
            if (sscanf(line, "room %31s %d %d %d %n", r->name, &r->feet, &r->lo, &r->hi, &k) == 4 && k) {
                snprintf(r->label, sizeof r->label, "%s", line + k); n_rooms++;
            }
        } else if (!strncmp(line, "pet ", 4) && n_pets < MAX_PETS) {
            PetInfo *p = &pets[n_pets];
            if (sscanf(line, "pet %31s %11s %n", p->cid, p->stage, &k) == 2 && k) {
                snprintf(p->label, sizeof p->label, "%s", line + k); n_pets++;
            }
        }
    }
    free(text);
}

static void load_font(void) {
    char *text = (char *)read_file(path_of("font.txt"), 0), *line, *save = 0;
    if (!text || !image_load(&font, "font.hli")) { free(text); return; }
    for (line = strtok_r(text, "\n", &save); line; line = strtok_r(0, "\n", &save)) {
        int cp, x, y, w, h, l, adv, top;
        if (sscanf(line, "lineheight %d ascent %d", &line_h, &ascent) == 2) continue;
        if (sscanf(line, "glyph %d %d %d %d %d %d %d %d", &cp, &x, &y, &w, &h, &l, &adv, &top) == 8 && cp < 0x3000 && n_glyphs < MAX_GLYPHS) {
            glyph[n_glyphs].x = x; glyph[n_glyphs].y = y; glyph[n_glyphs].w = w; glyph[n_glyphs].h = h;
            glyph[n_glyphs].l = l; glyph[n_glyphs].adv = adv; glyph[n_glyphs].top = top;
            glyph_of[cp] = ++n_glyphs;
        }
    }
    free(text);
}

static void load_strings(void) {
    char *text = (char *)read_file(path_of("strings.txt"), 0), *line, *save = 0;
    if (!text) return;
    for (line = strtok_r(text, "\n", &save); line && n_strings < MAX_STRINGS; line = strtok_r(0, "\n", &save)) {
        int k = 0;
        if (sscanf(line, "%23s %n", string_key[n_strings], &k) == 1 && k) {
            snprintf(strings[n_strings], sizeof strings[0], "%s", line + k); n_strings++;
        }
    }
    free(text);
}

static const char *SFX[] = { "an", "buoc-1", "buoc-2", "chay", "chieu", "chon", "dam", "dem", "doi-pet", "doi-phong",
                             "don-he", "guc", "menu", "met", "ngay", "ngu", "no", "om", "quay-lai", "thang",
                             "thuc-day", "trung-don", "vui" };
/* the sound each move starts with */
static const char *MOVE_SFX[][2] = { { "punch", "dam" }, { "attack", "don-he" }, { "blast", "chieu" }, { "hit", "trung-don" },
                                     { "faint", "guc" }, { "victory", "thang" }, { "eat", "an" }, { "happy", "vui" },
                                     { "tired", "met" }, { "sick", "om" }, { "sleep", "ngu" }, { "wake", "thuc-day" },
                                     { "hatch", "no" }, { "shake", "menu" } };

int core_init(const char *dir) {
    unsigned i;
    snprintf(data_dir, sizeof data_dir, "%s", dir);
    load_list();
    load_font();
    load_strings();
    for (i = 0; i < sizeof SFX / sizeof *SFX; ++i) load_sound("sfx", SFX[i]);
    /* the music shares its file names with the day / night chimes: renamed here */
    { int k = n_sounds; load_sound("nhac", "ngay"); if (n_sounds > k) snprintf(sounds[k].name, sizeof sounds[k].name, "nhac-ngay"); }
    { int k = n_sounds; load_sound("nhac", "dem"); if (n_sounds > k) snprintf(sounds[k].name, sizeof sounds[k].name, "nhac-dem"); }
    printf("%d rooms, %d pets, %d glyphs, %d sounds\n", n_rooms, n_pets, n_glyphs, n_sounds);
    if (!n_rooms || !n_pets || !n_glyphs) return 0;
    if (!load_room(0)) return 0;
    for (i = 0; i < (unsigned)n_pets; ++i)               /* start with the fire tiger child, as in the demos */
        if (!strcmp(pets[i].cid, "hoa-ho") && !strcmp(pets[i].stage, "child")) break;
    if (!load_pet(i < (unsigned)n_pets ? (int)i : 0)) return 0;
    music_update();
    return 1;
}

static void set_night(int on) {
    night = on;
    image_colour(&room.bg, on); image_colour(&room.deco, on); image_colour(&pet.atlas, on);
    play(on ? "dem" : "ngay", 200);
    music_update();
}

static float rnd(void) { seed = seed * 1664525u + 1013904223u; return (seed >> 8) / 16777216.0f; }

static void hud(void) {
    char line[256];
    const Move *m = pet.nmv ? &pet.mv[sel] : 0;
    shade(0, 0, SCREEN_W, 52, 150);
    text(10, 4, rooms[room_i].label, 0xFFE6A0);
    snprintf(line, sizeof line, "%s · %s", night ? str("night") : str("day"), music_on ? str("music_on") : str("music_off"));
    text(SCREEN_W - 10 - text_w(line), 4, line, 0xC8DCFF);
    snprintf(line, sizeof line, "%s   (%d/%d)", pets[pet_i].label, pet_i + 1, n_pets);
    text(10, 27, line, 0xFFFFFF);
    shade(0, SCREEN_H - 50, SCREEN_W, 50, 150);
    if (m) {
        const char *label = str(m->name);
        snprintf(line, sizeof line, "%s %s · %s", str("updown"), label, str("act"));
        text(10, SCREEN_H - 46, line, 0xFFE6A0);
    }
    text(SCREEN_W - 10 - text_w(str("walkhint")), SCREEN_H - 46, str("walkhint"), 0xFFFFFF);
    snprintf(line, sizeof line, "%s · %s", str("help"), str("quit"));
    text(10, SCREEN_H - 23, line, 0xB4B4B4);
}

void core_frame(const int held[BTN_COUNT], uint32_t *frame) {
    int press[BTN_COUNT], i, dir, walking = 0, run_move = -1, x, jx = 0, jy = 0, drawn = 0, feet;
    const Sample *s;
    const Frame *f;
    static const Sample still = { 0, 0, 0, 0, 0 };
    for (i = 0; i < BTN_COUNT; ++i) { press[i] = held[i] && !prev[i]; }
    fb = frame;

    /* SELECT + START quits; on their own they act when let go, so the combo does not toggle anything */
    if (held[BTN_NIGHT] && held[BTN_MUSIC]) { combo = 1; quit = 1; }
    if (!held[BTN_NIGHT] && prev[BTN_NIGHT] && !combo) set_night(!night);
    if (!held[BTN_MUSIC] && prev[BTN_MUSIC] && !combo) { music_on = !music_on; music_update(); play("chon", 200); }
    if (!held[BTN_NIGHT] && !held[BTN_MUSIC]) combo = 0;

    if (press[BTN_NEXT_ROOM] || press[BTN_PREV_ROOM]) {
        load_room((room_i + (press[BTN_NEXT_ROOM] ? 1 : n_rooms - 1)) % n_rooms);
        play("doi-phong", 220);
    }
    if (press[BTN_NEXT_PET] || press[BTN_PREV_PET]) {
        load_pet((pet_i + (press[BTN_NEXT_PET] ? 1 : n_pets - 1)) % n_pets);
        play("doi-pet", 220);
    }
    if (pet.nmv && (press[BTN_UP] || press[BTN_DOWN])) {
        do sel = (sel + (press[BTN_DOWN] ? 1 : pet.nmv - 1)) % pet.nmv;
        while (!strcmp(pet.mv[sel].name, "walk") || !strcmp(pet.mv[sel].name, "run"));
        play("menu", 200);
    }
    if (pet.nmv && press[BTN_ACT]) {
        unsigned k;
        cur = sel; tick = 0;
        for (k = 0; k < sizeof MOVE_SFX / sizeof *MOVE_SFX; ++k)
            if (!strcmp(MOVE_SFX[k][0], pet.mv[cur].name)) play(MOVE_SFX[k][1], 256);
    }

    dir = (held[BTN_RIGHT] ? 1 : 0) - (held[BTN_LEFT] ? 1 : 0);
    feet = rooms[room_i].feet;
    if (dir && pet.nmv) {
        int run = held[BTN_RUN] && move_of("run") >= 0, r, lo, hi;
        const char *base = run ? "run" : "walk";
        int mv = move_of(base);
        run_move = mv >= 0 ? mv : (move_of("idle") >= 0 ? move_of("idle") : 0);
        s = &pet.mv[run_move].s[tick % pet.mv[run_move].n];
        left_facing = dir < 0;
        r = reach(mv >= 0 ? base : "idle");
        lo = rooms[room_i].lo + r; hi = rooms[room_i].hi - r;
        feet_x += dir * (run ? 110.0f : 34.0f) * 2 * FRAME_MS / 1000.0f;
        feet_x = lo > hi ? (rooms[room_i].lo + rooms[room_i].hi) / 2.0f : feet_x < lo ? lo : feet_x > hi ? hi : feet_x;
        walking = 1;
        /* footsteps when a foot lands (frames -0 and -2), or every 10 steps when there is no walk drawing */
        if (mv >= 0 ? (s->f != walk_prev && (strstr(pet.fr[s->f].name, "-0") || strstr(pet.fr[s->f].name, "-2")))
                    : tick % 10 == 0) {
            play(run ? "chay" : (step_parity ^= 1) ? "buoc-1" : "buoc-2", run ? 200 : 230);
        }
        walk_prev = s->f;
    } else if (pet.nmv) {
        Move *m = &pet.mv[cur];
        walk_prev = -1;
        if (tick >= m->n) {
            if (m->loop) tick = 0;
            else { cur = move_of("idle") >= 0 ? move_of("idle") : 0; tick = 0; m = &pet.mv[cur]; }
        }
        s = &m->s[tick < m->n ? tick : m->n - 1];
    } else {
        s = &still;
    }
    tick++;
    if (s->shake) {
        jx = (int)lroundf((rnd() * 2 - 1) * s->shake);
        jy = (int)lroundf((rnd() * 2 - 1) * s->shake) >> 1;
    }
    f = &pet.fr[s->f];
    x = (int)lroundf(feet_x + (walking ? 0 : (left_facing ? -s->x : s->x))) + jx;

    memcpy(fb, room.bg.px, sizeof(uint32_t) * SCREEN_W * SCREEN_H);   /* alpha byte is ignored by the screen */
    for (i = 0; i <= room.n; ++i) {
        const Item *it = i < room.n ? &room.it[room.order[i]] : 0;
        if (!drawn && (!it || it->floor > feet)) {
            /* top-left from the canvas anchor moved by the frame's align dx, mirrored when facing left */
            int sx = left_facing ? x - (pet.cw - pet.ax) - f->dx + (pet.cw - f->ox - f->w) : x - pet.ax + f->dx + f->ox;
            int sy = feet - pet.ay + (int)lroundf(s->y) + jy + f->oy;
            blit(&pet.atlas, f->ax, f->ay, f->w, f->h, sx, sy, left_facing, s->flash);
            drawn = 1;
        }
        if (it) blit(&room.deco, it->ax, it->ay, it->w, it->h, it->sx, it->sy, 0, 0);
    }
    hud();
    memcpy(prev, held, sizeof prev);
}

int core_wants_quit(void) { return quit; }

void core_shutdown(void) {
    int i;
    pet_free();
    image_free(&room.bg); image_free(&room.deco); image_free(&font);
    for (i = 0; i < n_sounds; ++i) free(sounds[i].data);
    n_sounds = 0;
}
