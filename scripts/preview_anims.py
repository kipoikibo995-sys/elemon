"""Builds preview/<element>/<slug>/<stage>/<anim>.gif and .../showreel.gif at 30 fps.

Motion follows assets/creatures/<element>/<slug>/<stage>/anims.json (the data the game will play): between frame
changes the creature slides, breathes (upper body lifts a pixel or two), shakes and flashes, which hides the
small differences between the hand-drawn frames.
Usage: python preview_anims.py [slug | element | stage ...]
"""
import json, math, os, random
from PIL import Image, ImageDraw, ImageFont

import creatures

STEP = 33
LABELS = {'idle': 'Đứng thở', 'punch': 'Đấm', 'blast': 'Chiêu lửa', 'hit': 'Trúng đòn', 'faint': 'Gục ngã',
          'victory': 'Thắng', 'eat': 'Ăn', 'happy': 'Vui nhảy', 'tired': 'Mệt', 'sick': 'Ốm',
          'sleep': 'Ngủ', 'wake': 'Thức dậy', 'walk': 'Đi', 'shake': 'Lắc', 'hatch': 'Nở',
          'run': 'Chạy', 'attack': 'Đòn hệ'}
REPEAT = {'idle': 2, 'eat': 2, 'happy': 3, 'tired': 1, 'sick': 3, 'sleep': 2, 'walk': 3, 'shake': 2}


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def breathe(img, lift, split):
    """Moves the rows above `split` up by `lift` px (down when negative); the waist row fills the gap."""
    if lift == 0:
        return img
    w, h = img.size
    out = Image.new('RGBA', (w, h))
    out.alpha_composite(img.crop((0, split, w, h)), (0, split))
    if lift > 0:
        waist = img.crop((0, split - 1, w, split)).resize((w, lift + 1))
        out.alpha_composite(waist, (0, split - lift - 1))
    out.alpha_composite(img.crop((0, max(0, lift), w, split)), (0, max(0, -lift)))
    return out


def flash(img, amount):
    mixed = Image.blend(img, Image.new('RGBA', img.size, (255, 255, 255, 255)), amount)
    mixed.putalpha(img.getchannel('A'))
    return mixed


def samples(anim):
    """(frame, x, y, br, shake, flash) every STEP ms through one play of the animation."""
    prev = dict(x=0.0, y=0.0, br=0.0)
    out = []
    for key in anim['keys']:
        goal = dict(x=float(key.get('x', prev['x'])), y=float(key.get('y', prev['y'])),
                    br=float(key.get('br', 0)))
        steps = max(1, round(key['ms'] / STEP))
        for i in range(steps):
            t = ease((i + 1) / steps)
            v = {k: prev[k] + (goal[k] - prev[k]) * t for k in goal}
            out.append((key['f'], v['x'], v['y'], v['br'], key.get('shake', 0),
                        key.get('flash', 0) if i == 0 else 0))
        prev = goal
    return out


def main(cid, stage):
    fr, out = creatures.frames_dir(cid, stage), creatures.preview_dir(cid, stage)
    if not os.path.exists(os.path.join(creatures.frames_dir(cid, stage), 'frames.json')):
        print(f'{cid}/{stage}: not sliced yet, skipped')
        return
    title = f"{creatures.CREATURES[cid]['name']} ({creatures.STAGE_NAMES[stage]})"
    meta = json.load(open(os.path.join(fr, 'frames.json')))
    anims = {k: v for k, v in json.load(open(creatures.anims_path(cid, stage), encoding='utf-8')).items()
             if not k.startswith('_')}
    ax, ay = meta['anchor']
    split = ay - round(meta['canvas'][1] * 0.4)   # the breathing waist line
    frames = {n: Image.open(os.path.join(fr, 'png', n + '.png')).convert('RGBA') for n in meta['frames']}
    font = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 16)
    os.makedirs(out, exist_ok=True)
    rnd = random.Random(7)

    def screen(f, x, y, br, shake, fl, label):
        s = Image.new('RGBA', (320, 240), (52, 36, 40, 255))
        d = ImageDraw.Draw(s)
        d.rectangle([0, 176, 320, 240], fill=(92, 58, 42))
        sw = int(meta['canvas'][0] * 0.26 - max(0.0, -y) * 0.6)
        cx = 160 + round(x)
        d.ellipse([cx - sw, 176 - 5, cx + sw, 176 + 5], fill=(60, 36, 28))
        dx, dy = meta['align'][f]
        img = breathe(frames[f], round(br), split)
        if fl:
            img = flash(img, 0.75)
        jx = rnd.randint(-shake, shake) if shake else 0
        jy = rnd.randint(-shake, shake) // 2 if shake else 0
        s.alpha_composite(img, (160 - ax + dx + round(x) + jx, 176 - ay + dy + round(y) + jy))
        s = s.resize((640, 480), Image.NEAREST)
        ImageDraw.Draw(s).text((14, 10), f'{title} · {label}', fill=(255, 230, 160), font=font)
        return s.convert('RGB')

    reel = []
    for name, anim in anims.items():
        shots = [screen(*smp, LABELS.get(name, name)) for smp in samples(anim)]
        if not anim['loop']:
            shots += [shots[-1]] * 12
        shots[0].save(os.path.join(out, name + '.gif'), save_all=True, append_images=shots[1:],
                      duration=STEP, loop=0)
        reel += shots * REPEAT.get(name, 1)
    reel[0].save(os.path.join(out, 'showreel.gif'), save_all=True, append_images=reel[1:],
                 duration=STEP, loop=0)
    print(f'{cid}/{stage}: {len(anims)} animations, {len(reel)} showreel frames')


if __name__ == '__main__':
    for cid, stage in creatures.selected():
        main(cid, stage)
