# Tinh Linh Ngũ Hành — asset bàn giao (từ Claude cowork)

## File
- `hoa-ho-truong-thanh-spritesheet.png` — Hỏa Hổ (Trưởng thành), 1024x1536, lưới 4 cột x 6 hàng, NỀN ĐÃ TRONG SUỐT (gốc là magenta #FF00FF).
  - Các hàng ảnh (theo y): 22-243, 288-491, 519-745, 781-1006, 1031-1251, 1293-1501. Cột: chia đều 256px (lửa có thể chạm cột bên cạnh).
  - Hàng 1 Idle x4 | Hàng 2 Đánh: lấy đà, lao, đấm lửa, thu | Hàng 3 Chiêu: tụ lửa, gầm, sóng lửa, kết | Hàng 4 Đỡ, Bị đánh, Gục, Thắng | Hàng 5 Ăn, Vui, Buồn/đói, Ốm | Hàng 6 Ngủ x2, Thức x2.
  - Lỗi đã biết: sóng lửa (hàng 3 cột 3) tràn sang cột 4; nhân vật hơi mập hơn dạng Trưởng thành trong dòng tiến hóa.
- `hoa-ho-truong-thanh-24-khung-xem-truoc.png` — bảng xem trước có nhãn.
- `tinh-linh-ngu-hanh-tong-hop.png` — tổng hợp 31 tinh linh: dòng tiến hóa 5 khung (Trứng→Con→Nhi→Thiếu niên→Trưởng thành) + dạng huyền thoại.

## Thiết kế
- 5 hệ Ngũ hành: Kim, Mộc, Thủy, Hỏa, Thổ. Tương khắc (đấu, x1.5 / x0.75): Kim>Mộc>Thổ>Thủy>Hỏa>Kim. Tương sinh (nuôi): Kim→Thủy→Mộc→Hỏa→Thổ→Kim.
- Thức ăn quyết định hệ; bài tập quyết định lối đánh (Sức mạnh / Kiên trì / Nhanh nhẹn); cách nuôi quyết định nhánh (Thú hồn / Nguyên tố).
- Mỗi con: Trứng, Con, Nhi, Thiếu niên, Trưởng thành + 1 dạng Huyền thoại.
- Đấu: 3 nút đồng thời — Tấn công > Chiêu đặc biệt > Đỡ > Tấn công. Chế độ LAN 1-1, mặc định "Công bằng".

## Danh sách 31 con
Hỏa: Hỏa Hổ, Hỏa Quy, Hỏa Hồ (Thú hồn) | Viêm Long, Dung Nham Vệ, Hỏa Linh (Nguyên tố)
Kim: Kim Tê, Kim Giáp, Kim Ưng | Tinh Kim Hiệp, Kim Thạch Nhân, Liêm Đao
Mộc: Mộc Hùng, Mộc Lộc, Mộc Đường | Thụ Nhân, Rêu Linh, Diệp Linh | ẩn: Mộc Trư
Thủy: Thủy Sa, Thủy Giải, Thủy Long | Thủy Chiến, Bào Thủy, Thủy Giao
Thổ: Thổ Ngưu, Thổ Tượng, Thổ Tích | Thạch Nhân, Thành Trì, Thổ Long
(Thứ tự trong mỗi nhánh: Sức mạnh, Kiên trì, Nhanh nhẹn.)

Ảnh gốc độ phân giải cao của từng con nằm trong cuộc trò chuyện ChatGPT "Pixel Art Sprite Generation".

## Sprite sheet 4x6 – 30 con còn lại (2026-10-23)
File `<MÃ>_<slug>.png`, 1024x1536, nền magenta #FF00FF (chưa tách nền), bố cục giống Hỏa Hổ:
hàng 1 Idle x4 · 2 Attack x4 · 3 Special x4 · 4 Guard/Hurt/KO/Victory · 5 Eat/Happy/Sad/Sick · 6 Sleep x2 + Wake x2.
Mã: HO = Hỏa, KI = Kim, MO = Mộc, TH = Thủy, TO = Thổ.
- HO-N1_viem-long.png
- HO-N2_dung-nham-ve.png
- HO-N3_hoa-linh.png
- HO-T2_hoa-quy.png
- HO-T3_hoa-ho-cao.png
- KI-N1_tinh-kim-hiep.png
- KI-N2_kim-thach-nhan.png
- KI-N3_liem-dao.png
- KI-T1_kim-te.png
- KI-T2_kim-giap.png
- KI-T3_kim-ung.png
- MO-N1_thu-nhan.png
- MO-N2_reu-linh.png
- MO-N3_diep-linh.png
- MO-T1_moc-hung.png
- MO-T2_moc-loc.png
- MO-T3_moc-duong.png
- MO-X_moc-tru.png
- TH-N1_thuy-chien.png
- TH-N2_bao-thuy.png
- TH-N3_thuy-giao.png
- TH-T1_thuy-sa.png
- TH-T2_thuy-giai.png
- TH-T3_thuy-long.png
- TO-N1_thach-nhan.png
- TO-N2_thanh-tri.png
- TO-N3_tho-long.png
- TO-T1_tho-nguu.png
- TO-T2_tho-tuong.png
- TO-T3_tho-tich.png

## Sprite sheet giai đoạn nhỏ – 31 con x 4 (2026-10-23)
File `<MÃ>_<slug>_<egg|baby|child|teen>.png`, nền magenta #FF00FF (chưa tách nền). Kích thước phần lớn 1254x1254, vài bảng lệch (1774x887, 1536x1024...) – khi cắt phải dò lưới theo nền magenta, không cắt cứng.
- egg: 4x2 – hàng 1 rung/nhịp sáng x4; hàng 2 nứt nhỏ, nứt lớn, nở, vỏ trống
- baby/child/teen: 4x4 – hàng 1 idle x4; hàng 2 đi x4; hàng 3 ăn/vui/buồn/ốm; hàng 4 ngủ x2 + thức dậy x2
Ảnh soát: `_soat/soat-giai-doan.png`.

## Sprite sheet Huyền thoại – 31 con (2026-10-23)
File `<MÃ>_<slug>_legend.png`, lưới 4x6 giống dạng Trưởng thành, nền magenta, kích thước không đồng đều (1024x1536, ~1230x1278, vài bảng ngang) → cắt theo dò lưới magenta.
Cần soát kỹ: TH-N3_thuy-giao_legend có thể lệch lưới (bảng ngang).
Ảnh soát: `_soat/soat-huyen-thoai.png`.

## Dáng 4 chân (chốt 2026-10-23)
Thư mục `4-chan/`: `<MÃ>_<slug>_4chan_<adult|legend>.png`, lưới 4x6 (idle, đi, chạy/lao, đòn hệ+bị đánh+ngã+thắng, ăn/vui/buồn/ốm, ngủ+thức), nền magenta.
13 con có dáng 4 chân: Hỏa Hổ, Hỏa Quy, Hỏa Hồ, Viêm Long, Kim Tê, Kim Giáp, Mộc Hùng, Mộc Lộc, Mộc Trư, Thổ Ngưu, Thổ Tượng, Thổ Tích, Thổ Long.
**Cơ chế: ĐỘ THUẦN HÓA thấp → pet đi 4 chân (hoang dã). Thuần hóa cao → đứng 2 chân (dùng bảng 2 chân hiện có).**
Các con còn lại (chim, cá, cua, bọ, rắn, tinh linh) luôn dùng bảng 2 chân / dạng gốc.
