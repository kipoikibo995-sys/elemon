"""Takes the painted fire/energy aura off legend sheets, cell by cell, keeping the creature exactly as drawn.

In each 4x6 cell the bright aura colours that can be reached from outside are removed, then loose wisps and
little flecks go, and the piece around the body stays. A cell where this would cut a limb off (a loose piece
the size of a fist or bigger) is left as it was. The original sheet is copied to tinh-linh/_vien-cu/ first.
Usage: python strip_legend_aura.py <slug> ...
"""
import os
import shutil
import sys
import numpy as np
from PIL import Image

import creatures
from aura_anim import dilate
from slice_frames import magenta

BACKUP = os.path.join(creatures.SOURCE, '_vien-cu')
BRIGHT = (225, 165)        # top and second colour channel at least this: aura glow (any element)
MIN_CORE = 0.004           # a body piece is at least this share of the frame's core
LIMB = 0.025               # a loose piece this big (share of the body) means a cut-off limb
BRIDGE = 5                 # px of glow put back around a cut-off limb to join it again


def flood(seed, free):
    seen = seed & free
    while True:
        grown = dilate(seen) & free
        if (grown == seen).all():
            return seen
        seen = grown


def pieces(mask, min_share):
    left = mask.copy(); out = []; total = max(1, mask.sum())
    while left.any():
        ys, xs = np.nonzero(left)
        seed = np.zeros_like(left); seed[ys[0], xs[0]] = True
        p = flood(seed, left); left &= ~p
        if p.sum() >= min_share * total:
            out.append(p)
    return sorted(out, key=lambda q: -q.sum())


def strip(rgb, fg):
    """-> mask of what stays, or None when stripping would cut the creature apart"""
    srt = np.sort(rgb, axis=-1)
    free = ~fg | (fg & (srt[..., 2] >= BRIGHT[0]) & (srt[..., 1] >= BRIGHT[1]))
    edge = np.zeros_like(free); edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
    keep = fg & ~flood(edge, free)
    core = keep & ~dilate(~keep)
    core = core & ~dilate(~core)                     # two erosions: wisps vanish, limbs keep a core
    body = np.zeros_like(core)
    for p in pieces(core, MIN_CORE):
        body |= p
    for _ in range(2):
        body = dilate(body) & keep
    ps = pieces(body, MIN_CORE)
    if not ps:
        return None
    loose = [q for q in ps[1:] if q.sum() >= LIMB * ps[0].sum()]
    if loose:
        # a limb came off where a glow band crossed it (a fist inside a bright ring): keep the limb and put back
        # the bright pixels close to both the body and the limb, so the gap closes again
        parts = ps[0].copy()
        for q in loose:
            parts |= q
        near = parts.copy()
        for _ in range(BRIDGE):
            near = dilate(near)
        bridge = fg & ~parts & near
        joined = parts | bridge
        trimmed = joined & ~dilate(~joined)               # drop the outer rim of the bridge again
        body = (parts | (bridge & dilate(trimmed))) & fg
        ps = pieces(body, MIN_CORE)
        if any(q.sum() >= LIMB * ps[0].sum() for q in ps[1:]):
            return None
    return body


def main(slug):
    path = creatures.sheet(slug, 'legend')
    os.makedirs(BACKUP, exist_ok=True)
    bak = os.path.join(BACKUP, os.path.basename(path))
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    src = Image.open(bak).convert('RGB')
    a = np.array(src).astype(np.int32)
    out = a.copy()
    cw, ch = src.width / 4, src.height / 6
    kept = []
    for r in range(6):
        for c in range(4):
            x0, y0, x1, y1 = round(c * cw), round(r * ch), round((c + 1) * cw), round((r + 1) * ch)
            cell = a[y0:y1, x0:x1]
            fg = ~magenta(cell)
            body = strip(cell, fg)
            if body is None:
                kept.append(r * 4 + c)
                continue
            o = out[y0:y1, x0:x1]
            o[fg & ~body] = (255, 0, 255)
    Image.fromarray(out.astype(np.uint8)).save(path)
    print(f'{slug}: {os.path.basename(path)} stripped, cells kept as drawn: {kept or "none"}')


if __name__ == '__main__':
    for s in sys.argv[1:]:
        main(s)
