# Elemon online: tự tạo tài khoản và đưa máy chủ lên Cloudflare

Máy chủ nhỏ cho **Đấu trường → Y: Đấu online** (đấu với đội của người khác). Nó là một Cloudflare Worker
(`src/worker.js`) và một cơ sở dữ liệu D1 (`schema.sql`). Gói miễn phí của Cloudflare là đủ cho game nhỏ; hạn mức
cụ thể xem ở trang giá Workers và D1 của Cloudflare.

Phần tạo tài khoản, đăng nhập là **bạn tự làm**. Các lệnh dưới đây chạy trong PowerShell, ở thư mục
`D:\INDIEGAME\HoLua\server\elemon-online`. Máy đã có Node.js 22, nên `npx` dùng được luôn.

## 1. Tạo tài khoản Cloudflare
1. Vào https://dash.cloudflare.com/sign-up, đăng ký bằng email của bạn, xác nhận email.
2. Trong trang quản trị, mở **Workers & Pages** một lần để Cloudflare tạo cho bạn một tên miền con miễn phí
   dạng `<tên-bạn>.workers.dev` (nó hỏi tên thì chọn tên bạn thích).

## 2. Đăng nhập từ máy tính
```powershell
cd D:\INDIEGAME\HoLua\server\elemon-online
npx wrangler login
```
Lần đầu `npx` hỏi cài `wrangler` thì gõ `y`. Trình duyệt mở ra, bạn bấm **Allow**.

## 3. Tạo cơ sở dữ liệu D1
```powershell
npx wrangler d1 create elemon-online
```
Lệnh in ra một đoạn có `database_id = "xxxxxxxx-...."`. Mở `wrangler.toml`, thay `DIEN-ID-VAO-DAY` bằng mã đó.

Rồi tạo bảng:
```powershell
npx wrangler d1 execute elemon-online --remote --file=schema.sql
```

## 4. Đưa Worker lên
```powershell
npx wrangler deploy
```
Cuối cùng nó in địa chỉ, ví dụ `https://elemon-online.<tên-bạn>.workers.dev`. Thử:
```powershell
curl.exe https://elemon-online.<tên-bạn>.workers.dev/api/ping
```
Thấy `{"ok":true,"v":1}` là xong.

## 5. Cho game biết địa chỉ
Ghi địa chỉ đó vào **dòng đầu** của `packaging/trimui-brick/mang-url.txt` (cả bản Brick và R36S đều lấy file này khi
đóng gói). Để trống thì màn Đấu online chỉ báo "chưa có địa chỉ máy chủ", game vẫn chạy như cũ.

Địa chỉ chỉ tới máy người chơi khi bạn đóng gói và phát hành bản mới (hoặc đẩy OTA). Việc đó chỉ làm khi bạn đồng ý.

## Sửa máy chủ về sau
- Sửa `src/worker.js` rồi `npx wrangler deploy` lại. Dữ liệu trong D1 vẫn giữ nguyên.
- Xem lỗi lúc đang chạy: `npx wrangler tail`.
- Xem dữ liệu: `npx wrangler d1 execute elemon-online --remote --command "SELECT name, level, rating FROM players ORDER BY rating DESC LIMIT 20"`.
- Xóa một người chơi gian lận: `... --command "DELETE FROM players WHERE id = '<id>'"`.
- Công thức chỉ số (`STATS` trong `src/worker.js`) phải giống `of()` trong `game/src/chi-so.js`. Sửa một bên thì sửa
  cả bên kia.

## Thử trên máy tính, không cần tài khoản
```powershell
node test/api-test.mjs                                  # thử API (SQLite thay cho D1)
$env:MIN_FIGHT_MS=0; node test/local-server.mjs 8787    # máy chủ cục bộ cho harness
```
Rồi chạy harness của game trong WSL: `wsl bash build/qjs-host/online-test.sh` (tải đội lên, tìm đối thủ, đánh một
trận với bot Khó, gửi kết quả, xem bảng xếp hạng, rồi thử lúc không có máy chủ).

Trong trình duyệt (bản build/game/tien-hoa): mở Console, gõ
`localStorage.setItem('elemon-mang-url', 'http://localhost:8787')` rồi tải lại trang.

## Máy chủ làm gì
| Đường | Việc |
|---|---|
| `POST /api/team` | nhận đội (1-3 pet: loài, bậc, cấp, 6 thuộc tính, tên), kiểm tra, tự tính chỉ số chiến đấu |
| `GET /api/opponents?id=&lv=` | tối đa 6 đội có cấp gần mình nhất (±8, thiếu thì nới) |
| `POST /api/fight` | mở một trận với một pet của đội kia, trả mã trận dùng một lần |
| `POST /api/result` | ghi thắng/thua của trận đó, đổi điểm (Elo: người đánh K=24, đội bị đánh K=12) |
| `GET /api/top?id=` | 20 người điểm cao nhất, và hạng của mình |

**Chống gian lận đơn giản (có, nhưng không tuyệt đối):**
- Mỗi máy tự tạo một mã và một khóa bí mật (`mang-id.txt` cạnh bản lưu). Máy chủ chỉ giữ sha256 của khóa; không có
  khóa thì không ghi đè được đội của người khác.
- Máy chủ không tin số máu/công máy gửi lên. Nó chỉ nhận 6 thuộc tính và cấp, kiểm tra cấp khớp bậc tiến hóa, mỗi
  thuộc tính ≤ `40 + 2×cấp` (tối đa 120), tổng ≤ `100 + 6×cấp` (tối đa 720), loài pet nằm trong danh sách, rồi tự tính.
  Hai giới hạn này để rộng vì pet kẹt ở cấp cuối bậc vẫn tập và ăn thêm được mỗi ngày. Muốn chặt hơn thì sửa
  `ATTR_CAP` / `SUM_CAP`.
- Kết quả phải đi kèm một trận đã mở. Trận thắng phải dài ít nhất 15 giây. Mỗi mã trận ghi được một lần, hết hạn sau
  30 phút. Mỗi ngày đánh tối đa 60 trận, tối đa 5 trận với cùng một đội. Tải đội lên cách nhau ít nhất 10 giây.
- Trong trận online, START ("đấu lại" của sân) bị khóa, nên không đấu lại được tới khi thắng.
- Phần **chưa** chặn được: máy đã bị sửa vẫn có thể báo thắng giả, và vẫn gửi được thuộc tính "đẹp nhất" trong giới
  hạn. Muốn chặn hẳn thì máy chủ phải tự chạy lại trận từ các nút bấm. Việc này cần trận đấu tất định (xem
  `LOCKSTEP.md`); đây cũng là nền cho 1v1 trực tiếp.
