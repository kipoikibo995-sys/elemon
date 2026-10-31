"""Huyền thoại (Lv5) skill sheets into the arena page: assets/source/tinh-linh/chieu/<PRE>_<slug>_<n>_lv5.png ->
preview/dau-truong/img/<slug>/<fx>_lv5.png, under the arena's names (1-4 -> fx1-fx4, aura keeps its name). Same grid
and frame order as the level-2 sheets (scripts/lam_huyen_thoai_chieu.py draws them from those); a Huyền thoại pet in
Solo / Vùng đất fights with them (game/src/solo.js, its _lv5 hook), the level-2 sheet standing in for one not drawn.
Usage: python chep_lv5.py   (prints what it copied; run before game/build_game.py)"""
import glob, os, re, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHIEU = os.path.join(ROOT, 'assets', 'source', 'tinh-linh', 'chieu')
ARENA_IMG = os.path.join(ROOT, 'preview', 'dau-truong', 'img')
FX_NAME = {'1': 'fx1', '2': 'fx2', '3': 'fx3', '4': 'fx4'}


def main():
    n = skipped = 0
    for src in sorted(glob.glob(os.path.join(CHIEU, '*_lv5.png'))):
        m = re.match(r'^[A-Z]{2}-[A-Z]\d*_(.+)_([1-4]|aura)_lv5\.png$', os.path.basename(src))
        if not m:
            continue
        slug, k = m.groups()
        dst_dir = os.path.join(ARENA_IMG, slug)
        if not os.path.isdir(dst_dir):
            print('  no arena folder for', slug); skipped += 1; continue
        dst = os.path.join(dst_dir, f'{FX_NAME.get(k, k)}_lv5.png')
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            shutil.copy2(src, dst)
        n += 1
    print(f'{n} Lv5 sheets in the arena' + (f', {skipped} with no arena pet' if skipped else ''))


if __name__ == '__main__':
    main()
