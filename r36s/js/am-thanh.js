// 8-bit sound for the R36S build of the test page (assets/am-thanh, scripts/make_sfx_8bit.py). Loaded after the
// page: its own global functions (press, act, fadeTo, frame) are wrapped, so the page stays exactly as it is.
// SOUND.sfx(name, volume 0..256) and SOUND.music(name): on the R36S r36s/js/shim.js (native, r36s/jsrt.c), in a
// browser the <audio> stand-in game/build_game.py puts in the page.
(() => {
  const ok = () => typeof SOUND === 'object' && SOUND;
  const sfx = (name, vol) => { if (ok()) SOUND.sfx(name, vol); }, music = name => { if (ok()) SOUND.music(name); };
  const has = name => typeof globalThis[name] === 'function';
  const ANIM = { eat: 'an', happy: 'vui', sleep: 'ngu' };
  const FAIL = /không|hết|chưa|khóa|trống/i;

  if (has('press')) {
    const press0 = globalThis.press;
    globalThis.press = function (btn) {
      const was = { coins: S.coins, toast: S.toastT, night: S.nightGoal, sparkle: S.sparkle, key: [S.cursor, S.pick,
                    S.tab, S.item, S.mapSel, S.stats, S.sock, S.gp && S.gp.r, S.gp && S.gp.c, S.gemMode].join() };
      const r = press0.apply(this, arguments);
      if (S.coins < was.coins) sfx('xu', 240);                                 // bought something
      else if (S.toastT !== was.toast && FAIL.test(S.toast || '')) sfx('loi', 200);
      else if (S.toastT !== was.toast && /khảm/.test(S.toast || '')) sfx('sach', 220);
      else if (S.sparkle !== was.sparkle) sfx('sach', 220);                   // the room cleaned
      else if (was.night === 1 && S.nightGoal === 0) sfx('thuc-day', 230);     // woken up
      else if (btn === 'B') sfx('quay-lai', 180);
      else if (btn === 'A' || btn === 'SELECT' || btn === 'R2') sfx('chon', 190);
      else if ([S.cursor, S.pick, S.tab, S.item, S.mapSel, S.stats, S.sock, S.gp && S.gp.r, S.gp && S.gp.c,
                S.gemMode].join() !== was.key) sfx('menu', 160);
      return r;
    };
  }
  if (has('act')) {
    const act0 = globalThis.act;
    globalThis.act = function (anim) {
      const r = act0.apply(this, arguments);
      if (ANIM[anim] && anim !== 'eat') sfx(ANIM[anim], 230);   // eating crunches once a bite, below
      return r;
    };
  }
  if (has('fadeTo')) {
    const fade0 = globalThis.fadeTo;
    globalThis.fadeTo = function () { sfx('chuyen', 170); return fade0.apply(this, arguments); };
  }
  if (has('frame')) {
    const frame0 = globalThis.frame;
    let tune = null, stepAt = 0, step = 0, bite = -1, evo = '', asked = false;
    globalThis.frame = function (now) {
      const r = frame0.apply(this, arguments);
      // music: the room theme by day, the night theme with the lights out, none while evolving
      const want = S.mode === 'evo' ? '' : S.night > 0.5 ? 'dem' : 'ngay';
      if (want !== tune) { music(want); tune = want; }
      // footsteps: the pet strolling in the room, or walking over the map
      let walking = S.mode === 'room' && S.stats === null && !!S.walk;
      if (S.mode === 'map' && S.mapPos && typeof PL !== 'undefined') {
        const p = PL[S.mapSel];
        walking = Math.hypot(p.x - S.mapPos.x, p.y + (typeof PET_DY === 'number' ? PET_DY : 0) - S.mapPos.y) > 1;
      }
      if (walking && now - stepAt > 280) { sfx(step++ % 2 ? 'buoc-1' : 'buoc-2', 140); stepAt = now; }
      // eating: a crunch each time the bite comes round
      if (S.act && S.act.food && typeof total === 'function') {
        const k = Math.floor((now - S.actT) / total(DATA.stages[S.stage].anims.eat));
        if (k !== bite) { bite = k; sfx('an', 230); }
      } else bite = -1;
      // the "ready to evolve" panel pops up
      if (S.asked && !asked) sfx('ngay', 220);
      asked = S.asked;
      // evolution: the swirl rises, the flash, then the fanfare with the banner
      if (S.mode === 'evo' && typeof EVO === 'object') {
        const ms = now - S.t0;
        const k = ms >= EVO.banner[0] ? 'banner' : ms >= EVO.flash[0] ? 'flash' : ms >= EVO.swirl[0] ? 'swirl' : 'calm';
        if (k !== evo) {
          if (k === 'swirl') sfx('tien-hoa', 230);
          if (k === 'flash') sfx('no', 230);
          if (k === 'banner') sfx('thang', 250);
          evo = k;
        }
      } else evo = '';
      return r;
    };
  }
})();
