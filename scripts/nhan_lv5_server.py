import os
from http.server import BaseHTTPRequestHandler, HTTPServer
OUT = r'D:\INDIEGAME\HoLua\assets\source\tinh-linh\_ve-lv5\tai-ve'
os.makedirs(OUT, exist_ok=True)

RECEIVER_HTML = b"""<!doctype html><html><body>
<h1>LV5 receiver</h1><div id="log">waiting...</div>
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
        name = self.path.lstrip('/')
        name = name.replace('..', '').replace('/', '_').replace(chr(92), '_')
        if not name:
            name = 'unnamed.bin'
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length)
        path = os.path.join(OUT, name)
        with open(path, 'wb') as f:
            f.write(data)
        print(f'SAVED {name} {len(data)} bytes', flush=True)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, *a):
        pass

print('listening on 127.0.0.1:8787', flush=True)
HTTPServer(('127.0.0.1', 8787), H).serve_forever()
