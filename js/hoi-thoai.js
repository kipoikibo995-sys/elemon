// Elemon: the story's dialogue box (the story doc "Elemon — Cốt truyện và 5 vùng đất", 26/10/2026: a box at the
// bottom of the screen, the speaker's portrait on the left, A to go on). The words are all in game/src/truyen.js
// (globalThis.TRUYEN); here only when a scene starts and how it is drawn.
//   - a scene starts once, on the screen its `khi` names, when the pet's stage and level fit and nothing else is
//     going on there (no fade, no popup, no lesson half done); seen scenes are kept in S.truyen.da (saved with S)
//   - while it shows it takes every button: A or B shows the rest of the line at once, then the next page or line
//   - it is drawn over whatever screen is up, after the demo's frame (frame is wrapped, as song-that.js does)
// Portraits: the NPC's picture for that face, from the demo's own (IMG) or read from img/<path>.png; one not drawn
// yet (Già Quy) leaves the box without a portrait.
(() => {
  if (typeof press !== 'function' || typeof frame !== 'function' || typeof TRUYEN !== 'object') return;
  const BOX = { x: 16, y: 344, w: 608, h: 122 };
  const PORTRAIT_H = 240;                       // the tallest a portrait is drawn (the story's own are cut to 236)
  const PAD = 6, GAP = 8;                       // the portrait's frame round it, the space between it and the words
  const FONT = 'bold 17px Tahoma, sans-serif', FONT_I = 'italic bold 17px Tahoma, sans-serif';
  const LINE_H = 27, LINES = 3, CHAR_MS = 28;
  const VUNG = { hoa: 'Núi lửa', kim: 'Núi pha lê', moc: 'Rừng cổ thụ', tho: 'Hẻm vực', thuy: 'Hồ thác' };
  const sfx = (n, v) => { if (typeof SOUND === 'object' && SOUND) SOUND.sfx(n, v); };

  const PICS = {};
  function pic(path) {
    if (IMG[path] && IMG[path].width) return IMG[path];
    let im = PICS[path];
    if (!im) { im = PICS[path] = new Image(); im.onload = () => { im.__ok = true; }; im.src = `img/${path}.png`; }
    return im.__ok ? im : null;
  }

  // ---------- which scene, and when ----------
  const st = () => S.truyen || (S.truyen = { da: {}, dang: null });
  function calm() {                                    // the screen is settled enough to talk over
    if (S.fade !== 0) return false;
    switch (S.mode) {
      case 'egg': return !!S.egg && !S.egg.taps;
      case 'room': return S.stats === null && S.popupGoal === 0 && S.pickerGoal === 0 && !S.act;
      case 'school': return !!S.sch && S.sch.st === 'pick';
      case 'voduong': return !!S.vd && S.vd.view === 'menu';
      case 'vungdat': return !!S.vg && (S.vg.view === 'gate' || S.vg.view === 'result');   // a region's gate or a trip's end (vung-dat.js)
      case 'phim': return !!S.phim && !!S.phim.thoai;           // a film shot that waits for words (game/src/phim.js)
      default: return true;
    }
  }
  function nextScene() {
    if (!calm()) return null;
    const t = st();
    if (S.mode === 'phim') return TRUYEN.CANH.find(c => c.id === S.phim.thoai && !t.da[c.id]) || null;   // the one it names
    return TRUYEN.CANH.find(c => !t.da[c.id] && c.khi === S.mode && (!c.cap || c.cap.includes(S.stage)) &&
                                 (S.level || 0) >= (c.lv || 0) && here(c) &&
                                 (!c.dk || (typeof __truyenDk === 'function' && __truyenDk(c.dk, c.vung || EL())))) || null;
  }
  // a region scene: at that region (its `vung`, else the pet's own), on the screen its `man` names (the gate if none)
  const here = c => S.mode !== 'vungdat' || (S.vg.view === (c.man || 'gate') && S.vg.he === (c.vung || EL()));
  const fill = s => s.replace(/\{pet\}/g, DATA.pet.name).replace(/\{he\}/g, HE_NAME[EL()] || '')
                     .replace(/\{vung\}/g, VUNG[EL()] || '');

  // the line being shown: its speaker, portrait and pages of wrapped text (worked out once a line, and again once
  // its portrait has loaded: the words go to the right of it, so its width sets theirs)
  let shown = null;
  const portraitSize = img => { const k = Math.min(1, PORTRAIT_H / img.height); return [Math.round(img.width * k), Math.round(img.height * k)]; };
  function line(d) {
    const [who, face, words] = TRUYEN.CANH.find(c => c.id === d.id).cau[d.i];
    const npc = who && TRUYEN.NPC[who], path = npc && npc.anh && npc.anh[face], img = path ? pic(path) : null;
    if (shown && shown.id === d.id && shown.i === d.i && shown.img === img) return shown;
    const font = who ? FONT : FONT_I, room = img ? portraitSize(img)[0] + 2 * PAD + GAP : 0;
    const rows = wrapLines(fill(words), BOX.w - 48 - room, font), pages = [];
    for (let k = 0; k < rows.length; k += LINES) pages.push(rows.slice(k, k + LINES));
    const p = shown && shown.id === d.id && shown.i === d.i ? Math.min(d.p, pages.length - 1) : d.p;
    d.p = p;
    return (shown = { id: d.id, i: d.i, npc, img, room, font, pages });
  }
  const pageLen = p => p.reduce((n, r) => n + r.length, 0);

  // ---------- drawing ----------
  // a panel as the demo's cream label boxes: dark outer rim, blue inner one (fill null: the rims alone)
  function frameAt(x, y, w, h, fill, rims) {
    if (fill) { ctx.fillStyle = fill; ctx.beginPath(); ctx.roundRect(x, y, w, h, 10); ctx.fill(); }
    if (!rims) return;
    ctx.strokeStyle = '#4a3a2a'; ctx.lineWidth = 3; ctx.beginPath(); ctx.roundRect(x, y, w, h, 10); ctx.stroke();
    ctx.strokeStyle = '#7fb0d0'; ctx.lineWidth = 2; ctx.beginPath(); ctx.roundRect(x + 5, y + 5, w - 10, h - 10, 7); ctx.stroke();
  }
  function draw(now) {
    const d = st().dang, L = line(d), page = L.pages[d.p] || [], img = L.img;
    const left = BOX.x + L.room + 24;
    ctx.save();
    ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.fillRect(0, BOX.y - 40, 640, 480 - BOX.y + 40);
    if (img) {
      // the portrait in a frame of its own beside the words, bottoms level: the picture fills the frame exactly, so
      // the straight edges it was cut with (the bust's bottom, the shell's side) lie along the frame's
      const [w, h] = portraitSize(img), fw = w + 2 * PAD, fh = h + 2 * PAD, fy = BOX.y + BOX.h - fh;
      frameAt(BOX.x, fy, fw, fh, '#2b2333', false);
      ctx.save(); ctx.beginPath(); ctx.roundRect(BOX.x + 3, fy + 3, fw - 6, fh - 6, 7); ctx.clip();
      ctx.drawImage(img, BOX.x + PAD, fy + PAD, w, h);
      ctx.restore();
      frameAt(BOX.x, fy, fw, fh, null, true);
    }
    frameAt(BOX.x + L.room, BOX.y, BOX.w - L.room, BOX.h, '#fbf6ea', true);
    if (L.npc) {                                      // the name plate on the box's top edge
      ctx.font = 'bold 15px Tahoma, sans-serif';
      const w = Math.ceil(ctx.measureText(L.npc.ten).width) + 28;
      ctx.fillStyle = L.npc.mau; ctx.strokeStyle = '#2a1a10'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.roundRect(left - 8, BOX.y - 15, w, 28, 8); ctx.fill(); ctx.stroke();
      text(L.npc.ten, left - 8 + w / 2, BOX.y - 1, 15, '#fff6e0', 'center', true, 0);
    }
    // the words, letter by letter
    let n = Math.floor((now - d.t) / CHAR_MS);
    ctx.font = L.font; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillStyle = L.npc ? '#3a2a1a' : '#5a4a6a';
    page.forEach((r, k) => {
      if (n <= 0) return;
      ctx.fillText(r.slice(0, n), left, BOX.y + 32 + k * LINE_H);
      n -= r.length;
    });
    if (d.done && Math.floor(now / 400) % 2) {         // ▼: A goes on
      const x = BOX.x + BOX.w - 26, y = BOX.y + BOX.h - 22;
      ctx.fillStyle = '#c4553a'; ctx.beginPath(); ctx.moveTo(x - 7, y - 4); ctx.lineTo(x + 7, y - 4); ctx.lineTo(x, y + 4); ctx.fill();
    }
    ctx.restore();
    if (!d.done && (now - d.t) / CHAR_MS >= pageLen(page)) d.done = true;
  }

  // ---------- the hooks ----------
  let said = null;                                     // the line last spoken: '<scene>/<line>'
  const frame0 = frame;
  globalThis.frame = function (now) {
    frame0(now);
    const t = st();
    if (t.dang) {
      // a saved scene truyen.js no longer has (or has shorter), or one saved half way and loaded on another screen:
      // dropped, not seen (it starts again from its first line on its own screen)
      const c = TRUYEN.CANH.find(x => x.id === t.dang.id);
      if (!c || !c.cau[t.dang.i] || (c.khi !== S.mode && S.fade === 0)) { t.dang = null; shown = null; }
    }
    if (!t.dang) {
      said = null;                                     // a last line is left to finish
      const c = nextScene();
      if (!c) return;
      t.dang = { id: c.id, i: 0, p: 0, t: now, done: false };
      sfx('chon', 170);                                  // a scene opens
    }
    if (S.fade > 0) return;
    const d = t.dang, key = d.id + '/' + d.i;          // each line spoken as it comes up (game/src/giong.js)
    if (key !== said) { said = key; if (typeof __giong === 'function') __giong(__giongCau(d.id, d.i)); }
    draw(now);
  };
  const press0 = press;
  globalThis.press = function (btn) {
    const t = st(), d = t.dang;
    if (!d) return press0(btn);
    // START in a film skips it (game/src/phim.js), words and all: the scene is left unseen
    if (btn === 'START' && S.mode === 'phim') { t.dang = null; shown = null; return press0(btn); }
    if (btn !== 'A' && btn !== 'B') return;
    const now = performance.now();
    if (!d.done) { d.done = true; d.t = -1e9; return; }      // the rest of the page at once
    const L = line(d);
    if (d.p + 1 < L.pages.length) Object.assign(d, { p: d.p + 1, t: now, done: false });
    else if (d.i + 1 < TRUYEN.CANH.find(c => c.id === d.id).cau.length) Object.assign(d, { i: d.i + 1, p: 0, t: now, done: false });
    else { t.da[d.id] = 1; t.dang = null; shown = null; }
    sfx('menu', 220);                                    // on to the next line: a short click
  };
})();
