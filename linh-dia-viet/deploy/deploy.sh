#!/usr/bin/env bash
# Deploy Linh Địa Việt (+ tuỳ chọn build lại frontend Kinh Dịch) lên VPS.
#
#   DEPLOY_HOST=root@103.163.216.32 ./deploy/deploy.sh          # chỉ app /le-chua
#   DEPLOY_HOST=root@103.163.216.32 ./deploy/deploy.sh --fe     # + build & đẩy frontend Kinh Dịch
#
# Yêu cầu trên máy chủ: Docker + compose, nginx, chứng chỉ Let's Encrypt cho $LD_DOMAIN. Xem deploy/DEPLOY.md.
set -euo pipefail
HOST="${DEPLOY_HOST:?Đặt DEPLOY_HOST=user@host}"
REMOTE_DIR="${REMOTE_DIR:-/opt/linh-dia-viet}"
FE_DIR="${FE_DIR:-/var/www/kinhdich}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
WITH_FE=0
[ "${1:-}" = "--fe" ] && WITH_FE=1

echo "==> Kiểm tra máy chủ $HOST"
ssh "$HOST" 'docker compose version >/dev/null 2>&1 || { echo "Thiếu docker compose trên máy chủ"; exit 1; }'

echo "==> Đồng bộ mã nguồn → $REMOTE_DIR"
ssh "$HOST" "mkdir -p '$REMOTE_DIR'"
rsync -az --delete \
  --exclude '.venv/' --exclude 'data/' --exclude '__pycache__/' --exclude '.pytest_cache/' \
  --exclude '/.env' --exclude 'mosquitto/extra/devices.passwd*' --exclude 'pi-agent/data/' \
  "$HERE/" "$HOST:$REMOTE_DIR/"

echo "==> Cấu hình (.env) lần đầu"
ssh "$HOST" "cd '$REMOTE_DIR' && if [ ! -f .env ]; then
  cp .env.prod.example .env
  r() { openssl rand -hex 24; }
  ADMIN_PW=\$(openssl rand -base64 12 | tr -d '/+=')
  sed -i \"s|^SECRET_KEY=.*|SECRET_KEY=\$(r)|; s|^MQTT_PASSWORD=.*|MQTT_PASSWORD=\$(r)|; s|^DEMO_DEVICE_TOKEN=.*|DEMO_DEVICE_TOKEN=\$(r)|; s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=\$ADMIN_PW|\" .env
  chmod 600 .env
  echo \"   Đã tạo .env. Tài khoản admin: \$(grep ^ADMIN_EMAIL= .env | cut -d= -f2) / \$ADMIN_PW  (ghi lại ngay, chỉ hiện 1 lần)\"
else echo '   Giữ nguyên .env hiện có'; fi
mkdir -p mosquitto/extra && chown 10001 mosquitto/extra 2>/dev/null || true"

echo "==> Build & chạy container"
ssh "$HOST" "cd '$REMOTE_DIR' && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build"

echo "==> Kiểm tra sức khỏe"
PORT=$(ssh "$HOST" "grep -E '^LD_API_BIND=' '$REMOTE_DIR/.env' | cut -d: -f2" || true)
PORT=${PORT:-8042}
for i in $(seq 1 20); do
  if ssh "$HOST" "curl -fsS http://127.0.0.1:$PORT/le-chua/healthz" >/dev/null 2>&1; then echo "   API OK (cổng $PORT)"; break; fi
  sleep 3
  [ "$i" = 20 ] && { echo "   API chưa lên — xem: ssh $HOST 'cd $REMOTE_DIR && docker compose logs --tail 50 api'"; exit 1; }
done

if [ "$WITH_FE" = 1 ]; then
  echo "==> Build frontend Kinh Dịch"
  (cd "$REPO" && npm run build)
  echo "==> Đẩy dist → $HOST:$FE_DIR"
  rsync -az --delete "$REPO/dist/" "$HOST:$FE_DIR/"
fi

echo "==> nginx"
ssh "$HOST" "mkdir -p /etc/nginx/snippets && sed 's/127.0.0.1:8000/127.0.0.1:$PORT/' '$REMOTE_DIR/docs/nginx-le-chua.conf' > /etc/nginx/snippets/le-chua.conf"
if ssh "$HOST" "grep -rqs 'snippets/le-chua.conf' /etc/nginx/sites-enabled/ /etc/nginx/conf.d/"; then
  ssh "$HOST" "nginx -t && systemctl reload nginx" && echo "   nginx đã nạp lại"
else
  echo "   !! Thêm 1 dòng vào server { } của tuandv.id.vn (HTTPS) rồi chạy 'nginx -t && systemctl reload nginx':"
  echo "      include /etc/nginx/snippets/le-chua.conf;"
  echo "   và mở cổng 8883/tcp cho thiết bị (ufw allow 8883/tcp)."
fi
DOMAIN=$(ssh "$HOST" "grep -E '^LD_DOMAIN=' '$REMOTE_DIR/.env' | cut -d= -f2")
echo "Xong: https://${DOMAIN:-tuandv.id.vn}/le-chua/"
