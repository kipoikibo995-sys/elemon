// lam_bac2_tab.js for arena.ai (image/direct, gpt-image-2.5-sunburst): same jobs (input #claude-job / #claude-more),
// one picture per step. Arena names a download after the prompt's first words, so each prompt starts with the step's
// code (scripts/lam_bac2.py gom maps it back). Every arena tab shares one draft (text and attachments), so a lock in
// localStorage keeps two tabs from filling it at once. All creatures stay in this tab's one chat.
(() => {
  const S = window.__job = window.__job || { state: 'need-files', log: [] };
  S.queue = S.queue || []; S.imgs = S.imgs || {}; S.fails = S.fails || 0;
  if (window.__sup) clearInterval(window.__sup);
  const tok = S.tok = (S.tok || 0) + 1, me = Math.random().toString(36).slice(2);
  const live = () => S.tok === tok;
  if (S.running && S.runTok !== tok) S.running = false;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const box = () => [...document.querySelectorAll('textarea')].find(t => t.offsetParent !== null && t.placeholder);
  for (const id of ['claude-job', 'claude-more']) {
    let inp = document.getElementById(id);
    if (!inp) {
      inp = document.createElement('input');
      inp.type = 'file'; inp.multiple = true; inp.id = id; inp.setAttribute('aria-label', id.replace('-', ' ') + ' files');
      inp.style.cssText = `position:fixed;left:${id === 'claude-job' ? 0 : 50}px;bottom:0;width:40px;height:20px;opacity:0.01;z-index:99999`;
      document.body.appendChild(inp);
    }
    inp.onchange = async () => {
      for (const f of [...inp.files]) {
        if (f.name.endsWith('.json')) S.queue.push(JSON.parse(await f.text())); else S.imgs[f.name] = f;
      }
      if (!S.job && S.queue.length) { S.job = S.queue.shift(); S.state = 'ready'; run(); }
    };
  }
  async function lock() {               // the shared draft: one tab at a time between attaching and sending
    for (;;) {
      const l = JSON.parse(localStorage.getItem('claudeArenaLock') || 'null');
      if (!l || l.who === me || Date.now() - l.t > 90000) {
        localStorage.setItem('claudeArenaLock', JSON.stringify({ who: me, t: Date.now() }));
        await sleep(300);
        if (JSON.parse(localStorage.getItem('claudeArenaLock')).who === me) return;
      }
      await sleep(2000 + Math.random() * 2000);
    }
  }
  const unlock = () => { const l = JSON.parse(localStorage.getItem('claudeArenaLock') || 'null'); if (l && l.who === me) localStorage.removeItem('claudeArenaLock'); };
  async function send(text, file) {
    await lock();
    try {
      const fi = [...document.querySelectorAll('input[type=file]')].find(i => !i.id.startsWith('claude-'));
      for (const f of [].concat(file || [])) {     // one or more attachments (a look and a mould)
        const dt = new DataTransfer(); dt.items.add(f); fi.files = dt.files; fi.dispatchEvent(new Event('change', { bubbles: true }));
        for (let k = 0; k < 40 && ![...document.querySelectorAll('img')].some(i => i.alt === f.name && i.offsetParent); k++) await sleep(500);
        await sleep(1500);
      }
      const ta = box(), set = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
      set.call(ta, text); ta.dispatchEvent(new Event('input', { bubbles: true }));
      await sleep(800);
      for (let k = 0; k < 120; k++) {
        const b = document.querySelector('button[aria-label="Send message"]');
        if (b && !b.disabled && box().value) { b.click(); await sleep(1500); return true; }
        await sleep(500);
      }
      return false;
    } finally { unlock(); }
  }
  // a new download button shows up once the new picture is finished (arena lists them newest first, so count, not order)
  const dls = () => [...document.querySelectorAll('button')].filter(b => ((b.querySelector('svg path') || { getAttribute: () => '' }).getAttribute('d') || '').startsWith('M6 20L18 20'));
  async function drawn(n0) {
    const t0 = Date.now(); let still = 0;
    while (Date.now() - t0 < 420000) {
      await sleep(3000);
      if (!live()) return null;
      if (dls().length > n0) { if (++still >= 3) return true; } else still = 0;
    }
    return { fail: 'timeout' };
  }
  async function save() {               // the download button under the newest picture: the lowest on the page
    dls().sort((x, y) => y.getBoundingClientRect().top - x.getBoundingClientRect().top)[0].click();
    await sleep(3000);
  }
  async function draw(st) {
    for (let k = 0; k < 6; k++) {
      if (!live()) throw 'replaced';
      S.state = `${st.sheet}: resting`;
      await sleep(15000 + Math.random() * 15000);
      const n0 = dls().length;
      S.state = `${st.sheet}: ${k ? 'retry ' + k : 'drawing'}`;
      if (!await send(`${st.code} ` + st.prompt, (st.files || [st.file]).map(n => S.imgs[n]))) throw 'send ' + st.sheet;
      const im = await drawn(n0);
      if (!live()) throw 'replaced';
      if (im && !im.fail) { await save(); S.log.push(st.sheet); return; }
      S.fails++; S.state = `${st.sheet}: waiting after timeout`;
      await sleep(60000 * (k + 1));
    }
    throw 'gave up ' + st.sheet;
  }
  async function run() {
    if (!S.job || (S.running && S.runTok === tok)) return;
    S.running = true; S.runTok = tok; S.i = S.i || 0;
    try {
      while (S.job) {
        while (S.i < S.job.steps.length) { await draw(S.job.steps[S.i]); S.i++; }
        S.done = (S.done || []).concat(S.job.prefix);
        S.job = S.queue.shift() || null; S.i = 0; S.log = [];
      }
      S.state = 'done';
    } catch (e) { if (live()) S.state = 'error: ' + e; }
    if (live()) S.running = false;
  }
  window.__run = run;
  window.__sup = setInterval(() => {
    if (!live() || !S.job || S.running) return;
    if (!S.errT) { S.errT = Date.now(); return; }
    if (Date.now() - S.errT > 60000) { S.errT = 0; run(); }
  }, 5000);
  if (S.job && !S.running) run();
  return S.state;
})();
