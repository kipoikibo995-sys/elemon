# Giao diện (HoLua) – phong cách cổ phong Ngũ hành (gỗ sơn mài, viền đồng, mây)
- `goc/`  : bản gốc độ phân giải cao (nguồn để chỉnh / xuất lại).
- `r36s/` : bản đã thu nhỏ đúng cỡ màn 640x480 + giảm bảng màu (≤32–48 màu/ảnh, làm tròn về mức RGB565 của R36S). Dùng thẳng trong game. Kích thước: `kich-thuoc-r36s.json`.
- `_bang/`: 6 bảng gốc từ AI.

## Danh sách
- khung_panel (dùng 9-slice: góc ~12px), khung_vach-chia, tab_thuong / tab_chon / tab_cham-do, nut_L/R/A/B
- thanh_khung + thanh_fill_<màu> (cam, hong, xanh-duong, xanh-reu, do, vang, tim, ngoc): game cắt fill theo % rồi vẽ lên trong khung.
- icon_* (24px): no, vui, sach, nang-luong, suc-khoe, suc-manh, nhanh-nhen, ben-bi, thong-minh, tri-tue, tinh-than, tim-day/nua/rong, tien, nha
- linh-khi_ngu-giac (nền radar, code vẽ đa giác chỉ số đè lên) + he_hoa/kim/moc/thuy/tho
- tinh-cach_* (8 loại), the-trang_thanh + the-trang_kim, level_huy-hieu (Hồ sơ chỉ hiện LEVEL, bỏ hàng giai đoạn tiến hóa), the-thong-tin
- be-dung_<hệ> (bệ đứng pet theo hệ, trung-tinh)
Chữ: dùng font pixel có dấu tiếng Việt (chưa chọn).

## Đợt 2 (2026-10-24) – bảng gốc trong `_bang/`
- HUD1_menu: 8 nút hành động (Cho ăn, Dọn dẹp, Chơi, Tập luyện, Ngủ/Tắt đèn, Cửa hàng, Trang trí, Ra ngoài) + ô trống, ô đang chọn, thanh HUD trên, ô tiền, huy hiệu level.
- HUD2_cam-xuc: bong bóng trống, đói, buồn, ốm, buồn ngủ, vui, giận, tim.
- HUD3_cham-soc: phân 3 cỡ, vết bẩn 2, ruồi 3 frame, bọt xà phòng, đầu lâu, bình thuốc, viên thuốc, chữ Z 3 cỡ, tim bay 3 cỡ, lấp lánh, giọt mồ hôi, vụn đồ ăn.
- SHOP1_cua-hang: ô đồ (thường/chọn/khóa), nhãn giá, nút Mua (xanh ngọc)/Bán (đỏ), mũi tên, bảng mô tả, 4 tab danh mục, chủ quán gấu mèo.
- DEC1_trang-tri: ô sàn xanh (đặt được) / đỏ (không) / vàng (đang chọn), icon xoay, di chuyển, cất kho, xác nhận, hủy, bật lưới.
- EVO1_nen (nền màn tiến hóa riêng), EVO2_xoay (vòng xoáy 5 hệ x 4 frame), EVO3_bung-sang (8 frame nổ sáng/cột sáng/sóng), EVO4_banner (băng rôn rồng + 8 hạt hiệu ứng), EVO5_no-trung (8 frame nở trứng).
Mẫu: man-hinh-mau/thu-phong-nuoi-hud.png, tien-hoa.gif (kịch bản tiến hóa ~6s, script evo.py), tien-hoa-6-buoc.png.
