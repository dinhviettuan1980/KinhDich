#!/usr/bin/env bash
# Cập nhật sau mỗi lần git pull (được gọi từ ~/deploy-kinhdich.sh): cài thư viện, migrate, seed, restart.
set -euo pipefail
APP="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$APP"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r server/requirements.txt -r pi-agent/requirements.txt
# Sao lưu DB trước khi migrate/seed (bản sao nhất quán qua sqlite3 backup API; giữ 15 bản mới nhất)
DATA="${LINHDIA_DATA:-$HOME/linh-dia-viet-data}"
if [ -f "$DATA/linhdia.db" ]; then
  mkdir -p "$HOME/backups"
  .venv/bin/python -c 'import sqlite3, sys; s = sqlite3.connect(sys.argv[1]); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()' \
    "$DATA/linhdia.db" "$HOME/backups/linhdia-$(date +%Y%m%d-%H%M%S).db"
  ls -1t "$HOME"/backups/linhdia-*.db 2>/dev/null | tail -n +16 | xargs -r rm -f
fi
cd server
../.venv/bin/alembic upgrade head
../.venv/bin/python -m app.seed
if pm2 describe linhdia-api >/dev/null 2>&1; then pm2 restart linhdia-api --update-env >/dev/null; fi
echo "[deploy] linh-dia-viet done"
