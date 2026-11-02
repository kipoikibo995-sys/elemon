// Elemon: Đấu online (the user, 02/11/2026), Võ đường's middle card: "đấu với đội của người khác". Each player uploads their
// team (the pet being raised, then up to two from the other saves: pet, stage, level, six attributes, name); another
// player picks a team of a fitting level, one of its pets, and fights it in a Solo match, the bot at Khó (3) holding
// it, with that pet's stage body and its own attributes (__chiSo.pow with foeA). Wins and losses go to a ranking.
// The server: server/elemon-online (a Cloudflare Worker, its HUONG_DAN.md). Live 1v1 comes later (LOCKSTEP.md).
//
// The network: on the handheld r36s/jsrt.c's __cv.net(id, method, path, body) runs mang.sh (curl, else wget) on a
// thread of its own and this file reads .mang/<id>.st / .res every POLL ms, so a slow wifi never holds a frame;
// in a browser, fetch. No wifi, no server address: a quiet line on the screen, the rest of the game as it is.
//   Võ đường's middle card (game/src/vo-duong.js) opens it · ▲▼ A pick · B back to Võ đường
(() => {
  const SM = globalThis.__soloMatch;
  if (!SM || typeof __soloDraw !== 'function' || typeof __soloPress !== 'function') return;
  const VIEW = 'solo-online';                             // /^solo/: Võ đường hands it to __soloDraw / __soloPress
  const DEV = typeof __cv === 'object' && !!__cv.net;
  const clock = () => (DEV && __cv.clock ? __cv.clock() : Date.now());   // real ms: the harness's frame time runs its own pace
  const POLL = 200, TIMEOUT = 30e3, LEVEL = 3, SOLO_NL = 15, MAX_TEAM = 3;
  const STAGE_NAME = { baby: 'Con', child: 'Nhi', teen: 'Thiếu niên', adult: 'Trưởng thành', legend: 'Huyền thoại' };
  const sfx = (n, v) => { if (typeof SOUND === 'object' && SOUND) SOUND.sfx(n, v); };
  const roster = dir => SM.ROSTER.find(r => r.dir === dir && r.he !== 'hu');

  // ---------- the network ----------
  // -> { st: 'ok', code, data } (the server answered), or st 'net' (no connection), 'url' (no server address in this
  // build), 'none' (this build cannot reach out)
  let seq = 0;
  function ask(method, path, body) {
    if (DEV) return new Promise(done => {
      const id = 'q' + (++seq).toString(36) + Math.floor(Math.random() * 36 ** 6).toString(36);
      if (!__cv.net(id, method, path, body ? JSON.stringify(body) : '')) return done({ st: 'none' });
      const t0 = clock();
      (function poll() {
        const st = __cv.readText(`.mang/${id}.st`);
        if (!st) return clock() - t0 > TIMEOUT ? done({ st: 'net' }) : setTimeout(poll, POLL);
        const [w, code] = st.trim().split(' ');
        if (w !== 'ok') return done({ st: w === 'url' ? 'url' : 'net' });
        let data = null;
        try { data = JSON.parse(__cv.readText(`.mang/${id}.res`) || 'null'); } catch (e) {}
        done({ st: 'ok', code: +code, data });
      })();
    });
    let base = globalThis.__MANG_URL || '';
    try { base = localStorage.getItem('elemon-mang-url') || base; } catch (e) {}
    if (!base || typeof fetch !== 'function') return Promise.resolve({ st: 'url' });
    return fetch(base.replace(/\/$/, '') + path, method === 'POST' ? { method, body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' } } : {})
      .then(r => r.json().catch(() => null).then(data => ({ st: 'ok', code: r.status, data })), () => ({ st: 'net' }));
  }
  const SAY = {
    net: 'Không kết nối được máy chủ. Bật wifi rồi thử lại; không sao, game vẫn chơi bình thường.',
    url: 'Bản game này chưa có địa chỉ máy chủ online.',
    none: 'Máy này chưa chạy được phần online.',
  };
  // a request with the screen's "busy" line, its answer's data (ok) or null (said on the screen)
  function call(method, path, body, busy) {
    if (U.busy) return Promise.resolve(null);
    U.busy = busy; U.msg = ''; U.bad = false;
    return ask(method, path, body).then(r => {
      U.busy = '';
      if (r.st !== 'ok') { U.msg = SAY[r.st] || SAY.net; U.bad = true; return null; }
      if (!r.data || !r.data.ok) { U.msg = (r.data && r.data.msg) || `Máy chủ trả lỗi ${r.code}`; U.bad = true; return null; }
      return r.data;
    });
  }

  // ---------- who this is: an id and a secret key made here once, kept beside the saves ----------
  const ID_FILE = DEV ? __cv.saveDir + '/mang-id.txt' : null;
  const hex = n => { let s = ''; while (s.length < n) s += Math.floor(Math.random() * 65536 ^ (clock() * 7919) & 65535).toString(16).padStart(4, '0'); return s.slice(0, n); };
  let ME = null;
  function me() {
    if (ME) return ME;
    try { ME = JSON.parse(DEV ? __cv.readText(ID_FILE) : localStorage.getItem('elemon-mang-id')); } catch (e) { ME = null; }
    if (!ME || !/^[0-9a-f]{16}$/.test(ME.id) || !/^[0-9a-f]{32}$/.test(ME.key)) {
      ME = { id: hex(16), key: hex(32) };
      const t = JSON.stringify(ME);
      try { if (DEV) __cv.writeText(ID_FILE, t); else localStorage.setItem('elemon-mang-id', t); } catch (e) {}
    }
    return ME;
  }

  // ---------- the team: the pet being raised first, then the other saves' (game/src/song-that.js: __luu) ----------
  const r2 = v => Math.round(v * 100) / 100;
  function team() {
    const out = [];
    if (DATA.pet && roster(DATA.pet.creature))
      out.push({ dir: DATA.pet.creature, ten: DATA.pet.name, stage: S.stage, lv: S.level || 1, attr: __chiSo.attrs().map(r2) });
    const others = typeof __luu === 'object' && __luu ? __luu.list() : [];
    for (const { sv } of others.sort((a, b) => ((b.sv.S || {}).level || 0) - ((a.sv.S || {}).level || 0))) {
      const p = sv.pet || {}, s = sv.S || {};
      if (out.length >= MAX_TEAM) break;
      if (!roster(p.creature) || !Array.isArray(s.attr) || !LV[s.stage]) continue;
      if (DATA.pet && p.creature === DATA.pet.creature && p.name === DATA.pet.name) continue;   // the one being played
      out.push({ dir: p.creature, ten: p.name || 'Pet', stage: s.stage, lv: s.level || 1, attr: s.attr.map(r2) });
    }
    return out;
  }

  // ---------- the screen's state (not in the save: a reload starts it over) ----------
  let U = null, UP = false, RATING = null;              // UP: the team sent in this run (the server takes one each 10 s)
  function open() {
    U = { page: 'menu', sel: 0, busy: '', msg: '', bad: false, rating: RATING, list: [], li: 0, foe: null, pi: 0,
          top: null, ti: 0, res: null, pend: null };
    S.vd = { view: VIEW, sel: 1 };
  }
  const MENU = [['up', 'Tải đội lên'], ['find', 'Tìm đối thủ'], ['top', 'Bảng xếp hạng'], ['wifi', 'Đấu qua wifi'], ['back', 'Quay lại']];   // wifi: dau-wifi.js

  function upload() {
    const t = team();
    if (!t.length) { U.msg = `${DATA.pet.name} chưa vào được Đấu trường online`; U.bad = true; return Promise.resolve(null); }
    return call('POST', '/api/team', { ...me(), name: DATA.pet.name, team: t }, 'Đang tải đội lên…').then(d => {
      if (!d) return null;
      UP = true; U.rating = RATING = d.rating;
      U.msg = `Đã tải đội ${d.team.length} pet lên · điểm ${d.rating}`;
      return d;
    });
  }
  function find() {
    return call('GET', `/api/opponents?id=${me().id}&lv=${S.level || 1}`, null, 'Đang tìm đối thủ…').then(d => {
      if (!d) return;
      if (!d.list.length) { U.msg = 'Chưa có đội nào khác trên máy chủ, thử lại sau'; return; }
      U.list = d.list; U.li = 0; U.page = 'list';
    });
  }
  function ranking() {
    return call('GET', `/api/top?id=${me().id}`, null, 'Đang lấy bảng xếp hạng…').then(d => {
      if (!d) return;
      U.top = d; U.ti = 0; U.page = 'top';
      if (d.me) U.rating = RATING = d.me.rating;
    });
  }
  // a match: asked of the server first (it hands a one-time token), then the arena with the foe's pet
  function fight() {
    const foeTeam = U.foe, p = foeTeam.team[U.pi], mine = roster(DATA.pet.creature), foe = p && roster(p.dir);
    if (!mine) return toast(`${DATA.pet.name} chưa vào được Đấu trường`);
    if (!foe) return toast('Pet này máy bạn chưa có');
    const why = __chiSo.fit(SOLO_NL);
    if (why) return toast(`${DATA.pet.name} chưa đấu được: ${why}, về nghỉ đã`);
    if (globalThis.__SOLO_CUTS && foe.dir === mine.dir) return toast('Chọn pet khác loài với pet của bạn');
    (UP ? Promise.resolve(true) : upload()).then(ok => ok && call('POST', '/api/fight', { ...me(), foe: foeTeam.id, pet: U.pi }, 'Đang mở trận…'))
      .then(d => {
        if (!d) return;
        const pet = d.foe.pet, st = pet.stage === 'baby' ? 'child' : pet.stage;
        if (typeof __vgVs === 'function') __vgVs(mine.dir, foe.dir, 0, 0);
        fadeTo(() => {
          S.vd = { view: 'solo', sel: 1, level: LEVEL, online: { token: d.token, name: d.foe.name, pet } };
          // the foe in its own stage's body (Vùng đất's hooked arena, as the tree does: game/src/cay-dau-truong.js)
          const src = typeof __vgDuelSrc === 'function' && __vgDuelSrc(), plain = globalThis.__SOLO_SRC;
          if (src) { globalThis.__vgBotStage = __soloStage(foe.dir, st); globalThis.__SOLO_SRC = src; }
          try { SM.start(mine, foe, LEVEL); } finally { globalThis.__SOLO_SRC = plain; }
          globalThis.__soloPow = __chiSo.pow(pet.lv, 1, pet.attr);   // after start: the foe as strong as its own numbers
        });
      });
  }
  function sendResult() {
    const p = U.pend;
    if (!p) return;
    call('POST', '/api/result', { ...me(), token: p.token, win: p.win, me: p.me, bot: p.bot }, 'Đang gửi kết quả…').then(d => {
      if (!d) { if (/đã ghi|quá hạn|Không thấy|ngắn quá/.test(U.msg)) U.pend = null; return; }
      U.pend = null; U.rating = RATING = d.rating;
      U.res = { ...U.res, delta: d.delta, rating: d.rating };
      U.msg = '';
    });
  }

  // ---------- drawing ----------
  let back = null;
  function backdrop() {                                   // the dusk menu backdrop, dimmed, made once
    if (back) return back;
    const im = IMG['nen-menu_hoang-hon'];
    if (!im) return null;
    const c = document.createElement('canvas'); c.width = 640; c.height = 480;
    const g = c.getContext('2d'), k = Math.max(640 / im.width, 480 / im.height), w = Math.round(im.width * k), h = Math.round(im.height * k);
    g.fillStyle = '#1a120c'; g.fillRect(0, 0, 640, 480);
    g.drawImage(im, Math.round((640 - w) / 2), Math.round((480 - h) / 2), w, h);
    g.fillStyle = 'rgba(16,10,6,0.62)'; g.fillRect(0, 0, 640, 480);
    if (typeof __cv === 'object' && __cv.seal) __cv.seal(c.__id);
    return (back = c);
  }
  const PICS = {};
  function pic(dir) {                                     // img/solo/<dir>.png, the pick screen's small picture
    let im = PICS[dir];
    if (!im) { im = PICS[dir] = new Image(); im.onload = () => { im.__ok = true; }; im.src = `img/solo/${dir}.png`; }
    return im.__ok ? im : null;
  }
  function box(x, y, w, h, on) {
    ctx.fillStyle = on ? 'rgba(255,214,110,0.26)' : 'rgba(0,0,0,0.42)'; ctx.fillRect(x, y, w, h);
    ctx.strokeStyle = on ? '#ffd36e' : 'rgba(255,214,110,0.30)'; ctx.lineWidth = on ? 3 : 1; ctx.strokeRect(x, y, w, h);
  }
  const petLine = p => `${p.ten} · ${(roster(p.dir) || {}).name || p.dir} ${STAGE_NAME[p.stage] || ''} Lv${p.lv}`;
  function drawMenu(now) {
    const t = team();
    text(t.length ? `Đội của bạn: ${t.map(p => `${p.ten} Lv${p.lv}`).join(' · ')}` : 'Pet của bạn chưa vào được Đấu trường online',
         320, 82, 13, '#e0cfb0', 'center', false, 3);
    MENU.forEach(([k, name], i) => {
      const y = 100 + i * 60, on = i === U.sel;
      box(170, y, 300, 48, on);
      text(name, 320, y + 25, 18, on ? '#fff2d8' : '#f0e4ce', 'center', true, 3);
    });
    text('▲▼ chọn · A: vào · B: về Võ đường', 320, 438, 12, '#e0cfb0', 'center', false, 3);
  }
  function drawList() {
    text('Chọn một đội để đấu (bot mức Khó cầm đội đó)', 320, 82, 13, '#e0cfb0', 'center', false, 3);
    U.list.forEach((o, i) => {
      const y = 98 + i * 54, on = i === U.li;
      box(40, y, 560, 48, on);
      text(`${o.name}`, 56, y + 17, 15, on ? '#fff2d8' : '#f0e4ce', 'left', true, 3);
      text(`Lv${o.level} · Lực ${o.luc} · ${o.rating} điểm`, 584, y + 17, 13, '#ffe6a8', 'right', true, 2);
      text(o.team.map(p => `${(roster(p.dir) || {}).name || p.dir} Lv${p.lv}`).join(' · '), 56, y + 36, 11, '#cdbb9c', 'left', false, 2);
    });
    text('▲▼ chọn · A: xem đội · B: quay lại', 320, 438, 12, '#e0cfb0', 'center', false, 3);
  }
  function drawFoe(now) {
    const o = U.foe;
    text(`${o.name} · ${o.rating} điểm · thắng ${o.wins} / thua ${o.losses}`, 320, 82, 14, '#ffe6a8', 'center', true, 3);
    const n = o.team.length, W = 180, x0 = 320 - (n * W + (n - 1) * 14) / 2;
    o.team.forEach((p, i) => {
      const x = x0 + i * (W + 14), on = i === U.pi, cx = x + W / 2;
      box(x, 100, W, 250, on);
      const im = pic(p.dir);
      if (im) fit(im, cx, 180 + (on ? Math.round(Math.sin(now / 300) * 4) : 0), 130, 120, 0);
      text(p.ten, cx, 268, 15, on ? '#fff2d8' : '#f0e4ce', 'center', true, 3);
      text(`${(roster(p.dir) || {}).name || p.dir}`, cx, 288, 12, '#e0cfb0', 'center', false, 2);
      text(`${STAGE_NAME[p.stage] || ''} Lv${p.lv}`, cx, 306, 12, '#e0cfb0', 'center', false, 2);
      text(`Lực chiến ${p.luc}`, cx, 328, 13, '#ffd36e', 'center', true, 2);
    });
    const mine = __chiSo.luc(__chiSo.pet());
    text(`${DATA.pet.name} Lv${S.level || 1} · Lực chiến ${mine}`, 320, 376, 13, '#9fd8ff', 'center', true, 3);
    const why = __chiSo.fit(SOLO_NL);
    if (why) text(`Chưa đấu được: ${why}`, 320, 396, 12, '#ff8a7a', 'center', true, 3);
    text(`${n > 1 ? '◀▶ chọn pet · ' : ''}A: đấu (bot Khó) · B: quay lại`, 320, 438, 12, '#e0cfb0', 'center', false, 3);
  }
  function drawTop() {
    const d = U.top, rows = d.top.slice(U.ti, U.ti + 9);
    text(`${d.players} người chơi`, 320, 82, 13, '#e0cfb0', 'center', false, 3);
    rows.forEach((r, k) => {
      const y = 96 + k * 32;
      ctx.fillStyle = r.mine ? 'rgba(120,200,255,0.25)' : k % 2 ? 'rgba(0,0,0,0.25)' : 'rgba(0,0,0,0.40)'; ctx.fillRect(60, y, 520, 28);
      text(`${r.rank}`, 92, y + 15, 14, r.rank <= 3 ? '#ffd36e' : '#f0e4ce', 'right', true, 2);
      text(r.name, 108, y + 15, 14, '#fff2d8', 'left', true, 2);
      text(`Lv${r.level}`, 380, y + 15, 12, '#e0cfb0', 'right', false, 2);
      text(`${r.wins}-${r.losses}`, 470, y + 15, 12, '#e0cfb0', 'right', false, 2);
      text(`${r.rating}`, 566, y + 15, 14, '#ffe6a8', 'right', true, 2);
    });
    text(d.me ? `Bạn: hạng ${d.me.rank} · ${d.me.rating} điểm · thắng ${d.me.wins} / thua ${d.me.losses}` : 'Bạn chưa tải đội lên',
         320, 400, 14, '#9fd8ff', 'center', true, 3);
    text(`${d.top.length > 9 ? '▲▼ cuộn · ' : ''}B: quay lại`, 320, 438, 12, '#e0cfb0', 'center', false, 3);
  }
  function drawResult() {
    const r = U.res;
    title(r.win ? 'THẮNG!' : 'THUA', 320, 170, 32, r.win ? '#ffd36e' : '#c9a08a', 5);
    text(`${r.score} trước ${r.pet.ten} của ${r.name}`, 320, 214, 15, '#fff2d8', 'center', true, 3);
    if (r.delta !== undefined) text(`Điểm ${r.delta >= 0 ? '+' : ''}${r.delta} → ${r.rating}`, 320, 246, 16, '#ffe6a8', 'center', true, 3);
    text(U.pend ? 'A: gửi lại kết quả · B: về danh sách' : 'A / B: về danh sách', 320, 438, 12, '#e0cfb0', 'center', false, 3);
  }
  function draw(now) {
    if (!U) open();
    const b = backdrop();
    if (b) ctx.drawImage(b, 0, 0); else { ctx.fillStyle = '#1a120c'; ctx.fillRect(0, 0, 640, 480); }
    title('ĐẤU ONLINE', 320, 36, 24, '#ffe6a8', 4);
    text(U.rating === null ? 'Đấu với đội của người khác' : `Điểm của bạn: ${U.rating}`, 320, 60, 13, '#cfe8b0', 'center', false, 3);
    ({ menu: drawMenu, list: drawList, foe: drawFoe, top: drawTop, result: drawResult })[U.page](now);
    const line = U.busy ? U.busy + '.'.repeat(Math.floor(now / 300) % 4) : U.msg;
    if (line) {
      ctx.fillStyle = 'rgba(14,9,7,0.85)'; ctx.fillRect(0, 452, 640, 28);
      text(line, 320, 466, 12, U.busy ? '#fff2d8' : U.bad ? '#ffb08a' : '#cfe8b0', 'center', true, 2);
    }
  }

  // ---------- buttons ----------
  function press(btn) {
    if (S.fade > 0) return;
    const P = U.page, step = d => sfx('menu', 160) || d;
    if (btn === 'B') {
      sfx('quay-lai', 180);
      if (U.busy) return;                                  // a request on its way: wait for it (it is never long)
      if (P === 'menu') return fadeTo(() => { U = null; S.vd = { view: 'menu', sel: typeof __vdCard === 'function' ? __vdCard('online') : 1 }; });
      U.msg = ''; U.page = P === 'foe' ? 'list' : P === 'result' ? (U.list.length ? 'list' : 'menu') : 'menu';
      return;
    }
    if (U.busy) return;
    if (P === 'menu') {
      if (btn === 'UP') U.sel = step((U.sel + MENU.length - 1) % MENU.length);
      if (btn === 'DOWN') U.sel = step((U.sel + 1) % MENU.length);
      if (btn === 'A') {
        const k = MENU[U.sel][0];
        sfx('menu', 200);
        if (k === 'up') upload(); else if (k === 'find') find(); else if (k === 'top') ranking();
        else if (k === 'wifi') { if (typeof __dauWifi === 'function') __dauWifi(); }
        else fadeTo(() => { U = null; S.vd = { view: 'menu', sel: typeof __vdCard === 'function' ? __vdCard('online') : 1 }; });
      }
    } else if (P === 'list') {
      if (btn === 'UP') U.li = step((U.li + U.list.length - 1) % U.list.length);
      if (btn === 'DOWN') U.li = step((U.li + 1) % U.list.length);
      if (btn === 'A') { U.foe = U.list[U.li]; U.pi = 0; U.page = 'foe'; sfx('menu', 200); }
    } else if (P === 'foe') {
      const n = U.foe.team.length;
      if (btn === 'LEFT') U.pi = step((U.pi + n - 1) % n);
      if (btn === 'RIGHT') U.pi = step((U.pi + 1) % n);
      if (btn === 'A') fight();
    } else if (P === 'top') {
      const n = U.top.top.length;
      if (btn === 'UP') U.ti = Math.max(0, U.ti - 1);
      if (btn === 'DOWN') U.ti = Math.max(0, Math.min(n - 9, U.ti + 1));
    } else if (P === 'result') {
      if (btn === 'A') { if (U.pend) sendResult(); else { U.page = U.list.length ? 'list' : 'menu'; U.msg = ''; } }
    }
  }

  // ---------- the hooks ----------
  globalThis.__dauOnline = () => fadeTo(open);
  globalThis.__dauOnlineTest = { ask, team, me, state: () => U };   // tests (build/qjs-host)
  const draw0 = __soloDraw;
  globalThis.__soloDraw = now => {
    const v = S.vd;
    if (v && v.view === VIEW) return draw(now);
    // an online match is one match: the arena's START (a rematch) never reaches it, so a lost one cannot be played
    // again until won before the result is sent
    if (v && v.view === 'solo' && v.online && typeof HELD === 'object' && HELD) HELD.START = false;
    draw0(now);
  };
  const press0 = __soloPress;
  globalThis.__soloPress = btn => {
    const v = S.vd;
    if (v && v.view === VIEW) return press(btn);
    // an online match left: its result to the server (a match left before it started counts for nothing; one left
    // part-way is lost), then the online screen again with how it went
    const on = v && v.view === 'solo' && v.online;
    if (on && btn === 'SELECT') {
      const info = typeof __soloInfo === 'function' && __soloInfo(), fought = !!(info && info.started);
      const sc = globalThis.__soloSeen && __soloSeen.score, win = !!sc && sc.me > sc.bot;
      const r = press0(btn), cb = fadeCb;
      globalThis.__vgBotStage = null;
      if (!U) open();
      fadeCb = () => {
        if (cb) cb();
        S.vd = { view: VIEW, sel: 1 };
        if (!fought) { U.page = 'foe'; return; }
        U.res = { win, score: sc ? `${sc.me}-${sc.bot}` : '', pet: on.pet, name: on.name };
        U.pend = { token: on.token, win, me: sc ? sc.me : 0, bot: sc ? sc.bot : 0 };
        U.page = 'result';
        sendResult();
      };
      return r;
    }
    return press0(btn);
  };
})();
