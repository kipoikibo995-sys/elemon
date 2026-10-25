/* The viewer on the R36S (and any SDL2 box): window, buttons, sound. All drawing and mixing is in core.c. */
#include "core.h"
#include <SDL.h>
#include <stdio.h>
#include <string.h>

static SDL_GameController *pads[4];
static int pad_map[BTN_COUNT];

static void audio_callback(void *user, Uint8 *stream, int len) {
    (void)user;
    core_audio((int16_t *)stream, len / 2);
}

/* buttons.txt next to the program: "action=button" lines, see that file */
static void load_pad_map(void) {
    static const struct { const char *name; int btn; SDL_GameControllerButton def; } actions[] = {
        { "act", BTN_ACT, SDL_CONTROLLER_BUTTON_A }, { "run", BTN_RUN, SDL_CONTROLLER_BUTTON_B },
        { "prev_pet", BTN_PREV_PET, SDL_CONTROLLER_BUTTON_X }, { "next_pet", BTN_NEXT_PET, SDL_CONTROLLER_BUTTON_Y },
        { "prev_room", BTN_PREV_ROOM, SDL_CONTROLLER_BUTTON_LEFTSHOULDER },
        { "next_room", BTN_NEXT_ROOM, SDL_CONTROLLER_BUTTON_RIGHTSHOULDER },
        { "night", BTN_NIGHT, SDL_CONTROLLER_BUTTON_BACK }, { "music", BTN_MUSIC, SDL_CONTROLLER_BUTTON_START },
        { "left", BTN_LEFT, SDL_CONTROLLER_BUTTON_DPAD_LEFT }, { "right", BTN_RIGHT, SDL_CONTROLLER_BUTTON_DPAD_RIGHT },
        { "up", BTN_UP, SDL_CONTROLLER_BUTTON_DPAD_UP }, { "down", BTN_DOWN, SDL_CONTROLLER_BUTTON_DPAD_DOWN },
    };
    char line[128];
    unsigned i;
    FILE *f;
    for (i = 0; i < sizeof actions / sizeof *actions; ++i) pad_map[actions[i].btn] = actions[i].def;
    f = fopen("buttons.txt", "r");
    if (!f) return;
    while (fgets(line, sizeof line, f)) {
        char *eq = strchr(line, '='), *end;
        if (line[0] == '#' || !eq) continue;
        *eq++ = 0;
        for (end = eq; *end && *end != '\r' && *end != '\n' && *end != ' '; ++end) {}
        *end = 0;
        for (i = 0; i < sizeof actions / sizeof *actions; ++i)
            if (!strcmp(line, actions[i].name)) {
                SDL_GameControllerButton b = SDL_GameControllerGetButtonFromString(eq);
                if (b != SDL_CONTROLLER_BUTTON_INVALID) pad_map[actions[i].btn] = b;
            }
    }
    fclose(f);
}

int main(int argc, char **argv) {
    static uint32_t frame[SCREEN_W * SCREEN_H];
    SDL_Window *window;
    SDL_Renderer *renderer;
    SDL_Texture *texture;
    SDL_AudioSpec want;
    int audio = 0, running = 1, i, n = 0;
    (void)argc; (void)argv;
    setvbuf(stdout, 0, _IOLBF, 0);                         /* log.txt is written line by line */
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_TIMER | SDL_INIT_AUDIO | SDL_INIT_JOYSTICK | SDL_INIT_GAMECONTROLLER) != 0) {
        printf("SDL_Init: %s\n", SDL_GetError());
        return 1;
    }
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");
    window = SDL_CreateWindow("HoLua", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, SCREEN_W, SCREEN_H,
                              SDL_WINDOW_SHOWN | SDL_WINDOW_FULLSCREEN_DESKTOP);
    renderer = window ? SDL_CreateRenderer(window, -1, 0) : 0;
    texture = renderer ? SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STREAMING, SCREEN_W, SCREEN_H) : 0;
    if (!texture) { printf("no window: %s\n", SDL_GetError()); SDL_Quit(); return 1; }
    SDL_RenderSetLogicalSize(renderer, SCREEN_W, SCREEN_H);
    SDL_ShowCursor(SDL_DISABLE);
    load_pad_map();
    for (i = 0; i < SDL_NumJoysticks() && n < 4; ++i)
        if (SDL_IsGameController(i) && (pads[n] = SDL_GameControllerOpen(i)) != 0) {
            char *mapping = SDL_GameControllerMapping(pads[n]);
            printf("pad %d: %s | %s\n", n, SDL_GameControllerName(pads[n]), mapping ? mapping : "no mapping");
            SDL_free(mapping);
            ++n;
        }
    if (!core_init("data")) { printf("data/ missing or broken\n"); SDL_Quit(); return 1; }
    SDL_memset(&want, 0, sizeof want);
    want.freq = AUDIO_RATE;
    want.format = AUDIO_S16SYS;
    want.channels = 1;
    want.samples = 1024;
    want.callback = audio_callback;
    if (SDL_OpenAudio(&want, NULL) == 0) { audio = 1; SDL_PauseAudio(0); }   /* SDL converts to the device */
    else printf("no sound: %s\n", SDL_GetError());

    while (running) {
        Uint32 start = SDL_GetTicks(), spent;
        const Uint8 *keys;
        int held[BTN_COUNT];
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) running = 0;
            if (e.type == SDL_CONTROLLERDEVICEADDED)
                for (i = 0; i < 4; ++i) if (!pads[i]) { pads[i] = SDL_GameControllerOpen(e.cdevice.which); break; }
        }
        memset(held, 0, sizeof held);
        for (i = 0; i < BTN_COUNT; ++i) {
            int k;
            for (k = 0; k < 4; ++k)
                if (pads[k] && SDL_GameControllerGetButton(pads[k], (SDL_GameControllerButton)pad_map[i])) held[i] = 1;
        }
        keys = SDL_GetKeyboardState(0);                    /* keyboard on a PC */
        held[BTN_LEFT] |= keys[SDL_SCANCODE_LEFT]; held[BTN_RIGHT] |= keys[SDL_SCANCODE_RIGHT];
        held[BTN_UP] |= keys[SDL_SCANCODE_UP]; held[BTN_DOWN] |= keys[SDL_SCANCODE_DOWN];
        held[BTN_ACT] |= keys[SDL_SCANCODE_Z] | keys[SDL_SCANCODE_RETURN]; held[BTN_RUN] |= keys[SDL_SCANCODE_X];
        held[BTN_PREV_PET] |= keys[SDL_SCANCODE_A]; held[BTN_NEXT_PET] |= keys[SDL_SCANCODE_S];
        held[BTN_PREV_ROOM] |= keys[SDL_SCANCODE_Q]; held[BTN_NEXT_ROOM] |= keys[SDL_SCANCODE_W];
        held[BTN_NIGHT] |= keys[SDL_SCANCODE_N]; held[BTN_MUSIC] |= keys[SDL_SCANCODE_M];
        if (keys[SDL_SCANCODE_ESCAPE]) running = 0;

        core_frame(held, frame);
        if (audio) { SDL_LockAudio(); core_audio_commit(); SDL_UnlockAudio(); }
        if (core_wants_quit()) running = 0;
        SDL_UpdateTexture(texture, 0, frame, SCREEN_W * 4);
        SDL_RenderClear(renderer);
        SDL_RenderCopy(renderer, texture, 0, 0);
        SDL_RenderPresent(renderer);
        spent = SDL_GetTicks() - start;
        if (spent < FRAME_MS) SDL_Delay(FRAME_MS - spent);
    }
    if (audio) SDL_CloseAudio();
    core_shutdown();
    for (i = 0; i < 4; ++i) if (pads[i]) SDL_GameControllerClose(pads[i]);
    SDL_DestroyTexture(texture);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return 0;
}
