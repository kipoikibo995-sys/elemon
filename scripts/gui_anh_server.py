"""Hands a picture from the disk to a page in the app's browser that cannot fetch from 127.0.0.1 (ChatGPT): the tab opens
http://127.0.0.1:8788/<file>, which puts the file into window.name as base64 and goes on to the page in ?then=; that
page reads window.name. (The reverse of nhan_anh_server.py.)
    python gui_anh_server.py <folder>
"""
import base64
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DIR = sys.argv[1] if len(sys.argv) > 1 else '.'


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        u = urlparse(self.path)
        name = os.path.basename(u.path)
        p = os.path.join(DIR, name)
        if not name or not os.path.isfile(p):
            self.send_response(404); self.end_headers(); return
        if u.query == 'raw':                  # the file itself, for an <img crossorigin> on the page
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg' if name.endswith('.jpg') else 'image/png')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Private-Network', 'true')
            self.end_headers()
            self.wfile.write(open(p, 'rb').read())
            return
        b64 = base64.b64encode(open(p, 'rb').read()).decode()
        then = parse_qs(u.query).get('then', [''])[0]
        page = ('<!doctype html><body>%s<script>window.name = %s;%s</script></body>'
                % (name, json.dumps('img:' + name + ':' + b64),
                   ' location.href = %s;' % json.dumps(then) if then.startswith('https://') else ''))
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())

    def log_message(self, *a):
        pass


print(f'serving {DIR} on 127.0.0.1:8788', flush=True)
HTTPServer(('127.0.0.1', 8788), H).serve_forever()
