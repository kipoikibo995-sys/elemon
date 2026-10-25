"""Font test for Vietnamese text on the R36S (640x480) and PocketGo (320x240) screens.

Renders the same sentences with each candidate font (assets/source/font/_thu/) next to Tahoma (what the
demo uses now), on a dark panel and on a bright room, at the size each screen needs, pixel fonts at a whole
multiple of their own grid with no smoothing. Letters a font does not have are counted and listed.
Out: preview/font-test/so-sanh.png
Usage: python font_test.py
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, 'assets', 'source', 'font', '_thu')
OUT = os.path.join(ROOT, 'preview', 'font-test')
SENTENCES = ['Bông đói rồi! Hãy cho ăn ở bát đá.',
             'Tiến hóa · Huyền thoại · Thủy Cung · Ngủ ngon',
             'ễ ở ữ ặ ẩ ộ ừ ỡ Ạ Ế Ỗ Ữ Đ đ']
VIET = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ' \
       'ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ'
# name, file, (size on 640, size on 320), pixel font (no smoothing)
CANDIDATES = [
    ('Tahoma (đang dùng)', 'C:/Windows/Fonts/tahomabd.ttf', (16, 9), False),
    ('Silver', os.path.join(FONTS, 'silver', 'Silver.ttf'), (38, 19), True),
    ('FatPix VN', os.path.join(FONTS, 'fatpix', 'FatPix-VN-SVG.ttf'), (32, 16), True),
    ('GNU Unifont', os.path.join(FONTS, 'unifont', 'unifont-18.0.01.otf'), (16, 16), True),
]
FONT_UI = 'C:/Windows/Fonts/tahoma.ttf'


def missing(path, size):
    """Vietnamese letters the font draws as its 'no glyph' box (or not at all)."""
    f = ImageFont.truetype(path, size)
    grab = lambda ch: np.array(f.getmask(ch, mode='L')).tobytes()
    tofu = grab('\uE000')
    base = {ch: grab(ch) for ch in 'aeiouyAEIOUYd'}
    out = []
    for ch in VIET:
        m = grab(ch)
        # no glyph: empty, the font's box, or drawn exactly like its letter without the mark
        if not any(m) or m == tofu or m in base.values():
            out.append(ch)
    return out


def line(img, xy, text, path, size, pixel, colour=(255, 230, 168)):
    d = ImageDraw.Draw(img)
    if pixel:
        d.fontmode = '1'
    f = ImageFont.truetype(path, size)
    x, y = xy
    for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):      # 1 px dark edge, as the game would bake it
        d.text((x + ox, y + oy), text, font=f, fill=(26, 12, 6))
    d.text((x, y), text, font=f, fill=colour)
    return f.getbbox(text)


def panel(w, h, bright):
    if bright:
        room = os.path.join(ROOT, 'preview', 'tien-hoa', 'img', 'room_L4HO.png')
        if os.path.exists(room):
            return Image.open(room).convert('RGB').crop((0, 40, w, 40 + h)) if w <= 640 else Image.new('RGB', (w, h))
    return Image.new('RGB', (w, h), (40, 24, 16))


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    label = ImageFont.truetype(FONT_UI, 15)
    for name, path, (s640, s320), pixel in CANDIDATES:
        if not os.path.exists(path):
            continue
        miss = missing(path, s640)
        block = Image.new('RGB', (1300, 230), (14, 10, 8))
        d = ImageDraw.Draw(block)
        d.text((10, 6), f'{name}  ·  thiếu {len(miss)}/{len(VIET)} chữ Việt' + (f': {"".join(miss[:24])}' if miss else ''),
               font=label, fill=(255, 214, 120) if not miss else (240, 140, 120))
        # R36S: 640 wide, dark panel then the bright Đền Hỏa Long
        for j, bright in enumerate((False, True)):
            p = panel(640, 96, bright)
            for i, t in enumerate(SENTENCES):
                line(p, (8, 4 + i * (s640 + 8 if s640 < 30 else s640 - 6)), t, path, s640, pixel)
            block.paste(p, (10, 30 + j * 98))
        d.text((10, 226 - 4), '', font=label)
        # PocketGo: 320 wide shown 2x, so a pixel there is 2 pixels here
        p = panel(320, 96, False)
        for i, t in enumerate(SENTENCES[:2]):
            line(p, (4, 6 + i * (s320 + 6)), t, path, s320, True)
        block.paste(p.resize((640, 192), Image.NEAREST), (660, 30))
        d.text((660, 6 + 0), '', font=label)
        rows.append(block)
    head = Image.new('RGB', (1300, 30), (14, 10, 8))
    ImageDraw.Draw(head).text((10, 6), 'Trái: R36S 640×480 (nền tối, nền Đền Hỏa Long)   ·   Phải: PocketGo 320×240 phóng 2 lần',
                              font=label, fill=(220, 210, 190))
    sheet = Image.new('RGB', (1300, 30 + 230 * len(rows)), (14, 10, 8))
    sheet.paste(head, (0, 0))
    for i, r in enumerate(rows):
        sheet.paste(r, (0, 30 + i * 230))
    sheet.save(os.path.join(OUT, 'so-sanh.png'))
    print(os.path.join(OUT, 'so-sanh.png'))


if __name__ == '__main__':
    main()
