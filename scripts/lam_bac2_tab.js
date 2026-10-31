// Runs in a ChatGPT tab (pasted by Claude through the browser tools): draws creatures' level-2 sheets, one chat per
// creature. Jobs come in through the input #claude-job (and #claude-more): assets/source/tinh-linh/_ve-lv2/jobs/
// <prefix>.json plus the level-1 sheets it names (chieu/<prefix>_<n>.png); several creatures queue up. For each sheet:
// attach the level-1 sheet, send its prompt, save the drawing as lv2__<prefix>__<n>.png, then ask for its in-betweens
// and save lv2__<prefix>__<n>_mid.png (Chrome's download folder). When ChatGPT answers with an error instead of a
// picture it waits and asks again. A finished creature opens a new chat for the next one.
// window.__job.state says where it is. Pasting it again over a running copy takes over from it.
(() => {
  const S = window.__job = window.__job || { state: 'need-files', log: [] };
  S.queue = S.queue || []; S.imgs = S.imgs || {}; S.fails = S.fails || 0;
  if (window.__sup) clearInterval(window.__sup);
  const tok = S.tok = (S.tok || 0) + 1;                       // an older copy's loop stops at its next step
  const live = () => S.tok === tok;
  if (S.running && S.runTok !== undefined && S.runTok !== tok) S.running = false;   // an older copy of this stops by itself
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  // the visible composer: an image-edit box can leave a second, hidden one in the page
  const composer = () => [...document.querySelectorAll('#prompt-textarea, div.ProseMirror[contenteditable="true"]')].filter(e => e.offsetParent !== null).pop();
  const gens = () => [...document.querySelectorAll('main img')].filter(i => (i.alt || '').startsWith('Generated image') && i.naturalWidth > 600);
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
  async function attach(file) {          // hand the file to ChatGPT's own attach input, wait for its thumbnail
    for (let tries = 0; tries < 3; tries++) {
      const ed = composer(), box = ed && ed.closest('form');       // the attach input of the visible composer
      let ins = [...(box || document).querySelectorAll('input[type=file]')].filter(i => !i.id.startsWith('claude-') && !i.hasAttribute('capture'));
      if (!ins.length) ins = [...document.querySelectorAll('input[type=file]')].filter(i => !i.id.startsWith('claude-') && !i.hasAttribute('capture'));
      const t = ins[ins.length - 1], dt = new DataTransfer();
      dt.items.add(file); t.files = dt.files; t.dispatchEvent(new Event('change', { bubbles: true }));
      for (let k = 0; k < 60; k++) {
        await sleep(500);
        if (document.querySelector(`[aria-label="Remove ${file.name}"]`)) { await sleep(2000); return true; }
      }
      await sleep(3000);
    }
    return false;
  }
  async function send(text) {             // only sends once the text is really in the box
    let ok = false;
    for (let k = 0; k < 20 && !ok; k++) {
      const ed = composer();
      if (ed) {
        ed.focus(); document.execCommand('selectAll'); document.execCommand('insertText', false, text);
        await sleep(800);
        ok = ed.isConnected && ed.innerText.trim().startsWith(text.slice(0, 30));
      }
      if (!ok) await sleep(1000);
    }
    if (!ok) return false;
    for (let k = 0; k < 120; k++) {
      const ed = composer(), box = (ed && ed.closest('form')) || document;
      const b = box.querySelector('[data-testid="send-button"], button[aria-label="Send"]');
      if (b && !b.disabled) { b.click(); return true; }
      await sleep(500);
    }
    return false;
  }
  const lastReply = () => { const a = [...document.querySelectorAll('[data-message-author-role="assistant"], [class*="MarkdownRoot"]')].pop(); return a ? a.innerText : ''; };
  async function drawn(prev, before) {   // the newest generated image once it stops changing, or the error ChatGPT gave
    const t0 = Date.now(); let last = null, still = 0, quiet = 0;
    while (Date.now() - t0 < 420000) {
      await sleep(3000);
      if (!live()) return null;
      const i = gens().slice(-1)[0];
      if (i && i.src !== prev) {
        if (i.src === last) { if (++still >= 2) return i; } else { last = i.src; still = 0; }
      } else {
        const t = lastReply(), busy = document.querySelector('[data-testid="stop-button"]');
        if (t !== before && !busy && /wasn.t able|unable to|error|limit|try again|can.t (create|generate)|couldn.t/i.test(t)) return { fail: t.slice(0, 200) };
        quiet = t !== before && t && !busy ? quiet + 1 : 0;    // it answered in words, not with a picture
        if (quiet >= 8) return { fail: 'text: ' + t.slice(0, 120) };
      }
    }
    return { fail: 'timeout' };
  }
  async function save(img, name) {
    const b = await (await fetch(img.src)).blob(), a = document.createElement('a');
    a.href = URL.createObjectURL(b); a.download = name; document.body.appendChild(a); a.click(); a.remove();
  }
  async function draw(text, name, file) {   // one picture, asked again after an error (waiting longer each time)
    for (let k = 0; k < 6; k++) {
      if (!live()) throw 'replaced';
      S.state = `${name}: resting`;
      await sleep(15000 + Math.random() * 15000);     // a breather between pictures, so ChatGPT doesn't rate-limit
      if (!live()) throw 'replaced';
      for (const f of [].concat(file || [])) if (!await attach(f)) throw 'attach ' + f.name;
      const before = lastReply();
      S.state = `${name}: ${k ? 'retry ' + k : 'drawing'}`;
      if (!await send(k ? 'Generate the image now, do not ask questions. ' + text : text)) throw 'send ' + name;
      // only a picture that shows up after this message counts (send waits until ChatGPT is idle)
      const im = await drawn((gens().slice(-1)[0] || {}).src, before);
      if (!live()) throw 'replaced';
      if (im && !im.fail) { await save(im, `lv2__${S.job.prefix}__${name}.png`); S.log.push(name); return im; }
      S.fails++; S.lastFail = im && im.fail;
      S.state = `${name}: waiting after "${(im && im.fail || '').slice(0, 60)}"`;
      await sleep((/limit/i.test(S.lastFail) ? 300 : 60) * 1000 * (k + 1));
    }
    throw 'gave up ' + name;
  }
  async function run() {
    if (!S.job || (S.running && S.runTok === tok)) return;
    S.running = true; S.runTok = tok; S.i = S.i || 0; S.phase = S.phase || 'sheet';
    try {
      while (S.job) {
        const steps = S.job.steps;
        while (S.i < steps.length) {
          const st = steps[S.i];
          if (S.phase === 'sheet') { await draw(st.prompt, st.sheet, (st.files || [st.file]).map(n => S.imgs[n])); S.phase = 'mid'; }
          if (st.mid) await draw(st.mid, st.sheet + '_mid');
          S.phase = 'sheet'; S.i++;
        }
        S.done = (S.done || []).concat(S.job.prefix);
        S.job = S.queue.shift() || null; S.i = 0; S.phase = 'sheet'; S.log = [];
        // the next creature goes on in the same chat (the user's wish: no new chat per creature)
      }
      S.state = 'done';
    } catch (e) { if (live()) S.state = 'error: ' + e; }
    if (live()) S.running = false;
  }
  window.__run = run;
  // an error left behind (by this copy or an older one) is picked up again after a minute
  window.__sup = setInterval(() => {
    if (!live() || !S.job || (S.running && S.runTok === tok)) return;
    if (S.running && S.runTok !== tok && !/error/.test(S.state)) return;   // an older copy still working
    if (!S.errT) { S.errT = Date.now(); return; }
    if (Date.now() - S.errT > 60000) { S.errT = 0; S.running = false; run(); }
  }, 5000);
  if (S.job && !S.running) run();
  return S.state;
})();
