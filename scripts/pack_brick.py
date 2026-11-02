"""Packs the built game (dist/elemon/elemon, from game/build_game.py + scripts/r36s_game.py) for the TrimUI Brick's
own firmware: build/release/Elemon_<version>_Brick_Stock.zip, holding Apps/Elemon/ (the game, plus the Brick's
launcher, menu entry, icon, button map, the updater ota.sh and its CA list from packaging/trimui-brick/) and the
guide. The save lives outside the app (Saves/elemon), so copying a new version over never touches it.

Apps/Elemon/files.txt lists every file as "<sha256> <size> <path>" under "#version" and "#ref" (the git tag
scripts/push_ota.py puts the files at): the in-device update (ota.sh) compares it with the newest version's list
and fetches only the files that differ. The same list is written to build/release/ota-<version>.txt.

Usage: python scripts/pack_brick.py v1.1
"""
import hashlib, os, re, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, 'dist', 'elemon', 'elemon')
BRICK = os.path.join(ROOT, 'packaging', 'trimui-brick')
OUT = os.path.join(ROOT, 'build', 'release')
OWN = ['launch.sh', 'config.json', 'icon.png', 'buttons.txt', 'ota.sh', 'cacert.pem', 'mang.sh', 'mang-url.txt']   # the Brick's own, over the game's
RUNNABLE = ('elemon', 'launch.sh', 'ota.sh', 'mang.sh')
GUIDE = 'HUONG_DAN_Brick.md'
STORED = ('.png', '.ogg', '.hli', '.wav', '.mp3', '.jpg')         # already packed: stored as they are
SAFE = re.compile(r'^[A-Za-z0-9._/-]+$')                           # ota.sh puts paths in URLs as they are


def files():
    """(path in Apps/Elemon, file on disk), the Brick's own files over the game's"""
    out = {}
    for d, _, names in os.walk(GAME):
        for n in names:
            p = os.path.join(d, n)
            out[os.path.relpath(p, GAME).replace(os.sep, '/')] = p
    for n in OWN:
        out[n] = os.path.join(BRICK, n)
    out.pop('files.txt', None)
    return sorted(out.items())


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def manifest(ver, listed, ref=None):
    """files.txt: the version, its git tag (the R36S build's: ota-r36s-<version>), then a line a file"""
    lines = [f'#version {ver}', f'#ref {ref or "ota-" + ver}']
    lines += [f'{sha(p)} {os.path.getsize(p)} {n}' for n, p in listed]
    return '\n'.join(lines) + '\n'


def main():
    if len(sys.argv) != 2 or not re.match(r'^v\d+(\.\d+)*$', sys.argv[1]):
        sys.exit(__doc__)
    ver = sys.argv[1]
    if not os.path.isfile(os.path.join(GAME, 'elemon')):
        sys.exit(f'no game at {GAME}: run game/build_game.py and scripts/r36s_game.py first')
    for n in ('launch.sh', 'ota.sh', 'mang.sh'):
        if b'\r' in open(os.path.join(BRICK, n), 'rb').read():
            sys.exit(f'{n} has Windows line ends: the Brick\'s sh cannot run it')
    listed = files()
    bad = [n for n, _ in listed if not SAFE.match(n)]
    if bad:
        sys.exit('paths ota.sh cannot fetch (only A-Z a-z 0-9 . _ / -): ' + ', '.join(bad[:10]))
    os.makedirs(OUT, exist_ok=True)
    text = manifest(ver, listed)
    with open(os.path.join(OUT, f'ota-{ver}.txt'), 'w', newline='\n') as f:
        f.write(text)
    zpath = os.path.join(OUT, f'Elemon_{ver}_Brick_Stock.zip')
    with zipfile.ZipFile(zpath, 'w') as z:
        for n, p in listed:
            info = zipfile.ZipInfo.from_file(p, 'Apps/Elemon/' + n)
            if n in RUNNABLE:
                info.external_attr = 0o100755 << 16                # runnable when unzipped on Linux
            kind = zipfile.ZIP_STORED if n.lower().endswith(STORED) else zipfile.ZIP_DEFLATED
            with open(p, 'rb') as f:
                z.writestr(info, f.read(), compress_type=kind)
        z.writestr('Apps/Elemon/files.txt', text, zipfile.ZIP_DEFLATED)
        z.write(os.path.join(BRICK, GUIDE), GUIDE, zipfile.ZIP_DEFLATED)
    size = sum(os.path.getsize(p) for _, p in listed)
    print(f'{zpath}: {len(listed)} files, {size / 1048576:.1f} MB unpacked, {os.path.getsize(zpath) / 1048576:.1f} MB zip')


if __name__ == '__main__':
    main()
