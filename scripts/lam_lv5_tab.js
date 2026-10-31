// Runs in the ChatGPT tab of the Claude app's own browser (pasted by Claude through javascript_tool): draws the
// Huyền thoại (Lv5) skill sheets from _ve-lv5/text-jobs.json, all in ONE chat (the user asked: no new chat per picture),
// text only (that browser cannot attach files). Jobs come in with window.__lv5.add([{id, prompt}, ...]). Every 10 drawings (and when the queue runs
// out or ChatGPT stops drawing) they go out as ONE download, lv5__goi_<k>.zip of lv5__<id>.png, so the user clicks
// Save once per 10. window.__lv5.state / .log say where it is. Pasting it again over a running copy takes over.
(() => {
  const S = window.__lv5 = window.__lv5 || { state: 'idle', log: [], queue: [], done: [], pack: [], k: 0, fails: 0 };
  const tok = S.tok = (S.tok || 0) + 1;
  const live = () => S.tok === tok;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const log = t => { S.log.push(new Date().toTimeString().slice(0, 8) + ' ' + t); S.log = S.log.slice(-40); };
  const composer = () => [...document.querySelectorAll('#prompt-textarea, div.ProseMirror[contenteditable="true"]')].filter(e => e.offsetParent !== null).pop();
  const gens = () => [...document.querySelectorAll('main img')].filter(i => (i.alt || '').startsWith('Generated image') && i.naturalWidth > 600);
  const lastReply = () => ([...document.querySelectorAll('[data-message-author-role="assistant"]')].pop() || { innerText: '' }).innerText.slice(-600);
  const busy = () => document.querySelector('[data-testid="stop-button"], button[aria-label="Stop streaming"]');

  // a zip with stored (uncompressed) entries: PNGs do not shrink anyway
  const CRC = new Uint32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
  const crc32 = u => { let c = ~0; for (let i = 0; i < u.length; i++) c = CRC[(c ^ u[i]) & 255] ^ (c >>> 8); return ~c >>> 0; };
  async function zip(files) {
    const parts = [], central = []; let off = 0;
    for (const [name, blob] of files) {
      const data = new Uint8Array(await blob.arrayBuffer()), nm = new TextEncoder().encode(name), crc = crc32(data);
      const h = new DataView(new ArrayBuffer(30));
      [[0, 0x04034b50, 4], [4, 20, 2], [14, crc, 4], [18, data.length, 4], [22, data.length, 4], [26, nm.length, 2]].forEach(([o, v, s]) => s === 4 ? h.setUint32(o, v, true) : h.setUint16(o, v, true));
      const c = new DataView(new ArrayBuffer(46));
      [[0, 0x02014b50, 4], [4, 20, 2], [6, 20, 2], [16, crc, 4], [20, data.length, 4], [24, data.length, 4], [28, nm.length, 2], [42, off, 4]].forEach(([o, v, s]) => s === 4 ? c.setUint32(o, v, true) : c.setUint16(o, v, true));
      parts.push(h, nm, data); central.push(c, nm); off += 30 + nm.length + data.length;
    }
    const size = central.reduce((a, p) => a + p.byteLength, 0), e = new DataView(new ArrayBuffer(22));
    [[0, 0x06054b50, 4], [8, files.length, 2], [10, files.length, 2], [12, size, 4], [16, off, 4]].forEach(([o, v, s]) => s === 4 ? e.setUint32(o, v, true) : e.setUint16(o, v, true));
    return new Blob([...parts, ...central, e], { type: 'application/zip' });
  }
  // every drawing stays in IndexedDB until Claude has seen it on disk (S.confirm): a Save dialog the user missed
  // loses nothing, S.resend() downloads those again
  const db = () => new Promise((ok, bad) => { const r = indexedDB.open('lv5', 1); r.onupgradeneeded = () => r.result.createObjectStore('img'); r.onsuccess = () => ok(r.result); r.onerror = () => bad(r.error); });
  const idb = async (mode, f) => { const d = await db(); return new Promise((ok, bad) => { const t = d.transaction('img', mode), q = f(t.objectStore('img')); t.oncomplete = () => ok(q && q.result); t.onerror = () => bad(t.error); }); };
  const keep = (id, blob) => idb('readwrite', st => st.put(blob, id));
  const kept = () => idb('readonly', st => st.getAllKeys());
  async function bundle(ids) {
    const files = [];
    for (const id of ids) { const b = await idb('readonly', st => st.get(id)); if (b) files.push([`lv5__${id}.png`, b]); }
    if (!files.length) return;
    const a = document.createElement('a');
    a.href = URL.createObjectURL(await zip(files)); a.download = `lv5__goi_${++S.k}.zip`;
    document.body.appendChild(a); a.click(); a.remove();
    log(`saved lv5__goi_${S.k}.zip (${files.length})`);
  }
  async function flush() {
    if (!S.pack.length) return;
    await bundle(S.pack.splice(0));
  }
  S.confirm = async ids => { for (const id of ids) await idb('readwrite', st => st.delete(id)); return (await kept()).length; };
  S.resend = async () => { const ids = await kept(); for (let i = 0; i < ids.length; i += 10) await bundle(ids.slice(i, i + 10)); return ids.length; };
  S.kept = kept;
  async function newChat() {
    const b = [...document.querySelectorAll('button')].find(e => e.getAttribute('aria-label') === 'New chat' || (e.innerText || '').trim() === 'New chat');
    if (b) b.click();
    for (let k = 0; k < 20; k++) { await sleep(500); if (composer() && location.pathname === '/') { await sleep(1500); return true; } }
    return false;
  }
  async function send(text) {
    for (let k = 0; k < 10; k++) {
      const ed = composer();
      if (ed) {
        ed.focus(); document.execCommand('selectAll'); document.execCommand('insertText', false, text);
        await sleep(1500);
        const b = [...document.querySelectorAll('button[aria-label="Send"], button[aria-label="Send prompt"], [data-testid="send-button"]')].filter(e => e.offsetParent !== null).pop();
        if (b && ed.innerText.trim().startsWith(text.slice(0, 30))) { b.click(); return true; }
        S.why = `ed ${ed.innerText.length} btn ${!!b}`;
      } else S.why = 'no composer';
      await sleep(1000);
    }
    return false;
  }
  async function draw(job) {
    if (!S.chat || location.pathname !== S.chat) { if (!await newChat()) return 'nonew'; S.chat = ''; }
    const before = new Set(gens().map(i => i.src));   // the SPA can keep the last chat's image in the page
    if (!await send(S.chat ? 'Next sheet, a NEW separate image (do not edit the previous one). ' + job.prompt : job.prompt)) return 'nosend ' + S.why;
    const t0 = Date.now();
    for (let k = 0; k < 20 && !S.chat; k++) { await sleep(500); if (location.pathname.startsWith('/c/')) S.chat = location.pathname; }
    let seen = '';
    await sleep(8000);
    while (Date.now() - t0 < 6 * 60000) {
      if (!live()) return 'stopped';
      const img = gens().filter(i => !before.has(i.src)).pop(), text = lastReply();
      // the same finished picture on two checks in a row: not a preview still being refined
      if (img && img.complete && !busy()) { if (seen === img.src) return await (await fetch(img.src)).blob(); seen = img.src; } else seen = '';
      if (!busy() && /reached .*limit|limit .*reached|limit is still|generation limit|try again later|wait until|can.t (create|generate)|unable to (create|generate)|violat|content polic/i.test(text) && Date.now() - t0 > 15000) return 'refused: ' + text.slice(-160).replace(/\s+/g, ' ');
      await sleep(3000);
    }
    return 'timeout';
  }
  async function run() {
    const me = S.runId = (S.runId || 0) + 1;
    const mine = () => live() && S.runId === me;
    S.running = true;
    while (mine() && S.queue.length) {
      const job = S.queue[0];
      S.state = 'drawing ' + job.id;
      const r = await draw(job);
      if (!mine()) return;
      if (r instanceof Blob) {
        S.queue.shift(); S.fails = 0;
        await keep(job.id, r); S.pack.push(job.id); S.done.push(job.id); log('ok ' + job.id);
        if (S.pack.length >= 10) await flush();
        S.state = 'rest'; await sleep(15000 + Math.random() * 15000);
      } else if (/limit|try again later|wait until|resets/i.test(r) || (r === 'timeout' && /limit/i.test(lastReply()))) {
        S.state = 'limit, waiting'; log(job.id + ' limit: waiting 20 min'); await flush();
        await sleep(20 * 60000);
      } else {
        S.fails++; log(job.id + ' ' + r);
        if (S.fails >= 3) { S.state = 'stuck: ' + r; await flush(); S.running = false; return; }
        await sleep(60000);
      }
    }
    if (!mine()) return;
    await flush();
    S.state = S.queue.length ? S.state : 'idle'; S.running = false;
  }
  S.add = jobs => { const have = new Set([...S.done, ...S.queue.map(j => j.id)]); S.queue.push(...jobs.filter(j => !have.has(j.id))); if (!S.running) run(); return S.queue.length; };
  S.flush = flush;
  S.fails = 0; S.running = false;
  // a new chat first shows a temporary /c/local-chatgpt:.. address, then its real id: keep following the real one
  clearInterval(window.__chatWatch);
  window.__chatWatch = setInterval(() => { if (/^\/c\/[0-9a-f]{8}-/.test(location.pathname)) S.chat = location.pathname; }, 2000);
  if (S.queue.length) run();
  return 'lv5 driver ' + tok;
})();
