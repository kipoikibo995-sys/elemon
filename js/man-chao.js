// Elemon: the title screen's extras (the user, 31/10/2026).
//   - "Tiếp tục" opens the list of pets being raised (one save each, game/src/song-that.js: __luu): A plays one,
//     X twice deletes it, and "Nuôi thêm pet" starts another (a new egg) while there is a free slot
//   - the title's buttons in a row: Chơi mới · Tiếp tục · Cài đặt · Thoát game (◄ ► or ▲ ▼)
//   - "Cài đặt" (also START in the room): background music on/off, sound effects 0-10, the
//     story's voices on/off, the pet's talk (game/src/loi-noi.js) on/off; kept for every pet in holua-cai-dat
//   - "Thoát game": A twice ends the program (the runtime's __cv.exit, r36s/jsrt.c, which saves
//     through __quit on the way out like SELECT + START); a runtime without it, or a browser, says how to quit instead
//   - in the room SELECT asks "Về màn chào?" (A yes, B no): the pet is saved and the title screen comes back, to
//     play another pet (the user, 31/10); the stats screen, SELECT's job in the demo, opens on L1 / R1 instead
// Music has no volume on the handhelds' runtime (r36s/jsrt.c plays it as it is), so it is on or off.
(() => {
  if (typeof press !== 'function' || typeof drawEvo !== 'function' || typeof drawTitle !== 'function') return;
  const KEY = 'holua-cai-dat';
  const sfx = (n, v) => { if (typeof SOUND === 'object' && SOUND) SOUND.sfx(n, v); };
  const BAC = { baby: 'Con', child: 'Nhi', teen: 'Thiếu niên', adult: 'Trưởng thành', legend: 'Huyền thoại',
                adult4: 'Trưởng thành', legend4: 'Huyền thoại' };
  const HE_COL = { hoa: '#ff8a4a', kim: '#e8e8f0', moc: '#7ad86a', thuy: '#6ab8ff', tho: '#d8a860' };

  // ---------- the settings, and the sound through them ----------
  // three loudnesses, 0..10 (the user, 01/11: the music, the buttons' sounds and the rest each on its own; the
  // handheld's volume buttons still move all of them): nhac the music (7 = as loud as before), tiengNut the menu
  // sounds, tiengDong everything else; a save from before (nhac on/off, no tiengNut) reads as it sounded
  const CD = globalThis.CAI_DAT = { nhac: 7, tiengNut: 10, tiengDong: 10, giong: true, noi: true };
  try {
    const old = JSON.parse(localStorage.getItem(KEY) || '{}');
    Object.assign(CD, old);
    if (typeof old.nhac === 'boolean') CD.nhac = old.nhac ? 7 : 0;
    if (old.tiengNut === undefined && old.tiengDong !== undefined) CD.tiengNut = old.tiengDong;
  } catch (e) {}
  const keep = () => { try { localStorage.setItem(KEY, JSON.stringify(CD)); } catch (e) {} };
  const NUT = new Set(['menu', 'chon', 'quay-lai', 'chuyen', 'loi']);   // the buttons' sounds
  let song = '';
  if (typeof SOUND === 'object' && SOUND) {
    const S0 = SOUND;
    const musicVol = () => { if (S0.vol) S0.vol(CD.nhac * 20); };
    globalThis.SOUND = {
      sfx(name, vol) {
        const lv = name.startsWith('giong/') ? 10 : NUT.has(name) ? CD.tiengNut : CD.tiengDong;   // the voice: Giọng đọc's
        if (lv > 0) S0.sfx(name, Math.round(vol * lv / 10));
      },
      music(name) { song = name || ''; S0.music(CD.nhac ? song : ''); },
      _music: n => S0.music(n),
      _vol: musicVol,
    };
    musicVol();
  }
  if (typeof __giong === 'function') {
    const g0 = __giong;
    globalThis.__giong = key => { if (CD.giong || !key) return g0(key); g0(null); return __giongMs(key); };   // the films keep their pace
  }

  // ---------- the title screen: four buttons in a row (the user, 31/10: Cài đặt and Thoát game with Chơi mới and
  // Tiếp tục, the same buttons, side by side) ----------
  // the demo's title is drawn over img/title_b_trong (its two painted buttons covered with grass, game/build_game.py),
  // without its own labels, highlight and hint; then the row
  const BTNS = [{ name: 'Chơi mới', fill: '#fbdea9', ink: '#7a3410' }, { name: 'Tiếp tục', fill: '#c9edaf', ink: '#2f6a2a' },
                { name: 'Cài đặt', fill: '#bfe0f5', ink: '#24507a' }, { name: 'Thoát game', fill: '#f5c4c0', ink: '#8a2a22' }];
  const BW = 136, BH = 32, BGAP = 20, BX = (640 - (4 * BW + 3 * BGAP)) / 2, BY = 386;
  const SKIP = new Set(['Chơi mới', 'Tiếp tục', '▲ ▼ chọn · A: bắt đầu']);
  const CHOICES = 4;
  let quitAsk = -1e9, clean = null;
  function cleanTitle() {
    if (!clean) { clean = new Image(); clean.onload = () => { clean.__ok = true; }; clean.src = 'img/title_b_trong.png'; }
    return clean.__ok ? clean : null;
  }
  const title0 = drawTitle;
  globalThis.drawTitle = function (now) {
    const bg = IMG.title_b && cleanTitle();
    if (!bg) return title0(now);                                  // no clean picture: the demo's own two buttons
    const sel = S.titleSel, b0 = IMG.title_b, f0 = ctx.fillText, s0 = ctx.strokeText;
    ctx.fillText = function (t) { if (!SKIP.has(t)) return f0.apply(ctx, arguments); };
    ctx.strokeText = function (t) { if (!SKIP.has(t)) return s0.apply(ctx, arguments); };
    S.titleSel = -1; IMG.title_b = bg;
    try { title0(now); } finally { ctx.fillText = f0; ctx.strokeText = s0; S.titleSel = sel; IMG.title_b = b0; }
    const has = __luu.any();
    BTNS.forEach((b, i) => {
      const on = i === sel, x = BX + i * (BW + BGAP), y = BY - (on ? 2 : 0), grey = i === 1 && !has;
      ctx.save();
      ctx.beginPath(); ctx.roundRect(x, y, BW, BH, BH / 2);
      ctx.fillStyle = grey ? '#dfe8da' : b.fill; ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.fillRect(x + 10, y + 4, BW - 20, 5);       // the shine along the top
      ctx.lineWidth = 2; ctx.strokeStyle = '#493950'; ctx.stroke();
      if (on) {
        ctx.beginPath(); ctx.roundRect(x - 4, y - 4, BW + 8, BH + 8, BH / 2 + 4);
        ctx.lineWidth = 3; ctx.strokeStyle = `rgba(255,255,255,${0.75 + 0.25 * Math.sin(now / 200)})`; ctx.stroke();
      }
      ctx.restore();
      text(b.name, x + BW / 2, y + BH / 2 + 1, 16, grey ? '#8aa088' : b.ink, 'center', true);
    });
    if (Math.floor(now / 600) % 2) text('◄ ► chọn · A: bắt đầu', 320, 452, 12, '#ffffff', 'center', false, 3);
    if (sel === 3 && performance.now() - quitAsk < 3000) {
      ctx.fillStyle = 'rgba(18,11,9,0.88)'; ctx.fillRect(150, 214, 340, 44);
      text('Bấm A lần nữa để thoát game', 320, 236, 15, '#ffd36e', 'center', true, 3);
    }
  };
  function quitGame() {
    if (typeof __quit === 'function') __quit();                // the save, whatever was open
    if (typeof __cv === 'object' && typeof __cv.exit === 'function') { S.mode = 'thoat'; S.thoatT = performance.now(); return; }
    toast('Giữ SELECT + START để tắt game');                    // an older runtime, or a browser
  }
  function drawBye(now) {
    ctx.fillStyle = '#0c0806'; ctx.fillRect(0, 0, 640, 480);
    title('TẠM BIỆT!', 320, 220, 32, '#ffecaa', 5);
    text('Hẹn gặp lại nhé', 320, 262, 15, '#c9bba8', 'center', false, 3);
    if (now - S.thoatT > 700 && !S.thoatDone) { S.thoatDone = true; if (typeof SOUND === 'object' && SOUND) SOUND.music(''); __cv.exit(); }
  }

  // ---------- the pet list ----------
  const PICS = {};
  function petPic(sv) {                                    // the pet's standing frame at its stage, loaded once
    const id = sv.pet.creature, st = sv.S.stage, k = id + '/' + st;
    if (k in PICS) return PICS[k] && PICS[k].__ok ? PICS[k] : null;
    PICS[k] = null;
    petData(id).then(j => {
      const s = j.stages[st] || j.stages[Object.keys(j.stages)[0]], f = s.meta.frames.includes('idle-0') ? 'idle-0' : s.meta.frames[0];
      const im = new Image(); im.onload = () => { im.__ok = true; }; im.src = `../pets/${s.dir}/${f}.png`; PICS[k] = im;
    }).catch(() => {});
    return null;
  }
  const kindName = id => { const c = (DATA.creatures || []).find(c => c.id === id); return c ? c.name : id; };
  function ago(wall) {
    const m = Math.max(0, Math.round((Date.now() - wall) / 60e3));
    return m < 1 ? 'vừa chơi' : m < 60 ? `${m} phút trước` : m < 1440 ? `${Math.floor(m / 60)} giờ trước` : `${Math.floor(m / 1440)} ngày trước`;
  }
  function entries() {                                    // the pets, then "Nuôi thêm pet" while a slot is free
    const l = __luu.list().sort((a, b) => (b.sv.wall || 0) - (a.sv.wall || 0));
    return l.length < __luu.max ? [...l, { moi: true }] : l;
  }
  function openList() { S.ds = { sel: 0, list: entries(), xoa: -1, xoaT: 0 }; S.mode = 'dsPet'; }
  const CARD = { x0: 18, y0: 74, w: 296, h: 116, dx: 308, dy: 124 };
  function card(i) { return { x: CARD.x0 + (i % 2) * CARD.dx, y: CARD.y0 + Math.floor(i / 2) * CARD.dy, w: CARD.w, h: CARD.h }; }
  function frameBox(x, y, w, h, on, col) {
    ctx.fillStyle = on ? 'rgba(70,44,24,0.94)' : 'rgba(30,19,12,0.88)'; ctx.fillRect(x, y, w, h);
    ctx.lineWidth = on ? 3 : 2; ctx.strokeStyle = on ? '#ffd36e' : col || '#8a6232'; ctx.strokeRect(x + 1, y + 1, w - 2, h - 2);
  }
  function drawList(now) {
    pickBack();
    ctx.fillStyle = 'rgba(10,6,4,0.45)'; ctx.fillRect(0, 0, 640, 480);
    title('CHỌN PET', 320, 38, 32, '#ffecaa', 5);
    const d = S.ds;
    d.list.forEach((e, i) => {
      const b = card(i), on = i === d.sel;
      if (e.moi) {
        frameBox(b.x, b.y, b.w, b.h, on, '#5a7a3a');
        text('+', b.x + 54, b.y + b.h / 2, 44, on ? '#b8f08a' : '#8ac86a', 'center', true, 3);
        text('Nuôi thêm pet', b.x + 108, b.y + 44, 18, on ? '#fff2d8' : '#e8dcc0', 'left', true, 3);
        text(`Ấp một quả trứng mới (${d.list.length - 1}/${__luu.max})`, b.x + 108, b.y + 70, 12, '#c9bba8', 'left', false, 2);
        return;
      }
      const sv = e.sv, he = sv.pet.element, st = sv.S.stage;
      frameBox(b.x, b.y, b.w, b.h, on, HE_COL[he]);
      const im = petPic(sv);
      if (im) fit(im, b.x + 52, b.y + b.h / 2, 84, 96, 0);
      text(sv.pet.name || '?', b.x + 104, b.y + 26, 18, on ? '#fff2d8' : '#f0e4ce', 'left', true, 3);
      text(`${kindName(sv.pet.creature)} · ${BAC[st] || st}`, b.x + 104, b.y + 50, 13, HE_COL[he] || '#ffd28c', 'left', true, 2);
      text(`Lv ${sv.S.level || 1} · ${(sv.S.coins || 0).toLocaleString('en-US')} vàng`, b.x + 104, b.y + 72, 12, '#e0d0b0', 'left', false, 2);
      if (d.xoa === i && now - d.xoaT < 3000) text('Bấm X lần nữa để xóa!', b.x + 104, b.y + 94, 12, '#ff7a5a', 'left', true, 2);
      else text(ago(sv.wall || 0), b.x + 104, b.y + 94, 11, '#a89880', 'left', false, 2);
    });
    text('A: chơi · X: xóa pet · B: quay lại', 320, 464, 13, '#c9bba8', 'center', false, 3);
  }
  function listPress(btn) {
    const d = S.ds, n = d.list.length, now = performance.now();
    if (btn === 'LEFT' || btn === 'RIGHT') { d.sel = (d.sel + (btn === 'LEFT' ? n - 1 : 1)) % n; sfx('menu', 160); }
    if (btn === 'UP' && d.sel >= 2) { d.sel -= 2; sfx('menu', 160); }
    if (btn === 'DOWN' && d.sel + 2 < n) { d.sel += 2; sfx('menu', 160); }
    if (btn === 'B') { sfx('quay-lai', 180); return fadeTo(() => { S.mode = 'title'; S.ds = null; }); }
    const e = d.list[d.sel];
    if (btn === 'X' && e && !e.moi) {
      if (d.xoa === d.sel && now - d.xoaT < 3000) {
        __luu.remove(e.n); sfx('loi', 200);
        toast(`Đã xóa ${e.sv.pet.name}`);
        d.list = entries(); d.sel = Math.min(d.sel, d.list.length - 1); d.xoa = -1;
      } else { d.xoa = d.sel; d.xoaT = now; sfx('menu', 160); }
    }
    if (btn === 'A' || btn === 'START') {
      if (!e) return;
      if (e.moi) { S.mode = 'title'; S.titleSel = 0; S.ds = null; return press0('A'); }   // song-that: the next free slot
      __luu.open(e.n);
    }
  }

  // ---------- the settings screen ----------
  // Cập nhật (the in-device update): only on the handheld build, where elemon runs ota.sh (packaging/trimui-brick)
  const OTA = typeof __cv === 'object' && !!__cv.ota && !__cv.test && __cv.readText('ota.sh') !== null;
  const ROWS = [
    ['nhac', 'Nhạc nền'], ['tiengNut', 'Tiếng nút bấm'], ['tiengDong', 'Hiệu ứng'], ['giong', 'Giọng đọc truyện'], ['noi', 'Pet nói chuyện'],
    ...(OTA ? [['capNhat', 'Cập nhật']] : []), ['ve', 'Quay lại'],
  ];
  const LEVEL = new Set(['nhac', 'tiengNut', 'tiengDong']);   // the rows with a 0..10 bar
  function openSettings(back = 'title') { S.cd = { sel: 0, back }; S.mode = 'caiDat'; }

  // the update: ota.sh writes .ota/state ("status=..." lines); the version here is files.txt's "#version"
  const readKv = path => {
    const t = __cv.readText(path), o = {};
    if (t) for (const l of t.split('\n')) { const i = l.indexOf('='); if (i > 0) o[l.slice(0, i)] = l.slice(i + 1); }
    return o;
  };
  const myVersion = () => { const t = OTA && __cv.readText('files.txt'); const m = t && /^#version (\S+)/m.exec(t); return m ? m[1] : ''; };
  const MB = b => `${Math.max(0.1, (+b || 0) / 1048576).toFixed(1)} MB`;
  let otaSt = {}, otaT = 0, otaMine = false;                 // otaMine: started in this run (else a state left over)
  function otaState(now) {
    if (now - otaT > 400) { otaT = now; otaSt = readKv('.ota/state'); }
    const s = otaSt.status;
    if (!otaMine && (s === 'checking' || s === 'dl')) return { status: 'cut' };   // the game was closed mid-way
    return otaSt;
  }
  function otaLine(st) {                                     // [value at the row's right, the line under the list]
    const v = myVersion() || 'v1.0';
    switch (st.status) {
      case 'checking': return ['Đang kiểm tra…', 'Đang hỏi máy chủ có bản mới không'];
      case 'same': return [v, `Đang là bản mới nhất (${v})`];
      case 'new': return [`Có ${st.version}`, `Bản ${st.version}: ${st.files} file, ${MB(st.bytes)} · A: tải về`];
      case 'dl': return [`${Math.round(100 * (+st.got || 0) / Math.max(1, +st.bytes))}%`,
                         `Đang tải ${st.done}/${st.total} file · ${MB(st.got)} / ${MB(st.bytes)} · cứ chơi tiếp được`];
      case 'ready': return ['Sẵn sàng', `Đã tải xong ${st.version} · A: cài ngay (game tự mở lại)`];
      case 'installed': return [v, `Đã cài ${st.version}`];
      case 'cut': return [v, 'Lần tải trước chưa xong · A: tải tiếp'];
      case 'error': return ['Lỗi', st.msg || 'Có lỗi, thử lại sau'];
      default: return [v, 'A: kiểm tra bản mới (cần wifi)'];
    }
  }
  function otaPress(now) {
    const s = otaState(now).status;
    if (s === 'checking' || s === 'dl') return toast('Đang chạy, đợi chút');
    if (s === 'ready') {                                       // quit; launch.sh puts it in and opens the game again
      if (typeof __quit === 'function') __quit();
      toast('Đang cài bản mới…');
      return setTimeout(() => __cv.exit(), 600);
    }
    otaMine = __cv.ota(s === 'new' || s === 'cut' ? 'get' : 'check');
    otaT = 0;
    if (!otaMine) toast('Không chạy được trình cập nhật');
  }
  // a version just put in says it started (ota.sh after keeps it; without this it is undone on quitting)
  if (OTA && __cv.readText('.ota/trial')) setTimeout(() => __cv.writeText('.ota/ok', myVersion() || 'ok'), 5000);
  globalThis.__caiDat = back => fadeTo(() => openSettings(back));   // the room's START (game/build_game.py WORDING)
  function drawSettings(now) {
    pickBack();
    ctx.fillStyle = 'rgba(10,6,4,0.45)'; ctx.fillRect(0, 0, 640, 480);
    title('CÀI ĐẶT', 320, 44, 32, '#ffecaa', 5);
    const X = 90, W = 460, Y0 = 88, H = OTA ? 40 : 46, G = OTA ? 7 : 9;
    const ota = OTA ? otaLine(otaState(now)) : null;
    ROWS.forEach(([k, name], i) => {
      const y = Y0 + i * (H + G), on = i === S.cd.sel;
      frameBox(X, y, W, H, on);
      text(name, X + 22, y + H / 2 + 1, 17, on ? '#fff2d8' : '#f0e4ce', 'left', true, 3);
      if (k === 've') return;
      const vx = X + W - 22, cy = y + H / 2 + 1;
      if (k === 'capNhat') return text(ota[0], vx, cy, 15, '#ffe6a8', 'right', true, 3);
      if (LEVEL.has(k)) {
        for (let j = 0; j < 10; j++) {
          ctx.fillStyle = j < CD[k] ? '#ffd36e' : 'rgba(255,255,255,0.15)';
          ctx.fillRect(vx - 214 + j * 16, cy - 8, 12, 16);
        }
        text(CD[k] ? String(CD[k]) : 'Tắt', vx - 30, cy, 15, '#ffe6a8', 'right', true, 2);
      } else text(CD[k] ? '◄ Bật ►' : '◄ Tắt ►', vx, cy, 16, CD[k] ? '#8ce16e' : '#c98a7a', 'right', true, 3);
    });
    if (ota && ROWS[S.cd.sel][0] === 'capNhat') text(ota[1], 320, 436, 14, '#fff2d8', 'center', true, 3);
    text('▲ ▼ chọn · ◄ ► hoặc A: đổi · B: quay lại', 320, 464, 13, '#c9bba8', 'center', false, 3);
  }
  function setPress(btn) {
    const c = S.cd, k = ROWS[c.sel][0];
    if (btn === 'UP' || btn === 'DOWN') { c.sel = (c.sel + (btn === 'UP' ? ROWS.length - 1 : 1)) % ROWS.length; sfx('menu', 160); return; }
    if (btn === 'B' || (k === 've' && (btn === 'A' || btn === 'START'))) {
      sfx('quay-lai', 180); return fadeTo(() => { S.mode = c.back || 'title'; S.cd = null; });
    }
    if (k === 'capNhat') { if (btn === 'A') { sfx('chon', 190); otaPress(performance.now()); } return; }
    if (!['LEFT', 'RIGHT', 'A'].includes(btn) || k === 've') return;
    if (LEVEL.has(k)) {
      const dir = btn === 'LEFT' ? -1 : 1, was = CD[k];
      CD[k] = btn === 'A' ? (CD[k] ? 0 : k === 'nhac' ? 7 : 10) : Math.max(0, Math.min(10, CD[k] + dir));
      if (k === 'tiengNut') sfx('menu', 160);                 // heard at the new loudness
      if (k === 'tiengDong') sfx('vui', 230);
      if (k === 'nhac' && SOUND._vol) SOUND._vol();
      if (k === 'nhac' && !was !== !CD.nhac && SOUND._music) SOUND._music(CD.nhac ? song : '');
    } else CD[k] = !CD[k];
    keep();
    sfx('chon', 190);                                        // heard at the new loudness
  }

  // ---------- back to the title screen from the room ----------
  const PET0 = { ...DATA.pet };                             // a new pet starts from the demo's own (name and all)
  const roomCalm = () => S.mode === 'room' && S.stats === null && S.fade === 0 && S.popupGoal === 0 && S.pickerGoal === 0 &&
    S.popup < 0.05 && S.picker < 0.05 && !(S.truyen && S.truyen.dang) && !S.gemMode;
  function toTitle() {
    S.veChao = null;
    if (typeof __quit === 'function') __quit();               // the save (song-that.js)
    fadeTo(() => {
      for (const k of Object.keys(DATA.pet)) delete DATA.pet[k];
      Object.assign(DATA.pet, PET0);
      S = NEW(); S.titleSel = 1; S.fade = 0.001;               // the fade goes on into the title screen
      if (typeof SOUND === 'object' && SOUND) SOUND.music('');
    });
  }
  function drawAsk() {
    ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fillRect(0, 0, 640, 480);
    frameBox(150, 180, 340, 120, true);
    text('Về màn chào?', 320, 214, 20, '#ffecaa', 'center', true, 3);
    text(`${DATA.pet.name} được lưu lại, chơi tiếp lúc nào cũng được`, 320, 244, 12, '#e0d0b0', 'center', false, 2);
    text('A: về màn chào · B: ở lại', 320, 276, 14, '#f0e4ce', 'center', true, 3);
  }
  const frameR = frame;
  globalThis.frame = function (now) {
    const r = frameR.apply(this, arguments);
    if (S.veChao && S.mode === 'room') drawAsk(); else if (S.veChao) S.veChao = null;
    return r;
  };

  // ---------- the hooks ----------
  const press0 = press;
  globalThis.press = function (btn) {
    if (S.veChao) {                                            // the question takes every button
      if (btn === 'A') toTitle();
      else if (btn === 'B' || btn === 'SELECT') { S.veChao = null; sfx('quay-lai', 180); }
      return;
    }
    if (roomCalm() && btn === 'SELECT') { S.veChao = { t: performance.now() }; return sfx('menu', 160); }
    if (roomCalm() && (btn === 'L1' || btn === 'R1')) return press0('SELECT');   // the stats screen
    if (S.mode === 'title' && S.fade === 0) {
      if (['UP', 'DOWN', 'LEFT', 'RIGHT'].includes(btn)) {
        S.titleSel = (S.titleSel + (btn === 'UP' || btn === 'LEFT' ? CHOICES - 1 : 1)) % CHOICES; quitAsk = -1e9; sfx('menu', 160); return;
      }
      if (btn === 'A' || btn === 'START') {
        if (S.titleSel === 3) {
          const now = performance.now();
          if (now - quitAsk < 3000) return quitGame();
          quitAsk = now; return sfx('menu', 160);
        }
        if (S.titleSel === 2) return fadeTo(openSettings);
        if (S.titleSel === 1) { if (!__luu.any()) return toast('Chưa có pet nào: chọn Chơi mới'); return fadeTo(openList); }
      }
      return press0(btn);
    }
    if (S.mode === 'dsPet' && S.ds) { if (S.fade === 0) listPress(btn); return; }
    if (S.mode === 'caiDat' && S.cd) { if (S.fade === 0) setPress(btn); return; }
    if (S.mode === 'thoat') return;
    return press0(btn);
  };
  const evo0 = drawEvo;
  globalThis.drawEvo = function (now) {
    if (S.mode === 'dsPet' && S.ds) drawList(now);
    else if (S.mode === 'caiDat' && S.cd) drawSettings(now);
    else if (S.mode === 'thoat') return drawBye(now);
    else return evo0(now);
    if (S.toast && now - S.toastT < 1800) {                       // the demo draws toasts only on its own screens
      ctx.fillStyle = 'rgba(18,11,9,0.85)'; ctx.fillRect(140, 220, 360, 40); text(S.toast, 320, 240, 14, '#f0e4ce', 'center');
    }
  };
})();
