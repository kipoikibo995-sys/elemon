-- Elemon online (Đấu trường: đấu với đội của người khác). Chạy một lần sau khi tạo D1:
--   npx wrangler d1 execute elemon-online --remote --file=schema.sql
CREATE TABLE IF NOT EXISTS players (
  id TEXT PRIMARY KEY,              -- 16 hex, máy tự tạo (save/mang-id.txt)
  key_hash TEXT NOT NULL,           -- sha256 của khóa bí mật máy giữ; ai không có khóa không ghi đè được đội
  name TEXT NOT NULL,               -- tên người chơi (tên pet đầu đội)
  team TEXT NOT NULL,               -- JSON: [{dir, ten, stage, lv, attr[6], chieu}], đã kiểm tra
  level INTEGER NOT NULL,           -- cấp cao nhất trong đội: để ghép đối thủ hợp cấp
  luc INTEGER NOT NULL,             -- Lực chiến cao nhất (máy chủ tự tính)
  rating INTEGER NOT NULL DEFAULT 1000,
  wins INTEGER NOT NULL DEFAULT 0, losses INTEGER NOT NULL DEFAULT 0,      -- khi mình đi đánh
  dwins INTEGER NOT NULL DEFAULT 0, dlosses INTEGER NOT NULL DEFAULT 0,    -- khi đội mình bị đánh (bot giữ)
  created INTEGER NOT NULL, updated INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS players_level ON players(level);
CREATE INDEX IF NOT EXISTS players_rating ON players(rating);

-- một trận: mở bằng /api/fight, đóng một lần bằng /api/result (không gửi kết quả bịa liên tục được)
CREATE TABLE IF NOT EXISTS fights (
  token TEXT PRIMARY KEY,
  attacker TEXT NOT NULL, defender TEXT NOT NULL, pet INTEGER NOT NULL,
  started INTEGER NOT NULL, done INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS fights_attacker ON fights(attacker, started);
