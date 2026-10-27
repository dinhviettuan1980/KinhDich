"""Cấu hình agent: đọc file .env (KEY=VALUE) rồi biến môi trường (ưu tiên biến môi trường)."""
import os
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path


def load_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _hm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


@dataclass
class Config:
    server_url: str = "http://localhost:8000/le-chua"  # gồm cả tiền tố APP_PREFIX
    device_id: str = "pi-demo-01"
    device_token: str = ""
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_tls: bool = False
    data_dir: Path = Path("/var/lib/linh-dia-viet")
    player: str = "mpv"  # mpv | ffplay | aplay
    audio_device: str = ""  # vd "alsa/plughw:1,0" cho mpv, "plughw:1,0" cho aplay
    volume_max: int = 85  # trần âm lượng cứng (0–100), server không vượt được
    volume_default: int = 70
    quiet_start: time = field(default_factory=lambda: time(22, 0))  # giờ cấm phát
    quiet_end: time = field(default_factory=lambda: time(5, 0))
    timezone: str = "Asia/Ho_Chi_Minh"
    camera: str = "rpicam"  # rpicam | picamera2 | fswebcam | ffmpeg | none
    camera_device: str = "/dev/video0"
    photo_width: int = 1280
    photo_height: int = 960
    jpeg_quality: int = 80
    max_late_seconds: int = 600  # quá giờ hẹn bao lâu thì bỏ, không phát nữa
    clock_wait_seconds: int = 600  # sau khi bật máy, chờ đồng bộ giờ tối đa bao lâu rồi mới phát theo giờ máy
    status_interval: int = 60
    simulate: bool = False
    simulate_play_seconds: float = 3.0

    @classmethod
    def load(cls, env_path: Path | None = None, simulate: bool | None = None) -> "Config":
        env = load_env_file(env_path or Path(os.environ.get("LD_AGENT_ENV", ".env")))
        env.update({k: v for k, v in os.environ.items() if k.startswith("LD_")})
        g = lambda k, d=None: env.get(f"LD_{k}", d)  # noqa: E731
        c = cls()
        c.server_url = g("SERVER_URL", c.server_url).rstrip("/")
        c.device_id = g("DEVICE_ID", c.device_id)
        c.device_token = g("DEVICE_TOKEN", c.device_token)
        c.mqtt_host = g("MQTT_HOST", c.mqtt_host)
        c.mqtt_port = int(g("MQTT_PORT", c.mqtt_port))
        c.mqtt_tls = g("MQTT_TLS", "false").lower() == "true"
        c.data_dir = Path(g("DATA_DIR", str(c.data_dir))).expanduser()
        c.player = g("PLAYER", c.player)
        c.audio_device = g("AUDIO_DEVICE", c.audio_device)
        c.volume_max = max(0, min(100, int(g("VOLUME_MAX", c.volume_max))))
        c.volume_default = min(c.volume_max, int(g("VOLUME_DEFAULT", c.volume_default)))
        c.quiet_start = _hm(g("QUIET_START", "22:00"))
        c.quiet_end = _hm(g("QUIET_END", "05:00"))
        c.timezone = g("TIMEZONE", c.timezone)
        c.camera = g("CAMERA", c.camera)
        c.camera_device = g("CAMERA_DEVICE", c.camera_device)
        c.max_late_seconds = int(g("MAX_LATE_SECONDS", c.max_late_seconds))
        c.clock_wait_seconds = int(g("CLOCK_WAIT_SECONDS", c.clock_wait_seconds))
        c.status_interval = int(g("STATUS_INTERVAL", c.status_interval))
        c.simulate = (g("SIMULATE", "false").lower() == "true") if simulate is None else simulate
        c.simulate_play_seconds = float(g("SIMULATE_PLAY_SECONDS", c.simulate_play_seconds))
        return c

    def in_quiet_hours(self, local: time) -> bool:
        if self.quiet_start == self.quiet_end:
            return False
        if self.quiet_start < self.quiet_end:
            return self.quiet_start <= local < self.quiet_end
        return local >= self.quiet_start or local < self.quiet_end  # khoảng qua nửa đêm
