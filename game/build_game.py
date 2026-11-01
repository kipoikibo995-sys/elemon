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
  let song = null, songVol = 0.5;
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
      song = new Audio(`nhac/${name}.wav?v=${V}`); song.loop = true; song.volume = songVol; play(song);
    },
    vol(v) { songVol = Math.min(1, v / 280); if (song) song.volume = songVol; },   // the music's, 0..256
  };
})();
// a button beside "Chơi lại" that clears the save (testing in a browser)
(() => {
  const r = document.getElementById('btnR');
  if (!r) return;
  r.insertAdjacentHTML('afterend', ' <button class="restart" id="xoaLuu">Xóa bản lưu</button>');
  document.getElementById('xoaLuu').onclick = () => {
    if (!confirm('Xóa mọi bản lưu (mọi pet) của game?')) return;
    window.__noSave = true; for (let n = 1; n <= 6; n++) localStorage.removeItem('holua-save-' + n); localStorage.removeItem('holua-cuoi'); location.reload();
  };
})();
</script>
<script src="js/song-that.js"></script>
<script src="js/chi-so.js"></script>
<script src="js/di-bo.js"></script>
<script src="js/ve-nhanh.js"></script>
<script src="js/vo-duong.js"></script>
<script src="js/solo-arena.js"></script>
<script src="js/solo.js"></script>
<script src="js/am-thanh.js"></script>
<script src="js/set-huyen-thoai.js"></script>
<script src="js/nen-chi-so.js"></script>
<script src="js/vung-dat.js"></script>
<script src="js/tai-man.js"></script>
<script src="js/truyen.js"></script>
<script src="js/giong.js"></script>
<script src="js/phim.js"></script>
<script src="js/hoi-thoai.js"></script>
<script src="js/dat-ten.js"></script>
<script src="js/loi-noi.js"></script>
<script src="js/man-chao.js"></script>
<script src="js/cay-dau-truong.js"></script>
<script data-browser-only src="js/nut-thu.js"></script>
'''
# the golden sparks round a Huyền thoại pet (game/src/set-huyen-thoai.js): 4x3 sparks a sheet on magenta
SPARKS = os.path.join(ROOT, 'assets', 'source', 'tinh-linh', 'huyen-thoai-fx', 'set-vang_tia-manh*.png')
# the evolution backdrop (the user, 30/10: the demo's EVO1_nen is too busy): assets/source/tien-hoa/TH1_nen.png when it
# is there, its middle 4:3 cut to 640x480 over img/nen.png (the evolution, the naming after it, the demo's end screen)
EVO_BG = os.path.join(ROOT, 'assets', 'source', 'tien-hoa', 'TH1_nen.png')
SPARK_MAX = 96                       # px, the longest side of a cut spark (drawn at ~15 % of the pet's height)
# small wording changes for the real game: (demo text, game text); one the demo no longer has is skipped
WORDING = [
    ("'chăm sóc, tập luyện (L2: tua nhanh)'", "'chăm sóc, tập luyện mỗi ngày'"),
    ("'R2 chơi · X vuốt ve · L2 tua nhanh'", "'R2 chơi · X vuốt ve'"),
    ("'Bản demo: tua nhanh ¼ giai đoạn; ở mốc cấp thì mở bảng tiến hóa'", "'Ở mốc cấp: mở bảng tiến hóa'"),
    ('<title>Elemon demo R36S - từ trứng tới Huyền thoại</title>', '<title>Elemon</title>'),
    # pictures loaded screen by screen (game/src/tai-dan.js, tai-man.js), and at start the saved pet, not Hỏa Hổ
    ("const jobs = files.map(f => load(f, `img/${f}.png`));",
     "const jobs = globalThis.__lazyJobs ? __lazyJobs(files, load) : files.map(f => load(f, `img/${f}.png`));"),
    ("Promise.all(jobs).then(() => loadCreature('hoa-ho'))",
     "Promise.all(jobs).then(() => loadCreature(globalThis.__startPet && __startPet() || 'hoa-ho'))"),
    # the egg screen: the story's hatching room (assets/source/phim/NEN_no-trung.png, game/src/phim.js) when it is there,
    # without the darkening the room behind it needed
    ("  ctx.drawImage(IMG.room, 0, 0);\n  ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.fillRect(0, 0, 640, 480);",
     "  const nenNo = globalThis.__nenNoTrung && __nenNoTrung();\n  ctx.drawImage(nenNo || IMG.room, 0, 0);\n"
     "  if (!nenNo) { ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.fillRect(0, 0, 640, 480); }"),
    # the launch clean-up (the user, 31/10/2026): no "demo", no "chưa làm" left on screen
    ("    c.push(['Nhà cấp 4 + Hồn lửa xanh (bản demo: bỏ qua)', true, '']);\n", ''),
    ("  text('Lên Nhi trở đi tùy cách nuôi (sẽ làm sau)', 160, 400, 13, '#b8a080', 'left', false);\n", ''),
    ("title('HOÀN THÀNH DEMO'", "title('HUYỀN THOẠI!'"),
    ("`Từ trứng tới Huyền thoại: ${Math.floor(secs / 60)} phút ${secs % 60} giây · ${S.acts} lần chăm sóc`",
     "`Từ trứng tới Huyền thoại: ${Math.floor(secs / 86400)} ngày ${Math.floor(secs / 3600) % 24} giờ · ${S.acts} lần chăm sóc`"),
    ("'A: chơi tiếp với Huyền thoại · R: chơi lại từ đầu'", "'A: chơi tiếp với Huyền thoại'"),
    ("`${p.name}: đã mở (nội dung vùng làm sau)`", "`${p.name}: đã mở`"),
    # Chợ's X (Bán): the seed shop's selling tab (crops and fish), back to Chợ
    ("if (btn === 'X') toast('Bán: chưa làm');", "if (btn === 'X') return openSeedShop(2, 'shop');"),
    # Hồ sơ's A (Đổi tên): the naming screen (game/src/dat-ten.js)
    ("if (btn === 'A' && S.stats === 3) toast('Đổi tên: chưa làm');",
     "if (btn === 'A' && S.stats === 3 && typeof __datTen === 'function') { S.stats = null; return fadeTo(() => __datTen('room')); }"),
    # the room's START (Trang trí, not made): the settings (game/src/man-chao.js)
    ("if (btn === 'START') toast('Trang trí phòng: chưa làm');",
     "if (btn === 'START' && typeof __caiDat === 'function') return __caiDat('room');"),
    # the pet's own name, not Bông's
    ("'Khác hệ Bông: điểm hệ sẽ đổi dần · A để mua'", "`Khác hệ ${DATA.pet.name}: điểm hệ sẽ đổi dần · A để mua`"),
    ("'Mua mấy món\\nngon cho Bông\\nnào!'", "'Mua mấy món\\nngon cho pet\\nnào!'"),
    # the farm: each plot opened costs more than the one before (the user, 31/10/2026): 200, 300, 400... (the 9 plots
    # open from the start do not count)
    ("const OPEN_COST = 200;",
     "const OPEN_COST_BASE = 200, OPEN_COST_STEP = 100;\n"
     "const openCost = () => OPEN_COST_BASE + OPEN_COST_STEP * farmPlots().filter((p, i) => p.s !== 'khoa' && !(FIELD[i].r >= 3 && FIELD[i].c <= 2)).length;"),
    ("`Mở ô đất (${OPEN_COST} vàng)`", "`Mở ô đất (${openCost()} vàng)`"),
    ("    if (S.coins < OPEN_COST) return toast('Không đủ vàng');\n    S.coins -= OPEN_COST; p.s = 'tron'; toast('Đã mở thêm một ô đất');",
     "    const cost = openCost();\n    if (S.coins < cost) return toast(`Cần ${cost} vàng để mở ô này`);\n"
     "    S.coins -= cost; p.s = 'tron'; toast(`Đã mở thêm một ô đất · ô sau: ${openCost()} vàng`);"),
    # the stroll eases in and out (game/src/di-bo.js)
    ('    S.px = S.walk.from + (S.walk.to - S.walk.from) * t;',
     "    S.px = S.walk.from + (S.walk.to - S.walk.from) * (typeof walkEase === 'function' ? walkEase(t, S.walk.dur) : t);"),
    # the room without the dark hint strip under the HUD and its two lines (the user's call, 27/10: the room is
    # seen whole); matched after the 'R2 chơi' line above has been shortened
    ("  // the hint lines never sit straight on the room picture: a dark strip (65%) under the HUD carries them\n"
     "  ctx.fillStyle = 'rgba(12,7,5,0.65)'; ctx.fillRect(0, 38, 640, 44);\n"
     "  ctx.fillStyle = 'rgba(255,214,120,0.25)'; ctx.fillRect(0, 82, 640, 1);\n"
     "  text(hint(), 12, 52, 15, '#ffe6a8', 'left', true, 3);\n"
     "  text('R2 chơi · X vuốt ve', 12, 71, 13, '#c9bba8', 'left', false, 2);\n", ''),
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
            subprocess.run(['cmd', '/c', 'mklink', '/J', link, target], check=True, capture_output=True)


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


def evo_background():
    """TH1_nen.png over the demo's img/nen.png; whether it was there."""
    if not os.path.exists(EVO_BG):
        return False
    from PIL import Image
    im = Image.open(EVO_BG).convert('RGB')
    w, h = im.size
    cw, ch = min(w, round(h * 4 / 3)), min(h, round(w * 3 / 4))
    x, y = (w - cw) // 2, (h - ch) // 2
    im.crop((x, y, x + cw, y + ch)).resize((640, 480), Image.LANCZOS).save(os.path.join(PAGE, 'img', 'nen.png'), optimize=True)
    return True


# the title screen without its two painted buttons (game/src/man-chao.js draws four in a row, the user 31/10): the
# buttons' box covered with the grass to its right, the edges feathered
TITLE_PILLS = (232, 355, 408, 446)            # x0, y0, x1, y1 on the 640x480 title_b


def title_without_buttons():
    import numpy as np
    from PIL import Image
    src = os.path.join(PAGE, 'img', 'title_b.png')
    if not os.path.exists(src):
        return False
    a = np.array(Image.open(src).convert('RGB')).astype(float)
    x0, y0, x1, y1 = TITLE_PILLS
    w, h, f = x1 - x0, y1 - y0, 8
    m = np.ones((h, w))
    for i in range(f):
        k = (i + 1) / (f + 1)
        m[:, i] *= k; m[:, w - 1 - i] *= k; m[i, :] *= k; m[h - 1 - i, :] *= k
    a[y0:y1, x0:x1] = a[y0:y1, x0:x1] * (1 - m[..., None]) + a[y0:y1, x1:x1 + w] * m[..., None]
    Image.fromarray(a.round().astype(np.uint8)).save(os.path.join(PAGE, 'img', 'title_b_trong.png'), optimize=True)
    return True


# the Đấu trường tree (game/src/cay-dau-truong.js): one painted tree an element (assets/source/dau-truong/cay/
# CAY_<he>.png, a candelabra of six branches, ChatGPT) and the node frames (CAY_khung.png: open, picked, locked, Hư Ảnh
# on magenta). A tree is scaled to 640x560 and its top 480 kept (the trunk's foot goes under the bottom line); its six
# branches found where the picture stands out from its row's own colour, between the tips and the bough
CAY = os.path.join(ROOT, 'assets', 'source', 'dau-truong', 'cay')
CAY_HE = ('hoa', 'kim', 'moc', 'thuy', 'tho')
CAY_FRAME = 66                                 # px, a node frame's side on the screen


def cay_tree():
    """img/cay/<he>.png and khung_<0-3>.png; the layout for the page: {he: {x: [6], tip, bough}, frame}."""
    import numpy as np
    from PIL import Image
    out = os.path.join(PAGE, 'img', 'cay')
    os.makedirs(out, exist_ok=True)
    lay = {'frame': CAY_FRAME, 'trees': {}}
    for he in CAY_HE:
        src = os.path.join(CAY, f'CAY_{he}.png')
        if not os.path.exists(src):
            continue
        im = Image.open(src).convert('RGB').resize((640, 560), Image.LANCZOS).crop((0, 0, 640, 480))
        im.save(os.path.join(out, he + '.png'), optimize=True)
        a = np.array(im).astype(float)
        fg = np.abs(a - np.median(a, axis=1, keepdims=True)).sum(2) > 60
        band = np.convolve(fg[150:250].sum(0).astype(float), np.ones(9) / 9, 'same')
        xs = []
        for x in np.argsort(-band):
            if all(abs(int(x) - p) > 60 for p in xs):
                xs.append(int(x))
            if len(xs) == 6:
                break
        xs.sort()
        rows = np.convolve(fg[220:340].sum(1).astype(float), np.ones(7) / 7, 'same')
        bough = 220 + int(np.argmax(rows))                # the bough: between the tips and the trunk's glowing foot
        tips = []
        for x in xs:
            col = np.nonzero(fg[40:bough, max(0, x - 5):x + 6].any(1))[0]
            tips.append(40 + int(col.min()) if len(col) else 80)
        lay['trees'][he] = {'x': xs, 'tip': int(np.median(tips)), 'bough': bough}
    sheet = os.path.join(CAY, 'CAY_khung.png')
    if os.path.exists(sheet):
        b = np.array(Image.open(sheet).convert('RGBA'))
        key = (b[..., 0] > 200) & (b[..., 1] < 80) & (b[..., 2] > 200)
        b[key, 3] = 0
        cols = np.nonzero((b[..., 3] > 0).sum(0) > 3)[0]
        runs, st = [], cols[0]
        for p, q in zip(cols, cols[1:]):
            if q - p > 5:
                runs.append((st, p)); st = q
        runs.append((st, cols[-1]))
        for i, (x0, x1) in enumerate(runs[:4]):
            part = b[:, x0:x1 + 1]
            ys = np.nonzero(part[..., 3].sum(1) > 3)[0]
            f = Image.fromarray(part[ys.min():ys.max() + 1])
            f.resize((CAY_FRAME, CAY_FRAME), Image.LANCZOS).save(os.path.join(out, f'khung_{i}.png'), optimize=True)
    return lay


SIDE_PX = 190                       # px, the larger side of the Solo pick screen's standing pet


# the camouflage checker: whole runs of pixels cleared at once (same holes as the pixel-by-pixel loop, far fewer steps
# for the R36S's interpreter)
DITHER_LOOP = "for (let yy = 0; yy < o.height; yy++) for (let xx = 0; xx < o.width; xx++) if (((xx / b | 0) + (yy / b | 0)) % 2) p[(yy * o.width + xx) * 4 + 3] = 0;"
DITHER_RUNS = ("{ const u = new Uint32Array(p.buffer, p.byteOffset, o.width * o.height), W = o.width; "
               "for (let yy = 0; yy < o.height; yy++) { const r = yy * W; "
               "for (let xx = (yy / b | 0) % 2 ? 0 : b; xx < W; xx += 2 * b) u.fill(0, r + xx, r + Math.min(W, xx + b)); } }")
# the aiming funnel and arrow: drawn cell by cell every frame (~8000 cells, thousands of 2 px fills) they cost the
# R36S more than the fight; here each funnel (its base angle) and arrow (its 32 directions) is drawn once into a
# picture, put down on the same 2 px grid round the pet; the arrow in 128 directions (the original's 32 made it
# step visibly across the funnel), all of them made while the VS screen shows (__aimWarm)
AIM = r'''// the shapes are plain data, kept from match to match (the pictures belong to a match and are freed with it)
const AIM_FUNNELS = new Map(), AIM_ARROWS = new Map(), AIM_SHAPES = globalThis.__aimShapes || (globalThis.__aimShapes = new Map());
const AIM_DIRS = 64, ARROW_DIRS = 128;   // the funnel drawn in 64 directions, the arrow in 128 (2.8 degree steps)
const AIM_R = 88 / BLK, AIM_N = 2 * (Math.ceil(88 / BLK) + 1) + 1;
const ARROW_LEN = AIM_R * 0.66, ARROW_L = Math.ceil(AIM_R * 0.66) + 4, ARROW_N = 2 * ARROW_L + 1;
const AIM_PAL = { P: ['#ffb347', '#e0702a', '#8a3414', '#ffe08a'], B: ['#8fd8ff', '#2a76b8', '#123a66', '#cff0ff'] };
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
const aimMod = (k, n) => ((k % n) + n) % n;
// the funnel's cells for one of AIM_DIRS directions (both sides, both checker phases): 1 edge, 2 outer band, 3 inside
function aimShape(sk) {
  let shape = AIM_SHAPES.get(sk);
  if (shape) return shape;
  const n = AIM_N, R = (n - 1) / 2, r = AIM_R, b = sk * (Math.PI * 2 / AIM_DIRS);
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
  return shape;
}
function aimFunnel(side, par, sk) {
  const fk = side + par + ':' + sk;
  let c = AIM_FUNNELS.get(fk);
  if (c) return c;
  const n = AIM_N, shape = aimShape(sk), cells = new Uint32Array(n * n), P = AIM_PAL[side].map(aimRgba);
  for (let ly = 0; ly < n; ly++) for (let lx = 0; lx < n; lx++) {
    const v = shape[ly * n + lx];
    if (v) cells[ly * n + lx] = v === 1 ? P[0] : (lx + ly + par) % 2 === 0 ? P[v - 1] : 0;
  }
  c = aimPaint(n, cells);
  AIM_FUNNELS.set(fk, c);
  if (AIM_FUNNELS.size > 32) AIM_FUNNELS.delete(AIM_FUNNELS.keys().next().value);
  return c;
}
function aimArrow(side, st) {
  const ak = side + st;
  let c = AIM_ARROWS.get(ak);
  if (c) return c;
  const a = st * (Math.PI * 2 / ARROW_DIRS), ca = Math.cos(a), sa = Math.sin(a), len = ARROW_LEN, L = ARROW_L, n = ARROW_N;
  const inArrow = (lx, ly) => {
    const px = lx - L + 0.5, py = ly - L + 0.5, u = px * ca + py * sa, v = -px * sa + py * ca;
    if (u >= 10 && u <= len - 5 && Math.abs(v) <= 0.75) return true;
    return u > len - 6 && u <= len && Math.abs(v) <= (len - u) * 0.7;
  };
  // the arrow's cells lit, the cells round them dark (worked from the ~100 arrow cells, not every cell's neighbours)
  const lit = aimRgba(AIM_PAL[side][3]), dark = aimRgba('#1a0c06'), cells = new Uint32Array(n * n), on = [];
  for (let ly = 0; ly < n; ly++) for (let lx = 0; lx < n; lx++) if (inArrow(lx, ly)) { on.push(ly * n + lx); cells[ly * n + lx] = lit; }
  for (const i of on) {
    const lx = i % n, ly = (i - lx) / n;
    for (let yy = -1; yy <= 1; yy++) for (let xx = -1; xx <= 1; xx++) {
      const X = lx + xx, Y = ly + yy, j = Y * n + X;
      if (X >= 0 && Y >= 0 && X < n && Y < n && cells[j] !== lit) cells[j] = dark;
    }
  }
  c = aimPaint(n, cells);
  AIM_ARROWS.set(ak, c);
  return c;
}
// made ahead while the VS screen shows (game/src/solo.js calls it until it says false): every funnel shape and the
// player's arrows, so aiming never stops to work one out mid-fight (the bot points straight where it aims: one each)
let aimWarmI = 0;
globalThis.__aimWarm = () => {
  const i = aimWarmI++;
  if (i < AIM_DIRS) { aimShape(i); return true; }
  const k = i - AIM_DIRS;
  if (k < ARROW_DIRS) { aimArrow('P', k); return true; }
  return false;
};
function drawAim(f) {
  const a = f.aiming;
  if (!a) return;
  // the funnel's drawn direction in AIM_DIRS steps (the hit test keeps a.base as it is): the bot faces any way at all
  const side = f.bot ? 'B' : 'P', ox = Math.round(f.x / BLK), oy = Math.round((f.y - 24) / BLK), R = (AIM_N - 1) / 2;
  const sk = aimMod(Math.round(a.base / (Math.PI * 2 / AIM_DIRS)), AIM_DIRS);
  ctx.drawImage(aimFunnel(side, (ox + oy) & 1, sk), (ox - R) * BLK, (oy - R) * BLK);
  const st = aimMod(Math.round(a.ang / (Math.PI * 2 / ARROW_DIRS)), ARROW_DIRS);
  ctx.drawImage(aimArrow(side, st), (ox - ARROW_L) * BLK, (oy - ARROW_L) * BLK);
  if (a.k === 'i') ring(a.tx, a.ty, AIM_PAL[side][0], 0);
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


# the story's portraits (game/src/hoi-thoai.js): assets/source/npc/NPC_<name>.png, 4x2 faces on magenta, in this order
NPC_FACES = {'gia-quy': ['cuoi', 'ke-chuyen', 'gio-gay', 'ngac-nhien', 'lo-lang', 'chi-xa', 'gat-dau', 'buon']}
NPC_BOX = (220, 236)                 # px, the most a portrait takes (a smaller one loses the drawing's 1-2 px detail)


def cut_npc():
    """Each NPC sheet cut into img/npc/<name>_<n>-<face>.png: magenta (and its fringe) made clear, trimmed, every face
    of a sheet brought down by the same factor so the bust keeps its size from face to face. Number of faces cut."""
    import numpy as np
    from PIL import Image
    os.makedirs(os.path.join(PAGE, 'img', 'npc'), exist_ok=True)
    n = 0
    for name, faces in NPC_FACES.items():
        path = os.path.join(ROOT, 'assets', 'source', 'npc', f'NPC_{name}.png')
        if not os.path.exists(path):
            continue
        im = np.array(Image.open(path).convert('RGBA'))
        h, w = im.shape[:2]
        cells = []
        for i in range(len(faces)):
            r, c = divmod(i, 4)
            cell = im[r * h // 2:(r + 1) * h // 2, c * w // 4:(c + 1) * w // 4].copy()
            px = cell[..., :3].astype(int)
            key = (px[..., 0] > 150) & (px[..., 1] < 110) & (px[..., 2] > 150)
            # the fringe a soft-edged drawing leaves: pinkish pixels touching the cleared background
            near = np.zeros_like(key)
            near[1:] |= key[:-1]; near[:-1] |= key[1:]; near[:, 1:] |= key[:, :-1]; near[:, :-1] |= key[:, 1:]
            key |= near & (px[..., 0] > 110) & (px[..., 2] > 110) & (px[..., 1] < (px[..., 0] + px[..., 2]) / 2 - 40)
            cell[key, 3] = 0
            ys, xs = np.nonzero(cell[..., 3])
            cells.append(cell[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(xs) else cell[:1, :1])
        k = min(1.0, min(NPC_BOX[0] / max(c.shape[1] for c in cells), NPC_BOX[1] / max(c.shape[0] for c in cells)))
        for i, (face, cell) in enumerate(zip(faces, cells)):
            p = Image.fromarray(cell)
            p = p.resize((max(1, round(p.width * k)), max(1, round(p.height * k))), Image.LANCZOS)
            p.save(os.path.join(PAGE, 'img', 'npc', f'{name}_{i + 1}-{face}.png'), optimize=True)
            n += 1
    return n


# the films' pictures (game/src/phim.js): assets/source/phim/*.png, 16:9, brought down to FILM_PX (the film shows them
# 640x360 between its black bars; the extra room is for its slow camera)
FILM_PX = (800, 450)
# backdrops that are not film shots: the part of the drawing kept, and the screen size it is brought to
FILM_CROP = {'NEN_no-trung': ((159, 0, 1289, 848), (640, 480))}


def film_pictures():
    """assets/source/phim/<name>.png -> img/phim/<name>.png at FILM_PX. Number of pictures."""
    from PIL import Image
    os.makedirs(os.path.join(PAGE, 'img', 'phim'), exist_ok=True)
    n = 0
    for path in sorted(glob.glob(os.path.join(ROOT, 'assets', 'source', 'phim', '*.png'))):
        box, size = FILM_CROP.get(os.path.splitext(os.path.basename(path))[0], (None, FILM_PX))
        Image.open(path).convert('RGB').crop(box).resize(size, Image.LANCZOS).save(
            os.path.join(PAGE, 'img', 'phim', os.path.basename(path)), optimize=True)
        n += 1
    return n


def wide_pictures():
    """assets/source/rong/<path>_rong.png -> img/<path>_rong.png: a full-screen picture drawn out for a 16:9 screen (the
    picture with its two sides added, the same height; r36s/js/shim.js shows its sides there instead of the stretched
    edges), <path> as the page loads it under img/ (room, nen, phim/..). Number of pictures."""
    src = os.path.join(ROOT, 'assets', 'source', 'rong')
    n = 0
    for path in sorted(glob.glob(os.path.join(src, '**', '*_rong.png'), recursive=True)):
        dst = os.path.join(PAGE, 'img', os.path.relpath(path, src))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(path, dst)
        n += 1
    return n


def voices():
    """The story's spoken lines (scripts/make_giong.py: assets/am-thanh/giong) -> sfx/giong/, and js/giong.js with their
    lengths. Number of lines."""
    src = os.path.join(ROOT, 'assets', 'am-thanh', 'giong')
    ledger = os.path.join(src, '_giong.json')
    lens = {}
    if os.path.exists(ledger):
        os.makedirs(os.path.join(PAGE, 'sfx', 'giong'), exist_ok=True)
        for key, v in json.load(open(ledger, encoding='utf-8')).items():
            wav = os.path.join(src, key + '.wav')
            if os.path.exists(wav):
                shutil.copy(wav, os.path.join(PAGE, 'sfx', 'giong'))
                lens[key] = v['ms']
    code = open(os.path.join(HERE, 'src', 'giong.js'), encoding='utf-8').read()
    open(os.path.join(PAGE, 'js', 'giong.js'), 'w', encoding='utf-8', newline='\n').write(
        code.replace('__GIONG__', json.dumps(lens, separators=(',', ':'))))
    return len(lens)


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
    shutil.copy(os.path.join(HERE, 'src', 'chi-so.js'), os.path.join(PAGE, 'js'))     # the numbers (THIET-KE.md mục 6)
    shutil.copy(os.path.join(HERE, 'src', 'nut-thu.js'), os.path.join(PAGE, 'js'))       # test buttons (browser)
    shutil.copy(os.path.join(HERE, 'src', 'di-bo.js'), os.path.join(PAGE, 'js'))
    shutil.copy(os.path.join(HERE, 'src', 've-nhanh.js'), os.path.join(PAGE, 'js'))
    for name in ('tai-dan.js', 'tai-man.js', 'truyen.js', 'phim.js', 'hoi-thoai.js', 'dat-ten.js', 'loi-noi.js', 'man-chao.js'):     # truyen.js: the story's words
        shutil.copy(os.path.join(HERE, 'src', name), os.path.join(PAGE, 'js'))
    shutil.copy(os.path.join(HERE, 'src', 'vo-duong.js'), os.path.join(PAGE, 'js'))
    shutil.copy(os.path.join(HERE, 'src', 'solo.js'), os.path.join(PAGE, 'js'))
    copy_dojo()
    cut_npc()
    film_pictures()
    wide_pictures()
    solo = solo_arena()
    shutil.copy(os.path.join(ROOT, 'r36s', 'js', 'am-thanh.js'), os.path.join(PAGE, 'js'))
    sparks = cut_sparks()
    bg = evo_background()
    src = open(os.path.join(HERE, 'src', 'cay-dau-truong.js'), encoding='utf-8').read()
    open(os.path.join(PAGE, 'js', 'cay-dau-truong.js'), 'w', encoding='utf-8', newline='\n').write(
        src.replace('__CAY__', json.dumps(cay_tree())))
    title_without_buttons()
    src = open(os.path.join(HERE, 'src', 'set-huyen-thoai.js'), encoding='utf-8').read()
    open(os.path.join(PAGE, 'js', 'set-huyen-thoai.js'), 'w', encoding='utf-8', newline='\n').write(
        src.replace('__TIA_N__', str(sparks)))
    src = open(os.path.join(HERE, 'src', 'nen-chi-so.js'), encoding='utf-8').read()
    open(os.path.join(PAGE, 'js', 'nen-chi-so.js'), 'w', encoding='utf-8', newline='\n').write(
        src.replace('__NEN_CHI_SO__', json.dumps(stats_pieces())))
    import vung_dat                      # Vùng đất: the region maps and the pets' map pictures (scripts/vung_dat.py)
    src = open(os.path.join(HERE, 'src', 'vung-dat.js'), encoding='utf-8').read()
    open(os.path.join(PAGE, 'js', 'vung-dat.js'), 'w', encoding='utf-8', newline='\n').write(
        src.replace('__VUNG_DAT__', json.dumps(vung_dat.build(PAGE), ensure_ascii=False, separators=(',', ':'))))
    for kind in ('sfx', 'nhac'):
        os.makedirs(os.path.join(PAGE, kind), exist_ok=True)
        for p in glob.glob(os.path.join(ROOT, 'assets', 'am-thanh', kind, '*.wav')):
            shutil.copy(p, os.path.join(PAGE, kind))
    voices()
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
    # before the demo's own script: its pictures are then loaded screen by screen (game/src/tai-dan.js)
    j = html.index('<script>')
    html = html[:j] + f'<script src="js/tai-dan.js?v={stamp}"></script>\n' + html[j:]
    open(path, 'w', encoding='utf-8', newline='\n').write(html)
    # the demo page this build was made from (check_minimon.py compares it with the demo now)
    shutil.copy(os.path.join(ROOT, 'scripts', 'evo_app.html'), os.path.join(HERE, 'minimon-base.html'))
    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(PAGE) for f in fs)
    print(f'{PAGE}: {how}, {size / 2 ** 20:.1f} MB (khung hình pet đọc qua build/game/pets), {sparks} tia sét, nền tiến hóa {'mới (TH1_nen)' if bg else 'cũ (EVO1_nen)'}, đấu trường {solo} pet')
    for s in skipped:
        print(f'  bỏ qua sửa chữ (demo không còn dòng này): {s}')


if __name__ == '__main__':
    main()
