// Golden lightning crackling round a Huyền thoại pet, as on the frames session's test page (preview/huyen-thoai-set):
// sparks climb the pet's outline from the feet to the head, every climb with its own speed, number of rungs and
// pause after it, 0-2 sparks a rung on a random side, and a stray spark now and then. Each spark swaps between two
// drawings while it lives. The sparks are the 7 sheets of assets/source/tinh-linh/huyen-thoai-fx/set-vang_tia-manh*,
// cut at build time (game/build_game.py) into img/tia_<n>.png. It wraps the page's drawPet, so it shows wherever a
// legend pet is drawn.
(() => {
  const N = __TIA_N__;                                            // filled in by game/build_game.py
  if (!N || typeof drawPet !== 'function') return;
  const TIA = [];
  for (let i = 0; i < N; i++) { const im = new Image(); im.onload = () => TIA.push(im); im.src = `img/tia_${i}.png`; }
  const LEGEND = st => st === 'legend' || st === 'legend4';
  const LIFE_MIN = 220, LIFE_MAX = 420;
  const rnd = (a, b) => a + Math.random() * (b - a);

  // points just inside the outline of a frame (where the sparks crackle) and its drawn box, measured once a frame
  const EDGES = new Map();
  function edge(im) {
    let e = EDGES.get(im);
    if (e) return e;
    const c = document.createElement('canvas'); c.width = im.width; c.height = im.height;
    const g = c.getContext('2d'); g.drawImage(im, 0, 0);
    const p = g.getImageData(0, 0, c.width, c.height).data, W = c.width, H = c.height, pts = [];
    const a = (x, y) => x >= 0 && y >= 0 && x < W && y < H && p[(y * W + x) * 4 + 3] > 0;
    let y0 = H, y1 = 0;
    for (let y = 0; y < H; y += 2) for (let x = 0; x < W; x += 2) if (a(x, y)) { if (y < y0) y0 = y; if (y > y1) y1 = y; }
    for (let y = y0; y < y0 + (y1 - y0) * 0.92; y += 4) for (let x = 0; x < W; x += 4)
      if (a(x, y) && (!a(x - 8, y) || !a(x + 8, y) || !a(x, y - 8))) pts.push([x, y]);
    let x0 = W, x1 = 0;
    for (const [x] of pts) { if (x < x0) x0 = x; if (x > x1) x1 = x; }
    e = { pts, top: y0, h: Math.max(1, y1 - y0), mid: (x0 + x1) / 2 };
    EDGES.set(im, e);
    return e;
  }

  let live = [], climb = { next: 0, rungs: [] }, stepped = -1;
  function spark(e, frac, side, now) {                            // one spark on the outline at height frac (0 feet, 1 head)
    const yy = e.top + e.h * (1 - frac), band = e.h * 0.07;
    let row = e.pts.filter(([x, y]) => Math.abs(y - yy) < band && (side < 0 || (side === 0) === (x < e.mid)));
    if (!row.length) row = e.pts.filter(([, y]) => Math.abs(y - yy) < band * 2);
    if (!row.length) return;
    const [ex, ey] = row[(Math.random() * row.length) | 0];
    live.push({ ex, ey, t0: now, life: rnd(LIFE_MIN, LIFE_MAX), swap: rnd(90, 200), size: rnd(0.13, 0.21),
                a: (Math.random() * TIA.length) | 0, b: (Math.random() * TIA.length) | 0, flip: ex < e.mid });
  }
  function step(e, now) {
    if (now > climb.next && !climb.rungs.length) {                // plan a new climb: random rungs, random speed
      const n = 4 + ((Math.random() * 6) | 0), dur = rnd(600, 1500), start = rnd(0, 0.25);
      for (let r = 0; r < n; r++)
        climb.rungs.push({ at: now + dur * r / n + rnd(-40, 40), frac: start + (0.95 - start) * (r + rnd(0.2, 0.8)) / n });
      climb.next = now + dur + rnd(400, 2200);
    }
    while (climb.rungs.length && now >= climb.rungs[0].at) {
      const r = climb.rungs.shift(), k = Math.random();
      if (k < 0.15) continue;                                     // a gap in the climb
      if (k < 0.6) spark(e, r.frac, Math.random() < 0.5 ? 0 : 1, now);
      else { spark(e, r.frac, 0, now); spark(e, r.frac + rnd(-0.03, 0.05), 1, now); }
    }
    if (Math.random() < 0.012) spark(e, rnd(0.1, 0.9), -1, now);  // a stray spark between climbs
    live = live.filter(sp => now - sp.t0 <= sp.life);
  }
  function put(c, x, y, h, flip) {
    const w = c.width * h / c.height;
    ctx.save(); ctx.translate(Math.round(x), Math.round(y)); if (flip) ctx.scale(-1, 1);
    ctx.drawImage(c, -w / 2, -h / 2, w, h); ctx.restore();
  }

  const draw0 = drawPet;
  globalThis.drawPet = function (stage, s, fx, fy, white = 0, glow = 0, left = false) {
    const box = draw0.apply(this, arguments);
    if (!LEGEND(stage) || white > 0 || !TIA.length || !box || !s) return box;
    const im = IMG[`${stage}/${s.f}`];
    if (!im) return box;
    const e = edge(im), now = performance.now();
    if (now !== stepped) { stepped = now; step(e, now); }
    for (const sp of live) {
      const c = TIA[Math.floor((now - sp.t0) / sp.swap) % 2 ? sp.b : sp.a];
      if (!c) continue;
      // facing left the frame is drawn mirrored, so are the spark spots
      put(c, box.x + (left ? im.width - sp.ex : sp.ex), box.y + sp.ey, e.h * sp.size, left ? !sp.flip : sp.flip);
    }
    return box;
  };
})();
