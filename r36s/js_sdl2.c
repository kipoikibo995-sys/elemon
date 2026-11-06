/* Elemon (the game) on the R36S (and any SDL2 box): window, game pad, sound around jsrt.c. */
#include "jsrt.h"
#include <SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* the page's buttons, their pad bit, and the SDL button (or trigger axis) that presses them */
static struct { const char *name; unsigned bit; int button, axis; } map[] = {
    { "A", PAD_A, SDL_CONTROLLER_BUTTON_A, -1 }, { "B", PAD_B, SDL_CONTROLLER_BUTTON_B, -1 },
    { "X", PAD_X, SDL_CONTROLLER_BUTTON_X, -1 }, { "Y", PAD_Y, SDL_CONTROLLER_BUTTON_Y, -1 },
    { "L1", PAD_L1, SDL_CONTROLLER_BUTTON_LEFTSHOULDER, -1 }, { "R1", PAD_R1, SDL_CONTROLLER_BUTTON_RIGHTSHOULDER, -1 },
    { "L2", PAD_L2, -1, SDL_CONTROLLER_AXIS_TRIGGERLEFT }, { "R2", PAD_R2, -1, SDL_CONTROLLER_AXIS_TRIGGERRIGHT },
    { "SELECT", PAD_SELECT, SDL_CONTROLLER_BUTTON_BACK, -1 }, { "START", PAD_START, SDL_CONTROLLER_BUTTON_START, -1 },
    { "UP", PAD_UP, SDL_CONTROLLER_BUTTON_DPAD_UP, -1 }, { "DOWN", PAD_DOWN, SDL_CONTROLLER_BUTTON_DPAD_DOWN, -1 },
    { "LEFT", PAD_LEFT, SDL_CONTROLLER_BUTTON_DPAD_LEFT, -1 }, { "RIGHT", PAD_RIGHT, SDL_CONTROLLER_BUTTON_DPAD_RIGHT, -1 },
};
#define N_MAP (sizeof map / sizeof *map)
static SDL_GameController *pads[4];
/* a pad whose SDL mapping has no back or start (some clones' ArkOS, e.g. the R46H: SELECT and START did nothing):
   the first raw buttons its mapping leaves out stand in for them, -1 when the mapping has them */
static int raw_sel[4] = { -1, -1, -1, -1 }, raw_start[4] = { -1, -1, -1, -1 };
static char raw_seen[4][32];                               /* raw buttons outside the mapping already logged */

static void setup_pad(int k) {
    char *m = SDL_GameControllerMapping(pads[k]);
    SDL_Joystick *j = SDL_GameControllerGetJoystick(pads[k]);
    int nb = j ? SDL_JoystickNumButtons(j) : 0, b, used[64] = { 0 };
    const char *p;
    raw_sel[k] = raw_start[k] = -1;
    memset(raw_seen[k], 0, sizeof raw_seen[k]);
    printf("pad %d: %s, %d buttons | %s\n", k, SDL_GameControllerName(pads[k]), nb, m ? m : "no mapping");
    if (!m) return;
    for (p = m; (p = strstr(p, ":b")) != 0; p += 2) { b = atoi(p + 2); if (b >= 0 && b < 64) used[b] = 1; }
    for (b = 0; b < nb && b < 64; ++b)
        if (!used[b]) {
            if (!strstr(m, "back:") && raw_sel[k] < 0) raw_sel[k] = b;
            else if (!strstr(m, "start:") && raw_start[k] < 0) raw_start[k] = b;
        }
    if (raw_sel[k] >= 0 || raw_start[k] >= 0)
        printf("pad %d: no back/start in its mapping: SELECT = raw button %d, START = raw button %d\n", k, raw_sel[k], raw_start[k]);
    SDL_free(m);
}

/* the handheld's own volume: TrimUI's keymon writes the volume buttons' level (0..20, "vol") into
   system.json but sets no mixer the game's sound goes through, so the game scales its sound by it (30 dB from 1 to 20,
   0 silent); without the file (R36S) the sound is as it was */
#define VOL_FILE "/mnt/UDISK/system.json"
static volatile int vol_gain = 65536;                     /* 16.16 */
static int json_int(const char *s, const char *key, int dflt) {
    const char *p = strstr(s, key);
    if (!p) return dflt;
    p += strlen(key);
    while (*p == '"' || *p == ':' || *p == ' ' || *p == '\t') ++p;
    return *p >= '0' && *p <= '9' ? atoi(p) : dflt;
}
static void read_volume(void) {
    static int last = -2;
    char buf[4096];
    size_t n;
    int v;
    FILE *f = fopen(VOL_FILE, "r");
    if (!f) return;
    n = fread(buf, 1, sizeof buf - 1, f);
    fclose(f);
    buf[n] = 0;
    /* system.json's "mute" is not the handheld's mute: it stays 1 on a Brick that plays sound (06/11/2026, the
       game was silent); keymon's own mute leaves /tmp/system/muted (and turns the speaker off itself) */
    v = access("/tmp/system/muted", F_OK) == 0 ? 0 : json_int(buf, "\"vol\"", 20);
    if (v < 0) v = 0;
    if (v > 20) v = 20;
    if (v == last) return;
    last = v;
    vol_gain = v ? (int)(65536 * SDL_pow(10.0, 1.5 * (v - 20) / 20.0)) : 0;
    printf("volume %d/20: x%.3f\n", v, vol_gain / 65536.0);
}

static void audio_callback(void *user, Uint8 *stream, int len) {
    int16_t *s = (int16_t *)stream;
    int i, n = len / 2, g = vol_gain;
    (void)user;
    jsrt_audio(s, n);
    if (g != 65536) for (i = 0; i < n; ++i) s[i] = (int16_t)((s[i] * g) >> 16);
}

/* buttons.txt: "A=b" lines (SDL names; lefttrigger / righttrigger for the trigger axes) */
static void load_map(void) {
    char line[128];
    unsigned i;
    FILE *f = fopen("buttons.txt", "r");
    if (!f) return;
    while (fgets(line, sizeof line, f)) {
        char *eq = strchr(line, '='), *end;
        if (line[0] == '#' || !eq) continue;
        *eq++ = 0;
        for (end = eq; *end && *end != '\r' && *end != '\n' && *end != ' '; ++end) {}
        *end = 0;
        for (i = 0; i < N_MAP; ++i)
            if (!strcmp(line, map[i].name)) {
                SDL_GameControllerButton b = SDL_GameControllerGetButtonFromString(eq);
                SDL_GameControllerAxis a = SDL_GameControllerGetAxisFromString(eq);
                if (b != SDL_CONTROLLER_BUTTON_INVALID) { map[i].button = b; map[i].axis = -1; }
                else if (a == SDL_CONTROLLER_AXIS_TRIGGERLEFT || a == SDL_CONTROLLER_AXIS_TRIGGERRIGHT) { map[i].axis = a; map[i].button = -1; }
            }
    }
    fclose(f);
}

/* the two analog sticks work as the D-pad: a direction is on past STICK_ON and off again below STICK_OFF, so a
   stick held near the edge does not flicker (and menus do not step twice) */
#define STICK_ON 14000
#define STICK_OFF 9000
static unsigned stick_bits;

static unsigned sticks(SDL_GameController *p) {
    static const struct { SDL_GameControllerAxis axis; int sign; unsigned bit; } dir[] = {
        { SDL_CONTROLLER_AXIS_LEFTX, -1, PAD_LEFT }, { SDL_CONTROLLER_AXIS_LEFTX, 1, PAD_RIGHT },
        { SDL_CONTROLLER_AXIS_LEFTY, -1, PAD_UP }, { SDL_CONTROLLER_AXIS_LEFTY, 1, PAD_DOWN },
        { SDL_CONTROLLER_AXIS_RIGHTX, -1, PAD_LEFT }, { SDL_CONTROLLER_AXIS_RIGHTX, 1, PAD_RIGHT },
        { SDL_CONTROLLER_AXIS_RIGHTY, -1, PAD_UP }, { SDL_CONTROLLER_AXIS_RIGHTY, 1, PAD_DOWN } };
    unsigned bits = 0, i;
    for (i = 0; i < sizeof dir / sizeof *dir; ++i) {
        int v = SDL_GameControllerGetAxis(p, dir[i].axis) * dir[i].sign;
        if (v > STICK_ON || (v > STICK_OFF && (stick_bits & dir[i].bit))) bits |= dir[i].bit;
    }
    return bits;
}

static unsigned read_pad(void) {
    const Uint8 *keys = SDL_GetKeyboardState(0);
    unsigned bits = 0, stick = 0, i;
    int k;
    for (k = 0; k < 4; ++k) {
        if (!pads[k]) continue;
        for (i = 0; i < N_MAP; ++i) {
            if (map[i].button >= 0 && SDL_GameControllerGetButton(pads[k], (SDL_GameControllerButton)map[i].button)) bits |= map[i].bit;
            if (map[i].axis >= 0 && SDL_GameControllerGetAxis(pads[k], (SDL_GameControllerAxis)map[i].axis) > 16000) bits |= map[i].bit;
        }
        stick |= sticks(pads[k]);
        {
            SDL_Joystick *j = SDL_GameControllerGetJoystick(pads[k]);
            if (j && raw_sel[k] >= 0 && SDL_JoystickGetButton(j, raw_sel[k])) bits |= PAD_SELECT;
            if (j && raw_start[k] >= 0 && SDL_JoystickGetButton(j, raw_start[k])) bits |= PAD_START;
        }
    }
    stick_bits = stick;
    bits |= stick;
    /* keyboard on a PC, the same keys as the test page */
    if (keys[SDL_SCANCODE_UP]) bits |= PAD_UP;
    if (keys[SDL_SCANCODE_DOWN]) bits |= PAD_DOWN;
    if (keys[SDL_SCANCODE_LEFT]) bits |= PAD_LEFT;
    if (keys[SDL_SCANCODE_RIGHT]) bits |= PAD_RIGHT;
    if (keys[SDL_SCANCODE_RETURN] || keys[SDL_SCANCODE_Z] || keys[SDL_SCANCODE_SPACE]) bits |= PAD_A;
    if (keys[SDL_SCANCODE_X] || keys[SDL_SCANCODE_BACKSPACE]) bits |= PAD_B;
    if (keys[SDL_SCANCODE_C]) bits |= PAD_X;
    if (keys[SDL_SCANCODE_V]) bits |= PAD_Y;
    if (keys[SDL_SCANCODE_Q]) bits |= PAD_L1;
    if (keys[SDL_SCANCODE_W]) bits |= PAD_R1;
    if (keys[SDL_SCANCODE_1]) bits |= PAD_L2;
    if (keys[SDL_SCANCODE_2]) bits |= PAD_R2;
    if (keys[SDL_SCANCODE_E] || keys[SDL_SCANCODE_LSHIFT]) bits |= PAD_SELECT;
    if (keys[SDL_SCANCODE_S]) bits |= PAD_START;
    /* a handheld whose SELECT / START come in as keys rather than pad buttons */
    if (keys[SDL_SCANCODE_SELECT] || keys[SDL_SCANCODE_RSHIFT]) bits |= PAD_SELECT;
    if (keys[SDL_SCANCODE_MENU] || keys[SDL_SCANCODE_AC_HOME] || keys[SDL_SCANCODE_KP_ENTER]) bits |= PAD_START;
    return bits;
}

/* log.txt through a pipe: printf only fills the pipe, a thread of its own writes it to the card. On the SD card a
   write now and then waits (its housekeeping, up to seconds), and a log line written in the frame stopped the game */
static int log_out = -1;
static SDL_Thread *log_thread;
static int log_pump(void *arg) {
    int in = (int)(intptr_t)arg;
    char buf[4096];
    ssize_t n;
    while ((n = read(in, buf, sizeof buf)) > 0) {
        ssize_t off = 0;
        while (off < n) { ssize_t w = write(log_out, buf + off, (size_t)(n - off)); if (w <= 0) break; off += w; }
    }
    return 0;
}
static void log_through_pipe(void) {
    int fds[2];
    if (pipe(fds) != 0) return;
    log_out = dup(STDOUT_FILENO);
    if (log_out < 0) { close(fds[0]); close(fds[1]); return; }
    fflush(stdout);
    dup2(fds[1], STDOUT_FILENO);
    dup2(fds[1], STDERR_FILENO);
    close(fds[1]);
    if (!(log_thread = SDL_CreateThread(log_pump, "log", (void *)(intptr_t)fds[0]))) {   /* no thread: back to the file itself */
        dup2(log_out, STDOUT_FILENO); dup2(log_out, STDERR_FILENO);
    }
}

int main(int argc, char **argv) {
    SDL_Window *window;
    SDL_Renderer *renderer;
    SDL_Texture *texture;
    SDL_AudioSpec want;
    int audio = 0, running = 1, i, n = 0, sw;
    Uint32 start, quit_since = 0, vol_t = 0;
    (void)argc; (void)argv;
    setvbuf(stdout, 0, _IOLBF, 0);                         /* log.txt is written line by line */
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_TIMER | SDL_INIT_AUDIO | SDL_INIT_JOYSTICK | SDL_INIT_GAMECONTROLLER) != 0) {
        printf("SDL_Init: %s\n", SDL_GetError());
        return 1;
    }
    log_through_pipe();
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");
    window = SDL_CreateWindow("Elemon", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, JS_SCREEN_W, JS_SCREEN_H,
                              SDL_WINDOW_SHOWN | SDL_WINDOW_FULLSCREEN_DESKTOP);
    renderer = window ? SDL_CreateRenderer(window, -1, 0) : 0;
    /* a screen wider than the game's 4:3 (the TrimUI Smart Pro S, 1280x720): a canvas as wide as the screen's shape
       (854x480), the game in its middle and the sides filled by js/shim.js; a 4:3 screen keeps 640x480 as before */
    {
        int ow = 0, oh = 0;
        if (renderer && SDL_GetRendererOutputSize(renderer, &ow, &oh) == 0 && oh > 0 && ow * JS_SCREEN_H > oh * JS_SCREEN_W + oh / 8)
            jsrt_set_screen_w((ow * JS_SCREEN_H + oh) / (2 * oh) * 2);
        sw = jsrt_screen_w();
        printf("screen %dx%d%s, canvas %dx%d\n", ow, oh, sw > JS_SCREEN_W ? ": wide" : "", sw, JS_SCREEN_H);
    }
    texture = renderer ? SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STREAMING, sw, JS_SCREEN_H) : 0;
    if (!texture) { printf("no window: %s\n", SDL_GetError()); SDL_Quit(); return 1; }
    SDL_RenderSetLogicalSize(renderer, sw, JS_SCREEN_H);
    {
        SDL_RendererInfo info;
        if (SDL_GetRendererInfo(renderer, &info) == 0)
            printf("renderer: %s (video %s)%s%s\n", info.name, SDL_GetCurrentVideoDriver(),
                   info.flags & SDL_RENDERER_ACCELERATED ? ", accelerated" : ", software",
                   info.flags & SDL_RENDERER_PRESENTVSYNC ? ", vsync" : "");
    }
    SDL_ShowCursor(SDL_DISABLE);
    load_map();
    for (i = 0; i < SDL_NumJoysticks() && n < 4; ++i)
        if (SDL_IsGameController(i) && (pads[n] = SDL_GameControllerOpen(i)) != 0) {
            setup_pad(n);
            ++n;
        }
    SDL_memset(&want, 0, sizeof want);
    want.freq = JS_AUDIO_RATE;
    want.format = AUDIO_S16SYS;
    want.channels = 1;
    want.samples = 1024;
    want.callback = audio_callback;
    if (!jsrt_init(".")) { printf("the page did not start (see above)\n"); SDL_Quit(); return 1; }
    read_volume();
    if (SDL_OpenAudio(&want, NULL) == 0) { audio = 1; SDL_PauseAudio(0); }   /* SDL converts to the device */
    else printf("no sound: %s\n", SDL_GetError());

    start = SDL_GetTicks();
    {
    /* every 5 s a line in log.txt: frames a second and where the time went (the game's frame, putting it on the
       screen), so the real speed on the handheld can be read off the card */
    Uint32 stat_t = SDL_GetTicks(), stat_n = 0, stat_worst = 0, stat_lines = 0;
    Uint64 stat_js = 0, stat_show = 0, freq = SDL_GetPerformanceFrequency();
    while (running) {
        Uint32 t0 = SDL_GetTicks(), spent;
        Uint64 p0, p1, p2;
        unsigned pad;
        const uint32_t *screen;
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) running = 0;
            if (e.type == SDL_CONTROLLERDEVICEADDED) {
                /* SDL also announces the pads already open at start: those are not opened twice */
                SDL_JoystickID id = SDL_JoystickGetDeviceInstanceID(e.cdevice.which);
                int open = 0;
                for (i = 0; i < 4; ++i)
                    if (pads[i] && SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(pads[i])) == id) open = 1;
                if (!open)
                    for (i = 0; i < 4; ++i) if (!pads[i]) { if ((pads[i] = SDL_GameControllerOpen(e.cdevice.which)) != 0) setup_pad(i); break; }
            }
            /* a raw button the pad's mapping leaves out: logged once, so a log from a new handheld shows its keys */
            if (e.type == SDL_JOYBUTTONDOWN && e.jbutton.button < 32)
                for (i = 0; i < 4; ++i)
                    if (pads[i] && SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(pads[i])) == e.jbutton.which &&
                        !raw_seen[i][e.jbutton.button]) {
                        char *m = SDL_GameControllerMapping(pads[i]), key[8];
                        snprintf(key, sizeof key, ":b%d,", e.jbutton.button);
                        if (!m || !strstr(m, key)) printf("pad %d: raw button %d pressed (not in its mapping)\n", i, e.jbutton.button);
                        raw_seen[i][e.jbutton.button] = 1;
                        SDL_free(m);
                    }
            if (e.type == SDL_KEYDOWN && !e.key.repeat) {
                static int keys_logged;
                if (keys_logged++ < 12) printf("key %s pressed\n", SDL_GetScancodeName(e.key.keysym.scancode));
            }
        }
        pad = read_pad();
        /* SELECT + START held for half a second quits (on their own they are the page's buttons) */
        if ((pad & (PAD_SELECT | PAD_START)) == (PAD_SELECT | PAD_START)) {
            if (!quit_since) quit_since = t0;
            else if (t0 - quit_since > 500) running = 0;
        } else quit_since = 0;
        if (SDL_GetKeyboardState(0)[SDL_SCANCODE_ESCAPE] && SDL_GetKeyboardState(0)[SDL_SCANCODE_LCTRL]) running = 0;
        if (jsrt_wants_exit()) running = 0;
        if (t0 - vol_t >= 300) { vol_t = t0; read_volume(); }   /* the volume buttons, within a third of a second */                 /* the game's own "Thoát game" */

        p0 = SDL_GetPerformanceCounter();
        screen = jsrt_frame((double)(t0 - start), pad);
        p1 = SDL_GetPerformanceCounter();
        if (audio) { SDL_LockAudio(); jsrt_audio_commit(); SDL_UnlockAudio(); }
        SDL_UpdateTexture(texture, 0, screen, sw * 4);
        SDL_RenderClear(renderer);
        SDL_RenderCopy(renderer, texture, 0, 0);
        SDL_RenderPresent(renderer);
        p2 = SDL_GetPerformanceCounter();
        stat_js += p1 - p0; stat_show += p2 - p1; ++stat_n;
        if ((p1 - p0) * 1000 / freq > 300 || (p2 - p1) * 1000 / freq > 300)   /* a stall: when, and in which part */
            printf("slow: frame at t=%.1fs, game %u ms, screen %u ms\n", (SDL_GetTicks() - start) / 1000.0,
                   (unsigned)((p1 - p0) * 1000 / freq), (unsigned)((p2 - p1) * 1000 / freq));
        if ((Uint32)((p2 - p0) * 1000 / freq) > stat_worst) stat_worst = (Uint32)((p2 - p0) * 1000 / freq);
        if (SDL_GetTicks() - stat_t >= 5000) {
            double s = (SDL_GetTicks() - stat_t) / 1000.0;
            printf("t=%us  %.1f fps  game %.1f ms  screen %.1f ms  worst %u ms\n", (unsigned)((SDL_GetTicks() - start) / 1000),
                   stat_n / s, stat_js * 1000.0 / freq / stat_n, stat_show * 1000.0 / freq / stat_n, (unsigned)stat_worst);
            stat_t = SDL_GetTicks(); stat_n = 0; stat_js = stat_show = 0; stat_worst = 0;
            if (++stat_lines % 6 == 1) { char m[256]; jsrt_mem(m, sizeof m); printf("%s\n", m); }   /* every 30 s */
        }
        spent = SDL_GetTicks() - t0;
        if (spent < 16) SDL_Delay(16 - spent);              /* up to 60 frames a second, as a browser */
    }
    }
    jsrt_quit();
    if (audio) SDL_CloseAudio();
    jsrt_shutdown();
    for (i = 0; i < 4; ++i) if (pads[i]) SDL_GameControllerClose(pads[i]);
    SDL_DestroyTexture(texture);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    if (log_thread) {                            /* the last lines reach log.txt: the pipe closed, its thread done */
        fflush(stdout); fflush(stderr);
        dup2(log_out, STDOUT_FILENO); dup2(log_out, STDERR_FILENO);
        SDL_WaitThread(log_thread, 0);
    }
    SDL_Quit();
    return 0;
}
