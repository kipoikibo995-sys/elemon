// The pet's stats / profile pages with the pet's own values, on the demo's dark wood (the user tried the blurred room
// of assets/CAP-NHAT_man-chao-elemon.md in the pet box on 25/10 and wanted the wood back, balanced):
//   - the pedestal grows with a big pet instead of the pet shrinking to the pedestal; the pet only shrinks when it
//     would not fit the box at all
//   - Sinh tồn, Linh khí and Hồ sơ show the game's numbers: game/build_game.py draws those pages without their
//     values and notes where each one goes (P.live), and they are drawn here every frame
// It wraps the demo's drawStats (its first drawImage there, the page picture, is the one drawn this way, and its
// drawPet call is placed on the pedestal). Pieces: img/stats_be.png, img/hs_*.png.
(() => {
  const P = __NEN_CHI_SO__;                                       // filled in by game/build_game.py (null: no pieces)
  if (!P || typeof drawStats !== 'function') return;
  const L = P.live || {};
  const STAGE_NAME = { baby: 'Con', child: 'Nhi', teen: 'Thiếu niên', adult: 'Trưởng thành', legend: 'Huyền thoại',
                       adult4: 'Trưởng thành', legend4: 'Huyền thoại' };
  // not kept by the game yet: a temper from the element, a weight from the stage and how full the pet is
  const TEMPER = { hoa: 'Hiếu chiến', kim: 'Cứng cỏi', moc: 'Hiền hòa', thuy: 'Lanh lợi', tho: 'Điềm tĩnh' };
  const WEIGHT = { baby: 6, child: 10, teen: 16, adult: 22, legend: 26, adult4: 22, legend4: 26 };
  const HATES = { hoa: 'thuy', kim: 'hoa', moc: 'kim', tho: 'moc', thuy: 'tho' };   // the element that overcomes
  const IM = {};
  const want = ['stats_be', 'hs_exp_fill', 'hs_tim-day', 'hs_weight_mark',
                ...(L.bars || []).map(b => 'hs_fill_' + b.fill), ...Object.values(L.foods || {}).map(f => 'hs_food_' + f)];
  for (const n of new Set(want)) { const i = new Image(); i.onload = () => { IM[n] = i; }; i.src = `img/${n}.png`; }

  // ---------- the pet and its pedestal ----------
  const FIT_W = 222, TOP = 70, TOP_GEMS = 104, PED_BOTTOM = 404, PED_SHARE = 0.8;
  const SIZE = new Map();
  function drawnSize(im) {
    let r = SIZE.get(im);
    if (r) return r;
    const c = document.createElement('canvas'); c.width = im.width; c.height = im.height;
    const g = c.getContext('2d'); g.drawImage(im, 0, 0);
    const p = g.getImageData(0, 0, c.width, c.height).data;
    let x0 = c.width, x1 = -1, y0 = c.height, y1 = -1;
    for (let y = 0; y < c.height; y += 2) for (let x = 0; x < c.width; x += 2)
      if (p[(y * c.width + x) * 4 + 3] > 24) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    r = x1 < 0 ? [im.width, im.height] : [x1 - x0 + 2, y1 - y0 + 2];
    SIZE.set(im, r);
    return r;
  }
  // pet scale k, pedestal box, feet line; measured on the stage's standing frame so nothing changes while it moves
  function layout(stage) {
    const [bx, by, bw, bh] = P.be;
    const im = IMG[`${stage}/idle-0`] || IMG[`${stage}/${DATA.stages[stage].meta.frames[0]}`];
    const [w, h] = im ? drawnSize(im) : [bw, bh];
    const top = S.stats === 2 ? TOP_GEMS : TOP;
    let k = Math.min(1, FIT_W / w), out;
    for (let pass = 0; pass < 2; pass++) {
      const pw = Math.max(bw, w * k * PED_SHARE), ph = bh * pw / bw;
      const feet = Math.min(P.feet, PED_BOTTOM - ph * 0.58);
      out = { k, feet, ped: [130 - pw / 2, feet - ph * 0.42, pw, ph] };
      if (h * k <= feet - top) break;
      k = (feet - top) / h;                                       // too tall even so: smaller, then size the pedestal again
    }
    return out;
  }

  // ---------- the page picture (made without a pedestal), then the pedestal sized to the pet and its name ----------
  function page(bg) {
    const be = IM.stats_be;
    if (!be) return false;
    ctx.drawImage(bg, 0, 0);
    const [px, py, pw, ph] = layout(S.stage).ped;
    ctx.drawImage(be, Math.round(px), Math.round(py), Math.round(pw), Math.round(ph));
    text(DATA.pet.name, 130, 418, 17, '#f6e6c8', 'center', true, 3);
    text(`${DATA.creature_name || ''} · ${STAGE_NAME[S.stage] || ''}`, 130, 437, 12, '#e0cfb0', 'center', false, 3);
    return true;
  }

  // ---------- the pet's own values ----------
  const put = (s, sp, colour) => text(String(s), sp.x, sp.y + Math.round(sp.size * 0.62), sp.size, colour || sp.colour,
                                       sp.align, sp.bold);
  function fill(name, x, y, frameH, value) {                      // a bar's fill cut at value %, as the page draws it
    const f = IM[name];
    if (!f) return;
    const cap = Math.round(f.width * 0.085), w = cap + Math.round((f.width - 2 * cap) * Math.max(0, Math.min(100, value)) / 100);
    ctx.drawImage(f, 0, 0, w, f.height, x, y + Math.floor((frameH - f.height) / 2), w, f.height);
  }
  const foodName = file => {
    for (const row of (DATA.shop && DATA.shop.rows) || []) for (const r of row) if (r.file === file) return r.name;
    const b = (DATA.bag || []).find(x => x.file === file);
    return b ? b.name : file;
  };
  function values() {
    const n = S.need, he = EL();
    if (S.stats === 0 && L.bars) {
      const v = [n.no, n.vui, n.sach, n.nl, S.sick ? 25 : 100];  // Sức khỏe: the game only knows ill or well
      L.bars.forEach((b, i) => fill('hs_fill_' + b.fill, b.x, b.y, L.barH, v[i]));
      L.nums.forEach((sp, i) => put(Math.round(v[i]), sp, v[i] < 20 ? '#ff8a6a' : null));
    }
    if (S.stats === 1 && L.radarC) {
      const [cx, cy, r] = L.radarC, pts = L.radarKeys.map((key, i) => {
        const a = i * 72 * Math.PI / 180, v = Math.max(3, Math.min(100, S.lk[key] || 0)) / 100;
        return [cx + r * v * Math.sin(a), cy - r * v * Math.cos(a)];
      });
      ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath();
      ctx.fillStyle = 'rgb(205,112,78)'; ctx.fill();
      ctx.lineWidth = 2; ctx.strokeStyle = 'rgb(250,178,128)'; ctx.stroke();
      for (const sp of L.radar) {
        const key = L.radarKeys[L.radarNames.indexOf(sp.name)];
        put(`${sp.name} ${Math.round(S.lk[key] || 0)}`, sp);
      }
    }
    if (S.stats === 3 && L.hs) {
      const h = L.hs, [lo, hi] = LV[S.stage] || [S.level, S.level], cap = STAGE_EXP[S.stage] || 1;
      const per = cap / Math.max(1, hi - lo), into = S.level >= hi ? per : S.xp - (S.level - lo) * per;
      if (h.badge) put(S.level, h.badge);
      if (h.level) put(`Level ${S.level}`, h.level);
      if (h.exp) put(`EXP ${Math.floor(into)}/${Math.round(per)}`, h.exp);
      if (h.expbar) fill('hs_exp_fill', h.expbar.x, h.expbar.y, L.expH, 100 * into / per);
      if (h.pers) put(TEMPER[he] || '', h.pers);
      for (let i = 0; i < Math.min(5, Math.floor(S.tim)); i++) if (h.hearts && h.hearts[i] && IM['hs_tim-day'])
        ctx.drawImage(IM['hs_tim-day'], h.hearts[i][0], h.hearts[i][1]);
      for (const [spot, tspot, el] of [[h.likes, h.likes_t, he], [h.dislikes, h.dislikes_t, HATES[he]]]) {
        const file = L.foods[el], ic = IM['hs_food_' + file];
        if (spot && ic) ctx.drawImage(ic, spot[0] - ic.width / 2, spot[1] - ic.height / 2);
        if (tspot) put(foodName(file), tspot);
      }
      const kg = Math.round((WEIGHT[S.stage] || 10) + (n.no - 50) / 50 * 3);
      if (h.weight_t) put(`Thể trạng · ${kg}kg`, h.weight_t);
      if (h.wbar && IM.hs_weight_mark) {
        const [bx, by, bw, bh] = h.wbar, mk = IM.hs_weight_mark;
        const mx = bx + Math.round(bw * Math.max(0, Math.min(1, (kg - L.weight[0]) / (L.weight[1] - L.weight[0]))));
        ctx.drawImage(mk, mx - Math.floor(mk.width / 2), by + Math.floor(bh / 2 - mk.height / 2));
      }
      const home = DATA.houses && DATA.houses[S.house];
      if (h.home) put(home ? home.name : '', h.home);
      if (h.home2) put(home ? `Nhà cấp ${home.tier}` : '', h.home2);
    }
  }

  const stats0 = drawStats, draw = ctx.drawImage;
  globalThis.drawStats = function (now) {
    let first = true;
    const pet0 = globalThis.drawPet;
    ctx.drawImage = function (im, ...rest) {
      if (first) { first = false; if (rest.length === 2 && rest[0] === 0 && rest[1] === 0 && page(im)) return; }
      return draw.call(ctx, im, ...rest);
    };
    // the pet stands on the (maybe bigger) pedestal: moved to its feet line, shrunk only when it must be
    globalThis.drawPet = function (stage, s, fx, fy, ...rest) {
      const { k, feet } = layout(stage);
      ctx.save(); ctx.translate(fx, feet); ctx.scale(k, k); ctx.translate(-fx, -fy);
      try { return pet0(stage, s, fx, fy, ...rest); } finally { ctx.restore(); }
    };
    try { stats0(now); } finally { ctx.drawImage = draw; globalThis.drawPet = pet0; }
    values();
  };
})();
