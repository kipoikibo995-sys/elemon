#include "platform.h"

#include <SDL/SDL.h>
#include <stdlib.h>

struct Platform {
    SDL_Surface *screen;
    SDL_Surface *image[PLATFORM_IMAGE_SLOTS];
};

Platform *platform_init(const char *title) {
    Platform *p;
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_TIMER) != 0) return 0;
    p = (Platform *)calloc(1, sizeof(*p));
    if (!p) { SDL_Quit(); return 0; }
    p->screen = SDL_SetVideoMode(SCREEN_W, SCREEN_H, 16, SDL_SWSURFACE);
    if (!p->screen) { free(p); SDL_Quit(); return 0; }
    SDL_ShowCursor(SDL_DISABLE);
    SDL_WM_SetCaption(title, title);
    return p;
}

void platform_shutdown(Platform *p) {
    int i;
    if (p)
        for (i = 0; i < PLATFORM_IMAGE_SLOTS; ++i)
            if (p->image[i]) SDL_FreeSurface(p->image[i]);
    free(p);
    SDL_Quit();
}

int platform_load_image(Platform *p, int slot, const char *path, int keyed) {
    SDL_Surface *loaded, *converted;
    if (!p || slot < 0 || slot >= PLATFORM_IMAGE_SLOTS) return 0;
    loaded = SDL_LoadBMP(path);
    if (!loaded) return 0;
    if (keyed) SDL_SetColorKey(loaded, SDL_SRCCOLORKEY | SDL_RLEACCEL, SDL_MapRGB(loaded->format, 255, 0, 255));
    converted = SDL_DisplayFormat(loaded);
    SDL_FreeSurface(loaded);
    if (!converted) return 0;
    if (keyed) SDL_SetColorKey(converted, SDL_SRCCOLORKEY | SDL_RLEACCEL, SDL_MapRGB(converted->format, 255, 0, 255));
    if (p->image[slot]) SDL_FreeSurface(p->image[slot]);
    p->image[slot] = converted;
    return 1;
}

int platform_image_size(Platform *p, int slot, int *w, int *h) {
    if (!p || slot < 0 || slot >= PLATFORM_IMAGE_SLOTS || !p->image[slot]) return 0;
    *w = p->image[slot]->w;
    *h = p->image[slot]->h;
    return 1;
}

void platform_draw_image(Platform *p, int slot, int x, int y) {
    SDL_Rect d;
    if (!p || slot < 0 || slot >= PLATFORM_IMAGE_SLOTS || !p->image[slot]) return;
    d.x = (Sint16)x; d.y = (Sint16)y; d.w = 0; d.h = 0;
    SDL_BlitSurface(p->image[slot], 0, p->screen, &d);
}

void platform_draw_image_part(Platform *p, int slot, int x, int y, int sx, int sy, int w, int h) {
    SDL_Rect s, d;
    if (!p || slot < 0 || slot >= PLATFORM_IMAGE_SLOTS || !p->image[slot] || w <= 0 || h <= 0) return;
    s.x = (Sint16)sx; s.y = (Sint16)sy; s.w = (Uint16)w; s.h = (Uint16)h;
    d.x = (Sint16)x; d.y = (Sint16)y; d.w = 0; d.h = 0;
    SDL_BlitSurface(p->image[slot], &s, p->screen, &d);
}

void platform_clear(Platform *p, uint8_t r, uint8_t g, uint8_t b) {
    SDL_FillRect(p->screen, 0, SDL_MapRGB(p->screen->format, r, g, b));
}

void platform_rect(Platform *p, int x, int y, int w, int h, uint8_t r, uint8_t g, uint8_t b) {
    SDL_Rect d;
    if (w <= 0 || h <= 0) return;
    d.x = (Sint16)x; d.y = (Sint16)y; d.w = (Uint16)w; d.h = (Uint16)h;
    SDL_FillRect(p->screen, &d, SDL_MapRGB(p->screen->format, r, g, b));
}

void platform_present(Platform *p) { SDL_Flip(p->screen); }

/* MiyooCFW / PocketGo key codes (gmenu2x input.conf); the letters are for desktop testing. */
static Input map_key(SDLKey key) {
    switch (key) {
    case SDLK_LEFT: return INPUT_LEFT;
    case SDLK_RIGHT: return INPUT_RIGHT;
    case SDLK_UP: return INPUT_UP;
    case SDLK_DOWN: return INPUT_DOWN;
    case SDLK_LALT: case SDLK_a: return INPUT_A;
    case SDLK_LCTRL: case SDLK_b: return INPUT_B;
    case SDLK_SPACE: case SDLK_x: return INPUT_X;
    case SDLK_LSHIFT: case SDLK_y: return INPUT_Y;
    case SDLK_TAB: case SDLK_l: return INPUT_L;
    case SDLK_BACKSPACE: case SDLK_r: return INPUT_R;
    case SDLK_RETURN: return INPUT_START;
    case SDLK_ESCAPE: return INPUT_SELECT;
    default: return INPUT_NONE;
    }
}

int platform_poll(Platform *p, Input *input) {
    SDL_Event e;
    (void)p;
    while (SDL_PollEvent(&e)) {
        if (e.type == SDL_QUIT) { *input = INPUT_QUIT; return 1; }
        if (e.type == SDL_KEYDOWN) {
            Input in = map_key(e.key.keysym.sym);
            if (in != INPUT_NONE) { *input = in; return 1; }
        }
    }
    return 0;
}

int platform_held(Platform *p, Input input) {
    Uint8 *keys = SDL_GetKeyState(0);
    (void)p;
    switch (input) {
    case INPUT_LEFT: return keys[SDLK_LEFT] != 0;
    case INPUT_RIGHT: return keys[SDLK_RIGHT] != 0;
    case INPUT_UP: return keys[SDLK_UP] != 0;
    case INPUT_DOWN: return keys[SDLK_DOWN] != 0;
    case INPUT_A: return keys[SDLK_LALT] != 0;
    case INPUT_B: return keys[SDLK_LCTRL] != 0;
    default: return 0;
    }
}

uint32_t platform_ticks(void) { return SDL_GetTicks(); }
void platform_delay(uint32_t ms) { SDL_Delay(ms); }
