// Võ đường (assets/CAP-NHAT_man-chao-elemon.md, "Võ đường – MENU chọn" and "tab Tập luyện", 2026-10-25): Võ đường
// on the map opens a menu of 3 cards (Tập luyện, Solo đối kháng (comes later), Học né chiêu), and
// Tập luyện is 10 turns at the sandbag: 5 punches on the timing bar (a needle runs over it, A in the green middle is a
// strong hit: big swing, big flash, most EXP), then 5 dash-strikes aimed with the combat arena's sweeping arrow
// (preview/dau-truong).
// Each turn costs a little Năng lượng and No, and its EXP
// goes through the game's hourly EXP pool (song-that.js) like any other. The demo's own Võ đường (one instant
// training back in the room) is replaced. Pictures: assets/r36s/vo-duong/ (game/build_game.py copies them to img/vd/).
(() => {
  if (typeof press !== 'function' || typeof drawEvo !== 'function' || typeof PL === 'undefined') return;
  const MODE = 'voduong', PUNCHES = 10;
  const IM = {};
  const pics = ['menu/bang-chu', 'menu/bang-tieu-de', 'menu/khoa', 'menu/the_chon', 'menu/the_thuong',
    ...['tap-luyen', 'solo', 'ne-chieu'].flatMap(n => [`menu/hinh_${n}`, `menu/hinh_${n}_lon`]),
    'tap/nen_vo-duong', 'tap/thanh-nhip', 'tap/kim-nhip', ...[0, 1, 2, 3].flatMap(i => [`tap/bao-cat_${i}`, `tap/fx-trung_${i}`]),
    ...[0, 1, 2, 3, 4, 5, 6, 7].flatMap(i => [`tap/bao-cat8_${i}`, `tap/fx-trung8_${i}`]),
    ...['bao_cham-than', 'bao_len', 'bao_trai', 'bao_xuong', 'dan_bong-go', 'dan_cau-lua', 'dan_cau-nuoc', 'dan_con-xoay',
        'fx_bui', 'fx_ne-hoan-hao', 'fx_trung-don', 'tim_day', 'tim_rong', 'su-phu_cuoi', 'su-phu_dung', 'su-phu_lay-da',
        'su-phu_nem-cao', 'su-phu_nem-thap', 'su-phu_nem', 'su-phu_ngac-nhien', 'su-phu_that-vong', 'nen_san-da'].map(n => 'ne/' + n)];
  for (const n of pics) { const i = new Image(); i.onload = () => { IM[n] = i; }; i.src = `img/vd/${n}.png`; }
  const CARDS = [{ key: 'tap-luyen', name: 'Tập luyện', open: true },
                 { key: 'solo', name: 'Solo đối kháng', get open() { return typeof __soloOpen === 'function'; } },   // solo.js
                 { key: 'ne-chieu', name: 'Học né chiêu', open: true }];
  const CARD_X = [140, 320, 500], CARD_Y = 210, LABEL_Y = 352;
  const HIT = { strong: { exp: 8, bag: [2, 3, 1, 0], fx: 1, word: 'Mạnh!' }, ok: { exp: 4, bag: [1, 3, 0], fx: 0.75, word: 'Trúng' },
                weak: { exp: 1, bag: [1, 0], fx: 0.5, word: 'Hụt nhịp' } };
  const sfx = (n, v) => { if (typeof SOUND === 'object' && SOUND) SOUND.sfx(n, v); };
  const pic = n => IM[n];
  const centre = (im, x, y) => im && ctx.drawImage(im, Math.round(x - im.width / 2), Math.round(y - im.height / 2));

  // ---------- the pet's size, to place it on the mat and hang the bag at its chest ----------
  const SIZE = new Map();
  function extent(stage) {                                        // [drawn height, right edge from the feet anchor]
    const im = IMG[`${stage}/idle-0`] || IMG[`${stage}/${DATA.stages[stage].meta.frames[0]}`];
    if (!im) return [120, 50];
    let r = SIZE.get(im);
    if (r) return r;
    const c = document.createElement('canvas'); c.width = im.width; c.height = im.height;
    const g = c.getContext('2d'); g.drawImage(im, 0, 0);
    const p = g.getImageData(0, 0, c.width, c.height).data;
    let x1 = -1, y0 = c.height, y1 = -1;
    for (let y = 0; y < c.height; y += 2) for (let x = 0; x < c.width; x += 2)
      if (p[(y * c.width + x) * 4 + 3] > 24) { if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    r = x1 < 0 ? [120, 50] : [y1 - y0, x1 - DATA.stages[stage].meta.anchor[0]];
    SIZE.set(im, r);
    return r;
  }

  // ---------- the menu ----------
  function drawMenu(now) {
    const v = S.vd;
    ctx.drawImage(pic('tap/nen_vo-duong'), 0, 0);
    // a pastel wash so the cards stand out, as the user's mock-up of this menu (measured on it: 37 % of a light
    // blue-cream, half the colour left)
    ctx.fillStyle = 'rgba(206,219,228,0.37)'; ctx.fillRect(0, 0, 640, 480);
    centre(pic('menu/bang-tieu-de'), 320, 48);
    title('VÕ ĐƯỜNG', 320, 46, 26, '#ffe6a8', 4);
    CARDS.forEach((c, i) => {
      const on = i === v.sel, bob = on ? Math.round(2 * Math.sin(now / 260)) : 0;
      const card = pic(on ? 'menu/the_chon' : 'menu/the_thuong');
      centre(card, CARD_X[i], CARD_Y + bob);
      centre(pic(`menu/hinh_${c.key}${on ? '_lon' : ''}`), CARD_X[i], CARD_Y + bob);
      centre(pic('menu/bang-chu'), CARD_X[i], LABEL_Y);
      const k = pic('menu/khoa'), tx = c.open ? CARD_X[i] : CARD_X[i] + 9;
      if (!c.open && k) ctx.drawImage(k, CARD_X[i] - 62, LABEL_Y - 14, k.width * 0.34, k.height * 0.34);   // not open yet
      text(c.name, tx, LABEL_Y, c.name.length > 12 ? 13 : 15, c.open ? '#ffe6a8' : '#d8c8a8', 'center', true, 3);
    });
    text(['Đấm theo nhịp, lướt tới đánh theo mũi tên: nhiều EXP', CARDS[1].open ? 'Đấu 1-1 với bot: 15 pet Lv2' : 'Sắp có',
          'Sư phụ ném đòn: nhảy, lùi, cúi cho đúng lúc'][v.sel], 320, 404, 14, '#fff2d8', 'center', true, 3);
    text('◀ ▶ chọn · A: vào · B: ra bản đồ', 320, 462, 13, '#f0e4ce', 'center', false, 3);
  }

  // ---------- Tập luyện: round 1 punches on the timing bar, round 2 dash-strikes with the arena's sweeping aim ------
  // Everything is fitted to the pet's own punch: the frame where its fist reaches furthest (and how high that fist is)
  // is measured once, the bag hangs exactly there and swings, with the flash, at the moment of contact. Round 2 uses the
  // aim of preview/dau-truong (the combat session's arena): a funnel ±HALF from the fist with an arrow sweeping up and
  // down by itself; A sends the pet dashing along the arrow to strike the bag, which hangs at a new height each time.
  // Green spot on the funnel's rim = a strong hit, yellow = a hit, elsewhere the dash flies past.
  const NHIP = 5, HALF = 0.6, SWEEP_MS = 1100, DASH_MS = 230, HOLD_MS = 260, BACK_MS = 320, GREEN = 0.07, YELLOW = 0.17;
  const FEET = 392, MAX_H = 228, PX1 = 200, PX2 = 130, BAG2_X = 452;
  // the sandbag: the smooth 8-frame set (drawn with ChatGPT from the 4-frame one, 25/10) when it is there, else the
  // first set; where the body is in its picture, how fast it plays, which frames a hit runs through
  const BAG4 = { name: k => `tap/bao-cat_${k}`, top: 70, h: 112, l: 22, ms: 110,
                 seq: { strong: [2, 3, 1, 0], ok: [1, 3, 0], weak: [1, 0] }, fx: k => `tap/fx-trung_${k}`, fxN: 4, fxMs: 70 };
  const BAG8 = { name: k => `tap/bao-cat8_${k}`, top: 78, h: 105, l: 33, ms: 70,
                 seq: { strong: [1, 2, 3, 3, 2, 4, 5, 6, 7], ok: [1, 2, 4, 5, 6, 7], weak: [1, 6, 7] },
                 fx: k => `tap/fx-trung8_${k}`, fxN: 8, fxMs: 45 };
  const B = () => pic('tap/bao-cat8_0') && pic('tap/bao-cat8_7') && pic('tap/fx-trung8_7') ? BAG8 : BAG4;
  const needle = (t, now) => 0.5 - 0.5 * Math.cos((now - t.t0) * 2 * Math.PI / t.period);
  const arrow = (t, now) => Math.sin(((now - t.t0) % SWEEP_MS) / SWEEP_MS * Math.PI * 2) * HALF;
  const ease = x => 1 - (1 - x) * (1 - x);
  const punchAnim = stage => { const a = DATA.stages[stage].anims; return a.punch || a.attack || a.train; };

  // the drawn part of a frame: its right edge, how high the pixels at that edge are, its top and bottom
  const INFO = new Map();
  function frameInfo(im) {
    let r = INFO.get(im);
    if (r) return r;
    const c = document.createElement('canvas'); c.width = im.width; c.height = im.height;
    const g = c.getContext('2d'); g.drawImage(im, 0, 0);
    const p = g.getImageData(0, 0, c.width, c.height).data, W = c.width, H = c.height;
    const on = (x, y) => p[(y * W + x) * 4 + 3] > 40;
    let x1 = -1, y0 = H, y1 = -1;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (on(x, y)) { if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    let sy = 0, n = 0;
    for (let y = 0; y < H; y++) for (let x = Math.max(0, x1 - 5); x <= x1; x++) if (on(x, y)) { sy += y; n++; }
    r = x1 < 0 ? { x1: W / 2, yR: H / 2, y0: 0, y1: H } : { x1, yR: n ? sy / n : (y0 + y1) / 2, y0, y1 };
    INFO.set(im, r);
    return r;
  }
  // how far the pet's fist reaches from its feet anchor, how high, and when (ms into the punch); scale to fit
  const REACH = new Map();
  function reach(stage) {
    const key = DATA.pet.creature + '/' + stage;
    let r = REACH.get(key);
    if (r) return r;
    const m = DATA.stages[stage].meta, [ax, ay] = m.anchor;
    const idle = IMG[`${stage}/idle-0`] || IMG[`${stage}/${m.frames[0]}`];
    if (!idle) return { k: 1, ph: 120, reach: 50, fy: -66, tHit: 160, bs: 1, lunge: null };
    const fi = frameInfo(idle), ph = fi.y1 - fi.y0, k = Math.min(1, MAX_H / ph);
    let best = { reach: fi.x1 - ax, fy: fi.y0 + ph * 0.45 - ay, t: 160 };   // no punch: the front of the body, chest high
    const pa = punchAnim(stage);
    if (pa) for (let t = 0; t < total(pa); t += 10) {
      const s = sample(pa, t), im = IMG[`${stage}/${s.f}`];
      if (!im) continue;
      const f = frameInfo(im), dx = s.f.startsWith('walk') ? 0 : ((m.align || {})[s.f] || [0])[0], rr = s.x + dx + f.x1 - ax;
      if (rr > best.reach + 1) best = { reach: rr, fy: s.y + f.yR - ay, t };
    }
    r = { k, ph: ph * k, reach: best.reach * k, fy: best.fy * k, tHit: best.t, bs: Math.max(0.9, Math.min(1.4, ph * k / 160)) };
    REACH.set(key, r);
    return r;
  }
  function drawPetAt(stage, s, x, feetY, k, white = 0) {           // the pet scaled by k, feet at (x, feetY)
    ctx.save(); ctx.translate(x, feetY); ctx.scale(k, k); ctx.translate(-x, -FEET);
    drawPet(stage, s, x, FEET, white);
    ctx.restore();
  }
  function drawBag(left, bodyY, bs, f) {                          // the bag with its body's centre at bodyY
    const set = B(), bag = pic(set.name(f));
    if (!bag) return;
    const top = Math.round(bodyY - (set.top + set.h / 2) * bs);
    if (top > 0) { ctx.fillStyle = '#5a3a1a'; ctx.fillRect(Math.round(left + bag.width / 2 * bs - 2), 0, 4, top + 4); }
    ctx.drawImage(bag, Math.round(left), top, bag.width * bs, bag.height * bs);
  }
  const swing = (kind, since) => {
    const set = B(), k = Math.floor(since / set.ms), seq = set.seq[kind];
    return since < 0 || k >= seq.length ? 0 : seq[k];
  };
  function flash(kind, since, x, y) {
    const set = B();
    if (since < 0 || since >= set.fxN * set.fxMs) return;
    const fx = pic(set.fx(Math.floor(since / set.fxMs))), k = HIT[kind].fx;
    if (fx) ctx.drawImage(fx, x - fx.width * k / 2, y - fx.height * k / 2, fx.width * k, fx.height * k);
  }

  function startTraining(now) {
    if (S.stage === 'baby') return toast('Tiến hóa lên Nhi để mở Tập luyện');
    if (S.sick || S.need.nl < 25) return toast(`${DATA.pet.name} ${S.sick ? 'đang ốm' : 'mệt quá'}, về nghỉ đã`);
    fadeTo(() => { S.vd = { view: 'train', sel: S.vd.sel, t0: performance.now(), period: 1300, n: 0, exp: 0, hit: null, end: 0 }; });
  }
  function newTarget(t) {                                         // the bag's height for the next dash
    const R = reach(S.stage), oy = FEET + R.fy, dist = BAG2_X - PX2 - R.reach;
    t.ty = Math.max(130, Math.min(FEET - 30, oy + (Math.random() * 2 - 1) * Math.tan(HALF * 0.8) * dist));
  }
  function score(kind) {
    const t = S.vd;
    S.need.nl = Math.max(0, S.need.nl - 2); S.need.no = Math.max(0, S.need.no - 1);
    const xp0 = S.xp; gainExp(HIT[kind].exp); t.exp += Math.max(0, S.xp - xp0);
    if (t.n >= PUNCHES || S.need.nl < 5) t.end = performance.now() + 900;
  }
  function punch(now) {
    const t = S.vd;
    if (t.end) return;
    if (t.n < NHIP) {                                             // round 1: the timing bar
      if (t.hit && now - t.hit.t < 320) return;
      const d = Math.abs(needle(t, now) - 0.5), kind = d < 0.12 ? 'strong' : d < 0.27 ? 'ok' : 'weak';
      t.n++; t.hit = { kind, t: now, aim: false };
      t.period = Math.max(800, t.period - 70);
      setTimeout(() => sfx(kind === 'weak' ? 'trung-don' : 'dam', kind === 'strong' ? 250 : 200), reach(S.stage).tHit);
      if (t.n === NHIP) { t.t0 = now + 1100; newTarget(t); }     // round 2 after a breath
      return score(kind);
    }
    if (now < t.t0 || (t.hit && t.hit.aim && now - t.hit.t < DASH_MS + HOLD_MS + BACK_MS)) return;
    const R = reach(S.stage), ox = PX2 + R.reach, oy = FEET + R.fy, lx = BAG2_X + B().l * R.bs;
    const ang = arrow(t, now), want = Math.atan2(t.ty - oy, lx - ox), d = Math.abs(ang - want);
    const kind = d < GREEN ? 'strong' : d < YELLOW ? 'ok' : 'weak';
    t.n++; t.hit = { kind, t: now, aim: true, ang, ty: t.ty, D: lx - ox + 4 };
    setTimeout(() => sfx(kind === 'weak' ? 'quay-lai' : 'dam', kind === 'strong' ? 250 : 200), DASH_MS);
    setTimeout(() => { if (S.vd === t && !t.end) { newTarget(t); t.t0 = performance.now() + 200; } }, DASH_MS + HOLD_MS + BACK_MS + 100);
    score(kind);
  }

  function drawAim(o, ang, want, r) {                             // the funnel, the hit spot and the arrow
    ctx.save(); ctx.globalAlpha = 0.42; ctx.fillStyle = '#c4501a';
    ctx.beginPath(); ctx.moveTo(o[0], o[1]);
    for (let i = 0; i <= 12; i++) { const a = -HALF + 2 * HALF * i / 12; ctx.lineTo(o[0] + r * Math.cos(a), o[1] + r * Math.sin(a)); }
    ctx.closePath(); ctx.fill();
    ctx.globalAlpha = 1; ctx.strokeStyle = '#ffb347'; ctx.lineWidth = 3; ctx.stroke();
    const band = (a0, a1, col, lw) => {
      a0 = Math.max(-HALF, a0); a1 = Math.min(HALF, a1);
      if (a1 <= a0) return;
      ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.beginPath();
      for (let i = 0; i <= 6; i++) { const a = a0 + (a1 - a0) * i / 6, x = o[0] + (r - 6) * Math.cos(a), y = o[1] + (r - 6) * Math.sin(a); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
      ctx.stroke();
    };
    band(want - YELLOW - 0.02, want + YELLOW + 0.02, '#3a1406', 16);
    band(want - YELLOW, want + YELLOW, '#ffd23a', 11);
    band(want - GREEN, want + GREEN, '#5ee04a', 11);
    const ex = o[0] + r * 0.9 * Math.cos(ang), ey = o[1] + r * 0.9 * Math.sin(ang), hx = Math.cos(ang), hy = Math.sin(ang);
    for (const [col, lw] of [['#3a1406', 7], ['#ffe08a', 3]]) {    // a dark edge so it reads on the bright floor
      ctx.strokeStyle = col; ctx.lineWidth = lw;
      ctx.beginPath(); ctx.moveTo(o[0] + 14 * hx, o[1] + 14 * hy); ctx.lineTo(ex, ey); ctx.stroke();
    }
    ctx.fillStyle = '#3a1406'; ctx.beginPath();
    ctx.moveTo(ex + hx * 15, ey + hy * 15); ctx.lineTo(ex - hy * 9, ey + hx * 9); ctx.lineTo(ex + hy * 9, ey - hx * 9); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#ffe08a'; ctx.beginPath();
    ctx.moveTo(ex + hx * 12, ey + hy * 12); ctx.lineTo(ex - hy * 6, ey + hx * 6); ctx.lineTo(ex + hy * 6, ey - hx * 6); ctx.closePath(); ctx.fill();
    ctx.restore();
  }

  function drawTrain(now) {
    const t = S.vd, stage = S.stage, R = reach(stage), pa = punchAnim(stage), idle = idleOf(stage);
    const h = t.hit, at = h ? now - h.t : 1e9, round2 = t.n >= NHIP && !(h && !h.aim && at < 900);   // the 5th punch ends first
    ctx.drawImage(pic('tap/nen_vo-duong'), 0, 0);
    let word = null;
    if (!round2) {
      // round 1: the bag hangs where the fist lands; swing and flash start at the moment of contact
      const cx = PX1 + R.reach, cy = FEET + R.fy, since = h ? at - R.tHit : -1;
      drawBag(cx - B().l * R.bs - 4, cy + B().h * R.bs * 0.12, R.bs, h ? swing(h.kind, since) : 0);
      drawPetAt(stage, pa && h && at < total(pa) ? sample(pa, at) : sample(idle, now), PX1, FEET, R.k);
      if (h) { flash(h.kind, since, cx, cy); if (since >= 0 && since < 700) word = [HIT[h.kind].word, cx, cy, since]; }
      if (!t.end) {                                               // the timing bar under the mat
        const bar = pic('tap/thanh-nhip'), kim = pic('tap/kim-nhip'), bx = 320 - 120, byy = 432;
        if (bar) ctx.drawImage(bar, bx, byy);
        if (kim) ctx.drawImage(kim, Math.round(bx + 14 + needle(t, now) * (239 - 28) - kim.width / 2), byy - 30);
      }
    } else {
      // round 2: dash along the arrow, strike, step back
      const ox = PX2 + R.reach, oy = FEET + R.fy, lx = BAG2_X + B().l * R.bs;
      const dash = h && h.aim && at < DASH_MS + HOLD_MS + BACK_MS, miss = dash && h.kind === 'weak';
      const bagY = dash ? h.ty : t.ty || oy, since = dash ? at - DASH_MS : -1;
      drawBag(BAG2_X, bagY, R.bs, dash && !miss ? swing(h.kind, since) : 0);
      let px = PX2, py = FEET, s = sample(idle, now);
      if (dash) {
        const D = h.D * (miss ? 1.35 : 1), go = at < DASH_MS ? ease(at / DASH_MS) : at < DASH_MS + HOLD_MS ? 1
          : 1 - ease((at - DASH_MS - HOLD_MS) / BACK_MS);
        const lunge = pa ? sample(pa, R.tHit) : s;
        // the dash leaves two fading copies behind
        if (at < DASH_MS) for (const back of [0.3, 0.15]) {
          const g = Math.max(0, ease(at / DASH_MS) - back) * D;
          ctx.save(); ctx.globalAlpha = 0.3; drawPetAt(stage, lunge, PX2 + g, FEET + g * Math.tan(h.ang), R.k); ctx.restore();
        }
        px = PX2 + go * D; py = FEET + go * D * Math.tan(h.ang);
        s = at < DASH_MS + HOLD_MS ? lunge : sample(idle, now);
        if (!miss) flash(h.kind, since, lx, oy + D * Math.tan(h.ang));
        if (since >= 0 && since < 700) word = [miss ? 'Trượt' : HIT[h.kind].word, lx, oy + D * Math.tan(h.ang), since];
      }
      drawPetAt(stage, s, px, py, R.k);
      if (!t.end && !dash && now >= t.t0) {
        const want = Math.atan2((t.ty || oy) - oy, lx - ox);
        drawAim([ox, oy], arrow(t, now), want, Math.min(170, (lx - ox) * 0.8));
      }
    }
    if (word) text(word[0], word[1] + 8, word[2] - 64 - word[3] / 20, 18, h.kind === 'strong' ? '#ffe36a' : '#f0e4ce', 'center', true, 4);
    const what = round2 ? `lướt đánh ${Math.max(0, t.n - NHIP)}/${PUNCHES - NHIP}` : `đấm theo nhịp ${t.n}/${NHIP}`;
    text(`Tập luyện · ${what} · EXP +${Math.round(t.exp)}`, 320, 22, 15, '#fff2d8', 'center', true, 3);
    text(t.end ? 'Xong buổi tập!' : round2 ? (now < t.t0 ? 'Hiệp 2: mũi tên tự quét, pet lướt tới theo mũi tên' : 'A: lướt tới đánh khi mũi tên vào điểm xanh · B: thôi')
      : 'A: đấm khi kim vào vùng xanh · B: thôi', 320, 46, 13, '#f0e4ce', 'center', false, 3);
    if (t.end > 0 && now > t.end + 600 && S.fade === 0) {
      toast(`Tập xong: EXP +${Math.round(t.exp)}`);
      emote('bc_mo-hoi-nho'); S.bubble = 'tt_khat';
      fadeTo(() => { S.vd = { view: 'menu', sel: 0 }; });
      t.end = -1;                                                  // only once
    }
  }

  // ---------- Học né chiêu (CAP-NHAT_man-chao-elemon.md "HỌC NÉ CHIÊU", mock-up source/vo-duong/GHEP_ne-chieu.png) ------
  // The monkey master winds up (! over his head and an arrow showing where the throw will go), then throws: a low
  // throw is jumped (↑), a middle one stepped back from (←), a high one ducked under (↓). The right key close to the
  // moment of contact (≤ PERFECT_MS) is a PERFECT dodge, earlier a plain dodge, the wrong key or none a hit (a heart
  // lost, combo back to 0). Throws get faster, warnings shorter, and later on two can come one after the other.
  // 20 throws or 3 hearts lost ends it; EXP for every dodge (more for PERFECT) and for the best combo.
  const NE_THROWS = 20, NE_HEARTS = 3, PERFECT_MS = 150, NE_FEET = 400, NE_PX = 180, MASTER = [470, 250], THROW_X = 468;
  const NEED = { low: 'UP', mid: 'LEFT', high: 'DOWN' }, WARN = { low: 'ne/bao_len', mid: 'ne/bao_trai', high: 'ne/bao_xuong' };
  const THROW_POSE = { low: 'ne/su-phu_nem-thap', mid: 'ne/su-phu_nem', high: 'ne/su-phu_nem-cao' };
  const SHOTS = ['ne/dan_bong-go', 'ne/dan_cau-lua', 'ne/dan_con-xoay', 'ne/dan_cau-nuoc'];
  const lerp = (a, b, x) => a + (b - a) * Math.max(0, Math.min(1, x));
  function startNe(now) {
    if (S.stage === 'baby') return toast('Tiến hóa lên Nhi để học né chiêu');
    if (S.sick || S.need.nl < 25) return toast(`${DATA.pet.name} ${S.sick ? 'đang ốm' : 'mệt quá'}, về nghỉ đã`);
    fadeTo(() => {
      S.vd = { view: 'ne', sel: S.vd.sel, n: 0, hearts: NE_HEARTS, combo: 0, best: 0, dodged: 0, exp: 0, next: performance.now() + 1200,
               warn: null, shots: [], dodge: null, react: null, fxs: [], words: [], end: 0 };
    });
  }
  // the frames a pet dodges in, best first (stages have different sets: the young play-*, the grown-ups block/faint/hurt)
  const POSES = { UP: ['play-jump', 'play-air', 'jump-happy'], DOWN: ['play-crouch', 'faint', 'sleep-0'],
                  LEFT: ['block', 'play-land', 'walk-1'], HURT: ['hurt', 'sad', 'tired'] };
  const pose = (stage, kind) => POSES[kind].find(f => DATA.stages[stage].meta.frames.includes(f) && IMG[`${stage}/${f}`]);
  const neHeight = (h, R) => h === 'low' ? NE_FEET - 22 : h === 'mid' ? NE_FEET - R.ph * 0.5 : NE_FEET - R.ph * 0.84;
  function neDodge(btn, now) {
    const t = S.vd;
    if (t.end || !['UP', 'LEFT', 'DOWN'].includes(btn) || (t.dodge && now - t.dodge.t < 300)) return;
    t.dodge = { dir: btn, t: now };
  }
  function neGain(n) { const xp0 = S.xp; gainExp(n); S.vd.exp += Math.max(0, S.xp - xp0); }
  function neStep(now) {
    const t = S.vd, R = reach(S.stage), k = t.n / NE_THROWS;
    // a new wind-up when nothing is waiting
    if (!t.end && !t.warn && t.n < NE_THROWS && t.hearts > 0 && now >= t.next) {
      const h = ['low', 'mid', 'high'][Math.floor(Math.random() * 3)];
      t.warn = { h, at: now, throwAt: now + lerp(1000, 600, k) };
    }
    // the throw
    if (t.warn && now >= t.warn.throwAt) {
      const fly = lerp(950, 520, k), h = t.warn.h;
      t.shots.push({ h, t0: now, fly, img: SHOTS[Math.floor(Math.random() * SHOTS.length)], res: null, resT: 0 });
      t.n++; t.react = { img: THROW_POSE[h], t: now, ms: 280 }; t.warn = null;
      sfx('chieu', 150);
      t.next = t.n >= 8 && Math.random() < 0.3 ? now + 380 : now + fly + 550;   // later on: a second throw at once
      S.need.nl = Math.max(0, S.need.nl - 1);
    }
    // contact: dodged (the right key pressed during the throw), PERFECT (close to contact) or hit
    for (const s of t.shots) {
      const contact = s.t0 + s.fly;
      if (s.res || now < contact + 40) continue;
      const d = t.dodge, ok = d && d.dir === NEED[s.h] && d.t >= s.t0 - 250 && d.t <= contact + 40 && !d.used;
      const y = neHeight(s.h, R);
      if (ok) {
        d.used = true;
        const perfect = Math.abs(d.t - contact) <= PERFECT_MS;
        s.res = perfect ? 'perfect' : 'dodge'; s.resT = now;
        t.dodged++; t.combo++; t.best = Math.max(t.best, t.combo);
        neGain(perfect ? 5 : 3);
        t.fxs.push({ img: perfect ? 'ne/fx_ne-hoan-hao' : 'ne/fx_bui', x: NE_PX + (perfect ? 0 : -10), y: perfect ? y : NE_FEET - 12, t: now });
        t.words.push({ s: perfect ? 'PERFECT!' : 'Né được', x: NE_PX + 10, y: y - 50, t: now, col: perfect ? '#ffe36a' : '#f0e4ce' });
        if (perfect) t.react = { img: 'ne/su-phu_ngac-nhien', t: now, ms: 600 };
        else if (t.combo >= 3) t.react = { img: 'ne/su-phu_cuoi', t: now, ms: 500 };
        sfx(perfect ? 'vui' : 'quay-lai', perfect ? 230 : 170);
      } else {
        s.res = 'hit'; s.resT = now;
        t.hearts--; t.combo = 0;
        t.fxs.push({ img: 'ne/fx_trung-don', x: NE_PX + 20, y, t: now });
        t.words.push({ s: 'Trúng đòn!', x: NE_PX + 10, y: y - 50, t: now, col: '#ff8a6a' });
        t.react = { img: 'ne/su-phu_that-vong', t: now, ms: 550 }; t.hurt = now;
        sfx('trung-don', 220);
      }
    }
    t.shots = t.shots.filter(s => !s.res || now - s.resT < 700);
    t.fxs = t.fxs.filter(f => now - f.t < 450); t.words = t.words.filter(w => now - w.t < 800);
    // the end: 20 throws resolved, or no heart left
    if (!t.end && (t.hearts <= 0 || (t.n >= NE_THROWS && !t.warn && t.shots.every(s => s.res)))) {
      t.end = now; neGain(t.best * 2);
      t.react = { img: t.dodged >= 14 ? 'ne/su-phu_cuoi' : 'ne/su-phu_that-vong', t: now, ms: 99999 };
    }
    if (t.end > 0 && now - t.end > 1600 && S.fade === 0) {
      toast(`Né được ${t.dodged}/${NE_THROWS} · combo ${t.best} · EXP +${Math.round(t.exp)}`);
      emote(t.dodged >= 14 ? 'bc_tim' : 'bc_mo-hoi'); S.bubble = 'tt_khat';
      fadeTo(() => { S.vd = { view: 'menu', sel: 2 }; });
      t.end = -1;
    }
  }
  function drawNe(now) {
    neStep(now);
    const t = S.vd, stage = S.stage, R = reach(stage), anims = DATA.stages[stage].anims, idle = idleOf(stage);
    ctx.drawImage(pic('ne/nen_san-da') || pic('tap/nen_vo-duong'), 0, 0);     // the stone courtyard (VD_nen_san-da)
    // the master: winding up, throwing, reacting, or standing
    const m = t.react && now - t.react.t < t.react.ms ? t.react.img : t.warn ? 'ne/su-phu_lay-da' : 'ne/su-phu_dung';
    if (pic(m)) ctx.drawImage(pic(m), MASTER[0], MASTER[1]);
    if (t.warn) {                                                 // "!" over his head, the arrow where it will go
      const blink = Math.floor((now - t.warn.at) / 120) % 2 === 0;
      centre(pic('ne/bao_cham-than'), MASTER[0] + 95, MASTER[1] - 22 + (blink ? 0 : -3));
      centre(pic(WARN[t.warn.h]), 430, neHeight(t.warn.h, R));
    }
    // the pet in its own dodge frames while the dodge lasts: jumps up (↑), crouches or lies flat (↓), steps back on
    // guard (←); flinches when hit
    const d = t.dodge, open = t.shots.find(s => !s.res && d && d.dir === NEED[s.h]);
    const until = d ? Math.max(d.t + 450, open ? open.t0 + open.fly + 160 : 0) : 0, on = d && now < until;
    let px = NE_PX, feet = NE_FEET, s = sample(idle, now);
    if (on) {
      const p = Math.min(1, (now - d.t) / 120), out = Math.min(p, Math.max(0, (until - now) / 140)), f = pose(stage, d.dir);
      if (f) s = { f, x: 0, y: 0, br: 0 };
      if (d.dir === 'UP') feet -= 70 * out;
      if (d.dir === 'LEFT') px -= 45 * out;
    }
    const hurt = t.hurt && now - t.hurt < 380, hf = hurt && pose(stage, 'HURT');
    if (hf) s = { f: hf, x: 0, y: 0, br: 0 };
    drawPetAt(stage, s, px, feet, R.k, hurt ? 0.4 : 0);
    if (on && d.dir !== 'LEFT' && now - d.t < 260 && pic('ne/fx_bui')) { ctx.globalAlpha = 0.6; centre(pic('ne/fx_bui'), NE_PX, NE_FEET - 10); ctx.globalAlpha = 1; }
    // the throws in the air (a dodged one flies on past, a hit one stops)
    for (const sh of t.shots) {
      const p = (now - sh.t0) / sh.fly, im = pic(sh.img);
      if (!im || (sh.res === 'hit' && p > 1)) continue;
      const x = THROW_X - (THROW_X - (NE_PX + 30)) * p, y = neHeight(sh.h, R);
      if (x < -80) continue;
      ctx.save(); ctx.translate(Math.round(x), Math.round(y));
      if (sh.img.endsWith('con-xoay') || sh.img.endsWith('bong-go')) ctx.rotate(-now / 90);
      ctx.drawImage(im, -im.width / 2, -im.height / 2); ctx.restore();
    }
    for (const f of t.fxs) { const im = pic(f.img); if (im) centre(im, f.x, f.y); }
    for (const w of t.words) text(w.s, w.x, w.y - (now - w.t) / 25, w.s === 'PERFECT!' ? 20 : 16, w.col, 'center', true, 4);
    // hearts, count, combo
    for (let i = 0; i < NE_HEARTS; i++) centre(pic(i < t.hearts ? 'ne/tim_day' : 'ne/tim_rong'), 278 + i * 42, 26);
    text(`Học né chiêu · né được ${t.dodged}/${NE_THROWS}`, 320, 58, 15, '#fff2d8', 'center', true, 3);
    if (t.combo >= 2) text(`COMBO ${t.combo}`, 320, 80, 18, '#ffd36e', 'center', true, 4);
    text(t.end ? (t.hearts > 0 ? 'Xong bài học!' : 'Hết tim rồi!') : '↑ nhảy: đòn thấp · ← lùi: đòn giữa · ↓ cúi: đòn cao · B: thôi',
      320, 468, 13, '#f0e4ce', 'center', false, 3);
  }

  // ---------- the hooks ----------
  const evo0 = drawEvo;
  globalThis.drawEvo = function (now) {
    if (S.mode !== MODE) return evo0(now);
    if (!S.vd) S.vd = { view: 'menu', sel: 0 };
    if (!pic('tap/nen_vo-duong')) { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, 640, 480); return; }
    if (S.vd.view === 'train') drawTrain(now); else if (S.vd.view === 'ne') drawNe(now);
    else if (/^solo/.test(S.vd.view) && typeof __soloDraw === 'function') return __soloDraw(now);
    else drawMenu(now);
    if (S.toast && now - S.toastT < 1800) {                        // the demo draws toasts only on its own screens
      ctx.fillStyle = 'rgba(18,11,9,0.85)'; ctx.fillRect(140, 190, 360, 40); text(S.toast, 320, 210, 14, '#f0e4ce', 'center');
    }
  };
  const press0 = press;
  globalThis.press = function (btn) {
    const now = performance.now();
    // Võ đường on the map: our menu instead of the demo's instant training
    if (S.mode === 'map' && btn === 'A' && S.fade === 0 && PL[S.mapSel] && PL[S.mapSel].kind === 'train')
      return fadeTo(() => { S.mode = MODE; S.vd = { view: 'menu', sel: 0 }; });
    if (S.mode !== MODE) return press0(btn);
    if (S.fade > 0) return;
    const v = S.vd || (S.vd = { view: 'menu', sel: 0 });
    if (v.view === 'menu') {
      if (btn === 'LEFT') v.sel = (v.sel + 2) % 3;
      if (btn === 'RIGHT') v.sel = (v.sel + 1) % 3;
      if (btn === 'B') fadeTo(() => { S.mode = 'map'; });
      if (btn === 'A') !CARDS[v.sel].open ? toast(`${CARDS[v.sel].name}: sắp có`) : v.sel === 2 ? startNe(now)
        : v.sel === 1 ? __soloOpen() : startTraining(now);
      return;
    }
    if (/^solo/.test(v.view) && typeof __soloPress === 'function') return __soloPress(btn);
    if (v.view === 'ne') {
      if (btn === 'B' && !(v.end < 0)) return fadeTo(() => { S.vd = { view: 'menu', sel: 2 }; });
      return neDodge(btn, now);
    }
    if (btn === 'A') punch(now);
    if (btn === 'B' && !(v.end < 0)) fadeTo(() => { S.vd = { view: 'menu', sel: 0 }; });
  };
})();
