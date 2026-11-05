// HoLua, the real game on top of MiniMon's demo page (scripts/evo_app.html, built by build_evo_app.py).
// Loaded after the page: it wraps the page's own functions and changes no line of it, so whatever the demo gains
// comes into the game with the next build (game/build_game.py). What it adds:
//   - the save: the whole game state (S) in localStorage (on the R36S a file in ports/holua-save), written every
//     20 s, after the big moments and on quitting; "Tiếp tục" on the title screen loads it
//   - several pets (the user, 31/10/2026): one save a pet, holua-save-1 .. -6; "Chơi mới" starts the next free one
//     and leaves the others as they are, "Tiếp tục" lists them (game/src/man-chao.js, through __luu)
//   - a new game starts with no gems (the demo's test bag of gems and its free Ngọc Hồn at Trưởng thành are gone):
//     gems and Ngọc Hồn come from the bosses of Vùng đất
//   - real time: needs, droppings and crops run by the hour instead of by the second, everywhere in the game, and
//     keep going while it is off (made up for when it starts again, at most 72 h; a clock gone back counts as 0)
//   - growing up at the pace of THIET-KE.md mục 5 (Con ~1 ngày, Nhi 3-4 ngày, Thiếu niên 1-2 tuần, Trưởng thành
//     1-2 tháng): every stage needs more EXP, and EXP comes out of a pool that refills by the hour; no fast-forward
// The demo keeps its timers in performance.now(): here that clock is the game's own, carried over in the save
// (plus the time the game was off), so every timer the demo sets keeps its meaning across a restart.
(() => {
  const SLOT = n => `holua-save-${n}`, SLOTS = 6, LAST = 'holua-cuoi';   // LAST: the slot played last
  let KEY = SLOT(1);
  // demo seconds -> real: No 0.55/s -> 6.6/h (a full belly lasts ~15 h), a dropping every 2.5-4.2 h, so a day at
  // work or school leaves the pet hungry and its room dirty, not ill
  const SPEED = 1 / 300;
  const SLEEP_PER_MS = 10 / 60e3;            // Năng lượng asleep: +10 a minute, full in ~10 min (was +20 an hour: the bar
                                             // did not visibly move, and a Solo match costs 8); the demo: +8 a second
  const FARM = 1 / 1000;                     // a crop stage per ~2 h of wet soil; watering lasts ~6 h; dies ~8 h dry
  const OFFLINE_MAX = 72 * 3600e3, OFFLINE_STEP = 60e3;
  const AUTOSAVE_MS = 20e3;
  const START = { coins: 1000 };             // a new game (the demo starts rich, to show the shop)
  // EXP a stage needs = the demo's × EXP_X; the pool refills that in HOURS (an engaged player's pace), holding 8 h
  const EXP_X = { baby: 2, child: 4, teen: 8, adult: 20, legend: 30 };
  const HOURS = { baby: 20, child: 84, teen: 250, adult: 1000, legend: 2000 };
  const POOL_HOLD = 8;
  const OUT = ['title', 'phim', 'pickEgg', 'pickPet', 'egg', 'evo',   // no pet to look after (yet), or evolving
               'dsPet', 'caiDat', 'thoat'];                                     // (phim: the opening film, game/src/phim.js;
                                                                       // the pet list, settings: game/src/man-chao.js)
  const RESET = { fade: 0.001, stats: null, popup: 0, popupGoal: 0, picker: 0, pickerGoal: 0, gemMode: null, walk: null,
                  toast: null, emo: null, fish: null, askedKey: null, bagKind: null, view: [] };
  const NOSAVE = new Set(['pickList', 'view', 'veChao']);   // the egg pick's whole pet list (120 KB), the bag view,
                                                                 // the open "Về màn chào?" question (man-chao.js)
  // what this layer hooks onto: if the demo has renamed any of it, the page runs as the plain demo (and says why)
  const HOOKS = ['press', 'frame', 'tickNeeds', 'gainExp', 'loadCreature', 'fadeTo', 'toast', 'act', 'drawTitle', 'text'];
  const missing = HOOKS.filter(n => typeof globalThis[n] !== 'function');
  if (typeof NEW !== 'function' || typeof STAGE_EXP !== 'object' || typeof LV !== 'object') missing.push('NEW/STAGE_EXP/LV');
  if (missing.length) { console.log('song-that.js: the demo has no ' + missing.join(', ') + ': running as the demo'); return; }

  for (const k of Object.keys(EXP_X)) if (STAGE_EXP[k]) STAGE_EXP[k] *= EXP_X[k];

  // ---------- the game clock ----------
  const real = performance.now.bind(performance);
  let off = 0;
  performance.now = () => real() + off;
  const raf0 = requestAnimationFrame.bind(globalThis);
  globalThis.requestAnimationFrame = cb => raf0(() => cb(performance.now()));

  // ---------- the save ----------
  let SAVE = null, loading = false, pending = null, savedAt = -1e9, saveKey = '', poolDry = false;
  function read(key) {
    try { const t = localStorage.getItem(key), sv = t && JSON.parse(t); return sv && sv.S && sv.pet ? sv : null; }
    catch (e) { return null; }
  }
  const slots = () => { const out = []; for (let n = 1; n <= SLOTS; n++) { const sv = read(SLOT(n)); if (sv) out.push({ n, sv }); } return out; };
  try { const k = localStorage.getItem(LAST); if (k && read(k)) KEY = k; } catch (e) {}
  SAVE = read(KEY) || (slots()[0] || {}).sv || null;
  if (SAVE && !read(KEY)) KEY = SLOT(slots()[0].n);
  if (SAVE) S.titleSel = 1;
  const inGame = () => !OUT.includes(S.mode) && !(S.mode === 'datTen' && !S.real) && !loading && !!S.need;   // (naming at the hatching)
  function save() {
    if (!inGame() || globalThis.__noSave) return;               // __noSave: the browser's "Xóa bản lưu" button
    try {
      const t = JSON.stringify({ v: 1, wall: Date.now(), clock: performance.now(), pet: { ...DATA.pet }, S },
                               function (k, v) { return this === S && NOSAVE.has(k) ? undefined : v; });
      localStorage.setItem(KEY, t);
      if (lastKey !== KEY) { localStorage.setItem(LAST, KEY); lastKey = KEY; }
      SAVE = JSON.parse(t);
    } catch (e) { console.log('save failed: ' + e); }
    savedAt = real();
  }
  globalThis.__quit = save;                                       // the R36S runtime, on SELECT+START
  addEventListener('pagehide', save);
  addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') save(); });

  let lastKey = null;
  function startLoad() {
    loading = true;
    toast('Đang mở bản lưu…');
    const sv = SAVE;
    loadCreature(sv.pet.creature).then(() => fadeTo(() => {
      Object.assign(DATA.pet, sv.pet);
      const st = { ...NEW(), ...sv.S, ...RESET };                 // fields the demo added since the save: defaults
      st.mode = 'room';
      if (st.act && !st.act.hold) st.act = null;                  // asleep stays asleep, anything else ends
      S = st;
      pending = sv;                                               // the clock moves on after this frame
    }), e => { loading = false; toast('Không mở được bản lưu'); console.log('load: ' + e); });
  }
  // time passing with nobody looking: needs, droppings, sleep, crops, in steps
  function playThrough(from, ms) {
    for (let t = 0; t < ms; t += OFFLINE_STEP) {
      const d = Math.min(OFFLINE_STEP, ms - t), now = from + t + d, asleep = S.night > 0.5;
      tickNeeds(d, now);
      if (asleep) S.need.nl = Math.min(100, S.need.nl + d * SLEEP_PER_MS);
      if (S.farm) { farmed = false; farmTick(now, d); }
    }
  }
  // the test buttons of the browser page (game/src/nut-thu.js): jump the clock ahead as if that time went by
  globalThis.__tuaGio = ms => {
    if (!inGame()) return false;
    const from = performance.now();
    off += ms;
    playThrough(from, ms);
    lastNow = null;
    save();
    return true;
  };
  // after the fade's frame: the clock catches up with the time the game was off, and that time is played through
  function arrive(sv) {
    const away = Math.max(0, Math.min(OFFLINE_MAX, Date.now() - sv.wall)), target = sv.clock + away;
    if (target > performance.now()) off += target - performance.now();
    playThrough(sv.clock, away);
    fadeStart = performance.now(); last = performance.now(); lastNow = null;
    loading = false;
    if (!S.act && has('greet')) act('greet');
    const h = Math.floor(away / 3600e3), m = Math.floor(away / 60e3) % 60;
    toast(away < 60e3 ? `Chào mừng trở lại, ${DATA.pet.name}!` : `${DATA.pet.name} ở nhà ${h ? h + ' giờ ' : ''}${m} phút`);
    save();
  }

  // ---------- EXP out of a pool that refills by the hour ----------
  const rate = () => STAGE_EXP[S.stage] / HOURS[S.stage];          // EXP an hour
  function fillPool() {
    const t = performance.now(), cap = rate() * POOL_HOLD;
    if (typeof S.pool !== 'number') { S.pool = cap; S.poolT = t; }
    S.pool = Math.min(cap, S.pool + Math.max(0, t - S.poolT) / 3600e3 * rate());
    S.poolT = t;
  }
  // the pool gets smaller stage by stage (Con ~128, Trưởng thành ~61), so a reward is the demo's amount as a share of
  // a pool of EXP_REF: a meal (25) is ~15% of the pool at every stage, not two meals and the pool dry (THIET-KE.md 6.5)
  const EXP_REF = 160;
  const gain0 = gainExp;
  globalThis.gainExp = function (n) {
    if (!STAGE_EXP[S.stage] || S.xp >= STAGE_EXP[S.stage]) return gain0(n);
    fillPool();
    n *= rate() * POOL_HOLD / EXP_REF;
    const g = Math.max(0, Math.min(n, S.pool));
    S.pool -= g;
    // said once when the pool runs dry, and again only after it has refilled a quarter (before, every 20 s it was
    // dry, over the toast of whatever was just done: petting, the farm, a punch in Võ đường...)
    if (S.pool >= rate() * POOL_HOLD * 0.25) poolDry = false;
    if (g < n && !poolDry) {                                       // after the demo's own toast of this action
      poolDry = true;
      setTimeout(() => toast(`${DATA.pet.name} học đủ rồi, nghỉ chút nhé (EXP hồi theo giờ)`), 0);
    }
    return gain0(g);
  };
  // a boss's reward, k of a level, not out of the pool (a one-off: never "EXP hôm nay đã đầy"); the EXP it gave back
  globalThis.__expThuong = k => {
    if (!STAGE_EXP[S.stage] || !LV[S.stage]) return 0;
    const [lo, hi] = LV[S.stage], xp0 = S.xp;
    gain0(STAGE_EXP[S.stage] / Math.max(1, hi - lo) * k);
    return Math.max(0, Math.round(S.xp - xp0));
  };

  // ---------- needs and droppings by the hour ----------
  let ticked = false, farmed = false, lastNow = null;
  // a timer the demo set in its own seconds (now + 30 s) becomes real time (now + 30 s / SPEED); seen once
  function stretch(o, k, now, speed) {
    const v = o[k], seen = o._seen || (o._seen = {});
    if (typeof v !== 'number' || v === seen[k]) return;
    o[k] = v > now ? now + (v - now) / speed : v;
    seen[k] = o[k];
  }
  const tick0 = tickNeeds;
  globalThis.tickNeeds = function (dt, now) {
    ticked = true;
    stretch(S, 'nextPoop', now, SPEED); stretch(S, 'nextMess', now, SPEED);
    tick0(dt * SPEED, now);
    stretch(S, 'nextPoop', now, SPEED); stretch(S, 'nextMess', now, SPEED);
  };
  if (typeof farmTick === 'function') {
    const farm0 = farmTick;
    globalThis.farmTick = function (now, dt) {
      if (farmed) return;
      farmed = true;
      for (const p of S.farm || []) stretch(p, 'wet', now, FARM);
      farm0(now, dt * FARM);
    };
  }

  // ---------- toys ----------
  // playing takes a toy (the user, 02/11/2026: "phải vô chợ mua đồ chơi thì mới chơi được, khi chơi hết thì báo vào
  // chợ mua"): Bóng đồ chơi from Chợ -> Đặc biệt is good for BALL_PLAYS games, R2 or from the bag, then it is worn out;
  // S.bongLuot is what is left of the one in play (saved with S)
  const BALL_PLAYS = 5;
  const ballAt = () => S.items.findIndex((it, i) => it.use === 'ball' && S.bag[i] > 0);
  const hasToy = () => (S.bongLuot || 0) > 0 || ballAt() >= 0;
  const BUY_TOY = 'vào Chợ → Đặc biệt mua Bóng đồ chơi';
  function noToy() {
    emote('bc_hoi'); toast(`Hết đồ chơi rồi: ${BUY_TOY}`);
    if (typeof __noi === 'function') __noi('het_do_choi');
  }
  function played() {                                             // after a game: the ball wears
    if (!((S.bongLuot || 0) > 0)) { const i = ballAt(); if (i < 0) return; consume(i); S.bongLuot = BALL_PLAYS; }
    S.bongLuot--;
    if (S.bongLuot > 0) { if (S.bongLuot <= 2) toast(`Bóng còn chơi được ${S.bongLuot} lần`); }
    else if (ballAt() < 0) toast(`Bóng hỏng rồi! Muốn chơi tiếp thì ${BUY_TOY}`);
    else toast('Bóng hỏng rồi, lấy quả mới trong túi');
  }
  const useItem0 = useItem;
  globalThis.useItem = function (i) {                             // the ball from the bag: one game, as R2
    const it = S.items[i];
    if (!it || it.use !== 'ball' || S.sick) return useItem0.apply(this, arguments);
    const r = useItem0.apply(this, arguments);
    played();
    return r;
  };
  // the drink, the candy and the ball are used, not eaten: the bag's Dùng opens the care bag (thuốc, xà phòng), so
  // they are listed there too; before, Dùng on Nước tăng lực opened a bag without it and A swept the floor (the
  // user, 03/11/2026: "uống nước nhưng không tăng năng lượng")
  if (typeof CARE !== 'undefined') for (const u of ['energy', 'candy', 'ball']) if (!CARE.includes(u)) CARE.push(u);
  // the last one of a food eaten leaves S.items, but the closing bag still drew it from S.view (a script error a
  // frame, inline-2.js 'b.file'): the list is made again from what is left
  const pressBag = press;
  globalThis.press = function (btn) {
    const n0 = S.items ? S.items.length : 0, r = pressBag.apply(this, arguments);
    if (S.items && S.items.length !== n0 && Array.isArray(S.view) && typeof CARE !== 'undefined') {
      const pick = S.pick;
      S.view = S.items.map((b, i) => i).filter(i => CARE.includes(S.items[i].use) === (S.bagKind === 'care'));
      if (S.bagKind === 'care' && typeof SWEEP !== 'undefined') S.view.unshift(SWEEP);
      S.pick = Math.max(0, Math.min(pick, S.view.length - 1));
    }
    return r;
  };

  // fishing: the reel is held and let go for 5-10 s a fish, and only A did it, which wore A out (the user, 06/11/2026:
  // "dễ bị liệt nút quá"): ▲, R1 and R2 held reel the same as A; the line under the bar says so
  if (typeof drawFish === 'function' && typeof HELD === 'object' && HELD) {
    const REEL = ['UP', 'R1', 'R2'], REEL_LINE = 'Giữ A, ▲ hoặc R1/R2 để kéo vùng xanh theo cá';
    const drawFish0 = drawFish;
    globalThis.drawFish = function () {
      if (!S.fish || S.fish.st !== 'reel') return drawFish0.apply(this, arguments);
      const a0 = HELD.A, text0 = text;
      HELD.A = !!a0 || REEL.some(b => HELD[b]);
      globalThis.text = function (s, ...rest) { return text0.call(this, s === 'Giữ A để kéo vùng xanh theo cá' ? REEL_LINE : s, ...rest); };
      try { return drawFish0.apply(this, arguments); } finally { HELD.A = a0; globalThis.text = text0; }
    };
  }

  // ---------- buttons ----------
  const press0 = press;
  globalThis.press = function (btn) {
    // R2 in the room plays only with a toy; a game played wears the ball
    if (btn === 'R2' && S.mode === 'room' && S.stats === null && S.popupGoal === 0 && S.pickerGoal === 0 && S.fade === 0 &&
        S.night <= 0.5 && !(S.truyen && S.truyen.dang)) {
      if (!S.sick && S.need && S.need.nl >= 10 && !hasToy()) return noToy();
      const t0 = S.playedT, r = press0(btn);
      if (S.playedT !== t0) played();
      return r;
    }
    if (S.mode === 'title') {
      if (loading) return;
      if ((btn === 'A' || btn === 'START') && S.fade === 0) {
        if (S.titleSel === 1) { if (SAVE) startLoad(); else toast('Chưa có bản lưu'); return; }
        if (S.titleSel === 0) {                                     // a new pet in the next free slot
          const free = freeSlot();
          if (!free) return toast(`Đã nuôi đủ ${SLOTS} pet: vào Tiếp tục xóa bớt`);
          KEY = free; SAVE = null;
        }
      }
      return press0(btn);
    }
    // the demo's free Ngọc Hồn on reaching Trưởng thành: taken back (it drops from the bosses now)
    if (S.mode === 'evo' && S.waitA && btn === 'A' && S.fade === 0 && S.evoTo === 'adult') {
      const n0 = S.ngoc || 0, r = press0(btn), cb = fadeCb;
      if (cb) fadeCb = () => { const v = cb(); if ((S.ngoc || 0) > n0) { S.ngoc = n0; toast('Tiến hóa xong: +1000 vàng'); } return v; };
      return r;
    }
    // the demo's L2 fast-forward: gone (at a stage's last level L2 still opens the evolve panel)
    if (btn === 'L2' && S.mode === 'room' && S.stats === null && S.popupGoal === 0 && S.pickerGoal === 0 && S.fade === 0 &&
        S.night <= 0.5 && !atCap() && !(S.stage === 'legend' && S.level >= LV.legend[1]))
      return toast('Không tua nhanh được: chăm mỗi ngày để lớn');
    return press0(btn);
  };

  // ---------- the saves, for the title screen's pet list (game/src/man-chao.js) ----------
  function freeSlot() { for (let n = 1; n <= SLOTS; n++) if (!read(SLOT(n))) return SLOT(n); return null; }
  globalThis.__luu = {
    max: SLOTS,
    list: slots,                                                   // [{ n, sv }]
    open(n) { const sv = read(SLOT(n)); if (!sv || loading) return false; KEY = SLOT(n); SAVE = sv; startLoad(); return true; },
    remove(n) {
      try { localStorage.removeItem(SLOT(n)); } catch (e) {}
      if (KEY === SLOT(n)) { const f = slots()[0]; KEY = f ? SLOT(f.n) : SLOT(1); SAVE = f ? f.sv : null; }
    },
    any: () => !!SAVE,
  };

  // ---------- the title screen: "Tiếp tục" is open when there is a save ----------
  const title0 = drawTitle, text0 = text, UNGREY = { '#8aa088': '#2f6a2a', '#b8b0a8': '#fff2d8' };
  globalThis.drawTitle = function (now) {
    if (!SAVE) return title0(now);
    const lock = IMG['nut-menu_khoa'];
    IMG['nut-menu_khoa'] = IMG[S.titleSel === 1 ? 'nut-menu_chon' : 'nut-menu_thuong'] || lock;
    globalThis.text = function (s, x, y, size, color, ...rest) {
      return text0(s, x, y, size, s === 'Tiếp tục' ? UNGREY[color] || color : color, ...rest);
    };
    try { title0(now); } finally { globalThis.text = text0; IMG['nut-menu_khoa'] = lock; }
  };

  // ---------- the room: an item only goes in front of the pet when it stands clearly nearer than the pet's feet ----
  // (the demo puts every item with its foot below FEET_Y in front: a food bowl 5 px lower, right on the pet's path,
  // was drawn over its legs)
  const LAYER_SLACK = 8;
  if (typeof drawDecor === 'function' && typeof FEET_Y === 'number')
    globalThis.drawDecor = function (front) {
      const h = HOME();
      for (const d of h.items) if (isPlaced(h, d.id) && (d.floor > FEET_Y + LAYER_SLACK) === front) ctx.drawImage(IMG[d.img], d.x, d.y);
    };

  // ---------- the world map: every region open (the user, 25/10; their fights come with the combat rules) ----------
  const REGIONS = typeof PL !== 'undefined' ? PL.filter(p => p.kind === 'region').map(p => p.key) : [];
  const openRegions = () => { if (S.open) for (const k of REGIONS) S.open[k] = true; };

  // ---------- every frame ----------
  const frame0 = frame;
  let mode0 = S.mode, failed = '';
  globalThis.frame = function (now) {
    const dt = lastNow === null ? 0 : Math.min(50, Math.max(0, now - lastNow));
    lastNow = now; ticked = false; farmed = false;
    const asleep = S.night > 0.5, nl = S.need ? S.need.nl : 0;
    openRegions();
    if (!S.real && ['pickEgg', 'pickPet', 'egg'].includes(S.mode)) S.coins = START.coins;   // shown while picking
    // a slip in one frame of the demo must not freeze the game: the next frame is asked for again (logged once)
    try { frame0(now); }
    catch (e) {
      if (String(e) !== failed) { failed = String(e); console.log('frame: ' + (e && e.stack || e)); }
      requestAnimationFrame(globalThis.frame);
    }
    if (pending) { const sv = pending; pending = null; arrive(sv); }
    else if (inGame()) {
      if (!ticked) tickNeeds(dt, now);                            // the demo ticks only in the room
      if (!farmed && S.farm) farmTick(now, dt);                   // and its crops only grow while looked at
      if (asleep && S.night > 0.5) S.need.nl = Math.min(100, nl + dt * SLEEP_PER_MS);
    }
    // a new game: the real starting purse once the egg has hatched
    if ((mode0 === 'egg' || mode0 === 'datTen') && S.mode === 'room' && !S.real) {   // (datTen: named at the hatching)
      Object.assign(S, START); S.real = true; S.pool = undefined; fillPool();
      S.gemBag = {}; S.ngoc = 0;                                   // no gems: they drop from the bosses
      if (Array.isArray(S.gems)) S.gems = S.gems.map(() => null);
    }
    mode0 = S.mode;
    const key = [S.mode, S.stage, S.level, S.house].join();
    if (inGame() && S.fade === 0 && (key !== saveKey || real() - savedAt > AUTOSAVE_MS)) { saveKey = key; save(); }
  };
})();
