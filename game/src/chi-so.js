// Elemon: the pet's numbers, one set for the whole game (THIET-KE.md mục 6, the user's call 28/10/2026). Before it,
// Vùng đất, Solo and the stats screen each had their own: the six attributes were the sample pet's (Bông) for every
// pet, Solo was 100 HP whatever the level, and fighting cost almost nothing at home.
//   - six attributes (S.attr, 0-100 each, gems on top up to 120): from the egg, +1 a level (shared out by Linh khí),
//     food of an element (+0.25 to its two, at most +1 a day), Võ đường (+1 a day for each lesson, Solo won: Tinh thần)
//   - one formula for the pet, the foes and the bosses (__chiSo.of): Máu, Công, Kỹ năng, Linh lực, Thủ, Kháng hệ,
//     Tốc, Né, Chí mạng; low needs make the pet fight worse (__chiSo.pet)
//   - Sức khỏe (S.need.sk, 0-100) is the HP that lasts: a fight takes 30% of the HP lost in it, fainting leaves 10;
//     sleep, Mộc food and medicine bring it back; under 30 the pet falls ill easily, under 15 it cannot fight
//   - what a fight costs at home (__chiSo.cost) and how much stronger one side is in Solo (__chiSo.pow, capped x1.5)
//   - the arena's hooks for this (__chiSoSrc): the start HP, the power ratio, x0.75 when the foe overcomes
(() => {
  const PAIR = { hoa: [0, 1], thuy: [3, 4], tho: [2, 4], moc: [2, 5], kim: [0, 2] };   // = the gems' (preview_ui_stats.py)
  const HES = Object.keys(PAIR);
  const START = 10, START_EL = 15, BASE_CAP = 100, CAP = 120;
  const FOOD_STEP = 0.25, FOOD_DAY = 1;                     // per attribute a meal, all food together a day
  const SK_SLEEP = 5, SK_MOC = 2, SK_FOOD = 10, SK_MEDS = 40, SK_SICK = 30, SK_FIGHT = 15, SK_FAINT = 10, SK_LOSS = 0.3;
  const POW_MAX = 1.5;
  // Linh khí's own effects, at 100 (half at 50): Kim Thủ +15 and hunger x0.75, Hỏa Công +15% and hunger x1.25, Thủy Vui
  // drops x0.7 as fast and the mini games (fishing, cooking) 20% easier, Thổ sleep gives back energy x1.5, Mộc Sức khỏe
  // +2 an hour and falls ill only under 20
  const LK_KIM_THU = 15, LK_KIM_DOI = 0.25, LK_HOA_ATK = 0.15, LK_HOA_DOI = 0.25, LK_THUY_VUI = 0.3, LK_THUY_DE = 0.2,
        LK_THO_NGU = 0.5, LK_MOC_OM = 10;
  const SLEEP_PER_MS = 10 / 60e3;                           // Năng lượng asleep, as game/src/song-that.js gives it
  const lkK = he => Math.min(100, (typeof S === 'object' && S && S.lk && S.lk[he]) || 0) / 100;
  globalThis.__lkDe = () => 1 + LK_THUY_DE * lkK('thuy');   // a mini game's ease (scripts/evo_app.html: fishing, cooking)
  const day = () => Math.floor(Date.now() / 864e5);
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const need = () => S.need;

  // ---------- the attributes ----------
  function grow(points) {                                   // level points, shared out by Linh khí
    const lk = S.lk || {}, sum = HES.reduce((s, h) => s + (lk[h] || 0), 0), el = EL();
    for (const h of HES) {
      const share = sum > 0 ? (lk[h] || 0) / sum : h === el ? 1 : 0;
      for (const i of PAIR[h]) S.attr[i] = Math.min(BASE_CAP, S.attr[i] + points * share / 2);
    }
  }
  function ensure() {
    if (typeof S !== 'object' || !S || !S.need || typeof EL !== 'function') return false;
    if (typeof S.need.sk !== 'number') S.need.sk = S.sick ? 40 : 100;
    if (!Array.isArray(S.attr)) {                           // a new pet, or a save from before: what its levels gave
      S.attr = [START, START, START, START, START, START];
      for (const i of PAIR[EL()] || []) S.attr[i] = START_EL;
      S.attrLv = 1;
    }
    if ((S.level || 1) > (S.attrLv || 1)) { grow(S.level - (S.attrLv || 1)); S.attrLv = S.level; }
    if (!S.attrDay || S.attrDay.d !== day()) S.attrDay = { d: day(), food: 0, train: {} };
    return true;
  }
  function attrs() {                                        // with the gems, as the fights read them
    ensure();
    const b = typeof gemBonus === 'function' ? gemBonus() : [0, 0, 0, 0, 0, 0];
    return S.attr.map((v, i) => Math.min(CAP, v + (b[i] || 0)));
  }
  const NAMES = ['Sức mạnh', 'Nhanh nhẹn', 'Bền bỉ', 'Thông minh', 'Trí tuệ', 'Tinh thần'];
  // a meal of element he: its two attributes, a little; Mộc food is good for the health too
  globalThis.__anMon = he => {
    if (!ensure() || !PAIR[he]) return;
    const left = FOOD_DAY - S.attrDay.food, step = Math.min(FOOD_STEP, left / 2);
    if (step > 0) { for (const i of PAIR[he]) S.attr[i] = Math.min(BASE_CAP, S.attr[i] + step); S.attrDay.food += step * 2; }
    if (he === 'moc') S.need.sk = Math.min(100, S.need.sk + SK_FOOD);
  };
  // a cooked dish eaten (scripts/evo_app.html BUFF_N): Mộc, Sức khỏe +15 a star at once; the others, a buff for the
  // next trip or Solo match (one at a time, the newest kept): Hỏa Sức mạnh, Thủy Nhanh nhẹn, Thổ Bền bỉ +4 a star,
  // Kim Thủ +5 a star
  const BUFF_ATTR = { hoa: 0, thuy: 1, tho: 2 }, BUFF_NAME = { hoa: 'Sức mạnh', thuy: 'Nhanh nhẹn', tho: 'Bền bỉ', kim: 'Thủ' };
  globalThis.__monNau = (he, stars) => {
    if (!ensure() || !stars) return;
    const n = (typeof BUFF_N === 'object' && BUFF_N[he] || 4) * stars;
    if (he === 'moc') S.need.sk = Math.min(100, S.need.sk + n);
    else if (BUFF_NAME[he]) S.buff = { he, n };
  };
  const buffText = () => S.buff && BUFF_NAME[S.buff.he] ? `${BUFF_NAME[S.buff.he]} +${S.buff.n}` : '';
  const buffUsed = () => { if (S.buff) S.buff = null; };
  // a Võ đường lesson done: +1 to its attribute once a day ('dam' Sức mạnh, 'ne' Nhanh nhẹn, 'solo' won: Tinh thần)
  globalThis.__tapXong = kind => {
    const i = { dam: 0, ne: 1, solo: 5 }[kind];
    if (!ensure() || i === undefined || S.attrDay.train[kind]) return '';
    S.attrDay.train[kind] = 1;
    S.attr[i] = Math.min(BASE_CAP, S.attr[i] + 1);
    return `${NAMES[i]} +1`;
  };

  // ---------- the fighting numbers ----------
  // a = [Sức mạnh, Nhanh nhẹn, Bền bỉ, Thông minh, Trí tuệ, Tinh thần]
  function of(lv, a) {
    return { lv, hp: Math.round(80 + 4 * lv + 3 * a[2]), atk: 8 + 0.4 * lv + 0.4 * a[0], skill: 12 + 0.5 * lv + 0.5 * a[3],
             mp: Math.round(60 + 0.4 * lv + 1.5 * a[4]), thu: 0.5 * lv + 0.5 * a[2], khang: a[4] * 0.003,
             spd: 120 + 0.8 * a[1], ne: a[1] * 0.0015, crit: 0.04 + a[5] * 0.002, mpRegen: 1 };
  }
  const foeAttrs = lv => { const v = Math.min(BASE_CAP, 10 + 0.5 * lv); return [v, v, v, v, v, v]; };
  // the pet as it is now: low needs make it fight worse (THIET-KE.md 6.6)
  function pet() {
    ensure();
    const a = attrs(), b = S.buff;
    if (b && BUFF_ATTR[b.he] !== undefined) a[BUFF_ATTR[b.he]] += b.n;     // a dish's buff, for this trip / match
    const st = of(S.level || 1, a), n = need(), why = [];
    if (b && b.he === 'kim') st.thu += b.n;
    st.thu += LK_KIM_THU * lkK('kim'); st.atk *= 1 + LK_HOA_ATK * lkK('hoa');   // Linh khí: Kim guards, Hỏa hits harder
    st.buff = buffText();
    if (n.nl < 30) { st.atk *= 0.85; st.skill *= 0.85; st.spd *= 0.9; why.push('mệt'); }
    if (n.no < 20) { st.mpRegen = 0.5; why.push('đói'); }
    if (n.vui < 30) { st.crit /= 2; why.push('buồn'); }
    else if (n.vui >= 80) st.atk *= 1.05;
    st.why = why;
    return st;
  }
  const luc = st => Math.round(st.hp / 4 + st.atk + st.skill);    // Lực chiến: the two sides of a Solo match compared
  // Solo: each side's damage times the power ratio (at most x1.5, at least x0.67); hp0: the pet's HP at the start
  function pow(foeLv, foeK = 1) {
    const me = luc(pet()), foe = luc(of(foeLv, foeAttrs(foeLv))) * foeK, r = me / foe;
    return { me: clamp(r, 1 / POW_MAX, POW_MAX), foe: clamp(1 / r, 1 / POW_MAX, POW_MAX), hp0: clamp(need().sk, 1, 100) / 100,
             luc: me, lucFoe: Math.round(foe) };
  }
  // a foe on the map (a Hư Ảnh: 40% of a pet's HP of its level, its blows 45% of its Công), K its kind's factors
  function mob(lv, K) {
    const st = of(lv, foeAttrs(lv));
    return { hp: Math.round(st.hp * 0.4 * K.hp), dmg: st.atk * 0.45 * K.dmg };
  }

  // ---------- fighting at home: costs, health ----------
  const COST = {                                            // [Năng lượng, No, Vui, Sạch]
    khu: [-6, -4, 0, -8], clear: [0, 0, 8, 0], down: [-10, 0, -15, 0],
    soloWin: [-8, -4, 8, -3], soloLose: [-8, -4, -6, -3], train: [-10, -5, 5, -5],
  };
  function cost(kind) {
    const c = COST[kind], n = need();
    if (!c || !ensure()) return;
    ['nl', 'no', 'vui', 'sach'].forEach((k, i) => { n[k] = clamp((n[k] || 0) + c[i], 0, 100); });
    if (kind === 'down') n.sk = Math.min(n.sk, SK_FAINT);
  }
  // HP lost in a fight, as a share of the full bar (0-100): 30% of it comes off Sức khỏe
  function hurt(lostPct) { if (ensure() && lostPct > 0) need().sk = clamp(need().sk - SK_LOSS * lostPct, 0, 100); }
  // may the pet set out to fight: '' yes, else why not
  function fit(nlMin) {
    ensure();
    if (S.sick) return 'đang ốm';
    if (need().sk < SK_FIGHT) return `sức khỏe dưới ${SK_FIGHT}`;
    if (need().nl < nlMin) return `năng lượng dưới ${nlMin}`;
    return '';
  }

  // the clock: health back while asleep and with Mộc Linh khí; a weak pet falls ill on less. Linh khí shapes the needs
  // too (THIET-KE.md mục 2): Kim hungry slower, Hỏa hungry faster, Thủy stays cheerful longer, Thổ sleeps energy back
  // faster, Mộc falls ill less (a demo second's decay is scaled after the page has taken it)
  const tick0 = tickNeeds;
  globalThis.tickNeeds = function (dt, now) {
    const n0 = typeof S === 'object' && S && S.need, no0 = n0 && n0.no, vui0 = n0 && n0.vui;
    tick0(dt, now);
    if (!ensure()) return;
    const n = need(), h = dt / 3600e3, sick0 = S.sick;
    if (n === n0 && n.no < no0) n.no = clamp(no0 - (no0 - n.no) * (1 + LK_HOA_DOI * lkK('hoa') - LK_KIM_DOI * lkK('kim')), 0, 100);
    if (n === n0 && n.vui < vui0) n.vui = clamp(vui0 - (vui0 - n.vui) * (1 - LK_THUY_VUI * lkK('thuy')), 0, 100);
    if (S.night > 0.5) n.nl = Math.min(100, n.nl + dt * SLEEP_PER_MS * LK_THO_NGU * lkK('tho'));
    n.sk = Math.min(100, n.sk + h * ((S.night > 0.5 ? SK_SLEEP : 0) + SK_MOC * lkK('moc')));
    const sickAt = SK_SICK - LK_MOC_OM * lkK('moc');
    if (!S.sick && (n.sk < 5 || (n.sk < sickAt && (n.sach < 30 || n.no < 20)))) {
      S.sick = true; S.act = null;
      if (!sick0 && typeof toast === 'function') toast(`${DATA.pet.name} yếu quá nên bị ốm rồi! Cho uống thuốc nhé`);
    }
  };
  // medicine: well again and +40 health; a weak pet (under 60) may take it without being ill
  if (typeof useItem === 'function') {
    const use0 = useItem;
    globalThis.useItem = function (i) {
      const it = S.items[i], meds = it && it.use === 'medicine' && ensure();
      const weak = meds && !S.sick && need().sk < 60;
      if (weak) S.sick = true;                              // the page gives medicine to an ill pet only
      const was = S.sick, r = use0.apply(this, arguments);
      if (meds && was && !S.sick) need().sk = Math.min(100, need().sk + SK_MEDS);
      return r;
    };
  }

  // ---------- the arena's hooks (its script is not edited: game/src/solo.js and vung-dat.js run a hooked copy) ----------
  const HOOKS = [
    ['  P = fighter(170, 300, 0, false); B = fighter(470, 300, Math.PI, true);',
     '  P = fighter(170, 300, 0, false); B = fighter(470, 300, Math.PI, true);\n' +
     '  globalThis.__soloSeen = { P: () => P, B: () => B, over: () => over, score };\n' +
     '  if (globalThis.__soloPow) P.hp = Math.max(1, Math.round(MAX_HP * __soloPow.hp0));'],
    ["  if (khac) { dmg *= KHAC_X; if (!soft) say(f, 'Khắc!', '#ff8a3a'); }",
     "  if (khac) { dmg *= KHAC_X; if (!soft) say(f, 'Khắc!', '#ff8a3a'); }\n" +
     '  else if (KHAC[f.el] === by.el) dmg *= 0.75;\n' +
     '  if (globalThis.__soloPow && by !== f) dmg *= by === P ? __soloPow.me : f === P ? __soloPow.foe : 1;'],
  ];
  globalThis.__chiSoSrc = src => {
    for (const [a] of HOOKS) if (!src.includes(a)) { console.log('chi-so: the Solo arena has changed, no hook at: ' + a.slice(0, 50)); return src; }
    for (const [a, b] of HOOKS) src = src.replace(a, b);
    return src;
  };

  globalThis.__chiSo = { attrs, of, pet, luc, pow, mob, cost, hurt, fit, ensure, NAMES, buffText, buffUsed };
})();
