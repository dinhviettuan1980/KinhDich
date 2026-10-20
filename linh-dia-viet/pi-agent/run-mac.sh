#!/usr/bin/env bash
# "Pi giả" trên máy Mac/PC: nhận lệnh từ server thật và PHÁT RA LOA máy tính (ffplay), ảnh mâm lễ là ảnh giả.
#   ./run-mac.sh start | stop | status | log
# Cấu hình ở pi-agent/.env.mac (không commit; chứa token thiết bị). Mẫu: .env.mac.example
set -euo pipefail
cd "$(dirname "$0")"
PY="${PY:-../.venv/bin/python}"
RUN=${LD_RUN_DIR:-$HOME/.linh-dia-viet-pi}
mkdir -p "$RUN"
case "${1:-start}" in
  start)
    [ -f .env.mac ] || { echo "Thiếu pi-agent/.env.mac (chép từ .env.mac.example rồi điền token)"; exit 1; }
    if [ -f "$RUN/agent.pid" ] && kill -0 "$(cat "$RUN/agent.pid")" 2>/dev/null; then echo "Đang chạy (pid $(cat "$RUN/agent.pid"))"; exit 0; fi
    nohup "$PY" -m ld_agent --env .env.mac >> "$RUN/agent.log" 2>&1 &
    echo $! > "$RUN/agent.pid"; sleep 3; tail -3 "$RUN/agent.log" ;;
  stop)
    [ -f "$RUN/agent.pid" ] && kill "$(cat "$RUN/agent.pid")" 2>/dev/null && rm -f "$RUN/agent.pid" && echo "Đã dừng" || echo "Không chạy" ;;
  status)
    [ -f "$RUN/agent.pid" ] && kill -0 "$(cat "$RUN/agent.pid")" 2>/dev/null && echo "Đang chạy (pid $(cat "$RUN/agent.pid"))" || echo "Không chạy" ;;
  log) tail -f "$RUN/agent.log" ;;
esac
