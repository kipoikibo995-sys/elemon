"""Builds preview/tien-hoa/: the pet room and the evolution screen running live in a browser, the way the R36S app will
run it (640x480, real time, buttons), for the first evolution Con -> Nhi of Hỏa Hổ.

Flow: room with the baby (Lv 5, EXP full) -> "ready to evolve" panel (A: evolve, B: later) ->
evolution scene (swirl of the pet's element, white-out, light pillar, flash, the child appears,
banner + what was gained) -> A -> back in the room with the child (Lv 6).
Keys: A = Enter / Space / Z, B = Esc / X / Backspace, R = start over. The page has the same buttons.

This writes the pictures at screen size (PNG) + data, and index.html with the game loop in JavaScript.
Usage: python build_evo_app.py      then open preview/tien-hoa/index.html through the preview server
"""
import json, os, shutil
import numpy as np
from PIL import Image

os.environ.setdefault('HOLUA_SCREEN', '640')
import creatures
from demo_phong_nuoi import (EMPTY, ROOM, MENU_ICON, NEEDS, BAG, SHOP, SHOP_TABS, cat, goc, hslice, room_items, img,
                              W, H)
from preview_ui_stats import nine as ui_nine
from preview_decor_room import MANUAL as DECOR_MANUAL, flat as decor_flat

OUT = os.path.join(creatures.ROOT, 'preview', 'tien-hoa')
SRC = os.path.join(creatures.ROOT, 'assets', 'source')
PET = dict(creature='hoa-ho', name='Bông', before='baby', after='child', element='hoa')
# every stage of the pet, to look at in the room (L2 on the test page switches); level shown for each
LEVELS = dict(baby=5, child=6, teen=21, adult=46, legend=100, adult4=46, legend4=100)
MAP = os.path.join(SRC, 'nen', 'ngoai-troi')
# Hang đá's own items, sold in the shop's Trang trí tab (prices are placeholders); bought ones show up in the room
# the homes (nen/README.md): Hang đá Lv1 to start with, then Lv2-Lv4 of every element; any element may be bought.
# key, decor room, name, tier, element, price (gold, or Ngọc Hồn for Lv4), feet x range
HE_NAME = {'HO': 'Hỏa', 'KI': 'Kim', 'MO': 'Mộc', 'TH': 'Thủy', 'TO': 'Thổ'}
HOME_NAMES = {2: {'HO': 'Hang bếp than', 'KI': 'Lán thợ mỏ', 'MO': 'Lều tranh', 'TH': 'Chòi chài', 'TO': 'Nhà vách đất'},
              3: {'HO': 'Lò rèn núi lửa', 'KI': 'Xưởng kim loại', 'MO': 'Chòi trên cây', 'TH': 'Nhà sàn bên hồ',
                  'TO': 'Nhà đất nung'},
              4: {'HO': 'Đền Hỏa Long', 'KI': 'Điện Kim Cương', 'MO': 'Cây Thần', 'TH': 'Thủy Cung', 'TO': 'Thạch Điện'}}
HOME_PRICE = {2: (3000, 'vang'), 3: (8000, 'vang'), 4: (1, 'ngoc')}
WALK = {'L2-HO': (150, 480), 'L3-HO': (150, 470), 'L4-HO': (180, 470)}
# Nhà hoang (the shabby Lv1 house) is where a new pet starts; Hang đá is the other Lv1 home, bought in the shop
HOUSES = [('L1', 'L1-HO_nha-hoang', 'Nhà hoang', 1, 'HO', 0, 'free', (150, 480)),
          ('L1HD', 'L1-HO_hang-da', 'Hang đá', 1, 'HO', 800, 'vang', (140, 500))]
for tier in (2, 3, 4):
    for he in ('HO', 'KI', 'MO', 'TH', 'TO'):
        price, paid = HOME_PRICE[tier]
        HOUSES.append((f'L{tier}{he}', f'L{tier}-{he}', HOME_NAMES[tier][he], tier, he, price, paid,
                       WALK.get(f'L{tier}-{he}', (160, 470))))
# Vietnamese names of the Lv2-Lv4 items (file name without .png -> name); prices from the tier (placeholders)
ITEM_NAMES = {
    'L1-HO_nha-hoang': {'01_old-wooden-bowl': 'Bát gỗ cũ', '02_torn-blanket-hay-bed': 'Ổ rơm chăn rách',
                        '03_cracked-lantern': 'Đèn lồng nứt', '04_broken-chair': 'Ghế gãy', '05_wooden-bucket': 'Xô gỗ',
                        '06_dusty-shelf': 'Kệ bụi', '07_small-rag-rug': 'Thảm giẻ', '08_potted-weed': 'Chậu cỏ dại',
                        '09_old-training-post': 'Cọc tập cũ', '10_cobweb-wall-hanging': 'Mạng nhện treo tường',
                        '11_broken-plank-pile': 'Đống ván gãy', '12_old-sack': 'Bao tải cũ'},
    'L2-HO': {'01_clay-food-bowl': 'Bát đất nung', '02_hay-bed-with-red-cloth': 'Ổ rơm phủ vải đỏ', '03_small-brazier': 'Lò than nhỏ',
              '04_wooden-stool': 'Ghế gỗ', '05_red-banner': 'Cờ lửa đỏ', '06_firewood-pile': 'Đống củi',
              '07_charcoal-bucket': 'Thùng than', '08_ember-lamp': 'Đèn than hồng', '09_red-cloth-rug': 'Thảm vải đỏ',
              '10_clay-pot': 'Hũ đất', '11_iron-poker-rack': 'Giá que cời', '12_fire-pattern-wall-hanging': 'Tranh hoa văn lửa'},
    'L2-KI': {'01_tin-food-bowl': 'Bát thiếc', '02_simple-cot': 'Giường gấp', '03_oil-lantern': 'Đèn dầu',
              '04_pickaxe-rack': 'Giá cuốc chim', '05_small-ore-cart': 'Xe goòng nhỏ', '06_metal-bucket': 'Xô sắt',
              '07_silver-ore-rock': 'Tảng quặng bạc', '08_tool-crate': 'Thùng đồ nghề', '09_grey-wool-rug': 'Thảm len xám',
              '10_wall-shelf-with-tools': 'Kệ đồ nghề', '11_anvil-block': 'Khối đe', '12_iron-wall-lamp': 'Đèn tường sắt'},
    'L2-MO': {'01_wooden-food-bowl': 'Bát gỗ', '02_leaf-mat-bed': 'Nệm lá', '03_potted-sapling': 'Chậu cây non',
              '04_tree-stump-stool': 'Ghế gốc cây', '05_woven-basket': 'Giỏ đan', '06_hanging-herb-bundle': 'Bó thảo dược',
              '07_mushroom-cluster': 'Cụm nấm', '08_bamboo-shelf': 'Kệ tre', '09_green-woven-rug': 'Thảm cói xanh',
              '10_flower-pot': 'Chậu hoa', '11_log-bench': 'Ghế khúc gỗ', '12_vine-wall-hanging': 'Dây leo treo tường'},
    'L2-TH': {'01_shell-food-bowl': 'Bát vỏ sò', '02_net-hammock-bed': 'Võng lưới', '03_fishing-rod-stand': 'Giá cần câu',
              '04_water-barrel': 'Thùng nước', '05_bucket-of-fish': 'Xô cá', '06_rope-coil': 'Cuộn dây thừng', '07_buoy': 'Phao',
              '08_small-wooden-boat-model': 'Mô hình thuyền gỗ', '09_blue-rag-rug': 'Thảm vải xanh', '10_hanging-net': 'Lưới treo',
              '11_lantern-on-post': 'Đèn cột', '12_seashell-pile': 'Đống vỏ sò'},
    'L2-TO': {'01_clay-food-bowl': 'Bát đất', '02_straw-mat-bed': 'Chiếu rơm', '03_clay-water-jar': 'Vò nước đất',
              '04_stone-stool': 'Ghế đá', '05_cactus-pot': 'Chậu xương rồng', '06_grain-sack': 'Bao lúa',
              '07_woven-sand-rug': 'Thảm cói màu cát', '08_clay-oven': 'Lò đất', '09_stone-shelf': 'Kệ đá',
              '10_tribal-wall-hanging': 'Tranh thổ cẩm', '11_small-rock-garden': 'Vườn đá nhỏ', '12_oil-lamp': 'Đèn dầu'},
    'L3-HO': {'01_iron-food-bowl': 'Bát sắt', '02_warm-stone-bed-with-red-blanket': 'Giường đá ấm', '03_anvil': 'Đe rèn',
              '04_small-furnace': 'Lò rèn nhỏ', '05_weapon-rack': 'Giá vũ khí', '06_red-banner': 'Cờ lửa',
              '07_lava-lamp': 'Đèn dung nham', '08_coal-bucket': 'Thùng than đá', '09_red-rug': 'Thảm đỏ',
              '10_iron-training-dummy': 'Hình nộm sắt', '11_armor-stand': 'Giá giáp', '12_fire-crystal-pedestal': 'Bệ pha lê lửa'},
    'L3-KI': {'01_steel-food-bowl': 'Bát thép', '02_padded-metal-cot': 'Giường sắt có đệm', '03_gear-clock': 'Đồng hồ bánh răng',
              '04_tool-bench': 'Bàn đồ nghề', '05_crystal-lamp': 'Đèn pha lê', '06_metal-crates': 'Thùng kim loại',
              '07_silver-rug': 'Thảm bạc', '08_steel-training-dummy': 'Hình nộm thép', '09_small-anvil': 'Đe nhỏ',
              '10_robot-arm-decor': 'Cánh tay máy', '11_glowing-crystal-cluster': 'Cụm pha lê sáng', '12_metal-bookshelf': 'Tủ sách sắt'},
    'L3-MO': {'01_carved-wooden-food-bowl': 'Bát gỗ chạm', '02_leaf-hammock-bed': 'Võng lá', '03_hanging-lantern': 'Đèn lồng treo',
              '04_bookshelf': 'Tủ sách', '05_potted-plant': 'Chậu cây', '06_mushroom-stool': 'Ghế nấm', '07_woven-green-rug': 'Thảm xanh',
              '08_log-training-dummy': 'Hình nộm gỗ', '09_flower-pots': 'Chậu hoa', '10_bird-house': 'Tổ chim',
              '11_tea-table': 'Bàn trà', '12_fern-in-carved-pot': 'Dương xỉ chậu chạm'},
    'L3-TH': {'01_shell-food-bowl': 'Bát vỏ sò', '02_reed-bed': 'Giường sậy', '03_fishing-rod-rack': 'Giá cần câu',
              '04_barrel': 'Thùng gỗ', '05_shell-lamp': 'Đèn vỏ sò', '06_aquarium-jar': 'Bể cá', '07_blue-wave-rug': 'Thảm sóng xanh',
              '08_rope-training-buoy': 'Phao tập', '09_conch-decor': 'Ốc xà cừ', '10_ship-wheel-wall-decor': 'Bánh lái treo tường',
              '11_coral-pot': 'Chậu san hô', '12_anchor-statue': 'Tượng mỏ neo'},
    'L3-TO': {'01_clay-food-bowl': 'Bát đất', '02_woven-mat-bed': 'Giường chiếu', '03_tall-clay-pots': 'Chum đất cao',
              '04_cactus-pot': 'Chậu xương rồng', '05_stone-bench': 'Ghế đá dài', '06_amber-lamp': 'Đèn hổ phách',
              '07_patterned-sand-rug': 'Thảm hoa văn cát', '08_stone-training-pillar': 'Cột tập đá', '09_pottery-wheel': 'Bàn xoay gốm',
              '10_sandstone-statue': 'Tượng sa thạch', '11_clay-shelf': 'Kệ đất', '12_desert-flower-vase': 'Bình hoa sa mạc'},
    'L4-HO': {'01_ornate-gold-food-bowl': 'Bát vàng chạm trổ', '02_royal-red-bed': 'Giường đỏ hoàng gia',
              '03_sacred-flame-brazier': 'Lư lửa thiêng', '04_dragon-statue': 'Tượng rồng vàng',
              '05_golden-incense-burner': 'Lư hương vàng', '06_treasure-chest': 'Rương báu',
              '07_royal-red-dragon-carpet': 'Thảm rồng đỏ', '08_golden-training-dummy': 'Hình nộm vàng', '09_fire-throne': 'Ngai lửa'},
    'L4-KI': {'01_ornate-silver-food-bowl': 'Bát bạc chạm trổ', '02_royal-crystal-bed': 'Giường pha lê', '03_sword-altar': 'Đài kiếm',
              '04_diamond-lamp': 'Đèn kim cương', '05_silver-knight-statue': 'Tượng hiệp sĩ bạc', '06_crystal-chest': 'Rương pha lê',
              '07_white-blue-carpet': 'Thảm trắng xanh', '08_crystal-training-dummy': 'Hình nộm pha lê', '09_diamond-throne': 'Ngai kim cương',
              '10_crystal-banner': 'Cờ pha lê', '11_floating-diamond-pedestal': 'Bệ kim cương bay', '12_silver-mirror': 'Gương bạc'},
    'L4-MO': {'01_ornate-jade-food-bowl': 'Bát ngọc bích', '02_royal-leaf-bed': 'Giường lá hoàng gia', '03_jade-shrine': 'Miếu ngọc',
              '04_glowing-flower-pot': 'Chậu hoa phát sáng', '05_spirit-lantern': 'Đèn linh hồn', '06_carved-wooden-chest': 'Rương gỗ chạm',
              '07_moss-carpet': 'Thảm rêu', '08_ancient-wooden-training-dummy': 'Hình nộm gỗ cổ', '09_spirit-tree-bonsai': 'Bonsai cây thần',
              '10_leaf-banner': 'Cờ lá', '11_jade-throne': 'Ngai ngọc bích', '12_glowing-fairy-ring': 'Vòng nấm tiên'},
    'L4-TH': {'01_ornate-pearl-food-bowl': 'Bát ngọc trai', '02_royal-clam-bed': 'Giường vỏ sò', '03_pearl-altar': 'Đài ngọc trai',
              '04_coral-lamp': 'Đèn san hô', '05_treasure-chest': 'Rương báu', '06_seahorse-statue': 'Tượng cá ngựa',
              '07_blue-wave-carpet': 'Thảm sóng biển', '08_coral-training-dummy': 'Hình nộm san hô', '09_pearl-throne': 'Ngai ngọc trai',
              '10_jellyfish-lantern': 'Đèn sứa', '11_giant-pearl-pedestal': 'Bệ ngọc trai lớn', '12_coral-arch': 'Cổng san hô'},
    'L4-TO': {'01_ornate-gold-food-bowl': 'Bát vàng chạm trổ', '02_royal-stone-bed': 'Giường đá hoàng gia',
              '03_mountain-altar': 'Đài núi', '04_amber-crystal-lamp': 'Đèn hổ phách', '05_stone-guardian-statue': 'Tượng thần giữ cửa',
              '06_stone-chest': 'Rương đá', '07_earth-pattern-carpet': 'Thảm hoa văn đất', '08_stone-training-golem': 'Người đá tập luyện',
              '09_stone-throne': 'Ngai đá', '10_earth-banner': 'Cờ Thổ', '11_amber-crystal-pedestal': 'Bệ hổ phách',
              '12_golden-brazier': 'Lư vàng'},
}


def item_price(tier, iid):
    base = {1: 120, 2: 300, 3: 650, 4: 1200}[tier]
    k = 1.7 if any(w in iid for w in ('bed', 'throne', 'statue', 'cot', 'hammock')) else 0.8 if 'bowl' in iid else 1
    return int(round(base * k / 50) * 50)


DECOR = {'01_o-rom': ('Ổ rơm', 600), '02_bat-da': ('Bát đá', 120), '03_chieu-nho': ('Chiếu nhỏ', 200),
         '04_tham-lon': ('Thảm lớn', 700), '05_duoc-tuong': ('Đuốc tường', 250), '06_gay-treo-co': ('Gậy treo cờ', 400),
         '07_day-treo-long': ('Dây treo lông', 180), '08_chau-duong-xi': ('Chậu dương xỉ', 220),
         '09_hinh-nom': ('Hình nộm', 500), '10_bep-lua-noi': ('Bếp lửa nồi', 900), '11_cui-go': ('Củi gỗ', 100),
         '12_thung-go': ('Thùng gỗ', 300), '13_hu-do': ('Hũ đỏ', 150), '14_lo-nho': ('Lò nhỏ', 350),
         '15_bui-duong-xi': ('Bụi dương xỉ', 160), '16_ghe-da': ('Ghế đá', 450)}
# places on the world map (ban-do-the-gioi.png, 1448x1086): key, name, line under it, kind, x, y in map px.
# The 5 regions use the lock/centre points from ngoai-troi/vung/README.md; all start locked.
PLACES = [('nha', 'Nhà', 'Phòng nuôi của {pet}', 'home', 612, 488),
          ('truong', 'Trường học', 'Học Toán, Tiếng Anh, Hệ với cô Rắn', 'school', 705, 432),
          ('cho', 'Chợ', 'Mua đồ ăn, thuốc, đồ trang trí', 'shop', 806, 488),
          ('vo-duong', 'Võ đường', 'Tập luyện, đấu tập, luyện chiêu', 'train', 705, 560),
          ('hoa', 'Vùng Hỏa · Núi lửa', 'Đang khóa', 'region', 400, 190),
          ('kim', 'Vùng Kim · Núi pha lê', 'Đang khóa', 'region', 1170, 250),
          ('moc', 'Vùng Mộc · Rừng cổ thụ', 'Đang khóa', 'region', 230, 470),
          ('tho', 'Vùng Thổ · Hẻm vực', 'Đang khóa', 'region', 1220, 640),
          ('thuy', 'Vùng Thủy · Hồ thác', 'Đang khóa', 'region', 380, 880)]


def stages():
    """The pet's stages that are sliced at 640 (others are skipped)."""
    return [st for st in LEVELS
            if os.path.exists(os.path.join(creatures.frames_dir(PET['creature'], st), 'frames.json'))]


def wide_button(name, w, h, bolt=48, inner=30, corner=46, border=30):
    """A menu button (ui/cat/nut_*) made wider without stretching its picture: plain wood (from the empty
    slot o_trong) goes in just inside the frame's side bars - after the corner bolts in the bolt rows, right
    at the bar in between - so bolts, clouds and the picture stay whole. Then scaled to w x h."""
    import numpy as np
    a = np.array(Image.open(os.path.join(SRC, 'ui', 'cat', name + '.png')).convert('RGBA'))
    H, W = a.shape[:2]
    col = a[:, W // 2].copy()                         # the frame's own top / bottom border rows
    o = Image.open(os.path.join(SRC, 'ui', 'cat', 'o_trong.png')).convert('RGBA')
    oc = np.array(o)[border:o.height - border, o.width // 2:o.width // 2 + 1]
    col[border:H - border] = np.array(Image.fromarray(oc).resize((1, H - 2 * border), Image.LANCZOS))[:, 0]
    extra = max(0, round(H * w / h) - W)
    L, R = extra // 2, extra - extra // 2
    out = np.zeros((H, W + extra, 4), np.uint8)
    for y in range(H):
        s = corner if y < bolt or y >= H - bolt else inner
        out[y] = np.concatenate([a[y, :s], np.repeat(col[y:y + 1], L, 0), a[y, s:W - s],
                                 np.repeat(col[y:y + 1], R, 0), a[y, W - s:]])
    return Image.fromarray(out).resize((w, h), Image.LANCZOS)


def save(im, name):
    im.save(os.path.join(OUT, 'img', name + '.png'), optimize=True)


def save_stats():
    """The 4 pages of the stats screen (scripts/preview_ui_stats.py, R36S size) without the pet, which
    the page draws live on the pedestal: one set before and one after evolving."""
    import numpy as np
    import preview_ui_stats as U
    U.Screen.pet_frame = lambda *a, **k: None
    U.LIVE = True                       # page 3: bars, numbers and gems are drawn by the page (gems can change)
    for stage in STAGES:
        level, exp = LEVELS[stage], (100, 100) if stage == PET['before'] else (0, 160)
        U.PET.update(stage=stage, level=level, exp=exp)
        bg, sprites, glyphs = U.build('r36s')
        ui = U.read_ui(U.pack_ui(bg, sprites, glyphs))
        for page in range(4):
            sc = U.Screen(ui, None, U.TARGETS['r36s'])
            U.draw_page(sc, page, ('idle-0', 0, 0, 0))
            save(Image.fromarray(np.asarray(sc.px, np.uint8)), f'stats_{stage}_{page}')
    return save_gems(U)


def save_gems(U):
    """What the live page needs to draw page 3 (Thuộc tính) and the gem bag: bar fills and where they go,
    the gems at socket and bag size, the bag panel."""
    bar = U.piece('thanh_khung', 1.0, 0.96)
    rows = []
    for i, ((name, base), (icon, col)) in enumerate(zip(U.PET['attributes'], U.ATTRIBUTE_LOOK)):
        fill = U.piece('thanh_fill_' + col, 1.0, 0.96)
        save(fill, 'sfill_' + col)
        yc = 110 + 54 * i
        by = yc - bar.height // 2 + 2
        rows.append(dict(name=name, base=base, fill='sfill_' + col, x=318, y=by + (bar.height - fill.height) // 2,
                         cap=round(fill.width * 0.085), yc=yc))
    for he in U.GEM_ATTRS:
        for g in range(1, 6):
            save(U.gem_img(he, g, 19), f'gem_{he}_{g}')
            save(U.gem_img(he, g, 30), f'gemb_{he}_{g}')
    save(cat('o_hang', 40, 40), 'gem_cell')
    save(cat('o_hang-chon', 40, 40), 'gem_cell_sel')
    save(ui_nine('khung_panel', 232, 300, 1.0, 22, mid=46, thin=0.5), 'gem_panel')
    save(cat('tia-sang', 44), 'tia-sang')
    return dict(rows=rows, sockets=U.SOCKETS, start=U.PET['gems'], attrs=U.GEM_ATTRS, names=U.GEM_NAMES,
                grades=U.GRADES)


def hygiene_icon():
    """The menu has no drawn "Vệ sinh" (bath + medicine) button yet: until one is drawn, make it from the empty
    slot, a soap bubble pile and the medicine bottle. A drawn ui/cat/nut_ve-sinh.png replaces it (kept as is)."""
    path = os.path.join(SRC, 'ui', 'cat', 'nut_ve-sinh.png')
    if os.path.exists(path) and not Image.open(path).info.get('auto'):
        return
    from PIL.PngImagePlugin import PngInfo
    slot = Image.open(os.path.join(SRC, 'ui', 'cat', 'o_trong.png')).convert('RGBA')
    W0, H0 = slot.size
    soap = Image.open(os.path.join(SRC, 'ui', 'cat', 'bot_to.png')).convert('RGBA')
    soap.thumbnail((round(W0 * 0.56), round(H0 * 0.5)), Image.LANCZOS)
    pot = Image.open(os.path.join(SRC, 'ui', 'cat', 'binh-thuoc.png')).convert('RGBA')
    pot.thumbnail((round(W0 * 0.34), round(H0 * 0.48)), Image.LANCZOS)
    slot.alpha_composite(soap, (round(W0 * 0.12), H0 - soap.height - round(H0 * 0.16)))
    slot.alpha_composite(pot, (W0 - pot.width - round(W0 * 0.13), H0 - pot.height - round(H0 * 0.15)))
    info = PngInfo(); info.add_text('auto', '1')
    slot.save(path, pnginfo=info)


R36 = os.path.join(creatures.ROOT, 'assets', 'r36s')


def activity_icon():
    """The 'Hoạt động' (mini games) menu button, made like the Vệ sinh one until a drawn one replaces it: the empty
    slot with the fishing rod and the hoe on it."""
    path = os.path.join(SRC, 'ui', 'cat', 'nut_hoat-dong.png')
    if os.path.exists(path) and not Image.open(path).info.get('auto'):
        return
    from PIL.PngImagePlugin import PngInfo
    slot = Image.open(os.path.join(SRC, 'ui', 'cat', 'o_trong.png')).convert('RGBA')
    W0, H0 = slot.size
    for f, bx, w in (('mini-game/cau-ca/can-cau.png', 0.10, 0.46), ('farm/cay/cay_hoa-ot_4-chin.png', 0.50, 0.40)):
        if not os.path.exists(os.path.join(R36, f)):
            continue
        im = Image.open(os.path.join(R36, f)).convert('RGBA')
        im = im.resize((round(W0 * w), round(W0 * w * im.height / im.width)), Image.NEAREST)
        slot.alpha_composite(im, (round(W0 * bx), H0 - im.height - round(H0 * 0.16)))
    info = PngInfo(); info.add_text('auto', '1')
    slot.save(path, pnginfo=info)


def save_minigames():
    """Fishing (assets/r36s/mini-game/cau-ca, fish in ca/) and the farm (assets/r36s/farm, crops in cay/, soil in
    o-dat-tron/), already at R36S size: saved as cc_<name> and fm_<name>."""
    for folder, pre in (('mini-game/cau-ca', 'cc_'), ('mini-game/cau-ca/ca', 'cc_'), ('farm', 'fm_'), ('farm/cay', 'fm_'),
                        ('farm/o-dat', 'fm_'), ('shop-nong-san', 'sn_'), ('shop-nong-san/chu-quan', 'sn_'),
                        ('mini-game/cau-ca/fx', 'cc_'), ('ui/hoat-dong', 'hd_'),
                        ('mini-game/cau-ca/can', 'cc_'), ('shop-nong-san/do-cau', 'sn_'),
                        ('nau-an/nen', 'na_'), ('nau-an/hoat-anh', 'na_'), ('nau-an/popup', 'na_'), ('nau-an/mon', 'na_'), ('ui/tui-do', 'td_'),
                        ('truong-hoc', 'th_'), ('truong-hoc/co-giao', 'th_'), ('truong-hoc/ui', 'th_')):
        d = os.path.join(R36, folder)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith('.png'):
                save(Image.open(os.path.join(d, f)).convert('RGBA'), pre + f[:-4])
    fix_cooking()


def _strip(name):
    im = Image.open(os.path.join(R36, 'nau-an', 'hoat-anh', name + '_dai6.png')).convert('RGBA')
    fw = im.width // 6
    return [im.crop((k * fw, 0, k * fw + fw, im.height)) for k in range(6)]


def _join(frames, name):
    w, h = frames[0].size
    out = Image.new('RGBA', (w * 6, h))
    for k, f in enumerate(frames):
        out.alpha_composite(f, (k * w, 0))
    save(out, 'na_' + name + '_dai6')


def _runs(row):
    """[(x0, x1)] of the True runs in a row"""
    d = np.diff(np.concatenate([[0], row.astype(int), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0] - 1))


def _sleeve(a):
    """An arm that stops in mid air (its cream sleeve cut flat) is carried on down to the frame's bottom,
    following the arm's own slant: the row just above the cut is repeated, shifted a little each row."""
    h = a.shape[0]
    cream = (a[..., 0] > 215) & (a[..., 1] > 205) & (a[..., 2] > 175) & (a[..., 3] > 0)
    yb = None
    for y in range(h - 1, h // 3, -1):
        wide = [r for r in _runs(cream[y]) if r[1] - r[0] >= 24
                and cream[y - 10, r[0]:r[1] + 1].mean() > 0.7]     # a thick sleeve, not a thin rim highlight
        if wide:
            yb, (x0, x1) = y, max(wide, key=lambda r: r[1] - r[0])
            break
    if yb is None or yb >= h - 4:
        return a
    def centre(y):
        rs = [r for r in _runs(cream[y]) if r[1] >= x0 - 30 and r[0] <= x1 + 30 and r[1] - r[0] >= 10]
        return None if not rs else sum(rs[0]) / 2
    c0, c1 = centre(yb - 34), centre(yb - 4)
    slope = 0 if c0 is None or c1 is None else (c1 - c0) / 30
    t = yb - 4
    l, r = max(0, x0 - 4), min(a.shape[1], x1 + 5)
    tpl = a[t, l:r].copy()
    out = a.copy()
    for y in range(t + 1, h):
        dx = int(round(slope * (y - t)))
        for j in range(r - l):
            x = l + j + dx
            if 0 <= x < a.shape[1] and tpl[j, 3] > 0:
                out[y, x] = tpl[j]
    return out


def fix_rods():
    """The auto rod strips (mini-game/cau-ca/can/can_<quang|cho|keo>_dai4.png) come with their line and float drawn
    a short way off the jetty. The page casts much further, so the free line, the float, splashes and "!!" marks
    go (everything light or red that is not on the rod itself) and the page draws them; returns where the rod's
    tip is in each 130 px frame: {name: [[x, y] x 4]}."""
    from slice_frames import label
    tips = {}
    for name in ('quang', 'cho', 'keo'):
        path = os.path.join(R36, 'mini-game', 'cau-ca', 'can', f'can_{name}_dai4.png')
        if not os.path.exists(path):
            continue
        im = np.array(Image.open(path).convert('RGBA'))
        out, tips[name] = im.copy(), []
        for k in range(4):
            a = im[:, k * 130:(k + 1) * 130]
            r, g, b, al = [a[..., i].astype(int) for i in range(4)]
            light = np.minimum(np.minimum(r, g), b) > 170
            red = (r > 160) & (g < 70) & (b < 80)                 # the float's own red, not the warm wood
            solid = (al > 0) & ~light & ~red
            lab = label(solid)
            ids, sizes = np.unique(lab[lab > 0], return_counts=True)
            by_red = red.copy()                                  # the float's dark rim sits right by its red
            for dy in (-3, -2, -1, 0, 1, 2, 3):
                for dx in (-3, -2, -1, 0, 1, 2, 3):
                    by_red |= np.roll(np.roll(red, dy, 0), dx, 1)
            float_ids = set(np.unique(lab[by_red & (lab > 0)]))
            edge = set(np.unique(lab[:, [0, -1]]))                # bits of the next frame over the border
            rod = np.isin(lab, [i for i, z in zip(ids, sizes)
                                if z >= 60 or (z >= 6 and i not in float_ids and i not in edge)])
            near = rod.copy()                                    # the line running along the rod stays
            for dy in (-2, -1, 0, 1, 2):
                for dx in (-2, -1, 0, 1, 2):
                    near |= np.roll(np.roll(rod, dy, 0), dx, 1)
            keep = rod | (near & light & (al > 0))
            o = a.copy()
            o[..., 3] = np.where(keep, al, 0)
            out[:, k * 130:(k + 1) * 130] = o
            ys, xs = np.where(rod)
            far = ((xs - 10) ** 2 + (ys - 125) ** 2).argmax()   # the tip: furthest from the stand's foot
            tips[name].append([int(xs[far]), int(ys[far])])
        save(Image.fromarray(out, 'RGBA'), f'cc_can_{name}_dai4')
    return tips


def fix_cooking():
    """Cooking strips with cut edges, mended for the demo (the drawn files stay as they are):
    cat, khuay - ragged outlines and arms stopping in mid air in hoat-anh/: cut again from the v2 sheet
            (source/nau-an/NAU_cat-khuay_v2.png, 362 px cells on magenta), a cut-off sleeve carried down to the bottom;
    chien - bits of steam cut flat by the frame's bottom edge: dropped;
    xong  - steam cut flat by the frame's top edge: faded out over the top 40 px."""
    from slice_frames import label
    v2 = os.path.join(creatures.ROOT, 'assets', 'source', 'nau-an', 'NAU_cat-khuay_v2.png')
    if os.path.exists(v2):
        sheet = np.array(Image.open(v2).convert('RGB')).astype(int)
        xs = [0, 362, 724, 1085, 1447, 1809, 2171]
        for name, (y0, y1) in (('cat', (2, 361)), ('khuay', (364, 722))):
            frames = []
            for k in range(6):
                c = sheet[y0:y1, xs[k] + 2:xs[k + 1] - 1]
                r, g, b = c[..., 0], c[..., 1], c[..., 2]
                bg = (r > 180) & (b > 180) & (g < 110)                      # magenta
                spill = (r > g + 60) & (b > g + 60) & (np.abs(r - b) < 70)  # pink fringe
                a = ~(bg | spill)
                lab = label(a)                                              # the drawing only, no specks
                ids, sizes = np.unique(lab[lab > 0], return_counts=True)
                a = np.isin(lab, ids[sizes > 400])
                cell = np.zeros((362, 362, 4), np.uint8)                    # bottom-aligned on a 362 px square
                h, w = a.shape
                cell[362 - h:, :w] = np.dstack([c, a * 255]).astype(np.uint8)
                frames.append(Image.fromarray(_sleeve(cell), 'RGBA'))
            _join(frames, name)
    frames = []
    for f in _strip('chien'):
        a = np.array(f)
        lab = label(a[..., 3] > 0)
        for i in set(np.unique(lab[-24:])) - {0}:                      # small bits down by the bottom edge: steam
            ys = np.where((lab == i).any(1))[0]
            if (lab == i).sum() < 8000 and ys[0] > a.shape[0] * 0.7:
                a[lab == i, 3] = 0
        frames.append(Image.fromarray(a, 'RGBA'))
    _join(frames, 'chien')
    frames = []
    for f in _strip('xong'):
        a = np.array(f).astype(float)
        ramp = np.clip(np.arange(a.shape[0]) / 40.0, 0, 1)[:, None]
        a[..., 3] *= ramp
        frames.append(Image.fromarray(a.astype(np.uint8), 'RGBA'))
    _join(frames, 'xong')


# care props and warnings (assets/r36s/cham-soc/_bang, see-through, already drawn for 640x480), cut cell by cell
CARE_SHEETS = {
    'CHAM1_do-cham-soc': (4, 4, ['bat_day', 'bat_nua', 'bat_rong', 'bat_nuoc',
                                 'chau_nuoc', 'chau_bot', 'khan', 'xa-phong',
                                 'do-choi_bong', 'do-choi_chuong', 'do-choi_khuc-go', 'do-choi_long-vu',
                                 'choi_0', 'choi_1', 'choi_2', 'sach-bong']),
    'CHAM2_canh-bao': (4, 3, ['bao_chu-y', 'bao_chu-y-2', 'bao_chu-y-3', 'bao_nguy',
                              'o_toi', 'tim_vo', 'dau-x', 'dau-lau-tron',
                              'gio', 'bong_bay', 'sao_no', 'dong-ho-cat']),
}


def save_care():
    for sheet, (cols, rows, names) in CARE_SHEETS.items():
        path = os.path.join(R36, 'cham-soc', '_bang', sheet + '.png')
        if not os.path.exists(path):
            continue
        im = Image.open(path).convert('RGBA')
        for i, name in enumerate(names):
            c, r = i % cols, i // cols
            cell = im.crop((round(c * im.width / cols), round(r * im.height / rows),
                            round((c + 1) * im.width / cols), round((r + 1) * im.height / rows)))
            from preview_ui_stats import despeck
            cell = despeck(cell, 0.004)              # bits of the neighbour cell's glow
            box = cell.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
            if box:
                save(cell.crop(box), 'cs_' + name)


def save_demo():
    """The rest of the demo from start to end: title screen, the egg hatching, poop and flies, the sick bubble."""
    save(Image.open(os.path.join(SRC, 'ui', '_bang', 'TITLE1_nen.png')).convert('RGB').resize((W, H), Image.LANCZOS),
         'title_bg')
    save(cat('logo', 520), 'logo')
    # the chosen welcome screen (ui/man-hinh-chao/TITLE_B_nen.png: the tiger hugging its egg; name plate and two
    # empty buttons drawn in, the page writes on them); the logo screen above is the fallback
    chao = os.path.join(R36, 'ui', 'man-hinh-chao', 'MAN_CHAO_ELEMON.png')
    baked = os.path.exists(chao)
    if not baked:
        chao = os.path.join(SRC, 'ui', 'man-hinh-chao', 'TITLE_B_nen.png')
    if os.path.exists(chao):
        save(Image.open(chao).convert('RGB').resize((W, H), Image.LANCZOS), 'title_b')
        save_title_pet()
    # the game's name (ui/man-hinh-chao/LOGO_ELEMON.png, already at screen size) goes on the name plate
    logo = os.path.join(SRC, 'ui', 'man-hinh-chao', 'LOGO_ELEMON.png')
    if os.path.exists(logo) and not baked:
        save(Image.open(logo).convert('RGBA'), 'logo_elemon')
    for n in ('nut-menu_thuong', 'nut-menu_chon', 'nut-menu_khoa'):
        save(cat(n, 220), n)
    save(cat('con-tro', 22), 'con-tro')
    for i in range(4):
        save(cat(f'trung_{i}', 130), f'trung_{i}')
        save(cat(f'no-trung_{i}', 170), f'no-trung_{i}')
        save(cat(f'ruoi_{i % 3}', 18), f'ruoi_{i % 3}')
    # hatching (assets/r36s/ui/no-trung/<element>/f1..f8, already at R36S size): glowing egg, cracking, cracked,
    # burst, shards, two halves, bits, light
    hatch = os.path.join(creatures.ROOT, 'assets', 'r36s', 'ui', 'no-trung')
    for he in ('hoa', 'kim', 'moc', 'thuy', 'tho'):
        for i in range(1, 9):
            f = os.path.join(hatch, he, f'f{i}.png')
            if os.path.exists(f):
                save(Image.open(f).convert('RGBA'), f'no_{he}_{i}')
    save_care()
    # emotes over the pet (assets/r36s/bieu-cam, already at screen size) and the bath things of each house tier
    for f in sorted(os.listdir(os.path.join(R36, 'bieu-cam'))) if os.path.isdir(os.path.join(R36, 'bieu-cam')) else []:
        if f.endswith('.png'):
            save(Image.open(os.path.join(R36, 'bieu-cam', f)).convert('RGBA'), f[:-4])
    tam = os.path.join(R36, 'cham-soc', 'do-tam')
    for f in sorted(os.listdir(tam)) if os.path.isdir(tam) else []:
        if f.endswith('.png'):
            save(Image.open(os.path.join(tam, f)).convert('RGBA'), f[:-4])
    go = os.path.join(R36, 'ui', 'khung_chao-doi_go.png')       # the hanging wooden 'CHÚC MỪNG!' board of the hatch
    if os.path.exists(go):
        save(Image.open(go).convert('RGBA'), 'bang_go')
    # status bubbles and floor mess (ui/_bang/CHAM3_trang-thai.png, cut by cut_ui_sheets.py)
    for n in ('doi', 'ban', 'buon', 'om', 'buon-ngu', 'chan', 'khat', 'vui'):
        save(cat('tt_' + n, 50), 'tt_' + n)
    for n, w in (('phan-nho', 26), ('phan-to', 36), ('vet-ban', 54), ('vun-do-an', 46), ('vung-nuoc', 58),
                 ('long', 50), ('bui', 48), ('sach', 52)):
        save(cat('san_' + n, w), 'san_' + n)
    for n in ('phan_nho', 'phan_vua', 'phan_to'):
        save(cat(n, 34), n)
    save(cat('bong_om', 46), 'bong_om')
    for n, w in (('bot_nho', 18), ('bot_vua', 26), ('bot_to', 36)):
        save(cat(n, w), n)


# the tiger on welcome screen B, upper body (head, mane, arms, chest) down to the belt: the page lifts it a pixel or
# two so it breathes; box in 640 px
TITLE_PET = (196, 150, 420, 272)


def save_title_pet():
    """Cuts the painted tiger's upper body out of welcome screen B by colour (warm fur, dark stripes, cream belly;
    not sky, sea or grass), holes inside the body filled, as a layer the page can move."""
    import numpy as np
    im = Image.open(os.path.join(OUT, 'img', 'title_b.png')).convert('RGB').crop(TITLE_PET)
    c = np.array(im).astype(int)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    body = ((r > g + 18) & (r > b + 40)) | (c.max(2) < 80) | ((r > 200) & (g > 170) & (b < 200) & (r > b + 35))
    # outside = reachable from the box edge without crossing the body; everything else is the tiger
    out = np.zeros_like(body)
    out[0], out[:, 0], out[:, -1] = ~body[0], ~body[:, 0], ~body[:, -1]
    while True:
        g2 = out.copy()
        g2[1:] |= out[:-1]; g2[:-1] |= out[1:]; g2[:, 1:] |= out[:, :-1]; g2[:, :-1] |= out[:, 1:]
        g2 &= ~body
        if (g2 == out).all():
            break
        out = g2
    rgba = np.dstack([c, np.where(out, 0, 255)]).astype(np.uint8)
    save(Image.fromarray(rgba, 'RGBA'), 'title_pet')


def save_map():
    """The world map at screen size, plus each region's lock layer and gold edge cropped to what is drawn."""
    k = W / 1448
    save(Image.open(os.path.join(MAP, 'ban-do-the-gioi.png')).convert('RGB').resize((W, H), Image.LANCZOS), 'map')
    layers = {}
    for key, *_, kind, _x, _y in PLACES:
        if kind != 'region':
            continue
        for layer in ('khoa', 'chon'):
            im = Image.open(os.path.join(MAP, 'vung', f'{layer}_{key}.png')).convert('RGBA').resize((W, H), Image.LANCZOS)
            box = im.getchannel('A').point(lambda v: 255 if v > 6 else 0).getbbox()
            save(im.crop(box), f'{layer}_{key}')
            layers[f'{layer}_{key}'] = box[:2]
    save(cat('mui-ten_xuong', 22), 'mui-ten_xuong')
    save(cat('mui-ten_len', 22), 'mui-ten_len')
    save(ui_nine('khung_panel', 620, 70, 1.0, 22, mid=46, thin=0.5), 'map_info')
    return dict(layers=layers, places=[dict(key=key, name=n, line=line, kind=kind, x=round(x * k), y=round(y * k))
                                       for key, n, line, kind, x, y in PLACES])


def house_items(room):
    """A home's items at screen size and place (vi-tri.json + hand-set ones), back to front by where they touch the
    floor; an item listed but not in the folder is left out."""
    k = W / 1448
    folder = os.path.join(SRC, 'do-theo-phong', room)
    pos = json.load(open(os.path.join(folder, 'vi-tri.json'), encoding='utf-8'))
    pos.update(DECOR_MANUAL.get(room, {}))
    out = []
    for name, (x, y, sc) in pos.items():
        path = os.path.join(folder, name)
        if not os.path.exists(path):
            continue
        im = Image.open(path).convert('RGBA')
        im = im.resize((max(1, round(im.width * sc * k)), max(1, round(im.height * sc * k))), Image.LANCZOS)
        X, Y = round(x * k), round(y * k)
        out.append(dict(name=name, img=im, x=X, y=Y, floor=-1 if decor_flat(name) else Y + im.height))
    return sorted(out, key=lambda i: i['floor'])


def save_houses():
    """Every Hỏa home: its empty room, its items (one picture each, drawn once bought) with their shop icon and
    price, a thumbnail for the shop's Nhà tab, and the bathroom of the same tier (nen/nha-tam/NT_L1..4)."""
    houses = []
    for key, room, name, tier, he, price, paid, walk in HOUSES:
        save(Image.open(EMPTY[room]).convert('RGB').resize((W, H), Image.LANCZOS), f'room_{key}')
        save(Image.open(EMPTY[room]).convert('RGB').resize((60, 45), Image.LANCZOS), f'nha_{key}')
        save(Image.open(os.path.join(SRC, 'nen', 'nha-tam', f'NT_L{tier}.png')).convert('RGB')
             .resize((W, H), Image.LANCZOS), f'nha-tam-{tier}')
        names = DECOR if room == ROOM else {k: (n, item_price(tier, k)) for k, n in ITEM_NAMES[room].items()}
        items = []
        for it in house_items(room):
            iid = it['name'][:-4]
            if iid not in names:
                continue
            save(it['img'], f'h_{key}_{iid}')
            save(img(os.path.join(SRC, 'do-theo-phong', room, it['name']), box=(46, 46)), f'hi_{key}_{iid}')
            n, pr = names[iid]
            items.append(dict(id=iid, img=f'h_{key}_{iid}', icon=f'hi_{key}_{iid}', x=it['x'], y=it['y'],
                              floor=it['floor'], name=n, price=pr))
        houses.append(dict(key=key, name=name, tier=tier, he=HE_NAME[he], price=price, paid=paid, walk=list(walk),
                           room=f'room_{key}', thumb=f'nha_{key}', bath=f'nha-tam-{tier}', items=items))
    save(goc('icon_nha', 40, 40), 'tab_nha')
    return houses


def save_shop():
    """The shop (Chợ on the map): the same screen as the approved demo, drawn live; foods bought go to the bag."""
    save(ui_nine('khung_panel', 640, 436, 1.0, 22, mid=46, thin=0.7), 'shop_bg')
    # painted menu backgrounds (ui/nen-menu, already 640x436, kept as they are): sunset for picking, night for the shop
    for n in ('hoang-hon', 'troi-dem'):
        f = os.path.join(SRC, 'ui', 'nen-menu', f'nen-menu_{n}.png')
        if os.path.exists(f):
            save(Image.open(f).convert('RGB'), 'nen-menu_' + n)
    save(img(os.path.join(SRC, 'ui', 'cat', 'chu-quan.png'), 250), 'chu-quan')
    save(cat('bong_trong', 128), 'bong_trong')
    for t, _ in SHOP_TABS:
        save(cat(t, 40, 40), t)
    save(cat('o_hang-chon', 48, 48), 'tab_sel')
    for n in ('o_hang', 'o_hang-chon', 'o_hang-khoa'):
        save(cat(n, 64, 64), 'shelf_' + n)
    save(hslice(cat('nhan-gia'), 78, 24, 0.27, 0.10), 'nhan-gia')
    save(ui_nine('khung_panel', 364, 104, 1.0, 22, mid=46, thin=0.5), 'shop_desc')
    save(hslice(cat('nut_mua'), 120, 32, 0.15, 0.15), 'nut_mua')
    save(hslice(cat('nut_ban'), 120, 32, 0.15, 0.15), 'nut_ban')
    rows = {}
    for tab, items in SHOP.items():
        rows[tab] = []
        for path, name, price, info, state in items:
            key = os.path.splitext(os.path.basename(path))[0]
            save(img(os.path.join(SRC, path), box=(44, 44)), 'shop_' + key)
            save(img(os.path.join(SRC, path), box=(38, 38)), 'food_' + key)      # bag icon (foods, medicine, toys)
            if tab == 0:                      # a food: it can go into the bag and be eaten
                save(img(os.path.join(SRC, path), box=(30, 30)), 'mouth_' + key)
            he, _, effect = info.partition(' · ')
            rows[tab].append(dict(key='shop_' + key, file=key, name=name, price=price, info=info, he=he,
                                  effect=effect, state=state))
    rows[1] = []                          # the room items of the home the pet lives in: filled in by the page
    return dict(tabs=[dict(icon=t, name=n) for t, n in SHOP_TABS], rows=[rows[t] for t in range(len(SHOP_TABS))])


PETS_LINK = os.path.join(creatures.ROOT, 'preview', 'pets')


def save_creatures():
    """pets/<id>.json per creature (its stages' frame lists, anchors and moves) and the list for the egg / pet pick."""
    import subprocess
    if not os.path.exists(PETS_LINK):            # a junction needs no admin rights on Windows
        subprocess.run(['cmd', '/c', 'mklink', '/J', PETS_LINK, os.path.join(creatures.ROOT, 'assets', 'creatures-640')],
                       check=True, capture_output=True)
    os.makedirs(os.path.join(OUT, 'pets'), exist_ok=True)
    out = []
    for cid, c in creatures.CREATURES.items():
        sts = {}
        for stage in LEVELS:
            fr = creatures.frames_dir(cid, stage)
            path = os.path.join(fr, 'frames.json')
            if not os.path.exists(path):
                continue
            anims = json.load(open(creatures.anims_path(cid, stage), encoding='utf-8'))
            sts[stage] = dict(meta=json.load(open(path)), anims={k: v for k, v in anims.items() if not k.startswith('_')},
                              name=creatures.STAGE_NAMES[stage], level=LEVELS[stage],
                              dir=os.path.relpath(os.path.join(fr, 'png'), os.path.join(creatures.ROOT, 'assets',
                                                  'creatures-640')).replace(os.sep, '/'))
        if 'baby' not in sts:
            continue
        with open(os.path.join(OUT, 'pets', cid + '.json'), 'w', encoding='utf-8') as fh:
            json.dump(dict(id=cid, name=c['name'], element=c['element'], stages=sts, order=list(sts)), fh, ensure_ascii=False)
        out.append(dict(id=cid, name=c['name'], element=c['element']))
    return out


def main():
    global STAGES
    STAGES = stages()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'img'))
    # Hang đá empty (the egg hatches there); the homes and their items come from save_houses()
    save(Image.open(EMPTY[HOUSES[0][1]]).convert('RGB').resize((W, H), Image.LANCZOS), 'room')     # the start home: the egg hatches there
    save(Image.open(os.path.join(SRC, 'ui', '_bang', 'EVO1_nen.png')).convert('RGB').resize((W, H), Image.LANCZOS), 'nen')
    # HUD and menu
    for icon, col in NEEDS:
        save(goc(icon, 22), icon)
        save(goc('thanh_fill_' + col, 74, 10), 'fill_' + col)
    save(goc('thanh_khung', 74, 12), 'bar')
    save(hslice(cat('o_tien'), 112, 30, 0.40, 0.12), 'coin_box')
    save(cat('huy-hieu_lv', 32), 'badge')
    hygiene_icon()
    activity_icon()
    for n in MENU_ICON + ['nut_ve-sinh', 'nut_hoat-dong']:
        save(wide_button(n, 100, 50), n)
    save_minigames()
    save(cat('o_chon', 60, 60), 'o_chon')
    save(ui_nine('khung_panel', 440, 190, 1.0, 22, mid=46, thin=0.55), 'panel')
    for n in ('bong_tim', 'bong_vui', 'bong_doi', 'bong_buon-ngu', 'bong_gian', 'bong_buon'):
        save(cat(n, 46), n)
    # food picker (opens on Ăn, takes the menu bar's place)
    save(ui_nine('khung_panel', 620, 112, 1.0, 22, mid=46, thin=0.55), 'picker')
    save(cat('o_hang', 56, 56), 'o_hang')
    save(cat('o_hang-chon', 56, 56), 'o_hang-chon')
    for file, *_ in BAG:
        save(img(os.path.join(SRC, 'do-an', file + '.png'), box=(38, 38)), 'food_' + file)
        save(img(os.path.join(SRC, 'do-an', file + '.png'), box=(30, 30)), 'mouth_' + file)
    save(cat('vun-do-an', 30), 'vun-do-an')
    save(cat('lap-lanh', 26), 'lap-lanh')
    for n, w in (('tim_nho', 14), ('tim_vua', 18), ('z_nho', 12), ('z_vua', 16), ('z_to', 20)):
        save(cat(n, w), n)
    # evolution effects
    for he in ('hoa', 'kim', 'moc', 'thuy', 'tho'):        # the evolution swirl of each element
        for i in range(4):
            save(cat(f'xoay_{he}_{i}'), f'xoay_{he}_{i}')
    for n in ('cot-sang', 'cot-set', 'no-sang', 'vong-song', 'hat-sang'):
        save(cat(n), n)
    for n in ('hat_vang', 'hat_trang', 'hat_lua', 'hat_xoay', 'hat_la', 'hat_nuoc', 'hat_kim', 'hat_dat'):
        save(cat(n, 16), n)
    save(cat('bang-ron', 440), 'bang-ron')
    # the pet before and after
    data = dict(pet=PET, stages={}, bag=[dict(file=f, name=n, he=he, count=c, effect=e) for f, n, he, c, e in BAG])
    data['houses'] = save_houses()
    tdo = os.path.join(R36, 'farm', 'toa-do.json')        # the 6x6 field: centre of every plot on farm/nen.png
    data['farm'] = json.load(open(tdo)) if os.path.exists(tdo) else None
    data['rod_tips'] = fix_rods()
    # the title font (FatPix VN: free for commercial games, not to be resold; assets/source/font/_thu/fatpix)
    fp = os.path.join(SRC, 'font', '_thu', 'fatpix', 'FatPix-VN-SVG.ttf')
    if os.path.exists(fp):
        os.makedirs(os.path.join(OUT, 'font'), exist_ok=True)
        shutil.copy(fp, os.path.join(OUT, 'font', 'FatPix-VN.ttf'))
    data['title_baked'] = os.path.exists(os.path.join(R36, 'ui', 'man-hinh-chao', 'MAN_CHAO_ELEMON.png'))
    data['map'] = save_map()
    save_demo()
    data['shop'] = save_shop()
    # every creature: the page reads its cut frames straight from assets/creatures-640 through preview/pets (a
    # junction, nothing is copied) and loads the one the player picks from pets/<id>.json
    data['creatures'] = save_creatures()
    data['stats_stages'] = STAGES
    import time
    data['build'] = int(time.time())
    data['gems'] = save_stats()
    with open(os.path.join(OUT, 'data.js'), 'w', encoding='utf-8') as fh:
        fh.write('const DATA = ' + json.dumps(data, ensure_ascii=False) + ';\n')
    # the page names data.js with a build stamp, so a browser never keeps an old copy from its cache
    import time
    page = open(os.path.join(os.path.dirname(__file__), 'evo_app.html'), encoding='utf-8').read()
    page = page.replace('<script src="data.js"></script>', f'<script src="data.js?v={int(time.time())}"></script>')
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(page)
    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
    print(f'{OUT}: {size / 1024:.0f} KB')


if __name__ == '__main__':
    main()
