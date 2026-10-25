# Kiểm kê file PocketGo (`build/pak/`)

Tự ghi lại mỗi lần chạy `python scripts/pocketgo_pak.py` (hoặc `python scripts/build_assets.py`). Định dạng file: đầu `scripts/pocketgo_pak.py`. Chỉ chép `build/pak/` lên máy, không chép PNG/BMP/preview.

**Tổng: 35.7 MB trong 230 file** (trước khi tối ưu: `assets/creatures/` 348 MB; bản thử đầu chỉ pet: 18,9 MB).

| Nhóm | Số file | Dung lượng | Nhỏ nhất – lớn nhất |
| --- | ---: | ---: | ---: |
| Pet (mọi con, mọi cấp) | 212 | 33.24 MB | 8 – 447 KB |
| Phòng (nền + đồ) | 17 | 2.46 MB | 133 – 167 KB |
| Đồ ăn | 1 | 0.04 MB | 41 – 41 KB |

## Pet theo cấp

| Cấp | Số bộ | Khung | Dung lượng | Trung bình | Lớn nhất |
| --- | ---: | ---: | ---: | ---: | ---: |
| Trứng (`egg`) | 31 | 248 | 0.33 MB | 11 KB | 13 KB (moc-tru) |
| Con (`baby`) | 31 | 1209 | 2.35 MB | 77 KB | 103 KB (thuy-giai) |
| Nhi (`child`) | 31 | 961 | 2.95 MB | 97 KB | 131 KB (thanh-tri) |
| Thiếu niên (`teen`) | 31 | 961 | 4.36 MB | 144 KB | 193 KB (tho-long) |
| Trưởng thành (`adult`) | 31 | 1580 | 10.94 MB | 361 KB | 447 KB (moc-tru) |
| Huyền thoại (`legend`) | 31 | 744 | 8.27 MB | 273 KB | 369 KB (viem-long) |
| Trưởng thành 4 chân (`adult4`) | 13 | 312 | 1.89 MB | 148 KB | 192 KB (kim-te) |
| Huyền thoại 4 chân (`legend4`) | 13 | 312 | 2.17 MB | 171 KB | 243 KB (tho-nguu) |

## Pet theo hệ

| Hệ | Số bộ | Dung lượng |
| --- | ---: | ---: |
| Hỏa | 44 | 6.58 MB |
| Kim | 40 | 6.01 MB |
| Mộc | 48 | 7.66 MB |
| Thủy | 36 | 5.53 MB |
| Thổ | 44 | 7.46 MB |

## Phòng

| Phòng | Số đồ | Nền | Cả file |
| --- | ---: | ---: | ---: |
| L1-HO_hang-da | 16 | 126 KB | 146 KB |
| L1-HO_nha-hoang | 12 | 131 KB | 150 KB |
| L2-HO | 12 | 129 KB | 145 KB |
| L2-KI | 12 | 115 KB | 133 KB |
| L2-MO | 12 | 129 KB | 147 KB |
| L2-TH | 12 | 123 KB | 139 KB |
| L2-TO | 12 | 124 KB | 143 KB |
| L3-HO | 12 | 128 KB | 145 KB |
| L3-KI | 12 | 122 KB | 143 KB |
| L3-MO | 12 | 127 KB | 151 KB |
| L3-TH | 12 | 124 KB | 148 KB |
| L3-TO | 12 | 114 KB | 134 KB |
| L4-HO | 12 | 131 KB | 157 KB |
| L4-KI | 12 | 136 KB | 160 KB |
| L4-MO | 12 | 134 KB | 159 KB |
| L4-TH | 12 | 142 KB | 167 KB |
| L4-TO | 12 | 130 KB | 157 KB |

## RAM khi chạy

Một cảnh = 1 file phòng + 1 file pet đang nuôi + bộ đệm màn 320×240×2 = 150 KB (vẽ thẳng từ dữ liệu RLE, không cần giải nén ra ảnh). Nặng nhất có thể: **764 KB** (phòng lớn nhất + pet lớn nhất) trên 32 MB RAM. Đồ ăn nạp thêm 41 KB khi mở menu. Đêm không cần file riêng: tô màu theo `night` trong `danh-sach.json` lúc nạp phòng.

## Đã thử giảm thêm (24/10/2026)

| Cách | Kết quả | Dùng? |
| --- | --- | --- |
| Bảng màu 128 → 255 màu | Mỗi điểm vẫn 1 byte, chỉ +254 byte/bộ; sai màu giảm ~15% (Hỏa Hổ 4 chân: 6,4 → 5,4) | **Có** |
| Mã thêm "lặp 1 màu" trong RLE | Bù hết phần tăng do nhiều màu hơn: pet 18,9 → 18,8 MB dù lên 255 màu | **Có** |
| Nền phòng: RGB565 nén theo gói (thay cho cặp số-màu) | Hang đá 240 → 146 KB cả file (cặp số-màu còn nặng hơn ảnh thô 150 KB) | **Có** |
| Ít màu hơn cho con nhỏ (32/64 màu) | Chỉ nhẹ đi 0–8% (Con: 34 → 31 KB), sai màu tăng 40–70% | Không |
| Bỏ khung trùng nhau | 3.848 khung, không có khung nào trùng sau khi đóng gói | Không cần |
| Nén zlib cả file pet | Chỉ −3,6% (RLE đã gần hết phần thừa), lại phải giải nén trên máy | Không |
| Nền phòng 256 màu thay RGB565 | Còn ~75 KB/nền, nhưng dễ loang màu trên nền vẽ tay; chưa thử, chỉ đáng làm nếu thiếu RAM | Chưa |

Thẻ nhớ không phải giới hạn (vài GB); thứ cần giữ nhỏ là RAM, mà một cảnh chỉ cần < 0,5 MB trên 32 MB.
