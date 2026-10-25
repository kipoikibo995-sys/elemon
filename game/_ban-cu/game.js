// HoLua — the game. 640x480, buttons as on the R36S. Runs in a browser (build/game/index.html) and on the handheld
// (r36s/jsrt.c + r36s/js/shim.js). Built from MiniMon's approved demo (scripts/evo_app.html): same screens and look,
// with a real pet that lives on — saved, real time, every creature, every room. Numbers: rules.js.

// ---------- platform ----------
const ctx = document.getElementById('c').getContext('2d');
const native = typeof __cv !== 'undefined';
// sounds: native on the handheld, <audio> in a browser (index.html)
const sfx = (name, vol = 220) => { if (globalThis.SOUND) SOUND.sfx(name, vol); };
const music = name => { if (globalThis.SOUND) SOUND.music(name); };
const SAVE_KEY = 'holua-save';

// ---------- loading ----------
const IMG = {};
// many small pictures at once: a load can fail when the browser runs short of sockets, so try again a few times
function load(name, path, tries = 5) {
  if (IMG[name]) return Promise.resolve(IMG[name]);
  return new Promise(ok => {
    const im = new Image();
    im.onload = () => { IMG[name] = im; ok(im); };
    im.onerror = () => tries > 1 ? setTimeout(() => load(name, path, tries - 1).then(ok), 300) : ok(null);
    im.src = path;
  });
}
const json = path => fetch(path).then(r => r.json());
const NEEDS = [['icon_no', 'cam', 'no'], ['icon_vui', 'hong', 'vui'], ['icon_sach', 'xanh-duong', 'sach'],
               ['icon_nang-luong', 'xanh-reu', 'nl']];
// 4 care actions (play is on R2, decorating on Start; shop and training are in the village behind "Ra ngoài")
const MENU = [['nut_cho-an', 'Ăn'], ['nut_don-dep', 'Dọn'], ['nut_ngu', 'Ngủ / Đèn'], ['nut_ra-ngoai', 'Ra ngoài']];
const UI = ['nen', 'bar', 'coin_box', 'badge', 'o_chon', 'panel', 'picker', 'o_hang', 'o_hang-chon',
  'bong_tim', 'bong_vui', 'bong_doi', 'bong_buon-ngu', 'bong_gian', 'bong_buon', 'bong_om', 'vun-do-an', 'lap-lanh',
  'tim_nho', 'tim_vua', 'z_nho', 'z_vua', 'z_to', 'cot-sang', 'cot-set', 'no-sang', 'vong-song', 'hat-sang',
  'hat_vang', 'hat_trang', 'hat_lua', 'hat_xoay', 'bang-ron', 'phan_nho', 'phan_vua', 'phan_to', 'ruoi_0', 'ruoi_1',
  'ruoi_2', 'mo-hoi', ...MENU.map(m => m[0]), ...NEEDS.map(n => n[0]), ...NEEDS.map(n => 'fill_' + n[1]),
  'gem_cell', 'gem_cell_sel', 'gem_panel', 'tia-sang', ...DATA.gems.rows.map(r => r.fill),
  ...Object.keys(DATA.gems.attrs).flatMap(he => [1, 2, 3, 4, 5].flatMap(g => [`gem_${he}_${g}`, `gemb_${he}_${g}`])),
  'map', 'map_info', 'mui-ten_xuong', 'mui-ten_len', ...Object.keys(DATA.map.layers),
  'shop_bg', 'chu-quan', 'bong_trong', 'tab_sel', 'shelf_o_hang', 'shelf_o_hang-chon', 'shelf_o_hang-khoa', 'nhan-gia',
  'shop_desc', 'nut_mua', 'nut_ban', ...DATA.shopTabs.map(t => t.icon),
  ...['hoa', 'kim', 'moc', 'thuy', 'tho'].flatMap(he => [0, 1, 2, 3].map(i => `xoay_${he}_${i}`))];
const STATS_UI = ['bar', 'badge', 'cards', 'exp_bar', 'exp_fill', 'gem_frame', 'radar', 'socket', 'tab_cham-do',
  'tab_chon', 'tab_thuong', 'tim-day', 'tim-nua', 'tim-rong', 'weight_bar', 'weight_mark', 'icon_nha',
  'icon_tim-day_big', ...DATA.stats.survival.flatMap(([i, c]) => [i, 'fill_' + c]),
  ...DATA.stats.attributes.flatMap(([i, c]) => [i, 'fill_' + c]), ...DATA.stats.radar.map(r => 'he_' + r[0]),
  'tinh-cach_diem-tinh', 'tinh-cach_ham-an', 'tinh-cach_hien-lanh', 'tinh-cach_hieu-chien', 'tinh-cach_hieu-dong',
  'tinh-cach_kieu-hanh', 'tinh-cach_luoi', 'tinh-cach_to-mo', ...['hoa', 'kim', 'moc', 'thuy', 'tho'].map(h => 'bg_' + h)];
const FOODS = Object.fromEntries(DATA.foods.map(f => [f, foodInfo(f)]));
const icon = (kind, file) => IMG[`${kind}/${file}`];

// a creature at one stage: its frame atlas + frames {name: [x, y, w, h, x on canvas, y on canvas, align dx]} + moves
const SETS = {};
async function loadSet(cid, stage) {
  const key = `${cid}_${stage}`;
  if (SETS[key]) return SETS[key];
  const [set, img] = await Promise.all([json(`pet/${key}.json`), load('pet/' + key, `pet/${key}.png`)]);
  set.img = img; set.cid = cid; set.stage = stage;
  // how far the body reaches from the feet while walking: the pet strolls only where all of it stays on the floor
  const walk = Object.keys(set.frames).filter(n => n.startsWith('walk-'));
  set.reach = Math.max(...(walk.length ? walk : Object.keys(set.frames)).map(n => {
    const [, , w, , ox, , dx] = set.frames[n];
    return Math.max(set.anchor[0] - dx - ox, ox + w - set.anchor[0] + dx);
  }));
  return SETS[key] = set;
}
// a room: empty background + its decor atlas (items and where they go: DATA.rooms)
async function loadRoom(id) {
  await Promise.all([load('room/' + id, `room/${id}.png`), load('room_do/' + id, `room/${id}_do.png`),
                     ...DATA.rooms[id].items.map(it => load(`decor/${id}/${it.id}`, `img/decor/${id}/${it.id}.png`))]);
}

// ---------- the pet on screen ----------
const ease = t => 0.5 - 0.5 * Math.cos(Math.PI * Math.min(1, Math.max(0, t)));
// the gentle standing bounce approved on the stats screen (320 px units)
const BOUNCE = { loop: true, keys: [{ f: 'idle-0', ms: 300, br: -1 }, { f: 'idle-0', ms: 350, y: -1 },
                                    { f: 'idle-0', ms: 350, y: 0 }, { f: 'idle-0', ms: 300 }] };
function total(anim) { return anim.keys.reduce((a, k) => a + k.ms, 0); }
function sample(anim, ms) {           // -> {f, x, y, br} in 640 px, like scripts/preview_anims.py
  let t = anim.loop ? ms % total(anim) : Math.min(ms, total(anim) - 1);
  let prev = { x: 0, y: 0, br: 0 };
  for (const k of anim.keys) {
    const goal = { x: k.x ?? prev.x, y: k.y ?? prev.y, br: k.br ?? 0 };
    if (t < k.ms) {
      const e = ease((t + 1) / k.ms);
      return { f: k.f, x: 2 * (prev.x + (goal.x - prev.x) * e), y: 2 * (prev.y + (goal.y - prev.y) * e),
               br: 2 * (prev.br + (goal.br - prev.br) * e) };
    }
    t -= k.ms; prev = goal;
  }
  const k = anim.keys[anim.keys.length - 1];
  return { f: k.f, x: 2 * prev.x, y: 2 * prev.y, br: 2 * prev.br };
}
const full = document.createElement('canvas'), fctx = full.getContext('2d');
const off = document.createElement('canvas'), octx = off.getContext('2d');
const dark = document.createElement('canvas'), dctx = dark.getContext('2d');
const OUTLINE = '#1a0c06';     // 2 px dark edge so the pet does not sink into a room of its own colour
const EDGE = [[-2, 0], [2, 0], [0, -2], [0, 2], [-1, -1], [1, -1], [-1, 1], [1, 1], [-1, 0], [1, 0], [0, -1], [0, 1]];
// the frame with its upper body lifted by br (lowered when negative), white-out k, glow, dark outline
function drawPet(set, s, fx, fy, white = 0, glow = 0, left = false) {
  const [cw, ch] = set.canvas, [ax, ay] = set.anchor, fr = set.frames[s.f] || set.frames['idle-0'], dx = fr[6];
  full.width = cw; full.height = ch;                       // the frame back on its canvas
  fctx.drawImage(set.img, fr[0], fr[1], fr[2], fr[3], fr[4], fr[5], fr[2], fr[3]);
  const im = full, split = ay - Math.round(ch * 0.4), br = Math.round(s.br), lo = Math.max(0, -br);
  off.width = cw; off.height = ch + 8;
  octx.drawImage(im, 0, split, cw, ch - split, 0, split + 8, cw, ch - split);
  if (br > 0) octx.drawImage(im, 0, split - 1, cw, 1, 0, split + 8 - br - 1, cw, br + 1);
  octx.drawImage(im, 0, lo, cw, split - lo, 0, 8 - br + lo, cw, split - lo);
  if (white > 0) {
    octx.globalCompositeOperation = 'source-atop';
    octx.fillStyle = `rgba(255,255,250,${white})`; octx.fillRect(0, 0, off.width, off.height);
    octx.globalCompositeOperation = 'source-over';
  }
  // facing left: the picture is mirrored around the feet, so the anchor and the shift flip too
  const x = Math.round(left ? fx - s.x - (cw - ax) - dx : fx + s.x - ax + dx), y = Math.round(fy + s.y - ay - 8);
  const put = (c, px, py) => {
    if (!left) return ctx.drawImage(c, px, py);
    ctx.save(); ctx.translate(px + c.width, py); ctx.scale(-1, 1); ctx.drawImage(c, 0, 0); ctx.restore();
  };
  if (glow > 0) { ctx.save(); ctx.shadowColor = `rgba(255,200,90,${glow})`; ctx.shadowBlur = 18; put(off, x, y); ctx.restore(); }
  else {
    dark.width = off.width; dark.height = off.height;
    dctx.drawImage(off, 0, 0); dctx.globalCompositeOperation = 'source-in';
    dctx.fillStyle = OUTLINE; dctx.fillRect(0, 0, dark.width, dark.height); dctx.globalCompositeOperation = 'source-over';
    for (const [ox, oy] of EDGE) put(dark, x + ox, y + oy);
    put(off, x, y);
  }
  return { x, y: y + 8, w: cw, h: ch };
}
// standing still: young stages bounce gently (approved), grown-ups play their own idle loop
function idleOf(set) { return ['baby', 'child', 'teen'].includes(set.stage) ? BOUNCE : set.anims.idle || BOUNCE; }

// ---------- the game (saved) and the screen (not saved) ----------
let G = null;                      // {v, t: when simulated up to, pet, coins, bag: [[file, n]], owned, room, placed, gems, gemBag}
let PET = null, ROOM = null;       // the pet's current set, the current room's data
function newGame(cid = 'hoa-ho', stage = 'baby') {
  const he = DATA.creatures[cid].he;
  return { v: 1, t: Date.now(), created: Date.now(), pet: newPet(cid, stage, he), coins: RULES.start.coins,
           bag: RULES.start.bag.map(([f, n]) => [f, n]), owned: {}, room: 'L1-HO_hang-da', placed: {},
           gems: [null, null, null, null, null],
           gemBag: Object.fromEntries(Object.keys(DATA.gems.attrs).flatMap(h => [1, 2, 3, 4, 5].map(g => [`${h}_${g}`, 0]))) };
}
function saveGame() {
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(G)); } catch (e) { console.log('save failed: ' + e); }
}
function loadGame() {
  try { const t = localStorage.getItem(SAVE_KEY); if (t) return JSON.parse(t); } catch (e) { console.log('save unreadable: ' + e); }
  return null;
}
// bring the pet up to now: real time since the last look, offline time in steps (and never backwards)
function catchUp(now) {
  const dt = (now - G.t) / 3600e3;
  if (dt <= 0) { G.t = now; return 0; }               // the clock went back: nothing is taken away
  const hours = Math.min(dt, RULES.offline.max);
  for (let h = 0; h < hours; h += RULES.offline.step) simulate(G, Math.min(RULES.offline.step, hours - h));
  G.t = now;
  return hours;
}

const NEW_SCREEN = () => ({ mode: 'room', t0: performance.now(), popup: 0, popupGoal: 0, fade: 0, waitA: false,
  cursor: 0, picker: 0, pickerGoal: 0, pick: 0, act: null, actT: 0, night: 0, toast: null, toastT: 0, sparkle: 0,
  bubble: null, bubbleT: 0, stats: null, px: 320, left: false, walk: null, nextWalk: performance.now() + 2500,
  fresh: [], freshT: 0, mapSel: 0, tab: 0, item: 0, buyT: 0, gemMode: null, sock: 0, gp: { r: 0, c: 0 }, gemFx: 0 });
let S = NEW_SCREEN();
const T = { calm: 700, swirl: 1000, pillar: 260, flash: 320, reveal: 700, banner: 600 };
const EVO = {}; let acc = 0;
for (const [k, v] of Object.entries(T)) { EVO[k] = [acc, acc + v]; acc += v; }
const parts = Array.from({ length: 18 }, (_, i) => ({ x: 30 + Math.random() * 580, y: 60 + Math.random() * 380,
  v: 0.02 + Math.random() * 0.04, img: ['hat_vang', 'hat_trang', 'hat_lua', 'hat_xoay'][i % 4] }));
const petName = () => G.pet.name;
const creature = () => DATA.creatures[G.pet.cid];

function text(s, x, y, size, color = '#f0e4ce', align = 'left', bold = true, stroke = 0, base = 'middle') {
  ctx.font = `${bold ? 'bold ' : ''}${size}px Tahoma, sans-serif`;
  ctx.textAlign = align; ctx.textBaseline = base;
  if (stroke) { ctx.lineWidth = stroke; ctx.strokeStyle = '#1a0c06'; ctx.strokeText(s, x, y); }
  ctx.fillStyle = color; ctx.fillText(s, x, y);
}
function toast(s) { S.toast = s; S.toastT = performance.now(); }
function bubble(name) { S.bubble = name; S.bubbleT = performance.now(); }

// ---------- room ----------
function drawHud() {
  ctx.fillStyle = 'rgba(18,11,9,0.88)'; ctx.fillRect(0, 0, 640, 38);
  NEEDS.forEach(([ic, col, key], i) => {
    const x = 8 + i * 104;
    ctx.drawImage(IMG[ic], x, 8); ctx.drawImage(IMG.bar, x + 26, 13);
    const f = IMG['fill_' + col], w = Math.round(4 + (f.width - 8) * G.pet.need[key] / 100);
    ctx.drawImage(f, 0, 0, w, f.height, x + 26, 14, w, f.height);
  });
  drawCoins();
  ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fillRect(444, 34, 186, 4);
  ctx.fillStyle = '#ffd36e'; ctx.fillRect(444, 34, Math.round(186 * expFrac()), 4);
}
function expFrac() { return Math.min(1, G.pet.exp / expNeed(G.pet.level)); }
function expNeed(level) { return 60 + 20 * level; }       // levelling comes with the next step; shown already
function drawCoins() {
  ctx.drawImage(IMG.coin_box, 444, 4); text(G.coins.toLocaleString('en-US'), 548, 19, 15, '#f0e4ce', 'right');
  text('Lv', 566, 19, 13); ctx.drawImage(IMG.badge, 596, 3); text(String(G.pet.level), 612, 19, 13, '#f0e4ce', 'center');
}
function drawTop(title) {
  ctx.fillStyle = 'rgba(18,11,9,0.88)'; ctx.fillRect(0, 0, 640, 38);
  text(title, 14, 19, 18, '#ffd67a'); drawCoins();
}
// the menu sits right on the room (no bar): the chosen button is full bright, a bit bigger, glowing; the rest dimmed
function drawMenu(now) {
  MENU.forEach(([n, label], i) => {
    const im = IMG[n], on = i === S.cursor, k = on ? 1.04 : 1, w = im.width * k, h = im.height * k;
    const cx = 80 + i * 160, y = 476 - h - (on ? Math.round(2 + 2 * Math.sin(now / 200)) : 0);
    ctx.save();
    if (on) { ctx.shadowColor = 'rgba(255,214,90,0.95)'; ctx.shadowBlur = 16; }
    else ctx.filter = 'brightness(0.62) saturate(0.8)';
    ctx.drawImage(im, cx - w / 2, y, w, h);
    ctx.restore();
    if (on) text(label, cx, y - 10, 14, '#ffe6a8', 'center', true, 4);
  });
  text('R2: chơi · Start: trang trí', 630, 52, 12, '#e8d4b0', 'right', false, 3);
}
// the bag: takes the menu bar's place, so the room stays open; B goes back
function drawPicker() {
  const p = ease(S.picker), y = Math.round(480 - IMG.picker.height * p);
  ctx.drawImage(IMG.picker, 10, y);
  text('Túi đồ', 32, y + 16, 14, '#ffd67a');
  text('◀ ▶ chọn · A: dùng · B: quay lại', 610, y + 16, 12, '#b8a080', 'right', false);
  if (!G.bag.length) { text('Túi trống, ra Chợ mua nhé', 240, y + 64, 14, '#b8a080', 'center', false); return; }
  const first = Math.max(0, Math.min(S.pick - 5, G.bag.length - 6));
  G.bag.slice(first, first + 6).forEach(([file, n], j) => {
    const i = first + j, sx = 34 + j * 70, sy = y + 36, f = icon('food', file);
    ctx.drawImage(IMG[i === S.pick ? 'o_hang-chon' : 'o_hang'], sx, sy);
    if (f) ctx.drawImage(f, sx + 28 - f.width / 2, sy + 28 - f.height / 2);
    text('x' + n, sx + 52, sy + 48, 12, '#f0e4ce', 'right', true, 3);
  });
  if (first > 0) text('◀', 22, y + 64, 12, '#ffd67a', 'center');
  if (first + 6 < G.bag.length) text('▶', 450, y + 64, 12, '#ffd67a', 'center');
  const b = FOODS[G.bag[S.pick][0]];
  text(b.name, 462, y + 44, 16);
  const mark = b.file === liked() ? ' · món thích' : b.file === hated() ? ' · món ghét' : '';
  text((b.he ? 'Hệ ' + ELEMENTS[b.he].name : 'Vật phẩm') + mark, 462, y + 64, 12, '#b8a080', 'left', false);
  const e = b.line.split(' · ');
  for (let j = 0; j < e.length && j < 4; j += 2) text(e.slice(j, j + 2).join(' · '), 462, y + 80 + j * 8, 12, '#f0e4ce', 'left', false);
}
// what the pet likes most (its own element's simplest food) and will not eat (that of the element beating it)
function liked() { return Object.keys(FOOD_HE).find(k => FOOD_HE[k] === creature().he) + '_1_' + firstName(creature().he); }
function hated() { const he = Object.keys(BEATS).find(k => BEATS[k] === creature().he); return Object.keys(FOOD_HE).find(k => FOOD_HE[k] === he) + '_1_' + firstName(he); }
function firstName(he) { const pre = Object.keys(FOOD_HE).find(k => FOOD_HE[k] === he); return DATA.foods.find(f => f.startsWith(pre + '_1_')).slice(pre.length + 3); }

function placed(id) { return !!(G.placed[G.room] || {})[id]; }
function drawDecor(front) {
  const atlas = IMG['room_do/' + G.room];
  for (const d of ROOM.items)
    if (placed(d.id) && (d.floor > ROOM.feet) === front)
      ctx.drawImage(atlas, d.atlas[0], d.atlas[1], d.atlas[2], d.atlas[3], d.x, d.y, d.atlas[2], d.atlas[3]);
}
function walkRange() { return [ROOM.floor[0] + PET.reach, ROOM.floor[1] - PET.reach]; }
function moodBubble() {
  const n = G.pet.need;
  if (G.pet.sick) return 'bong_om';
  if (n.no < 25) return 'bong_doi';
  if (n.nl < 20) return 'bong_buon-ngu';
  if (n.vui < 30) return 'bong_buon';
  return null;
}
function drawRoom(now) {
  ctx.drawImage(IMG['room/' + G.room], 0, 0);
  drawDecor(false);
  // droppings on the floor, with flies when the room gets dirty
  G.pet.poop.forEach((x, i) => {
    const im = IMG[['phan_nho', 'phan_vua', 'phan_to'][i % 3]];
    ctx.drawImage(im, x - im.width / 2, ROOM.feet + 10 - im.height);
    if (G.pet.need.sach < 50) ctx.drawImage(IMG['ruoi_' + (Math.floor(now / 90 + i) % 3)],
      x - 7 + 10 * Math.sin(now / 300 + i * 2), ROOM.feet - 30 - im.height + 6 * Math.cos(now / 230 + i));
  });
  let s, act = S.act, at = now - S.actT;
  const anims = PET.anims, FEET_Y = ROOM.feet, [w0, w1] = walkRange();
  if (act && at > total(anims[act.anim]) * (act.loops || 1) && !act.hold) { S.act = act = null; }
  if (G.pet.wokeUp) {                                  // slept its fill: up it gets
    G.pet.wokeUp = false; S.act = act = null;
    if (anims.wake) { S.act = act = { anim: 'wake' }; S.actT = now; at = 0; }
    sfx('thuc-day');
  }
  if (G.pet.asleep && (!act || act.anim !== 'sleep') && anims.sleep) { S.act = act = { anim: 'sleep', hold: true }; S.actT = now; at = 0; }
  const sad = G.pet.need.vui < 30 && anims.sad, sick = G.pet.sick && anims.sick;
  const busy = act || S.popup > 0.05 || S.picker > 0.05 || S.night > 0.05 || S.fade > 0 || G.pet.asleep;
  if (S.walk) {
    const t = Math.min(1, (now - S.walk.t0) / S.walk.dur);
    S.px = S.walk.from + (S.walk.to - S.walk.from) * t;
    if (t >= 1 || busy) { S.walk = null; S.nextWalk = now + 2000 + Math.random() * 3000; }
  } else if (!busy && now > S.nextWalk && anims.walk && !sad && !sick && w1 - w0 > 100) {
    // a new spot on the floor, not too close; the body stays clear of the walls
    let to = S.px;
    while (Math.abs(to - S.px) < 90) to = w0 + Math.random() * (w1 - w0);
    S.walk = { from: S.px, to, t0: now, dur: Math.abs(to - S.px) / 70 * 1000 };
    S.left = to < S.px;
  }
  S.px = Math.min(Math.max(S.px, w0), Math.max(w0, w1));
  s = act ? sample(anims[act.anim], at) : S.walk ? sample(anims.walk, now - S.walk.t0)
    : sick ? sample(anims.sick, now) : sad ? sample(anims.sad, now) : sample(idleOf(PET), now);
  const px = Math.round(S.px), front = S.left ? -1 : 1;
  // eating: the food sits on the floor in front of the pet and gets smaller bite by bite (drawn under the head)
  if (act && act.food) {
    const f = icon('food', act.food), k = 1.15 * Math.max(0.45, 1 - at / (total(anims[act.anim]) * (act.loops || 1)));
    if (f) {
      const w = f.width * k, h = f.height * k, fx = px + front * 66;
      ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.beginPath(); ctx.ellipse(fx, FEET_Y, w * 0.45, 4, 0, 0, 7); ctx.fill();
      ctx.drawImage(f, fx - w / 2, FEET_Y - h + 2, w, h);
    }
  }
  const box = drawPet(PET, s, px, FEET_Y, 0, 0, S.left);
  drawDecor(true);
  // items just bought sparkle for a moment the first time the room is seen
  if (S.fresh.length && S.fade === 0) {
    if (!S.freshT) S.freshT = now;
    for (const id of S.fresh) {
      const d = ROOM.items.find(e => e.id === id);
      if (d) ctx.drawImage(IMG['lap-lanh'], d.x + d.atlas[2] / 2 - 13 + 10 * Math.sin(now / 90), d.y + d.atlas[3] / 2 - 13);
    }
    if (now - S.freshT > 1800) { S.fresh = []; S.freshT = 0; }
  }
  const hx = box.x + box.w / 2 + 24, hy = box.y - 38 + Math.round(2 * Math.sin(now / 200));
  if (act && act.food && s.f === 'eat-chew' && Math.floor(at / 130) % 2)
    ctx.drawImage(IMG['vun-do-an'], px + front * 46 - 15, FEET_Y - 12);
  if (act && act.anim === 'happy')
    for (let j = 0; j < 3; j++) ctx.drawImage(IMG[j % 2 ? 'tim_vua' : 'tim_nho'], px - 30 + j * 30, box.y + 30 - ((at / 16 + j * 23) % 60));
  const bub = S.bubble && now - S.bubbleT < 4000 ? S.bubble : moodBubble();
  if (bub && !act && !G.pet.asleep) ctx.drawImage(IMG[bub], hx, hy);
  if (S.sparkle && now - S.sparkle < 900) ctx.drawImage(IMG['lap-lanh'], px - 20 + 40 * Math.sin(now / 90), FEET_Y - 44);
  if (S.night > 0) { ctx.fillStyle = `rgba(8,10,40,${0.62 * S.night})`; ctx.fillRect(0, 0, 640, 480); }
  if (S.night > 0.5) for (let j = 0; j < 3; j++) {
    const ph = (now / 33 + j * 18) % 54;
    ctx.drawImage(IMG[['z_nho', 'z_vua', 'z_to'][j]], px + 30 + j * 10 + ph / 4, box.y - ph);
  }
  // menus open: the room dims a little so they read clearly
  const dim = Math.max(S.picker, S.popup) * 0.18;
  if (dim > 0) { ctx.fillStyle = `rgba(0,0,0,${dim})`; ctx.fillRect(0, 38, 640, 442); }
  drawHud();
  if (S.picker > 0) drawPicker(); else drawMenu(now);
  if (S.popup > 0) drawPopup();
}
function drawPopup() {
  const p = ease(S.popup), y = Math.round(480 - (480 - 140) * p), next = S.popupNext;
  ctx.fillStyle = `rgba(0,0,0,${0.35 * p})`; ctx.fillRect(0, 0, 640, 480);
  ctx.drawImage(IMG.panel, 100, y);
  text(`${petName()} đủ điều kiện tiến hóa!`, 320, y + 34, 18, '#ffd36e', 'center');
  if (next) text(`${creature().name}: ${DATA.stageNames[G.pet.stage]}  →  ${DATA.stageNames[next]}`, 320, y + 66, 15, '#f0e4ce', 'center');
  text('A: Tiến hóa', 230, y + 146, 15, '#f0e4ce', 'center');
  text('B: Để sau', 410, y + 146, 15, '#b8a080', 'center');
}

// ---------- stats screen (SELECT): 4 pages, L1/R1 or ◀ ▶ to turn, B back (laid out as scripts/preview_ui_stats.py) ----------
const ST = DATA.stats, st = n => IMG['st/' + n];
function stext(s, x, y, style, colour = ST.text, align = 'left') {
  const [size, bold] = ST.sizes[style];
  text(s, x, y, size, colour, align, bold, 0, 'top');
}
function sbar(x, y, fillName, value, frame = 'bar') {
  const fr = st(frame), f = st(fillName), cap = Math.round(f.width * 0.085);
  ctx.drawImage(fr, x, y);
  const w = cap + Math.round((f.width - 2 * cap) * Math.min(100, Math.max(0, value)) / 100);
  ctx.drawImage(f, 0, 0, w, f.height, x, y + Math.floor((fr.height - f.height) / 2), w, f.height);
}
const PERSONALITY = { 'diem-tinh': 'Điềm tĩnh', 'ham-an': 'Ham ăn', 'hien-lanh': 'Hiền lành', 'hieu-chien': 'Hiếu chiến',
                      'hieu-dong': 'Hiếu động', 'kieu-hanh': 'Kiêu hãnh', luoi: 'Lười', 'to-mo': 'Tò mò' };
function drawStats(now) {
  const p = G.pet, page = S.stats;
  ctx.drawImage(st('bg_' + creature().he), 0, 0);
  const alert = ['no', 'vui', 'sach', 'nl', 'khoe'].some(k => p.need[k] < 20);
  ST.pages.forEach((name, i) => {
    const x = [42, 182, 324, 466][i], tab = i === page ? 'tab_chon' : i === 0 && alert ? 'tab_cham-do' : 'tab_thuong';
    ctx.drawImage(st(tab), x, tab === 'tab_cham-do' ? 4 : 5);
    stext(name, x + 66, 12, 'tab', i === page ? '#fff5e1' : ST.muted, 'center');
  });
  drawPet(PET, sample(idleOf(PET), now), 130, ST.feet);
  stext(p.name, 130, 410, 'name', ST.text, 'center');
  stext(`${creature().name} · ${DATA.stageNames[p.stage]}`, 130, 432, 'sub', ST.muted, 'center');
  stext({ 3: 'B: quay lại', 2: 'A: khảm ngọc · B: quay lại' }[page] || 'B: quay lại', 632, 462, 'small', ST.muted, 'right');
  stext('L/R: đổi trang', 8, 462, 'small', ST.muted);
  if (page === 0) {
    const vals = [p.need.no, p.need.vui, p.need.sach, p.need.nl, p.need.khoe].map(Math.round);
    const names = ['No', 'Vui', 'Sạch', 'Năng lượng', 'Sức khỏe'];
    ST.survival.forEach(([ic, col], i) => {
      const yc = 122 + 60 * i, im = st(ic);
      ctx.drawImage(im, 292 - Math.floor(im.width / 2), yc - Math.floor(im.height / 2));
      stext(names[i], 320, yc - 27, 'label');
      sbar(318, yc - Math.floor(st('bar').height / 2) + 2, 'fill_' + col, vals[i]);
      stext(String(vals[i]), 612, yc - 9, 'value', vals[i] < 20 ? '#e66e5a' : ST.text, 'right');
    });
    if (p.sick) stext('Đang ốm: cho uống thuốc', 450, 418, 'label', '#e66e5a', 'center');
  } else if (page === 1) drawRadar(p);
  else if (page === 2) {
    const fr = st('gem_frame'), so = st('socket');
    ctx.drawImage(fr, 28, 58);
    for (const [cx, cy] of DATA.gems.sockets) ctx.drawImage(so, cx - Math.floor(so.width / 2), cy - Math.floor(so.height / 2));
    ST.attributes.forEach(([ic], i) => {
      const yc = 110 + 54 * i, im = st(ic);
      ctx.drawImage(im, 292 - Math.floor(im.width / 2), yc - Math.floor(im.height / 2));
      stext(ATTRS[i], 320, yc - 27, 'label');
      ctx.drawImage(st('bar'), 318, yc - Math.floor(st('bar').height / 2) + 2);
    });
    drawAttrLive(now);
  } else drawProfile(p);
}
function drawRadar(p) {
  const rd = st('radar'), rx = 450 - Math.floor(rd.width / 2), ry = 78, cx = rx + rd.width / 2, cy = ry + rd.height * 0.535;
  ctx.drawImage(rd, rx, ry);
  const R = rd.height * 0.44, rmax = R * 0.8, ang = k => k * 72 * Math.PI / 180;
  const pts = ST.radar.map(([key], k) => [cx + rmax * p.linh[key] / 100 * Math.sin(ang(k)), cy - rmax * p.linh[key] / 100 * Math.cos(ang(k))]);
  ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath();
  ctx.fillStyle = '#cd704e'; ctx.fill(); ctx.strokeStyle = '#fab280'; ctx.lineWidth = 2; ctx.stroke();
  ST.radar.forEach(([key, name, colour], k) => {
    const ex = cx + R * Math.sin(ang(k)), ey = cy - R * Math.cos(ang(k)), he = st('he_' + key);
    ctx.drawImage(he, Math.round(ex) - Math.floor(he.width / 2), Math.round(ey) - Math.floor(he.height / 2));
    const [dx, dy] = [[0, -36], [26, -14], [12, 22], [-12, 22], [-26, -14]][k];
    stext(`${name} ${Math.round(p.linh[key])}`, Math.round(ex) + dx, Math.round(ey) + dy, 'label', colour,
          ['center', 'left', 'left', 'right', 'right'][k]);
  });
  stext('Ăn món hệ nào thì Linh khí hệ đó tăng', 450, 408, 'small', ST.muted, 'center');
}
function drawProfile(p) {
  const ox = 276, oy = 58, b = st('badge');
  ctx.drawImage(st('cards'), ox, oy);
  ctx.drawImage(b, ox + 12, oy + 35 - Math.floor(b.height / 2));
  stext(String(p.level), ox + 12 + Math.floor(b.width / 2), oy + 23, 'big', ST.text, 'center');
  stext('Cấp độ', ox + 76, oy + 14, 'small', ST.muted);
  stext(`Level ${p.level}`, ox + 76, oy + 32, 'value');
  stext(`EXP ${Math.floor(p.exp)}/${expNeed(p.level)}`, ox + 330, oy + 14, 'small', ST.muted, 'right');
  sbar(ox + 178, oy + 38, 'exp_fill', 100 * expFrac(), 'exp_bar');
  ctx.drawImage(st('tinh-cach_' + p.personality), ox + 10, oy + 92);
  stext('Tính cách', ox + 52, oy + 88, 'small', ST.muted);
  stext(PERSONALITY[p.personality], ox + 52, oy + 106, 'label');
  ctx.drawImage(st('icon_tim-day_big'), ox + 186, oy + 92);
  stext('Thân thiết', ox + 228, oy + 88, 'small', ST.muted);
  const hw = st('tim-day').width;
  for (let i = 0; i < 5; i++) ctx.drawImage(st(i < p.closeness ? 'tim-day' : 'tim-rong'), ox + 228 + i * (hw + 2), oy + 108);
  [[0, liked(), 'Thích'], [176, hated(), 'Ghét']].forEach(([col, file, title]) => {
    const ic = icon('food', file);
    if (ic) ctx.drawImage(ic, ox + col + 26 - Math.floor(ic.width / 2), oy + 182 - Math.floor(ic.height / 2));
    stext(title, ox + col + 52, oy + 160, 'small', ST.muted);
    stext(FOODS[file].name, ox + col + 52, oy + 178, 'label');
  });
  stext(`Thể trạng · ${Math.round(p.weight)}kg`, ox + 14, oy + 230, 'small', ST.muted);
  const wb = st('weight_bar'), mk = st('weight_mark'), bx = ox + 24, by = oy + 258;
  ctx.drawImage(wb, bx, by);
  const mx = bx + Math.round(wb.width * Math.min(1, Math.max(0, (p.weight - 5) / 30)));
  ctx.drawImage(mk, mx - Math.floor(mk.width / 2), by + Math.floor(wb.height / 2) - Math.floor(mk.height / 2));
  stext('Gầy · Vừa · Mập', ox + 330, oy + 258, 'small', ST.muted, 'right');
  ctx.drawImage(st('icon_nha'), ox + 10, oy + 306);
  stext('Nhà', ox + 52, oy + 302, 'small', ST.muted);
  stext(ROOM.name, ox + 52, oy + 320, 'label');
  stext(ROOM.he ? `Lv${ROOM.level} · hệ ${ELEMENTS[ROOM.he].name}` : 'Lv1', ox + 330, oy + 316, 'label', ST.green, 'right');
}

// ---------- page 3 (Thuộc tính): gem sockets; a socketed gem raises its element's two attributes ----------
const GEM = DATA.gems, HE = Object.keys(GEM.attrs);
function gemBonus() {
  const b = [0, 0, 0, 0, 0, 0];
  for (const g of G.gems) if (g) for (const a of GEM.attrs[g[0]]) b[a] += GEM.grades[g[1] - 1][1];
  return b;
}
function drawAttrLive(now) {
  const bonus = gemBonus();
  GEM.rows.forEach((r, i) => {
    const v = Math.round(G.pet.attr[i]) + bonus[i], f = IMG[r.fill], w = r.cap + Math.round((f.width - 2 * r.cap) * Math.min(100, v) / 100);
    ctx.drawImage(f, 0, 0, w, f.height, r.x, r.y, w, f.height);
    text(String(v), 612, r.yc + 1 - (bonus[i] ? 7 : 0), 17, '#eee2ce', 'right');
    if (bonus[i]) text('+' + bonus[i], 612, r.yc + 15, 12, '#8ce16e', 'right', false);
  });
  GEM.sockets.forEach(([cx, cy], i) => {
    const g = G.gems[i];
    if (g) { const im = IMG[`gem_${g[0]}_${g[1]}`]; ctx.drawImage(im, cx - im.width / 2, cy - im.height / 2); }
    else text('+', cx, cy, 17, '#b0967a', 'center');
    if (S.gemMode && i === S.sock) {
      ctx.strokeStyle = `rgba(255,214,90,${0.65 + 0.35 * Math.sin(now / 150)})`; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(cx, cy, 17, 0, 7); ctx.stroke();
    }
  });
  const fx = (now - S.gemFx) / 600;
  if (fx < 1) {
    const [cx, cy] = GEM.sockets[S.sock], im = IMG['tia-sang'], k = 0.6 + 0.8 * fx;
    ctx.globalAlpha = 1 - fx; ctx.drawImage(im, cx - im.width * k / 2, cy - im.height * k / 2, im.width * k, im.height * k);
    ctx.globalAlpha = 1;
  }
  if (S.gemMode === 'pick') drawGemBag();
  if (S.gemMode) {
    ctx.fillStyle = '#000'; ctx.fillRect(0, 456, 640, 24);
    text(S.gemMode === 'pick' ? 'Mũi tên: chọn ngọc · A: khảm · B: quay lại' : '◀ ▶ chọn ô · A: chọn ngọc · X: gỡ ngọc · B: xong',
         632, 468, 12, '#b0967a', 'right', false);
  }
}
function drawGemBag() {
  const X = 16, Y = 140;
  ctx.drawImage(IMG.gem_panel, X, Y);
  text('Túi ngọc', X + 18, Y + 22, 15, '#ffd67a');
  HE.forEach((he, r) => {
    for (let g = 1; g <= 5; g++) {
      const cx = X + 12 + (g - 1) * 42, cy = Y + 38 + r * 42, n = G.gemBag[`${he}_${g}`], im = IMG[`gemb_${he}_${g}`];
      ctx.drawImage(IMG[S.gp.r === r && S.gp.c === g - 1 ? 'gem_cell_sel' : 'gem_cell'], cx, cy);
      ctx.globalAlpha = n ? 1 : 0.3; ctx.drawImage(im, cx + 20 - im.width / 2, cy + 20 - im.height / 2); ctx.globalAlpha = 1;
      if (n) text('x' + n, cx + 39, cy + 34, 11, '#f0e4ce', 'right', true, 3);
    }
  });
  const he = HE[S.gp.r], [gn, amt] = GEM.grades[S.gp.c];
  text(`Ngọc ${GEM.names[he]} · ${gn}`, X + 18, Y + 266, 14, '#f0e4ce');
  text(GEM.attrs[he].map(a => `${ATTRS[a]} +${amt}`).join(' · '), X + 18, Y + 284, 12, '#8ce16e', 'left', false);
}
function gemInput(btn) {
  if (S.gemMode === 'pick') {
    const d = { LEFT: [0, -1], RIGHT: [0, 1], UP: [-1, 0], DOWN: [1, 0] }[btn];
    if (d) S.gp = { r: (S.gp.r + d[0] + 5) % 5, c: (S.gp.c + d[1] + 5) % 5 };
    if (btn === 'B') S.gemMode = 'sock';
    if (btn === 'A') {
      const he = HE[S.gp.r], g = S.gp.c + 1, key = `${he}_${g}`, old = G.gems[S.sock];
      if (!G.gemBag[key]) return toast('Chưa có viên này');
      if (old) G.gemBag[`${old[0]}_${old[1]}`]++;
      G.gemBag[key]--; G.gems[S.sock] = [he, g]; S.gemFx = performance.now(); S.gemMode = 'sock';
      sfx('sach'); toast(`Đã khảm Ngọc ${GEM.names[he]} · ${GEM.grades[g - 1][0]}`); saveGame();
    }
    return;
  }
  if (btn === 'LEFT' || btn === 'UP') S.sock = (S.sock + 4) % 5;
  if (btn === 'RIGHT' || btn === 'DOWN') S.sock = (S.sock + 1) % 5;
  if (btn === 'B') S.gemMode = null;
  if (btn === 'X') {
    const old = G.gems[S.sock];
    if (!old) return toast('Ô này đang trống');
    G.gemBag[`${old[0]}_${old[1]}`]++; G.gems[S.sock] = null; toast('Đã gỡ ngọc, cất vào túi'); saveGame();
  }
  if (btn === 'A') {
    const g = G.gems[S.sock];
    S.gp = g ? { r: HE.indexOf(g[0]), c: g[1] - 1 } : S.gp;
    S.gemMode = 'pick';
  }
}

// ---------- world map (Ra ngoài): arrows pick a place, A goes in, B goes home ----------
const PL = DATA.map.places;
function layer(name) { const [x, y] = DATA.map.layers[name]; ctx.drawImage(IMG[name], x, y); }
function drawMap(now) {
  ctx.drawImage(IMG.map, 0, 0);
  const sel = PL[S.mapSel];
  for (const p of PL) if (p.kind === 'region') layer('khoa_' + p.key);
  if (sel.kind === 'region') { ctx.globalAlpha = 0.65 + 0.35 * Math.sin(now / 220); layer('chon_' + sel.key); ctx.globalAlpha = 1; }
  else {                                  // a building in the village: a soft gold ring on the ground
    ctx.strokeStyle = `rgba(255,214,90,${0.6 + 0.3 * Math.sin(now / 220)})`; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.ellipse(sel.x, sel.y + 8, 30, 12, 0, 0, 7); ctx.stroke();
  }
  // the only marker on the map: a gold arrow bobbing over the chosen place
  const a = IMG['mui-ten_xuong'], aw = a.width * 1.5, ah = a.height * 1.5;
  ctx.drawImage(a, sel.x - aw / 2, sel.y - 30 - ah + Math.round(4 * Math.sin(now / 150)), aw, ah);
  drawTop('Bản đồ');
  ctx.drawImage(IMG.map_info, 10, 404);
  text(sel.name, 32, 426, 16, '#ffd67a');
  text(sel.line.replace('{pet}', petName()), 32, 450, 13, sel.kind === 'region' ? '#e6a08a' : '#f0e4ce', 'left', false);
  const go = { home: 'A: về phòng', shop: 'A: vào chợ', train: 'A: tập luyện', soon: '', region: '' }[sel.kind];
  text([go, 'B: về nhà'].filter(Boolean).join(' · '), 608, 438, 12, '#b8a080', 'right', false);
}
// the arrow keys pick the nearest place that way
function mapMove(dir) {
  const [ux, uy] = { UP: [0, -1], DOWN: [0, 1], LEFT: [-1, 0], RIGHT: [1, 0] }[dir], c = PL[S.mapSel];
  let best = -1, score = 1e9;
  PL.forEach((p, i) => {
    const dx = p.x - c.x, dy = p.y - c.y, d = Math.hypot(dx, dy), cos = (dx * ux + dy * uy) / (d || 1);
    if (i === S.mapSel || cos < 0.4) return;
    const sc = d * (1 + 2 * (1 - cos));
    if (sc < score) { score = sc; best = i; }
  });
  if (best >= 0) S.mapSel = best;
}
function openMap() { S.mode = 'map'; S.mapSel = 0; S.pickerGoal = 0; S.act = null; music('ngay'); }

// ---------- the shop (Chợ): L1/R1 tabs, arrows pick, A buys, B back to the map ----------
// shelves: 0 every element food, 1 this room's items, 2 medicine and care, 3 special things
function shopRows(tab) {
  if (tab === 0) return DATA.foods.filter(f => !f.startsWith('DacBiet')).map(f => ({ kind: 'food', key: f, ...FOODS[f] }));
  if (tab === 1) return ROOM.items.map(it => ({ kind: 'decor', key: it.id, name: it.name, price: it.price, line: `Đồ phòng ${ROOM.name}` }));
  return DATA.foods.filter(f => f.startsWith('DacBiet') && FOODS[f].special.tab === tab).map(f => ({ kind: 'item', key: f, ...FOODS[f] }));
}
const SAY = () => [`Mua mấy món\nngon cho ${petName()}\nnào!`, `Đủ ${ROOM.items.length} món\n${ROOM.name} là\nlên nhà mới!`,
                   'Có thuốc phòng\nốm nè!', 'Đồ hiếm đây,\nnhìn thử đi!'];
const placedCount = () => ROOM.items.filter(d => placed(d.id)).length;
function stateOf(r) {
  if (r.kind === 'decor') return placed(r.key) ? 'co' : '';
  if (r.special && r.special.locked) return 'khoa';
  if (r.special && r.special.keep && G.owned[r.key]) return 'co';
  return '';
}
function inBag(file) { const e = G.bag.find(b => b[0] === file); return e ? e[1] : 0; }
function shopIcon(r) { return r.kind === 'decor' ? IMG[`decor/${G.room}/${r.key}`] : icon('shop', r.key); }
function drawShop(now) {
  ctx.fillStyle = '#180e0a'; ctx.fillRect(0, 0, 640, 480);
  ctx.drawImage(IMG.shop_bg, 0, 40);
  const kp = IMG['chu-quan']; ctx.drawImage(kp, 4, 480 - kp.height - 30);
  ctx.drawImage(IMG.bong_trong, 118, 150);
  SAY()[S.tab].split('\n').forEach((l, j) => text(l, 182, 186 + j * 15, 12, '#462814', 'center', false));
  drawTop('Cửa hàng');
  DATA.shopTabs.forEach((t, i) => {
    const tx = 176 + i * 54;
    if (i === S.tab) ctx.drawImage(IMG.tab_sel, tx - 4, -1);
    ctx.drawImage(IMG[t.icon], tx, 3);
  });
  text(DATA.shopTabs[S.tab].name, 380, 66, 16, '#ffd67a', 'center');
  const rows = shopRows(S.tab), top = Math.max(0, Math.floor(S.item / 4) - 1);   // 2 rows show at a time
  rows.forEach((r, i) => {
    const row = Math.floor(i / 4) - top;
    if (row < 0 || row > 1) return;
    const sx = 270 + (i % 4) * 90, sy = 84 + row * 104, sta = stateOf(r);
    ctx.drawImage(IMG[sta === 'khoa' ? 'shelf_o_hang-khoa' : i === S.item ? 'shelf_o_hang-chon' : 'shelf_o_hang'], sx, sy);
    const ic = shopIcon(r);
    if (sta !== 'khoa' && ic) {
      if (sta === 'co') ctx.globalAlpha = 0.45;
      ctx.drawImage(ic, sx + 32 - ic.width / 2, sy + 32 - ic.height / 2); ctx.globalAlpha = 1;
    }
    ctx.drawImage(IMG['nhan-gia'], sx - 7, sy + 68);
    text(sta === 'co' ? 'Đã có' : r.price ? String(r.price) : '—', sx + 66, sy + 80, 13, sta === 'co' ? '#8ce16e' : '#f0e4ce', 'right');
    if (i === S.item && now - S.buyT < 700) ctx.drawImage(IMG['lap-lanh'], sx + 40 + 4 * Math.sin(now / 60), sy - 8);
  });
  const bob = Math.round(2 * Math.sin(now / 160));
  if (top > 0) ctx.drawImage(IMG['mui-ten_len'], 608, 80 + bob);
  if ((top + 2) * 4 < rows.length) ctx.drawImage(IMG['mui-ten_xuong'], 608, 266 - bob);
  ctx.drawImage(IMG.shop_desc, 264, 300);
  const r = rows[S.item];
  if (r) {
    text(r.name, 284, 322, 16);
    text(r.line.split(' · ').slice(0, 3).join(' · '), 284, 346, 13, '#f0e4ce', 'left', false);
    text(S.tab === 1 ? `${stateOf(r) === 'co' ? 'Đã đặt trong phòng · ' : ''}Bộ ${ROOM.name}: ${placedCount()}/${ROOM.items.length} món`
         : `Trong túi: ${r.special && r.special.keep ? (G.owned[r.key] ? 'đã có' : 0) : inBag(r.key)}`, 284, 366, 13, '#b8a080', 'left', false);
  }
  const down = now - S.buyT < 140 ? 2 : 0;
  ctx.drawImage(IMG.nut_ban, 264, 412); ctx.drawImage(IMG.nut_mua, 508, 412 + down);
  text('Bán', 324, 428, 14, '#f0e4ce', 'center', true, 2); text('Mua', 568, 428 + down, 14, '#f0e4ce', 'center', true, 2);
  text('L1 / R1: đổi mục · A: mua · B: ra bản đồ', 630, 468, 12, '#b8a080', 'right', false);
}
function buy() {
  const r = shopRows(S.tab)[S.item];
  if (!r) return;
  const sta = stateOf(r);
  if (sta === 'khoa') { sfx('loi'); return toast(r.special.locked); }
  if (sta === 'co') { sfx('loi'); return toast(r.kind === 'decor' ? 'Món này đặt trong phòng rồi' : 'Đã có món này rồi'); }
  if (G.coins < r.price) { sfx('loi'); return toast('Không đủ tiền'); }
  G.coins -= r.price; S.buyT = performance.now(); sfx('xu', 240);
  if (r.kind === 'decor') {                                      // a room item goes straight into the room
    (G.placed[G.room] = G.placed[G.room] || {})[r.key] = 1; S.fresh.push(r.key); S.freshT = 0;
    if (placedCount() === ROOM.items.length) { saveGame(); return toast(`Đủ bộ ${ROOM.name}! Mở được nhà cấp mới`); }
  } else if (r.special && r.special.keep) G.owned[r.key] = 1;  // kept for good (the toy ball)
  else {                                                          // foods and medicine go into the bag
    const e = G.bag.find(b => b[0] === r.key);
    if (e) e[1]++; else G.bag.push([r.key, 1]);
  }
  saveGame();
  toast(`Đã mua ${r.name} (-${r.price})`);
}

// ---------- evolution (the scene; the conditions come with the levelling step) ----------
function inRange(ms, k) { return ms >= EVO[k][0] && ms < EVO[k][1]; }
function frac(ms, k) { return (ms - EVO[k][0]) / (EVO[k][1] - EVO[k][0]); }
function drawEvo(now) {
  const ms = now - S.t0, CX = 320, FY = 330, he = creature().he;
  const bright = ms < EVO.calm[1] ? 0.45 - 0.25 * frac(ms, 'calm') : 0.2;
  ctx.drawImage(IMG.nen, 0, 0);
  ctx.fillStyle = `rgba(0,0,0,${bright})`; ctx.fillRect(0, 0, 640, 480);
  for (const p of parts) {
    const y = ((p.y - ms * p.v) % 420 + 420) % 420 + 30;
    ctx.globalAlpha = 0.8; ctx.drawImage(IMG[p.img], p.x, y, 14, 14 * IMG[p.img].height / IMG[p.img].width); ctx.globalAlpha = 1;
  }
  const before = S.evoFrom, after = S.evoTo, idle = sample(BOUNCE, now);
  if (ms < EVO.swirl[0]) drawPet(before, idle, CX, FY);
  else if (inRange(ms, 'swirl')) {
    const k = frac(ms, 'swirl'), box = drawPet(before, idle, CX, FY, 0.95 * k, 0.9);
    const v = IMG[`xoay_${he}_${Math.floor(ms / 70) % 4}`], h = 70 + 70 * k, w = v.width * h / v.height * 1.6;
    ctx.drawImage(v, CX - w / 2, box.y + box.h * 0.55 - h / 2, w, h);
  } else if (inRange(ms, 'pillar')) {
    drawPet(before, idle, CX, FY, 1, 1);
    const c = IMG[Math.floor(ms / 60) % 2 ? 'cot-set' : 'cot-sang'], h = 420, w = c.width * h / c.height;
    ctx.drawImage(c, CX - w / 2, FY + 30 - h, w, h);
  } else if (inRange(ms, 'flash')) {
    const n = IMG['no-sang'], s = 460;
    ctx.drawImage(n, CX - s / 2, FY - 80 - s / 2, s, s);
    ctx.fillStyle = `rgba(255,255,245,${0.5 + 0.5 * frac(ms, 'flash')})`; ctx.fillRect(0, 0, 640, 480);
  } else {
    const k = inRange(ms, 'reveal') ? 1 - frac(ms, 'reveal') : 0;
    if (k > 0.4) {
      const r = IMG['vong-song'], w = 120 + 300 * (1 - k), h = r.height * w / r.width;
      ctx.drawImage(r, CX - w / 2, FY - 6 - h / 2, w, h);
    }
    drawPet(after, idle, CX, FY, 0.9 * k, k > 0 ? 0.8 : 0);
    if (k > 0) { ctx.fillStyle = `rgba(255,255,245,${0.6 * k})`; ctx.fillRect(0, 0, 640, 480); }
    if (ms >= EVO.banner[0]) {
      const b = IMG['bang-ron'], by = Math.round(-130 + 150 * ease((ms - EVO.banner[0]) / T.banner));
      ctx.drawImage(b, CX - b.width / 2, by);
      if (ms > EVO.banner[0] + 250) text('TIẾN HÓA!', CX, by + b.height * 0.58, 28, '#ffecaa', 'center', true, 5);
      if (ms > EVO.banner[0] + 550)
        text(`${creature().name}  →  ${DATA.stageNames[after.stage]}`, CX, FY + 40, 18, '#ffecaa', 'center', true, 4);
      if (ms > EVO.banner[0] + 1100) {
        S.waitA = true;
        if (Math.floor(now / 450) % 2) text('A: tiếp tục', CX, 452, 14, '#f0e4ce', 'center', true, 3);
      }
    }
  }
}

// ---------- input ----------
function act(anim, extra = {}) { S.act = { anim, ...extra }; S.actT = performance.now(); }
const has = anim => !!PET.anims[anim];
function comeHome() { S.mode = 'room'; music(G.pet.asleep ? 'dem' : 'ngay'); if (has('wave') && !G.pet.asleep) act('wave', { loops: 2 }); }
function useItem(file) {
  const info = FOODS[file];
  if (file === hated() && has('refuse')) {
    S.pickerGoal = 0; G.pet.need.vui = Math.max(0, G.pet.need.vui - 10); bubble('bong_gian');
    act('refuse'); sfx('loi'); toast(`${petName()} không chịu ăn ${info.name}`); return;
  }
  const e = G.bag[S.pick];
  e[1]--;
  if (!e[1]) { G.bag.splice(S.pick, 1); S.pick = Math.min(S.pick, Math.max(0, G.bag.length - 1)); }
  S.pickerGoal = 0;
  const wasSick = G.pet.sick;
  feed(G, info);
  if (file === liked()) { G.pet.need.vui = Math.min(100, G.pet.need.vui + 8); bubble('bong_tim'); }
  else bubble(info.he === creature().he ? 'bong_tim' : 'bong_vui');
  if (wasSick && !G.pet.sick) toast(`${petName()} hết ốm rồi!`);
  if (info.special && info.special.fx.sach) { S.sparkle = performance.now(); sfx('sach'); }
  else { act(has('eat') ? 'eat' : 'happy', { food: file, loops: info.special ? 1 : 3 }); }
  saveGame();
}
function press(btn) {
  if (S.fade > 0) return;
  const now = performance.now(), was = [S.cursor, S.pick, S.tab, S.item, S.mapSel, S.stats, S.sock, S.gp.r, S.gp.c].join();
  const r = pressMode(btn, now);
  if (r === 'quiet') return;
  if (btn === 'B') sfx('quay-lai', 180);
  else if (btn === 'A' || btn === 'SELECT') sfx('chon', 190);
  else if ([S.cursor, S.pick, S.tab, S.item, S.mapSel, S.stats, S.sock, S.gp.r, S.gp.c].join() !== was) sfx('menu', 160);
}
function pressMode(btn, now) {
  if (S.mode === 'evo') {
    if (S.waitA && btn === 'A') fadeTo(() => { S.mode = 'room'; S.act = null; bubble('bong_tim'); music('ngay'); });
    return;
  }
  if (S.mode === 'map') {
    if (['UP', 'DOWN', 'LEFT', 'RIGHT'].includes(btn)) mapMove(btn);
    if (btn === 'B') fadeTo(comeHome);
    if (btn === 'A') {
      const p = PL[S.mapSel];
      if (p.kind === 'home') fadeTo(comeHome);
      else if (p.kind === 'shop') fadeTo(() => { S.mode = 'shop'; S.tab = 0; S.item = 0; });
      else if (p.kind === 'train') { sfx('loi'); toast('Võ đường: sắp mở'); }
      else { sfx('loi'); toast(p.kind === 'region' ? `${p.name}: đang khóa` : `${p.name}: sắp mở`); }
      return 'quiet';
    }
    return;
  }
  if (S.mode === 'shop') {
    const n = shopRows(S.tab).length;
    if (btn === 'LEFT' && S.item % 4) S.item--;
    if (btn === 'RIGHT' && S.item % 4 < 3 && S.item + 1 < n) S.item++;
    if (btn === 'UP' && S.item >= 4) S.item -= 4;
    if (btn === 'DOWN' && S.item + 4 < n) S.item += 4;
    if (btn === 'L1' || btn === 'R1') { S.tab = (S.tab + (btn === 'R1' ? 1 : 3)) % 4; S.item = 0; }
    if (btn === 'A') { buy(); return 'quiet'; }
    if (btn === 'X') toast('Bán: sắp mở');
    if (btn === 'B') fadeTo(() => { S.mode = 'map'; });
    return;
  }
  if (S.stats !== null) {                                     // the stats screen
    if (S.stats === 2 && S.gemMode) return gemInput(btn);
    if (S.stats === 2 && btn === 'A') { S.gemMode = 'sock'; return; }
    if (['LEFT', 'UP', 'L1'].includes(btn)) S.stats = (S.stats + 3) % 4;
    if (['RIGHT', 'DOWN', 'R1'].includes(btn)) S.stats = (S.stats + 1) % 4;
    if (btn === 'B' || btn === 'SELECT') S.stats = null;
    return;
  }
  if (S.pickerGoal === 1) {                                   // the bag
    const n = Math.max(1, G.bag.length);
    if (btn === 'LEFT' || btn === 'UP') S.pick = (S.pick + n - 1) % n;
    if (btn === 'RIGHT' || btn === 'DOWN') S.pick = (S.pick + 1) % n;
    if (btn === 'B') S.pickerGoal = 0;
    if (btn === 'A' && G.bag.length) { useItem(G.bag[S.pick][0]); return 'quiet'; }
    return;
  }
  if (G.pet.asleep) {                                         // asleep: only A, which wakes it
    if (btn !== 'A') return 'quiet';
    G.pet.asleep = false; S.act = null; if (has('wake')) act('wake'); sfx('thuc-day'); music('ngay'); saveGame();
    return 'quiet';
  }
  if (btn === 'LEFT' || btn === 'UP') S.cursor = (S.cursor + MENU.length - 1) % MENU.length;
  if (btn === 'RIGHT' || btn === 'DOWN') S.cursor = (S.cursor + 1) % MENU.length;
  if (btn === 'START') toast('Trang trí phòng: sắp mở');
  if (btn === 'SELECT') { S.stats = 0; S.pickerGoal = 0; return; }
  if (btn === 'Y') {                                         // show off a move, if this stage has any
    const a = PET.anims, moves = ['punch', 'blast', 'attack', 'victory', 'run'].filter(m => a[m]);
    if (!moves.length) { toast('Bậc này chưa có chiêu'); return; }
    S.move = ((S.move || 0) + 1) % moves.length; act(moves[S.move], { loops: moves[S.move] === 'run' ? 3 : 2 });
    sfx({ punch: 'dam', blast: 'chieu', attack: 'don-he', victory: 'thang', run: 'chay' }[moves[S.move]]); return 'quiet';
  }
  if (btn === 'X') {
    S.pokes = (S.pokes || []).filter(t => now - t < 2500).concat(now);
    if (S.pokes.length >= 4 && has('angry')) {
      S.pokes = []; G.pet.need.vui = Math.max(0, G.pet.need.vui - 5); bubble('bong_gian'); act('angry', { loops: 2 });
      toast(`${petName()} bực rồi, đừng vuốt nữa!`);
    } else if (has('petted')) {
      if (!S.act || S.act.anim !== 'petted') act('petted', { loops: 2 }); else S.actT = now;
      G.pet.need.vui = Math.min(100, G.pet.need.vui + 3); bubble('bong_tim');
    } else toast('Bậc này chưa có động tác vuốt ve');
    return;
  }
  if (['L1', 'R1', 'L2', 'F'].includes(btn)) return 'quiet';
  if (btn === 'R2') {                                        // play with the pet
    if (G.pet.sick) { sfx('loi'); toast(`${petName()} đang ốm, chưa chơi được`); return 'quiet'; }
    if (G.pet.need.nl < 10) { sfx('loi'); toast(`${petName()} mệt quá rồi`); return 'quiet'; }
    const toy = G.owned['DacBiet_6_toy-ball'] ? 2 : 1;
    G.pet.need.vui = Math.min(100, G.pet.need.vui + 15 * toy); G.pet.need.nl = Math.max(0, G.pet.need.nl - 5);
    bubble('bong_vui'); act('happy', { loops: 2 }); sfx('vui'); saveGame(); return 'quiet';
  }
  if (btn !== 'A') return;
  switch (S.cursor) {
    case 0: if (G.bag.length) { S.pickerGoal = 1; S.pick = Math.min(S.pick, G.bag.length - 1); } else toast('Hết đồ ăn rồi, ra Chợ mua nhé'); break;
    case 1:
      if (!G.pet.poop.length && G.pet.need.sach >= 99) { toast('Phòng đang sạch rồi'); break; }
      G.pet.poop = []; G.pet.need.sach = 100; S.sparkle = now; sfx('sach'); toast('Phòng sạch bong!'); saveGame(); return 'quiet';
    case 2: G.pet.asleep = true; S.act = null; if (has('sleep')) act('sleep', { hold: true }); sfx('ngu'); music('dem'); saveGame(); return 'quiet';
    case 3: fadeTo(openMap); break;
  }
}
let fadeCb = null, fadeStart = 0;
function fadeTo(cb) { fadeCb = cb; fadeStart = performance.now(); S.fade = 0.001; sfx('chuyen', 170); }
// a game pad (standard layout: 0 bottom, 1 right, 2 left, 3 top; the R36S build maps its buttons to these)
const PAD = { 0: 'A', 1: 'B', 2: 'X', 3: 'Y', 4: 'L1', 5: 'R1', 6: 'L2', 7: 'R2', 8: 'SELECT', 9: 'START',
              12: 'UP', 13: 'DOWN', 14: 'LEFT', 15: 'RIGHT' };
const padDown = {};
function pollPad() {
  for (const gp of navigator.getGamepads ? navigator.getGamepads() : []) {
    if (!gp) continue;
    for (const [i, name] of Object.entries(PAD)) {
      const id = gp.index + ':' + i, down = !!(gp.buttons[i] && gp.buttons[i].pressed);
      // a button already held when the pad is first seen (some virtual pads) counts only after a release
      if (id in padDown && down && !padDown[id]) press(name);
      padDown[id] = down;
    }
  }
}
// keys on a PC (index.html also has buttons)
const KEYS = { arrowup: 'UP', arrowdown: 'DOWN', arrowleft: 'LEFT', arrowright: 'RIGHT', enter: 'A', ' ': 'A', z: 'A',
  escape: 'B', x: 'B', backspace: 'B', c: 'X', v: 'Y', s: 'START', shift: 'SELECT', e: 'SELECT', q: 'L1', w: 'R1', '1': 'L2',
  '2': 'R2', f: 'F' };
addEventListener('keydown', e => { const k = KEYS[e.key.toLowerCase()]; if (k) { press(k); e.preventDefault(); } });

// ---------- loop ----------
let last = 0, lastSave = 0, ready = false;
const step = (v, goal, dt, ms) => v + Math.sign(goal - v) * Math.min(Math.abs(goal - v), dt / ms);
function frame(now) {
  const dt = Math.min(50, now - last); last = now;
  pollPad();
  if (ready) {
    catchUp(Date.now());
    S.popup = step(S.popup, S.popupGoal, dt, 300);
    S.picker = step(S.picker, S.pickerGoal, dt, 220);
    S.night = step(S.night, G.pet.asleep ? 1 : 0, dt, 900);
    if (S.mode === 'room' && S.stats !== null) drawStats(now); else if (S.mode === 'room') drawRoom(now);
    else if (S.mode === 'map') drawMap(now); else if (S.mode === 'shop') drawShop(now); else drawEvo(now);
    if (S.toast && now - S.toastT < 2200) {
      ctx.fillStyle = 'rgba(18,11,9,0.85)'; ctx.fillRect(110, 190, 420, 40);
      text(S.toast, 320, 210, 14, '#f0e4ce', 'center');
    }
    if (S.fade > 0) {
      const t = (now - fadeStart) / 350;
      if (t >= 1 && fadeCb) { fadeCb(); fadeCb = null; fadeStart = now; }
      const a = fadeCb ? Math.min(1, t) : Math.max(0, 1 - (now - fadeStart) / 350);
      if (!fadeCb && a <= 0) S.fade = 0;
      ctx.fillStyle = `rgba(0,0,0,${a})`; ctx.fillRect(0, 0, 640, 480);
    }
    if (now - lastSave > RULES.autosaveMs) { saveGame(); lastSave = now; }
  }
  requestAnimationFrame(frame);
}
// the handheld asks before it quits (SELECT + START held): the game is saved first
globalThis.__quit = () => { if (G) saveGame(); };

async function start() {
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, 640, 480);
  await Promise.all([...UI.map(n => load(n, `img/${n}.png`)), ...STATS_UI.map(n => load('st/' + n, `img/stats/${n}.png`)),
                     ...DATA.foods.flatMap(f => [load('food/' + f, `img/food/${f}.png`), load('shop/' + f, `img/shop/${f}.png`)])]);
  G = loadGame();
  let away = 0;
  if (!G || !G.pet) G = newGame();
  else away = catchUp(Date.now());
  ROOM = DATA.rooms[G.room];
  await Promise.all([loadRoom(G.room), loadSet(G.pet.cid, G.pet.stage).then(s => { PET = s; })]);
  S.px = (walkRange()[0] + walkRange()[1]) / 2;
  saveGame();
  ready = true;
  music(G.pet.asleep ? 'dem' : 'ngay');
  if (away > 1 / 6) toast(`${petName()} đã ở một mình ${away >= 1 ? Math.round(away) + ' giờ' : Math.round(away * 60) + ' phút'}`);
  requestAnimationFrame(frame);
}
start();
