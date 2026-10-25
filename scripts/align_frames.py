"""Measures how far each frame must move so the creature's body stays put when the frame changes.

The sheet was drawn frame by frame, so the stance drifts a few pixels between poses. The legs of
each frame are matched against the frame before it in its animation (flames ignored), sideways
only so the feet stay on the floor, and the
offsets are written to assets/creatures/<element>/<slug>/<stage>/frames.json as
"align": {name: [dx, dy]}.
Usage: python align_frames.py [slug | element | stage ...]
"""
import json, os
import numpy as np
from PIL import Image

import creatures

# chains per layout: every frame is aligned to the one before it; a chain's first frame is fixed
# (or already aligned by an earlier chain). Walk and run frames are not in any chain: their legs differ
# on purpose, so matching legs frame to frame only adds up drift (up to 7 px at 320). They stay where
# slice_frames.py put them, body on the shared centre line (align 0).
CHAINS = {
    'adult': [
        ['idle-0', 'idle-1', 'idle-2', 'idle-3'],
        ['idle-0', 'punch-0', 'punch-1', 'punch-2', 'punch-3'],
        ['idle-0', 'blast-0', 'blast-1', 'blast-3'],
        ['idle-0', 'block', 'hurt'],
        ['idle-0', 'victory', 'flex'],
        ['sleep-0', 'sleep-1', 'yawn'],
        ['eat', 'tired', 'sick'],
    ],
    'young': [
        ['idle-0', 'idle-1', 'idle-2', 'idle-3'],
        ['idle-0', 'flex'],
        ['sleep-0', 'sleep-1', 'yawn'],
        ['eat', 'tired', 'sick'],
    ],
    'four': [
        ['idle-0', 'idle-1', 'idle-2', 'idle-3'],
        ['idle-0', 'attack', 'hurt'],
        ['idle-0', 'victory', 'flex'],
        ['sleep-0', 'sleep-1', 'yawn'],
        ['eat', 'tired', 'sick'],
    ],
    'egg': [
        ['egg-0', 'egg-1', 'egg-2', 'egg-3'],
        ['egg-0', 'crack-0', 'crack-1'],
    ],
}
# the extra sheet (slice_frames.py LAYOUTS['extra']), on any layout that has it; jump, air and spin are off
# the floor and stay on the centre line
EXTRA_CHAINS = [
    ['idle-0', 'eat-look', 'eat-bite', 'eat-chew', 'eat-lick'],
    ['idle-0', 'play-crouch', 'play-land'],
    ['idle-0', 'play-cheer'],
    ['idle-0', 'refuse'], ['idle-0', 'petted'], ['idle-0', 'wave'], ['idle-0', 'angry'],
]
# activity sheets (creatures.ACTS): ball and medicine follow the legs from idle-0; a bath frame is mostly tub,
# so the tub of bath-0 stays where slice_frames.py put it and the others follow it
EXTRA_CHAINS += [['idle-0'] + [f'ball-{i}' for i in range(8)], ['idle-0'] + [f'medicine-{i}' for i in range(8)],
                 [f'bath-{i}' for i in range(8)]]
FIXED = ['idle-0', 'sleep-0', 'eat', 'egg-0', 'bath-0']
RANGE = round(8 * creatures.SIZE)
# poses whose legs are too different to match (lunge, knock-back): keep where the artist put them
KEEP = {'blast-2': [0, 0], 'hurt': [0, 0]}

def body(fr, name):
    a = np.array(Image.open(os.path.join(fr, 'png', name + '.png')))
    rgb = a[..., :3].astype(int)
    flame = (rgb[..., 0] > 220) & (rgb[..., 1] > 150)
    m = (a[..., 3] > 0) & ~flame
    m[:int(m.shape[0] * 0.55)] = False     # legs and feet only: they must stay planted
    return m

def shift(m, dx, dy):
    out = np.zeros_like(m)
    h, w = m.shape
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = m[ys, xs]
    return out

def best(ref, m):
    top = None
    for dy in (0,):                          # feet stay on the floor
        for dx in range(-RANGE, RANGE + 1):
            s = shift(m, dx, dy)
            score = (s & ref).sum() / max(1, (s | ref).sum())
            if top is None or score > top[0] + 1e-9: top = (score, dx, dy)
    return top[1], top[2]

def main(cid, stage):
    fr = creatures.frames_dir(cid, stage)
    if not os.path.exists(os.path.join(creatures.frames_dir(cid, stage), 'frames.json')):
        print(f'{cid}/{stage}: not sliced yet, skipped')
        return
    path = os.path.join(fr, 'frames.json')
    meta = json.load(open(path))
    align = {n: [0, 0] for n in FIXED if n in meta['frames']}
    if meta['layout'] == 'adult':
        align.update(KEEP)
    extra = [c for c in EXTRA_CHAINS if c[1] in meta['frames']]
    for chain in CHAINS[meta['layout']] + extra:
        for prev, cur in zip(chain, chain[1:]):
            if cur in align: continue
            px, py = align[prev]
            ref = shift(body(fr, prev), px, py)
            dx, dy = best(ref, body(fr, cur))
            if abs(dx) >= RANGE:                 # the legs did not match anywhere: leave it be
                print(f'{cid}/{stage}: {cur} has no match near {prev}, kept in place')
                dx, dy = 0, 0
            align[cur] = [dx, dy]
    for n in meta['frames']: align.setdefault(n, [0, 0])
    meta['align'] = align
    json.dump(meta, open(path, 'w'), indent=2)
    print(f'{cid}/{stage}', ' '.join(f'{n}:{align[n][0]}' for n in meta['frames']))

if __name__ == '__main__':
    for cid, stage in creatures.selected():
        main(cid, stage)
