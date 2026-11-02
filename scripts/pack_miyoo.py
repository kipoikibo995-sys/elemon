"""Packs the built game for the Miyoo Mini Plus (OnionOS, or the stock firmware):
build/release/Elemon_<version>_MiyooMiniPlus.zip, holding App/Elemon/ and the guide. The game's data is the one in
dist/elemon/elemon (game/build_game.py + scripts/r36s_game.py), the same as the Brick's and the R36S's; the program
is the ARMv7 one from scripts/build-miyoo.ps1 (build/miyoo-armv7/elemon) in place of the ARM64 one, with the Miyoo's
launcher and menu entry from packaging/miyoo/ and the online files (mang.sh, its URL, the CA list) from
packaging/trimui-brick/. The save lives outside the app (Saves/elemon), so copying a new version over never touches it.

App/Elemon/files.txt lists every file as on the Brick, under the same "#version" (Đấu qua wifi lets two handhelds
meet only when their versions are the same) and "#ref ota-miyoo-<version>". There is no ota.sh: the in-device update
fetches the files of a version's tag, which are the ARM64 build's, so the menu entry stays hidden until the Miyoo
has a branch of its own (scripts/push_ota.py does not make one yet).

Usage: python scripts/pack_miyoo.py v1.4.1
"""
import io, os, re, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pack_brick import GAME, BRICK, OUT, STORED, SAFE, manifest, sha   # noqa: E402  (one way of listing files)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIYOO = os.path.join(ROOT, 'packaging', 'miyoo')
BINARY = os.path.join(ROOT, 'build', 'miyoo-armv7', 'elemon')
SOURCES = [os.path.join(ROOT, 'r36s', n) for n in ('jsrt.c', 'jsrt.h', 'js_miyoo.c')]
OWN = {'launch.sh': MIYOO, 'config.json': MIYOO, 'mang.sh': BRICK, 'mang-url.txt': BRICK, 'cacert.pem': BRICK}
DROP = {'buttons.txt', 'files.txt'}            # buttons.txt names SDL pad buttons: the Miyoo reads keys (js_miyoo.c)
RUNNABLE = ('elemon', 'launch.sh', 'mang.sh')
TOP = 'App/Elemon/'
GUIDE = 'HUONG_DAN_Miyoo.md'
ICON = 80                                      # px: the size of the menu's own app icons


def files():
    """(path in App/Elemon, file on disk): the game's, the ARMv7 program in place of the ARM64 one, the Miyoo's own"""
    out = {}
    for d, _, names in os.walk(GAME):
        for n in names:
            p = os.path.join(d, n)
            out[os.path.relpath(p, GAME).replace(os.sep, '/')] = p
    for n in DROP:
        out.pop(n, None)
    out['elemon'] = BINARY
    for n, where in OWN.items():
        out[n] = os.path.join(where, n)
    return sorted(out.items())


def icon():
    """the Brick's 300 px icon at the menu's size (as it is without Pillow)"""
    src = os.path.join(BRICK, 'icon.png')
    try:
        from PIL import Image
    except ImportError:
        return open(src, 'rb').read()
    b = io.BytesIO()
    Image.open(src).convert('RGBA').resize((ICON, ICON), Image.LANCZOS).save(b, 'PNG', optimize=True)
    return b.getvalue()


def main():
    if len(sys.argv) != 2 or not re.match(r'^v\d+(\.\d+)*$', sys.argv[1]):
        sys.exit(__doc__)
    ver = sys.argv[1]
    if not os.path.isfile(os.path.join(GAME, 'js', 'load.txt')):
        sys.exit(f'no game at {GAME}: run game/build_game.py and scripts/r36s_game.py first')
    if not os.path.isfile(BINARY):
        sys.exit(f'no {BINARY}: run scripts/build-miyoo.ps1 first')
    old = [s for s in SOURCES if os.path.getmtime(s) > os.path.getmtime(BINARY)]
    if old:
        sys.exit('the program is older than ' + ', '.join(os.path.basename(s) for s in old) + ': run scripts/build-miyoo.ps1 again')
    if open(BINARY, 'rb').read(20)[18] != 40:                       # e_machine 40: 32-bit ARM
        sys.exit(f'{BINARY} is not a 32-bit ARM program')
    for n in ('launch.sh', 'mang.sh'):
        if b'\r' in open(os.path.join(OWN[n], n), 'rb').read():
            sys.exit(f'{n} has Windows line ends: the Miyoo\'s sh cannot run it')
    listed = files()
    bad = [n for n, _ in listed if not SAFE.match(n)]
    if bad:
        sys.exit('paths outside A-Z a-z 0-9 . _ / -: ' + ', '.join(bad[:10]))
    os.makedirs(OUT, exist_ok=True)
    pic = icon()
    text = manifest(ver, listed, f'ota-miyoo-{ver}')
    size = sum(os.path.getsize(p) for _, p in listed)
    zpath = os.path.join(OUT, f'Elemon_{ver}_MiyooMiniPlus.zip')
    with zipfile.ZipFile(zpath, 'w') as z:
        for n, p in listed:
            info = zipfile.ZipInfo.from_file(p, TOP + n)
            if n in RUNNABLE:
                info.external_attr = 0o100755 << 16                # runnable when unzipped on Linux
            kind = zipfile.ZIP_STORED if n.lower().endswith(STORED) else zipfile.ZIP_DEFLATED
            with open(p, 'rb') as f:
                z.writestr(info, f.read(), compress_type=kind)
        z.writestr(TOP + 'icon.png', pic, zipfile.ZIP_STORED)
        z.writestr(TOP + 'files.txt', text, zipfile.ZIP_DEFLATED)
        z.write(os.path.join(MIYOO, GUIDE), GUIDE, zipfile.ZIP_DEFLATED)
    print(f'{zpath}: {len(listed) + 1} files, {size / 1048576:.1f} MB unpacked, {os.path.getsize(zpath) / 1048576:.1f} MB zip'
          f' (program sha256 {sha(BINARY)[:16]})')


if __name__ == '__main__':
    main()
