# Đợt 04: 5 khu của vùng Hỏa (bản đồ khám phá nhìn từ trên xuống)

Mỗi vùng gồm 6 khu nối nhau; đi ra mép khu này là sang khu kế. Khu 6 (Lò rèn & Hang boss) đã có:
`assets/source/nen/vung/MAP_hoa.png`. Đợt này vẽ khu 1–5.

```
                    [6] Lò rèn & Hang boss  (đã có)
                              ▲
                    [5] Sông dung nham
                              ▲
 [4] Suối nước nóng ◀── [3] Mỏ quặng lửa
                              ▲
                    [2] Rừng tro
                              ▲
   Bản đồ thế giới ──▶ [1] Chân núi lửa
```

Luật riêng của đợt này (thay luật nền magenta trong `README.md`): ảnh vẽ kín khung, không nền magenta, không cần
`optimize_sheet.py`. Mỗi việc **đính kèm 1 ảnh mẫu**: `assets/source/nen/vung/MAP_hoa.png` (để mọi khu cùng nét vẽ,
cùng góc nhìn, cùng cỡ đá và cây). Vẽ cả 5 khu trong **cùng một cuộc trò chuyện**.

Ảnh hỏng nếu: có nhân vật, con vật, chữ, khung; góc nhìn khác ảnh mẫu; **lối ra không chạm đúng mép đã ghi** (lối ra
là chỗ đường đất chạm mép ảnh, pet đi qua đó để sang khu khác).

Ảnh ra: 1536x1024. Lưu thẳng vào **Đích**.

---

## Việc 1 — Khu 1 · Chân núi lửa
- [x] (1536x1024)
- **Đích:** `assets/source/nen/vung/MAP_hoa_1.png`
- **Lời nhắc:**
```
Create an image. Top-down pixel art game map for a handheld creature-raising RPG, landscape 1536x1024, exactly the same art style, camera angle, colour palette and object scale as IMAGE 1 (another area of the same volcano region). This area is the FOOT OF THE VOLCANO, the gentlest part of the region: reddish-brown earth, wide dirt paths, patches of red-orange grass and autumn shrubs, a few ash-grey dead trees, small boulders, thin cracks glowing with lava, a wooden signpost, only a few small purple crystals (the corruption is weak here). EXITS: a dirt path enters at the middle of the BOTTOM edge (from the world map) and a dirt path leaves through the middle of the TOP edge. Lava, cliffs and rock walls block the left and right edges. About half of the map is open walkable ground. No characters, no creatures, no text, no UI, no grid lines, no frame.
```

## Việc 2 — Khu 2 · Rừng tro
- [ ]
- **Đích:** `assets/source/nen/vung/MAP_hoa_2.png`
- **Lời nhắc:**
```
Create an image. Top-down pixel art game map for a handheld creature-raising RPG, landscape 1536x1024, exactly the same art style, camera angle, colour palette and object scale as IMAGE 1 (another area of the same volcano region). This area is the ASH FOREST: a burnt forest of many charred black and ash-grey dead trees, grey ash covering the ground like snow, glowing embers in fallen logs, red-orange shrubs, small clearings between the trees, some purple smoke wisps. EXITS: a dirt path enters at the middle of the BOTTOM edge, a dirt path leaves through the middle of the TOP edge, and a narrow side path leaves through the middle of the RIGHT edge. Dense dead trees and rocks block the left edge. About half of the map is open walkable ground. No characters, no creatures, no text, no UI, no grid lines, no frame.
```

## Việc 3 — Khu 3 · Mỏ quặng lửa
- [ ]
- **Đích:** `assets/source/nen/vung/MAP_hoa_3.png`
- **Lời nhắc:**
```
Create an image. Top-down pixel art game map for a handheld creature-raising RPG, landscape 1536x1024, exactly the same art style, camera angle, colour palette and object scale as IMAGE 1 (another area of the same volcano region). This area is the FIRE ORE MINE: an open-pit mining area of dark basalt, many glowing orange and red ore rocks and crystal veins, old wooden mine cart tracks with a few abandoned carts, wooden scaffolds, a boarded-up mine tunnel in a rock wall, scattered pickaxes and crates, purple crystals growing over some ore. EXITS: a dirt path enters at the middle of the BOTTOM edge, a dirt path leaves through the middle of the TOP edge, and a path leaves through the middle of the LEFT edge. Rock walls block the right edge. About half of the map is open walkable ground. No characters, no creatures, no text, no UI, no grid lines, no frame.
```

## Việc 4 — Khu 4 · Suối nước nóng (khu phụ)
- [ ]
- **Đích:** `assets/source/nen/vung/MAP_hoa_4.png`
- **Lời nhắc:**
```
Create an image. Top-down pixel art game map for a handheld creature-raising RPG, landscape 1536x1024, exactly the same art style, camera angle, colour palette and object scale as IMAGE 1 (another area of the same volcano region). This area is the HOT SPRINGS, a quiet hidden corner of the volcano: several steaming turquoise hot spring pools ringed with smooth stones, white steam clouds, red and orange flowering herbs, glowing warm stones, a small stone shrine, a few purple crystals near the pools. EXITS: only one, a dirt path leaving through the middle of the RIGHT edge. Cliffs and lava block the other edges. About half of the map is open walkable ground. No characters, no creatures, no text, no UI, no grid lines, no frame.
```

## Việc 5 — Khu 5 · Sông dung nham
- [ ]
- **Đích:** `assets/source/nen/vung/MAP_hoa_5.png`
- **Lời nhắc:**
```
Create an image. Top-down pixel art game map for a handheld creature-raising RPG, landscape 1536x1024, exactly the same art style, camera angle, colour palette and object scale as IMAGE 1 (another area of the same volcano region). This area is the LAVA RIVERS, close to the crater: wide rivers of lava cut the land into islands joined by stone bridges and stepping stones, black basalt columns, lava falls, falling ash, the lava turning purple in places, many purple crystals and purple smoke (the corruption is strong here). EXITS: a dirt path enters at the middle of the BOTTOM edge and a dirt path leaves through the LEFT part of the TOP edge. Lava blocks the left and right edges. About half of the map is open walkable ground. No characters, no creatures, no text, no UI, no grid lines, no frame.
```
