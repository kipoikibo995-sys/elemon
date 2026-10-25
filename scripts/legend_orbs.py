"""Golden flame orbs that circle a legend (prototype asset), drawn pixel by pixel.

Writes one sheet: 4 flicker frames (columns) x 3 sizes (rows) of a small teardrop flame, solid colours on
magenta #FF00FF, plus 4 frames of a 4-point sparkle in the last row. The game puts the orbs on an ellipse around
the pet's waist: the ones on the far side are drawn behind the pet, the near ones in front, a little bigger.
Usage: python legend_orbs.py <out.png> [palette: vang|hoa|kim|moc|thuy|tho]
"""
import sys
import math
import numpy as np
from PIL import Image

PAL = {   # outline, edge, body, core
    'vang': [(120, 62, 8), (232, 150, 24), (255, 214, 64), (255, 252, 214)],
    'hoa':  [(130, 30, 10), (236, 96, 24), (255, 186, 50), (255, 248, 200)],
    'kim':  [(70, 90, 130), (160, 190, 230), (226, 238, 255), (255, 255, 255)],
    'moc':  [(30, 90, 30), (90, 190, 60), (180, 240, 100), (240, 255, 200)],
    'thuy': [(20, 70, 160), (50, 150, 236), (140, 224, 255), (236, 255, 255)],
    'tho':  [(110, 64, 16), (206, 140, 40), (248, 204, 90), (255, 246, 196)],
}
CELL = 24
SIZES = [5, 7, 9]           # flame body radius in px for small / medium / large


def flame(r, t, pal):
    """a teardrop flame of radius r, tip swaying with t (0..3); returns CELLxCELL RGBA"""
    img = np.zeros((CELL, CELL, 4), np.uint8)
    cx, cy = CELL / 2, CELL - 3 - r
    sway = [0, 1, 0, -1][t]
    tall = r * (1.9 + 0.25 * [0, 1, 2, 1][t])
    for y in range(CELL):
        for x in range(CELL):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            if dy >= 0:
                d = math.hypot(dx, dy) / r                         # round bottom
            else:
                k = -dy / tall                                     # 0 at the middle, 1 at the tip
                if k >= 1:
                    continue
                w = r * (1 - k) ** 1.4
                d = abs(dx - sway * k * r * 0.6) / max(w, 0.01)
                d = max(d, k)
            if d > 1:
                continue
            band = 0 if d > 0.86 else 1 if d > 0.62 else 2 if d > 0.32 else 3
            img[y, x, :3] = pal[band]; img[y, x, 3] = 255
    return img


def sparkle(t, pal):
    img = np.zeros((CELL, CELL, 4), np.uint8)
    c = CELL // 2
    arm = [3, 6, 8, 5][t]
    for i in range(-arm, arm + 1):
        a = abs(i)
        col = pal[3] if a <= 1 else pal[2] if a <= arm // 2 else pal[1]
        for (y, x) in ((c + i, c), (c, c + i)):
            img[y, x, :3] = col; img[y, x, 3] = 255
    img[c - 1:c + 2, c - 1:c + 2, :3] = pal[3]; img[c - 1:c + 2, c - 1:c + 2, 3] = 255
    return img


if __name__ == '__main__':
    pal = PAL[sys.argv[2] if len(sys.argv) > 2 else 'vang']
    sheet = np.zeros((CELL * 4, CELL * 4, 4), np.uint8)
    for row, r in enumerate(SIZES):
        for t in range(4):
            sheet[row * CELL:(row + 1) * CELL, t * CELL:(t + 1) * CELL] = flame(r, t, pal)
    for t in range(4):
        sheet[3 * CELL:4 * CELL, t * CELL:(t + 1) * CELL] = sparkle(t, pal)
    out = Image.new('RGB', (CELL * 4, CELL * 4), (255, 0, 255))
    out.paste(Image.fromarray(sheet), (0, 0), Image.fromarray(sheet))
    out.save(sys.argv[1])
    print(sys.argv[1], out.size)
