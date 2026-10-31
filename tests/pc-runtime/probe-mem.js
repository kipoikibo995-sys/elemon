// test probe (loaded right after js/shim.js): the pixels of the pictures alive (newCanvas / resize / loadImage minus
// free), with the real clock, frame and screen every 60 frames (matched with the RSS samples of run-mem.sh)
(() => {
  const size = new Map(); let bytes = 0, n = 0, voices = 0;
  const set = (id, b) => { bytes += b - (size.get(id) || 0); size.set(id, b); };
  const nc = __cv.newCanvas, rs = __cv.resize, li = __cv.loadImage, fr = __cv.free, vo = __cv.voice;
  __cv.newCanvas = (w, h) => { const id = nc(w, h); set(id, w * h * 4); return id; };
  __cv.resize = (id, w, h) => { rs(id, w, h); if (id) set(id, w * h * 4); };
  __cv.loadImage = p => { const r = li(p); if (r) set(r[0], r[1] * r[2] * 4); return r; };
  __cv.free = id => { if (size.has(id)) { bytes -= size.get(id); size.delete(id); } return fr(id); };
  if (vo) __cv.voice = k => { if (k) voices++; return vo(k); };
  globalThis.__probeFrame = now => {
    if (++n % 60 === 0) __cv.log(`memprobe ${__cv.clock().toFixed(0)} ${n} ${typeof S === 'object' ? S.mode : '?'}${typeof S === 'object' && S.vd ? '/' + S.vd.view : ''}${typeof S === 'object' && S.vg ? '/' + S.vg.view : ''} ${(bytes / 1048576).toFixed(1)} ${voices}`);
  };
})();
