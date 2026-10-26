"""Arena backdrops: turns every picture in assets/source/dau-truong/<element>/ into a ready 640x480 arena.

Drop a new picture (png / webp / jpg, any size, 4:3 or wide 2:1) into the folder of its element (hoa, thuy, moc, tho,
kim, or chung for a neutral one) and run this. For each picture:
  1. trims the plain borders a screenshot or a generator leaves (black or white bands),
  2. fits it to 640 wide; a wide picture is also stretched a little in height (at most x1.26) so the floor fills more
     of the 4:3 screen,
  3. finds the fighting floor: a flood fill from the middle of the picture over the floor's colour, then its bounding
     box is the ring's inside,
  4. moves the picture up or down so that floor ends just above the skill icons (y 445), fills the rest with dark,
  5. writes preview/dau-truong/ui/san/<element>_<name>.png (full colour) and assets/r36s/dau-truong/<element>_<name>.png
     (the R36S copy: colours cut to RGB565 and a 64-colour palette, no dithering),
  6. lists every arena with its ring (centre y, half width, half height) in preview/dau-truong/ui/san/san.json, which
     the arena page reads. The world map can use the same list later: arenas are grouped by element.
Also writes preview/dau-truong/ui/san/_xem.png, all arenas side by side with the found ring drawn on them, to check.
Usage: python lam_san_dau.py
"""
import json, os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'source', 'dau-truong')
OUT = os.path.join(ROOT, 'preview', 'dau-truong', 'ui', 'san')
R36S = os.path.join(ROOT, 'assets', 'r36s', 'dau-truong')
ELEMENTS = ['hoa', 'thuy', 'moc', 'tho', 'kim', 'chung']
W, H = 640, 480
FLOOR_BOTTOM = 445          # where the floor should end: just above the skill icons
MAX_STRETCH = 1.26          # how much a wide picture may be stretched in height
DARK = (8, 10, 14)
RING_TOP = 100              # the ring never reaches higher than this: the health bars live above it
RING_MAX_RX = 296           # nor closer than this to the screen's sides


def trim(im):
    """Cut plain bands (near black or near white) off all four sides."""
    g = im.convert('L')
    w, h = g.size
    px = g.load()
    def plain(vals):
        m = sum(vals) / len(vals)
        return (m < 22 or m > 235) and max(vals) - min(vals) < 40
    top, bot, left, right = 0, h, 0, w
    while top < h // 4 and plain([px[x, top] for x in range(0, w, 4)]): top += 1
    while bot > h * 3 // 4 and plain([px[x, bot - 1] for x in range(0, w, 4)]): bot -= 1
    while left < w // 4 and plain([px[left, y] for y in range(top, bot, 4)]): left += 1
    while right > w * 3 // 4 and plain([px[right - 1, y] for y in range(top, bot, 4)]): right -= 1
    return im.crop((left, top, right, bot))


def find_floor(im):
    """Bounding box of the floor: flood fill from a few points in the middle over similar colours, keep the biggest."""
    best = None
    w, h = im.size
    for fx, fy in ((0.5, 0.62), (0.4, 0.6), (0.6, 0.6), (0.5, 0.7)):
        probe = im.copy()
        ImageDraw.floodfill(probe, (int(w * fx), int(h * fy)), (255, 0, 255), thresh=70)
        data = probe.load()
        xs, ys = [], []
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                if data[x, y] == (255, 0, 255): xs.append(x); ys.append(y)
        if not xs: continue
        box = (min(xs), min(ys), max(xs), max(ys))
        area = (box[2] - box[0]) * (box[3] - box[1])
        if best is None or area > best[0]: best = (area, box)
    return best[1] if best else (int(w * 0.05), int(h * 0.3), int(w * 0.95), int(h * 0.92))


def build(path, he, name):
    im = trim(Image.open(path).convert('RGB'))
    w, h = im.size
    sx = W / w
    sy = sx * min(MAX_STRETCH, max(1.0, (H / W) / (h / w))) if h / w < H / W else sx
    fit = im.resize((W, round(h * sy)), Image.LANCZOS)
    x0, y0, x1, y1 = find_floor(fit)
    oy = FLOOR_BOTTOM - y1
    oy = max(H - fit.height, min(60, oy))           # never leave a gap at the bottom; at most 60 px of dark on top
    canvas = Image.new('RGB', (W, H), DARK)
    canvas.paste(fit, (0, oy))
    top, bottom = max(RING_TOP, y0 + oy + 10), min(FLOOR_BOTTOM - 10, y1 + oy - 10)       # an open floor runs to the edges: keep the ring under the HUD
    ring = {'y': round((top + bottom) / 2), 'rx': min(RING_MAX_RX, max(120, round((x1 - x0) / 2) - 12)), 'ry': max(60, round((bottom - top) / 2))}
    return canvas, ring, (x0, y0 + oy, x1, y1 + oy)


def r36s_copy(im):
    """RGB565, then a 64-colour palette (no dithering): what the console shows, and a small file."""
    q = im.point(lambda v: round(v / 255 * 31) * 255 // 31)
    return q.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)


def main():
    os.makedirs(OUT, exist_ok=True); os.makedirs(R36S, exist_ok=True)
    listing, previews = {he: [] for he in ELEMENTS}, []
    for he in ELEMENTS:
        folder = os.path.join(SRC, he)
        if not os.path.isdir(folder): continue
        for fn in sorted(os.listdir(folder)):
            if not fn.lower().endswith(('.png', '.webp', '.jpg', '.jpeg')): continue
            name = os.path.splitext(fn)[0]
            canvas, ring, box = build(os.path.join(folder, fn), he, name)
            key = f'{he}_{name}'
            canvas.save(os.path.join(OUT, key + '.png'), optimize=True)
            r36s_copy(canvas).save(os.path.join(R36S, key + '.png'), optimize=True)
            listing[he].append({'id': key, 'file': 'ui/san/' + key + '.png', **ring})
            prev = canvas.copy(); d = ImageDraw.Draw(prev)
            d.ellipse((320 - ring['rx'], ring['y'] - ring['ry'], 320 + ring['rx'], ring['y'] + ring['ry']), outline=(255, 0, 255), width=2)
            d.text((6, 460), key, fill=(255, 255, 0))
            previews.append(prev)
            print(f'{key:24s} ring y={ring["y"]} rx={ring["rx"]} ry={ring["ry"]}  r36s {os.path.getsize(os.path.join(R36S, key + ".png")) // 1024} KB')
    with open(os.path.join(OUT, 'san.json'), 'w', encoding='utf-8') as f:
        json.dump({he: v for he, v in listing.items() if v}, f, ensure_ascii=False, indent=1)
    if previews:
        cols = 3; rows = (len(previews) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * 320, rows * 240), (0, 0, 0))
        for i, p in enumerate(previews): sheet.paste(p.resize((320, 240)), ((i % cols) * 320, (i // cols) * 240))
        sheet.save(os.path.join(OUT, '_xem.png'))
    print('ok', sum(len(v) for v in listing.values()), 'arenas')


if __name__ == '__main__':
    main()
