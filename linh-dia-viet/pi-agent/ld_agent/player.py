"""Phát âm thanh qua mpv / ffplay / aplay, hoặc giả lập."""
import logging
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger("ld_agent.player")


class Player:
    def start(self, path: Path, volume: int, now: float) -> None: ...
    def is_playing(self, now: float) -> bool: ...
    def stop(self) -> None: ...
    def result(self) -> str | None:
        """None nếu phát bình thường, ngược lại là mô tả lỗi."""
        return None


class ProcessPlayer(Player):
    def __init__(self, kind: str, audio_device: str = ""):
        if not shutil.which(kind):
            raise RuntimeError(f"Không tìm thấy trình phát {kind}")
        self.kind, self.audio_device = kind, audio_device
        self.proc: subprocess.Popen | None = None

    def cmd(self, path: Path, volume: int) -> list[str]:
        if self.kind == "mpv":
            c = ["mpv", "--no-video", "--really-quiet", f"--volume={volume}"]
            if self.audio_device:
                c.append(f"--audio-device={self.audio_device}")
            return c + [str(path)]
        if self.kind == "ffplay":
            return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", "-volume", str(volume), str(path)]
        # aplay chỉ phát WAV: đổi mp3 → wav qua ffmpeg; âm lượng đặt bằng amixer (xem README)
        c = ["sh", "-c", f'ffmpeg -v error -i "{path}" -f wav - | aplay -q {"-D " + self.audio_device if self.audio_device else ""} -']
        return c

    def start(self, path, volume, now):
        self.proc = subprocess.Popen(self.cmd(path, volume), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def is_playing(self, now):
        return self.proc is not None and self.proc.poll() is None

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def result(self):
        if self.proc and self.proc.returncode not in (0, None, -15):
            err = (self.proc.stderr.read() or b"").decode(errors="ignore")[-300:] if self.proc.stderr else ""
            return f"{self.kind} thoát mã {self.proc.returncode}: {err}".strip()
        return None


class SimPlayer(Player):
    """Chế độ --simulate: không cần loa, 'phát' trong N giây theo đồng hồ của agent."""

    def __init__(self, seconds: float):
        self.seconds, self.until, self.stopped = seconds, 0.0, False

    def start(self, path, volume, now):
        log.info("[giả lập] PHÁT %s ở âm lượng %s trong %.1fs", path, volume, self.seconds)
        self.until, self.stopped = now + self.seconds, False

    def is_playing(self, now):
        return not self.stopped and now < self.until

    def stop(self):
        self.stopped = True
