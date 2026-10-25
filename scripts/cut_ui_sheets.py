"""Cuts the 2nd batch of UI sheets (assets/source/ui/_bang/HUD*.png) into named pieces on see-through
backgrounds: assets/source/ui/cat/<name>.png, full source resolution (scale them when building).

Pieces are found as blobs on the magenta background (stink lines and motion marks stay with their
poop / fly), sorted into rows top to bottom and left to right inside a row, then named from NAMES.
Usage: python cut_ui_sheets.py [sheet ...]
"""
import os, sys
import numpy as np
from PIL import Image

import creatures
from slice_frames import label

UI = os.path.join(creatures.ROOT, 'assets', 'source', 'ui')
OUT = os.path.join(UI, 'cat')

# per sheet: rows of names, top to bottom (a row is a band of pieces at about the same height)
NAMES = {
    'HUD1_menu': [
        ['nut_cho-an', 'nut_don-dep', 'nut_choi', 'nut_tap-luyen'],
        ['nut_ngu', 'nut_cua-hang', 'nut_trang-tri', 'nut_ra-ngoai'],
        # third band, left to right: empty slot, selected slot, coin box, top HUD bar, level badge
        ['o_trong', 'o_chon', 'o_tien', 'thanh_hud', 'huy-hieu_lv'],
    ],
    'HUD2_cam-xuc': [
        ['bong_trong', 'bong_doi', 'bong_buon', 'bong_om'],
        ['bong_buon-ngu', 'bong_vui', 'bong_gian', 'bong_tim'],
    ],
    'HUD3_cham-soc': [
        ['phan_nho', 'phan_vua', 'phan_to', 'ban_1', 'ban_2'],
        ['ruoi_0', 'ruoi_1', 'ruoi_2', 'bot_nho', 'bot_vua', 'bot_to'],
        ['dau-lau', 'binh-thuoc', 'vien-thuoc', 'z_nho', 'z_vua', 'z_to'],
        ['vun-do-an', 'tim_nho', 'tim_vua', 'tim_to', 'lap-lanh', 'mo-hoi'],
    ],
    'SHOP1_cua-hang': [
        ['o_hang', 'o_hang-chon', 'o_hang-khoa'],
        # the up / down arrows sit one above the other at the right end of this band
        ['nhan-gia', 'nut_mua', 'nut_ban', 'mui-ten_len', 'mui-ten_xuong'],
        ['bang-mo-ta', 'tab_do-an', 'tab_trang-tri', 'tab_thuoc', 'tab_dac-biet'],
        ['chu-quan'],
    ],
    'EVO2_xoay': [[f'xoay_{he}_{i}' for i in range(4)] for he in ('hoa', 'kim', 'moc', 'thuy', 'tho')],
    'EVO3_bung-sang': [
        ['sang_nho', 'sang_to', 'cot-sang', 'cot-set'],
        ['no-sang', 'vong-song', 'vong-hat', 'hat-sang'],
    ],
    'EVO4_banner': [
        ['bang-ron'],
        ['hat_vang', 'hat_trang', 'hat_lua', 'hat_la', 'hat_nuoc', 'hat_kim', 'hat_dat', 'hat_xoay'],
    ],
    'EVO5_no-trung': [[f'trung_{i}' for i in range(4)], [f'no-trung_{i}' for i in range(4)]],
    # status bubbles over the pet, and what a pet leaves on the floor (CHAM3, 24/10/2026)
    'CHAM3_trang-thai': [
        ['tt_doi', 'tt_ban', 'tt_buon', 'tt_om'], ['tt_buon-ngu', 'tt_chan', 'tt_khat', 'tt_vui'],
        ['san_phan-nho', 'san_phan-to', 'san_vet-ban', 'san_vun-do-an'], ['san_vung-nuoc', 'san_long', 'san_bui', 'san_sach'],
    ],
    # title screen: the logo (tiger, dragon, 5-element badge, empty name plate), menu buttons, cursor
    'TITLE2_logo': [['logo'], ['nut-menu_thuong', 'nut-menu_chon', 'nut-menu_khoa'], ['con-tro']],
    # gems: one row per element, 5 grades left to right (rough stone ... emblem)
    'NGOC1_ngoc': [[f'ngoc_{he}_{g}' for g in range(1, 6)] for he in ('hoa', 'thuy', 'tho', 'moc', 'kim')],
    # equipment slots (empty / chosen), gem sockets, forging pieces
    'EQ1_o-trang-bi': [
        ['tb_mu', 'tb_day-chuyen', 'tb_giap', 'tb_vuot', 'tb_bua-deo'],
        ['tb_mu_chon', 'tb_day-chuyen_chon', 'tb_giap_chon', 'tb_vuot_chon', 'tb_bua-deo_chon'],
        ['o-kham_trong', 'o-kham_ngoc', 'o-kham_khoa', 'khung-kham_2', 'khung-kham_3'],
        ['bua-ren', 'de-ren', 'co-may-man', 'ngoc-vo', 'tia-sang'],
    ],
}
GROW = 10          # px: marks this close to a piece belong to it
GROW_SHEET = {'HUD1_menu': 2, 'SHOP1_cua-hang': 4, 'EVO3_bung-sang': 14, 'EVO5_no-trung': 14, 'EVO4_banner': 2,
              'EQ1_o-trang-bi': 14, 'CHAM3_trang-thai': 6}      # pieces packed close together there


def magenta(a):
    r, g, b = (a[..., i].astype(int) for i in range(3))
    return ((r > 150) & (b > 150) & (g < 110)) | ((r > 90) & (b > 90) & (g < 0.6 * np.minimum(r, b)) & (abs(r - b) < 90))


def grow(m, n):
    for _ in range(n):
        g = m.copy()
        g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
        m = g
    return m


# smallest piece kept, as a share of the sheet (stray sparkles are smaller)
MIN_PIECE = {'EVO4_banner': 0.002}
# sheets laid out on an even grid whose pieces break into many small bits (swirls): cut by cell
GRID = {'EVO2_xoay': (4, 5), 'EVO3_bung-sang': (4, 2), 'EVO5_no-trung': (4, 2), 'NGOC1_ngoc': (5, 5), 'CHAM3_trang-thai': (4, 4)}


def cut_grid(sheet, rows, a, solid):
    cols, nrows = GRID[sheet]
    h, w = solid.shape
    out = {}
    for r, names in enumerate(rows):
        for c, name in enumerate(names):
            x0, y0, x1, y1 = round(c * w / cols), round(r * h / nrows), round((c + 1) * w / cols), round((r + 1) * h / nrows)
            piece = a[y0:y1, x0:x1].copy()
            keep = solid[y0:y1, x0:x1].copy()
            # bits of the next cell's sparkles poke in at the edges: drop small blobs that touch the border
            lab = label(keep)
            edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
            for i in edge:
                if (lab == i).sum() < 0.02 * keep.size:
                    keep[lab == i] = False
            piece[..., 3] = np.where(keep, 255, 0)
            im = Image.fromarray(piece, 'RGBA')
            im = im.crop(im.getbbox())
            im.save(os.path.join(OUT, name + '.png'))
            out[name] = im.size
    return out


def cut(sheet, rows):
    a = np.array(Image.open(os.path.join(UI, '_bang', sheet + '.png')).convert('RGBA'))
    solid = ~magenta(a)
    if sheet in GRID:
        return cut_grid(sheet, rows, a, solid)
    # half size for the blob search: same result, a quarter of the work
    small = solid[::2, ::2]
    lab = label(grow(small, GROW_SHEET.get(sheet, GROW) // 2))
    ids, counts = np.unique(lab[lab > 0], return_counts=True)
    big = [i for i, n in zip(ids, counts) if n > MIN_PIECE.get(sheet, 0.0008) * small.size]
    boxes = []
    for i in big:
        ys, xs = np.nonzero(lab == i)
        boxes.append(dict(id=i, x0=xs.min() * 2, y0=ys.min() * 2, x1=xs.max() * 2 + 2, y1=ys.max() * 2 + 2,
                          cy=ys.mean() * 2, cx=xs.mean() * 2))
    want = sum(len(r) for r in rows)
    if len(boxes) != want:
        sys.exit(f'{sheet}: found {len(boxes)} pieces, expected {want}')
    boxes.sort(key=lambda b: b['cy'])
    out, k = {}, 0
    for names in rows:
        band = sorted(boxes[k:k + len(names)], key=lambda b: (round(b['cx'] / 80), b['cy']))
        k += len(names)
        for name, b in zip(names, band):
            mask = np.repeat(np.repeat(lab == b['id'], 2, 0), 2, 1)[:a.shape[0], :a.shape[1]] & solid
            piece = a.copy()
            piece[..., 3] = np.where(mask, 255, 0)
            im = Image.fromarray(piece, 'RGBA').crop((b['x0'], b['y0'], b['x1'], b['y1']))
            im = im.crop(im.getbbox())
            im.save(os.path.join(OUT, name + '.png'))
            out[name] = im.size
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    for sheet, rows in NAMES.items():
        if only and sheet not in only:
            continue
        sizes = cut(sheet, rows)
        print(sheet, ' '.join(f'{n}:{w}x{h}' for n, (w, h) in sizes.items()))


if __name__ == '__main__':
    main()
