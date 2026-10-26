// Elemon: the pet drawn the way the demo's drawPet does, but each pose made once. drawPet builds, every frame, the
// frame with its chest lifted (3 draws), a dark copy (a fill over it), the dark copy 12 times round it for the
// outline, then the frame: ~16 passes over the pet, over a million pixels a frame for a grown pet, which the
// R36S (pixels by its CPU) felt as lag in the room and every screen with the pet. Here the finished picture,
// outline included, is kept per frame and lift (the last CACHE_MAX used) and put down in one draw. The white-out
// (evolving) and glow are rare and changing: those still go the demo's way.
(() => {
  if (typeof drawPet !== 'function') return;
  const CACHE_MAX = 40;                         // poses kept (a grown pet's ~360 KB each)
  const PAD = 2;                                // the outline reaches 2 px out
  const plain = drawPet, cache = new Map();
  const free = c => { if (c && c.__id !== undefined && typeof __cv === 'object' && __cv.free) __cv.free(c.__id); };
  const canvas = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };

  function pose(im, m, br) {
    const [, ay] = m.anchor, split = ay - Math.round(m.canvas[1] * 0.4), lo = Math.max(0, -br);
    const W = im.width, H = im.height + 8;
    const o = canvas(W, H), ox = o.getContext('2d');                 // the frame, chest lifted by br
    ox.drawImage(im, 0, split, W, im.height - split, 0, split + 8, W, im.height - split);
    if (br > 0) ox.drawImage(im, 0, split - 1, W, 1, 0, split + 8 - br - 1, W, br + 1);
    ox.drawImage(im, 0, lo, W, split - lo, 0, 8 - br + lo, W, split - lo);
    const d = canvas(W, H), dx = d.getContext('2d');                 // its dark copy
    dx.drawImage(o, 0, 0); dx.globalCompositeOperation = 'source-in';
    dx.fillStyle = OUTLINE; dx.fillRect(0, 0, W, H); dx.globalCompositeOperation = 'source-over';
    const c = canvas(W + 2 * PAD, H + 2 * PAD), cx = c.getContext('2d');
    for (const [ex, ey] of EDGE) cx.drawImage(d, PAD + ex, PAD + ey);
    cx.drawImage(o, PAD, PAD);
    free(o); free(d);
    return c;
  }

  drawPet = function (stage, s, fx, fy, white = 0, glow = 0, left = false) {
    const st = DATA.stages[stage], im = st && IMG[`${stage}/${s.f}`];
    if (white > 0 || glow > 0 || !im || !im.width) return plain.apply(this, arguments);
    const m = st.meta, [ax, ay] = m.anchor, dx = s.f.startsWith('walk') ? 0 : ((m.align || {})[s.f] || [0])[0];
    const br = Math.round(s.br), key = `${stage}/${s.f}/${br}`;
    let e = cache.get(key);
    if (e && e.im !== im) { free(e.c); cache.delete(key); e = null; }          // another pet, or the frame reloaded
    if (e) { cache.delete(key); cache.set(key, e); }                           // most recently used last
    else {
      e = { im, c: pose(im, m, br) };
      cache.set(key, e);
      if (cache.size > CACHE_MAX) { const [k0, e0] = cache.entries().next().value; cache.delete(k0); free(e0.c); }
    }
    // where the demo puts it (facing left: mirrored round the feet); the outline set is symmetric, so the
    // mirrored picture is the demo's mirrored outline + frame
    const x = Math.round(left ? fx - s.x - (im.width - ax) - dx : fx + s.x - ax + dx), y = Math.round(fy + s.y - ay - 8);
    const c = e.c;
    if (!left) ctx.drawImage(c, x - PAD, y - PAD);
    else { ctx.save(); ctx.translate(x - PAD + c.width, y - PAD); ctx.scale(-1, 1); ctx.drawImage(c, 0, 0); ctx.restore(); }
    return { x, y: y + 8, w: im.width, h: im.height };
  };
})();
