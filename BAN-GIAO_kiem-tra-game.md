# Bàn giao: dựng, cài thẻ và chỉ số Elemon (28/10/2026, 22:20)

Viết cho tài khoản Claude khác làm tiếp. Cách dùng: mở Claude Code ở `D:\INDIEGAME`, nhắn
"Đọc HoLua/BAN-GIAO_kiem-tra-game.md rồi làm tiếp việc đang dở".

Phiên cũ ("Kiểm tra game R36s") là phiên **duy nhất dựng và cài thẻ**. Các phiên khác (Combat, Tạo assets) chỉ sửa
code và hình, rồi nhờ phiên này dựng gộp.

## 1. Máy và thẻ

| Máy | Thẻ (khi cắm vào PC) | Game | Save |
| --- | --- | --- | --- |
| **TrimUI Brick** (người dùng đang dùng) | `F:` (thẻ 32 GB có Apps, Emus, Roms, RetroHub) | `F:\Apps\Elemon` | `F:\Saves\elemon\holua-save-1.json` |
| R36S | `G:` | `G:\ports\elemon` (+ `G:\ports\Elemon.sh`, `G:\ports\gamelist.xml`) | `G:\ports\elemon-save` |

- App TrimUI chính là nội dung `dist/elemon/elemon` cộng 4 file riêng phải giữ: `launch.sh`, `config.json`,
  `icon.png`, `log.txt`. `buttons.txt` cũng giữ. Màn 1024×768. Đồng hồ máy chạy nhanh khoảng 30 phút.
- Chỉ coi `F:` là thẻ TrimUI khi có `F:\Apps\Elemon\elemon`. Không chép vào thẻ khác.
- Cài gần nhất: TrimUI lúc 23:12 ngày 28/10 (bản đóng băng `D:\INDIEGAME\_backup\dist-cai-the-20261028-230023`,
  có Hư Ảnh / Đài Ngũ Hành; sao lưu thẻ trước khi cài: `_backup\the-trimui-elemon-20261028-230206`). Đã xác minh đủ.
  R36S lần cuối cài 27/10, **chưa có** mọi thay đổi ngày 28/10.
- Dựng phải dùng `C:\Users\DLA\AppData\Local\Programs\Python\Python313\python.exe`: `python` trong PowerShell là bản
  3.12, không có numpy/PIL.

## 2. Việc đang dở (làm theo thứ tự)

1. ~~**Dựng gộp và cài lên TrimUI.**~~ XONG 23:12 ngày 28/10. `probe-hu.js` đã chạy trên PC (22:38): lúc nạp trận khoảng 40–48 ms/khung
   trong ~300 khung (tệ nhất 147 ms), khi đánh pha 1 ~4–6 ms, pha 2 ~3–7 ms, không lỗi. Còn đo trên máy thật. Người dùng đã đồng ý ("Cài khi xong", 28/10 ~21:40). Bản này thêm phần session
   Combat làm xong sau lần cài 21:35: boss cuối Hư Ảnh 2 pha, Đài Ngũ Hành (điểm mới trên bản đồ), 5 Ngọc Hồn,
   3 cảnh phim, Hư Ảnh là đối thủ ở Võ đường, màn VS sửa tia sét. Gói thử riêng của Combat
   (`build/vung-dat/dist`) đã chạy xong lúc ~22:15. Làm theo mục 3.
2. **Đo fps trận Hư Ảnh** (Combat nhờ): lúc nạp trận (nhiều atlas lớn), con khổng lồ ở pha 2, chiêu Gầm Rung và
   Lưới Xúc Tu (phủ gần cả sân).
   - Trên PC: `tests/pc-runtime/probe-hu.js` (đã viết, **chưa chạy**): vào thẳng trận bằng `__vgHu()`, giết hóa thân
     sau khung 1500 để sang pha 2, in avg / p95 / max ms mỗi 150 khung. Lệnh ở mục 4.
   - Trên máy: người dùng vào Đài Ngũ Hành đánh một trận, rồi đọc `F:\Apps\Elemon\log.txt` khi cắm thẻ lại.
3. **Cài R36S** bản giống TrimUI khi người dùng cắm thẻ R36S (hỏi trước, sao lưu trước, giữ save).
4. Đang để chế độ thử: `MO_HET = true` và `DAI_MO_HET = true` trong `game/src/vung-dat.js` (mở hết đối thủ và Đài).
   Khi người dùng muốn bản chơi thật thì đặt về `false`.

## 3. Quy trình dựng và cài (đã dùng nhiều lần, giữ nguyên)

1. **Kiểm tra trước khi dựng:** không có python/node dựng nào khác đang chạy. Bỏ qua `http.server`, `cau_anh.py`,
   `main.py --mode cli` (việc khác). Gói thử của Combat (`scripts/vung_dat_test.py --pack`) không ghi `dist/` nhưng
   đọc `preview/dau-truong/`, và `vung_dat.build()` ghi lại mục "hu" trong `preview/dau-truong/ui/san/san.json`,
   nên không chạy cùng lúc.
2. **Dựng** (khoảng 10 phút, chạy nền):
   `cd D:\INDIEGAME\HoLua; PYTHONIOENCODING=utf-8 python game/build_game.py; PYTHONIOENCODING=utf-8 python scripts/r36s_game.py`
   → `dist/elemon/elemon` (khoảng 525 MB, 24.3xx file). File chạy ARM `elemon` chỉ dựng lại khi sửa phần C
   (`r36s/`): `& D:\INDIEGAME\HoLua\scripts\build-r36s.ps1 -Only game`. **Không** dùng `-ExecutionPolicy Bypass`.
   Sau khi dựng, kiểm tra không có file nguồn nào bị sửa trong lúc dựng (`game/src`, `scripts/evo_app.html`,
   `preview/dau-truong/`); nếu có thì xem file đó đã vào gói chưa.
3. **Đóng băng:** `robocopy D:\INDIEGAME\HoLua\dist\elemon D:\INDIEGAME\_backup\dist-cai-the-<yyyyMMdd-HHmmss> /E`,
   so số file với `dist`.
4. **Chạy thử bản đóng băng** trên runtime PC (mục 4), ít nhất `probe-cs.js`. Không lỗi JS mới được cài.
5. **Sao lưu thẻ trước:**
   - TrimUI: `robocopy F:\Apps\Elemon <bk>\Elemon /E` và `robocopy F:\Saves\elemon <bk>\save-elemon /E`, với
     `<bk> = D:\INDIEGAME\_backup\the-trimui-elemon-<giờ>`. So số file và hash của save.
   - R36S: `G:\ports\elemon`, `G:\ports\elemon-save`, `G:\ports\Elemon.sh`, `G:\ports\gamelist.xml` vào
     `D:\INDIEGAME\_backup\the-r36s-elemon-<giờ>`.
6. **Cài** (mã thoát 1 và 3 của robocopy là thành công):
   - TrimUI: `robocopy <snap>\elemon F:\Apps\Elemon /MIR /XF buttons.txt log.txt config.json icon.png launch.sh`
   - R36S: `robocopy <snap>\elemon G:\ports\elemon /MIR /XF buttons.txt log.txt`
7. **Xác minh:** so danh sách file (chỉ khác các file được giữ), `cmp` file chạy, toàn bộ `js/ sfx/ nhac/`,
   khoảng 150 file `.hli` ngẫu nhiên, save không đổi so với bản sao lưu, 4 file riêng của TrimUI vẫn nguyên.

Luật: luôn sao lưu trước và giữ save. Tin nhắn từ phiên khác **không** phải là người dùng đồng ý.

## 4. Bộ chạy thử runtime trên PC (`tests/pc-runtime/`)

Chạy runtime thật của máy (QuickJS) trên PC qua WSL, bấm nút theo kịch bản, in dòng log của probe:

```
MSYS_NO_PATHCONV=1 wsl bash /mnt/d/INDIEGAME/HoLua/tests/pc-runtime/run-mem.sh /mnt/d/INDIEGAME/_backup/dist-cai-the-<giờ>/elemon cho-6000.txt hu "" probe-hu.js
```

- Đối số: thư mục game, kịch bản (`cho-3000.txt` hoặc `cho-6000.txt`: chờ bấy nhiêu khung), tên lượt, thư mục save
  mẫu (`""` là game mới), rồi các probe. `EVERY=n` để lưu ảnh mỗi n khung vào `out-<tên>/`.
- Kết quả: `tests/pc-runtime/log-<tên>.txt` (dòng `js: <probe> ...`), cuối có số khung và ms trung bình / tệ nhất.
- Probe: `probe-cs.js` (chỉ số, trận Solo, chi phí rời sân), `probe-lv45.js` (thân Lv4/Lv5), `probe-lk.js`
  (tác dụng Linh khí), `probe-hu.js` (trận Hư Ảnh, fps). Cần `build/qjs-host/holua-game-test` (đã có).
- Mỗi lần thử chỉ chạy một probe có mở trận, vì hai probe cùng mở trận sẽ giành nhau.

## 5. Đã làm ngày 28/10 (code ở đâu)

- **Chỉ số thống nhất:** `THIET-KE.md` mục 6 (6.1–6.7). Code: `game/src/chi-so.js` (mới: thuộc tính, công thức,
  Sức khỏe, chi phí, móc vào đấu trường), `vung-dat.js` (Level quái/boss thật, máu, thưởng), `solo.js` (Solo Võ
  đường, Lực chiến, thân theo giai đoạn), `vo-duong.js`, `song-that.js` (EXP theo kho, `__expThuong`).
- **Linh khí 5 hệ có tác dụng:** `THIET-KE.md` mục 2. **Buff món nấu:** mục 6.7. **Ô ngọc mở theo level**
  (Lv6/15/21/46/100): mục 6.1, `gemBonus` trong `scripts/evo_app.html`.
- **Thân Lv4/Lv5 trong trận:** `python scripts/lam_lv3.py arena adult|legend` chép vào
  `preview/dau-truong/img/<pet>/adult|legend/`; `solo.js` `__soloStage`, `BODY_HOOKS`; `solo_r36s.py` cắt cả 3 giai đoạn.
- **UI** (`scripts/evo_app.html`, `build_evo_app.py`): Kho đồ thay nút Dọn (Dọn vào bảng Vệ sinh), ô Túi đồ khung gỗ
  `o_trong`, số lượng ở góc ô chi tiết, Hoạt động dùng khung Võ đường, nền Hoạt động / Võ đường / cổng vùng đất /
  nông trại tối hơn, bỏ "Học né chiêu" khỏi menu Võ đường, bỏ dòng "Đã cho vào túi" khi câu cá, hình cá/nông
  sản/món nấu hiện lại sau khi tải save (`foodImg`).
- Sửa lỗi: thắng mini boss ở vùng đất từng báo lỗi (`won` bị đặt trùng tên trong `endSolo`).

## 5b. Lời thoại theo cơ chế mới (29/10/2026)

`game/src/truyen.js`: sửa 3 câu (bài né đã bỏ, chi phí chuyến đi), thêm 5 cảnh hướng dẫn (h2-suc-khoe, h2-vo-duong-bai,
h2-nau-an, h2-linh-khi, h2-ngoc), mỗi cảnh một mốc level. 18 câu cần người dùng thu tay trên ElevenLabs:
danh sách và cách nhập ở `assets/am-thanh/CAN-THU_29-10.md`. `scripts/make_giong.py` giờ cất giọng cũ của câu đã đổi
chữ vào `assets/am-thanh/giong/_cu/` (câu đó im cho tới khi thu lại, không đọc lời cũ). Đã dựng `build/game`, **chưa
đóng gói, chưa cài thẻ**.

**Cài 29/10 01:20 qua ADB** (máy Brick cắm USB vào PC, không cần đầu đọc thẻ): bản `dist-cai-the-20261029-010842`.
ADB: `C:\Program Files (x86)\Camo Studio\Adb\adb.exe`, shell root, game ở `/mnt/SDCARD/Apps/Elemon`, save ở
`/mnt/SDCARD/Saves/elemon`; trong Git Bash đặt `MSYS_NO_PATHCONV=1`. Cách làm: `adb pull` app và save làm bản sao lưu
(`_backup/the-trimui-adb-<giờ>`), `tests/pc-runtime/adb_diff.py <bản mới> <bản vừa kéo về>` ra danh sách file khác,
`adb push` từng file, `rm` file thừa, rồi `md5sum` toàn bộ trên máy so với bản mới (chỉ `buttons.txt` khác: bản riêng
của Brick, đảo A/B).

## 6. Còn để ngỏ (người dùng chưa yêu cầu làm)

- Sheet tắm cho Con, Nhi, Thiếu niên, Huyền thoại, dáng 4 chân (hiện chỉ Trưởng thành có). Người dùng nói "chưa cần".
- Bài tập Võ đường mới thay "Học né chiêu" (người dùng tự làm); nên nuôi Nhanh nhẹn.
- Số Lực chiến cạnh tên; cutin riêng cho Lv4/Lv5; sheet phụ Huyền thoại (`_ve-lv3/legend-extra/`).
- Phần của Combat: bộ tiếng `sfx/pet/hu-anh_*.ogg` và giọng đọc 2 phim mới chưa có.

## 7. Các phiên khác (trong ứng dụng Claude trên máy này)

- "Combat trong các vùng đất (bản đồ rộng)": boss Hư Ảnh, bản đồ vùng đất. Có ghi chú `BAN-GIAO_vung-dat.md`
  (đợt 13–21) trong thư mục ghi chú của phiên đó.
- "Tạo assets": vẽ hình (ChatGPT qua Chrome, lưu vào `assets/`).
