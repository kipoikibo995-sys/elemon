"""A browser build of the game packed to run as it is on the R36S under QuickJS (r36s/jsrt.c + r36s/js/shim.js):
the game itself (build/game/tien-hoa/, made by game/build_game.py) or MiniMon's demo page (preview/tien-hoa/, --demo).

dist/elemon/Elemon.sh                     launcher (Ports); saves go to ports/elemon-save/, kept by a reinstall
dist/elemon/elemon/
    js/load.txt                           the scripts to run, in the order of index.html (js/shim.js first);
                                          <script data-browser-only> is left out (the shim does that part)
    every file of the build                pictures as .hli (r36s_app.py), the rest as it is
    up/pets/<dir>/<frame>.hli             the pet frames the page reads beside itself (../pets/, listed in
                                          pets/<id>.json); the shim reads ../ as up/
    font/<size><b|r>.hli, .txt            DejaVu Sans for every character in the scripts, 10-30 px
    sfx/, nhac/                           assets/am-thanh (make_sfx_8bit.py)
    buttons.txt, cover.png
The program itself: scripts/build-r36s.ps1 (elemon). Pictures are 8-bit with alpha per colour when that
looks the same (r36s_pak.to_palette), otherwise full colour.
Usage: python r36s_game.py [page dir]         (default build/game/tien-hoa)
       python r36s_game.py --demo [--build]   (MiniMon's page; --build runs build_evo_app.py first)
"""
import glob, json, os, re, shutil, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r36s_pak
from r36s_app import write_hli

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist', 'elemon')
GAME = os.path.join(DIST, 'elemon')
FONTS = {0: os.path.join(ROOT, 'assets', 'font', 'DejaVuSans.ttf'), 1: os.path.join(ROOT, 'assets', 'font', 'DejaVuSans-Bold.ttf')}
# DejaVu is about 11 % wider than the Tahoma the pages are laid out with: glyphs are narrowed to match
NARROW = 0.89
SIZES = [*range(9, 31), 32]        # what the pages ask for (big titles: 32, the arena's small labels: 9)


def picture(src, dst):
    im = Image.open(src)
    if im.mode not in ('RGB', 'RGBA', 'P'):
        im = im.convert('RGBA')
    if im.mode == 'P' and not (im.palette and im.palette.mode == 'RGBA') and 'transparency' not in im.info:
        im = im.convert('RGB')
    elif im.mode == 'P':
        im = im.convert('RGBA')
    if im.mode == 'RGBA' and np.array(im)[..., 3].min() == 255:
        im = im.convert('RGB')
    if im.mode == 'RGBA':
        q, err = r36s_pak.to_palette(im)
        im = q or im
    elif im.width * im.height > 4096:
        q, err = r36s_pak.to_palette(im.convert('RGBA'))
        if q is not None:
            im = q
    write_hli(dst, im)


def font_set(size, bold, chars, out):
    font = ImageFont.truetype(FONTS[bold], size)
    asc, desc = font.getmetrics()
    top = min(0, min(font.getbbox(ch)[1] for ch in chars))
    bottom = max(asc + desc, max(font.getbbox(ch)[3] for ch in chars))
    row_h, atlas_w = bottom - top + 2, 1024
    cells, x, y = [], 0, 0
    for ch in chars:
        l, t, r, b = font.getbbox(ch)
        w = max(1, r - l)
        img = Image.new('L', (w + 2, row_h), 0)
        ImageDraw.Draw(img).text((1 - l, -top), ch, font=font, fill=255)
        nw = max(1, round(img.width * NARROW))
        img = img.resize((nw, row_h), Image.LANCZOS)
        if x + nw + 1 > atlas_w:
            x, y = 0, y + row_h
        cells.append((ch, x, y, img, round((l - 1) * NARROW), round(font.getlength(ch) * NARROW)))
        x += nw + 1
    atlas = Image.new('RGBA', (atlas_w, y + row_h), (255, 255, 255, 0))
    lines = [f'metrics {asc} {desc}']
    for ch, gx, gy, img, l, adv in cells:
        atlas.paste(Image.merge('RGBA', (*[Image.new('L', img.size, 255)] * 3, img)), (gx, gy))
        lines.append(f'glyph {ord(ch)} {gx} {gy} {img.width} {row_h} {l} {adv} {top}')
    name = f'{size}{"b" if bold else "r"}'
    write_hli(os.path.join(out, name + '.hli'), atlas)
    with open(os.path.join(out, name + '.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')


def scripts_of(src, html):
    """The page's scripts in order: (path in the build, or None with the inline text)."""
    out = []
    for m in re.finditer(r'<script([^>]*)>(.*?)</script>', html, re.S):
        attrs, body = m.group(1), m.group(2)
        if 'data-browser-only' in attrs:
            continue
        s = re.search(r'\bsrc="([^"]+)"', attrs)
        if s:
            out.append((re.sub(r'[?#].*$', '', s.group(1)), None))
        elif body.strip():
            out.append((None, body))
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    demo = '--demo' in sys.argv
    src = os.path.join(ROOT, 'preview', 'tien-hoa') if demo else os.path.abspath(args[0] if args else os.path.join(ROOT, 'build', 'game', 'tien-hoa'))
    if demo and '--build' in sys.argv:
        subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'build_evo_app.py')], check=True)
    html = open(os.path.join(src, 'index.html'), encoding='utf-8').read()
    # the program (scripts/build-r36s.ps1) is kept across a repack
    prog = os.path.join(GAME, 'elemon')
    keep = open(prog, 'rb').read() if os.path.isfile(prog) else None
    if os.path.exists(GAME):
        shutil.rmtree(GAME)
    os.makedirs(os.path.join(GAME, 'js'))
    if keep:
        open(prog, 'wb').write(keep)
    # every file of the build: pictures become .hli, the rest is copied (not the page's own title font: fonts here
    # are the bitmap sets below, and the page does without it)
    jobs = []
    for dp, _, fs in os.walk(src):
        if os.path.basename(dp).startswith('_'):
            continue
        for f in fs:
            rel = os.path.relpath(os.path.join(dp, f), src)
            if rel == 'index.html' or f.endswith(('.ttf', '.otf', '.woff', '.woff2')):
                continue
            dst = os.path.join(GAME, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if f.endswith('.png'):
                jobs.append((os.path.join(dp, f), os.path.splitext(dst)[0] + '.hli'))
            else:
                shutil.copy(os.path.join(dp, f), dst)
    # the pet frames beside the page (../pets/<dir>/<frame>.png, from pets/<id>.json) -> up/pets/
    for pj in glob.glob(os.path.join(src, 'pets', '*.json')):
        for st in json.load(open(pj, encoding='utf-8')).get('stages', {}).values():
            for f in st['meta']['frames']:
                a = os.path.join(src, '..', 'pets', st['dir'], f + '.png')
                if os.path.exists(a):
                    b = os.path.join(GAME, 'up', 'pets', st['dir'], f + '.hli')
                    os.makedirs(os.path.dirname(b), exist_ok=True)
                    jobs.append((a, b))
    with ProcessPoolExecutor() as pool:
        list(pool.map(picture, *zip(*jobs), chunksize=32))
    n_pics = len(jobs)
    load = ['js/shim.js']
    shutil.copy(os.path.join(ROOT, 'r36s', 'js', 'shim.js'), os.path.join(GAME, 'js'))
    for i, (path, body) in enumerate(scripts_of(src, html)):
        if path is None:
            path = f'js/inline-{i}.js'
            with open(os.path.join(GAME, path), 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(body)
        load.append(path)
    if demo:                                     # the demo has no sound of its own: hooked on from outside
        shutil.copy(os.path.join(ROOT, 'r36s', 'js', 'am-thanh.js'), os.path.join(GAME, 'js'))
        load.append('js/am-thanh.js')
    # Solo đối kháng: the arena's sheets cut ahead of time, its HUD, arenas and sounds (solo_r36s.py), read before solo.js
    if 'js/solo.js' in load:
        import solo_r36s
        print('Solo đối kháng:', solo_r36s.build(GAME), 'sheet đã cắt sẵn')
        load.insert(load.index('js/solo.js'), 'js/solo-cuts.js')
    with open(os.path.join(GAME, 'js', 'load.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(load) + '\n')
    text = ''.join(open(os.path.join(GAME, p), encoding='utf-8').read() for p in load)
    chars = sorted(set(c for c in text if 160 <= ord(c) < 0x3000) | set(chr(c) for c in range(32, 127)))
    os.makedirs(os.path.join(GAME, 'font'), exist_ok=True)
    for size in SIZES:
        for bold in (0, 1):
            font_set(size, bold, chars, os.path.join(GAME, 'font'))
    for kind in ('sfx', 'nhac'):
        os.makedirs(os.path.join(GAME, kind), exist_ok=True)
        for p in glob.glob(os.path.join(ROOT, 'assets', 'am-thanh', kind, '*.wav')):
            shutil.copy(p, os.path.join(GAME, kind))
    for name, dst in (('Elemon.sh', os.path.join(DIST, 'Elemon.sh')), ('buttons-game.txt', os.path.join(GAME, 'buttons.txt'))):
        with open(os.path.join(ROOT, 'r36s', name), encoding='utf-8') as a, open(dst, 'w', encoding='utf-8', newline='\n') as b:
            b.write(a.read())
    cover = os.path.join(ROOT, 'preview', 'r36s', 'elemon-cover.png')
    if os.path.exists(cover):
        shutil.copy(cover, os.path.join(GAME, 'cover.png'))
    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(DIST) for f in fs)
    print(f'{DIST} <- {os.path.relpath(src, ROOT)}: {n_pics} hình, {len(load)} script, {len(chars)} chữ x '
          f'{len(SIZES) * 2} cỡ, {size / 2 ** 20:.1f} MB')


if __name__ == '__main__':
    main()
