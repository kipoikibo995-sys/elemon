"""Scenes drawn only from the packed R36S files in build/r36s/ (run r36s_pak.py first), the way SDL2
will draw them on the 640x480 screen: PNG atlases with alpha blending, white flash added while drawing.
Each is set against the same picture drawn from the sources.

Writes to preview/r36s/:
    canh-thu.mp4             every scene of SCENES whose pet is packed, one after another
    so-sanh_<room>.png       full colour | R36S, whole screen and the pet zoomed 2x
    17-phong.png             every packed room, full colour | R36S
    do-an.png                every food icon and bowl piece, full colour | R36S
Usage: python preview_r36s.py
"""
import json, os, random, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import r36s_pak as pak                  # sets HOLUA_SCREEN=640 before creatures is imported
import creatures
from preview_anims import STEP, LABELS, samples
from preview_decor_room import EMPTY, ACROSS, FLOOR_X, across

OUT = os.path.join(creatures.ROOT, 'preview', 'r36s')
# the PocketGo scenes at twice the size (feet x and y on the 640x480 screen)
SCENES = [
    ('L1-HO_hang-da', 'hoa-ho', 'adult4', 320, 330, ['idle', 'walk-across', 'run-across', 'attack', 'eat']),
    ('L1-HO_hang-da', 'hoa-ho', 'child', 320, 340, ['idle', 'walk-across', 'eat', 'happy']),
    ('L2-TH', 'thuy-sa', 'child', 330, 360, ['idle', 'walk-across', 'eat', 'happy']),
    ('L3-KI', 'kim-ung', 'teen', 330, 370, ['idle', 'walk-across', 'punch', 'happy']),
    ('L4-MO', 'moc-loc', 'legend', 320, 364, ['idle', 'punch', 'blast', 'victory']),
]


def read_index(path):
    """{'canvas', 'anchor', 'frames' | 'items' | 'sprites'} from a .txt index."""
    out = dict(frames={}, items=[], sprites={})
    for line in open(path, encoding='utf-8'):
        p = line.split()
        if not p or p[0].startswith('#'):
            continue
        if p[0] == 'canvas':
            out['canvas'], out['anchor'] = (int(p[1]), int(p[2])), (int(p[4]), int(p[5]))
        elif p[0] == 'frame':
            x, y, w, h, ox, oy, dx = map(int, p[2:9])
            out['frames'][p[1]] = dict(rect=(x, y, w, h), ox=ox, oy=oy, dx=dx)
        elif p[0] == 'item':
            x, y, w, h, sx, sy, floor = map(int, p[2:9])
            out['items'].append(dict(name=p[1], rect=(x, y, w, h), x=sx, y=sy, floor=floor))
        elif p[0] == 'sprite':
            out['sprites'][p[1]] = tuple(map(int, p[2:6]))
        elif p[0] == 'background':
            out['background'] = p[1]
    return out


def cut(atlas, rect):
    x, y, w, h = rect
    return atlas.crop((x, y, x + w, y + h))


def flash(img):
    """White flash as the device does it: the colour pushed 3/4 of the way to white, same alpha."""
    a = np.array(img).astype(np.int32)
    a[..., :3] += (255 - a[..., :3]) * 3 // 4
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def load_room(room):
    R = read_index(os.path.join(pak.ROOM_DIR, room + '_do.txt'))
    R['bg'] = Image.open(os.path.join(pak.ROOM_DIR, R['background'])).convert('RGBA')
    atlas = Image.open(os.path.join(pak.ROOM_DIR, room + '_do.png')).convert('RGBA')
    for it in R['items']:
        it['img'] = cut(atlas, it['rect'])
    return R


def load_pet(cid, stage):
    base = os.path.join(pak.PET_DIR, f'{cid}_{stage}')
    P = read_index(base + '.txt')
    atlas = Image.open(base + '.png').convert('RGBA')
    for f in P['frames'].values():
        f['img'] = cut(atlas, f['rect'])
        f['w'], f['h'] = f['img'].size
    return P


def pet_pos(P, f, cx, floor, x, y, jx, jy, left):
    """Top-left of a cropped frame, from the canvas anchor moved by align dx; mirrored when facing left."""
    (cw, _), (ax, ay) = P['canvas'], P['anchor']
    if left:
        sx = cx + round(x) + jx - (cw - ax) - f['dx'] + (cw - f['ox'] - f['w'])
    else:
        sx = cx + round(x) + jx - ax + f['dx'] + f['ox']
    return sx, floor - ay + round(y) + jy + f['oy']


def turn_points(room, P, base):
    left, right = (2 * v for v in FLOOR_X.get(room, (0, 320)))
    ax = P['anchor'][0]
    names = [n for n in P['frames'] if n.startswith(base + '-')] or list(P['frames'])
    reach = max(max(ax - f['dx'] - f['ox'], f['ox'] + f['w'] - ax + f['dx']) for f in (P['frames'][n] for n in names))
    lo, hi = left + reach, right - reach
    return (lo, hi) if lo <= hi else ((left + right) // 2,) * 2


def device_frame(R, P, f, cx, floor, x, y, jx, jy, fl, left):
    s = R['bg'].copy()
    fr = P['frames'][f]
    for it in sorted(R['items'] + [dict(floor=floor, pet=True)], key=lambda d: d['floor']):
        if it.get('pet'):
            img = fr['img'].transpose(Image.FLIP_LEFT_RIGHT) if left else fr['img']
            s.alpha_composite(flash(img) if fl else img, pet_pos(P, fr, cx, floor, x, y, jx, jy, left))
        else:
            s.alpha_composite(it['img'], (it['x'], it['y']))
    return s.convert('RGB')


def source_frame(room, cid, stage, f, cx, floor):
    """The same moment from the sources: 1448x1086 room and items shrunk once, the 640 frame PNG."""
    s = Image.open(EMPTY[room]).convert('RGBA').resize((640, 480), Image.LANCZOS)
    fr = creatures.frames_dir(cid, stage)
    meta = json.load(open(os.path.join(fr, 'frames.json')))
    img = Image.open(os.path.join(fr, 'png', f + '.png')).convert('RGBA')
    ax, ay = meta['anchor']
    dx = meta['align'].get(f, [0, 0])[0]
    items = pak.room_items(room)
    for it in sorted(items + [dict(floor=floor, pet=True)], key=lambda d: d['floor']):
        if it.get('pet'):
            s.alpha_composite(img, (cx - ax + dx, floor - ay))
        else:
            s.alpha_composite(it['img'], (it['x'], it['y']))
    return s.convert('RGB')


def bar(img, text, font):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, img.width, 28], fill=(0, 0, 0))
    d.text((10, 4), text, fill=(255, 230, 160), font=font)
    return img


def pair(a, b, font, left='Bản gốc', right='R36S', scale=1):
    A = bar(a.resize((a.width * scale, a.height * scale), Image.NEAREST), left, font)
    B = bar(b.resize((b.width * scale, b.height * scale), Image.NEAREST), right, font)
    out = Image.new('RGB', (A.width * 2 + 10, A.height), (40, 40, 40))
    out.paste(A, (0, 0)); out.paste(B, (A.width + 10, 0))
    return out


def scenes(font, report):
    tmp = tempfile.mkdtemp()
    n = 0
    rnd = random.Random(5)
    done_rooms = set()
    for room, cid, stage, cx, floor, moves in SCENES:
        if room in done_rooms:
            continue
        try:
            R, P = load_room(room), load_pet(cid, stage)
        except OSError:
            print(f'bỏ qua cảnh {room} + {cid}/{stage}: chưa đóng gói')
            continue
        done_rooms.add(room)
        anims = json.load(open(creatures.anims_path(cid, stage), encoding='utf-8'))
        title = f"{creatures.CREATURES[cid]['name']} ({creatures.STAGE_NAMES[stage]}) · {room} · R36S"
        still = None
        k = creatures.SIZE              # anims.json is in 320 units, shared with the PocketGo set
        for move in moves:
            if move in ACROSS:
                if ACROSS[move][0] not in anims:
                    continue
                lo, hi = turn_points(room, P, ACROSS[move][0])
                smp, label = across(anims, move, cx / k, lo / k, hi / k)
            else:
                if move not in anims:
                    continue
                a = anims[move]
                smp = samples(a)
                smp = smp * max(1, round(2200 / (len(smp) * STEP))) if a['loop'] else smp + [smp[-1]] * 10
                smp = [t + (False,) for t in smp]
                label = LABELS.get(move, move)
            smp = [(f, x * k, y * k, br * k, round(shake * k), fl, left) for f, x, y, br, shake, fl, left in smp]
            for f, x, y, br, shake, fl, left in smp:
                jx = rnd.randint(-shake, shake) if shake else 0
                jy = rnd.randint(-shake, shake) // 2 if shake else 0
                img = device_frame(R, P, f, cx, floor, x, y, jx, jy, fl, left)
                if still is None:
                    still = (f, device_frame(R, P, f, cx, floor, 0, 0, 0, 0, False, False))
                bar(img, f'{title} · {label}', font).save(os.path.join(tmp, f'{n:05d}.png'))
                n += 1
        f, dev = still
        src = source_frame(room, cid, stage, f, cx, floor)
        top = pair(src, dev, font)
        fr = P['frames'][f]
        sx, sy = pet_pos(P, fr, cx, floor, 0, 0, 0, 0, False)
        box = (max(0, sx - 12), max(0, sy - 12), min(640, sx + fr['w'] + 12), min(480, sy + fr['h'] + 12))
        zoom = pair(src.crop(box), dev.crop(box), font, 'Bản gốc ×2', 'R36S ×2', 2)
        sheet = Image.new('RGB', (max(top.width, zoom.width), top.height + zoom.height + 10), (40, 40, 40))
        sheet.paste(top, (0, 0)); sheet.paste(zoom, (0, top.height + 10))
        sheet.save(os.path.join(OUT, f'so-sanh_{room}.png'))
        report[f'{room} + {cid}/{stage}'] = dict(
            room_kb=report_kb(os.path.join(pak.ROOM_DIR, room + '.png'), os.path.join(pak.ROOM_DIR, room + '_do.png')),
            pet_kb=report_kb(os.path.join(pak.PET_DIR, f'{cid}_{stage}.png')),
            ram_mb=round((640 * 480 * 4 * 2 + sum(i['img'].width * i['img'].height * 4 for i in R['items'])
                          + Image.open(os.path.join(pak.PET_DIR, f'{cid}_{stage}.png')).size[0]
                          * Image.open(os.path.join(pak.PET_DIR, f'{cid}_{stage}.png')).size[1] * 4) / 2 ** 20, 1))
    if n:
        video = os.path.join(OUT, 'canh-thu.mp4')
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-framerate', str(round(1000 / STEP)),
                        '-i', os.path.join(tmp, '%05d.png'), '-vf', 'format=yuv420p', '-c:v', 'libx264',
                        '-crf', '18', '-movflags', '+faststart', video], check=True)
        print(f'{video}: {n} khung')


def report_kb(*paths):
    return round(sum(os.path.getsize(p) for p in paths) / 1024)


def rooms_sheet(font):
    rows = []
    for room in EMPTY:
        try:
            R = load_room(room)
        except OSError:
            continue
        dev = R['bg'].copy()
        for it in sorted(R['items'], key=lambda d: d['floor']):
            dev.alpha_composite(it['img'], (it['x'], it['y']))
        src = Image.open(EMPTY[room]).convert('RGBA').resize((640, 480), Image.LANCZOS)
        for it in sorted(pak.room_items(room), key=lambda d: d['floor']):
            src.alpha_composite(it['img'], (it['x'], it['y']))
        rows.append(pair(src.convert('RGB'), dev.convert('RGB'), font, f'{room} · gốc', 'R36S'))
    if rows:
        w, h = rows[0].size
        sheet = Image.new('RGB', (w, (h + 10) * len(rows)), (20, 20, 20))
        for i, r in enumerate(rows):
            sheet.paste(r, (0, i * (h + 10)))
        sheet.resize((w // 2, sheet.height // 2), Image.LANCZOS).save(os.path.join(OUT, '17-phong.png'))


def food_sheet(font):
    F = read_index(os.path.join(pak.OUT, 'do-an.txt'))
    atlas = Image.open(os.path.join(pak.OUT, 'do-an.png')).convert('RGBA')
    names = sorted(k[5:] for k in F['sprites'] if k.startswith('icon/'))
    cell, cols = 104, 8
    sheet = Image.new('RGBA', (cols * cell * 2 + 30, (len(names) + cols - 1) // cols * cell + 40), (60, 52, 44, 255))
    bar(sheet, 'Đồ ăn: trái = gốc, phải = R36S · icon 64px và miếng trong bát 28px', font)
    for i, name in enumerate(names):
        src = Image.open(os.path.join(pak.FOOD, name + '.png')).convert('RGBA')
        for half in (0, 1):
            ox, oy = (i % cols) * cell + half * (cols * cell + 30), 40 + (i // cols) * cell
            for kind, box, (dx, dy) in (('icon', pak.FOOD_ICON, (0, 0)), ('bat', pak.FOOD_BOWL, (70, 60))):
                im = pak.fit(src, box) if half == 0 else cut(atlas, F['sprites'][f'{kind}/{name}'])
                sheet.alpha_composite(im, (ox + dx, oy + dy))
    sheet.convert('RGB').save(os.path.join(OUT, 'do-an.png'))


def main():
    os.makedirs(OUT, exist_ok=True)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 16)
    report = {}
    scenes(font, report)
    rooms_sheet(font)
    food_sheet(font)
    with open(os.path.join(OUT, 'dung-luong.json'), 'w', encoding='utf-8') as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
