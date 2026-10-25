"""Makes a sheet small before (or after) it goes into assets/source/.

The magenta background of a generated image is noisy (250,2,249 / 255,0,253 ...), which costs most of
the file. Every pixel slice_frames.py would read as background becomes exact #FF00FF, then the image is
saved as a 256-colour PNG (no dithering): pixel art keeps its look, the file shrinks several times.
A really see-through sheet keeps its alpha (256 colours with alpha).
Usage: python optimize_sheet.py <downloaded.png> <assets/source/...png>
       python optimize_sheet.py --in-place <sheet.png> ...    (a file is only replaced when it gets smaller)
"""
import os, sys, tempfile
import numpy as np
from PIL import Image

from slice_frames import magenta


def optimize(src, dst):
    im = Image.open(src)
    before = os.path.getsize(src)
    if im.mode == 'RGBA' and (np.array(im)[..., 3] == 0).any():
        rgba = np.array(im)
        rgba[rgba[..., 3] == 0] = 0                 # hidden colour under the holes only costs bytes
        out = Image.fromarray(rgba, 'RGBA').quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
        shown = rgba[..., 3] > 0
        back = np.array(out.convert('RGBA')).astype(int)
        err = np.abs(back - rgba.astype(int))[shown].mean()
    else:
        rgb = np.array(im.convert('RGB'))
        bg = magenta(rgb.astype(np.int32))
        rgb[bg] = (255, 0, 255)
        out = Image.fromarray(rgb, 'RGB').quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        # the background must stay the exact key colour, whatever palette entry it was merged into
        if bg.any():
            pal = out.getpalette()[:768]
            idx = np.array(out)
            key = int(np.bincount(idx[bg]).argmax())
            pal[key * 3:key * 3 + 3] = [255, 0, 255]
            idx[bg] = key
            out = Image.fromarray(idx, 'P')
            out.putpalette(pal)
        back = np.array(out.convert('RGB')).astype(int)
        err = np.abs(back - rgb.astype(int))[~bg].mean() if (~bg).any() else 0
    fd, tmp = tempfile.mkstemp(suffix='.png', dir=os.path.dirname(os.path.abspath(dst)))
    os.close(fd)
    out.save(tmp, optimize=True)
    after = os.path.getsize(tmp)
    if src == dst and after >= before:
        os.remove(tmp)
        print(f'{os.path.basename(dst)}: {before / 1024:.0f} KB, already small, kept')
        return before, before
    os.replace(tmp, dst)
    print(f'{os.path.basename(dst)}: {before / 1024:.0f} KB -> {after / 1024:.0f} KB, colour error {err:.1f}')
    return before, after


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--in-place':
        sizes = [optimize(p, p) for p in sys.argv[2:]]
        print(f'total {sum(b for b, _ in sizes) / 2**20:.1f} MB -> {sum(a for _, a in sizes) / 2**20:.1f} MB')
    elif len(sys.argv) == 3:
        optimize(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)
