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

Đã làm (28/10/2026, `game/src/chi-so.js`). Mức tác dụng tỉ lệ với Linh khí, đủ 100 thì đầy đủ, 50 thì một nửa:

| Hệ | Ở mức 100 |
| --- | --- |
| Kim | Thủ +15, No giảm chậm còn ×0,75 |
| Mộc | Sức khỏe tự hồi +2 mỗi giờ, chỉ dễ ốm khi Sức khỏe dưới 20 (thay vì 30) |
| Thủy | Vui giảm chậm còn ×0,7, câu cá và nấu ăn dễ hơn 20% |
| Hỏa | Công +15%, No giảm nhanh hơn ×1,25 |
| Thổ | Ngủ hồi Năng lượng nhanh ×1,5 (Cân nặng chưa có trong game) |

Kim và Hỏa cùng cao thì hai tác dụng lên No bù trừ cho nhau. Linh khí chỉ tăng khi ăn món của hệ (+6 mỗi bữa) và không tự giảm.

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

## 6. Chỉ số thống nhất (chốt và làm 28/10/2026)

Code: `game/src/chi-so.js` (thuộc tính, công thức, Sức khỏe, chi phí, móc vào đấu trường), `vung-dat.js` (Level quái và boss, máu, thưởng), `solo.js` (Solo ở Võ đường), `vo-duong.js` (bài tập), `song-that.js` (EXP theo kho, thưởng boss). File đấu trường của session Chiến đấu không bị sửa: các thay đổi được chèn vào bản chạy. Chưa làm: số Lực chiến cạnh tên. Trong Solo, Né, Tốc và Kháng hệ được gộp vào Lực chiến chứ không tính riêng.

Người dùng chốt 4 hướng (28/10/2026):
- Boss và quái ghi **Level thật 1–150**, cùng thang với pet.
- **Solo có tính level và thuộc tính**, nhưng chênh lệch có trần.
- Sáu thuộc tính tăng bằng **lên level (theo Linh khí), món ăn theo hệ và bài tập Võ đường**, cộng thêm ngọc như cũ.
- Khắc hệ ở mọi nơi: **khắc ×1,5, bị khắc ×0,75**.

Trước đó game có 3 bộ số chạy riêng:
- Sáu thuộc tính cố định theo con mẫu "Bông" (38/30/22/12/10/25) cho mọi pet.
- Vùng đất tính máu và công theo level và thuộc tính, còn Solo luôn 100 máu, không tính level.
- Boss ghi "Lv2–5" (thật ra là giai đoạn), trong khi pet có Level 1–150.
- Khắc hệ ở vùng đất có ×0,75, ở Solo thì không.

### 6.1 Sáu thuộc tính (0–100)

| Nguồn | Tăng bao nhiêu | Vào thuộc tính nào |
| --- | --- | --- |
| Trứng nở | Mỗi thuộc tính 10, riêng 2 thuộc tính của hệ pet 15 | |
| Lên level | +1 điểm mỗi level (tối đa +149) | Chia theo tỉ lệ Linh khí 5 hệ, mỗi hệ chia đều cho 2 thuộc tính của nó |
| Món ăn theo hệ | +0,25 vào mỗi thuộc tính của hệ món, tối đa +1 điểm mỗi ngày | 2 thuộc tính của hệ món (bảng Liên kết với Ngũ Hành) |
| Võ đường | +1 điểm mỗi buổi tập xong, tối đa 1 buổi tính điểm mỗi ngày cho mỗi bài | Đấm theo nhịp: Sức mạnh. Né đòn: Nhanh nhẹn (bài Học né chiêu đã gỡ khỏi menu 28/10/2026, người dùng sẽ làm bài khác thay; bài mới nên nuôi Nhanh nhẹn). Đấu Solo thắng: Tinh thần |
| Ngọc | Như cũ (Đá thô +1 … Ngọc thần +10) | 2 thuộc tính của hệ ngọc |

- 5 ô ngọc mở theo level (28/10/2026): Lv6 (lên Nhi), Lv15, Lv21 (Thiếu niên), Lv46 (Trưởng thành), Lv100 (Huyền thoại). Ô chưa mở hiện ổ khóa và level mở. Ngọc nằm ở ô chưa mở (ngọc có sẵn khi bắt đầu, bản lưu cũ) được trả về túi.
- Phần gốc (không kể ngọc) tối đa 100. Kể cả ngọc tối đa 120. Thanh trên màn chỉ số đầy ở 100, số vẫn ghi đủ.
- Bài tập chỉ nuôi Sức mạnh, Nhanh nhẹn và Tinh thần. Thông minh và Trí tuệ đến từ level và món ăn (cá suối, món Thủy, Thổ), khớp với luật 4 chân / 2 chân ở mục 4.
- Ước tính một pet Huyền thoại Lv150 chăm đều có tổng khoảng 450/600: 2 thuộc tính chính gần 100, còn lại 50–70.

### 6.2 Chỉ số chiến đấu (một công thức cho pet, quái, boss)

| Chỉ số | Công thức | Lv15 (SM 25, Bền 20) | Lv100 (SM 90, Bền 80) |
| --- | --- | --- | --- |
| Máu | 80 + 4×Lv + 3×Bền bỉ | 200 | 720 |
| Công (đòn thường) | 8 + 0,4×Lv + 0,4×Sức mạnh | 24 | 84 |
| Kỹ năng (chiêu hệ) | 12 + 0,5×Lv + 0,5×Thông minh | | |
| Linh lực | 60 + 0,4×Lv + 1,5×Trí tuệ | | |
| Thủ | 0,5×Lv + 0,5×Bền bỉ. Sát thương nhận × 100 / (100 + Thủ) | ×0,85 | ×0,53 |
| Kháng hệ | Trí tuệ × 0,3% giảm sát thương chiêu hệ | | |
| Tốc | 120 + 0,8×Nhanh nhẹn | | |
| Né | Nhanh nhẹn × 0,15% | | |
| Chí mạng | 4% + Tinh thần × 0,2%, đòn chí mạng ×1,6 | | |

- Khắc hệ: ×1,5 khi khắc, ×0,75 khi bị khắc, ở cả vùng đất và Solo.
- Lực chiến (số hiện cạnh tên): (Máu / 4 + Công + Kỹ năng) làm tròn. Dùng để so hai bên trong Solo.

### 6.3 Quái và boss theo vùng (Level thật)

| Nơi | Level | Thân hình dùng |
| --- | --- | --- |
| Khu 1 (rìa vùng, Nhi đi được) | Quái Lv6–12, mini boss Lv14, boss khu Lv16 | Nhi |
| Khu 2 (cần Thiếu niên) | Quái Lv22–32, mini boss Lv34, boss khu Lv36 | Thiếu niên |
| Khu 3 | Quái Lv46–58, mini boss Lv60, boss khu Lv62 | Trưởng thành |
| Boss cuối vùng | Lv100 | Huyền thoại |

- Thân hình theo Level: đến Lv20 là Nhi, Lv21–45 Thiếu niên, Lv46–99 Trưởng thành, từ Lv100 Huyền thoại. Pet của người chơi cũng đánh bằng thân của giai đoạn nó đang ở (Con dùng thân Nhi). Bộ hình: `preview/dau-truong/img/<pet>/teen|adult|legend/`, chép bằng `python scripts/lam_lv3.py arena adult|legend` (28/10/2026). Trên R36S, giai đoạn nào chưa cắt sẵn thì lùi về giai đoạn dưới.

- Quái tính bằng cùng bảng 6.2, thuộc tính bằng 10 + Level × 0,5, nhân hệ số loại quái như hiện có (`KIND` trong `vung-dat.js`: cận, nhanh, trâu, bắn). Quái thường là Hư Ảnh nên chỉ có 40% máu so với pet cùng level.
- Thông báo ghi Level thật: "Kim Giáp Lv34 chặn lối!". Bỏ cách ghi Lv2–5.
- Độ khéo của bot (Dễ / Vừa / Khó) vẫn tính riêng, theo cách gặp boss như hiện nay.

### 6.4 Solo

- Cả hai bên vẫn hiện thanh máu 100, nhưng sát thương được nhân thêm theo tỉ lệ Lực chiến: bên mạnh hơn ×(Lực chiến mình / Lực chiến đối thủ), **tối đa ×1,5**, bên yếu hơn tối thiểu ×0,67.
- Giữ hệ số cân bằng từng chiêu (`KIT_POWER`, `KIT_DEF`) như cũ.
- Võ đường đấu với bot: bot lấy Level bằng pet người chơi (đấu tập công bằng). Boss: Level theo bảng 6.3.

### 6.5 EXP

- Kho EXP hồi theo giờ vẫn giữ (`song-that.js`), nhưng kho nhỏ dần theo giai đoạn (Con chứa ~128, Trưởng thành ~61). Thưởng cố định (cho ăn +25) nên lúc lớn cho ăn 2 lần là cạn kho.
- Đổi lại: **thưởng tính theo phần trăm kho**, mọi giai đoạn chơi cảm giác như nhau. Cho ăn 15% kho, vuốt ve 2%, dọn phân 10%, buổi tập Võ đường tối đa 40%, quái thường 3%.
- **Boss không lấy từ kho** (thưởng một lần, không bị "EXP hôm nay đã đầy"): mini boss 30% một level, boss khu 60% một level, boss cuối 1 level. Boss khu luôn hơn mini boss.

### 6.6 Đánh nhau ảnh hưởng chỉ số sinh tồn (yêu cầu 28/10/2026)

Người dùng: đánh ở vùng đất (rừng…) hay Solo đều làm mất máu, mất năng lượng, mất vui… Trước đó game chỉ trừ một ít Năng lượng và No (vùng đất −4 / −2 mỗi khu, Solo −8 / −4 mỗi trận, gục −10 Vui). Máu hết trận là mất, không để lại gì, và Sạch không giảm.

**Máu chính là Sức khỏe.** Sức khỏe thành thanh 0–100 thật (trước chỉ có trạng thái ốm / không ốm):
- Vào trận, Máu hiện tại = Máu tối đa (6.2) × Sức khỏe / 100.
- Hết trận (vùng đất hay Solo), Sức khỏe mất 30% số máu đã mất, tính theo phần trăm thanh máu: mất 60% máu thì Sức khỏe −18. Ở vùng đất máu tự hồi khi không bị đánh, nên tính theo tổng máu đã mất chứ không theo máu còn lại lúc về.
- Sức khỏe hồi khi ngủ (+5 mỗi giờ), ăn món hệ Mộc như Lá non (+10), uống thuốc (+40, khỏi ốm). Linh khí Mộc cao thì tự hồi thêm (tối đa +2 mỗi giờ).
- Thuốc uống được khi ốm, hoặc khi Sức khỏe dưới 60 dù chưa ốm.
- Sức khỏe dưới 30 mà đói hoặc bẩn thì bị ốm. Dưới 5 thì ốm luôn. Dưới 15 thì không cho ra trận.
- Code: `game/src/chi-so.js` (làm 28/10/2026).

**Mỗi lần đánh trừ (cộng) gì:**

| Hoạt động | Năng lượng | No | Vui | Sạch | Sức khỏe |
| --- | --- | --- | --- | --- | --- |
| Vùng đất, mỗi khu đi qua | −6 | −4 | | −8 (bùn đất) | Theo máu còn lại |
| Phá xong một khu / thắng boss | | | +8 | | |
| Gục trên đường | −10 thêm | | −15 | | Còn 10 |
| Solo, mỗi trận | −8 | −4 | Thắng +8, thua −6 | −3 | 30% máu đã mất |
| Võ đường, mỗi buổi tập | −10 | −5 | +5 | −5 | |

**Ngược lại, chỉ số sinh tồn thấp làm pet đánh yếu đi:**

| Khi | Ảnh hưởng trong trận |
| --- | --- |
| Năng lượng < 30 | Công và Kỹ năng ×0,85, Tốc ×0,9 |
| No < 20 | Linh lực hồi chậm một nửa |
| Vui < 30 | Chí mạng giảm một nửa |
| Vui ≥ 80 | Công +5% (hăng hái) |
| Đang ốm | Không ra trận được (như hiện nay) |

- Màn chọn khu và màn chọn đối thủ Solo hiện Sức khỏe cạnh Năng lượng, và báo trước pet đang bị giảm sức vì sao.

### 6.7 Món nấu (làm 28/10/2026)

Trước đó buff của món nấu chỉ là chữ, ăn vào như món thường. Giờ một món nấu 1–3 sao:
- No +30 / +40 / +50 (đúng như ghi trên món).
- **Món hệ Mộc:** Sức khỏe +15 mỗi sao, có tác dụng ngay (cộng thêm +10 như mọi món Mộc).
- **Món hệ khác:** buff cho chuyến vùng đất hoặc trận Solo kế tiếp, hết chuyến hoặc rời sân là hết. Hỏa: Sức mạnh +4 mỗi sao. Thủy: Nhanh nhẹn +4 mỗi sao. Thổ: Bền bỉ +4 mỗi sao (thêm 12 máu mỗi sao). Kim: Thủ +5 mỗi sao.
- Chỉ giữ một buff, ăn món mới thì thay buff cũ. Màn cổng vùng đất và màn chọn đối thủ Solo hiện buff đang có.
- Cùng một món nấu ra số sao khác nhau thì nằm ở hai ô riêng trong túi.

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

## Cốt truyện, phim và giọng đọc (làm 26–27/10/2026)

Theo tài liệu "Elemon — Cốt truyện và 5 vùng đất". Đã có Mở đầu, Hồi 1 và Hồi 2 (lời thoại, chưa đụng boss: người dùng chưa chuẩn bị xong phần boss). Cảnh Hồi 2 ở cổng vùng đất cùng hệ dùng mode `vungdat` của `vung-dat.js`. **Chỉ mới thử trên trình duyệt, chưa chạy trên R36S lần nào.**

| Phần | File | Ghi chú |
| --- | --- | --- |
| Lời thoại, kịch bản phim, giọng từng vai | `game/src/truyen.js` | Chỉ có chữ, sửa lời ở đây; đầu file có hướng dẫn |
| Hộp thoại đáy màn hình | `game/src/hoi-thoai.js` | Khung chân dung riêng, chữ chạy dần, A/B sang câu |
| Phim (`mo-dau` khi Chơi mới, `dem-ay` sau khi chọn trứng) | `game/src/phim.js` | Mode `phim`, không lưu game giữa phim (`song-that.js`), nhạc đêm (`r36s/js/am-thanh.js`) |
| Phát giọng | `game/src/giong.js` | `__giong(key)`, độ dài từng câu do `build_game.py` chèn vào |
| Tạo giọng | `scripts/make_giong.py` | edge-tts (giọng Việt online của Microsoft: Hoài My nữ, Nam Minh nam), ra `assets/am-thanh/giong/*.wav` 22050 Hz mono; chỉ tạo lại câu đã sửa |
| Ảnh | `assets/source/phim/` (5 cảnh phim 16:9 + `NEN_no-trung.png` nền ấp trứng), `assets/source/npc/NPC_gia-quy.png` | `build_game.py` thu ảnh phim về 800×450, cắt nền ấp trứng 640×480 cho lòng ổ rơm trùng chỗ đặt trứng, cắt Già Quy thành 8 chân dung khoảng 205×220 |

**Việc cần làm khi tối ưu cho máy (chưa làm):**
1. **R36S không ngắt được tiếng:** `SOUND.sfx` không dừng được âm đang phát. Bấm A khi câu thoại chưa đọc xong thì câu cũ vẫn đọc tiếp, đè lên câu mới (trên trình duyệt câu cũ được ngắt). Cần thêm một kênh giọng riêng trong `r36s/jsrt.c`: phát câu mới thì dừng câu cũ (ví dụ `holua.voice(name)` và `SOUND.voice` trong `r36s/js/shim.js`), rồi cho `giong.js` dùng kênh đó nếu có.
2. **Bộ nhớ giọng:** `load_sound` giữ mọi âm đã nạp. 98 câu WAV khoảng 25 MB, khoảng 9 phút 40 giây (câu nhắc tới hệ hoặc vùng có 5 bản, mỗi hệ một bản). Nên giải phóng câu đã đọc xong, hoặc giảm còn 16 kHz / nén ADPCM.
3. **Phim phóng ảnh ở mọi khung hình:** camera của phim vẽ cả màn hình có co giãn ở mỗi khung (bản đồ 640×480, ảnh phim 800×450 về 640×360). Theo kinh nghiệm ở `ve-nhanh.js` và `vung-dat.js`, R36S chậm với kiểu vẽ này nên có thể bị giật. Cách sửa: giảm hoặc bỏ phóng, hoặc dựng sẵn khung.
4. **Ảnh không được giải phóng:** `phim.js` và `hoi-thoai.js` giữ ảnh phim và chân dung trong bộ đệm suốt cả lượt chơi. Nên `__cv.free` ảnh của cuộn phim khi phim xong, và bỏ chân dung của cảnh đã xong. Ảnh phim cộng nền ấp trứng khoảng 4,3 MB PNG.
5. **PocketGo 320×240:** chưa có bản 320 của phim, chân dung và giọng. Cần bản thu nhỏ, hoặc tắt phim và giọng trên máy đó (RAM 32 MB).
6. **Nhạc không nhỏ đi khi có giọng đọc:** nhạc nền vẫn giữ âm lượng cũ trong lúc giọng đọc.
7. **Tạo giọng cần mạng và chậm:** dịch vụ edge-tts chập chờn, script tự thử lại, mỗi câu mất khoảng 10–20 giây. Tên pet do người chơi đặt nên giọng đọc là "bé"; phần trong ngoặc như "(R2)" không đọc.

## Điểm cần chốt khi làm game

- **No** và **Vui** chưa ghi giảm khi nào. Tạm hiểu là giảm dần theo thời gian (như Mimo).
- **Cân nặng** được nhắc tới (Khoai đất tăng cân, Thổ tăng cân chậm) nhưng chưa có trong bảng chỉ số.
- **Đã chốt (23/10/2026):** dùng bộ chỉ số trong file này (5 chỉ số sinh tồn + Linh khí 5 hệ + 6 thuộc tính). `nen/README.md` còn ghi chỉ số chính theo hệ là Công / Chí mạng-Ý chí / HP / Tốc / Thủ, cần đổi phần cộng chỉ số của nhà sang 6 thuộc tính (ví dụ nhà hệ Hỏa cộng Sức mạnh + Nhanh nhẹn, theo bảng Liên kết với Ngũ Hành).
- `tinh-linh/README.md` ghi "bài tập quyết định lối đánh (Sức mạnh / Kiên trì / Nhanh nhẹn)", còn ở đây thức ăn theo hệ cũng nuôi thuộc tính. Cần chốt cái nào quyết định nhánh tiến hóa.
