# Sheet phụ 4x4: ăn, chơi, từ chối ăn, được vuốt ve, vẫy tay, buồn, giận

Mỗi con, mỗi giai đoạn Con / Nhi / Thiếu niên: một cuộc trò chuyện ChatGPT mới, đính kèm sheet chính của đúng giai đoạn đó
(`<HỆ>-<NHÁNH>_<con>_<baby|child|teen>.png`), dán lời nhắc dưới đây (thay `{NAME}` và `{STAGE}` = BABY / CHILD / TEEN).
Tải về, chạy `python scripts/optimize_sheet.py <file tải về> assets/source/tinh-linh/<HỆ>-<NHÁNH>_<con>_<stage>_extra.png`,
rồi `python scripts/build_assets.py <con>` (và `HOLUA_SCREEN=640`). Thứ tự ô khớp `LAYOUTS['extra']` trong `scripts/slice_frames.py`.

```
Create an image. Pixel art sprite sheet for a handheld game. The attached image is the existing sprite sheet of this exact character ({NAME}, {STAGE} stage). Draw NEW animation frames of the SAME character: identical pixel art style, palette, dark outline, proportions, body shape, colours, markings and accessories, and the same size as in the attached sheet, always facing right. Square canvas 1024x1024, flat solid magenta background #FF00FF everywhere (no gradient, no floor, no shadow, no text, no numbers, no grid lines). NO food, NO props, NO human hands. Grid of 4 columns x 4 rows, one character per cell, centered, the whole character fully inside its cell (nothing cropped), sprites must not touch each other, feet on the same line in every cell except the mid-air frames. Row 1: (1) standing idle exactly like the first frame of the attached sheet; (2) EAT look: looking down at food on the floor in front of it, tongue out, excited; (3) EAT bite: head bent down to the floor, mouth open, biting; (4) EAT chew: head up, cheeks puffed, eyes closed, chewing. Row 2: (5) EAT happy: licking its lips, rubbing its belly, satisfied; (6) PLAY crouch: squatting low, ready to jump; (7) PLAY jump: springing up, body stretched; (8) PLAY mid-air: high in the air, legs tucked, big smile. Row 3: (9) PLAY spin: curled into a ball doing a somersault; (10) PLAY land: landing with bent legs; (11) PLAY cheer: arms or front paws raised high, eyes closed happy, mouth open; (12) REFUSE food: turning its head away, eyes shut, mouth closed tight, one paw or hand pushing away. Row 4: (13) PETTED: eyes closed blissfully, blushing cheeks, head tilted up as if being stroked, two tiny hearts; (14) WAVE: friendly smile, one paw or hand raised waving hello; (15) SAD: sitting slumped, head down, droopy teary eyes; (16) ANGRY: angry frowning face with puffed cheeks, stomping, a small puff of steam above the head.
```

## Kiểu riêng từng con (chốt 24/10/2026)

Hỏa (6 con) và Kim (6 con) vẽ bằng lời nhắc chung ở trên. Mộc, Thủy, Thổ (19 con) mỗi con ăn/chơi/phản ứng theo kiểu riêng:
mô tả từng ô ở `kieu-an-choi.json`. Lời nhắc ghép như trên nhưng thay các ô (2)–(16) bằng
`EAT: <eat[i]>`, `PLAY: <play[i]>`, `REFUSE food: <refuse>`, `PETTED: <petted>`, `WAVE hello: <wave>`, `SAD: <sad>`, `ANGRY: <angry>`.
Cột `motion` (jump / ground / float, slow / fast) chỉnh nhịp `eat` / `happy` bằng `scripts/apply_motion.py` (chạy sẵn trong build_assets.py).

Nguồn ảnh: ChatGPT (chạy 5–7 tab song song được); hết lượt thì arena.ai `image/direct?model_a=gpt-image-2.5-sunburst`
(chỉ 2 tab cùng lúc, nhiều hơn bị "rate limit"; ô nhập + ảnh đính kèm là bản nháp CHUNG mọi tab, phải gỡ ảnh cũ trước khi gửi;
nút tải ra file `gpt-image-2.5-sunburst_a_<đầu lời nhắc>.png`, có lúc mở ảnh ở tab mới).
