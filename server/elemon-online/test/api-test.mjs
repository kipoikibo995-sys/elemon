// Thử API của Worker (máy chủ cục bộ, SQLite trong bộ nhớ):  node test/api-test.mjs
import assert from 'node:assert/strict';
import { serve } from './local-server.mjs';
import { checkTeam, ATTR_CAP } from '../src/worker.js';

const PORT = 8799, U = `http://localhost:${PORT}`;
const srv = await serve(PORT, undefined, { MIN_FIGHT_MS: '0' });
const hex = n => [...crypto.getRandomValues(new Uint8Array(n / 2))].map(x => x.toString(16).padStart(2, '0')).join('');
const get = p => fetch(U + p).then(r => r.json());
const post = (p, b) => fetch(U + p, { method: 'POST', body: JSON.stringify(b) }).then(r => r.json());
const pet = (dir, lv, stage, a, ten = 'Bé') => ({ dir, ten, stage, lv, attr: a, chieu: 1, hp: 99999 });
let ok = 0;
const t = async (name, f) => { await f(); ok++; console.log('ok', name); };

const A = { id: hex(16), key: hex(32) }, B = { id: hex(16), key: hex(32) }, C = { id: hex(16), key: hex(32) };
await t('ping', async () => assert.equal((await get('/api/ping')).ok, true));
await t('upload A', async () => {
  const r = await post('/api/team', { ...A, name: 'An', team: [pet('hoa-ho', 25, 'teen', [30, 20, 25, 15, 15, 20], 'Hổ Lửa')] });
  assert.equal(r.ok, true, r.msg); assert.equal(r.level, 25); assert.equal(r.rating, 1000);
  assert.ok(r.team[0].luc > 0); assert.equal(r.team[0].hp, undefined);       // máy chủ tự tính, không giữ số máy gửi
});
await t('upload B, C', async () => {
  assert.equal((await post('/api/team', { ...B, team: [pet('kim-te', 28, 'teen', [25, 25, 25, 25, 25, 25])] })).ok, true);
  assert.equal((await post('/api/team', { ...C, team: [pet('tho-nguu', 120, 'legend', [90, 80, 90, 70, 70, 80])] })).ok, true);
});
await t('reject: stats over the cap', async () => {
  const r = await post('/api/team', { id: hex(16), key: hex(32), team: [pet('hoa-ho', 10, 'child', [ATTR_CAP(10) + 1, 10, 10, 10, 10, 10])] });
  assert.equal(r.ok, false); assert.match(r.msg, /giới hạn/);
});
await t('reject: level vs stage, unknown pet, wrong key, too soon', async () => {
  assert.equal((await post('/api/team', { id: hex(16), key: hex(32), team: [pet('hoa-ho', 60, 'child', [10, 10, 10, 10, 10, 10])] })).ok, false);
  assert.equal((await post('/api/team', { id: hex(16), key: hex(32), team: [pet('hu-anh', 100, 'legend', [10, 10, 10, 10, 10, 10])] })).ok, false);
  assert.equal((await post('/api/team', { id: A.id, key: hex(32), team: [pet('hoa-ho', 25, 'teen', [10, 10, 10, 10, 10, 10])] })).ok, false);
  assert.match((await post('/api/team', { ...A, team: [pet('hoa-ho', 25, 'teen', [10, 10, 10, 10, 10, 10])] })).msg, /đợi/);
});
await t('opponents near level first', async () => {
  const r = await get(`/api/opponents?id=${A.id}&lv=25`);
  assert.equal(r.ok, true); assert.deepEqual(r.list.map(x => x.id), [B.id, C.id]);
});
let token;
await t('fight + result (win) moves ratings', async () => {
  const f = await post('/api/fight', { ...A, foe: B.id, pet: 0 });
  assert.equal(f.ok, true, f.msg); assert.equal(f.foe.pet.dir, 'kim-te'); token = f.token;
  const r = await post('/api/result', { ...A, token, win: true, me: 2, bot: 1 });
  assert.equal(r.ok, true, r.msg); assert.ok(r.delta > 0);
});
await t('result only once', async () => assert.equal((await post('/api/result', { ...A, token, win: true })).ok, false));
await t('top', async () => {
  const r = await get(`/api/top?id=${B.id}`);
  assert.equal(r.top[0].id, A.id); assert.equal(r.me.rank, 3); assert.equal(r.players, 3);
});
await t('bad json', async () => assert.equal((await fetch(U + '/api/team', { method: 'POST', body: '{' }).then(r => r.json())).ok, false));
await t('checkTeam names', async () => assert.equal(checkTeam([pet('hoa-ho', 3, 'baby', [10, 10, 10, 10, 10, 10], 'A\u0000<b>Ơi')])[0][0].ten, 'AbƠi'));
srv.close();
console.log(`${ok} ok`);
