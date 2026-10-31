"""Asset boss cuối Hư Ảnh (assets/source/boss-cuoi/YEU-CAU-ASSET.md), vẽ bằng ChatGPT qua driver lam_bac2_tab.js.

Mỗi đợt một job (prefix BOSS<n>), mỗi bước một tấm; driver lưu lv2__BOSS<n>__<tên tấm>.png vào thư mục tải về.
Ảnh mẫu lưới đính kèm TRƯỚC, ảnh dáng Hư Ảnh SAU (bài học từ Lv4: mẫu đứng sau thì nó chép lưới của ảnh dáng).

Usage: python lam_boss_cuoi.py jobs  -> boss-cuoi/_jobs/BOSS<n>.json (n = 1..4 theo "Thứ tự nên làm")
       python lam_boss_cuoi.py gom   -> lv2__BOSS*__<tên>.png -> boss-cuoi/<tên>.png
"""
import glob, json, os, re, shutil, sys

from lam_bac2 import DOWNLOADS, ROOT

SRC = os.path.join(ROOT, 'assets', 'source')
OUT = os.path.join(SRC, 'boss-cuoi')

LOOK = ("The SECOND attached image shows the HU ANH (the dark smoke spirit) only for its LOOK: colours, smoke, eyes, "
        "tentacles, crystal shards. ")
A_HEAD = ("Create an image. Pixel art sprite sheet for a handheld fighting game, same art style as the FIRST attached "
          "sprite sheet (use it ONLY for the grid layout, size and style, NOT for the character). " + LOOK +
          "Flat solid magenta background #FF00FF everywhere (no gradient, no floor, no shadow, no text, no grid lines). "
          "One character per cell, centered, same size in every cell, feet (smoke base) on the same line, sprites must not "
          "touch each other or the cell edges. Character: HU ANH AVATAR, the final boss: a dark purple-black SMOKE BEAST "
          "the size of a big wolf, made entirely of thick swirling shadow smoke, no fur, no scales, no real animal. Two "
          "glowing white-violet slanted eyes, a glowing crack for a mouth, 4-6 smoke tentacles flowing from the back and "
          "shoulders, wispy smoke base instead of clear feet. Five thin glowing cracks across its body in five colours: "
          "red, silver-white, green, blue, earth-gold. Small floating violet crystal shards around it. Menacing but "
          "readable at small size, strong dark outline. ")
DIR_ROWS = ("Canvas 1254x1254, grid 4 columns x 4 rows, every frame FACING {d}. Row 1: fighting stance breathing, 4 frames. "
            "Row 2: gliding run, 4 frames. Row 3: claw wind-up, claw slash, recover, smoke dash. Row 4: charging (smoke "
            "gathering), casting (arms/tentacles thrust forward), hit (recoil, smoke scattering), stunned (eyes dim, swirls).")
B_HEAD = ("Create an image. Pixel art effect sprite sheet, same style, canvas size and grid as the FIRST attached effect "
          "sheet, flat magenta #FF00FF background, effects drawn moving to the RIGHT, no character, no text. "
          "Colours and mood from the SECOND attached image (purple-black smoke, violet crystal). ")
FX = "Create an image. Pixel art effect sheet, flat magenta #FF00FF background everywhere, no character, no text. "

PHIM1 = 'PHIM_1_hu-anh.png'
REF_S = 'KI-T2_kim-giap_legend_s.png'


def chieu(n):
    return f'KI-T2_kim-giap_{n}.png'


def step(name, files, prompt):
    return {'sheet': name, 'file': files[0] if files else '', 'files': files, 'mid': '', 'prompt': prompt}


def batches():
    a = [step('HU-ANH_xoay', ['KI-T2_kim-giap_child_xoay.png', PHIM1], A_HEAD +
              'Canvas 2172x724, 1 row of 5 cells: the same pose seen facing down, down-right, right, up-right, up '
              '(turnaround sheet).')]
    for s, d in [('s', 'DOWN (toward the viewer)'), ('se', 'DOWN-RIGHT (3/4 view)'), ('e', 'RIGHT (side view)'),
                 ('ne', 'UP-RIGHT (3/4 back view)'), ('n', 'UP (back view)')]:
        a.append(step(f'HU-ANH_{s}', [REF_S, PHIM1], A_HEAD + DIR_ROWS.format(d=d)))
    a.append(step('HU-ANH_chung', ['KI-T2_kim-giap_legend_chung.png', PHIM1], A_HEAD +
                  'Canvas 1774x887, grid 4 columns x 2 rows, facing the viewer. Row 1: defeated x2 (smoke collapsing, eyes '
                  'fading), victory x2 (rising tall, tentacles spread). Row 2: ultimate charge x2 (huge smoke vortex '
                  'gathering, eyes blazing), ultimate release x2 (roaring, tentacles exploding outward).'))
    a.append(step('HU-ANH_cutin', ['KI-T2_kim-giap_cutin.png', PHIM1], A_HEAD +
                  'Canvas 2172x724, ONE wide close-up portrait for an ultimate cut-in, NOT a sprite sheet: the Hu Anh face '
                  'filling the frame, blazing white-violet eyes, glowing crack mouth roaring, smoke tentacles and violet '
                  'crystal shards flying, five coloured light cracks on its face. Dramatic, high detail pixel art. Magenta '
                  '#FF00FF only outside the smoke silhouette.'))
    for n, size, grid, extra in [
            ('1', '2240x1120', '4x2', 'Row 1: 3 frames of a purple-black smoke claw slash flying right + 1 empty. Row 2: '
             '3 frames of its hit burst (violet sparks, smoke puff) + 1 empty.'),
            ('2', '1774x887', '4x2', 'Row 1: 4 frames of a dark smoke tentacle bursting out of the ground and lashing '
             'right. Row 2: 4 frames of the impact: tentacle slamming down, violet shockwave ring.'),
            ('3', '1774x887', '4x2', '8 frames: a body-sized cloud of purple smoke dissolving into wisps and re-forming '
             '(teleport), crystal shards swirling.'),
            ('4', '1448x1086', '4x3', 'Row 1: 2 warning frames (a dark violet circle on the ground, cracks glowing) + 2 '
             'frames of a black void opening. Row 2: 4 frames of a huge swirling black-violet vortex pulling everything '
             'in, five coloured sparks being sucked into it. Row 3: 2 frames of the vortex collapsing in a flash + 2 '
             'fading smoke frames.'),
            ('aura', '1440x720', '4x2', '8 frames of a looping aura of rising purple-black smoke and floating violet '
             'crystal shards around a body-sized empty centre.')]:
        a.append(step(f'HU-ANH_{n}', [chieu(n), PHIM1], B_HEAD + f'Canvas {size}, grid {grid}. ' + extra))

    b = [step('SAN_dai-ngu-hanh', ['hoa_nui-lua.png', 'PHIM_4_dai-ngu-hanh.png'],
              'Create an image. Pixel art fighting arena background, canvas 1448x1086, solid scene (no magenta), SAME '
              'camera angle and layout as the first attached arena: an oval stone fighting ring in the middle of the lower '
              'two thirds. This arena is the top of the Five Elements Altar from the second image at night: a pentagram '
              'carved in the floor, five stone pillars around the ring each holding a glowing gem (red, silver, green, '
              'blue, gold), violet smoke leaking from cracks, dark stormy purple sky, no characters, no text.'),
         step('NGOC-HON', [], 'Create an image. Pixel art game icons, flat magenta #FF00FF background, grid 5 columns x 2 '
              'rows, one icon per cell, centered, not touching. Row 1: five SOUL GEMS, glowing faceted orbs with a tiny '
              'beast spirit inside: red (fire dragon), silver-white (eagle), green (tree), blue (water dragon), gold-brown '
              '(earth dragon). Row 2: the same five gems dim and grey (not collected yet). No text.')]

    c = [step('HU-ANH_khong-lo', [PHIM1], 'Create an image. Pixel art, same style as the attached image, canvas '
              '1448x1086. The giant HU ANH from the reference seen from the FRONT, upper body only, filling the top two '
              'thirds of the canvas, rising from below the bottom edge: huge smoke body, two enormous glowing slanted eyes, '
              'glowing crack mouth, many thick smoke tentacles spreading left and right, five coloured light cracks across '
              'the chest, a bright violet CORE crystal in the centre of the chest. Flat magenta #FF00FF background '
              'everywhere outside the silhouette, no scenery, no text.'),
         step('HU-ANH_xuc-tu', [PHIM1], FX + 'Purple-black smoke like the attached image. Canvas 1448x1086, grid 4x3. '
              'Row 1: 4 frames of a giant smoke tentacle rising up high (seen from the side, vertical). Row 2: 4 frames of '
              'it slamming straight down onto the ground. Row 3: 4 frames of the ground impact: violet shockwave, cracks, '
              'smoke dust.'),
         step('HU-ANH_mua-khoi', [PHIM1], FX + 'Purple-black smoke like the attached image. Canvas 1774x887, grid 4x2. '
              'Row 1: 4 frames of a dark violet smoke orb falling from the sky with a trail. Row 2: 4 frames of it '
              'bursting on the ground.'),
         step('HU-ANH_mat', [PHIM1], FX + 'Canvas 2172x724, grid 4x1: the giant\'s pair of glowing eyes only (like the '
              'attached image), 4 frames: open, glowing brighter, narrowed (angry), closed (blink).'),
         step('NGU-HANH_tia', ['PHIM_3_phong-an.png'], FX + 'Canvas 1448x1086, grid 4x3, seen from above at a 3/4 angle '
              'like the attached image. Row 1: 4 frames of five coloured light beams (red fire, silver metal, green wood, '
              'blue water, gold earth) shooting from the five corners toward the centre. Row 2: 4 frames of the beams '
              'meeting in a pentagram of light at the centre, blinding white core. Row 3: 4 frames of the burst fading '
              'into sparkles.'),
         step('NGU-HANH_than-thu', ['PHIM_2_than-thu.png'], 'Create an image. Pixel art, flat magenta #FF00FF '
              'background, canvas 2172x724, one row of 5 cells, each a small glowing spirit silhouette of one guardian '
              'beast from the attached image, facing the centre: Vien Long red fire dragon, Kim Ung silver eagle, Thu Nhan '
              'green tree giant, Thuy Long blue water dragon, Tho Long gold earth dragon. Same size, semi-transparent '
              'glowing look. No text.')]

    d = [step('PHIM_6_dat-ngoc', ['PHIM_5_phong-an-nut.png'], 'Create an image. Same painted pixel art style as the '
              'attached image, canvas 1448x1086. The Five Elements Altar at night: a young trainer and a small spirit pet '
              'seen from behind, placing the last glowing soul gem into one of five stone pillars; the other four pillars '
              'already shine red, silver, green, blue; light lines start to connect the pillars into a pentagram. Calm '
              'before the storm. No text.'),
         step('PHIM_7_hu-anh-thuc', [PHIM1, 'PHIM_5_phong-an-nut.png'], 'Create an image. Same style as the attached '
              'images, canvas 1448x1086. The seal under the altar bursts open: a massive column of purple-black smoke '
              'erupts and forms the giant HU ANH (first image) with blazing eyes towering over the altar (second image), '
              'tentacles spreading over the village; the trainer and pet tiny in the foreground, standing their ground. '
              'No text.'),
         step('PHIM_8_ket', ['PHIM_2_than-thu.png'], 'Create an image. Same style as the attached image, canvas 1448x1086. '
              'Dawn after the battle: the purple smoke is gone, the five guardian beasts (fire dragon, silver eagle, tree '
              'giant, water dragon, earth dragon) stand around the glowing altar, bowing toward the small trainer and pet; '
              'the village and the five regions are green and bright again. Peaceful, hopeful. No text.')]
    return [a, b, c, d]


def jobs():
    os.makedirs(os.path.join(OUT, '_jobs'), exist_ok=True)
    for n, steps in enumerate(batches(), 1):
        json.dump({'prefix': f'BOSS{n}', 'steps': steps},
                  open(os.path.join(OUT, '_jobs', f'BOSS{n}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        print(f'BOSS{n}', len(steps), sorted({f for s in steps for f in s['files']}))


def gom():
    for f in sorted(os.listdir(DOWNLOADS)):
        m = re.match(r'lv2__BOSS\d__(.+\.png)$', f)
        if m:
            shutil.move(os.path.join(DOWNLOADS, f), os.path.join(OUT, m.group(1)))
            print(m.group(1))


{'jobs': jobs, 'gom': gom}[sys.argv[1]]()
