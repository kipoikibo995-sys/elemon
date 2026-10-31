// Elemon: the story's voices. scripts/make_giong.py reads every line of game/src/truyen.js aloud into
// assets/am-thanh/giong/<key>.wav; game/build_game.py copies them to sfx/giong/ and puts their lengths here.
//   __giong(key)          speaks a line (the one before stops), null stops; its length in ms, 0 if none
//   __giongCau(id, i)     the key of a scene's line: <id>_<i>_<pet's element> when the line names the element
//   __giongMs(key)        a line's length in ms (the films wait for it, and type their words in step with it)
// In a browser one <audio> at a time; on the R36S the runtime's voice channel (__cv.voice, r36s/jsrt.c): one line at
// a time too, the one before stopped, and each line given back after it is said (an older runtime: SOUND.sfx, which
// cannot stop a line cut short by A and keeps every line in memory).
(() => {
  const LEN = __GIONG__;                                   // key -> ms (game/build_game.py); also the file's version in
                                                           // the browser, so a line made again is never the cached one
  const native = typeof __cv === 'object';                 // the R36S runtime (r36s/js/shim.js)
  let cur = null;
  globalThis.__giongMs = key => (key && LEN[key]) || 0;
  globalThis.__giongCau = (id, i) => {
    const he = typeof EL === 'function' ? `${id}_${i}_${EL()}` : '';
    return LEN[he] ? he : LEN[`${id}_${i}`] ? `${id}_${i}` : null;
  };
  const voice = native && typeof __cv.voice === 'function';
  globalThis.__giong = key => {
    if (cur) { cur.pause(); cur = null; }
    if (voice) __cv.voice('');
    if (!key || !LEN[key]) return 0;
    if (!native && typeof Audio === 'function') { cur = new Audio(`sfx/giong/${key}.wav?v=${LEN[key]}`); cur.play().catch(() => {}); }
    else if (voice) __cv.voice(`giong/${key}`);
    else if (typeof SOUND === 'object' && SOUND) SOUND.sfx(`giong/${key}`, 256);
    return LEN[key];
  };
})();
