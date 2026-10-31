"""A drawn 8-frame run cycle into the arena: assets/source/tinh-linh/_ve-chay/tai-ve/<pet>_<stage>_<dir>_chay8*.png (the
newest of a pet, stage and direction; ChatGPT, 4x2 on magenta) -> preview/dau-truong/img/<pet>/<stage>/<dir>_chay8.png,
a 4x2 sheet laid out like the arena's own: the cells the size of that stage's <dir>.png cells, each frame at the size the
body has there (its run row's median height) and standing where that row's frames stand (their feet line, their middle),
on magenta. The arena plays it while the pet runs that way (game/src/solo.js, its run hook); the old run row stays for
a direction not drawn.
    python scripts/ghep_chay8.py [pet stage dir ...]      (no arguments: every drawn one)
"""
import glob, os, re, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'assets', 'source', 'tinh-linh', '_ve-chay', 'tai-ve')
ARENA = os.path.join(ROOT, 'preview', 'dau-truong', 'img')
sys.path.insert(0, HERE)
from xem_chay8 import cut, key                         # noqa: E402


def place(pet, stage, d, src):
    old_path = os.path.join(ARENA, pet, stage, d + '.png')
    old = np.array(Image.open(old_path).convert('RGBA'))
    H, W = old.shape[:2]
    cw, ch = W // 4, H // 4
    # the run row as the arena has it: each frame's height, feet line and middle inside its cell
    bg = key(old)
    hs, feet, mids = [], [], []
    for c in range(4):
        m = ~bg[ch:2 * ch, c * cw:(c + 1) * cw]
        yy, xx = np.nonzero(m)
        if not len(xx):
            continue
        hs.append(yy.max() - yy.min() + 1); feet.append(yy.max() + 1)
        w = m.sum(0).astype(float); mids.append(float((np.arange(cw) * w).sum() / max(1, w.sum())))
    H0, F0, M0 = np.median(hs), int(np.median(feet)), np.median(mids)
    new = [f for f in cut(src, 4, 2) if f]
    if len(new) != 8:
        raise SystemExit(f'{src}: {len(new)} frames, not 8')
    k = H0 / np.median([f[1] for f in new])             # the body at the arena's size
    out = Image.new('RGBA', (cw * 4, ch * 2), (255, 0, 255, 255))
    for i, (im, h, cx) in enumerate(new):
        im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
        a = np.array(im); a[..., 3] = np.where(a[..., 3] < 110, 0, 255); im = Image.fromarray(a)
        x = (i % 4) * cw + round(M0 - cx * k)
        y = (i // 4) * ch + F0 - im.height
        cell = Image.new('RGBA', (cw * 4, ch * 2), (0, 0, 0, 0))
        cell.alpha_composite(im, (max(0, x), max(0, y)))
        # kept inside its own cell (the arena cuts on the grid)
        box = Image.new('L', (cw * 4, ch * 2), 0)
        box.paste(255, ((i % 4) * cw + 2, (i // 4) * ch + 2, (i % 4 + 1) * cw - 2, (i // 4 + 1) * ch - 2))
        cell.putalpha(Image.fromarray(np.minimum(np.array(cell.getchannel('A')), np.array(box))))
        out.alpha_composite(cell)
    dst = os.path.join(ARENA, pet, stage, d + '_chay8.png')
    out.convert('RGB').save(dst)
    return dst, k


def main():
    args = sys.argv[1:]
    jobs = [tuple(args[i:i + 3]) for i in range(0, len(args), 3)] if args else sorted({
        m.groups() for p in glob.glob(os.path.join(SRC, '*_chay8*.png'))
        for m in [re.match(r'^(.+)_(child|teen|adult|legend)_(s|se|e|ne|n)_chay8', os.path.basename(p))] if m})
    for pet, stage, d in jobs:
        srcs = sorted(glob.glob(os.path.join(SRC, f'{pet}_{stage}_{d}_chay8*.png')), key=os.path.getmtime)
        if not srcs:
            print('  no drawing for', pet, stage, d); continue
        dst, k = place(pet, stage, d, srcs[-1])
        print(f'{dst}  <- {os.path.basename(srcs[-1])} (x{k:.2f})')


if __name__ == '__main__':
    main()
