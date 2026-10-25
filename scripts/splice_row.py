"""Replaces one row of a grid sheet (magenta background) with the cells of a 1-row strip.

Each strip cell's sprite is cut out, scaled so the strip frame at REF matches the height of the sheet frame it
replaces at that position, and pasted into its cell, centred, feet on the cell's old feet line.
Usage: python splice_row.py <sheet.png> <cols> <rows> <row index> <strip.png> [ref column, default 2]
"""
import sys
import numpy as np
from PIL import Image

from slice_frames import magenta


def boxes(img, cols, rows, row=None):
    """sprite bbox (x0, y0, x1, y1) in sheet px for every cell of a row (or the only row)"""
    a = np.array(img.convert('RGB')).astype(np.int32)
    fg = ~magenta(a)
    cw, ch = img.width / cols, img.height / rows
    out = []
    r = 0 if row is None else row
    for c in range(cols):
        x0, y0 = round(c * cw), round(r * ch)
        m = fg[y0:round(y0 + ch), x0:round(x0 + cw)].copy()
        m[:3] = m[-3:] = False; m[:, :3] = m[:, -3:] = False      # neighbour's spill at the edges
        ys, xs = np.where(m)
        out.append((x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1))
    return out


def main(sheet_path, cols, rows, row, strip_path, ref=2):
    sheet = Image.open(sheet_path).convert('RGB')
    strip = Image.open(strip_path).convert('RGB')
    old = boxes(sheet, cols, rows, row)
    new = boxes(strip, cols, 1)
    k = (old[ref][3] - old[ref][1]) / (new[ref][3] - new[ref][1])
    cw, ch = sheet.width / cols, sheet.height / rows
    s = np.array(strip).astype(np.int32)
    for c in range(cols):
        x0, y0, x1, y1 = new[c]
        part = strip.crop((x0, y0, x1, y1))
        mask = Image.fromarray((~magenta(s[y0:y1, x0:x1]) * 255).astype(np.uint8))
        fit = min(k, (cw - 8) / part.width, (ch - 6) / part.height)     # a wide pose shrinks a little to fit
        w, h = max(1, round(part.width * fit)), max(1, round(part.height * fit))
        part, mask = part.resize((w, h), Image.NEAREST), mask.resize((w, h), Image.NEAREST)
        cx, cy0, cy1 = round(c * cw), round(row * ch), round((row + 1) * ch)
        sheet.paste((255, 0, 255), (cx, cy0, round(cx + cw), cy1))
        feet = old[c][3]
        px = cx + round((cw - w) / 2)
        py = max(cy0 + 2, min(feet, cy1 - 2) - h)
        sheet.paste(part, (px, py), mask)
        if w > cw - 4 or py + h > cy1:
            print(f'cell {c}: {w}x{h} does not fit a {round(cw)}x{round(ch)} cell')
    sheet.save(sheet_path)
    print(f'{sheet_path}: row {row} replaced, scale {k:.3f}')


if __name__ == '__main__':
    if len(sys.argv) < 6:
        sys.exit(__doc__)
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5],
         int(sys.argv[6]) if len(sys.argv) > 6 else 2)
