// test: the new story scenes play (room Lv9 -> h2-suc-khoe), no voice for the re-worded lines
(() => {
  let k = 0;
  const f1 = globalThis.__frame, L = s => __cv.log('thoai ' + s);
  globalThis.__frame = now => {
    try { f1(now); } catch (e) { L('frame err ' + e); }
    k++;
    try {
      if (k === 300) { S.mode = 'room'; S.stage = 'child'; S.level = 9; S.stats = null; S.popupGoal = 0; S.pickerGoal = 0; S.act = null; S.fade = 0;
        S.truyen = { da: { 'h1-chao': 1, 'h1-ket': 1, 'h2-truyen-thuyet': 1 }, dang: null }; L('set'); }
      if (k === 420) L('dang ' + JSON.stringify(S.truyen.dang) + ' voice h2-ban-do_1=' + __giongMs('h2-ban-do_1') + ' h2-truyen-thuyet_0=' + __giongMs('h2-truyen-thuyet_0'));
    } catch (e) { L('err ' + (e && e.stack || e)); }
  };
})();
