# Nền đấu trường (theo hệ)

Mỗi hệ một thư mục: `hoa/`, `thuy/`, `moc/`, `tho/`, `kim/`, và `chung/` cho sân không theo hệ.
Sau này bản đồ thế giới dùng lại cách chia này: mỗi vùng thuộc hệ nào thì đấu ở sân của hệ đó.

## Thêm một sân mới
1. Bỏ hình (png / webp / jpg, cỡ nào cũng được, tỉ lệ 4:3 hoặc dẹt 2:1) vào thư mục của hệ.
   Đặt tên ngắn không dấu, vd `hoa/nui-lua-dem.png`.
2. Chạy:

   ```bash
   python scripts/lam_san_dau.py
   ```

3. Mở `preview/dau-truong/ui/san/_xem.png` xem viền tím có khớp mép trong vòng đá không.

Script tự làm:
- cắt viền đen / trắng thừa;
- thu về 640×480 (hình dẹt được kéo cao thêm tối đa ×1.26);
- tìm sàn đánh (vòng đá) bằng cách loang màu từ giữa sân;
- đặt sàn kết thúc ngay trên hàng icon chiêu;
- xuất bản cho trang thử `preview/dau-truong/ui/san/<hệ>_<tên>.png`;
- xuất bản cho R36S `assets/r36s/dau-truong/<hệ>_<tên>.png` (màu RGB565, 64 màu, khoảng 110 KB);
- ghi danh sách + vòng đá vào `preview/dau-truong/ui/san/san.json`.

## Trận đấu chọn sân thế nào
- Có đối thủ (`&vs=`): bốc ngẫu nhiên một sân thuộc hệ của đối thủ.
- Không có đối thủ: sân `chung`.
- Chọn tay: `&san=hoa` (bốc trong hệ Hỏa) hoặc `&san=hoa_nui-lua` (đúng sân đó).

## Hình nên có
Sàn giữa phẳng, trống, không có vật cao trong vòng đá; vòng đá rõ; cảnh chỉ ở xung quanh.
Hình càng lớn càng nét (4 sân Hỏa / Thủy / Mộc / Thổ và Kim hiện tại lấy từ ảnh chụp nhỏ ~470×240 nên hơi mờ).
Prompt mẫu: xem phần "Prompt (tiếng Anh)" trong lịch sử trao đổi, hoặc nhờ Claude viết lại.

`_cu/`: các bản nền cũ. `_tho/`: ảnh chụp gốc trước khi cắt.
