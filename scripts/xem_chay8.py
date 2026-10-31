"""A drawn run cycle (ChatGPT, 4x2 on magenta: assets/source/tinh-linh/_ve-chay/tai-ve/<pet>_<stage>_<dir>_chay8*.png) cut
into its 8 frames, keyed, set on one ground line and one centre, and shown looping beside the arena's run row it would
replace (the stage's <dir>.png row 2, as it plays now): build/xem-chieu-boss/chay8_<name>.gif, and the frames as
build/xem-chieu-boss/chay8_<name>/<i>.png.
    python scripts/xem_chay8.py <sheet.png> <arena sheet, e.g. preview/dau-truong/img/hoa-ho/legend/e.png> [ms]
"""
import os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'xem-chieu-boss')


def key(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    bg = (r > 150) & (b > 150) & (g < 120) & (np.abs(r - b) < 90)         # magenta and its painted fringe
    if a.shape[-1] == 4:
        bg |= a[..., 3] < 128                                               # or drawn on a clear background
    return bg


def cut(path, cols, rows):
    """cols x rows frames, each cut at the emptiest line near its grid line, keyed: [(RGBA crop, bottom, centre x)]"""
    a = np.array(Image.open(path).convert('RGBA'))
    bg = key(a)
    a[bg, 3] = 0
    H, W = bg.shape
    ink = ~bg
    def lines(n, size, count):
        out = [0]
        for i in range(1, n):
            nom, rng = round(i * size / n), round(size / n * 0.3)
            seg = count[nom - rng:nom + rng + 1]
            out.append(nom - rng + int(np.argmin(seg)))
        return out + [size]
    ys = lines(rows, H, ink.sum(1))
    frames = []
    for r in range(rows):
        band = ink[ys[r]:ys[r + 1]]
        xs = lines(cols, W, band.sum(0))
        for c in range(cols):
            m = band[:, xs[c]:xs[c + 1]]
            # the biggest blob only (stray specks of other frames or of the key left out)
            yy, xx = np.nonzero(m)
            if not len(xx):
                frames.append(None); continue
            y0, y1, x0, x1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
            px = a[ys[r] + y0:ys[r] + y1, xs[c] + x0:xs[c] + x1].copy()
            alpha = px[..., 3] > 0
            cx = np.nonzero(alpha.any(0))[0]
            # the body's centre: the middle of its columns weighted by how much of it each holds (tail and scarf
            # sway, the body does not)
            w = alpha.sum(0).astype(float)
            centre = float((np.arange(len(w)) * w).sum() / max(1, w.sum()))
            frames.append((Image.fromarray(px), y1 - y0, centre))
    return frames


def strip(frames, size):
    """each frame on a size x size canvas: bottoms on one line, centres on one column"""
    out = []
    for f in frames:
        c = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        if f:
            im, h, cx = f
            c.alpha_composite(im, (int(round(size / 2 - cx)), size - 12 - h))
        out.append(c)
    return out


def main():
    sheet, arena = sys.argv[1], sys.argv[2]
    ms = int(sys.argv[3]) if len(sys.argv) > 3 else 90
    name = os.path.splitext(os.path.basename(sheet))[0]
    new = cut(sheet, 4, 2)
    old = cut(arena, 4, 4)[4:8]                                  # the run row it replaces
    k = max(max(f[0].height for f in new if f), max(f[0].height for f in old if f))
    scale_old = 1.0
    size = int(k * 1.25)
    newc = strip(new, size)
    # the old row at the same body height, as the game would show the two
    hn = np.median([f[1] for f in new if f]); ho = np.median([f[1] for f in old if f]); scale_old = hn / ho
    old = [(f[0].resize((round(f[0].width * scale_old), round(f[0].height * scale_old)), Image.LANCZOS), round(f[1] * scale_old), f[2] * scale_old) if f else None for f in old]
    oldc = strip(old, size)
    d = os.path.join(OUT, 'chay8_' + name)
    os.makedirs(d, exist_ok=True)
    for i, f in enumerate(newc):
        f.save(os.path.join(d, f'{i}.png'))
    # the GIF: old (4 frames, 100 ms each, as the arena plays them) left, new (8 frames, ms each) right, 2.4 s
    bg = (58, 52, 44, 255)
    pics = []
    for t in range(0, 2400, 30):
        p = Image.new('RGBA', (size * 2 + 20, size), bg)
        p.alpha_composite(oldc[(t // 100) % 4], (0, 0))
        p.alpha_composite(newc[(t // ms) % 8], (size + 20, 0))
        pics.append(p.convert('RGB').convert('P', palette=Image.ADAPTIVE))
    gif = os.path.join(OUT, f'chay8_{name}.gif')
    pics[0].save(gif, save_all=True, append_images=pics[1:], duration=30, loop=0)
    # and a sheet of the 8 cut frames
    s = Image.new('RGBA', (size * 8, size), bg)
    for i, f in enumerate(newc):
        s.alpha_composite(f, (i * size, 0))
    s.convert('RGB').save(os.path.join(OUT, f'chay8_{name}_khung.png'))
    print(gif, 'frames', [f[0].size if f else None for f in new], 'old scaled x%.2f' % scale_old)


if __name__ == '__main__':
    main()
