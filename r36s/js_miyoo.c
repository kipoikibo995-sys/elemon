/* Elemon (the game) on the Miyoo Mini Plus (OnionOS or the stock firmware): screen, buttons, sound around jsrt.c,
   with no SDL. The screen is /dev/fb0 (640x480, 32 bits, turned 180 degrees: the picture is written back to front),
   the buttons are /dev/input/event0 (keys, as Onion's own apps read them), the sound is OSS /dev/dsp, which the
   firmware's libpadsp.so (LD_PRELOAD, packaging/miyoo/launch.sh) hands to its audioserver. Built with -DJSRT_LAZY
   (pictures read in when drawn, a budget kept: 128 MB of memory), by scripts/build-miyoo.ps1.
   Notes on the machine: packaging/miyoo/README.md. */
#include "jsrt.h"
#include <errno.h>
#include <fcntl.h>
#include <linux/fb.h>
#include <linux/input.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/soundcard.h>
#include <time.h>
#include <unistd.h>

static double now_ms(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1000.0 + t.tv_nsec / 1e6;
}

/* ---------------------------------------------------------------- screen */

static int fb = -1, fb_pages = 1, fb_page, fb_bpp, fb_stride, turn = 1;
static uint8_t *fb_mem;
static size_t fb_size;
static struct fb_var_screeninfo fb_old, fb_var;

static int screen_open(void) {
    struct fb_fix_screeninfo fix;
    if ((fb = open("/dev/fb0", O_RDWR)) < 0) { printf("no /dev/fb0: %s\n", strerror(errno)); return 0; }
    ioctl(fb, FBIOGET_VSCREENINFO, &fb_old);
    fb_var = fb_old;
    /* two pages one above the other: one shown while the next is written (FBIOPAN_DISPLAY) */
    fb_var.xres = fb_var.xres_virtual = JS_SCREEN_W;
    fb_var.yres = JS_SCREEN_H;
    fb_var.yres_virtual = JS_SCREEN_H * 2;
    fb_var.xoffset = fb_var.yoffset = 0;
    fb_var.bits_per_pixel = 32;
    if (ioctl(fb, FBIOPUT_VSCREENINFO, &fb_var) != 0) {
        fb_var = fb_old;
        fb_var.yoffset = 0;
        ioctl(fb, FBIOPUT_VSCREENINFO, &fb_var);
    }
    ioctl(fb, FBIOGET_VSCREENINFO, &fb_var);
    ioctl(fb, FBIOGET_FSCREENINFO, &fix);
    fb_bpp = (int)fb_var.bits_per_pixel;
    fb_stride = (int)fix.line_length;
    fb_pages = fb_var.yres_virtual >= 2 * fb_var.yres ? 2 : 1;
    fb_size = (size_t)fb_stride * fb_var.yres_virtual;
    if (fix.smem_len && fb_size > fix.smem_len) { fb_pages = 1; fb_size = (size_t)fb_stride * fb_var.yres; }
    fb_mem = (uint8_t *)mmap(0, fb_size, PROT_READ | PROT_WRITE, MAP_SHARED, fb, 0);
    if (fb_mem == MAP_FAILED) { printf("fb0 mmap: %s\n", strerror(errno)); fb_mem = 0; return 0; }
    printf("screen %ux%u, %d bits (red at %u), %d pages, line %d bytes%s\n", fb_var.xres, fb_var.yres, fb_bpp,
           fb_var.red.offset, fb_pages, fb_stride, turn ? ", turned 180" : "");
    if ((fb_bpp != 32 && fb_bpp != 16) || fb_var.xres < JS_SCREEN_W || fb_var.yres < JS_SCREEN_H) {
        printf("this screen is not one the game knows\n");
        return 0;
    }
    return 1;
}

/* the game's ARGB picture onto the page not shown, then that page shown */
static void screen_show(const uint32_t *px) {
    int page = fb_pages > 1 ? fb_page ^ 1 : 0, x, y;
    uint8_t *base = fb_mem + (size_t)page * fb_var.yres * fb_stride;
    for (y = 0; y < JS_SCREEN_H; ++y) {
        const uint32_t *src = px + (size_t)(turn ? JS_SCREEN_H - 1 - y : y) * JS_SCREEN_W;
        if (fb_bpp == 32) {
            uint32_t *d = (uint32_t *)(base + (size_t)y * fb_stride);
            if (turn) for (x = 0; x < JS_SCREEN_W; ++x) d[x] = src[JS_SCREEN_W - 1 - x] | 0xFF000000u;
            else for (x = 0; x < JS_SCREEN_W; ++x) d[x] = src[x] | 0xFF000000u;
        } else {
            uint16_t *d = (uint16_t *)(base + (size_t)y * fb_stride);
            for (x = 0; x < JS_SCREEN_W; ++x) {
                uint32_t c = src[turn ? JS_SCREEN_W - 1 - x : x];
                d[x] = (uint16_t)((c >> 8 & 0xF800) | (c >> 5 & 0x07E0) | (c >> 3 & 0x001F));
            }
        }
    }
    if (fb_pages > 1) {
        fb_var.yoffset = (unsigned)page * fb_var.yres;
        ioctl(fb, FBIOPAN_DISPLAY, &fb_var);
        fb_page = page;
    }
}

static void screen_close(void) {
    if (fb_mem) { memset(fb_mem, 0, fb_size); munmap(fb_mem, fb_size); }
    if (fb >= 0) { fb_old.yoffset = 0; ioctl(fb, FBIOPUT_VSCREENINFO, &fb_old); close(fb); }   /* the menu draws on page 0 */
}

/* ---------------------------------------------------------------- buttons */

/* the Mini Plus's keys (Onion: src/common/utils/keymap_hw.h) and the game's pad bits */
static struct { int code; unsigned bit; const char *name; } keys[] = {
    { KEY_UP, PAD_UP, "UP" }, { KEY_DOWN, PAD_DOWN, "DOWN" }, { KEY_LEFT, PAD_LEFT, "LEFT" }, { KEY_RIGHT, PAD_RIGHT, "RIGHT" },
    { KEY_SPACE, PAD_A, "A" }, { KEY_LEFTCTRL, PAD_B, "B" }, { KEY_LEFTSHIFT, PAD_X, "X" }, { KEY_LEFTALT, PAD_Y, "Y" },
    { KEY_E, PAD_L1, "L1" }, { KEY_T, PAD_R1, "R1" }, { KEY_TAB, PAD_L2, "L2" }, { KEY_BACKSPACE, PAD_R2, "R2" },
    { KEY_RIGHTCTRL, PAD_SELECT, "SELECT" }, { KEY_ENTER, PAD_START, "START" },
};
#define N_KEYS (sizeof keys / sizeof *keys)
#define PAD_MENU (1u << 20)                  /* not the game's: held, it quits */
static int input = -1;
static unsigned held;

/* buttons-miyoo.txt: "A=57" lines (key codes), for a machine whose keys differ */
static void load_map(void) {
    char line[128];
    FILE *f = fopen("buttons-miyoo.txt", "r");
    unsigned i;
    if (!f) return;
    while (fgets(line, sizeof line, f)) {
        char *eq = strchr(line, '=');
        if (line[0] == '#' || !eq) continue;
        *eq++ = 0;
        for (i = 0; i < N_KEYS; ++i) if (!strcmp(line, keys[i].name)) keys[i].code = atoi(eq);
    }
    fclose(f);
}

static void read_keys(void) {
    struct input_event e;
    static int logged;
    unsigned i;
    while (input >= 0 && read(input, &e, sizeof e) == (ssize_t)sizeof e) {
        unsigned bit = 0;
        if (e.type != EV_KEY || e.value == 2) continue;          /* 2: the key held, repeating */
        if (e.code == KEY_ESC) bit = PAD_MENU;
        for (i = 0; i < N_KEYS; ++i) if (e.code == keys[i].code) bit = keys[i].bit;
        if (!bit && e.value && logged++ < 12) printf("key %d pressed (not the game's)\n", e.code);
        if (e.value) held |= bit; else held &= ~bit;
    }
}

/* ---------------------------------------------------------------- sound */

/* the mixer runs at 22050 Hz mono (jsrt.c); the device gets 44100 Hz stereo, each sample four times */
#define OUT_RATE 44100
#define CHUNK 512
static pthread_mutex_t audio_lock = PTHREAD_MUTEX_INITIALIZER;
static volatile int audio_on;
static pthread_t audio_thread;

static void *audio_pump(void *arg) {
    int dsp = (int)(intptr_t)arg;
    int16_t in[CHUNK], out[CHUNK * 4];
    int i;
    while (audio_on) {
        pthread_mutex_lock(&audio_lock);
        jsrt_audio(in, CHUNK);
        pthread_mutex_unlock(&audio_lock);
        for (i = 0; i < CHUNK; ++i) out[4 * i] = out[4 * i + 1] = out[4 * i + 2] = out[4 * i + 3] = in[i];
        {
            const char *p = (const char *)out;
            size_t left = sizeof out;
            while (left && audio_on) {                                  /* blocks: the device sets the pace */
                ssize_t w = write(dsp, p, left);
                if (w <= 0) { if (errno == EINTR) continue; audio_on = 0; break; }
                p += w; left -= (size_t)w;
            }
        }
    }
    close(dsp);
    return 0;
}

static void audio_open(void) {
    int dsp = open("/dev/dsp", O_WRONLY), fmt = AFMT_S16_LE, ch = 2, rate = OUT_RATE, frag = 0x0008000B;   /* 8 x 2 KB */
    if (dsp < 0) { printf("no sound: /dev/dsp: %s (LD_PRELOAD libpadsp.so?)\n", strerror(errno)); return; }
    ioctl(dsp, SNDCTL_DSP_SETFRAGMENT, &frag);
    if (ioctl(dsp, SNDCTL_DSP_SETFMT, &fmt) != 0 || fmt != AFMT_S16_LE || ioctl(dsp, SNDCTL_DSP_CHANNELS, &ch) != 0 ||
        ch != 2 || ioctl(dsp, SNDCTL_DSP_SPEED, &rate) != 0) {
        printf("no sound: the device would not take 16-bit stereo (format %d, %d channels)\n", fmt, ch);
        close(dsp);
        return;
    }
    if (rate != OUT_RATE) printf("sound: the device runs at %d Hz, not %d: it will sound off\n", rate, OUT_RATE);
    audio_on = 1;
    if (pthread_create(&audio_thread, 0, audio_pump, (void *)(intptr_t)dsp) != 0) { audio_on = 0; close(dsp); return; }
    printf("sound: /dev/dsp %d Hz stereo\n", rate);
}

/* ---------------------------------------------------------------- the log, the loop */

/* log.txt through a pipe, as js_sdl2.c: a write to the SD card now and then waits, and must not stop a frame */
static int log_out = -1;
static void *log_pump(void *arg) {
    int in = (int)(intptr_t)arg;
    char buf[4096];
    ssize_t n;
    while ((n = read(in, buf, sizeof buf)) > 0) {
        ssize_t off = 0;
        while (off < n) { ssize_t w = write(log_out, buf + off, (size_t)(n - off)); if (w <= 0) break; off += w; }
    }
    return 0;
}
static pthread_t log_thread;
static int log_piped;
static void log_through_pipe(void) {
    int fds[2];
    if (pipe(fds) != 0) return;
    if ((log_out = dup(STDOUT_FILENO)) < 0) { close(fds[0]); close(fds[1]); return; }
    fflush(stdout);
    dup2(fds[1], STDOUT_FILENO);
    dup2(fds[1], STDERR_FILENO);
    close(fds[1]);
    if (pthread_create(&log_thread, 0, log_pump, (void *)(intptr_t)fds[0]) != 0) { dup2(log_out, STDOUT_FILENO); dup2(log_out, STDERR_FILENO); }
    else log_piped = 1;
}

static volatile sig_atomic_t stop;
static void on_signal(int s) { (void)s; stop = 1; }   /* the power button's shutdown (Onion's keymon): the game saves */

int main(int argc, char **argv) {
    double start, quit_since = 0, menu_since = 0, stat_t, stat_js = 0, stat_show = 0, stat_worst = 0;
    unsigned stat_n = 0, stat_lines = 0;
    (void)argc; (void)argv;
    setvbuf(stdout, 0, _IOLBF, 0);
    log_through_pipe();
    signal(SIGTERM, on_signal);
    signal(SIGINT, on_signal);
    signal(SIGPIPE, SIG_IGN);
    if (getenv("HOLUA_TURN")) turn = atoi(getenv("HOLUA_TURN")) != 0;   /* 0: a screen that is not upside down */
    if (!screen_open()) { screen_close(); return 1; }
    if ((input = open("/dev/input/event0", O_RDONLY | O_NONBLOCK)) < 0) printf("no buttons: /dev/input/event0: %s\n", strerror(errno));
    load_map();
    if (!jsrt_init(".")) { printf("the page did not start (see above)\n"); screen_close(); return 1; }
    audio_open();
    start = stat_t = now_ms();
    while (!stop) {
        double t0 = now_ms(), p1, p2, spent;
        const uint32_t *screen;
        unsigned pad;
        read_keys();
        pad = held & ~PAD_MENU;
        /* SELECT + START for half a second, or MENU for one, quits (the game saves) */
        if ((pad & (PAD_SELECT | PAD_START)) == (PAD_SELECT | PAD_START)) { if (!quit_since) quit_since = t0; else if (t0 - quit_since > 500) break; }
        else quit_since = 0;
        if (held & PAD_MENU) { if (!menu_since) menu_since = t0; else if (t0 - menu_since > 1000) break; }
        else menu_since = 0;
        if (jsrt_wants_exit()) break;
        screen = jsrt_frame(t0 - start, pad);
        p1 = now_ms();
        if (audio_on) { pthread_mutex_lock(&audio_lock); jsrt_audio_commit(); pthread_mutex_unlock(&audio_lock); }
        screen_show(screen);
        p2 = now_ms();
        stat_js += p1 - t0; stat_show += p2 - p1; ++stat_n;
        if (p2 - t0 > stat_worst) stat_worst = p2 - t0;
        if (p1 - t0 > 300) printf("slow: frame at t=%.1fs, game %.0f ms\n", (t0 - start) / 1000, p1 - t0);
        if (p2 - stat_t >= 5000) {
            double s = (p2 - stat_t) / 1000;
            printf("t=%.0fs  %.1f fps  game %.1f ms  screen %.1f ms  worst %.0f ms\n", (p2 - start) / 1000, stat_n / s,
                   stat_js / stat_n, stat_show / stat_n, stat_worst);
            stat_t = p2; stat_n = 0; stat_js = stat_show = stat_worst = 0;
            if (++stat_lines % 6 == 1) { char m[512]; jsrt_mem(m, sizeof m); printf("%s\n", m); }   /* every 30 s */
        }
        spent = now_ms() - t0;
        if (spent < 16) usleep((useconds_t)((16 - spent) * 1000));   /* up to 60 frames a second, as a browser */
    }
    jsrt_quit();
    if (audio_on) { audio_on = 0; pthread_join(audio_thread, 0); }
    jsrt_shutdown();
    if (input >= 0) close(input);
    screen_close();
    if (log_piped) {
        fflush(stdout); fflush(stderr);
        dup2(log_out, STDOUT_FILENO); dup2(log_out, STDERR_FILENO);
        pthread_join(log_thread, 0);
    }
    return 0;
}
