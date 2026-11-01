// Elemon: the Đấu trường tree (the user, 31/10/2026), in place of Solo đối kháng's pick screens (game/src/solo.js).
// The pet being raised fights; the foes grow on the trees: one painted tree an element (img/cay/<he>.png, a candelabra
// of six branches: game/build_game.py finds them), its six pets one a branch, each pet's four stages up its branch
// (Nhi at the bough, Huyền thoại at the tip); the five trees side by side and Hư Ảnh after them, the view sliding
// from one to the next as the D-pad goes past an edge (L1/R1: a tree at once). A node shows its pet once won over:
//   - a Solo match won in Vùng đất (game/src/vung-dat.js calls __cayThang): that pet at the stage it fought as (khu 1
//     mini boss a Nhi, khu 2 a Thiếu niên, khu 3 a Trưởng thành, a region's Thần thú a Huyền thoại)
//   - a Trưởng thành beaten here, in Đấu trường: its Huyền thoại
//   - Hư Ảnh: once sealed at Đài Ngũ Hành
// Only the pets' names are written (the user: no stage or element labels). Kept in S.cay ('<dir>/<stage>': 1).
(() => {
  const SM = globalThis.__soloMatch;
  if (!SM || typeof __soloOpen !== 'function' || typeof __soloDraw !== 'function' || typeof __soloPress !== 'function') return;
  const LAY = {"frame": 66, "trees": {"hoa": {"x": [50, 157, 267, 374, 482, 590], "tip": 81, "bough": 284}, "kim": {"x": [44, 150, 257, 383, 489, 596], "tip": 73, "bough": 280}, "moc": {"x": [44, 154, 267, 372, 485, 595], "tip": 79, "bough": 276}, "thuy": {"x": [56, 163, 273, 368, 479, 585], "tip": 62, "bough": 277}, "tho": {"x": [38, 145, 256, 382, 494, 602], "tip": 82, "bough": 273}}};                                     // game/build_game.py: {frame, trees: {he: {x, tip, bough}}}
  const VIEW = 'solo-cay';                                // /^solo/: Võ đường hands it to __soloDraw / __soloPress
  const ORDER = ['hoa', 'kim', 'moc', 'thuy', 'tho'];
  // each tree's six, branch by branch (Vùng đất's foes of that region, its Thần thú in the middle)
  const PETS = { hoa: ['hoa-ho-cao', 'hoa-quy', 'viem-long', 'hoa-linh', 'dung-nham-ve', 'hoa-ho'],
                 kim: ['kim-te', 'tinh-kim-hiep', 'kim-ung', 'liem-dao', 'kim-giap', 'kim-thach-nhan'],
                 moc: ['moc-loc', 'moc-tru', 'thu-nhan', 'reu-linh', 'diep-linh', 'moc-duong'],
                 thuy: ['thuy-sa', 'thuy-giai', 'thuy-long', 'bao-thuy', 'thuy-chien', 'thuy-giao'],
                 tho: ['tho-tich', 'thach-nhan', 'tho-long', 'tho-tuong', 'thanh-tri', 'tho-nguu'] };
  const STAGES = ['child', 'teen', 'adult', 'legend'];
  const LV = { child: 14, teen: 34, adult: 60, legend: 90 }, BOT = { child: 1, teen: 2, adult: 3, legend: 3 };
  const HE_COL = { hoa: '#ff9a6a', kim: '#e4f0ff', moc: '#a8e88a', thuy: '#8ad0ff', tho: '#f0c880', hu: '#d8b8ff' };
  const SOLO_NL = 15, FR = LAY.frame || 66, PIC = Math.round(FR * 0.62);
  const sfx = (n, v) => { if (typeof SOUND === 'object' && SOUND) SOUND.sfx(n, v); };
  const roster = dir => SM.ROSTER.find(r => r.dir === dir);

  // ---------- the trees: each one a screen, its nodes ----------
  const TREES = ORDER.map((he, t) => {
    const L = (LAY.trees || {})[he] || { x: [60, 164, 268, 372, 476, 580], tip: 90, bough: 300 };
    const top = L.tip + FR / 2 - 6, step = (L.bough - top) / 3;      // Huyền thoại at the tip, Nhi on the bough
    const rows = STAGES.map((_, j) => Math.round(L.bough - j * step));
    return { he, t, x0: t * 640, rows, stems: PETS[he].map((d, i) => ({ r: roster(d), x: L.x[i] })).filter(s => s.r), bough: L.bough };
  });
  const HU = roster('hu-anh'), HU_T = ORDER.length;
  const has = () => S.cay || (S.cay = {});
  const key = (dir, st) => dir + '/' + st;
  function carryOver() {                                  // pets won over before the tree: their Nhi
    const mo = S.vung && S.vung.mo;
    if (!mo || S.cayCu) return;
    S.cayCu = 1;
    for (const d of Object.keys(mo)) if (d !== 'hu-anh') has()[key(d, 'child')] = 1;
  }
  const huOpen = () => !!(S.vung && S.vung.mo && S.vung.mo['hu-anh']) || !!has()[key('hu-anh', 'legend')];
  const isOpen = (dir, st) => dir === 'hu-anh' ? huOpen() : !!has()[key(dir, st)];
  globalThis.__cayThang = (dir, st) => {
    if (dir) has()[key(dir, STAGES.includes(st) ? st : 'child')] = 1;
  };
  const ALL = TREES.reduce((n, T) => n + T.stems.length * 4, 0) + (HU ? 1 : 0);
  const count = () => TREES.reduce((n, T) => n + T.stems.reduce((m, s) => m + STAGES.filter(st => isOpen(s.r.dir, st)).length, 0), 0) + (HU && huOpen() ? 1 : 0);

  // ---------- pictures ----------
  const PICS = {};
  function img(path) {                                    // img/<path>.png, once
    let im = PICS[path];
    if (!im) { im = PICS[path] = new Image(); im.onload = () => { im.__ok = true; }; im.src = `img/${path}.png`; }
    return im.__ok ? im : null;
  }
  function petPic(dir, st) {                              // the pet at that stage: its standing frame
    const k = 'p:' + key(dir, st);
    if (k in PICS) return PICS[k] && PICS[k].__ok ? PICS[k] : null;
    PICS[k] = null;
    petData(dir).then(j => {
      const s = j.stages[st] || j.stages.child, f = s.meta.frames.includes('idle-0') ? 'idle-0' : s.meta.frames[0];
      const im = new Image(); im.onload = () => { im.__ok = true; }; im.src = `../pets/${s.dir}/${f}.png`; PICS[k] = im;
    }).catch(() => {});
    return null;
  }

  // ---------- the cursor and the view ----------
  // c: { t (tree, HU_T = Hư Ảnh), i (branch), j (stage) }; cx the view's left edge in the world
  function open() {
    carryOver();
    const own = DATA.pet && DATA.pet.creature;
    let c = { t: 0, i: 0, j: 0 };
    TREES.forEach((T, t) => T.stems.forEach((s, i) => { if (s.r.dir === own) c = { t, i, j: 0 }; }));
    c.cx = c.t * 640;
    S.vd = { view: VIEW, sel: 1, c };
  }
  const cur = c => c.t === HU_T ? { r: HU, st: 'legend' } : { r: TREES[c.t].stems[c.i].r, st: STAGES[c.j] };

  // ---------- drawing ----------
  function drawTree(T, ox, c) {
    const bg = img('cay/' + T.he);
    if (bg) ctx.drawImage(bg, ox, 0); else { ctx.fillStyle = '#0c0a14'; ctx.fillRect(ox, 0, 640, 480); }
    T.stems.forEach((s, i) => {
      let any = false;
      STAGES.forEach((st, j) => {
        const o = isOpen(s.r.dir, st), on = c.t === T.t && c.i === i && c.j === j;
        any = any || o;
        node(s.x + ox, T.rows[j], o ? (on ? 1 : 0) : 2, o ? petPic(s.r.dir, st) : null, on);
      });
      text(any ? s.r.name : '???', s.x + ox, T.bough + FR / 2 + 10, 12, any ? HE_COL[T.he] : '#9a8a78', 'center', true, 3);
    });
  }
  function node(x, y, f, pet, on) {                       // f: the frame (0 open, 1 picked, 2 locked, 3 Hư Ảnh)
    const fr = img('cay/khung_' + f);
    if (on && f === 2) {                                  // a locked node picked: the stone frame, glowing
      ctx.strokeStyle = `rgba(255,236,170,${0.6 + 0.4 * Math.sin(performance.now() / 180)})`; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(x, y, FR / 2 + 3, 0, 7); ctx.stroke();
    }
    if (fr) ctx.drawImage(fr, Math.round(x - FR / 2), Math.round(y - FR / 2));
    else { ctx.fillStyle = '#1e140e'; ctx.beginPath(); ctx.arc(x, y, FR / 2 - 4, 0, 7); ctx.fill(); }
    if (pet) fit(pet, x, y, PIC, PIC, 0);
  }
  function drawHu(ox, c) {
    const bg = IMG.nen;
    if (bg) { ctx.drawImage(bg, ox, 0, 640, 480); ctx.fillStyle = 'rgba(20,6,30,0.55)'; ctx.fillRect(ox, 0, 640, 480); }
    const o = huOpen(), on = c.t === HU_T, x = ox + 320, y = 230;
    if (on) {
      ctx.strokeStyle = `rgba(216,184,255,${0.6 + 0.4 * Math.sin(performance.now() / 180)})`; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(x, y, FR * 0.8 + 4, 0, 7); ctx.stroke();
    }
    const fr = img('cay/khung_' + (o ? 3 : 2)), s = Math.round(FR * 1.6);
    if (fr) ctx.drawImage(fr, x - s / 2, y - s / 2, s, s);
    if (o) { const p = img('solo/hu-anh'); if (p) fit(p, x, y, s * 0.62, s * 0.62, 0); }
    text(o ? HU.name : '???', x, y + s / 2 + 18, 14, o ? HE_COL.hu : '#9a8a78', 'center', true, 3);
  }
  function draw(now) {
    const v = S.vd, c = v.c;
    c.cx += (c.t * 640 - c.cx) * 0.22;
    if (Math.abs(c.t * 640 - c.cx) < 0.5) c.cx = c.t * 640;
    const left = Math.floor(c.cx / 640);
    for (const t of [left, left + 1]) {
      const ox = Math.round(t * 640 - c.cx);
      if (ox >= 640 || ox <= -640) continue;
      if (t < HU_T) drawTree(TREES[t], ox, c); else if (t === HU_T && HU) drawHu(ox, c);
    }
    title('ĐẤU TRƯỜNG', 320, 24, 22, '#ffe6a8', 4);
    text(`${count()}/${ALL}`, 628, 24, 12, '#e0d0b8', 'right', false, 2);
    const { r, st } = cur(c), o = r && isOpen(r.dir, st);
    ctx.fillStyle = 'rgba(14,9,7,0.85)'; ctx.fillRect(0, 446, 640, 34);
    text(o ? `${r.name} · A: đấu · B: thoát` : 'Chưa mở: hạ nó ở Vùng đất · B: thoát', 320, 463, 13, '#f0e4ce', 'center', true, 2);
  }

  // ---------- buttons ----------
  function move(c, btn) {
    const last = HU ? HU_T : HU_T - 1;
    if (btn === 'L1' || btn === 'R1') {                    // a whole tree at once
      c.t = Math.max(0, Math.min(last, c.t + (btn === 'R1' ? 1 : -1)));
      c.i = btn === 'R1' ? 0 : c.t < HU_T ? TREES[c.t].stems.length - 1 : 0;
      return;
    }
    if (c.t === HU_T) { if (btn === 'LEFT') { c.t = HU_T - 1; c.i = TREES[c.t].stems.length - 1; c.j = 3; } return; }
    const n = TREES[c.t].stems.length;
    if (btn === 'UP' && c.j < 3) c.j++;
    if (btn === 'DOWN' && c.j > 0) c.j--;
    if (btn === 'LEFT') { if (c.i > 0) c.i--; else if (c.t > 0) { c.t--; c.i = TREES[c.t].stems.length - 1; } }
    if (btn === 'RIGHT') { if (c.i < n - 1) c.i++; else if (c.t < last) { c.t++; c.i = 0; } }
  }
  function fight(c) {
    const { r: foe, st } = cur(c);
    if (!foe) return;
    if (!isOpen(foe.dir, st)) { sfx('loi', 200); return toast('Chưa mở: hạ nó ở Vùng đất trước'); }
    const me = roster(DATA.pet.creature);
    if (!me) return toast(`${DATA.pet.name} chưa vào được Đấu trường`);
    const why = __chiSo.fit(SOLO_NL);
    if (why) return toast(`${DATA.pet.name} chưa đấu được: ${why}, về nghỉ đã`);
    if (globalThis.__SOLO_CUTS && foe.dir === me.dir) return toast('Chọn đối thủ khác loài với pet của bạn');
    const hu = c.t === HU_T, lv = hu ? 100 : LV[st], level = hu ? 3 : BOT[st];
    if (typeof __vgVs === 'function') __vgVs(me.dir, foe.dir, 0, 0);
    fadeTo(() => {
      S.vd = { view: 'solo', sel: 1, level, cay: { dir: foe.dir, st, t: c.t, i: c.i, j: c.j } };
      // the foe in its node's stage's body (Vùng đất's hooked arena; the one below while that stage is not cut, R36S)
      const src = !hu && typeof __vgDuelSrc === 'function' && __vgDuelSrc(), plain = globalThis.__SOLO_SRC;
      if (src) { globalThis.__vgBotStage = __soloStage(foe.dir, st); globalThis.__SOLO_SRC = src; }
      try { SM.start(me, foe, level); } finally { globalThis.__SOLO_SRC = plain; }
      globalThis.__soloPow = __chiSo.pow(lv);              // after start: the foe as strong as its stage's level
    });
  }

  // ---------- the hooks ----------
  globalThis.__soloOpen = () => fadeTo(open);
  const draw0 = __soloDraw;
  globalThis.__soloDraw = now => (S.vd && S.vd.view === VIEW ? draw(now) : draw0(now));
  const press0 = __soloPress;
  globalThis.__soloPress = btn => {
    const v = S.vd;
    if (v && v.view === VIEW) {
      if (S.fade > 0) return;
      if (['UP', 'DOWN', 'LEFT', 'RIGHT', 'L1', 'R1'].includes(btn)) { move(v.c, btn); return sfx('menu', 160); }
      if (btn === 'A') return fight(v.c);
      if (btn === 'B') { sfx('quay-lai', 180); return fadeTo(() => { S.vd = { view: 'menu', sel: 1 }; }); }
      return;
    }
    // a tree match left: a Trưởng thành beaten here opens its Huyền thoại; then back to the tree, on that node
    const cay = v && v.view === 'solo' && v.cay;
    if (cay && btn === 'SELECT') {
      const sc = globalThis.__soloSeen && __soloSeen.score, win = !!sc && sc.me > sc.bot;
      if (win && cay.st === 'adult' && !isOpen(cay.dir, 'legend')) { has()[key(cay.dir, 'legend')] = 1; setTimeout(() => toast('Mở nhánh Huyền thoại!'), 0); }
      const r = press0(btn), cb = fadeCb;
      if (!globalThis.__hu) globalThis.__vgBotStage = null;
      if (cb) fadeCb = () => { cb(); open(); Object.assign(S.vd.c, { t: cay.t, i: cay.i, j: cay.j, cx: cay.t * 640 }); };
      return r;
    }
    return press0(btn);
  };
})();
