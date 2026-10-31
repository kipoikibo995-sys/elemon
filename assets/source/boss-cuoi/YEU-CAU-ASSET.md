# Boss cuối: Hư Ảnh ở Đài Ngũ Hành (đề xuất 28/10/2026)

## Theo truyện

- Năm mảnh Hư Ảnh nhập vào năm Thần thú: Viêm Long (Hỏa), Kim Ưng (Kim), Thụ Nhân (Mộc), Thủy Long (Thủy), Thổ Long (Thổ).
  Mỗi con là boss cuối khu 3 của một vùng. Thắng thì Thần thú được giải thoát và rơi **Ngọc Hồn** của hệ đó.
- Đủ 5 Ngọc Hồn thì Già Quy dẫn về Đài Ngũ Hành. Đặt 5 viên vào 5 trụ, phong ấn mở ra và Hư Ảnh hiện nguyên hình.
- Cô Rắn từng nói không hệ nào khắc được Hư Ảnh. Lời giải: **cả năm hệ cùng lúc**. 5 Thần thú đã được giải thoát quay lại giúp,
  giống cảnh phong ấn ngàn năm trước (PHIM_3).

## Trận đánh (người dùng duyệt 2 pha, 28/10/2026; chưa code)

- **Pha 1 – Hóa thân:** Hư Ảnh thu nhỏ thành một con thú khói cỡ pet, đánh như trận Solo bình thường (dùng khung Solo sẵn có).
  Có lính là bóng Hư.
- **Pha 2 – Nguyên hình:** chỉ khi giết được hóa thân (người dùng 28/10/2026, thay cho mốc 50% máu). Hư Ảnh khổng lồ hiện lên phía sau sân (một hình lớn, đứng yên, chỉ mắt
  và xúc tu chuyển động). Nó đập xúc tu xuống sân (báo trước vùng đỏ rồi đập) và mưa cầu khói. Đánh vào **lõi** giữa sân.
- **Ngũ Hành hợp lực:** mỗi lần thanh tuyệt chiêu đầy, nút tuyệt chiêu gọi 5 Thần thú bắn 5 tia vào lõi, như cảnh phong ấn.
  Đây là cách duy nhất làm nó mất nhiều máu ở pha 2.
- Thắng: phim kết, mở **Hư Ảnh làm đối thủ ở Võ đường** (đúng luật mở đối thủ).

## Cách tạo (giống các đợt trước)

Mỗi tấm: mở cuộc trò chuyện mới, đính kèm ảnh tham chiếu ghi bên dưới, dán **Phần chung** rồi dán lời nhắc của tấm đó.
Lưu đúng tên file vào thư mục này (`assets/source/boss-cuoi/`) rồi báo để cắt khung.
Tham chiếu dáng Hư Ảnh: `assets/source/phim/PHIM_1_hu-anh.png`. Tham chiếu Đài: `PHIM_4_dai-ngu-hanh.png`, `PHIM_5_phong-an-nut.png`.

**Dáng Hư Ảnh (dùng cho mọi tấm):** khối khói tím đen đặc, không có hình con vật cụ thể, hai mắt trắng tím sáng xếch, miệng là vết nứt
sáng. Nhiều xúc tu khói, đầu xúc tu mỏng như sương. Trong thân có 5 vết nứt sáng 5 màu (đỏ, trắng bạc, xanh lá, xanh dương, vàng
đất): đó là 5 mảnh Linh khí nó đã nuốt. Mảnh tinh thể tím bay lơ lửng quanh người.

---

## A. Bộ đánh Solo của hóa thân (ưu tiên 1, thiếu là không đánh được)

Đính kèm: `PHIM_1_hu-anh.png` + một bảng mẫu để giữ lưới, ví dụ `assets/source/tinh-linh/arena/KI-T2_kim-giap_legend_s.png`.

**Phần chung**
```
Pixel art sprite sheet for a handheld fighting game, same art style as the attached sprite sheet (use it ONLY for the grid layout, size and style, NOT for the character).
Flat solid magenta background #FF00FF everywhere (no gradient, no floor, no shadow, no text, no grid lines). One character per cell, centered, same size in every cell, feet (smoke base) on the same line, sprites must not touch each other or the cell edges.
Character: HU ANH AVATAR, the final boss: a dark purple-black SMOKE BEAST the size of a big wolf, made entirely of thick swirling shadow smoke, no fur, no scales, no real animal. Two glowing white-violet slanted eyes, a glowing crack for a mouth, 4-6 smoke tentacles flowing from the back and shoulders, wispy smoke base instead of clear feet. Five thin glowing cracks across its body in five colours: red, silver-white, green, blue, earth-gold. Small floating violet crystal shards around it. Menacing but readable at small size, strong dark outline.
```

| File | Lưới | Thêm vào cuối lời nhắc |
|---|---|---|
| `HU-ANH_xoay.png` | 2172x724, 1 hàng 5 ô | `Canvas 2172x724, 1 row of 5 cells: the same pose seen facing down, down-right, right, up-right, up (turnaround sheet).` |
| `HU-ANH_s.png` | 1254x1254, 4x4 | `Canvas 1254x1254, grid 4 columns x 4 rows, every frame FACING DOWN (toward the viewer). Row 1: fighting stance breathing, 4 frames. Row 2: gliding run, 4 frames. Row 3: claw wind-up, claw slash, recover, smoke dash. Row 4: charging (smoke gathering), casting (arms/tentacles thrust forward), hit (recoil, smoke scattering), stunned (eyes dim, swirls).` |
| `HU-ANH_se.png` | như trên | giống `_s` nhưng `every frame FACING DOWN-RIGHT (3/4 view)` |
| `HU-ANH_e.png` | như trên | giống `_s` nhưng `every frame FACING RIGHT (side view)` |
| `HU-ANH_ne.png` | như trên | giống `_s` nhưng `every frame FACING UP-RIGHT (3/4 back view)` |
| `HU-ANH_n.png` | như trên | giống `_s` nhưng `every frame FACING UP (back view)` |
| `HU-ANH_chung.png` | 1774x887, 4x2 | `Canvas 1774x887, grid 4 columns x 2 rows, facing the viewer. Row 1: defeated x2 (smoke collapsing, eyes fading), victory x2 (rising tall, tentacles spread). Row 2: ultimate charge x2 (huge smoke vortex gathering, eyes blazing), ultimate release x2 (roaring, tentacles exploding outward).` |
| `HU-ANH_cutin.png` | 2172x724, 1 ô | `Canvas 2172x724, ONE wide close-up portrait for an ultimate cut-in, NOT a sprite sheet: the Hu Anh face filling the frame, blazing white-violet eyes, glowing crack mouth roaring, smoke tentacles and violet crystal shards flying, five coloured light cracks on its face. Dramatic, high detail pixel art. Magenta #FF00FF only outside the smoke silhouette.` |

## B. Chiêu của hóa thân (ưu tiên 1)

Đính kèm: `PHIM_1_hu-anh.png` + tấm chiêu mẫu cùng số, ví dụ `assets/source/tinh-linh/chieu/KI-T2_kim-giap_2.png`.
Phần chung: `Pixel art effect sprite sheet, same style, canvas size and grid as the attached effect sheet, flat magenta #FF00FF background, effects drawn moving to the RIGHT, no character, no text.`
Cỡ theo mẫu: `_1` 2240x1120, `_2` và `_3` 1774x887, `_4` 1448x1086, `_aura` 1440x720.

| File | Lưới | Chiêu | Lời nhắc thêm |
|---|---|---|---|
| `HU-ANH_1.png` | 4x2 | Vuốt Hư: đánh thường | `Row 1: 3 frames of a purple-black smoke claw slash flying right + 1 empty. Row 2: 3 frames of its hit burst (violet sparks, smoke puff) + 1 empty.` |
| `HU-ANH_2.png` | 4x2 | Xúc Tu Trồi: chiêu chính | `Row 1: 4 frames of a dark smoke tentacle bursting out of the ground and lashing right. Row 2: 4 frames of the impact: tentacle slamming down, violet shockwave ring.` |
| `HU-ANH_3.png` | 4x2 | Tan Vào Khói: lướt/ẩn | `8 frames: a body-sized cloud of purple smoke dissolving into wisps and re-forming (teleport), crystal shards swirling.` |
| `HU-ANH_4.png` | 4x3 | Hư Không Nuốt: tuyệt chiêu | `Row 1: 2 warning frames (a dark violet circle on the ground, cracks glowing) + 2 frames of a black void opening. Row 2: 4 frames of a huge swirling black-violet vortex pulling everything in, five coloured sparks being sucked into it. Row 3: 2 frames of the vortex collapsing in a flash + 2 fading smoke frames.` |
| `HU-ANH_aura.png` | 4x2 | hào quang | `8 frames of a looping aura of rising purple-black smoke and floating violet crystal shards around a body-sized empty centre.` |

## C. Pha 2: Hư Ảnh khổng lồ (ưu tiên 2)

| File | Cỡ | Lời nhắc |
|---|---|---|
| `HU-ANH_khong-lo.png` | 1448x1086 | Đính kèm `PHIM_1_hu-anh.png`. `Pixel art, same style. The giant HU ANH from the reference seen from the FRONT, upper body only, filling the top two thirds of the canvas, rising from below the bottom edge: huge smoke body, two enormous glowing slanted eyes, glowing crack mouth, many thick smoke tentacles spreading left and right, five coloured light cracks across the chest, a bright violet CORE crystal in the centre of the chest. Flat magenta #FF00FF background everywhere outside the silhouette, no scenery, no text.` |
| `HU-ANH_xuc-tu.png` | 4x3 | `Pixel art effect sheet, magenta #FF00FF background, grid 4x3. Row 1: 4 frames of a giant smoke tentacle rising up high (seen from the side, vertical). Row 2: 4 frames of it slamming straight down onto the ground. Row 3: 4 frames of the ground impact: violet shockwave, cracks, smoke dust.` |
| `HU-ANH_mua-khoi.png` | 4x2 | `Pixel art effect sheet, magenta background, grid 4x2. Row 1: 4 frames of a dark violet smoke orb falling from the sky with a trail. Row 2: 4 frames of it bursting on the ground.` |
| `HU-ANH_mat.png` | 4x1 | `Pixel art, magenta background, grid 4x1: the giant's pair of glowing eyes only, 4 frames: open, glowing brighter, narrowed (angry), closed (blink).` |

## D. Ngũ Hành hợp lực và Ngọc Hồn (ưu tiên 2)

| File | Lưới | Lời nhắc |
|---|---|---|
| `NGU-HANH_tia.png` | 4x3 | Đính kèm `PHIM_3_phong-an.png`. `Pixel art effect sheet, magenta background, grid 4x3, seen from above at a 3/4 angle like the reference. Row 1: 4 frames of five coloured light beams (red fire, silver metal, green wood, blue water, gold earth) shooting from the five corners toward the centre. Row 2: 4 frames of the beams meeting in a pentagram of light at the centre, blinding white core. Row 3: 4 frames of the burst fading into sparkles.` |
| `NGU-HANH_than-thu.png` | 5x1 | Đính kèm `PHIM_2_than-thu.png`. `Pixel art, magenta background, one row of 5 cells, each a small glowing spirit silhouette of one guardian beast, facing the centre: Vien Long red fire dragon, Kim Ung silver eagle, Thu Nhan green tree giant, Thuy Long blue water dragon, Tho Long gold earth dragon. Same size, semi-transparent glowing look.` |
| `NGOC-HON.png` | 5x2 | `Pixel art game icons, magenta background, grid 5x2. Row 1: five SOUL GEMS, glowing faceted orbs with a tiny beast spirit inside: red (fire dragon), silver-white (eagle), green (tree), blue (water dragon), gold-brown (earth dragon). Row 2: the same five gems dim and grey (not collected yet).` |

## E. Cảnh và sân (ưu tiên 2)

| File | Cỡ | Lời nhắc |
|---|---|---|
| `SAN_dai-ngu-hanh.png` | 1448x1086, nền đặc | Đính kèm `preview/dau-truong/ui/san/hoa_nui-lua.png` (góc nhìn sân) + `PHIM_4_dai-ngu-hanh.png`. `Pixel art fighting arena background, SAME camera angle and layout as the first attached arena: an oval stone fighting ring in the middle of the lower two thirds. This arena is the top of the Five Elements Altar from the second image at night: a pentagram carved in the floor, five stone pillars around the ring each holding a glowing gem (red, silver, green, blue, gold), violet smoke leaking from cracks, dark stormy purple sky, no characters, no text.` |
| `PHIM_6_dat-ngoc.png` | 1448x1086 | Đính kèm `PHIM_5_phong-an-nut.png`. `Same painted pixel art style. The Five Elements Altar at night: a young trainer and a small spirit pet seen from behind, placing the last glowing soul gem into one of five stone pillars; the other four pillars already shine red, silver, green, blue; light lines start to connect the pillars into a pentagram. Calm before the storm. No text.` |
| `PHIM_7_hu-anh-thuc.png` | 1448x1086 | Đính kèm `PHIM_1_hu-anh.png` + `PHIM_5_phong-an-nut.png`. `Same style. The seal under the altar bursts open: a massive column of purple-black smoke erupts and forms the giant HU ANH with blazing eyes towering over the altar, tentacles spreading over the village; the trainer and pet tiny in the foreground, standing their ground. No text.` |
| `PHIM_8_ket.png` | 1448x1086 | Đính kèm `PHIM_2_than-thu.png`. `Same style. Dawn after the battle: the purple smoke is gone, the five guardian beasts (fire dragon, silver eagle, tree giant, water dragon, earth dragon) stand around the glowing altar, bowing toward the small trainer and pet; the village and the five regions are green and bright again. Peaceful, hopeful. No text.` |

## F. Không phải hình (để sau)

- Nhạc trận boss cuối, tiếng gầm Hư Ảnh, tiếng tia Ngũ Hành.
- Lời thoại Hồi cuối (Già Quy ở Đài, sau khi thắng): làm cùng phiên cốt truyện.

## Thứ tự nên làm

1. A (8 tấm) + B (5 tấm): đủ để đánh pha 1 và có màn VS.
2. `SAN_dai-ngu-hanh` + `NGOC-HON`: có sân riêng và hiện 5 viên ngọc trên màn chọn vùng.
3. C + `NGU-HANH_*`: pha 2 và đòn hợp lực.
4. Ba tấm PHIM: phim mở và phim kết.

## G. Đài Ngũ Hành trên bản đồ thế giới (28/10/2026)

Đặt ở ngã tư giữa làng, giữa Trường học và Võ đường. Chỗ trống ở đó khoảng 110x60 px trên bản đồ gốc 1448x1086.

| File | Cỡ | Đính kèm |
|---|---|---|
| `DAI_ban-do.png` | 512x512, nền magenta | `_tham-chieu_lang.png` (góc nhìn, nét vẽ của làng) + `assets/source/phim/PHIM_4_dai-ngu-hanh.png` (hình dáng Đài) |

```
Pixel art map icon for a top-down 3/4 view world map, EXACTLY the same art style, outline thickness, colours and camera angle as the first attached image (a village on the map): the FIVE ELEMENTS ALTAR from the second attached image, as a small landmark seen from above at the same angle as the village houses. A low round stone platform with a few steps, a pentagram carved on top glowing softly violet in the middle, and five short stone pillars around its edge, each with a small gem on top: red, white-silver, green, blue, gold-brown. A thin wisp of violet smoke rising from the centre crack. Compact and readable at small size (it will be shown about 50 pixels wide), wider than tall, no buildings, no trees, no ground tiles around it, no characters, no text. Flat solid magenta background #FF00FF everywhere outside the altar (no shadow on the background, no gradient).
```
