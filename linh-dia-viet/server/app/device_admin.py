"""Thêm thiết bị, cấp lại / thu hồi token, đồng bộ file mật khẩu Mosquitto.

Mosquitto đọc mật khẩu dạng băm ($7$ = PBKDF2-SHA512). API ghi file `MQTT_PASSWD_FILE` (thư mục dùng chung với
container mosquitto); entrypoint của mosquitto thấy file đổi thì nạp lại (SIGHUP). Token gốc chỉ hiện 1 lần.
"""
import base64
import hashlib
import os
import re
import secrets
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import Device
from .security import hash_token, new_token

DEVICE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{2,40}$")
RESERVED = {"ld-server"}


def mosquitto_hash(password: str, iterations: int = 101) -> str:
    salt = secrets.token_bytes(12)
    dk = hashlib.pbkdf2_hmac("sha512", password.encode(), salt, iterations)
    return f"$7${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def write_mqtt_passwd(db: Session) -> Path | None:
    """Ghi lại toàn bộ dòng `device_id:hash` của các thiết bị còn hiệu lực (trừ thiết bị demo lấy từ env)."""
    path = get_settings().mqtt_passwd_file
    if not path:
        return None
    s = get_settings()
    lines = [f"{d.id}:{d.mqtt_hash}" for d in db.scalars(select(Device).order_by(Device.id))
             if d.mqtt_hash and not d.revoked and d.id != s.demo_device_id]
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text("".join(x + "\n" for x in lines))
    os.chmod(tmp, 0o640)
    tmp.replace(p)
    return p


def create_device(db: Session, device_id: str, name: str) -> str:
    device_id = device_id.strip().lower()
    if not DEVICE_ID_RE.match(device_id) or device_id in RESERVED:
        raise ValueError("Mã thiết bị chỉ gồm chữ thường, số, dấu '-' (3–41 ký tự)")
    if db.get(Device, device_id):
        raise ValueError("Mã thiết bị đã tồn tại")
    token = new_token(24)
    db.add(Device(id=device_id, name=name.strip() or device_id, token_hash=hash_token(token),
                  mqtt_hash=mosquitto_hash(token)))
    db.flush()
    write_mqtt_passwd(db)
    return token


def rotate_token(db: Session, dev: Device) -> str:
    token = new_token(24)
    dev.token_hash, dev.mqtt_hash, dev.revoked = hash_token(token), mosquitto_hash(token), False
    db.flush()
    write_mqtt_passwd(db)
    return token


def revoke(db: Session, dev: Device) -> None:
    dev.revoked, dev.online = True, False
    db.flush()
    write_mqtt_passwd(db)
