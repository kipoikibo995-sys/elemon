"""Demo of the main pet-room screen for the R36S (640x480), like ui/man-hinh-mau/thu-phong-nuoi-hud.png:
a furnished room, the pet living in it, the top HUD (4 needs, coins, level), the action menu, the food
picker that opens on "Cho ăn", the shop, and a scripted half minute of play:
hungry -> pick a food -> eat -> clean up -> play -> walk about -> shop (buy, switch tab) -> lights out.

Everything is built from the asset folders (rooms, room items, HUD and shop pieces cut by
cut_ui_sheets.py, food icons, creatures-640 frames made with HOLUA_SCREEN=640) and drawn with
transparency, as SDL2 on the R36S can. Writes preview/demo/<room>_<creature>-<stage>.mp4 and a still
per screen.
Usage: python demo_phong_nuoi.py
"""
import json, math, os, random, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

os.environ.setdefault('HOLUA_SCREEN', '640')
import creatures
from preview_anims import STEP, samples, breathe
from preview_decor_room import EMPTY, MANUAL, flat
from preview_ui_stats import nine as ui_nine

ROOT = creatures.ROOT
SRC = os.path.join(ROOT, 'assets', 'source')
UI = os.path.join(SRC, 'ui')
OUT = os.path.join(ROOT, 'preview', 'demo')
W, H = 640, 480
K = W / 1448                                  # room source px -> screen px
FONT_B = 'C:/Windows/Fonts/tahomabd.ttf'
FONT_R = 'C:/Windows/Fonts/tahoma.ttf'
TEXT = (240, 228, 206)
MUTED = (186, 160, 128)
GOLD = (255, 214, 120)
INK = (20, 10, 6)

ROOM = 'L1-HO_hang-da'
PET = dict(creature='hoa-ho', stage='child', name='Bông', level=12, coins=1250)
FEET = (320, 344)                             # where the pet stands (on the big rug)
WALK = (120, 520)                             # how far it walks left and right (feet x)
MENU = ['Cho ăn', 'Dọn dẹp', 'Chơi', 'Tập luyện', 'Ngủ', 'Cửa hàng', 'Trang trí', 'Ra ngoài']
MENU_ICON = ['nut_cho-an', 'nut_don-dep', 'nut_choi', 'nut_tap-luyen', 'nut_ngu', 'nut_cua-hang',
             'nut_trang-tri', 'nut_ra-ngoai']
NEEDS = [('icon_no', 'cam'), ('icon_vui', 'hong'), ('icon_sach', 'xanh-duong'), ('icon_nang-luong', 'xanh-reu')]
# the gentle bounce the user approved on the stats screen (320 px units, doubled here)
BOUNCE = {'loop': True, 'keys': [{'f': 'idle-0', 'ms': 300, 'br': -1}, {'f': 'idle-0', 'ms': 350, 'y': -1},
                                 {'f': 'idle-0', 'ms': 350, 'y': 0}, {'f': 'idle-0', 'ms': 300}]}

# the pet's bag: (food file, name, element, count, effect line). Later: from the save file.
BAG = [('Tho_7_golden-rice-ball', 'Cơm nắm vàng', 'Thổ', 5, 'No +30'),
       ('Tho_1_roasted-corn', 'Bắp nướng', 'Thổ', 1, 'No +20'),
       ('Hoa_1_roasted-chili-pepper', 'Ớt nướng', 'Hỏa', 3, 'No +10 · Năng lượng +15 · món thích'),
       ('Thuy_1_fresh-fish', 'Cá tươi', 'Thủy', 2, 'No +15 · Vui +10 · món ghét'),
       ('Moc_1_green-leaf-bundle', 'Bó lá non', 'Mộc', 4, 'No +10 · Sức khỏe +5'),
       ('Kim_1_iron-crunch-biscuit', 'Bánh quy sắt', 'Kim', 2, 'No +8 · Linh khí Kim +3')]
# shop shelves per tab: (icon path relative to assets/source, name, price, line 2, state)
SHOP_TABS = [('tab_do-an', 'Đồ ăn'), ('tab_trang-tri', 'Trang trí'), ('tab_thuoc', 'Thuốc'), ('tab_dac-biet', 'Đặc biệt')]
SHOP = {
    0: [('do-an/Hoa_1_roasted-chili-pepper.png', 'Ớt nướng', 20, 'Hỏa · No +10 · Năng lượng +15', ''),
        ('do-an/Hoa_2_grilled-meat-skewer.png', 'Xiên thịt nướng', 35, 'Hỏa · No +20', ''),
        ('do-an/Hoa_3_fire-apple.png', 'Táo lửa', 60, 'Hỏa · No +15 · Vui +10 · Linh khí Hỏa +3', ''),
        ('do-an/Hoa_5_charcoal-baked-sweet-potato.png', 'Khoai nướng than', 90, 'Hỏa · No +30 · Sức mạnh +1', ''),
        ('do-an/Thuy_1_fresh-fish.png', 'Cá tươi', 25, 'Thủy · No +15 · Vui +10', ''),
        ('do-an/Moc_5_forest-berry-basket.png', 'Giỏ quả rừng', 80, 'Mộc · No +20 · Sức khỏe +10', ''),
        ('do-an/Kim_6_golden-pear.png', 'Lê vàng', 120, 'Kim · No +20 · Bền bỉ +1', ''),
        ('do-an/Tho_7_golden-rice-ball.png', 'Cơm nắm vàng', 150, 'Thổ · No +30 · Linh khí Thổ +5', '')],
    2: [('do-an/DacBiet_1_healing-medicine-bottle.png', 'Thuốc chữa ốm', 80, 'Hết ốm ngay', ''),
        ('do-an/DacBiet_2_herbal-pill.png', 'Viên thảo dược', 40, 'Phòng ốm 1 ngày', ''),
        ('do-an/DacBiet_3_vitamin-candy.png', 'Kẹo vitamin', 30, 'Vui +15', ''),
        ('do-an/DacBiet_4_energy-drink.png', 'Nước tăng lực', 45, 'Năng lượng +30', ''),
        ('do-an/DacBiet_5_soap-bubble-bath.png', 'Xà phòng tắm', 25, 'Sạch +40', '')],
    3: [('do-an/DacBiet_6_toy-ball.png', 'Bóng đồ chơi', 70, 'Vui +20 mỗi lần chơi', ''),
        ('do-an/DacBiet_7_evolution-stone.png', 'Đá tiến hóa', 900, 'Cần Lv 20 để dùng', 'khoa'),
        ('do-an/DacBiet_8_spirit-soul-gem.png', 'Ngọc Hồn', 0, 'Chỉ rơi từ boss', 'khoa')],
}


def img(path, w=None, h=None, box=None):
    im = Image.open(path).convert('RGBA')
    if box:
        im = im.crop(im.getbbox())
        im.thumbnail(box, Image.LANCZOS)
        return im
    if w or h:
        if not h:
            h = round(im.height * w / im.width)
        if not w:
            w = round(im.width * h / im.height)
        im = im.resize((w, h), Image.LANCZOS)
    return im


def cat(name, w=None, h=None):
    return img(os.path.join(UI, 'cat', name + '.png'), w, h)


def goc(name, w=None, h=None):
    return img(os.path.join(UI, 'goc', name + '.png'), w, h)


def hslice(im, w, h, left, right):
    """Scales a horizontal piece to height h, keeps its two ends (fractions of its width) and stretches
    only the middle to width w - so the coin of a coin box stays round."""
    k = h / im.height
    src_l, src_r = round(im.width * left), round(im.width * (1 - right))
    L = im.crop((0, 0, src_l, im.height)).resize((max(1, round(src_l * k)), h), Image.LANCZOS)
    R = im.crop((src_r, 0, im.width, im.height)).resize((max(1, round((im.width - src_r) * k)), h), Image.LANCZOS)
    M = im.crop((src_l, 0, src_r, im.height)).resize((max(1, w - L.width - R.width), h), Image.LANCZOS)
    out = Image.new('RGBA', (w, h))
    out.alpha_composite(L, (0, 0)); out.alpha_composite(M, (L.width, 0)); out.alpha_composite(R, (w - R.width, 0))
    return out


def room_items():
    folder = os.path.join(SRC, 'do-theo-phong', ROOM)
    pos = json.load(open(os.path.join(folder, 'vi-tri.json'), encoding='utf-8'))
    pos.update(MANUAL.get(ROOM, {}))
    items = []
    for name, (x, y, s) in pos.items():
        im = Image.open(os.path.join(folder, name)).convert('RGBA')
        im = im.resize((max(1, round(im.width * s * K)), max(1, round(im.height * s * K))), Image.LANCZOS)
        X, Y = round(x * K), round(y * K)
        items.append(dict(name=name, img=im, x=X, y=Y, floor=-1 if flat(name) else Y + im.height))
    return items


class Pet:
    def __init__(self):
        fr = creatures.frames_dir(PET['creature'], PET['stage'])
        self.meta = json.load(open(os.path.join(fr, 'frames.json')))
        self.frames = {n: Image.open(os.path.join(fr, 'png', n + '.png')).convert('RGBA') for n in self.meta['frames']}
        self.anims = json.load(open(creatures.anims_path(PET['creature'], PET['stage']), encoding='utf-8'))
        ax, ay = self.meta['anchor']
        self.split = ay - round(self.meta['canvas'][1] * 0.4)

    def play(self, anim, ms):
        """(frame, x, y, br) samples for ms milliseconds; motion is kept in 320 units and doubled here."""
        a = self.anims[anim] if isinstance(anim, str) else anim
        one = [(f, x * 2, y * 2, br * 2) for f, x, y, br, *_ in samples(a)]
        n = max(1, round(ms / STEP))
        return [one[i % len(one)] if a['loop'] else one[min(i, len(one) - 1)] for i in range(n)]

    def image(self, f, br, left):
        im = breathe(self.frames[f], round(br), self.split)
        return im.transpose(Image.FLIP_LEFT_RIGHT) if left else im

    def place(self, f, im, feet_x, feet_y, left):
        ax, ay = self.meta['anchor']
        # walking frames are not aligned: the legs move on purpose (see align_frames.py)
        dx = 0 if f.startswith('walk') else self.meta['align'].get(f, [0, 0])[0]
        x = feet_x - (im.width - ax) - dx if left else feet_x - ax + dx
        return x, feet_y - ay


def shadow(w):
    sh = Image.new('RGBA', (w, 12))
    ImageDraw.Draw(sh).ellipse([0, 2, w - 1, 10], fill=(0, 0, 0, 90))
    return sh


# ---------------- the script ----------------

def script(pet):
    """The demo, one entry per video frame: what the pet does and what the screen shows."""
    st = dict(no=22, vui=45, sach=35, nl=40, coins=PET['coins'], cursor=0, press=-1, bubble='bong_doi',
              dirty=True, night=0.0, eating=None, sparkle=0, hearts=0, zs=0, screen='room',
              panel=0.0, pick=0, bag=[b[3] for b in BAG], tab=0, item=0, bought=0, fade=0.0, buy_press=False,
              x=FEET[0])
    timeline = []

    def hold(ms, pet_samples=None, x=None, left=False, **changes):
        frames = pet_samples or pet.play(BOUNCE, ms)
        n = len(frames)
        start = dict(st)
        for i, (f, ox, oy, br) in enumerate(frames):
            t = (i + 1) / n
            s = dict(start)
            for k, v in changes.items():
                num = isinstance(v, (int, float)) and not isinstance(v, bool) and isinstance(start[k], (int, float))
                s[k] = start[k] + (v - start[k]) * t if num else v
            px = (x(t) if callable(x) else st['x']) + ox
            timeline.append(dict(s, frame=f, px=px, py=FEET[1] + oy, br=br, left=left, bag=list(st['bag'])))
        st.update(changes)

    def step(key, to, ms=260):
        while st[key] != to:
            st[key] += 1 if to > st[key] else -1
            hold(ms)

    def press(key='press', value=None, ms=200):
        st[key] = st['cursor'] if value is None else value
        hold(ms)
        st[key] = -1 if value is None else False

    hold(2200)                                                   # hungry, a fly over the mess
    press()
    hold(300, panel=1.0)                                         # the food picker slides up
    hold(500)
    step('pick', 2, 380)                                         # -> Ớt nướng, the pet's favourite
    hold(700)
    st['bag'][2] -= 1
    hold(250, panel=0.0)
    st['eating'] = BAG[2][0]
    hold(2600, pet.play('eat', 2600), no=58, nl=62)               # eats the chilli
    st['eating'] = None
    st['bubble'] = 'bong_tim'
    hold(900)
    step('cursor', 1)
    press()
    st['sparkle'] = 1
    hold(1300, sach=96)                                          # sweeps: bubbles and sparkles
    st.update(sparkle=0, dirty=False, bubble=None)
    hold(600)
    step('cursor', 2)
    press()
    st['hearts'] = 1
    st['bubble'] = 'bong_vui'
    hold(2400, pet.play('happy', 2400), vui=92)                 # plays
    st.update(hearts=0, bubble=None)
    hold(400)
    for x0, x1 in ((FEET[0], WALK[1]), (WALK[1], WALK[0]), (WALK[0], FEET[0])):   # walks about
        ms = abs(x1 - x0) / 70 * 1000
        hold(ms, pet.play('walk', ms), x=lambda t, x0=x0, x1=x1: x0 + (x1 - x0) * t, left=x1 < x0)
    hold(300)
    step('cursor', 5)
    press()
    hold(300, fade=1.0)                                          # into the shop
    st['screen'] = 'shop'
    hold(300, fade=0.0)
    hold(800)
    step('item', 2, 330)                                         # -> Táo lửa
    hold(900)
    press('buy_press', True, 220)
    st['bought'] = 1
    hold(900, coins=st['coins'] - SHOP[0][2][2])                 # coins count down
    st['bought'] = 0
    hold(500)
    st.update(tab=1, item=0)                                     # L/R: the decor shelf
    hold(2200)
    st.update(tab=2, item=3)                                     # medicine
    hold(1600)
    hold(300, fade=1.0)                                          # B: back to the room
    st['screen'] = 'room'
    hold(300, fade=0.0)
    step('cursor', 4)
    press()
    st['zs'] = 1
    st['bubble'] = 'bong_buon-ngu'
    hold(1200, pet.play('sleep', 1200), night=0.62)              # lights out
    st['bubble'] = None
    hold(3200, pet.play('sleep', 3200), nl=80)
    return timeline


# ---------------- drawing ----------------

class Art:
    """Every picture of the demo at screen size, made once."""

    def __init__(self, pet):
        self.room = Image.open(EMPTY[ROOM]).convert('RGBA').resize((W, H), Image.LANCZOS)
        self.items = room_items()
        self.icons = {n: goc(n, 22) for n, _ in NEEDS}
        self.bar = goc('thanh_khung', 74, 12)
        self.fills = {c: goc('thanh_fill_' + c, 74, 10) for _, c in NEEDS}
        self.coin_box = hslice(cat('o_tien'), 112, 30, 0.40, 0.12)
        self.badge = cat('huy-hieu_lv', 32)
        self.buttons = [cat(n, 50, 50) for n in MENU_ICON]
        self.selected = cat('o_chon', 60, 60)
        self.bubbles = {n: cat(n, 46) for n in ('bong_doi', 'bong_vui', 'bong_tim', 'bong_buon-ngu')}
        self.poop = cat('phan_vua', 30)
        self.flies = [cat(f'ruoi_{i}', 22) for i in range(3)]
        self.stain = cat('ban_1', 46)
        self.crumbs = cat('vun-do-an', 30)
        self.sparkle = cat('lap-lanh', 26)
        self.soap = cat('bot_vua', 40)
        self.hearts = [cat('tim_nho', 14), cat('tim_vua', 18)]
        self.zs = [cat('z_nho', 12), cat('z_vua', 16), cat('z_to', 20)]
        self.shadow = shadow(round(pet.meta['canvas'][0] * 0.55))
        self.food = {b[0]: img(os.path.join(SRC, 'do-an', b[0] + '.png'), box=(38, 38)) for b in BAG}
        self.food_mouth = {b[0]: img(os.path.join(SRC, 'do-an', b[0] + '.png'), box=(30, 30)) for b in BAG}
        # food picker
        self.panel = ui_nine('khung_panel', 620, 118, 1.0, 22, mid=46, thin=0.55)
        self.slot = cat('o_hang', 56, 56)
        self.slot_sel = cat('o_hang-chon', 56, 56)
        # shop
        self.shop_bg = ui_nine('khung_panel', 640, 436, 1.0, 22, mid=46, thin=0.7)
        self.keeper = img(os.path.join(UI, 'cat', 'chu-quan.png'), 250)
        self.say = cat('bong_trong', 128)
        self.tabs = [cat(t, 40, 40) for t, _ in SHOP_TABS]
        self.tab_sel = cat('o_hang-chon', 48, 48)
        self.shelf_slot = cat('o_hang', 64, 64)
        self.shelf_sel = cat('o_hang-chon', 64, 64)
        self.shelf_lock = cat('o_hang-khoa', 64, 64)
        self.price = hslice(cat('nhan-gia'), 78, 24, 0.27, 0.10)
        self.desc = ui_nine('khung_panel', 364, 104, 1.0, 22, mid=46, thin=0.5)
        self.buy = hslice(cat('nut_mua'), 120, 32, 0.15, 0.15)
        self.sell = hslice(cat('nut_ban'), 120, 32, 0.15, 0.15)
        self.arrows = (cat('mui-ten_len', 22), cat('mui-ten_xuong', 22))
        self.shelf_icons = {}
        for tab, rows in SHOP.items():
            for path, *_ in rows:
                self.shelf_icons[path] = img(os.path.join(SRC, path), box=(44, 44))
        # decor tab: this room's own items
        folder = os.path.join(SRC, 'do-theo-phong', ROOM)
        self.decor = [(n, img(os.path.join(folder, n), box=(46, 46))) for n in sorted(os.listdir(folder))
                      if n.endswith('.png')][:8]
        self.f = {k: ImageFont.truetype(p, s) for k, (p, s) in dict(
            label=(FONT_B, 14), num=(FONT_B, 15), lv=(FONT_B, 13), small=(FONT_R, 12), title=(FONT_B, 18),
            name=(FONT_B, 16), body=(FONT_R, 13), count=(FONT_B, 12), price=(FONT_B, 13)).items()}


def text(d, xy, s, font, fill=TEXT, anchor='la', stroke=0):
    d.text(xy, s, font=font, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=INK)


def draw_top(scr, A, s, title=None):
    scr.alpha_composite(Image.new('RGBA', (W, 38), (18, 11, 9, 225)), (0, 0))
    d = ImageDraw.Draw(scr)
    if title:
        text(d, (14, 9), title, A.f['title'], GOLD)
    else:
        for i, ((icon, col), key) in enumerate(zip(NEEDS, ('no', 'vui', 'sach', 'nl'))):
            x = 8 + i * 104
            scr.alpha_composite(A.icons[icon], (x, 8))
            scr.alpha_composite(A.bar, (x + 26, 13))
            fw = round(4 + (A.fills[col].width - 8) * s[key] / 100)
            scr.alpha_composite(A.fills[col].crop((0, 0, fw, A.fills[col].height)), (x + 26, 14))
    scr.alpha_composite(A.coin_box, (444, 4))
    text(d, (548, 19), f"{round(s['coins']):,}", A.f['num'], anchor='rm')
    text(d, (566, 19), 'Lv', A.f['lv'], anchor='lm')
    scr.alpha_composite(A.badge, (596, 3))
    text(d, (612, 19), str(PET['level']), A.f['lv'], anchor='mm')


def draw_room(scr, A, s, k, rnd):
    poop_at, stain_at = (450, 296), (232, 386)
    layers = [(it['floor'], 'item', it) for it in A.items]
    if s['dirty']:
        layers += [(stain_at[1] - 50, 'stain', None), (poop_at[1] + A.poop.height, 'poop', None)]
    layers.append((s['py'], 'pet', None))
    for _, kind, it in sorted(layers, key=lambda t: t[0]):
        if kind == 'item':
            scr.alpha_composite(it['img'], (it['x'], it['y']))
        elif kind == 'stain':
            scr.alpha_composite(A.stain, stain_at)
        elif kind == 'poop':
            scr.alpha_composite(A.poop, poop_at)
        else:
            lift = max(0, FEET[1] - s['py'])
            w = max(10, int(A.shadow.width * (1 - lift / 60)))
            scr.alpha_composite(A.shadow.resize((w, A.shadow.height)), (round(s['px']) - w // 2, FEET[1] - 6))
            im = pet.image(s['frame'], s['br'], s['left'])
            scr.alpha_composite(im, pet.place(s['frame'], im, round(s['px']), round(s['py']), s['left']))
            head = (round(s['px']) + 30, round(s['py']) - im.height + 10)
            if s['bubble']:
                scr.alpha_composite(A.bubbles[s['bubble']], (head[0], head[1] - 40 + round(2 * math.sin(k / 6))))
            if s['eating']:
                bite = 1 - 0.5 * ((k % 24) / 24)              # the food gets smaller as it is eaten
                f = A.food_mouth[s['eating']]
                f = f.resize((max(1, round(f.width * bite)), max(1, round(f.height * bite))))
                scr.alpha_composite(f, (round(s['px']) + 26, FEET[1] - 26))
                if k % 8 < 4:
                    scr.alpha_composite(A.crumbs, (round(s['px']) + 18, FEET[1] - 8))
            if s['hearts']:
                for j in range(3):
                    ph = (k * 2 + j * 23) % 60
                    hx = round(s['px']) - 30 + j * 30 + round(4 * math.sin((k + j * 7) / 5))
                    scr.alpha_composite(A.hearts[j % 2], (hx, head[1] + 30 - ph))
    if s['dirty']:                                   # the fly circles the poop
        ang = k / 4
        scr.alpha_composite(A.flies[k % 3], (poop_at[0] + 6 + round(22 * math.cos(ang)),
                                             poop_at[1] - 10 + round(10 * math.sin(ang * 1.3))))
    if s['sparkle']:
        for j, (x, y) in enumerate((poop_at, stain_at)):
            scr.alpha_composite(A.soap, (x - 6 + rnd.randint(-2, 2), y - 8))
            if (k + j) % 6 < 3:
                scr.alpha_composite(A.sparkle, (x + 14, y - 18))
    if s['night'] > 0:                               # lights out: dark blue over the room
        scr.alpha_composite(Image.new('RGBA', (W, H), (8, 10, 40, round(255 * s['night']))))
    if s['zs']:
        for j in range(3):
            ph = (k + j * 18) % 54
            scr.alpha_composite(A.zs[j], (round(s['px']) + 34 + j * 10 + ph // 4, round(s['py']) - 70 - ph))
    if s['panel'] > 0:
        draw_food_picker(scr, A, s)
    draw_top(scr, A, s)
    # action menu
    scr.alpha_composite(Image.new('RGBA', (W, 66), (18, 11, 9, 230)), (0, H - 66))
    d = ImageDraw.Draw(scr)
    if s['panel'] == 0:
        text(d, (14, H - 88), MENU[s['cursor']], A.f['label'], stroke=2)
    for i, b in enumerate(A.buttons):
        cx = 40 + i * 80
        if i == s['cursor']:
            scr.alpha_composite(A.selected, (cx - 30, H - 63))
        scr.alpha_composite(b, (cx - 25, H - 58 + (2 if s['press'] == i else 0)))


def draw_food_picker(scr, A, s):
    """Slides up over the room when "Cho ăn" is pressed: the bag's food, how many of each, what it does."""
    y = round(H - 66 - A.panel.height * s['panel'])
    x = 10
    scr.alpha_composite(A.panel, (x, y))
    d = ImageDraw.Draw(scr)
    text(d, (x + 22, y + 10), 'Chọn món', A.f['label'], GOLD)
    text(d, (x + 598, y + 10), 'A: cho ăn · B: đóng', A.f['small'], MUTED, anchor='ra')
    for i, (file, name, he, _, _) in enumerate(BAG):
        sx, sy = x + 24 + i * 70, y + 30
        scr.alpha_composite(A.slot_sel if i == s['pick'] else A.slot, (sx, sy))
        f = A.food[file]
        scr.alpha_composite(f, (sx + 28 - f.width // 2, sy + 28 - f.height // 2))
        n = s['bag'][i]
        text(d, (sx + 52, sy + 52), f'x{n}', A.f['count'], TEXT if n else (230, 110, 90), anchor='rb', stroke=2)
    file, name, he, _, effect = BAG[s['pick']]
    text(d, (x + 452, y + 34), name, A.f['name'])
    text(d, (x + 452, y + 54), f'Hệ {he}', A.f['small'], MUTED)
    lines = effect.split(' · ')
    for j in range(0, len(lines), 2):
        text(d, (x + 452, y + 70 + j * 8), ' · '.join(lines[j:j + 2]), A.f['small'])


def draw_shop(scr, A, s, k):
    scr.paste((24, 14, 10, 255), (0, 0, W, H))
    scr.alpha_composite(A.shop_bg, (0, 40))
    scr.alpha_composite(A.keeper, (4, H - A.keeper.height - 30))
    scr.alpha_composite(A.say, (118, 150))
    d = ImageDraw.Draw(scr)
    line = 'Mua mấy món\nngon cho Bông\nnào!' if s['tab'] == 0 else 'Đồ trong phòng\nđủ bộ rồi đó!' if s['tab'] == 1 else 'Có thuốc phòng\nốm nè!'
    d.multiline_text((182, 200), line, font=A.f['small'], fill=(70, 40, 20), anchor='mm', align='center')
    draw_top(scr, A, s, title='Cửa hàng')
    for i, tab in enumerate(A.tabs):
        tx = 176 + i * 54
        if i == s['tab']:
            scr.alpha_composite(A.tab_sel, (tx - 4, -1))
        scr.alpha_composite(tab, (tx, 3))
    text(d, (W // 2 + 60, 58), SHOP_TABS[s['tab']][1], A.f['name'], GOLD, anchor='mt')
    # the shelf
    if s['tab'] == 1:
        rows = [(None, n.split('_', 1)[1][:-4].replace('-', ' ').capitalize(), 0, '', 'co') for n, _ in A.decor]
    else:
        rows = SHOP.get(s['tab'], [])
    for i, (path, name, price, info, state) in enumerate(rows):
        c, r = i % 4, i // 4
        sx, sy = 270 + c * 90, 84 + r * 104
        slot = A.shelf_lock if state == 'khoa' else A.shelf_sel if i == s['item'] else A.shelf_slot
        scr.alpha_composite(slot, (sx, sy))
        icon = A.decor[i][1] if s['tab'] == 1 else A.shelf_icons[path]
        if state != 'khoa':
            scr.alpha_composite(icon, (sx + 32 - icon.width // 2, sy + 32 - icon.height // 2))
        scr.alpha_composite(A.price, (sx - 7, sy + 68))
        tag = 'Đã có' if state == 'co' else '—' if not price else f'{price}'
        text(d, (sx + 66, sy + 80), tag, A.f['price'], anchor='rm')
        if s['bought'] and i == s['item']:
            scr.alpha_composite(A.sparkle, (sx + 40 + (k % 4), sy - 8))
    # description of the chosen thing
    scr.alpha_composite(A.desc, (264, 300))
    if s['tab'] == 1:
        text(d, (284, 318), 'Bộ đồ Hang đá', A.f['name'])
        text(d, (284, 342), 'Đã mua 16/16 món', A.f['body'], (140, 225, 110))
        text(d, (284, 362), 'Đủ bộ: mở nhà Lv2 trong mục Ra ngoài', A.f['body'])
    elif rows:
        path, name, price, info, state = rows[s['item']]
        text(d, (284, 318), name, A.f['name'])
        text(d, (284, 342), info, A.f['body'])
        owned = next((s['bag'][j] for j, b in enumerate(BAG) if b[1] == name), 0) + (1 if s['coins'] < PET['coins'] and name == 'Táo lửa' else 0)
        text(d, (284, 362), f'Trong túi: {owned}', A.f['body'], MUTED)
    scr.alpha_composite(A.sell, (264, 412))
    scr.alpha_composite(A.buy, (508, 412 + (2 if s['buy_press'] else 0)))
    text(d, (324, 428), 'Bán', A.f['label'], anchor='mm', stroke=2)
    text(d, (568, 428 + (2 if s['buy_press'] else 0)), 'Mua', A.f['label'], anchor='mm', stroke=2)
    text(d, (W - 10, H - 6), 'L/R: đổi mục · A: mua · B: quay lại', A.f['small'], MUTED, anchor='rb')


def main():
    global pet
    os.makedirs(OUT, exist_ok=True)
    pet = Pet()
    A = Art(pet)
    tl = script(pet)
    tmp = tempfile.mkdtemp()
    rnd = random.Random(4)
    stills = {}
    for k, s in enumerate(tl):
        scr = Image.new('RGBA', (W, H))
        if s['screen'] == 'room':
            scr.alpha_composite(A.room)
            draw_room(scr, A, s, k, rnd)
        else:
            draw_shop(scr, A, s, k)
        if s['fade'] > 0:
            scr.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, round(255 * s['fade']))))
        out = scr.convert('RGB')
        out.save(os.path.join(tmp, f'{k:05d}.png'))
        key = 'cua-hang' if s['screen'] == 'shop' and s['tab'] == 0 and s['item'] == 2 else \
              'chon-mon' if s['panel'] == 1.0 and s['pick'] == 2 else 'phong' if k == 40 else None
        if key and key not in stills:
            stills[key] = out
    base = f'{ROOM}_{PET["creature"]}-{PET["stage"]}'
    for key, im in stills.items():
        im.save(os.path.join(OUT, f'{base}_{key}.png'))
    video = os.path.join(OUT, base + '.mp4')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-framerate', str(round(1000 / STEP)), '-i',
                    os.path.join(tmp, '%05d.png'), '-vf', 'format=yuv420p', '-c:v', 'libx264', '-crf', '18',
                    '-movflags', '+faststart', video], check=True)
    print(video, len(tl), 'frames, stills:', ', '.join(stills))


if __name__ == '__main__':
    main()
