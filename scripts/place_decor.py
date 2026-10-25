"""Default place of each decor item of a room, so a fully furnished room can be rebuilt as:
empty room + items (the player moves them later).

Hang đá: its items were cut out of a hand-made layout picture (REFERENCE), so they are found there by
masked template matching (coarse at 1/4 size, then exact at full size). The other rooms' items
were drawn on their own sheets (do-theo-phong/_bang/) and are mostly not in the concept picture, so
they go into fixed slots by kind (bowl, bed, rug, wall, ceiling, floor), see layout().
Writes assets/source/do-theo-phong/<room>/vi-tri.json: {file: [x, y, scale]} = top-left on the 1448x1086 room
and the size the item is drawn at.
Usage: python place_decor.py L1-HO_hang-da [more rooms]
"""
import glob, json, os, sys
import numpy as np
from PIL import Image

import creatures

DECOR = os.path.join(creatures.ROOT, 'assets', 'source', 'do-theo-phong')
NEN = os.path.join(creatures.ROOT, 'assets', 'source', 'nen')
# decor room -> home code of its concept / empty room
ROOM_CODE = {'L1-HO_hang-da': 'N0-1', 'L1-HO_nha-hoang': 'N0-2',
             **{f'L2-{e}': f'L2-{e}' for e in ('HO', 'KI', 'MO', 'TH', 'TO')},
             **{f'L3-{e}': f'N1-{e}' for e in ('HO', 'KI', 'MO', 'TH', 'TO')},
             **{f'L4-{e}': f'N2-{e}' for e in ('HO', 'KI', 'MO', 'TH', 'TO')}}
# rooms whose items were laid out by hand in another picture than the concept
REFERENCE = {'L1-HO_hang-da': os.path.join(NEN, 'hang-da', '_thu-ghep-lai.png'),
             'L3-HO': os.path.join(DECOR, '_thu-ghep_lo-ren.png')}


def masked_ssd(img, tpl, mask):
    """Sum over the mask of (img - tpl)^2 for every top-left offset (valid positions only), via FFT."""
    H, W = img.shape[:2]
    h, w = mask.shape
    shape = (H + h, W + w)
    m = mask.astype(np.float64)
    fm = np.fft.rfft2(m[::-1, ::-1], shape)
    total = np.zeros((H - h + 1, W - w + 1))
    for c in range(img.shape[2]):
        I = img[..., c].astype(np.float64)
        T = tpl[..., c].astype(np.float64) * m
        fI, fI2 = np.fft.rfft2(I, shape), np.fft.rfft2(I * I, shape)
        sI2 = np.fft.irfft2(fI2 * fm, shape)[h - 1:H, w - 1:W]
        sIT = np.fft.irfft2(fI * np.fft.rfft2(T[::-1, ::-1], shape), shape)[h - 1:H, w - 1:W]
        total += sI2 - 2 * sIT + (T * T).sum()
    return total


def scaled(item, s):
    return item.resize((max(2, round(item.width * s)), max(2, round(item.height * s))), Image.LANCZOS)


def locate(concept, item):
    """(error, x, y, scale): the item may have been drawn bigger or smaller in the picture."""
    small = 4
    cs = np.array(concept.resize((concept.width // small, concept.height // small), Image.BOX))
    coarse = None
    for s in np.arange(0.5, 1.61, 0.05):
        it = scaled(item, s / small)
        mask = np.array(it)[..., 3] > 128
        if not mask.any() or it.width >= cs.shape[1] or it.height >= cs.shape[0]:
            continue
        ssd = masked_ssd(cs, np.array(it.convert('RGB')), mask) / mask.sum()
        y, x = np.unravel_index(np.argmin(ssd), ssd.shape)
        if coarse is None or ssd[y, x] < coarse[0]:
            coarse = (ssd[y, x], x * small, y * small, s)
    _, cx, cy, cs_ = coarse
    full = np.array(concept)
    best = None
    for s in (cs_ - 0.03, cs_ - 0.015, cs_, cs_ + 0.015, cs_ + 0.03):
        it = scaled(item, s)
        rgb, alpha = np.array(it.convert('RGB')).astype(np.int32), np.array(it)[..., 3] > 128
        for dy in range(-small * 2, small * 2 + 1, 2):
            for dx in range(-small * 2, small * 2 + 1, 2):
                X, Y = cx + dx, cy + dy
                if X < 0 or Y < 0 or X + it.width > full.shape[1] or Y + it.height > full.shape[0]:
                    continue
                d = full[Y:Y + it.height, X:X + it.width].astype(np.int32) - rgb
                err = float((d * d).sum(2)[alpha].mean())
                if best is None or err < best[0]:
                    best = (err, int(X), int(Y), round(float(s), 3))
    return best


# Default layout for rooms whose items were drawn on their own sheet (not cut from the concept, so
# matching finds nothing). Every room has the same shape: back wall down to y~500 with a window in
# the middle, floor from ~500 to ~880, foreground below. Kinds come from the item's file name.
WALL = ('banner', 'wall', 'hanging-herb', 'hanging-net', 'gear-clock', 'shell-lamp', 'pickaxe-rack',
        'dusty-shelf', 'clay-shelf', 'buoy')
CEILING = ('lava-lamp', 'hanging-lantern', 'diamond-lamp', 'golden-lantern', 'jellyfish-lantern', 'amber-crystal-lamp')
# (centre x, bottom y) on the 1448x1086 room; ceiling slots give the top y
BOWL, BED, RUG = (480, 790), (290, 650), (760, 810)
WALL_SLOTS = [(150, 470), (1300, 470), (380, 470), (1070, 470)]
CEILING_SLOTS = [(540, 40), (910, 40)]
# tallest things go to the back, behind where the pet walks; small ones to the sides
FLOOR_SLOTS = [(850, 600), (1080, 600), (620, 610), (1320, 620), (90, 760), (1370, 760),
               (200, 880), (1250, 880), (1180, 740)]
FLOOR_MAX_W = 280


def kind(name):
    n = name.lower()
    if n.startswith('01_'):
        return 'bowl'
    if n.startswith('02_'):
        return 'bed'
    if '-rug' in n or '-carpet' in n:
        return 'rug'
    if any(w in n for w in CEILING):
        return 'ceiling'
    if any(w in n for w in WALL):
        return 'wall'
    return 'floor'


def layout(room):
    """{file: [x, y, scale]} from the slots above; anything over the slots is put out of the way
    at the front corners (the player moves items anyway)."""
    items = {os.path.basename(p): Image.open(p).size for p in sorted(glob.glob(os.path.join(DECOR, room, '*.png')))}
    free = {'wall': list(WALL_SLOTS), 'ceiling': list(CEILING_SLOTS), 'floor': list(FLOOR_SLOTS)}
    out = {}

    def put(name, cx, y, s, top=False):
        w, h = items[name]
        out[name] = [round(cx - w * s / 2), round(y if top else y - h * s), round(s, 3)]
    by_height = sorted(items, key=lambda n: -items[n][1])
    for name in by_height:
        k = kind(name)
        w, h = items[name]
        if k in ('bowl', 'bed', 'rug'):
            put(name, *{'bowl': BOWL, 'bed': BED, 'rug': RUG}[k], 1.0)
            continue
        slots = free[k] or free['floor'] or [(200, 880)]
        cx, y = slots.pop(0)
        s = min(1.0, FLOOR_MAX_W / w) if k == 'floor' else 1.0
        put(name, cx, y, s, top=k == 'ceiling')
    return out


def main(rooms):
    for room in rooms:
        if room not in REFERENCE:
            found = layout(room)
            for name, (x, y, s) in found.items():
                print(f'{room}/{name}: {kind(name)} ({x}, {y}) x{s}')
        else:
            concept = Image.open(REFERENCE[room]).convert('RGB')
            found = {}
            for path in sorted(glob.glob(os.path.join(DECOR, room, '*.png'))):
                item = Image.open(path).convert('RGBA')
                err, x, y, scale = locate(concept, item)
                found[os.path.basename(path)] = [x, y, scale]
                print(f'{room}/{os.path.basename(path)}: ({x}, {y}) x{scale} error {err:.0f}')
        with open(os.path.join(DECOR, room, 'vi-tri.json'), 'w', encoding='utf-8') as fh:
            json.dump(found, fh, indent=1)


if __name__ == '__main__':
    main(sys.argv[1:] or ['L1-HO_hang-da'])
