"""The Solo arenas (preview/dau-truong/ui/san/*.png) without the dark band left at their top (the user, 2026-10-27:
"kéo ảnh sân lên"): each painting is stretched down to fill the whole 640x480 (top to bottom; it is a little softer)
and its ring in san.json (y, ry) moved and stretched with it. The originals are kept in ui/san/_goc/ and always
worked from, so running this again gives the same result. Used by Solo đối kháng (Võ đường) and Vùng đất's matches.
Usage: python scripts/san_keo.py
"""
import json, os, shutil, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAN = os.path.join(ROOT, 'preview', 'dau-truong', 'ui', 'san')
GOC = os.path.join(SAN, '_goc')
DARK = 24                                    # a row this dark on average is the band


def band(im):
    a = np.asarray(im.convert('RGB')).astype(int).mean(axis=(1, 2))
    n = 0
    while n < len(a) // 3 and a[n] < DARK:
        n += 1
    return n


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    os.makedirs(GOC, exist_ok=True)
    jpath, jgoc = os.path.join(SAN, 'san.json'), os.path.join(GOC, 'san.json')
    if not os.path.exists(jgoc):
        shutil.copy(jpath, jgoc)
    man = json.load(open(jgoc, encoding='utf-8'))
    for he, arenas in man.items():
        for a in arenas:
            name = os.path.basename(a['file'])
            src, goc = os.path.join(SAN, name), os.path.join(GOC, name)
            if not os.path.exists(goc):
                shutil.copy(src, goc)
            im = Image.open(goc).convert('RGB')
            b = band(im)
            if b:
                k = im.height / (im.height - b)
                im.crop((0, b, im.width, im.height)).resize(im.size, Image.LANCZOS).save(src, optimize=True)
                a['y'] = round((a['y'] - b) * k)
                a['ry'] = round(a['ry'] * k)
            else:
                im.save(src, optimize=True)
            print(name, 'dải tối', b, 'px ->', a['y'], a['rx'], a['ry'])
    with open(jpath, 'w', encoding='utf-8') as fh:
        json.dump(man, fh, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
