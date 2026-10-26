"""Solo đối kháng for the R36S: everything the arena (preview/dau-truong) reads, made ready for the handheld, written
into the R36S game package by r36s_game.py:
    up/solo/cut/<sheet path>/<i>.hli   every sheet cut ahead of time by the arena's own cut() (scripts/solo_cut.js,
                                       run in Node), frames at half size (still more than they are drawn at)
    js/solo-cuts.js                    __SOLO_CUTS: for each sheet the frames' size and anchor at full size, so the
                                       arena draws them exactly as in the browser (game/src/solo.js loads them)
    up/solo/ui/...                     health bars, badge, arenas (san/) and san.json
    sfx/solo/..., nhac/solo-*.wav      its sounds and battle music, ogg -> 22050 Hz mono WAV (ffmpeg)
Only the pets in game/src/solo.js's ROSTER (and the tiger sheets the arena always loads) are packed.
Usage: python solo_r36s.py <R36S game folder>          (r36s_game.py calls build())
"""
import glob, json, os, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARENA = os.path.join(ROOT, 'preview', 'dau-truong')
K = 0.5                                     # frames at half size
BODY = [('s', 4, 4), ('se', 4, 4), ('e', 4, 4), ('ne', 4, 4), ('n', 4, 4), ('chung', 4, 2)]
FX = [('fx1', 4, 2), ('fx2', 4, 2), ('fx3', 4, 2), ('fx4', 4, 3), ('aura', 4, 2), ('cutin', 1, 1)]
EXTRA = [('vo', 4, 2), ('no', 4, 2)]          # the fire kit's (the arena loads them when PET.kit is 'hoa')
PET_SOUNDS = ['j', 'k', 'l', 'gong', 'ult', 'dau', 'nga', 'trung', 'nang']


def roster():
    src = open(os.path.join(ROOT, 'game', 'src', 'solo.js'), encoding='utf-8').read()
    return re.findall(r"\['\w+', '([a-z-]+)', '[^']+', '\w+'\]", src)


def sheets():
    """(path as the arena asks for it, cols, rows) of every sheet a match can load."""
    out = [(f'img/nhi/{n}.png', c, r) for n, c, r in BODY] + [(f'img/{n}.png', c, r) for n, c, r in FX]
    for d in roster():
        out += [(f'img/{d}/{n}.png', c, r) for n, c, r in BODY + FX + EXTRA]
        out += [(f'img/{d}/{n}_lv2.png', c, r) for n, c, r in FX if n != 'cutin']
    return [s for s in out if os.path.exists(os.path.join(ARENA, s[0]))]


def frame_hli(args):
    """One cut frame: raw RGBA -> half size -> .hli (8-bit with alpha per colour when that looks the same)."""
    raw, dst = args
    sys.path.insert(0, HERE)
    import r36s_pak
    from r36s_app import write_hli
    b = open(raw, 'rb').read()
    w, h = int.from_bytes(b[0:4], 'little'), int.from_bytes(b[4:8], 'little')
    im = Image.frombytes('RGBA', (w, h), b[8:8 + w * h * 4]) if w * h else Image.new('RGBA', (1, 1))
    im = im.resize((max(1, round(w * K)), max(1, round(h * K))), Image.LANCZOS)
    a = np.array(im)
    a[..., 3] = np.where(a[..., 3] < 96, 0, 255)            # solid pixels, as the sheets were drawn
    im = Image.fromarray(a)
    q, _ = r36s_pak.to_palette(im)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    write_hli(dst, q or im)
    return dst


def picture(src, dst):
    sys.path.insert(0, HERE)
    import r36s_game
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    r36s_game.picture(src, dst)


def wav(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-ac', '1', '-ar', '22050', '-sample_fmt', 's16', dst],
                   check=True)


def build(game):
    up = os.path.join(game, 'up', 'solo')
    if not os.path.exists(os.path.join(ARENA, 'index.html')):
        return 0
    cuts, jobs = {}, []
    with tempfile.TemporaryDirectory() as tmp:
        for i, (path, cols, rows) in enumerate(sheets()):
            im = np.ascontiguousarray(np.array(Image.open(os.path.join(ARENA, path)).convert('RGBA')))
            raw = os.path.join(tmp, f'{i}.rgba')
            with open(raw, 'wb') as fh:
                fh.write(im.shape[1].to_bytes(4, 'little') + im.shape[0].to_bytes(4, 'little') + im.tobytes())
            jobs.append(dict(path=path, **{'in': raw, 'cols': cols, 'rows': rows, 'out': os.path.join(tmp, f'{i}')}))
        js = os.path.join(tmp, 'jobs.json')
        json.dump([{k: j[k] for k in ('in', 'cols', 'rows', 'out')} for j in jobs], open(js, 'w'))
        subprocess.run(['node', os.path.join(HERE, 'solo_cut.js'), os.path.join(ARENA, 'index.html'), js], check=True)
        work = []
        for j in jobs:
            meta = json.load(open(os.path.join(j['out'], 'frames.json')))
            cuts[j['path']] = meta
            base = os.path.join(up, 'cut', os.path.splitext(j['path'])[0])
            work += [(os.path.join(j['out'], f'{n}.rgba'), os.path.join(base, f'{n}.hli')) for n in range(len(meta))]
        with ProcessPoolExecutor() as pool:
            list(pool.map(frame_hli, work, chunksize=16))
    with open(os.path.join(game, 'js', 'solo-cuts.js'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('// scripts/solo_r36s.py: the arena\'s sheets cut ahead of time (frames at half size), for game/src/solo.js\n'
                 f'globalThis.__SOLO_CUTS = {json.dumps(cuts, separators=(",", ":"))};\nglobalThis.__SOLO_K = {1 / K:g};\n')
    # the HUD pieces and the arenas
    for p in glob.glob(os.path.join(ARENA, 'ui', '*.png')):
        picture(p, os.path.join(up, 'ui', os.path.splitext(os.path.basename(p))[0] + '.hli'))
    man = json.load(open(os.path.join(ARENA, 'ui', 'san', 'san.json'), encoding='utf-8'))
    for a in [a for v in man.values() for a in v]:
        picture(os.path.join(ARENA, a['file']), os.path.join(up, os.path.splitext(a['file'])[0] + '.hli'))
    os.makedirs(os.path.join(up, 'ui', 'san'), exist_ok=True)
    shutil.copy(os.path.join(ARENA, 'ui', 'san', 'san.json'), os.path.join(up, 'ui', 'san', 'san.json'))
    # sounds: the element sets, loops, announcer; the roster's own sets; the battle music
    for p in glob.glob(os.path.join(ARENA, 'sfx', '*.ogg')):
        n = os.path.splitext(os.path.basename(p))[0]
        if n.startswith('chien-dau'):
            wav(p, os.path.join(game, 'nhac', f'solo-{n}.wav'))
        else:
            wav(p, os.path.join(game, 'sfx', 'solo', n + '.wav'))
    for d in roster():
        for k in PET_SOUNDS:
            p = os.path.join(ARENA, 'sfx', 'pet', f'{d}_{k}.ogg')
            if os.path.exists(p):
                wav(p, os.path.join(game, 'sfx', 'solo', 'pet', f'{d}_{k}.wav'))
    return len(cuts)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print(build(os.path.abspath(sys.argv[1])), 'sheets')
