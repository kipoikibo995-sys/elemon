"""Shows creatures living in the pet homes: preview/phong/<scene>.gif at 320x240 (shown 2x), 30 fps,
plus preview/phong/index.html and assets/KIEM-KE-NEN.md (which home has which pictures).

A home's picture is assets/source/nen/<code>_<slug>_<ngay|dem>.png; a home that has no finished
day picture yet falls back to its empty room phong-trong/PT_<code>_*.png (the khai-niem pictures
are not used: some have a pet drawn in them).
Usage: python preview_rooms.py
"""
import glob, json, os, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import creatures
from preview_anims import STEP, LABELS, breathe, flash, samples

NEN = os.path.join(creatures.ROOT, 'assets', 'source', 'nen')
OUT = os.path.join(creatures.ROOT, 'preview', 'phong')
FLOOR_Y = 206          # where the feet stand on the 320x240 screen (approved on the Lv1/Lv3/Lv4 homes)

# code -> (name, tier, floor y). Lv2 rooms have a dark rock / railing strip at the bottom, so their
# floor sits higher.
HOMES = {
    'N0-1': ('Hang đá hoang', 1, FLOOR_Y), 'N0-2': ('Nhà hoang', 1, FLOOR_Y),
    'L2-HO': ('Hang bếp than', 2, 162), 'L2-KI': ('Lán thợ mỏ', 2, 168), 'L2-MO': ('Lều tranh', 2, 155),
    'L2-TH': ('Chòi chài', 2, 152), 'L2-TO': ('Nhà vách đất', 2, 165),
    'N1-HO': ('Lò rèn núi lửa', 3, FLOOR_Y), 'N1-KI': ('Xưởng kim loại', 3, FLOOR_Y),
    'N1-MO': ('Chòi trên cây', 3, FLOOR_Y), 'N1-TH': ('Nhà sàn bên hồ', 3, FLOOR_Y),
    'N1-TO': ('Nhà đất nung', 3, FLOOR_Y),
    'N2-HO': ('Đền Hỏa Long', 4, FLOOR_Y), 'N2-KI': ('Điện Kim Cương', 4, FLOOR_Y),
    'N2-MO': ('Cây Thần', 4, FLOOR_Y), 'N2-TH': ('Thủy Cung', 4, FLOOR_Y), 'N2-TO': ('Thạch Điện', 4, FLOOR_Y),
}
TIERS = {1: 'Lv1 – Tân thủ', 2: 'Lv2 – Bình dân', 3: 'Lv3 – Cao cấp', 4: 'Lv4 – Cao nhất'}

# (home code, time, creature, stage, x, moves)
SCENES = [
    ('N0-1', 'ngay', 'hoa-ho', 'baby', 150, ['idle', 'walk', 'happy', 'eat']),
    ('N0-2', 'ngay', 'moc-hung', 'egg', 160, ['idle', 'shake', 'hatch']),
    ('L2-HO', 'ngay', 'hoa-linh', 'child', 165, ['idle', 'happy', 'eat']),
    ('L2-KI', 'ngay', 'kim-te', 'teen', 150, ['idle', 'walk', 'happy']),
    ('L2-MO', 'ngay', 'moc-hung', 'baby', 165, ['idle', 'walk', 'sleep']),
    ('L2-TH', 'ngay', 'thuy-long', 'child', 165, ['idle', 'happy', 'eat']),
    ('L2-TO', 'ngay', 'tho-nguu', 'adult', 160, ['idle', 'punch', 'victory']),
    ('N1-HO', 'ngay', 'hoa-ho', 'adult', 140, ['idle', 'punch', 'blast', 'victory']),
    ('N1-TH', 'ngay', 'thuy-sa', 'child', 160, ['idle', 'happy', 'eat']),
    ('N1-TO', 'dem', 'tho-long', 'child', 165, ['sleep', 'wake', 'idle']),
    ('N2-MO', 'ngay', 'moc-loc', 'teen', 165, ['idle', 'walk', 'happy']),
    ('N2-KI', 'ngay', 'kim-ung', 'adult', 150, ['idle', 'blast', 'victory']),
]


def home_files(code):
    """{'ngay': path, 'dem': path, 'trong': path, 'khai-niem': path} for what exists."""
    found = {}
    for t in ('ngay', 'dem'):
        hit = glob.glob(os.path.join(NEN, f'{code}_*_{t}.png'))
        if hit:
            found[t] = hit[0]
    hit = glob.glob(os.path.join(NEN, 'phong-trong', f'PT_{code}_*.png'))
    if hit:
        found['trong'] = hit[0]
    hit = glob.glob(os.path.join(NEN, 'khai-niem', f'KN_{code}_*.png'))
    if hit:
        found['khai-niem'] = hit[0]
    return found


def background(code, time):
    files = home_files(code)
    if time in files:
        return files[time], time
    if time == 'ngay' and 'trong' in files:
        return files['trong'], 'trong'
    raise SystemExit(f'{code}: no {time} picture')


def shadow(w):
    """A soft dark ellipse w px wide, as an RGBA image."""
    img = Image.new('RGBA', (w + 8, 14), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([4, 3, w + 4, 11], fill=(0, 0, 0, 90))
    return img.filter(ImageFilter.GaussianBlur(1.5))


def scene(code, time, cid, stage, cx, moves, font):
    home, tier, floor = HOMES[code]
    path, used = background(code, time)
    name = f'{code}_{time}_{cid}-{stage}'
    bg = Image.open(path).convert('RGBA').resize((320, 240), Image.LANCZOS)
    fr = creatures.frames_dir(cid, stage)
    meta = json.load(open(os.path.join(fr, 'frames.json')))
    anims = json.load(open(creatures.anims_path(cid, stage), encoding='utf-8'))
    frames = {n: Image.open(os.path.join(fr, 'png', n + '.png')).convert('RGBA') for n in meta['frames']}
    ax, ay = meta['anchor']
    split = ay - round(meta['canvas'][1] * 0.4)
    base_shadow = shadow(int(meta['canvas'][0] * 0.55))
    rnd = random.Random(3)
    title = f"{creatures.CREATURES[cid]['name']} ({creatures.STAGE_NAMES[stage]})"
    shots = []
    for move in moves:
        anim = anims[move]
        smp = samples(anim)
        if anim['loop']:
            smp = smp * max(1, round(2200 / (len(smp) * STEP)))
        else:
            smp = smp + [smp[-1]] * 10
        for f, x, y, br, shake, fl in smp:
            s = bg.copy()
            lift = max(0.0, -y)
            sh = base_shadow.resize((max(8, int(base_shadow.size[0] * (1 - lift / 80))), base_shadow.size[1]))
            s.alpha_composite(sh, (cx + round(x) - sh.size[0] // 2, floor - 7))
            img = breathe(frames[f], round(br), split)
            if fl:
                img = flash(img, 0.75)
            jx = rnd.randint(-shake, shake) if shake else 0
            jy = rnd.randint(-shake, shake) // 2 if shake else 0
            dx = meta['align'].get(f, [0, 0])[0]
            s.alpha_composite(img, (cx - ax + dx + round(x) + jx, floor - ay + round(y) + jy))
            s = s.resize((640, 480), Image.NEAREST)
            d = ImageDraw.Draw(s)
            d.rectangle([0, 0, 640, 30], fill=(0, 0, 0))
            d.text((10, 5), f"{title} · {LABELS.get(move, move)}", fill=(255, 230, 160), font=font)
            shots.append(s.convert('RGB'))
    shots[0].save(os.path.join(OUT, name + '.gif'), save_all=True, append_images=shots[1:], duration=STEP, loop=0)
    shots[len(shots) // 3].save(os.path.join(OUT, name + '.png'))
    print(f'{name}: {len(shots)} frames')
    note = {'ngay': 'ngày', 'dem': 'đêm', 'trong': 'phòng trống (chưa có bản ngày)'}[used]
    return dict(file=name + '.gif', tier=tier, label=f'{home} ({code}) · {note} · {title}')


def write_index(items):
    sections = []
    for tier, tname in TIERS.items():
        figs = ''.join(f'<figure><img src="{it["file"]}" loading="lazy"><figcaption>{it["label"]}</figcaption></figure>'
                       for it in items if it['tier'] == tier)
        if figs:
            sections.append(f'<h2>{tname}</h2><div class="grid">{figs}</div>')
    html = f'''<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Pet trong nhà</title><style>
body{{margin:0;background:#16171d;color:#f1e6cf;font:15px "Segoe UI",sans-serif;padding:16px}}
h1{{color:#ffcf6e;font-size:20px;margin:0 0 4px}} h2{{font-size:17px;margin:20px 0 8px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:12px}}
figure{{margin:0;background:#22242e;border-radius:8px;overflow:hidden}}
img{{width:100%;display:block;image-rendering:pixelated}} figcaption{{padding:6px 10px;color:#9c9488}}
</style></head><body><h1>Pet trong nhà</h1><p style="color:#9c9488;margin:0">Màn 320×240 phóng to 2 lần</p>
{''.join(sections)}</body></html>'''
    with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8') as fh:
        fh.write(html)


def write_inventory():
    cols = [('ngay', 'Ngày'), ('dem', 'Đêm'), ('trong', 'Phòng trống'), ('khai-niem', 'Khái niệm')]
    lines = ['# Kiểm kê nơi nuôi', '',
             'Sinh tự động bởi `scripts/preview_rooms.py` từ `assets/source/nen/`. ✓ có file · – chưa có.', '',
             '| Cấp | Mã | Nhà | ' + ' | '.join(c[1] for c in cols) + ' |', '|---|---|---|' + '---|' * len(cols)]
    for code, (name, tier, _) in HOMES.items():
        f = home_files(code)
        lines.append(f'| {tier} | {code} | {name} | ' + ' | '.join('✓' if k in f else '–' for k, _ in cols) + ' |')
    with open(os.path.join(creatures.ROOT, 'assets', 'KIEM-KE-NEN.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')


def main():
    os.makedirs(OUT, exist_ok=True)
    for old in glob.glob(os.path.join(OUT, '*.gif')) + glob.glob(os.path.join(OUT, '*.png')):
        os.remove(old)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 16)
    write_index([scene(*sc, font) for sc in SCENES])
    write_inventory()


if __name__ == '__main__':
    main()
