// test probe: every use of a picture after it was freed (drawn from, drawn onto, resized, read), and the skills fired
(() => {
  const freed = new Set(), use = {}, seen = {};
  const bad = (what, id) => { if (freed.has(id)) use[what] = (use[what] || 0) + 1; };
  const w = (name, at) => { const f = __cv[name]; __cv[name] = function (...a) { for (const i of at) bad(name, a[i]); return f.apply(this, a); }; };
  w('drawImage', [0, 1]); w('fillRect', [0]); w('ellipse', [0]); w('poly', [0]); w('text', [0]); w('resize', [0]); w('pixels', [0]); w('put', [0]); w('seal', [0]);
  const fr = __cv.free; __cv.free = id => { freed.add(id); return fr(id); };
  const sfx = __cv.sfx; __cv.sfx = (n, v) => { seen[n] = (seen[n] || 0) + 1; return sfx(n, v); };
  globalThis.__staleReport = () => __cv.log(`stale uses ${JSON.stringify(use)} | freed ${freed.size} | sounds ${Object.keys(seen).length}: ${Object.entries(seen).sort((a, b) => b[1] - a[1]).slice(0, 12).map(e => e.join('x')).join(' ')}`);
  let n = 0; const f0 = globalThis.__frame;
  globalThis.__frame = now => { f0(now); if (++n % 900 === 0) __staleReport(); };
})();
