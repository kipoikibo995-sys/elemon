"""Huyền thoại (Lv5, bậc 5) skill effect sheets, drawn from the level-2 sheets.

chieu/<prefix>_<n>_lv5.png and _lv5_mid.png: same grid, frame order and size as the level-1/level-2 sheets (the game cuts
them the same way), but a mythic tier: divine gold-white light, rune circles, a spirit-beast motif. One picture per sheet
like lam_bac2 jobs: the frames on the odd rows, their in-betweens on the even rows.

Usage: python lam_huyen_thoai_chieu.py jobs  -> _ve-lv5/jobs/<prefix>.json (sheets not yet drawn); the driver
                                               lam_bac2_tab.js saves lv2__<prefix>__HT-<n>.png into DOWNLOADS
       python lam_huyen_thoai_chieu.py gom   -> those drawings into _ve-lv5/tai-ve/, split and fitted into chieu/
       python lam_huyen_thoai_chieu.py text  -> _ve-lv5/text-jobs.json: prompts that describe the frames (no attachment)
       python lam_huyen_thoai_chieu.py gom-text            -> lv5__<prefix>__<n>.png in Downloads into chieu/
       python lam_huyen_thoai_chieu.py nhan <png> <prefix> <n>  -> one frames-only drawing into chieu/<..>_<n>_lv5.png
"""
import json, os, re, shutil, sys, tempfile
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from lam_bac2 import (CHIEU, COMBO, DOWNLOADS, ELEMENT, NOTES, ORDER_2, ORDER_3, ROOT, SHEET, TL, grid, row_cuts,
                      soften)
from optimize_sheet import optimize
from creatures import NAMES

OUT = os.path.join(TL, '_ve-lv5')
TAG = 'HT-'

FLAME = {'HO': 'red-orange fire with white-gold cores', 'TH': 'cyan-blue spirit flames with white foam', 'MO': 'green-gold spirit flames with flying petals',
         'KI': 'silver-white plasma flames with gold edges', 'TO': 'amber-gold lava flames with flying rock shards'}

LEGEND = {
    'HO': 'a celestial phoenix-fire motif, white-gold sun flames',
    'TH': 'a celestial sea-dragon motif, glowing white-gold tidal light',
    'MO': 'a sacred world-tree motif, glowing golden leaves and blossoms',
    'KI': 'a heavenly sword motif, radiant gold star blades',
    'TO': 'an ancient mountain-god motif, molten gold runes in stone',
}

PROMPT = """IMPORTANT LAYOUT: exactly {cols} columns x {rows2} rows of equal cells. Create an image. Pixel art game VFX sprite sheet. The attached image is the LEVEL-2 version of a skill effect sheet of {name} ({element}). Redraw it as the LEGENDARY (final mythic tier) version, FRAME FOR FRAME: a grid of {cols} columns x {rows2} rows, same order, every frame shows the same moment as the attached frame in the same cell, facing right, same pixel art style with a dark outline. Canvas {canvas}. Flat solid magenta background #FF00FF everywhere (no gradient, no shadow, no text, no numbers, no grid lines, no borders). Each effect stays inside its own cell with a clear magenta gap on every side and must not touch its neighbours{edge}.
Legendary rules: it must look DIVINE and GODLIKE, clearly a tier above the attached level-2 version, like the final transformation super move of an anime boss. Keep the same timing but make every frame SPECTACULAR and full of motion: MASSIVE THUNDER - huge thick jagged lightning bolts striking down and forking around the effect in every frame (a different bolt shape each frame so it flickers when animated), electric arcs crackling across it; ROARING FLAMES - big swirling tongues of blazing fire and energy flames ({flame}) trailing and licking off every shape, flowing in the direction of motion; plus radiant WHITE-GOLD divine light at the core, a glowing golden RUNE CIRCLE or halo ring behind the big moments, {motif}, bright light rays bursting outward, sharp shockwave rings, swirling energy spirals and strong rim light. Keep the {colours} colours as the base and add radiant gold and a soft prismatic shine so it reads as LEGENDARY. Big bold shapes with thick outlines and flat colour blocks, NOT tiny scattered particles or sparkle noise. The effect can fill more of its cell than level 2 but still tapers off and ENDS inside the cell.
This sheet: {note} {combo}"""


def mould(pre, n):
    return os.path.join(CHIEU, f'{pre}_{n}_lv2.png')


def jobs():
    os.makedirs(os.path.join(OUT, 'jobs'), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, 'jobs')):
        os.remove(os.path.join(OUT, 'jobs', f))
    count = 0
    for pre, notes in NOTES.items():
        colours = ELEMENT[pre[:2]][0]
        steps = []
        for n in ('4', 'aura', '2', '1', '3'):          # ultimate first: the one players notice most
            if n not in notes or not os.path.exists(mould(pre, n)):
                continue
            if all(os.path.exists(os.path.join(CHIEU, f'{pre}_{n}_lv5{m}.png')) for m in ('', '_mid')):
                continue
            cols, nrows = grid(os.path.join(CHIEU, f'{pre}_{n}.png'))
            note = notes[n]
            prompt = ' '.join(PROMPT.format(
                name=NAMES[pre.split('_', 1)[1]], element=colours.split(':')[0], cols=cols, rows2=2 * nrows,
                canvas='portrait 2:3' if nrows == 3 else 'square 1:1',
                edge=' (a beam segment meant to tile may touch the left and right edges of its cell)' if 'tile' in note else '',
                motif=LEGEND[pre[:2]], flame=FLAME[pre[:2]], colours=colours.split(': ')[1],
                note=f'{SHEET[n]} - level 2 was: {note}',
                combo=COMBO.format(third=', row 5 = its row 3' if nrows == 3 else '',
                                   order=ORDER_3 if nrows == 3 else ORDER_2).replace('level-2 frames', 'legendary frames'),
            ).splitlines())
            steps.append(dict(sheet=TAG + n, file=os.path.basename(mould(pre, n)), mid='', prompt=prompt))
        if steps:
            with open(os.path.join(OUT, 'jobs', pre + '.json'), 'w', encoding='utf-8') as f:
                json.dump(dict(prefix=pre, steps=steps), f, ensure_ascii=False)
            count += len(steps)
    print(count, 'sheets in', len(os.listdir(os.path.join(OUT, 'jobs'))), 'jobs')


def fit(src, pre, n, suf):
    """each cell of the drawing fitted into the level-1 cell size (aspect kept), cut edges faded, optimized"""
    cols, nrows = grid(os.path.join(CHIEU, f'{pre}_{n}.png'))
    tw, th = Image.open(os.path.join(CHIEU, f'{pre}_{n}.png')).size
    sw, sh = src.size
    out = Image.new('RGB', (tw, th), (255, 0, 255))
    cw, ch, dw, dh = sw / cols, sh / nrows, tw / cols, th / nrows
    k = min(dw / cw, dh / ch)
    for r in range(nrows):
        for c in range(cols):
            cell = src.crop((round(c * cw), round(r * ch), round((c + 1) * cw), round((r + 1) * ch)))
            cell = cell.resize((max(1, round(cell.width * k)), max(1, round(cell.height * k))), Image.NEAREST)
            out.paste(cell, (round(c * dw + (dw - cell.width) / 2), round(r * dh + (dh - cell.height) / 2)))
    if 'tile' not in NOTES[pre].get(n, ''):
        out = soften(out, cols, nrows)
    dst = os.path.join(CHIEU, f'{pre}_{n}_lv5{suf}.png')
    tmp = os.path.join(tempfile.gettempdir(), f'{pre}_{n}_lv5{suf}_tmp.png')
    out.save(tmp)
    optimize(tmp, dst)
    os.remove(tmp)
    print(dst)


def gom():
    keep = os.path.join(OUT, 'tai-ve')
    os.makedirs(keep, exist_ok=True)
    for f in sorted(os.listdir(DOWNLOADS)):
        m = re.fullmatch(r'lv2__([A-Z]{2}-[A-Z0-9]+_[a-z-]+)__' + TAG + r'([a-z0-9]+)\.png', f)
        if not m:
            continue
        pre, n = m.groups()
        src = os.path.join(keep, f)
        os.replace(os.path.join(DOWNLOADS, f), src)
        im = Image.open(src).convert('RGB')
        rows = 2 * grid(os.path.join(CHIEU, f'{pre}_{n}.png'))[1]
        cuts = row_cuts(im, rows)
        slot = im.height // rows
        for odd, suf in ((0, ''), (1, '_mid')):        # odd rows the frames, even rows their in-betweens
            half = Image.new('RGB', (im.width, slot * rows // 2), (255, 0, 255))
            for k, r in enumerate(range(odd, rows, 2)):
                band = im.crop((0, cuts[r], im.width, cuts[r + 1]))
                if band.height > slot:
                    top = (band.height - slot) // 2
                    band = band.crop((0, top, im.width, top + slot))
                half.paste(band, (0, k * slot + (slot - band.height) // 2))
            fit(half, pre, n, suf)


# ---- text-only mode: the in-app ChatGPT tab cannot attach the level-2 sheet, so each prompt describes the frames
# (_ve-lv5/mo-ta/<prefix>.json, written from the level-2 sheets). Big cut-out shapes; the ultimate's row 3 is the
# lingering field that slows enemies, which the game also drops (smaller) after the other legendary skills.

FIELD = {
    'HO': 'molten lava ground with a ring of low flames around its edge, slow drifting embers and heat haze',
    'TH': 'a swirling whirlpool of deep water with frost crystals at its edge, slow rising bubbles and mist',
    'MO': 'a tangle of thorny vines and roots with glowing pollen drifting slowly and blossoms opening at its edge',
    'KI': 'polished steel ground with gold blades floating and slowly turning around its edge, magnetic sparks drifting',
    'TO': 'cracked quicksand ground with amber crystals poking up at its edge, slow drifting dust and pebbles',
}

TEXT = """Create an image. IMPORTANT LAYOUT: exactly 4 columns x {rows} rows of equal cells, {canvas} canvas. PIXEL ART game VFX sprite sheet (crisp visible pixels, limited palette, dark 1-2px outline, like a 16-bit console game), {n} animation frames read left to right, top to bottom: the LEGENDARY {role} of {name}, a {element} creature. Flat solid magenta background #FF00FF everywhere. CUTOUT RULE: every frame is ONE isolated effect shape floating on magenta, with magenta clearly visible all around it (about 6% gap to each cell border){edge}; NEVER fill a cell with a rectangle of fire, smoke, water, sky or ground; no background scenery, no creature body, no text, no numbers, no grid lines, no borders. Make each effect as BIG as possible inside that gap: a huge, heavy, screen-shaking legendary move.
Frames: {frames}
LEGENDARY look: divine and spectacular like an anime boss final super move: thick jagged golden-white lightning bolts forking around the effect in every frame (a different bolt shape each frame so it flickers), roaring {flame} trailing in the direction of motion, {motif}, shockwave rings and light rays on the big moments. Colours {colours} plus radiant gold."""

ULT_ROW3 = ("Row 3 (frames 9-12) REPLACES the description above for that row: a LINGERING SLOW FIELD, seamless loop, 3/4 top "
            "view: a very wide flat oval almost as wide as the cell, {field}, engraved with a glowing golden rune circle "
            "and glyph ring, small golden lightning sparks crackling on it, reading clearly as a zone that SLOWS enemies "
            "standing in it; the runes pulse and the particles drift between frames.")


def text_jobs():
    rows = []
    for pre, notes in NOTES.items():
        f = os.path.join(OUT, 'mo-ta', pre + '.json')
        if not os.path.exists(f):
            continue
        desc = json.load(open(f, encoding='utf-8'))
        e = pre[:2]
        colours = ELEMENT[e][0]
        for n in ('4', 'aura', '2', '1', '3'):
            if n not in desc or os.path.exists(os.path.join(CHIEU, f'{pre}_{n}_lv5.png')):
                continue
            cols, nrows = grid(os.path.join(CHIEU, f'{pre}_{n}.png'))
            frames = desc[n] + (' ' + ULT_ROW3.format(field=FIELD[e]) if nrows == 3 else '')
            tile = 'tile' in notes.get(n, '') or 'tiles' in desc[n]
            rows.append(dict(id=f'{pre}__{n}', prompt=' '.join(TEXT.format(
                rows=nrows, canvas='landscape 4:3' if nrows == 3 else 'wide landscape 2:1', n=4 * nrows,
                role={'1': 'basic attack', '2': 'main skill', '3': 'utility skill', '4': 'ultimate skill',
                      'aura': 'power-up aura (row 1 a ring drawn behind the creature with an empty middle, row 2 its spirit beast shown above its head)'}[n],
                name=NAMES[pre.split('_', 1)[1]], element=colours.split(':')[0],
                edge=' (except a horizontal beam segment meant to tile, which touches the left and right cell edges)' if tile else '',
                frames=frames, flame=FLAME[e], motif=LEGEND[e], colours=colours.split(': ')[1]).splitlines())))
    json.dump(rows, open(os.path.join(OUT, 'text-jobs.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(len(rows), 'text jobs')


def nhan(path, pre, n):
    """one drawn sheet (frames only, no in-betweens) -> chieu/<pre>_<n>_lv5.png at the level-1 sheet's size"""
    fit(Image.open(path).convert('RGB'), pre, n, '')


def gom_text():
    """every lv5__<prefix>__<n>.png the in-app ChatGPT driver (lam_lv5_tab.js) saved to Downloads (as lv5__goi_<k>.zip bundles) -> chieu/"""
    dl = os.path.join(os.path.expanduser('~'), 'Downloads')
    keep = os.path.join(OUT, 'tai-ve')
    os.makedirs(keep, exist_ok=True)
    import zipfile
    for f in sorted(os.listdir(dl)):           # the driver bundles 10 drawings per download: one Save click each
        if re.fullmatch(r'lv5__goi_\d+\.zip', f):
            with zipfile.ZipFile(os.path.join(dl, f)) as z:
                z.extractall(dl)
            os.remove(os.path.join(dl, f))
    for f in sorted(os.listdir(dl)):
        m = re.fullmatch(r'lv5__([A-Z]{2}-[A-Z0-9]+_[a-z-]+)__([a-z0-9]+)\.png', f)
        if m:
            dst = os.path.join(keep, f'{m.group(1)}_{m.group(2)}.png')
            shutil.move(os.path.join(dl, f), dst)
            nhan(dst, *m.groups())

if __name__ == '__main__':
    if sys.argv[1:2] == ['nhan']:
        nhan(*sys.argv[2:5])
    else:
        {'jobs': jobs, 'gom': gom, 'text': text_jobs, 'gom-text': gom_text}.get(sys.argv[1:2] and sys.argv[1], lambda: print(__doc__))()
