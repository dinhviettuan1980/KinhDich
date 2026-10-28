"""Quay video mâm lễ KÈM TIẾNG thu tại đền trong lúc loa đọc sớ (webcam USB có micro), để khách xem/nghe lại.

- Webcam thật (camera fswebcam/ffmpeg, v4l2): ffmpeg ghi hình /dev/video0 + tiếng từ micro USB (ALSA) ra MP4.
  Dừng bằng cách gửi "q" để ffmpeg đóng file MP4 đúng chuẩn. Webcam bận suốt lúc quay → ảnh "start" lấy từ 1 khung hình.
- simulate: dựng video giả = ảnh mâm giả + chính bài khấn (lọc nhẹ cho giống tiếng loa thu qua micro).
"""
import logging
import re
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger("ld_agent.recorder")

V4L2 = ("fswebcam", "ffmpeg")  # loại camera là webcam USB (v4l2) quay được video


def find_usb_mic() -> str:
    """ALSA của micro USB đầu tiên (thường là micro của webcam), vd 'plughw:CARD=Camera,DEV=0'. Không có → ''."""
    try:
        cards = Path("/proc/asound/cards").read_text()
    except OSError:
        return ""
    for m in re.finditer(r"^\s*\d+\s+\[(\S+)\s*\]:\s*USB-Audio", cards, re.M):
        card = m.group(1)
        if any(Path("/proc/asound").glob(f"{card}/pcm*c")):  # có thiết bị thu (capture)
            return f"plughw:CARD={card},DEV=0"
    return ""


class Recorder:
    def __init__(self, camera_kind: str, device: str = "/dev/video0", audio_in: str = "auto",
                 size: str = "1280x720", fps: int = 10, max_seconds: int = 300):
        self.kind, self.device, self.size, self.fps, self.max_seconds = camera_kind, device, size, fps, max_seconds
        self.audio_in = find_usb_mic() if audio_in == "auto" else audio_in
        self.proc: subprocess.Popen | None = None
        self.path: Path | None = None

    @property
    def enabled(self) -> bool:
        return (self.kind == "simulate" or self.kind in V4L2) and bool(shutil.which("ffmpeg"))

    @property
    def uses_camera(self) -> bool:
        """True nếu đang quay chiếm webcam (không chụp ảnh song song được)."""
        return self.kind in V4L2

    def busy(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def start(self, dst: Path, audio: Path | None = None, still: Path | None = None) -> bool:
        """audio/still chỉ dùng cho simulate (bài khấn + ảnh mâm giả)."""
        dst.parent.mkdir(parents=True, exist_ok=True)
        if self.kind == "simulate":
            if not (audio and still and audio.exists() and still.exists()):
                return False
            cmd = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "5", "-i", str(still), "-i", str(audio),
                   "-filter_complex", "[1:a]highpass=f=180,lowpass=f=5500,aecho=0.8:0.5:60:0.2,apad=pad_dur=3[a]",
                   "-map", "0:v", "-map", "[a]", "-shortest", "-t", str(self.max_seconds),
                   "-vf", "scale=-2:720,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
                   "-crf", "30", "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", str(dst)]
        else:
            cmd = ["ffmpeg", "-v", "error", "-y",
                   "-f", "v4l2", "-input_format", "mjpeg", "-video_size", self.size, "-framerate", str(self.fps),
                   "-thread_queue_size", "512", "-i", self.device]
            if self.audio_in:
                cmd += ["-f", "alsa", "-thread_queue_size", "1024", "-ac", "1", "-i", self.audio_in]
            else:
                log.warning("Không thấy micro USB — video không có tiếng")
            cmd += ["-t", str(self.max_seconds), "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
                    "-maxrate", "600k", "-bufsize", "1200k", "-pix_fmt", "yuv420p", "-g", str(self.fps * 4)]
            if self.audio_in:
                cmd += ["-c:a", "aac", "-b:a", "64k"]
            cmd += ["-movflags", "+faststart", str(dst)]
        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except OSError as e:
            log.error("Không chạy được ffmpeg để quay: %s", e)
            return False
        self.path = dst
        log.info("Bắt đầu quay %s (%s, micro: %s)", dst.name, self.kind, self.audio_in or "không")
        return True

    def stop(self) -> None:
        """Webcam thật: bảo ffmpeg dừng và đóng file. simulate: để ffmpeg tự chạy xong."""
        if self.kind == "simulate" or not self.busy():
            return
        try:
            self.proc.stdin.write(b"q")
            self.proc.stdin.flush()
        except OSError:
            self.proc.terminate()

    def finish(self, timeout: float = 20) -> Path | None:
        """Chờ ffmpeg kết thúc, trả file MP4 nếu hợp lệ."""
        if not self.proc:
            return None
        try:
            self.proc.wait(timeout)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(5)
        err = (self.proc.stderr.read() or b"").decode(errors="ignore")[-300:] if self.proc.stderr else ""
        path, self.proc, self.path = self.path, None, None
        if path and path.exists() and path.stat().st_size > 1000:
            return path
        log.error("Quay video lỗi: %s", err.strip() or "file rỗng")
        return None


def grab_frame(video: Path, dst: Path, at_s: float = 2.0) -> bool:
    """Lấy 1 khung hình từ video làm ảnh 'start' (để nhận diện mâm lễ)."""
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(at_s), "-i", str(video), "-frames:v", "1",
                        "-q:v", "3", str(dst)], check=True, timeout=30, capture_output=True)
        return dst.exists() and dst.stat().st_size > 0
    except Exception as e:
        log.error("Không lấy được khung hình: %s", e)
        return False
