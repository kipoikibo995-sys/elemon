"""Lays a room's standing furniture against the back wall, tidy but natural.

Big pieces (bed, throne, statue, shelf...) stand side by side on the wall line, the bed in the left corner, at
their own size (shrunk together only if the wall is too short, never below MIN_K). Big pieces the wall has no room for stand along the side walls. Small pieces (chest, pot,
lamp, bucket...) stand a step in front of the wall, each at the seam between two big pieces, the way a chest sits
at the foot of a bed. Wall hangings, the rug and the food bowl keep their place.
Usage: python -I xep_do_sat_tuong.py <room> <in.json> <out.json> [wall line y on the 640x480 screen]"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from preview_decor_room import DECOR, flat

K = 640 / 1448
MIN_K, LEFT, RIGHT = 0.85, 6, 634
SMALL = 0.55          # a piece lower than this share of the tallest one is a small piece
STEP = 16             # how far in front of the wall line the small pieces stand (screen px)
room, src, dst = sys.argv[1:4]
p = json.load(open(src, encoding='utf-8'))
box = {}
for n, (x, y, s) in p.items():
    im = Image.open(os.path.join(DECOR, room, n))
    box[n] = (x * K, y * K, im.width * s * K, im.height * s * K, s)
BOWL = ('bowl', 'bat-')                       # the food bowl stays out on the floor
BED = ('bed', 'cot', 'o-rom', 'hammock')
stand = {n: b for n, b in box.items() if not flat(n) and not any(w in n for w in BOWL)}
bottoms = sorted(b[1] + b[3] for b in stand.values())
wall = float(sys.argv[4]) if len(sys.argv) > 4 else bottoms[len(bottoms) // 3]
hang = {n for n, b in stand.items() if b[1] + b[3] < wall - 30}
pieces = [n for n in stand if n not in hang]
tall = max(stand[n][3] for n in pieces)
big = sorted((n for n in pieces if stand[n][3] >= SMALL * tall or any(w in n for w in BED)), key=lambda n: stand[n][0])
small = sorted((n for n in pieces if n not in big), key=lambda n: stand[n][0])
bed = [n for n in big if any(w in n for w in BED)]
big = bed + [n for n in big if n not in bed]
# a back wall too short for every big piece: the smallest ones go to the side walls, front of the corners
side = []
while len(big) > 2 and sum(stand[n][2] for n in big) * MIN_K > RIGHT - LEFT:
    m = min(big[1:], key=lambda n: stand[n][2] * stand[n][3])
    big.remove(m); side.append(m)
total = sum(stand[n][2] for n in big)
k = min(1.0, max(MIN_K, (RIGHT - LEFT) / total))
gap = max(0.0, (RIGHT - LEFT - total * k) / max(1, len(big) - 1))
x, seams = LEFT, []
for i, n in enumerate(big):
    w, h, s = stand[n][2] * k, stand[n][3] * k, stand[n][4] * k
    p[n] = [round(x / K), round((wall - h) / K), round(s, 3)]
    x += w
    if i < len(big) - 1:
        seams.append(x + gap / 2)
    x += gap
seams = seams or [(LEFT + RIGHT) / 2]
# small pieces: one per seam, spread from the bed side; more pieces than seams share them a little apart
for i, n in enumerate(small):
    j = round(i * (len(seams) - 1) / max(1, len(small) - 1)) if len(small) > 1 else 0
    sx = seams[min(j, len(seams) - 1)]
    w, h, s = stand[n][2] * k, stand[n][3] * k, stand[n][4] * k
    sx = min(max(sx - w / 2, LEFT), RIGHT - w)
    p[n] = [round(sx / K), round((wall + STEP - h) / K), round(s, 3)]
for i, n in enumerate(side):                      # right wall first (the bed has the left corner)
    w, h, s = stand[n][2] * k, stand[n][3] * k, stand[n][4] * k
    sx = RIGHT - w if i % 2 == 0 else LEFT
    p[n] = [round(sx / K), round((wall + 40 + (i // 2) * 34 - h) / K), round(s, 3)]
json.dump(p, open(dst, 'w', encoding='utf-8'), indent=1)
print(room, 'wall', round(wall), 'scale', round(k, 2), 'big', len(big), 'small', len(small), 'side', len(side))
