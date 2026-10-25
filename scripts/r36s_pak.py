"""Packs the R36S / H700 set (640x480 screen, SDL2 with alpha blending) into build/r36s/: PNG atlases the
game loads straight into GPU textures (IMG_Load + SDL_CreateTextureFromSurface), with a text index each.
Everything is already at screen size and keeps its soft edges; nothing is scaled on the device.

Output (build/r36s/):
    pet/<creature>_<stage>.png + .txt   all frames of one creature at one stage, cropped, in one atlas
                                        (from assets/creatures-640/, cut by HOLUA_SCREEN=640 slice_frames.py)
    phong/<room>.png                    the empty room, 640x480, opaque
    phong/<room>_do.png + .txt          its decor items in one atlas, with their place on the screen
    do-an.png + .txt                    every food: menu icon (fits 64x64) and piece in the bowl (fits 28x28)
    danh-sach.json                      what was packed, sizes, and the night tint (as pocketgo_pak.NIGHT)
Only pets that changed are packed again; rooms and food always (they are quick). Anything not ready is
reported and skipped, its old files kept.

Index files (.txt), one thing per line, numbers in pixels, '#' starts a comment:
    canvas W H anchor AX AY                pets: the canvas every frame is placed on, feet at AX, AY
    frame NAME X Y W H OX OY DX            pets: atlas rect, place on the canvas, align shift (as frames.json)
    background FILE                        rooms: the opaque 640x480 picture
    item NAME X Y W H SX SY FLOOR          rooms: atlas rect, top-left on the screen, floor line for draw
                                           order (-1 = lies flat under everything)
    sprite NAME X Y W H                    food: atlas rect; NAME is icon/<file> or bat/<file>
White flash and night are colour changes while drawing (additive blend / tint once at room load), as on
the PocketGo; no extra pictures are stored.

Pet and decor atlases are 8-bit PNG with alpha per colour (see PALETTE), food and backgrounds full
colour; SDL_image loads both kinds the same way.

Usage: python r36s_pak.py [creature / element / stage names]   (rooms and food only when nothing is named)
       --all   pack the pets again even if up to date
       --rgba  keep every atlas full colour (about 4 times bigger)
"""
import glob, json, os, sys
import numpy as np
from PIL import Image

os.environ['HOLUA_SCREEN'] = '640'      # before creatures is imported: frames from assets/creatures-640/
import creatures
from pocketgo_pak import NIGHT

ROOT = creatures.ROOT
OUT = os.path.join(ROOT, 'build', 'r36s')
PET_DIR = os.path.join(OUT, 'pet')
ROOM_DIR = os.path.join(OUT, 'phong')
FOOD = os.path.join(ROOT, 'assets', 'source', 'do-an')
W, H = 640, 480
FOOD_ICON, FOOD_BOWL = 64, 28
ATLAS_W = 2048                         # the R36S GPU (Mali-G31) takes textures up to 4096
CLEAR = 4                              # alpha below this is dropped (stray specks from shrinking)
# Pet and decor atlases are saved as 8-bit PNG (256 colours, each with its own alpha, so soft edges
# stay): about a quarter of the size, no visible change at screen size. An atlas whose colours drift
# too far (mean of the worst channel over visible pixels) stays full colour. --rgba: all full colour.
PALETTE = '--rgba' not in sys.argv
MAX_ERR = 16
SETTINGS = dict(version=2, clear=CLEAR, atlas=ATLAS_W, palette=PALETTE, max_err=MAX_ERR)
QUALITY = {}                           # atlas file -> (format, mean error), for the inventory


def clean(im):
    """RGBA with see-through pixels set to 0,0,0,0 (smaller PNG, no colour bleeding when filtered)."""
    a = np.array(im.convert('RGBA'))
    a[a[..., 3] < CLEAR] = 0
    return Image.fromarray(a, 'RGBA')


def crop(im):
    box = im.getchannel('A').getbbox() or (0, 0, 1, 1)
    return im.crop(box), box


def pack_atlas(images):
    """Shelf packing, tallest first: {key: (x, y)} and the atlas size. 1 px gap so filtering never
    picks up a neighbour."""
    order = sorted(images, key=lambda k: -images[k].height)
    place, x, y, row = {}, 0, 0, 0
    for k in order:
        w, h = images[k].size
        if x + w > ATLAS_W:
            x, y, row = 0, y + row + 1, 0
        place[k] = (x, y)
        x += w + 1
        row = max(row, h)
    width = min(ATLAS_W, max(place[k][0] + images[k].width for k in place))
    return place, (width, y + row)


def to_palette(atlas):
    """8-bit version of an RGBA atlas and its mean error, or (None, error) when it drifts too far."""
    q = atlas.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    a, b = np.array(atlas).astype(np.int16), np.array(q.convert('RGBA')).astype(np.int16)
    seen = a[..., 3] > 0
    err = float(np.abs(a[..., :3] - b[..., :3]).max(-1)[seen].mean()) if seen.any() else 0.0
    return (q if err <= MAX_ERR else None), err


def save_atlas(path, images, palette=False):
    place, size = pack_atlas(images)
    atlas = Image.new('RGBA', size, (0, 0, 0, 0))
    for k, im in images.items():
        atlas.paste(im, place[k])
    q, err = to_palette(atlas) if palette and PALETTE else (None, 0.0)
    tmp = path + '.tmp.png'
    (q or atlas).save(tmp, optimize=True)
    os.replace(tmp, path)
    QUALITY[os.path.relpath(path, OUT).replace(os.sep, '/')] = ('8-bit' if q else 'RGBA', round(err, 1))
    return place


def write_index(path, lines):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')
    os.replace(tmp, path)


def pack_pet(cid, stage, base):
    fr = creatures.frames_dir(cid, stage)
    meta = json.load(open(os.path.join(fr, 'frames.json')))
    images, boxes = {}, {}
    for n in meta['frames']:
        images[n], boxes[n] = crop(clean(Image.open(os.path.join(fr, 'png', n + '.png'))))
    place = save_atlas(base + '.png', images, palette=True)
    lines = [f'# {creatures.CREATURES[cid]["name"]} ({creatures.STAGE_NAMES[stage]}), atlas {cid}_{stage}.png',
             'canvas {} {} anchor {} {}'.format(*meta['canvas'], *meta['anchor'])]
    for n in meta['frames']:
        x, y = place[n]
        bx, by, bx1, by1 = boxes[n]
        lines.append(f"frame {n} {x} {y} {bx1 - bx} {by1 - by} {bx} {by} {meta['align'].get(n, [0, 0])[0]}")
    write_index(base + '.txt', lines)


def room_items(room):
    """Decor of a room at 640 size and place: the same vi-tri.json as the PocketGo set
    (preview_decor_room.items_of, at twice the screen)."""
    from preview_decor_room import DECOR, MANUAL, ROOM_W, flat
    k = W / ROOM_W
    pos = json.load(open(os.path.join(DECOR, room, 'vi-tri.json'), encoding='utf-8'))
    pos.update(MANUAL.get(room, {}))
    out = []
    for name, (x, y, s) in pos.items():
        path = os.path.join(DECOR, room, name)
        if not os.path.exists(path):
            print(f'  {room}: thiếu {name}, bỏ qua')
            continue
        img = Image.open(path).convert('RGBA')
        w, h = max(1, round(img.width * s * k)), max(1, round(img.height * s * k))
        img, box = crop(clean(img.resize((w, h), Image.LANCZOS)))
        sx, sy = round(x * k) + box[0], round(y * k) + box[1]
        out.append(dict(name=os.path.splitext(name)[0], img=img, x=sx, y=sy,
                        floor=-1 if flat(name) else round(y * k) + h))
    return out


def pack_room(room, empty):
    bg = Image.open(empty).convert('RGB').resize((W, H), Image.LANCZOS)
    tmp = os.path.join(ROOM_DIR, room + '.tmp.png')
    bg.save(tmp, optimize=True)
    os.replace(tmp, os.path.join(ROOM_DIR, room + '.png'))
    items = room_items(room)
    place = save_atlas(os.path.join(ROOM_DIR, room + '_do.png'), {it['name']: it['img'] for it in items}, palette=True)
    lines = [f'# {room}: background, then decor (atlas {room}_do.png) in the order of the file',
             f'background {room}.png']
    for it in items:
        x, y = place[it['name']]
        lines.append(f"item {it['name']} {x} {y} {it['img'].width} {it['img'].height} {it['x']} {it['y']} {it['floor']}")
    write_index(os.path.join(ROOM_DIR, room + '_do.txt'), lines)
    return len(items)


def fit(im, box):
    im, _ = crop(clean(im))
    s = box / max(im.size)
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)


def size_kb(*paths):
    return round(sum(os.path.getsize(p) for p in paths) / 1024, 1)


# ---------------------------------------------------------------- build

def fresh(outs, inputs, force):
    if force or not all(os.path.exists(o) for o in outs):
        return False
    return min(os.path.getmtime(o) for o in outs) >= max(os.path.getmtime(p) for p in inputs if os.path.exists(p))


def pets(units, force, report):
    for cid, stage in units:
        fr = creatures.frames_dir(cid, stage)
        base = os.path.join(PET_DIR, f'{cid}_{stage}')
        outs = [base + '.png', base + '.txt']
        if not os.path.exists(os.path.join(fr, 'frames.json')):
            continue                    # not cut at 640 yet (counted in the summary)
        inputs = [os.path.join(fr, 'frames.json')] + glob.glob(os.path.join(fr, 'png', '*.png'))
        try:
            if not fresh(outs, inputs, force):
                pack_pet(cid, stage, base)
                print(f'  pet/{cid}_{stage}: {size_kb(*outs):.0f} KB')
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
            print(f'  bỏ qua {cid}/{stage}: {e}')
            continue
        nfr = sum(1 for line in open(base + '.txt', encoding='utf-8') if line.startswith('frame '))
        key = f'pet/{cid}_{stage}'
        fmt, err = QUALITY.get(key + '.png') or (report.get(key, {}).get('format'), report.get(key, {}).get('err'))
        report[key] = dict(kb=size_kb(*outs), frames=nfr, element=creatures.CREATURES[cid]['element'],
                           creature=cid, stage=stage, format=fmt, err=err)


def rooms(report):
    import place_decor
    from preview_decor_room import EMPTY, DECOR
    for room in place_decor.ROOM_CODE:
        folder = os.path.join(DECOR, room)
        if room not in EMPTY or not glob.glob(os.path.join(folder, '*.png')):
            print(f'  bỏ qua phòng {room}: chưa có nền trống hoặc chưa có đồ')
            continue
        try:
            if not os.path.exists(os.path.join(folder, 'vi-tri.json')):
                print(f'  {room}: chưa có vi-tri.json, đặt đồ mặc định (place_decor.py)')
                place_decor.main([room])
            n = pack_room(room, EMPTY[room])
        except (OSError, ValueError, KeyError, IndexError, json.JSONDecodeError) as e:
            print(f'  bỏ qua phòng {room}: {e}')
            continue
        files = [os.path.join(ROOM_DIR, room + s) for s in ('.png', '_do.png', '_do.txt')]
        fmt, err = QUALITY[f'phong/{room}_do.png']
        report[f'phong/{room}'] = dict(kb=size_kb(*files), background_kb=size_kb(files[0]), items=n, format=fmt, err=err)
        print(f'  phong/{room}: {report[f"phong/{room}"]["kb"]:.0f} KB')


def food(report):
    sprites = {}
    for p in sorted(glob.glob(os.path.join(FOOD, '*.png'))):
        stem = os.path.splitext(os.path.basename(p))[0]
        if stem.startswith('_'):
            continue
        try:
            im = Image.open(p).convert('RGBA')
        except OSError as e:
            print(f'  bỏ qua món {stem}: {e}')
            continue
        sprites['icon/' + stem], sprites['bat/' + stem] = fit(im, FOOD_ICON), fit(im, FOOD_BOWL)
    if not sprites:
        return
    place = save_atlas(os.path.join(OUT, 'do-an.png'), sprites)
    write_index(os.path.join(OUT, 'do-an.txt'), ['# food: icon/<file> fits 64x64 (menu), bat/<file> fits 28x28 (bowl)'] +
                [f'sprite {k} {place[k][0]} {place[k][1]} {im.width} {im.height}' for k, im in sorted(sprites.items())])
    report['do-an'] = dict(kb=size_kb(os.path.join(OUT, 'do-an.png'), os.path.join(OUT, 'do-an.txt')),
                           foods=len(sprites) // 2)
    print(f"  do-an: {report['do-an']['kb']:.0f} KB")


INVENTORY = os.path.join(ROOT, 'assets', 'KIEM-KE-R36S.md')


def write_inventory(report, missing):
    pets_ = [v for k, v in report.items() if k.startswith('pet/')]
    rooms_ = {k[6:]: v for k, v in report.items() if k.startswith('phong/')}
    total = sum(v['kb'] for v in report.values())
    L = ['# Kiểm kê bộ hình R36S (`build/r36s/`)', '',
         'Tự ghi lại mỗi lần chạy `python scripts/r36s_pak.py` (hoặc `HOLUA_SCREEN=640 python scripts/build_assets.py`). '
         'Định dạng: đầu `scripts/r36s_pak.py`. Màn 640×480, PNG có viền mịn (trộn trong suốt bằng GPU). '
         'Chỉ chép `build/r36s/` vào gói PortMaster.', '',
         f'**Tổng: {total / 1024:.1f} MB trong {len(report)} bộ.**' +
         (f' Còn {missing} bộ pet chưa cắt cỡ 640 (`assets/creatures-640/`), chưa có trong bảng.' if missing else ''), '',
         '| Nhóm | Số bộ | Dung lượng | Nhỏ nhất – lớn nhất |', '| --- | ---: | ---: | ---: |']

    def row(name, vals):
        kb = [v['kb'] for v in vals]
        if kb:
            L.append(f'| {name} | {len(kb)} | {sum(kb) / 1024:.2f} MB | {min(kb):.0f} – {max(kb):.0f} KB |')
    row('Pet', pets_)
    row('Phòng (nền + đồ)', list(rooms_.values()))
    row('Đồ ăn', [v for k, v in report.items() if k == 'do-an'])
    atl = {k: v for k, v in report.items() if k.startswith(('pet/', 'phong/'))}
    n8 = {k: v for k, v in atl.items() if v.get('format') == '8-bit'}
    if n8:
        worst = max(n8, key=lambda k: n8[k]['err'])
        L += ['', f'Atlas pet và đồ phòng lưu PNG 8-bit (256 màu, mỗi màu có độ trong riêng nên vẫn giữ viền mịn): '
              f'{len(n8)}/{len(atl)} atlas, sai màu trung bình (kênh lệch nhất) '
              f'{sum(v["err"] for v in n8.values()) / len(n8):.1f}, lớn nhất {n8[worst]["err"]:.1f} (`{worst}`). '
              f'Atlas nào sai quá {MAX_ERR} giữ đủ màu. Nền phòng và đồ ăn luôn đủ màu. '
              'Chạy `r36s_pak.py --rgba --all` để giữ mọi atlas đủ màu (to gấp khoảng 4 lần).']
    if pets_:
        L += ['', '## Pet theo cấp', '', '| Cấp | Số bộ | Dung lượng | Trung bình | Lớn nhất |',
              '| --- | ---: | ---: | ---: | ---: |']
        for st in creatures.STAGES:
            vals = [v for v in pets_ if v['stage'] == st]
            if vals:
                kb = [v['kb'] for v in vals]
                big = max(vals, key=lambda v: v['kb'])
                L.append(f"| {creatures.STAGE_NAMES[st]} (`{st}`) | {len(vals)} | {sum(kb) / 1024:.2f} MB | "
                         f"{sum(kb) / len(kb):.0f} KB | {big['kb']:.0f} KB ({big['creature']}) |")
    L += ['', '## Phòng', '', '| Phòng | Số đồ | Nền | Cả phòng |', '| --- | ---: | ---: | ---: |']
    for room, v in rooms_.items():
        L.append(f"| {room} | {v['items']} | {v['background_kb']:.0f} KB | {v['kb']:.0f} KB |")
    L += ['', '## RAM khi chạy', '',
          'Ảnh PNG được giải nén lúc nạp: một cảnh cần nền 640×480×4 = 1,2 MB, atlas đồ của phòng và atlas pet '
          '(mỗi điểm 4 byte), cộng bộ đệm màn. Trên R36S (RAM 1 GB) chừng này không đáng kể; vẫn giữ luật '
          '"mỗi màn chỉ nạp thứ cần" để khớp bản PocketGo.']
    with open(INVENTORY, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    args = [a for a in sys.argv[1:] if a not in ('--all', '--rgba')]
    for d in (PET_DIR, ROOM_DIR):
        os.makedirs(d, exist_ok=True)
    index_path = os.path.join(OUT, 'danh-sach.json')
    try:
        index = json.load(open(index_path, encoding='utf-8'))
    except (OSError, ValueError):
        index = {}
    report = index.get('paks', {})
    force = '--all' in sys.argv or index.get('settings') != SETTINGS
    units = creatures.selected([''] + args)
    print('== pet (640)')
    pets(units, force, report)
    missing = sum(1 for cid, st in units if not os.path.exists(os.path.join(creatures.frames_dir(cid, st), 'frames.json')))
    if missing:
        print(f'  {missing} bộ chưa cắt cỡ 640, bỏ qua (HOLUA_SCREEN=640 python slice_frames.py ...)')
    if not args:
        print('== phòng')
        rooms(report)
        print('== đồ ăn')
        food(report)
    report = {k: v for k, v in sorted(report.items())
              if os.path.exists(os.path.join(OUT, k + '.png')) or os.path.exists(os.path.join(OUT, k + '_do.png'))}
    total = sum(v['kb'] for v in report.values())
    with open(index_path, 'w', encoding='utf-8') as fh:
        json.dump(dict(settings=SETTINGS, screen=[W, H], night=NIGHT, total_mb=round(total / 1024, 2), paks=report),
                  fh, ensure_ascii=False, indent=1)
    if not args:
        write_inventory(report, missing)
    print(f'tổng {total / 1024:.1f} MB, bảng: assets/KIEM-KE-R36S.md')


if __name__ == '__main__':
    main()
