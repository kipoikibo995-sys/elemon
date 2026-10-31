// test: the game's numbers (game/src/chi-so.js) on the R36S runtime: the pet's stats, a Võ đường Solo match with the
// power ratio and the start HP from Sức khỏe, the HP lost, what leaving costs; a meal, a level, medicine
(() => {
  let k = 0, started = false;
  const f1 = globalThis.__frame, L = s => __cv.log('cs ' + s), J = o => JSON.stringify(o);
  globalThis.__frame = now => {
    try { f1(now); } catch (e) { L('frame err ' + e); }
    k++;
    try {
      if (k === 250) {
        L('fn ' + J([typeof __chiSo, typeof __chiSoSrc, typeof __expThuong, typeof __anMon, typeof __tapXong]));
        __chiSo.ensure();
        L('attr0 ' + J(S.attr) + ' sk ' + S.need.sk);
        __anMon('hoa'); __anMon('moc');
        S.lk.hoa = 50; S.level = 9; __chiSo.ensure();
        const p = __chiSo.pet();
        L('lv9 attr ' + J(S.attr.map(v => +v.toFixed(2))) + ' pet ' + J({ hp: p.hp, atk: +p.atk.toFixed(1), skill: +p.skill.toFixed(1), thu: p.thu, luc: __chiSo.luc(p) }));
        L('pow lv9 ' + J(__chiSo.pow(9)) + ' boss16 ' + J(__chiSo.pow(16, 1.2)));
        L('mob lv9 ' + J(__chiSo.mob(9, { hp: 1, dmg: 1 })));
      }
      if (k === 300) {
        const M = __soloMatch, R = M.ROSTER; S.mode = 'voduong'; S.need.nl = 100; S.need.sk = 70; S.sick = false;
        S.vd = { view: 'solo', sel: 1, level: 3 };
        globalThis.__soloPow = __chiSo.pow(S.level);
        M.start(R.find(r => r.dir === 'hoa-ho'), R.find(r => r.dir === 'thuy-long'), 3); started = true; L('solo start');
      }
      const seen = globalThis.__soloSeen;
      if (started && seen && k % 150 === 0) L(`k=${k} P.hp=${seen.P().hp} B.hp=${seen.B().hp} lost=${__soloMatch.lost()} score=${J(seen.score)}`);
      if (started && k === 2400) {
        const n0 = J(S.need);
        __soloPress('SELECT');
        L('left need0 ' + n0 + ' need ' + J(S.need) + ' toast ' + S.toast);
        L('xp boss ' + __expThuong(0.6));
        L('done');
      }
    } catch (e) { L('err ' + (e && e.stack || e)); }
  };
})();
