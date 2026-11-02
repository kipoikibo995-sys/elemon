# Elemon cho TrimUI Brick / Smart Pro chạy NX Redux

Elemon: nuôi tinh linh Ngũ Hành, cho ăn, tiến hóa, đi Vùng đất đánh boss, đấu Solo ở Đấu trường.

Gói này giống hệt bản Brick firmware gốc, chỉ khác chỗ để game: NX Redux mở app từ thư mục `Tools`.

## Cài

1. Tắt máy, rút thẻ nhớ cắm vào máy tính.
2. Giải nén gói này. Chép thư mục `Tools` vào gốc thẻ nhớ (gộp với thư mục `Tools` có sẵn).
   Xong sẽ có `Tools/Elemon.pak/` trên thẻ.
3. Bật máy, vào mục **Tools**, chọn **Elemon**.

## Cập nhật lên bản mới

Ngay trên máy (cần wifi): **Cài đặt → Cập nhật → A**. Game chỉ tải những file đã đổi, kiểm tra từng file, cài xong
tự mở lại. Bản mới không mở được thì game tự quay về bản cũ.

Hoặc cài tay: chép đè thư mục `Tools/Elemon.pak/` của bản mới lên bản cũ.

Bản lưu nằm riêng ở `Saves/elemon/` trên thẻ, cập nhật kiểu nào cũng không mất.

## Đấu wifi

Bật wifi trong cài đặt của NX Redux trước khi mở game. Máy NX Redux đấu chung phòng được với Brick, Smart Pro và
R36S khi cùng một bản Elemon.

## Phím

- D-pad: đi, chọn. A: đồng ý. B: quay lại.
- SELECT trong phòng: về màn chào. START trong phòng: Cài đặt.
- Thoát: nút **Thoát game** ở màn chào, hoặc giữ SELECT + START.

Nếu A và B bị ngược: mở `Tools/Elemon.pak/buttons.txt`, thêm `#` trước 4 dòng `A=b`, `B=a`, `X=y`, `Y=x`.

## Khi có lỗi

Gửi file `Tools/Elemon.pak/log.txt` cho tác giả.
