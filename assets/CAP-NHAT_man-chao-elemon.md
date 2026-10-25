# Cập nhật: Màn hình chào – tên game ELEMON (2026-10-24)

Tên game chốt: **Elemon** (thay "Tinh Linh Ngũ Hành"). Style màn chào mới: pastel dịu kiểu Digimon (bản B – đồi cỏ, Hỏa Hổ ôm trứng). Các màn khác GIỮ NGUYÊN UI cũ.

## File (R36S, dùng luôn)
- `assets/r36s/ui/man-hinh-chao/MAN_CHAO_ELEMON.png` – 640x480, nền + logo đã ghép sẵn (64 màu, ~80KB)
- `assets/r36s/ui/man-hinh-chao/TITLE_B_nen.png` – chỉ nền (không logo), 640x480
- `assets/r36s/ui/man-hinh-chao/LOGO_ELEMON.png` – logo riêng, nền trong suốt, 292x68; đặt tại **x=174, y=49** trên màn 640x480
- Bản gốc: `assets/source/ui/man-hinh-chao/` (TITLE_B_nen.png, LOGO_ELEMON.png, LOGO_A/B.png)

## Nút (chữ do code vẽ, hình nút đã có sẵn trong nền)
- Nút trên (màu đào): "Chơi mới" – tâm khoảng (320, 384)
- Nút dưới (xanh bạc hà): "Tiếp tục" – tâm khoảng (320, 425)
- Gợi ý màu chữ: nâu (110,70,40) trên nút đào; xanh lá đậm (50,100,60) trên nút bạc hà
- Nút đang chọn: làm sáng nút / thêm con trỏ bên trái (chưa có asset con trỏ riêng)

## Thay thế
- Bỏ `ui/_bang/TITLE1_nen.png` + `TITLE2_logo.png` (bản đỏ vàng cũ) khỏi màn chào.

# Cập nhật: Khung "Chào đời" (màn nở trứng) – 2026-10-24
- Thay khung rồng vàng cũ bằng `assets/r36s/ui/khung_chao-doi_go.png` (bảng gỗ treo dây, 440x126, trong suốt).
- Đặt tại **x=100, y=0** trên màn 640x480 (dây thừng chạm mép trên).
- Vùng chữ (tính từ góc trái-trên khung): (34,76) → (407,113). Code vẽ "CHÀO ĐỜI!" ở giữa, màu nâu đậm (110,55,25), viền kem (255,226,170).
- Ảnh mẫu: `assets/source/ui/man-hinh-mau/chao-doi_khung-go.png`.

# Asset mới khác (2026-10-24)
- Nở trứng 5 hệ: `r36s/ui/no-trung/<hoa|kim|moc|thuy|tho>/f1..f8.png` (cao 120px, khung cố định).
- Ngọc 25 viên: `r36s/ngoc/NGOC_<he>_<1-5>.png` (32px) + `_lon` (48px); ô gắn ngọc `r36s/ngoc/O_NGOC_*.png` (40px). Catalog: `source/ngoc/catalog.json`.
- Chăm sóc: `r36s/cham-soc/` – bát (đầy/vơi/hết/nước), chậu, khăn, xà phòng, đồ chơi, chổi 3 frame, bong bóng "!", icon trạng thái `tt_*` (đói, bẩn, buồn, ốm, buồn ngủ, chán, khát, vui), vết bẩn `ban_*` (phân, dấu chân, vụn, vũng nước, lông, bụi, sạch).
- Nhà tắm 4 level: `r36s/nen/nha-tam/NT_L1..L4.png` (640x480).
- Menu theo hệ: `source/ui/he/<kim|moc|thuy|tho>/` (hệ Hỏa dùng bộ gốc).

# Chốt màn "Chào đời" v2 (2026-10-24) – ảnh mẫu: source/ui/man-hinh-mau/chao-doi_v2.png
Dựng từ asset có sẵn (preview/tien-hoa/img):
1. Nền `room` + phủ đen 40% (rgba 0,0,0,0.4).
2. Đèn sân khấu: hình thang sáng màu (255,220,150) từ (290..350, y60) xuống (220..420, y350), làm mờ ~16px, alpha ~0.37; elip sáng dưới chân (215,318)-(425,372) alpha ~0.6.
3. Bóng đổ elip dưới chân pet; mảnh vỏ `no_<he>_7` phóng ~230px rộng, đặt SAU pet, đáy tại y≈364.
4. Pet (baby, tư thế reo vui) chân tại y≈350, cao ~128px.
5. Tàn lửa `hat_lua` + `lap-lanh` bay lên hai bên pet (cách tâm 80–150px), không đè lên pet.
6. Bảng gỗ `khung_chao-doi_go` ở (100,0), chữ trên bảng: "CHÚC MỪNG!".
7. Chữ: "<Tên> đã chào đời!" 24px tại (320,392), màu (255,236,170) viền (40,18,8); dòng nhỏ "<Loài> · Hệ <Hệ>" 14px tại (320,420); "A: vào phòng nuôi" (320,456).

# Asset mới (2026-10-24 chiều)
- Biểu cảm trên đầu pet: `r36s/bieu-cam/bc_*.png` (≤28px): tim, tim-nho, gian, xi-khoi, zzz, mo-hoi, mo-hoi-nho, not-nhac-doi, not-nhac, hoi (?), cham-than (!), choang.
- Đồ tắm 4 level: `r36s/cham-soc/do-tam/tam_L<1-4>_<xa-phong|khan|vit|dau-goi>.png` (≤36px). Mua đủ bộ level N → nâng nhà tắm lên `NT_L<N>`.

# Mini game CÂU CÁ (kiểu Stardew) – ảnh mẫu source/ui/man-hinh-mau/cau-ca.png
`r36s/mini-game/cau-ca/`:
- `nen.png` 640x480 (cầu gỗ bên trái; pet đứng cuối cầu, chân ~ (225,245)).
- Thanh câu `thanh-cau.png` 61x300 đặt ~ (530,90); rãnh nước bên trong rộng ~28px từ x+17. Vùng bắt `vung-bat_xanh.png` / `vung-bat_vang.png` 28x72 trượt lên xuống trong rãnh; cá `ca_icon.png` 30x22 nhảy trong rãnh.
- Thanh tiến độ `thanh-tien-do.png` 37x300 ở (596,90); `fill_tien-do.png` 18x272 cắt từ dưới lên theo %, đặt tại (606, 90+14).
- `phao.png`, `phao_chim.png` (cá cắn), `gon-nuoc.png`, `nuoc-ban.png`, `cham-than.png` (báo cắn câu), `can-cau.png`, `ruong_dong.png` / `ruong_mo.png` (rương báu ngẫu nhiên).
- 20 cá `ca/CA_<hoa|kim|moc|thuy|tho>_<1-4>.png` (≤40px): 1 thường → 4 huyền thoại.

# NÔNG TRẠI (farm) – ảnh mẫu source/ui/man-hinh-mau/farm.png
`r36s/farm/`:
- `nen.png` 640x480 (nhà kho trái, giếng phải, sân đất giữa để đặt ruộng).
- Ô ruộng rộng 100px: `o_co` (cỏ, chưa cuốc), `o_cuoc` (đã cuốc), `o_tuoi` (đã tưới), `o_kho` (khô nứt), `o_co-dai`, `o_sau`, `o_cay-heo`; `fx_thu-hoach` (ô có lấp lánh "sẵn thu hoạch"). Lưới 3x2 gợi ý: góc (168,205), bước x 104, bước y 82.
- Cây đặt giữa ô, chân cây cách đáy ô ~14px: `cay/cay_<hoa|kim|moc|thuy|tho>_<1-hat|2-mam|3-lon|4-chin|5-nong-san>.png` (≤48px). Nông sản: ớt (Hỏa), củ cải trắng (Kim), cải bắp (Mộc), củ sen (Thủy), bí ngô (Thổ).
- Dụng cụ / hiệu ứng: `dc_cuoc`, `dc_binh-tuoi`, `dc_tui-hat`, `dc_phan-bon`, `dc_gio`, `dc_bien-go`, `fx_nuoc`, `fx_bui-dat`.

## NÔNG TRẠI – bản chốt (thay mục nông trại ở trên)
- Nền: `r36s/farm/nen.png` (kho gỗ trái, giếng phải, sân đất giữa). Ảnh mẫu: source/ui/man-hinh-mau/farm_36-o.png
- Ô đất TRƠN không khung, 66x36: `r36s/farm/o-dat-tron/dat_<trong|cuoc|tuoi|kho|co-dai|sau|cay-heo>.png` (`dat_trong` = ô chưa mở, mờ).
- Lưới tối đa 6x6 = 36 ô: góc trái-trên (112,210), bước x 70, bước y 40 (khe 4px). Mở dần ô theo cấp/tiền.
- Cây (cao ~32px; hạt ~18px) đặt giữa ô, chân cây cách đáy ô ~7px.

## NÔNG TRẠI v2 – CHỐT (thay toàn bộ các mục nông trại trước; bản cũ ở _cu_khong-ref/farm_v1)
Bối cảnh: đồi thác nước (cùng màn chào). Góc nhìn nghiêng isometric. Ảnh mẫu: source/ui/man-hinh-mau/farm_v2.png
- `r36s/farm/nen.png` 640x480 (sân đất hình thoi ở giữa).
- Ô đất hình thoi (rộng ~81px, có thành đất): `r36s/farm/o-dat/dat_<tron|cuoc|tuoi|kho|co-dai|sau|cay-heo|gieo-hat|khoa>.png`; con trỏ chọn ô `con-tro_trang`, `con-tro_vang`; `fx_nuoc` (tưới).
- Lưới 6x6 = 36 ô: `r36s/farm/toa-do.json` có 4 góc ruộng + tâm từng ô. Vẽ ô từ SAU ra TRƯỚC (y nhỏ trước), cạnh trái tile trùng góc trái hình thoi ô.
- Cây: `r36s/farm/cay/cay_<hoa|kim|moc|thuy|tho>_<1-mam|2-non|3-lon|4-chin|5-nong-san>.png` (cao ~34px), chân cây tại tâm ô + 4px.
- Tương tác nông trại: KHÔNG có pet trên màn. Người chơi di chuyển ô sáng bằng D-pad, bấm A để cuốc/gieo/tưới/thu hoạch.
- Ô sáng: `r36s/farm/o-dat/con-tro_o_vang.png` (hoặc `con-tro_o.png` trắng), 87x49, đặt tại (góc trái hình thoi ô − (3, 21.7)). Nên nhấp nháy nhẹ.

## Nông trại – 15 loại cây (thay bộ 5 cây)
`r36s/farm/cay/cay_<loai>_<1-mam|2-non|3-lon|4-chin|5-nong-san>.png`, loai:
Hỏa: hoa-ot, hoa-ca-chua, hoa-dau-tay · Kim: kim-cu-cai, kim-toi, kim-sup-lo · Mộc: moc-bap-cai, moc-ngo, moc-dau-ha-lan · Thủy: thuy-sen, thuy-dua-hau, thuy-lua · Thổ: tho-bi-ngo, tho-khoai-lang, tho-ca-rot.

## SHOP NÔNG SẢN (mua hạt / bán nông sản) – ảnh mẫu source/ui/man-hinh-mau/shop-nong-san.png
`r36s/shop-nong-san/`:
- `nen.png` 640x480 (quầy hàng bên trái, phải để trống cho bảng).
- Bảng kem viền xanh (code vẽ) ~ (352,40) 272x406. Tab `tab_mua.png` (đào) / `tab_ban.png` (bạc hà) 86px đặt nhô trên mép bảng.
- Lưới 3x3 ô hàng `o-hang.png` / `o-hang_chon.png` 58px, bước x 82, y 104; nhãn giá `the-gia.png` 74px dưới ô; `xu.png` (xu).
- 15 gói hạt `hat_<loai>.png` (cao 40) cùng tên loại như cây. Tab Bán: dùng ảnh nông sản `cay_<loai>_5-nong-san.png` trong ô.
- Chủ quán (cô gấu mèo tanuki): `r36s/shop-nong-san/chu-quan/chu_<1-cuoi|2-chop-mat|3-chao|4-cuoi-lon|5-suy-nghi|6-dua-hat|7-nhan-xu|8-cam-on>.png` (cao ≤150). Đặt chân ~ (150,268), vẽ SAU nền rồi vẽ lại phần quầy (40,262)-(300,330) đè lên để che chân. Idle: 1↔2 chớp mắt; vào shop: 3; chọn hàng: 6; mua xong: 7→8; bán: 4. Bong bóng thoại do code vẽ.

## Câu cá v2 (thác nước) + hoạt ảnh
- Nền mới `r36s/mini-game/cau-ca/nen.png` (đường chân trời thấp, ít chi tiết; cầu gỗ trái). Nền cũ ở _cu_khong-ref/cau-ca.
- Dải 6 frame ngang (chia đều 6) trong `r36s/mini-game/cau-ca/fx/`: `phao_noi_dai6` (phao nhấp nhô, lặp), `phao_can_dai6` (cá cắn → chìm), `ca_keo_dai6` (cá bật lên giãy), `gon-nuoc_dai6` (gợn lan rồi tan). ~110ms/frame. Đáy frame = mặt nước. Xem source/ui/man-hinh-mau/cau-ca_hieu-ung.gif
- Cập nhật nền câu cá: cầu hạ thấp, trời cao hơn. Mặt cầu y≈402 (chân pet), pet hiển thị cao ~90px (đứng cuối cầu, chân x≈130). Phao đặt trên mặt nước y≈440–470.

## Màn HOẠT ĐỘNG (chọn mini game) – ảnh mẫu source/ui/man-hinh-mau/hoat-dong.png
`r36s/ui/hoat-dong/`: nền đổi theo thẻ đang chọn: `nen_cau-ca.png` khi chọn Câu cá, `nen_nong-trai.png` khi chọn Nông trại (nên chuyển mờ dần ~200ms), `bang-ten.png` 300px (tiêu đề, đặt (170,8)), thẻ `the.png` 170x252 / `the_chon.png` 210x297 (thẻ đang chọn, to hơn, viền đào lấp lánh) / `the_khoa.png` 170x252.
- 3 thẻ, tâm x = 115 / 320 / 525, đáy thẻ y = 395.
- Ô ảnh trong thẻ (trong suốt, vẽ ảnh xem trước PHÍA SAU thẻ): `the` (23,30)-(147,165); `the_chon` (39,56)-(168,196).
- Chữ tên ở ~86% chiều cao thẻ, dòng mô tả nhỏ ngay dưới.
- Nút: `mui-ten_trai/phai.png` 30px, `nut_A.png` (đỏ) / `nut_B.png` (vàng) 26px — chữ A/B/Vào/Về do code vẽ.

## Câu cá – cần câu tự động (dùng chung mọi pet)
`r36s/mini-game/cau-ca/can/can_<quang|cho|keo>_dai4.png`: dải 4 frame ngang (mỗi frame 130x130). Đặt frame tại (120, 410−130+6) – chân giá cần chạm mặt cầu; pet (≈90px) đứng bên trái ~ (40,312). Thứ tự: quang 1-4 → cho 1↔2 lặp (chờ) → cho 3-4 (cá cắn, kèm fx phao_can) → mini-game thanh câu → keo 1-4 (kèm fx ca_keo). Xem source/ui/man-hinh-mau/cau-ca_can.gif

## Shop – thêm tab ĐỒ CÂU + bán cá (dùng chung quầy nông sản)
Tab: Hạt · Đồ câu · Bán (3 tab, 78x32, cách 84px). Ảnh mẫu source/ui/man-hinh-mau/shop_do-cau.png
`r36s/shop-nong-san/do-cau/`: cần `can_1-tre … can_5-vang` (cần tốt → cá hiếm), mồi `moi_giun, moi_vun-banh, moi_tom, moi_moi-gia, moi_phep`, đồ khác `xo-ca, vot, hop-do-nghe, thung-da, thung-ca-da`.
Tab Bán: liệt kê cả nông sản (`cay_*_5-nong-san`) và cá (`r36s/mini-game/cau-ca/ca/CA_<he>_<1-4>.png`).

## NẤU ĂN (hoạt động thứ 3) – góc nhìn thứ nhất, bấm theo popup. Ảnh mẫu source/ui/man-hinh-mau/nau-an_4-buoc.jpg
`r36s/nau-an/`:
- nen/: `nen_cat` (thớt), `nen_khuay` (bếp – nồi), `nen_chien` (bếp – chảo), `nen_ban-an` (kết quả). 640x480.
- dung-cu/: cà chua `ca-chua_nguyen|nua|lat`, `dao`, nồi `noi_rong|song|soi_a|soi_b` (soi_a↔b luân phiên = sôi), chảo `chao_song|vang|chay` (theo kết quả bước chiên), `muong-go`, `hoi-nuoc`, tay đeo găng `tay_gang|tay_dao|tay_muong` (dùng chung mọi pet, đặt góc dưới phải).
- popup/: `khung-popup` (kéo giãn được), `nut-bam`/`nut-bam_nhan` (Cắt: bấm A liên tục), `mui-ten-xuong`, `xoay` + `vong_khung`/`vong_day` (Khuấy: xoay D-pad, vòng đầy dần – code vẽ cung), `thanh_khung`, `thanh_nhiet` + `kim-chi` (Chiên: kim chạy qua lại, bấm A trong vùng xanh), `sao`/`sao_rong` (1–3 sao), `buff_suc-manh`, `hoan-hao` / `truot` (báo đúng/trượt mỗi lần bấm), `lap-lanh`.
- mon/: 16 món `mon_*` (canh-ca-ca-chua, ca-chien-ot, banh-dau, com-trung-ca-chua, ham-cu-cai-toi, sup-lo-nuong, bap-cai-cuon, ngo-nuong, com-chien-dau, canh-ngo-sen, nuoc-dua-hau, com-nam-ca, sup-bi-ngo, khoai-lang-nuong, banh-ca-rot, lau-hai-san). Mỗi món = chuỗi 2–4 bước; điểm chính xác → 1–3 sao → mức buff.
- Icon buff khác chỉ số: dùng icon chỉ số có sẵn trong ui (suc-manh, nhanh-nhen, ben-bi…).
- Hoạt ảnh nấu `r36s/nau-an/hoat-anh/<cat|khuay|chien|xong>_dai6.png`: dải 6 frame ngang chia đều (cat 358x358/frame, còn lại 320x320). Tâm frame đặt ~ (320,255) trên nền tương ứng; ~120ms/frame. cat: 1 nhịp bấm A = chạy 1 vòng 6 frame; khuay: lặp khi đang xoay D-pad; chien: 1-3 lặp xèo xèo, 4-6 khi bấm (lật cá); xong: hơi nước bay + lấp lánh rồi hiện popup sao. Xem source/ui/man-hinh-mau/nau-an_hoat-anh.gif
- Cập nhật cách đặt hoạt ảnh nấu (sát khung, không bay): cat ×1.35 đáy frame tràn mép dưới màn (+30px), kéo dài ống tay xuống mép; khuay ×1.25 tâm (300,320) + bóng elip (300,330,330x90) dưới nồi, tay tràn mép dưới; chien ×1.2 tâm (318,285) + bóng (318,300,300x80); xong: đáy nồi tại y≈434 + bóng đậm (320,420,330x56). Xem gif mẫu.
- Đã lọc mảnh thừa (dính từ ô bên cạnh) trong mọi frame nấu. Kéo dài ống tay: chỉ kéo các cột chạm đáy frame xuống mép màn.
- Tay trong hoạt ảnh nấu: tay tròn trung tính màu kem (dùng chung mọi pet). Bộ tay_gang/tay_dao/tay_muong cũ trong dung-cu/ không dùng nữa.
- Cắt/khuấy v2: tay nằm gọn trong frame, đặt đáy frame chạm mép dưới màn (cat ×1.35, khuay ×1.3, tâm x≈300–320). Không cần kéo dài ống tay nữa.

## TÚI ĐỒ – ảnh mẫu source/ui/man-hinh-mau/tui-do.png
`r36s/ui/tui-do/`: `tui.png` (icon túi, 40px), 7 tab tròn 34px `tab_tat-ca | tab_nong-san | tab_ca | tab_hat | tab_do-cau | tab_mon-an | tab_ngoc` + `tab_chon.png` (vòng đào sau tab đang chọn), `so-luong.png` (nhãn số lượng góc dưới ô), `o-khoa.png` (ô chưa mở), `moi.png` (sao "mới"), nút `dung | yeu-thich | vut`, `sap-xep.png`.
- Dùng lại ô hàng của shop: `r36s/shop-nong-san/o-hang.png` / `o-hang_chon.png` (58px). Lưới 6x4 tại (40,128), bước 64. Bảng chi tiết bên phải (440,128)-(604,384). Khung bảng và chữ do code vẽ (kem viền xanh như shop).
- Ảnh vật phẩm dùng lại: nông sản `cay_*_5-nong-san`, cá `CA_*`, hạt `hat_*`, đồ câu `do-cau/*`, món `mon_*`, ngọc `NGOC_*`.

## TRƯỜNG HỌC – nền chốt: chòi học ngoài trời (góc nhìn ngồi bàn đầu)
- `r36s/truong-hoc/nen_lop.png` 640x480. Bảng đen trống, đã phóng to (vùng viết ~ (118,58)-(522,262)) để code vẽ bài học; vở mở trên bàn (~ (150,385)-(510,480)) có thể ghi điểm/ghi chú.
- Cô giáo rắn: `r36s/truong-hoc/co-giao/co_<1-cuoi|2-chop-mat|3-giang|4-khen|5-suy-nghi|6-ngac-nhien|7-sai|8-len-cap>.png` (cao ≤150; đặt bên phải bảng, chân ~ (560,345), có thể phóng 1.15). Idle 1↔2; ra câu hỏi 3; đúng 4; chờ 5; sai 7; xong bài/lên cấp 8. Ảnh mẫu source/ui/man-hinh-mau/truong-hoc.png
- Môn học (dự kiến): Toán, Tiếng Anh, Hệ (ngũ hành). Câu hỏi + đáp án do code vẽ trên bảng.
- UI trường `r36s/truong-hoc/ui/`: thẻ môn `the_toan|the_anh|the_he` (150px) + `the_chon` (170px, đặt sau thẻ đang chọn, lệch (-10,-6)); nút đáp án `nut_thuong|nut_chon|nut_dung|nut_sai` (rộng 250; chữ cái A–D đặt trong vòng tròn bên trái, đáp án viết bên phải); `khung-giay` (560 rộng, giãn được) cho câu dài + `thanh-cuon`/`mui-ten-cuon`. Ảnh mẫu source/ui/man-hinh-mau/truong_chon-mon.png, truong_tieng-anh.png
- Tiếng Anh: câu hỏi ngẫu nhiên từ kho TOEIC 300–800 (dữ liệu JSON/CSV do code nạp), 4 đáp án A–D. Câu ngắn viết thẳng lên bảng; câu dài dùng khung-giay.

## Màu nền trang chỉ số (thử) – source/ui/nen-mau/<go-am|go-mat-ong|hoa|moc|thuy|kim|tho>/
`khung_panel.png`, `the-thong-tin.png` cùng khung gỗ cũ nhưng lòng nền đổi màu (sáng hơn). ĐÃ BỎ – không dùng, xem mục "Nền trang chỉ số / Hồ sơ (sáng hơn)" bên dưới.

## Nền trang chỉ số / Hồ sơ (sáng hơn) — 2026-10-25
- Thư mục: r36s/ui/nen-chi-so/
- nen_chi-so_<hoa|moc|thuy|kim|tho>.png (640x480): nền phòng mờ theo hệ của pet. Vẽ ĐẦU TIÊN, sau đó vẽ khung/panel cũ lên.
- o-pet_<he>.png (250x391): chỉ phần ô pet bên trái, đặt tại (12,52). Dùng nếu muốn giữ nền gỗ cũ cho phần còn lại.
- Quy tắc: ô pet bên trái KHÔNG phủ nền gỗ (hiện nền phòng); cột thông tin bên phải giữ gỗ đặc như cũ để chữ rõ.
- Pet + bệ vẽ đè lên nền. Mẫu ghép: MAU_ho-so_v4.png. (Bỏ nen_trang-chi-so.png bản B cũ.)
- VIỆC CẦN LÀM (Minimon): trang Hồ sơ/chỉ số chọn nen_chi-so_<hệ>.png theo hệ của pet đang xem; bỏ phần nền gỗ tối ở ô pet bên trái (vùng 12,52 → 262,443) để nền phòng hiện ra; giữ nguyên tab, khung, cột thông tin bên phải. Áp dụng cho cả 4 tab (Sinh tồn, Linh khí, Thuộc tính, Hồ sơ) nếu cùng bố cục.

## Võ đường – tab Tập luyện — 2026-10-25
- Thư mục: r36s/vo-duong/tap-luyen/ · mockup: source/vo-duong/MOCK_vo-duong_1/2/3.png (Tập luyện / Nâng cấp / Kỹ năng)
- nen_vo-duong.png 640x480: nền võ đường (không pet, không UI). Pet đứng trên thảm đỏ ~ (80–300, 300–440). Bên phải ~40% sẽ bị panel che.
- bao-cat_0..3 (82x183, cùng khung, móc dây ở giữa mép trên): 0 đứng yên, 1 trúng lệch nhẹ, 2 lệch nhiều, 3 đong đưa về trái. Treo tại ~ (300,0).
- fx-trung_0..3 (110x110, cùng khung): tia lửa nhỏ → nổ lớn → vòng tan → tàn. Đặt tâm tại điểm đấm trúng.
- thanh-nhip.png (239x42): thanh canh nhịp, vùng xanh ở giữa = trúng mạnh. kim-nhip.png (38x39): kim chạy qua lại trên thanh.
- nut-cong.png / nut-cong_sang.png: nút + thường / đang chọn (cộng điểm tiềm năng).
- Cách chơi gợi ý: kim chạy qua lại, bấm A khi kim trong vùng xanh → đòn mạnh (bao-cat 2 + fx lớn, nhiều EXP); ngoài vùng → đòn yếu (bao-cat 1).
- Khung panel/chỉ số bên phải: dùng lại khung gỗ cũ (khung_panel, the-thong-tin). Icon chỉ số + ô kỹ năng: làm ở bước sau.

## Võ đường – MENU chọn (vào phòng tập) — 2026-10-25
- 3 mục: 1 Tập luyện · 2 Solo đối kháng · 3 Học né chiêu. Mockup: source/vo-duong/MOCK_vd_menu.png. Ghép mẫu: source/vo-duong/GHEP_menu-vd.png
- Thư mục: r36s/vo-duong/menu/ . Nền: dùng lại r36s/vo-duong/tap-luyen/nen_vo-duong.png
- KHÔNG có pet trong asset menu — nếu muốn, code tự vẽ pet hiện tại của người chơi.
- bang-tieu-de.png (255x68): bảng tiêu đề trống, code viết chữ "VÕ ĐƯỜNG".
- the_thuong.png (159x201) / the_chon.png (178x223, viền vàng sáng): khung thẻ; căn giữa theo cùng tâm.
- hinh_tap-luyen / hinh_solo / hinh_ne-chieu .png (109x153) đặt giữa the_thuong; bản *_lon.png (118x165) đặt giữa the_chon.
- bang-chu.png (136x47): bảng chữ dưới thẻ (code viết tên mục). khoa.png: ổ khóa nếu mục chưa mở.

## Võ đường – HỌC NÉ CHIÊU (game phản xạ) — 2026-10-25
- Thư mục: r36s/vo-duong/ne-chieu/ · Mockup: source/vo-duong/MOCK_vd_ne.png · Ghép mẫu: source/vo-duong/GHEP_ne-chieu.png
- Nền: r36s/vo-duong/tap-luyen/nen_vo-duong.png. KHÔNG có pet trong asset – code vẽ pet hiện tại của người chơi bên trái (~x 80–220, chân y ~400), quay mặt sang phải.
- Sư phụ khỉ (145x155, cùng khung, chân cùng baseline, quay trái), đặt ~ (470,250):
  su-phu_dung · su-phu_lay-da (chuẩn bị) · su-phu_nem (ném ngang) · su-phu_nem-cao · su-phu_nem-thap · su-phu_cuoi (khen) · su-phu_ngac-nhien (né PERFECT) · su-phu_that-vong (bị trúng / thua)
- Đạn (bay sang trái): dan_bong-go · dan_cau-lua · dan_con-xoay · dan_cau-nuoc
- Báo đòn: bao_len (đòn thấp → bấm ↑ nhảy) · bao_trai (đòn giữa → bấm ← lùi) · bao_xuong (đòn cao → bấm ↓ cúi) · bao_cham-than (sắp ném)
- FX: fx_bui (né thường) · fx_ne-hoan-hao (né PERFECT) · fx_trung-don (bị trúng). Mạng: tim_day / tim_rong.
- LUẬT GỢI Ý (game phản xạ):
  1. Sư phụ lấy đà (su-phu_lay-da + bao_cham-than) → hiện mũi tên báo hướng 0.6–1.0s trước khi ném.
  2. Đạn bay tới pet; người chơi bấm đúng hướng trong cửa sổ thời gian. Bấm sát lúc đạn chạm (≤150ms) = PERFECT (fx_ne-hoan-hao, combo +1, sư phụ ngạc nhiên); đúng nhưng sớm = né thường (fx_bui); sai/không bấm = trúng (fx_trung-don, mất 1 tim, combo về 0).
  3. Càng về sau đạn càng nhanh, báo đòn càng ngắn, có lúc ném 2 đạn liên tiếp.
  4. 20 đòn hoặc hết 3 tim thì kết thúc. Thưởng: chỉ số Tốc độ/Phản xạ + EXP theo số né được và combo cao nhất.
- Chữ "PERFECT!", "Né được x/20", "COMBO" do code viết (dùng bảng gỗ cũ / bang-chu của menu).
