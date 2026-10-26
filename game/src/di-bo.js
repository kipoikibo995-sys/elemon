// Elemon: the stroll across the room, smoother than the demo's. The pets have 4 walk frames but only two poses
// (walk-0 ~ walk-2, walk-1 ~ walk-3), swapped every 160 ms at one speed from the first step to the last: it looked
// stiff. Here
//   - the pet speeds up over its first steps and slows down into its last (walkEase, used by drawRoom through the
//     line game/build_game.py changes in the demo page),
//   - the frame follows the ground covered, not the clock, so the feet do not slide when it is slow,
//   - the body bobs once a step on a curve (and the chest breathes with it) instead of 1-2 px jumps.
(() => {
  const RAMP = 320;          // ms to reach full speed, and to stop from it
  const STRIDE = 11;         // px of floor a frame (the demo: 70 px/s x 160 ms)
  const BOB = 3;             // px the body rises mid-step (in sample's units)

  // t in 0..1 of the walk's time -> 0..1 of its way: speeding up, steady, slowing down, ending on time
  globalThis.walkEase = (t, dur) => {
    const a = Math.min(0.45, RAMP / Math.max(1, dur)), v = 1 / (1 - a);     // v: the top speed (way per time)
    if (t <= 0) return 0;
    if (t >= 1) return 1;
    if (t < a) return v * t * t / (2 * a);
    if (t > 1 - a) { const u = 1 - t; return 1 - v * u * u / (2 * a); }
    return v * (t - a / 2);
  };

  const plain = sample;
  sample = function (anim, ms) {
    const st = typeof S === 'object' && S && S.walk && DATA.stages[S.stage];
    if (!st || anim !== st.anims.walk || !anim.keys || !anim.keys.length) return plain(anim, ms);
    const n = anim.keys.length, step = Math.abs(S.px - S.walk.from) / STRIDE;    // frames' worth of floor covered
    const k = anim.keys[Math.floor(step) % n], ph = step % 1;
    const lift = Math.sin(Math.PI * ph);                                      // 0 at a foot's landing, 1 mid-step
    return { f: k.f, x: 2 * (k.x || 0), y: -BOB * lift, br: 2 * lift };
  };
})();
