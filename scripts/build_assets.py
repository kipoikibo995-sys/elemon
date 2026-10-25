"""Rebuilds every generated asset from assets/source, in order. Run after changing a sprite sheet
or an assets/creatures/<id>/anims.json. The last step packs the files the device loads (rooms and
food too when no creature is named):
    PocketGo (default)       pocketgo_pak.py -> build/pak/    from assets/creatures/
    R36S (HOLUA_SCREEN=640)  r36s_pak.py     -> build/r36s/   from assets/creatures-640/
Usage: python build_assets.py [creature-id ...]   (all creatures when none is named)
       python build_assets.py --pak-only          only the packing
       HOLUA_SCREEN=640 python build_assets.py    the same for the R36S set"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
R36S = os.environ.get('HOLUA_SCREEN', '320') == '640'
# the 640 set has no bmp (flash is drawn by code) and shares preview/ and src/anim_data.h with the 320 set,
# so it only cuts, aligns and packs
STEPS = (('slice_frames.py', 'align_frames.py', 'r36s_pak.py') if R36S else
         ('slice_frames.py', 'align_frames.py', 'apply_motion.py', 'make_anim_data.py', 'preview_anims.py',
          'make_preview_page.py',
          'pocketgo_pak.py'))
args = [a for a in sys.argv[1:] if a != '--pak-only']
for step in STEPS[-1:] if '--pak-only' in sys.argv else STEPS:
    print('==', step)
    subprocess.run([sys.executable, os.path.join(HERE, step)] + args, check=True)
