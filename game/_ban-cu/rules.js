// HoLua — the numbers of the game in one place (THIET-KE.md; the figures are placeholders until balanced).
// Times are in hours of real time; needs, Linh khí and attributes run 0..100.
const RULES = {
  start: { coins: 1000, bag: [['Hoa_1_roasted-chili-pepper', 5], ['Tho_1_roasted-corn', 3], ['DacBiet_1_healing-medicine-bottle', 1]] },
  // what each need loses an hour, awake / asleep (Năng lượng fills up while asleep)
  need: {
    no: { awake: -12, asleep: -5 },
    vui: { awake: -8, asleep: -2 },
    nl: { awake: -7, asleep: 20 },
  },
  // droppings: one every few hours awake (sooner after a big meal), at most 3 on the floor; each takes Sạch down
  poop: { every: 2.5, afterMeal: 0.6, max: 3, sachPerHour: -12 },
  // Sức khỏe: falls while a need is empty, comes back slowly while all are fine; under `sick` the pet is ill
  health: { emptyPerHour: -9, okPerHour: 2, okAbove: 30, sick: 35, sickVuiFaster: 1.5 },
  sleep: { wakeAt: 100 },               // asleep with the lights out until Năng lượng is full (or A)
  // time away: simulated in steps, at most this long (a clock gone wrong never empties everything)
  offline: { step: 1 / 12, max: 72 },
  autosaveMs: 20000,
};

// 5 elements: the two attributes each one feeds (THIET-KE.md "Liên kết với Ngũ Hành"), names
const ELEMENTS = {
  hoa: { name: 'Hỏa', attrs: [0, 1] }, kim: { name: 'Kim', attrs: [0, 2] }, moc: { name: 'Mộc', attrs: [2, 5] },
  thuy: { name: 'Thủy', attrs: [3, 4] }, tho: { name: 'Thổ', attrs: [2, 4] },
};
const ATTRS = ['Sức mạnh', 'Nhanh nhẹn', 'Bền bỉ', 'Thông minh', 'Trí tuệ', 'Tinh thần'];
// file prefix of the foods -> element
const FOOD_HE = { Hoa: 'hoa', Kim: 'kim', Moc: 'moc', Thuy: 'thuy', Tho: 'tho' };
// X beats Y (tương khắc): a pet does not like the food of the element that beats its own
const BEATS = { kim: 'moc', moc: 'tho', tho: 'thuy', thuy: 'hoa', hoa: 'kim' };

// every food: Vietnamese name, price; effects follow from element and tier (foodEffect)
const FOOD_NAMES = {
  Hoa: ['Ớt nướng', 'Xiên thịt nướng', 'Táo lửa', 'Bánh bao dung nham', 'Khoai nướng than', 'Thanh long lửa',
        'Trứng phượng chiên', 'Kẹo lõi dung nham'],
  Kim: ['Bánh quy sắt', 'Cá bạc', 'Óc chó thép', 'Kẹo đá pha lê', 'Tảng muối khoáng', 'Lê vàng', 'Bánh trăng sao kim',
        'Quả mọng kim cương'],
  Moc: ['Bó lá non', 'Hạt dẻ sồi', 'Nấm mật ong', 'Măng tre', 'Giỏ quả rừng', 'Miếng dưa ngọc', 'Hạt sen linh',
        'Quả cây thế giới'],
  Thuy: ['Cá tươi', 'Cuộn rong biển', 'Sò ngọc trai', 'Thạch xanh', 'Bánh bao băng', 'Tôm san hô', 'Bình nước trăng',
         'Vảy rồng biển'],
  Tho: ['Bắp nướng', 'Khoai nướng đất', 'Bao đậu phộng', 'Bí ngô vàng', 'Tổ ong mật', 'Chà là cát', 'Cơm nắm vàng',
        'Nhân sâm núi'],
};
const FOOD_PRICE = [20, 35, 60, 90, 120, 160, 400, 650];
// special items (DacBiet_<n>): name, price, shop tab (2 Thuốc, 3 Đặc biệt), what they do, locked line or ''
const SPECIAL = {
  1: { name: 'Thuốc chữa ốm', price: 80, tab: 2, line: 'Hết ốm · Sức khỏe +40', fx: { cure: 1, khoe: 40 } },
  2: { name: 'Viên thảo dược', price: 40, tab: 2, line: 'Không ốm trong 1 ngày', fx: { guard: 24, khoe: 10 } },
  3: { name: 'Kẹo vitamin', price: 30, tab: 2, line: 'Vui +15', fx: { vui: 15 } },
  4: { name: 'Nước tăng lực', price: 45, tab: 2, line: 'Năng lượng +30', fx: { nl: 30 } },
  5: { name: 'Xà phòng tắm', price: 25, tab: 2, line: 'Sạch +40', fx: { sach: 40 } },
  6: { name: 'Bóng đồ chơi', price: 70, tab: 3, line: 'Chơi (R2) vui gấp đôi', fx: { toy: 1 }, keep: true },
  7: { name: 'Đá tiến hóa', price: 900, tab: 3, line: 'Cần Lv 20 để dùng', fx: {}, locked: 'Cần Lv 20 để dùng' },
  8: { name: 'Ngọc Hồn', price: 0, tab: 3, line: 'Chỉ rơi từ boss', fx: {}, locked: 'Chỉ rơi từ boss' },
};

function foodInfo(file) {
  const [pre, n] = file.split('_');
  if (pre === 'DacBiet') {
    const s = SPECIAL[+n];
    return { file, he: null, tier: +n, name: s.name, price: s.price, special: s, line: s.line };
  }
  const tier = +n, he = FOOD_HE[pre], fx = foodEffect(he, tier);
  return { file, he, tier, name: FOOD_NAMES[pre][tier - 1], price: FOOD_PRICE[tier - 1], fx, line: effectLine(he, fx) };
}

// an element food: fills No by tier, feeds its element's Linh khí and (from tier 5) its two attributes, and does
// what that element does (THIET-KE.md "Thức ăn gắn với hệ"): Hỏa +Năng lượng, Thủy +Vui, Mộc +Sức khỏe,
// Kim fills less but feeds more Linh khí, Thổ fills more and adds weight
function foodEffect(he, tier) {
  const fx = { no: 8 + 3 * tier, linh: { [he]: 2 + tier }, attr: {} };
  if (tier >= 5) for (const a of ELEMENTS[he].attrs) fx.attr[a] = tier >= 7 ? 2 : 1;
  if (tier >= 3) fx.vui = 2 * tier;
  if (he === 'hoa') fx.nl = 4 + tier;
  if (he === 'thuy') fx.vui = (fx.vui || 0) + 5;
  if (he === 'moc') fx.khoe = 2 + tier;
  if (he === 'kim') { fx.no = Math.round(fx.no * 0.8); fx.linh.kim += 2; }
  if (he === 'tho') { fx.no = Math.round(fx.no * 1.3); fx.weight = 0.3; }
  return fx;
}

function effectLine(he, fx) {
  const out = [];
  if (fx.no) out.push(`No +${fx.no}`);
  if (fx.vui) out.push(`Vui +${fx.vui}`);
  if (fx.nl) out.push(`Năng lượng +${fx.nl}`);
  if (fx.khoe) out.push(`Sức khỏe +${fx.khoe}`);
  for (const [k, v] of Object.entries(fx.linh || {})) out.push(`Linh khí ${ELEMENTS[k].name} +${v}`);
  for (const [a, v] of Object.entries(fx.attr || {})) out.push(`${ATTRS[a]} +${v}`);
  return out.join(' · ');
}

const clamp = (v, lo = 0, hi = 100) => Math.max(lo, Math.min(hi, v));

// time passing for the pet: dt hours (small steps; offline time is cut into RULES.offline.step pieces)
function simulate(g, dt, rnd = Math.random) {
  const p = g.pet;
  if (!p || p.stage === 'egg') return;
  const asleep = p.asleep, R = RULES;
  p.need.no = clamp(p.need.no + R.need.no[asleep ? 'asleep' : 'awake'] * dt);
  p.need.vui = clamp(p.need.vui + R.need.vui[asleep ? 'asleep' : 'awake'] * dt * (p.sick ? R.health.sickVuiFaster : 1));
  p.need.nl = clamp(p.need.nl + R.need.nl[asleep ? 'asleep' : 'awake'] * dt);
  // droppings while awake, sooner after eating
  if (!asleep) {
    p.poopIn -= dt;
    if (p.poopIn <= 0) {
      if (p.poop.length < R.poop.max) p.poop.push(Math.round(150 + rnd() * 340));
      p.poopIn = R.poop.every * (0.7 + 0.6 * rnd());
    }
  }
  p.need.sach = clamp(p.need.sach + R.poop.sachPerHour * p.poop.length * dt);
  // health
  const empty = p.need.no <= 0 || p.need.vui <= 0 || p.need.sach <= 0 || p.need.nl <= 0;
  const fine = ['no', 'vui', 'sach', 'nl'].every(k => p.need[k] >= R.health.okAbove);
  const guarded = p.guardUntil && g.t < p.guardUntil;
  if (empty && !guarded) p.need.khoe = clamp(p.need.khoe + R.health.emptyPerHour * dt);
  else if (fine && !p.sick) p.need.khoe = clamp(p.need.khoe + R.health.okPerHour * dt);
  if (p.need.khoe < R.health.sick && !guarded) p.sick = true;
  if (asleep && p.need.nl >= R.sleep.wakeAt) { p.asleep = false; p.wokeUp = true; }
}

// apply a food or item to the pet
function feed(g, info) {
  const p = g.pet, fx = info.special ? info.special.fx : info.fx;
  for (const k of ['no', 'vui', 'nl', 'khoe', 'sach']) if (fx[k]) p.need[k] = clamp(p.need[k] + fx[k]);
  for (const [k, v] of Object.entries(fx.linh || {})) p.linh[k] = clamp(p.linh[k] + v);
  for (const [a, v] of Object.entries(fx.attr || {})) p.attr[a] = clamp(p.attr[a] + v);
  if (fx.weight) p.weight = Math.min(40, p.weight + fx.weight);
  if (fx.cure) p.sick = false;
  if (fx.guard) p.guardUntil = g.t + fx.guard * 3600e3;
  if (!info.special) p.poopIn = Math.min(p.poopIn, RULES.poop.afterMeal + RULES.poop.every * 0.5);
}

function newPet(cid, stage, he) {
  return { cid, stage, name: 'Bông', level: 1, exp: 0, born: Date.now(),
           need: { no: 70, vui: 70, sach: 100, nl: 80, khoe: 100 },
           linh: { hoa: 0, kim: 0, moc: 0, thuy: 0, tho: 0, [he]: 10 }, attr: [10, 10, 10, 10, 10, 10],
           poop: [], poopIn: RULES.poop.every, sick: false, guardUntil: 0, asleep: false,
           weight: 10, closeness: 1, personality: 'hieu-dong' };
}
