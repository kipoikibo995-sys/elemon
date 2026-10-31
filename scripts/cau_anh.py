"""Cầu nối ảnh cho khung trình duyệt trong app (không có file_upload/tải về như Claude in Chrome).

GET  /f/<đường dẫn tương đối từ assets/source>  -> trả file (ảnh mẫu, job json), có CORS
POST /save?name=<tên.png>                       -> ghi thân request vào assets/source/boss-cuoi/<tên.png>
                                                   (lv2__*.png thì vào assets/5 vùng, chỗ lam_bac2 gom)
GET  /relay                                     -> trang chuyển tiếp: tab chatgpt.com mở nó bằng window.open rồi
                                                   postMessage {id, get: path} / {id, save: name, blob}, nó trả {id, blob|ok}
Chỉ nghe 127.0.0.1. Usage: python cau_anh.py [port]
"""
import os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

SRC = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'source'))
OUT = os.path.join(SRC, 'boss-cuoi')
DL = os.path.realpath(os.path.join(SRC, '..', '5 vùng'))
RELAY = b'''<!doctype html><title>relay</title><script>
addEventListener('message', async e => {
  if (e.origin !== 'https://chatgpt.com') return;
  const m = e.data;
  try {
    if (m.get) { const r = await fetch('/f/' + m.get); if (!r.ok) throw r.status; e.source.postMessage({id: m.id, blob: await r.blob()}, e.origin); }
    if (m.save) { const r = await fetch('/save?name=' + encodeURIComponent(m.save), {method: 'POST', body: m.blob}); e.source.postMessage({id: m.id, ok: r.ok}, e.origin); }
  } catch (err) { e.source.postMessage({id: m.id, err: String(err)}, e.origin); }
});
if (opener) opener.postMessage({relay: 'ready'}, 'https://chatgpt.com');
</script>relay ok'''


class H(BaseHTTPRequestHandler):
    def cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Private-Network', 'true')

    def do_OPTIONS(self):
        self.send_response(204); self.cors(); self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == '/relay':
            self.send_response(200); self.send_header('Content-Type', 'text/html'); self.end_headers()
            self.wfile.write(RELAY); return
        p = os.path.realpath(os.path.join(SRC, unquote(u.path[3:]))) if u.path.startswith('/f/') else ''
        if not p.startswith(SRC + os.sep) or not os.path.isfile(p):
            self.send_response(404); self.cors(); self.end_headers(); return
        data = open(p, 'rb').read()
        self.send_response(200); self.cors()
        self.send_header('Content-Type', 'application/json' if p.endswith('.json') else 'image/png')
        self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)

    def do_POST(self):
        u = urlparse(self.path)
        name = os.path.basename(parse_qs(u.query).get('name', [''])[0])
        if not name.endswith(('.png', '.webp')):
            self.send_response(400); self.cors(); self.end_headers(); return
        data = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        open(os.path.join(DL if name.startswith('lv2__') else OUT, name), 'wb').write(data)
        print('saved', name, len(data), flush=True)
        self.send_response(200); self.cors(); self.end_headers(); self.wfile.write(b'ok')


ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1]) if len(sys.argv) > 1 else 8765), H).serve_forever()
