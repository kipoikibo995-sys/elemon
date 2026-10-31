"""Sheet phụ 4x4 (ăn, chơi, từ chối ăn, được vuốt ve, vẫy tay, buồn, giận) cho dạng Huyền thoại (Lv5).

Lời nhắc theo _lam-lai/LOI-NHAC-KHUNG-PHU.md với STAGE = LEGENDARY; Mộc, Thủy, Thổ dùng kiểu riêng trong kieu-an-choi.json.
Ảnh đính kèm là sheet huyền thoại 4x6 <prefix>_legend.png. Driver lam_bac2_tab.js lưu lv2__<prefix>__legendx.png.

Usage: python lam_legend_extra.py jobs  -> _ve-lv3/jobs-legendx/<prefix>.json
       python lam_legend_extra.py gom   -> lv2__<prefix>__legendx.png trong Downloads -> _ve-lv3/legend-extra/<prefix>_legend_extra.png
Kết quả chưa đưa vào tinh-linh/ (build sẽ tự nhận *_legend_extra.png) cho tới khi nạp game.
"""
import glob, json, os, shutil, sys

SRC = os.path.join(os.path.dirname(__file__), '..', 'assets', 'source', 'tinh-linh')
LV3 = os.path.join(SRC, '_ve-lv3')
from lam_bac2 import DOWNLOADS

HEAD = ("Create an image. Pixel art sprite sheet for a handheld game. The attached image is the existing sprite sheet of "
        "this exact character ({name}, LEGENDARY (final mythic form) stage). Draw NEW animation frames of the SAME character: "
        "identical pixel art style, palette, dark outline, proportions, body shape, colours, markings and accessories, and the "
        "same size as in the attached sheet, always facing right. Square canvas 1024x1024, flat solid magenta background "
        "#FF00FF everywhere (no gradient, no floor, no shadow, no text, no numbers, no grid lines). NO food, NO props, NO human "
        "hands. Grid of 4 columns x 4 rows, one character per cell, centered, the whole character fully inside its cell "
        "(nothing cropped), sprites must not touch each other, feet on the same line in every cell except the mid-air frames. ")
SHARED = ("Row 1: (1) standing idle exactly like the first frame of the attached sheet; (2) EAT look: looking down at food on "
          "the floor in front of it, tongue out, excited; (3) EAT bite: head bent down to the floor, mouth open, biting; (4) EAT "
          "chew: head up, cheeks puffed, eyes closed, chewing. Row 2: (5) EAT happy: licking its lips, rubbing its belly, "
          "satisfied; (6) PLAY crouch: squatting low, ready to jump; (7) PLAY jump: springing up, body stretched; (8) PLAY "
          "mid-air: high in the air, legs tucked, big smile. Row 3: (9) PLAY spin: curled into a ball doing a somersault; (10) "
          "PLAY land: landing with bent legs; (11) PLAY cheer: arms or front paws raised high, eyes closed happy, mouth open; "
          "(12) REFUSE food: turning its head away, eyes shut, mouth closed tight, one paw or hand pushing away. Row 4: (13) "
          "PETTED: eyes closed blissfully, blushing cheeks, head tilted up as if being stroked, two tiny hearts; (14) WAVE: "
          "friendly smile, one paw or hand raised waving hello; (15) SAD: sitting slumped, head down, droopy teary eyes; (16) "
          "ANGRY: angry frowning face with puffed cheeks, stomping, a small puff of steam above the head.")


def own(k):
    e, p = k['eat'], k['play']
    return (f"Row 1: (1) standing idle exactly like the first frame of the attached sheet; (2) EAT: {e[0]}; (3) EAT: {e[1]}; "
            f"(4) EAT: {e[2]}. Row 2: (5) EAT: {e[3]}; (6) PLAY: {p[0]}; (7) PLAY: {p[1]}; (8) PLAY: {p[2]}. Row 3: (9) PLAY: "
            f"{p[3]}; (10) PLAY: {p[4]}; (11) PLAY: {p[5]}; (12) REFUSE food: {k['refuse']}. Row 4: (13) PETTED: {k['petted']}; "
            f"(14) WAVE hello: {k['wave']}; (15) SAD: {k['sad']}; (16) ANGRY: {k['angry']}.")


def prefixes():
    return sorted(os.path.basename(f)[:-len('_legend.png')] for f in glob.glob(os.path.join(SRC, '*_legend.png')))


def jobs():
    kieu = json.load(open(os.path.join(SRC, '_lam-lai', 'kieu-an-choi.json'), encoding='utf-8'))
    out = os.path.join(LV3, 'jobs-legendx')
    os.makedirs(out, exist_ok=True)
    for pre in prefixes():
        slug = pre.split('_', 1)[1]
        k = kieu.get(slug)
        name = k['who'] if k else slug.replace('-', ' ').title()
        prompt = HEAD.format(name=name) + (own(k) if k else SHARED)
        job = {'prefix': pre, 'steps': [{'sheet': 'legendx', 'file': f'{pre}_legend.png',
                                         'files': [f'{pre}_legend.png'], 'mid': '', 'prompt': prompt}]}
        json.dump(job, open(os.path.join(out, f'{pre}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        print(pre, 'own' if k else 'shared')


def gom():
    out = os.path.join(LV3, 'legend-extra')
    os.makedirs(out, exist_ok=True)
    for pre in prefixes():
        f = os.path.join(DOWNLOADS, f'lv2__{pre}__legendx.png')
        if os.path.exists(f):
            shutil.move(f, os.path.join(out, f'{pre}_legend_extra.png'))
    print(len(glob.glob(os.path.join(out, '*_legend_extra.png'))))


{'jobs': jobs, 'gom': gom}[sys.argv[1]]()
