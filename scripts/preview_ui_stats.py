"""The pet stats screen (4 pages: Sinh tồn, Linh khí, Thuộc tính, Hồ sơ) built from the UI pieces in
assets/source/ui/ and the pet's own data, then drawn the way the device draws it: only from packed
files (one RGB565 background + palette sprites + bitmap font), no alpha blending.

The layout is written once in 640x480 units (the mock-ups in assets/source/ui/mau/) and built for
    pocketgo  320x240 (everything at half size)
    r36s      640x480
Writes build/pak/ui-stats_<target>.pak, preview/ui/<target>.mp4 (pages switch with L/R),
preview/ui/<target>_<page>.png and preview/ui/so-sanh_<page>.png (mock-up | PocketGo | R36S).
Usage: python preview_ui_stats.py [pocketgo] [r36s]   (default: pocketgo)
"""
import io, json, math, os, struct, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import creatures
import pocketgo_pak as pak
from preview_anims import STEP, samples

UI = os.path.join(creatures.ROOT, 'assets', 'source', 'ui')
FOOD = os.path.join(creatures.ROOT, 'assets', 'source', 'do-an')
OUT = os.path.join(creatures.ROOT, 'preview', 'ui')
TARGETS = {'pocketgo': 0.5, 'r36s': 1.0}
BUILD = ['pocketgo']                    # the R36S copy is made only when named on the command line
# the pet on this screen stands still and bounces: knees bend (upper body down), a small hop up,
# land, rest. Same key format as the anims.json files; whole-pixel moves only, cheap on the device.
BOUNCE = {'loop': True, 'keys': [{'f': 'idle-0', 'ms': 300, 'br': -1}, {'f': 'idle-0', 'ms': 350, 'y': -1},
                                 {'f': 'idle-0', 'ms': 350, 'y': 0}, {'f': 'idle-0', 'ms': 300}]}
FONT = 'C:/Windows/Fonts/tahomabd.ttf'
FONT_REGULAR = 'C:/Windows/Fonts/tahoma.ttf'
# no Tahoma (Linux, macOS): DejaVu Sans from assets/font, the game's own font on the R36S. It is about 11 % wider,
# so it is drawn that much smaller to keep the layout
FONT_SHRINK = 1.0
if not os.path.exists(FONT):
    FONT = os.path.join(creatures.ROOT, 'assets', 'font', 'DejaVuSans-Bold.ttf')
    FONT_REGULAR = os.path.join(creatures.ROOT, 'assets', 'font', 'DejaVuSans.ttf')
    FONT_SHRINK = 0.89
# below 9 px Vietnamese marks run into the letters, so nothing on the small screen is smaller

# ---- the pet shown (later: read from the save file) ----
PET = dict(
    name='Bông', creature='hoa-ho', stage='teen',
    survival=[('No', 72), ('Vui', 55), ('Sạch', 90), ('Năng lượng', 15), ('Sức khỏe', 100)],
    linh_khi=dict(hoa=80, tho=45, kim=25, thuy=15, moc=35), evolve_at=60,
    attributes=[('Sức mạnh', 38), ('Nhanh nhẹn', 30), ('Bền bỉ', 22), ('Thông minh', 12), ('Trí tuệ', 10),
                ('Tinh thần', 25)],
    level=12, exp=(620, 1000), personality=('hieu-chien', 'Hiếu chiến'), closeness=4,
    likes=('Hoa_1_roasted-chili-pepper', 'Ớt nướng'), dislikes=('Thuy_1_fresh-fish', 'Cá tươi'),
    weight=18, weight_range=(8, 30), home=('Lò rèn núi lửa', '+2/ngày'),
    gems=[('hoa', 3), ('thuy', 2), ('tho', 2), ('moc', 2), None],      # 5 sockets: (element, grade 1-5) or empty
)
# gems (ui/_bang/NGOC1_ngoc.png, 5 elements x 5 grades): a socketed gem raises its element's two attributes
# (THIET-KE.md "Liên kết với Ngũ Hành"); amounts per grade are placeholders
GEM_ATTRS = {'hoa': (0, 1), 'thuy': (3, 4), 'tho': (2, 4), 'moc': (2, 5), 'kim': (0, 2)}
GEM_NAMES = {'hoa': 'Hỏa', 'thuy': 'Thủy', 'tho': 'Thổ', 'moc': 'Mộc', 'kim': 'Kim'}
GRADES = [('Đá thô', 1), ('Ngọc mài', 2), ('Ngọc cắt', 4), ('Ngọc quý', 6), ('Ngọc thần', 10)]
SOCKETS = [(50 + 40 * i, 77) for i in range(5)]        # socket centres, 640 units (high up: big pets stand below)
LIVE = False      # True: page 3 leaves the bars, numbers and gems to the live page (build_evo_app.py)


def gem_bonus(gems):
    out = [0] * 6
    for g in gems:
        if g:
            for a in GEM_ATTRS[g[0]]:
                out[a] += GRADES[g[1] - 1][1]
    return out


def gem_img(he, grade, size):
    im = Image.open(os.path.join(UI, 'cat', f'ngoc_{he}_{grade}.png')).convert('RGBA')
    im.thumbnail((size, size), Image.LANCZOS)
    return im


def cat_img(name, w, h=None):
    im = Image.open(os.path.join(UI, 'cat', name + '.png')).convert('RGBA')
    return im.resize((max(1, w), max(1, h or round(im.height * w / im.width))), Image.LANCZOS)
SURVIVAL_LOOK = [('icon_no', 'cam'), ('icon_vui', 'hong'), ('icon_sach', 'xanh-duong'),
                 ('icon_nang-luong', 'xanh-reu'), ('icon_suc-khoe', 'do')]
ATTRIBUTE_LOOK = [('icon_suc-manh', 'do'), ('icon_nhanh-nhen', 'cam'), ('icon_ben-bi', 'xanh-reu'),
                  ('icon_thong-minh', 'xanh-duong'), ('icon_tri-tue', 'tim'), ('icon_tinh-than', 'hong')]
# radar corners clockwise from the top: the generating cycle Hỏa > Thổ > Kim > Thủy > Mộc
RADAR = [('hoa', 'Hỏa', (255, 205, 130)), ('tho', 'Thổ', (240, 200, 90)), ('kim', 'Kim', (230, 230, 230)),
         ('thuy', 'Thủy', (120, 175, 255)), ('moc', 'Mộc', (125, 210, 95))]
PAGES = ['Sinh tồn', 'Linh khí', 'Thuộc tính', 'Hồ sơ']
PET_FEET = 350                          # feet on the pedestal's top, 640 units
TEXT = (238, 226, 206)
MUTED = (176, 150, 122)
GREEN = (140, 225, 110)
DARK = (28, 17, 13)


# ---------------- building the pieces (PC side) ----------------

def goc(name):
    return Image.open(os.path.join(UI, 'goc', name + '.png')).convert('RGBA')


def r36_size(name):
    return Image.open(os.path.join(UI, 'r36s', name + '.png')).size


def despeck(im, smallest=0.002):
    """Drops stray specks (blobs smaller than this share of the picture) left around a cut-out piece."""
    a = np.array(im)
    solid = a[..., 3] >= 128
    lab = np.zeros(solid.shape, np.int32)
    n = 0
    for y, x in zip(*np.nonzero(solid)):
        if lab[y, x]:
            continue
        n += 1
        stack, blob = [(y, x)], []
        lab[y, x] = n
        while stack:
            cy, cx = stack.pop()
            blob.append((cy, cx))
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < solid.shape[0] and 0 <= nx < solid.shape[1] and solid[ny, nx] and not lab[ny, nx]:
                    lab[ny, nx] = n
                    stack.append((ny, nx))
        if len(blob) < smallest * solid.size:
            ys, xs = zip(*blob)
            a[list(ys), list(xs), 3] = 0
    return Image.fromarray(a, 'RGBA')


def piece(name, s, k=1.0, clean=False):
    """A UI piece at k times its R36S size, for a screen scale s (made from the big source)."""
    w, h = r36_size(name)
    im = goc(name).resize((max(1, round(w * k * s)), max(1, round(h * k * s))), Image.LANCZOS)
    return despeck(im) if clean else im


def nine(name, w640, h640, s, corner, mid=0, thin=1.0):
    """9-slice of a frame piece to w640 x h640 (640 units); corner in R36S px; mid = width of an
    ornament kept unstretched in the middle of the top and bottom edges; thin < 1 draws the border
    and its ornaments smaller than the piece's own size."""
    src = goc(name)
    k = src.width / r36_size(name)[0] / thin
    W, H, c, m = round(w640 * k), round(h640 * k), round(corner * k), round(mid * k)
    w, h = src.size
    out = Image.new('RGBA', (W, H))

    def put(box, x, y, dw, dh):
        if dw > 0 and dh > 0 and box[2] > box[0] and box[3] > box[1]:
            out.alpha_composite(src.crop(box).resize((dw, dh), Image.LANCZOS), (x, y))
    xs, ys, XS, YS = [0, c, w - c, w], [0, c, h - c, h], [0, c, W - c, W], [0, c, H - c, H]
    for i in range(3):
        for j in range(3):
            put((xs[j], ys[i], xs[j + 1], ys[i + 1]), XS[j], YS[i], XS[j + 1] - XS[j], YS[i + 1] - YS[i])
    if m:
        for y0, y1, Y in ((0, c, 0), (h - c, h, H - c)):
            put((w // 2 - m // 2, y0, w // 2 + m // 2, y1), W // 2 - m // 2, Y, m, c)
    return out.resize((max(1, round(w640 * s)), max(1, round(h640 * s))), Image.LANCZOS)


def food_icon(name, size):
    im = Image.open(os.path.join(FOOD, name + '.png')).convert('RGBA')
    im = im.crop(im.getbbox())
    im.thumbnail((size, size), Image.LANCZOS)
    return im


def font(style, s):
    size, bold = SIZES[style]
    return ImageFont.truetype(FONT if bold else FONT_REGULAR, max(9, round(size * s * FONT_SHRINK)))


def glyph_set(sizes, s):
    """Every character of every text, at every size: {(size, ch): white RGBA glyph, advance}."""
    texts = PAGES + [t for t, _ in PET['survival']] + [t for t, _ in PET['attributes']] + [n for _, n, _ in RADAR]
    texts += [PET['name'], creatures.CREATURES[PET['creature']]['name'], creatures.STAGE_NAMES[PET['stage']],
              'L/R: đổi trang', 'B: quay lại', 'A: đổi tên · B: quay lại', 'Vòng nét đứt = ngưỡng tiến hóa',
              'A: khảm ngọc · B: quay lại',
              'Cấp độ', 'Level', 'EXP', 'Tính cách', 'Thân thiết', 'Thích', 'Ghét', 'Thể trạng', 'kg',
              'Gầy · Vừa · Mập', 'Nhà', PET['personality'][1], PET['likes'][1], PET['dislikes'][1],
              *PET['home'], '0123456789/·+ ']
    chars = sorted(set(''.join(texts)))
    glyphs = {}
    for size in sizes:
        f = font(size, s)                          # here `size` is a style name
        asc, desc = f.getmetrics()
        for ch in chars:
            adv = max(1, round(f.getlength(ch)))
            im = Image.new('L', (adv + 2, asc + desc + 2))
            d = ImageDraw.Draw(im)
            d.fontmode = '1'                       # no antialiasing: the device draws a pixel or not
            d.text((0, 0), ch, font=f, fill=255)
            rgba = Image.new('RGBA', im.size, (255, 255, 255, 0))
            rgba.putalpha(im)
            glyphs[(size, ch)] = (rgba, adv)
    return glyphs


# style -> (size in 640 units, bold)
SIZES = {'tab': (15, True), 'label': (15, True), 'value': (17, True), 'name': (18, True), 'sub': (13, False),
         'small': (12, False), 'big': (20, True)}
STYLES = list(SIZES)


def build(target):
    """-> (background RGB, {sprite name: RGBA}, glyphs) for one target, laid out for that screen size."""
    s = TARGETS[target]
    W, H = round(640 * s), round(480 * s)
    S = lambda v: round(v * s)
    bg = Image.new('RGBA', (W, H), DARK + (255,))
    bg.alpha_composite(nine('khung_panel', 640, 410, s, 22, mid=46, thin=0.7), (0, S(44)))
    bg.alpha_composite(nine('khung_vach-chia', 24, 352, s, 12), (S(246), S(74)))
    bg.alpha_composite(piece('nut_L', s), (S(6), S(10)))
    bg.alpha_composite(piece('nut_R', s), (S(612), S(10)))
    ped = piece('be-dung_hoa', s, 1.0)
    bg.alpha_composite(ped, (S(130) - ped.width // 2, S(PET_FEET) - round(ped.height * 0.42)))
    ImageDraw.Draw(bg).rectangle([0, S(456), W, H], fill=(0, 0, 0))

    sp = {}
    for name in ('tab_chon', 'tab_thuong', 'tab_cham-do'):
        sp[name] = nine(name, 132, 32 if name != 'tab_cham-do' else 34, s, 10)
    sp['bar'] = piece('thanh_khung', s, 0.96)
    for col in ('cam', 'hong', 'xanh-duong', 'xanh-reu', 'do', 'tim', 'vang'):
        sp['fill_' + col] = piece('thanh_fill_' + col, s, 0.96)
    for icon, _ in SURVIVAL_LOOK + ATTRIBUTE_LOOK:
        sp[icon] = piece(icon, s, 1.5)
    radar = piece('linh-khi_ngu-giac', s, 1.1, clean=True)
    sp['radar'] = radar
    for key, *_ in RADAR:
        sp['he_' + key] = piece('he_' + key, s, 1.1)
    # profile page: the cards never move, so they are one picture
    cards = Image.new('RGBA', (S(344), S(364)))
    for x, y, w, h in ((0, 0, 344, 70), (0, 78, 168, 64), (176, 78, 168, 64), (0, 150, 168, 64),
                       (176, 150, 168, 64), (0, 222, 344, 64), (0, 294, 344, 64)):
        cards.alpha_composite(nine('the-thong-tin', w, h, s, 9), (S(x), S(y)))
    sp['cards'] = cards
    sp['badge'] = piece('level_huy-hieu', s, 1.3)
    sp['exp_bar'] = nine('thanh_khung', 150, 16, s, 8)
    sp['exp_fill'] = nine('thanh_fill_vang', 150, 14, s, 8)
    sp['personality'] = piece('tinh-cach_' + PET['personality'][0], s, 1.5)
    for h in ('tim-day', 'tim-nua', 'tim-rong'):
        sp[h] = piece('icon_' + h, s, 0.8)
    sp['icon_tim-day_big'] = piece('icon_tim-day', s, 1.5)
    sp['likes'] = food_icon(PET['likes'][0], S(34))
    sp['dislikes'] = food_icon(PET['dislikes'][0], S(34))
    sp['weight_bar'] = piece('the-trang_thanh', s, 1.5)
    sp['weight_mark'] = piece('the-trang_kim', s, 1.3)
    sp['icon_nha'] = piece('icon_nha', s, 1.5)
    sp['gem_frame'] = nine('the-thong-tin', 204, 38, s, 9)
    sp['socket'] = cat_img('o-kham_trong', S(31))
    for g in PET['gems']:
        if g:
            sp[f'gem_{g[0]}_{g[1]}'] = gem_img(*g, S(19))
    glyphs = glyph_set(STYLES, s)
    return bg.convert('RGB'), sp, glyphs


def pack_ui(bg, sprites, glyphs):
    """'HLPU' u8 version u8 colours u16 sprites u16 glyphs u16 w u16 h u32 bg_len, RGB565 RLE bg,
    palette, sprites {name, u16 w, u16 h, u32 len, rows}, glyphs {u8 size, utf-8 char, u8 advance,
    u8 w, u8 h, u32 len, rows}. Glyphs are 1 colour: drawn in the colour the game asks for."""
    # gems are tiny next to the frames: count them several times so their colours get palette slots
    gems = [im for n, im in sprites.items() if n.startswith('gem_')]
    cols, pal = pak.make_palette(list(sprites.values()) + gems * 8)
    out = io.BytesIO()
    b = pak.rle565(bg)
    out.write(b'HLPU' + struct.pack('<BBHHHHI', 1, len(cols), len(sprites), len(glyphs), *bg.size, len(b)) + b)
    pak.write_palette(out, cols)
    for name, im in sprites.items():
        rows = pak.rle_rows(pak.index_image(im, pal, len(cols)))
        nb = name.encode()
        out.write(struct.pack('<B', len(nb)) + nb + struct.pack('<HHI', im.width, im.height, len(rows)) + rows)
    for (style, ch), (im, adv) in glyphs.items():
        idx = (np.array(im)[..., 3] >= 128).astype(np.int16)
        rows = pak.rle_rows(idx)
        cb = ch.encode()
        out.write(struct.pack('<BB', STYLES.index(style), len(cb)) + cb + struct.pack('<BBBI', adv, im.width, im.height, len(rows)) + rows)
    return out.getvalue()


def read_ui(data):
    _, ver, ncol, nsp, ngl, w, h, bl = struct.unpack_from('<4sBBHHHHI', data, 0)
    p = 4 + struct.calcsize('<BBHHHHI')
    bg = pak.unrle565(data, p, w, h)
    p += bl
    palette, p = pak.read_palette(data, p, ncol)
    sprites, glyphs = {}, {}
    for _ in range(nsp):
        nl = data[p]; name = data[p + 1:p + 1 + nl].decode(); p += 1 + nl
        sw, sh, ln = struct.unpack_from('<HHI', data, p); p += 8
        sprites[name] = pak.unrle_rows(data[p:p + ln], sw, sh); p += ln
    for _ in range(ngl):
        size, cl = data[p], data[p + 1]; ch = data[p + 2:p + 2 + cl].decode(); p += 2 + cl
        adv, gw, gh, ln = struct.unpack_from('<BBBI', data, p); p += 7
        glyphs[(STYLES[size], ch)] = (pak.unrle_rows(data[p:p + ln], gw, gh), adv); p += ln
    return dict(bg=bg, palette=np.array([(0, 0, 0)] + palette[1:], np.uint8), sprites=sprites, glyphs=glyphs)


# ---------------- drawing (device side: only what read_ui / read_creature give) ----------------

class Screen:
    def __init__(self, ui, pet, s):
        self.ui, self.pet, self.s = ui, pet, s
        self.px = ui['bg'].copy()

    def S(self, v):
        return round(v * self.s)

    def sprite(self, name, x, y, clip_w=None):
        idx = self.ui['sprites'][name]
        if clip_w is not None:
            idx = idx[:, :max(0, clip_w)]
        self.blit(idx, self.ui['palette'], x, y)

    def blit(self, idx, lut, x, y, mono=None):
        h, w = idx.shape
        H, W = self.px.shape[:2]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        part = idx[y0 - y:y1 - y, x0 - x:x1 - x]
        m = part > 0
        self.px[y0:y1, x0:x1][m] = mono if mono is not None else lut[part[m]]

    def text(self, s, x, y, size, colour, align='left'):
        width = sum(self.ui['glyphs'][(size, ch)][1] for ch in s)
        x = x - width if align == 'right' else x - width // 2 if align == 'center' else x
        for ch in s:
            idx, adv = self.ui['glyphs'][(size, ch)]
            self.blit(idx, None, x, y, mono=np.array(colour, np.uint8))
            x += adv

    def bar(self, x, y, fill, value, sprite='bar', fill_sprite=None):
        """Empty frame, then the full bar cut at value% between its two end ornaments."""
        self.sprite(sprite, x, y)
        fs = fill_sprite or 'fill_' + fill
        w = self.ui['sprites'][fs].shape[1]
        cap = round(w * 0.085)
        self.sprite(fs, x, y + (self.ui['sprites'][sprite].shape[0] - self.ui['sprites'][fs].shape[0]) // 2,
                    cap + round((w - 2 * cap) * value / 100))

    def pet_frame(self, frame, cx, feet, lift=0, br=0):
        """lift: whole body up (px); br: upper body up (down when negative) over the waist row,
        the waist row repeated to fill the gap - the same 'breathing' as the animation previews."""
        P = self.pet
        fr = P['frames'][frame]
        k = 1 if self.s <= 0.5 else 2           # the creature files are made for 320x240
        idx = fr['idx'] if k == 1 else np.repeat(np.repeat(fr['idx'], 2, 0), 2, 1)
        ax, ay = P['anchor']
        x, y = cx - (ax - fr['dx'] - fr['x']) * k, feet - (ay - fr['y']) * k - lift
        waist = max(1, (ay - round(P['canvas'][1] * 0.4) - fr['y']) * k)   # rows above it move with br
        br *= k
        if br == 0 or waist >= idx.shape[0]:
            self.blit(idx, P['lut'], x, y)
            return
        self.blit(idx[waist:], P['lut'], x, y + waist)
        for i in range(max(0, br)):
            self.blit(idx[waist - 1:waist], P['lut'], x, y + waist - 1 - i)
        top = idx[max(0, -br):waist] if br < 0 else idx[:waist]
        self.blit(top, P['lut'], x, y - br + max(0, -br))


def draw_page(sc, page, pet):
    S, t = sc.S, sc.text
    alert = any(v < 20 for _, v in PET['survival'])
    for i, name in enumerate(PAGES):
        x = S([42, 182, 324, 466][i])
        tab = 'tab_chon' if i == page else 'tab_cham-do' if (i == 0 and alert) else 'tab_thuong'
        sc.sprite(tab, x, S(4) if tab == 'tab_cham-do' else S(5))
        t(name, x + S(66), S(12), 'tab', (255, 245, 225) if i == page else MUTED, 'center')
    frame, _, y, br = pet[:4]
    sc.pet_frame(frame, S(130), S(PET_FEET), lift=-round(y), br=round(br))
    t(PET['name'], S(130), S(410), 'name', TEXT, 'center')
    cname = creatures.CREATURES[PET['creature']]['name']
    t(f"{cname} · {creatures.STAGE_NAMES[PET['stage']]}", S(130), S(432), 'sub', MUTED, 'center')
    fy = sc.px.shape[0] - sc.ui['glyphs'][('small', 'L')][0].shape[0]     # footer line, bottom-aligned
    t({3: 'A: đổi tên · B: quay lại', 2: 'A: khảm ngọc · B: quay lại'}.get(page, 'B: quay lại'), S(632), fy,
      'small', MUTED, 'right')
    t('L/R: đổi trang', S(8), fy, 'small', MUTED)

    if page == 2:                      # the gem sockets: a framed row above the pet
        fr = sc.ui['sprites']['gem_frame']
        sc.sprite('gem_frame', S(28), S(58))
        so = sc.ui['sprites']['socket']
        for (cx, cy), g in zip(SOCKETS, PET['gems']):
            sc.sprite('socket', S(cx) - so.shape[1] // 2, S(cy) - so.shape[0] // 2)
            if LIVE:
                continue
            if g:
                gi = sc.ui['sprites'][f'gem_{g[0]}_{g[1]}']
                sc.sprite(f'gem_{g[0]}_{g[1]}', S(cx) - gi.shape[1] // 2, S(cy) - gi.shape[0] // 2)
            else:
                t('+', S(cx), S(cy) - S(11), 'value', MUTED, 'center')
    if page in (0, 2):
        rows = PET['survival'] if page == 0 else PET['attributes']
        look = SURVIVAL_LOOK if page == 0 else ATTRIBUTE_LOOK
        top, step = (122, 60) if page == 0 else (110, 54)
        bonus = gem_bonus(PET['gems']) if page == 2 else [0] * len(rows)
        for i, ((label, value), (icon, colour)) in enumerate(zip(rows, look)):
            yc = S(top + step * i)
            ic = sc.ui['sprites'][icon]
            sc.sprite(icon, S(292) - ic.shape[1] // 2, yc - ic.shape[0] // 2)
            t(label, S(320), yc - S(27), 'label', TEXT)
            bh = sc.ui['sprites']['bar'].shape[0]
            if page == 2 and LIVE:
                sc.sprite('bar', S(318), yc - bh // 2 + S(2))
                continue
            sc.bar(S(318), yc - bh // 2 + S(2), colour, min(100, value + bonus[i]))
            t(str(value + bonus[i]), S(612), yc - S(9) - (S(7) if bonus[i] else 0), 'value', TEXT, 'right')
            if bonus[i]:
                t(f'+{bonus[i]}', S(612), yc + S(8), 'small', GREEN, 'right')
    elif page == 1:
        rd = sc.ui['sprites']['radar']
        rx, ry = S(450) - rd.shape[1] // 2, S(78)
        sc.sprite('radar', rx, ry)
        cx, cy = rx + rd.shape[1] / 2, ry + rd.shape[0] * 0.535
        R = rd.shape[0] * 0.44                # centre to corner circle
        r_max = R * 0.80                      # a value of 100
        corners = [(cx + R * math.sin(math.radians(72 * k)), cy - R * math.cos(math.radians(72 * k))) for k in range(5)]
        pts = [(cx + r_max * PET['linh_khi'][key] / 100 * math.sin(math.radians(72 * k)),
                cy - r_max * PET['linh_khi'][key] / 100 * math.cos(math.radians(72 * k)))
               for k, (key, *_) in enumerate(RADAR)]
        # the value shape: a solid fill and a light outline (no transparency on the device)
        mask = Image.new('L', (sc.px.shape[1], sc.px.shape[0]))
        ImageDraw.Draw(mask).polygon(pts, fill=255)
        m = np.array(mask) > 0
        sc.px[m] = (205, 112, 78)
        edge = Image.new('L', mask.size)
        ImageDraw.Draw(edge).line(pts + [pts[0]], fill=255, width=max(1, S(2)))
        sc.px[np.array(edge) > 0] = (250, 178, 128)
        for k, (key, name, colour) in enumerate(RADAR):
            ex, ey = corners[k]
            he = sc.ui['sprites']['he_' + key]
            sc.sprite('he_' + key, round(ex) - he.shape[1] // 2, round(ey) - he.shape[0] // 2)
            label = f"{name} {PET['linh_khi'][key]}"
            dx, dy = [(0, -S(36)), (S(26), -S(14)), (S(12), S(22)), (-S(12), S(22)), (-S(26), -S(14))][k]
            align = ['center', 'left', 'left', 'right', 'right'][k]
            t(label, round(ex) + dx, round(ey) + dy, 'label', colour, align)
        t('Vòng nét đứt = ngưỡng tiến hóa', S(450), S(408), 'small', MUTED, 'center')
    else:
        ox, oy = S(276), S(58)
        sc.sprite('cards', ox, oy)
        b = sc.ui['sprites']['badge']
        sc.sprite('badge', ox + S(12), oy + S(35) - b.shape[0] // 2)
        t(str(PET['level']), ox + S(12) + b.shape[1] // 2, oy + S(23), 'big', TEXT, 'center')
        t('Cấp độ', ox + S(76), oy + S(14), 'small', MUTED)
        t(f"Level {PET['level']}", ox + S(76), oy + S(32), 'value', TEXT)
        e, emax = PET['exp']
        t(f'EXP {e}/{emax}', ox + S(330), oy + S(14), 'small', MUTED, 'right')
        sc.bar(ox + S(178), oy + S(38), None, 100 * e / emax, 'exp_bar', 'exp_fill')
        # Tính cách / Thân thiết
        sc.sprite('personality', ox + S(10), oy + S(92))
        t('Tính cách', ox + S(52), oy + S(88), 'small', MUTED)
        t(PET['personality'][1], ox + S(52), oy + S(106), 'label', TEXT)
        sc.sprite('icon_tim-day_big', ox + S(186), oy + S(92))
        t('Thân thiết', ox + S(228), oy + S(88), 'small', MUTED)
        hw = sc.ui['sprites']['tim-day'].shape[1]
        for i in range(5):
            sc.sprite('tim-day' if i < PET['closeness'] else 'tim-rong', ox + S(228) + i * (hw + S(2)), oy + S(108))
        # Thích / Ghét
        for col, key, title in ((0, 'likes', 'Thích'), (176, 'dislikes', 'Ghét')):
            ic = sc.ui['sprites'][key]
            sc.sprite(key, ox + S(col + 26) - ic.shape[1] // 2, oy + S(182) - ic.shape[0] // 2)
            t(title, ox + S(col + 52), oy + S(160), 'small', MUTED)
            t(PET[key][1], ox + S(col + 52), oy + S(178), 'label', TEXT)
        # Thể trạng
        lo, hi = PET['weight_range']
        t(f"Thể trạng · {PET['weight']}kg", ox + S(14), oy + S(230), 'small', MUTED)
        wb = sc.ui['sprites']['weight_bar']
        bx, by = ox + S(24), oy + S(258)
        sc.sprite('weight_bar', bx, by)
        mk = sc.ui['sprites']['weight_mark']
        mx = bx + round(wb.shape[1] * (PET['weight'] - lo) / (hi - lo))
        sc.sprite('weight_mark', mx - mk.shape[1] // 2, by + wb.shape[0] // 2 - mk.shape[0] // 2)
        t('Gầy · Vừa · Mập', ox + S(330), oy + S(258), 'small', MUTED, 'right')
        # Nhà
        sc.sprite('icon_nha', ox + S(10), oy + S(306))
        t('Nhà', ox + S(52), oy + S(302), 'small', MUTED)
        t(PET['home'][0], ox + S(52), oy + S(320), 'label', TEXT)
        t(PET['home'][1], ox + S(330), oy + S(316), 'label', GREEN, 'right')


def run(target):
    s = TARGETS[target]
    bg, sprites, glyphs = build(target)
    ui_bytes = pack_ui(bg, sprites, glyphs)
    pet_bytes = pak.pack_creature(PET['creature'], PET['stage'])
    os.makedirs(pak.PAK_DIR, exist_ok=True)
    with open(os.path.join(pak.PAK_DIR, f'ui-stats_{target}.pak'), 'wb') as fh:
        fh.write(ui_bytes)
    ui = read_ui(ui_bytes)
    P = pak.read_creature(pet_bytes)
    P['lut'] = np.array([(0, 0, 0)] + P['palette'][1:], np.uint8)
    anims = json.load(open(creatures.anims_path(PET['creature'], PET['stage']), encoding='utf-8'))
    idle = samples(BOUNCE)
    tmp = tempfile.mkdtemp()
    n = 0
    shown = {}
    per_page = round(3000 / STEP)
    for page in range(4):
        for i in range(per_page):
            sc = Screen(ui, P, s)
            draw_page(sc, page, idle[n % len(idle)])
            img = Image.fromarray(sc.px)
            if i == 0:
                shown[page] = img
                img.save(os.path.join(OUT, f'{target}_{page + 1}.png'))
            img.resize((640, 480), Image.NEAREST).save(os.path.join(tmp, f'{n:05d}.png'))
            n += 1
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-framerate', str(round(1000 / STEP)),
                    '-i', os.path.join(tmp, '%05d.png'), '-vf', 'format=yuv420p', '-c:v', 'libx264',
                    '-crf', '16', '-movflags', '+faststart', os.path.join(OUT, f'{target}.mp4')], check=True)
    ram = len(ui_bytes) + len(pet_bytes) + bg.width * bg.height * 2
    print(f'{target}: ui pak {len(ui_bytes) / 1024:.0f} KB, pet pak {len(pet_bytes) / 1024:.0f} KB, '
          f'RAM about {ram / 1024:.0f} KB; {len(sprites)} sprites, {len(glyphs)} glyphs')
    return shown, len(ui_bytes)


def main():
    os.makedirs(OUT, exist_ok=True)
    targets = sys.argv[1:] or BUILD
    shots = {t: run(t)[0] for t in targets}
    for page in range(4):
        mock = Image.open(os.path.join(UI, 'mau', f'mau-{page + 1}.png')).convert('RGB').resize((640, 480))
        row = Image.new('RGB', (640 * 3 + 20, 480 + 24), (0, 0, 0))
        d = ImageDraw.Draw(row)
        shown = [('Mẫu', mock)] + [({'pocketgo': 'PocketGo 320x240 (phóng to 2 lần)', 'r36s': 'R36S 640x480'}[t],
                                    shots[t][page]) for t in targets]
        row = Image.new('RGB', (650 * len(shown) - 10, 480 + 24), (0, 0, 0))
        d = ImageDraw.Draw(row)
        for i, (label, im) in enumerate(shown):
            row.paste(im.resize((640, 480), Image.NEAREST), (i * 650, 24))
            d.text((i * 650 + 6, 4), label, fill=(255, 230, 160), font=ImageFont.truetype(FONT, 14))
        row.save(os.path.join(OUT, f'so-sanh_{page + 1}.png'))


if __name__ == '__main__':
    main()
