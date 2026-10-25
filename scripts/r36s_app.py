"""Data of the R36S viewer app (r36s/): the packed R36S set (build/r36s/, from r36s_pak.py) turned into
files the app reads with plain C, no image or JSON library on the handheld:

dist/holua-r36s/holua/data/
    list.txt                   rooms (name, label, feet y, floor edges) and pets (creature, stage, labels)
    bg/<room>.hli              empty room, 640x480
    phong/<room>_do.hli, .txt  decor atlas and its index (as build/r36s)
    pet/<c>_<stage>.hli, .txt  frame atlas and index (as build/r36s)
    pet/<c>_<stage>.anim       moves from the shared anims.json, already at 640 size (x, y, br, shake x2)
    font.hli, font.txt         DejaVu Sans Bold glyphs for every character the app shows
    sfx/*.wav, nhac/*.wav      assets/am-thanh (make_sfx_8bit.py)
dist/holua-r36s/HoLua.sh, holua/buttons.txt, holua/cover.png   launcher, button map, Ports picture

.hli: 'HLI1', u16 width, u16 height, u16 colours, then
    colours 1..256: colours x RGBA palette, then the indices of all rows in packets:
        0x00-0x7F n+1 indices follow;  0x80-0xFF n-0x7E (2..129) times the index that follows
    colours 0: raw RGBA;  colours 0xFFFF: raw RGB
.anim, one line each:  move NAME LOOP(0/1)  /  key FRAME MS X Y BR SHAKE FLASH
Usage: python r36s_app.py   (after r36s_pak.py and make_sfx_8bit.py)
"""
import glob, json, os, shutil, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

os.environ['HOLUA_SCREEN'] = '640'
import creatures

ROOT = creatures.ROOT
PAK = os.path.join(ROOT, 'build', 'r36s')
DIST = os.path.join(ROOT, 'dist', 'holua-r36s')
DATA = os.path.join(DIST, 'holua', 'data')
SOUNDS = os.path.join(ROOT, 'assets', 'am-thanh')
FONT = os.path.join(ROOT, 'assets', 'font', 'DejaVuSans-Bold.ttf')
FONT_PX = 15
K = creatures.SIZE

ROOMS = {
    'L1-HO_hang-da': 'Lv1 · Hang đá', 'L1-HO_nha-hoang': 'Lv1 · Nhà hoang',
    'L2-HO': 'Lv2 Hỏa · Hang bếp than', 'L2-KI': 'Lv2 Kim · Lán thợ mỏ', 'L2-MO': 'Lv2 Mộc · Lều tranh',
    'L2-TH': 'Lv2 Thủy · Chòi chài', 'L2-TO': 'Lv2 Thổ · Nhà vách đất',
    'L3-HO': 'Lv3 Hỏa · Lò rèn núi lửa', 'L3-KI': 'Lv3 Kim · Xưởng kim loại', 'L3-MO': 'Lv3 Mộc · Chòi trên cây',
    'L3-TH': 'Lv3 Thủy · Nhà sàn bên hồ', 'L3-TO': 'Lv3 Thổ · Nhà đất nung',
    'L4-HO': 'Lv4 Hỏa · Đền Hỏa Long', 'L4-KI': 'Lv4 Kim · Điện Kim Cương', 'L4-MO': 'Lv4 Mộc · Cây Thần',
    'L4-TH': 'Lv4 Thủy · Thủy Cung', 'L4-TO': 'Lv4 Thổ · Thạch Điện',
}
# feet y and floor edges on the 320 screen (as preview_pocketgo / xem-truc-tiep.html), doubled in list.txt
FLOOR = {'L1-HO_hang-da': (165, 30, 290), 'L3-HO': (175, 30, 295), 'L2-TH': (180, 20, 300),
         'L3-KI': (185, 25, 290), 'L4-MO': (182, 50, 285)}
FLOOR_DEFAULT = (180, 30, 290)
MOVE_LABELS = {'idle': 'Đứng thở', 'punch': 'Đấm', 'blast': 'Chiêu', 'hit': 'Trúng đòn', 'faint': 'Gục ngã',
               'victory': 'Thắng', 'eat': 'Ăn', 'happy': 'Vui nhảy', 'tired': 'Mệt', 'sick': 'Ốm', 'sleep': 'Ngủ',
               'wake': 'Thức dậy', 'attack': 'Đòn hệ', 'shake': 'Lắc', 'hatch': 'Nở', 'walk': 'Đi', 'run': 'Chạy'}
# every piece of text the app shows (strings.txt: "key text"; the move names are keys too)
UI = {'updown': '▲▼', 'act': 'A làm', 'walkhint': '◀▶ đi · giữ B chạy',
      'help': 'L1/R1 phòng · X/Y pet · SELECT đêm · START nhạc', 'quit': 'SELECT+START thoát',
      'day': 'Ngày', 'night': 'Đêm', 'music_on': '♪ bật', 'music_off': '♪ tắt'}


def rle(idx):
    out, lit = bytearray(), []

    def flush():
        for k in range(0, len(lit), 128):
            part = lit[k:k + 128]
            out.append(len(part) - 1)
            out.extend(part)
        lit.clear()
    v = idx.ravel().tolist()
    i, n = 0, len(v)
    while i < n:
        j = i
        while j < n and v[j] == v[i] and j - i < 129:
            j += 1
        if j - i >= 2:
            flush()
            out += bytes((0x7E + j - i, v[i]))
        else:
            lit.append(v[i])
        i = j
    flush()
    return bytes(out)


def write_hli(path, im):
    """P (with alpha per colour), RGBA or RGB picture -> .hli"""
    w, h = im.size
    if im.mode == 'P':
        if im.palette and im.palette.mode == 'RGBA':          # quantized in memory: alpha is in the palette
            rgba = bytes(im.getpalette('RGBA'))
            n = len(rgba) // 4
        else:                                                  # read from a PNG: alpha in its tRNS chunk
            pal = im.getpalette() or []
            n = len(pal) // 3
            trns = im.info.get('transparency', b'')
            if isinstance(trns, int):
                alpha = [0 if i == trns else 255 for i in range(n)]
            else:
                alpha = list(trns) + [255] * (n - len(trns))
            rgba = bytes(c for i in range(n) for c in (pal[3 * i], pal[3 * i + 1], pal[3 * i + 2], alpha[i]))
        body = struct.pack('<HHH', w, h, n) + rgba + rle(np.array(im, np.uint8))
        # what the app will see must be exactly the PNG
        check = np.array(im.convert('RGBA'))
        lut = np.frombuffer(rgba, np.uint8).reshape(-1, 4)
        assert (lut[np.array(im)] == check)[check[..., 3] > 0].all(), path
    elif im.mode == 'RGBA':
        body = struct.pack('<HHH', w, h, 0) + im.tobytes()
    else:
        body = struct.pack('<HHH', w, h, 0xFFFF) + im.convert('RGB').tobytes()
    with open(path, 'wb') as fh:
        fh.write(b'HLI1' + body)


def write_anim(path, anims):
    lines = []
    for name, a in anims.items():
        if name.startswith('_'):
            continue
        lines.append(f"move {name} {1 if a.get('loop') else 0}")
        for key in a['keys']:
            # '-' = keep the previous key's x / y (as preview_anims.samples does)
            x = key['x'] * K if 'x' in key else '-'
            y = key['y'] * K if 'y' in key else '-'
            lines.append(f"key {key['f']} {key['ms']} {x} {y} {key.get('br', 0) * K} "
                         f"{round(key.get('shake', 0) * K)} {key.get('flash', 0)}")
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')


def write_font(texts):
    chars = sorted(set(''.join(texts)) | set(chr(c) for c in range(32, 127)))
    font = ImageFont.truetype(FONT, FONT_PX)
    asc, desc = font.getmetrics()
    # Vietnamese capitals with two marks (Ố, Ỗ...) reach above the ascent: every cell is as tall as the
    # tallest and deepest glyph, or a mark spills into the cell of the row above
    top = min(0, min(font.getbbox(ch)[1] for ch in chars))
    bottom = max(asc + desc, max(font.getbbox(ch)[3] for ch in chars))
    glyphs, x, row_h, atlas_w = [], 0, bottom - top + 2, 1024
    y = 0
    for ch in chars:
        l, t, r, b = font.getbbox(ch)
        w = max(1, r - l)
        if x + w + 1 > atlas_w:
            x, y = 0, y + row_h
        glyphs.append((ch, x, y, w, l, font.getlength(ch)))
        x += w + 1
    atlas = Image.new('RGBA', (atlas_w, y + row_h), (255, 255, 255, 0))
    d = ImageDraw.Draw(atlas)
    lines = [f'lineheight {asc + desc} ascent {asc}']
    for ch, gx, gy, w, l, adv in glyphs:
        d.text((gx - l, gy - top), ch, font=font, fill=(255, 255, 255, 255))
        # last number: where the cell starts relative to the text line's top (negative = above it)
        lines.append(f'glyph {ord(ch)} {gx} {gy} {w} {row_h} {l} {round(adv)} {top}')
    write_hli(os.path.join(DATA, 'font.hli'), atlas)
    with open(os.path.join(DATA, 'font.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')
    return len(chars)


def cover():
    """Ports list picture: a still of the first R36S test scene."""
    still = os.path.join(ROOT, 'preview', 'r36s', 'so-sanh_L1-HO_hang-da.png')
    if os.path.exists(still):
        im = Image.open(still).convert('RGB').crop((650, 28, 1290, 480))
        im.resize((480, 339), Image.LANCZOS).save(os.path.join(DIST, 'holua', 'cover.png'))


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if os.path.exists(DATA):
        shutil.rmtree(DATA)
    for d in ('bg', 'phong', 'pet', 'sfx', 'nhac'):
        os.makedirs(os.path.join(DATA, d))
    strings = {**UI, **MOVE_LABELS}
    with open(os.path.join(DATA, 'strings.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(f'{k} {v}' for k, v in strings.items()) + '\n')
    # the HUD lines must fit the 640 px screen
    font = ImageFont.truetype(FONT, FONT_PX)
    for line in (UI['help'] + ' · ' + UI['quit'],):
        if font.getlength(line) > 620:
            print(f'  dòng chữ quá dài ({font.getlength(line):.0f} px): {line}')
    lines, texts = [], list(ROOMS.values()) + list(strings.values()) + ['()/ ·']
    for room, label in ROOMS.items():
        bg = os.path.join(PAK, 'phong', room + '.png')
        if not os.path.exists(bg):
            print(f'  bỏ qua phòng {room}: chưa đóng gói (r36s_pak.py)')
            continue
        write_hli(os.path.join(DATA, 'bg', room + '.hli'), Image.open(bg))
        write_hli(os.path.join(DATA, 'phong', room + '_do.hli'), Image.open(os.path.join(PAK, 'phong', room + '_do.png')))
        shutil.copy(os.path.join(PAK, 'phong', room + '_do.txt'), os.path.join(DATA, 'phong'))
        feet, lo, hi = FLOOR.get(room, FLOOR_DEFAULT)
        lines.append(f'room {room} {int(feet * K)} {int(lo * K)} {int(hi * K)} {label}')
    n_pets = 0
    for cid, stage in creatures.selected(['']):
        base = os.path.join(PAK, 'pet', f'{cid}_{stage}')
        if not os.path.exists(base + '.png'):
            continue
        anims = json.load(open(creatures.anims_path(cid, stage), encoding='utf-8'))
        write_hli(os.path.join(DATA, 'pet', f'{cid}_{stage}.hli'), Image.open(base + '.png'))
        shutil.copy(base + '.txt', os.path.join(DATA, 'pet'))
        write_anim(os.path.join(DATA, 'pet', f'{cid}_{stage}.anim'), anims)
        name, st = creatures.CREATURES[cid]['name'], creatures.STAGE_NAMES[stage]
        lines.append(f'pet {cid} {stage} {name} · {st}')
        texts.append(f'{name} · {st}')
        n_pets += 1
    with open(os.path.join(DATA, 'list.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')
    for kind in ('sfx', 'nhac'):
        for p in glob.glob(os.path.join(SOUNDS, kind, '*.wav')):
            shutil.copy(p, os.path.join(DATA, kind))
    n_glyphs = write_font(texts)
    for f in ('HoLua.sh', 'buttons.txt'):
        src = os.path.join(ROOT, 'r36s', f)
        dst = os.path.join(DIST, f) if f.endswith('.sh') else os.path.join(DIST, 'holua', f)
        with open(src, encoding='utf-8') as a, open(dst, 'w', encoding='utf-8', newline='\n') as b:
            b.write(a.read())
    cover()
    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(DIST) for f in fs)
    print(f'{DIST}: {len(lines) - n_pets} phòng, {n_pets} bộ pet, {n_glyphs} chữ, {size / 2 ** 20:.1f} MB')


if __name__ == '__main__':
    main()
