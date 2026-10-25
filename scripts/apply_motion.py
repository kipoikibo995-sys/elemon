"""Sets each creature's own timing for eat / happy from assets/source/tinh-linh/_lam-lai/kieu-an-choi.json.

'motion' words: jump (the template's leap), ground (stays near the floor), float (drifts up slowly);
slow / fast scale every key's ms. Only units with an extra sheet are touched; the other anims in their
anims.json stay as they are. Run after the anims exist (build_assets.py), then build_evo_app.py if needed.
Usage: python apply_motion.py [slug | element | stage ...]
"""
import json, os

import creatures

SPEC = os.path.join(creatures.SOURCE, '_lam-lai', 'kieu-an-choi.json')
# y of play-jump, play-air, play-spin, play-air (the happy keys 1..4) for each kind of play
LIFT = {'jump': None, 'ground': [-3, -5, -4, -2], 'float': [-8, -14, -16, -10]}
PACE = {'slow': 1.3, 'fast': 0.8, 'float': 1.3}


def main(cid, stage):
    spec = json.load(open(SPEC, encoding='utf-8')).get(cid)
    if not spec or not creatures.extra_sheet(cid, stage):
        return
    words = spec['motion'].split()
    path = creatures.anims_path(cid, stage)
    blocks = creatures._anim_blocks(open(path, encoding='utf-8').read())
    tpl = creatures._anim_blocks(open(os.path.join(creatures.ROOT, 'assets', 'anim-templates',
                                                   creatures.LAYOUT[stage] + '.json'), encoding='utf-8').read())
    pace = 1.0
    for w in words:
        pace *= PACE.get(w, 1.0)
    for name in ('eat', 'happy'):
        anim = json.loads('{' + tpl[name] + '}')[name]           # always from the template: rerunning is safe
        for k in anim['keys']:
            k['ms'] = round(k['ms'] * pace / 10) * 10
        lift = next((LIFT[w] for w in words if w in LIFT), None)
        if name == 'happy' and lift:
            for k, y in zip(anim['keys'][1:5], lift):
                k['y'] = y
        keys = ',\n                                     '.join(json.dumps(k) for k in anim['keys'])
        blocks[name] = f'  "{name}": {{"loop": {json.dumps(anim["loop"])}, "keys": [{keys}]}}'
    open(path, 'w', encoding='utf-8').write(creatures._anim_text(blocks))
    print(f'{cid}/{stage}: {spec["motion"]}')


if __name__ == '__main__':
    for cid, stage in creatures.selected():
        main(cid, stage)
