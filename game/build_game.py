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
KEEP = {'pets', 'solo'}              # the junctions: never removed here (deleting through them would hit the sources)
ARENA = os.path.join(ROOT, 'preview', 'dau-truong')       # the combat session's arena: Solo đối kháng (game/src/solo.js)
SOLO = os.path.join(OUT, 'solo')

# put in the page right before </body>: browser-only parts first (the R36S packer leaves them out), then the layers
ADD = '''<script data-browser-only>
// in a browser: the sounds through <audio> (on the R36S r36s/js/shim.js makes SOUND); music waits for a first key
window.SOUND = (() => {
  const V = '__SND_V__';                     // the build: a browser never plays an old copy from its cache
  const cache = {}, play = a => a.play().catch(() => {});
  let song = null;
  for (const ev of ['keydown', 'pointerdown']) addEventListener(ev, () => { if (song && song.paused) play(song); });
  return {
    sfx(name, vol) {
      const a = (cache[name] = cache[name] || new Audio(`sfx/${name}.wav?v=${V}`)).cloneNode();
      a.volume = Math.min(1, vol / 256); play(a);
    },
    music(name) {
      if (song) song.pause();
      song = null;
      if (!name) return;
      song = new Audio(`nhac/${name}.wav?v=${V}`); song.loop = true; song.volume = 0.5; play(song);
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
    window.__noSave = true; for (const k of ['holua-save-1', 'holua-save-1-bak']) localStorage.removeItem(k); location.reload();
  };
})();
</script>
<script src="js/song-that.js"></script>
<script src="js/di-bo.js"></script>
<script src="js/ve-nhanh.js"></script>
<script src="js/vo-duong.js"></script>
<script src="js/solo-arena.js"></script>
<script src="js/solo.js"></script>
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
    # the stroll eases in and out (game/src/di-bo.js)
    ('    S.px = S.walk.from + (S.walk.to - S.walk.from) * t;',
     "    S.px = S.walk.from + (S.walk.to - S.walk.from) * (typeof walkEase === 'function' ? walkEase(t, S.walk.dur) : t);"),
]


def clean():
    os.makedirs(OUT, exist_ok=True)
    for name in os.listdir(OUT):
        if name in KEEP:
            continue
        p = os.path.join(OUT, name)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    for link, target in ((PETS, os.path.join(ROOT, 'assets', 'creatures-640')), (SOLO, ARENA)):
        if not os.path.exists(link) and os.path.exists(target):     # a junction needs no admin rights on Windows
            if os.name == 'nt':
                subprocess.run(['cmd', '/c', 'mklink', '/J', link, target], check=True, capture_output=True)
            else:
                os.symlink(target, link, target_is_directory=True)


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


SIDE_PX = 190                       # px, the larger side of the Solo pick screen's standing pet


# the camouflage checker: whole runs of pixels cleared at once (same holes as the pixel-by-pixel loop, far fewer steps
# for the R36S's interpreter)
DITHER_LOOP = "for (let yy = 0; yy < o.height; yy++) for (let xx = 0; xx < o.width; xx++) if (((xx / b | 0) + (yy / b | 0)) % 2) p[(yy * o.width + xx) * 4 + 3] = 0;"
DITHER_RUNS = ("{ const u = new Uint32Array(p.buffer, p.byteOffset, o.width * o.height), W = o.width; "
               "for (let yy = 0; yy < o.height; yy++) { const r = yy * W; "
               "for (let xx = (yy / b | 0) % 2 ? 0 : b; xx < W; xx += 2 * b) u.fill(0, r + xx, r + Math.min(W, xx + b)); } }")
# the aiming funnel and arrow: drawn cell by cell every frame (~8000 cells, thousands of 2 px fills) they cost the
# R36S more than the fight; here each funnel (its base angle) and arrow (its 32 directions) is drawn once into a
# picture, put down on the same 2 px grid round the pet
AIM = r'''const AIM_FUNNELS = new Map(), AIM_ARROWS = new Map(), AIM_SHAPES = new Map();
function aimCanvas(n) { const c = document.createElement('canvas'); c.width = c.height = n * BLK; return c; }
// a picture made in one go from cells: cells[i] = 0 (empty) or an RGBA colour, n x n cells of BLK x BLK pixels
function aimPaint(n, cells) {
  const c = aimCanvas(n), g = c.getContext('2d'), W = n * BLK, im = g.createImageData(W, W), u = new Uint32Array(im.data.buffer);
  for (let ly = 0; ly < n; ly++) for (let lx = 0; lx < n; lx++) {
    const v = cells[ly * n + lx];
    if (v) for (let yy = 0; yy < BLK; yy++) u.fill(v, (ly * BLK + yy) * W + lx * BLK, (ly * BLK + yy) * W + lx * BLK + BLK);
  }
  g.putImageData(im, 0, 0);
  return c;
}
const aimRgba = h => { const v = parseInt(h.slice(1), 16); return (255 << 24 | (v & 255) << 16 | (v >> 8 & 255) << 8 | v >> 16) >>> 0; };
function drawAim(f) {
  const a = f.aiming;
  if (!a) return;
  const pal = f.bot ? ['#8fd8ff', '#2a76b8', '#123a66', '#cff0ff'] : ['#ffb347', '#e0702a', '#8a3414', '#ffe08a'];
  // the funnel's drawn direction in 64 steps (the hit test keeps a.base as it is): the bot faces any way at all
  const ox = Math.round(f.x / BLK), oy = Math.round((f.y - 24) / BLK), r = 88 / BLK, R = Math.ceil(r) + 1;
  const bs = Math.round(a.base / (Math.PI / 32)), b = bs * (Math.PI / 32);
  const fk = (f.bot ? 'B' : 'P') + ((ox + oy) & 1) + ':' + (((bs % 64) + 64) % 64);
  let fn = AIM_FUNNELS.get(fk);
  if (!fn) {
    // the shape for this direction (shared by both sides and both checker phases): 1 edge, 2 outer band, 3 inside
    const n = 2 * R + 1, sk = ((bs % 64) + 64) % 64;
    let shape = AIM_SHAPES.get(sk);
    if (!shape) {
      shape = new Uint8Array(n * n);
      const angIn = t => { const d = ((t - b + Math.PI * 3) % (Math.PI * 2)) - Math.PI; return Math.abs(d) <= HALF; };
      for (let ly = 0; ly < n; ly++) for (let lx = 0; lx < n; lx++) {
        const dx = lx - R + 0.5, dy = ly - R + 0.5, d = Math.hypot(dx, dy);
        if (d < 10 || d > r) continue;
        const t = Math.atan2(dy, dx);
        if (!angIn(t)) continue;
        shape[ly * n + lx] = d > r - 1.2 || !angIn(t + 1.4 / d) || !angIn(t - 1.4 / d) ? 1 : d > r - 6 ? 2 : 3;
      }
      AIM_SHAPES.set(sk, shape);
    }
    const cells = new Uint32Array(n * n), par = (ox + oy) & 1, P = pal.map(aimRgba);
    for (let ly = 0; ly < n; ly++) for (let lx = 0; lx < n; lx++) {
      const v = shape[ly * n + lx];
      if (v) cells[ly * n + lx] = v === 1 ? P[0] : (lx + ly + par) % 2 === 0 ? P[v - 1] : 0;
    }
    fn = { c: aimPaint(n, cells), R };
    AIM_FUNNELS.set(fk, fn);
    if (AIM_FUNNELS.size > 32) { const k0 = AIM_FUNNELS.keys().next().value; AIM_FUNNELS.delete(k0); }
  }
  ctx.drawImage(fn.c, (ox - fn.R) * BLK, (oy - fn.R) * BLK);
  const step = Math.round(a.ang / (Math.PI / 16)), ak = (f.bot ? 'B' : 'P') + ((step % 32) + 32) % 32;
  let ar = AIM_ARROWS.get(ak);
  if (!ar) {
    const sa32 = step * (Math.PI / 16), ca = Math.cos(sa32), sa = Math.sin(sa32), len = r * 0.66, L = Math.ceil(len) + 4;
    const inArrow = (lx, ly) => {
      const px = lx - L + 0.5, py = ly - L + 0.5, u = px * ca + py * sa, v = -px * sa + py * ca;
      if (u >= 10 && u <= len - 5 && Math.abs(v) <= 0.75) return true;
      return u > len - 6 && u <= len && Math.abs(v) <= (len - u) * 0.7;
    };
    const n = 2 * L + 1, on = new Uint8Array(n * n);
    for (let ly = 0; ly < n; ly++) for (let lx = 0; lx < n; lx++) if (inArrow(lx, ly)) on[ly * n + lx] = 1;
    const cells = new Uint32Array(n * n), dark = aimRgba('#1a0c06'), lit = aimRgba(pal[3]);
    for (let ly = 0; ly < n; ly++) for (let lx = 0; lx < n; lx++) {
      if (on[ly * n + lx]) { cells[ly * n + lx] = lit; continue; }
      let near = false;
      for (let yy = -1; yy <= 1 && !near; yy++) for (let xx = -1; xx <= 1; xx++) {
        const X = lx + xx, Y = ly + yy;
        if (X >= 0 && Y >= 0 && X < n && Y < n && on[Y * n + X]) { near = true; break; }
      }
      if (near) cells[ly * n + lx] = dark;
    }
    ar = { c: aimPaint(n, cells), L };
    AIM_ARROWS.set(ak, ar);
  }
  ctx.drawImage(ar.c, (ox - ar.L) * BLK, (oy - ar.L) * BLK);
  if (a.k === 'i') ring(a.tx, a.ty, pal[0], 0);
}
function drawAim0(f) {'''
OUTLINED = r'''function drawOutlined(cell, x, y, flip, k) { const key = Math.round(k * 512), m = cell.__ol || (cell.__ol = new Map()); let o = m.get(key); if (!o) { if (m.size >= 4) return drawOutlined0(cell, x, y, flip, k); const b = black(cell), w = cell.w * k, h = cell.h * k, P = OUTLINE_PX + 1, c = document.createElement('canvas'); c.width = Math.ceil(w) + 2 * P; c.height = Math.ceil(h) + 2 * P; const g = c.getContext('2d'); for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1], [-0.7, -0.7], [0.7, -0.7], [-0.7, 0.7], [0.7, 0.7]]) g.drawImage(b.c, P + Math.round(dx * OUTLINE_PX), P + Math.round(dy * OUTLINE_PX), w, h); g.drawImage(cell.c, P, P, w, h); o = { c, x: Math.round(-w / 2) - P, y: Math.round(-h) - P }; m.set(key, o); } ctx.save(); ctx.globalAlpha = 1; ctx.translate(Math.round(x), Math.round(y)); if (flip) ctx.scale(-1, 1); ctx.drawImage(o.c, o.x, o.y); ctx.restore(); }
function drawOutlined0(cell, x, y, flip, k) {'''


def solo_arena():
    """The arena page's script wrapped in a function of its own (globalThis.__SOLO_SRC), run by game/src/solo.js with
    stand-ins for the page around it; and a small portrait of each pet for the pick screen. Number of pets."""
    import re
    import numpy as np
    from PIL import Image
    page = os.path.join(ARENA, 'index.html')
    if not os.path.exists(page):
        return 0
    src = re.search(r'<script>(.*)</script>', open(page, encoding='utf-8').read(), re.S).group(1).replace('\r\n', '\n')
    # small changes, harmless in a browser: a sheet already cut (the R36S, scripts/solo_r36s.py) is handed back as
    # it is; the bot always has its own pet here, so the tiger sheets are not recoloured for it; and a pet with its
    # outline is put together once per pose and size (OUTLINED), then drawn in one go instead of nine scaled draws
    for old, new in (('function cut(img, cols, rows) {', 'function cut(img, cols, rows) { if (img.__cells) return img.__cells;'),
                     ('function recolourBot() {', 'function recolourBot() { if (BOTPET) return;'),
                     ('function drawOutlined(cell, x, y, flip, k) {', OUTLINED),
                     (DITHER_LOOP, DITHER_RUNS),
                     ('function drawAim(f) {', AIM),
                     # the screen shake by whole pixels: a part-pixel shift made the backdrop (and everything) a
                     # pixel-by-pixel draw instead of a row copy, in exactly the frames where blows land
                     ('if (shake > 0) { ctx.translate((Math.random() - 0.5) * shake * 2, (Math.random() - 0.5) * shake * 2);',
                      'if (shake > 0) { ctx.translate(Math.round((Math.random() - 0.5) * shake * 2), Math.round((Math.random() - 0.5) * shake * 2));')):
        if old in src:
            src = src.replace(old, new, 1)
        else:
            print('  đấu trường: không thấy', old)
    with open(os.path.join(PAGE, 'js', 'solo-arena.js'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write("// preview/dau-truong/index.html (the combat session's arena), wrapped by game/build_game.py: do not edit\n"
                 'globalThis.__SOLO_SRC = function (document, window, location, addEventListener, requestAnimationFrame, '
                 'fetch, Image) {\n' + src + '\n};\n')
    os.makedirs(os.path.join(PAGE, 'img', 'solo'), exist_ok=True)
    n = 0
    for d in os.listdir(os.path.join(ARENA, 'img')):
        sheet = os.path.join(ARENA, 'img', d, 's.png')
        if not os.path.exists(sheet):
            continue
        im = np.array(Image.open(sheet).convert('RGBA'))
        cell = im[:im.shape[0] // 4, :im.shape[1] // 4].copy()           # facing us, standing
        key = (cell[..., 0] > 150) & (cell[..., 1] < 120) & (cell[..., 2] > 150)
        cell[key, 3] = 0
        ys, xs = np.nonzero(cell[..., 3])
        if not len(xs):
            continue
        p = Image.fromarray(cell[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
        p.thumbnail((76, 76), Image.LANCZOS)
        p.save(os.path.join(PAGE, 'img', 'solo', d + '.png'), optimize=True)
        n += 1
        side = os.path.join(ARENA, 'img', d, 'e.png')               # facing the side, breathing: 4 frames, one box
        if os.path.exists(side):
            im = np.array(Image.open(side).convert('RGBA'))
            ch, cw = im.shape[0] // 4, im.shape[1] // 4
            cells = []
            for k in range(4):
                c = im[:ch, k * cw:(k + 1) * cw].copy()
                c[(c[..., 0] > 150) & (c[..., 1] < 120) & (c[..., 2] > 150), 3] = 0
                cells.append(c)
            al = np.any(np.stack([c[..., 3] for c in cells]), axis=0)
            ys, xs = np.nonzero(al)
            if len(xs):
                box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
                k2 = min(1.0, SIDE_PX / max(box[2] - box[0], box[3] - box[1]))
                for k, c in enumerate(cells):
                    q = Image.fromarray(c).crop(box)
                    q = q.resize((round(q.width * k2), round(q.height * k2)), Image.LANCZOS)
                    q.save(os.path.join(PAGE, 'img', 'solo', f'{d}_e{k}.png'), optimize=True)
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
    shutil.copy(os.path.join(HERE, 'src', 'di-bo.js'), os.path.join(PAGE, 'js'))
    shutil.copy(os.path.join(HERE, 'src', 've-nhanh.js'), os.path.join(PAGE, 'js'))
    shutil.copy(os.path.join(HERE, 'src', 'vo-duong.js'), os.path.join(PAGE, 'js'))
    shutil.copy(os.path.join(HERE, 'src', 'solo.js'), os.path.join(PAGE, 'js'))
    copy_dojo()
    solo = solo_arena()
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
    html = html[:i] + ADD.replace('.js"', f'.js?v={stamp}"').replace('__SND_V__', str(stamp)) + html[i:]
    open(path, 'w', encoding='utf-8', newline='\n').write(html)
    # the demo page this build was made from (check_minimon.py compares it with the demo now)
    shutil.copy(os.path.join(ROOT, 'scripts', 'evo_app.html'), os.path.join(HERE, 'minimon-base.html'))
    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(PAGE) for f in fs)
    print(f'{PAGE}: {how}, {size / 2 ** 20:.1f} MB (khung hình pet đọc qua build/game/pets), {sparks} tia sét, đấu trường {solo} pet')
    for s in skipped:
        print(f'  bỏ qua sửa chữ (demo không còn dòng này): {s}')


if __name__ == '__main__':
    main()
