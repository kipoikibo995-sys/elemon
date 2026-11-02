# Trận Solo chạy khác nhau giữa các lần: ghi chép làm nền cho 1v1 lockstep

Lockstep nghĩa là hai máy chỉ gửi cho nhau **nút bấm theo từng nhịp**, mỗi máy tự chạy trận. Muốn vậy, cùng nút bấm
ở cùng nhịp thì trận phải ra **y hệt** trên mọi máy và mọi lần chạy. Hiện chưa được như vậy. Dưới đây là các chỗ gây
lệch, tìm trong sân đấu (`preview/dau-truong/index.html`, game chạy bản đã móc qua `game/src/solo.js`,
`chi-so.js`, `vung-dat.js`) và trong runtime (`r36s/`). Chưa sửa chỗ nào: đây là danh sách để làm sau.

## Đo trên harness (02/11/2026)
`build/qjs-host/det-test.sh` chạy cùng một trận bốn lần: Hỏa Hổ đấu Kim Tê, bot Khó. Nút bấm tính theo **khung của
trận**, không theo khung của chương trình (`test-det.js`). Vị trí và máu hai bên được ghi mỗi 15 khung.

| Cách chạy | Hai lần có giống nhau? |
|---|---|
| Như bây giờ | **Không.** Lệch từ khung 165, khi bot quyết định khác (`det-plain-1.txt` và `-2.txt`) |
| `Math.random` có hạt giống cố định từ lúc trận bắt đầu | **Có**, giống hệt cả 420 khung (`det-seed-1.txt` và `-2.txt`) |

Như vậy **trên harness** (mỗi khung đúng 1000/30 ms), chỉ cần hai việc là trận đã tất định: hạt giống cho
`Math.random` (mục 1) và tính nút bấm theo khung của trận (mục 3). Trên máy thật còn thêm thời gian thực (mục 2), vì
mỗi khung dài ngắn khác nhau.

## 1. Số ngẫu nhiên: `Math.random` (nặng nhất)
QuickJS lấy hạt giống từ đồng hồ lúc mở game (`js_random_init`: `gettimeofday`), nên mỗi lần chạy ra một dãy khác.
Sân đấu có 54 chỗ gọi `Math.random`. Những chỗ **làm đổi diễn biến trận**:
- Bộ não bot (`think`, khoảng dòng 2880-3005): hướng vòng (`brain.orbit`, dòng 787), né hay không (`botDodges`),
  đổi hướng (`juke`), phạt đòn (`punish`), sai số ngắm (`b.err`), thời gian giữ chiêu (`holdUntil`), tung tuyệt chiêu
  (dòng 2943, 2992).
- Sân được chọn ngẫu nhiên (`pickArena`, dòng 3588): mỗi sân có vòng tròn khác (`RING_Y`, `RING_RX`, `RING_RY`).
- Chiêu có vị trí ngẫu nhiên: đá rơi của Rồng (`updateDragonDive`, dòng 1772), lưới mạch nước phun
  (`geyserField`, dòng 2612-2613), góc chém (dòng 2510).
- `game/src/vung-dat.js`: các trận ở Vùng đất và Hư Ảnh có thêm ngẫu nhiên riêng (dòng 1751-1924, 2038). Trận online
  dùng bản sân đã móc của Vùng đất (`__vgDuelSrc`), nên cũng mang theo các chỗ này.

Những chỗ **chỉ để vẽ** (hạt bụi, lá, tia lửa, số sát thương bay, rung màn hình dòng 2759/3300) không đổi diễn biến
trận. Nhưng chúng **lấy chung một dãy số**: vẽ nhiều hay ít hạt sẽ làm lệch các số mà phần trận lấy sau đó.

**Cách sửa:** hai dãy riêng. Một dãy có hạt giống chung cho logic trận (máy chủ hoặc chủ phòng gửi hạt giống lúc bắt
đầu). Một dãy tự do cho hiệu ứng. Thay các `Math.random` của logic bằng `rng()`, giữ `Math.random` cho phần vẽ.

## 2. Thời gian thực trong vòng lặp trận
- `frame(t)` (dòng 3072-3074): `dt = min(50, t - real)`. Mỗi bước di chuyển, đạn, hồi chiêu đều nhân với `dt`.
  `t` là thời gian của khung (trên máy là đồng hồ SDL). Khung chậm thì bước dài, và tích phân lệch theo tốc độ máy.
- Khựng khi trúng đòn (hit-stop: `stopUntil = real + 50..140`, dòng 916, 972, 1087, 2766, 2781, 2856) tính bằng
  **thời gian thật**. Số khung bị khựng tùy máy nhanh hay chậm.
- **Cách sửa:** chạy logic theo **nhịp cố định** (vd 1 nhịp = 1000/60 ms, hoặc 1000/30 như harness), tách khỏi
  khung vẽ. Hit-stop tính bằng số nhịp. Phần vẽ có thể nội suy giữa hai nhịp.

## 3. Lúc trận bắt đầu phụ thuộc tốc độ máy
`game/src/solo.js` (`__soloDraw`): đọc trước khung hình, âm thanh và `__aimWarm` trong một ngân sách
`PRELOAD_MS` = 30 ms **thời gian thật** mỗi khung. Máy chậm thì màn VS kéo dài thêm khung. Nút bấm tính theo khung
của chương trình sẽ rơi vào lúc khác của trận. Đây là lý do script nút bấm của harness (`game-*.txt`) cho kết quả
khác nhau dù `Math.random` có giống nhau.
**Cách sửa:** đếm nhịp từ lúc trận thật sự bắt đầu (`arena.started`). Lockstep gửi nút bấm kèm số nhịp của trận,
không kèm số khung. `test-det.js` đã làm vậy.

## 4. Số liệu mỗi bên tự tính
- `__soloPow` (`chi-so.js` `pow`): tỉ lệ sức mạnh và máu đầu trận (`hp0` theo Sức khỏe) tính từ nhu cầu (mệt, đói,
  buồn), món ăn đang có tác dụng, Linh khí. Mấy thứ này đổi theo **giờ thật** (`tickNeeds`, `Date.now` trong
  `day()`). Hai máy sẽ tính ra số khác nhau.
- **Cách sửa:** chốt số lúc vào trận. Mỗi máy gửi bộ số của pet mình (như `/api/team` đã làm: 6 thuộc tính + cấp,
  cộng phần nhu cầu và món ăn lúc đó). Cả hai dùng chung bộ số, tốt nhất do máy chủ tính và gửi lại.

## 5. Số thực khác nhau giữa các máy
Trận dùng `Math.sin`, `cos`, `atan2`, `hypot`, `sqrt`. Brick và R36S đều ARM64 và chạy cùng file `elemon` (dịch bằng
zig, cùng thư viện toán), nên **giữa hai máy này** nhiều khả năng ra giống nhau. Máy tính (x86, harness, trình duyệt)
có thể lệch ở chữ số cuối, rồi lệch dần qua vài nghìn nhịp.
**Cách sửa:** chỉ cho đấu lockstep giữa hai bản `elemon` cùng phiên bản. Lưu vị trí bằng số nguyên hoặc làm tròn
sau mỗi nhịp (vd 1/256 px) để sai số nhỏ không lớn dần. Thêm "checksum" trạng thái mỗi N nhịp để phát hiện lệch.

## 6. Những thứ khác cần để ý
- Đầu vào: `feedKeys` đọc `HELD` mỗi khung vẽ. Lockstep phải gom nút theo nhịp và chỉ chạy nhịp khi đã có nút của
  cả hai bên.
- Bot: trong 1v1 không có bot. Nhưng nếu giữ bot (đấu với đội người khác như bây giờ, hoặc để máy chủ chạy lại trận
  kiểm tra kết quả), bot phải lấy số từ `rng()` có hạt giống.
- START trong sân là "đấu lại", số 0-3 là đổi mức bot (phím máy tính). Chế độ online phải khóa các phím này
  (`dau-online.js` đã khóa START).
- Âm thanh, giọng đọc, rung màn hình, hạt bụi: không ảnh hưởng nếu đã tách dãy ngẫu nhiên như mục 1.

## Thứ tự nên làm
1. `rng()` có hạt giống cho logic, `Math.random` cho phần vẽ (mục 1).
2. Nhịp cố định và hit-stop tính bằng nhịp (mục 2).
3. Đếm nhịp từ lúc trận bắt đầu, ghi nút bấm theo nhịp (mục 3). Từ đây có thể **ghi lại trận** (replay), và máy chủ
   có thể chạy lại trận để kiểm tra kết quả do máy báo, tức là chống gian lận thật cho chế độ đấu đội hiện tại.
4. Chốt số liệu đầu trận (mục 4), checksum (mục 5), rồi mới làm phần mạng 1v1 (phòng chờ và chuyển nút qua máy chủ,
   ví dụ Cloudflare Durable Objects + WebSocket, cạnh Worker hiện có).

## 02/11/2026: Đấu qua wifi (cùng một mạng) đã làm theo cách trên
`game/src/dau-wifi.js` (Võ đường → Đấu online → Đấu qua wifi), UDP trong `r36s/jsrt.c` (`udpOpen/udpSend/udpRecv/udpClose/myIp`).
- Mục 1: trong lúc một nhịp chạy, `Math.random` của sân là dãy có hạt giống của phòng; sân chọn theo `__lanSan`.
- Mục 2: nhịp cố định 1000/30 ms, sân nhận đồng hồ của nhịp (`1000 + n × TICK`), nên hit-stop cũng theo nhịp.
- Mục 3: nút bấm ở nhịp n có hiệu lực ở nhịp n + 3, gửi kèm 12 nhịp trước (mất gói vẫn đủ); thiếu nút bên kia thì đứng chờ.
- Mục 4: chỉ số hai bên chốt lúc vào phòng (`__soloPow` chủ phòng tính, gửi kèm), máu đầu trận đầy, không tính nhu cầu.
- Mục 5: mỗi 30 nhịp so vị trí + máu + tỉ số; lệch thì ghi `wifi: LỆCH` vào log.txt và hiện chữ LỆCH.
- Thử: `build/qjs-host/wifi-test.sh` (hai harness cùng lúc trên một máy, tìm phòng bằng broadcast): 2178 nhịp, 73/73 lần so khớp.
- Chưa có: đánh qua internet (cần máy chủ phòng + TLS), thanh chiêu dưới màn của máy khách vẫn là của bên trái.
