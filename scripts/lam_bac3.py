"""Level-3 (bậc 3) skill effect sheets, drawn from the level-2 ones (trial: Hỏa Quy).

Each sheet is one picture: the level-3 frames and their in-betweens on alternating rows, like lam_bac2's jobs. The ChatGPT
tab driver (lam_bac2_tab.js) saves lv2__<prefix>__b3_<n>x.png; gather() splits it into chieu/<prefix>_<n>_lv3.png and
_lv3_mid.png. Nothing is copied to the arena page yet (the R36S build reads preview/dau-truong/).

Usage: python lam_bac3.py jobs   -> _ve-bac3/jobs/<prefix>.json
       python lam_bac3.py gom    -> every lv2__<prefix>__b3_<n>x.png Chrome saved, split and taken in
"""
import json, os, re, sys, tempfile
from PIL import Image

from optimize_sheet import optimize
from creatures import NAMES
from lam_bac2 import (CHIEU, DOWNLOADS, ELEMENT, SHEET, TL, COMBO, ORDER_2, ORDER_3, grid, row_cuts, soften)

OUT = os.path.join(TL, '_ve-bac3')

NOTES = {
    'HO-T2_hoa-quy': {
        '2': 'Shell Roll: the rolling shell is wrapped in a blazing phoenix-fire comet with a long trail of golden runes, '
             'the impact erupts into a lava dome with a ring of fire pillars.',
        '4': 'Volcano Turtle slam: a giant spectral volcano-turtle spirit rises behind the slam, a burning rune seal opens '
             'on the ground, molten fissures spread to the cell edges and a column of fire erupts to the sky.',
    },
}

COMMON = """Create an image. Pixel art game VFX sprite sheet. The attached image is the LEVEL-2 version of a skill effect sheet of {name} ({element}). Redraw it as the LEVEL-3 (mythic tier) version, FRAME FOR FRAME: exactly the same grid of {cols} columns x {rows} rows, the same order, every frame shows the same moment as the attached frame in the same cell, facing right, same pixel art style with a dark outline. Canvas {canvas}. Flat solid magenta background #FF00FF everywhere (no gradient, no shadow, no text, no numbers, no grid lines). Each effect stays inside its own cell and must not touch its neighbours.
Level-3 rules: one tier ABOVE the attached level 2, a MYTHIC, god-tier move: keep everything level 2 has (thick lightning, shockwaves) and add a GLOWING MAGIC RUNE CIRCLE / SEAL, a translucent SPIRIT-BEAST silhouette of the creature made of energy, and pillars of light; the effect fills more of its cell than level 2 but still ENDS inside the cell with a clear magenta gap on every side, never cut by the cell border. Big bold shapes, thick outlines, flat colour blocks, high contrast, no tiny particle noise. Keep the {colours} colours with {accent}, plus a new deep violet-black core shadow and white-gold divine light so it clearly reads as a higher tier than level 2.
This sheet: {note}"""


def jobs():
    os.makedirs(os.path.join(OUT, 'jobs'), exist_ok=True)
    for pre, notes in NOTES.items():
        colours, accent, bolt = ELEMENT[pre[:2]]
        steps = []
        for n, note in notes.items():
            if os.path.exists(os.path.join(CHIEU, f'{pre}_{n}_lv3.png')):
                continue
            cols, nrows = grid(os.path.join(CHIEU, f'{pre}_{n}.png'))
            text = COMMON.format(name=NAMES[pre.split('_', 1)[1]], element=colours.split(':')[0], cols=cols,
                                 rows=2 * nrows, canvas='portrait 2:3' if nrows == 3 else 'square 1:1',
                                 colours=colours.split(': ')[1], accent=accent, note=SHEET.get(n, n) + ' - ' + note)
            combo = COMBO.replace('level-2', 'level-3').format(third=', row 5 = its row 3' if nrows == 3 else '',
                                                                 order=ORDER_3 if nrows == 3 else ORDER_2)
            steps.append(dict(sheet=f'b3_{n}x', file=f'{pre}_{n}_lv2.png', mid='', prompt=' '.join(text.splitlines()) + ' ' + combo))
        if steps:
            with open(os.path.join(OUT, 'jobs', pre + '.json'), 'w', encoding='utf-8') as f:
                json.dump(dict(prefix=pre, steps=steps), f, ensure_ascii=False)
            print(pre, len(steps), 'sheets')


def take_in(src, pre, n, suf):
    """each cell of a half fitted into the level-1 cell size, edges faded, optimized -> chieu/<..>_<n>_lv3<suf>.png"""
    cols, nrows = grid(os.path.join(CHIEU, f'{pre}_{n}.png'))
    tw, th = Image.open(os.path.join(CHIEU, f'{pre}_{n}.png')).size
    sw, sh = src.size
    out = Image.new('RGB', (tw, th), (255, 0, 255))
    cw, ch, dw, dh = sw / cols, sh / nrows, tw / cols, th / nrows
    k = min(dw / cw, dh / ch)
    for r in range(nrows):
        for c in range(cols):
            cell = src.crop((round(c * cw), round(r * ch), round((c + 1) * cw), round((r + 1) * ch)))
            cell = cell.resize((max(1, round(cell.width * k)), max(1, round(cell.height * k))), Image.NEAREST)
            out.paste(cell, (round(c * dw + (dw - cell.width) / 2), round(r * dh + (dh - cell.height) / 2)))
    out = soften(out, cols, nrows)
    dst = os.path.join(CHIEU, f'{pre}_{n}_lv3{suf}.png')
    tmp = os.path.join(tempfile.gettempdir(), f'{pre}_{n}_lv3{suf}_tmp.png')
    out.save(tmp)
    optimize(tmp, dst)
    os.remove(tmp)
    print(dst)


def gather():
    keep = os.path.join(OUT, 'tai-ve')
    os.makedirs(keep, exist_ok=True)
    for f in sorted(os.listdir(DOWNLOADS)):
        m = re.fullmatch(r'lv2__([A-Z]{2}-[A-Z0-9]+_[a-z-]+)__b3_([a-z0-9]+)x\.png', f)
        if not m:
            continue
        pre, n = m.groups()
        src = os.path.join(keep, f)
        os.replace(os.path.join(DOWNLOADS, f), src)
        im = Image.open(src).convert('RGB')
        rows = 2 * grid(os.path.join(CHIEU, f'{pre}_{n}.png'))[1]
        cuts, slot = row_cuts(im, rows), im.height // rows
        for odd, suf in ((0, ''), (1, '_mid')):
            half = Image.new('RGB', (im.width, slot * rows // 2), (255, 0, 255))
            for k, r in enumerate(range(odd, rows, 2)):
                band = im.crop((0, cuts[r], im.width, cuts[r + 1]))
                if band.height > slot:
                    top = (band.height - slot) // 2
                    band = band.crop((0, top, im.width, top + slot))
                half.paste(band, (0, k * slot + (slot - band.height) // 2))
            take_in(half, pre, n, suf)


if __name__ == '__main__':
    {'jobs': jobs, 'gom': gather}.get(sys.argv[1:2] and sys.argv[1], lambda: print(__doc__))()
