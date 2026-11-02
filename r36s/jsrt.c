/* See jsrt.h. A small software 2D canvas (what the page calls: drawImage with source rects, scale and mirror,
   fillRect, ellipse / arc fill and stroke, fillText / strokeText, globalAlpha, source-over / source-atop /
   source-in, shadowBlur glow), the pictures and fonts made by scripts/r36s_game.py, an 8-channel sound mixer,
   and their bindings for QuickJS (used from js/shim.js). Pixels are straight-alpha ARGB. */
#include "jsrt.h"
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#include "quickjs/quickjs.h"
#pragma GCC diagnostic pop
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <pthread.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <ifaddrs.h>
#include <net/if.h>

#define MAX_SURF 32768                       /* pictures at once; a freed slot is handed out again (surf_add) */
#define SLOT_BITS 15                         /* an id is slot | generation << SLOT_BITS (MAX_SURF = 1 << SLOT_BITS) */
#define MAX_FONTS 64
#define MAX_GLYPHS 512
#define SCALE_MAX 4096                       /* the widest / tallest draw the fast paths take */
#define MAX_SOUNDS 1024   /* the game's and every Solo pet's (31 x 9) and element sounds, each read from the card once */
#define CHANNELS 9                           /* 0 the music, 1-7 sounds, VOICE the story's voice */
#define VOICE (CHANNELS - 1)

typedef struct { int w, h, opaque; uint32_t *px; } Surf;   /* opaque: a picture with no see-through pixel */
typedef struct { int size, bold, ascent, descent, loaded; Surf atlas; uint16_t map[0x3000];
                 struct { short x, y, w, h, l, adv, top; } g[MAX_GLYPHS]; } Font;
typedef struct { char name[48]; int16_t *data; int len; } Sound;
typedef struct { const int16_t *d; int len, pos, vol, loop; } Channel;

static char root[512];
static Surf *surf[MAX_SURF];
static int n_surf;                           /* slots ever used; the free ones among them are in free_slot */
static int free_slot[MAX_SURF], n_free;
static uint16_t slot_gen[MAX_SURF];          /* bumped when a slot is freed: an old id of it then finds nothing */
static Font *fonts[MAX_FONTS];
static int n_fonts;
static Sound sounds[MAX_SOUNDS];
static int n_sounds;
static Channel chan[CHANNELS];
static struct { int sound, vol; } pending[16];
static int n_pending, music_next = -1, music_vol = 140;   /* music_vol: holua.musicVol, 0..256 */     /* -1 nothing to do, -2 stop, else the sound to loop on channel 0 */
static JSRuntime *rt;
static JSContext *jc;
static double now_ms;
static unsigned pad_bits;
/* tests: HOLUA_TEST=1 makes Math.random repeat (js/shim.js), HOLUA_TEST=slow also turns off the fast paths */
static int test_mode, no_fast;

/* ---------------------------------------------------------------- files */

static uint8_t *read_file(const char *rel, long *len) {
    char path[1024];
    FILE *f;
    uint8_t *b;
    long n;
    snprintf(path, sizeof path, "%s/%s", root, rel);
    f = fopen(path, "rb");
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

static Surf *surf_new(int w, int h) {
    Surf *s = (Surf *)calloc(1, sizeof *s);
    s->w = w > 0 ? w : 0;
    s->h = h > 0 ? h : 0;
    s->px = (uint32_t *)calloc((size_t)(s->w * s->h) + 1, 4);
    return s;
}

/* .hli (scripts/r36s_app.py): 'HLI1', u16 w, u16 h, u16 colours; palette + packets / raw RGBA / raw RGB */
static Surf *load_hli(const char *rel) {
    long len, p = 10;
    uint8_t *b = read_file(rel, &len);
    Surf *s;
    int i, n, ncol;
    if (!b || len < 10 || memcmp(b, "HLI1", 4)) { free(b); return 0; }
    s = surf_new(b[4] | b[5] << 8, b[6] | b[7] << 8);
    ncol = b[8] | b[9] << 8;
    n = s->w * s->h;
    if (ncol >= 1 && ncol <= 256) {
        uint32_t pal[256];
        int k = 0;
        for (i = 0; i < ncol; ++i, p += 4) pal[i] = (uint32_t)b[p + 3] << 24 | b[p] << 16 | b[p + 1] << 8 | b[p + 2];
        while (k < n && p < len) {
            int c = b[p++], m;
            if (c < 0x80) { for (m = 0; m <= c && k < n; ++m) s->px[k++] = pal[b[p + m]]; p += c + 1; }
            else { uint32_t v = pal[b[p++]]; for (m = 0; m < c - 0x7E && k < n; ++m) s->px[k++] = v; }
        }
    } else if (ncol == 0xFFFF) {
        for (i = 0; i < n; ++i, p += 3) s->px[i] = 0xFF000000u | b[p] << 16 | b[p + 1] << 8 | b[p + 2];
    } else {
        for (i = 0; i < n; ++i, p += 4) s->px[i] = (uint32_t)b[p + 3] << 24 | b[p] << 16 | b[p + 1] << 8 | b[p + 2];
    }
    free(b);
    for (s->opaque = 1, i = 0; i < n && s->opaque; ++i) s->opaque = s->px[i] >> 24 == 255;
    return s;
}

/* ---------------------------------------------------------------- pixels */

enum { OP_OVER, OP_ATOP, OP_IN };
typedef struct { double a, b, c, d, e, f; } Mat;   /* x' = a x + c y + e, y' = b x + d y + f */

static inline uint32_t div255(uint32_t v) { return (v + 128 + ((v + 128) >> 8)) >> 8; }

/* colour c (RGB of an ARGB value) with alpha sa (0..255) onto *d */
static inline void put(uint32_t *d, uint32_t c, uint32_t sa, int op) {
    uint32_t dv = *d, da = dv >> 24, r, g, b, oa;
    if (op == OP_IN) {                       /* the source where the destination is, nothing else */
        *d = div255(sa * da) << 24 | (c & 0xFFFFFF);
        return;
    }
    if (!sa) return;
    if (op == OP_ATOP) {
        if (!da) return;
        r = div255(((c >> 16) & 255) * sa + ((dv >> 16) & 255) * (255 - sa));
        g = div255(((c >> 8) & 255) * sa + ((dv >> 8) & 255) * (255 - sa));
        b = div255((c & 255) * sa + (dv & 255) * (255 - sa));
        *d = da << 24 | r << 16 | g << 8 | b;
        return;
    }
    if (da == 255 || sa == 255) {
        uint32_t ia = 255 - sa, rb;
        if (sa == 255) { *d = 0xFF000000u | (c & 0xFFFFFF); return; }
        /* red and blue in one multiply (each in its own 16 bits), the same rounding as div255() */
        rb = (c & 0xFF00FFu) * sa + (dv & 0xFF00FFu) * ia + 0x800080u;
        rb = ((rb + ((rb >> 8) & 0xFF00FFu)) >> 8) & 0xFF00FFu;
        g = div255(((c >> 8) & 255) * sa + ((dv >> 8) & 255) * ia);
        *d = 0xFF000000u | rb | g << 8;
        return;
    }
    {   /* both partly see-through */
        uint32_t dw = div255(da * (255 - sa));
        oa = sa + dw;
        if (!oa) { *d = 0; return; }
        r = (((c >> 16) & 255) * sa + ((dv >> 16) & 255) * dw) / oa;
        g = (((c >> 8) & 255) * sa + ((dv >> 8) & 255) * dw) / oa;
        b = ((c & 255) * sa + (dv & 255) * dw) / oa;
        *d = oa << 24 | r << 16 | g << 8 | b;
    }
}

static int invert(const Mat *m, Mat *o) {
    double det = m->a * m->d - m->b * m->c;
    if (fabs(det) < 1e-12) return 0;
    o->a = m->d / det; o->b = -m->b / det; o->c = -m->c / det; o->d = m->a / det;
    o->e = -(o->a * m->e + o->c * m->f);
    o->f = -(o->b * m->e + o->d * m->f);
    return 1;
}

static inline int clampi(int v, int lo, int hi) { return v < lo ? lo : v > hi ? hi : v; }

/* the destination pixels a user-space rectangle can touch */
static void bounds(const Surf *d, const Mat *m, double x, double y, double w, double h, int *x0, int *y0, int *x1, int *y1) {
    double xs[4] = { x, x + w, x, x + w }, ys[4] = { y, y, y + h, y + h }, lx = 1e9, ly = 1e9, hx = -1e9, hy = -1e9;
    int i;
    for (i = 0; i < 4; ++i) {
        double X = m->a * xs[i] + m->c * ys[i] + m->e, Y = m->b * xs[i] + m->d * ys[i] + m->f;
        lx = X < lx ? X : lx;
        hx = X > hx ? X : hx;
        ly = Y < ly ? Y : ly;
        hy = Y > hy ? Y : hy;
    }
    *x0 = clampi((int)floor(lx + 0.5), 0, d->w);
    *y0 = clampi((int)floor(ly + 0.5), 0, d->h);
    *x1 = clampi((int)floor(hx + 0.5), 0, d->w);
    *y1 = clampi((int)floor(hy + 0.5), 0, d->h);
}

static uint32_t alpha_of(double a) { return a <= 0 ? 0 : a >= 1 ? 255 : (uint32_t)(a * 255 + 0.5); }

static void fill_rect(Surf *d, double x, double y, double w, double h, const Mat *m, uint32_t rgba, double alpha, int op,
                      int checker) {
    uint32_t sa = div255((rgba >> 24) * alpha_of(alpha));
    int x0, y0, x1, y1, X, Y;
    Mat inv;
    if (!invert(m, &inv)) return;
    bounds(d, m, x, y, w, h, &x0, &y0, &x1, &y1);
    if (checker > 0 && m->b == 0 && m->c == 0 && x1 - x0 <= SCALE_MAX) {
        /* a repeating checker pattern (createPattern of checker x checker blocks, the arena's dimming): only its
           solid blocks are touched, every other pixel is left as it is */
        static unsigned char odd[SCALE_MAX];
        for (X = x0; X < x1; ++X) odd[X - x0] = (unsigned char)((long)floor((inv.a * (X + 0.5) + inv.e) / checker) & 1);
        for (Y = y0; Y < y1; ++Y) {
            uint32_t *row = d->px + Y * d->w;
            int ry = (int)((long)floor((inv.d * (Y + 0.5) + inv.f) / checker) & 1);
            for (X = x0; X < x1; ++X) if (odd[X - x0] == ry) put(row + X, rgba, sa, op);
        }
        return;
    }
    if (m->b == 0 && m->c == 0 && !no_fast) {  /* not rotated: the bounds are the rectangle */
        for (Y = y0; Y < y1; ++Y) {
            uint32_t *row = d->px + Y * d->w;
            for (X = x0; X < x1; ++X) put(row + X, rgba, sa, op);
        }
        return;
    }
    for (Y = y0; Y < y1; ++Y)
        for (X = x0; X < x1; ++X) {
            double u = inv.a * (X + 0.5) + inv.c * (Y + 0.5) + inv.e, v = inv.b * (X + 0.5) + inv.d * (Y + 0.5) + inv.f;
            if (u >= x && u < x + w && v >= y && v < y + h) put(&d->px[Y * d->w + X], rgba, sa, op);
        }
}

static uint32_t bilinear(const Surf *s, double px, double py, int sx0, int sy0, int sx1, int sy1) {
    int x = (int)floor(px - 0.5), y = (int)floor(py - 0.5), i;
    double fx = px - 0.5 - x, fy = py - 0.5 - y, acc[4] = { 0, 0, 0, 0 };
    for (i = 0; i < 4; ++i) {
        int xx = x + (i & 1), yy = y + (i >> 1);
        double w = ((i & 1) ? fx : 1 - fx) * ((i >> 1) ? fy : 1 - fy), a;
        uint32_t c;
        xx = clampi(xx, sx0, sx1 - 1);
        yy = clampi(yy, sy0, sy1 - 1);
        c = s->px[yy * s->w + xx];
        a = (c >> 24) * w;
        acc[0] += a; acc[1] += ((c >> 16) & 255) * a; acc[2] += ((c >> 8) & 255) * a; acc[3] += (c & 255) * a;
    }
    if (acc[0] < 0.5) return 0;
    return (uint32_t)(acc[0] + 0.5) << 24 | (uint32_t)(acc[1] / acc[0] + 0.5) << 16 |
           (uint32_t)(acc[2] / acc[0] + 0.5) << 8 | (uint32_t)(acc[3] / acc[0] + 0.5);
}

/* a blurred, tinted copy of what a draw covers (canvas shadowBlur with no offset), under it */
static void glow(Surf *d, const Surf *s, int sx0, int sy0, int sx1, int sy1, double sx, double sy, double sw, double sh,
                 double dx, double dy, double dw, double dh, const Mat *inv, int x0, int y0, int x1, int y1,
                 uint32_t rgba, double blur) {
    int r = (int)(blur / 2 + 0.5), W, H, X, Y, pass;
    float *m, *t;
    uint32_t sa = rgba >> 24;
    x0 -= 3 * r; y0 -= 3 * r; x1 += 3 * r; y1 += 3 * r;
    x0 = clampi(x0, 0, d->w); y0 = clampi(y0, 0, d->h);
    x1 = clampi(x1, 0, d->w); y1 = clampi(y1, 0, d->h);
    W = x1 - x0; H = y1 - y0;
    if (W <= 0 || H <= 0 || !sa) return;
    m = (float *)calloc((size_t)(W * H), sizeof(float));
    t = (float *)calloc((size_t)(W * H), sizeof(float));
    for (Y = 0; Y < H; ++Y)
        for (X = 0; X < W; ++X) {
            double u = inv->a * (X + x0 + 0.5) + inv->c * (Y + y0 + 0.5) + inv->e;
            double v = inv->b * (X + x0 + 0.5) + inv->d * (Y + y0 + 0.5) + inv->f;
            int px = (int)floor(sx + (u - dx) * sw / dw), py = (int)floor(sy + (v - dy) * sh / dh);
            if (px >= sx0 && px < sx1 && py >= sy0 && py < sy1) m[Y * W + X] = (float)(s->px[py * s->w + px] >> 24) / 255.0f;
        }
    for (pass = 0; pass < 3 && r > 0; ++pass) {        /* three box blurs ~ a gaussian of sigma blur/2 */
        for (Y = 0; Y < H; ++Y) {
            float acc = 0;
            for (X = -r; X < W + r; ++X) {
                if (X + r < W) acc += m[Y * W + X + r];
                if (X - r - 1 >= 0) acc -= m[Y * W + X - r - 1];
                if (X >= 0 && X < W) t[Y * W + X] = acc / (2 * r + 1);
            }
        }
        for (X = 0; X < W; ++X) {
            float acc = 0;
            for (Y = -r; Y < H + r; ++Y) {
                if (Y + r < H) acc += t[(Y + r) * W + X];
                if (Y - r - 1 >= 0) acc -= t[(Y - r - 1) * W + X];
                if (Y >= 0 && Y < H) m[Y * W + X] = acc / (2 * r + 1);
            }
        }
    }
    for (Y = 0; Y < H; ++Y)
        for (X = 0; X < W; ++X) {
            uint32_t a = (uint32_t)(m[Y * W + X] * sa + 0.5f);
            if (a) put(&d->px[(Y + y0) * d->w + X + x0], rgba, a > 255 ? 255 : a, OP_OVER);
        }
    free(m); free(t);
}

/* ctx.filter brightness(b) then saturate(s), as one colour matrix (the CSS filter formulas); off when both are 1 */
static int filter_on;
static float filter_m[9];

static void set_filter(double b, double s) {
    float k = (float)b, t = (float)s;
    filter_on = fabs(b - 1) > 1e-6 || fabs(s - 1) > 1e-6;
    filter_m[0] = k * (0.213f + 0.787f * t); filter_m[1] = k * (0.715f - 0.715f * t); filter_m[2] = k * (0.072f - 0.072f * t);
    filter_m[3] = k * (0.213f - 0.213f * t); filter_m[4] = k * (0.715f + 0.285f * t); filter_m[5] = k * (0.072f - 0.072f * t);
    filter_m[6] = k * (0.213f - 0.213f * t); filter_m[7] = k * (0.715f - 0.715f * t); filter_m[8] = k * (0.072f + 0.928f * t);
}


/* bilinear() in whole numbers: four source pixels, the share of the right / lower ones in sixteenths */
static inline uint32_t blend4(uint32_t c00, uint32_t c10, uint32_t c01, uint32_t c11, uint32_t fx, uint32_t fy) {
    uint32_t w00, w10, w01, w11, a00, a10, a01, a11, A, h;
    if (c00 == c10 && c00 == c01 && c00 == c11) return c00;
    w00 = (16 - fx) * (16 - fy); w10 = fx * (16 - fy); w01 = (16 - fx) * fy; w11 = fx * fy;
    a00 = (c00 >> 24) * w00; a10 = (c10 >> 24) * w10; a01 = (c01 >> 24) * w01; a11 = (c11 >> 24) * w11;
    A = a00 + a10 + a01 + a11;
    if (A < 128) return 0;
    h = A / 2;
#define CH(sh) ((((c00 >> sh) & 255) * a00 + ((c10 >> sh) & 255) * a10 + ((c01 >> sh) & 255) * a01 + ((c11 >> sh) & 255) * a11 + h) / A)
    return ((A + 128) >> 8) << 24 | CH(16) << 16 | CH(8) << 8 | CH(0);
#undef CH
}

static uint32_t filtered(uint32_t c) {
    float r = (float)((c >> 16) & 255), g = (float)((c >> 8) & 255), b = (float)(c & 255), o[3];
    int i;
    for (i = 0; i < 3; ++i) {
        o[i] = filter_m[3 * i] * r + filter_m[3 * i + 1] * g + filter_m[3 * i + 2] * b + 0.5f;
        o[i] = o[i] < 0 ? 0 : o[i] > 255 ? 255 : o[i];
    }
    return (c & 0xFF000000u) | (uint32_t)o[0] << 16 | (uint32_t)o[1] << 8 | (uint32_t)o[2];
}

static void draw_image(Surf *d, const Surf *s, double sx, double sy, double sw, double sh, double dx, double dy,
                       double dw, double dh, const Mat *m, double alpha, int op, uint32_t shadow, double blur) {
    uint32_t ga = alpha_of(alpha);
    int x0, y0, x1, y1, X, Y, sx0, sy0, sx1, sy1, scaled;
    Mat inv;
    if (!s || !s->w || !s->h || sw <= 0 || sh <= 0 || dw == 0 || dh == 0 || !invert(m, &inv)) return;
    sx0 = (int)floor(sx); sy0 = (int)floor(sy); sx1 = (int)ceil(sx + sw); sy1 = (int)ceil(sy + sh);
    sx0 = clampi(sx0, 0, s->w); sy0 = clampi(sy0, 0, s->h);
    sx1 = clampi(sx1, 0, s->w); sy1 = clampi(sy1, 0, s->h);
    if (sx0 >= sx1 || sy0 >= sy1) return;
    bounds(d, m, dx, dy, dw, dh, &x0, &y0, &x1, &y1);
    if (blur > 0 && (shadow >> 24)) glow(d, s, sx0, sy0, sx1, sy1, sx, sy, sw, sh, dx, dy, dw, dh, &inv, x0, y0, x1, y1, shadow, blur);
    scaled = fabs(fabs(m->a * dw / sw) - 1) > 1e-6 || fabs(fabs(m->d * dh / sh) - 1) > 1e-6 || m->b != 0 || m->c != 0;
    if (!scaled && !no_fast) {
        /* the common case: same size, moved by whole pixels, maybe mirrored (a pet facing left).
           Source pixel = K + step * destination pixel, along each axis. */
        int fx = m->a < 0, fy = m->d < 0;
        double kx = fx ? sx + m->e - dx - 1 : sx - m->e - dx, ky = fy ? sy + m->f - dy - 1 : sy - m->f - dy;
        if (kx == floor(kx) && ky == floor(ky) && sx == floor(sx) && sy == floor(sy)) {
            int KX = (int)kx, KY = (int)ky, sxs = fx ? -1 : 1, sys = fy ? -1 : 1, X0, X1, Y0, Y1;
            /* destination range whose source pixel is inside [s0, s1) */
            X0 = fx ? KX - sx1 + 1 : sx0 - KX; X1 = fx ? KX - sx0 + 1 : sx1 - KX;
            Y0 = fy ? KY - sy1 + 1 : sy0 - KY; Y1 = fy ? KY - sy0 + 1 : sy1 - KY;
            X0 = X0 > x0 ? X0 : x0; X1 = X1 < x1 ? X1 : x1;
            Y0 = Y0 > y0 ? Y0 : y0; Y1 = Y1 < y1 ? Y1 : y1;
            for (Y = Y0; Y < Y1; ++Y) {
                const uint32_t *row = s->px + (KY + sys * Y) * s->w;
                uint32_t *out = d->px + Y * d->w;
                int px = KX + sxs * X0;
                if (s->opaque && op == OP_OVER && ga == 255 && sxs == 1 && !filter_on) {   /* a room background: copied */
                    if (X1 > X0) memcpy(out + X0, row + px, (size_t)(X1 - X0) * 4);
                    continue;
                }
                for (X = X0; X < X1; ++X, px += sxs) {
                    uint32_t c = row[px], a = ga == 255 ? c >> 24 : div255((c >> 24) * ga);
                    if (a || op == OP_IN) put(out + X, filter_on ? filtered(c) : c, a, op);
                }
            }
            return;
        }
    }
    if (scaled && m->b == 0 && m->c == 0 && !no_fast && x1 - x0 <= SCALE_MAX && y1 - y0 <= SCALE_MAX) {
        /* scaled but not turned (Solo's half-size frames, the pets in the room): the same smoothing as bilinear(),
           in whole numbers. Each column and row is worked out once: its two source pixels and the share of the
           second (sixteenths); a spot whose four source pixels are the same is that pixel */
        static int ci0[SCALE_MAX], ci1[SCALE_MAX], cf[SCALE_MAX], ri0[SCALE_MAX], ri1[SCALE_MAX], rf[SCALE_MAX];
        static unsigned char cok[SCALE_MAX], rok[SCALE_MAX];
        int k;
        for (k = 0; k < x1 - x0; ++k) {
            double p = sx + (inv.a * (x0 + k + 0.5) + inv.e - dx) * sw / dw, q = p - 0.5;
            int i = (int)floor(q), f = (int)((q - i) * 16 + 0.5);
            if (f == 16) { ++i; f = 0; }
            cok[k] = p >= sx && p < sx + sw;
            ci0[k] = clampi(i, sx0, sx1 - 1); ci1[k] = clampi(i + 1, sx0, sx1 - 1); cf[k] = f;
        }
        for (k = 0; k < y1 - y0; ++k) {
            double p = sy + (inv.d * (y0 + k + 0.5) + inv.f - dy) * sh / dh, q = p - 0.5;
            int i = (int)floor(q), f = (int)((q - i) * 16 + 0.5);
            if (f == 16) { ++i; f = 0; }
            rok[k] = p >= sy && p < sy + sh;
            ri0[k] = clampi(i, sy0, sy1 - 1); ri1[k] = clampi(i + 1, sy0, sy1 - 1); rf[k] = f;
        }
        for (Y = y0; Y < y1; ++Y) {
            const uint32_t *r0, *r1;
            uint32_t *out = d->px + Y * d->w;
            int fy;
            if (!rok[Y - y0]) continue;
            r0 = s->px + ri0[Y - y0] * s->w; r1 = s->px + ri1[Y - y0] * s->w; fy = rf[Y - y0];
            for (X = x0; X < x1; ++X) {
                int j = X - x0;
                uint32_t c, a;
                if (!cok[j]) continue;
                c = blend4(r0[ci0[j]], r0[ci1[j]], r1[ci0[j]], r1[ci1[j]], (uint32_t)cf[j], (uint32_t)fy);
                a = ga == 255 ? c >> 24 : div255((c >> 24) * ga);
                if (a || op == OP_IN) put(out + X, filter_on ? filtered(c) : c, a, op);
            }
        }
        return;
    }
    if (!no_fast && sx1 - sx0 < 30000 && sy1 - sy0 < 30000) {
        /* anything else (turned, or moved by part of a pixel): the source point of a destination pixel is linear in
           X and Y, so along a row it steps by a constant; kept in 16.16 fixed point, with blend4() for scaled draws */
        const double kx = sw / dw, ky = sh / dh, F = 65536.0;
        const double ax = inv.a * kx, cx = inv.c * kx, ex = sx + (inv.e - dx) * kx;   /* px = ax X + cx Y + ex */
        const double by = inv.b * ky, dy2 = inv.d * ky, fy0 = sy + (inv.f - dy) * ky; /* py = by X + dy2 Y + fy0 */
        const int64_t lox = (int64_t)ceil(sx * F), hix = (int64_t)ceil((sx + sw) * F);
        const int64_t loy = (int64_t)ceil(sy * F), hiy = (int64_t)ceil((sy + sh) * F);
        const int64_t stx = (int64_t)llround(ax * F), sty = (int64_t)llround(by * F);
        for (Y = y0; Y < y1; ++Y) {
            uint32_t *out = d->px + Y * d->w;
            int64_t P = (int64_t)llround((ax * (x0 + 0.5) + cx * (Y + 0.5) + ex) * F);
            int64_t Q = (int64_t)llround((by * (x0 + 0.5) + dy2 * (Y + 0.5) + fy0) * F);
            for (X = x0; X < x1; ++X, P += stx, Q += sty) {
                uint32_t c, a;
                if (P < lox || P >= hix || Q < loy || Q >= hiy) continue;
                if (scaled) {
                    int64_t qx = P - 32768, qy = Q - 32768;              /* bilinear's "- 0.5" */
                    int ix = (int)(qx >> 16), iy = (int)(qy >> 16);
                    uint32_t fx = (uint32_t)(((qx & 0xFFFF) + 2048) >> 12), fy = (uint32_t)(((qy & 0xFFFF) + 2048) >> 12);
                    int ix0, ix1, iy0, iy1;
                    if (fx == 16) { ++ix; fx = 0; }
                    if (fy == 16) { ++iy; fy = 0; }
                    ix0 = clampi(ix, sx0, sx1 - 1); ix1 = clampi(ix + 1, sx0, sx1 - 1);
                    iy0 = clampi(iy, sy0, sy1 - 1); iy1 = clampi(iy + 1, sy0, sy1 - 1);
                    c = blend4(s->px[iy0 * s->w + ix0], s->px[iy0 * s->w + ix1], s->px[iy1 * s->w + ix0], s->px[iy1 * s->w + ix1], fx, fy);
                } else {
                    int ix = (int)(P >> 16), iy = (int)(Q >> 16);
                    if (ix < sx0 || ix >= sx1 || iy < sy0 || iy >= sy1) continue;
                    c = s->px[iy * s->w + ix];
                }
                a = ga == 255 ? c >> 24 : div255((c >> 24) * ga);
                if (a || op == OP_IN) put(out + X, filter_on ? filtered(c) : c, a, op);
            }
        }
        return;
    }
    for (Y = y0; Y < y1; ++Y)
        for (X = x0; X < x1; ++X) {
            double u = inv.a * (X + 0.5) + inv.c * (Y + 0.5) + inv.e, v = inv.b * (X + 0.5) + inv.d * (Y + 0.5) + inv.f;
            double px = sx + (u - dx) * sw / dw, py = sy + (v - dy) * sh / dh;
            uint32_t c, a;
            if (px < sx || px >= sx + sw || py < sy || py >= sy + sh) continue;
            if (scaled) c = bilinear(s, px, py, sx0, sy0, sx1, sy1);
            else {
                int ix = (int)floor(px), iy = (int)floor(py);
                if (ix < sx0 || ix >= sx1 || iy < sy0 || iy >= sy1) continue;
                c = s->px[iy * s->w + ix];
            }
            a = div255((c >> 24) * ga);
            if (a || op == OP_IN) put(&d->px[Y * d->w + X], filter_on ? filtered(c) : c, a, op);
        }
}

/* filled (line 0) or stroked ellipse, edges smoothed over a pixel */
static void ellipse(Surf *d, double cx, double cy, double rx, double ry, const Mat *m, uint32_t rgba, double alpha,
                    double line, int op) {
    uint32_t sa = div255((rgba >> 24) * alpha_of(alpha));
    double pad = line / 2 + 2, rr = (rx + ry) / 2;
    int x0, y0, x1, y1, X, Y;
    Mat inv;
    if (rx <= 0 || ry <= 0 || !invert(m, &inv)) return;
    bounds(d, m, cx - rx - pad, cy - ry - pad, 2 * (rx + pad), 2 * (ry + pad), &x0, &y0, &x1, &y1);
    for (Y = y0; Y < y1; ++Y)
        for (X = x0; X < x1; ++X) {
            double u = inv.a * (X + 0.5) + inv.c * (Y + 0.5) + inv.e - cx, v = inv.b * (X + 0.5) + inv.d * (Y + 0.5) + inv.f - cy;
            double dist = sqrt((u / rx) * (u / rx) + (v / ry) * (v / ry)), cover;
            if (line <= 0) cover = (1 - dist) * rr + 0.5;
            else cover = line / 2 - fabs(dist - 1) * rr + 0.5;
            if (cover <= 0) continue;
            if (cover > 1) cover = 1;
            put(&d->px[Y * d->w + X], rgba, (uint32_t)(sa * cover + 0.5), op);
        }
}

/* a polygon (pts: x0 y0 x1 y1 ...): filled by scanline (even-odd), or stroked (line > 0) along its edges; an open
   one (a path never closed, like a fishing line) has no edge back from the last point to the first */
static void polygon(Surf *d, const double *pts, int n, const Mat *m, uint32_t rgba, double alpha, double line, int op,
                    int open) {
    uint32_t sa = div255((rgba >> 24) * alpha_of(alpha));
    double xs[64], ys[64], lx = 1e9, ly = 1e9, hx = -1e9, hy = -1e9, pad = line / 2 + 1;
    int i, j, X, Y, x0, y0, x1, y1;
    if (n < 2 || n > 64 || !sa) return;
    for (i = 0; i < n; ++i) {
        xs[i] = m->a * pts[2 * i] + m->c * pts[2 * i + 1] + m->e;
        ys[i] = m->b * pts[2 * i] + m->d * pts[2 * i + 1] + m->f;
        lx = xs[i] < lx ? xs[i] : lx; hx = xs[i] > hx ? xs[i] : hx;
        ly = ys[i] < ly ? ys[i] : ly; hy = ys[i] > hy ? ys[i] : hy;
    }
    x0 = clampi((int)floor(lx - pad), 0, d->w); x1 = clampi((int)ceil(hx + pad), 0, d->w);
    y0 = clampi((int)floor(ly - pad), 0, d->h); y1 = clampi((int)ceil(hy + pad), 0, d->h);
    if (x0 >= x1 || y0 >= y1) return;
    if (line <= 0) {
        /* each pixel row: where its centre line crosses the edges, sorted; a pixel is in between the 1st and 2nd,
           3rd and 4th ... crossing (the same pixels as testing every pixel against every edge) */
        for (Y = y0; Y < y1; ++Y) {
            double py = Y + 0.5, cx[64], v;
            int nc = 0, k;
            for (i = 0, j = n - 1; i < n; j = i++)
                if ((ys[i] > py) != (ys[j] > py)) cx[nc++] = (xs[j] - xs[i]) * (py - ys[i]) / (ys[j] - ys[i]) + xs[i];
            for (i = 1; i < nc; ++i) {
                v = cx[i];
                for (k = i; k > 0 && cx[k - 1] > v; --k) cx[k] = cx[k - 1];
                cx[k] = v;
            }
            for (k = 0; k + 1 < nc; k += 2) {
                int a = clampi((int)ceil(cx[k] - 0.5), x0, x1), b = clampi((int)ceil(cx[k + 1] - 0.5), x0, x1);
                for (X = a; X < b; ++X) put(&d->px[Y * d->w + X], rgba, sa, op);
            }
        }
    } else {
        /* how much each pixel is covered, edge by edge over the edge's own box (the strongest edge wins, so the
           corners are not drawn twice), then blended once */
        int bw = x1 - x0, bh = y1 - y0, e;
        uint8_t *mask = (uint8_t *)calloc((size_t)bw * bh, 1);
        if (!mask) return;
        for (e = open ? 1 : 0; e < n; ++e) {
            int a = e ? e - 1 : n - 1, ex0, ex1, ey0, ey1;
            double ax = xs[a], ay = ys[a], ex = xs[e] - ax, ey = ys[e] - ay, l2 = ex * ex + ey * ey;
            ex0 = clampi((int)floor((ax < xs[e] ? ax : xs[e]) - pad), x0, x1);
            ex1 = clampi((int)ceil((ax > xs[e] ? ax : xs[e]) + pad), x0, x1);
            ey0 = clampi((int)floor((ay < ys[e] ? ay : ys[e]) - pad), y0, y1);
            ey1 = clampi((int)ceil((ay > ys[e] ? ay : ys[e]) + pad), y0, y1);
            for (Y = ey0; Y < ey1; ++Y)
                for (X = ex0; X < ex1; ++X) {
                    double px = X + 0.5, py = Y + 0.5, t, qx, qy, cover;
                    uint8_t *mk = &mask[(Y - y0) * bw + (X - x0)];
                    unsigned c;
                    t = l2 > 0 ? ((px - ax) * ex + (py - ay) * ey) / l2 : 0;
                    t = t < 0 ? 0 : t > 1 ? 1 : t;
                    qx = ax + t * ex - px; qy = ay + t * ey - py;
                    cover = line / 2 - sqrt(qx * qx + qy * qy) + 0.5;
                    if (cover <= 0) continue;
                    c = cover >= 1 ? 255 : (unsigned)(cover * 255 + 0.5);
                    if (c > *mk) *mk = (uint8_t)c;
                }
        }
        for (Y = y0; Y < y1; ++Y)
            for (X = x0; X < x1; ++X) {
                unsigned c = mask[(Y - y0) * bw + (X - x0)];
                if (c) put(&d->px[Y * d->w + X], rgba, c == 255 ? sa : div255(sa * c), op);
            }
        free(mask);
    }
}

/* ---------------------------------------------------------------- text */

static Font *font_of(int size, int bold) {
    char rel[64], *text, *line, *save = 0;
    Font *f;
    Surf *atlas;
    int i;
    if (size < 8) size = 8;
    if (size > 40) size = 40;
    for (i = 0; i < n_fonts; ++i) if (fonts[i]->size == size && fonts[i]->bold == bold) return fonts[i]->loaded ? fonts[i] : 0;
    if (n_fonts >= MAX_FONTS) return 0;
    f = fonts[n_fonts++] = (Font *)calloc(1, sizeof(Font));
    f->size = size; f->bold = bold;
    snprintf(rel, sizeof rel, "font/%d%s.hli", size, bold ? "b" : "r");
    atlas = load_hli(rel);
    snprintf(rel, sizeof rel, "font/%d%s.txt", size, bold ? "b" : "r");
    text = (char *)read_file(rel, 0);
    if (!atlas || !text) { printf("no font %s\n", rel); free(text); return 0; }
    f->atlas = *atlas;
    free(atlas);
    {
        int n = 0;
        for (line = strtok_r(text, "\n", &save); line; line = strtok_r(0, "\n", &save)) {
            int cp, x, y, w, h, l, adv, top;
            if (sscanf(line, "metrics %d %d", &f->ascent, &f->descent) == 2) continue;
            if (sscanf(line, "glyph %d %d %d %d %d %d %d %d", &cp, &x, &y, &w, &h, &l, &adv, &top) == 8 && cp < 0x3000 && n < MAX_GLYPHS) {
                f->g[n].x = (short)x; f->g[n].y = (short)y; f->g[n].w = (short)w; f->g[n].h = (short)h;
                f->g[n].l = (short)l; f->g[n].adv = (short)adv; f->g[n].top = (short)top;
                f->map[cp] = (uint16_t)++n;
            }
        }
    }
    free(text);
    f->loaded = 1;
    return f;
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

static int text_width(const Font *f, const char *s) {
    int w = 0;
    while (*s) {
        int c = utf8(&s), g = c < 0x3000 ? f->map[c] - 1 : -1;
        if (g >= 0) w += f->g[g].adv;
    }
    return w;
}

/* fillText (stroke 0) or strokeText (stroke = lineWidth): align 0 left 1 center 2 right, base 0 alphabetic
   1 middle 2 top; only the transform's move is used (the page never draws text scaled) */
static void draw_text(Surf *d, const char *s, double x, double y, const Mat *m, int size, int bold, int align, int base,
                      uint32_t rgba, double alpha, double stroke) {
    Font *f = font_of(size, bold);
    uint32_t sa = div255((rgba >> 24) * alpha_of(alpha));
    int pen, top, r = (int)ceil(stroke / 2), ox, oy;
    if (!f || !sa) return;
    pen = (int)floor(m->a * x + m->c * y + m->e + 0.5);
    top = (int)floor(m->b * x + m->d * y + m->f + 0.5);
    if (align == 1) pen -= text_width(f, s) / 2; else if (align == 2) pen -= text_width(f, s);
    if (base == 1) top -= (f->ascent + f->descent) / 2; else if (base == 0) top -= f->ascent;
    while (*s) {
        int c = utf8(&s), g = c < 0x3000 ? f->map[c] - 1 : -1, i, j;
        if (g < 0) continue;
        for (oy = -r; oy <= r; ++oy)
            for (ox = -r; ox <= r; ++ox) {
                if (stroke > 0 ? ox * ox + oy * oy > (stroke / 2) * (stroke / 2) + 0.5 : (ox || oy)) continue;
                for (j = 0; j < f->g[g].h; ++j)
                    for (i = 0; i < f->g[g].w; ++i) {
                        uint32_t a = f->atlas.px[(f->g[g].y + j) * f->atlas.w + f->g[g].x + i] >> 24;
                        int X = pen + f->g[g].l + i + ox, Y = top + f->g[g].top + j + oy;
                        if (a && X >= 0 && Y >= 0 && X < d->w && Y < d->h) put(&d->px[Y * d->w + X], rgba, div255(a * sa), OP_OVER);
                    }
            }
        pen += f->g[g].adv;
    }
}

/* ---------------------------------------------------------------- sound */

static int sound_of(const char *name) {
    int i;
    for (i = 0; i < n_sounds; ++i) if (!strcmp(sounds[i].name, name)) return i;
    return -1;
}

/* real milliseconds (also in the test harness): long reads and writes are named in the log */
static double clock_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1e3 + ts.tv_nsec / 1e6;
}
/* a .wav's samples (22050 Hz mono 16-bit, make_sfx_8bit.py), malloc'd, and how many; 0 if it cannot be read */
static int16_t *read_wav(const char *rel, int *samples) {
    long len, p = 12;
    double t0 = clock_ms();
    uint8_t *b = read_file(rel, &len);
    if (clock_ms() - t0 > 200) printf("slow: sound %s took %.0f ms\n", rel, clock_ms() - t0);
    if (!b || len < 44 || memcmp(b, "RIFF", 4)) { free(b); return 0; }
    while (p + 8 <= len) {
        long size = b[p + 4] | b[p + 5] << 8 | b[p + 6] << 16 | (long)b[p + 7] << 24;
        if (!memcmp(b + p, "data", 4)) {
            int16_t *d;
            if (size > len - p - 8) size = len - p - 8;
            d = (int16_t *)malloc((size_t)size + 2);
            if (d) { memcpy(d, b + p + 8, (size_t)size); *samples = (int)(size / 2); }
            free(b);
            return d;
        }
        p += 8 + size + (size & 1);
    }
    free(b);
    return 0;
}

static int load_sound(const char *rel, const char *name) {
    int k = sound_of(name), n = 0;
    int16_t *d;
    if (k >= 0) return k;                    /* already in memory: the card is read only the first time */
    if (n_sounds >= MAX_SOUNDS || !(d = read_wav(rel, &n))) return -1;
    snprintf(sounds[n_sounds].name, sizeof sounds[n_sounds].name, "%s", name);
    sounds[n_sounds].data = d;
    sounds[n_sounds].len = n;
    return n_sounds++;
}

/* the story's voice (game/src/giong.js): one line at a time on its own channel, read from the card each time it is
   said and given back once it has been said or another line has started (each line is heard about once, so
   keeping them, as the sounds are kept, would only fill memory). voice_new waits for jsrt_audio_commit */
static int16_t *voice_data, *voice_new;
static int voice_new_len, voice_next;       /* voice_next: 0 nothing, 1 say voice_new, 2 stop */

void jsrt_audio_commit(void) {
    int i, k;
    /* the voice: started or stopped, and a line no channel plays any more freed (the audio thread is locked) */
    if (voice_next) {
        chan[VOICE].d = 0;
        free(voice_data);
        voice_data = 0;
        if (voice_next == 1 && voice_new) {
            voice_data = voice_new;
            chan[VOICE].d = voice_data; chan[VOICE].len = voice_new_len;
            chan[VOICE].pos = 0; chan[VOICE].vol = 256; chan[VOICE].loop = 0;
        } else free(voice_new);
        voice_new = 0;
        voice_next = 0;
    } else if (voice_data && !chan[VOICE].d) { free(voice_data); voice_data = 0; }
    if (music_next == -2) chan[0].d = 0;
    else if (music_next >= 0) {
        chan[0].d = sounds[music_next].data; chan[0].len = sounds[music_next].len;
        chan[0].pos = 0; chan[0].loop = 1;
    }
    chan[0].vol = music_vol;                        /* Cài đặt's Nhạc nền, on the song playing too */
    music_next = -1;
    for (i = 0; i < n_pending; ++i) {
        int best = 1;
        for (k = 1; k < VOICE; ++k)                 /* a free channel, or the one nearest its end */
            if (!chan[k].d) { best = k; break; } else if (chan[k].len - chan[k].pos < chan[best].len - chan[best].pos) best = k;
        chan[best].d = sounds[pending[i].sound].data; chan[best].len = sounds[pending[i].sound].len;
        chan[best].pos = 0; chan[best].vol = pending[i].vol; chan[best].loop = 0;
    }
    n_pending = 0;
}

void jsrt_audio(int16_t *out, int n) {
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

/* ---------------------------------------------------------------- bindings */

#define ARG_D(i) double_arg(ctx, argc, argv, i)
#define ARG_I(i) ((int)double_arg(ctx, argc, argv, i))
static double double_arg(JSContext *ctx, int argc, JSValueConst *argv, int i) {
    double v = 0;
    if (i < argc) JS_ToFloat64(ctx, &v, argv[i]);
    return v;
}
static uint32_t u32_arg(JSContext *ctx, int argc, JSValueConst *argv, int i) {
    uint32_t v = 0;
    if (i < argc) JS_ToUint32(ctx, &v, argv[i]);
    return v;
}
/* the slot of an id still in use, else -1 (a freed picture's id, or nonsense) */
static int slot_of(int id) {
    int k = id & (MAX_SURF - 1);
    if (id < 0 || k >= n_surf || !surf[k] || (unsigned)id >> SLOT_BITS != slot_gen[k]) return -1;
    return k;
}
static Surf *surf_arg(JSContext *ctx, int argc, JSValueConst *argv, int i) {
    int k = slot_of((int)double_arg(ctx, argc, argv, i));
    return k >= 0 ? surf[k] : 0;
}
/* a new picture in a free slot (one given back by free() first): its id, or -1 when all are taken */
static int surf_add(Surf *s) {
    int k;
    if (n_free) k = free_slot[--n_free];
    else if (n_surf < MAX_SURF) k = n_surf++;
    else return -1;
    surf[k] = s;
    return k | slot_gen[k] << SLOT_BITS;
}
static Mat mat_args(JSContext *ctx, int argc, JSValueConst *argv, int i) {
    Mat m;
    m.a = ARG_D(i); m.b = ARG_D(i + 1); m.c = ARG_D(i + 2); m.d = ARG_D(i + 3); m.e = ARG_D(i + 4); m.f = ARG_D(i + 5);
    return m;
}

static JSValue b_now(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    (void)t; (void)argc; (void)argv;
    return JS_NewFloat64(ctx, now_ms);
}
/* clock(): real milliseconds, also in the test harness (whose now() is the frame clock): for timing code */
static JSValue b_clock(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    struct timespec ts;
    (void)t; (void)argc; (void)argv;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return JS_NewFloat64(ctx, ts.tv_sec * 1e3 + ts.tv_nsec / 1e6);
}
static JSValue b_pad(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    (void)t; (void)argc; (void)argv;
    return JS_NewInt32(ctx, (int32_t)pad_bits);
}
static JSValue b_log(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    const char *s = argc ? JS_ToCString(ctx, argv[0]) : 0;
    (void)t;
    if (s) { printf("js: %s\n", s); JS_FreeCString(ctx, s); }
    return JS_UNDEFINED;
}
static JSValue b_new_canvas(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    Surf *s = surf_new(ARG_I(0), ARG_I(1));
    int id = surf_add(s);
    (void)t;
    if (id < 0) { free(s->px); free(s); return JS_ThrowInternalError(ctx, "too many canvases"); }
    return JS_NewInt32(ctx, id);
}
/* free(id): give a canvas's or picture's pixels and its slot back (Solo đối kháng frees a match's frames when it
   ends); the screen (0) is never freed, and an id freed already is left alone */
static JSValue b_free(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    int k = slot_of(ARG_I(0));
    (void)t;
    if (k > 0) {
        free(surf[k]->px); free(surf[k]); surf[k] = 0;
        slot_gen[k] = (uint16_t)((slot_gen[k] + 1) & 0xFFFF);
        free_slot[n_free++] = k;
    }
    return JS_UNDEFINED;
}
static JSValue b_resize(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    Surf *s = surf_arg(ctx, argc, argv, 0);
    int w = ARG_I(1), h = ARG_I(2);
    (void)t;
    if (s) {                                   /* like a canvas: setting the size clears it */
        w = w < 0 ? 0 : w;
        h = h < 0 ? 0 : h;
        if (w * h > s->w * s->h) { free(s->px); s->px = (uint32_t *)calloc((size_t)(w * h) + 1, 4); }
        else memset(s->px, 0, (size_t)(w * h) * 4);
        s->w = w; s->h = h; s->opaque = 0;
    }
    return JS_UNDEFINED;
}
/* seal(id): a canvas that will not change any more is checked for see-through pixels; with none, drawing it
   1:1 is a plain copy of rows (as a background picture is) */
static JSValue b_seal(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    Surf *s = surf_arg(ctx, argc, argv, 0);
    int i, n;
    (void)t;
    if (!s) return JS_FALSE;
    for (s->opaque = 1, i = 0, n = s->w * s->h; i < n && s->opaque; ++i) s->opaque = s->px[i] >> 24 == 255;
    return JS_NewBool(ctx, s->opaque);
}
static JSValue b_load_image(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    const char *path = argc ? JS_ToCString(ctx, argv[0]) : 0;
    double t0 = clock_ms();
    Surf *s = path ? load_hli(path) : 0;
    JSValue r;
    int id;
    if (path && clock_ms() - t0 > 200) printf("slow: picture %s took %.0f ms\n", path, clock_ms() - t0);
    (void)t;
    if (!s) { if (path) { printf("missing picture %s\n", path); JS_FreeCString(ctx, path); } return JS_NULL; }
    JS_FreeCString(ctx, path);
    if ((id = surf_add(s)) < 0) { printf("too many pictures\n"); free(s->px); free(s); return JS_NULL; }
    r = JS_NewArray(ctx);
    JS_SetPropertyUint32(ctx, r, 0, JS_NewInt32(ctx, id));
    JS_SetPropertyUint32(ctx, r, 1, JS_NewInt32(ctx, s->w));
    JS_SetPropertyUint32(ctx, r, 2, JS_NewInt32(ctx, s->h));
    return r;
}
/* fillRect(id, x, y, w, h, a, b, c, d, e, f, rgba, alpha, op) */
static JSValue b_fill_rect(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    Surf *s = surf_arg(ctx, argc, argv, 0);
    Mat m = mat_args(ctx, argc, argv, 5);
    (void)t;
    if (s) fill_rect(s, ARG_D(1), ARG_D(2), ARG_D(3), ARG_D(4), &m, u32_arg(ctx, argc, argv, 11), ARG_D(12), ARG_I(13),
                     argc > 14 ? ARG_I(14) : 0);
    return JS_UNDEFINED;
}
/* drawImage(dst, src, sx, sy, sw, sh, dx, dy, dw, dh, a, b, c, d, e, f, alpha, op, shadowRgba, shadowBlur,
             brightness, saturate) */
static JSValue b_draw_image(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    Surf *d = surf_arg(ctx, argc, argv, 0), *s = surf_arg(ctx, argc, argv, 1);
    Mat m = mat_args(ctx, argc, argv, 10);
    (void)t;
    set_filter(argc > 20 ? ARG_D(20) : 1, argc > 21 ? ARG_D(21) : 1);
    if (d && s && d != s)
        draw_image(d, s, ARG_D(2), ARG_D(3), ARG_D(4), ARG_D(5), ARG_D(6), ARG_D(7), ARG_D(8), ARG_D(9), &m,
                   ARG_D(16), ARG_I(17), u32_arg(ctx, argc, argv, 18), ARG_D(19));
    filter_on = 0;
    return JS_UNDEFINED;
}
/* ellipse(id, cx, cy, rx, ry, a, b, c, d, e, f, rgba, alpha, line, op) */
static JSValue b_ellipse(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    Surf *s = surf_arg(ctx, argc, argv, 0);
    Mat m = mat_args(ctx, argc, argv, 5);
    (void)t;
    if (s) ellipse(s, ARG_D(1), ARG_D(2), ARG_D(3), ARG_D(4), &m, u32_arg(ctx, argc, argv, 11), ARG_D(12), ARG_D(13), ARG_I(14));
    return JS_UNDEFINED;
}
/* text(id, str, x, y, a, b, c, d, e, f, size, bold, align, base, rgba, alpha, stroke) */
static JSValue b_text(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    Surf *s = surf_arg(ctx, argc, argv, 0);
    const char *str = argc > 1 ? JS_ToCString(ctx, argv[1]) : 0;
    Mat m = mat_args(ctx, argc, argv, 4);
    (void)t;
    if (s && str) draw_text(s, str, ARG_D(2), ARG_D(3), &m, ARG_I(10), ARG_I(11), ARG_I(12), ARG_I(13),
                            u32_arg(ctx, argc, argv, 14), ARG_D(15), ARG_D(16));
    if (str) JS_FreeCString(ctx, str);
    return JS_UNDEFINED;
}
/* poly(id, [x0, y0, ...], a, b, c, d, e, f, rgba, alpha, line, op, open) */
static JSValue b_poly(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    Surf *s = surf_arg(ctx, argc, argv, 0);
    Mat m = mat_args(ctx, argc, argv, 2);
    double pts[128];
    int n = 0, i;
    (void)t;
    if (!s || argc < 12) return JS_UNDEFINED;
    for (i = 0; i < 128; ++i) {
        JSValue v = JS_GetPropertyUint32(ctx, argv[1], (uint32_t)i);
        if (JS_IsUndefined(v)) break;
        JS_ToFloat64(ctx, &pts[i], v);
        JS_FreeValue(ctx, v);
        n = i + 1;
    }
    polygon(s, pts, n / 2, &m, u32_arg(ctx, argc, argv, 8), ARG_D(9), ARG_D(10), ARG_I(11), ARG_I(12));
    return JS_UNDEFINED;
}
/* pixels(id, x, y, w, h) -> ArrayBuffer of RGBA bytes (getImageData); outside the picture reads as 0 */
static JSValue b_pixels(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    Surf *s = surf_arg(ctx, argc, argv, 0);
    int x = ARG_I(1), y = ARG_I(2), w = ARG_I(3), h = ARG_I(4), X, Y;
    uint8_t *b;
    JSValue r;
    (void)t;
    if (w <= 0 || h <= 0 || w > 4096 || h > 4096) return JS_NULL;
    b = (uint8_t *)calloc((size_t)w * h, 4);
    if (!b) return JS_NULL;
    if (s)
        for (Y = 0; Y < h; ++Y)
            for (X = 0; X < w; ++X) {
                int sx = x + X, sy = y + Y;
                uint32_t p;
                uint8_t *o = b + 4 * ((size_t)Y * w + X);
                if (sx < 0 || sy < 0 || sx >= s->w || sy >= s->h) continue;
                p = s->px[sy * s->w + sx];
                o[0] = (uint8_t)(p >> 16); o[1] = (uint8_t)(p >> 8); o[2] = (uint8_t)p; o[3] = (uint8_t)(p >> 24);
            }
    r = JS_NewArrayBufferCopy(ctx, b, (size_t)w * h * 4);
    free(b);
    return r;
}
/* put(id, x, y, w, h, bytes): RGBA bytes (getImageData's layout) written over the surface, as putImageData does */
static JSValue b_put(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    Surf *s = surf_arg(ctx, argc, argv, 0);
    int x = ARG_I(1), y = ARG_I(2), w = ARG_I(3), h = ARG_I(4), X, Y;
    size_t n = 0;
    uint8_t *b = argc > 5 ? JS_GetArrayBuffer(ctx, &n, argv[5]) : 0;
    (void)t;
    if (!s || !b || w <= 0 || h <= 0 || n < (size_t)w * h * 4) return JS_UNDEFINED;
    for (Y = 0; Y < h; ++Y)
        for (X = 0; X < w; ++X) {
            int dx = x + X, dy = y + Y;
            const uint8_t *i = b + 4 * ((size_t)Y * w + X);
            if (dx < 0 || dy < 0 || dx >= s->w || dy >= s->h) continue;
            s->px[dy * s->w + dx] = (uint32_t)i[3] << 24 | (uint32_t)i[0] << 16 | (uint32_t)i[1] << 8 | i[2];
            if (i[3] != 255) s->opaque = 0;
        }
    return JS_UNDEFINED;
}
/* files under the game folder (or the save folder, by full path): readText(path) -> string or null,
   writeText(path, text) -> true when written (through a temporary file, so a save is never left half done) */
static JSValue b_read_text(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    const char *path = argc ? JS_ToCString(ctx, argv[0]) : 0;
    char full[1024];
    FILE *f;
    JSValue r = JS_NULL;
    (void)t;
    if (!path) return JS_NULL;
    snprintf(full, sizeof full, "%s%s%s", path[0] == '/' ? "" : root, path[0] == '/' ? "" : "/", path);
    f = fopen(full, "rb");
    if (f) {
        long n;
        char *b;
        fseek(f, 0, SEEK_END); n = ftell(f); fseek(f, 0, SEEK_SET);
        b = (char *)malloc((size_t)n + 1);
        if (b && fread(b, 1, (size_t)n, f) == (size_t)n) r = JS_NewStringLen(ctx, b, (size_t)n);
        free(b);
        fclose(f);
    }
    JS_FreeCString(ctx, path);
    return r;
}
/* writing files on a thread of its own: an SD card stops now and then (its own housekeeping; up to seconds on the
   handhelds), and a save written in the frame stopped the game with it. The newest text for a file wins; quitting
   waits for the writes left (writer_flush in jsrt_shutdown) */
static pthread_mutex_t wr_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t wr_wake = PTHREAD_COND_INITIALIZER, wr_idle = PTHREAD_COND_INITIALIZER;
static char wr_path[1024], *wr_text;
static size_t wr_len;
static int wr_started, wr_busy;

static int write_file_now(const char *full, const char *text, size_t len) {
    char tmp[1100];
    FILE *f;
    int ok = 0;
    double t0 = clock_ms();
    snprintf(tmp, sizeof tmp, "%s.tmp", full);
    f = fopen(tmp, "wb");
    if (f) {
        ok = fwrite(text, 1, len, f) == len;
        ok = fclose(f) == 0 && ok;
        ok = ok && rename(tmp, full) == 0;
    }
    if (!ok) printf("could not write %s\n", full);
    if (clock_ms() - t0 > 200) printf("slow: writing %s took %.0f ms (on the writer thread)\n", full, clock_ms() - t0);
    return ok;
}
static void *writer(void *arg) {
    (void)arg;
    pthread_mutex_lock(&wr_lock);
    for (;;) {
        while (!wr_text) pthread_cond_wait(&wr_wake, &wr_lock);
        {
            char path[1024];
            char *text = wr_text;
            size_t len = wr_len;
            snprintf(path, sizeof path, "%s", wr_path);
            wr_text = 0; wr_busy = 1;
            pthread_mutex_unlock(&wr_lock);
            write_file_now(path, text, len);
            free(text);
            pthread_mutex_lock(&wr_lock);
            wr_busy = 0;
            if (!wr_text) pthread_cond_broadcast(&wr_idle);
        }
    }
    return 0;
}
static int write_later(const char *full, const char *text, size_t len) {
    char *copy = (char *)malloc(len + 1);
    if (!copy) return write_file_now(full, text, len);
    memcpy(copy, text, len);
    pthread_mutex_lock(&wr_lock);
    if (!wr_started) {
        pthread_t th;
        wr_started = pthread_create(&th, 0, writer, 0) == 0 ? 1 : -1;
        if (wr_started == 1) pthread_detach(th);
    }
    if (wr_started != 1) { pthread_mutex_unlock(&wr_lock); free(copy); return write_file_now(full, text, len); }
    if (wr_text && strcmp(wr_path, full)) {          /* another file still waiting: written first, here */
        char *old = wr_text; size_t ol = wr_len; char op[1024];
        snprintf(op, sizeof op, "%s", wr_path); wr_text = 0;
        pthread_mutex_unlock(&wr_lock);
        write_file_now(op, old, ol); free(old);
        pthread_mutex_lock(&wr_lock);
    }
    free(wr_text);                                   /* a newer text for the same file replaces the waiting one */
    snprintf(wr_path, sizeof wr_path, "%s", full);
    wr_text = copy; wr_len = len;
    pthread_cond_signal(&wr_wake);
    pthread_mutex_unlock(&wr_lock);
    return 1;
}
static void writer_flush(void) {
    pthread_mutex_lock(&wr_lock);
    while (wr_started == 1 && (wr_text || wr_busy)) pthread_cond_wait(&wr_idle, &wr_lock);
    pthread_mutex_unlock(&wr_lock);
}

static JSValue b_write_text(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    const char *path = argc > 1 ? JS_ToCString(ctx, argv[0]) : 0;
    size_t len = 0;
    const char *text = path ? JS_ToCStringLen(ctx, &len, argv[1]) : 0;
    char full[1024];
    int ok = 0;
    (void)t;
    if (path && text) {
        snprintf(full, sizeof full, "%s%s%s", path[0] == '/' ? "" : root, path[0] == '/' ? "" : "/", path);
        ok = test_mode ? write_file_now(full, text, len) : write_later(full, text, len);
    }
    if (text) JS_FreeCString(ctx, text);
    if (path) JS_FreeCString(ctx, path);
    return JS_NewBool(ctx, ok);
}
static JSValue b_measure(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    const char *str = argc ? JS_ToCString(ctx, argv[0]) : 0;
    Font *f = font_of(ARG_I(1), ARG_I(2));
    int w = str && f ? text_width(f, str) : 0;
    (void)t;
    if (str) JS_FreeCString(ctx, str);
    return JS_NewInt32(ctx, w);
}
/* holua.sfx(name, volume 0..256), holua.music(name or '') */
static JSValue b_sfx(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    const char *name = argc ? JS_ToCString(ctx, argv[0]) : 0;
    (void)t;
    if (name) {
        char rel[96];
        int k;
        snprintf(rel, sizeof rel, "sfx/%s.wav", name);
        k = load_sound(rel, name);
        if (k >= 0 && n_pending < 16) { pending[n_pending].sound = k; pending[n_pending].vol = argc > 1 ? ARG_I(1) : 230; n_pending++; }
        JS_FreeCString(ctx, name);
    }
    return JS_UNDEFINED;
}
/* holua.voice(name under sfx/, or '' to stop): the line before stops either way */
static JSValue b_voice(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    const char *name = argc ? JS_ToCString(ctx, argv[0]) : 0;
    (void)t;
    free(voice_new);                         /* one asked for this frame already: never started */
    voice_new = 0;
    voice_next = 2;
    if (name && *name) {
        char rel[96];
        snprintf(rel, sizeof rel, "sfx/%s.wav", name);
        if ((voice_new = read_wav(rel, &voice_new_len)) != 0) voice_next = 1;
    }
    if (name) JS_FreeCString(ctx, name);
    return JS_UNDEFINED;
}
static JSValue b_music(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    const char *name = argc ? JS_ToCString(ctx, argv[0]) : 0;
    (void)t;
    if (name && *name) {
        char rel[96], key[48];
        snprintf(rel, sizeof rel, "nhac/%s.wav", name);
        snprintf(key, sizeof key, "nhac-%s", name);     /* music and chimes may share a file name */
        music_next = load_sound(rel, key);
        if (music_next < 0) music_next = -2;
    } else music_next = -2;
    if (name) JS_FreeCString(ctx, name);
    return JS_UNDEFINED;
}

/* holua.musicVol(0..256): the music's loudness (Cài đặt -> Nhạc nền), the sounds and the voice as they are */
static JSValue b_music_vol(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    int v = argc ? ARG_I(0) : 140;
    (void)t;
    music_vol = v < 0 ? 0 : v > 256 ? 256 : v;
    return JS_UNDEFINED;
}

static void print_exception(void) {
    JSValue e = JS_GetException(jc), stack;
    const char *s = JS_ToCString(jc, e);
    printf("js error: %s\n", s ? s : "?");
    if (s) JS_FreeCString(jc, s);
    stack = JS_GetPropertyStr(jc, e, "stack");
    if (!JS_IsUndefined(stack)) {
        const char *st = JS_ToCString(jc, stack);
        if (st) { printf("%s\n", st); JS_FreeCString(jc, st); }
    }
    JS_FreeValue(jc, stack);
    JS_FreeValue(jc, e);
}

static void run_jobs(void) {
    JSContext *c;
    int r;
    while ((r = JS_ExecutePendingJob(rt, &c)) != 0)
        if (r < 0) print_exception();
}

static int run_file(const char *rel) {
    long len;
    char *src = (char *)read_file(rel, &len);
    JSValue v;
    if (!src) { printf("missing %s\n", rel); return 0; }
    v = JS_Eval(jc, src, (size_t)len, rel, JS_EVAL_TYPE_GLOBAL);
    free(src);
    if (JS_IsException(v)) { print_exception(); return 0; }
    JS_FreeValue(jc, v);
    run_jobs();
    return 1;
}

/* the game's own "Thoát game" (game/src/man-chao.js): the program ends after this frame, through jsrt_quit like
   SELECT + START */
static int exit_asked;
static JSValue b_exit(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    (void)ctx; (void)t; (void)argc; (void)argv;
    exit_asked = 1;
    return JS_UNDEFINED;
}
int jsrt_wants_exit(void) { return exit_asked; }

/* exists(path): a file of the game folder is there (js/shim.js looks for a picture's drawn wide version) */
static JSValue b_exists(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    const char *rel = argc ? JS_ToCString(ctx, argv[0]) : 0;
    char path[1024];
    struct stat st;
    int ok;
    (void)t;
    if (!rel) return JS_FALSE;
    snprintf(path, sizeof path, "%s/%s", root, rel);
    JS_FreeCString(ctx, rel);
    ok = stat(path, &st) == 0;
    return JS_NewBool(ctx, ok);
}

static int screen_w = JS_SCREEN_W;
void jsrt_set_screen_w(int w) {
    if (w < JS_SCREEN_W) w = JS_SCREEN_W;
    if (w > JS_SCREEN_MAX_W) w = JS_SCREEN_MAX_W;
    screen_w = w & ~1;
}
int jsrt_screen_w(void) { return screen_w; }

/* the in-device update (Cài đặt -> Cập nhật): ota("check") or ota("get") starts ota.sh beside the game in the
   background (its output in .ota/log.txt); the game reads .ota/state to follow it. -> true when started */
static JSValue b_ota(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    const char *what = argc ? JS_ToCString(ctx, argv[0]) : 0;
    char cmd[1400];
    int ok = 0;
    (void)t;
    if (what && (!strcmp(what, "check") || !strcmp(what, "get"))) {
        snprintf(cmd, sizeof cmd, "cd '%s' && mkdir -p .ota && [ -f ota.sh ] && (sh ./ota.sh %s </dev/null >>.ota/log.txt 2>&1 &)",
                 root, what);
        ok = system(cmd) == 0;
    }
    if (what) JS_FreeCString(ctx, what);
    return JS_NewBool(ctx, ok);
}

/* Elemon online (game/src/dau-online.js): net(id, "GET"|"POST", path, body) asks the server through mang.sh beside
   the game (curl, else wget). A thread of its own writes .mang/<id>.req and runs the script, so neither the card nor
   the wifi ever holds a frame up; the game reads .mang/<id>.st (written last) and .mang/<id>.res. -> true when
   started. id: [a-z0-9] only, path: [A-Za-z0-9/_.?=&-] only (they reach the shell) */
typedef struct { char id[24], method[8], path[256], *body; size_t len; } NetJob;
static void *net_job(void *arg) {
    NetJob *j = (NetJob *)arg;
    char full[1400], cmd[1800];
    snprintf(full, sizeof full, "%s/.mang", root);
    mkdir(full, 0755);
    snprintf(full, sizeof full, "%s/.mang/%s.req", root, j->id);
    if (write_file_now(full, j->body, j->len)) {
        snprintf(cmd, sizeof cmd, "cd '%s' && [ -f mang.sh ] && sh ./mang.sh %s '%s' %s </dev/null >>.mang/log.txt 2>&1",
                 root, j->method, j->path, j->id);
        if (system(cmd) != 0) printf("net: mang.sh %s failed\n", j->path);
    }
    free(j->body); free(j);
    return 0;
}
static int net_safe(const char *s, const char *ok) {
    for (; *s; ++s)
        if (!((*s >= 'a' && *s <= 'z') || (*s >= 'A' && *s <= 'Z') || (*s >= '0' && *s <= '9') || (*ok && strchr(ok, *s))))
            return 0;
    return 1;
}
static JSValue b_net(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    const char *id = argc > 2 ? JS_ToCString(ctx, argv[0]) : 0, *method = id ? JS_ToCString(ctx, argv[1]) : 0,
               *path = method ? JS_ToCString(ctx, argv[2]) : 0, *body = 0;
    size_t len = 0;
    int ok = 0;
    (void)t;
    if (path && argc > 3) body = JS_ToCStringLen(ctx, &len, argv[3]);
    if (path && *id && strlen(id) < 24 && net_safe(id, "") && (!strcmp(method, "GET") || !strcmp(method, "POST")) &&
        strlen(path) < 256 && net_safe(path, "/_.?=&-")) {
        NetJob *j = (NetJob *)calloc(1, sizeof *j);
        pthread_t th;
        pthread_attr_t at;
        if (j) {
            snprintf(j->id, sizeof j->id, "%s", id); snprintf(j->method, sizeof j->method, "%s", method);
            snprintf(j->path, sizeof j->path, "%s", path);
            j->len = body ? len : 0;
            j->body = (char *)malloc(j->len + 1);
            if (j->body) {
                if (j->len) memcpy(j->body, body, j->len);
                pthread_attr_init(&at); pthread_attr_setdetachstate(&at, PTHREAD_CREATE_DETACHED);
                ok = pthread_create(&th, &at, net_job, j) == 0;
                pthread_attr_destroy(&at);
            }
            if (!ok) { free(j->body); free(j); }
        }
    }
    if (body) JS_FreeCString(ctx, body);
    if (path) JS_FreeCString(ctx, path);
    if (method) JS_FreeCString(ctx, method);
    if (id) JS_FreeCString(ctx, id);
    return JS_NewBool(ctx, ok);
}

/* Đấu qua wifi (game/src/dau-wifi.js): one UDP socket, never blocking a frame. udpOpen(port) binds it (0: any port,
   broadcasts allowed), udpSend(ip, port, text) sends one datagram (ip "*": the broadcast address of every network
   the handheld is on, and 255.255.255.255), udpRecv() -> [[ip, port, text], ...] all that came in since,
   udpClose(), myIp() -> the handheld's address on its network (or null) */
static int udp_fd = -1;
static JSValue b_udp_close(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    (void)ctx; (void)t; (void)argc; (void)argv;
    if (udp_fd >= 0) close(udp_fd);
    udp_fd = -1;
    return JS_UNDEFINED;
}
static JSValue b_udp_open(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    struct sockaddr_in a;
    int on = 1, port = argc ? ARG_I(0) : 0;
    (void)t;
    b_udp_close(ctx, t, 0, argv);
    udp_fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (udp_fd < 0) return JS_FALSE;
    setsockopt(udp_fd, SOL_SOCKET, SO_REUSEADDR, &on, sizeof on);
    setsockopt(udp_fd, SOL_SOCKET, SO_BROADCAST, &on, sizeof on);
    memset(&a, 0, sizeof a);
    a.sin_family = AF_INET; a.sin_addr.s_addr = htonl(INADDR_ANY); a.sin_port = htons((unsigned short)port);
    if (bind(udp_fd, (struct sockaddr *)&a, sizeof a) != 0 || fcntl(udp_fd, F_SETFL, fcntl(udp_fd, F_GETFL, 0) | O_NONBLOCK) != 0) {
        close(udp_fd); udp_fd = -1; return JS_FALSE;
    }
    return JS_TRUE;
}
static int udp_to(unsigned addr, int port, const char *s, size_t n) {
    struct sockaddr_in a;
    memset(&a, 0, sizeof a);
    a.sin_family = AF_INET; a.sin_addr.s_addr = addr; a.sin_port = htons((unsigned short)port);
    return sendto(udp_fd, s, n, 0, (struct sockaddr *)&a, sizeof a) == (ssize_t)n;
}
static JSValue b_udp_send(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    const char *ip = argc > 2 ? JS_ToCString(ctx, argv[0]) : 0, *s = 0;
    size_t n = 0;
    int port = argc > 2 ? ARG_I(1) : 0, ok = 0;
    (void)t;
    if (ip) s = JS_ToCStringLen(ctx, &n, argv[2]);
    if (udp_fd >= 0 && ip && s && port > 0 && n < 1400) {
        if (!strcmp(ip, "*")) {
            struct ifaddrs *ifs = 0, *i;
            ok = udp_to(htonl(INADDR_BROADCAST), port, s, n);
            if (getifaddrs(&ifs) == 0) {
                for (i = ifs; i; i = i->ifa_next)
                    if (i->ifa_addr && i->ifa_addr->sa_family == AF_INET && (i->ifa_flags & IFF_BROADCAST) && i->ifa_broadaddr &&
                        !(i->ifa_flags & IFF_LOOPBACK))
                        ok |= udp_to(((struct sockaddr_in *)i->ifa_broadaddr)->sin_addr.s_addr, port, s, n);
                freeifaddrs(ifs);
            }
        } else {
            struct in_addr ia;
            if (inet_pton(AF_INET, ip, &ia) == 1) ok = udp_to(ia.s_addr, port, s, n);
        }
    }
    if (s) JS_FreeCString(ctx, s);
    if (ip) JS_FreeCString(ctx, ip);
    return JS_NewBool(ctx, ok);
}
static JSValue b_udp_recv(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    JSValue out = JS_NewArray(ctx);
    char buf[1500], ip[INET_ADDRSTRLEN];
    int k = 0;
    (void)t; (void)argc; (void)argv;
    while (udp_fd >= 0 && k < 128) {
        struct sockaddr_in a;
        socklen_t al = sizeof a;
        ssize_t n = recvfrom(udp_fd, buf, sizeof buf, 0, (struct sockaddr *)&a, &al);
        JSValue row;
        if (n < 0) break;
        inet_ntop(AF_INET, &a.sin_addr, ip, sizeof ip);
        row = JS_NewArray(ctx);
        JS_SetPropertyUint32(ctx, row, 0, JS_NewString(ctx, ip));
        JS_SetPropertyUint32(ctx, row, 1, JS_NewInt32(ctx, ntohs(a.sin_port)));
        JS_SetPropertyUint32(ctx, row, 2, JS_NewStringLen(ctx, buf, (size_t)n));
        JS_SetPropertyUint32(ctx, out, (uint32_t)k++, row);
    }
    return out;
}
static JSValue b_my_ip(JSContext *ctx, JSValueConst t, int argc, JSValueConst *argv) {
    struct ifaddrs *ifs = 0, *i;
    char ip[INET_ADDRSTRLEN] = "";
    (void)t; (void)argc; (void)argv;
    if (getifaddrs(&ifs) != 0) return JS_NULL;
    for (i = ifs; i && !*ip; i = i->ifa_next)
        if (i->ifa_addr && i->ifa_addr->sa_family == AF_INET && !(i->ifa_flags & IFF_LOOPBACK) && (i->ifa_flags & IFF_UP))
            inet_ntop(AF_INET, &((struct sockaddr_in *)i->ifa_addr)->sin_addr, ip, sizeof ip);
    freeifaddrs(ifs);
    return *ip ? JS_NewString(ctx, ip) : JS_NULL;
}

int jsrt_init(const char *dir) {
    static const struct { const char *name; JSCFunction *f; int n; } fns[] = {
        { "now", b_now, 0 }, { "clock", b_clock, 0 }, { "pad", b_pad, 0 }, { "log", b_log, 1 }, { "newCanvas", b_new_canvas, 2 },
        { "resize", b_resize, 3 }, { "loadImage", b_load_image, 1 }, { "fillRect", b_fill_rect, 14 },
        { "drawImage", b_draw_image, 22 }, { "ellipse", b_ellipse, 15 }, { "text", b_text, 17 },
        { "measure", b_measure, 3 }, { "sfx", b_sfx, 2 }, { "music", b_music, 1 }, { "musicVol", b_music_vol, 1 }, { "voice", b_voice, 1 }, { "poly", b_poly, 13 }, { "pixels", b_pixels, 5 }, { "put", b_put, 6 }, { "free", b_free, 1 }, { "seal", b_seal, 1 },
        { "readText", b_read_text, 1 }, { "writeText", b_write_text, 2 }, { "exit", b_exit, 0 }, { "ota", b_ota, 1 }, { "exists", b_exists, 1 }, { "net", b_net, 4 },
        { "udpOpen", b_udp_open, 1 }, { "udpSend", b_udp_send, 3 }, { "udpRecv", b_udp_recv, 0 }, { "udpClose", b_udp_close, 0 },
        { "myIp", b_my_ip, 0 } };
    /* the scripts to run, in order: js/load.txt (one path a line, scripts/r36s_game.py), else the test page's set */
    static const char *scripts[] = { "js/shim.js", "js/data.js", "js/page.js", "js/am-thanh.js" };
    char *list, *line, *save = 0, save_dir[1200];
    const char *sd = getenv("HOLUA_SAVE_DIR");
    JSValue global, cv;
    unsigned i;
    snprintf(root, sizeof root, "%s", dir);
    surf[n_surf++] = surf_new(screen_w, JS_SCREEN_H);          /* canvas 0: the screen */
    for (i = 0; i < (unsigned)(screen_w * JS_SCREEN_H); ++i) surf[0]->px[i] = 0xFF000000u;
    rt = JS_NewRuntime();
    if (!rt) return 0;
    JS_SetMaxStackSize(rt, 1 << 20);
    jc = JS_NewContext(rt);
    if (!jc) return 0;
    global = JS_GetGlobalObject(jc);
    cv = JS_NewObject(jc);
    for (i = 0; i < sizeof fns / sizeof *fns; ++i)
        JS_SetPropertyStr(jc, cv, fns[i].name, JS_NewCFunction(jc, fns[i].f, fns[i].name, fns[i].n));
    {
        const char *t = getenv("HOLUA_TEST");
        test_mode = t && *t;
        no_fast = t && !strcmp(t, "slow");
    }
    JS_SetPropertyStr(jc, cv, "test", JS_NewBool(jc, test_mode));
    JS_SetPropertyStr(jc, cv, "screenW", JS_NewInt32(jc, screen_w));
    /* saves: HOLUA_SAVE_DIR (the launcher puts it next to the game folder, so a reinstall keeps it), else save/ */
    snprintf(save_dir, sizeof save_dir, "%s", sd && *sd ? sd : "save");
    if (save_dir[0] != '/') {
        char rel[600];
        snprintf(rel, sizeof rel, "%s", save_dir);
        snprintf(save_dir, sizeof save_dir, "%s/%s", root, rel);
    }
    mkdir(save_dir, 0755);
    JS_SetPropertyStr(jc, cv, "saveDir", JS_NewString(jc, save_dir));
    JS_SetPropertyStr(jc, global, "__cv", cv);
    JS_FreeValue(jc, global);
    list = (char *)read_file("js/load.txt", 0);
    if (list) {
        int ok = 1;
        for (line = strtok_r(list, "\r\n", &save); line && ok; line = strtok_r(0, "\r\n", &save))
            if (*line && *line != '#') ok = run_file(line);
        free(list);
        return ok;
    }
    for (i = 0; i < sizeof scripts / sizeof *scripts; ++i)
        if (!run_file(scripts[i])) return 0;
    return 1;
}

/* before quitting: the game's own __quit() (it saves) */
void jsrt_quit(void) {
    JSValue global = JS_GetGlobalObject(jc), f = JS_GetPropertyStr(jc, global, "__quit");
    if (JS_IsFunction(jc, f)) {
        JSValue r = JS_Call(jc, f, global, 0, 0);
        if (JS_IsException(r)) print_exception();
        JS_FreeValue(jc, r);
    }
    JS_FreeValue(jc, f);
    JS_FreeValue(jc, global);
}

void jsrt_mem(char *buf, int size) {
    double pics = 0, big = 0, snd = 0, fnt = 0;
    int np = 0, nb = 0, ns = 0, i;
    long rss = 0;
    FILE *f;
    for (i = 1; i < n_surf; ++i) if (surf[i] && surf[i]->w) {       /* 0 is the screen */
        double b = (double)surf[i]->w * surf[i]->h * 4;
        pics += b; ++np;
        if (b >= 512 * 1024) { big += b; ++nb; }                  /* the big ones: backdrops, atlases */
    }
    for (i = 0; i < n_sounds; ++i) { snd += sounds[i].len * 2.0; ++ns; }
    for (i = 0; i < n_fonts; ++i) fnt += (double)fonts[i]->atlas.w * fonts[i]->atlas.h * 4 + sizeof(Font);
    if ((f = fopen("/proc/self/statm", "r"))) { long pages; if (fscanf(f, "%*ld %ld", &pages) == 1) rss = pages * 4096; fclose(f); }
    snprintf(buf, (size_t)size, "mem: pictures %.0f MB (%d, of them %d over 0.5 MB: %.0f MB), sounds %.0f MB (%d), "
             "fonts %.0f MB, process %ld MB", pics / 1048576, np, nb, big / 1048576, snd / 1048576, ns,
             fnt / 1048576, rss / 1048576);
}

const uint32_t *jsrt_frame(double now, unsigned pad) {
    JSValue global = JS_GetGlobalObject(jc), f = JS_GetPropertyStr(jc, global, "__frame"), arg, r;
    now_ms = now;
    pad_bits = pad;
    arg = JS_NewFloat64(jc, now);
    r = JS_Call(jc, f, global, 1, &arg);
    if (JS_IsException(r)) print_exception();
    JS_FreeValue(jc, r);
    JS_FreeValue(jc, f);
    JS_FreeValue(jc, global);
    run_jobs();
    return surf[0]->px;
}

void jsrt_shutdown(void) {
    int i;
    writer_flush();                              /* the save written on quitting reaches the card first */
    if (jc) JS_FreeContext(jc);
    if (rt) JS_FreeRuntime(rt);
    jc = 0; rt = 0;
    for (i = 0; i < n_surf; ++i) if (surf[i]) { free(surf[i]->px); free(surf[i]); surf[i] = 0; }
    n_surf = n_free = 0;
    for (i = 0; i < n_fonts; ++i) { free(fonts[i]->atlas.px); free(fonts[i]); }
    n_fonts = 0;
    for (i = 0; i < n_sounds; ++i) free(sounds[i].data);
    n_sounds = 0;
    free(voice_data); free(voice_new);
    voice_data = voice_new = 0;
    voice_next = 0;
}
