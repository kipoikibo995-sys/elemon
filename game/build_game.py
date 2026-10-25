"""Builds build/game/: HoLua, the game. Its body is MiniMon's demo page as it is (scripts/evo_app.html and
build_evo_app.py, the demo the user approves); on top of it go the real game (game/src/song-that.js: the save,
real time, the pace of growing up) and the 8-bit sounds (r36s/js/am-thanh.js). Both only wrap the page's own
functions, so a rebuild takes in whatever the demo changed; game/check_minimon.py tells when it has.

build/game/
    tien-hoa/                 the page: build_evo_app.py's output (index.html, data.js, img/, pets/<id>.json, font/)
        js/song-that.js       the real game
        js/am-thanh.js        the sounds
        sfx/, nhac/           assets/am-thanh (make_sfx_8bit.py)
    pets -> assets/creatures-640    a junction, like preview/pets: the page reads its frames from ../pets/
If the demo cannot be built right now (MiniMon in the middle of editing it), its last build (preview/tien-hoa/) is
used instead, and the build says so.
Browser: the holua-game preview server (build/game, port 8771), page /tien-hoa/
R36S:    python scripts/r36s_game.py      (packs build/game/tien-hoa for the handheld)
Usage:   python game/build_game.py
"""
import glob, importlib, json, os, shutil, subprocess, sys, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
os.environ['HOLUA_SCREEN'] = '640'

OUT = os.path.join(ROOT, 'build', 'game')
PAGE = os.path.join(OUT, 'tien-hoa')
PETS = os.path.join(OUT, 'pets')
DEMO_BUILT = os.path.join(ROOT, 'preview', 'tien-hoa')
KEEP = {'pets'}                      # the junction: never removed here (deleting through it would hit the frames)

# put in the page right before </body>: browser-only parts first (the R36S packer leaves them out), then the layers
ADD = '''<script data-browser-only>
// in a browser: the sounds through <audio> (on the R36S r36s/js/shim.js makes SOUND); music waits for a first key
window.SOUND = (() => {
  const cache = {}, play = a => a.play().catch(() => {});
  let song = null;
  for (const ev of ['keydown', 'pointerdown']) addEventListener(ev, () => { if (song && song.paused) play(song); });
  return {
    sfx(name, vol) {
      const a = (cache[name] = cache[name] || new Audio(`sfx/${name}.wav`)).cloneNode();
      a.volume = Math.min(1, vol / 256); play(a);
    },
    music(name) {
      if (song) song.pause();
      song = null;
      if (!name) return;
      song = new Audio(`nhac/${name}.wav`); song.loop = true; song.volume = 0.5; play(song);
    },
  };
})();
// a button beside "Chơi lại" that clears the save (testing in a browser)
(() => {
  const r = document.getElementById('btnR');
  if (!r) return;
  r.insertAdjacentHTML('afterend', ' <button class="restart" id="xoaLuu">Xóa bản lưu</button>');
  document.getElementById('xoaLuu').onclick = () => {
    if (!confirm('Xóa bản lưu của game?')) return;
    window.__noSave = true; localStorage.removeItem('holua-save-1'); location.reload();
  };
})();
</script>
<script src="js/song-that.js"></script>
<script src="js/vo-duong.js"></script>
<script src="js/am-thanh.js"></script>
<script src="js/set-huyen-thoai.js"></script>
<script src="js/nen-chi-so.js"></script>
<script data-browser-only src="js/nut-thu.js"></script>
'''
# the golden sparks round a Huyền thoại pet (game/src/set-huyen-thoai.js): 4x3 sparks a sheet on magenta
SPARKS = os.path.join(ROOT, 'assets', 'source', 'tinh-linh', 'huyen-thoai-fx', 'set-vang_tia-manh*.png')
SPARK_MAX = 96                       # px, the longest side of a cut spark (drawn at ~15 % of the pet's height)
# small wording changes for the real game: (demo text, game text); one the demo no longer has is skipped
WORDING = [
    ("'chăm sóc, tập luyện (L2: tua nhanh)'", "'chăm sóc, tập luyện mỗi ngày'"),
    ("'R2 chơi · X vuốt ve · L2 tua nhanh'", "'R2 chơi · X vuốt ve'"),
    ("'Bản demo: tua nhanh ¼ giai đoạn; ở mốc cấp thì mở bảng tiến hóa'", "'Ở mốc cấp: mở bảng tiến hóa'"),
    ('<title>Elemon demo R36S - từ trứng tới Huyền thoại</title>', '<title>Elemon</title>'),
]


def clean():
    os.makedirs(OUT, exist_ok=True)
    for name in os.listdir(OUT):
        if name in KEEP:
            continue
        p = os.path.join(OUT, name)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    if not os.path.exists(PETS):          # a junction needs no admin rights on Windows
        subprocess.run(['cmd', '/c', 'mklink', '/J', PETS, os.path.join(ROOT, 'assets', 'creatures-640')],
                       check=True, capture_output=True)


def build_page():
    """MiniMon's demo built into build/game/tien-hoa; its last build if it cannot be built now."""
    try:
        bea = importlib.import_module('build_evo_app')
        bea.OUT, bea.PETS_LINK = PAGE, PETS
        bea.main()
        return 'dựng mới từ scripts/evo_app.html'
    except Exception:
        traceback.print_exc()
        if not os.path.exists(os.path.join(DEMO_BUILT, 'index.html')):
            raise SystemExit('demo chưa dựng được và chưa có bản dựng sẵn (preview/tien-hoa)')
        if os.path.exists(PAGE):
            shutil.rmtree(PAGE)
        shutil.copytree(DEMO_BUILT, PAGE)
        return 'demo đang sửa dở: dùng bản dựng sẵn preview/tien-hoa'


def cut_sparks():
    """The spark sheets cut into img/tia_<n>.png (magenta made clear, trimmed, scaled down); how many there are."""
    import numpy as np
    from PIL import Image
    n = 0
    for sheet in sorted(glob.glob(SPARKS)):
        im = np.array(Image.open(sheet).convert('RGBA'))
        h, w = im.shape[:2]
        for r in range(3):
            for c in range(4):
                cell = im[round(r * h / 3):round((r + 1) * h / 3), round(c * w / 4):round((c + 1) * w / 4)].copy()
                key = (cell[..., 0] > 170) & (cell[..., 1] < 110) & (cell[..., 2] > 170)
                cell[key, 3] = 0
                ys, xs = np.nonzero(cell[..., 3])
                if not len(xs):
                    continue
                sp = Image.fromarray(cell[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
                k = min(1, SPARK_MAX / max(sp.size))
                sp = sp.resize((max(1, round(sp.width * k)), max(1, round(sp.height * k))), Image.LANCZOS)
                sp.save(os.path.join(PAGE, 'img', f'tia_{n}.png'), optimize=True)
                n += 1
    return n


def copy_dojo():
    """Võ đường's pictures (assets/r36s/vo-duong/menu, tap-luyen, ne-chieu) -> img/vd/menu, tap, ne (game/src/vo-duong.js)."""
    src = os.path.join(ROOT, 'assets', 'r36s', 'vo-duong')
    for part, dst in (('menu', 'menu'), ('tap-luyen', 'tap'), ('ne-chieu', 'ne')):
        os.makedirs(os.path.join(PAGE, 'img', 'vd', dst), exist_ok=True)
        for p in glob.glob(os.path.join(src, part, '*.png')):
            shutil.copy(p, os.path.join(PAGE, 'img', 'vd', dst))
    # Học né chiêu's stone courtyard: only the full-size drawing so far, brought to screen size here
    from PIL import Image
    yard = os.path.join(ROOT, 'assets', 'source', 'vo-duong', 'VD_nen_san-da.png')
    if os.path.exists(yard):
        Image.open(yard).convert('RGB').resize((640, 480), Image.LANCZOS).save(
            os.path.join(PAGE, 'img', 'vd', 'ne', 'nen_san-da.png'), optimize=True)


def stats_pieces():
    """For game/src/nen-chi-so.js: the pedestal of the pet box (drawn by the game, sized to the pet), where it stands,
    and the layout of the live values (live_stats, which also draws the pages without pedestal and values)."""
    import preview_ui_stats as U                  # the same pedestal, size and place as the demo's pages
    ped = U.piece('be-dung_hoa', U.TARGETS['r36s'], 1.0)
    ped.save(os.path.join(PAGE, 'img', 'stats_be.png'), optimize=True)
    return dict(be=[130 - ped.width // 2, U.PET_FEET - round(ped.height * 0.42), ped.width, ped.height],
                feet=U.PET_FEET, live=live_stats())


# Hồ sơ: what a pet likes (its element's first food) and dislikes (the food of the element that overcomes its own)
HE_FOOD = {'hoa': 'Hoa_1_roasted-chili-pepper', 'kim': 'Kim_1_iron-crunch-biscuit', 'moc': 'Moc_1_green-leaf-bundle',
           'thuy': 'Thuy_1_fresh-fish', 'tho': 'Tho_1_roasted-corn'}


def live_stats():
    """The 4 stats pages drawn again by preview_ui_stats.py (the same pieces and layout as the demo's) without the
    pet box's pedestal and name lines (the game draws the pedestal sized to the pet) and, on Sinh tồn, Linh khí and
    Hồ sơ, with every value left out: bars empty, no numbers, no radar shape, empty hearts (Thuộc tính is already
    live in the demo: drawn as the demo does, U.LIVE). Where each value goes is noted, and game/src/nen-chi-so.js
    draws the pet's own values there. The pages replace the demo's stats_<stage>_<page>.png. Returns that layout."""
    import re
    import numpy as np
    from PIL import Image
    import preview_ui_stats as U
    stages = json.loads(open(os.path.join(PAGE, 'data.js'), encoding='utf-8').read().split('=', 1)[1].rstrip().rstrip(';'))['stats_stages']
    keep, pet_frame, piece, live = dict(U.PET), U.Screen.pet_frame, U.piece, U.LIVE
    U.Screen.pet_frame = lambda *a, **k: None
    U.LIVE = True
    U.piece = lambda name, *a, **k: (Image.new('RGBA', piece(name, *a, **k).size, (0, 0, 0, 0)) if name == 'be-dung_hoa'
                                     else piece(name, *a, **k))
    lay = dict(bars=[], nums=[], radar=[], hs={})
    try:
        U.PET.update(survival=[(n, 50) for n, _ in keep['survival']], linh_khi={k: 0 for k in keep['linh_khi']},
                     level=77, exp=(1, 2), personality=(keep['personality'][0], '§P'), closeness=0, likes=(keep['likes'][0], '§L'),
                     dislikes=(keep['dislikes'][0], '§D'), weight=19, home=('§H', '§B'))
        bg, sprites, glyphs = U.build('r36s')
        ui = U.read_ui(U.pack_ui(bg, sprites, glyphs))
        mark = {'77': 'badge', 'Level 77': 'level', '§P': 'pers', '§L': 'likes_t', '§D': 'dislikes_t', '§H': 'home',
                '§B': 'home2'}
        pages = {}
        for page in (0, 1, 2, 3):
            sc = U.Screen(ui, None, U.TARGETS['r36s'])
            text0, bar0, sprite0 = sc.text, sc.bar, sc.sprite

            def text(s, x, y, style, colour, align='left', page=page, text0=text0):
                spot = dict(x=x, y=y, size=U.SIZES[style][0], bold=U.SIZES[style][1], colour='#%02x%02x%02x' % tuple(colour),
                            align=align)
                if x == 130:                                   # name lines in the pet box: drawn live
                    return
                if page == 0 and s.isdigit():
                    return lay['nums'].append(spot)
                m = re.match(r'^(\S+) 0$', s)
                if page == 1 and m:
                    return lay['radar'].append(dict(spot, name=m.group(1)))
                if page == 3 and (s in mark or s.startswith('EXP 1/2') or s.startswith('Thể trạng')):
                    lay['hs'][mark.get(s, 'exp' if s.startswith('EXP') else 'weight_t')] = spot
                    return
                text0(s, x, y, style, colour, align)

            def bar(x, y, fill, value, sprite='bar', fill_sprite=None, page=page, bar0=bar0):
                if page == 0:
                    lay['bars'].append(dict(x=x, y=y, fill=fill))
                else:
                    lay['hs']['expbar'] = dict(x=x, y=y)
                bar0(x, y, fill, 0, sprite, fill_sprite)

            def sprite(name, x, y, clip_w=None, sprite0=sprite0):
                if name == 'tim-rong':
                    lay['hs'].setdefault('hearts', []).append([x, y])
                elif name in ('likes', 'dislikes'):
                    w, h = sprites[name].size
                    lay['hs'][name] = [x + w // 2, y + h // 2]
                    return
                elif name == 'weight_mark':
                    return
                elif name == 'weight_bar':
                    lay['hs']['wbar'] = [x, y, sprites[name].width, sprites[name].height]
                sprite0(name, x, y, clip_w)

            sc.text, sc.bar, sc.sprite = text, bar, sprite
            U.draw_page(sc, page, ('idle-0', 0, 0, 0))
            pages[page] = Image.fromarray(np.asarray(sc.px, np.uint8))
        for st in stages:
            for page, im in pages.items():
                im.save(os.path.join(PAGE, 'img', f'stats_{st}_{page}.png'), optimize=True)
        # the pieces the live values are drawn with
        for col in {f for _, f in U.SURVIVAL_LOOK}:
            sprites['fill_' + col].save(os.path.join(PAGE, 'img', f'hs_fill_{col}.png'))
        for name in ('exp_fill', 'tim-day', 'weight_mark'):
            sprites[name].save(os.path.join(PAGE, 'img', f'hs_{name}.png'))
        for f in HE_FOOD.values():
            U.food_icon(f, 34).save(os.path.join(PAGE, 'img', f'hs_food_{f}.png'))
        rd = sprites['radar']
        rx, ry = 450 - rd.width // 2, 78
        lay.update(barH=sprites['bar'].height, expH=sprites['exp_bar'].height, foods=HE_FOOD,
                   weight=list(keep['weight_range']),
                   radarC=[rx + rd.width / 2, ry + rd.height * 0.535, rd.height * 0.44 * 0.80],
                   radarKeys=[k for k, *_ in U.RADAR], radarNames=[n for _, n, _ in U.RADAR])
    finally:
        U.PET.clear(); U.PET.update(keep)
        U.Screen.pet_frame, U.piece, U.LIVE = pet_frame, piece, live
    return lay


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    clean()
    how = build_page()
    os.makedirs(os.path.join(PAGE, 'js'), exist_ok=True)
    shutil.copy(os.path.join(HERE, 'src', 'song-that.js'), os.path.join(PAGE, 'js'))
    shutil.copy(os.path.join(HERE, 'src', 'nut-thu.js'), os.path.join(PAGE, 'js'))       # test buttons (browser)
    shutil.copy(os.path.join(HERE, 'src', 'vo-duong.js'), os.path.join(PAGE, 'js'))
    copy_dojo()
    shutil.copy(os.path.join(ROOT, 'r36s', 'js', 'am-thanh.js'), os.path.join(PAGE, 'js'))
    sparks = cut_sparks()
    src = open(os.path.join(HERE, 'src', 'set-huyen-thoai.js'), encoding='utf-8').read()
    open(os.path.join(PAGE, 'js', 'set-huyen-thoai.js'), 'w', encoding='utf-8', newline='\n').write(
        src.replace('__TIA_N__', str(sparks)))
    import json
    src = open(os.path.join(HERE, 'src', 'nen-chi-so.js'), encoding='utf-8').read()
    open(os.path.join(PAGE, 'js', 'nen-chi-so.js'), 'w', encoding='utf-8', newline='\n').write(
        src.replace('__NEN_CHI_SO__', json.dumps(stats_pieces())))
    for kind in ('sfx', 'nhac'):
        os.makedirs(os.path.join(PAGE, kind), exist_ok=True)
        for p in glob.glob(os.path.join(ROOT, 'assets', 'am-thanh', kind, '*.wav')):
            shutil.copy(p, os.path.join(PAGE, kind))
    path = os.path.join(PAGE, 'index.html')
    html = open(path, encoding='utf-8').read()
    skipped = []
    for old, new in WORDING:
        if old in html:
            html = html.replace(old, new)
        else:
            skipped.append(old[:50])
    # a build stamp on the layers, so a browser never runs an old copy from its cache (the R36S packer drops it)
    i, stamp = html.rindex('</body>'), int(time.time())
    html = html[:i] + ADD.replace('.js"', f'.js?v={stamp}"') + html[i:]
    open(path, 'w', encoding='utf-8', newline='\n').write(html)
    # the demo page this build was made from (check_minimon.py compares it with the demo now)
    shutil.copy(os.path.join(ROOT, 'scripts', 'evo_app.html'), os.path.join(HERE, 'minimon-base.html'))
    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(PAGE) for f in fs)
    print(f'{PAGE}: {how}, {size / 2 ** 20:.1f} MB (khung hình pet đọc qua build/game/pets), {sparks} tia sét')
    for s in skipped:
        print(f'  bỏ qua sửa chữ (demo không còn dòng này): {s}')


if __name__ == '__main__':
    main()
