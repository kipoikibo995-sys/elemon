// Round-robin balance sim for the arena (dev tool, not part of the game): both fighters are run by the bot brain and
// drawing is skipped, so a game takes a few ms. In the page console:
//   eval(await (await fetch('_sim.js')).text()); pairs = []; for (const a of SIM.kits) for (const b of SIM.kits) if (a < b) pairs.push([a, b]);
//   await SIM.run(pairs, 6); SIM.res   // wins per pet; aim for ~50%, then adjust KIT_POWER / KIT_DEF in index.html
window.SIM = (() => {
  const kits = Object.keys(PETS);
  const realThink = think, realDraw = draw;
  let histB = [], brainP = null;
  function swap() { [P, B] = [B, P]; [brain, brainP] = [brainP, brain]; histB = hist.splice(0, hist.length, ...histB); }
  function setup(ka, kb) {
    newRound();
    for (const [f, k] of [[P, ka], [B, kb]]) { const pt = PETS[k]; f.kit = k; f.el = pt.el; f.bot = true; f.cd = { j: 0, k: 0, l: 0, i: 0 }; }
    histB = []; brainP = { ...brain, orbit: -brain.orbit, seen: new WeakSet() };
    startT = now - 1600;
  }
  function game(ka, kb, capMs) {
    setup(ka, kb);
    let t = real, ms = 0;
    while (!over && ms < capMs) {
      histB.push({ t: now, x: B.x, y: B.y, vx: B.vx, vy: B.vy, act: B.act, stun: now < B.stunUntil, aiming: B.aiming && { k: B.aiming.k, ang: B.aiming.ang } });
      while (histB.length > 90) histB.shift();
      t += 16.7; ms += 16.7; frame(t);
    }
    return over ? (over.winner === P ? 1 : 0) : (P.hp > B.hp ? 1 : P.hp < B.hp ? 0 : 0.5);
  }
  function install() {
    think = () => { realThink(); swap(); realThink(); swap(); };
    draw = () => { fxs.length = 0; fieldThings = []; };
    window.requestAnimationFrame = () => 0;
  }
  return { kits, game, install, res: {}, errs: [],
    async run(pairs, games = 2, capMs = 45000) {
      install(); level = 2;
      for (const [a, b] of pairs) {
        for (let g = 0; g < games; g++) {
          const swapSides = g % 2, [x, y] = swapSides ? [b, a] : [a, b];
          let w; try { w = game(x, y, capMs); } catch (e) { this.errs.push(x + '-' + y + ': ' + String(e).slice(0, 120)); w = 0.5; }
          const winA = swapSides ? 1 - w : w;
          (this.res[a] = this.res[a] || { w: 0, n: 0 }).w += winA; this.res[a].n++;
          (this.res[b] = this.res[b] || { w: 0, n: 0 }).w += 1 - winA; this.res[b].n++;
        }
        await new Promise(r => setTimeout(r, 0));
      }
      return 'done';
    } };
})();
