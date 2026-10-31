"""Hư Ảnh, the last boss (assets/source/boss-cuoi/, the user's design 2026-10-28): its pictures made ready.

  arena()       its Solo body and small blows into the arena page, as a pet's (preview/dau-truong/img/hu-anh/):
                s se e ne n (4x4), chung (4x2), cutin; fx1 = HU-ANH_1 (Vuốt Hư), fx2 = HU-ANH_2, fx3 = HU-ANH_3
                (Tan Vào Khói), fx4 = HU-ANH_4, aura. It fights with Liêm Đao's kit for its claw and its blink
                (game/src/vung-dat.js); its six big skills are drawn by vung-dat.js, from:
  skills(out)   img/vg/hu/c<n>.png: each of the six big skills (HU-ANH_c<n>_*.png, 4x3: charge, release, burst and
                fade) cut into its 12 frames, off its magenta, at ATLAS of its size, packed in rows. -> their meta:
                {c1: {cw, ch, f: [[x, y, w, h, ox, oy], ...]}, ...}: cw x ch a cell at atlas size, each frame where it
                is in the atlas and where its top-left sits from its cell's centre (so a frame that moves in its
                cell, a crystal falling, keeps moving; the sweep's long frame, spilling into the next cell, stays
                whole: the rows are cut at their emptiest columns near the cell lines, not on them)
  phase 2 (the same atlases, their meta under these names): xt (HU-ANH_xuc-tu, the giant's tentacle slam, 4x3),
                mk (HU-ANH_mua-khoi, its smoke orbs, 4x2), mat (HU-ANH_mat, its eyes, 4x1), nh (NGU-HANH_tia, the
                Five Elements' beams, 4x3), tt (NGU-HANH_than-thu, the five Thần thú's spirits, 5x1), and the giant's
                other four attacks, 4x3 each: vt (HU-ANH_p2_vo-tay), gr (_gam-rung), lx (_luoi-xuc-tu), bh (_bong-hu)
  giant(out)    img/vg/hu/khong-lo.png: the giant (HU-ANH_khong-lo) off its magenta at GIANT_W wide -> {w, h, core: [x, y],
                eyes: [x0, y0, x1, y1]} (the crystal in its chest, where it is hit, and its eyes, found in the picture)
  dai(out)      img/vg/dai.png: the altar on the world map
  san()         Đài Ngũ Hành's arena (SAN_dai-ngu-hanh) for Hư Ảnh's matches, into the arena page's ui/san/ and its
                san.json under 'hu' (the arena picks its arena by the foe's element)
  ngoc(out)     img/vg/ngoc.png: the five Ngọc Hồn (NGOC-HON, 5x2: won, not yet), small, for the gate screen
  phim()        the films of the altar (PHIM_6..8) cut to the films' 16:9 into assets/source/phim/, where game/build_game.py
                takes the films from (PHIM_7, too tall for 16:9, as two: the risen Hư Ảnh, and the pet under it)
scripts/vung_dat.py calls them (build()). Usage: python scripts/hu_anh.py   (arena() only)
"""
import os, shutil, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'assets', 'source', 'boss-cuoi')
ARENA_IMG = os.path.join(ROOT, 'preview', 'dau-truong', 'img', 'hu-anh')
DIR = 'hu-anh'
SHEETS = {'s': 'HU-ANH_s', 'se': 'HU-ANH_se', 'e': 'HU-ANH_e', 'ne': 'HU-ANH_ne', 'n': 'HU-ANH_n', 'chung': 'HU-ANH_chung',
          'cutin': 'HU-ANH_cutin', 'fx1': 'HU-ANH_1', 'fx2': 'HU-ANH_2', 'fx3': 'HU-ANH_3', 'fx4': 'HU-ANH_4',
          'aura': 'HU-ANH_aura'}
SKILLS = ['c1_xuc-tu-quet', 'c2_xuc-tu-troi', 'c3_mua-tinh-the', 'c4_vong-hu-khong', 'c5_tia-mat-hu', 'c6_hu-khong-nuot']
CUTS = {'c1_xuc-tu-quet': {1: 3}}           # frames in a row when not 4: the sweep's row 2 has a long third frame
# phase 2's sheets: atlas name, file, columns, rows, their share of their painted size
PHASE2 = [('xt', 'HU-ANH_xuc-tu', 4, 3, 0.55), ('mk', 'HU-ANH_mua-khoi', 4, 2, 0.45), ('mat', 'HU-ANH_mat', 4, 1, 0.45),
          ('nh', 'NGU-HANH_tia', 4, 3, 0.55), ('tt', 'NGU-HANH_than-thu', 5, 1, 0.3),
          ('vt', 'HU-ANH_p2_vo-tay', 4, 3, 0.55), ('gr', 'HU-ANH_p2_gam-rung', 4, 3, 0.55),
          ('lx', 'HU-ANH_p2_luoi-xuc-tu', 4, 3, 0.55), ('bh', 'HU-ANH_p2_bong-hu', 4, 3, 0.55)]
GIANT_W = 470                               # the giant's width on the 640 px arena (its still picture)
# the giant drawn by hand, 16 frames a move (4x4 cells of 313 px; the user: no warping by code): standing (a loop),
# gathering and striking, hurt (by the Five Elements), falling; 12 frames a second. Cut at GIANT_K of their painted size
# and drawn 1:1, a cell's centre at GIANT_Y: its body (about 300 x 240 of a cell) from just under the screen's top edge
# down over only the back of the ring (the user, 2026-10-28: room left in the arena to fight it; at 1.9x it covered it)
GIANT_ANIM = {'gd': 'HU-ANH_khong-lo_dung16', 'gg': 'HU-ANH_khong-lo_gong16', 'gh': 'HU-ANH_khong-lo_dau16',
              'gu': 'HU-ANH_khong-lo_guc16'}
GIANT_K, GIANT_Y = 0.9, 103
PHASE2 += [(k, f, 4, 4, GIANT_K) for k, f in GIANT_ANIM.items()]
BODY = ['s', 'se', 'e', 'ne', 'n', 'chung', 'cutin']
ATLAS = 0.55                                # the skills' frames at this share of their painted size
WIDE = 2048                                 # an atlas row's width at most


def arena():
    """The body and blow sheets into the arena page (palette PNGs on their magenta, as the pets' are)."""
    sys.path.insert(0, HERE)
    from optimize_sheet import optimize
    os.makedirs(ARENA_IMG, exist_ok=True)
    n = 0
    for name, src in SHEETS.items():
        p, dst = os.path.join(SRC, src + '.png'), os.path.join(ARENA_IMG, name + '.png')
        if not os.path.exists(p):
            continue
        if not os.path.exists(dst) or os.path.getmtime(dst) < max(os.path.getmtime(p), os.path.getmtime(__file__)):
            tmp = dst + '.tmp.png'
            keep_violet(p, tmp)
            optimize(tmp, dst)
            os.remove(tmp)
        if name in BODY:                         # and as its Huyền thoại body: it fights at that size
            os.makedirs(os.path.join(ARENA_IMG, 'legend'), exist_ok=True)
            shutil.copy(dst, os.path.join(ARENA_IMG, 'legend', name + '.png'))
        n += 1
    return n


def keep_violet(src, dst):
    """The arena keys out anything magenta-ish (r > 170, g < 110, b > 170: cut() in preview/dau-truong): Hư Ảnh's bright
    violets would go with the background. Those that are not the magenta itself get their green just above it."""
    a = np.array(Image.open(src).convert('RGB'))
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    loose = (r > 170) & (g < 110) & (b > 170)
    a[loose & ~key(np.dstack([a, np.full(r.shape, 255, np.uint8)])), 1] = 112
    Image.fromarray(a).save(dst)


def key(a):
    """Where the magenta is: tight (the skills glow violet, close to it), then its painted fringe next to it."""
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    bg = (r > 200) & (b > 200) & (g < 80) & (np.abs(r - b) < 50)
    sys.path.insert(0, HERE)
    from vung_dat import grow
    fringe = (r > 170) & (b > 170) & (g < 120) & (np.abs(r - b) < 70) & grow(bg, 2)
    return bg | fringe


def cuts(ink, n, size, cols=4):
    """n spans along a row: cut at the emptiest column near each of its cell lines (the lines the spans keep)."""
    sys.path.insert(0, HERE)
    from vung_dat import cut_lines
    xs = cut_lines(cols, size, ink.sum(0))
    keep = list(range(cols + 1)) if n == cols else {3: [0, 1, 2, 4]}[n]
    return [xs[i] for i in keep]


def outside(a):
    """The magenta round a picture, grown from its edges through magenta-ish paint only (a loose key: the pictures
    come compressed, with glows into the magenta), so bright violet inside it stays."""
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    loose = (r > 150) & (b > 150) & (g < 130) & (np.abs(r - b) < 80)
    out = np.zeros_like(loose)
    out[0], out[-1], out[:, 0], out[:, -1] = loose[0], loose[-1], loose[:, 0], loose[:, -1]
    while True:
        nxt = out.copy()
        nxt[1:] |= out[:-1]; nxt[:-1] |= out[1:]; nxt[:, 1:] |= out[:, :-1]; nxt[:, :-1] |= out[:, 1:]
        nxt &= loose
        if (nxt == out).all():
            return out
        out = nxt


def skill_frames(path, cols=4, rows=3, per_row=None, soft=False):
    """The sheet's frames: (RGBA crop, its top-left from its cell's centre) a frame, in reading order. soft: a sheet
    whose glows run into the magenta (the spirits): keyed from the outside in"""
    a = np.array(Image.open(path).convert('RGBA'))
    bg = outside(a) if soft else key(a)
    if soft == 'giant':                         # the giant: and the magenta caught inside its smoke
        bg |= key(a)
    elif soft:                                  # the glow's pink edge left round the spirits: off too
        sys.path.insert(0, HERE)
        from vung_dat import grow
        r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
        bg |= grow(bg, 6) & (r - g > 50) & (b - g > 20) & (r > 160)
    a[bg, 3] = 0
    H, W = bg.shape
    cw, ch = W / cols, H / rows
    out = []
    for r in range(rows):
        y0, y1 = round(r * ch), round((r + 1) * ch)
        band = ~bg[y0:y1]
        xs = cuts(band, (per_row or {}).get(r, cols), W, cols)
        for c in range(len(xs) - 1):
            m = band[:, xs[c]:xs[c + 1]]
            yy, xx = np.nonzero(m)
            if not len(xx):
                out.append(None)
                continue
            fy0, fy1, fx0, fx1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
            px = a[y0 + fy0:y0 + fy1, xs[c] + fx0:xs[c] + fx1]
            # the cell it belongs to: in a full row the c-th; else the cell it starts in (a cut moved left of its cell
            # line, past a frame that spills over it, put that frame a cell too early: drawn a cell to the right)
            cell = c if len(xs) - 1 == cols else min(cols - 1, int((xs[c] + 1) // cw))
            ox, oy = xs[c] + fx0 - (cell + 0.5) * cw, fy0 - ch / 2
            out.append((Image.fromarray(px), ox, oy))
    return out, cw, ch


def skills(out):
    os.makedirs(out, exist_ok=True)
    meta = {}
    jobs = [(f'c{i}', f'HU-ANH_{n}', 4, 3, ATLAS, CUTS.get(n)) for i, n in enumerate(SKILLS, 1)]
    jobs += [(k, f, c, r, sc, None) for k, f, c, r, sc in PHASE2]
    for name, src, cols, rows, sc, per_row in jobs:
        p = os.path.join(SRC, src + '.png')
        if os.path.exists(p):
            meta[name] = sheet_atlas(p, cols, rows, per_row, sc, os.path.join(out, name + '.png'),
                                     soft='giant' if name in GIANT_ANIM else name == 'tt')
    return meta


def sheet_atlas(p, cols, rows, per_row, sc, dst, soft=False):
    """A sheet's frames packed in rows at sc of their size -> {cw, ch, f: [[x, y, w, h, ox, oy] | None, ...]}"""
    sys.path.insert(0, HERE)
    from vung_dat import save, shrink
    fr, cw, ch = skill_frames(p, cols, rows, per_row, soft)
    cells = [(shrink(f, sc), ox * sc, oy * sc) if f else None for f, ox, oy in [x or (None, 0, 0) for x in fr]]
    # shelf packing
    x = y = rowh = 0
    spots = []
    for c in cells:
        if not c:
            spots.append(None)
            continue
        im = c[0]
        if x + im.width > WIDE:
            x, y, rowh = 0, y + rowh, 0
        spots.append((x, y))
        x += im.width
        rowh = max(rowh, im.height)
    at = Image.new('RGBA', (max(1, max((s[0] + c[0].width for s, c in zip(spots, cells) if s), default=1)),
                            max(1, y + rowh)), (0, 0, 0, 0))
    fm = []
    for s, c in zip(spots, cells):
        if not s:
            fm.append(None)
            continue
        at.alpha_composite(c[0], s)
        fm.append([s[0], s[1], c[0].width, c[0].height, round(c[1]), round(c[2])])
    save(at, dst, optimize=True)
    return dict(cw=round(cw * sc), ch=round(ch * sc), f=fm)


def giant(out):
    """img/vg/hu/khong-lo.png and where its core crystal and its eyes are (see the top); with its hand-drawn moves,
    {anim: true, k (drawn this much bigger than cut: 1), y, core: [x, y] from a cell's centre at its cut size (its
    first standing frame)} instead"""
    p = os.path.join(SRC, GIANT_ANIM['gd'] + '.png')
    if os.path.exists(p):
        a = np.array(Image.open(p).convert('RGBA'))[:313, :313]
        a[outside(a) | key(a), 3] = 0
        r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
        bright = (a[..., 3] > 0) & (r > 200) & (g > 170) & (b > 220)
        mid = np.zeros_like(bright)
        mid[int(313 * 0.35):int(313 * 0.85), int(313 * 0.4):int(313 * 0.6)] = True
        cy, cx = np.nonzero(bright & mid)
        core = [(cx.min() + cx.max()) / 2 - 156.5, (cy.min() + cy.max()) / 2 - 156.5] if len(cx) else [0, 20]
        return dict(anim=True, k=1, y=GIANT_Y, core=[round(v * GIANT_K) for v in core])
    p = os.path.join(SRC, 'HU-ANH_khong-lo.png')
    if not os.path.exists(p):
        return None
    sys.path.insert(0, HERE)
    from vung_dat import save, shrink
    a = np.array(Image.open(p).convert('RGBA'))
    a[outside(a) | key(a), 3] = 0                # and the magenta caught inside its smoke
    x0, y0, x1, y1 = Image.fromarray(a).getbbox()
    a = a[y0:y1, x0:x1]
    H, W = a.shape[:2]
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    bright = (a[..., 3] > 0) & (r > 200) & (g > 170) & (b > 220)
    # the core: the bright crystal in the middle column, below the eyes; the eyes: bright in the top part
    mid = np.zeros_like(bright)
    mid[int(H * 0.35):int(H * 0.85), int(W * 0.42):int(W * 0.58)] = True
    cy, cx = np.nonzero(bright & mid)
    top = np.zeros_like(bright)
    top[:int(H * 0.4), int(W * 0.25):int(W * 0.75)] = True
    ey, ex = np.nonzero(bright & top)
    k = GIANT_W / W
    small = shrink(Image.fromarray(a), k)
    save(small, os.path.join(out, 'khong-lo.png'), optimize=True)
    core = [round((cx.min() + cx.max()) / 2 * k), round((cy.min() + cy.max()) / 2 * k)] if len(cx) else [small.width // 2, round(small.height * 0.6)]
    eyes = [round(ex.min() * k), round(ey.min() * k), round(ex.max() * k), round(ey.max() * k)] if len(ex) else None
    return dict(w=small.width, h=small.height, core=core, eyes=eyes)


# the altar on the world map (DAI_ban-do.png): its gems where the painter put them, red Hỏa, white Kim, blue Thủy,
# green Mộc, gold Thổ (picture px), so the game can dim those whose Thần thú is not freed yet
DAI_GEMS = {'hoa': (517, 300), 'kim': (925, 300), 'thuy': (393, 465), 'moc': (1047, 465), 'tho': (713, 605)}
DAI_W = 34                                  # its width on the 640 px map


def dai(out):
    """img/vg/dai.png: the altar off its magenta, at DAI_W wide. -> {w, h, gems: {he: [x, y]}}, or None"""
    p = os.path.join(SRC, 'DAI_ban-do.png')
    if not os.path.exists(p):
        return None
    sys.path.insert(0, HERE)
    from vung_dat import save, shrink
    a = np.array(Image.open(p).convert('RGBA'))
    a[outside(a), 3] = 0                         # the pentagram's bright violet inside stays
    im = Image.fromarray(a)
    x0, y0, x1, y1 = im.getbbox()
    k = DAI_W / (x1 - x0)
    small = shrink(im.crop((x0, y0, x1, y1)), k)
    save(small, os.path.join(out, 'dai.png'), optimize=True)
    return dict(w=small.width, h=small.height, gems={h: [round((x - x0) * k), round((y - y0) * k)] for h, (x, y) in DAI_GEMS.items()})


# the arena of the last fight: its stone floor's ring (centre y, half width, half height) on the 640x480 picture, read
# off the painting (inside its low wall, behind the front steps)
SAN = dict(id='hu_dai-ngu-hanh', file='ui/san/hu_dai-ngu-hanh.png', y=270, rx=284, ry=108)


def san():
    """Into the arena page: its picture at 640x480, and its entry in san.json (written again whenever it is missing:
    scripts/san_keo.py makes san.json again from its own copy, which does not list it). -> the entry, or None"""
    p = os.path.join(SRC, 'SAN_dai-ngu-hanh.png')
    if not os.path.exists(p):
        return None
    sys.path.insert(0, HERE)
    from vung_dat import save
    import json
    folder = os.path.join(ROOT, 'preview', 'dau-truong', 'ui', 'san')
    dst = os.path.join(ROOT, 'preview', 'dau-truong', *SAN['file'].split('/'))
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(p):
        save(Image.open(p).convert('RGB').resize((640, 480), Image.LANCZOS), dst, optimize=True)
    jpath = os.path.join(folder, 'san.json')
    man = json.load(open(jpath, encoding='utf-8'))
    if man.get('hu') != [SAN]:
        man['hu'] = [SAN]
        tmp = f'{jpath}.{os.getpid()}.tmp'
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(man, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, jpath)
    return SAN


HE5 = ['hoa', 'kim', 'moc', 'thuy', 'tho']   # NGOC-HON's order
NGOC_H = 26                                 # a Ngọc Hồn's height on the screen


def ngoc(out):
    """img/vg/ngoc.png: the gems in a 5x2 grid of cw x ch cells (row 1 won, row 2 not yet) -> {cw, ch, he}, or None"""
    p = os.path.join(SRC, 'NGOC-HON.png')
    if not os.path.exists(p):
        return None
    sys.path.insert(0, HERE)
    from vung_dat import save, shrink
    fr, _, _ = skill_frames(p, 5, 2, soft=True)
    k = NGOC_H / max(f.height for f, _, _ in [x for x in fr if x])
    cells = [shrink(f, k) if f else None for f, _, _ in [x or (None, 0, 0) for x in fr]]
    cw, ch = max(c.width for c in cells if c), max(c.height for c in cells if c)
    at = Image.new('RGBA', (cw * 5, ch * 2), (0, 0, 0, 0))
    for i, c in enumerate(cells):
        if c:
            at.alpha_composite(c, ((i % 5) * cw + (cw - c.width) // 2, (i // 5) * ch + (ch - c.height) // 2))
    save(at, os.path.join(out, 'ngoc.png'), optimize=True)
    return dict(cw=cw, ch=ch, he=HE5)


# the altar's films, 4:3 paintings, cut to 16:9 (the films' shape: game/src/phim.js shows a picture 640x360): the
# band kept starts this far down (px of the painting); PHIM_7 twice, its top and its bottom
PHIM_CUTS = {'PHIM_6_dat-ngoc': [('PHIM_6_dat-ngoc', 100)], 'PHIM_8_ket': [('PHIM_8_ket', 50)],
             'PHIM_7_hu-anh-thuc': [('PHIM_7_hu-anh-thuc', 0), ('PHIM_7_hu-anh-thuc_duoi', None)]}


def phim():
    """Into assets/source/phim/ (made again when the painting is newer). -> the film pictures' names"""
    out, names = os.path.join(ROOT, 'assets', 'source', 'phim'), []
    for src, cuts in PHIM_CUTS.items():
        p = os.path.join(SRC, src + '.png')
        if not os.path.exists(p):
            continue
        im = None
        for name, y0 in cuts:
            dst = os.path.join(out, name + '.png')
            names.append(name)
            if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(p):
                continue
            im = im or Image.open(p).convert('RGB')
            h = round(im.width * 9 / 16)
            y0 = im.height - h if y0 is None else y0
            im.crop((0, y0, im.width, y0 + h)).save(dst, optimize=True)
    return names


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print(arena(), 'tấm vào', ARENA_IMG)
    if '--xem' in sys.argv:
        m = skills(os.path.join(ROOT, 'build', 'vung-dat', 'hu'))
        print({k: (v['cw'], v['ch'], len([f for f in v['f'] if f])) for k, v in m.items()})
        print(giant(os.path.join(ROOT, 'build', 'vung-dat', 'hu')))
