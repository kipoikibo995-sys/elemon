"""Vùng đất (game/src/vung-dat.js): the region maps and the pictures the fights on them use, made from the painted
top-down maps in assets/source/vung-dat/<he>/*.png (one per khu, 1536x1024, in name order: the last one is the boss's),
the gate scenes in assets/5 vùng/ and the Solo arena's sheets (preview/dau-truong/img/<pet>/).

Written into the page (game/build_game.py calls build(page)):
    img/vg/<he>/cong.png          the region's gate scene, 640x480
    img/vg/<he>/k<n>.png          a khu's map at 1:1, its tà khí (purple crystals and smoke) taken out and filled with
                                  the ground round it (copied from a clean spot nearby)
    img/vg/<he>/k<n>_o<i>.png     the tà khí cut out: a nest, drawn over the map while it stands
    img/vg/pet/<dir>.png          a pet's body on the map: 5 directions (s se e ne n) x 12 poses (idle 4, walk 4,
                                  strike 2, skill, hurt), each feet-down in a cell of the same size, outlined
    img/vg/fx/<dir>.png           its effects on the map: fx1's slash in 8 directions and hit, fx2's shot in 8
                                  directions and burst, each centred in a cell of its group's size
    img/vg/fx/<dir>_u.png         and fx4, its ultimate (loaded for the pet raised and a boss only)
    sfx/solo/<he>_<k>.wav         the element sounds (the R36S packer, solo_r36s.py, makes the same files)
build() returns the data vung-dat.js is built with (sizes, cells, walk grids, exits, nests).
What it worked out of the maps can be looked at: python scripts/vung_dat.py --xem -> build/vung-dat/xem/
Cut pictures are kept in build/vung-dat/ (made again when their sources change).
Usage: python scripts/vung_dat.py [--xem]       (HOLUA_VUNG_SRC=<folder of <he>/ folders> reads other maps)
       python scripts/vung_dat.py --thu [--dist]   the test copy (test_copy()), and the R36S test package with it
"""
import glob, hashlib, json, os, re, shutil, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.environ.get('HOLUA_VUNG_SRC') or os.path.join(ROOT, 'assets', 'source', 'vung-dat')
GATES = os.path.join(ROOT, 'assets', '5 vùng')
ARENA = os.path.join(ROOT, 'preview', 'dau-truong')
CACHE = os.path.join(ROOT, 'build', 'vung-dat')
VERSION = 10                                  # bump to cut everything again

MAP_W, MAP_H = 1536, 1024                    # a khu, drawn 1:1 (about 2.4 x 2.1 screens)
C = 16                                       # px, a walk-grid cell
PATH_TOL = 110                               # the path: colour distance from its seed's
LINE_K, GROUND_K = 0.4, 0.35                 # an outline: darker than this share of the ground; a ground cell: this much reached
EXIT_W = 176                                 # px, the widest a way out may be
PORTAL = 90000                               # px, a tà khí patch this big is a gate (the boss's), not a nest
BODY_H = 60                                  # px, the pet standing (idle, facing us) on the map
OUTLINE = (26, 12, 6)
BODY = ['s', 'se', 'e', 'ne', 'n']           # the arena's direction sheets (sw, w, nw are these mirrored)
POSES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14]   # of each sheet's 16: idle 0-3, walk 4-7, strike 8-9, skill 10, hurt 14
# effect groups: (sheet, its cols x rows, frames, turned to 8 directions, longest side in px)
FX = {'slash': ('fx1', 4, 2, [0, 1, 2, 3], True, 84), 'hit': ('fx1', 4, 2, [4, 5, 6, 7], False, 60),
      'shot': ('fx2', 4, 2, [0, 1, 2, 3], True, 52), 'burst': ('fx2', 4, 2, [4, 5, 6, 7], False, 76),
      'ult': ('fx4', 4, 3, list(range(12)), False, 190)}
SOUNDS = ['danh', 'ban', 'trung', 'luot', 'ult', 'vung']

# a region: its gate scene, the tà khí-ridden spirits on its maps (pet folder, how it fights), its boss; a khu's
# settings by its file name: name, seed (a point on its dirt path, near where it comes in: the path is found from
# it), walk-grid fixes as ('walk' | 'block', x0, y0, x1, y1) in map px
K = lambda name, x, y, *fix, ways=('bottom', 'top'), exits=None: dict(name=name, seed=(x, y), fix=list(fix), ways=ways, exits=exits)
BOSS = ('bottom',)                           # a boss khu is entered from below and has no way on
REGIONS = {
    'hoa': dict(name='Vùng Hỏa · Núi lửa', gate='00c03be8-2fcb-491b-86c7-3baa5757279a.png',
                mobs=[['hoa-ho-cao', 'nhanh'], ['hoa-quy', 'trau'], ['hoa-linh', 'ban'], ['dung-nham-ve', 'trau'],
                      ['hoa-ho', 'can']], boss='viem-long',
                khu={'khu1_rung-thu': K('Rừng lá đỏ', 780, 990),
                     # bridges, the stairs and the yard up to the gate walkable, the forge's buildings not
                     'khu2_lo-ren': K('Lò rèn khói tím', 70, 1000, ('walk', 1245, 0, 1400, 300), ('walk', 96, 432, 236, 520), ('walk', 800, 690, 960, 760),
                                      ('walk', 1170, 230, 1330, 365), ('walk', 1245, 190, 1400, 300),
                                      ('block', 300, 236, 705, 340), ('block', 615, 330, 700, 392),
                                      exits=[['bottom', 16, 128], ['top', 1260, 1400]]),
                     'khu3_cong-nui-lua': K('Cổng núi lửa', 470, 990, ('walk', 640, 190, 1170, 340), ways=BOSS)}),
    'kim': dict(name='Vùng Kim · Núi pha lê', gate='Snowy Crystal Mountain Mine.png',
                mobs=[['kim-te', 'trau'], ['tinh-kim-hiep', 'nhanh'], ['liem-dao', 'can'], ['kim-giap', 'trau'],
                      ['kim-thach-nhan', 'ban']], boss='kim-ung',       # the story's Thần thú of the Kim region
                khu={'khu1_suon-tuyet': K('Sườn tuyết', 730, 990, ('walk', 830, 0, 1000, 480), exits=[['bottom', 650, 820], ['top', 830, 1000]]), 'khu2_mo-pha-le': K('Mỏ pha lê', 640, 1000, exits=[['bottom', 592, 704], ['top', 880, 990]]),
                     'khu3_cong-bang': K('Cổng băng', 450, 965, ('walk', 600, 190, 1180, 400), ways=BOSS)}),
    'moc': dict(name='Vùng Mộc · Rừng cổ thụ', gate='Enchanted Forest Root Cavern.png',
                mobs=[['moc-loc', 'nhanh'], ['moc-tru', 'trau'], ['reu-linh', 'ban'], ['diep-linh', 'ban'],
                      ['moc-duong', 'can']], boss='thu-nhan',
                khu={'khu1_bia-rung': K('Bìa rừng', 640, 965), 'khu2_rung-sau': K('Rừng sâu', 580, 990),
                     'khu3_cong-re': K('Cổng rễ cổ thụ', 680, 900, ('walk', 520, 290, 1080, 520), ways=BOSS)}),
    'thuy': dict(name='Vùng Thủy · Hồ thác', gate='Mystic Whirlpool Waterfall Valley.png',
                 mobs=[['thuy-sa', 'nhanh'], ['thuy-giai', 'trau'], ['bao-thuy', 'ban'], ['thuy-chien', 'can'],
                       ['thuy-giao', 'nhanh']], boss='thuy-long',
                 khu={'khu1_bo-ho': K('Bờ hồ', 720, 965), 'khu2_thac-nuoc': K('Thung lũng thác', 720, 900,
                                                                               ('walk', 580, 440, 880, 660),
                                                                               exits=[['bottom', 608, 768], ['top', 980, 1120]]),
                      'khu3_cong-xoay-nuoc': K('Cổng xoáy nước', 690, 900, ('walk', 590, 210, 1110, 500),
                                               ('walk', 660, 500, 840, 650), ways=BOSS)}),
    'tho': dict(name='Vùng Thổ · Hẻm vực', gate='Amber Cave Beneath the Desert Arch.png',
                mobs=[['tho-tich', 'nhanh'], ['thach-nhan', 'trau'], ['tho-tuong', 'trau'], ['thanh-tri', 'ban'],
                      ['tho-nguu', 'can']], boss='tho-long',
                khu={'khu1_hem-cat': K('Hẻm cát', 700, 965), 'khu2_hang-ho-phach': K('Hang hổ phách', 700, 990, ('walk', 850, 0, 990, 150), exits=[['bottom', 612, 788], ['top', 860, 980]]),
                     'khu3_cong-da': K('Cổng đá', 690, 990, ('walk', 560, 300, 1180, 560), ways=BOSS, exits=[['bottom', 600, 790]])}),
}
# the arena a mini boss is fought in (assets/r36s/dau-truong, Solo's): a stone ring round a floor, 640x480
SAN = {'hoa': 'hoa_nui-lua', 'kim': 'kim_nui-tuyet', 'moc': 'moc_rung-xanh', 'thuy': 'thuy_den-bao', 'tho': 'tho_hem-da-do'}
# the painted maps darkened and their contrast lowered a little, so the pets and foes stand out on them
MAP_CONTRAST, MAP_BRIGHT, MAP_SAT = 0.8, 0.86, 0.88


def save(im, path, **kw):
    """A picture written whole or not at all (a temporary file renamed): another build (game/build_game.py) may be
    making the same cache at the same time."""
    tmp = f'{path}.{os.getpid()}.tmp.png'
    im.save(tmp, **kw)
    os.replace(tmp, path)


# ---------------------------------------------------------------- small array tools

def grow(m, r):
    """A bool mask grown by r px (square)."""
    if r <= 0:
        return m
    out = m.copy()
    h, w = m.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx or dy:
                out[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)] |= m[max(0, -dy):h + min(0, -dy), max(0, -dx):w + min(0, -dx)]
    return out


def parts(m):
    """Connected parts (8-neighbour) of a small bool grid: lists of (y, x)."""
    seen, out = np.zeros_like(m, bool), []
    h, w = m.shape
    for y0, x0 in zip(*np.nonzero(m)):
        if seen[y0, x0]:
            continue
        stack, part = [(y0, x0)], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            part.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    Y, X = y + dy, x + dx
                    if 0 <= Y < h and 0 <= X < w and m[Y, X] and not seen[Y, X]:
                        seen[Y, X] = True
                        stack.append((Y, X))
        out.append(part)
    return out


def hsv(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    return r, g, b, mx, (mx - mn) / np.maximum(mx, 1)


# ---------------------------------------------------------------- a khu's map

def taint(a):
    """Tà khí: the core (the strong magenta-purple of its smoke and crystals: the lavender rock tops are far greyer)
    and its softer edge pixels (crystal highlights, smoke edges)."""
    r, g, b, mx, sat = hsv(a)
    core = (sat > 0.62) & (b > 140) & (b > g + 80) & (r > g + 60)
    soft = (sat > 0.3) & (b > g + 30) & (r > g + 20) & (b > 80) & (b * 10 >= r * 6)
    return core, soft


def fill(a, hole, x0, y0, bad):
    """Fills hole (a mask of the box at x0, y0) with pixels copied from the clean spot nearby whose ring round the
    hole matches best: the ground's own texture, not a smear."""
    h, w = hole.shape
    H, W = a.shape[:2]
    ring = grow(hole, 4) & ~hole
    here = a[y0:y0 + h, x0:x0 + w]
    best, pick = None, None
    span = max(w, h)
    for rad in range(max(12, span // 2), span * 3, 8):
        for k in range(16):
            t = k * np.pi / 8
            dx, dy = int(round(rad * np.cos(t))), int(round(rad * np.sin(t)))
            sx, sy = x0 + dx, y0 + dy
            if sx < 0 or sy < 0 or sx + w > W or sy + h > H:
                continue
            if bad[sy:sy + h, sx:sx + w][grow(hole, 2)].any():
                continue
            src = a[sy:sy + h, sx:sx + w]
            score = np.abs(src[ring] - here[ring]).sum()
            if best is None or score < best:
                best, pick = score, src.copy()
        if pick is not None and rad > span:
            break
    if pick is not None:
        here[hole] = pick[hole]


def tone(px):
    """The map's look in the game (MAP_CONTRAST, MAP_BRIGHT, MAP_SAT) on RGB pixels, int arrays."""
    f = px.astype(np.float32)
    grey = f.mean(-1, keepdims=True)
    f = grey + (f - grey) * MAP_SAT
    f = (128 + (f - 128) * MAP_CONTRAST) * MAP_BRIGHT
    return np.clip(np.round(f), 0, 255).astype(px.dtype)


def khu_map(src, k, he):
    """A khu's painted map -> (map without tà khí, nests [(sprite, x, y)], walk grid rows, exits, gate). k: its
    settings (REGIONS[he]['khu'][stem])."""
    im = Image.open(src).convert('RGB')
    if im.size != (MAP_W, MAP_H):
        im = im.resize((MAP_W, MAP_H), Image.LANCZOS)
    a = np.asarray(im).astype(np.int16).copy()
    core, soft = taint(a)
    # the nests: parts of the tà khí on an 8 px grid; a nest is the core grown into its soft edge, and 2 px more
    G = 8
    gh, gw = MAP_H // G, MAP_W // G
    cells = core[:gh * G, :gw * G].reshape(gh, G, gw, G).mean(axis=(1, 3)) > 0.04
    near = grow(core, 8)
    whole = grow(core | (soft & near), 2)
    nests, gate = [], None
    for part in sorted(parts(grow(cells, 1)), key=len, reverse=True):
        if len(part) < 4 or sum(core[y * G:(y + 1) * G, x * G:(x + 1) * G].sum() for y, x in part) < 150:
            continue
        ys, xs = zip(*part)
        x0, y0 = max(0, min(xs) * G - 6), max(0, min(ys) * G - 6)
        x1, y1 = min(MAP_W, (max(xs) + 1) * G + 6), min(MAP_H, (max(ys) + 1) * G + 6)
        hole = whole[y0:y1, x0:x1].copy()
        if hole.sum() < 60:
            continue
        yy, xx = np.nonzero(hole)
        bx0, by0, bx1, by1 = xx.min(), yy.min(), xx.max() + 1, yy.max() + 1
        hole = hole[by0:by1, bx0:bx1]
        x0, y0 = x0 + bx0, y0 + by0
        if hole.size > PORTAL:                   # a whole tà khí gate: it stays painted, the boss comes out of it
            gate = [int(x0), int(y0), int(hole.shape[1]), int(hole.shape[0])]
            continue
        rgba = np.zeros(hole.shape + (4,), np.uint8)
        rgba[..., :3] = tone(a[y0:y0 + hole.shape[0], x0:x0 + hole.shape[1]])
        rgba[..., 3] = hole * 255
        nests.append((Image.fromarray(rgba), int(x0), int(y0)))
    bad = whole.copy()
    for spr, x0, y0 in nests:
        hole = np.asarray(spr)[..., 3] > 0
        fill(a, hole, x0, y0, bad)
        bad[y0:y0 + hole.shape[0], x0:x0 + hole.shape[1]] &= ~hole
    rows, exits = walk_grid(a, k.get('fix', []), k.get('seed', (MAP_W // 2, MAP_H - 30)), he)
    if k.get('exits'):
        exits = k['exits']
    else:                                       # one way out a side, on the sides the khu uses, at most EXIT_W wide
        best = {}
        for e in exits:
            if e[0] in k.get('ways', ('bottom', 'top')) and (e[0] not in best or e[2] - e[1] > best[e[0]][2] - best[e[0]][1]):
                best[e[0]] = e
        exits = []
        for side, a0, a1 in best.values():
            if side == 'bottom':                # the way in: round the seed when it is in that run
                m = k['seed'][0] if a0 <= k['seed'][0] <= a1 else (a0 + a1) // 2
            else:
                m = (a0 + a1) // 2
            exits.append([side, max(a0, m - EXIT_W // 2), min(a1, m + EXIT_W // 2)])
    clean = Image.fromarray(tone(a).astype(np.uint8))
    return clean, nests, rows, exits, gate


def walk_grid(a, fixes, seed, he):
    """The walk grid: '#' blocked, '.' ground; and the exits, where the dirt path meets the edge of the map: [side,
    from, to] along that edge. Everything standing on these maps (rocks, cliffs, trunks, bushes, buildings) is drawn
    with a dark outline, and the ground is not: the ground is what can be reached from the seed (a point on the path,
    set per khu) without crossing an outline (paint darker than LINE_K of the ground there, grown by a pixel to close
    small gaps), water or lava, worked out on a 2 px grid; a cell is ground when enough of it was reached."""
    from collections import deque
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = a.sum(-1) / 3
    gh, gw = MAP_H // C, MAP_W // C
    sx, sy = seed
    med = np.median(lum[max(0, sy - 40):sy + 10, max(0, sx - 40):sx + 40])
    water = (b > r + 40) & (g > r + 20) & (b > 150)
    lava = (r > 230) & (g > 170) & (b < 120) & (r - b > 150) if he == 'hoa' else np.zeros_like(water)
    wall = grow(lum < LINE_K * med, 1) | water | lava
    for kind, x0, y0, x1, y1 in fixes:          # the fixes count in the flood too (a bridge: crossed)
        wall[y0:y1, x0:x1] = kind == 'block'
    R = 2
    ws = wall[:gh * C, :gw * C].reshape(gh * C // R, R, gw * C // R, R).any(axis=(1, 3))
    H, Wd = ws.shape
    seen = np.zeros_like(ws)
    q = deque()
    for y in range(sy // R - 6, sy // R + 6):
        for x in range(sx // R - 6, sx // R + 6):
            if 0 <= y < H and 0 <= x < Wd and not ws[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for Y, X in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= Y < H and 0 <= X < Wd and not seen[Y, X] and not ws[Y, X]:
                seen[Y, X] = True
                q.append((Y, X))
    n = C // R
    block = ~(seen.reshape(gh, n, gw, n).mean(axis=(1, 3)) > GROUND_K)
    for kind, x0, y0, x1, y1 in fixes:
        block[y0 // C:(y1 + C - 1) // C, x0 // C:(x1 + C - 1) // C] = kind == 'block'
    # the path (the paint like the seed's) where it meets an edge on open ground: the exits
    ref = np.median(a[max(0, sy - 16):sy + 16, max(0, sx - 16):sx + 16].reshape(-1, 3), axis=0)
    pa = (np.abs(a - ref).sum(-1) < PATH_TOL)[:gh * C, :gw * C].reshape(gh, C, gw, C).mean(axis=(1, 3)) > 0.45
    pa &= ~block
    exits = []
    for side, line in (('top', pa[0] | pa[1]), ('bottom', pa[-1] | pa[-2]), ('left', pa[:, 0] | pa[:, 1]),
                       ('right', pa[:, -1] | pa[:, -2])):
        on = list(line) + [False]
        start = None
        for i, v in enumerate(on):
            if v and start is None:
                start = i
            elif not v and start is not None:
                if i - start >= 3:
                    exits.append([side, start * C, i * C])
                start = None
    # only the ground joined to the seed (the fixes may have opened or cut some)
    land = parts(~block)
    keep = [p for p in land if any(abs(y - sy // C) <= 1 and abs(x - sx // C) <= 1 for y, x in p)] or sorted(land, key=len)[-1:]
    block[:] = True
    for p in keep:
        for y, x in p:
            block[y, x] = False
    rows = [''.join('#' if block[y, x] else '.' for x in range(gw)) for y in range(gh)]
    return rows, exits


def preview(clean, nests, rows, exits, dst):
    im = clean.convert('RGBA')
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '#':
                d.rectangle([x * C, y * C, x * C + C - 1, y * C + C - 1], fill=(0, 110, 255, 100))
            elif ch == '~':
                d.rectangle([x * C + 4, y * C + 4, x * C + C - 5, y * C + C - 5], fill=(255, 240, 0, 150))
    for spr, x, y in nests:
        ov.alpha_composite(spr, (x, y))
        d.rectangle([x, y, x + spr.width, y + spr.height], outline=(255, 0, 255, 255), width=3)
    for side, a0, a1 in exits:
        box = {'top': [a0, 0, a1, 10], 'bottom': [a0, MAP_H - 10, a1, MAP_H], 'left': [0, a0, 10, a1],
               'right': [MAP_W - 10, a0, MAP_W, a1]}[side]
        d.rectangle(box, fill=(0, 255, 0, 255))
    Image.alpha_composite(im, ov).convert('RGB').save(dst)


# ---------------------------------------------------------------- the arena's sheets, cut for the map

def cut_lines(n, size, count):
    """The arena's cutLines: the emptiest line near each nominal cut."""
    out = [0]
    for i in range(1, n):
        nom, rng = round(i * size / n), round(size / n * 0.3)
        best, bc = nom, count[nom]
        d = 1
        while d <= rng and bc > 0:
            for v in (nom - d, nom + d):
                if 0 <= v < size and count[v] < bc:
                    best, bc = v, count[v]
            d += 1
        out.append(best)
    out.append(size)
    return out


def frames(path, cols, rows):
    """A sheet on magenta cut into its frames, each cropped to its paint (RGBA, full size); None for an empty one."""
    a = np.asarray(Image.open(path).convert('RGBA'))
    ink = ~((a[..., 0] > 170) & (a[..., 1] < 110) & (a[..., 2] > 170))
    H, W = ink.shape
    ys = cut_lines(rows, H, ink[:, ::2].sum(1))
    out = []
    for r in range(rows):
        band = ink[ys[r]:ys[r + 1]]
        xs = cut_lines(cols, W, band[::2].sum(0))
        for c in range(cols):
            m = band[:, xs[c]:xs[c + 1]]
            yy, xx = np.nonzero(m)
            if not len(xx):
                out.append(None)
                continue
            y0, y1, x0, x1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
            px = a[ys[r] + y0:ys[r] + y1, xs[c] + x0:xs[c] + x1].copy()
            px[..., 3] = m[y0:y1, x0:x1] * 255
            out.append(Image.fromarray(px))
    return out


def shrink(im, k, outline=False):
    """Scaled by k (smoothly, alpha kept solid as the sheets were drawn), with a 1 px dark outline if asked."""
    w, h = max(1, round(im.width * k)), max(1, round(im.height * k))
    s = np.array(im.convert('RGBa').resize((w, h), Image.LANCZOS).convert('RGBA'))
    solid = s[..., 3] >= 110
    s[..., 3] = solid * 255
    if not outline:
        return Image.fromarray(s)
    o = np.zeros((h + 2, w + 2, 4), np.uint8)
    o[1:-1, 1:-1] = s
    ring = grow(np.pad(solid, 1), 1) & ~np.pad(solid, 1)
    o[ring] = OUTLINE + (255,)
    return Image.fromarray(o)


def body_atlas(d, dst):
    """img/vg/pet/<dir>.png: 5 rows (s se e ne n) x 12 poses, every frame feet-down in a cell of one size. -> [cw, ch]"""
    sheets = {n: frames(os.path.join(ARENA, 'img', d, n + '.png'), 4, 4) for n in BODY}
    k = BODY_H / sheets['s'][0].height
    small = {n: [shrink(sheets[n][p], k, True) if sheets[n][p] else None for p in POSES] for n in BODY}
    cw = max(f.width for n in BODY for f in small[n] if f)
    ch = max(f.height for n in BODY for f in small[n] if f)
    at = Image.new('RGBA', (cw * len(POSES), ch * len(BODY)), (0, 0, 0, 0))
    for r, n in enumerate(BODY):
        for c, f in enumerate(small[n]):
            if f:
                at.alpha_composite(f, (c * cw + (cw - f.width) // 2, r * ch + ch - f.height))
    save(at, dst, optimize=True)
    return [cw, ch]


# a foe's size on the map by how it fights (vung-dat.js reads them from here: FOE_K), and its tà khí look: a little
# darker and greyer, then a purple wash (made here once, not in the game while a khu loads)
FOE_K = {'can': 0.82, 'nhanh': 0.76, 'trau': 0.9, 'ban': 0.78, 'boss': 1.35, 'mini': 1.08}
FOE_DIM, FOE_SAT, FOE_WASH = 0.92, 0.75, ((120, 30, 170), 0.3)


def foe_atlas(body, cell, k, dst):
    """The pet's map body (img/vg/pet/<dir>.png) as a foe: each cell scaled by k (whole cells, so they stay whole
    pixels), tinted. -> [cw, ch]"""
    im = Image.open(body).convert('RGBA')
    cw0, ch0 = cell
    cw, ch = round(cw0 * k), round(ch0 * k)
    out = Image.new('RGBA', (cw * len(POSES), ch * len(BODY)), (0, 0, 0, 0))
    for r in range(len(BODY)):
        for c in range(len(POSES)):
            cut = im.crop((c * cw0, r * ch0, (c + 1) * cw0, (r + 1) * ch0))
            out.paste(cut.convert('RGBa').resize((cw, ch), Image.LANCZOS).convert('RGBA'), (c * cw, r * ch))
    a = np.array(out).astype(np.float32)
    rgb = a[..., :3] * FOE_DIM
    grey = (rgb * [0.2126, 0.7152, 0.0722]).sum(-1, keepdims=True)
    rgb = grey + (rgb - grey) * FOE_SAT
    (wr, wg, wb), wa = FOE_WASH
    rgb = rgb * (1 - wa) + np.array([wr, wg, wb], np.float32) * wa
    a[..., :3] = np.clip(np.round(rgb), 0, 255)
    a[..., 3] = (a[..., 3] >= 110) * 255
    save(Image.fromarray(a.astype(np.uint8)), dst, optimize=True)
    return [cw, ch]


def fx_atlas(d, dst):
    """img/vg/fx/<dir>.png (slash, hit, shot, burst: what a foe on the map may use too) and <dir>_u.png (the
    ultimate: the pet raised and a boss only). Each group in its own band, 4 frames a row, frames centred in cells of
    the group's size; a turned group is its frames for e, then se s sw w nw n ne. -> {group: [file (0 | 1), x, y, cw,
    ch, frames, turned]}"""
    cut, meta, bands = {}, {}, ([], [])
    for g, (sheet, cols, rows, which, turned, side) in FX.items():
        if sheet not in cut:
            cut[sheet] = frames(os.path.join(ARENA, 'img', d, sheet + '.png'), cols, rows)
        src = [cut[sheet][i] for i in which]
        src = [f if f else Image.new('RGBA', (1, 1)) for f in src]
        k = side / max(max(f.size) for f in src)
        # turned: e, se, s, then sw w nw as se e ne mirrored (a flame or a claw keeps its top up), n, ne
        turn = lambda f, t: f if t == 0 else f.rotate(-45 * t, Image.BICUBIC, expand=True)
        way = lambda f, t: turn(f, 4 - t).transpose(Image.FLIP_LEFT_RIGHT) if t in (3, 4, 5) else turn(f, t)
        cells = [shrink(way(f, t), k) for t in (range(8) if turned else [0]) for f in src]
        bands[g == 'ult'].append((g, cells, max(c.width for c in cells), max(c.height for c in cells), turned, len(src)))
    for u, path in ((0, dst), (1, dst.replace('.png', '_u.png'))):
        W = max(cw * 4 for _, cells, cw, ch, _, _ in bands[u])
        H = sum(ch * -(-len(cells) // 4) for _, cells, cw, ch, _, _ in bands[u])
        at = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        y = 0
        for g, cells, cw, ch, turned, n in bands[u]:
            meta[g] = [u, 0, y, cw, ch, n, 1 if turned else 0]
            for i, c in enumerate(cells):
                at.alpha_composite(c, ((i % 4) * cw + (cw - c.width) // 2, y + (i // 4) * ch + (ch - c.height) // 2))
            y += ch * -(-len(cells) // 4)
        save(at, path, optimize=True)
    return meta


# the foes' own blows on the map, one sheet per element drawn for them (assets/source/vung-dat/fx/linh_<he>.png, 4 x 3
# on magenta): row 1 the ball flying right (4 frames, looped), row 2 the swipe facing right (4 frames, once), row 3 the
# hit landing (4 frames, once). Turned to the 8 ways here, so nothing turns in the game
LINH_SRC = os.path.join(SRC, 'fx')
LINH_SIZE = {'shot': 48, 'swipe': 72, 'hit': 64}         # px, the longest side of the group's biggest frame


def unkey(im):
    """A frame cut off magenta: the magenta-tinted edge pixels (the painter's smoothing into the background) go too."""
    a = np.array(im)
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    pink = ((r - g > 90) & (b - g > 90) & (np.abs(r - b) < 90)) | ((b - g > 55) & (r - g > 55) & (b > 110))
    a[pink, 3] = 0
    return Image.fromarray(a)


def linh_atlas(he, dst):
    """img/vg/fx/linh_<he>.png: shot (8 ways x 4), swipe (8 ways x 4), hit (4); laid out as fx_atlas lays a pet's.
    -> its meta"""
    cut = [unkey(f) if f else Image.new('RGBA', (1, 1)) for f in frames(os.path.join(LINH_SRC, f'linh_{he}.png'), 4, 3)]
    turn = lambda f, t: f if t == 0 else f.rotate(-45 * t, Image.BICUBIC, expand=True)
    way = lambda f, t: turn(f, 4 - t).transpose(Image.FLIP_LEFT_RIGHT) if t in (3, 4, 5) else turn(f, t)
    bands, meta = [], {}
    for g, row in (('shot', 0), ('swipe', 1), ('hit', 2)):
        src = cut[row * 4:row * 4 + 4]
        k = LINH_SIZE[g] / max(max(f.size) for f in src)
        cells = [shrink(way(f, t), k) for t in (range(8) if g != 'hit' else [0]) for f in src]
        bands.append((g, cells, max(c.width for c in cells), max(c.height for c in cells), g != 'hit'))
    W = max(cw * 4 for _, cells, cw, ch, _ in bands)
    H = sum(ch * -(-len(cells) // 4) for _, cells, cw, ch, _ in bands)
    at = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    y = 0
    for g, cells, cw, ch, turned in bands:
        meta[g] = [0, 0, y, cw, ch, 4, 1 if turned else 0]
        for i, c in enumerate(cells):
            at.alpha_composite(c, ((i % 4) * cw + (cw - c.width) // 2, y + (i // 4) * ch + (ch - c.height) // 2))
        y += ch * -(-len(cells) // 4)
    at.save(dst, optimize=True)
    return meta


def pet_job(d):
    """Both atlases of a pet, from the cache when its sheets have not changed. -> (dir, body meta, fx meta)"""
    srcs = [os.path.join(ARENA, 'img', d, n + '.png') for n in BODY + ['fx1', 'fx2', 'fx4']]
    if not all(os.path.exists(p) for p in srcs):
        return d, None, None
    key = hashlib.md5(json.dumps([VERSION, BODY_H, POSES, FX, [os.path.getmtime(p) for p in srcs]]).encode()).hexdigest()[:12]
    base = os.path.join(CACHE, 'pet', d)
    os.makedirs(os.path.dirname(base), exist_ok=True)
    mj = base + '.json'
    if os.path.exists(mj):
        m = json.load(open(mj))
        if m.get('key') == key and all(os.path.exists(base + x) for x in ('_body.png', '_fx.png', '_fx_u.png')):
            return d, m['body'], m['fx']
    body = body_atlas(d, base + '_body.png')
    fx = fx_atlas(d, base + '_fx.png')
    json.dump(dict(key=key, body=body, fx=fx), open(mj, 'w'))
    return d, body, fx


def roster():
    """The pets Solo has (game/src/solo.js's ROSTER): any of them can be the one raised, or a foe on a map."""
    src = open(os.path.join(ROOT, 'game', 'src', 'solo.js'), encoding='utf-8').read()
    return re.findall(r"\['\w+', '([a-z-]+)', '[^']+', '\w+'\]", src)


# ---------------------------------------------------------------- the build

def khu_job(args):
    """A khu's map, from the cache when it has not changed. -> (khu data, cached picture paths)"""
    he, src, k, xem = args
    stem = os.path.splitext(os.path.basename(src))[0]
    key = hashlib.md5(json.dumps([VERSION, C, os.path.getmtime(src), os.path.getsize(src), k, MAP_CONTRAST, MAP_BRIGHT, MAP_SAT, PATH_TOL, LINE_K, GROUND_K]).encode()).hexdigest()[:12]
    base = os.path.join(CACHE, 'map', he, stem)
    os.makedirs(os.path.dirname(base), exist_ok=True)
    mj = base + '.json'
    if os.path.exists(mj) and not xem:
        m = json.load(open(mj, encoding='utf-8'))
        if m.get('key') == key:
            return m
    clean, nests, rows, exits, gate = khu_map(src, k, he)
    save(clean.quantize(256, method=Image.Quantize.MAXCOVERAGE, dither=Image.Dither.NONE), base + '.png', optimize=True)
    for i, (spr, x, y) in enumerate(nests):
        save(spr, f'{base}_o{i}.png', optimize=True)
    if xem:
        os.makedirs(os.path.join(CACHE, 'xem'), exist_ok=True)
        preview(clean, nests, rows, exits, os.path.join(CACHE, 'xem', f'{he}_{stem}.png'))
    m = dict(key=key, stem=stem, w=MAP_W, h=MAP_H, grid=rows, exits=exits, gate=gate,
             nests=[[x, y, spr.width, spr.height] for spr, x, y in nests])
    json.dump(m, open(mj, 'w', encoding='utf-8'))
    return m


def link(khus):
    """Each khu's way in and way on: the first khu is entered from the bottom (the gate), each next one from the side
    facing the way out of the one before; the way on is the exit across from the way in."""
    across = {'top': 'bottom', 'bottom': 'top', 'left': 'right', 'right': 'left'}
    want_in = 'bottom'
    for i, k in enumerate(khus):
        ex = k['exits']
        sides = [e[0] for e in ex]
        k['in'] = sides.index(want_in) if want_in in sides else (0 if ex else -1)
        k['on'] = -1
        if i + 1 < len(khus):
            back = ex[k['in']][0] if k['in'] >= 0 else want_in
            order = [across[back]] + [s for s in ('top', 'right', 'left', 'bottom') if s != back]
            for s in order:
                if s in sides and sides.index(s) != k['in']:
                    k['on'] = sides.index(s)
                    break
            want_in = across[ex[k['on']][0]] if k['on'] >= 0 else 'bottom'


def sounds(page):
    """The element sounds -> sfx/solo/<he>_<k>.wav, the arena's boss music -> nhac/vung-boss.wav."""
    jobs = [(os.path.join(ARENA, 'sfx', f'{he}_{k}.ogg'), os.path.join('sfx', 'solo', f'{he}_{k}.wav'))
            for he in REGIONS for k in SOUNDS] + [(os.path.join(ARENA, 'sfx', 'chien-dau-boss.ogg'), os.path.join('nhac', 'vung-boss.wav')),
                                    (os.path.join(ARENA, 'sfx', 'fight.ogg'), os.path.join('sfx', 'solo', 'fight.wav'))]   # the VS screen's "Fight!"
    for src, rel in jobs:
        if not os.path.exists(src):
            continue
        cached = os.path.join(CACHE, rel)
        if not os.path.exists(cached) or os.path.getmtime(cached) < os.path.getmtime(src):
            os.makedirs(os.path.dirname(cached), exist_ok=True)
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-ac', '1', '-ar', '22050',
                            '-sample_fmt', 's16', cached], check=True)
        os.makedirs(os.path.dirname(os.path.join(page, rel)), exist_ok=True)
        shutil.copy(cached, os.path.join(page, rel))



# ---------------------------------------------------------------- the UI (assets/source/vung-dat/ui, drawn by the user)
UI_SRC = os.path.join(SRC, 'ui')
# name: (sheet, box in the sheet (x0, y0, x1, y1), the longest side wanted on the 640x480 screen)
CARD_COLS = [(0, 470), (466, 936), (932, 1402)]
UI_PARTS = {
    'the': [('the-khu', (x0, 150, x1, 900), 150) for x0, x1 in CARD_COLS],            # normal, chosen, locked
    'bang-doc': [('bang', (16, 16, 600, 792), 300)], 'bang-ngang': [('bang', (608, 72, 1760, 632), 430)],
    'bang-ten': [('bang', (600, 656, 1768, 848), 440)],
    'vong-mat': [('hud', (16, 120, 616, 752), 62)], 'khung-thanh': [('hud', (608, 256, 1752, 456), 172)],
    'khung-thanh-nho': [('hud', (608, 256, 1752, 456), 132)],
    'bang-nho': [('hud', (680, 504, 1256, 744), 200)], 'xu': [('hud', (1368, 536, 1600, 768), 18)],
    'nut': [('nut-chieu', (x0, y0, x1, y1), 42) for y0, y1 in ((16, 412), (412, 828))
            for x0, x1 in ((64, 464), (480, 880), (896, 1300), (1316, 1724))],          # A B X Y (red yellow blue green), then lit
    'canh-bao': [('canh-bao', (40, 40, 1736, 392), 380)],
    'mui-ten': [('canh-bao', (488, 376, 840, 656), 34), ('canh-bao', (960, 376, 1304, 656), 34)],   # gold, red
    'vien-do': [('canh-bao', (32, 680, 1744, 832), 640)],
    'icon': [('icon', b, 30) for b in ((40, 72, 504, 576), (520, 88, 1008, 576), (1032, 96, 1504, 560), (1552, 96, 1960, 576))],
    'icon-lon': [('icon', b, 46) for b in ((40, 72, 504, 576), (520, 88, 1008, 576), (1032, 96, 1504, 560), (1552, 96, 1960, 576))],
    'he': [('bo-ui-them', (544 + i * 120, 200, 664 + i * 120, 320), 30) for i in range(5)],     # hoa thuy moc tho kim
    'co': [('bo-ui-them', (520 + i * 128, 344, 648 + i * 128, 632), 70) for i in range(5)],    # the same order
    'dau': [('bo-ui-them', b, 28) for b in ((512, 656, 696, 848), (704, 656, 888, 848), (896, 648, 1096, 856))],   # tick skull lock
    'thanh-tim': [('bo-ui-them', (1112, 728, 1512, 824), 170)],
}
# the thin frames (khung-manh.png, drawn for the small screen: the first ones were too busy once shrunk) in their place
if os.path.exists(os.path.join(UI_SRC, 'khung-manh.png')):
    UI_PARTS.update({
        'khung-thanh': [('khung-manh', (48, 60, 546, 120), 150)], 'khung-thanh-nho': [('khung-manh', (588, 66, 924, 120), 110)],
        'bang-nho': [('khung-manh', (966, 30, 1410, 150), 200)], 'vong-mat': [('khung-manh', (174, 198, 396, 414), 54)],
        'nut': [('khung-manh', b, 40) for b in ((474, 162, 630, 318), (648, 162, 804, 318), (816, 162, 978, 318), (990, 162, 1146, 318),
                                                (474, 324, 630, 480), (642, 324, 798, 480), (816, 324, 972, 480), (990, 324, 1146, 480))],
        'bang-doc': [('khung-manh', (42, 480, 462, 1020), 300)], 'bang-ngang': [('khung-manh', (486, 510, 1410, 894), 430)],
        'bang-ten': [('khung-manh', (498, 918, 1410, 1026), 440)],
    })
UI_HE = ['hoa', 'thuy', 'moc', 'tho', 'kim']            # the order of the element icons and banners on the sheet


def ui_piece(sheet, box, side, hole=False):
    """A piece of a UI sheet: the background cleared by a flood from the box's edges (a magenta sheet: what is close
    to magenta and joined to the edge; a sheet with alpha: its own), its magenta-tinted edge pixels too, cropped and
    scaled so its longest side is `side`."""
    from collections import deque
    im = Image.open(os.path.join(UI_SRC, sheet + '.png'))
    a = np.array(im.convert('RGBA').crop(box)).astype(np.int32)
    h, w = a.shape[:2]
    if im.mode != 'RGBA':
        near = (np.abs(a[..., 0] - 250) + a[..., 1] + np.abs(a[..., 2] - 250)) < 150
        bg = np.zeros((h, w), bool)
        q = deque([(y, x) for x in range(w) for y in (0, h - 1)] + [(y, x) for y in range(h) for x in (0, w - 1)])
        while q:
            y, x = q.popleft()
            if bg[y, x] or not near[y, x]:
                continue
            bg[y, x] = True
            for Y, X in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= Y < h and 0 <= X < w and not bg[Y, X]:
                    q.append((Y, X))
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        pink = (r - g > 90) & (b - g > 90) & (np.abs(r - b) < 100)
        if hole:                                 # a ring: its middle is see-through too
            bg |= near
        bg |= pink & grow(bg, 3)
        a[bg, 3] = 0
    yy, xx = np.nonzero(a[..., 3] > 20)
    a = a[yy.min():yy.max() + 1, xx.min():xx.max() + 1].astype(np.uint8)
    piece = Image.fromarray(a)
    k = side / max(piece.size)
    return shrink(piece, k) if k < 1 else piece


def card_window(card):
    """The card's picture window: the box of the see-through part inside it (not joined to its edges)."""
    al = np.asarray(card)[..., 3] < 30
    inner = [p for p in parts(al[::2, ::2]) if not any(y in (0, al.shape[0] // 2 - 1) or x in (0, al.shape[1] // 2 - 1) for y, x in p)]
    if not inner:
        return [0, 0, card.width, card.height]
    p = max(inner, key=len)
    ys, xs = zip(*p)
    return [min(xs) * 2, min(ys) * 2, (max(xs) + 1) * 2 - min(xs) * 2, (max(ys) + 1) * 2 - min(ys) * 2]


def ui_build(out):
    """img/vg/ui/<name>_<i>.png; -> {name: [[w, h], ...]} and the cards' picture window"""
    os.makedirs(out, exist_ok=True)
    meta = {}
    if not os.path.isdir(UI_SRC):
        return meta
    for name, pieces in UI_PARTS.items():
        if not os.path.exists(os.path.join(UI_SRC, pieces[0][0] + '.png')):
            continue
        meta[name] = []
        for i, (sheet, box, side) in enumerate(pieces):
            im = ui_piece(sheet, box, side, hole=name == 'vong-mat')
            im.save(os.path.join(out, f'{name}_{i}.png'), optimize=True)
            meta[name].append([im.width, im.height])
            if name == 'the' and i == 0:
                meta['cua-so'] = [int(v) for v in card_window(im)]
    meta['thu-tu-he'] = UI_HE
    # the bars' colours (Solo's fills), cut to the inside of each bar frame
    for frame in ('khung-thanh', 'khung-thanh-nho'):
        if frame not in meta:
            continue
        x, y, w, h = inside_dark(Image.open(os.path.join(out, f'{frame}_0.png')))
        meta[frame + '-trong'] = [x, y, w, h]
        for col in ('do', 'ngoc', 'vang'):
            src = os.path.join(ARENA, 'ui', f'thanh_fill_{col}.png')
            if os.path.exists(src):
                Image.open(src).convert('RGBA').resize((w, h), Image.LANCZOS).save(os.path.join(out, f'{frame}_{col}.png'), optimize=True)
    return meta


def inside_dark(im):
    """The dark inside of a bar frame: its longest dark run across the middle row, and down the middle of that."""
    a = np.asarray(im.convert('RGBA')).astype(int)
    dark = (a[..., :3].sum(-1) < 240) & (a[..., 3] > 200)
    def run(line):
        best, cur, start, bs = 0, 0, 0, 0
        for i, v in enumerate(list(line) + [False]):
            if v:
                if not cur:
                    start = i
                cur += 1
            else:
                if cur > best:
                    best, bs = cur, start
                cur = 0
        return bs, best
    x, w = run(dark[a.shape[0] // 2])
    y, h = run(dark[:, x + w // 2])
    return [int(x) + 1, int(y) + 1, int(w) - 2, int(h) - 2]


def thumb(src, size, dst):
    """A khu's map shrunk to fill a card's window (cut to its shape)."""
    im = Image.open(src).convert('RGB')
    w, h = size
    k = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * k)), max(h, round(im.height * k))), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    im.crop((x, y, x + w, y + h)).save(dst, optimize=True)



# ---------------------------------------------------------------- the khu bosses (one a khu, Lv4: the adult sheets)
# The user (2026-10-27): every khu has a boss to beat before the way on opens; for now drawn with the Lv4 (Trưởng
# thành) frames of assets/creatures-640/<he>/<dir>/adult, side-on (they face right; turned left by mirroring).
CREATURES = os.path.join(ROOT, 'assets', 'creatures-640')
SIDE_FRAMES = [f'{a}-{i}' for a in ('idle', 'walk', 'punch', 'blast') for i in range(4)] + ['hurt', 'faint']
SIDE_H = 92                                  # px, the boss standing (idle) on the map


def side_atlas(d, he):
    """img/vg/boss/<dir>.png (freed) and <dir>_t.png (possessed): SIDE_FRAMES in a row, each in a cell of one size,
    feet at the same spot. -> [cw, ch, ax, ay] (the feet in a cell)"""
    base = os.path.join(CREATURES, he, d, 'adult')
    meta = json.load(open(os.path.join(base, 'frames.json')))
    ax, ay = meta['anchor']
    srcs = [os.path.join(base, 'png', f + '.png') for f in SIDE_FRAMES]
    key = hashlib.md5(json.dumps([VERSION, SIDE_H, FOE_DIM, FOE_SAT, FOE_WASH, [os.path.getmtime(p) for p in srcs]]).encode()).hexdigest()[:12]
    out = os.path.join(CACHE, 'boss', d)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out + '.json'):
        m = json.load(open(out + '.json'))
        if m.get('key') == key and os.path.exists(out + '.png') and os.path.exists(out + '_t.png'):
            return m['cell']
    ims = [Image.open(p).convert('RGBA') for p in srcs]
    box = [10 ** 6, 10 ** 6, -1, -1]                   # the union of the frames' paint, relative to the canvas
    for im in ims:
        bb = im.getbbox()
        if bb:
            box = [min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3])]
    idle = ims[0].getbbox()
    k = SIDE_H / (idle[3] - idle[1])
    cw, ch = round((box[2] - box[0]) * k) + 2, round((box[3] - box[1]) * k) + 2
    at = Image.new('RGBA', (cw * len(ims), ch), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        cut = shrink(im.crop(box), k, True)
        at.alpha_composite(cut, (i * cw, 0))
    save(at, out + '.png', optimize=True)
    a = np.array(at).astype(np.float32)
    rgb = a[..., :3] * FOE_DIM
    grey = (rgb * [0.2126, 0.7152, 0.0722]).sum(-1, keepdims=True)
    rgb = grey + (rgb - grey) * FOE_SAT
    (wr, wg, wb), wa = FOE_WASH
    a[..., :3] = np.clip(np.round(rgb * (1 - wa) + np.array([wr, wg, wb], np.float32) * wa), 0, 255)
    save(Image.fromarray(a.astype(np.uint8)), out + '_t.png', optimize=True)
    cell = [cw, ch, round((ax - box[0]) * k) + 1, round((ay - box[1]) * k) + 1]
    json.dump(dict(key=key, cell=cell), open(out + '.json', 'w'))
    return cell


def khu_bosses(reg, n):
    """Each khu's boss: the region's spirits in turn (not the khu's mini boss), the last khu its Thần thú."""
    mobs = [d for d, _ in reg['mobs']]
    out = []
    for ki in range(n):
        if ki == n - 1 and reg['boss']:
            out.append(reg['boss'])
        else:
            out.append(mobs[(ki + 2) % len(mobs)] if mobs else reg['boss'])
    return out



# ---------------------------------------------------------------- the VS screen before a mini boss's Solo match
# (the user's mock-up, 2026-10-27): two halves split by a slanted lightning bolt, the pet's ultimate cut-in on the
# left, the foe's on the right (mirrored, possessed purple), VS in the middle. Each half is made here at 640x480 so
# the game only puts pictures down 1:1: vs/<dir>_l.png (whole screen) and vs/<dir>_r.png (see-through left of the
# split), vs/set.png and vs/vs.png (assets/source/vung-dat/vs/giua.png)
VS_SRC = os.path.join(SRC, 'vs')
VS_SPLIT = (160, 480)                        # the split: x at the top, x at the bottom
VS_BG = {'hoa': (120, 30, 10), 'kim': (40, 60, 90), 'moc': (30, 80, 30), 'thuy': (20, 50, 110), 'tho': (100, 60, 20)}
# where the face is in a pet's cut-in (share of its width, height), and how big it is drawn (screen heights)
# where each pet's face is in its ultimate cut-in: (share across, share down, the face's height as a share of the
# picture's), read off the 31 pictures. The face is drawn VS_FACE_H tall at the middle of its half (zoomed between
# VS_ZOOM), as the user's reference (Hỏa Hổ vs Hỏa Hồ). Pictures with no face drawn: their main figure
VS_FOCUS = {
    'hu-anh': (0.50, 0.50, 0.45),
    'hoa-ho': (0.66, 0.40, 0.55), 'hoa-quy': (0.47, 0.48, 0.45), 'hoa-ho-cao': (0.43, 0.50, 0.45),
    'viem-long': (0.43, 0.45, 0.40), 'dung-nham-ve': (0.60, 0.40, 0.30), 'hoa-linh': (0.62, 0.52, 0.32),
    'tinh-kim-hiep': (0.47, 0.45, 0.40), 'kim-te': (0.49, 0.50, 0.60), 'kim-giap': (0.58, 0.48, 0.50),
    'kim-ung': (0.58, 0.55, 0.35), 'kim-thach-nhan': (0.51, 0.32, 0.28), 'liem-dao': (0.60, 0.32, 0.32),
    'moc-hung': (0.55, 0.45, 0.60), 'moc-duong': (0.50, 0.45, 0.50), 'reu-linh': (0.36, 0.40, 0.28),
    'moc-tru': (0.84, 0.45, 0.40), 'moc-loc': (0.76, 0.32, 0.30), 'thu-nhan': (0.72, 0.42, 0.30),
    'diep-linh': (0.80, 0.40, 0.28), 'thuy-long': (0.60, 0.60, 0.45), 'thuy-sa': (0.50, 0.32, 0.55),
    'thuy-giai': (0.50, 0.55, 0.35), 'thuy-chien': (0.42, 0.22, 0.25), 'bao-thuy': (0.30, 0.50, 0.80),
    'thuy-giao': (0.60, 0.25, 0.35), 'tho-nguu': (0.52, 0.45, 0.60), 'tho-tuong': (0.55, 0.35, 0.40),
    'tho-tich': (0.63, 0.45, 0.72), 'thach-nhan': (0.55, 0.27, 0.30), 'thanh-tri': (0.50, 0.42, 0.35),
    'tho-long': (0.70, 0.55, 0.30)}
VS_DEFAULT = (0.55, 0.45, 0.45)
VS_FACE_H, VS_ZOOM = 215, (1.0, 1.6)


def main_body(ink, share=0.05, step=4):
    """The paint joined to the picture's big shapes (each at least share of the biggest), on a 1/step grid: what
    floats loose (a crystal, a spark) is left out."""
    h, w = ink.shape
    small = ink[:h - h % step, :w - w % step].reshape(h // step, step, w // step, step).any(axis=(1, 3))
    sh, sw = small.shape
    lab = np.full(small.shape, -1, int)
    sizes = []
    for y0 in range(sh):
        for x0 in range(sw):
            if not small[y0, x0] or lab[y0, x0] >= 0:
                continue
            n, stack = 0, [(y0, x0)]
            lab[y0, x0] = len(sizes)
            while stack:
                y, x = stack.pop()
                n += 1
                for yy in (y - 1, y, y + 1):
                    for xx in (x - 1, x, x + 1):
                        if 0 <= yy < sh and 0 <= xx < sw and small[yy, xx] and lab[yy, xx] < 0:
                            lab[yy, xx] = len(sizes)
                            stack.append((yy, xx))
            sizes.append(n)
    if not sizes:
        return ink
    keep = np.array([n >= max(sizes) * share for n in sizes])
    big = np.where(lab >= 0, keep[np.maximum(lab, 0)], False)
    full = np.zeros_like(ink)
    full[:big.shape[0] * step, :big.shape[1] * step] = big.repeat(step, 0).repeat(step, 1)
    return full


def vs_key(path, tight=False):
    """The cut-in off its magenta, and the pink-tinted pixels at its edges too (mixed with the magenta when it was
    painted: left in, they showed as stray pink bits on the VS screen). tight: a picture painted in violets (Hư Ảnh),
    which the loose key punched holes in: only the magenta itself and its fringe right next to it"""
    a = np.array(Image.open(path).convert('RGBA')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    if tight:
        key = (r > 200) & (b > 200) & (g < 80) & (np.abs(r - b) < 50)
        key |= (r > 170) & (b > 170) & (g < 120) & (np.abs(r - b) < 70) & grow(key, 2)
        a[key, 3] = 0
        a[~main_body(~key), 3] = 0               # its loose crystals and sparks: stray bits by the bolt on the VS screen
        return Image.fromarray(a.astype(np.uint8))
    key = (r - g > 80) & (b - g > 80) & (np.abs(r - b) < 110)
    pink = (b - g > 35) & (r - g > 35) & (b > 90) & (np.abs(r - b) < 140)
    key |= pink & grow(key, 4)
    a[key, 3] = 0
    return Image.fromarray(a.astype(np.uint8))


def vs_half(d, he, right, purple=True):
    """One half of the VS screen (the user's pick, 2026-10-27: the ultimate's cut-in, big and balanced): the
    element's colour with speed lines, the pet's ultimate cut-in over it, its face (VS_FOCUS, read off each cut-in)
    put at the middle of its half; the right one mirrored, purple, see-through left of the split."""
    W, H = 640, 480
    im = vs_key(os.path.join(ARENA, 'img', d, 'cutin.png'), tight=d == 'hu-anh')
    if right:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    fx, fy, fh = VS_FOCUS.get(d, VS_DEFAULT)
    zoom = min(VS_ZOOM[1], max(VS_ZOOM[0], VS_FACE_H / (fh * H)))
    k = H * zoom / im.height
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    bg = VS_BG.get(he, (60, 40, 30))
    out = Image.new('RGBA', (W, H), bg + (255,))
    d2 = ImageDraw.Draw(out)
    rng = np.random.default_rng(len(d) + (7 if right else 1))
    for _ in range(40):                          # speed lines (seen where the cut-in is see-through)
        y, l, x = int(rng.uniform(0, H)), int(rng.uniform(60, 260)), int(rng.uniform(-100, W))
        d2.line([(x, y), (x + l, y - l // 6)], fill=tuple(min(255, c + 60) for c in bg) + (255,), width=int(rng.uniform(2, 6)))
    if right:
        fx = 1 - fx
    tx, ty = (W * 0.76, H * 0.46) if right else (W * 0.24, H * 0.46)
    px, py = int(tx - im.width * fx), int(ty - im.height * fy)
    py = min(0, max(H - im.height, py))          # never a gap: it always covers the screen
    # nor sideways where it shows: the left half is seen up to the split's far end (x 480), the right one from its
    # near end (x 160); past those the other half covers it, so a face near its picture's edge can still come in
    lo, hi = (VS_SPLIT[1] - im.width, 0) if not right else (W - im.width, VS_SPLIT[0])
    px = min(hi, max(lo, px))
    out.alpha_composite(im, (px, py))
    if right:
        if purple:                               # a spirit taken by the Hư Ảnh; Võ đường's foes are plain (_rt)
            out.alpha_composite(Image.new('RGBA', (W, H), (110, 30, 160, 70)))
        mask = Image.new('L', (W, H), 0)
        ImageDraw.Draw(mask).polygon([(VS_SPLIT[0], 0), (W, 0), (W, H), (VS_SPLIT[1], H)], fill=255)
        out.putalpha(mask)
        ImageDraw.Draw(out).line([VS_SPLIT[0], 0, VS_SPLIT[1], H], fill=(20, 8, 20, 255), width=10)
    return out


def vs_build(out, pets):
    """the VS pictures into img/vg/vs/; -> where the bolt and VS go"""
    src = os.path.join(VS_SRC, 'giua.png')
    if not os.path.exists(src):
        return None
    os.makedirs(out, exist_ok=True)
    sheet = vs_key(src)
    def piece(box):
        im = sheet.crop(box)
        bb = im.getbbox()
        return im.crop(bb)
    bolt, vs = piece((40, 0, 740, 1024)), piece((680, 160, 1500, 840))
    # the bolt's box reaches into the VS badge's: its red sparks, cut flat at the box's edge, came along (stray red
    # bits by the bolt on the screen). Only the bolt and what touches it stay
    ba = np.array(bolt)
    ba[~main_body(ba[..., 3] > 0, share=0.2, step=2), 3] = 0
    bolt = Image.fromarray(ba)
    bolt = bolt.crop(bolt.getbbox())
    kb = 480 * 1.08 / bolt.height
    bolt = bolt.resize((round(bolt.width * kb), round(bolt.height * kb)), Image.LANCZOS)
    vs = vs.resize((190, round(vs.height * 190 / vs.width)), Image.LANCZOS)
    save(bolt, os.path.join(out, 'set.png'), optimize=True)
    save(vs, os.path.join(out, 'vs.png'), optimize=True)
    for d, he in pets:
        for right, x, purple in ((False, 'l', False), (True, 'r', True), (True, 'rt', False)):
            dst = os.path.join(out, f'{d}_{x}.png')
            cached = os.path.join(CACHE, 'vs', f'{d}_{x}.png')
            srcp = os.path.join(ARENA, 'img', d, 'cutin.png')
            if not os.path.exists(srcp):
                continue
            if not os.path.exists(cached) or os.path.getmtime(cached) < max(os.path.getmtime(srcp), os.path.getmtime(__file__)):
                os.makedirs(os.path.dirname(cached), exist_ok=True)
                im = vs_half(d, he, right, purple)
                save(im if right else im.convert('RGB'), cached, optimize=True)
            shutil.copy(cached, dst)
    cx = (VS_SPLIT[0] + VS_SPLIT[1]) // 2
    return dict(set=[cx - bolt.width // 2 + 6, -round(480 * 0.04)], vs=[320 - vs.width // 2, 240 - vs.height // 2])


def build(page, xem=False):
    """Everything above into the page (build/game/tien-hoa); the data vung-dat.js is built with."""
    out = os.path.join(page, 'img', 'vg')
    os.makedirs(os.path.join(out, 'pet'), exist_ok=True)
    os.makedirs(os.path.join(out, 'fx'), exist_ok=True)
    data = dict(C=C, bodyH=BODY_H, pets={}, regions={}, foeK=FOE_K, v=int(time.time()))
    jobs = []
    for he, reg in REGIONS.items():
        for src in sorted(glob.glob(os.path.join(SRC, he, '*.png'))):
            stem = os.path.splitext(os.path.basename(src))[0]
            jobs.append((he, src, reg['khu'].get(stem, {}), xem))
    with ProcessPoolExecutor() as pool:
        maps = list(pool.map(khu_job, jobs))
        pets = list(pool.map(pet_job, roster()))
    for d, body, fx in pets:
        if not body:
            continue
        shutil.copy(os.path.join(CACHE, 'pet', d + '_body.png'), os.path.join(out, 'pet', d + '.png'))
        shutil.copy(os.path.join(CACHE, 'pet', d + '_fx.png'), os.path.join(out, 'fx', d + '.png'))
        shutil.copy(os.path.join(CACHE, 'pet', d + '_fx_u.png'), os.path.join(out, 'fx', d + '_u.png'))
        data['pets'][d] = dict(cell=body, fx=fx, foe={})
    for reg in REGIONS.values():                 # the region's foes and boss, tinted and at their size
        for d, kind in reg['mobs'] + [[reg['boss'], 'boss']] + [[d, 'mini'] for d, _ in reg['mobs']]:
            if d not in data['pets']:
                continue
            kk = round(FOE_K[kind] * 100)
            src = os.path.join(CACHE, 'pet', d + '_body.png')
            dst = os.path.join(CACHE, 'pet', f'{d}_t{kk}.png')
            if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src) or os.path.getmtime(dst) < os.path.getmtime(__file__):
                foe_atlas(src, data['pets'][d]['cell'], kk / 100, dst)
            w, h = Image.open(dst).size
            data['pets'][d]['foe'][kk] = [w // len(POSES), h // len(BODY)]
            shutil.copy(dst, os.path.join(out, 'pet', f'{d}_t{kk}.png'))
    data['linh'] = {}
    for he in REGIONS:                           # the foes' blows (linh_atlas), per element
        if os.path.exists(os.path.join(LINH_SRC, f'linh_{he}.png')):
            data['linh'][he] = linh_atlas(he, os.path.join(out, 'fx', f'linh_{he}.png'))
    by = {}
    for (he, src, _, _), m in zip(jobs, maps):
        by.setdefault(he, []).append(m)
    for he, reg in REGIONS.items():
        os.makedirs(os.path.join(out, he), exist_ok=True)
        san = os.path.join(ARENA, 'ui', 'san', SAN[he] + '.png')   # the map's own arena (scripts/san_keo.py: no dark band)
        if os.path.exists(san):
            Image.fromarray(tone(np.asarray(Image.open(san).convert('RGB')))).save(os.path.join(out, he, 'san.png'), optimize=True)
        gate = os.path.join(GATES, reg['gate'])
        if os.path.exists(gate):
            Image.open(gate).convert('RGB').resize((640, 480), Image.LANCZOS).save(os.path.join(out, he, 'cong.png'), optimize=True)
        khus = []
        for n, m in enumerate(by.get(he, []), 1):
            base = os.path.join(CACHE, 'map', he, m['stem'])
            shutil.copy(base + '.png', os.path.join(out, he, f'k{n}.png'))
            for i in range(len(m['nests'])):
                shutil.copy(f'{base}_o{i}.png', os.path.join(out, he, f'k{n}_o{i}.png'))
            khus.append(dict(name=reg['khu'].get(m['stem'], {}).get('name', f'Khu {n}'), w=m['w'], h=m['h'],
                             grid=m['grid'], exits=m['exits'], nests=m['nests'], gate=m.get('gate')))
        link(khus)
        data['regions'][he] = dict(name=reg['name'], mobs=[x for x in reg['mobs'] if x[0] in data['pets']],
                                   boss=reg['boss'] if reg['boss'] in data['pets'] else None, khu=khus,
                                   khuBoss=[d if d in data['pets'] else None for d in khu_bosses(reg, len(khus))])
        os.makedirs(os.path.join(out, 'boss'), exist_ok=True)
        # every spirit of the element may be a khu's boss (picked at random in the game): all their side-on pictures
        for d in sorted(os.listdir(os.path.join(CREATURES, he))) if os.path.isdir(os.path.join(CREATURES, he)) else []:
            if d in data['pets'] and os.path.exists(os.path.join(CREATURES, he, d, 'adult', 'frames.json')):
                data['pets'][d]['side'] = side_atlas(d, he)
                for x in ('', '_t'):
                    shutil.copy(os.path.join(CACHE, 'boss', d + x + '.png'), os.path.join(out, 'boss', d + x + '.png'))
    data['ui'] = ui_build(os.path.join(out, 'ui'))
    he_of = {d: he for he in REGIONS for d in os.listdir(os.path.join(CREATURES, he))} if os.path.isdir(CREATURES) else {}
    # Hư Ảnh, the last boss (scripts/hu_anh.py): its Solo sheets into the arena page, its six big skills here
    sys.path.insert(0, HERE)
    import hu_anh
    hu_anh.arena()
    data['hu'] = hu_anh.skills(os.path.join(out, 'hu'))
    data['huGiant'] = hu_anh.giant(os.path.join(out, 'hu'))   # phase 2
    data['dai'] = hu_anh.dai(out)               # Đài Ngũ Hành on the world map
    data['ngoc'] = hu_anh.ngoc(out)             # the five Ngọc Hồn on the gate screen
    hu_anh.san()                                # its arena, in the arena page
    # its films: their pictures into assets/source/phim/, where game/build_game.py makes img/phim/ of them; here too
    # (the 800x450 of game/build_game.py film_pictures()) when the page has none yet, as a test copy does not
    os.makedirs(os.path.join(page, 'img', 'phim'), exist_ok=True)
    for name in hu_anh.phim():
        src, dst = os.path.join(ROOT, 'assets', 'source', 'phim', name + '.png'), os.path.join(page, 'img', 'phim', name + '.png')
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            save(Image.open(src).convert('RGB').resize((800, 450), Image.LANCZOS), dst, optimize=True)
    data['vs'] = vs_build(os.path.join(out, 'vs'), [(d, he_of.get(d, 'hoa')) for d in data['pets']] + [(hu_anh.DIR, 'hu')])
    rt = os.path.join(out, 'vs', f'{hu_anh.DIR}_rt.png')
    if os.path.exists(rt):                       # the Hư itself: not tinted purple as a spirit taken by it
        shutil.copy(rt, os.path.join(out, 'vs', f'{hu_anh.DIR}_r.png'))
    win = data['ui'].get('cua-so')
    if win:                                      # each khu's map in its card on the gate screen
        for he, r in data['regions'].items():
            for n in range(1, len(r['khu']) + 1):
                src = os.path.join(out, he, f'k{n}.png')
                if os.path.exists(src):
                    thumb(src, (win[2], win[3]), os.path.join(out, he, f'k{n}_nho.png'))
    sounds(page)
    return data


def test_copy():
    """build/vung-dat/game/: a copy of the game's last build (build/game/tien-hoa, pets and solo beside it) with the
    regions made again into it, to try the maps without a whole build (nor touching build/game, which another
    build may be redoing). Its folder for the browser and for scripts/r36s_game.py."""
    game = os.path.join(ROOT, 'build', 'game')
    out = os.path.join(CACHE, 'game')
    page = os.path.join(out, 'tien-hoa')
    if not os.path.exists(os.path.join(game, 'tien-hoa', 'index.html')):
        raise SystemExit('build/game/tien-hoa chưa dựng xong (python game/build_game.py)')
    if os.path.exists(page):
        shutil.rmtree(page)
    shutil.copytree(os.path.join(game, 'tien-hoa'), page)
    for link, target in (('pets', os.path.join(ROOT, 'assets', 'creatures-640')), ('solo', os.path.join(ROOT, 'preview', 'dau-truong'))):
        if not os.path.exists(os.path.join(out, link)):
            subprocess.run(['cmd', '/c', 'mklink', '/J', os.path.join(out, link), target], check=True, capture_output=True)
    return page


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    page = test_copy() if '--thu' in sys.argv else os.path.join(CACHE, 'page')
    d = build(page, xem='--xem' in sys.argv)
    if '--thu' in sys.argv:
        src = open(os.path.join(ROOT, 'game', 'src', 'vung-dat.js'), encoding='utf-8').read()
        open(os.path.join(page, 'js', 'vung-dat.js'), 'w', encoding='utf-8', newline='\n').write(
            src.replace('__VUNG_DAT__', json.dumps(d, ensure_ascii=False, separators=(',', ':'))))
        shutil.copy(os.path.join(ROOT, 'game', 'src', 'solo.js'), os.path.join(page, 'js', 'solo.js'))   # its match hook
        shutil.copy(os.path.join(ROOT, 'game', 'src', 'phim.js'), os.path.join(page, 'js', 'phim.js'))   # the altar's films
        html = os.path.join(page, 'index.html')            # a new stamp: the browser reads these, not its cache
        text = open(html, encoding='utf-8').read()
        text = re.sub(r'js/(vung-dat|solo|phim)\.js\?v=\d+', lambda m: f'js/{m.group(1)}.js?v={int(time.time())}', text)
        open(html, 'w', encoding='utf-8', newline='\n').write(text)
        print('bản thử:', page)
    dist = os.path.join(CACHE, 'dist', 'elemon')
    if '--thu' in sys.argv and '--dist' in sys.argv and os.path.exists(dist):
        # the R36S test package (scripts/vung_dat_test.py --pack) brought up to date with only what this file makes
        import r36s_game
        shutil.rmtree(os.path.join(dist, 'img', 'vg'), ignore_errors=True)
        pngs = glob.glob(os.path.join(page, 'img', 'vg', '**', '*.png'), recursive=True)
        pngs += glob.glob(os.path.join(page, 'img', 'phim', 'PHIM_[678]*.png'))     # the altar's films
        dsts = [os.path.join(dist, os.path.splitext(os.path.relpath(p, page))[0] + '.hli') for p in pngs]
        for p in dsts:
            os.makedirs(os.path.dirname(p), exist_ok=True)
        with ProcessPoolExecutor() as pool:
            list(pool.map(r36s_game.picture, pngs, dsts, chunksize=8))
        for rel in ['js/vung-dat.js', 'js/solo.js', 'js/phim.js', 'nhac/vung-boss.wav'] + [os.path.relpath(p, page) for p in glob.glob(os.path.join(page, 'sfx', 'solo', '*.wav'))]:
            os.makedirs(os.path.dirname(os.path.join(dist, rel)), exist_ok=True)
            shutil.copy(os.path.join(page, rel), os.path.join(dist, rel))
        print('gói thử R36S:', dist, len(pngs), 'hình')
    for he, r in d['regions'].items():
        print(he, r['name'], [(k['name'], len(k['nests']), k['exits'], k['in'], k['on']) for k in r['khu']])
    print(len(d['pets']), 'pet')
