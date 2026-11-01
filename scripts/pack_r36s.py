"""Packs the built game (dist/elemon, from game/build_game.py + scripts/r36s_game.py + scripts/build-r36s.ps1) for the
R36S and other ArkOS / PortMaster handhelds: build/release/Elemon_<version>_R36S.zip, holding ports/Elemon.sh and
ports/elemon/ (unzip it onto the card's EASYROMS partition, or copy the two into its ports folder) and the guide.
The save lives beside the game folder (ports/elemon-save), so copying a new version over never touches it.

The in-device update is the Brick's ota.sh (packaging/trimui-brick) with packaging/r36s/ota-branch.txt naming this
build's own branch, "ota-r36s" (scripts/push_ota.py --r36s puts the files there, tagged ota-r36s-<version>), so the
Brick's files never reach an R36S. ports/elemon/files.txt lists every file as in the Brick's (scripts/pack_brick.py).
Elemon.sh itself sits outside the game folder and is not updated that way.

Usage: python scripts/pack_r36s.py v1.3
"""
import os, re, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pack_brick import manifest, ROOT, SAFE

DIST = os.path.join(ROOT, 'dist', 'elemon')
GAME = os.path.join(DIST, 'elemon')
OUT = os.path.join(ROOT, 'build', 'release')
OWN = {'ota.sh': os.path.join(ROOT, 'packaging', 'trimui-brick', 'ota.sh'),
       'cacert.pem': os.path.join(ROOT, 'packaging', 'trimui-brick', 'cacert.pem'),
       'ota-branch.txt': os.path.join(ROOT, 'packaging', 'r36s', 'ota-branch.txt')}
LEAVE = ('files.txt', 'log.txt')                                   # made here, or left by a run
RUNNABLE = ('elemon', 'ota.sh')
STORED = ('.png', '.ogg', '.hli', '.wav', '.mp3', '.jpg')          # already packed: stored as they are
GUIDE = """Elemon cho R36S (ArkOS, dArkOS, AmberELEC... có PortMaster)

Cài:
1. Tắt máy, rút thẻ nhớ (thẻ game, phân vùng EASYROMS) cắm vào máy tính.
2. Giải nén file zip này vào gốc thẻ EASYROMS: thư mục ports/ trong zip nhập vào ports/ của thẻ.
   (Hoặc chép tay Elemon.sh và thư mục elemon vào thư mục ports của thẻ.)
3. Cắm thẻ lại, bật máy, vào mục Ports, chọn Elemon.

Cập nhật bản mới:
- Máy có wifi: trong game vào Cài đặt -> Cập nhật, tải xong bấm A để cài (game tự mở lại).
- Không có wifi: tải Elemon_R36S.zip mới, chép đè như trên.
Bản lưu nằm ở ports/elemon-save, không bị mất.
Nút: D-pad di chuyển, A chọn, B quay lại, X/Y/L/R theo hướng dẫn trong game, START tạm dừng.
"""


def ref(ver):
    return f'ota-r36s-{ver}'


def files():
    """(path in ports/elemon, file on disk): the game, then the updater's own"""
    out = {}
    for d, _, names in os.walk(GAME):
        for name in names:
            p = os.path.join(d, name)
            rel = os.path.relpath(p, GAME).replace(os.sep, '/')
            if rel in LEAVE or rel.startswith('.ota/'):
                continue
            out[rel] = p
    out.update(OWN)
    return sorted(out.items())


def main():
    if len(sys.argv) != 2 or not re.match(r'^v\d+(\.\d+)*$', sys.argv[1]):
        sys.exit(__doc__)
    version = sys.argv[1]
    if b'\r' in open(OWN['ota.sh'], 'rb').read():
        sys.exit('ota.sh has Windows line ends: the handheld\'s sh cannot run it')
    listed = files()
    bad = [n for n, _ in listed if not SAFE.match(n)]
    if bad:
        sys.exit('paths ota.sh cannot fetch (only A-Z a-z 0-9 . _ / -): ' + ', '.join(bad[:10]))
    os.makedirs(OUT, exist_ok=True)
    text = manifest(version, listed, ref(version))
    with open(os.path.join(OUT, f'ota-r36s-{version}.txt'), 'w', newline='\n') as f:
        f.write(text)
    dst = os.path.join(OUT, f'Elemon_{version}_R36S.zip')
    with zipfile.ZipFile(dst, 'w') as z:
        sh = zipfile.ZipInfo.from_file(os.path.join(DIST, 'Elemon.sh'), 'ports/Elemon.sh')
        sh.external_attr, sh.compress_type = 0o100755 << 16, zipfile.ZIP_DEFLATED
        with open(os.path.join(DIST, 'Elemon.sh'), 'rb') as f:
            z.writestr(sh, f.read().replace(b'\r\n', b'\n'))           # the launcher with Unix line ends
        for rel, p in listed:
            info = zipfile.ZipInfo.from_file(p, 'ports/elemon/' + rel)
            if rel in RUNNABLE:
                info.external_attr = (0o100755 << 16)       # runnable
            info.compress_type = zipfile.ZIP_STORED if rel.lower().endswith(STORED) else zipfile.ZIP_DEFLATED
            with open(p, 'rb') as f:
                z.writestr(info, f.read())
        z.writestr('ports/elemon/files.txt', text, zipfile.ZIP_DEFLATED)
        z.writestr('HUONG_DAN_R36S.txt', GUIDE)
    print(f'{dst}: {len(listed)} files, {os.path.getsize(dst) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
