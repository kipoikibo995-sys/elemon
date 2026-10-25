"""A fully furnished room with one creature living in it: preview/phong-do/<room>_<creature>-<stage>.gif.

Room = empty room + every item of assets/source/do-theo-phong/<room>/ at the place and size in its
vi-tri.json (from place_decor.py, or set by hand in MANUAL below). Items and the creature are drawn
back to front by where they touch the floor, so the creature can walk in front of or behind things.
Everything is laid out on the 1448x1086 room and shrunk to the 320x240 screen at the end.
Usage: python preview_decor_room.py
"""
import glob, json, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import creatures
from place_decor import ROOM_CODE
from preview_anims import STEP, LABELS, breathe, flash, samples

SRC = os.path.join(creatures.ROOT, 'assets', 'source')
DECOR = os.path.join(SRC, 'do-theo-phong')
OUT = os.path.join(creatures.ROOT, 'preview', 'phong-do')
# decor room -> its empty room (nen/phong-trong/PT_<code>_*.png; Hang đá has its own)
EMPTY = {room: found[0] for room, code in ROOM_CODE.items()
         if (found := glob.glob(os.path.join(SRC, 'nen', 'phong-trong', f'PT_{code}_*.png')))}
EMPTY['L1-HO_hang-da'] = os.path.join(SRC, 'nen', 'hang-da', 'phong-trong.png')
ROOM_W, ROOM_H = 1448, 1086
K = 320 / ROOM_W                      # room px -> screen px

# items the matcher could not find in the reference picture: [x, y, scale] set by hand
# (the hand-set places of Hang đá and L3-HO now live in their vi-tri.json, with the tidied layout of every room)
MANUAL = {}
# flat things (mats, rugs, carpets) lie under everything else, whatever their floor line
FLAT = {'03_chieu-nho.png', '04_tham-lon.png'}


def flat(name):
    return name in FLAT or any(w in name for w in ('-rug', '-carpet'))

# (room, creature, stage, feet x and y on the screen, moves)
SCENES = [
    ('L1-HO_hang-da', 'hoa-ho', 'legend', 170, 178, ['idle', 'punch', 'blast', 'victory', 'happy', 'sleep', 'wake']),
    ('L1-HO_hang-da', 'hoa-ho', 'adult4', 160, 165, ['idle', 'walk-across', 'run-across', 'attack', 'eat', 'sleep']),
    ('L1-HO_hang-da', 'hoa-ho', 'legend4', 160, 165, ['idle', 'walk-across', 'run-across', 'attack', 'happy']),
    ('L1-HO_hang-da', 'viem-long', 'adult4', 160, 165, ['idle', 'walk-across', 'run-across', 'attack']),
    ('L1-HO_hang-da', 'kim-te', 'adult4', 160, 165, ['idle', 'walk-across', 'run-across', 'attack']),
    ('L3-HO', 'hoa-ho', 'adult4', 160, 170, ['idle', 'walk-across', 'run-across', 'attack', 'eat', 'sleep']),
    ('L3-HO', 'viem-long', 'legend4', 160, 170, ['idle', 'walk-across', 'run-across', 'attack', 'happy']),
]


def items_of(room):
    """Items at screen size and place; one listed but not (yet) in the folder is left out."""
    pos = json.load(open(os.path.join(DECOR, room, 'vi-tri.json'), encoding='utf-8'))
    pos.update(MANUAL.get(room, {}))
    out = []
    for name, (x, y, s) in pos.items():
        path = os.path.join(DECOR, room, name)
        if not os.path.exists(path):
            print(f'  {room}: thiếu {name}, bỏ qua')
            continue
        img = Image.open(path).convert('RGBA')
        w, h = round(img.width * s * K), round(img.height * s * K)
        img = img.resize((max(1, w), max(1, h)), Image.LANCZOS)
        sx, sy = round(x * K), round(y * K)
        out.append(dict(name=name, img=img, x=sx, y=sy, floor=-1 if flat(name) else sy + h))
    for name in sorted({os.path.basename(p) for p in glob.glob(os.path.join(DECOR, room, '*.png'))} - set(pos)):
        print(f'  {room}: {name} chưa có vị trí (chạy place_decor.py {room}), bỏ qua')
    return out


# moves that travel across the floor: (frames to play, screen px per second, default turn points)
ACROSS = {'walk-across': ('walk', 34, 70, 250), 'run-across': ('run', 110, 60, 260)}
# where the floor ends left and right at the feet line of each room (screen px): the whole body,
# head to tail, must stay between these
FLOOR_X = {'L1-HO_hang-da': (30, 290), 'L3-HO': (30, 295),
           # feet at y 180 / 185 / 182 (scripts/preview_pocketgo.py SCENES)
           'L2-TH': (20, 300), 'L3-KI': (25, 290), 'L4-MO': (50, 285)}


def body_reach(meta, frames, names):
    """How far the body reaches from the feet, the longer of front and back, over these frames."""
    ax = meta['anchor'][0]
    reach = 0
    for n in names:
        box = frames[n].getbbox()
        if box:
            dx = meta['align'].get(n, [0, 0])[0]
            reach = max(reach, ax - dx - box[0], box[2] - ax + dx)
    return reach


def turn_points(room, meta, frames, base):
    """Left and right turn points for the feet so the body never leaves the floor."""
    left, right = FLOOR_X.get(room, (0, 320))
    names = [n for n in meta['frames'] if n.startswith(base + '-')] or meta['frames']
    reach = body_reach(meta, frames, names)
    lo, hi = left + reach, right - reach
    if lo > hi:                      # too long for this floor: pace on the spot
        lo = hi = (left + right) // 2
    return lo, hi


def across(anims, move, cx, lo=None, hi=None):
    """Walk or run right to one turn point, back left past the start to the other, and return: samples
    with the creature's own x offset and whether it faces left."""
    base, speed, dlo, dhi = ACROSS[move]
    lo, hi = (dlo, dhi) if lo is None else (lo, hi)
    cx = min(max(cx, lo), hi)
    cycle = samples(anims[base])
    route = [(cx, hi), (hi, lo), (lo, cx)]
    out, i = [], 0
    for a, b in route:
        steps = max(1, round(abs(b - a) / speed * 1000 / STEP))
        for k in range(steps):
            f, _, y, br, shake, fl = cycle[i % len(cycle)]
            i += 1
            out.append((f, a + (b - a) * (k + 1) / steps - cx, y, br, shake, fl, b < a))
    return out, LABELS.get(base, base) + (' nhanh' if base == 'run' else ' qua lại')


def shadow(w):
    img = Image.new('RGBA', (w + 8, 14), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([4, 3, w + 4, 11], fill=(0, 0, 0, 90))
    return img.filter(ImageFilter.GaussianBlur(1.5))


def scene(room, cid, stage, cx, floor, moves, font):
    bg = Image.open(EMPTY[room]).convert('RGBA').resize((320, 240), Image.LANCZOS)
    items = items_of(room)
    fr = creatures.frames_dir(cid, stage)
    meta = json.load(open(os.path.join(fr, 'frames.json')))
    anims = json.load(open(creatures.anims_path(cid, stage), encoding='utf-8'))
    frames = {n: Image.open(os.path.join(fr, 'png', n + '.png')).convert('RGBA') for n in meta['frames']}
    ax, ay = meta['anchor']
    split = ay - round(meta['canvas'][1] * 0.4)
    base_shadow = shadow(int(meta['canvas'][0] * 0.45))
    rnd = random.Random(5)
    title = f"{creatures.CREATURES[cid]['name']} ({creatures.STAGE_NAMES[stage]})"
    shots = []
    for move in moves:
        if move in ACROSS:
            lo, hi = turn_points(room, meta, frames, ACROSS[move][0])
            smp, label = across(anims, move, cx, lo, hi)
        else:
            anim = anims[move]
            smp = samples(anim)
            smp = smp * max(1, round(2200 / (len(smp) * STEP))) if anim['loop'] else smp + [smp[-1]] * 10
            smp = [t + (False,) for t in smp]
            label = LABELS.get(move, move)
        for f, x, y, br, shake, fl, left in smp:
            s = bg.copy()
            img = breathe(frames[f], round(br), split)
            if left:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            if fl:
                img = flash(img, 0.75)
            jx = rnd.randint(-shake, shake) if shake else 0
            jy = rnd.randint(-shake, shake) // 2 if shake else 0
            dx = meta['align'].get(f, [0, 0])[0]
            pet = dict(floor=floor, pet=True)
            for it in sorted(items + [pet], key=lambda d: d['floor']):
                if it.get('pet'):
                    lift = max(0.0, -y)
                    sh = base_shadow.resize((max(8, int(base_shadow.width * (1 - lift / 80))), base_shadow.height))
                    s.alpha_composite(sh, (cx + round(x) - sh.width // 2, floor - 7))
                    # the sprite's left edge is cx - ax + dx; mirrored, the anchor and the shift flip too
                    px = cx + round(x) + jx + (-(img.width - ax) - dx if left else -ax + dx)
                    s.alpha_composite(img, (px, floor - ay + round(y) + jy))
                else:
                    s.alpha_composite(it['img'], (it['x'], it['y']))
            s = s.resize((640, 480), Image.NEAREST)
            d = ImageDraw.Draw(s)
            d.rectangle([0, 0, 640, 30], fill=(0, 0, 0))
            d.text((10, 5), f"{title} · {label}", fill=(255, 230, 160), font=font)
            shots.append(s.convert('RGB'))
    name = f'{room}_{cid}-{stage}'
    shots[0].save(os.path.join(OUT, name + '.gif'), save_all=True, append_images=shots[1:], duration=STEP, loop=0)
    shots[len(shots) // 5].save(os.path.join(OUT, name + '.png'))
    print(f'{name}: {len(shots)} frames')


def main():
    os.makedirs(OUT, exist_ok=True)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 16)
    rooms = sys.argv[1:]                 # only these rooms when named
    for sc in SCENES:
        if not rooms or sc[0] in rooms:
            scene(*sc, font)


if __name__ == '__main__':
    main()
