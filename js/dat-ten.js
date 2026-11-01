// Elemon: naming the pet again after each evolution (Con → Nhi → Thiếu niên → Trưởng thành → Huyền thoại).
// A on the demo's "A: tiếp tục" lets its own fade run, then this screen comes up over the stage the fade set
// (room, or 'end' after Huyền thoại) with the old name filled in; Xong puts the name in DATA.pet.name (saved with
// the pet by song-that.js) and goes back to that screen.
// The handhelds have no keyboard: a 10 x 4 grid of keys picked with the D-pad.
//   - A types the key, B rubs out the last letter, X a space, START = Xong
//   - a word's first letter is a capital by itself; the ⇧ key turns capitals on for every letter
//   - the five tone keys put their mark on the right vowel of the last word (the old style, as the game writes
//     "hóa"); the same tone again takes it off
// Pictures from assets/source/tien-hoa/TH8_ban-phim.png (th_ten, th_phim...) when they are there; drawn plain if not.
(() => {
  if (typeof press !== 'function' || typeof frame !== 'function' || typeof fadeTo !== 'function') return;
  const MODE = 'datTen', MAX = 12;
  const sfx = (n, v) => { if (typeof SOUND === 'object' && SOUND) SOUND.sfx(n, v); };
  const TONES = [['́', 'á'], ['̀', 'à'], ['̉', 'ả'], ['̃', 'ã'], ['̣', 'ạ']];
  const TONE_RE = /[̣̀́̃̉]/g;
  const VOWELS = 'aăâeêioôơuưy', HATS = 'ăâêôơư';
  // the keys, row by row: a letter, or [kind, label, width in keys]
  const ROWS = [
    [...'aăâbcdđeêg'],
    [...'hiklmnoôơp'],
    [...'qrstuưvxy', ['hoa', '⇧', 1]],
    [...TONES.map(([m, l]) => ['dau', l, 1, m]), ['cach', 'Cách', 2], ['xoa', 'Xóa', 1], ['xong', 'Xong', 2]],
  ];
  const KW = 54, KH = 44, GAP = 6, KX = (640 - (10 * KW + 9 * GAP)) / 2, KY = 258;
  const PLATE = { x: 214, y: 118, w: 404, h: 64 };
  const PET_X = 112, PET_Y = 232;

  const PICS = {};
  function pic(path) {
    if (IMG[path] && IMG[path].width) return IMG[path];
    let im = PICS[path];
    if (!im) { im = PICS[path] = new Image(); im.onload = () => { im.__ok = true; }; im.onerror = () => { im.__bad = true; }; im.src = `img/${path}.png`; }
    return im.__ok ? im : null;
  }
  // a key's column span: [first column, width]
  const spans = r => { let c = 0; return ROWS[r].map(k => { const w = typeof k === 'string' ? 1 : k[2], s = [c, w]; c += w; return s; }); };
  const SPANS = ROWS.map((_, r) => spans(r));
  const keyAt = (r, col) => SPANS[r].findIndex(([c, w]) => col >= c && col < c + w);

  // ---------- the words ----------
  const nfc = s => s.normalize('NFC');
  const bare = ch => nfc(ch.normalize('NFD').replace(TONE_RE, ''));       // a letter without its tone (hats stay)
  const len = s => [...s].length;
  const atWordStart = s => !s || s.endsWith(' ');
  // the tone on the last word: which vowel takes it (qu-, gi- are consonants; a hat vowel first; a closed syllable
  // its last vowel; an open one of two vowels the first, of three the middle)
  function tone(s, mark) {
    const m = /(\S+)$/.exec(s);
    if (!m) return null;
    const letters = [...m[1]].map(bare), low = letters.map(c => c.toLowerCase());
    const had = [...m[1]].map(c => (c.normalize('NFD').match(TONE_RE) || [])[0]).find(Boolean);
    let from = 0;
    if ((low[0] === 'q' && low[1] === 'u') || (low[0] === 'g' && low[1] === 'i' && VOWELS.includes(low[2] || ''))) from = 2;
    let end = -1, start = -1;
    for (let i = low.length - 1; i >= from; i--) {
      if (VOWELS.includes(low[i])) { if (end < 0) end = i; start = i; }
      else if (end >= 0) break;
    }
    if (end < 0) return null;
    const group = []; for (let i = start; i <= end; i++) group.push(i);
    const hats = group.filter(i => HATS.includes(low[i]));
    const at = hats.length ? hats[hats.length - 1] : group.length === 1 ? start : end < low.length - 1 ? end
      : group.length === 2 ? start : start + 1;
    if (had !== mark) letters[at] = nfc(letters[at] + mark);
    return s.slice(0, s.length - m[1].length) + letters.join('');
  }

  // ---------- the screen ----------
  function open(back) {
    const name = DATA.pet.name || '';
    S.datTen = { name, old: name, r: 0, c: 0, caps: false, back, t0: performance.now() };
    S.mode = MODE;
  }
  globalThis.__datTen = open;                                   // the egg screen could use it too
  const upper = d => d.caps || atWordStart(d.name);

  function plain(x, y, w, h, on) {                               // a key or the name plate without pictures
    ctx.fillStyle = on ? '#6a3e1c' : '#2c1a10'; ctx.fillRect(x, y, w, h);
    ctx.lineWidth = on ? 3 : 2; ctx.strokeStyle = on ? '#ffd36e' : '#a0743a'; ctx.strokeRect(x + 1, y + 1, w - 2, h - 2);
  }
  function key(x, y, w, h, on, wide) {
    const im = pic(wide ? (on ? 'th_phim-rong_chon' : 'th_phim-rong') : (on ? 'th_phim_chon' : 'th_phim'));
    if (im) ctx.drawImage(im, x, y, w, h); else plain(x, y, w, h, on);
  }
  function draw(now) {
    const d = S.datTen;
    ctx.drawImage(IMG.nen, 0, 0, 640, 480);              // the evolution's backdrop (TH1_nen.png when drawn)
    ctx.fillStyle = 'rgba(8,5,12,0.55)'; ctx.fillRect(0, 0, 640, 480);
    // the pet in its new form, on the left
    if (typeof drawPet === 'function' && DATA.stages[S.stage]) drawPet(S.stage, sample(BOUNCE, now), PET_X, PET_Y);
    title('ĐẶT TÊN', 416, 50, 32, '#ffecaa', 5);
    text(`${DATA.creature_name} · ${DATA.stages[S.stage] ? DATA.stages[S.stage].name : ''}`, 416, 92, 15, '#ffd28c', 'center', true, 3);
    // the name plate and the name
    const P = PLATE, plate = pic('th_ten');
    if (plate) ctx.drawImage(plate, P.x - 20, P.y - 6, P.w + 40, P.h + 12); else plain(P.x, P.y, P.w, P.h, false);
    const tx = P.x + P.w / 2, ty = P.y + P.h / 2 + 1;
    text(d.name || ' ', tx, ty, 26, '#fff2d8', 'center', true, 4);
    ctx.font = 'bold 26px Tahoma, sans-serif';
    const w = d.name ? ctx.measureText(d.name).width : 0;
    if (Math.floor(now / 450) % 2) { ctx.fillStyle = '#ffd36e'; ctx.fillRect(Math.round(tx + w / 2 + 3), P.y + 16, 3, P.h - 32); }
    text(`${len(d.name)}/${MAX}`, P.x + P.w - 8, P.y + P.h + 12, 11, '#c9bba8', 'right', false, 2);
    // the keys
    const panel = pic('th_phim-nen');
    if (panel) ctx.drawImage(panel, KX - 16, KY - 14, 10 * KW + 9 * GAP + 32, 4 * KH + 3 * GAP + 28);
    const up = upper(d);
    ROWS.forEach((row, r) => row.forEach((k, i) => {
      const [c, wc] = SPANS[r][i], x = KX + c * (KW + GAP), y = KY + r * (KH + GAP), w = wc * KW + (wc - 1) * GAP;
      const on = r === d.r && i === keyAt(r, d.c);
      key(x, y, w, KH, on, wc > 1);
      let label = typeof k === 'string' ? (up ? k.toUpperCase() : k) : k[1], col = on ? '#fff2d8' : '#f0e4ce';
      if (typeof k !== 'string' && k[0] === 'hoa' && d.caps) col = '#8ce16e';
      if (typeof k !== 'string' && k[0] === 'xong') col = on ? '#fff2d8' : '#ffd36e';
      text(label, x + w / 2, y + KH / 2 + 1, typeof k === 'string' || k[0] === 'dau' || k[0] === 'hoa' ? 21 : 16, col, 'center', true, 3);
    }));
    text('A: gõ · B: xóa · X: cách · START: xong', 320, 466, 13, '#c9bba8', 'center', false, 3);
  }

  function done() {
    const d = S.datTen, name = d.name.trim().replace(/ +/g, ' ');
    DATA.pet.name = name || d.old;
    sfx('vui', 220);
    fadeTo(() => {
      S.mode = d.back; S.datTen = null;
      toast(name && name !== d.old ? `Từ nay gọi là ${DATA.pet.name}!` : `${DATA.pet.name} vẫn giữ tên cũ`);
    });
  }
  function typeKey(d) {
    const k = ROWS[d.r][keyAt(d.r, d.c)];
    if (typeof k === 'string') {
      if (len(d.name) >= MAX) { sfx('loi', 200); return toast(`Tên dài nhất ${MAX} chữ`); }
      d.name += upper(d) ? k.toUpperCase() : k;
    } else if (k[0] === 'dau') {
      const s = tone(d.name, k[3]);
      if (s === null) return sfx('loi', 200);
      d.name = s;
    } else if (k[0] === 'hoa') d.caps = !d.caps;
    else if (k[0] === 'cach') space(d);
    else if (k[0] === 'xoa') rub(d);
    else if (k[0] === 'xong') return done();
  }
  function space(d) { if (d.name && !d.name.endsWith(' ') && len(d.name) < MAX) d.name += ' '; }
  function rub(d) { if (!d.name) return sfx('loi', 200); d.name = [...d.name].slice(0, -1).join(''); sfx('quay-lai', 180); }

  // ---------- the hooks ----------
  const press0 = press;
  globalThis.press = function (btn) {
    if (S.mode === 'evo' && S.waitA && btn === 'A' && S.fade === 0 && S.evoTo) {
      press0(btn);                                               // the demo's own fade: the new stage, the gold
      const cb = fadeCb;
      if (cb) fadeCb = () => { const r = cb(); open(S.mode); return r; };
      return;
    }
    if (S.mode !== MODE || !S.datTen) return press0(btn);
    if (S.fade > 0) return;
    const d = S.datTen;
    if (btn === 'UP' || btn === 'DOWN') {                        // every row spans the 10 columns: the column stays
      d.r = (d.r + (btn === 'UP' ? 3 : 1)) % 4;
      sfx('menu', 160);
    } else if (btn === 'LEFT' || btn === 'RIGHT') {
      const sp = SPANS[d.r], i = keyAt(d.r, d.c), j = (i + (btn === 'LEFT' ? sp.length - 1 : 1)) % sp.length;
      d.c = sp[j][0];
      sfx('menu', 160);
    } else if (btn === 'A') typeKey(d);
    else if (btn === 'B') rub(d);
    else if (btn === 'X') { space(d); sfx('menu', 160); }
    else if (btn === 'START') done();
  };
  const evo0 = drawEvo;
  globalThis.drawEvo = function (now) {
    if (S.mode !== MODE || !S.datTen) return evo0(now);
    draw(now);
    if (S.toast && now - S.toastT < 1800) {                       // the demo draws toasts only on its own screens
      ctx.fillStyle = 'rgba(18,11,9,0.85)'; ctx.fillRect(140, 190, 360, 40); text(S.toast, 320, 210, 14, '#f0e4ce', 'center');
    }
  };
  globalThis.__tone = tone;                                      // for the test harness
})();
