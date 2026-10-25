# Thông số asset HoLua (R36S – màn 640x480, màu 16-bit RGB565)

File trong `assets/source/` là BẢN GỐC từ AI (thường 1448x1086 hoặc 1024x1536, PNG 24-bit, 2–4MB, nền magenta #FF00FF).
KHÔNG đưa thẳng vào máy. Chạy `python toi_uu_r36s.py` → sinh `assets/r36s/` (cùng cấu trúc thư mục) đã tối ưu.

| Nhóm (thư mục source) | Gốc | Bản R36S | Màu | Ghi chú |
|---|---|---|---|---|
| tinh-linh/ (pet, lưới 4x6/4x4/4x2) | ~1024–1448px | x0.5 (ô ~128px) | ≤64 | tách nền magenta → trong suốt |
| tinh-linh/4-chan/ | 1448x1086 | x0.5 | ≤64 | như trên |
| nen/phong-trong/, nen/khai-niem/, nen/nha-tam/ | 1448x1086 | 640x480 | ≤64 | nền đặc, không trong suốt |
| nen/ngoai-troi/ban-do-the-gioi | 1448x1086 | 640x480 | ≤64 | lớp vung/ (mask, khoa, chon) cũng 640x480 |
| do-theo-phong/ (đồ trang trí) | theo cảnh 1448 | x0.442 (khớp phòng 640x480) | ≤32 | trong suốt |
| do-an/ | ~150–250px | cao tối đa 32px | ≤32 | trong suốt |
| ui/r36s/ | – | ĐÃ TỐI ƯU sẵn | ≤32–48 | dùng luôn |
| ui/_bang/ (bảng gốc) | 1448x1086 | cắt từng món theo README ui | ≤32 | |
| trang-bi/ (ô đồ, ngọc, trang bị) | 1448x1086 | icon 32px, ngọc 24px | ≤32 | trong suốt |

Quy tắc chung:
- Thu nhỏ bằng LANCZOS rồi lượng tử hóa (không dither), làm tròn kênh màu về mức RGB565.
- Lưu PNG-8 (palette) có alpha 1-bit (ngưỡng 110) → mỗi file thường chỉ 5–60KB.
- Pixel art phóng to trong game: dùng NEAREST, không lọc mịn.
- Từ nay mỗi đợt asset mới: bản gốc vào `source/`, Claude chạy luôn bản `r36s/` kèm theo.
| ngoc/ (25 ngọc + ô gắn ngọc) | ~110-230px | icon ≤32px, _lon ≤48px; ô ngọc 40px | ≤32 | trong suốt |
| ui/no-trung/<he>/f1..f8 (nở trứng 5 hệ) | 443x443/frame | cao 120px | ≤32 | trong suốt, khung cố định mọi frame (không giật) |
| cham-soc/ (bát, chậu, khăn, đồ chơi, chổi, cảnh báo !) | theo bảng | đồ nhỏ ≤40px, chậu/chổi ≤64px | ≤32 | trong suốt |
| bieu-cam/ (12 biểu cảm trên đầu pet) | ~200px | ≤28px | ≤32 | trong suốt |
| cham-soc/do-tam/ (xà phòng, khăn, vịt, dầu gội × 4 level) | ~250px | ≤36px | ≤32 | trong suốt |
