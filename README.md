# Hổ Lửa — PocketGo

Game nuôi hổ lửa cho máy PocketGo (MiyooCFW, ARM, uClibc, SDL 1.2), làm theo từng giai đoạn.

## Giai đoạn 1 (hiện tại): xem động tác

Chương trình `holua` chiếu 12 động tác của hổ đúng như trong game: đứng thở, đấm, chiêu lửa, trúng đòn, gục ngã, thắng, ăn, vui nhảy, mệt, ốm, ngủ, thức dậy. Nền phòng tạm thời vẽ bằng màu, sẽ thay khi có ảnh nền.

| Nút | Việc |
| --- | --- |
| Trái / Phải (Lên / Xuống) | Chọn động tác |
| A | Chơi lại |
| B | Thoát |

## Thiết kế cơ chế nuôi

Chỉ số sinh tồn, Linh khí theo hệ, thức ăn và 6 thuộc tính: xem [THIET-KE.md](THIET-KE.md).

## Tinh linh: hệ > con > cấp

31 tinh linh, 5 hệ (Hỏa, Kim, Mộc, Thủy, Thổ), mỗi con 5 cấp: Trứng (`egg`), Con (`baby`), Nhi (`child`), Thiếu niên (`teen`), Trưởng thành (`adult`).

Ảnh gốc bỏ chung vào `assets/source/tinh-linh/`, đặt tên `<HỆ>-<NHÁNH>_<tên>[_<cấp>].png`, ví dụ `MO-T2_moc-loc_egg.png`; không ghi cấp là Trưởng thành. Script tự nhận file mới, không cần khai báo.

| Cấp | Lưới | Khung |
| --- | --- | --- |
| Trứng | 4×2 | nhịp sáng ×4 · nứt nhẹ, nứt lớn, vỡ, vỏ |
| Con / Nhi / Thiếu niên | 4×4 | đứng ×4 · đi ×4 · ăn, vui, mệt, ốm · ngủ ×2, ngáp, vươn vai |
| Trưởng thành | 4×6 | đứng ×4 · đánh ×4 · chiêu ×4 · đỡ, trúng đòn, gục, thắng · ăn, vui, mệt, ốm · ngủ ×2, thức ×2 |

```text
assets/source/tinh-linh/                 Ảnh gốc (nền hồng)
assets/creatures/KIEM-KE.md              Bảng kiểm kê: cấp nào xong / cần làm lại / chưa có
assets/creatures/<hệ>/<con>/<cấp>/
    png/  bmp/  bmp-flash/               Khung đã cắt (trong suốt / nền hồng cho SDL / chớp trắng)
    frames.json                          Cỡ khung, điểm chân, độ lệch từng khung
    anims.json                           Thời gian và chuyển động   <- sửa ở đây
assets/anim-templates/                   Chuyển động mẫu cho cấp mới (egg / young / adult)
preview/index.html                       Trang xem: chọn hệ > con > cấp
preview/<hệ>/<con>/<cấp>/*.gif           Ảnh động từng động tác
scripts/creatures.py                     Danh sách tự đọc từ tên file; REDO = file vẽ nhầm cần làm lại
src/main.c, platform/                    Chương trình xem động tác trên PocketGo (Hỏa Hổ)
```

## Dựng lại asset

```bash
python scripts/build_assets.py                 # tất cả
python scripts/build_assets.py moc             # một hệ
python scripts/build_assets.py moc-loc egg     # một con, một cấp
```

Các bước: cắt khung, căn chân, khung chớp trắng (và `src/anim_data.h` cho Hỏa Hổ), ảnh động, trang xem và bảng kiểm kê.

## Game Elemon cho R36S (Linux / WSL / macOS)

Cần Python 3 với `pillow numpy ziglang` (thêm `scipy` thì bước cắt khung nhanh hơn rất nhiều) và `curl`. Trên Windows dùng `scripts/build-r36s.ps1` như cũ.

```bash
pip install pillow numpy scipy ziglang
HOLUA_SCREEN=640 python3 scripts/build_assets.py   # cắt pet cỡ 640 (~8 phút)
python3 game/build_game.py                          # trang game -> build/game/
python3 scripts/r36s_game.py                        # gói dữ liệu -> dist/elemon/
scripts/build-r36s.sh game                          # file chạy ARM64 -> dist/elemon/elemon/elemon
```

Chép `dist/elemon/Elemon.sh` và thư mục `dist/elemon/elemon/` vào `ports/` của thẻ nhớ (phân vùng EASYROMS), rồi mở **Ports → Elemon**. Bản lưu nằm ở `ports/elemon-save/`, cài bản mới không mất. Giữ SELECT+START để thoát (game lưu trước khi thoát).

Không có Tahoma (máy không phải Windows): màn chỉ số dùng DejaVu Sans trong `assets/font/`.

## Biên dịch (WSL, SDK MiyooCFW ở /opt/miyoo)

```bash
cd /mnt/d/INDIEGAME/HoLua
make package     # -> dist/holua
make sim         # giả lập trên PC, ảnh chụp ở build/sim/shots
```

## Cài lên thẻ nhớ

Sao lưu thẻ trước, rồi trong PowerShell (thay `E:\` bằng ổ thẻ nhớ):

```powershell
.\scripts\install-to-pocketgo.ps1 -SdRoot E:\            # chỉ kiểm tra
.\scripts\install-to-pocketgo.ps1 -SdRoot E:\ -Install   # chép vào apps\holua + thêm vào menu Applications
```
