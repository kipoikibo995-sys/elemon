// Elemon: Đấu qua wifi (the user, 02/11/2026), in Võ đường → Đấu online: two handhelds on the same wifi fight each
// other in the Solo arena. No server: one makes a room, the other finds it (a broadcast on the network, or its IP typed
// in), and from then on they send each other only their buttons (UDP, r36s/jsrt.c udpOpen/udpSend/udpRecv).
//
// Lockstep: the match runs in fixed ticks of TICK ms (30 a second), the same on both handhelds. The buttons pressed at
// tick n count at tick n + DELAY, sent with the last few ticks' so a lost packet is covered by the next; a tick runs only
// once both sides' buttons for it are in. Everything the arena draws by chance comes from one seeded generator (the
// room's seed) while a tick runs, its clock is the tick's, and the room maker is the left fighter (P), the one who
// joins the right one (B, the bot's place: its brain is swapped for the other player's buttons, LAN_HOOKS). Both
// fight in their Nhi body, their strength from their own six attributes (the same __soloPow on both). Best of three.
// Every HASH_EVERY ticks each side sends where the fighters are; a difference is logged ("wifi: LỆCH") and marked.
// Notes on what makes a match differ between runs: LOCKSTEP.md.
(() => {
  const SM = globalThis.__soloMatch;
  if (!SM || typeof __soloDraw !== 'function' || typeof __soloPress !== 'function') return;
  const VIEW = 'solo-wifi';
  const NET = typeof __cv === 'object' && !!__cv.udpOpen;
  const PORT = 47777, VER = 1, TICK = 1000 / 30, DELAY = 3, SEND_BACK = 12, HASH_EVERY = 30;
  const WAIT_SAY = 1500, WAIT_GIVEUP = 15000, WAIT_LOAD = 60000, FIND_EVERY = 1000, JOIN_EVERY = 400, ROOM_AGE = 4000, WIN = 2, NEXT_ROUND = 90;
  const BIT = { UP: 1, DOWN: 2, LEFT: 4, RIGHT: 8, A: 16, B: 32, X: 64, Y: 128, R1: 256, L1: 512 };
  const P_KEY = [['UP', 'ArrowUp'], ['DOWN', 'ArrowDown'], ['LEFT', 'ArrowLeft'], ['RIGHT', 'ArrowRight'],
                 ['A', 'j'], ['B', 'k'], ['X', 'l'], ['Y', 'i']];
  const ACT = [['A', 'j'], ['B', 'k'], ['X', 'l'], ['Y', 'i']];
  const DASH = BIT.R1 | BIT.L1;
  const clock = () => (NET && __cv.clock ? __cv.clock() : performance.now());
  const sfx = (n, v) => { if (typeof SOUND === 'object' && SOUND) SOUND.sfx(n, v); };
  const log = s => console.log('wifi: ' + s);
  const roster = dir => SM.ROSTER.find(r => r.dir === dir && r.he !== 'hu');
  const version = () => { const t = NET && __cv.readText('files.txt'); const m = t && /^#version (\S+)/m.exec(t); return m ? m[1] : 'dev'; };

  // ---------- the arena, hooked for two players (on top of chi-so.js's and solo.js's hooks) ----------
  const LAN_HOOKS = [
    ['  if (dt) think();', '  if (dt) { if (globalThis.__lanB) __lanB(B, press, release, live); else think(); }'],
    ['const sp = (f.bot ? LEVELS[level].speed : SPEED)', 'const sp = (f.bot && !globalThis.__lanB ? LEVELS[level].speed : SPEED)'],
    ['if (l && !f.act && !f.bot) f.ang = Math.atan2(f.my, f.mx);', 'if (l && !f.act && (!f.bot || globalThis.__lanB)) f.ang = Math.atan2(f.my, f.mx);'],
    ['  if (f.bot) { a.ang = a.base; a.t0 = now; }', '  if (f.bot && !globalThis.__lanB) { a.ang = a.base; a.t0 = now; }'],
    ['  if (!f.bot && Math.abs(((a.ang - at)', '  if ((!f.bot || globalThis.__lanB) && Math.abs(((a.ang - at)'],
    ['  if (f.bot) { const r = Math.min(RANGE.i', '  if (f.bot && !globalThis.__lanB) { const r = Math.min(RANGE.i'],
    ['f.dashAng = f.bot ? f.dashAng : f.ang;', 'f.dashAng = f.bot && !globalThis.__lanB ? f.dashAng : f.ang;'],
    ['  SAN = pool[Math.floor(Math.random() * pool.length)];',
     '  SAN = pool[globalThis.__lanSan !== undefined && globalThis.__lanSan !== null ? __lanSan % pool.length : Math.floor(Math.random() * pool.length)];'],
    ["    center(over.winner === P ? 'THẮNG!' : 'THUA!', 250, 44, over.winner === P ? '#ffe08a' : '#8fd8ff');",
     "    { const w = (over.winner === P) !== !!globalThis.__lanFlip; center(w ? 'THẮNG!' : 'THUA!', 250, 44, w ? '#ffe08a' : '#8fd8ff'); }"],
    ["    center('Enter: đấu lại · 0/1/2/3: Tập/Dễ/Vừa/Khó', 290, 14, '#ddd');",
     "    if (!globalThis.__lanB) center('Enter: đấu lại · 0/1/2/3: Tập/Dễ/Vừa/Khó', 290, 14, '#ddd');"],
  ];
  const RAW = globalThis.__SOLO_SRC;
  let LAN_SRC;
  function lanSrc() {
    if (LAN_SRC !== undefined) return LAN_SRC;
    LAN_SRC = null;
    try {
      let src = String(RAW);
      if (typeof __soloBodySrc === 'function') src = __soloBodySrc(src);
      if (typeof __chiSoSrc === 'function') src = __chiSoSrc(src);
      const miss = LAN_HOOKS.filter(([a]) => !src.includes(a));
      if (miss.length) { log('the arena has changed, no hook at: ' + miss.map(([a]) => a.slice(0, 40)).join(' | ')); return null; }
      for (const [a, b] of LAN_HOOKS) src = src.replace(a, b);
      LAN_SRC = (0, eval)('(' + src + ')');
    } catch (e) { log('hooked arena: ' + e); }
    return LAN_SRC;
  }

  // the other player's buttons for B, inside the arena's frame (the think() hook)
  let bNow = 0, bPrev = 0;
  function lanB(B, press, release, live) {
    const b = bNow, was = bPrev, down = b & ~was, up = was & ~b;
    bPrev = b;
    const on = live();
    B.mx = on ? (b & BIT.RIGHT ? 1 : 0) - (b & BIT.LEFT ? 1 : 0) : 0;
    B.my = on ? (b & BIT.DOWN ? 1 : 0) - (b & BIT.UP ? 1 : 0) : 0;
    for (const [n, k] of ACT) { if (down & BIT[n]) press(B, k); if (up & BIT[n]) release(B, k); }
    if (b & DASH && !(was & DASH)) press(B, 'shift');
    if (!(b & DASH) && was & DASH) release(B, 'shift');
  }
  // a seeded generator (mulberry32): the arena's every Math.random while a tick runs
  function rngOf(seed) {
    let a = seed | 0;
    return () => { a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  }
  const heldBits = () => {
    let b = 0;
    if (typeof HELD === 'object' && HELD) for (const n in BIT) if (HELD[n]) b |= BIT[n];
    return b;
  };

  // ---------- the network ----------
  const send = (to, o) => NET && to && __cv.udpSend(to.ip, to.port, JSON.stringify(o));
  function recv() {
    if (!NET) return [];
    const out = [];
    for (const [ip, port, text] of __cv.udpRecv()) { try { out.push({ ip, port, m: JSON.parse(text) }); } catch (e) {} }
    return out;
  }
  // the pet that fights: the one being raised (dau-online.js's team, or worked out here)
  function myPet() {
    const st = (S.stage || 'child').replace(/4$/, '');
    return { dir: DATA.pet.creature, ten: DATA.pet.name, stage: st, lv: S.level || 1, attr: __chiSo.attrs().map(v => Math.round(v * 100) / 100) };
  }
  const lucOf = p => __chiSo.luc(__chiSo.of(p.lv, p.attr));
  function powOf(left, right) {                          // the left fighter's (P's) damage ratio and the right one's
    const r = lucOf(left) / Math.max(1, lucOf(right)), c = v => Math.max(1 / 1.5, Math.min(1.5, v));
    return { me: c(r), foe: c(1 / r), hp0: 1, luc: lucOf(left), lucFoe: lucOf(right) };
  }

  // ---------- the lobby ----------
  let W = null;                                          // the screens' state
  let L = null;                                          // the match's
  function open() {
    W = { page: 'menu', sel: 0, msg: '', bad: false, rooms: [], ri: 0, ip: null, lastFind: 0, peer: null, joinT: 0, res: null, sock: false };
    S.vd = { view: VIEW, sel: 1 };
  }
  const MENU = [['host', 'Tạo phòng'], ['find', 'Tìm phòng'], ['back', 'Quay lại']];
  function sock(port) {
    if (!NET) { W.msg = 'Đấu qua wifi chỉ có trên máy chơi game (R36S, Brick)'; W.bad = true; return false; }
    if (!__cv.udpOpen(port)) { W.msg = port ? 'Không mở được phòng (cổng mạng đang bận), thử lại' : 'Không mở được mạng'; W.bad = true; return false; }
    W.sock = true; W.myIp = __cv.myIp();
    if (!W.myIp) { W.msg = 'Máy chưa vào wifi. Bật wifi rồi thử lại.'; W.bad = true; }
    return true;
  }
  function closeSock() { if (NET && W && W.sock) { __cv.udpClose(); W.sock = false; } }
  function hostRoom() {
    if (!roster(DATA.pet.creature)) { W.msg = `${DATA.pet.name} chưa vào được sân đấu`; W.bad = true; return; }
    if (!sock(PORT)) return;
    W.page = 'host'; W.msg = ''; W.bad = false;
    log(`room open on ${W.myIp}:${PORT}`);
  }
  function findRooms() {
    if (!sock(0)) return;
    W.page = 'find'; W.rooms = []; W.ri = 0; W.msg = ''; W.bad = false; W.lastFind = 0;
    const ip = W.myIp || '192.168.1.2';
    W.ip = ip.split('.').map(Number);
  }
  function join(ip) {
    W.peer = { ip, port: PORT }; W.joinT = 0; W.page = 'joining'; W.joinStart = clock();
    log(`joining ${ip}`);
  }
  // what came in, for the lobby
  function lobbyNet() {
    const now = clock();
    for (const { ip, port, m } of recv()) {
      if (W.page === 'host') {
        if (m.t === 'tim') send({ ip, port }, { t: 'phong', v: VER, ver: version(), ten: DATA.pet.name, pet: DATA.pet.creature, lv: S.level || 1 });
        if (m.t === 'vao') hostAccept({ ip, port }, m);
      } else if (W.page === 'find') {
        if (m.t === 'phong') {
          const r = W.rooms.find(q => q.ip === ip);
          if (r) Object.assign(r, m, { seen: now }); else W.rooms.push({ ip, port, ...m, seen: now });
        }
      } else if (W.page === 'joining') {
        if (m.t === 'bat') return guestStart({ ip, port }, m);
        if (m.t === 'het') { W.page = 'find'; W.msg = m.msg || 'Phòng không nhận'; W.bad = true; }
      }
    }
    if (W.page === 'find') {
      if (now - W.lastFind > FIND_EVERY) { W.lastFind = now; send({ ip: '*', port: PORT }, { t: 'tim', v: VER }); }
      W.rooms = W.rooms.filter(r => now - r.seen < ROOM_AGE);
      if (W.ri > W.rooms.length) W.ri = W.rooms.length;
    }
    if (W.page === 'joining') {
      if (now - W.joinT > JOIN_EVERY) { W.joinT = now; send(W.peer, { t: 'vao', v: VER, ver: version(), pet: myPet() }); }
      if (now - W.joinStart > 20000) { W.page = 'find'; W.msg = 'Không vào được phòng. Hai máy phải cùng một wifi.'; W.bad = true; }
    }
  }
  function hostAccept(peer, m) {
    const g = m.pet, mine = myPet();
    const no = msg => { send(peer, { t: 'het', msg }); log('refused: ' + msg); };
    if (m.v !== VER) return no('Hai máy khác phiên bản game, cập nhật cả hai');
    if (m.ver !== version()) return no(`Hai máy khác bản game (${version()} và ${m.ver}), cập nhật cả hai`);
    if (!g || !roster(g.dir) || !Array.isArray(g.attr)) return no('Pet của máy kia chưa vào được sân đấu');
    if (globalThis.__SOLO_CUTS && g.dir === mine.dir) return no('Hai pet trùng loài: chọn pet khác');
    const seed = (Math.random() * 2147483647) | 1, san = Math.floor(Math.random() * 1000);
    const bat = { t: 'bat', v: VER, seed, san, left: mine, right: g, pow: powOf(mine, g) };
    log(`${g.ten} (${g.dir}) joined from ${peer.ip}:${peer.port}`);
    send(peer, bat); send(peer, bat);                    // again from the match until the other side is heard
    begin({ host: true, peer, bat });
  }
  function guestStart(peer, bat) {
    log(`room ${peer.ip} starts: seed ${bat.seed}`);
    begin({ host: false, peer, bat });
  }

  // ---------- the match ----------
  function begin({ host, peer, bat }) {
    const left = roster(bat.left.dir), right = roster(bat.right.dir), src = lanSrc();
    if (!left || !right || !src) { W.msg = 'Không mở được sân đấu'; W.bad = true; W.page = 'menu'; return; }
    L = { host, me: host ? 0 : 1, peer, bat, tick: 0, acc: 0, last: null, inp: [{}, {}], pPrev: 0, over: -1, hash: {}, theirs: {},
          lastSend: 0, waitFrom: 0, waiting: false, desync: 0, gone: '', done: false, rng: rngOf(bat.seed), heard: false, heardN: false };
    for (let n = 0; n < DELAY; n++) { L.inp[0][n] = 0; L.inp[1][n] = 0; }
    bNow = 0; bPrev = 0;
    W.page = 'match';
    if (typeof __vgVs === 'function') __vgVs(left.dir, right.dir, 0, 0);
    fadeTo(() => {
      S.vd = { view: 'solo', sel: 1, level: 3, lan: true, quiet: false };
      globalThis.__lanSan = bat.san; globalThis.__lanFlip = !host; globalThis.__vgBotStage = null;
      const plain = globalThis.__SOLO_SRC;
      globalThis.__SOLO_SRC = src;
      try { SM.start(left, right, 3, { meStage: 'child', drive }); } finally { globalThis.__SOLO_SRC = plain; }
      globalThis.__soloPow = bat.pow;
    });
  }
  function sendInputs(force) {
    const now = clock();
    if (!force && now - L.lastSend < 30) return;
    L.lastSend = now;
    const mine = L.inp[L.me], top = L.tick + DELAY, a = Math.max(0, top - SEND_BACK), k = [];
    for (let n = a; n < top; n++) k.push(mine[n] || 0);
    send(L.peer, { t: 'n', a, k });
    if (L.host && !L.heard) send(L.peer, L.bat);         // until the other side is heard: the room's start again
  }
  function matchNet() {
    for (const { ip, m } of recv()) {
      if (ip !== L.peer.ip) continue;
      if (m.t === 'n') {
        L.heard = true; L.heardN = true;
        const them = L.inp[1 - L.me];
        m.k.forEach((b, i) => { if (them[m.a + i] === undefined) them[m.a + i] = b; });
      } else if (m.t === 'h') {
        if (L.hash[m.n] !== undefined) check(m.n, m.h); else L.theirs[m.n] = m.h;
      } else if (m.t === 'bye') { L.gone = 'Đối thủ đã rời trận'; log('the other side left'); }
      else if (m.t === 'vao' && L.host) send(L.peer, L.bat);   // its 'vao' crossed our start: say it again
    }
  }
  function check(n, h) {
    if (L.hash[n] === h) return;
    L.desync++;
    log(`LỆCH at tick ${n}: ${L.hash[n]} / ${h}`);
  }
  function stateHash() {
    const s = globalThis.__soloSeen, P = s && s.P(), B = s && s.B(), r = v => Math.round(v * 10);
    if (!P || !B) return '-';
    return [r(P.x), r(P.y), r(P.hp), r(B.x), r(B.y), r(B.hp), s.score.me, s.score.bot].join(',');
  }
  // one tick of the arena: P's keys as events, B's through the think() hook, the tick's clock, the seeded chance
  function stepTick(arena, n) {
    const pb = L.inp[0][n], bb = L.inp[1][n], ev = (type, k) => { for (const fn of arena.keyFns[type]) fn({ key: k, preventDefault() {} }); };
    const r0 = Math.random;
    Math.random = L.rng;
    globalThis.__lanB = lanB;
    try {
      const down = pb & ~L.pPrev, up = L.pPrev & ~pb;
      for (const [b, k] of P_KEY) { if (down & BIT[b]) ev('keydown', k); if (up & BIT[b]) ev('keyup', k); }
      if (down & DASH && !(L.pPrev & DASH)) ev('keydown', 'Shift');
      if (up & DASH && !(pb & DASH)) ev('keyup', 'Shift');
      L.pPrev = pb;
      bNow = bb;
      // a round over: the next one starts by itself after NEXT_ROUND ticks, until one side has WIN rounds
      const seen = globalThis.__soloSeen, over = seen && seen.over(), sc = seen && seen.score;
      if (over && L.over < 0) L.over = n;
      if (!over) L.over = -1;
      if (over && sc && Math.max(sc.me, sc.bot) < WIN && n - L.over === NEXT_ROUND) { ev('keydown', 'Enter'); ev('keyup', 'Enter'); }
      if (over && sc && Math.max(sc.me, sc.bot) >= WIN) L.done = true;
      const cbs = arena.rafs.splice(0);
      for (const fn of cbs) try { fn(1000 + n * TICK); } catch (e) { log('arena: ' + (e && e.stack || e)); }
    } finally { Math.random = r0; }
    if (n % HASH_EVERY === 0) {
      const h = stateHash();
      L.hash[n] = h;
      send(L.peer, { t: 'h', n, h });
      if (L.theirs[n] !== undefined) check(n, L.theirs[n]);
      log(`h ${n} ${h}`);
    }
  }
  function drive(arena) {
    matchNet();
    const now = performance.now();
    if (L.last === null) L.last = now;
    L.acc = Math.min(L.acc + now - L.last, 4 * TICK); L.last = now;
    let ran = 0;
    while (L.acc >= TICK && ran < 2) {
      const n = L.tick;
      if (L.inp[1 - L.me][n] === undefined) {
        if (!L.waiting) { L.waiting = true; L.waitFrom = clock(); }
        break;
      }
      L.waiting = false;
      L.inp[L.me][n + DELAY] = L.gone || L.done ? 0 : heldBits();
      stepTick(arena, n);
      L.tick++; L.acc -= TICK; ran++;
      sendInputs(true);
    }
    if (!ran) {
      sendInputs(false);
      // before its first buttons the other side may still be loading the arena (an R36S takes a while)
      if (L.waiting && !L.gone && clock() - L.waitFrom > (L.heardN ? WAIT_GIVEUP : WAIT_LOAD)) { L.gone = 'Mất kết nối với máy kia'; log('lost the other side'); }
    }
  }
  function leave() {
    if (!L) return;
    for (let i = 0; i < 3; i++) send(L.peer, { t: 'bye' });
    const sc = globalThis.__soloSeen && __soloSeen.score, mine = sc ? (L.host ? sc.me : sc.bot) : 0, theirs = sc ? (L.host ? sc.bot : sc.me) : 0;
    W.res = { mine, theirs, them: L.host ? L.bat.right : L.bat.left, gone: L.gone, desync: L.desync, ticks: L.tick };
    log(`left at tick ${L.tick}: ${mine}-${theirs}, ${L.desync} differences`);
    globalThis.__lanB = null; globalThis.__lanSan = null; globalThis.__lanFlip = null; globalThis.__soloPow = null;
    L = null;
    SM.stop();
    closeSock();
    fadeTo(() => { S.vd = { view: VIEW, sel: 1 }; W.page = 'result'; });
  }

  // ---------- drawing ----------
  function box(x, y, w, h, on) {
    ctx.fillStyle = on ? 'rgba(255,214,110,0.26)' : 'rgba(0,0,0,0.42)'; ctx.fillRect(x, y, w, h);
    ctx.strokeStyle = on ? '#ffd36e' : 'rgba(255,214,110,0.30)'; ctx.lineWidth = on ? 3 : 1; ctx.strokeRect(x, y, w, h);
  }
  const petName = p => `${p.ten} (${(roster(p.dir || p.pet) || {}).name || p.dir || p.pet})`;
  function drawLobby(now) {
    ctx.fillStyle = '#1a120c'; ctx.fillRect(0, 0, 640, 480);
    const bg = IMG['nen-menu_troi-dem'];
    if (bg) { ctx.globalAlpha = 0.45; ctx.drawImage(bg, 0, 0, 640, 480); ctx.globalAlpha = 1; }
    title('ĐẤU QUA WIFI', 320, 36, 24, '#ffe6a8', 4);
    text('Hai máy cùng một mạng wifi đánh với nhau', 320, 60, 13, '#cfe8b0', 'center', false, 3);
    if (W.myIp) text(`IP máy này: ${W.myIp}`, 320, 80, 12, '#9fd8ff', 'center', false, 2);
    const P = W.page, dots = '.'.repeat(Math.floor(now / 300) % 4);
    if (P === 'menu') {
      MENU.forEach(([k, name], i) => { const y = 120 + i * 64; box(170, y, 300, 50, i === W.sel); text(name, 320, y + 26, 18, '#fff2d8', 'center', true, 3); });
      text('Một máy Tạo phòng, máy kia Tìm phòng. Hai pet đánh bằng thân Nhi, mạnh theo chỉ số.', 320, 340, 12, '#e0cfb0', 'center', false, 3);
      text('▲▼ chọn · A: vào · B: quay lại', 320, 438, 12, '#e0cfb0', 'center', false, 3);
    } else if (P === 'host') {
      text(`Phòng của ${DATA.pet.name} đang mở${dots}`, 320, 170, 18, '#fff2d8', 'center', true, 3);
      text('Máy kia vào Đấu qua wifi → Tìm phòng', 320, 204, 14, '#e0cfb0', 'center', false, 3);
      if (W.myIp) text(`hoặc nhập IP: ${W.myIp}`, 320, 228, 14, '#9fd8ff', 'center', true, 3);
      text('B: đóng phòng', 320, 438, 12, '#e0cfb0', 'center', false, 3);
    } else if (P === 'find') {
      text(`Đang tìm phòng trong mạng wifi${dots}`, 320, 108, 14, '#fff2d8', 'center', true, 3);
      const rows = [...W.rooms.map(r => ({ r })), { ip: true }];
      rows.forEach((row, i) => {
        const y = 124 + i * 50, on = i === W.ri;
        box(80, y, 480, 42, on);
        if (row.r) {
          text(`Phòng của ${row.r.ten}`, 96, y + 15, 15, '#fff2d8', 'left', true, 3);
          text(`${(roster(row.r.pet) || {}).name || row.r.pet} Lv${row.r.lv} · ${row.r.ip}`, 96, y + 32, 11, '#cdbb9c', 'left', false, 2);
        } else {
          const ip = W.ip.join('.');
          text(`Nhập IP chủ phòng: ${ip}`, 96, y + 21, 15, '#9fd8ff', 'left', true, 3);
          if (on) text('◀▶ ±1 · L1 R1 ±10', 544, y + 21, 11, '#cdbb9c', 'right', false, 2);
        }
      });
      if (!W.rooms.length) text('Chưa thấy phòng nào: chờ chút, hoặc nhập IP máy chủ phòng', 320, 420, 12, '#e0cfb0', 'center', false, 3);
      text('▲▼ chọn · A: vào phòng · B: quay lại', 320, 438, 12, '#e0cfb0', 'center', false, 3);
    } else if (P === 'joining') {
      text(`Đang vào phòng ${W.peer.ip}${dots}`, 320, 200, 18, '#fff2d8', 'center', true, 3);
      text('B: thôi', 320, 438, 12, '#e0cfb0', 'center', false, 3);
    } else if (P === 'result') {
      const r = W.res;
      const won = r.mine > r.theirs, same = r.mine === r.theirs;
      title(r.gone && same ? 'KẾT THÚC' : won ? 'THẮNG!' : same ? 'HÒA' : 'THUA', 320, 170, 32, won ? '#ffd36e' : '#c9a08a', 5);
      text(`${r.mine} - ${r.theirs} với ${petName(r.them)}`, 320, 214, 16, '#fff2d8', 'center', true, 3);
      if (r.gone) text(r.gone, 320, 244, 14, '#ffb08a', 'center', true, 3);
      if (r.desync) text(`Hai máy bị lệch ${r.desync} lần (ghi trong log.txt)`, 320, 268, 12, '#ffb08a', 'center', false, 3);
      text('A / B: về Đấu qua wifi', 320, 438, 12, '#e0cfb0', 'center', false, 3);
    }
    if (W.msg) {
      ctx.fillStyle = 'rgba(14,9,7,0.85)'; ctx.fillRect(0, 452, 640, 28);
      text(W.msg, 320, 466, 12, W.bad ? '#ffb08a' : '#cfe8b0', 'center', true, 2);
    }
  }
  // over the match: which side is yours, waiting, the end
  function drawMatch(now) {
    if (!L) return;
    const left = L.me === 0;
    text(left ? 'Bạn: bên TRÁI' : 'Bạn: bên PHẢI', left ? 8 : 632, 466, 12, '#9fd8ff', left ? 'left' : 'right', true, 3);
    if (L.desync) text('LỆCH', 320, 466, 11, '#ff8a7a', 'center', true, 2);
    let say = '';
    if (L.gone) say = `${L.gone} · SELECT: ra`;
    else if (L.done) say = 'Hết trận · SELECT: ra';
    else if (L.waiting && clock() - L.waitFrom > WAIT_SAY) say = 'Đang chờ máy kia…';
    if (say) { ctx.fillStyle = 'rgba(14,9,7,0.8)'; ctx.fillRect(160, 330, 320, 34); text(say, 320, 347, 14, '#fff2d8', 'center', true, 3); }
  }

  // ---------- buttons ----------
  function press(btn) {
    if (S.fade > 0) return;
    const P = W.page, mv = d => { sfx('menu', 160); return d; };
    if (P === 'menu') {
      if (btn === 'UP') W.sel = mv((W.sel + MENU.length - 1) % MENU.length);
      if (btn === 'DOWN') W.sel = mv((W.sel + 1) % MENU.length);
      if (btn === 'B' || (btn === 'A' && MENU[W.sel][0] === 'back')) { sfx('quay-lai', 180); closeSock(); W = null; return fadeTo(() => { S.vd = { view: 'solo-online', sel: 1 }; }); }
      if (btn === 'A') { sfx('menu', 200); W.msg = ''; if (MENU[W.sel][0] === 'host') hostRoom(); else findRooms(); }
      return;
    }
    if (P === 'host' || P === 'joining') { if (btn === 'B') { sfx('quay-lai', 180); closeSock(); W.page = 'menu'; W.msg = ''; } return; }
    if (P === 'find') {
      const n = W.rooms.length + 1, onIp = W.ri === W.rooms.length;
      if (btn === 'UP') W.ri = mv((W.ri + n - 1) % n);
      if (btn === 'DOWN') W.ri = mv((W.ri + 1) % n);
      if (onIp && ['LEFT', 'RIGHT', 'L1', 'R1'].includes(btn)) {
        const d = { LEFT: -1, RIGHT: 1, L1: -10, R1: 10 }[btn];
        W.ip[3] = Math.max(1, Math.min(254, W.ip[3] + d)); sfx('menu', 120);
      }
      if (btn === 'A') { sfx('menu', 200); W.msg = ''; join(onIp ? W.ip.join('.') : W.rooms[W.ri].ip); }
      if (btn === 'B') { sfx('quay-lai', 180); closeSock(); W.page = 'menu'; W.msg = ''; }
      return;
    }
    if (P === 'result' && (btn === 'A' || btn === 'B')) { W.page = 'menu'; W.res = null; }
  }

  // ---------- the hooks ----------
  globalThis.__dauWifi = () => fadeTo(open);
  globalThis.__dauWifiTest = { join: ip => { if (!W) open(); if (sock(0)) join(ip); }, host: () => { if (!W) open(); hostRoom(); },
                                state: () => W, match: () => L, find: () => { if (!W) open(); findRooms(); } };
  const draw0 = __soloDraw;
  globalThis.__soloDraw = now => {
    const v = S.vd;
    if (v && v.view === VIEW) { if (!W) open(); if (W.sock && W.page !== 'match') lobbyNet(); return drawLobby(now); }
    draw0(now);
    if (v && v.view === 'solo' && v.lan) drawMatch(now);
  };
  const press0 = __soloPress;
  globalThis.__soloPress = btn => {
    const v = S.vd;
    if (v && v.view === VIEW) return W && press(btn);
    if (v && v.view === 'solo' && v.lan) { if (btn === 'SELECT' && !(S.fade > 0)) leave(); return; }   // the rest: the lockstep's own buttons
    return press0(btn);
  };
})();
