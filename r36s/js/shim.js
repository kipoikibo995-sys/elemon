// The browser pieces the test page (preview/tien-hoa/index.html) uses, on top of the native canvas of r36s/jsrt.c
// (__cv). Loaded before the page: the page itself runs unchanged.
globalThis.window = globalThis;
// tests (HOLUA_TEST): the same "random" numbers every run, so two runs can be compared pixel by pixel
if (__cv.test) { let seed = 12345; Math.random = () => (seed = (Math.imul(seed, 1103515245) + 12345) >>> 0) / 4294967296; }
globalThis.console = { log: (...a) => __cv.log(a.join(' ')), warn: (...a) => __cv.log(a.join(' ')),
                       error: (...a) => __cv.log(a.join(' ')) };

// CSS colours -> 0xAARRGGBB
const __colours = new Map();
function __rgba(s) {
  if (typeof s !== 'string') return 0xFF000000;
  let v = __colours.get(s);
  if (v !== undefined) return v;
  const t = s.trim().toLowerCase();
  let r = 0, g = 0, b = 0, a = 1, m;
  if (t[0] === '#') {
    const h = t.slice(1);
    const x = h.length <= 4 ? h.split('').map(c => parseInt(c + c, 16)) : h.match(/../g).map(c => parseInt(c, 16));
    [r, g, b] = x; if (x.length > 3) a = x[3] / 255;
  } else if ((m = t.match(/^rgba?\(([^)]*)\)/))) {
    const p = m[1].split(',').map(Number);
    [r, g, b] = p; if (p.length > 3) a = p[3];
  } else if (t === 'white') { r = g = b = 255; } else if (t === 'transparent') a = 0;
  v = ((Math.round(Math.max(0, Math.min(1, a)) * 255) << 24) | (r << 16) | (g << 8) | b) >>> 0;
  __colours.set(s, v);
  return v;
}
// a gradient is drawn as one colour: the mean of its stops (the page's only one is a small slot backing)
class CanvasGradient {
  constructor() { this._stops = []; }
  addColorStop(at, colour) { this._stops.push(__rgba(colour)); }
  get _colour() {
    const n = this._stops.length;
    if (!n) return 0;
    const sum = [24, 16, 8, 0].map(sh => this._stops.reduce((t, c) => t + ((c >>> sh) & 255), 0) / n);
    return ((Math.round(sum[0]) << 24) | (Math.round(sum[1]) << 16) | (Math.round(sum[2]) << 8) | Math.round(sum[3])) >>> 0;
  }
}
const __col = c => typeof c === 'number' ? c : c._colour;
// file paths of the page: no ?v= / #, and the folders beside the page (../pets/...) packed under up/
const __file = p => String(p).replace(/[?#].*$/, '').replace(/^(\.\.\/)+/, 'up/');
const __OPS = { 'source-over': 0, 'source-atop': 1, 'source-in': 2 };
const __ALIGN = { left: 0, start: 0, center: 1, right: 2, end: 2 };
const __BASE = { alphabetic: 0, middle: 1, top: 2, hanging: 2 };

class CanvasRenderingContext2D {
  constructor(canvas) {
    this.canvas = canvas;
    this._s = { fs: '#000', fill: 0xFF000000, ss: '#000', stroke: 0xFF000000, lw: 1, alpha: 1, op: 'source-over',
                font: '10px sans-serif', size: 10, bold: 0, align: 'start', base: 'alphabetic', shc: 'rgba(0,0,0,0)',
                shadow: 0, blur: 0, filter: 'none', bright: 1, sat: 1, m: [1, 0, 0, 1, 0, 0] };
    this._stack = [];
    this._path = [];
    this.imageSmoothingEnabled = true;
  }
  get fillStyle() { return this._s.fs; }
  set fillStyle(v) { this._s.fs = v; this._s.fill = v instanceof CanvasGradient ? v : __rgba(v); }
  get strokeStyle() { return this._s.ss; }
  set strokeStyle(v) { this._s.ss = v; this._s.stroke = v instanceof CanvasGradient ? v : __rgba(v); }
  createLinearGradient() { return new CanvasGradient(); }
  createRadialGradient() { return new CanvasGradient(); }
  get lineWidth() { return this._s.lw; } set lineWidth(v) { this._s.lw = +v; }
  get globalAlpha() { return this._s.alpha; } set globalAlpha(v) { this._s.alpha = Math.max(0, Math.min(1, +v)); }
  get globalCompositeOperation() { return this._s.op; } set globalCompositeOperation(v) { if (v in __OPS) this._s.op = v; }
  get font() { return this._s.font; }
  set font(v) {
    const m = /(\d+(?:\.\d+)?)px/.exec(v);
    this._s.font = v; this._s.size = m ? Math.round(+m[1]) : 10; this._s.bold = /bold|[6-9]00/.test(v) ? 1 : 0;
  }
  get textAlign() { return this._s.align; } set textAlign(v) { this._s.align = v; }
  get textBaseline() { return this._s.base; } set textBaseline(v) { this._s.base = v; }
  get shadowColor() { return this._s.shc; } set shadowColor(v) { this._s.shc = v; this._s.shadow = __rgba(v); }
  get shadowBlur() { return this._s.blur; } set shadowBlur(v) { this._s.blur = +v; }
  // filter: brightness() and saturate() only (what the page uses), on drawImage
  get filter() { return this._s.filter; }
  set filter(v) {
    const amount = name => { const m = new RegExp(name + '\\(\\s*([\\d.]+)(%?)\\s*\\)').exec(v); return m ? +m[1] / (m[2] ? 100 : 1) : 1; };
    this._s.filter = v; this._s.bright = amount('brightness'); this._s.sat = amount('saturate');
  }
  save() { this._stack.push({ ...this._s, m: [...this._s.m] }); }
  restore() { if (this._stack.length) this._s = this._stack.pop(); }
  translate(x, y) { const m = this._s.m; m[4] += m[0] * x + m[2] * y; m[5] += m[1] * x + m[3] * y; }
  scale(x, y) { const m = this._s.m; m[0] *= x; m[1] *= x; m[2] *= y; m[3] *= y; }
  rotate(r) {
    const m = this._s.m, c = Math.cos(r), s = Math.sin(r), [a, b, cc, d] = m;
    m[0] = a * c + cc * s; m[1] = b * c + d * s; m[2] = cc * c - a * s; m[3] = d * c - b * s;
  }
  // clip(): a rectangle on screen only (rect() with no rotation), applied to drawImage and fillRect
  clip() {
    const s = this._s, m = s.m, p = this._path.length === 1 && this._path[0].rect;
    if (!p || m[1] || m[2]) return;
    const xa = m[0] * p[0] + m[4], xb = m[0] * (p[0] + p[2]) + m[4], ya = m[3] * p[1] + m[5], yb = m[3] * (p[1] + p[3]) + m[5];
    let c = [Math.min(xa, xb), Math.min(ya, yb), Math.max(xa, xb), Math.max(ya, yb)];
    if (s.clip) c = [Math.max(c[0], s.clip[0]), Math.max(c[1], s.clip[1]), Math.min(c[2], s.clip[2]), Math.min(c[3], s.clip[3])];
    s.clip = c;
  }
  // the part of a destination rectangle inside the clip, with the matching part of the source (null: nothing left)
  _clipped(sx, sy, sw, sh, dx, dy, dw, dh) {
    const c = this._s.clip, m = this._s.m;
    if (!c || m[1] || m[2]) return [sx, sy, sw, sh, dx, dy, dw, dh];
    const X = u => m[0] * u + m[4], Y = v => m[3] * v + m[5];
    const x0 = Math.min(X(dx), X(dx + dw)), x1 = Math.max(X(dx), X(dx + dw));
    const y0 = Math.min(Y(dy), Y(dy + dh)), y1 = Math.max(Y(dy), Y(dy + dh));
    const cx0 = Math.max(x0, c[0]), cx1 = Math.min(x1, c[2]), cy0 = Math.max(y0, c[1]), cy1 = Math.min(y1, c[3]);
    if (cx0 >= cx1 || cy0 >= cy1) return null;
    if (cx0 === x0 && cx1 === x1 && cy0 === y0 && cy1 === y1) return [sx, sy, sw, sh, dx, dy, dw, dh];
    // back to page units, then the same fractions of the source
    const ua = (cx0 - m[4]) / m[0], ub = (cx1 - m[4]) / m[0], va = (cy0 - m[5]) / m[3], vb = (cy1 - m[5]) / m[3];
    const nx = Math.min(ua, ub), nw = Math.abs(ub - ua), ny = Math.min(va, vb), nh = Math.abs(vb - va);
    const fx = (nx - dx) / dw, fw = nw / dw, fy = (ny - dy) / dh, fh = nh / dh;
    return [sx + fx * sw, sy + fy * sh, fw * sw, fh * sh, nx, ny, nw, nh];
  }
  setTransform(a, b, c, d, e, f) { this._s.m = [a, b, c, d, e, f]; }
  resetTransform() { this._s.m = [1, 0, 0, 1, 0, 0]; }
  fillRect(x, y, w, h) {
    const s = this._s, m = s.m;
    if (w < 0) { x += w; w = -w; } if (h < 0) { y += h; h = -h; }
    if (s.clip) { const r = this._clipped(0, 0, 1, 1, x, y, w, h); if (!r) return; [x, y, w, h] = r.slice(4); }
    __cv.fillRect(this.canvas.__id, x, y, w, h, m[0], m[1], m[2], m[3], m[4], m[5], __col(s.fill), s.alpha, __OPS[s.op]);
  }
  clearRect(x, y, w, h) {
    const s = this._s, m = s.m;
    __cv.fillRect(this.canvas.__id, x, y, w, h, m[0], m[1], m[2], m[3], m[4], m[5], 0, 1, 2);
  }
  drawImage(im, a, b, c, d, e, f, g, h) {
    if (!im || im.__id === undefined) return;
    let sx = 0, sy = 0, sw = im.width, sh = im.height, dx, dy, dw, dh;
    if (e === undefined) { dx = a; dy = b; dw = c === undefined ? sw : c; dh = d === undefined ? sh : d; }
    else { sx = a; sy = b; sw = c; sh = d; dx = e; dy = f; dw = g; dh = h; }
    const s = this._s, m = s.m;
    if (s.clip) { const r = this._clipped(sx, sy, sw, sh, dx, dy, dw, dh); if (!r) return; [sx, sy, sw, sh, dx, dy, dw, dh] = r; }
    __cv.drawImage(this.canvas.__id, im.__id, sx, sy, sw, sh, dx, dy, dw, dh, m[0], m[1], m[2], m[3], m[4], m[5],
                   s.alpha, __OPS[s.op], s.blur > 0 ? s.shadow : 0, s.blur, s.bright, s.sat);
  }
  // paths: whole ellipses / circles (ellipse, arc) and polygons (moveTo, lineTo, curves as short lines, rect,
  // roundRect), each filled or stroked whole; a polygon left open is stroked open
  beginPath() { this._path = []; this._poly = null; }
  closePath() { if (this._poly) this._poly.closed = true; this._poly = null; }
  moveTo(x, y) { this._poly = [x, y]; this._path.push(this._poly); }
  lineTo(x, y) { if (!this._poly) this.moveTo(x, y); else this._poly.push(x, y); }
  quadraticCurveTo(cx, cy, x, y) {
    if (!this._poly) this.moveTo(cx, cy);
    const p = this._poly, x0 = p[p.length - 2], y0 = p[p.length - 1];
    for (let i = 1; i <= 12; i++) {
      const t = i / 12, u = 1 - t;
      p.push(u * u * x0 + 2 * u * t * cx + t * t * x, u * u * y0 + 2 * u * t * cy + t * t * y);
    }
  }
  bezierCurveTo(ax, ay, bx, by, x, y) {
    if (!this._poly) this.moveTo(ax, ay);
    const p = this._poly, x0 = p[p.length - 2], y0 = p[p.length - 1];
    for (let i = 1; i <= 14; i++) {
      const t = i / 14, u = 1 - t;
      p.push(u * u * u * x0 + 3 * u * u * t * ax + 3 * u * t * t * bx + t * t * t * x,
             u * u * u * y0 + 3 * u * u * t * ay + 3 * u * t * t * by + t * t * t * y);
    }
  }
  rect(x, y, w, h) {
    const p = [x, y, x + w, y, x + w, y + h, x, y + h];
    p.closed = true; p.rect = [x, y, w, h];
    this._path.push(p); this._poly = null;
  }
  roundRect(x, y, w, h, r = 0) {
    const rr = Math.max(0, Math.min(Array.isArray(r) ? r[0] || 0 : +r || 0, Math.abs(w) / 2, Math.abs(h) / 2));
    if (!rr) return this.rect(x, y, w, h);
    const p = [];
    for (const [cx, cy, a0] of [[x + w - rr, y + rr, -90], [x + w - rr, y + h - rr, 0], [x + rr, y + h - rr, 90], [x + rr, y + rr, 180]])
      for (let i = 0; i <= 4; i++) {
        const a = (a0 + i * 22.5) * Math.PI / 180;
        p.push(cx + rr * Math.cos(a), cy + rr * Math.sin(a));
      }
    p.closed = true;
    this._path.push(p); this._poly = null;
  }
  ellipse(x, y, rx, ry) { this._path.push({ x, y, rx, ry }); this._poly = null; }
  arc(x, y, r) { this._path.push({ x, y, rx: r, ry: r }); this._poly = null; }
  _shape(colour, line) {
    const s = this._s, m = s.m;
    colour = __col(colour);
    for (const p of this._path) {
      if (Array.isArray(p)) {
        if (p.length >= (line ? 4 : 6))
          __cv.poly(this.canvas.__id, p, m[0], m[1], m[2], m[3], m[4], m[5], colour, s.alpha, line, __OPS[s.op], line && !p.closed ? 1 : 0);
      }
      else __cv.ellipse(this.canvas.__id, p.x, p.y, p.rx, p.ry, m[0], m[1], m[2], m[3], m[4], m[5], colour, s.alpha, line, __OPS[s.op]);
    }
  }
  fill() { this._shape(this._s.fill, 0); }
  stroke() { this._shape(this._s.stroke, Math.max(1, this._s.lw)); }
  _text(t, x, y, colour, stroke) {
    const s = this._s, m = s.m;
    __cv.text(this.canvas.__id, String(t), x, y, m[0], m[1], m[2], m[3], m[4], m[5], s.size, s.bold,
              __ALIGN[s.align] || 0, __BASE[s.base] || 0, colour, s.alpha, stroke);
  }
  fillText(t, x, y) { this._text(t, x, y, __col(this._s.fill), 0); }
  strokeText(t, x, y) { this._text(t, x, y, __col(this._s.stroke), Math.max(1, this._s.lw)); }
  getImageData(x, y, w, h) {
    const b = __cv.pixels(this.canvas.__id, x, y, w, h);
    return { width: w, height: h, data: b ? new Uint8ClampedArray(b) : new Uint8ClampedArray(w * h * 4) };
  }
  measureText(t) { return { width: __cv.measure(String(t), this._s.size, this._s.bold) }; }
}

class HTMLCanvasElement {
  constructor(id, w, h) { this.__id = id; this._w = w; this._h = h; this._ctx = null; this.style = {}; }
  get width() { return this._w; } set width(v) { this._w = Math.max(0, v | 0); __cv.resize(this.__id, this._w, this._h); }
  get height() { return this._h; } set height(v) { this._h = Math.max(0, v | 0); __cv.resize(this.__id, this._w, this._h); }
  getContext() { return this._ctx || (this._ctx = new CanvasRenderingContext2D(this)); }
}

class Image {
  constructor() { this.width = 0; this.height = 0; this.complete = false; this.onload = null; this.onerror = null; }
  get src() { return this._src; }
  set src(p) {
    this._src = p;
    const r = __cv.loadImage(__file(p).replace(/\.(png|jpe?g|webp)$/i, '.hli'));
    Promise.resolve().then(() => {
      if (!r) { if (this.onerror) this.onerror(); else if (this.onload) this.onload(); return; }
      [this.__id, this.width, this.height] = r; this.complete = true;
      if (this.onload) this.onload();
    });
  }
}

// the page's side panel and buttons do not exist here: stand-ins that accept what the page does with them
function __element() {
  return { textContent: '', innerHTML: '', style: {}, dataset: {}, classList: { add() {}, remove() {}, toggle() {} },
           insertAdjacentHTML() {}, addEventListener() {}, appendChild() {}, onclick: null };
}
const __screen = new HTMLCanvasElement(0, 640, 480);
globalThis.document = {
  getElementById: id => id === 'c' ? __screen : __element(),
  createElement: t => t === 'canvas' ? new HTMLCanvasElement(__cv.newCanvas(0, 0), 0, 0) : __element(),
  querySelectorAll: () => [], querySelector: () => null, addEventListener() {}, body: __element()
};
globalThis.addEventListener = () => {};
globalThis.performance = { now: () => __cv.now() };

let __raf = [];
globalThis.requestAnimationFrame = cb => { __raf.push(cb); return __raf.length; };
let __timers = [], __timerId = 1;
globalThis.setTimeout = (cb, ms = 0) => { __timers.push({ id: __timerId, at: __cv.now() + ms, cb }); return __timerId++; };
globalThis.clearTimeout = id => { __timers = __timers.filter(t => t.id !== id); };

// one standard game pad: the R36S buttons (r36s/js_sdl2.c) in the page's own index order
const __gamepad = { index: 0, connected: true, mapping: 'standard', buttons: Array.from({ length: 17 }, () => ({ pressed: false, value: 0 })) };
globalThis.navigator = {
  getGamepads: () => {
    const bits = __cv.pad();
    for (let i = 0; i < 17; i++) { const on = !!(bits & (1 << i)); __gamepad.buttons[i].pressed = on; __gamepad.buttons[i].value = on ? 1 : 0; }
    return [__gamepad];
  }
};

// files of the game folder through fetch (the game reads its pet / room data as JSON)
globalThis.fetch = url => {
  const t = __cv.readText(__file(url));
  return Promise.resolve({ ok: t !== null, status: t !== null ? 200 : 404,
                           text: () => Promise.resolve(t), json: () => Promise.resolve(JSON.parse(t)) });
};
// localStorage kept on the card: one file per key in the save folder (__cv.saveDir), written safely by the runtime
globalThis.localStorage = {
  getItem: k => __cv.readText(`${__cv.saveDir}/${k}.json`),
  setItem: (k, v) => { __cv.writeText(`${__cv.saveDir}/${k}.json`, String(v)); },
  removeItem: k => { __cv.writeText(`${__cv.saveDir}/${k}.json`, ''); },
};
// the game's sounds (in a browser, index.html makes these with <audio>)
globalThis.SOUND = { sfx: (name, vol) => __cv.sfx(name, vol), music: name => __cv.music(name || '') };

// QuickJS prints numbers without grouping: the page asks for 'en-US' (10,000)
Number.prototype.toLocaleString = function () {
  const [i, f] = String(this).split('.');
  return i.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (f ? '.' + f : '');
};

// called by the runtime once a frame
globalThis.__frame = now => {
  if (__timers.length) {
    const due = __timers.filter(t => t.at <= now);
    if (due.length) { __timers = __timers.filter(t => t.at > now); for (const t of due) t.cb(); }
  }
  const cbs = __raf; __raf = [];
  for (const cb of cbs) cb(now);
};
