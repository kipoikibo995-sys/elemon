"""Level-2 (bậc 2) skill effect sheets: the prompts to draw them, and taking a drawn sheet back in.

Thiếu niên (Lv3) and up fight with the level-2 effects: chieu/<..>_<n>_lv2.png, same grid and frame order as the
level-1 sheet chieu/<..>_<n>.png (the game cuts both the same way), but bigger, wider and with more going on.
Each sheet is drawn by attaching its level-1 sheet as the mould and pasting its prompt (one chat per creature).

Usage: python lam_bac2.py gom                             -> every lv2__*.png in Chrome's download folder taken in and
                                                             copied to the arena page (preview/dau-truong/img/<slug>/)
       python lam_bac2.py prompts                         -> assets/source/tinh-linh/_ve-lv2/LOI-NHAC-BAC2.md + prompts.json
       python lam_bac2.py nhan <downloaded.png> <HO-T2_hoa-quy> <1|2|3|4|aura|..>[_mid]
           -> chieu/<..>_<n>_lv2[_mid].png: each cell of the drawing fitted into the level-1 cell (aspect kept), then optimized
"""
import json, os, re, shutil, sys, tempfile
import numpy as np
from PIL import Image

from optimize_sheet import optimize
from slice_frames import magenta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = os.path.join(ROOT, 'assets', 'source', 'tinh-linh')
CHIEU = os.path.join(TL, 'chieu')
OUT = os.path.join(TL, '_ve-lv2')

# level-2 already drawn (24/10/2026)
DONE = {'HO-T2_hoa-quy'}

ELEMENT = {
    'HO': ('fire: red, orange, yellow', 'white-hot cores and golden flame tips', 'golden-white lightning with a red glow'),
    'TH': ('water: blue, cyan, white foam', 'gold rims and white shine, small golden dragon-scale motifs',
           'white and electric cyan lightning'),
    'MO': ('wood: green, lime, pink blossoms', 'golden thorns, golden flowers and a golden glow ring',
           'golden and lime-green lightning'),
    'KI': ('metal: silver, white, steel blue', 'bright gold edges and big four-point star flares',
           'white and gold lightning'),
    'TO': ('earth: brown, ochre, amber', 'glowing amber-gold cracks and gold-veined rocks', 'amber-gold lightning'),
}

COMMON = """Create an image. Pixel art game VFX sprite sheet. The attached image is the LEVEL-1 version of a skill effect sheet of {name} ({element}). Redraw it as the LEVEL-2 (upgraded) version, FRAME FOR FRAME: exactly the same grid of {cols} columns x {rows} rows, the same order, every frame shows the same moment as the attached frame in the same cell, facing right, same pixel art style with a dark outline. Canvas {canvas}. Flat solid magenta background #FF00FF everywhere (no gradient, no shadow, no text, no numbers, no grid lines). Each effect stays inside its own cell and must not touch its neighbours{edge}.
Level-2 rules: it must look COOL, POWERFUL and EPIC, like a boss-tier anime super move, not just the level-1 drawn bigger. Each effect is bigger than level 1 and covers a WIDER area, but it must stay fully inside its own cell with a clear magenta gap on every side (about one tenth of the cell): flames, trails, lightning and debris taper off and END inside the cell, never cut by the cell border and never reaching the neighbouring frame. Add crackling LIGHTNING BOLTS: THICK bold jagged electric arcs (thick enough to read even when the sprite is shown small) bursting out of and wrapping around every effect ({bolt}), plus a raging energy aura, sharp shockwave rings, radial speed lines and strong white rim light with high contrast. Bigger impacts with ground cracks and debris thrown up. Draw it as big bold shapes with thick outlines and flat colour blocks, NOT tiny scattered particles or sparkle noise. Keep the {colours} colours and add {accent} so it clearly reads as a much stronger tier.
This sheet: {note}"""

SHEET = {'1': 'skill 1 (basic attack)', '2': 'skill 2 (main skill)', '3': 'skill 3 (utility)',
         '4': 'skill 4 (ultimate)', 'aura': 'aura: row 1 the power-up ring drawn BEHIND the creature, row 2 the spirit beast shown above its head'}

# per sheet: what level 2 adds (the attached level-1 sheet already shows what each frame is)
NOTES = {
    'HO-T1_hoa-ho': {
        '1': 'Fire Claw: three huge golden-white claw arcs, hit burst twice as big.',
        '2': 'Tiger Roar fireball: bigger fire tiger head with a golden flame mane, explodes into a double fire ring.',
        '3': 'Fire Shield: taller fire ring with golden tiger-stripe flames.',
        '4': 'Heavenly Fire Tiger King: bigger and more falling fire tigers, wider warning ring with golden runes, giant final blast with a gold flash.',
        'aura': 'bigger flame ring; the spirit tiger gets golden horn-like flames and blazing eyes.',
        'vo': 'Tiger Pounce: bigger fire tiger with golden flames, wider landing explosion and crater; row 2 burning pool wider with tall golden flames.',
        'no': 'Fire Rage: row 1 taller white-gold flame ring around the body; row 2 the burn flame on the victim bigger with a golden tip.',
    },
    'MO-T1_moc-hung': {
        '1': 'Bear Slap: bigger leaf claw marks with golden thorns and a bigger bear paw print.',
        '2': 'Binding Vine: row 1 the flying vine head bigger with golden thorns; row 2 the vine coil around the target thicker with a golden flower.',
        '3': 'Healing Roots: wider root ring with golden flowers, taller light column, bigger plus signs.',
        '4': 'Ancient Forest: wider warning ring, bigger roots and a huge golden tree with a carved bear face, bigger leaf wave.',
        'aura': 'bigger leaf ring; spirit forest bear with golden branch antlers.',
    },
    'TH-T3_thuy-long': {
        '1': 'Water Claw: bigger dragon-claw water slash with a gold edge, bigger splash.',
        '2': 'Dragon Water Arrow: row 1 the beam segment thicker with two small water dragons coiling round it (it must still tile left-right); row 2 bigger mouth burst and splash.',
        '3': 'Water Curtain: taller curtain with dragon scales and golden dragon heads, bigger impact and collapse.',
        '4': 'Dragon Waterspout: taller spout with storm clouds, golden lightning and a water dragon head, bigger burst and rain.',
        'aura': 'bigger water ring; spirit water dragon with golden horns.',
    },
    'HO-T2_hoa-quy': {
        '1': 'Lava ball: bigger lava ball with a golden core and a short flame tail, bigger splash explosion.',
        '2': 'Shell Roll: wider fire trail with golden flames, bigger impact burst with a shock ring.',
        '3': 'Spinning fire ring: double ring (outer red, inner gold), much wider.',
        '4': 'Volcano Turtle slam: wider shadow and cracks glowing gold, taller fire columns throwing lava rocks, bigger lingering embers.',
        'aura': 'bigger lava flame ring; spirit turtle with a golden volcano shell.',
    },
    'HO-T3_hoa-ho-cao': {
        '1': 'Fire claw: bigger claw marks shaped like fox tails with golden tips.',
        '2': 'Fire heart kiss: bigger fire heart with a golden outline, bigger burst, bigger heart halo.',
        '3': 'Fox fire: bigger vortex and more fox-fire orbs (five instead of three).',
        '4': 'Nine-Tailed Fox: bigger fox with golden tail tips, wider and brighter lava pools.',
        'aura': 'bigger fox-fire ring; spirit fox with nine golden-tipped tails.',
    },
    'HO-N1_viem-long': {
        '1': 'Claw: bigger golden claw slash; row 2 flame stream segment thicker with a white-hot core (it must still tile left-right).',
        '2': 'Wing wind under the flying dragon wider; fire hit burst bigger.',
        '3': 'Fire zone halo: wider ring with golden runes on the rim, taller flames.',
        '4': 'Dragon-head fireball bigger with golden horns; bigger explosion; flames on the feet bigger.',
        'aura': 'bigger flame ring; spirit dragon with golden horns and wings.',
    },
    'HO-N2_dung-nham-ve': {
        '1': 'Ram streak bigger with golden lava, bigger hit burst.',
        '2': 'Floor fire trail taller (still tiles), rolling dust ring wider with gold sparks.',
        '3': 'Body flames bigger with white-gold cores, bigger flare and spark hits.',
        '4': 'Bigger explosion with a gold shock ring; mini lava golems with glowing gold cores; their explosions bigger.',
        'aura': 'bigger lava ring; spirit lava giant with golden glowing cracks.',
    },
    'HO-N3_hoa-linh': {
        '1': 'Fireball bigger with a golden core, bigger explosion.',
        '2': 'Fire seal: bigger golden rune seal, bigger mark above the head, bigger seal burst.',
        '3': 'Orbiting fireballs: five bigger fireballs instead of three.',
        '4': 'Ground cracks wider and glowing gold, fire columns taller with white-gold cores.',
        'aura': 'bigger fire ring; spirit fire wisp with a golden crown flame.',
    },
    'KI-N1_tinh-kim-hiep': {
        '1': 'Punch: bigger shock cone; charge orb bigger with gold lightning.',
        '2': 'Lightning beam segment thicker with gold lightning around a white core (must still tile left-right); bigger palm burst and hits.',
        '3': 'Lightning cage bigger with gold bars; bigger blast.',
        '4': 'Charge orb bigger; crescent waves bigger with gold edges; bigger hits.',
        'aura': 'bigger lightning ring; spirit crystal knight with golden lightning.',
    },
    'KI-N2_kim-thach-nhan': {
        '1': 'Crystal punch: bigger crystal shards and a gold star flare.',
        '2': 'Crystal spike: wider warning glyph with gold, a CLUSTER of big spikes instead of one.',
        '3': 'Crystal pillar taller with gold veins; more and bigger flying shards.',
        '4': 'Crystal prison bigger with gold edges; spike wave wider; bigger shatter.',
        'aura': 'bigger crystal ring; spirit crystal golem with golden facets.',
    },
    'KI-N3_liem-dao': {
        '1': 'Scythe slash: wider crescent slash with a gold edge.',
        '2': 'Boomerang scythe bigger with a golden blade and a longer trail.',
        '3': 'Shadow step: bigger X slash in silver and gold.',
        '4': 'Crescent moon blade huge, spanning the cell, gold edge; warning line wider.',
        'aura': 'bigger blade ring; spirit mantis with golden scythes.',
    },
    'KI-T1_kim-te': {
        '1': 'Horn ram: bigger silver-gold horn streak and hit flare.',
        '2': 'Needle burst: more and bigger steel needles with gold tips.',
        '3': 'Leap slam: wider landing shock ring with gold cracks.',
        '4': 'Rune circle wider with gold runes, denser needle rain, the giant steel horn bigger with gold bands.',
        'aura': 'bigger steel ring; spirit rhino with a golden horn.',
    },
    'KI-T2_kim-giap': {
        '1': 'Steel claw: bigger claw marks with gold edges.',
        '2': 'Scale shot: five bigger scales instead of three, gold edges.',
        '3': 'Curl guard: bigger steel dome with gold plates, bigger reflect flare.',
        '4': 'Giant steel ball bigger with gold bands, wider rolling shockwave.',
        'aura': 'bigger steel ring; spirit pangolin with golden armour.',
    },
    'KI-T3_kim-ung': {
        '1': 'Steel feather bigger with a gold edge and a longer trail.',
        '2': 'Wind cone wider and longer with gold wind streaks.',
        '3': 'Dive: wider impact ring with silver and gold feathers.',
        '4': 'Giant steel eagle bigger with golden wings; wider lock-on ring; bigger impact.',
        'aura': 'bigger wind ring; spirit eagle with golden wings.',
    },
    'MO-T2_moc-loc': {
        '1': 'Antler strike bigger; seeds and flowers bigger with golden petals.',
        '2': 'Healing flower carpet wider with golden flowers.',
        '3': 'Golden light pillar taller and wider, bigger flower ring.',
        '4': 'Divine deer bigger with golden glowing antlers; wider summon and flower rings.',
        'aura': 'bigger leaf ring; spirit deer with golden antlers.',
    },
    'MO-T3_moc-duong': {
        '1': 'Leaf blade slash wider with golden leaves.',
        '2': 'Dash trail longer with big golden leaves.',
        '3': 'Camouflage leaf ring bigger; sneak slash bigger with gold.',
        '4': 'Leaf storm wider; the big slashes huge with gold edges.',
        'aura': 'bigger leaf ring; spirit mantis-leaf with golden blades.',
    },
    'MO-N1_thu-nhan': {
        '1': 'Wood chips hit bigger; crawling root bigger with golden thorns.',
        '2': 'Roots erupt bigger with golden thorns; wood wave wider.',
        '3': 'Root ring wider; thorn reflect bigger with gold.',
        '4': 'Cracks wider, giant wooden fist bigger with gold bands, wood spike row taller.',
        'aura': 'bigger root ring; spirit ancient tree with a golden face.',
    },
    'MO-N2_reu-linh': {
        '1': 'Moss mushroom bigger with a golden cap rim; spores and moss blobs bigger.',
        '2': 'Moss smash bigger; moss swamp wider with golden flowers.',
        '3': 'Spore ring and summon ring wider with gold.',
        '4': 'Giant moss monster bigger with golden glowing eyes and golden mushrooms on its back; wider warning ring and slam wave.',
        'aura': 'bigger spore ring; spirit moss beast with golden eyes.',
    },
    'MO-N3_diep-linh': {
        '1': 'Leaf dart bigger with gold; leaf trap bigger.',
        '2': 'Wind gust wider; whirl taller with golden leaves.',
        '3': 'Leaf rain wider; leaf carpet bigger with golden flowers.',
        '4': 'Leaf tornado taller and wider with golden petals.',
        'aura': 'bigger leaf ring; spirit leaf fairy with golden wings.',
    },
    'MO-X_moc-tru': {
        '1': 'Ram hit bigger; dust trail longer with golden thorns.',
        '2': 'Wall crash bigger; roar ring wider.',
        '3': 'Red rage steam taller with gold veins.',
        '4': 'Plough trench wider, dust blast bigger, red boar spirit bigger with golden tusks.',
        'aura': 'bigger rage ring; spirit boar with golden tusks.',
    },
    'TH-N1_thuy-chien': {
        '1': 'Water slashes wider with gold edges; sword wave bigger.',
        '2': 'Surf wave bigger and taller with white foam and gold rim.',
        '3': 'Water shield bigger with gold rim, bigger burst.',
        '4': 'Six water swords bigger with golden hilts, water column taller and wider.',
        'aura': 'bigger water ring; spirit water warrior with golden armour.',
    },
    'TH-N2_bao-thuy': {
        '1': 'Bubble bigger with a gold shine, bigger pop.',
        '2': 'Trapping bubble bigger with a golden rim.',
        '3': 'Rolling puff bigger with a wider splash.',
        '4': 'Bubble rain denser with bigger bubbles; giant bubble bigger; bigger final burst with gold.',
        'aura': 'bigger bubble ring; spirit pufferfish with golden spikes.',
    },
    'TH-N3_thuy-giao': {
        '1': 'Water arrow bigger with a gold tip.',
        '2': 'Vortex wider with a gold rim.',
        '3': 'Mist cloud bigger and denser.',
        '4': 'Water dragon bigger with golden horns; water column taller and wider.',
        'aura': 'bigger water ring; spirit sea serpent with golden horns.',
    },
    'TH-T1_thuy-sa': {
        '1': 'Bite: bigger jaws splash with a gold shine.',
        '2': 'Dive: bigger fin and wake; bigger emerge splash.',
        '3': 'Whirlpool wider with a gold rim.',
        '4': 'Giant shark bigger with golden fins; bigger shadow and splash.',
        'aura': 'bigger water ring; spirit shark with golden fins.',
    },
    'TH-T2_thuy-giai': {
        '1': 'Claw pinch: bigger claw splash with a gold edge.',
        '2': 'Shell spikes bigger with gold tips.',
        '3': 'Shell guard bigger; water jet stronger and longer.',
        '4': 'Giant claw bigger with golden edges; bigger smash splash.',
        'aura': 'bigger water ring; spirit crab with golden claws.',
    },
    'TO-T1_tho-nguu': {
        '1': 'Ram: bigger rock burst.',
        '2': 'Rock gather ring wider; horn charge bigger with amber-gold glow.',
        '3': 'Rock armour ring bigger with gold veins; bigger shatter.',
        '4': 'Ground cracks wider glowing gold; rock spikes taller and more.',
        'aura': 'bigger rock ring; spirit bull with golden horns.',
    },
    'TO-T2_tho-tuong': {
        '1': 'Club swing wider with a bigger rock burst.',
        '2': 'Mud spray wider; mud puddle bigger.',
        '3': 'Stomp ring wider with gold cracks.',
        '4': 'War mammoth bigger with golden tusk armour; bigger dust wave.',
        'aura': 'bigger dust ring; spirit mammoth with golden tusks.',
    },
    'TO-T3_tho-tich': {
        '1': 'Tail whip wider with a bigger dust burst.',
        '2': 'Bouncing stone bigger with gold veins.',
        '3': 'Shed-skin decoy and puff bigger.',
        '4': 'Meteors bigger, flaming amber-gold; giant meteor huge; wider warning rings.',
        'aura': 'bigger sand ring; spirit lizard with a golden crest.',
    },
    'TO-N1_thach-nhan': {
        '1': 'Rock punch: bigger rock burst.',
        '2': 'Rolling boulder bigger with gold veins.',
        '3': 'Orbiting stones bigger with gold veins.',
        '4': 'Stone pillar rings taller and wider with gold cracks.',
        'aura': 'bigger rock ring; spirit stone golem with golden cracks.',
    },
    'TO-N2_thanh-tri': {
        '1': 'Shield bash bigger with a shock ring.',
        '2': 'Stone wall taller and wider with gold trims.',
        '3': 'Turret bigger with gold trims; bigger stone shots.',
        '4': 'Fortress walls taller with gold trims; bigger catapult stones and impacts.',
        'aura': 'bigger stone ring; spirit fortress with golden banners.',
    },
    'TO-N3_tho-long': {
        '1': 'Sand spray wider and longer.',
        '2': 'Ground spike row longer with taller spikes and gold veins.',
        '3': 'Fissure wider glowing gold.',
        '4': 'Earth dragon bigger with golden horns; falling rocks bigger; wider warning rings.',
        'aura': 'bigger sand ring; spirit earth dragon with golden horns.',
    },
}
# the level-1 sheets these are drawn from that the game no longer uses are left out (HO-N1_viem-long_lua)


def grid(path):
    """(cols, rows) of a level-1 sheet: 4x3 for the ultimates (about 4:3), 4x2 otherwise"""
    w, h = Image.open(path).size
    return (4, 3) if w / h < 1.6 else (4, 2)


def prompts():
    rows = []
    for pre, notes in NOTES.items():
        if pre in DONE:
            continue
        slug = pre.split('_', 1)[1]
        from creatures import NAMES
        colours, accent, bolt = ELEMENT[pre[:2]]
        for n, note in notes.items():
            src = os.path.join(CHIEU, f'{pre}_{n}.png')
            cols, nrows = grid(src)
            text = COMMON.format(name=NAMES[slug], element=colours.split(':')[0], cols=cols, rows=nrows,
                                 canvas='landscape 4:3' if nrows == 3 else 'wide landscape 2:1',
                                 edge=' (a beam segment meant to tile may touch the left and right edges of its cell)'
                                 if 'tile' in note else '', colours=colours.split(": ")[1], accent=accent, bolt=bolt,
                                 note=SHEET.get(n, n) + ' - ' + note)
            rows.append(dict(prefix=pre, sheet=n, name=NAMES[slug], mould=os.path.relpath(src, ROOT).replace('\\', '/'),
                             out=f'assets/source/tinh-linh/chieu/{pre}_{n}_lv2.png', prompt=text))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'prompts.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    md = ['# Hiệu ứng chiêu bậc 2 — lời nhắc vẽ', '',
          'Thiếu niên (Lv3) trở lên dùng hiệu ứng bậc 2. Mỗi con một cuộc trò chuyện ChatGPT (hoặc arena.ai): lần lượt đính kèm',
          'sheet bậc 1 (cột "Khuôn") rồi dán lời nhắc của sheet đó. Tải về rồi chạy',
          '`python scripts/lam_bac2.py nhan <ảnh tải về> <tiền tố> <sheet>` để ra `chieu/<..>_<sheet>_lv2.png`.', '',
          'Tạo lại file này: `python scripts/lam_bac2.py prompts` (nội dung từng chiêu sửa ở NOTES trong script).', '']
    last = None
    for r in rows:
        if r['prefix'] != last:
            md += ['', f"## {r['name']} — `{r['prefix']}`", '']
            last = r['prefix']
        md += [f"- [ ] **{r['sheet']}**: khuôn `{r['mould']}`", '', '```', r['prompt'], '```', '']
    with open(os.path.join(OUT, 'LOI-NHAC-BAC2.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(len(rows), 'prompts ->', OUT)


# 8x8 ordered-dither thresholds: the fade at a cut edge breaks up into pixels instead of a straight line
BAYER = np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38],
                  [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
                  [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]) / 64


def soften(img, cols, nrows, band=0.22):
    """A drawn effect that runs into the next cell gets cut there in a straight line. Where a cell's art touches one of
    its sides, thin it out with ordered dither along a rounded (elliptic) front instead: gone at the side, untouched
    `band` inside, the far sides of the ellipse pushed out so they cost nothing. The cut then reads as the effect
    fading out in a curve, and the cells no longer touch."""
    rgb = np.array(img)
    bg = magenta(rgb.astype(np.int32))
    h, w = bg.shape
    yy, xx = np.mgrid[0:h, 0:w]
    thr = BAYER[yy % 8, xx % 8]
    drop = np.zeros_like(bg)
    for r in range(nrows):
        for c in range(cols):
            x0, x1, y0, y1 = round(c * w / cols), round((c + 1) * w / cols), round(r * h / nrows), round((r + 1) * h / nrows)
            cell = ~bg[y0:y1, x0:x1]
            left, right, top, bottom = cell[:, :2].any(), cell[:, -2:].any(), cell[:2].any(), cell[-2:].any()
            if not (left or right or top or bottom):
                continue
            cx, cy, rx, ry = (x0 + x1 - 1) / 2, (y0 + y1 - 1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
            dx, dy = xx[y0:y1, x0:x1] - cx, yy[y0:y1, x0:x1] - cy
            # a side with art on it is the ellipse's edge; a clear side lies well outside it
            ex = dx / (rx * np.where(dx < 0, 1 if left else 1.6, 1 if right else 1.6))
            ey = dy / (ry * np.where(dy < 0, 1 if top else 1.6, 1 if bottom else 1.6))
            dist = (1 - np.hypot(ex, ey)) / band          # <= 0 outside the ellipse, >= 1 safely inside
            drop[y0:y1, x0:x1] = cell & (thr[y0:y1, x0:x1] >= dist)
    rgb[drop] = (255, 0, 255)
    return Image.fromarray(rgb)


MID = """IN-BETWEEN FRAMES for smoother animation: take the level-2 sheet you just generated ({cols} columns x {rows} rows) and draw a NEW sheet with exactly the same grid, same canvas, same pixel art style, colours, lightning style and SAME SIZE of the effect, where EACH cell is the in-between moment exactly HALFWAY between the frame in that same cell and the NEXT frame. {order} Every in-between must be a NEW drawing whose shapes are halfway in size, position and lightning shape between the two frames, NOT a copy of either. Keep the effect in the same place in its cell. Flat solid magenta #FF00FF background, no text, no grid lines, each effect fully inside its cell with a clear magenta gap on every side, nothing cut by the cell border."""
ORDER_2 = ("Row 1 loops: cells 1-3 = halfway from frame n to n+1, cell 4 = halfway from frame 4 back to frame 1. Row 2 plays "
           "once: cells 5-7 = halfway from frame n to n+1, cell 8 = frame 8 fading out a bit further.")
ORDER_3 = ("The 12 frames are ONE sequence read left to right, top to bottom: cell n = halfway from frame n to frame n+1 "
           "(cell 4 -> 5, cell 8 -> 9), cell 12 = frame 12 fading out a bit further.")


COMBO = ("LAYOUT OF THIS ONE IMAGE: rows alternate. Odd rows (1, 3, 5...) are the level-2 frames: row 1 = row 1 of the attached "
         "sheet, row 3 = its row 2{third}, frame for frame, same order. Each EVEN row, right under a frame row, holds the IN-BETWEEN "
         "frames for smoother animation: the cell under a frame is the moment exactly HALFWAY between that frame and the NEXT "
         "frame, a new drawing halfway in size, position and lightning shape, not a copy. {order} All cells the same size, "
         "every effect fully inside its own cell with a magenta gap, same place in its cell as the frame above it.")


def arena_code(pre, sheet):
    """short tag an arena.ai prompt starts with: arena names the download after the prompt's first words"""
    import hashlib
    return 'Q' + hashlib.md5(f'{pre}/{sheet}'.encode()).hexdigest()[:5]


def jobs():
    """_ve-lv2/jobs/<prefix>.json: what a ChatGPT tab draws for one creature, in order: each sheet, then its in-betweens"""
    rows = json.load(open(os.path.join(OUT, 'prompts.json'), encoding='utf-8'))
    out = {}
    for r in rows:
        have = [os.path.join(CHIEU, f"{r['prefix']}_{r['sheet']}_lv2{m}.png") for m in ('', '_mid')]
        if all(map(os.path.exists, have)):     # drawn already: not asked again
            continue
        cols, nrows = grid(os.path.join(ROOT, r['mould']))
        # one picture per sheet: its level-2 frames on top, their in-betweens below (half the requests)
        prompt = ' '.join(r['prompt'].splitlines()).replace(
            f'exactly the same grid of {cols} columns x {nrows} rows', f'a grid of {cols} columns x {2 * nrows} rows').replace(
            'Canvas wide landscape 2:1.', 'Canvas square 1:1.').replace('Canvas landscape 4:3.', 'Canvas portrait 2:3.')
        out.setdefault(r['prefix'], []).append(dict(
            sheet=r['sheet'] + 'x', file=os.path.basename(r['mould']), mid='', code=arena_code(r['prefix'], r['sheet'] + 'x'),
            prompt=prompt + ' ' + COMBO.format(third=', row 5 = its row 3' if nrows == 3 else '',
                                                 order=ORDER_3 if nrows == 3 else ORDER_2)))
    os.makedirs(os.path.join(OUT, 'jobs'), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, 'jobs')):
        os.remove(os.path.join(OUT, 'jobs', f))
    for pre, steps in out.items():
        with open(os.path.join(OUT, 'jobs', pre + '.json'), 'w', encoding='utf-8') as f:
            json.dump(dict(prefix=pre, steps=steps), f, ensure_ascii=False)
    print(len(out), 'jobs')


def take_in(drawn, pre, n):
    """fit each cell of the drawing into the matching cell of the level-1 sheet's size, aspect kept, feet line kept,
    then fade out the art where it runs into a cell side (a beam segment meant to tile keeps its edges)"""
    base, mid = (n[:-4], '_mid') if n.endswith('_mid') else (n, '')    # <n>_mid: its in-between frames, same grid
    mould = os.path.join(CHIEU, f'{pre}_{base}.png')
    cols, nrows = grid(mould)
    tw, th = Image.open(mould).size
    src = Image.open(drawn).convert('RGB')
    sw, sh = src.size
    out = Image.new('RGB', (tw, th), (255, 0, 255))
    cw, ch, dw, dh = sw / cols, sh / nrows, tw / cols, th / nrows
    k = min(dw / cw, dh / ch)
    for r in range(nrows):
        for c in range(cols):
            cell = src.crop((round(c * cw), round(r * ch), round((c + 1) * cw), round((r + 1) * ch)))
            cell = cell.resize((max(1, round(cell.width * k)), max(1, round(cell.height * k))), Image.NEAREST)
            out.paste(cell, (round(c * dw + (dw - cell.width) / 2), round(r * dh + (dh - cell.height) / 2)))
    if 'tile' not in NOTES.get(pre, {}).get(base, ''):
        out = soften(out, cols, nrows)
    dst = os.path.join(CHIEU, f'{pre}_{base}_lv2{mid}.png')
    tmp = os.path.join(tempfile.gettempdir(), f'{pre}_{n}_lv2_tmp.png')
    out.save(tmp)
    optimize(tmp, dst)
    os.remove(tmp)
    print(dst)

DOWNLOADS = os.path.join(ROOT, 'assets', '5 vùng')        # where the user's Chrome saves (that profile's setting)
ARENA_IMG = os.path.join(ROOT, 'preview', 'dau-truong', 'img')
FX_NAME = {'1': 'fx1', '2': 'fx2', '3': 'fx3', '4': 'fx4'}   # the arena's names; aura, vo, no keep theirs


def row_cuts(im, rows):
    """where a drawing's rows really part: ChatGPT draws them unevenly, so each line between two rows moves to the
    emptiest pixel row within 30% of a row around where an even split would put it"""
    ink = (~magenta(np.array(im).astype(np.int32))).sum(1)
    h = im.height / rows
    cuts = [0]
    for k in range(1, rows):
        lo, hi = round(k * h - 0.3 * h), round(k * h + 0.3 * h)
        cuts.append(lo + int(np.argmin(ink[lo:hi])))
    return cuts + [im.height]


def gather():
    """every lv2__<prefix>__<n>[_mid].png Chrome saved: into _ve-lv2/tai-ve/, taken in, copied to the arena page"""
    keep = os.path.join(OUT, 'tai-ve')
    os.makedirs(keep, exist_ok=True)
    codes = {arena_code(r['prefix'], r['sheet'] + 'x'): f"lv2__{r['prefix']}__{r['sheet']}x.png"
             for r in json.load(open(os.path.join(OUT, 'prompts.json'), encoding='utf-8'))}
    for f in sorted(os.listdir(DOWNLOADS)):     # arena.ai saves gpt-image-..._a_<first words of the prompt>.png
        a = re.match(r'gpt-image.*?_a_(Q[0-9a-f]{5})', f)
        if a and a.group(1) in codes:
            os.replace(os.path.join(DOWNLOADS, f), os.path.join(DOWNLOADS, codes[a.group(1)]))
    for f in sorted(os.listdir(DOWNLOADS)):
        m = re.fullmatch(r'lv2__([A-Z]{2}-[A-Z0-9]+_[a-z-]+)__([a-z0-9]+)(_mid)?\.png', f)
        if not m:
            continue
        pre, n, mid = m.group(1), m.group(2), m.group(3) or ''
        if n.startswith(('teen', 'adult')):   # pet bodies: lam_lv3.py gom
            continue
        src = os.path.join(keep, f)
        os.replace(os.path.join(DOWNLOADS, f), src)
        parts = [(src, n, mid)]
        if n.endswith('x'):                # <n>x: rows alternate, a row of the sheet then its in-betweens
            n, im = n[:-1], Image.open(src).convert('RGB')
            rows = 2 * grid(os.path.join(CHIEU, f'{pre}_{n}.png'))[1]
            cuts = row_cuts(im, rows)
            parts = []
            for odd, suf in ((0, ''), (1, '_mid')):
                half = Image.new('RGB', (im.width, im.height // 2), (255, 0, 255))
                for k, r in enumerate(range(odd, rows, 2)):
                    band = im.crop((0, cuts[r], im.width, cuts[r + 1]))       # its art centred in an even slot
                    slot = im.height // rows
                    band = band.crop((0, max(0, (band.height - slot) // 2), im.width, max(0, (band.height - slot) // 2) + slot))                         if band.height > slot else band
                    half.paste(band, (0, k * slot + (slot - band.height) // 2))
                p = os.path.join(tempfile.gettempdir(), f'{pre}_{n}{suf}_half.png')
                half.save(p)
                parts.append((p, n, suf))
        for p, n, mid in parts:
            take_in(p, pre, n + mid)
            dst = os.path.join(ARENA_IMG, pre.split('_', 1)[1], f'{FX_NAME.get(n, n)}{mid}_lv2.png')
            shutil.copy(os.path.join(CHIEU, f'{pre}_{n}_lv2{mid}.png'), dst)


if __name__ == '__main__':
    if sys.argv[1:2] == ['prompts']:
        prompts()
        jobs()
    elif sys.argv[1:2] == ['gom']:
        gather()
    elif sys.argv[1:2] == ['nhan'] and len(sys.argv) == 5:
        take_in(*sys.argv[2:])
    else:
        print(__doc__)
