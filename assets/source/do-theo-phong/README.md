# Đồ trang trí THEO PHÒNG (hướng A) – HoLua

Mỗi phòng có bộ đồ RIÊNG, tách từ chính cảnh khái niệm của phòng đó → đúng ánh sáng, đúng tông, đúng tỉ lệ.
**Đồ của phòng nào chỉ dùng trong phòng đó.** Người chơi mua / cất vào kho / đặt / dời lại tự do trong phòng.

## Thư mục
`<mã phòng>/NN_ten-mon.png` (PNG nền trong suốt). Mã phòng ↔ nền trống (`nen/phong-trong/`):
- L1-HO_hang-da ↔ PT_N0-1_hang-da · L1-HO_nha-hoang ↔ PT_N0-2_nha-hoang
- L2-HO/KI/MO/TH/TO ↔ PT_L2-*
- L3-HO/KI/MO/TH/TO ↔ PT_N1-* (Lò rèn, Xưởng kim loại, Chòi trên cây, Nhà sàn, Nhà đất nung)
- L4-HO/KI/MO/TH/TO ↔ PT_N2-* (Đền Hỏa Long, Điện Kim Cương, Cây Thần, Thủy Cung, Thạch Điện)
`catalog.json`: {room, file, level, he, name, w, h}.

## Tỉ lệ khi đặt
Đồ đã ở đúng tỉ lệ của phòng: đặt **nguyên cỡ (×1.0)** trên phòng 1448x1086 (≈ ×0.44 khi phòng thu về 640x480).
Không cần nhuộm màu / bóng thêm – ánh sáng đã khớp phòng. Neo đồ theo **đáy giữa** (chân đồ chạm sàn).
Gợi ý vị trí mặc định: xem ảnh khái niệm `nen/khai-niem/KN_*` (đồ đứng ở đâu trong cảnh thì đặt ở đó).

Ảnh thử ghép lại: `_thu-ghep_lo-ren.png`, `_thu-ghep_thuy-cung.png`.
Bảng gốc: `_bang/`. Kho đồ dùng chung cũ (bỏ, không dùng) ở `do-trang-tri/_cu-khong-dung/`.

## Luật nâng cấp phòng (chốt 2026-10-23)
Muốn nâng cấp lên phòng cấp kế tiếp → phải MUA ĐỦ toàn bộ đồ của phòng hiện tại (hoàn thành bộ sưu tập phòng).
- Lv1 → Lv2: mua đủ đồ Hang đá / Nhà hoang.
- Lv2 → Lv3, Lv3 → Lv4: mua đủ đồ của phòng hiện tại (Lv4 thêm điều kiện Ngọc Hồn từ boss).
- Gợi ý: hiện tiến độ "x/12 món" trong menu phòng; đồ đã mua giữ lại trong kho (có thể quay về phòng cũ trang trí lại).
- Đồ đã mua GIỮ LẠI trong kho: lên nhà mới vẫn quay về phòng cũ trang trí được (chốt).

## Phòng khác hệ & ĐIỂM HỆ (chốt 2026-10-23, thay luật tương sinh/khắc cũ)
- Người chơi TỰ CHỌN phòng muốn ở (Lv2–Lv4, hệ nào cũng được).
- Phòng luôn cộng CHỈ SỐ CHÍNH của hệ PHÒNG theo cấp (Hỏa→Công, Kim→Chí mạng/Ý chí, Mộc→HP, Thủy→Tốc, Thổ→Thủ).
- Mỗi pet có thanh ĐIỂM HỆ cho 5 hệ. Ở phòng khác hệ: điểm hệ của phòng tăng dần, điểm hệ gốc của pet giảm dần.
- Điểm hệ ảnh hưởng: (1) tiến hóa – hệ khác đủ cao → rẽ nhánh lai / con khác; (2) sức mạnh hệ gốc – điểm hệ gốc thấp → chiêu hệ gốc & bonus khắc hệ yếu đi.
- Quay về phòng đúng hệ thì điểm hệ gốc HỒI LẠI TỪ TỪ (chốt).
