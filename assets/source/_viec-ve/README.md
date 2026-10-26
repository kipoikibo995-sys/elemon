# Việc vẽ cho Codex

Thư mục này chứa các đợt vẽ ảnh cho HoLua. Codex đọc một file đợt (`dot-*.md`), vẽ từng việc trong đó bằng công cụ
tạo ảnh, lưu đúng tên file, tối ưu, rồi đánh dấu xong. Phiên Claude vẽ frame soạn các đợt và duyệt ảnh; Codex chỉ vẽ.

## Cách làm một việc

1. Mở ảnh mẫu ghi ở mục **Ảnh mẫu** (đường dẫn tính từ `D:\INDIEGAME\HoLua`) và đính kèm khi tạo ảnh.
2. Tạo ảnh bằng đúng **Lời nhắc** (dán nguyên văn, tiếng Anh). Không thêm chữ, khung, bóng, sàn.
3. Lưu ảnh tạo ra vào `assets/source/_viec-ve/tai-ve/<ten-file>` (tên ở mục **Lưu thành**).
4. Tối ưu vào đích, chạy trong `D:\INDIEGAME\HoLua\scripts`:
   `python optimize_sheet.py ../assets/source/_viec-ve/tai-ve/<ten-file> <Đích>`
5. Đổi `- [ ]` của việc đó thành `- [x]` và ghi kích thước ảnh, ví dụ `- [x] (1536x1024)`.

## Luật chung (mọi việc)

- Nền phải là **magenta đặc #FF00FF** khắp ảnh. Ảnh ra nền trắng, nền chuyển màu, có bóng hay có sàn là hỏng: vẽ lại.
- Pixel art, nét viền tối, **màu đặc, không trong suốt, không glow mờ** (máy PocketGo không trộn màu được).
- Mỗi khung nằm gọn trong ô của nó, có khoảng magenta giữa các ô, không ô nào trống, không chạm mép ô.
- Giữ **đúng nhân vật trong ảnh mẫu**: dáng, màu, đồ, phụ kiện, cỡ. Không vẽ lại kiểu khác.
- Vẽ lần lượt trong **cùng một cuộc trò chuyện** cho cả đợt, không mở cuộc mới cho từng việc.
- Hết lượt tạo ảnh thì dừng, ghi `HẾT LƯỢT` dưới việc đang dở, không đổi sang công cụ khác.
- Không sửa file nào khác ngoài ảnh đích và dấu `[x]` trong file đợt.
