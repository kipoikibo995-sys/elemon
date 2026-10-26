// HoLua, the real game on top of MiniMon's demo page (scripts/evo_app.html, built by build_evo_app.py).
// Loaded after the page: it wraps the page's own functions and changes no line of it, so whatever the demo gains
// comes into the game with the next build (game/build_game.py). What it adds:
//   - the save: the whole game state (S) in localStorage (on the R36S a file in ports/holua-save), written every
//     20 s, after the big moments and on quitting; "Tiếp tục" on the title screen loads it
//   - real time: needs, droppings and crops run by the hour instead of by the second, everywhere in the game, and
//     keep going while it is off (made up for when it starts again, at most 72 h; a clock gone back counts as 0)
//   - growing up at the pace of THIET-KE.md mục 5 (Con ~1 ngày, Nhi 3-4 ngày, Thiếu niên 1-2 tuần, Trưởng thành
//     1-2 tháng): every stage needs more EXP, and EXP comes out of a pool that refills by the hour; no fast-forward
// The demo keeps its timers in performance.now(): here that clock is the game's own, carried over in the save
// (plus the time the game was off), so every timer the demo sets keeps its meaning across a restart.
(() => {
  const KEY = 'holua-save-1';
  // demo seconds -> real: No 0.55/s -> 6.6/h (a full belly lasts ~15 h), a dropping every 2.5-4.2 h, so a day at
  // work or school leaves the pet hungry and its room dirty, not ill
  const SPEED = 1 / 300;
  const SLEEP_PER_MS = 20 / 3600e3;          // Năng lượng asleep: +20 an hour (the demo: +8 a second)
  const FARM = 1 / 1000;                     // a crop stage per ~2 h of wet soil; watering lasts ~6 h; dies ~8 h dry
  const OFFLINE_MAX = 72 * 3600e3, OFFLINE_STEP = 60e3;
  const AUTOSAVE_MS = 20e3;
  const START = { coins: 1000 };             // a new game (the demo starts rich, to show the shop)
  // EXP a stage needs = the demo's × EXP_X; the pool refills that in HOURS (an engaged player's pace), holding 8 h
  const EXP_X = { baby: 2, child: 4, teen: 8, adult: 20, legend: 30 };
  const HOURS = { baby: 20, child: 84, teen: 250, adult: 1000, legend: 2000 };
  const POOL_HOLD = 8;
  const OUT = ['title', 'pickEgg', 'pickPet', 'egg', 'evo'];      // no pet to look after (yet), or evolving
  const RESET = { fade: 0.001, stats: null, popup: 0, popupGoal: 0, picker: 0, pickerGoal: 0, gemMode: null, walk: null,
                  toast: null, emo: null, fish: null, askedKey: null, bagKind: null, view: [] };
  const NOSAVE = new Set(['pickList', 'view']);                    // the egg pick's whole pet list (120 KB), the bag view
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
  let SAVE = null, loading = false, pending = null, newAsk = 0, savedAt = -1e9, saveKey = '', poolDry = false;
  try { const t = localStorage.getItem(KEY); if (t) { SAVE = JSON.parse(t); if (!SAVE || !SAVE.S || !SAVE.pet) SAVE = null; } }
  catch (e) { SAVE = null; }
  if (SAVE) S.titleSel = 1;
  const inGame = () => !OUT.includes(S.mode) && !loading && !!S.need;
  function save() {
    if (!inGame() || globalThis.__noSave) return;               // __noSave: the browser's "Xóa bản lưu" button
    try {
      const t = JSON.stringify({ v: 1, wall: Date.now(), clock: performance.now(), pet: { ...DATA.pet }, S },
                               function (k, v) { return this === S && NOSAVE.has(k) ? undefined : v; });
      localStorage.setItem(KEY, t);
      SAVE = JSON.parse(t);
    } catch (e) { console.log('save failed: ' + e); }
    savedAt = real();
  }
  globalThis.__quit = save;                                       // the R36S runtime, on SELECT+START
  addEventListener('pagehide', save);
  addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') save(); });

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
  const gain0 = gainExp;
  globalThis.gainExp = function (n) {
    if (!STAGE_EXP[S.stage] || S.xp >= STAGE_EXP[S.stage]) return gain0(n);
    fillPool();
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

  // ---------- buttons ----------
  const press0 = press;
  globalThis.press = function (btn) {
    if (S.mode === 'title') {
      if (loading) return;
      if ((btn === 'A' || btn === 'START') && S.fade === 0) {
        if (S.titleSel === 1) { if (SAVE) startLoad(); else toast('Chưa có bản lưu'); return; }
        if (SAVE && real() - newAsk > 3000) { newAsk = real(); toast('Bấm A lần nữa: chơi mới, xóa bản lưu cũ'); return; }
      }
      return press0(btn);
    }
    // the demo's L2 fast-forward: gone (at a stage's last level L2 still opens the evolve panel)
    if (btn === 'L2' && S.mode === 'room' && S.stats === null && S.popupGoal === 0 && S.pickerGoal === 0 && S.fade === 0 &&
        S.night <= 0.5 && !atCap() && !(S.stage === 'legend' && S.level >= LV.legend[1]))
      return toast('Không tua nhanh được: chăm mỗi ngày để lớn');
    return press0(btn);
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
    if (mode0 === 'egg' && S.mode === 'room' && !S.real) { Object.assign(S, START); S.real = true; S.pool = undefined; fillPool(); }
    mode0 = S.mode;
    const key = [S.mode, S.stage, S.level, S.house].join();
    if (inGame() && S.fade === 0 && (key !== saveKey || real() - savedAt > AUTOSAVE_MS)) { saveKey = key; save(); }
  };
})();
