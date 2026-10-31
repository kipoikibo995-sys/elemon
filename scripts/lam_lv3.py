"""Thiếu niên (Lv3) combat sheets, drawn from the Nhi (Lv2) ones: two pictures per creature instead of seven.

  A  8x8: the Nhi sheets s | se over e | ne (4x4 each) redrawn frame for frame with the Thiếu niên body
  B  8x4: n (4x4) on the left, chung (4x2) on the top right, the bottom right left empty
The cut-in stays the Nhi one for now. Each picture's mould is the Nhi sheets put together; the creature's Thiếu niên
sheet (<prefix>_teen.png) goes along as the look to draw. The ChatGPT tab driver (lam_bac2_tab.js) draws the jobs and
saves lv2__<prefix>__teena.png / teenb.png; gather() splits them back into arena/<prefix>_teen_<s|se|e|ne|n|chung>.png
(Nhi sizes) and copies them, with the Nhi cut-in, to preview/dau-truong/img/<slug>/teen/.

The same goes for the Trưởng thành (Lv4) sheets with the stage word `adult`: the look is <prefix>.png (the adult 4x6
sheet), the pictures are lv2__<prefix>__adult{a,b}.png and the sheets arena/<prefix>_adult_<..>.png. Those are not copied
to the arena page yet (the R36S build reads preview/dau-truong/).

Usage: python lam_lv3.py jobs [adult]   -> _ve-lv3/jobs/<prefix>.json + _ve-lv3/khuon/<prefix>_teen{a,b}.png
       python lam_lv3.py gom [adult]    -> every lv2__<prefix>__<stage>{a,b}.png Chrome saved, split (and copied)
       python lam_lv3.py arena adult|legend -> the stage's sheets into preview/dau-truong/img/<slug>/<stage>/
"""
import json, os, re, shutil, sys, tempfile
from PIL import Image

from optimize_sheet import optimize
from lam_bac2 import DOWNLOADS, ROOT, TL, ARENA_IMG, row_cuts, arena_code
from creatures import NAMES

ARENA = os.path.join(TL, 'arena')
OUT = os.path.join(TL, '_ve-lv3')
DIRS_A = ['s', 'se', 'e', 'ne']          # 2x2 blocks, reading order
STAGE = sys.argv[2] if len(sys.argv) > 2 else 'teen'
STAGE_WORD = {'teen': 'TEEN', 'adult': 'ADULT (fully grown)', 'legend': 'LEGENDARY (final mythic form)'}[STAGE]
DIR_WORDS = {'s': 'facing down (towards the viewer)', 'se': 'facing down-right', 'e': 'facing right',
             'ne': 'facing up-right', 'n': 'facing up (back to the viewer)'}

COMMON = ("Create an image. Pixel art sprite sheet for a handheld game. The FIRST attached image is {name} at its {stage} "
          "stage: THIS is the character to draw, exactly as it looks there: its head size, neck, shell or body shape, "
          "body proportions, face, colours, markings and accessories. The SECOND attached image is the same creature at "
          "its smaller CHILD stage and is ONLY a pose and layout guide: {layout} Draw the {short} character in every cell, "
          "doing the pose of the matching cell of the guide, with the same facing and the same order; do NOT copy the "
          "child's proportions, big head or face. The same grid of {cols} columns x {rows} rows, pixel art with a dark "
          "outline, every sprite fully inside its own cell, centred, all at the same size, feet on the same line within a "
          "row, sprites not touching. Flat solid magenta background #FF00FF everywhere (no gradient, no shadow, no text, "
          "no numbers, no grid lines). Small cells are fine: a clean readable silhouette true to the {short} matters more "
          "than fine detail.{extra}")
LAYOUT_A = ("four 4x4 blocks, top-left block = {s}, top-right = {se}, bottom-left = {e}, bottom-right = {ne}; in each "
            "block row 1 guard stance x4, row 2 run x4, row 3 attack wind-up / slash / recover / dash, row 4 charge / "
            "release / hit / stunned.").format(**DIR_WORDS)
LAYOUT_B = ("the left 4x4 block is " + DIR_WORDS['n'] + " (row 1 guard x4, row 2 run x4, row 3 attack wind-up / slash / "
            "recover / dash, row 4 charge / release / hit / stunned); the top-right 4x2 block is the front view: knocked "
            "down x2, victory x2, then ultimate charge x2, ultimate release x2; the bottom-right 4x2 is empty.")


def prefixes():
    return sorted(f[:-len('_child_s.png')] for f in os.listdir(ARENA) if f.endswith('_child_s.png'))


def moulds(pre):
    """the two mould pictures from the Nhi sheets"""
    os.makedirs(os.path.join(OUT, 'khuon'), exist_ok=True)
    sheets = {d: Image.open(os.path.join(ARENA, f'{pre}_child_{d}.png')).convert('RGB') for d in DIRS_A + ['n', 'chung']}
    S = 768                                   # each 4x4 block (the picture goes in small anyway)
    a = Image.new('RGB', (2 * S, 2 * S), (255, 0, 255))
    for k, d in enumerate(DIRS_A):
        a.paste(sheets[d].resize((S, S), Image.LANCZOS), ((k % 2) * S, (k // 2) * S))
    b = Image.new('RGB', (2 * S, S), (255, 0, 255))
    b.paste(sheets['n'].resize((S, S), Image.LANCZOS), (0, 0))
    b.paste(sheets['chung'].resize((S, S // 2), Image.LANCZOS), (S, 0))
    pa, pb = (os.path.join(OUT, 'khuon', f'{pre}_teen{x}.png') for x in 'ab')
    a.save(pa); b.save(pb)
    return pa, pb


def jobs():
    os.makedirs(os.path.join(OUT, 'jobs'), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, 'jobs')):
        os.remove(os.path.join(OUT, 'jobs', f))
    n = 0
    for pre in prefixes():
        if all(os.path.exists(os.path.join(ARENA, f'{pre}_{STAGE}_{d}.png')) for d in DIRS_A + ['n', 'chung']):
            continue                          # drawn already (Mộc Hùng was done by hand)
        pa, pb = moulds(pre)
        name = NAMES[pre.split('_', 1)[1]]
        ref = {'teen': f'{pre}_teen.png', 'legend': f'{pre}_legend.png'}.get(STAGE, f'{pre}.png')
        steps = [dict(sheet=STAGE + 'a', code=arena_code(pre, STAGE + 'a'), file=os.path.basename(pa), files=[ref, os.path.basename(pa)], mid='',
                      prompt=COMMON.format(stage=STAGE_WORD, short=STAGE_WORD.split()[0], name=name, layout=LAYOUT_A, cols=8, rows=8, extra=' Square canvas 1:1.')),
                 dict(sheet=STAGE + 'b', code=arena_code(pre, STAGE + 'b'), file=os.path.basename(pb), files=[ref, os.path.basename(pb)], mid='',
                      prompt=COMMON.format(stage=STAGE_WORD, short=STAGE_WORD.split()[0], name=name, layout=LAYOUT_B, cols=8, rows=4,
                                           extra=' Wide canvas 2:1. Leave the bottom-right 4x2 block empty magenta.'))]
        with open(os.path.join(OUT, 'jobs', pre + '.json'), 'w', encoding='utf-8') as fh:
            json.dump(dict(prefix=pre, steps=steps), fh, ensure_ascii=False)
        n += 1
    print(n, 'jobs ->', os.path.join(OUT, 'jobs'))


def block(im, cuts_x, cuts_y, c0, r0, cols, rows, size):
    """cells c0..c0+cols, r0..r0+rows of the drawing as one Nhi-sized sheet, each cell fitted into its slot"""
    out = Image.new('RGB', size, (255, 0, 255))
    dw, dh = size[0] / cols, size[1] / rows
    for r in range(rows):
        for c in range(cols):
            cell = im.crop((cuts_x[c0 + c], cuts_y[r0 + r], cuts_x[c0 + c + 1], cuts_y[r0 + r + 1]))
            k = min(dw / cell.width, dh / cell.height)
            cell = cell.resize((max(1, round(cell.width * k)), max(1, round(cell.height * k))), Image.LANCZOS)
            out.paste(cell, (round(c * dw + (dw - cell.width) / 2), round(r * dh + (dh - cell.height) / 2)))
    return out


def save(img, pre, d):
    dst = os.path.join(ARENA, f'{pre}_{STAGE}_{d}.png')
    tmp = os.path.join(tempfile.gettempdir(), f'{pre}_{STAGE}_{d}.png')
    img.save(tmp)
    optimize(tmp, dst)
    os.remove(tmp)
    print(dst)
    if STAGE != 'teen':                       # Lv4: kept out of the arena page for now
        return
    slug = pre.split('_', 1)[1]
    os.makedirs(os.path.join(ARENA_IMG, slug, 'teen'), exist_ok=True)
    shutil.copy(dst, os.path.join(ARENA_IMG, slug, 'teen', f'{d}.png'))


def gather():
    keep = os.path.join(OUT, 'tai-ve')
    os.makedirs(keep, exist_ok=True)
    codes = {arena_code(p, STAGE + x): f'lv2__{p}__{STAGE}{x}.png' for p in prefixes() for x in 'ab'}
    for f in sorted(os.listdir(DOWNLOADS)):     # arena.ai names a download after the prompt's first words (its code)
        a = re.match(r'(?:gpt-image.*?_)?a_(Q[0-9a-f]{5})_.*\.(png|webp)$', f)     # sometimes a .webp without the model name
        if a and a.group(1) in codes:
            if a.group(2) == 'webp':
                Image.open(os.path.join(DOWNLOADS, f)).convert('RGB').save(os.path.join(DOWNLOADS, codes[a.group(1)]))
                os.remove(os.path.join(DOWNLOADS, f))
            else:
                os.replace(os.path.join(DOWNLOADS, f), os.path.join(DOWNLOADS, codes[a.group(1)]))
    for f in sorted(os.listdir(DOWNLOADS)):
        m = re.fullmatch(r'lv2__([A-Z]{2}-[A-Z0-9]+_[a-z-]+)__' + STAGE + r'([ab])\.png', f)
        if not m:
            continue
        pre, x = m.groups()
        src = os.path.join(keep, f)
        os.replace(os.path.join(DOWNLOADS, f), src)
        im = Image.open(src).convert('RGB')
        rows = 8 if x == 'a' else 4
        cy = row_cuts(im, rows)
        cx = row_cuts(im.transpose(Image.Transpose.TRANSPOSE), 8)      # the same search across the columns
        if x == 'a':
            for k, d in enumerate(DIRS_A):
                save(block(im, cx, cy, (k % 2) * 4, (k // 2) * 4, 4, 4, (1254, 1254)), pre, d)
        else:
            save(block(im, cx, cy, 0, 0, 4, 4, (1254, 1254)), pre, 'n')
            save(block(im, cx, cy, 4, 0, 4, 2, (1774, 887)), pre, 'chung')
        if STAGE != 'teen':
            continue
        slug = pre.split('_', 1)[1]           # the cut-in: the Nhi one until a Thiếu niên one is drawn
        cut = os.path.join(ARENA_IMG, slug, 'teen', 'cutin.png')
        if not os.path.exists(cut):
            shutil.copy(os.path.join(ARENA_IMG, slug, 'cutin.png'), cut)


def to_arena():
    """The stage's finished sheets (arena/<prefix>_<stage>_<s|se|e|ne|n|chung>.png) into the arena page,
    preview/dau-truong/img/<slug>/<stage>/, with the Nhi cut-in until the stage's own is drawn (28/10/2026: Lv4 and Lv5
    go into Vùng đất's fights)."""
    n = 0
    for f in sorted(os.listdir(ARENA)):
        m = re.fullmatch(r'([A-Z]{2}-[A-Z0-9]+_[a-z-]+)_' + STAGE + r'_(s|se|e|ne|n|chung)\.png', f)
        if not m:
            continue
        slug = m.group(1).split('_', 1)[1]
        out = os.path.join(ARENA_IMG, slug, STAGE)
        os.makedirs(out, exist_ok=True)
        shutil.copy(os.path.join(ARENA, f), os.path.join(out, m.group(2) + '.png'))
        cut = os.path.join(out, 'cutin.png')
        if not os.path.exists(cut):
            shutil.copy(os.path.join(ARENA_IMG, slug, 'cutin.png'), cut)
        n += 1
    print(f'{n} sheet {STAGE} -> {ARENA_IMG}')


if __name__ == '__main__':
    {'jobs': jobs, 'gom': gather, 'arena': to_arena}.get(sys.argv[1:2] and sys.argv[1], lambda: print(__doc__))()
