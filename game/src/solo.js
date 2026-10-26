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
  ].map(([p, dir, name, he]) => ({ p, dir, name, he }));
  const LEVEL_NAMES = ['Tập', 'Dễ', 'Vừa', 'Khó'];
  const KEY = { UP: 'ArrowUp', DOWN: 'ArrowDown', LEFT: 'ArrowLeft', RIGHT: 'ArrowRight', A: 'j', B: 'k', X: 'l', Y: 'i',
                R1: 'Shift', L1: 'Shift', START: 'Enter' };
  // the pick screen: one element at a time (UP/DOWN), its pets in a row (LEFT/RIGHT)
  const HES = [...new Set(ROSTER.map(r => r.he))];
  const GROUP = he => ROSTER.map((r, i) => i).filter(i => ROSTER[i].he === he);
  const LX = 20, LW = 300, TAB_W = LW / 5, GCOLS = 4, CELL = LW / GCOLS, GY = 112;   // left: elements, pets
  const RX = 340, RW = 280;                                                          // right: the one picked
  const HE_COL = { hoa: '#ff7a4a', kim: '#cfe6ff', moc: '#8fdc6a', thuy: '#6ac0ff', tho: '#e0b060' };
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
  function start(me, foe, level) {
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
    const search = `?${me.p}&vs=${foe.p}&bot=${level}`;
    __SOLO_SRC(doc, win, { search }, (type, fn) => { if (keyFns[type]) keyFns[type].push(fn); }, fn => { rafs.push(fn); },
               (u, o) => !AC && /\.ogg$/.test(u) ? Promise.resolve({ arrayBuffer: () => Promise.resolve(soundOf(u)) }) : fetch(fix(u), o),
               Img);
    arena = { cv, keyFns, rafs, ctxs, held: {}, me, foe, level, t0: performance.now(), load, started: false, owned, preload, preTotal: 0 };
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
  let pickBack = null;
  function backdrop() {
    if (pickBack) return pickBack;
    if (!IMG['nen-menu_hoang-hon']) return null;
    const c = document.createElement('canvas'); c.width = 640; c.height = 480;
    const g = c.getContext('2d');
    g.fillStyle = '#1a120c'; g.fillRect(0, 0, 640, 480);
    g.drawImage(IMG['nen-menu_hoang-hon'], 0, 22);
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
  function drawPick(now) {
    const v = S.vd, r = ROSTER[v.cur], back = backdrop();
    if (back) ctx.drawImage(back, 0, 0);
    else { ctx.fillStyle = '#1a120c'; ctx.fillRect(0, 0, 640, 480); }
    title(v.step === 0 ? 'CHỌN PET CỦA BẠN' : 'CHỌN ĐỐI THỦ', 320, 36, 22, '#ffe6a8', 4);
    text(`Solo đối kháng · ${ROSTER.length} pet · bộ chiêu 1`, 320, 60, 13, '#e0cfb0', 'center', false, 3);
    // left: the elements, the shown one lit up; under them its pets, small
    HES.forEach((he, k) => {
      const x = LX + k * TAB_W, on = he === r.he;
      ctx.fillStyle = on ? 'rgba(255,214,110,0.30)' : 'rgba(0,0,0,0.40)'; ctx.fillRect(x + 2, 76, TAB_W - 4, 28);
      if (on) { ctx.strokeStyle = HE_COL[he] || '#ffd36e'; ctx.lineWidth = 2; ctx.strokeRect(x + 2, 76, TAB_W - 4, 28); }
      text(HE_NAME[he] || he, x + TAB_W / 2, 95, 13, on ? HE_COL[he] || '#ffe6a8' : '#b8a888', 'center', true, 2);
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
    });
    if (v.step === 1) text(`Pet của bạn: ${ROSTER[v.me].name}`, LX + LW / 2, GY + 2 * CELL + 22, 13, '#9fd8ff', 'center', true, 3);
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
    text(`hệ ${HE_NAME[r.he] || r.he}`, cx, 366, 13, HE_COL[r.he] || '#e0cfb0', 'center', true, 3);
    text(`Bot: ◀ L1  ${LEVEL_NAMES[v.level]}  R1 ▶`, 320, 398, 13, '#ffd36e', 'center', true, 3);
    text('▲▼ đổi hệ · ◀▶ chọn pet', 320, 418, 12, '#e0cfb0', 'center', false, 3);
    text(v.step === 0 ? 'A: chọn pet · B: về Võ đường' : 'A: vào đấu · B: chọn lại pet', 320, 438, 12, '#f0e4ce', 'center', false, 3);
  }
  function pickPress(btn) {
    const v = S.vd, r = ROSTER[v.cur], g = GROUP(r.he), k = g.indexOf(v.cur);
    if (btn === 'LEFT') v.cur = g[(k + g.length - 1) % g.length];
    if (btn === 'RIGHT') v.cur = g[(k + 1) % g.length];
    if (btn === 'UP' || btn === 'DOWN') {
      const h = HES.indexOf(r.he), g2 = GROUP(HES[(h + (btn === 'UP' ? HES.length - 1 : 1)) % HES.length]);
      v.cur = g2[Math.min(k, g2.length - 1)];
    }
    if (btn === 'L1') v.level = (v.level + 3) % 4;
    if (btn === 'R1') v.level = (v.level + 1) % 4;
    if (btn === 'B') { if (v.step === 1) { v.step = 0; v.cur = v.me; } else fadeTo(() => { S.vd = { view: 'menu', sel: 1 }; }); }
    if (btn === 'A') {
      if (v.step === 0) {                                         // the foe starts on the next element's first pet
        v.me = v.cur; v.step = 1;
        v.cur = GROUP(HES[(HES.indexOf(r.he) + 1) % HES.length])[0];
        return;
      }
      if (S.sick || S.need.nl < 15) return toast(`${DATA.pet.name} ${S.sick ? 'đang ốm' : 'mệt quá'} (năng lượng dưới 15), về nghỉ đã`);
      // the arena tells a mirror match apart by recolouring one side; the R36S cannot recolour (yet)
      if (globalThis.__SOLO_CUTS && v.cur === v.me) return toast('Chọn đối thủ khác pet của bạn');
      const me = ROSTER[v.me], foe = ROSTER[v.cur], level = v.level;
      fadeTo(() => { S.vd = { view: 'solo', sel: 1, level }; start(me, foe, level); });
    }
  }

  // the wait while the arena loads its sheets: the two pets face to face, VS, how far the loading has got
  function drawLoading(now) {
    const { me, foe, load } = arena, a = load.asked ? load.done / load.asked : 0;
    const left = arena.preload.length + preSounds.length, total = Math.max(arena.preTotal, left);
    const k = arena.rafs.length && total ? 0.4 + 0.6 * (1 - left / total) : 0.4 * a;
    ctx.fillStyle = '#120c08'; ctx.fillRect(0, 0, 640, 480);
    if (IMG['nen-menu_troi-dem']) { ctx.globalAlpha = 0.5; ctx.drawImage(IMG['nen-menu_troi-dem'], 0, 22); ctx.globalAlpha = 1; }
    for (const [r, x, flip] of [[me, 170, false], [foe, 470, true]]) {
      const im = IM[r.dir];
      if (im) {
        const s = 2, w = im.width * s, h = im.height * s, bob = Math.sin(now / 300 + x) * 4;
        ctx.save(); ctx.translate(x, 250 + bob); if (flip) ctx.scale(-1, 1);
        ctx.drawImage(im, -w / 2, -h / 2, w, h); ctx.restore();
      }
      text(r.name, x, 340, 18, '#ffe6a8', 'center', true, 4);
      text(`hệ ${HE_NAME[r.he] || r.he}`, x, 362, 13, '#e0cfb0', 'center', false, 3);
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
  globalThis.__soloOpen = () => fadeTo(() => {
    // the pet being raised, when the arena has it, is picked to start with
    const own = Math.max(0, ROSTER.findIndex(r => DATA.pet && r.dir === DATA.pet.creature));
    S.vd = { view: 'solo-pick', sel: 1, step: 0, cur: own, me: own, level: 1 };
  });
  globalThis.__soloDraw = now => {
    const v = S.vd;
    if (v.view === 'solo-pick') return drawPick(now);
    if (!arena) { S.vd = { view: 'menu', sel: 1 }; return; }        // e.g. after a reload: back to the menu
    if (!arena.started && !arena.rafs.length) return drawLoading(now);   // the arena still loading its pictures
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
    arena.started = true;
    feedKeys();
    const cbs = arena.rafs.splice(0);                            // the same list the arena keeps adding to
    for (const fn of cbs) try { fn(performance.now()); } catch (e) { console.log('arena: ' + (e && e.stack || e)); }
    if (arena.cv !== ctx.canvas && arena.cv.__id !== 0) ctx.drawImage(arena.cv, 0, 0);
    text('SELECT: rời sân', 632, 470, 11, 'rgba(240,228,206,0.7)', 'right', false, 2);
  };
  globalThis.__soloPress = btn => {
    const v = S.vd;
    if (v.view === 'solo-pick') return pickPress(btn);
    if (btn === 'SELECT') {
      if (arena && arena.started) {                               // left before the fight began: nothing gained, nothing spent
        S.need.nl = Math.max(0, S.need.nl - 8); S.need.no = Math.max(0, S.need.no - 4);
        const xp0 = S.xp; gainExp(20);
        toast(`Rời sân đấu · EXP +${Math.round(Math.max(0, S.xp - xp0))}`);
      }
      stop(); fadeTo(() => { S.vd = { view: 'menu', sel: 1 }; });
    }
    // everything else reaches the arena through the held buttons (feedKeys)
  };
})();
