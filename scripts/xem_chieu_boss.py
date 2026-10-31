"""Hư Ảnh's six big skills (c1-c6) as the game plays them: each skill's 12 frames from its atlas (img/vg/hu/c<n>.png,
the meta in js/vung-dat.js VG.hu), on a sheet with how long each frame shows (game/src/vung-dat.js HU_T: the warning
row across warn ms, the strike and burst rows at row ms a frame), and as animated GIFs: nhip-cu (one frame each 320-450 ms,
as before 30/10), nhip-moi (as the game plays them now: playAt); with --ms N one more at N ms a frame.
    python scripts/xem_chieu_boss.py [--ms 90]      -> build/xem-chieu-boss/
"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, 'build', 'game', 'tien-hoa')
OUT = os.path.join(ROOT, 'build', 'xem-chieu-boss')
FONT = os.path.join(ROOT, 'assets', 'font', 'DejaVuSans-Bold.ttf')
NAMES = {'c1': 'Chieu 1', 'c2': 'Chieu 2', 'c3': 'Chieu 3', 'c4': 'Chieu 4', 'c5': 'Chieu 5', 'c6': 'Chieu 6 (tuyet chieu)'}


def game_numbers():
    src = open(os.path.join(ROOT, 'game', 'src', 'vung-dat.js'), encoding='utf-8').read()
    t = re.search(r'const HU_T = \{([^}]*)\}', src).group(1)
    num = lambda k: float(re.search(rf'\b{k}: ([0-9.]+)', t).group(1))
    vg = open(os.path.join(PAGE, 'js', 'vung-dat.js'), encoding='utf-8').read().split('\n')
    line = next(l for l in vg if l.strip().startswith('const VG = '))
    fast = float(re.search(r'const HU_FAST = ([0-9.]+)', src).group(1))
    return {'warn': num('warn'), 'warnUlt': num('warnUlt'), 'row': num('row'), 'fast': fast}, json.loads(line[line.index('{'):line.rindex('}') + 1])['hu']


def frames(name, meta):
    atlas = Image.open(os.path.join(PAGE, 'img', 'vg', 'hu', name + '.png')).convert('RGBA')
    cw, ch = meta['cw'], meta['ch']
    out = []
    for sx, sy, w, h, ox, oy in meta['f']:          # each frame placed in a cw x ch cell by its offset from the centre
        cell = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
        cell.alpha_composite(atlas.crop((sx, sy, sx + w, sy + h)), (cw // 2 + ox, ch // 2 + oy))
        out.append(cell)
    return out


def play_row(first, n, v, d, once, fast):
    """game/src/vung-dat.js row(): [i, j, t], frame i fading into frame j"""
    if n <= 1:
        return first, first, 0
    if once or n * fast >= d:
        k = min(n - 1, v / (d / n)); i = int(k)
        return (first + n - 1, first + n - 1, 0) if i >= n - 1 else (first + i, first + i + 1, k - i)
    if v < (n - 1) * fast:
        k = v / fast; i = int(k)
        return first + i, first + i + 1, k - i
    w = (v - (n - 1) * fast) / fast; p = int(w); a = n - 2 if p % 2 else n - 1
    return first + a, first + (2 * n - 3 - a), w - p


def fade(im, a):
    if a >= 1:
        return im
    out = im.copy()
    out.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    return out


def timing(n, rows, T):
    warn = T['warnUlt'] if n == 'c6' else T['warn']
    return [warn / rows[0]] * rows[0] + [T['row']] * (rows[1] + rows[2])


def main():
    os.makedirs(OUT, exist_ok=True)
    T, HU = game_numbers()
    cmp_ms = int(sys.argv[sys.argv.index('--ms') + 1]) if '--ms' in sys.argv else None
    font = ImageFont.truetype(FONT, 15)
    small = ImageFont.truetype(FONT, 12)
    sheets = []
    for n in ['c1', 'c2', 'c3', 'c4', 'c5', 'c6']:
        meta = HU[n]
        fr = frames(n, meta)
        rows = [4, 3, 4] if len(fr) == 11 else [4, 4, 4]
        ms = timing(n, rows, T)
        bg = (24, 14, 34, 255)
        k = 1.0
        cw, ch = meta['cw'], meta['ch']
        sheet = Image.new('RGBA', (cw * 4 + 10, 30 + 3 * (ch + 22)), bg)
        d = ImageDraw.Draw(sheet)
        d.text((8, 6), f'{NAMES[n]}: {len(fr)} khung, tong {sum(ms) / 1000:.1f} s', font=font, fill=(255, 226, 160))
        i = 0
        for r, cnt in enumerate(rows):
            for c in range(cnt):
                x, y = 5 + c * cw, 30 + r * (ch + 22)
                sheet.alpha_composite(fr[i], (x, y))
                d.text((x + 4, y + ch + 2), f'#{i + 1}  {ms[i]:.0f} ms', font=small, fill=(220, 210, 240))
                i += 1
        sheet.save(os.path.join(OUT, f'{n}_khung.png'))
        sheets.append(sheet)
        # the GIF as the game plays it (and, to compare, at cmp_ms a frame); on the arena's dark violet
        def gif(path, durations):
            pics = []
            for f in fr:
                p = Image.new('RGBA', (cw, ch), bg); p.alpha_composite(f)
                pics.append(p.convert('RGB').convert('P', palette=Image.ADAPTIVE))
            pics[0].save(path, save_all=True, append_images=pics[1:], duration=[int(round(x)) for x in durations], loop=0, disposal=2)
        gif(os.path.join(OUT, f'{n}_nhip-cu.gif'), ms)
        if cmp_ms:
            gif(os.path.join(OUT, f'{n}_{cmp_ms}ms.gif'), [cmp_ms] * len(fr))
        # as the game plays it now (vung-dat.js playAt: rows at HU_FAST, the last two swinging, one frame fading into
        # the next), at 30 frames a second
        warn = T['warnUlt'] if n == 'c6' else T['warn']
        strike, end = warn + rows[1] * T['row'], warn + (rows[1] + rows[2]) * T['row']
        pics, u = [], 0.0
        while u < end:
            if u < warn: i, j, t = play_row(0, rows[0], u, warn, False, T['fast'])
            elif u < strike: i, j, t = play_row(rows[0], rows[1], u - warn, strike - warn, False, T['fast'])
            else: i, j, t = play_row(rows[0] + rows[1], rows[2], u - strike, end - strike, True, T['fast'])
            p = Image.new('RGBA', (cw, ch), bg)
            p.alpha_composite(fade(fr[i], 1 - t))
            if t > 0.04: p.alpha_composite(fade(fr[j], t))
            pics.append(p.convert('RGB').convert('P', palette=Image.ADAPTIVE))
            u += 1000 / 30
        pics[0].save(os.path.join(OUT, f'{n}_nhip-moi.gif'), save_all=True, append_images=pics[1:], duration=33, loop=0)
    W = max(s.width for s in sheets)
    allsheet = Image.new('RGBA', (W * 3, max(s.height for s in sheets) * 2), (12, 8, 18, 255))
    for i, s in enumerate(sheets):
        allsheet.alpha_composite(s, ((i % 3) * W, (i // 3) * s.height))
    allsheet.convert('RGB').save(os.path.join(OUT, 'tat-ca_khung.png'))
    print(f'{OUT}: warn {T["warn"]:.0f} ms (ult {T["warnUlt"]:.0f}), {T["row"]:.0f} ms a frame after')


if __name__ == '__main__':
    main()
