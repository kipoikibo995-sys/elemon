"""Packs the built game (dist/elemon, from game/build_game.py + scripts/r36s_game.py + scripts/build-r36s.ps1) for the
R36S and other ArkOS / PortMaster handhelds: build/release/Elemon_<version>_R36S.zip, holding ports/Elemon.sh and
ports/elemon/ (unzip it onto the card's EASYROMS partition, or copy the two into its ports folder) and the guide.
The save lives beside the game folder (ports/elemon-save), so copying a new version over never touches it.
No in-device update here: that is the Brick's (ota.sh is not packed, so Cài đặt shows no Cập nhật).

Usage: python scripts/pack_r36s.py v1.1
"""
import os, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist', 'elemon')
OUT = os.path.join(ROOT, 'build', 'release')
LEAVE = ('ota.sh', 'cacert.pem', 'files.txt', 'log.txt')          # the Brick's, or left by a run
STORED = ('.png', '.ogg', '.hli', '.wav', '.mp3', '.jpg')          # already packed: stored as they are
GUIDE = """Elemon cho R36S (ArkOS, dArkOS, AmberELEC... có PortMaster)

Cài:
1. Tắt máy, rút thẻ nhớ (thẻ game, phân vùng EASYROMS) cắm vào máy tính.
2. Giải nén file zip này vào gốc thẻ EASYROMS: thư mục ports/ trong zip nhập vào ports/ của thẻ.
   (Hoặc chép tay Elemon.sh và thư mục elemon vào thư mục ports của thẻ.)
3. Cắm thẻ lại, bật máy, vào mục Ports, chọn Elemon.

Cập nhật bản mới: chép đè như trên. Bản lưu nằm ở ports/elemon-save, không bị mất.
Nút: D-pad di chuyển, A chọn, B quay lại, X/Y/L/R theo hướng dẫn trong game, START tạm dừng.
"""


def main(version):
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, f'Elemon_{version}_R36S.zip')
    n = 0
    with zipfile.ZipFile(dst, 'w') as z:
        sh = zipfile.ZipInfo.from_file(os.path.join(DIST, 'Elemon.sh'), 'ports/Elemon.sh')
        sh.external_attr, sh.compress_type = 0o100755 << 16, zipfile.ZIP_DEFLATED
        with open(os.path.join(DIST, 'Elemon.sh'), 'rb') as f:
            z.writestr(sh, f.read().replace(b'\r\n', b'\n'))           # the launcher with Unix line ends
        game = os.path.join(DIST, 'elemon')
        for d, _, names in os.walk(game):
            for name in names:
                p = os.path.join(d, name)
                rel = os.path.relpath(p, game).replace(os.sep, '/')
                if rel in LEAVE or rel.startswith('.ota/'):
                    continue
                info = zipfile.ZipInfo.from_file(p, 'ports/elemon/' + rel)
                if rel == 'elemon':
                    info.external_attr = (0o100755 << 16)       # runnable
                info.compress_type = zipfile.ZIP_STORED if name.lower().endswith(STORED) else zipfile.ZIP_DEFLATED
                with open(p, 'rb') as f:
                    z.writestr(info, f.read())
                n += 1
        z.writestr('HUONG_DAN_R36S.txt', GUIDE)
    print(f'{dst}: {n} files, {os.path.getsize(dst) / 1e6:.1f} MB')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'v1.1')
