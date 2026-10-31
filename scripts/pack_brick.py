"""Packs the built game (dist/elemon/elemon, from game/build_game.py + scripts/r36s_game.py) for the TrimUI Brick's
own firmware: build/release/Elemon_<version>_Brick_Stock.zip, holding Apps/Elemon/ (the game, plus the Brick's
launcher, menu entry, icon and button map from packaging/trimui-brick/) and the guide. The save lives outside the
app (Saves/elemon), so copying a new version over never touches it.

Each file's size and SHA-256 go into Apps/Elemon/files.json with the version, so a later update can fetch only
the files that changed.

Usage: python scripts/pack_brick.py v1.0
"""
import hashlib, json, os, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, 'dist', 'elemon', 'elemon')
BRICK = os.path.join(ROOT, 'packaging', 'trimui-brick')
OUT = os.path.join(ROOT, 'build', 'release')
OWN = ['launch.sh', 'config.json', 'icon.png', 'buttons.txt']     # the Brick's own, over the game's
GUIDE = 'HUONG_DAN_Brick.md'
STORED = ('.png', '.ogg', '.hli', '.wav', '.mp3', '.jpg')         # already packed: stored as they are


def files():
    """(path in Apps/Elemon, file on disk), the Brick's own files over the game's"""
    out = {}
    for d, _, names in os.walk(GAME):
        for n in names:
            p = os.path.join(d, n)
            out[os.path.relpath(p, GAME).replace(os.sep, '/')] = p
    for n in OWN:
        out[n] = os.path.join(BRICK, n)
    return sorted(out.items())


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    if len(sys.argv) != 2 or not sys.argv[1].startswith('v'):
        sys.exit(__doc__)
    ver = sys.argv[1]
    if not os.path.isfile(os.path.join(GAME, 'elemon')):
        sys.exit(f'no game at {GAME}: run game/build_game.py and scripts/r36s_game.py first')
    os.makedirs(OUT, exist_ok=True)
    zpath = os.path.join(OUT, f'Elemon_{ver}_Brick_Stock.zip')
    listed = files()
    index = {'version': ver, 'files': {n: {'size': os.path.getsize(p), 'sha256': sha(p)} for n, p in listed}}
    with zipfile.ZipFile(zpath, 'w') as z:
        for n, p in listed:
            info = zipfile.ZipInfo.from_file(p, 'Apps/Elemon/' + n)
            if n in ('elemon', 'launch.sh'):
                info.external_attr = 0o100755 << 16                # runnable when unzipped on Linux
            kind = zipfile.ZIP_STORED if n.lower().endswith(STORED) else zipfile.ZIP_DEFLATED
            with open(p, 'rb') as f:
                z.writestr(info, f.read(), compress_type=kind)
        z.writestr('Apps/Elemon/files.json', json.dumps(index, ensure_ascii=False, indent=0), zipfile.ZIP_DEFLATED)
        z.write(os.path.join(BRICK, GUIDE), GUIDE, zipfile.ZIP_DEFLATED)
    size = sum(v['size'] for v in index['files'].values())
    print(f'{zpath}: {len(listed)} files, {size / 1048576:.1f} MB unpacked, {os.path.getsize(zpath) / 1048576:.1f} MB zip')


if __name__ == '__main__':
    main()
