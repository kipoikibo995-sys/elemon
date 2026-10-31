// test: Linh khí's effects (game/src/chi-so.js) on the R36S runtime: an hour of needs with no Linh khí, then with each
// element at 100; Kim / Hỏa in the fight numbers; Thủy's mini game ease
(() => {
  let k = 0;
  const f1 = globalThis.__frame, L = s => __cv.log('lk ' + s), J = o => JSON.stringify(o);
  const hour = (lk, night) => {
    S.lk = Object.assign({ hoa: 0, kim: 0, moc: 0, thuy: 0, tho: 0 }, lk);
    S.need = Object.assign(S.need, { no: 80, vui: 80, sach: 90, nl: 50, sk: 50 }); S.night = night ? 1 : 0; S.sick = false; S.poops = [];
    tickNeeds(3600e3, performance.now());
    const n = S.need; return { no: +n.no.toFixed(1), vui: +n.vui.toFixed(1), nl: +n.nl.toFixed(1), sk: +n.sk.toFixed(2) };
  };
  globalThis.__frame = now => {
    try { f1(now); } catch (e) { L('frame err ' + e); }
    k++;
    try {
      if (k === 300) {
        __chiSo.ensure();
        L('day none ' + J(hour({}, false)));
        L('day kim ' + J(hour({ kim: 100 }, false)));
        L('day hoa ' + J(hour({ hoa: 100 }, false)));
        L('day thuy ' + J(hour({ thuy: 100 }, false)));
        L('night none ' + J(hour({}, true)));
        L('night tho ' + J(hour({ tho: 100 }, true)));
        L('night moc ' + J(hour({ moc: 100 }, true)));
        for (const lk of [{}, { kim: 100 }, { hoa: 100 }]) {
          S.lk = Object.assign({ hoa: 0, kim: 0, moc: 0, thuy: 0, tho: 0 }, lk); S.need.nl = 80; S.need.vui = 60; S.need.no = 80;
          const p = __chiSo.pet(); L('fight ' + J(lk) + ' ' + J({ atk: +p.atk.toFixed(2), thu: +p.thu.toFixed(2) }));
        }
        S.lk.thuy = 100; L('ease thuy100 ' + __lkDe()); S.lk.thuy = 0; L('ease thuy0 ' + __lkDe());
        L('done');
      }
    } catch (e) { L('err ' + (e && e.stack || e)); }
  };
})();
