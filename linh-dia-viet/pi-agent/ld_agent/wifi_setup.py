"""Chế độ cài Wi-Fi tại đền, không cần máy tính / SSH.

Mất mạng liên tục SETUP_AFTER giây (lắp ở đền mới, đền đổi mật khẩu Wi-Fi...) → Pi tự phát Wi-Fi
"LinhDia-Setup-<mã>" (có mật khẩu). Điện thoại vào mạng đó → trang cài đặt tự bật lên (captive portal):
chọn Wi-Fi của đền, nhập mật khẩu → Pi lưu (ưu tiên cao nhất) và thử kết nối. Sai thì phát lại Wi-Fi cài đặt, báo lỗi.
Khi Wi-Fi cài đặt bật mà không ai dùng trang trong RETRY_IDLE giây → tắt đi, thử lại các mạng đã biết.

Chạy bằng root (cần nmcli): python -m ld_agent.wifi_setup --env /etc/linh-dia-viet/agent.env
"""
import argparse
import html
import logging
import re
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from .config import load_env_file

log = logging.getLogger("ld_agent.wifi_setup")

AP_CON = "ld-setup-ap"
AP_IP = "10.42.0.1"
DNSMASQ_CONF = Path("/etc/NetworkManager/dnsmasq-shared.d/ld-setup.conf")  # mọi tên miền → Pi (bật trang cài đặt)


def nm(*args: str, timeout: float = 60) -> subprocess.CompletedProcess:
    return subprocess.run(["nmcli", *args], capture_output=True, text=True, timeout=timeout)


class WifiSetup:
    def __init__(self, device_id: str, password: str, setup_after: float = 180, retry_idle: float = 600,
                 run=nm, clock=time.monotonic):
        self.ssid = "LinhDia-Setup-" + (device_id.removeprefix("pi-")[:12] or "pi")
        self.password = password if len(password) >= 8 else "linhdiaviet"  # WPA2 cần ≥ 8 ký tự
        self.setup_after, self.retry_idle, self.run, self.clock = setup_after, retry_idle, run, clock
        self.device_id = device_id
        self.offline_since: float | None = None
        self.ap_on = False
        self.last_seen_user = 0.0  # lần cuối có người mở trang cài đặt
        self.networks: list[dict] = []  # Wi-Fi dò được trước khi bật AP (đang phát AP thì không dò được)
        self.message = ""  # kết quả lần lưu gần nhất, hiện trên trang
        self.lock = threading.Lock()

    # ---------------- trạng thái mạng ----------------

    def online(self) -> bool:
        """Có kết nối Wi-Fi/dây nào đang chạy (không tính AP cài đặt)."""
        r = self.run("-t", "-f", "NAME,TYPE", "connection", "show", "--active")
        for line in r.stdout.splitlines():
            name, _, typ = line.rpartition(":")
            if name != AP_CON and typ in ("802-11-wireless", "802-3-ethernet"):
                return True
        return False

    def scan(self) -> list[dict]:
        r = self.run("-t", "-e", "no", "-f", "SIGNAL,SECURITY,SSID", "device", "wifi", "list", "--rescan", "yes")
        best: dict[str, dict] = {}
        for line in r.stdout.splitlines():
            parts = line.split(":", 2)
            if len(parts) != 3 or not parts[2] or parts[2].startswith("LinhDia-Setup"):
                continue
            sig = int(parts[0]) if parts[0].isdigit() else 0
            if parts[2] not in best or sig > best[parts[2]]["signal"]:
                best[parts[2]] = {"ssid": parts[2], "signal": sig, "secure": parts[1] not in ("", "--")}
        return sorted(best.values(), key=lambda n: -n["signal"])

    # ---------------- vòng kiểm tra ----------------

    def tick(self) -> None:
        with self.lock:
            now = self.clock()
            if self.ap_on:
                if now - self.last_seen_user >= self.retry_idle:  # không ai cài → thử lại mạng cũ (router vừa bật lại?)
                    log.info("Không ai dùng trang cài đặt — tắt %s, thử lại các mạng đã biết", self.ssid)
                    self.stop_ap()
                    self.offline_since = now
                return
            if self.online():
                self.offline_since = None
                return
            if self.offline_since is None:
                self.offline_since = now
            elif now - self.offline_since >= self.setup_after:
                self.start_ap()

    def start_ap(self) -> None:
        self.networks = self.scan() or self.networks
        self.run("connection", "delete", AP_CON)
        self.run("connection", "add", "type", "wifi", "ifname", "wlan0", "con-name", AP_CON, "autoconnect", "no",
                 "ssid", self.ssid, "802-11-wireless.mode", "ap", "802-11-wireless.band", "bg",
                 "ipv4.method", "shared", "ipv4.addresses", f"{AP_IP}/24", "ipv6.method", "disabled",
                 "wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", self.password)
        r = self.run("connection", "up", AP_CON)
        self.ap_on = r.returncode == 0
        self.last_seen_user = self.clock()
        log.warning("Mất mạng — %s Wi-Fi cài đặt %s", "đã phát" if self.ap_on else "KHÔNG phát được", self.ssid)

    def stop_ap(self) -> None:
        self.run("connection", "down", AP_CON)
        self.ap_on = False

    # ---------------- lưu Wi-Fi của đền ----------------

    @staticmethod
    def con_name(ssid: str) -> str:
        return "ld-wifi-" + (re.sub(r"[^A-Za-z0-9]+", "-", ssid).strip("-").lower()[:24] or "x")

    def save(self, ssid: str, psk: str) -> str | None:
        """Lưu + thử kết nối (gọi trong luồng riêng). Trả lỗi hoặc None nếu vào được mạng."""
        if not ssid or len(ssid) > 32:
            return "Tên Wi-Fi không hợp lệ"
        if psk and not 8 <= len(psk) <= 63:
            return "Mật khẩu Wi-Fi phải từ 8 đến 63 ký tự"
        name = self.con_name(ssid)
        with self.lock:
            self.run("connection", "delete", name)
            sec = ["wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", psk] if psk else []
            r = self.run("connection", "add", "type", "wifi", "ifname", "wlan0", "con-name", name, "ssid", ssid,
                         "connection.autoconnect", "yes", "connection.autoconnect-priority", "50", *sec)
            if r.returncode != 0:
                return "Không lưu được cấu hình: " + (r.stderr or r.stdout).strip()[:120]
            self.stop_ap()
            r = self.run("--wait", "45", "connection", "up", name, timeout=60)
            if r.returncode == 0:
                self.message, self.offline_since = f"Đã kết nối Wi-Fi “{ssid}”.", None
                log.info("Đã vào Wi-Fi %s", ssid)
                return None
            log.warning("Không vào được Wi-Fi %s: %s", ssid, (r.stderr or r.stdout).strip()[:200])
            self.message = f"Không kết nối được “{ssid}”. Kiểm tra lại mật khẩu, và Wi-Fi phải có băng 2.4 GHz."
            self.start_ap()
            return self.message

    # ---------------- trang cài đặt ----------------

    def page(self) -> str:
        e = html.escape
        opts = "".join(f'<label class="n"><input type="radio" name="ssid" value="{e(n["ssid"])}" required> '
                       f'<b>{e(n["ssid"])}</b> <small>{"🔒" if n["secure"] else "mở"} · sóng {n["signal"]}%</small></label>'
                       for n in self.networks) or "<p>Không dò thấy Wi-Fi nào. Nhập tên Wi-Fi bên dưới.</p>"
        msg = f'<p class="m">{e(self.message)}</p>' if self.message else ""
        return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Cài Wi-Fi · Linh Địa Việt</title>
<style>body{{font:16px system-ui,-apple-system,sans-serif;margin:0;background:#faf6ee;color:#2b1d14}}
h1{{background:#7a1f1f;color:#fff;margin:0;padding:16px;font-size:20px}}main{{padding:16px;max-width:480px;margin:auto}}
.n{{display:block;background:#fff;border:1px solid #e6dccb;border-radius:10px;padding:12px;margin:8px 0}}
.n small{{color:#6f5f52}}input[type=text],input[type=password]{{width:100%;box-sizing:border-box;padding:12px;
font-size:16px;border:1px solid #e6dccb;border-radius:10px;margin:6px 0 12px}}button{{width:100%;padding:14px;
font-size:17px;background:#7a1f1f;color:#fff;border:0;border-radius:10px}}.m{{background:#fff3cd;padding:12px;
border-radius:10px}}.h{{color:#6f5f52;font-size:14px}}</style></head><body>
<h1>Cài Wi-Fi cho thiết bị {e(self.device_id)}</h1><main>{msg}
<form method="post" action="/luu"><p><b>Chọn Wi-Fi của đền</b></p>{opts}
<p class="h">Không thấy trong danh sách (Wi-Fi ẩn)? Nhập tên:</p>
<input type="text" name="ssid_tay" placeholder="Tên Wi-Fi" autocomplete="off" autocapitalize="none">
<p><b>Mật khẩu Wi-Fi</b></p><input type="password" name="psk" placeholder="Để trống nếu Wi-Fi không có mật khẩu">
<button>Kết nối</button></form>
<p class="h">Thiết bị chỉ bắt được Wi-Fi băng 2.4 GHz. Sau khi bấm Kết nối, điện thoại sẽ rời mạng {e(self.ssid)}.
Nếu sau 2 phút mạng {e(self.ssid)} xuất hiện lại tức là chưa kết nối được — vào lại để xem lỗi.</p></main></body></html>"""

    def handler(self):
        setup = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, body: str, code: int = 200):
                data = body.encode()
                self.send_response(code)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _closed(self) -> bool:
                """Chỉ mở khi đang phát Wi-Fi cài đặt — không cho người trong mạng đền đổi Wi-Fi của thiết bị."""
                if setup.ap_on:
                    setup.last_seen_user = setup.clock()
                    return False
                self._send("<h1>404</h1>", 404)
                return True

            def do_GET(self):  # mọi đường dẫn (kể cả captive.apple.com/hotspot-detect.html) → trang cài đặt
                if not self._closed():
                    self._send(setup.page())

            def do_POST(self):
                if self._closed():
                    return
                n = min(int(self.headers.get("Content-Length") or 0), 4096)
                f = parse_qs(self.rfile.read(n).decode(errors="ignore"))
                ssid = (f.get("ssid_tay", [""])[0] or f.get("ssid", [""])[0]).strip()
                psk = f.get("psk", [""])[0]
                if not ssid:
                    setup.message = "Chưa chọn Wi-Fi."
                    return self._send(setup.page())
                self._send(f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<body style="font:17px system-ui;padding:24px;background:#faf6ee"><h2>Đang kết nối “{html.escape(ssid)}”…</h2>
<p>Điện thoại sẽ rời mạng {html.escape(setup.ssid)}. Khoảng 1 phút sau, thiết bị sẽ hiện “Đang trực tuyến” trên trang quản lý.</p></body>""")
                threading.Timer(2, setup.save, args=(ssid, psk)).start()  # trả trang trước rồi mới tắt AP
        return H


def install_dnsmasq_redirect() -> None:
    """Khi phát AP, trả mọi tên miền về Pi → điện thoại tự bật trang cài đặt."""
    try:
        DNSMASQ_CONF.parent.mkdir(parents=True, exist_ok=True)
        want = f"address=/#/{AP_IP}\n"
        if not DNSMASQ_CONF.exists() or DNSMASQ_CONF.read_text() != want:
            DNSMASQ_CONF.write_text(want)
    except OSError as e:
        log.warning("Không ghi được %s: %s", DNSMASQ_CONF, e)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ld_agent.wifi_setup")
    ap.add_argument("--env", type=Path, default=Path("/etc/linh-dia-viet/agent.env"))
    ap.add_argument("--port", type=int, default=80)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    env = load_env_file(args.env)
    setup = WifiSetup(env.get("LD_DEVICE_ID", "pi"), env.get("LD_SETUP_PASSWORD", "linhdiaviet"),
                      float(env.get("LD_SETUP_AFTER_SECONDS", 180)), float(env.get("LD_SETUP_RETRY_IDLE_SECONDS", 600)))
    install_dnsmasq_redirect()
    srv = ThreadingHTTPServer(("0.0.0.0", args.port), setup.handler())
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log.info("Theo dõi mạng; mất mạng %ss sẽ phát Wi-Fi cài đặt %s", setup.setup_after, setup.ssid)
    while True:
        try:
            setup.tick()
        except Exception as e:  # nmcli lỗi tạm thời: không được làm chết dịch vụ
            log.error("Lỗi kiểm tra mạng: %s", e)
        time.sleep(20)


if __name__ == "__main__":
    raise SystemExit(main())
