"""Writes the overview of every creature at every stage:
  preview/index.html          pick element > creature > stage, see each move (GIFs from preview_anims.py)
  assets/creatures/KIEM-KE.md the same as a table: done / to redo / missing
Open index.html in any browser; it only reads the GIFs next to it."""
import json, os

import creatures

MOVE_NAMES = {'idle': 'Đứng thở', 'walk': 'Đi', 'run': 'Chạy', 'attack': 'Đòn hệ', 'punch': 'Đấm', 'blast': 'Chiêu', 'hit': 'Trúng đòn',
              'faint': 'Gục ngã', 'victory': 'Thắng', 'eat': 'Ăn', 'happy': 'Vui nhảy', 'tired': 'Mệt',
              'sick': 'Ốm', 'sleep': 'Ngủ', 'wake': 'Thức dậy', 'shake': 'Lắc', 'hatch': 'Nở'}
MARK = {'done': '✓', 'redo': '✗', 'missing': '–', 'na': '·'}

PAGE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tinh Linh - xem chuyển động</title>
<style>
:root { --bg:#16171d; --panel:#22242e; --text:#f1e6cf; --muted:#9c9488; --gold:#ffcf6e; --bad:#ff7a6e; }
body { margin:0; background:var(--bg); color:var(--text); font:15px/1.4 "Segoe UI", sans-serif; }
header { position:sticky; top:0; background:var(--bg); padding:12px 16px; border-bottom:1px solid #333; z-index:1; }
h1 { margin:0 0 8px; font-size:20px; color:var(--gold); }
.he { display:flex; flex-wrap:wrap; gap:6px; align-items:center; margin:4px 0; }
.he b { width:44px; color:var(--muted); font-weight:600; }
button { background:var(--panel); color:var(--text); border:1px solid #3a3d4a; border-radius:6px; padding:5px 10px;
         cursor:pointer; font:inherit; }
button.on { border-color:var(--gold); color:var(--gold); }
button:disabled { opacity:.45; cursor:default; }
button.redo { color:var(--bad); }
button small { color:var(--muted); margin-left:4px; letter-spacing:1px; }
#stages { display:flex; gap:6px; flex-wrap:wrap; margin-top:8px; }
main { padding:16px; }
h2 { margin:0 0 4px; }
#note { color:var(--muted); margin:0 0 12px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:12px; }
figure { margin:0; background:var(--panel); border-radius:8px; overflow:hidden; }
figure img { width:100%; display:block; image-rendering:pixelated; }
figcaption { padding:6px 10px; color:var(--muted); }
</style></head><body>
<header><h1>Tinh Linh Ngũ Hành</h1><div id="pick"></div><div id="stages"></div></header>
<main><h2 id="title"></h2><p id="note"></p><div class="grid" id="moves"></div></main>
<script>
const DATA = __DATA__;
const STAGES = __STAGES__;
const MOVES = __MOVES__;
let cur = { id: DATA[0].id, stage: 'adult' };
function save() { try { localStorage.setItem('tinhlinh-pick', JSON.stringify(cur)); } catch (e) {} }
function render() {
  const c = DATA.find(x => x.id === cur.id);
  if (c.units[cur.stage].state !== 'done')
    cur.stage = STAGES.map(s => s[0]).reverse().find(s => c.units[s].state === 'done') || cur.stage;
  const u = c.units[cur.stage];
  document.querySelectorAll('#pick button').forEach(b => b.classList.toggle('on', b.dataset.id === cur.id));
  document.getElementById('stages').innerHTML = STAGES.map(([s, name]) => {
    const st = c.units[s].state;
    return `<button data-s="${s}" class="${s === cur.stage ? 'on' : ''} ${st === 'redo' ? 'redo' : ''}"
      ${st === 'done' ? '' : 'disabled'} ${st === 'na' ? 'hidden' : ''}>${name}${st === 'redo' ? ' (cần làm lại)' : st === 'missing' ? ' (chưa có)' : ''}</button>`;
  }).join('');
  document.querySelectorAll('#stages button').forEach(b => b.onclick = () => { cur.stage = b.dataset.s; save(); render(); });
  document.getElementById('title').textContent = `${c.name} · ${c.he} · ${c.branch} · ${STAGES.find(s => s[0] === cur.stage)[1]}`;
  document.getElementById('note').textContent = u.state === 'done' ? '' : 'Cấp này chưa có hình dùng được.';
  document.getElementById('moves').innerHTML = u.state !== 'done' ? '' : u.moves.map(m =>
    `<figure><img src="${c.he_dir}/${c.id}/${cur.stage}/${m}.gif" alt="${MOVES[m] || m}" loading="lazy">
     <figcaption>${MOVES[m] || m}</figcaption></figure>`).join('');
}
const pick = document.getElementById('pick');
[...new Set(DATA.map(c => c.he))].forEach(he => {
  const row = document.createElement('div'); row.className = 'he';
  row.innerHTML = '<b>' + he + '</b>';
  DATA.filter(c => c.he === he).forEach(c => {
    const b = document.createElement('button'); b.dataset.id = c.id;
    b.innerHTML = c.name + '<small>' + STAGES.filter(([s]) => c.units[s].state !== 'na').map(([s]) => c.units[s].mark).join('') + '</small>';
    if (STAGES.some(([s]) => c.units[s].state === 'redo')) b.classList.add('redo');
    b.onclick = () => { cur.id = c.id; save(); render(); };
    row.appendChild(b);
  });
  pick.appendChild(row);
});
try { const s = JSON.parse(localStorage.getItem('tinhlinh-pick')); if (s && DATA.some(c => c.id === s.id)) cur = s; } catch (e) {}
render();
</script></body></html>
"""


def unit_state(cid, stage):
    c = creatures.CREATURES[cid]
    if creatures.LAYOUT[stage] == 'four' and cid not in creatures.QUADRUPEDS:
        return 'na'
    if stage in c['redo']:
        return 'redo'
    if stage in c['sheets'] and os.path.exists(os.path.join(creatures.preview_dir(cid, stage), 'showreel.gif')):
        return 'done'
    return 'missing'


def moves(cid, stage):
    path = os.path.join(creatures.frames_dir(cid, stage), 'anims.json')
    if not os.path.exists(path):
        return []
    return [k for k in json.load(open(path, encoding='utf-8')) if not k.startswith('_')]


def main():
    data = []
    for cid, c in creatures.CREATURES.items():
        units = {}
        for st in creatures.STAGES:
            state = unit_state(cid, st)
            units[st] = {'state': state, 'mark': MARK[state], 'moves': moves(cid, st) if state == 'done' else []}
        data.append({'id': cid, 'name': c['name'], 'he': creatures.element_name(cid), 'he_dir': c['element'],
                     'branch': creatures.branch_name(cid), 'units': units})
    stages = [[s, creatures.STAGE_NAMES[s]] for s in creatures.STAGES]
    html = PAGE.replace('__DATA__', json.dumps(data, ensure_ascii=False)) \
               .replace('__STAGES__', json.dumps(stages, ensure_ascii=False)) \
               .replace('__MOVES__', json.dumps(MOVE_NAMES, ensure_ascii=False))
    with open(os.path.join(creatures.ROOT, 'preview', 'index.html'), 'w', encoding='utf-8') as fh:
        fh.write(html)

    lines = ['# Kiểm kê tinh linh', '',
             'Sinh tự động bởi `scripts/make_preview_page.py`. ✓ đã có khung chuyển động · '
             f'✗ cần làm lại ({creatures.REDO_WHY}) · – chưa có file · · không có dạng này (chỉ 13 con đi 4 chân).', '',
             '| Hệ | Nhánh | Mã | Tinh linh | ' + ' | '.join(creatures.STAGE_NAMES[s] for s in creatures.STAGES) + ' |',
             '|---|---|---|---|' + '---|' * len(creatures.STAGES)]
    count = {'done': 0, 'redo': 0, 'missing': 0, 'na': 0}
    for d in data:
        c = creatures.CREATURES[d['id']]
        cells = []
        for s in creatures.STAGES:
            count[d['units'][s]['state']] += 1
            cells.append(d['units'][s]['mark'])
        lines.append(f"| {d['he']} | {d['branch']} | {c['code']}-{c['branch']} | {d['name']} | " + ' | '.join(cells) + ' |')
    lines += ['', f"Tổng: {count['done']} ✓, {count['redo']} ✗, {count['missing']} –"]
    with open(os.path.join(creatures.ROOT, 'assets', 'creatures', 'KIEM-KE.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    print(f"{len(data)} creatures: {count['done']} done, {count['redo']} to redo, {count['missing']} missing")


if __name__ == '__main__':
    main()
