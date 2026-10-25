"""Animated aura for legend frames (prototype).

A legend frame has its aura painted in, so it never moves. This splits a built frame into the body (everything
the dark outline closes in) and the painted aura (what can be reached from outside without crossing the outline),
draws moving flames behind the whole sprite (or, with split, drops the painted aura and draws the new one around the body): flame tongues that rise and flicker, N frames that loop,
solid pixel colours in 2 px cells (no alpha blending, so it shows the same on the PocketGo).
Usage: python aura_anim.py <element> <frame.png> <out_prefix> [frames=6]
       writes <out_prefix>_0.png .. _<N-1>.png (RGBA, same canvas size as the frame) and <out_prefix>_body.png
"""
import sys
import numpy as np
from PIL import Image

PALETTE = {          # outer -> inner
    'hoa':  [(196, 52, 18), (255, 128, 28), (255, 206, 72), (255, 248, 196)],
    'kim':  [(84, 112, 178), (146, 186, 238), (214, 232, 255), (255, 255, 255)],
    'moc':  [(36, 116, 40), (84, 196, 58), (166, 238, 88), (236, 255, 186)],
    'thuy': [(26, 84, 186), (48, 156, 238), (126, 226, 255), (226, 255, 255)],
    'tho':  [(142, 84, 26), (212, 146, 48), (248, 202, 88), (255, 244, 188)],
}
CELL = 2                 # aura drawn in 2x2 cells, like the aim funnel


def shift(m, dy, dx):
    out = np.zeros_like(m)
    h, w = m.shape
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = m[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return out


def dilate(m):
    r = m.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            r |= shift(m, dy, dx)
    return r


def body_mask(rgba):
    """pixels closed in by the dark outline (plus the outline itself)"""
    a = rgba[..., 3] > 0
    rgb = rgba[..., :3].astype(int)
    dark = a & (rgb.sum(-1) < 200)
    dark = dilate(dark)                            # close one-pixel gaps in the outline
    free = ~dark                                   # flood from the border through anything that is not outline
    seen = np.zeros_like(free)
    seen[0, :] = free[0, :]; seen[-1, :] = free[-1, :]; seen[:, 0] = free[:, 0]; seen[:, -1] = free[:, -1]
    while True:
        grown = dilate(seen) & free
        if (grown == seen).all():
            break
        seen = grown
    body = a & ~seen
    # the outline ring that faces the outside belongs to the body too
    return body | (dark & a & dilate(body))


def periodic_noise(h, w, cell, period_cells, seed):
    """value noise, bilinear, that repeats every period_cells grid rows (so the scroll loops)"""
    rng = np.random.default_rng(seed)
    gh, gw = period_cells, w // cell + 2
    g = rng.random((gh, gw))
    ys = np.arange(h)[:, None] / cell
    xs = np.arange(w)[None, :] / cell
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    fy = ys - y0; fx = xs - x0
    fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
    def at(yy, xx):
        return g[yy % gh, np.clip(xx, 0, gw - 1)]
    top = at(y0, x0) * (1 - fx) + at(y0, x0 + 1) * fx
    bot = at(y0 + 1, x0) * (1 - fx) + at(y0 + 1, x0 + 1) * fx
    return top * (1 - fy) + bot * fy


def aura_frames(rgba, element, n=6, reach=16, split=False):
    h, w = rgba.shape[:2]
    # split=True drops the painted aura (needs a closed dark outline); by default the whole sprite stays as drawn
    # and the moving flames go behind it, around its silhouette
    body = body_mask(rgba) if split else rgba[..., 3] > 0
    # distance (in px) outside the body, up to `reach`
    dist = np.full((h, w), 999, np.int32)
    ring = body.copy()
    for d in range(1, reach + 1):
        nxt = dilate(ring)
        dist[nxt & ~ring] = d
        ring = nxt
    pal = PALETTE[element]
    cy = np.arange(h)[:, None].repeat(w, 1)
    top = np.where(body.any(1))[0][0]
    out = []
    period = 6                                     # noise rows per loop
    for t in range(n):
        frame = np.zeros((h, w, 4), np.uint8)
        # flames rise: sample the noise lower down as time goes on; taller above the shoulders
        shift_px = int(round(t * period * 10 / n))
        nz = periodic_noise(h + 64, w, 10, period * 8, 7)[shift_px:shift_px + h]
        nz2 = periodic_noise(h + 64, w, 5, period * 16, 11)[2 * shift_px % 32:2 * shift_px % 32 + h]
        up = np.clip((cy - top) / max(1, h - top), 0, 1)          # 0 at the head, 1 at the feet
        lim = 2 + 11 * (1 - up) * (0.2 + 1.0 * nz) + 4 * nz2       # flame height around the body
        heat = 1 - dist / np.maximum(lim, 1)
        lit = (dist < 999) & (heat > 0) & ~body
        band = np.clip((heat * 4.2).astype(int), 0, 3)
        # 2x2 cells: every cell takes the value of its top-left pixel
        yy = (np.arange(h) // CELL * CELL)[:, None]; xx = (np.arange(w) // CELL * CELL)[None, :]
        lit = lit[yy, xx]; band = band[yy, xx]
        for b in range(4):
            sel = lit & (band == b)
            frame[sel, :3] = pal[b]; frame[sel, 3] = 255
        # a few embers floating up
        rng = np.random.default_rng(3)
        for e in range(10):
            ex = rng.integers(0, w // CELL) * CELL
            base = rng.integers(0, h)
            ey = int((base - (t / n) * 60 - rng.integers(0, 20)) % h) // CELL * CELL
            if dist[ey, ex] < 999 and dist[ey, ex] > 8 and not body[ey, ex]:
                frame[ey:ey + CELL, ex:ex + CELL, :3] = pal[2 + e % 2]; frame[ey:ey + CELL, ex:ex + CELL, 3] = 255
        frame[body] = rgba[body]
        out.append(frame)
    b = rgba.copy(); b[~body] = 0
    return out, b


if __name__ == '__main__':
    el, src, pre = sys.argv[1], sys.argv[2], sys.argv[3]
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    im = np.array(Image.open(src).convert('RGBA'))
    pad = 24                                       # room for flames beyond the old canvas
    im = np.pad(im, ((pad, 4), (pad, pad), (0, 0)))
    frames, body = aura_frames(im, el, n)
    for i, f in enumerate(frames):
        Image.fromarray(f).save(f'{pre}_{i}.png')
    Image.fromarray(body).save(f'{pre}_body.png')
    print(pre, len(frames), 'frames', im.shape[1], 'x', im.shape[0])
