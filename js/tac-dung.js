// Elemon: what the shop's goods do is what the shop says (the user, 03/11/2026: "Sửa cho đúng chữ"). Until now every
// food gave No +25 whatever its line said, and the extras on the line (Năng lượng, Vui, Linh khí...) were not given;
// Xà phòng gave Sạch +60 for "Sạch +40", the ball from the bag Vui +25 for "Vui +20", and Viên thảo dược cured like
// the medicine where its line says "Phòng ốm 1 ngày".
// Each food of the Chợ's Đồ ăn tab, once eaten, gets the numbers of its own line (scripts/demo_phong_nuoi.py SHOP):
//   No +N, Vui +N, Năng lượng +N, Sức khỏe +N     instead of the demo's own (No +25 for every food)
//   Linh khí <Hệ> +N, Sức mạnh +1, Bền bỉ +1...    on top of what every food gives (its element's Linh khí +6)
// The eaten-food's other gains (EXP, a heart, its element's two attributes a little) stay as they are. Food that is
// not from the shop (crops, fish, cooked dishes) is left as it was.
// Viên thảo dược: S.phongOm, the time until which the pet does not fall ill (24 h); taken while ill it does not cure
// (Thuốc chữa ốm does). Loaded after chi-so.js, so its illness checks run inside this file's tickNeeds.
(() => {
  if (typeof press !== 'function' || typeof useItem !== 'function' || typeof tickNeeds !== 'function' ||
      typeof DATA !== 'object' || !DATA.shop) return;
  const DAY = 24 * 3600e3, HE = { 'Hỏa': 'hoa', 'Thủy': 'thuy', 'Thổ': 'tho', 'Mộc': 'moc', 'Kim': 'kim' };
  const ATTR = ['Sức mạnh', 'Nhanh nhẹn', 'Bền bỉ', 'Thông minh', 'Trí tuệ', 'Tinh thần'];
  const FOODS = {};
  for (const r of DATA.shop.rows[0] || []) FOODS[r.file] = r;
  const clamp = v => Math.max(0, Math.min(100, v));
  // "Hỏa · No +10 · Năng lượng +15" -> [['No', 10], ['Năng lượng', 15]]
  const parts = info => String(info || '').split('·').map(s => s.trim().match(/^(.+?) \+(\d+)$/)).filter(Boolean).map(m => [m[1], +m[2]]);

  // ---------- a shop food eaten from the bag ----------
  const press0 = press;
  globalThis.press = function (btn) {
    const k = btn === 'A' && S.pickerGoal === 1 && Array.isArray(S.view) ? S.view[S.pick] : undefined;
    const it = typeof k === 'number' && S.items ? S.items[k] : null, row = it && !it.use && FOODS[it.file];
    if (!row || !S.bag[k]) return press0.apply(this, arguments);
    const left = () => { const j = S.items.findIndex(b => b.file === it.file); return j < 0 ? 0 : S.bag[j]; };
    const n = S.need, had = left(), was = { no: n.no, vui: n.vui, nl: n.nl, sk: n.sk };
    const r = press0.apply(this, arguments);
    if (left() >= had) return r;                                   // not eaten (refused, or not hungry)
    n.no = was.no;
    for (const [what, v] of parts(row.info)) {
      if (what === 'No') n.no = clamp(was.no + v);
      else if (what === 'Vui') n.vui = clamp(was.vui + v);
      else if (what === 'Năng lượng') n.nl = clamp(was.nl + v);
      else if (what === 'Sức khỏe' && typeof was.sk === 'number') n.sk = clamp(was.sk + v);
      else if (what.startsWith('Linh khí ') && S.lk && HE[what.slice(9)]) { const h = HE[what.slice(9)]; S.lk[h] = clamp((S.lk[h] || 0) + v); }
      else if (ATTR.includes(what) && Array.isArray(S.attr)) { const i = ATTR.indexOf(what); S.attr[i] = Math.min(100, S.attr[i] + v); }
    }
    return r;
  };

  // ---------- the bag's care goods ----------
  const use0 = useItem;
  globalThis.useItem = function (i) {
    const it = S.items[i], n = S.need;
    if (it && it.use === 'medicine' && /herbal/.test(it.file)) {            // Viên thảo dược: no illness for a day
      if (S.sick) return toast(`${DATA.pet.name} đang ốm rồi, cần Thuốc chữa ốm`);
      S.phongOm = Date.now() + DAY;
      if (typeof act === 'function') act('happy', { loops: 1 });
      toast('Phòng ốm 1 ngày');
      return consume(i);
    }
    const was = it && { sach: n.sach, vui: n.vui };
    const r = use0.apply(this, arguments);
    if (it && it.use === 'bath') n.sach = clamp(was.sach + 40);
    if (it && it.use === 'ball' && n.vui > was.vui) n.vui = clamp(was.vui + 20);
    return r;
  };

  // ---------- no illness while Viên thảo dược holds ----------
  const tick0 = tickNeeds;
  globalThis.tickNeeds = function (dt, now) {
    const sick0 = S.sick, toast0 = S.toast, r = tick0.apply(this, arguments);
    if (!sick0 && S.sick && (S.phongOm || 0) > Date.now()) {
      S.sick = false;
      if (S.toast !== toast0 && /ốm/.test(S.toast || '')) S.toast = toast0;
    }
    return r;
  };
})();
