// Elemon: the films of a new game (the story doc's prologue). Their shots and words are in game/src/truyen.js
// (TRUYEN.PHIM), two reels:
//   'mo-dau'  once a new game is started, before the egg pick: the isles, Hư Ảnh, the five guardians, the sealing
//             under Đài Ngũ Hành, the village, Già Quy greeting the newcomer
//   'dem-ay'  once the egg is picked, before the hatching: Già Quy hands it over, the seal cracks that night
// Here they are played:
//   - the world map or a film picture (assets/source/phim/, made 800x450 by game/build_game.py into img/phim/), a slow
//     camera over it; a white flash where a shot asks for one
//   - black bars top and bottom, the words typed out in the lower one
//   - A shows the rest of the words, then the next shot; START skips the reel; a shot with `thoai` waits for that
//     TRUYEN scene (shown by game/src/hoi-thoai.js), then the reel goes on, and at its end to the screen it names
// Mode 'phim' (song-that.js leaves it out of the save, r36s/js/am-thanh.js plays the night tune under it).
(() => {
  if (typeof press !== 'function' || typeof frame !== 'function' || typeof drawEvo !== 'function' ||
      typeof TRUYEN !== 'object' || !TRUYEN.PHIM) return;
  const MODE = 'phim', REELS = TRUYEN.PHIM;
  const TOP = 40, LOW = 400;                       // the black bars: above TOP, below LOW (a film picture fills between)
  const CHAR_MS = 32, WORDS_AT = 400, HOLD_MS = 1800;
  const FONT = 'bold 17px Tahoma, sans-serif', LINE_H = 24;
  const sfx = (n, v) => { if (typeof SOUND === 'object' && SOUND) SOUND.sfx(n, v); };

  // ---------- pictures ----------
  const PICS = {};
  function pic(src) {
    let im = PICS[src];
    if (!im) { im = PICS[src] = new Image(); im.onload = () => { im.__ok = true; }; im.src = src; }
    return im.__ok ? im : null;
  }
  const backdrop = nen => nen === 'map' ? (IMG.map && IMG.map.width ? IMG.map : pic('img/map.png')) : pic(`img/phim/${nen}.png`);
  // the egg screen's backdrop (game/build_game.py has the demo's drawEgg ask for it; null until it has loaded)
  globalThis.__nenNoTrung = () => pic('img/phim/NEN_no-trung.png');
  // every picture of a reel asked for as it starts, so a shot does not wait for its own
  const warm = reel => REELS[reel].canh.forEach(sh => backdrop(sh.nen));
  // the R36S: a reel's pictures given back once it is over (a new game's films are seen once, ~1.4 MB a picture);
  // the egg screen's backdrop is kept until the egg has hatched
  const EGG_BG = 'img/phim/NEN_no-trung.png';
  function giveBack(all) {
    if (typeof __cv !== 'object' || !__cv.free) return;
    for (const src of Object.keys(PICS))
      if ((all || src !== EGG_BG) && PICS[src].__id !== undefined) { __cv.free(PICS[src].__id); delete PICS[src]; }
  }

  // ---------- the shots ----------
  const P = () => S.phim;
  const shots = () => REELS[P().cuon].canh;
  const chu = sh => sh.chu ? sh.chu.replace(/\{pet\}/g, DATA.pet.name) : '';   // {pet}: the pet's name (truyen.js)
  const words = sh => sh.chu ? wrapLines(chu(sh), 580, FONT) : [];
  // a shot's words are read aloud (game/src/giong.js) and typed in step with the voice
  const voiceKey = p => `phim_${p.cuon}_${p.i}`;
  const voiceMs = p => typeof __giongMs === 'function' ? __giongMs(voiceKey(p)) : 0;
  const charMs = (sh, p) => { const v = voiceMs(p); return v && sh.chu ? Math.max(CHAR_MS, Math.min(90, v / sh.chu.length)) : CHAR_MS; };
  const wordsMs = (sh, p) => WORDS_AT + (sh.chu ? sh.chu.length : 0) * charMs(sh, p);
  const speak = p => typeof __giong === 'function' && __giong(shots()[p.i].chu ? voiceKey(p) : null);
  // t0: when the shot began (its picture moves by it), w0: when its words began (A brings them forward)
  function start(reel, now) {
    warm(reel);
    S.mode = MODE;
    S.phim = { cuon: reel, i: 0, t0: now, w0: now, thoai: REELS[reel].canh[0].thoai || null };
    speak(S.phim);
  }
  // a reel another screen starts (game/src/vung-dat.js: Đài Ngũ Hành's); at its end, the screen its `sau` names
  globalThis.__phim = reel => !!REELS[reel] && (start(reel, performance.now()), true);
  function next() {
    const p = P(), all = shots(), i = p.i + 1;
    if (i >= all.length) return end();
    const go = () => { const t = performance.now(); Object.assign(p, { i, t0: t, w0: t, thoai: all[i].thoai || null, flashed: false }); speak(p); };
    if (all[i].nen !== all[p.i].nen) fadeTo(go); else go();
  }
  function end() {
    const after = REELS[P().cuon].sau;
    if (typeof __giong === 'function') __giong(null);
    sfx('chuyen', 160);
    fadeTo(() => { S.mode = after; if (after === 'pickEgg') S.pickEl = 0; S.phim = null; giveBack(false); });
  }

  // ---------- drawing ----------
  const ease = x => x < 0 ? 0 : x > 1 ? 1 : x * x * (3 - 2 * x);
  // the camera: [zoom, x, y] eased from its first to its last over the shot; x, y on the picture taken as 640 wide
  function drawBackdrop(sh, t) {
    const im = backdrop(sh.nen);
    if (!im) return;
    const map = sh.nen === 'map', BW = 640, BH = map ? 480 : 360;
    const [a, b] = sh.cam || [[1, BW / 2, BH / 2], [1, BW / 2, BH / 2]], e = ease(t);
    const z = a[0] + (b[0] - a[0]) * e, cx = a[1] + (b[1] - a[1]) * e, cy = a[2] + (b[2] - a[2]) * e;
    const k = im.width / BW, sw = im.width / z, sh2 = im.height / z;
    const sx = Math.max(0, Math.min(im.width - sw, cx * k - sw / 2)), sy = Math.max(0, Math.min(im.height - sh2, cy * k - sh2 / 2));
    if (map) ctx.imageSmoothingEnabled = false;        // the map is pixel art at 640x480: kept crisp when zoomed
    ctx.drawImage(im, sx, sy, sw, sh2, 0, map ? 0 : TOP, 640, map ? 480 : LOW - TOP);
    ctx.imageSmoothingEnabled = true;
  }
  function drawFilm(now) {
    const p = P(), sh = shots()[p.i], el = now - p.t0, t = el / (sh.ms || 1);
    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, 640, 480);
    drawBackdrop(sh, t);
    if (sh.chop) {                                     // the seal: a white flash at three quarters of the shot
      const fl = t < 0.72 ? 0 : t < 0.78 ? (t - 0.72) / 0.06 : Math.max(0, 1 - (t - 0.78) / 0.22);
      if (fl > 0) { ctx.globalAlpha = fl; ctx.fillStyle = '#fffbe8'; ctx.fillRect(0, 0, 640, 480); ctx.globalAlpha = 1; }
      if (!p.flashed && t >= 0.72) { p.flashed = true; sfx('tien-hoa', 200); }
    }
    // the bars, the words, the hint
    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, 640, TOP); ctx.fillRect(0, LOW, 640, 480 - LOW);
    if (!sh.thoai) {
      let n = Math.floor((now - p.w0 - WORDS_AT) / charMs(sh, p));
      ctx.font = FONT; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#f0e4ce';
      const rows = words(sh), y0 = LOW + 40 - (rows.length - 1) * LINE_H / 2;
      rows.forEach((r, k) => {
        if (n <= 0) return;
        // typed from the left of the centred line: the part shown is drawn where the whole line would start
        ctx.fillText(r.slice(0, n), Math.round(320 - ctx.measureText(r).width / 2), y0 + k * LINE_H);
        n -= r.length;
      });
    }
    text('START: bỏ qua', 626, TOP / 2, 12, 'rgba(240,228,206,0.55)', 'right', false, 0);
  }

  // ---------- the hooks ----------
  // the screen changes that start a reel (once a page: going back and starting again does not show it twice)
  const CUES = [['title', 'pickEgg', 'mo-dau'], ['pickPet', 'egg', 'dem-ay']];
  let prev = null;
  const played = new Set();
  const frame0 = frame;
  globalThis.frame = function (now) {
    frame0(now);
    for (const [from, to, reel] of CUES)
      if (prev === from && S.mode === to && REELS[reel] && !played.has(reel)) { played.add(reel); start(reel, now); }
    if (prev === 'egg' && S.mode !== 'egg') giveBack(true);   // hatched: the egg's backdrop too
    prev = S.mode;
    const p = P();
    if (S.mode !== MODE || !p || S.fade > 0) return;
    const sh = shots()[p.i];
    if (sh.thoai) {                                    // its words said (or none left to say): on with the reel
      if (!(S.truyen && S.truyen.dang) && TRUYEN.CANH.every(c => c.id !== sh.thoai || (S.truyen && S.truyen.da[c.id]))) next();
    } else if (now - p.t0 >= (sh.ms || 0) && now - p.w0 >= Math.max(wordsMs(sh, p), WORDS_AT + voiceMs(p)) + HOLD_MS) next();
  };
  const evo0 = drawEvo;
  globalThis.drawEvo = function (now) {
    if (S.mode !== MODE || !P()) return evo0(now);
    drawFilm(now);
  };
  const press0 = press;
  globalThis.press = function (btn) {
    if (S.mode !== MODE) return press0(btn);
    const p = P();
    if (S.fade > 0 || !p) return;
    if (btn === 'START') return end();
    const sh = shots()[p.i];
    if (btn !== 'A' || sh.thoai) return;
    const now = performance.now();
    if (now - p.w0 < wordsMs(sh, p)) p.w0 = now - wordsMs(sh, p);     // the rest of the words at once
    else next();
  };
})();
