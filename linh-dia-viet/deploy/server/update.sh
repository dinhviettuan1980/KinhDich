#!/usr/bin/env bash
# Cập nhật sau mỗi lần git pull (được gọi từ ~/deploy-kinhdich.sh): cài thư viện, migrate, seed, restart.
set -euo pipefail
APP="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$APP"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r server/requirements.txt -r pi-agent/requirements.txt
cd server
../.venv/bin/alembic upgrade head
../.venv/bin/python -m app.seed
if pm2 describe linhdia-api >/dev/null 2>&1; then pm2 restart linhdia-api --update-env >/dev/null; fi
echo "[deploy] linh-dia-viet done"
