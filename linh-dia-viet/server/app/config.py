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
    in_person_fee: int = 50000  # phí thủ nhang đọc sớ tại chỗ (VND / đền)
    platform_fee_pct: int = 10  # phí nền tảng trên mỗi đơn hoàn tất
    accept_timeout_seconds: int = 7200  # thủ nhang phải nhận đơn trong thời gian này, quá hạn tự hoàn tiền
    group_asap_delay_seconds: int = 15  # "phát ngay" nhiều đền: chừa thêm để mọi thiết bị tải xong file
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
    tts_voice: str = "vi-VN-NamMinhNeural,-8%,-6Hz"  # giọng nam miền Bắc, đọc chậm & trầm hơn chút (Edge: tên,tốc độ,cao độ)
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
    alert_lead_minutes: int = 60  # thiết bị mất kết nối mà có lễ trong vòng N phút tới → cảnh báo
    telegram_bot_token: str = ""  # tuỳ chọn: gửi cảnh báo qua Telegram
    telegram_chat_id: str = ""
    signed_url_ttl_seconds: int = 3600
    capture_before_s: int = 60
    capture_after_s: int = 5
    default_volume: int = 70
    scheduler_interval_seconds: float = 10.0
    scheduler_enabled: bool = True

    # Bản đồ đình chùa: có key → Google Maps JS; để trống → Leaflet + nền OpenStreetMap (chỉ hợp cho dev/ít truy cập).
    google_maps_api_key: str = ""
    google_maps_map_id: str = "DEMO_MAP_ID"  # Map ID (bắt buộc cho Advanced Marker); production nên tạo Map ID riêng
    places_autoload: bool = True  # seed nạp app/data/places_vn.json.gz khi snapshot đổi phiên bản

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
