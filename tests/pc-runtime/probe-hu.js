// test: the Hư Ảnh fight (Đài Ngũ Hành) on the R36S runtime: its loading, phase 1, then phase 2 (the avatar killed),
// the frame cost every 150 frames (avg, 95th percentile, worst), the pet kept alive; errors and missing pictures
(() => {
  let k = 0, t = [], killed = 0;
  const f1 = globalThis.__frame, L = s => __cv.log('hu ' + s);
  const clock = () => (typeof __cv === 'object' && __cv.clock ? __cv.clock() : performance.now());
  globalThis.__frame = now => {
    const a = clock();
    try { f1(now); } catch (e) { L('frame err ' + e); }
    t.push(clock() - a);
    k++;
    try {
      if (k === 200) { S.need.nl = 100; S.need.sk = 100; S.sick = false; __vgHu(); L('go'); }
      if (k % 150 === 0) {
        const s = t.slice().sort((x, y) => x - y), avg = s.reduce((p, c) => p + c, 0) / s.length;
        L(`k=${k} ${S.mode}/${S.vg && S.vg.view} phase=${globalThis.__hu ? __hu.phase : '-'} avg=${avg.toFixed(2)} p95=${s[Math.floor(s.length * 0.95)].toFixed(1)} max=${s[s.length - 1].toFixed(1)}`);
        t = [];
      }
      const A = globalThis.__arenaApi;
      if (A && A.P && A.P()) A.P().hp = Math.max(A.P().hp, 60);          // the pet kept standing
      if (!killed && k > 1500 && A && A.B && globalThis.__hu && __hu.phase === 1) {
        const B = A.B(), P = A.P(); A.hit(B, 9999, P.x, P.y, true, P, ''); killed = k; L('avatar killed at ' + k);
      }
      if (k === 5900) L('done');
    } catch (e) { L('err ' + (e && e.stack || e)); }
  };
})();
