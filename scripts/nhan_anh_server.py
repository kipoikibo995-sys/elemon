"""A receiver for pictures drawn in the ChatGPT tab of the app's browser (its downloads do not reach the disk): the tab
opens http://127.0.0.1:8787/receiver and posts {name, blob} to it with postMessage; each one is written into OUT.
(nhan_lv5_server.py, made general: the folder is the first argument.)
    python nhan_anh_server.py <folder>
"""
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build', 'tai-ve')
os.makedirs(OUT, exist_ok=True)

RECEIVER_HTML = b"""<!doctype html><html><body>
<h1>Elemon receiver</h1><div id="log">waiting...</div>
<script>
const log = document.getElementById('log');
const say = t => log.innerText = (new Date().toTimeString().slice(0,8) + ' ' + t) + '\\n' + log.innerText;
window.addEventListener('message', async ev => {
  const d = ev.data;
  if (!d || !d.name || !d.blob) return;
  try {
    const r = await fetch('/' + d.name, { method: 'POST', body: d.blob });
    say('posted ' + d.name + ' ' + d.blob.size + ' -> ' + r.status);
    if (ev.source && ev.source.postMessage) ev.source.postMessage({ ack: d.name, status: r.status }, '*');
  } catch (e) {
    say('err ' + d.name + ' ' + e);
    if (ev.source && ev.source.postMessage) ev.source.postMessage({ ack: d.name, error: String(e) }, '*');
  }
});
say('ready');
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_GET(self):
        if self.path in ('/', '/receiver', '/receiver.html'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(RECEIVER_HTML)
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        name = self.path.lstrip('/').replace('..', '').replace('/', '_').replace(chr(92), '_') or 'unnamed.bin'
        data = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        with open(os.path.join(OUT, name), 'wb') as f:
            f.write(data)
        print(f'SAVED {name} {len(data)} bytes', flush=True)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, *a):
        pass


print(f'listening on 127.0.0.1:8787 -> {OUT}', flush=True)
HTTPServer(('127.0.0.1', 8787), H).serve_forever()
