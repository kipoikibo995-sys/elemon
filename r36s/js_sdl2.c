/* Elemon (the game) on the R36S (and any SDL2 box): window, game pad, sound around jsrt.c. */
#include "jsrt.h"
#include <SDL.h>
#include <stdio.h>
#include <string.h>

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

static void audio_callback(void *user, Uint8 *stream, int len) {
    (void)user;
    jsrt_audio((int16_t *)stream, len / 2);
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

static unsigned read_pad(void) {
    const Uint8 *keys = SDL_GetKeyboardState(0);
    unsigned bits = 0, i;
    int k;
    for (k = 0; k < 4; ++k) {
        if (!pads[k]) continue;
        for (i = 0; i < N_MAP; ++i) {
            if (map[i].button >= 0 && SDL_GameControllerGetButton(pads[k], (SDL_GameControllerButton)map[i].button)) bits |= map[i].bit;
            if (map[i].axis >= 0 && SDL_GameControllerGetAxis(pads[k], (SDL_GameControllerAxis)map[i].axis) > 16000) bits |= map[i].bit;
        }
    }
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
    return bits;
}

int main(int argc, char **argv) {
    SDL_Window *window;
    SDL_Renderer *renderer;
    SDL_Texture *texture;
    SDL_AudioSpec want;
    int audio = 0, running = 1, i, n = 0;
    Uint32 start, quit_since = 0;
    (void)argc; (void)argv;
    setvbuf(stdout, 0, _IOLBF, 0);                         /* log.txt is written line by line */
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_TIMER | SDL_INIT_AUDIO | SDL_INIT_JOYSTICK | SDL_INIT_GAMECONTROLLER) != 0) {
        printf("SDL_Init: %s\n", SDL_GetError());
        return 1;
    }
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");
    window = SDL_CreateWindow("Elemon", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, JS_SCREEN_W, JS_SCREEN_H,
                              SDL_WINDOW_SHOWN | SDL_WINDOW_FULLSCREEN_DESKTOP);
    renderer = window ? SDL_CreateRenderer(window, -1, 0) : 0;
    texture = renderer ? SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STREAMING, JS_SCREEN_W, JS_SCREEN_H) : 0;
    if (!texture) { printf("no window: %s\n", SDL_GetError()); SDL_Quit(); return 1; }
    SDL_RenderSetLogicalSize(renderer, JS_SCREEN_W, JS_SCREEN_H);
    SDL_ShowCursor(SDL_DISABLE);
    load_map();
    for (i = 0; i < SDL_NumJoysticks() && n < 4; ++i)
        if (SDL_IsGameController(i) && (pads[n] = SDL_GameControllerOpen(i)) != 0) {
            char *mapping = SDL_GameControllerMapping(pads[n]);
            printf("pad %d: %s | %s\n", n, SDL_GameControllerName(pads[n]), mapping ? mapping : "no mapping");
            SDL_free(mapping);
            ++n;
        }
    SDL_memset(&want, 0, sizeof want);
    want.freq = JS_AUDIO_RATE;
    want.format = AUDIO_S16SYS;
    want.channels = 1;
    want.samples = 1024;
    want.callback = audio_callback;
    if (!jsrt_init(".")) { printf("the page did not start (see above)\n"); SDL_Quit(); return 1; }
    if (SDL_OpenAudio(&want, NULL) == 0) { audio = 1; SDL_PauseAudio(0); }   /* SDL converts to the device */
    else printf("no sound: %s\n", SDL_GetError());

    start = SDL_GetTicks();
    while (running) {
        Uint32 t0 = SDL_GetTicks(), spent;
        unsigned pad;
        const uint32_t *screen;
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) running = 0;
            if (e.type == SDL_CONTROLLERDEVICEADDED)
                for (i = 0; i < 4; ++i) if (!pads[i]) { pads[i] = SDL_GameControllerOpen(e.cdevice.which); break; }
        }
        pad = read_pad();
        /* SELECT + START held for half a second quits (on their own they are the page's buttons) */
        if ((pad & (PAD_SELECT | PAD_START)) == (PAD_SELECT | PAD_START)) {
            if (!quit_since) quit_since = t0;
            else if (t0 - quit_since > 500) running = 0;
        } else quit_since = 0;
        if (SDL_GetKeyboardState(0)[SDL_SCANCODE_ESCAPE] && SDL_GetKeyboardState(0)[SDL_SCANCODE_LCTRL]) running = 0;

        screen = jsrt_frame((double)(t0 - start), pad);
        if (audio) { SDL_LockAudio(); jsrt_audio_commit(); SDL_UnlockAudio(); }
        SDL_UpdateTexture(texture, 0, screen, JS_SCREEN_W * 4);
        SDL_RenderClear(renderer);
        SDL_RenderCopy(renderer, texture, 0, 0);
        SDL_RenderPresent(renderer);
        spent = SDL_GetTicks() - t0;
        if (spent < 16) SDL_Delay(16 - spent);              /* up to 60 frames a second, as a browser */
    }
    jsrt_quit();
    if (audio) SDL_CloseAudio();
    jsrt_shutdown();
    for (i = 0; i < 4; ++i) if (pads[i]) SDL_GameControllerClose(pads[i]);
    SDL_DestroyTexture(texture);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return 0;
}
