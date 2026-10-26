"""Cut a creature's sheet (4 columns, transparent or on magenta) into game frames.

Layouts (LAYOUTS): adult/legend 4x6, four legs 4x6, baby/child/teen 4x4, egg 4x2; the cell size follows the image.
Every frame is put on one shared canvas with the feet on the same baseline and the body
on the same centre line, so swapping frames never makes the creature jump around.
Writes assets/creatures/<element>/<slug>/<stage>/png/<name>.png (transparent, hard edge), .../bmp/<name>.bmp
(magenta 255,0,255 colour key for SDL 1.2) and .../frames.json.
With HOLUA_SCREEN=640 (R36S, SDL2 blends alpha): assets/creatures-640/..., twice the size, png with the
soft edge of the downscale kept, no bmp.
Usage: python slice_frames.py [slug | element | stage ...]   (see creatures.selected)
"""
import json, os, sys
import numpy as np
from PIL import Image

import creatures

SCALE = 0.5          # adult: source body is ~220 px tall -> ~110 px on the 320x240 screen
# younger stages are scaled so their first idle frame is this tall on screen: they grow up visibly
TARGET_H = {'egg': 44, 'baby': 52, 'child': 70, 'teen': 90, 'legend': 126,
            'adult4': 80, 'legend4': 92}  # four legs: lower and longer than standing
# a legend is drawn GROW times as tall as the same creature as an adult (its sheet may be drawn smaller);
# TARGET_H is used only when that adult is not cut yet
GROW = {'legend': ('adult', 1.0), 'legend4': ('adult4', 1.0)}    # the user, 25/10: legend as tall as adult (was 1.15)
GROUP_PX = 8         # loose pieces closer than this belong together (a volley of darts)
BELOW_FEET_PENALTY = 60  # how much nearer a body in the row below must be to take a piece under feet
WEAK = 0.3            # a cell whose body is under 30% of the usual body size lost its body to a neighbour

LAYOUTS = {
    'adult': [
        ['idle-0', 'idle-1', 'idle-2', 'idle-3'],
        ['punch-0', 'punch-1', 'punch-2', 'punch-3'],
        ['blast-0', 'blast-1', 'blast-2', 'blast-3'],
        ['block', 'hurt', 'faint', 'victory'],
        ['eat', 'jump-happy', 'tired', 'sick'],
        ['sleep-0', 'sleep-1', 'yawn', 'flex'],
    ],
    'young': [
        ['idle-0', 'idle-1', 'idle-2', 'idle-3'],
        ['walk-0', 'walk-1', 'walk-2', 'walk-3'],
        ['eat', 'jump-happy', 'tired', 'sick'],
        ['sleep-0', 'sleep-1', 'yawn', 'flex'],
    ],
    'four': [
        ['idle-0', 'idle-1', 'idle-2', 'idle-3'],
        ['walk-0', 'walk-1', 'walk-2', 'walk-3'],
        ['run-0', 'run-1', 'run-2', 'run-3'],
        ['attack', 'hurt', 'faint', 'victory'],
        ['eat', 'jump-happy', 'tired', 'sick'],
        ['sleep-0', 'sleep-1', 'yawn', 'flex'],
    ],
    'egg': [
        ['egg-0', 'egg-1', 'egg-2', 'egg-3'],
        ['crack-0', 'crack-1', 'burst', 'shell'],
    ],
    # <..>_<stage>_extra.png (creatures.extra_sheet): eating and playing in steps, refusing food, being petted,
    # waving, sad, angry. 'ref' stands like
    # idle-0 and only sets the size: the sheet is scaled so it matches the main sheet's idle-0.
    'extra': [
        ['ref', 'eat-look', 'eat-bite', 'eat-chew'],
        ['eat-lick', 'play-crouch', 'play-jump', 'play-air'],
        ['play-spin', 'play-land', 'play-cheer', 'refuse'],
        ['petted', 'wave', 'sad', 'angry'],
    ],
}

def magenta(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (r > 170) & (g < 110) & (b > 170) & (np.abs(r - b) < 60)

def column_runs(mask):
    used = mask.any(0)
    runs, start = [], None
    for x, on in enumerate(used):
        if on and start is None: start = x
        if not on and start is not None: runs.append((start, x)); start = None
    if start is not None: runs.append((start, len(used)))
    return [r for r in runs if r[1] - r[0] > 3]

def near_edge(fg, px):
    """Foreground pixels within px pixels of a transparent one."""
    inner = fg.copy()
    for _ in range(px):
        shrunk = inner.copy()
        shrunk[1:] &= inner[:-1]; shrunk[:-1] &= inner[1:]
        shrunk[:, 1:] &= inner[:, :-1]; shrunk[:, :-1] &= inner[:, 1:]
        inner = shrunk
    return fg & ~inner


def split_by_columns(fg, layout, ch):
    """One mask per frame when every row band holds its sprites with empty columns between
    them, each in its own column cell, and nothing crosses into the rows above or below;
    None otherwise (two touching sprites plus a loose spark can also make 4 runs)."""
    masks = []
    cw = fg.shape[1] / len(layout[0])
    for row, names in enumerate(layout):
        y0, y1 = round(row * ch), round((row + 1) * ch)
        band = fg[y0:y1]
        runs = column_runs(band)
        if len(runs) != len(names) or band[0].any() or band[-1].any():
            return None
        if any(int((x0 + x1) / 2 // cw) != k for k, (x0, x1) in enumerate(runs)):
            return None
        for x0, x1 in runs:
            m = np.zeros_like(fg)
            m[y0:y1, x0:x1] = band[:, x0:x1]
            masks.append(m)
    return masks


def label(fg):
    """Connected pixels (8 neighbours) share a label; 0 is background. A part's label is 1 + the flat index of its
    first pixel (row by row). With scipy installed the same labels come out of ndimage, many times faster."""
    try:
        from scipy import ndimage
    except ImportError:
        return label_numpy(fg)
    lab, n = ndimage.label(fg, structure=np.ones((3, 3), bool))
    first = np.full(n + 1, lab.size, np.int64)
    flat = lab.ravel()
    np.minimum.at(first, flat, np.arange(1, lab.size + 1))
    first[0] = 0
    return first[lab]


def label_numpy(fg):
    h, w = fg.shape
    big = h * w + 1
    lab = np.where(fg, np.arange(1, h * w + 1).reshape(h, w), big)
    while True:
        m = lab.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy or dx:
                    sh = np.full_like(lab, big)
                    sh[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = \
                        lab[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
                    m = np.minimum(m, sh)
        m = np.where(fg, m, big)
        m = np.minimum(m, m.ravel()[np.clip(m - 1, 0, h * w - 1)].reshape(h, w))  # jump to the root
        m = np.where(fg, m, big)
        if (m == lab).all():
            break
        lab = m
    return np.where(fg, lab, 0)


def split_by_blobs(fg, unit, layout, cw, ch):
    """For sheets whose sprites touch: the biggest blob in each cell is that frame's body.
    The other blobs (sparks, rocks, a raised shield, smoke, a volley of darts) are grouped with
    their close neighbours first, so a volley that crosses a cell border stays together; a group
    joins the body of the cell its centre is in, unless another body is far nearer."""
    lab = label(fg)
    cells = [(r, c) for r in range(len(layout)) for c in range(len(layout[r]))]
    smallest = 0.03 * cw * ch          # a body covers at least ~3% of its cell

    def find_bodies():
        ids, counts = np.unique(lab[lab > 0], return_counts=True)
        blobs = []
        for i, n in zip(ids, counts):
            ys, xs = np.where(lab == i)
            blobs.append(dict(id=i, n=n, box=(xs.min(), ys.min(), xs.max(), ys.max()),
                              c=(xs.mean(), ys.mean())))
        bodies = {}
        for bl in blobs:
            cell = (int(bl['c'][1] // ch), int(bl['c'][0] // cw))
            if cell not in bodies or bl['n'] > bodies[cell]['n']:
                bodies[cell] = bl
        return blobs, bodies, [cell for cell in cells if cell not in bodies or bodies[cell]['n'] < smallest]

    blobs, bodies, missing = find_bodies()
    # Two neighbours that touch (a cape brushing the next frame's fist, a jump reaching up into the
    # row above) form one blob and leave a cell empty, or with only a splash in it: cut that blob
    # at its thinnest line between the two cell centres.
    median = float(np.median([bodies[cell]['n'] for cell in cells if cell in bodies]))
    weak = [cell for cell in cells if cell not in bodies or bodies[cell]['n'] < max(smallest, WEAK * median)]
    for r, c in weak:
        best = None
        for nr, nc in ((r, c - 1), (r, c + 1), (r - 1, c), (r + 1, c)):
            if (nr, nc) not in bodies or (nr, nc) in weak:
                continue
            bid = bodies[(nr, nc)]['id']
            box = (round(c * cw), round(r * ch), round((c + 1) * cw), round((r + 1) * ch))
            inside = (lab[box[1]:box[3], box[0]:box[2]] == bid).sum()
            if inside > 0.1 * median and (best is None or inside > best[0]):
                best = (inside, bid, nr, nc)
        if best is None:
            continue
        _, bid, nr, nc = best
        side = np.zeros_like(fg)
        if nr == r:
            a, b = round((min(c, nc) + 0.5) * cw), round((max(c, nc) + 0.5) * cw)
            cut = a + int(np.argmin((lab[:, a:b] == bid).sum(0)))
            if nc > c:
                side[:, :cut] = True
            else:
                side[:, cut:] = True
            where = f'x={cut}'
        else:
            a, b = round((min(r, nr) + 0.5) * ch), round((max(r, nr) + 0.5) * ch)
            cut = a + int(np.argmin((lab[a:b] == bid).sum(1)))
            if nr > r:
                side[:cut] = True
            else:
                side[cut:] = True
            where = f'y={cut}'
        lab[(lab == bid) & side] = lab.max() + 1
        print(f'{unit}: cell {(r, c)} was joined to {(nr, nc)}, cut at {where}')
    if weak:
        blobs, bodies, missing = find_bodies()
    if missing:
        sys.exit(f'{unit}: no sprite found in cells {missing}')
    owner = {bodies[cell]['id']: cell for cell in cells}

    loose = np.isin(lab, [bl['id'] for bl in blobs if bl['id'] not in owner])
    grown = loose.copy()
    for _ in range(GROUP_PX):
        g = grown.copy()
        g[1:] |= grown[:-1]; g[:-1] |= grown[1:]
        g[:, 1:] |= grown[:, :-1]; g[:, :-1] |= grown[:, 1:]
        grown = g
    group_of = label(grown)
    groups = {}
    for bl in blobs:
        if bl['id'] in owner:
            continue
        x0, y0, x1, y1 = bl['box']
        gid = group_of[y0:y1 + 1, x0:x1 + 1][lab[y0:y1 + 1, x0:x1 + 1] == bl['id']][0]
        groups.setdefault(gid, []).append(bl)

    def gap(c, body):
        x0, y0, x1, y1 = body['box']
        return max(x0 - c[0], 0, c[0] - x1) + max(y0 - c[1], 0, c[1] - y1)
    for members in groups.values():
        n = sum(bl['n'] for bl in members)
        c = (sum(bl['c'][0] * bl['n'] for bl in members) / n, sum(bl['c'][1] * bl['n'] for bl in members) / n)
        nearest = min(cells, key=lambda cell: gap(c, bodies[cell]))
        home = (int(c[1] // ch), int(c[0] // cw))
        if home not in bodies or gap(c, bodies[home]) > 2 * gap(c, bodies[nearest]) + 20:
            home = nearest
        # a piece hanging under a body's feet is usually the top (raised hands, dizzy swirls) of the
        # sprite in the row below; dust under a jump stays, as nothing below is near it
        if min(bl['box'][1] for bl in members) > bodies[home]['box'][3] + 3:
            below = [cell for cell in cells if cell[0] == home[0] + 1]
            if below:
                under = min(below, key=lambda cell: gap(c, bodies[cell]))
                if gap(c, bodies[under]) < gap(c, bodies[home]) + BELOW_FEET_PENALTY:
                    home = under
        for bl in members:
            owner[bl['id']] = home
    masks = {cell: np.zeros_like(fg) for cell in cells}
    for i, cell in owner.items():
        masks[cell] |= lab == i
    return [masks[cell] for cell in cells]


# activity sheets (creatures.ACTS, 4x2, no reference cell): how tall a frame is next to idle-0 - the tallest
# ball / medicine frame stands upright like idle-0, the median bath frame is the creature sitting in its tub
ACT_HEIGHT = {'choi': ('max', 1.0), 'thuoc': ('max', 1.0), 'tam': ('median', 0.95), 'front': ('median', 1.0),
              'di': ('median', 1.0)}


def cut(unit, path, layout):
    """[{name, img (RGBA at sheet size), ax, h, w, k}] in layout order; k = 1 (scale to the main sheet)"""
    src = Image.open(path)
    if src.mode == 'P' and 'transparency' in src.info:     # a 256-colour see-through sheet (optimize_sheet.py)
        src = src.convert('RGBA')
    cw, ch = src.size[0] / len(layout[0]), src.size[1] / len(layout)
    rgb = np.array(src.convert('RGB')).astype(np.int32)
    # a real see-through sheet uses its alpha; an opaque one (even saved as RGBA) is on magenta
    alpha = np.array(src)[..., 3] if src.mode == 'RGBA' else None
    fg = alpha > 0 if alpha is not None and (alpha == 0).any() else ~magenta(rgb)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # magenta spill: pinkish pixels on the outline (and the purple floor line) go,
    # pinkish pixels inside lose their blue so flame edges turn red/orange instead of pink.
    # Bright blue-violet (red well below a strong blue) is water/metal glow, not spill.
    pink = (b > g + 50) & (r > g + 30) & ~((r * 10 < b * 6) & (b > 150))
    fg &= ~(pink & near_edge(fg, 3))
    rgb[..., 2] = np.where(pink, np.minimum(b, g + 10), b)
    masks = split_by_columns(fg, layout, ch)
    if masks is None:
        print(f'{unit}: sprites touch or cross cell borders, splitting by blobs')
        masks = split_by_blobs(fg, unit, layout, cw, ch)
    frames = []
    for mask, name in zip(masks, [n for names in layout for n in names]):
        ys = np.where(mask.any(1))[0]
        xs = np.where(mask.any(0))[0]
        y0, y1, x0, x1 = ys[0], ys[-1] + 1, xs[0], xs[-1] + 1
        m = mask[y0:y1, x0:x1]
        # anchor: the middle of the feet (lowest 24 rows), bottom = lowest pixel
        feet = np.where(m[-24:].any(0))[0]
        ax = (feet[0] + feet[-1]) / 2.0
        rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        rgba[..., :3] = rgb[y0:y1, x0:x1]
        rgba[..., 3] = m * 255
        frames.append(dict(name=name, img=rgba, ax=ax, h=y1 - y0, w=x1 - x0, k=1.0))
    return frames


def target_h(cid, stage):
    """How tall (320 screen px) the first idle frame of this unit is drawn."""
    if stage in GROW:
        base, k = GROW[stage]
        p = os.path.join(creatures.frames_dir(cid, base), 'png', 'idle-0.png')
        if os.path.exists(p):
            box = Image.open(p).getchannel('A').point(lambda a: 255 if a >= 110 else 0).getbbox()
            if box:
                return (box[3] - box[1]) / creatures.SIZE * k
    return TARGET_H[stage]


def main(cid, stage):
    unit = f'{cid}/{stage}'
    out = creatures.frames_dir(cid, stage)
    frames = cut(unit, creatures.sheet(cid, stage), LAYOUTS[creatures.LAYOUT[stage]])
    extra = creatures.extra_sheet(cid, stage)
    if extra:
        more = cut(unit + ' extra', extra, LAYOUTS['extra'])
        k = frames[0]['h'] / more[0]['h']      # its 'ref' as tall as idle-0
        frames += [dict(f, k=k) for f in more[1:]]
    for kind, path in creatures.act_sheets(cid, stage).items():
        name = creatures.ACTS[kind]
        names = creatures.FRONT_FRAMES if kind == 'front' else [[f'{name}-{i}' for i in range(4)]] if kind == 'di' \
            else [[f'{name}-{i}' for i in range(r, r + 4)] for r in (0, 4)]
        more = cut(f'{unit} {kind}', path, names)
        how, times = ACT_HEIGHT[kind]
        k = frames[0]['h'] * times / float(getattr(np, how)([f['h'] for f in more]))
        frames += [dict(f, k=k) for f in more]
    scale = (SCALE if stage == 'adult' else target_h(cid, stage) / frames[0]['h']) * creatures.SIZE
    left = max(f['ax'] * f['k'] for f in frames)
    right = max((f['w'] - f['ax']) * f['k'] for f in frames)
    top = max(f['h'] * f['k'] for f in frames)
    W = int(np.ceil((left + right) * scale)) + 4
    H = int(np.ceil(top * scale)) + 2
    anchor_x = int(round(left * scale)) + 2
    keyed = creatures.SCREEN == 320          # SDL 1.2: colour key, no alpha blending
    os.makedirs(os.path.join(out, 'png'), exist_ok=True)
    if keyed:
        os.makedirs(os.path.join(out, 'bmp'), exist_ok=True)
    meta = dict(canvas=[W, H], anchor=[anchor_x, H - 1], scale=round(scale, 4),
                layout=creatures.LAYOUT[stage], frames=[])
    for f in frames:
        img = Image.fromarray(f['img'], 'RGBA')
        w, h = max(1, round(f['w'] * scale * f['k'])), max(1, round(f['h'] * scale * f['k']))
        # premultiplied area downscale (edge pixels take only the creature's colours), then a hard
        # alpha edge for the colour key
        arr = np.array(img).astype(np.float32)
        arr[..., :3] *= arr[..., 3:4] / 255.0
        small = np.array(Image.fromarray(arr.astype(np.uint8), 'RGBA').resize((w, h), Image.BOX)).astype(np.float32)
        a = small[..., 3:4]
        small[..., :3] = np.where(a > 0, small[..., :3] * 255.0 / np.maximum(a, 1), 0)
        if keyed:
            small[..., 3] = np.where(small[..., 3] >= 110, 255, 0)
        small = small.clip(0, 255).astype(np.uint8)
        canvas = np.zeros((H, W, 4), np.uint8)
        px = anchor_x - int(round(f['ax'] * scale * f['k']))
        py = H - 1 - h + 1
        canvas[py:py + h, px:px + w] = small
        Image.fromarray(canvas, 'RGBA').save(os.path.join(out, 'png', f['name'] + '.png'))
        meta['frames'].append(f['name'])
        if not keyed:
            continue
        bmp = canvas[..., :3].copy()
        # keep real pixels away from the exact key colour
        key = (bmp[..., 0] == 255) & (bmp[..., 1] == 0) & (bmp[..., 2] == 255)
        bmp[key] = (254, 0, 254)
        bmp[canvas[..., 3] == 0] = (255, 0, 255)
        Image.fromarray(bmp, 'RGB').save(os.path.join(out, 'bmp', f['name'] + '.bmp'))
    with open(os.path.join(out, 'frames.json'), 'w') as fh:
        json.dump(meta, fh, indent=2)
    print(f'{unit}: {len(frames)} frames, canvas {W}x{H}, anchor {anchor_x},{H - 1}')

if __name__ == '__main__':
    for cid, stage in creatures.selected():
        main(cid, stage)
