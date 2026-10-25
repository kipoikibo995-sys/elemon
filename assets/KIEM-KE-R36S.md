# Kiểm kê bộ hình R36S (`build/r36s/`)

Tự ghi lại mỗi lần chạy `python scripts/r36s_pak.py` (hoặc `HOLUA_SCREEN=640 python scripts/build_assets.py`). Định dạng: đầu `scripts/r36s_pak.py`. Màn 640×480, PNG có viền mịn (trộn trong suốt bằng GPU). Chỉ chép `build/r36s/` vào gói PortMaster.

**Tổng: 59.2 MB trong 230 bộ.**

| Nhóm | Số bộ | Dung lượng | Nhỏ nhất – lớn nhất |
| --- | ---: | ---: | ---: |
| Pet | 212 | 49.84 MB | 18 – 698 KB |
| Phòng (nền + đồ) | 17 | 8.93 MB | 464 – 666 KB |
| Đồ ăn | 1 | 0.44 MB | 451 – 451 KB |

Atlas pet và đồ phòng lưu PNG 8-bit (256 màu, mỗi màu có độ trong riêng nên vẫn giữ viền mịn): 229/229 atlas, sai màu trung bình (kênh lệch nhất) 7.7, lớn nhất 14.5 (`phong/L4-MO`). Atlas nào sai quá 16 giữ đủ màu. Nền phòng và đồ ăn luôn đủ màu. Chạy `r36s_pak.py --rgba --all` để giữ mọi atlas đủ màu (to gấp khoảng 4 lần).

## Pet theo cấp

| Cấp | Số bộ | Dung lượng | Trung bình | Lớn nhất |
| --- | ---: | ---: | ---: | ---: |
| Trứng (`egg`) | 31 | 0.83 MB | 27 KB | 34 KB (kim-ung) |
| Con (`baby`) | 31 | 1.97 MB | 65 KB | 114 KB (hoa-ho) |
| Nhi (`child`) | 31 | 2.98 MB | 98 KB | 205 KB (hoa-ho) |
| Thiếu niên (`teen`) | 31 | 4.95 MB | 164 KB | 215 KB (tho-long) |
| Trưởng thành (`adult`) | 31 | 12.56 MB | 415 KB | 522 KB (moc-tru) |
| Huyền thoại (`legend`) | 31 | 16.88 MB | 558 KB | 698 KB (bao-thuy) |
| Trưởng thành 4 chân (`adult4`) | 13 | 4.49 MB | 354 KB | 459 KB (kim-te) |
| Huyền thoại 4 chân (`legend4`) | 13 | 5.18 MB | 408 KB | 489 KB (tho-nguu) |

## Phòng

| Phòng | Số đồ | Nền | Cả phòng |
| --- | ---: | ---: | ---: |
| L1-HO_hang-da | 16 | 434 KB | 490 KB |
| L1-HO_nha-hoang | 12 | 468 KB | 522 KB |
| L2-HO | 12 | 471 KB | 506 KB |
| L2-KI | 12 | 424 KB | 471 KB |
| L2-MO | 12 | 497 KB | 551 KB |
| L2-TH | 12 | 451 KB | 503 KB |
| L2-TO | 12 | 486 KB | 539 KB |
| L3-HO | 12 | 472 KB | 518 KB |
| L3-KI | 12 | 481 KB | 539 KB |
| L3-MO | 12 | 459 KB | 531 KB |
| L3-TH | 12 | 430 KB | 501 KB |
| L3-TO | 12 | 412 KB | 464 KB |
| L4-HO | 12 | 483 KB | 555 KB |
| L4-KI | 12 | 490 KB | 568 KB |
| L4-MO | 12 | 560 KB | 632 KB |
| L4-TH | 12 | 588 KB | 666 KB |
| L4-TO | 12 | 511 KB | 587 KB |

## RAM khi chạy

Ảnh PNG được giải nén lúc nạp: một cảnh cần nền 640×480×4 = 1,2 MB, atlas đồ của phòng và atlas pet (mỗi điểm 4 byte), cộng bộ đệm màn. Trên R36S (RAM 1 GB) chừng này không đáng kể; vẫn giữ luật "mỗi màn chỉ nạp thứ cần" để khớp bản PocketGo.
