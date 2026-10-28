"""Chế độ cài Wi-Fi: mất mạng → phát LinhDia-Setup, lưu Wi-Fi đền, sai mật khẩu thì phát lại."""
import subprocess
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from urllib.parse import urlencode

from ld_agent.wifi_setup import AP_CON, WifiSetup


class FakeNM:
    def __init__(self):
        self.active = ["IMIP:802-11-wireless"]
        self.calls, self.up_ok = [], True
        self.scan = "80:WPA2:Chua Tran Quoc\n55:WPA2:Chua Tran Quoc\n40::Khach\n30:WPA2:LinhDia-Setup-x\n20:WPA2:a:b\n"

    def __call__(self, *args, timeout=60):
        self.calls.append(args)
        out, rc = "", 0
        if args[:3] == ("-t", "-f", "NAME,TYPE"):
            out = "\n".join(self.active)
        elif "wifi" in args and "list" in args:
            out = self.scan
        elif "up" in args:
            name = args[-1]
            rc = 0 if (name == AP_CON or self.up_ok) else 4
            if rc == 0:
                self.active = [f"{name}:802-11-wireless"]
        elif "down" in args:
            self.active = [a for a in self.active if not a.startswith(args[-1] + ":")]
        return subprocess.CompletedProcess(args, rc, out, "Secrets were required" if rc else "")


def make(nm, t):
    return WifiSetup("pi-tranquoc-01", "matkhau123", setup_after=180, retry_idle=600, run=nm, clock=lambda: t["now"])


def test_ap_only_after_offline_for_a_while():
    nm, t = FakeNM(), {"now": 0}
    s = make(nm, t)
    s.tick()
    assert not s.ap_on and s.offline_since is None
    nm.active = []  # mất Wi-Fi
    s.tick()
    t["now"] = 100
    s.tick()
    assert not s.ap_on  # chưa đủ 3 phút (router đền khởi động lại thì không phát)
    t["now"] = 181
    s.tick()
    assert s.ap_on and s.ssid == "LinhDia-Setup-tranquoc-01"
    add = next(c for c in nm.calls if c[:2] == ("connection", "add") and AP_CON in c)
    assert "ap" in add and "shared" in add and "matkhau123" in add
    assert [n["ssid"] for n in s.networks] == ["Chua Tran Quoc", "Khach", "a:b"]  # gộp trùng, bỏ AP của mình, SSID có ':'
    assert s.networks[0]["signal"] == 80 and s.networks[1]["secure"] is False


def test_idle_ap_retries_known_networks():
    nm, t = FakeNM(), {"now": 0}
    s = make(nm, t)
    nm.active = []
    s.tick()
    t["now"] = 200
    s.tick()
    assert s.ap_on
    t["now"] = 200 + 601
    s.tick()
    assert not s.ap_on and ("connection", "down", AP_CON) in nm.calls


def test_save_success_and_wrong_password():
    nm, t = FakeNM(), {"now": 0}
    s = make(nm, t)
    s.ap_on = True
    assert s.save("Chua Tran Quoc", "short") == "Mật khẩu Wi-Fi phải từ 8 đến 63 ký tự"
    assert s.save("Chua Tran Quoc", "dung-mat-khau") is None
    add = next(c for c in nm.calls if c[:2] == ("connection", "add") and "ld-wifi-chua-tran-quoc" in c)
    assert "50" in add and "dung-mat-khau" in add  # ưu tiên cao hơn mạng cũ
    assert not s.ap_on and "Đã kết nối" in s.message
    nm.up_ok = False
    assert "Không kết nối được" in s.save("Chua Tran Quoc", "sai-mat-khau")
    assert s.ap_on  # sai → phát lại Wi-Fi cài đặt để sửa


def test_portal_only_while_ap_on():
    nm, t = FakeNM(), {"now": 0}
    s = make(nm, t)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), s.handler())
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_port}"
    try:
        try:
            urllib.request.urlopen(url + "/hotspot-detect.html")
            raise AssertionError("phải 404 khi đang có mạng")
        except urllib.error.HTTPError as e:
            assert e.code == 404
        s.ap_on, s.networks = True, [{"ssid": "<script>", "signal": 50, "secure": True}]
        page = urllib.request.urlopen(url + "/hotspot-detect.html").read().decode()
        assert "Cài Wi-Fi cho thiết bị pi-tranquoc-01" in page and "&lt;script&gt;" in page
        saved = []
        s.save = lambda ssid, psk: saved.append((ssid, psk))
        body = urlencode({"ssid": "Chua Tran Quoc", "ssid_tay": "", "psk": "dung-mat-khau"}).encode()
        r = urllib.request.urlopen(url + "/luu", data=body).read().decode()
        assert "Đang kết nối" in r
        threading.Event().wait(2.5)
        assert saved == [("Chua Tran Quoc", "dung-mat-khau")]
    finally:
        srv.shutdown()
