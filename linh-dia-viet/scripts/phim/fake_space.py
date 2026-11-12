"""AI nhận diện mâm lễ GIẢ cho bản quay giả lập: thấy đủ mọi món, trừ món thiết bị giả đánh dấu "chưa bày"
(LD-MISSING trong chú thích JPEG)."""
import json, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        miss = re.search(rb"LD-MISSING:(.*?);;", raw)
        missing = set(miss.group(1).decode().split("|")) if miss else set()
        body = raw.decode("utf-8", "replace")
        m = re.search(r'name="items"\r\n\r\n(.*?)\r\n--', body, re.S)
        items = json.loads(m.group(1)) if m else []
        out = {"items": [{"name": i["name"], "seen": 0 if i["name"] in missing else i["qty"], "note": ""} for i in items],
               "extra": [], "summary": "Giả lập"}
        data = json.dumps(out, ensure_ascii=False).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(data)
    def log_message(self, *a): pass

ThreadingHTTPServer(("127.0.0.1", 8199), H).serve_forever()
