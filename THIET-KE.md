# Thiết kế cơ chế nuôi — Tinh Linh Ngũ Hành

Ghi lại theo yêu cầu (2026-10-23), dùng khi làm phần game chạy. Số liệu cụ thể (tốc độ giảm, mức hồi) chưa chốt.

Liên quan:
- `assets/source/tinh-linh/README.md`: 31 tinh linh, tương sinh / tương khắc, nhánh Thú hồn / Nguyên tố.
- `assets/source/nen/README.md`: 4 cấp nhà và cộng chỉ số theo hệ.

## 1. Chỉ số sinh tồn

| Chỉ số | Giảm khi nào | Hồi bằng |
| --- | --- | --- |
| No | *(chưa ghi)* | Cho ăn |
| Vui | *(chưa ghi)* | Chơi mini-game, vuốt ve |
| Sạch | Khi có phân trong chuồng | Dọn dẹp |
| Năng lượng | Giảm khi thức, hồi khi ngủ | Tắt đèn cho ngủ |
| Sức khỏe | Giảm khi chỉ số khác bằng 0 lâu | Thuốc |

## 2. Linh khí (0–100 mỗi hệ)

| Hệ | Ý nghĩa | Ảnh hưởng khi cao |
| --- | --- | --- |
| Kim | Cứng rắn, sắc bén | +Phòng thủ, đói chậm hơn |
| Mộc | Sinh trưởng, hồi phục | Tự hồi Sức khỏe, ít ốm |
| Thủy | Mềm dẻo, thông minh | Mini-game dễ hơn, vui lâu hơn |
| Hỏa | Nhiệt huyết, bùng nổ | +Tấn công, nhưng đói nhanh hơn |
| Thổ | Vững chãi, kiên nhẫn | Tăng cân chậm, ngủ hồi năng lượng nhanh |

## 3. Thức ăn gắn với hệ

| Món | Hệ | Tác dụng |
| --- | --- | --- |
| Quặng ngọt | Kim +3 | No ít |
| Lá non | Mộc +3 | Hồi sức khỏe nhẹ |
| Cá suối | Thủy +3 | +Vui |
| Ớt lửa | Hỏa +3 | +Năng lượng |
| Khoai đất | Thổ +3 | No nhiều, tăng cân |
| Cơm thường | Không hệ | Chỉ hồi No |

## 4. Sáu thuộc tính

| Thuộc tính | Lúc nuôi | Lúc chiến đấu (sau này) |
| --- | --- | --- |
| Sức mạnh | Ăn nhiều hơn mới no | Sát thương đòn thường |
| Nhanh nhẹn | Hay chạy nhảy, vui nhanh khi chơi | Đánh trước, né đòn |
| Bền bỉ | Ít ốm, đói lâu | Máu (HP), chịu đòn |
| Thông minh | Học trò chơi nhanh, hiểu lệnh | Sức mạnh kỹ năng hệ |
| Trí tuệ | Tự đi vệ sinh đúng chỗ, ít quậy | Năng lượng kỹ năng, kháng hệ |
| Tinh thần | Ít buồn, ít giận dỗi khi bị bỏ bê | Chống trạng thái xấu, đánh chí mạng |

### Liên kết với Ngũ Hành

Mỗi hệ nuôi 2 thuộc tính, nên ăn món hệ nào sẽ thiên về kiểu thú đó.

| Hệ | Tăng thuộc tính | Hình mẫu thú |
| --- | --- | --- |
| Kim | Sức mạnh + Bền bỉ | Chiến binh giáp sắt |
| Mộc | Bền bỉ + Tinh thần | Hồi phục, dai dẳng |
| Thủy | Thông minh + Trí tuệ | Pháp sư |
| Hỏa | Sức mạnh + Nhanh nhẹn | Sát thủ bùng nổ |
| Thổ | Bền bỉ + Trí tuệ | Thủ vững, phản đòn |

### Dáng đi 4 chân (chốt 24/10/2026)

13 con có dáng 4 chân (Hỏa Hổ, Hỏa Quy, Hỏa Hồ, Viêm Long, Kim Tê, Kim Giáp, Mộc Hùng, Mộc Lộc, Mộc Trư, Thổ Ngưu, Thổ Tượng, Thổ Tích, Thổ Long).

- **Thông minh và Trí tuệ giảm (thấp) → pet đi bằng 4 chân** (dáng hoang dã, bảng `adult4` / `legend4`).
- Thông minh và Trí tuệ cao → đứng 2 chân (bảng `adult` / `legend` thường).
- Ngưỡng cụ thể (ví dụ trung bình 2 chỉ số dưới bao nhiêu thì đổi dáng) chưa chốt.
- `tinh-linh/README.md` đang ghi "độ thuần hóa thấp → 4 chân": hiểu độ thuần hóa chính là Thông minh + Trí tuệ.
- 18 con còn lại (chim, cá, cua, bọ, rắn, tinh linh) luôn dùng dáng gốc.

## 5. Giai đoạn và cấp độ (chốt 24/10/2026)

| Giai đoạn | Level | Điều kiện để lên cấp tiếp | Thời gian (ước tính) |
| --- | --- | --- | --- |
| Trứng | không có | Ấp 30 phút đến 1 giờ | Buổi đầu |
| Con | 1 → 5 | Lv 5 | ~1 ngày |
| Nhi | 6 → 20 | Lv 20 + một hệ Linh khí ≥ 30 | 3–4 ngày |
| Thiếu niên | 21 → 45 | Lv 45 + Linh khí chủ đạo ≥ 60 | 1–2 tuần |
| Trưởng thành | 46 → 99 | Lv 99 + đủ 5 tim + nhà cấp 4 + Hồn lửa xanh | 1–2 tháng |
| Huyền thoại | 100 → 150 | Trần cuối | Lâu dài |

Ghi chú để khớp với phần khác:
- **Linh khí chủ đạo:** hiểu là hệ có Linh khí cao nhất. Màn Linh khí có dòng "Vòng nét đứt = ngưỡng tiến hóa": vòng này nên vẽ ở 30 (lên Nhi) hoặc 60 (lên Thiếu niên) tùy giai đoạn hiện tại.
- **5 tim:** là mục Thân thiết ở trang Hồ sơ (đang hiện 5 ô tim).
- **Nhà cấp 4:** Lv4 trong `nen/README.md` (Đền Hỏa Long, Điện Kim Cương, Cây Thần, Thủy Cung, Thạch Điện), mở bằng Ngọc Hồn từ boss.
- **Hồn lửa xanh:** vật phẩm mới, chưa có hình và chưa ghi lấy ở đâu (rơi từ boss? sự kiện?).
- Hỏa Hổ "Bông" ở màn chỉ số mẫu đang Level 12 nhưng ghi Thiếu niên. Theo bảng này Lv 12 là **Nhi**, cần sửa dữ liệu mẫu khi làm game.
- Đường kinh nghiệm (EXP mỗi level) chưa chốt. Cần tính sao cho khớp thời gian ước tính ở cột cuối.

## Nền tảng (chốt 24/10/2026)

Một bộ code, hai bản dựng, hai bộ hình làm từ cùng ảnh gốc:

| | PocketGo V1 | R36S và Anbernic H700 (RG35XX Plus/H/SP, RG40XX…) |
| --- | --- | --- |
| Màn | 320×240 | 640×480 |
| Máy | ARM926, RAM 32 MB, uClibc | 4 nhân ARM64, RAM 1 GB, glibc |
| Thư viện | SDL 1.2, không trộn trong suốt | SDL2 có GPU, trộn trong suốt được |
| Bộ hình | gói 320 (`.pak` 8-bit, đã thử) | gói 640 (pet cắt lại cỡ gấp đôi, viền mịn, chữ khử răng cưa) |
| Wi-Fi | không có | RG35XX Plus/H/SP, RG40XX… có sẵn; R36S cần USB Wi-Fi |
| Phát hành | thư mục `apps/holua` + mục menu gmenu2x | gói PortMaster |

- Phần luật nuôi (chỉ số, thức ăn, tiến hóa, lưu game) viết chung, không phụ thuộc máy.
- Mỗi máy chỉ khác lớp vẽ màn hình, đọc nút và đọc giờ.
- Mọi tính năng mạng (đấu LAN 1-1, lấy giờ chuẩn, trao đổi pet) đều là phần thêm: bản PocketGo và máy không có Wi-Fi tự ẩn các mục đó, game vẫn chơi đủ.
- Đồng hồ: lưu mốc giờ trong file save; nếu thấy đồng hồ máy lùi thì không trừ chỉ số vô lý.

**Thứ tự làm (chốt 24/10/2026): R36S trước, sau đó chuyển sang PocketGo V1.** Để lúc chuyển không phải làm lại, ngay từ đầu giữ các ràng buộc của PocketGo:
- Thông tin quan trọng không được chỉ dựa vào hiệu ứng trong suốt (bản PocketGo sẽ không có).
- Mỗi màn chỉ nạp những gì cần, ước lượng được bộ nhớ cho bản 320 (máy có 32 MB).
- Bộ hình 320 dựng song song với bộ 640, từ cùng ảnh gốc.
- Có lệnh dựng thử bản PocketGo (giả lập trên PC như `make sim`) để kiểm tra định kỳ, không đợi tới cuối.

**Bộ hình R36S (dựng 24/10/2026):** `HOLUA_SCREEN=640 python scripts/build_assets.py` (cắt pet cỡ gấp đôi vào `assets/creatures-640/`, giữ viền mịn, không có BMP) rồi `scripts/r36s_pak.py` gói vào `build/r36s/`: mỗi bộ pet / đồ phòng / đồ ăn là 1 atlas PNG + 1 file chỉ mục `.txt`, nền phòng PNG 640×480. Atlas pet và đồ phòng lưu PNG 8-bit có độ trong theo từng màu (nhỏ còn ~1/4, nhìn không khác); nền và đồ ăn đủ màu. Tổng 53,4 MB (pet 44 MB), bảng ở `assets/KIEM-KE-R36S.md`. `anims.json` chỉ có một bản (đơn vị 320, trong `assets/creatures/`); bản 640 nhân x/y/br với 2 lúc vẽ. Khung đi/chạy không căn nối tiếp nữa (trước bị lệch dồn tới 7 px), để theo đường tâm lúc cắt. Ảnh thử: `preview/r36s/` (`scripts/preview_r36s.py`).

## Tối ưu để chạy trên PocketGo (bắt buộc khi làm game)

Máy PocketGo yếu (Allwinner F1C100S: ARM926 khoảng 500–700 MHz, RAM 32 MB, màn 320×240 16-bit), nên asset hiện tại **quá nặng để chép nguyên**:

| Đo ngày 24/10/2026 | Dung lượng |
| --- | --- |
| Toàn bộ `assets/creatures/` (png + bmp + bmp chớp trắng) | 348 MB |
| Riêng BMP 24-bit | 142 MB (+142 MB bản chớp trắng) |
| 3.848 khung, đổi sang 16-bit RGB565 | ~93 MB |
| …cắt sát khung hình (bỏ phần trong suốt) | ~57 MB |
| …thêm bảng màu 8-bit cho mỗi bộ | ~29 MB |

Cách làm khi port:
1. **Không đưa PNG và bản xem trước lên máy**, chỉ đưa dữ liệu game.
2. **Bỏ file chớp trắng:** tô trắng lúc vẽ bằng code (cộng màu), không lưu ảnh riêng.
3. **Cắt sát từng khung** và lưu kèm độ lệch, thay vì mọi khung cùng cỡ canvas.
4. **Màu 8-bit có bảng màu riêng cho mỗi bộ** (khoảng 64–128 màu, pixel art nhìn không khác), nén RLE cho vùng trong suốt. Có thể gói mỗi con/cấp thành 1 file `.pak`.
5. **Chỉ nạp vào RAM bộ khung của pet đang nuôi ở cấp hiện tại** (khoảng 16–24 khung, vài trăm KB), nạp bộ khác khi tiến hóa hoặc đổi dáng. Không nạp cả 212 bộ.
6. Nền 1448×1086 thu sẵn về 320×240 lúc dựng, không thu nhỏ trên máy. Đồ trang trí cũng thu sẵn về cỡ màn.
7. Ảnh động xem trước (`preview/`) chỉ dùng trên PC, không chép vào thẻ.

**Đã thử (24/10/2026):** `scripts/pocketgo_pak.py` đóng gói theo cách trên (pet 128 màu, cắt sát, nén RLE; phòng là nền RGB565 nén + đồ dùng chung 192 màu, cỡ màn sẵn). Kết quả:
- Cả 212 bộ pet: **18,9 MB** (thay vì 348 MB), mỗi bộ 7–209 KB.
- Một cảnh Hang đá đủ đồ + Hỏa Hổ 4 chân cần khoảng **530 KB RAM** (phòng 234 KB + pet 149 KB + bộ đệm màn 150 KB).
- `scripts/preview_pocketgo.py` dựng cảnh chỉ từ file đã đóng gói. So với bản gốc nhìn gần như không khác (`preview/pocketgo/so-sanh.png`).
- Mép mờ của đồ (alpha < 160) bị bỏ vì máy không trộn trong suốt, nếu không sẽ thành viền tím.

**Bước dựng chính thức (24/10/2026):** `python scripts/build_assets.py --pak-only` (hoặc `python scripts/pocketgo_pak.py`; `build_assets.py` đầy đủ cũng chạy bước này cuối cùng) ra toàn bộ `build/pak/`: `pet/` (212 bộ), `phong/` (17 phòng, nền + đồ), `do-an.pak` (48 món, icon 32 px + miếng trong bát 14 px), `danh-sach.json` (danh sách + công thức tô màu đêm). Bảng dung lượng tự ghi vào `assets/KIEM-KE-PAK.md`. Lên 255 màu cho mọi bộ (không tốn thêm byte), RLE thêm mã "lặp 1 màu", nền phòng còn ~130 KB. Đêm không lưu ảnh riêng: tô màu lúc nạp phòng, lửa/đèn giữ sáng. Vị trí đồ mặc định của các phòng (trừ Hang đá, Lò rèn đã ghép tay) đặt theo ô cố định trong `scripts/place_decor.py`, người chơi tự dời sau. Ảnh thử: `preview/pocketgo/`.

## Màn phòng nuôi (chốt 24/10/2026)

- **Menu 5 nút:** Ăn, Dọn, Vệ sinh, Ngủ/Đèn, Ra ngoài. **Tập luyện** chuyển sang **Võ đường** trên bản đồ (chốt 24/10/2026).
- **Vệ sinh** (thêm 24/10/2026): mở bảng gồm **Tắm** (xà phòng, sang cảnh nhà tắm `nen/nha-tam/NT_L1..4`, cấp nhà tắm theo cấp nhà) và **Uống thuốc**. Túi Ăn chỉ còn đồ ăn và đồ chơi.
- **Chơi với pet:** bấm nút **R2** (không có icon trên menu).
- **Cửa hàng** nằm trong bản đồ làng (vào bằng Ra ngoài), không phải nút trong phòng.
- **Trang trí phòng:** bấm nút **Start**.
- **Màn chỉ số:** bấm **Select**; L1/R1 đổi trang; B quay lại.
- **Thuốc:** nằm trong túi đồ (Ăn) và mục Thuốc của cửa hàng, không có nút riêng.
- Pet có **viền tối 2 px** (màu `#1a0c06`, chốt 24/10/2026) để không chìm vào nền cùng màu.
- Khi mở bảng (chọn món, tiến hóa…), phòng tối đi khoảng 18%.
- Bảng chọn món **thế chỗ thanh menu** (không chồng lên); B để quay lại.
- Bản chạy thử: `preview/tien-hoa/` (dựng bằng `scripts/build_evo_app.py`).
- **Chợ → mục Nhà** (24/10/2026): bán nhà Lv2–Lv4 của **cả 5 hệ**, không bắt buộc theo hệ pet. Mua đủ đồ của một nhà ở cấp cao nhất đang có thì mở được mọi nhà cấp kế tiếp; Lv4 cần thêm 1 Ngọc Hồn. Nhà đã mua được giữ lại, dọn qua lại miễn phí.

## Đặc tính đồ trang trí (ghi theo yêu cầu 24/10/2026, số liệu chưa chốt)

Đồ trong phòng không chỉ để nhìn. Mỗi món thuộc một **nhóm công dụng**, đặt trong phòng thì có tác dụng, thiếu thì pet chịu thiệt. Nhóm được nhận ra qua tên file đồ (`do-theo-phong/<phòng>/NN_<tên>.png`), nên cả 16 phòng dùng chung một luật.

| Nhóm | Đồ thuộc nhóm (từ khóa tên file) | Có trong phòng | Không có |
| --- | --- | --- | --- |
| **Giường** | bed, cot, hammock, o-rom, chieu, mat-bed | Ngủ hồi Năng lượng nhanh (×1,5), ngủ ngon, sáng dậy Vui + | Ngủ nằm đất: hồi chậm (×0,5), phải ngủ lâu hơn, dậy hay cáu |
| **Bát ăn** | food-bowl, bat-da | Ăn gọn, ít vụn, No hồi đủ | Ăn dưới đất: rơi vãi, phòng bẩn nhanh hơn, No hồi ít hơn |
| **Chỗ đi vệ sinh** | *chưa có hình*: cần vẽ thêm khay cát / bô / góc rơm cho mỗi phòng | Pet đi đúng chỗ, phân ít và tự gom vào đó, Sạch giảm chậm | Phân bậy khắp nhà, liên tục, kéo ruồi; bẩn lâu dễ ốm |
| **Thảm, chiếu** | rug, carpet, tham, chieu-nho | Sàn khó bẩn: Sạch giảm chậm hơn | Bẩn nhanh hơn |
| **Đèn, lò, lửa** | lamp, lantern, brazier, furnace, duoc, bep, oven | Phòng ấm sáng: Vui giảm chậm, ít ốm | Phòng lạnh tối: dễ buồn, dễ ốm hơn |
| **Đồ tập** | training-dummy, golem, pillar, hinh-nom, weapon-rack | Tập tại nhà được (EXP nhỏ), tập ở Võ đường thêm % | Chỉ tập được ở Võ đường |
| **Cây, hoa, cảnh** | plant, pot, fern, flower, bonsai, duong-xi | Vui giảm chậm, thư giãn | — |
| **Đồ chứa** | chest, crate, shelf, barrel, basket, thung | Túi đồ rộng hơn (thêm ô) | Túi đồ ít ô |
| **Ngai, tượng, cờ** | throne, statue, banner, altar | Cộng chỉ số chính của hệ phòng (theo cấp nhà) | — |

Gợi ý cách tính: mỗi nhóm có hoặc không (không cộng dồn khi có 2 món cùng nhóm), nhà cấp cao thì món cùng nhóm mạnh hơn (Lv1 ×1, Lv4 ×2). Bộ đủ món vẫn là điều kiện mở nhà cấp sau.

Việc cần làm: vẽ thêm món **chỗ đi vệ sinh** cho 16 phòng (hiện chưa phòng nào có), rồi gắn các nhóm trên vào bản chạy thử.

## Điểm cần chốt khi làm game

- **No** và **Vui** chưa ghi giảm khi nào. Tạm hiểu là giảm dần theo thời gian (như Mimo).
- **Cân nặng** được nhắc tới (Khoai đất tăng cân, Thổ tăng cân chậm) nhưng chưa có trong bảng chỉ số.
- **Đã chốt (23/10/2026):** dùng bộ chỉ số trong file này (5 chỉ số sinh tồn + Linh khí 5 hệ + 6 thuộc tính). `nen/README.md` còn ghi chỉ số chính theo hệ là Công / Chí mạng-Ý chí / HP / Tốc / Thủ, cần đổi phần cộng chỉ số của nhà sang 6 thuộc tính (ví dụ nhà hệ Hỏa cộng Sức mạnh + Nhanh nhẹn, theo bảng Liên kết với Ngũ Hành).
- `tinh-linh/README.md` ghi "bài tập quyết định lối đánh (Sức mạnh / Kiên trì / Nhanh nhẹn)", còn ở đây thức ăn theo hệ cũng nuôi thuộc tính. Cần chốt cái nào quyết định nhánh tiến hóa.
