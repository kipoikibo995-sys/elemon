"""Every creature sheet in assets/source/tinh-linh/, sorted into element > creature > stage.

Nothing to type when a new sheet arrives: a file named <ELEMENT>-<BRANCH>_<slug>[_<stage>].png is
found by itself (e.g. MO-T2_moc-loc_egg.png = Mộc, Thú hồn 2, Mộc Lộc, egg; no stage = adult).
Output goes to assets/creatures/<element>/<slug>/<stage>/ and preview/<element>/<slug>/<stage>/.

Command line of every build script: creature slugs, element folders (hoa kim moc thuy tho) and
stages (egg baby child teen adult legend) narrow the selection; nothing named = everything.
"""
import glob, hashlib, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, 'assets', 'source', 'tinh-linh')

# code -> (folder, name), in Ngũ Hành order
ELEMENTS = {'HO': ('hoa', 'Hỏa'), 'KI': ('kim', 'Kim'), 'MO': ('moc', 'Mộc'),
            'TH': ('thuy', 'Thủy'), 'TO': ('tho', 'Thổ')}
BRANCHES = {'T': 'Thú hồn', 'N': 'Nguyên tố', 'X': 'Ẩn'}
# adult4 / legend4: the same adult / legend creature walking on four legs (wild, low taming);
# only the QUADRUPEDS have them, from assets/source/tinh-linh/4-chan/<CODE>_<slug>_4chan_<adult|legend>.png
STAGES = ['egg', 'baby', 'child', 'teen', 'adult', 'legend', 'adult4', 'legend4']
STAGE_NAMES = {'egg': 'Trứng', 'baby': 'Con', 'child': 'Nhi', 'teen': 'Thiếu niên', 'adult': 'Trưởng thành',
               'legend': 'Huyền thoại', 'adult4': 'Trưởng thành 4 chân', 'legend4': 'Huyền thoại 4 chân'}
# which sheet layout (scripts/slice_frames.py) each stage uses
LAYOUT = {'egg': 'egg', 'baby': 'young', 'child': 'young', 'teen': 'young', 'adult': 'adult', 'legend': 'adult',
          'adult4': 'four', 'legend4': 'four'}
QUADRUPEDS = {'hoa-ho', 'hoa-quy', 'hoa-ho-cao', 'viem-long', 'kim-te', 'kim-giap', 'moc-hung', 'moc-loc',
              'moc-tru', 'tho-nguu', 'tho-tuong', 'tho-tich', 'tho-long'}

NAMES = {
    'hoa-ho': 'Hỏa Hổ', 'hoa-quy': 'Hỏa Quy', 'hoa-ho-cao': 'Hỏa Hồ', 'viem-long': 'Viêm Long',
    'dung-nham-ve': 'Dung Nham Vệ', 'hoa-linh': 'Hỏa Linh',
    'kim-te': 'Kim Tê', 'kim-giap': 'Kim Giáp', 'kim-ung': 'Kim Ưng', 'tinh-kim-hiep': 'Tinh Kim Hiệp',
    'kim-thach-nhan': 'Kim Thạch Nhân', 'liem-dao': 'Liêm Đao',
    'moc-hung': 'Mộc Hùng', 'moc-loc': 'Mộc Lộc', 'moc-duong': 'Mộc Đường', 'thu-nhan': 'Thụ Nhân',
    'reu-linh': 'Rêu Linh', 'diep-linh': 'Diệp Linh', 'moc-tru': 'Mộc Trư',
    'thuy-sa': 'Thủy Sa', 'thuy-giai': 'Thủy Giải', 'thuy-long': 'Thủy Long', 'thuy-chien': 'Thủy Chiến',
    'bao-thuy': 'Bào Thủy', 'thuy-giao': 'Thủy Giao',
    'tho-nguu': 'Thổ Ngưu', 'tho-tuong': 'Thổ Tượng', 'tho-tich': 'Thổ Tích', 'thach-nhan': 'Thạch Nhân',
    'thanh-tri': 'Thành Trì', 'tho-long': 'Thổ Long',
}
# sheets that do not follow the file-name pattern
EXTRA = {('hoa-ho', 'adult'): ('HO', 'T1', 'hoa-ho-truong-thanh-spritesheet.png')}

# Sheets drawn as the wrong creature: skipped while the file is still this exact one (MD5).
# Replace the file and it is picked up again by itself.
REDO = {
    ('viem-long', 'baby'): '4bc607282b71fc88cbccbf5379db5ca8',
    ('viem-long', 'child'): '864eccbf288127eb654dcbb10d852ff4',
    ('viem-long', 'teen'): '508ca4ce0d35b9c347661c22d425b889',
    ('hoa-linh', 'egg'): 'bbe553e1f50efe45eef9d68efd84d03f',
    ('hoa-linh', 'child'): '496be9b92ee9c3dd5878d1470fbf0f94',
    ('hoa-linh', 'teen'): '3f8acac6dcae9e9ddb4dfdca93d02f79',
    ('hoa-quy', 'baby'): '0b6be5bf3488842d4f6fbf81c983db9e',
    ('hoa-quy', 'child'): '43cdee79d07180e434299e77b9b5b12d',
    ('hoa-quy', 'teen'): '91dc2021f651aea9b06b882459d8d530',
    ('dung-nham-ve', 'teen'): '6465a9bb35b4b1cf5d279fce3cca5cbd',
    ('hoa-ho-cao', 'egg'): '354d62e479c312fffac3af8d75452c17',
    ('hoa-ho-cao', 'baby'): 'f5ef2cf5e915d2d6fe31557ac885cf2e',
    ('hoa-ho-cao', 'child'): 'a0329d1c93f94d8329e1d17976307b94',
    ('hoa-ho-cao', 'teen'): '795e775e274129595669b0266d41dbad',
}
REDO_WHY = 'vẽ ra hổ, không đúng con'

PATTERN = re.compile(r'^([A-Z]{2})-([TNX]\d?)_([a-z0-9-]+?)(?:_(egg|baby|child|teen|legend))?\.png$')
PATTERN4 = re.compile(r'^([A-Z]{2})-([TNX]\d?)_([a-z0-9-]+?)_4chan_(adult|legend)\.png$')
# Extra action frames for a stage that already has its main sheet: <ELEMENT>-<BRANCH>_<slug>_<stage>_extra.png,
# layout 'extra' in slice_frames.py (first cell = a standing pose that only sets the size). Cut onto the
# same canvas as the main sheet; a stage without one is built exactly as before.
PATTERN_EXTRA = re.compile(r'^([A-Z]{2})-([TNX]\d?)_([a-z0-9-]+?)_(baby|child|teen|adult|legend)_extra\.png$')
# Activity sheets, 4x2 on magenta, in assets/source/tinh-linh/act2/<ELEMENT>-<BRANCH>_<slug>_<stage>_<kind>.png:
# kind choi = playing ball, tam = bath (the tub is part of each frame), thuoc = taking medicine.
# Each becomes 8 frames <name>-0..7 on the stage's canvas and the anim <name> (assets/anim-templates/<layout>.json).
# kind front = the creature seen from the front, three-quarter and back (FRONT_FRAMES), no anim of its own.
# kind di = a walk strip, 1 row of 4 (contact, passing, contact, passing) for stages whose main sheet has none.
ACTS = {'choi': 'ball', 'tam': 'bath', 'thuoc': 'medicine', 'front': 'front', 'di': 'walk'}
FRONT_FRAMES = [['front-idle', 'front-blink', 'front-happy', 'front-wave'],
                ['turn', 'back', 'front-sad', 'front-sleep']]
PATTERN_ACT = re.compile(r'^([A-Z]{2})-([TNX]\d?)_([a-z0-9-]+?)_(baby|child|teen|adult|legend)_(choi|tam|thuoc|front|di)\.png$')


def md5(path):
    with open(path, 'rb') as fh:
        return hashlib.md5(fh.read()).hexdigest()


def _scan():
    """{slug: {'name', 'code', 'branch', 'element', 'sheets': {stage: path}, 'redo': {stage}}}"""
    found = {}

    def add(code, branch, slug, stage, path):
        c = found.setdefault(slug, {'name': NAMES.get(slug, slug), 'code': code, 'branch': branch,
                                    'element': ELEMENTS[code][0], 'sheets': {}, 'extras': {}, 'acts': {},
                                    'redo': set()})
        if REDO.get((slug, stage)) == md5(path):
            c['redo'].add(stage)
        else:
            c['sheets'][stage] = path
    for path in sorted(glob.glob(os.path.join(SOURCE, '*.png'))):
        m = PATTERN.match(os.path.basename(path))
        if m and m.group(1) in ELEMENTS:
            add(m.group(1), m.group(2), m.group(3), m.group(4) or 'adult', path)
    for path in sorted(glob.glob(os.path.join(SOURCE, '4-chan', '*.png'))):
        m = PATTERN4.match(os.path.basename(path))
        if m and m.group(1) in ELEMENTS:
            add(m.group(1), m.group(2), m.group(3), m.group(4) + '4', path)
    for (slug, stage), (code, branch, name) in EXTRA.items():
        add(code, branch, slug, stage, os.path.join(SOURCE, name))
    for path in sorted(glob.glob(os.path.join(SOURCE, '*_extra.png'))):
        m = PATTERN_EXTRA.match(os.path.basename(path))
        if m and m.group(3) in found:
            found[m.group(3)]['extras'][m.group(4)] = path
    for path in sorted(glob.glob(os.path.join(SOURCE, 'act2', '*.png'))):
        m = PATTERN_ACT.match(os.path.basename(path))
        if m and m.group(3) in found:
            found[m.group(3)]['acts'].setdefault(m.group(4), {})[m.group(5)] = path
    order = list(ELEMENTS)
    return dict(sorted(found.items(), key=lambda kv: (order.index(kv[1]['code']),
                                                      'TNX'.index(kv[1]['branch'][0]), kv[1]['branch'])))


CREATURES = _scan()


def element_name(cid):
    return ELEMENTS[CREATURES[cid]['code']][1]


def branch_name(cid):
    return BRANCHES[CREATURES[cid]['branch'][0]]


def sheet(cid, stage):
    return CREATURES[cid]['sheets'][stage]


def extra_sheet(cid, stage):
    """the sheet of extra action frames, or None"""
    return CREATURES[cid]['extras'].get(stage)


def act_sheets(cid, stage):
    """{kind: path} of the activity sheets (ACTS) of this unit"""
    return CREATURES[cid]['acts'].get(stage, {})


# Screen the frames are made for: HOLUA_SCREEN=640 builds the R36S set (640x480, twice the size)
# into assets/creatures-640/; unset = the PocketGo set (320x240) in assets/creatures/.
SCREEN = int(os.environ.get('HOLUA_SCREEN', '320'))
SIZE = SCREEN / 320                     # 1 or 2
CREATURE_DIR = 'creatures' if SCREEN == 320 else f'creatures-{SCREEN}'


def frames_dir(cid, stage):
    """png/, bmp/, bmp-flash/, frames.json, anims.json of one creature at one stage"""
    return os.path.join(ROOT, 'assets', CREATURE_DIR, CREATURES[cid]['element'], cid, stage)


def preview_dir(cid, stage):
    return os.path.join(ROOT, 'preview', CREATURES[cid]['element'], cid, stage)


# anims drawn with the extra sheet's frames (slice_frames.py LAYOUTS['extra']); a template keeps the one-frame
# eat / happy as "_eat_1khung" / "_happy_1khung" for stages that have no extra sheet
EXTRA_ANIMS = ('eat', 'happy', 'refuse', 'petted', 'wave', 'sad', 'angry')


def _anim_blocks(text):
    """{name: its text} of the top-level entries of a hand-laid anims file, in order"""
    body = text.strip()[1:-1]
    parts = re.split(r'^(?=  ")', body, flags=re.M)
    return {re.match(r'\s*"(\w+)"', b).group(1): b.rstrip().rstrip(',') for b in parts if b.strip()}


def _anim_text(blocks):
    return '{\n' + ',\n'.join(blocks.values()) + '\n}\n'


def anims_path(cid, stage):
    """A new unit starts from the approved motion template of its layout; edit its own copy after.
    One file for both sets, in 320 units (assets/creatures/...): the 640 set multiplies x, y and br
    by SIZE while drawing. A unit that gets its extra sheet later has the template's EXTRA_ANIMS put in
    (its other anims are kept)."""
    folder = os.path.join(ROOT, 'assets', 'creatures', CREATURES[cid]['element'], cid, stage)
    path = os.path.join(folder, 'anims.json')
    template = os.path.join(ROOT, 'assets', 'anim-templates', LAYOUT[stage] + '.json')
    tpl = _anim_blocks(open(template, encoding='utf-8').read())
    one = {k[1:-len('_1khung')]: v.replace(f'"{k}":', f'"{k[1:-len("_1khung")]}":', 1)
           for k, v in tpl.items() if k.endswith('_1khung')}
    if not one:                                   # a template without the extra-sheet anims
        if not os.path.exists(path):
            os.makedirs(folder, exist_ok=True)
            shutil.copy(template, path)
        _act_anims(cid, stage, path, tpl)
        return path
    extra = extra_sheet(cid, stage)
    if not os.path.exists(path):
        os.makedirs(folder, exist_ok=True)
        if extra:
            out = {k: v for k, v in tpl.items() if k not in ['_' + a + '_1khung' for a in one]}
        else:
            out = {k: v for k, v in tpl.items() if k not in EXTRA_ANIMS and not k.endswith('_1khung')}
            first = list(tpl).index('eat')            # the one-frame anims where eat / happy were
            items = list(out.items())
            items[first:first] = list(one.items())
            out = dict(items)
        open(path, 'w', encoding='utf-8').write(_anim_text(out))
    elif extra:
        own = _anim_blocks(open(path, encoding='utf-8').read())
        if not all(a in own for a in EXTRA_ANIMS):     # an older copy: put the extra-sheet anims in
            out = {}
            for k, v in own.items():
                out[k] = tpl[k] if k in EXTRA_ANIMS else v
                if k == 'happy':
                    out.update({a: tpl[a] for a in EXTRA_ANIMS if a not in own})
            out.update({a: tpl[a] for a in EXTRA_ANIMS if a not in out})
            open(path, 'w', encoding='utf-8').write(_anim_text(out))
    _act_anims(cid, stage, path, tpl)
    return path


def _act_anims(cid, stage, path, tpl):
    """Puts the template's ACTS anims in a unit that has those sheets and drops them where it has not."""
    have = {ACTS[k] for k in act_sheets(cid, stage)}
    names = [a for a in ACTS.values() if a in tpl]
    if LAYOUT[stage] != 'adult':                  # young / four sheets draw their own walk: never drop it
        names = [a for a in names if a != 'walk']
    if not names:
        return
    own = _anim_blocks(open(path, encoding='utf-8').read())
    out = {k: v for k, v in own.items() if k not in names or k in have}
    out.update({a: tpl[a] for a in names if a in have and a not in out})
    if list(out) != list(own):
        open(path, 'w', encoding='utf-8').write(_anim_text(out))


def selected(argv=None):
    """(creature, stage) pairs that have a usable sheet, narrowed by the names on the command line."""
    args = (sys.argv if argv is None else argv)[1:]
    folders = {f for f, _ in ELEMENTS.values()}
    unknown = [a for a in args if a not in CREATURES and a not in folders and a not in STAGES]
    if unknown:
        sys.exit(f'unknown {unknown}; use creature slugs, {sorted(folders)} or {STAGES}')
    want_c = [a for a in args if a in CREATURES]
    want_e = [a for a in args if a in folders]
    want_s = [a for a in args if a in STAGES]
    units = []
    for cid, c in CREATURES.items():
        # creatures and elements add up ("hoa-linh tho" = Hỏa Linh plus all of Thổ); stages narrow
        if (want_c or want_e) and cid not in want_c and c['element'] not in want_e:
            continue
        units += [(cid, st) for st in STAGES if st in c['sheets'] and (not want_s or st in want_s)]
    return units
