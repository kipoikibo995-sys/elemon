// Solo đối kháng (Võ đường's middle card): the combat session's arena, preview/dau-truong/index.html, with its balanced
// rules as they are (skills tier 1, traits and combos, the aim funnel, ring, arenas, HUD, sounds, the bot brain). The
// arena script is wrapped at build time (game/build_game.py -> js/solo-arena.js: globalThis.__SOLO_SRC) so it runs in
// its own scope on its own canvas, reading its pictures and sounds from ../solo/ (a junction to preview/dau-truong).
// This file adds the pick screen (the 15 Lv2 pets, the opponent, the bot level), feeds the R36S buttons in as the
// arena's keys and draws its canvas on the screen.
//   ◀▶▲▼ move · A J (basic) · B K · X L · Y I (ultimate) · R1/L1 dash · START rematch · SELECT leave
// Handover: side-session-notes/.../BAN-GIAO_solo-doi-khang_lv2-bac1.md. More pets / skill tiers: add to ROSTER.
(() => {
  if (typeof __SOLO_SRC !== 'function') return;
  const BASE = '../solo/';
  // every pet the arena has (skill tier 1), grouped by element: the arena's URL name for it (its PET / VS_PET
  // tests), its picture folder, its name, element
  const ROSTER = [
    ['hoa', 'hoa-ho', 'Hỏa Hổ', 'hoa'], ['quy', 'hoa-quy', 'Hỏa Quy', 'hoa'], ['cao', 'hoa-ho-cao', 'Hỏa Hồ', 'hoa'],
    ['viem', 'viem-long', 'Viêm Long', 'hoa'], ['dung', 'dung-nham-ve', 'Dung Nham Vệ', 'hoa'], ['linh', 'hoa-linh', 'Hỏa Linh', 'hoa'],
    ['kim', 'tinh-kim-hiep', 'Tinh Kim Hiệp', 'kim'], ['kimte', 'kim-te', 'Kim Tê', 'kim'], ['kimgiap', 'kim-giap', 'Kim Giáp', 'kim'],
    ['kimung', 'kim-ung', 'Kim Ưng', 'kim'], ['kimthach', 'kim-thach-nhan', 'Kim Thạch Nhân', 'kim'], ['liemdao', 'liem-dao', 'Liêm Đao', 'kim'],
    ['moc', 'moc-hung', 'Mộc Hùng', 'moc'], ['duong', 'moc-duong', 'Mộc Đường', 'moc'], ['reu', 'reu-linh', 'Rêu Linh', 'moc'],
    ['tru', 'moc-tru', 'Mộc Trư', 'moc'], ['loc', 'moc-loc', 'Mộc Lộc', 'moc'], ['nhan', 'thu-nhan', 'Thụ Nhân', 'moc'],
    ['diep', 'diep-linh', 'Diệp Linh', 'moc'],
    ['thuy', 'thuy-long', 'Thủy Long', 'thuy'], ['sa', 'thuy-sa', 'Thủy Sa', 'thuy'], ['giai', 'thuy-giai', 'Thủy Giải', 'thuy'],
    ['chien', 'thuy-chien', 'Thủy Chiến', 'thuy'], ['bao', 'bao-thuy', 'Bão Thủy', 'thuy'], ['giao', 'thuy-giao', 'Thủy Giao', 'thuy'],
    ['tho', 'tho-nguu', 'Thổ Ngưu', 'tho'], ['tuong', 'tho-tuong', 'Thổ Tượng', 'tho'], ['tich', 'tho-tich', 'Thổ Tích', 'tho'],
    ['thach', 'thach-nhan', 'Thạch Nhân', 'tho'], ['thanh', 'thanh-tri', 'Thành Trì', 'tho'], ['tholong', 'tho-long', 'Thổ Long', 'tho'],
    // Hư Ảnh, the last boss: a foe only (not a pet to play), once sealed at Đài Ngũ Hành; game/src/vung-dat.js runs it
    ['huanh', 'hu-anh', 'Hư Ảnh', 'hu'],
  ].map(([p, dir, name, he]) => ({ p, dir, name, he }));
  const BOSS = 'hu';                                     // its "element": a tab of its own, at the foe's pick only
  const VS_MIN_MS = 1200;                                // the VS screen's least time on screen
  const SOLO_NL = 15;                                   // the energy a match needs (a match then costs 8)
  const LEVEL_NAMES = ['Tập', 'Dễ', 'Vừa', 'Khó'];
  const KEY = { UP: 'ArrowUp', DOWN: 'ArrowDown', LEFT: 'ArrowLeft', RIGHT: 'ArrowRight', A: 'j', B: 'k', X: 'l', Y: 'i',
                R1: 'Shift', L1: 'Shift', START: 'Enter' };
  // the pick screen: one element at a time (UP/DOWN), its pets in a row (LEFT/RIGHT)
  const HES = [...new Set(ROSTER.map(r => r.he))];
  const GROUP = he => ROSTER.map((r, i) => i).filter(i => ROSTER[i].he === he);
  const tabsOf = step => step === 0 ? HES.filter(h => h !== BOSS) : HES;          // the boss's tab: the foe's pick only
  const LX = 20, LW = 300, GCOLS = 4, CELL = LW / GCOLS, GY = 112;                   // left: elements, pets
  const RX = 340, RW = 280;                                                          // right: the one picked
  const HE_COL = { hoa: '#ff7a4a', kim: '#cfe6ff', moc: '#8fdc6a', thuy: '#6ac0ff', tho: '#e0b060', hu: '#c8a0ff' };
  const heName = he => he === BOSS ? 'Hư' : HE_NAME[he] || he;
  const IM = {};
  for (const r of ROSTER) { const i = new Image(); i.onload = () => { IM[r.dir] = i; }; i.src = `img/solo/${r.dir}.png`; }
  const SIDE = {};                                    // side-on standing frames (game/build_game.py), loaded when first shown
  const sideOf = dir => SIDE[dir] || (SIDE[dir] = [0, 1, 2, 3].map(k => { const i = new Image(); i.src = `img/solo/${dir}_e${k}.png`; return i; }));

  // R36S: no WebAudio there. The arena's sounds as names for the game's mixer (scripts/solo_r36s.py made the WAVs):
  // sfx/<x>.ogg -> SOUND.sfx('solo/<x>'), sfx/pet/<x>.ogg -> 'solo/pet/<x>', the battle music -> SOUND.music('solo-...');
  // gains along a sound's path set its volume; the lasting-effect loops stay silent there
  function soundOf(u) {
    const n = u.replace(/^sfx\//, '').replace(/\.ogg$/, '');
    return /^chien-dau/.test(n) ? { music: 'solo-' + n } : { sfx: 'solo/' + n };
  }
  function DeviceAudio() {
    const node = () => ({ gain: { value: 1, setTargetAtTime() {} }, threshold: {}, ratio: {}, attack: {}, release: {},
                          connect(n) { this.next = n; return n; } });
    return {
      state: 'running', currentTime: 0, destination: {}, resume() {}, close() {},
      createGain: node, createDynamicsCompressor: node,
      decodeAudioData: b => { if (b && b.sfx) preSounds.push(b.sfx); return Promise.resolve(b); },
      createBufferSource() {
        return { buffer: null, loop: false, onended: null, connect(n) { this.next = n; return n; }, stop() {},
          start() {
            const b = this.buffer;
            if (!b || this.loop || typeof SOUND !== 'object' || !SOUND) return;
            if (b.music) return SOUND.music(b.music);
            let g = 1;
            for (let n = this.next; n; n = n.next) if (n.gain) g *= n.gain.value;
            SOUND.sfx(b.sfx, Math.max(0, Math.min(256, Math.round(170 * g))));
          } };
      },
    };
  }

  // R36S: what is read from the card while the VS screen shows: the two fighters' frames (img/<their dir>/...) and
  // every sound the arena decodes. Read at their first use instead, a skill's first cast stalled the match for
  // 50-150 ms (its pose, its effects, its sound off the card in the middle of the fight)
  let preSounds = [];
  const PRELOAD_MS = 30;                                          // a VS-screen frame's share of the reading
  let arena = null;                                               // the running match
  // the arena's script with the game's numbers hooked in (game/src/chi-so.js: start HP, power ratio, x0.75), made the
  // first time; Vùng đất hands in a copy hooked its own way (and with these) while its matches start
  const RAW = globalThis.__SOLO_SRC;
  let STAT_SRC = null;
  function statSrc() {
    if (STAT_SRC !== null) return STAT_SRC;
    STAT_SRC = RAW;
    if (typeof RAW === 'function' && typeof __chiSoSrc === 'function')
      try { STAT_SRC = (0, eval)('(' + __chiSoSrc(bodySrc(String(RAW))) + ')'); } catch (e) { console.log('solo: hooked arena: ' + e); STAT_SRC = RAW; }
    return STAT_SRC;
  }
  // the pet's body by its stage (the arena itself knows Nhi and, with &teen, Thiếu niên): Trưởng thành and Huyền thoại
  // have their own folders too, img/<pet>/adult/ and legend/ (scripts/lam_lv3.py arena); __soloMeStage, set by start()
  const BODY_HOOKS = [
    ["const PET_STAGE = PET && /teen/.test(location.search) ? 'teen' : 'child';",
     "const PET_STAGE = PET && globalThis.__soloMeStage ? __soloMeStage : PET && /teen/.test(location.search) ? 'teen' : 'child';"],
    ["    const body = PET_STAGE === 'teen' ? dir + 'teen/' : dir;",
     "    const body = PET_STAGE !== 'child' ? dir + PET_STAGE + '/' : dir;"],
    // a Huyền thoại fights with its Lv5 skill sheets (<fx>_lv5.png, scripts/chep_lv5.py), the level-2 one standing in
    // for a sheet not drawn; the Lv5 sheets have no in-between frames, so none (the level-2 ones would not match)
    ["    const L2 = async (n, c, r) => { try { return [n, cut(await may(dir + n + '_lv2.png'), c, r)]; } catch (e) { return null; } };",
     "    const L2 = async (n, c, r) => { const lv5 = PET_STAGE === 'legend'; if (lv5 && /_mid$/.test(n)) return null;" +
     " for (const t of lv5 ? ['_lv5', '_lv2'] : ['_lv2']) { try { return [n, cut(await may(dir + n + t + '.png'), c, r)]; } catch (e) {} } return null; };"],
    // a Huyền thoại running: its own drawn 8-frame run cycle for a direction when there is one (<dir>_chay8.png, 4x2:
    // scripts/ghep_chay8.py), RUN8_MS a frame; else its run row, whose 4th cell is a dash pose (speed lines), stepped
    // 1-2-3-2 (WALK5_MS a frame) with the body rising a little mid-step (__walkBob); the other stages' run rows are
    // real strides, as before
    ["    W.cutin = cut(await load(body + 'cutin.png'), 1, 1)[0];",
     "    W.cutin = cut(await load(body + 'cutin.png'), 1, 1)[0];\n" +
     "    if (PET_STAGE === 'legend') await Promise.all(['s', 'se', 'e', 'ne', 'n'].map(async n => { try { W[n + '_chay8'] = cut(await new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = no; i.src = body + n + '_chay8.png'; }), 4, 2); } catch (e) {} }));"],
    ["  if (moving) return [rows[4 + Math.floor(now / 100) % 4], flip];",
     "  if (moving) { const r8 = sh[sheet + '_chay8']; if (r8 && r8.length >= 8) return [r8[Math.floor(now / __RUN8_MS) % 8], flip];" +
     " return [rows[4 + (globalThis.__walkLv5 && __walkLv5(f, PET_STAGE) ? [0, 1, 2, 1][Math.floor(now / __WALK5_MS) % 4] : Math.floor(now / 100) % 4)], flip]; }"],
    ["drawOutlined(now - f.hurtT < FLASH_MS ? white(cell) : body, f.x, f.y - (f.z || 0), flip",
     "drawOutlined(now - f.hurtT < FLASH_MS ? white(cell) : body, f.x, f.y - (f.z || 0) - (globalThis.__walkBob && !sheetOf(f)[SHEET_OF[f.dir][0] + '_chay8'] ? __walkBob(f, now, PET_STAGE) : 0), flip"],
  ];
  const WALK5_MS = 120, WALK5_BOB = 2, RUN8_MS = 90;                 // ms a step frame; px the body rises mid-step; ms a drawn run frame
  globalThis.__WALK5_MS = WALK5_MS;
  globalThis.__RUN8_MS = RUN8_MS;
  // a Huyền thoại fighter (the player's at that stage, or Vùng đất's foe of it)
  globalThis.__walkLv5 = (f, petStage) => f.bot ? globalThis.__vgBotStage === 'legend' : petStage === 'legend';
  globalThis.__walkBob = (f, now, petStage) => {
    if (!(f.mx || f.my) || f.act === 'dash' || f.z || !__walkLv5(f, petStage)) return 0;
    const t = (now % (4 * WALK5_MS)) / (2 * WALK5_MS);                 // two steps a cycle: 0 and 1 at the contacts
    return Math.round(WALK5_BOB * Math.abs(Math.sin(Math.PI * t)));
  };
  function bodySrc(src) {
    for (const [a] of BODY_HOOKS) if (!src.includes(a)) { console.log('solo: the arena has changed, no body hook at: ' + a.slice(0, 50)); return src; }
    for (const [a, b] of BODY_HOOKS) src = src.replace(a, b);
    return src;
  }
  globalThis.__soloBodySrc = bodySrc;                              // Vùng đất's hooked copy takes these too
  // a stage's body, or the one below it while that is missing: on the R36S only the sheets cut ahead are there
  // (scripts/solo_r36s.py); in a browser every stage drawn is in the arena's folders
  const STAGES = ['child', 'teen', 'adult', 'legend'];
  globalThis.__soloStage = (dir, stage) => {
    const cuts = globalThis.__SOLO_CUTS;
    let i = Math.max(0, STAGES.indexOf(stage));
    while (i > 0 && cuts && !cuts[`img/${dir}/${STAGES[i]}/s.png`]) i--;
    return STAGES[i];
  };
  // opt (Đấu qua wifi, game/src/dau-wifi.js): meStage the left fighter's body, san the arena's ground (&san=), drive(arena)
  // runs the match's frames instead of the buttons and the clock here (two handhelds stepping it in lockstep)
  function start(me, foe, level, opt = {}) {
    const AC = globalThis.AudioContext || globalThis.webkitAudioContext;
    // R36S: the arena draws straight onto the screen (a second context on surface 0, its own state), saving a
    // 640x480 copy a frame; in a browser it has a canvas of its own, copied over
    const direct = !!globalThis.__SOLO_CUTS && typeof HTMLCanvasElement === 'function' && typeof __cv === 'object';
    const cv = direct ? new HTMLCanvasElement(0, 640, 480) : document.createElement('canvas');
    if (!direct) { cv.width = 640; cv.height = 480; }
    const keyFns = { keydown: [], keyup: [] }, rafs = [], ctxs = [];
    const fix = src => /^(https?:|blob:|data:|\.\.\/|\/)/.test(src) ? src : BASE + src;
    const desc = typeof HTMLImageElement !== 'undefined' && Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src');
    const load = { asked: 0, done: 0 }, owned = direct ? [] : [cv];  // its canvases and pictures (freed after, R36S)
    const CUTS = globalThis.__SOLO_CUTS, CK = globalThis.__SOLO_K || 1;
    const mine = new RegExp(`^img/(${me.dir}|${foe.dir})/`), preload = [];
    preSounds = [];
    const setSrc = desc ? desc.set : null;
    function Img() {                                              // its pictures, from its own folder
      const i = new Image(), set = setSrc || Object.getOwnPropertyDescriptor(Object.getPrototypeOf(i), 'src').set;
      load.asked++; owned.push(i);
      Object.defineProperty(i, 'src', {
        set(v) {
          const done = i.onload;
          i.onload = () => { load.done++; if (done) done.call(i); };
          if (!CUTS || !CUTS[v]) return set.call(i, fix(v));
          // R36S: a sheet cut ahead of time (scripts/solo_r36s.py): its frames, stored at 1/CK of their size; the
          // arena's cut() hands these back (its first line, see game/build_game.py). A frame is read from the card
          // the first time it is drawn, not before the match: most of a kit's frames are never needed in a round
          const base = 'cut/' + v.replace(/\.png$/, ''), meta = CUTS[v];
          i.__cells = meta.map(([w, h, ax, ay], n) => {
            const cell = { w, h, ax, ay };
            let f = null;
            Object.defineProperty(cell, 'c', {
              enumerable: true,
              get() {
                if (!f) {
                  f = new Image(); owned.push(f);
                  const r = __cv.loadImage(__file(fix(`${base}/${n}.png`)).replace(/\.png$/, '.hli'));
                  if (r) f.__id = r[0];
                  f.width = w; f.height = h; f.__k = CK; f.complete = true;
                }
                return f;
              },
              set(x) { f = x; },
            });
            if (mine.test(v)) preload.push(cell);
            return cell;
          });
          Promise.resolve().then(() => i.onload && i.onload());
        },
        get() { return desc ? desc.get.call(i) : i._src; },
      });
      return i;
    }
    const win = { AudioContext: AC ? function () { const a = new AC(); ctxs.push(a); return a; } : DeviceAudio };
    const blank = { innerHTML: '', style: {}, classList: { add() {} }, appendChild() {}, insertBefore() {}, querySelector: () => blank };
    const doc = { getElementById: id => id === 'c' ? cv : blank, body: blank, title: '',
                  createElement: t => { const e = document.createElement(t); owned.push(e); return e; } };
    const search = `?${me.p}&vs=${foe.p}&bot=${level}${opt.san ? '&san=' + opt.san : ''}`;
    // the pet being raised fights in its own stage's body (a Con as a Nhi: no arena body for it)
    const own = DATA.pet && me.dir === DATA.pet.creature;
    globalThis.__soloMeStage = __soloStage(me.dir, opt.meStage || (own ? String(S.stage || 'child').replace(/4$/, '').replace('baby', 'child') : 'child'));
    // Hư Ảnh in Võ đường: the arena with its own hooks (game/src/vung-dat.js; Vùng đất hands in its own copy instead)
    const hu = foe.dir === 'hu-anh' && globalThis.__SOLO_SRC === RAW && typeof __vgHuDuel === 'function' && __vgHuDuel();
    const run = hu || (globalThis.__SOLO_SRC === RAW ? statSrc() : globalThis.__SOLO_SRC);
    run(doc, win, { search }, (type, fn) => { if (keyFns[type]) keyFns[type].push(fn); }, fn => { rafs.push(fn); },
               (u, o) => !AC && /\.ogg$/.test(u) ? Promise.resolve({ arrayBuffer: () => Promise.resolve(soundOf(u)) }) : fetch(fix(u), o),
               Img);
    arena = { cv, keyFns, rafs, ctxs, held: {}, me, foe, level, t0: performance.now(), load, started: false, owned, preload, preTotal: 0,
              lost: 0, lastP: null, lastHp: 0, drive: opt.drive || null };
    console.log(`solo: ${me.dir} vs ${foe.dir}, bot ${level}`);                  // log.txt on the R36S: where the fps lines are
    const fire = k => { for (const fn of keyFns.keydown) fn({ key: k, preventDefault() {} }); };
    fire('F1'); arena.keyFns.keyup.forEach(fn => fn({ key: 'F1', preventDefault() {} }));   // a "key" that does nothing: wakes its sound
    if (typeof SOUND === 'object' && SOUND) SOUND.music('');      // the arena plays its own battle music
  }
  function stop() {
    if (!arena) return;
    console.log('solo: end');
    for (const a of arena.ctxs) try { a.close(); } catch (e) {}
    if (typeof __cv === 'object' && __cv.free) for (const o of arena.owned) if (o.__id !== undefined) __cv.free(o.__id);   // R36S
    if (typeof __vgVsDrop === 'function') __vgVsDrop(arena.me.dir, arena.foe.dir);
    if (typeof __vgHuDone === 'function') __vgHuDone();       // a match with Hư Ảnh: its hooks put away
    arena = null;
    if (typeof SOUND === 'object' && SOUND) SOUND.music('ngay');
  }
  function feedKeys() {                                           // R36S buttons held -> the arena's keys down / up
    const ev = (type, k) => { for (const fn of arena.keyFns[type]) fn({ key: k, preventDefault() {} }); };
    for (const [btn, k] of Object.entries(KEY)) {
      const on = !!HELD[btn];
      if (on !== !!arena.held[btn]) { arena.held[btn] = on; ev(on ? 'keydown' : 'keyup', k); }
    }
  }

  // ---------- the pick screen ----------
  // the pick screen's still parts (the dimmed dusk backdrop, the right-hand box) made once: on the R36S, where every
  // pixel is the CPU's, redrawing them each frame cost more than the rest of the screen. Sealed there, it is copied
  let pickBack = null, loadBack = null;
  // a menu backdrop (640x436) scaled once to cover the whole 640x480 screen, its sides cut evenly: the R36S shows
  // no bare strips above and below it
  function cover(g, im) {
    const k = Math.max(640 / im.width, 480 / im.height), w = Math.round(im.width * k), h = Math.round(im.height * k);
    g.drawImage(im, Math.round((640 - w) / 2), Math.round((480 - h) / 2), w, h);
  }
  function backdrop() {
    if (pickBack) return pickBack;
    if (!IMG['nen-menu_hoang-hon']) return null;
    const c = document.createElement('canvas'); c.width = 640; c.height = 480;
    const g = c.getContext('2d');
    g.fillStyle = '#1a120c'; g.fillRect(0, 0, 640, 480);
    cover(g, IMG['nen-menu_hoang-hon']);
    g.fillStyle = 'rgba(16,10,6,0.55)'; g.fillRect(0, 0, 640, 480);
    g.fillStyle = 'rgba(0,0,0,0.30)'; g.fillRect(RX, 76, RW, 300);
    g.strokeStyle = 'rgba(255,214,110,0.45)'; g.lineWidth = 2; g.strokeRect(RX, 76, RW, 300);
    if (typeof __cv === 'object' && __cv.seal) __cv.seal(c.__id);
    return (pickBack = c);
  }
  // the small pictures at the size they are shown, made once each
  const THUMB = {};
  function thumb(dir) {
    if (THUMB[dir]) return THUMB[dir];
    const im = IM[dir];
    if (!im) return null;
    const k = Math.min(1, (CELL - 16) / Math.max(im.width, im.height));
    if (k === 1) return (THUMB[dir] = im);
    const c = document.createElement('canvas'); c.width = Math.round(im.width * k); c.height = Math.round(im.height * k);
    c.getContext('2d').drawImage(im, 0, 0, c.width, c.height);
    return (THUMB[dir] = c);
  }
  // a foe is open once won over in a Solo match in Vùng đất (game/src/vung-dat.js; without it every foe is open)
  const foeOpen = dir => typeof __vgMo !== 'function' || __vgMo(dir);

  function drawPick(now) {
    const v = S.vd, r = ROSTER[v.cur], back = backdrop();
    if (back) ctx.drawImage(back, 0, 0);
    else { ctx.fillStyle = '#1a120c'; ctx.fillRect(0, 0, 640, 480); }
    title(v.step === 0 ? 'CHỌN PET CỦA BẠN' : 'CHỌN ĐỐI THỦ', 320, 36, 22, '#ffe6a8', 4);
    text(`Solo đối kháng · ${ROSTER.filter(q => q.he !== BOSS).length} pet · bộ chiêu 1`, 320, 60, 13, '#e0cfb0', 'center', false, 3);
    // left: the elements, the shown one lit up; under them its pets, small
    const tabs = tabsOf(v.step), TW = LW / tabs.length;
    tabs.forEach((he, k) => {
      const x = LX + k * TW, on = he === r.he;
      ctx.fillStyle = on ? 'rgba(255,214,110,0.30)' : 'rgba(0,0,0,0.40)'; ctx.fillRect(x + 2, 76, TW - 4, 28);
      if (on) { ctx.strokeStyle = HE_COL[he] || '#ffd36e'; ctx.lineWidth = 2; ctx.strokeRect(x + 2, 76, TW - 4, 28); }
      text(heName(he), x + TW / 2, 95, 13, on ? HE_COL[he] || '#ffe6a8' : '#b8a888', 'center', true, 2);
    });
    GROUP(r.he).forEach((i, k) => {
      const q = ROSTER[i], x = LX + (k % GCOLS) * CELL, y = GY + Math.floor(k / GCOLS) * CELL;
      const on = i === v.cur, mine = v.step === 1 && i === v.me;
      ctx.fillStyle = on ? 'rgba(255,214,110,0.35)' : mine ? 'rgba(120,200,255,0.28)' : 'rgba(0,0,0,0.40)';
      ctx.fillRect(x + 3, y + 3, CELL - 6, CELL - 6);
      if (on) { ctx.strokeStyle = '#ffd36e'; ctx.lineWidth = 3; ctx.strokeRect(x + 3, y + 3, CELL - 6, CELL - 6); }
      const im = thumb(q.dir);
      if (im) ctx.drawImage(im, Math.round(x + CELL / 2 - im.width / 2), Math.round(y + CELL / 2 - im.height / 2 - 6));
      text(q.name, x + CELL / 2, y + CELL - 9, 9, on ? '#ffe6a8' : '#d8c8a8', 'center', true, 2);
      if (v.step === 1 && !foeOpen(q.dir)) {                     // not won over yet: dimmed, locked
        ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(x + 3, y + 3, CELL - 6, CELL - 6);
        text('KHÓA', x + CELL / 2, y + CELL / 2, 11, '#b8a888', 'center', true, 2);
      }
    });
    if (v.step === 1) text(`Pet của bạn: ${ROSTER[v.me].name}`, LX + LW / 2, GY + 2 * CELL + 22, 13, '#9fd8ff', 'center', true, 3);
    // the pet being raised has to be fit to fight: said here, before the picking, not only when A is refused
    const nl = Math.round(S.need ? S.need.nl : 0), sk = Math.round(S.need ? S.need.sk : 0), why = __chiSo.fit(SOLO_NL), weak = __chiSo.pet().why;
    text(`${DATA.pet.name} Lv${S.level}: năng lượng ${nl} · sức khỏe ${sk}`, LX + LW / 2, GY + 2 * CELL + 46, 12,
         why ? '#ff8a7a' : '#cfe8b0', 'center', true, 3);
    if (why) text(`Chưa đấu được: ${why}`, LX + LW / 2, GY + 2 * CELL + 66, 11, '#ff8a7a', 'center', true, 3);
    else if (weak.length) text(`Pet đang ${weak.join(', ')}: đánh yếu hơn`, LX + LW / 2, GY + 2 * CELL + 66, 11, '#ffc07a', 'center', true, 3);
    else if (__chiSo.buffText()) text(`Món nấu: ${__chiSo.buffText()} trận này`, LX + LW / 2, GY + 2 * CELL + 66, 11, '#ffe08a', 'center', true, 3);
    // right (its box is in the backdrop): the one under the cursor, standing side-on and breathing, facing the list
    if (!back) { ctx.fillStyle = 'rgba(0,0,0,0.30)'; ctx.fillRect(RX, 76, RW, 300); }
    const fr = sideOf(r.dir), f = fr && fr[Math.floor(now / 220) % 4];
    const cx = RX + RW / 2, foot = 318;
    ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.beginPath(); ctx.ellipse(cx, foot + 2, 62, 11, 0, 0, Math.PI * 2); ctx.fill();
    if (f && f.width) {
      // its own size, whole pixels: a plain copy on the R36S (the breathing frames and the bob make it move)
      const bob = Math.round(Math.abs(Math.sin(now / 300)) * 7);
      ctx.save(); ctx.translate(Math.round(cx), foot - bob); ctx.scale(-1, 1);
      ctx.drawImage(f, -Math.round(f.width / 2), -f.height); ctx.restore();
    }
    text(r.name, cx, 346, 18, '#fff2d8', 'center', true, 3);
    text(r.he === BOSS ? 'Boss cuối · Đài Ngũ Hành' : `hệ ${heName(r.he)}`, cx, 366, 13, HE_COL[r.he] || '#e0cfb0', 'center', true, 3);
    if (v.step === 1 && !foeOpen(r.dir))
      text(r.he === BOSS ? 'Chưa mở: phong ấn nó ở Đài Ngũ Hành' : 'Chưa mở: hạ nó ở Vùng đất', cx, 384, 11, '#ff8a7a', 'center', true, 3);
    text(`Bot: ◀ L1  ${LEVEL_NAMES[v.level]}  R1 ▶`, 320, 398, 13, '#ffd36e', 'center', true, 3);
    text('▲▼ đổi hệ · ◀▶ chọn pet', 320, 418, 12, '#e0cfb0', 'center', false, 3);
    text(v.step === 0 ? 'A: chọn pet · B: về Võ đường' : 'A: vào đấu · B: chọn lại pet', 320, 438, 12, '#f0e4ce', 'center', false, 3);
  }
  function pickPress(btn) {
    const v = S.vd, r = ROSTER[v.cur], g = GROUP(r.he), k = g.indexOf(v.cur);
    if (btn === 'LEFT') v.cur = g[(k + g.length - 1) % g.length];
    if (btn === 'RIGHT') v.cur = g[(k + 1) % g.length];
    if (btn === 'UP' || btn === 'DOWN') {
      const T = tabsOf(v.step), h = T.indexOf(r.he), g2 = GROUP(T[(h + (btn === 'UP' ? T.length - 1 : 1)) % T.length]);
      v.cur = g2[Math.min(k, g2.length - 1)];
    }
    if (btn === 'L1') v.level = (v.level + 3) % 4;
    if (btn === 'R1') v.level = (v.level + 1) % 4;
    if (btn === 'B') { if (v.step === 1) { v.step = 0; v.cur = v.me; } else fadeTo(() => { S.vd = { view: 'menu', sel: typeof __vdCard === 'function' ? __vdCard('solo') : 1 }; }); }
    if (btn === 'A') {
      if (v.step === 0) {                                         // the foe starts on the next element's first pet
        const els = tabsOf(0);
        v.me = v.cur; v.step = 1;
        v.cur = GROUP(els[(els.indexOf(r.he) + 1) % els.length])[0];
        return;
      }
      const why = __chiSo.fit(SOLO_NL);
      if (why) return toast(`${DATA.pet.name} chưa đấu được: ${why}, về nghỉ đã`);
      // the arena tells a mirror match apart by recolouring one side; the R36S cannot recolour (yet)
      if (globalThis.__SOLO_CUTS && v.cur === v.me) return toast('Chọn đối thủ khác pet của bạn');
      if (!foeOpen(ROSTER[v.cur].dir))
        return toast(r.he === BOSS ? 'Hư Ảnh chưa mở: phong ấn nó ở Đài Ngũ Hành' : `${ROSTER[v.cur].name} chưa mở: hạ nó trong trận Solo ở Vùng đất`);
      const me = ROSTER[v.me], foe = ROSTER[v.cur], level = v.level;
      if (typeof __vgVs === 'function') __vgVs(me.dir, foe.dir, 0, 0);   // its VS pictures start loading during the fade
      fadeTo(() => { S.vd = { view: 'solo', sel: 1, level }; globalThis.__soloPow = __chiSo.pow(S.level || 1); start(me, foe, level); });
    }
  }

  // the wait while the arena loads its sheets: the two pets face to face, VS, how far the loading has got
  function drawLoading(now) {
    const { me, foe, load } = arena, a = load.asked ? load.done / load.asked : 0;
    const left = arena.preload.length + preSounds.length, total = Math.max(arena.preTotal, left);
    const k = arena.rafs.length && total ? 0.4 + 0.6 * (1 - left / total) : 0.4 * a;
    // the VS screen of Vùng đất (game/src/vung-dat.js: the two pets' ultimate pictures, the bolt, VS) when it has them
    if (!(S.vd && S.vd.quiet) && typeof __vgVs === 'function' && __vgVs(me.dir, foe.dir, now - arena.t0, k)) {
      text('SELECT: hủy', 632, 466, 11, 'rgba(240,228,206,0.8)', 'right', false, 2);
      return;
    }
    // Vùng đất's matches (quiet): it draws its VS screen over this right after; nothing here (on the R36S this
    // screen under it took a good share of each loading frame)
    if (S.vd && S.vd.quiet && typeof __vgVsUp === 'function' && __vgVsUp()) return;
    // the night backdrop at half strength over the dark, made once and then copied (a frame used to blend it anew)
    if (!loadBack && IMG['nen-menu_troi-dem']) {
      const c = document.createElement('canvas'); c.width = 640; c.height = 480;
      const g = c.getContext('2d');
      g.fillStyle = '#120c08'; g.fillRect(0, 0, 640, 480);
      g.globalAlpha = 0.5; cover(g, IMG['nen-menu_troi-dem']); g.globalAlpha = 1;
      if (typeof __cv === 'object' && __cv.seal) __cv.seal(c.__id);
      loadBack = c;
    }
    if (loadBack) ctx.drawImage(loadBack, 0, 0);
    else { ctx.fillStyle = '#120c08'; ctx.fillRect(0, 0, 640, 480); }
    for (const [r, x, flip] of [[me, 170, false], [foe, 470, true]]) {
      const im = IM[r.dir];
      if (im) {
        const s = 2, w = im.width * s, h = im.height * s, bob = Math.sin(now / 300 + x) * 4;
        ctx.save(); ctx.translate(x, 250 + bob); if (flip) ctx.scale(-1, 1);
        ctx.drawImage(im, -w / 2, -h / 2, w, h); ctx.restore();
      }
      text(r.name, x, 340, 18, '#ffe6a8', 'center', true, 4);
      text(r.he === BOSS ? 'Boss cuối' : `hệ ${heName(r.he)}`, x, 362, 13, '#e0cfb0', 'center', false, 3);
    }
    title('VS', 320, 250 + Math.sin(now / 160) * 3, 32, '#ffd36e', 5);
    text(`Bot: ${LEVEL_NAMES[arena.level]}`, 320, 300, 13, '#e0cfb0', 'center', false, 3);
    ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fillRect(170, 410, 300, 12);
    ctx.fillStyle = '#ffd36e'; ctx.fillRect(172, 412, Math.round(296 * k), 8);
    text(`Đang chuẩn bị sân đấu… ${Math.round(k * 100)}%`, 320, 440, 14, '#fff2d8', 'center', true, 3);
    text('SELECT: hủy', 632, 470, 11, 'rgba(240,228,206,0.7)', 'right', false, 2);
  }

  // ---------- the hooks Võ đường calls ----------
  globalThis.__soloInfo = () => arena && { rafs: arena.rafs.length, keys: arena.keyFns.keydown.length, cv: arena.cv, started: arena.started };   // tests
  globalThis.__soloMatch = { ROSTER, start, stop,    // Vùng đất (game/src/vung-dat.js): its mini boss fights are Solo matches
                              lost: () => arena ? arena.lost : 0 };   // the HP the pet lost in it (0-100 a round)
  globalThis.__soloOpen = () => fadeTo(() => {
    // the pet being raised, when the arena has it, is picked to start with
    const own = Math.max(0, ROSTER.findIndex(r => DATA.pet && r.dir === DATA.pet.creature));
    S.vd = { view: 'solo-pick', sel: 1, step: 0, cur: own, me: own, level: 1 };
  });
  globalThis.__soloDraw = now => {
    const v = S.vd;
    if (v.view === 'solo-pick') return drawPick(now);
    if (!arena) { S.vd = { view: 'menu', sel: typeof __vdCard === 'function' ? __vdCard('solo') : 1 }; return; }        // e.g. after a reload: back to the menu
    if (!arena.started && !arena.rafs.length) return drawLoading(now);   // the arena still loading its pictures
    if (!arena.started && arena.aimWarm !== false && typeof __aimWarm === 'function' &&
        !arena.preload.length && !preSounds.length) {                 // then the aiming pictures (the arena's __aimWarm)
      const clock = typeof __cv === 'object' && __cv.clock ? __cv.clock : () => performance.now(), t = clock();
      while (clock() - t < PRELOAD_MS) if (!__aimWarm()) { arena.aimWarm = false; break; }
      return drawLoading(now);
    }
    if (!arena.started && (arena.preload.length || preSounds.length)) {   // then the reading ahead (R36S)
      arena.preTotal = Math.max(arena.preTotal, arena.preload.length + preSounds.length);
      const clock = typeof __cv === 'object' && __cv.clock ? __cv.clock : () => performance.now();   // real ms (now() is the frame's)
      const t = clock();
      while ((arena.preload.length || preSounds.length) && clock() - t < PRELOAD_MS) {
        if (arena.preload.length) void arena.preload.pop().c;
        else if (typeof SOUND === 'object' && SOUND) SOUND.sfx(preSounds.pop(), 0); else preSounds.pop();
      }
      return drawLoading(now);
    }
    // the VS screen (Vùng đất's, when it draws) stays at least VS_MIN_MS before the match
    if (!v.quiet && typeof __vgVs === 'function' && performance.now() - arena.t0 < VS_MIN_MS) return drawLoading(now);
    arena.started = true;
    if (arena.drive) arena.drive(arena);                         // Đấu qua wifi: its own frames, its own keys
    else {
      feedKeys();
      const cbs = arena.rafs.splice(0);                          // the same list the arena keeps adding to
      for (const fn of cbs) try { fn(performance.now()); } catch (e) { console.log('arena: ' + (e && e.stack || e)); }
    }
    const seen = globalThis.__soloSeen, p = seen && seen.P();      // the HP the pet loses (each round a new fighter)
    if (p) { if (p === arena.lastP && p.hp < arena.lastHp) arena.lost += arena.lastHp - p.hp; arena.lastP = p; arena.lastHp = p.hp; }
    if (arena.cv !== ctx.canvas && arena.cv.__id !== 0) ctx.drawImage(arena.cv, 0, 0);
    if (!v.quiet) text('SELECT: rời sân', 632, 470, 11, 'rgba(240,228,206,0.7)', 'right', false, 2);   // quiet: Vùng đất's matches
  };
  globalThis.__soloPress = btn => {
    const v = S.vd;
    if (v.view === 'solo-pick') return pickPress(btn);
    if (btn === 'SELECT') {
      // a match fought (not one left while loading): it cost energy and food, cheered or saddened the pet by how it
      // went, and 30% of the HP lost comes off Sức khỏe (THIET-KE.md 6.6); won, a day's Tinh thần +1
      const fought = arena && arena.started, sc = globalThis.__soloSeen && __soloSeen.score, win = !!sc && sc.me > sc.bot;
      let said = 'Rời sân đấu';
      if (fought) {
        __chiSo.cost(win ? 'soloWin' : 'soloLose');
        __chiSo.hurt(arena.lost); __chiSo.buffUsed();         // a dish's buff lasted the match
        const xp0 = S.xp; gainExp(20);
        const up = win ? __tapXong('solo') : '';
        said = `${win ? 'Thắng' : 'Thua'} ${sc ? sc.me + '-' + sc.bot : ''} · EXP +${Math.round(Math.max(0, S.xp - xp0))}${up ? ' · ' + up : ''}`;
      }
      toast(said);
      globalThis.__soloPow = null; globalThis.__soloSeen = null;
      stop(); fadeTo(() => { S.vd = { view: 'menu', sel: typeof __vdCard === 'function' ? __vdCard('solo') : 1 }; });
    }
    // everything else reaches the arena through the held buttons (feedKeys)
  };
})();
