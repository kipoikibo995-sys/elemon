// Chạy Worker trên máy tính, không cần tài khoản Cloudflare: D1 thay bằng SQLite có sẵn trong Node 22 (node:sqlite).
//   node test/local-server.mjs [cổng, mặc định 8787] [file .db, mặc định trong bộ nhớ]
// MIN_FIGHT_MS=0 (biến môi trường) để harness ghi được kết quả trận ngắn.
import http from 'node:http';
import fs from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
import worker from '../src/worker.js';

const HERE = new URL('.', import.meta.url);
export function d1(file = ':memory:') {
  const db = new DatabaseSync(file);
  db.exec(fs.readFileSync(new URL('../schema.sql', HERE), 'utf8'));
  const stmt = (sql, args = []) => ({
    bind: (...a) => stmt(sql, a),
    first: async () => db.prepare(sql).get(...args) ?? null,
    all: async () => ({ results: db.prepare(sql).all(...args) }),
    run: async () => { const r = db.prepare(sql).run(...args); return { meta: { changes: Number(r.changes) } }; },
  });
  return { prepare: sql => stmt(sql), batch: async list => Promise.all(list.map(s => s.run())) };
}

export function serve(port = 8787, file, env = {}) {
  const e = { DB: d1(file), ...env };
  const srv = http.createServer(async (req, res) => {
    const chunks = [];
    for await (const c of req) chunks.push(c);
    const r = await worker.fetch(new Request(`http://localhost:${port}${req.url}`, {
      method: req.method, headers: req.headers, body: ['GET', 'HEAD'].includes(req.method) ? undefined : Buffer.concat(chunks) }), e);
    res.writeHead(r.status, Object.fromEntries(r.headers));
    res.end(Buffer.from(await r.arrayBuffer()));
    console.log(req.method, req.url, r.status);
  });
  return new Promise(ok => srv.listen(port, '0.0.0.0', () => ok(srv)));
}

if (import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/').replace(/^\//, '')}`) {
  const port = +process.argv[2] || 8787;
  await serve(port, process.argv[3], { MIN_FIGHT_MS: process.env.MIN_FIGHT_MS });
  console.log(`elemon-online local: http://localhost:${port}`);
}
