// Elemon online, phần máy chủ (Cloudflare Worker + D1): Đấu trường "đấu với đội của người khác".
// Máy tải đội của mình lên; người khác tải đội đó về và đánh với bot Solo mức Khó cầm đội ấy; kết quả ghi vào bảng
// xếp hạng (Elo). Không có đăng nhập: mỗi máy tự tạo một id và một khóa bí mật (save/mang-id.txt), lần tải đầu
// máy chủ giữ sha256 của khóa, về sau chỉ ai có khóa mới ghi được vào id đó.
//
//   GET  /api/ping                                   -> {ok, v}
//   POST /api/team     {id, key, team: [pet..]}       -> {ok, team, rating, luc}      tải / cập nhật đội (1-3 pet)
//   GET  /api/opponents?id=&lv=                       -> {ok, list: [{id, name, level, luc, rating, team}]}
//   POST /api/fight    {id, key, foe, pet}            -> {ok, token, foe: {name, pet}} mở một trận
//   POST /api/result   {id, key, token, win, me, bot} -> {ok, rating, delta}          đóng trận đó, một lần
//   GET  /api/top?id=                                 -> {ok, top: [...], me: {rank, rating, ...}}
// Lỗi: {ok: false, msg: "<câu tiếng Việt để game hiện ra>"}.
//
// Chống gian lận đơn giản: máy chủ không tin số máu / công máy gửi lên, chỉ nhận 6 thuộc tính + cấp, kiểm tra giới hạn
// theo cấp (ATTR_CAP / SUM_CAP), rồi tự tính chỉ số bằng đúng công thức của game (game/src/chi-so.js: of). Kết quả
// trận phải đi kèm một trận đã mở (token), mở ít nhất MIN_FIGHT_MS trước, mỗi token dùng một lần, có hạn mức một ngày.
// Sửa công thức trong chi-so.js thì sửa cả STATS ở đây.

export const PETS = new Set([
  'hoa-ho', 'hoa-quy', 'hoa-ho-cao', 'viem-long', 'dung-nham-ve', 'hoa-linh',
  'tinh-kim-hiep', 'kim-te', 'kim-giap', 'kim-ung', 'kim-thach-nhan', 'liem-dao',
  'moc-hung', 'moc-duong', 'reu-linh', 'moc-tru', 'moc-loc', 'thu-nhan', 'diep-linh',
  'thuy-long', 'thuy-sa', 'thuy-giai', 'thuy-chien', 'bao-thuy', 'thuy-giao',
  'tho-nguu', 'tho-tuong', 'tho-tich', 'thach-nhan', 'thanh-tri', 'tho-long',
]);
// cấp của từng bậc (scripts/evo_app.html: LV)
export const LV = { baby: [1, 5], child: [6, 20], teen: [21, 45], adult: [46, 99], legend: [100, 150] };
// giới hạn thuộc tính theo cấp: một thuộc tính, và tổng sáu cái. Rộng tay vì pet kẹt ở cấp cuối bậc vẫn tập và ăn
// thêm được mỗi ngày (chi-so.js: +1/ngày mỗi bài tập, +1/ngày đồ ăn, ngọc tới 120)
export const ATTR_CAP = lv => Math.min(120, 40 + 2 * lv);
export const SUM_CAP = lv => Math.min(720, 100 + 6 * lv);
const MAX_TEAM = 3, NAME_MAX = 16;
const MIN_FIGHT_MS = 15e3, FIGHT_TTL_MS = 30 * 60e3, FIGHTS_DAY = 60, SAME_FOE_DAY = 5, UPLOAD_GAP_MS = 10e3;
const K_ATTACK = 24, K_DEFEND = 12, START_RATING = 1000;

// = game/src/chi-so.js of(lv, a): a = [Sức mạnh, Nhanh nhẹn, Bền bỉ, Thông minh, Trí tuệ, Tinh thần]
export function STATS(lv, a) {
  return { hp: Math.round(80 + 4 * lv + 3 * a[2]), atk: 8 + 0.4 * lv + 0.4 * a[0], skill: 12 + 0.5 * lv + 0.5 * a[3],
           mp: Math.round(60 + 0.4 * lv + 1.5 * a[4]), thu: 0.5 * lv + 0.5 * a[2], spd: 120 + 0.8 * a[1] };
}
export const LUC = st => Math.round(st.hp / 4 + st.atk + st.skill);    // = chi-so.js luc

// tên: chữ (cả tiếng Việt), số, khoảng trắng và vài dấu; bỏ ký tự điều khiển, cắt độ dài
export function cleanName(s) {
  if (typeof s !== 'string') return '';
  return s.normalize('NFC').replace(/[^\p{L}\p{N} _.\-']/gu, '').replace(/\s+/g, ' ').trim().slice(0, NAME_MAX);
}

// -> [đội đã sạch, ''] hoặc [null, lý do]
export function checkTeam(team) {
  if (!Array.isArray(team) || team.length < 1 || team.length > MAX_TEAM) return [null, `Đội phải có 1-${MAX_TEAM} pet`];
  const out = [];
  for (const p of team) {
    if (!p || typeof p !== 'object') return [null, 'Dữ liệu pet hỏng'];
    if (!PETS.has(p.dir)) return [null, 'Pet này chưa vào được Đấu trường online'];
    const r = LV[p.stage];
    if (!r) return [null, 'Bậc tiến hóa không đúng'];
    const lv = p.lv;
    if (!Number.isInteger(lv) || lv < r[0] || lv > r[1]) return [null, 'Cấp không khớp với bậc tiến hóa'];
    const a = p.attr;
    if (!Array.isArray(a) || a.length !== 6 || !a.every(v => typeof v === 'number' && Number.isFinite(v) && v >= 0))
      return [null, 'Thuộc tính hỏng'];
    if (a.some(v => v > ATTR_CAP(lv))) return [null, `Thuộc tính vượt giới hạn của cấp ${lv}`];
    if (a.reduce((s, v) => s + v, 0) > SUM_CAP(lv)) return [null, `Tổng thuộc tính vượt giới hạn của cấp ${lv}`];
    const attr = a.map(v => Math.round(v * 100) / 100);
    const chieu = p.stage === 'legend' ? 5 : 1;               // bộ chiêu theo bậc (Huyền thoại: bộ Lv5), không lấy số máy gửi
    const st = STATS(lv, attr);
    out.push({ dir: p.dir, ten: cleanName(p.ten) || 'Pet', stage: p.stage, lv, attr, chieu, st, luc: LUC(st) });
  }
  return [out, ''];
}

export function elo(ra, rb, win, k) {
  const e = 1 / (1 + Math.pow(10, (rb - ra) / 400));
  return Math.round(k * ((win ? 1 : 0) - e));
}

// ---------- HTTP ----------
const HEX = (n, s) => typeof s === 'string' && new RegExp(`^[0-9a-f]{${n}}$`).test(s);
const CORS = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS' };
const json = (o, status = 200) => new Response(JSON.stringify(o), { status, headers: { 'Content-Type': 'application/json; charset=utf-8', ...CORS } });
const fail = (msg, status = 400) => json({ ok: false, msg }, status);
async function sha256(s) {
  const b = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)));
  return [...b].map(x => x.toString(16).padStart(2, '0')).join('');
}
function randHex(n) {
  const b = crypto.getRandomValues(new Uint8Array(n / 2));
  return [...b].map(x => x.toString(16).padStart(2, '0')).join('');
}
const pub = row => row && { id: row.id, name: row.name, level: row.level, luc: row.luc, rating: row.rating,
  wins: row.wins + row.dwins, losses: row.losses + row.dlosses,
  team: JSON.parse(row.team).map(({ dir, ten, stage, lv, attr, chieu, luc }) => ({ dir, ten, stage, lv, attr, chieu, luc })) };

async function body(req) {
  const t = await req.text();
  if (t.length > 8192) throw new Error('big');
  return JSON.parse(t);
}
// the player by id and key: [row, ''] or [null, why]
async function who(db, b) {
  if (!HEX(16, b.id) || !HEX(32, b.key)) return [null, 'Mã người chơi hỏng'];
  const row = await db.prepare('SELECT * FROM players WHERE id = ?').bind(b.id).first();
  if (!row) return [null, 'Chưa tải đội lên'];
  if (row.key_hash !== await sha256(b.key)) return [null, 'Khóa không khớp'];
  return [row, ''];
}

async function putTeam(db, b, now) {
  if (!HEX(16, b.id) || !HEX(32, b.key)) return fail('Mã người chơi hỏng');
  const [team, why] = checkTeam(b.team);
  if (!team) return fail(why);
  const hash = await sha256(b.key), old = await db.prepare('SELECT key_hash, updated FROM players WHERE id = ?').bind(b.id).first();
  if (old && old.key_hash !== hash) return fail('Khóa không khớp', 403);
  if (old && now - old.updated < UPLOAD_GAP_MS) return fail('Vừa tải xong, đợi một chút', 429);
  const level = Math.max(...team.map(p => p.lv)), luc = Math.max(...team.map(p => p.luc));
  const name = cleanName(b.name) || team[0].ten;
  if (old) await db.prepare('UPDATE players SET name = ?, team = ?, level = ?, luc = ?, updated = ? WHERE id = ?')
    .bind(name, JSON.stringify(team), level, luc, now, b.id).run();
  else await db.prepare('INSERT INTO players (id, key_hash, name, team, level, luc, rating, created, updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)')
    .bind(b.id, hash, name, JSON.stringify(team), level, luc, START_RATING, now, now).run();
  const row = await db.prepare('SELECT * FROM players WHERE id = ?').bind(b.id).first();
  return json({ ok: true, ...pub(row) });
}

// đối thủ hợp cấp: cấp gần mình nhất trước (±8, chưa đủ thì nới ra), lấy ngẫu nhiên trong nhóm gần
async function opponents(db, url) {
  const id = url.searchParams.get('id') || '', lv = Math.max(1, Math.min(150, parseInt(url.searchParams.get('lv'), 10) || 1));
  let rows = [];
  for (const span of [8, 20, 150]) {
    rows = (await db.prepare('SELECT * FROM players WHERE id != ? AND level BETWEEN ? AND ? ORDER BY ABS(level - ?) LIMIT 30')
      .bind(id, lv - span, lv + span, lv).all()).results || [];
    if (rows.length >= 6) break;
  }
  for (let i = rows.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [rows[i], rows[j]] = [rows[j], rows[i]]; }
  rows = rows.slice(0, 6).sort((a, b) => Math.abs(a.level - lv) - Math.abs(b.level - lv) || b.rating - a.rating);
  return json({ ok: true, list: rows.map(pub) });
}

async function fight(db, b, now) {
  const [me, why] = await who(db, b);
  if (!me) return fail(why, 403);
  if (!HEX(16, b.foe) || b.foe === me.id) return fail('Đối thủ không đúng');
  const foe = await db.prepare('SELECT * FROM players WHERE id = ?').bind(b.foe).first();
  if (!foe) return fail('Đối thủ không còn trên máy chủ');
  const team = JSON.parse(foe.team), pet = Number.isInteger(b.pet) && b.pet >= 0 && b.pet < team.length ? b.pet : 0;
  const day = now - 864e5;
  const n = await db.prepare('SELECT COUNT(*) AS n, SUM(defender = ?) AS same FROM fights WHERE attacker = ? AND started > ?')
    .bind(foe.id, me.id, day).first();
  if (n && n.n >= FIGHTS_DAY) return fail('Hôm nay đánh đủ rồi, mai quay lại nhé', 429);
  if (n && n.same >= SAME_FOE_DAY) return fail('Đã đánh đội này nhiều lần hôm nay, chọn đội khác', 429);
  const token = randHex(32);
  await db.prepare('INSERT INTO fights (token, attacker, defender, pet, started) VALUES (?, ?, ?, ?, ?)').bind(token, me.id, foe.id, pet, now).run();
  return json({ ok: true, token, foe: { id: foe.id, name: foe.name, rating: foe.rating, pet: team[pet] } });
}

async function result(db, b, now, minMs = MIN_FIGHT_MS) {
  const [me, why] = await who(db, b);
  if (!me) return fail(why, 403);
  if (!HEX(32, b.token)) return fail('Trận không đúng');
  const f = await db.prepare('SELECT * FROM fights WHERE token = ? AND attacker = ?').bind(b.token, me.id).first();
  if (!f) return fail('Không thấy trận này');
  if (f.done) return fail('Trận này đã ghi rồi');
  const win = b.win === true;
  if (win && now - f.started < minMs) return fail('Trận ngắn quá, không ghi');   // bỏ trận giữa chừng thì vẫn ghi thua
  if (now - f.started > FIGHT_TTL_MS) return fail('Trận quá hạn, không ghi');
  const foe = await db.prepare('SELECT * FROM players WHERE id = ?').bind(f.defender).first();
  if (!foe) return fail('Đối thủ không còn trên máy chủ');
  const dMe = elo(me.rating, foe.rating, win, K_ATTACK), dFoe = elo(foe.rating, me.rating, !win, K_DEFEND);
  const upd = await db.prepare('UPDATE fights SET done = 1 WHERE token = ? AND done = 0').bind(b.token).run();
  if (upd.meta && upd.meta.changes === 0) return fail('Trận này đã ghi rồi');
  await db.batch([
    db.prepare(`UPDATE players SET rating = MAX(0, rating + ?), ${win ? 'wins = wins + 1' : 'losses = losses + 1'} WHERE id = ?`).bind(dMe, me.id),
    db.prepare(`UPDATE players SET rating = MAX(0, rating + ?), ${win ? 'dlosses = dlosses + 1' : 'dwins = dwins + 1'} WHERE id = ?`).bind(dFoe, foe.id),
  ]);
  return json({ ok: true, win, delta: dMe, rating: Math.max(0, me.rating + dMe) });
}

async function top(db, url) {
  const id = url.searchParams.get('id') || '';
  const rows = (await db.prepare('SELECT * FROM players ORDER BY rating DESC, updated ASC LIMIT 20').all()).results || [];
  const list = rows.map((r, i) => ({ rank: i + 1, ...pub(r), team: undefined, mine: r.id === id }));
  let me = null;
  const row = HEX(16, id) && await db.prepare('SELECT * FROM players WHERE id = ?').bind(id).first();
  if (row) {
    const above = await db.prepare('SELECT COUNT(*) AS n FROM players WHERE rating > ?').bind(row.rating).first();
    me = { rank: (above ? above.n : 0) + 1, ...pub(row), team: undefined };
  }
  const all = await db.prepare('SELECT COUNT(*) AS n FROM players').first();
  return json({ ok: true, top: list, me, players: all ? all.n : 0 });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url), db = env.DB, now = Date.now();
    if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
    try {
      if (url.pathname === '/api/ping') return json({ ok: true, v: 1 });
      if (req.method === 'GET' && url.pathname === '/api/opponents') return await opponents(db, url);
      if (req.method === 'GET' && url.pathname === '/api/top') return await top(db, url);
      if (req.method === 'POST') {
        let b;
        try { b = await body(req); } catch (e) { return fail('Dữ liệu gửi lên hỏng'); }
        if (!b || typeof b !== 'object') return fail('Dữ liệu gửi lên hỏng');
        if (url.pathname === '/api/team') return await putTeam(db, b, now);
        if (url.pathname === '/api/fight') return await fight(db, b, now);
        if (url.pathname === '/api/result') return await result(db, b, now, env.MIN_FIGHT_MS ? +env.MIN_FIGHT_MS : MIN_FIGHT_MS);   // tests: shorter
      }
      return fail('Không có đường này', 404);
    } catch (e) {
      console.log('error', e && e.stack || e);
      return fail('Máy chủ lỗi, thử lại sau', 500);
    }
  },
};
