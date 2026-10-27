import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


def _env_files() -> tuple[str, ...] | None:
    # APP_ENV_FILE="" để tắt (test), hoặc danh sách file cách nhau bằng dấu phẩy.
    raw = os.environ.get("APP_ENV_FILE", ".env,../.env")
    files = tuple(f for f in raw.split(",") if f.strip())
    return files or None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_files(), extra="ignore")

    env: str = "dev"
    secret_key: str = "dev-secret-change-me"
    database_url: str = "sqlite:///./data/linhdia.db"
    data_dir: Path = Path("./data")

    # Tiền tố của toàn bộ route, để ghép dưới domain khác (vd tuandv.id.vn/le-chua).
    app_prefix: str = "/le-chua"
    public_base_url: str = "http://localhost:8000"
    session_https_only: bool = False
    default_timezone: str = "Asia/Ho_Chi_Minh"
    home_url: str = ""  # link "về trang chính" ở header (vd trang Kinh Dịch)
    home_label: str = "Kinh Dịch"

    # Admin khởi tạo khi seed
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"

    # Đặt lễ
    max_temples_per_order: int = 100
    min_lead_seconds: int = 120
    asap_delay_seconds: int = 8  # "phát ngay": chừa thời gian để Pi tải file trước khi phát (Pi trễ vẫn phát bù)
    max_prayer_chars: int = 3000
    max_audio_seconds: int = 300
    max_upload_bytes: int = 20 * 1024 * 1024
    auto_approve_recordings: bool = True

    payment_webhook_secret: str = ""  # để trống = tắt webhook

    # TTS
    # Nhận diện mâm lễ (đếm lễ vật trên ảnh camera): hfspace (HF Space OCR /tray, miễn phí) | fake | off
    recognition_provider: str = "hfspace"
    recognition_url: str = "https://tuandv80-ocr-numbers.hf.space"
    tts_provider: str = "edge"  # edge | google | fpt | fake
    tts_voice: str = "vi-VN-HoaiMyNeural"
    google_tts_api_key: str = ""
    fpt_tts_api_key: str = ""

    # Thiết bị
    device_bus: str = "mqtt"  # mqtt | memory
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str = "ld-server"
    mqtt_password: str = ""
    mqtt_tls: bool = False
    mqtt_passwd_file: str = ""  # vd /srv/mqtt-extra/devices.passwd (thư mục dùng chung với mosquitto)
    dispatch_lead_seconds: int = 600
    play_grace_seconds: int = 900
    evidence_timeout_seconds: int = 600
    device_offline_after_seconds: int = 180
    signed_url_ttl_seconds: int = 3600
    capture_before_s: int = 60
    capture_after_s: int = 5
    default_volume: int = 70
    scheduler_interval_seconds: float = 10.0
    scheduler_enabled: bool = True

    # Seed
    demo_device_id: str = "pi-demo-01"
    demo_device_token: str = "dev-device-token-change-me"
    demo_staff_password: str = "demo12345"  # chỉ seed khi ENV=dev/test

    @property
    def prefix(self) -> str:
        p = "/" + self.app_prefix.strip("/")
        return "" if p == "/" else p


@lru_cache
def get_settings() -> Settings:
    return Settings()
