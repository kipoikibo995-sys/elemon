"""Packs every creature, room and food into the small files the PocketGo build loads, and reads them
back. Everything is already at screen size (320x240 screen): nothing is scaled on the device.

Output (build/pak/):
    pet/<creature>_<stage>.pak    one creature at one stage
    phong/<room>.pak              one room: empty background + its decor items
    do-an.pak                     every food, as a menu icon and as the small piece in the bowl
    danh-sach.json                what was packed, sizes, and the night tint
Only what changed is packed again. Anything not ready (a sheet still being copied, a room without
items yet) is reported and skipped; its old .pak, if any, is kept.

Sprite rows (pets, decor, food): 8-bit palette indices, index 0 = see-through and not stored.
Each row of a sprite is a run of packets, until the row's width is filled:
    0x00-0x7F  n+1 indices follow (stored as index-1)
    0x80-0xBF  n-0x7F (1..64) see-through pixels
    0xC0-0xFF  n-0xBD (3..66) times the one index that follows (stored as index-1)
Background rows (RGB565, little-endian u16), until 320 pixels are filled:
    0x00-0x7F  n+1 colours follow;  0x80-0xFF  n-0x7E (2..129) times the one colour that follows
There is no white "flash" copy: the game lightens the palette while drawing. Night is the same:
the game runs every colour through the tint in danh-sach.json (fitted from the painted
day/night pictures), once per room load.

Creature pak, little-endian:
    'HLPC' u8 version=2 u8 colours u16 frames  u16 canvas_w u16 canvas_h u16 anchor_x u16 anchor_y
    colours x u16 RGB565
    frames x { u8 name_len, name, i16 align_dx, u16 x, u16 y, u16 w, u16 h, u32 data_len, rows }
    Each frame is cropped to its visible pixels (x, y = place on the canvas).
Room pak:
    'HLPR' u8 version=2 u8 colours u16 items u32 bg_len, background rows (320x240)
    colours x u16 RGB565 (shared by all items)
    items x { u8 name_len, name, i16 x, i16 y, i16 floor, u16 w, u16 h, u32 data_len, rows }
    floor = screen y where the item touches the floor (draw back to front); -1 = lies flat, under all.
Food pak:
    'HLPF' u8 version=2 u8 colours u16 sprites, colours x u16 RGB565,
    sprites x { u8 name_len, name, u16 w, u16 h, u32 data_len, rows }
    names "icon/<file>" (menu, fits 32x32) and "bat/<file>" (in the bowl, fits 14x14).

Usage: python pocketgo_pak.py [creature / element / stage names]   (see creatures.py; rooms and
       food are packed only when nothing is named)  --all  pack again even if up to date
"""
import glob, io, json, os, struct, sys
import numpy as np
from PIL import Image

import creatures

ROOT = creatures.ROOT
PAK_DIR = os.path.join(ROOT, 'build', 'pak')
PET_DIR = os.path.join(PAK_DIR, 'pet')
ROOM_DIR = os.path.join(PAK_DIR, 'phong')
FOOD = os.path.join(ROOT, 'assets', 'source', 'do-an')
VERSION = 2
# 8-bit indices cost the same whatever the count, so every set gets the full palette
COLOURS = 255
FOOD_ICON, FOOD_BOWL = 32, 14
# fitted from the 12 painted day/night pairs (nen/N*_ngay.png -> _dem.png): dark = a * day + b per
# channel. Lights (fire, lava, lanterns: bright and strongly coloured) keep their day colour:
#   hi = max(r,g,b), lo = min(r,g,b), keep = clamp((hi - 215) / 40) * clamp((hi - lo - 90) / 60)
#   night = dark + (day - dark) * keep
NIGHT = {'r': [0.464, -6.4], 'g': [0.549, -5.6], 'b': [0.675, 16.8], 'glow': [215, 40, 90, 60]}


def rgb565(rgb):
    r, g, b = (int(c) for c in rgb)
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def unpack565(v):
    return ((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31


# The device has no alpha blending: a pixel is drawn or not. Soft edges (from shrinking an item)
# below this alpha are dropped, otherwise their dark, half-mixed colour shows as a fringe.
SOLID = 160


def make_palette(images, colours=COLOURS):
    """One palette for a group of RGBA images (only their solid pixels count): (colour list, P image)."""
    px = np.concatenate([np.array(im)[..., :3][np.array(im)[..., 3] >= SOLID] for im in images])
    if not len(px):
        px = np.zeros((1, 3), np.uint8)
    q = Image.fromarray(px.reshape(1, -1, 3), 'RGB').quantize(colours, method=Image.Quantize.MEDIANCUT,
                                                               dither=Image.Dither.NONE)
    flat = q.getpalette()
    cols = [tuple(flat[i * 3:i * 3 + 3]) for i in np.unique(np.array(q)).tolist()]
    # pad by repeating the last colour, so a pixel that lands on a pad entry still gets a real colour
    pal = Image.new('P', (1, 1))
    pal.putpalette([c for col in cols + [cols[-1]] * (256 - len(cols)) for c in col])
    return cols, pal


def index_image(im, pal, n):
    """RGBA -> palette indices 1..n, 0 where see-through."""
    q = np.minimum(np.array(im.convert('RGB').quantize(palette=pal, dither=Image.Dither.NONE)), n - 1)
    q = q.astype(np.int16) + 1
    q[np.array(im)[..., 3] < SOLID] = 0
    return q


def rle_rows(idx):
    out = bytearray()
    lit = []

    def flush():
        for k in range(0, len(lit), 128):
            part = lit[k:k + 128]
            out.append(len(part) - 1)
            out.extend(v - 1 for v in part)
        lit.clear()
    for row in idx:
        row = [int(v) for v in row]
        i, n = 0, len(row)
        while i < n:
            j = i
            while j < n and row[j] == row[i]:
                j += 1
            run = j - i
            if row[i] == 0:
                flush()
                for k in range(0, run, 64):
                    out.append(0x7F + min(64, run - k))
            elif run >= 3:
                flush()
                k = 0
                while run - k >= 3:
                    m = min(66, run - k)
                    out += bytes((0xBD + m, row[i] - 1))
                    k += m
                lit.extend([row[i]] * (run - k))
            else:
                lit.extend(row[i:j])
            i = j
        flush()
    return bytes(out)


def unrle_rows(data, w, h):
    idx = np.zeros((h, w), np.int16)
    p = 0
    for y in range(h):
        x = 0
        while x < w:
            n = data[p]; p += 1
            if n < 0x80:
                idx[y, x:x + n + 1] = np.frombuffer(data[p:p + n + 1], np.uint8).astype(np.int16) + 1
                p += n + 1
                x += n + 1
            elif n < 0xC0:
                x += n - 0x7F
            else:
                idx[y, x:x + n - 0xBD] = data[p] + 1
                p += 1
                x += n - 0xBD
    return idx


def rle565(img):
    """320x240 RGB -> background rows (see the top of the file)."""
    a = np.array(img.convert('RGB')).astype(np.int32)
    v = ((a[..., 0] >> 3) << 11) | ((a[..., 1] >> 2) << 5) | (a[..., 2] >> 3)
    out = bytearray()
    lit = []

    def flush():
        for k in range(0, len(lit), 128):
            part = lit[k:k + 128]
            out.append(len(part) - 1)
            out.extend(struct.pack(f'<{len(part)}H', *part))
        lit.clear()
    for row in v:
        row = [int(c) for c in row]
        i, n = 0, len(row)
        while i < n:
            j = i
            while j < n and row[j] == row[i] and j - i < 129:
                j += 1
            if j - i >= 2:
                flush()
                out += struct.pack('<BH', 0x7E + j - i, row[i])
            else:
                lit.append(row[i])
            i = j
        flush()
    return bytes(out)


def unrle565(data, p, w=320, h=240):
    """-> (h, w, 3) RGB as the screen shows it"""
    bg = np.zeros((h, w, 3), np.uint8)
    for y in range(h):
        x = 0
        while x < w:
            n = data[p]; p += 1
            if n < 0x80:
                for c in struct.unpack_from(f'<{n + 1}H', data, p):
                    bg[y, x] = unpack565(c); x += 1
                p += 2 * (n + 1)
            else:
                bg[y, x:x + n - 0x7E] = unpack565(struct.unpack_from('<H', data, p)[0])
                p += 2
                x += n - 0x7E
    return bg


def write_palette(out, cols):
    for c in cols:
        out.write(struct.pack('<H', rgb565(c)))


def read_palette(data, p, n):
    return [None] + [unpack565(v) for v in struct.unpack_from(f'<{n}H', data, p)], p + 2 * n


def pack_creature(cid, stage):
    fr = creatures.frames_dir(cid, stage)
    meta = json.load(open(os.path.join(fr, 'frames.json')))
    ims = [Image.open(os.path.join(fr, 'png', n + '.png')).convert('RGBA') for n in meta['frames']]
    cols, pal = make_palette(ims)
    out = io.BytesIO()
    out.write(b'HLPC' + struct.pack('<BBH4H', VERSION, len(cols), len(ims), *meta['canvas'], *meta['anchor']))
    write_palette(out, cols)
    for name, im in zip(meta['frames'], ims):
        x0, y0, x1, y1 = im.getchannel('A').point(lambda a: 255 if a >= SOLID else 0).getbbox() or (0, 0, 1, 1)
        rows = rle_rows(index_image(im.crop((x0, y0, x1, y1)), pal, len(cols)))
        nb = name.encode()
        out.write(struct.pack('<B', len(nb)) + nb)
        out.write(struct.pack('<h4HI', meta['align'].get(name, [0, 0])[0], x0, y0, x1 - x0, y1 - y0, len(rows)))
        out.write(rows)
    return out.getvalue()


def read_creature(data):
    """{'canvas', 'anchor', 'palette' [None, (r,g,b)...], 'frames': {name: dict(dx, x, y, idx)}}"""
    _, ver, ncol, nfr, cw, ch, ax, ay = struct.unpack_from('<4sBBH4H', data, 0)
    pal, p = read_palette(data, 4 + struct.calcsize('<BBH4H'), ncol)
    frames = {}
    for _ in range(nfr):
        nl = data[p]; name = data[p + 1:p + 1 + nl].decode(); p += 1 + nl
        dx, x, y, w, h, ln = struct.unpack_from('<h4HI', data, p); p += struct.calcsize('<h4HI')
        frames[name] = dict(dx=dx, x=x, y=y, idx=unrle_rows(data[p:p + ln], w, h))
        p += ln
    return dict(canvas=(cw, ch), anchor=(ax, ay), palette=pal, frames=frames)


def pack_room(background, items):
    """background: 320x240 image; items: [(name, RGBA image at screen size, x, y, floor)]"""
    cols, pal = make_palette([im for _, im, *_ in items])
    out = io.BytesIO()
    bg = rle565(background)
    out.write(b'HLPR' + struct.pack('<BBHI', VERSION, len(cols), len(items), len(bg)) + bg)
    write_palette(out, cols)
    for name, im, x, y, floor in items:
        rows = rle_rows(index_image(im, pal, len(cols)))
        nb = name.encode()
        out.write(struct.pack('<B', len(nb)) + nb + struct.pack('<3h2HI', x, y, floor, im.width, im.height, len(rows)))
        out.write(rows)
    return out.getvalue()


def read_room(data):
    _, ver, ncol, nit, bgl = struct.unpack_from('<4sBBHI', data, 0)
    p = 4 + struct.calcsize('<BBHI')
    bg = unrle565(data, p)
    pal, p = read_palette(data, p + bgl, ncol)
    items = []
    for _ in range(nit):
        nl = data[p]; name = data[p + 1:p + 1 + nl].decode(); p += 1 + nl
        x, y, floor, w, h, ln = struct.unpack_from('<3h2HI', data, p); p += struct.calcsize('<3h2HI')
        items.append(dict(name=name, x=x, y=y, floor=floor, idx=unrle_rows(data[p:p + ln], w, h)))
        p += ln
    return dict(background=bg, palette=pal, items=items)


def fit(im, box):
    """Shrink an RGBA image to fit box x box, cropped to its solid pixels first."""
    im = im.crop(im.getchannel('A').point(lambda a: 255 if a >= SOLID else 0).getbbox() or (0, 0, 1, 1))
    s = box / max(im.size)
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)


def pack_food(paths):
    sprites = []
    for path in paths:
        stem = os.path.splitext(os.path.basename(path))[0]
        im = Image.open(path).convert('RGBA')
        sprites += [('icon/' + stem, fit(im, FOOD_ICON)), ('bat/' + stem, fit(im, FOOD_BOWL))]
    cols, pal = make_palette([im for _, im in sprites])
    out = io.BytesIO()
    out.write(b'HLPF' + struct.pack('<BBH', VERSION, len(cols), len(sprites)))
    write_palette(out, cols)
    for name, im in sprites:
        rows = rle_rows(index_image(im, pal, len(cols)))
        nb = name.encode()
        out.write(struct.pack('<B', len(nb)) + nb + struct.pack('<2HI', im.width, im.height, len(rows)) + rows)
    return out.getvalue()


def read_food(data):
    _, ver, ncol, n = struct.unpack_from('<4sBBH', data, 0)
    pal, p = read_palette(data, 8, ncol)
    sprites = {}
    for _ in range(n):
        nl = data[p]; name = data[p + 1:p + 1 + nl].decode(); p += 1 + nl
        w, h, ln = struct.unpack_from('<2HI', data, p); p += 8
        sprites[name] = unrle_rows(data[p:p + ln], w, h)
        p += ln
    return dict(palette=pal, sprites=sprites)


# ---------------------------------------------------------------- build

# a pet pak is packed again when one of these changes (rooms and food are cheap: always packed)
SETTINGS = dict(version=VERSION, colours=COLOURS, solid=SOLID)


def fresh(out, inputs, force):
    """Already packed from these inputs."""
    if force or not os.path.exists(out):
        return False
    return os.path.getmtime(out) >= max(os.path.getmtime(p) for p in inputs if os.path.exists(p))


def save(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'wb') as fh:
        fh.write(data)
    os.replace(tmp, path)


def pets(units, force, report):
    for cid, stage in units:
        fr = creatures.frames_dir(cid, stage)
        out = os.path.join(PET_DIR, f'{cid}_{stage}.pak')
        if not os.path.exists(os.path.join(fr, 'frames.json')):
            print(f'  bỏ qua {cid}/{stage}: chưa cắt khung')
            continue
        inputs = [os.path.join(fr, 'frames.json')] + glob.glob(os.path.join(fr, 'png', '*.png'))
        try:
            if not fresh(out, inputs, force):
                save(out, pack_creature(cid, stage))
                print(f'  pet/{cid}_{stage}.pak: {os.path.getsize(out) / 1024:.0f} KB')
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
            print(f'  bỏ qua {cid}/{stage}: {e}')
            continue
        data = open(out, 'rb').read()
        report[f'pet/{cid}_{stage}.pak'] = dict(kb=round(len(data) / 1024, 1), frames=struct.unpack_from('<H', data, 6)[0],
                                                element=creatures.CREATURES[cid]['element'], creature=cid, stage=stage)


def rooms(report):
    import place_decor
    from preview_decor_room import EMPTY, DECOR, items_of
    for room in place_decor.ROOM_CODE:
        out = os.path.join(ROOM_DIR, f'{room}.pak')
        folder = os.path.join(DECOR, room)
        if room not in EMPTY or not glob.glob(os.path.join(folder, '*.png')):
            print(f'  bỏ qua phòng {room}: chưa có nền trống hoặc chưa có đồ')
            continue
        try:
            if not os.path.exists(os.path.join(folder, 'vi-tri.json')):
                print(f'  {room}: chưa có vi-tri.json, đặt đồ mặc định (place_decor.py)')
                place_decor.main([room])
            bg = Image.open(EMPTY[room]).convert('RGB').resize((320, 240), Image.LANCZOS)
            items = [(it['name'], it['img'], it['x'], it['y'], it['floor']) for it in items_of(room)]
            save(out, pack_room(bg, items))
            print(f'  phong/{room}.pak: {os.path.getsize(out) / 1024:.0f} KB')
        except (OSError, ValueError, KeyError, IndexError, json.JSONDecodeError) as e:
            print(f'  bỏ qua phòng {room}: {e}')
            continue
        data = open(out, 'rb').read()
        _, _, ncol, nit, bgl = struct.unpack_from('<4sBBHI', data, 0)
        report[f'phong/{room}.pak'] = dict(kb=round(len(data) / 1024, 1), items=nit, background_kb=round(bgl / 1024, 1))


def food(report):
    out = os.path.join(PAK_DIR, 'do-an.pak')
    ok = []
    for p in sorted(glob.glob(os.path.join(FOOD, '*.png'))):
        if os.path.basename(p).startswith('_'):
            continue
        try:
            with Image.open(p) as im:
                im.load()
            ok.append(p)
        except OSError as e:
            print(f'  bỏ qua món {os.path.basename(p)}: {e}')
    if not ok:
        return
    save(out, pack_food(ok))
    print(f'  do-an.pak: {os.path.getsize(out) / 1024:.0f} KB')
    report['do-an.pak'] = dict(kb=round(os.path.getsize(out) / 1024, 1), foods=len(ok))


INVENTORY = os.path.join(ROOT, 'assets', 'KIEM-KE-PAK.md')
# measured on 24/10/2026 (tried, not used: none saves enough to be worth what it costs)
NOTES = """## Đã thử giảm thêm (24/10/2026)

| Cách | Kết quả | Dùng? |
| --- | --- | --- |
| Bảng màu 128 → 255 màu | Mỗi điểm vẫn 1 byte, chỉ +254 byte/bộ; sai màu giảm ~15% (Hỏa Hổ 4 chân: 6,4 → 5,4) | **Có** |
| Mã thêm "lặp 1 màu" trong RLE | Bù hết phần tăng do nhiều màu hơn: pet 18,9 → 18,8 MB dù lên 255 màu | **Có** |
| Nền phòng: RGB565 nén theo gói (thay cho cặp số-màu) | Hang đá 240 → 146 KB cả file (cặp số-màu còn nặng hơn ảnh thô 150 KB) | **Có** |
| Ít màu hơn cho con nhỏ (32/64 màu) | Chỉ nhẹ đi 0–8% (Con: 34 → 31 KB), sai màu tăng 40–70% | Không |
| Bỏ khung trùng nhau | 3.848 khung, không có khung nào trùng sau khi đóng gói | Không cần |
| Nén zlib cả file pet | Chỉ −3,6% (RLE đã gần hết phần thừa), lại phải giải nén trên máy | Không |
| Nền phòng 256 màu thay RGB565 | Còn ~75 KB/nền, nhưng dễ loang màu trên nền vẽ tay; chưa thử, chỉ đáng làm nếu thiếu RAM | Chưa |

Thẻ nhớ không phải giới hạn (vài GB); thứ cần giữ nhỏ là RAM, mà một cảnh chỉ cần < 0,5 MB trên 32 MB.
"""


def write_inventory(report):
    """assets/KIEM-KE-PAK.md: sizes of everything in build/pak/, from danh-sach.json."""
    pets_ = [v for k, v in report.items() if k.startswith('pet/')]
    rooms_ = {k[6:-4]: v for k, v in report.items() if k.startswith('phong/')}
    total = sum(v['kb'] for v in report.values())
    L = ['# Kiểm kê file PocketGo (`build/pak/`)', '',
         'Tự ghi lại mỗi lần chạy `python scripts/pocketgo_pak.py` (hoặc `python scripts/build_assets.py`). '
         'Định dạng file: đầu `scripts/pocketgo_pak.py`. Chỉ chép `build/pak/` lên máy, không chép PNG/BMP/preview.', '',
         f'**Tổng: {total / 1024:.1f} MB trong {len(report)} file** (trước khi tối ưu: `assets/creatures/` 348 MB; '
         'bản thử đầu chỉ pet: 18,9 MB).', '',
         '| Nhóm | Số file | Dung lượng | Nhỏ nhất – lớn nhất |', '| --- | ---: | ---: | ---: |']

    def row(name, vals):
        kb = [v['kb'] for v in vals]
        if kb:
            L.append(f'| {name} | {len(kb)} | {sum(kb) / 1024:.2f} MB | {min(kb):.0f} – {max(kb):.0f} KB |')
    row('Pet (mọi con, mọi cấp)', pets_)
    row('Phòng (nền + đồ)', list(rooms_.values()))
    row('Đồ ăn', [v for k, v in report.items() if k == 'do-an.pak'])
    L += ['', '## Pet theo cấp', '', '| Cấp | Số bộ | Khung | Dung lượng | Trung bình | Lớn nhất |',
          '| --- | ---: | ---: | ---: | ---: | ---: |']
    for st in creatures.STAGES:
        vals = [v for v in pets_ if v['stage'] == st]
        if vals:
            kb = [v['kb'] for v in vals]
            big = max(vals, key=lambda v: v['kb'])
            L.append(f"| {creatures.STAGE_NAMES[st]} (`{st}`) | {len(vals)} | {sum(v['frames'] for v in vals)} | "
                     f"{sum(kb) / 1024:.2f} MB | {sum(kb) / len(kb):.0f} KB | {big['kb']:.0f} KB ({big['creature']}) |")
    L += ['', '## Pet theo hệ', '', '| Hệ | Số bộ | Dung lượng |', '| --- | ---: | ---: |']
    for code, (folder, name) in creatures.ELEMENTS.items():
        kb = [v['kb'] for v in pets_ if v['element'] == folder]
        if kb:
            L.append(f'| {name} | {len(kb)} | {sum(kb) / 1024:.2f} MB |')
    L += ['', '## Phòng', '', '| Phòng | Số đồ | Nền | Cả file |', '| --- | ---: | ---: | ---: |']
    for room, v in rooms_.items():
        L.append(f"| {room} | {v['items']} | {v['background_kb']:.0f} KB | {v['kb']:.0f} KB |")
    if pets_ and rooms_:
        worst = max(v['kb'] for v in pets_) + max(v['kb'] for v in rooms_.values()) + 150
        L += ['', '## RAM khi chạy', '',
              'Một cảnh = 1 file phòng + 1 file pet đang nuôi + bộ đệm màn 320×240×2 = 150 KB '
              '(vẽ thẳng từ dữ liệu RLE, không cần giải nén ra ảnh). '
              f'Nặng nhất có thể: **{worst:.0f} KB** (phòng lớn nhất + pet lớn nhất) trên 32 MB RAM. '
              f"Đồ ăn nạp thêm {report.get('do-an.pak', {}).get('kb', 0):.0f} KB khi mở menu. "
              'Đêm không cần file riêng: tô màu theo `night` trong `danh-sach.json` lúc nạp phòng.']
    L += ['', NOTES]
    with open(INVENTORY, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L))


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if creatures.SCREEN != 320:
        sys.exit('pocketgo_pak.py packs the 320 set; for HOLUA_SCREEN=640 use r36s_pak.py')
    args = [a for a in sys.argv[1:] if a != '--all']
    force = '--all' in sys.argv
    for d in (PET_DIR, ROOM_DIR):
        os.makedirs(d, exist_ok=True)
    # the first trial wrote everything flat into build/pak/
    for old in glob.glob(os.path.join(PAK_DIR, '*.pak')):
        if os.path.basename(old) != 'do-an.pak':
            os.remove(old)
    index_path = os.path.join(PAK_DIR, 'danh-sach.json')
    try:
        index = json.load(open(index_path, encoding='utf-8'))
    except (OSError, ValueError):
        index = {}
    report = index.get('paks', {})
    force = force or index.get('settings') != SETTINGS
    print('== pet')
    pets(creatures.selected([''] + args), force, report)
    if not args:
        print('== phòng')
        rooms(report)
        print('== đồ ăn')
        food(report)
    report = {k: v for k, v in sorted(report.items()) if os.path.exists(os.path.join(PAK_DIR, k))}
    total = sum(v['kb'] for v in report.values())
    with open(index_path, 'w', encoding='utf-8') as fh:
        json.dump(dict(version=VERSION, settings=SETTINGS, night=NIGHT, total_mb=round(total / 1024, 2), paks=report),
                  fh, ensure_ascii=False, indent=1)
    write_inventory(report)
    print(f'tổng {total / 1024:.1f} MB trong {len(report)} file, bảng: assets/KIEM-KE-PAK.md')


if __name__ == '__main__':
    main()
