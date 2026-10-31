"""Vùng đất on the PC test of the R36S runtime (build/qjs-host/holua-game-test, under WSL): a save with a Nhi pet is
continued, the pet goes out to the Hỏa region, walks its first khu and fights, and each frame's time is measured.
    python scripts/vung_dat_test.py [--pack] [--boss]
--pack first packs build/vung-dat/game/tien-hoa (scripts/vung_dat.py --thu) into build/vung-dat/dist/elemon, as
scripts/r36s_game.py does for the card (dist/elemon is left alone). Frames go to build/vung-dat/test/out (every 6th as
.ppm, and a contact sheet sheet.png); the frame times of the loading, the walk and the fight are printed.
"""
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEST = os.path.join(ROOT, 'build', 'vung-dat', 'test')
DIST = os.path.join(ROOT, 'build', 'vung-dat', 'dist')
EVERY = 6
# the scenario at 30 frames a second: (name of the part, its words for holua-game-test). UP:40 holds UP 40 frames
PARTS = [
    ('mở bản lưu', '90 A 150'),
    ('ra bản đồ', 'RIGHT RIGHT RIGHT RIGHT RIGHT A 45'),
    ('chọn vùng Hỏa', 'UP UP 15 A 45'),
    ('màn cổng', '30 A 20'),
    ('nạp khu 1', '90'),
    ('đi bộ', (0.70, 0.47)),                     # to the crystal nest right of the path
    ('đánh', 'A 6 A 6 A 20 B 20 A 6 A 6 A 20 UP:15 A 6 A 6 A 20 B 25 X 10 A 6 A 6 A 20 B 20 RIGHT:20 A 6 A 6 A 20 B 30'),
    ('đánh tiếp', 'UP:25 A 6 A 6 A 20 B 20 A 6 A 6 A 20 Y 60 A 6 A 6 A 20 B 30 LEFT:20 A 6 A 6 A 20'),
    ('tạm dừng, rời vùng', 'START 20 DOWN 10 A 60 A 40'),
]
# --boss: the region's maps are only its boss khu (HOLUA_VUNG_SRC with one map): the most nests and foes at once;
# the walk there is found on the khu's walk grid (route())
BOSS = PARTS[:5] + [
    ('đi bộ', (0.45, 0.45)),
    ('đánh đông quái', ' '.join(['A 6 A 6 A 20 B 20 UP:8 A 6 A 6 A 20 RIGHT:8'] * 6)),
    ('tuyệt chiêu', 'Y 60 A 6 A 6 A 20 B 30 UP,RIGHT:20 A 6 A 6 A 20'),
    ('đánh tiếp', ' '.join(['A 6 A 6 A 20 B 20 RIGHT:10 A 6 A 6 A 20 UP:10'] * 5)),
]


def route(data, he, goal, spd=144):
    """Held arrows that walk the pet from its way into the region's first khu to goal (a share of the map's width and
    height), along the shortest way on the walk grid (8 directions, no corner cutting). spd: the pet's px a second."""
    from collections import deque
    k = data['regions'][he]['khu'][0]
    C, rows = data['C'], k['grid']
    side, a, b = k['exits'][k['in']]
    m = (a + b) / 2
    sx, sy = {'top': (m, 44), 'bottom': (m, k['h'] - 44), 'left': (44, m), 'right': (k['w'] - 44, m)}[side]
    free = lambda x, y: 0 <= y < len(rows) and 0 <= x < len(rows[0]) and rows[y][x] != '#'
    start, end = (int(sx // C), int(sy // C)), (int(goal[0] * k['w'] // C), int(goal[1] * k['h'] // C))
    while not free(*end):
        end = (end[0] + 1, end[1])
    prev, q = {start: None}, deque([start])
    while q:
        c = q.popleft()
        if c == end:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            n = (c[0] + dx, c[1] + dy)
            if n not in prev and free(*n) and (not dx or not dy or (free(c[0] + dx, c[1]) and free(c[0], c[1] + dy))):
                prev[n] = c
                q.append(n)
    steps, c = [], end
    while prev.get(c):
        p = prev[c]
        steps.append((c[0] - p[0], c[1] - p[1]))
        c = p
    steps.reverse()
    words, i = [], 0
    names = {1: 'RIGHT', -1: 'LEFT'}, {1: 'DOWN', -1: 'UP'}
    while i < len(steps):
        j = i
        while j < len(steps) and steps[j] == steps[i]:
            j += 1
        dx, dy = steps[i]
        held = ','.join(filter(None, (names[1].get(dy), names[0].get(dx))))
        px = (j - i) * C * (1.4142 if dx and dy else 1)
        words.append(f'{held}:{max(1, round(px / spd * 30))}')
        i = j
    return ' '.join(words)


def frames(words):
    n = 0
    for w in words.split():
        if w.isdigit():
            n += int(w)
        elif ':' in w:
            n += int(w.split(':')[1])
        else:
            n += 15                                  # a tap: 3 frames down, 12 up
    return n


def save_fixture(path):
    """A Nhi Hỏa Hổ, rested and fed, its story scenes seen, the save written now (no time to play through)."""
    s = json.load(open(os.path.join(HERE, 'vung_dat_save.json'), encoding='utf-8'))
    s['wall'] = int(time.time() * 1000)
    s['S'].update(mode='room', vung={}, vg=None)
    s['S']['need'].update(no=90, vui=80, sach=90, nl=95)
    story = os.path.join(ROOT, 'game', 'src', 'truyen.js')          # every story scene seen: no talk in the way
    if os.path.exists(story):
        import re
        for sid in re.findall(r"\bid: '([^']+)'", open(story, encoding='utf-8').read()):
            s['S']['truyen']['da'][sid] = 1
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(s, open(path, 'w', encoding='utf-8'), ensure_ascii=False)


def wsl(p):
    p = os.path.abspath(p).replace('\\', '/')
    return '/mnt/' + p[0].lower() + p[2:]


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    boss = '--boss' in sys.argv                      # before --pack's r36s_game.main() takes sys.argv
    if '--pack' in sys.argv:
        sys.path.insert(0, HERE)
        import r36s_game
        r36s_game.DIST, r36s_game.GAME = DIST, os.path.join(DIST, 'elemon')
        sys.argv = [sys.argv[0], os.path.join(ROOT, 'build', 'vung-dat', 'game', 'tien-hoa')]
        r36s_game.main()
    out, save = os.path.join(TEST, 'out'), os.path.join(TEST, 'save')
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))
    save_fixture(os.path.join(save, 'holua-save-1.json'))
    parts = BOSS if boss else PARTS
    if any(not isinstance(w, str) for _, w in parts):
        js = open(os.path.join(DIST, 'elemon', 'js', 'vung-dat.js'), encoding='utf-8').read()
        data = json.loads(js.split('const VG = ', 1)[1].split(';', 1)[0])
        parts = [(n, w if isinstance(w, str) else route(data, 'hoa', w)) for n, w in parts]
    script = os.path.join(TEST, 'kich-ban.txt')
    with open(script, 'w', encoding='utf-8', newline='\n') as fh:
        for name, words in parts:
            fh.write(f'# {name}\n{words}\n')
    cmd = (f'cd {wsl(ROOT)} && HOLUA_TEST=1 HOLUA_SAVE_DIR={wsl(save)} build/qjs-host/holua-game-test '
           f'{wsl(os.path.join(DIST, "elemon"))} {wsl(out)} {EVERY} {wsl(script)}')
    r = subprocess.run(['wsl', 'bash', '-lc', cmd], capture_output=True, text=True, encoding='utf-8', errors='replace')
    log = r.stdout + r.stderr
    open(os.path.join(TEST, 'log.txt'), 'w', encoding='utf-8').write(log)
    print('\n'.join(l for l in log.splitlines() if 'vung-dat' in l or 'frames' in l or 'rror' in l)[-3000:])
    ms = [float(x) for x in open(os.path.join(out, 'times.txt')).read().split()]
    at = 0
    print(f'{"phần":22} {"khung":>6} {"tb ms":>7} {"p95":>7} {"max":>7}')
    for name, words in parts:
        n = frames(words)
        part = sorted(ms[at:at + n])
        if part:
            print(f'{name:22} {len(part):6} {sum(part) / len(part):7.2f} {part[int(len(part) * 0.95) - 1 if len(part) > 1 else 0]:7.2f} {part[-1]:7.2f}')
        at += n
    sheet(out)


def sheet(out):
    """Every 6th of the written frames, half size, 4 across: build/vung-dat/test/sheet.png"""
    from PIL import Image
    fs = sorted(f for f in os.listdir(out) if f.endswith('.ppm'))[::6]
    if not fs:
        return
    cols, w, h = 4, 320, 240
    im = Image.new('RGB', (cols * w, -(-len(fs) // cols) * h))
    for i, f in enumerate(fs):
        im.paste(Image.open(os.path.join(out, f)).resize((w, h)), ((i % cols) * w, (i // cols) * h))
    im.save(os.path.join(TEST, 'sheet.png'))
    print('sheet:', os.path.join(TEST, 'sheet.png'), len(fs), 'khung')


if __name__ == '__main__':
    main()
