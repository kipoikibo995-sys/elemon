// Elemon: the gate in front of each screen (see game/src/tai-dan.js). Loaded last, so its frame is the outermost:
// a screen whose pictures are not all in yet is held behind a short "Đang tải" screen (real time, a bar with how far
// it has got) while they are read; in the room and the other screens the rest are read a few at a time meanwhile,
// so the wait is usually over before the screen is opened.
(() => {
  const L = globalThis.__LAZY;
  if (!L || !L.load || typeof frame !== 'function') return;
  // what each screen needs, from the game state
  const NEED = () => {
    const m = S.mode, out = [];
    if (m === 'farm') out.push('farm');
    if (m === 'fish') out.push('fish');
    if (m === 'cook') out.push('cook');
    if (m === 'school') out.push('school');
    if (m === 'shop') out.push('shop');
    if (m === 'tui') out.push('tui');
    if (m === 'bath') out.push('bath');
    if (m === 'egg' || m === 'pickEgg') out.push('hatch');   // the egg picker shows the hatching's first frame
    if (S.stats !== null && S.stats !== undefined) out.push('stats');
    return out.filter(g => L.groups[g] && !L.done[g]);
  };
  const ORDER = ['hatch', 'stats', 'shop', 'tui', 'bath', 'farm', 'school', 'cook', 'fish'];   // the background's order
  const GATE_MS = 30, IDLE_MS = 3;                 // a loading frame's reading time; a playing frame's share
  const clock = typeof __cv === 'object' && __cv.clock ? __cv.clock : () => performance.now();   // real ms
  const device = typeof __cv === 'object';         // R36S: a picture is read as soon as it is asked for
  const queue = {};                                // group -> names not asked for yet
  let inFlight = 0;
  function step(g, budget) {                       // ask for more of a group; true when all of it has arrived
    const q = queue[g] || (queue[g] = L.groups[g].slice()), t = clock();
    if (!L.started[g]) L.started[g] = { asked: 0, got: 0, all: L.groups[g].length };
    const st = L.started[g];
    while (q.length && clock() - t < budget && (device || inFlight < 12)) {
      const n = q.shift();
      st.asked++; inFlight++;
      L.load(n, `img/${n}.png`).then(() => { st.got++; inFlight--; if (st.got === st.all) L.done[g] = true; });
    }
    return !!L.done[g];
  }
  function drawWait(groups) {
    let got = 0, all = 0;
    for (const g of groups) { const st = L.started[g]; all += L.groups[g].length; got += st ? st.got : 0; }
    const k = all ? got / all : 1;
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1;
    ctx.fillStyle = '#120c08'; ctx.fillRect(0, 0, 640, 480);
    ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fillRect(170, 250, 300, 12);
    ctx.fillStyle = '#ffd36e'; ctx.fillRect(172, 252, Math.round(296 * k), 8);
    ctx.restore();
    text(`Đang tải… ${Math.round(k * 100)}%`, 320, 230, 16, '#fff2d8', 'center', true, 3);
  }

  const frame0 = globalThis.frame;
  let waiting = null;
  globalThis.frame = function (now) {
    const need = NEED();
    if (need.length) {                              // held until this screen's pictures are in
      for (const g of need) step(g, GATE_MS / need.length);
      waiting = need;
      drawWait(need);
      requestAnimationFrame(globalThis.frame);
      return;
    }
    waiting = null;
    const r = frame0.apply(this, arguments);
    {                                               // meanwhile (title screen too): the rest, a little at a time
      const g = ORDER.find(k => L.groups[k] && !L.done[k] && (queue[k] === undefined || queue[k].length));
      if (g) step(g, IDLE_MS);
    }
    return r;
  };
  globalThis.__lazyInfo = () => ({ waiting, done: { ...L.done }, started: L.started });   // tests

  // the pet: at start the saved one rather than the demo's Hỏa Hổ (song-that.js knows the save), and not read
  // again when "Tiếp tục" asks for the same one. Another pet picked (a new game after the one read at start): the
  // old one's frames are given back once the new one's are in (R36S: ~45 MB for a grown pet, the demo only drops
  // them from IMG)
  const lc0 = globalThis.loadCreature;
  const STAGE_PIC = /^(baby|child|teen|adult|legend|adult4|legend4)\//;   // the demo's loadCreature's own test
  let loadedId = null;
  globalThis.loadCreature = function (id) {
    if (id === loadedId && PET_READY) return Promise.resolve();
    const old = Object.keys(IMG).filter(k => STAGE_PIC.test(k)).map(k => IMG[k]);
    return lc0.apply(this, arguments).then(r => {
      loadedId = id;
      if (typeof __cv === 'object' && __cv.free) {
        const kept = new Set(Object.values(IMG));
        for (const im of old) if (!kept.has(im) && im.__id !== undefined) __cv.free(im.__id);
      }
      return r;
    });
  };
})();
