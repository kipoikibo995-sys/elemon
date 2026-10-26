// Cuts the arena's sheets ahead of time, for the R36S (scripts/solo_r36s.py runs it): the arena page's own cut() and
// cutLines() (preview/dau-truong/index.html), so the frames are exactly the ones the browser cuts, run here in Node on
// raw pixels instead of a canvas. The R36S is far too slow to cut ~50 MB of sheets at the start of every match.
//   node solo_cut.js <index.html> <jobs.json>
// jobs.json: [{ in: "<file>.rgba", cols, rows, out: "<dir>" }]; a .rgba file is u32 width, u32 height, then RGBA bytes.
// Writes <dir>/<i>.rgba for every frame and <dir>/frames.json = [[w, h, ax, ay], ...].
const fs = require('fs'), path = require('path');
const [page, jobsFile] = process.argv.slice(2);
const html = fs.readFileSync(page, 'utf8').replace(/\r\n/g, '\n');
const grab = (start, end) => { const a = html.indexOf(start), b = html.indexOf(end, a); if (a < 0 || b < 0) throw new Error('not found: ' + start); return html.slice(a, b); };
const code = grab('function cutLines(', '\n}\n') + '\n}\n' + grab('const POKE_SHARE', '\n}\n') + '\n}\n';

// the few canvas pieces cut() touches: a whole-sheet canvas it reads, and the frame canvases it writes
class Canvas {
  constructor() { this.width = 0; this.height = 0; this.data = null; }
  getContext() {
    const c = this;
    return {
      drawImage(img) { c.data = img.data; },
      getImageData() { return { data: c.data }; },
      createImageData(w, h) { return { data: new Uint8ClampedArray(w * h * 4) }; },
      putImageData(d) { c.data = d.data; },
    };
  }
}
const document = { createElement: () => new Canvas() };
const cut = new Function('document', code + '\nreturn cut;')(document);

for (const job of JSON.parse(fs.readFileSync(jobsFile, 'utf8'))) {
  const buf = fs.readFileSync(job.in), W = buf.readUInt32LE(0), H = buf.readUInt32LE(4);
  const img = { width: W, height: H, data: new Uint8ClampedArray(buf.buffer, buf.byteOffset + 8, W * H * 4) };
  const cells = cut(img, job.cols, job.rows);
  fs.mkdirSync(job.out, { recursive: true });
  const meta = cells.map((cell, i) => {
    const head = Buffer.alloc(8); head.writeUInt32LE(cell.c.width, 0); head.writeUInt32LE(cell.c.height, 4);
    fs.writeFileSync(path.join(job.out, i + '.rgba'), Buffer.concat([head, Buffer.from(cell.c.data ? cell.c.data.buffer : new ArrayBuffer(cell.c.width * cell.c.height * 4))]));
    return [cell.w, cell.h, cell.ax, cell.ay];
  });
  fs.writeFileSync(path.join(job.out, 'frames.json'), JSON.stringify(meta));
  process.stdout.write('.');
}
process.stdout.write('\n');
