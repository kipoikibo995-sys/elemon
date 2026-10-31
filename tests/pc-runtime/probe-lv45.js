// test: Lv4/Lv5 bodies on the R36S runtime. The pet raised (Kim Giáp) at Huyền thoại against Thủy Long in Trưởng thành,
// the foe's body hooked in as Vùng đất does it (game/src/vung-dat.js SOLO_HOOKS); every picture asked for is logged
(() => {
  let k = 0;
  const f1 = globalThis.__frame, L = s => __cv.log('lv45 ' + s);
  const HOOKS = [
    ["const stage = bot ? (NHI || PET || BOTPET ? 'child' : 'adult')", "const stage = bot ? (globalThis.__vgBotStage || (NHI || PET || BOTPET ? 'child' : 'adult'))"],
    ["    const T = async (n, c, r) => { const cells = cut(await load(dir + n + '.png'), c, r); WB[n] = mirror ? tint(cells, 'hue-rotate(170deg) saturate(1.2)') : cells; };",
     "    const bdir = globalThis.__vgBotStage && __vgBotStage !== 'child' ? dir + __vgBotStage + '/' : dir, BODY_N = ['s', 'se', 'e', 'ne', 'n', 'chung'];\n" +
     "    const T = async (n, c, r) => { const cells = cut(await load((BODY_N.includes(n) ? bdir : dir) + n + '.png'), c, r); WB[n] = mirror ? tint(cells, 'hue-rotate(170deg) saturate(1.2)') : cells; };"],
    ["    WB.cutin = cut(await load(dir + 'cutin.png'), 1, 1)[0];", "    WB.cutin = cut(await load(bdir + 'cutin.png'), 1, 1)[0];"],
  ];
  globalThis.__frame = now => {
    try { f1(now); } catch (e) { L('frame err ' + e); }
    k++;
    try {
      if (k === 250) {
        let src = String(__SOLO_SRC), miss = 0;
        for (const [a, b] of HOOKS) { if (!src.includes(a)) miss++; src = src.replace(a, b); }
        src = __chiSoSrc(__soloBodySrc(src));
        L('hooks missing ' + miss + ' stage adult->' + __soloStage('thuy-long', 'adult') + ' legend->' + __soloStage('kim-giap', 'legend'));
        globalThis.__lvSrc = (0, eval)('(' + src + ')');
      }
      if (k === 300) {
        const M = __soloMatch, R = M.ROSTER;
        DATA.pet.creature = 'kim-giap'; S.stage = 'legend'; S.mode = 'voduong'; S.need.nl = 100; S.need.sk = 100; S.sick = false;
        S.vd = { view: 'solo', sel: 1, level: 0, quiet: true };
        globalThis.__vgBotStage = 'adult'; globalThis.__soloPow = __chiSo.pow(S.level);
        const plain = globalThis.__SOLO_SRC; globalThis.__SOLO_SRC = __lvSrc;
        try { M.start(R.find(r => r.dir === 'kim-giap'), R.find(r => r.dir === 'thuy-long'), 0); } finally { globalThis.__SOLO_SRC = plain; }
        L('start me stage ' + globalThis.__soloMeStage);
      }
      const seen = globalThis.__soloSeen;
      if (seen && k % 300 === 0) L(`k=${k} P.stage=${seen.P().stage} P.h=${seen.P().h} B.stage=${seen.B().stage} B.h=${seen.B().h} started=${__soloInfo() && __soloInfo().started}`);
      if (k === 1500) L('done');
    } catch (e) { L('err ' + (e && e.stack || e)); }
  };
})();
