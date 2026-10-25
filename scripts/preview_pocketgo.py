"""Scenes drawn only from the packed PocketGo files in build/pak/ (run pocketgo_pak.py first), the way
the device will draw them: 320x240 RGB565 screen, palette sprites, no alpha, white flash and night
computed while drawing. Each is set against the same picture drawn in full colour from the sources.

Writes to preview/pocketgo/:
    canh-thu.mp4             every scene in SCENES, one after another (2x size)
    so-sanh_<room>.png       full colour | PocketGo, whole screen and the pet zoomed 3x
    17-phong.png             every packed room, full colour | PocketGo
    do-an.png                every food icon and bowl piece, full colour | PocketGo
    dem.png                  one room by day and by night (night tint from danh-sach.json)
    dung-luong.json          size and RAM of each scene
Usage: python preview_pocketgo.py
"""
import json, os, random, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import creatures
import pocketgo_pak as pak
from preview_anims import STEP, LABELS, samples
from preview_decor_room import EMPTY, ACROSS, FLOOR_X, across, items_of

OUT = os.path.join(creatures.ROOT, 'preview', 'pocketgo')
# (room, creature, stage, feet x and y on the screen, moves): one room of each level.
# Walking stays inside the room's FLOOR_X (preview_decor_room.py), add the floor edges of a new room there.
SCENES = [
    ('L1-HO_hang-da', 'hoa-ho', 'adult4', 160, 165, ['idle', 'walk-across', 'run-across', 'attack', 'eat']),
    ('L2-TH', 'thuy-sa', 'child', 165, 180, ['idle', 'walk-across', 'eat', 'happy']),
    ('L3-KI', 'kim-ung', 'teen', 165, 185, ['idle', 'walk-across', 'punch', 'happy']),
    ('L4-MO', 'moc-loc', 'legend', 160, 182, ['idle', 'punch', 'blast', 'victory']),
]
NIGHT_ROOM = 'L3-HO'


def to565(rgb):
    """What the 16-bit screen actually shows."""
    a = rgb.astype(np.int32)
    return np.stack([(a[..., 0] >> 3) * 255 // 31, (a[..., 1] >> 2) * 255 // 63, (a[..., 2] >> 3) * 255 // 31], -1).astype(np.uint8)


def blit(screen, idx, lut, x, y, flip=False):
    """Palette sprite onto the screen; index 0 is see-through."""
    if flip:
        idx = idx[:, ::-1]
    h, w = idx.shape
    x0, y0, x1, y1 = max(0, x), max(0, y), min(320, x + w), min(240, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    part = idx[y0 - y:y1 - y, x0 - x:x1 - x]
    m = part > 0
    screen[y0:y1, x0:x1][m] = lut[part[m]]


def lut_of(palette):
    return np.array([(0, 0, 0)] + palette[1:], np.uint8)


def night(rgb, tint):
    """The night tint of pocketgo_pak.NIGHT: darker and bluer, lights keep their colour."""
    a = rgb.astype(np.float64)
    dark = np.stack([a[..., i] * tint[c][0] + tint[c][1] for i, c in enumerate('rgb')], -1)
    lo, span, sat, sat_span = tint['glow']
    hi = a.max(-1)
    keep = np.clip((hi - lo) / span, 0, 1) * np.clip((hi - a.min(-1) - sat) / sat_span, 0, 1)
    return np.clip(dark + (a - dark) * keep[..., None], 0, 255).astype(np.uint8)


def load(name):
    with open(os.path.join(pak.PAK_DIR, name), 'rb') as fh:
        return fh.read()


def room_screen(R):
    """Background and items drawn back to front, as (screen, items sorted for drawing)."""
    return R['background'].copy(), sorted(R['items'], key=lambda d: d['floor'])


def pet_pos(P, fr, cx, floor, x, y, jx, jy, left):
    """Top-left of a cropped frame on the screen, from the canvas anchor, moved by the frame's align
    dx (as src/main.c does); mirrored when facing left, the align shift too."""
    ax, ay = P['anchor']
    cw = P['canvas'][0]
    if left:
        sx = cx + round(x) + jx - (cw - ax) - fr['dx'] + (cw - fr['x'] - fr['idx'].shape[1])
    else:
        sx = cx + round(x) + jx - ax + fr['dx'] + fr['x']
    return sx, floor - ay + round(y) + jy + fr['y']


def turn_points(room, P, base):
    """Left and right turn points for the feet so the whole body stays on the room's floor (same idea
    as preview_decor_room.turn_points, measured on the packed frames)."""
    left, right = FLOOR_X.get(room, (0, 320))
    ax = P['anchor'][0]
    names = [n for n in P['frames'] if n.startswith(base + '-')] or list(P['frames'])
    reach = 0
    for n in names:
        fr = P['frames'][n]
        # body left and right of the feet, facing right; facing left swaps the two
        reach = max(reach, ax - fr['dx'] - fr['x'], fr['x'] + fr['idx'].shape[1] - ax + fr['dx'])
    lo, hi = left + reach, right - reach
    if lo > hi:                      # too long for this floor: pace on the spot
        lo = hi = (left + right) // 2
    return lo, hi


def device_frame(R, P, luts, f, cx, floor, x, y, jx, jy, fl, left):
    screen, items = room_screen(R)
    fr = P['frames'][f]
    room_lut, pet_lut, flash_lut = luts
    pet = dict(floor=floor, pet=True)
    for it in sorted(items + [pet], key=lambda d: d['floor']):
        if it.get('pet'):
            sx, sy = pet_pos(P, fr, cx, floor, x, y, jx, jy, left)
            blit(screen, fr['idx'], flash_lut if fl else pet_lut, sx, sy, left)
        else:
            blit(screen, it['idx'], room_lut, it['x'], it['y'])
    return to565(screen)


def source_frame(room, cid, stage, f, cx, floor):
    """The same moment in full colour, straight from the sources (soft edges, all colours)."""
    s = Image.open(EMPTY[room]).convert('RGBA').resize((320, 240), Image.LANCZOS)
    fr = creatures.frames_dir(cid, stage)
    meta = json.load(open(os.path.join(fr, 'frames.json')))
    img = Image.open(os.path.join(fr, 'png', f + '.png')).convert('RGBA')
    ax, ay = meta['anchor']
    dx = meta['align'].get(f, [0, 0])[0]
    for it in sorted(items_of(room) + [dict(floor=floor, pet=True)], key=lambda d: d['floor']):
        if it.get('pet'):
            s.alpha_composite(img, (cx - ax + dx, floor - ay))
        else:
            s.alpha_composite(it['img'], (it['x'], it['y']))
    return np.array(s.convert('RGB'))


def bar(img, text, font, w=None):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w or img.width, 30], fill=(0, 0, 0))
    d.text((10, 5), text, fill=(255, 230, 160), font=font)
    return img


def pair(a, b, font, left='Bản gốc', right='PocketGo', scale=2):
    """Two equal pictures side by side, each scaled up with hard pixels and labelled."""
    A = bar(Image.fromarray(a).resize((a.shape[1] * scale, a.shape[0] * scale), Image.NEAREST), left, font)
    B = bar(Image.fromarray(b).resize((b.shape[1] * scale, b.shape[0] * scale), Image.NEAREST), right, font)
    out = Image.new('RGB', (A.width * 2 + 10, A.height), (40, 40, 40))
    out.paste(A, (0, 0)); out.paste(B, (A.width + 10, 0))
    return out


def scenes(font, report):
    tmp = tempfile.mkdtemp()
    n = 0
    rnd = random.Random(5)
    for room, cid, stage, cx, floor, moves in SCENES:
        try:
            room_bytes, pet_bytes = load(f'phong/{room}.pak'), load(f'pet/{cid}_{stage}.pak')
        except OSError as e:
            print(f'bỏ qua cảnh {room}: {e}')
            continue
        # ---- the device side: everything here reads only the two paks ----
        R, P = pak.read_room(room_bytes), pak.read_creature(pet_bytes)
        pet_lut = lut_of(P['palette'])
        flash_lut = (pet_lut.astype(np.int32) + (255 - pet_lut.astype(np.int32)) * 3 // 4).astype(np.uint8)
        luts = (lut_of(R['palette']), pet_lut, flash_lut)
        anims = json.load(open(creatures.anims_path(cid, stage), encoding='utf-8'))
        title = f"{creatures.CREATURES[cid]['name']} ({creatures.STAGE_NAMES[stage]}) · {room} · PocketGo"
        still = None
        for move in moves:
            if move in ACROSS:
                if ACROSS[move][0] not in anims:
                    continue
                smp, label = across(anims, move, cx, *turn_points(room, P, ACROSS[move][0]))
            else:
                if move not in anims:
                    continue
                a = anims[move]
                smp = samples(a)
                smp = smp * max(1, round(2200 / (len(smp) * STEP))) if a['loop'] else smp + [smp[-1]] * 10
                smp = [t + (False,) for t in smp]
                label = LABELS.get(move, move)
            for f, x, y, br, shake, fl, left in smp:
                jx = rnd.randint(-shake, shake) if shake else 0
                jy = rnd.randint(-shake, shake) // 2 if shake else 0
                screen = device_frame(R, P, luts, f, cx, floor, x, y, jx, jy, fl, left)
                if still is None:
                    still = (f, device_frame(R, P, luts, f, cx, floor, 0, 0, 0, 0, False, False))
                img = Image.fromarray(screen).resize((640, 480), Image.NEAREST)
                bar(img, f'{title} · {label}', font).save(os.path.join(tmp, f'{n:05d}.png'))
                n += 1
        # ---- side by side with the full-colour picture at the same moment ----
        f, dev = still
        src = source_frame(room, cid, stage, f, cx, floor)
        top = pair(src, dev, font)
        fr = P['frames'][f]
        sx, sy = pet_pos(P, fr, cx, floor, 0, 0, 0, 0, False)
        h, w = fr['idx'].shape
        box = (max(0, sx - 8), max(0, sy - 8), min(320, sx + w + 8), min(240, sy + h + 8))
        zoom = pair(src[box[1]:box[3], box[0]:box[2]], dev[box[1]:box[3], box[0]:box[2]], font,
                    'Bản gốc ×3', 'PocketGo ×3', 3)
        sheet = Image.new('RGB', (max(top.width, zoom.width), top.height + zoom.height + 10), (40, 40, 40))
        sheet.paste(top, (0, 0)); sheet.paste(zoom, (0, top.height + 10))
        sheet.save(os.path.join(OUT, f'so-sanh_{room}.png'))
        report[f'{room} + {cid}/{stage}'] = dict(
            room_pak_kb=round(len(room_bytes) / 1024), pet_pak_kb=round(len(pet_bytes) / 1024),
            ram_kb=round((len(room_bytes) + len(pet_bytes) + 320 * 240 * 2) / 1024))
    video = os.path.join(OUT, 'canh-thu.mp4')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-framerate', str(round(1000 / STEP)),
                    '-i', os.path.join(tmp, '%05d.png'), '-vf', 'format=yuv420p', '-c:v', 'libx264',
                    '-crf', '18', '-movflags', '+faststart', video], check=True)
    print(f'{video}: {n} khung')


def rooms_sheet(font):
    """Every packed room without a pet: full colour | PocketGo, two rooms a row."""
    rows = []
    for room in EMPTY:
        try:
            R = pak.read_room(load(f'phong/{room}.pak'))
        except OSError:
            continue
        screen, items = room_screen(R)
        lut = lut_of(R['palette'])
        for it in items:
            blit(screen, it['idx'], lut, it['x'], it['y'])
        s = Image.open(EMPTY[room]).convert('RGBA').resize((320, 240), Image.LANCZOS)
        for it in sorted(items_of(room), key=lambda d: d['floor']):
            s.alpha_composite(it['img'], (it['x'], it['y']))
        rows.append(pair(np.array(s.convert('RGB')), to565(screen), font, f'{room} · gốc', 'PocketGo'))
    if not rows:
        return
    w, h = rows[0].size
    sheet = Image.new('RGB', (w * 2 + 20, (h + 10) * ((len(rows) + 1) // 2)), (20, 20, 20))
    for i, r in enumerate(rows):
        sheet.paste(r, ((i % 2) * (w + 20), (i // 2) * (h + 10)))
    sheet.save(os.path.join(OUT, '17-phong.png'))


def food_sheet(font):
    F = pak.read_food(load('do-an.pak'))
    lut = lut_of(F['palette'])
    names = sorted(n[5:] for n in F['sprites'] if n.startswith('icon/'))
    cell, cols = 80, 8
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cell * 2 + 30, rows * cell + 40), (60, 52, 44))
    bar(sheet, 'Đồ ăn: trái = gốc (thu nhỏ có viền mờ), phải = PocketGo · icon 32px và miếng trong bát 14px, phóng ×2', font)
    for i, name in enumerate(names):
        src = Image.open(os.path.join(pak.FOOD, name + '.png')).convert('RGBA')
        for half in (0, 1):
            ox = (i % cols) * cell + half * (cols * cell + 30)
            oy = 40 + (i // cols) * cell
            for k, (kind, box) in enumerate((('icon', pak.FOOD_ICON), ('bat', pak.FOOD_BOWL))):
                if half == 0:
                    im = pak.fit(src, box)
                    tile = Image.new('RGBA', im.size, (60, 52, 44, 255))
                    tile.alpha_composite(im)
                    tile = tile.convert('RGB')
                else:
                    idx = F['sprites'][f'{kind}/{name}']
                    tile = np.full(idx.shape + (3,), (60, 52, 44), np.uint8)
                    m = idx > 0
                    tile[m] = lut[idx[m]]
                    tile = Image.fromarray(to565(tile))
                tile = tile.resize((tile.width * 2, tile.height * 2), Image.NEAREST)
                sheet.paste(tile, (ox + (0 if k == 0 else 66), oy + (0 if k == 0 else 40)))
    sheet.save(os.path.join(OUT, 'do-an.png'))


def night_sheet(font):
    try:
        R = pak.read_room(load(f'phong/{NIGHT_ROOM}.pak'))
        tint = json.load(open(os.path.join(pak.PAK_DIR, 'danh-sach.json'), encoding='utf-8'))['night']
    except (OSError, KeyError):
        return
    day, items = room_screen(R)
    lut = lut_of(R['palette'])
    for it in items:
        blit(day, it['idx'], lut, it['x'], it['y'])
    # on the device: the background once at room load, the palettes as 255 entries
    dark, _ = room_screen(R)
    dark = night(dark, tint)
    nlut = night(lut, tint)
    for it in items:
        blit(dark, it['idx'], nlut, it['x'], it['y'])
    pair(to565(day), to565(dark), font, f'{NIGHT_ROOM} · ngày', 'đêm (tô màu lúc vẽ, không lưu ảnh riêng)').save(
        os.path.join(OUT, 'dem.png'))


def main():
    os.makedirs(OUT, exist_ok=True)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 16)
    report = {}
    scenes(font, report)
    rooms_sheet(font)
    food_sheet(font)
    night_sheet(font)
    with open(os.path.join(OUT, 'dung-luong.json'), 'w', encoding='utf-8') as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
