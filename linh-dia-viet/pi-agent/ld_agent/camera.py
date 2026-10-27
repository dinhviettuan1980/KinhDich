"""Chụp ảnh mâm lễ: rpicam-still / picamera2 (camera CSI), fswebcam / ffmpeg (webcam USB), hoặc giả lập."""
import io
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

log = logging.getLogger("ld_agent.camera")

class Camera:
    def __init__(self, kind: str, device: str = "/dev/video0", width: int = 1280, height: int = 960,
                 quality: int = 80):
        self.kind, self.device, self.w, self.h, self.q = kind, device, width, height, quality

    def capture(self, dst: Path, label: str = "", tray: dict | None = None) -> bool:
        """tray: lễ vật của đơn (kèm lệnh phát) — chỉ dùng để dựng ảnh mâm giả khi kind=simulate."""
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            if self.kind == "simulate":
                try:
                    from . import fake_tray
                    dst.write_bytes(fake_tray.render(tray, label))
                except Exception as e:  # dựng mâm giả lỗi → vẫn có ảnh đơn giản
                    log.warning("Không dựng được mâm giả: %s", e)
                    dst.write_bytes(self._fake(label))
                return True
            if self.kind == "none":
                return False
            if self.kind == "picamera2":
                from picamera2 import Picamera2  # chỉ có trên Raspberry Pi OS
                cam = Picamera2()
                cam.configure(cam.create_still_configuration(main={"size": (self.w, self.h)}))
                cam.options["quality"] = self.q
                cam.start()
                cam.capture_file(str(dst))
                cam.close()
                return dst.exists()
            cmd = {
                "rpicam": ["rpicam-still", "-n", "-t", "1500", "--width", str(self.w), "--height", str(self.h),
                           "-q", str(self.q), "-o", str(dst)],
                "fswebcam": ["fswebcam", "-q", "-d", self.device, "-r", f"{self.w}x{self.h}", "--no-banner",
                             "--jpeg", str(self.q), "-S", "10", str(dst)],
                "ffmpeg": ["ffmpeg", "-v", "error", "-y", "-f", "v4l2", "-video_size", f"{self.w}x{self.h}",
                           "-i", self.device, "-frames:v", "1", "-q:v", str(max(2, (100 - self.q) // 10)), str(dst)],
            }[self.kind]
            if not shutil.which(cmd[0]):
                log.error("Không tìm thấy %s", cmd[0])
                return False
            subprocess.run(cmd, check=True, timeout=30, capture_output=True)
            return dst.exists() and dst.stat().st_size > 0
        except Exception as e:
            log.error("Chụp ảnh lỗi (%s): %s", self.kind, e)
            return False

    def _fake(self, label: str) -> bytes:
        from PIL import Image, ImageDraw
        im = Image.new("RGB", (640, 480), (122, 31, 31))
        d = ImageDraw.Draw(im)
        d.text((20, 20), f"Anh gia lap - {label}", fill=(255, 230, 160))
        d.text((20, 50), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fill=(255, 255, 255))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=70)
        return buf.getvalue()
