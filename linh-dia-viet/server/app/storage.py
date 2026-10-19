"""Lưu file (audio, ảnh). Bản đầu dùng thư mục cục bộ; interface đủ để thay bằng S3 sau này."""
import hashlib
import hmac
import re
import shutil
import time
from pathlib import Path
from typing import Protocol

from .config import get_settings

_KEY_RE = re.compile(r"^[A-Za-z0-9_\-]+(/[A-Za-z0-9_\-.]+)*$")


def check_key(key: str) -> str:
    if not _KEY_RE.match(key) or ".." in key:
        raise ValueError(f"storage key không hợp lệ: {key!r}")
    return key


class Storage(Protocol):
    def put_file(self, src: Path, key: str) -> str: ...
    def put_bytes(self, data: bytes, key: str) -> str: ...
    def exists(self, key: str) -> bool: ...
    def local_path(self, key: str) -> Path: ...
    def delete(self, key: str) -> None: ...


class LocalStorage:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def local_path(self, key: str) -> Path:
        p = (self.root / check_key(key)).resolve()
        if self.root not in p.parents:
            raise ValueError("ngoài thư mục lưu trữ")
        return p

    def put_file(self, src: Path, key: str) -> str:
        dst = self.local_path(key)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        return key

    def put_bytes(self, data: bytes, key: str) -> str:
        dst = self.local_path(key)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        return key

    def exists(self, key: str) -> bool:
        return self.local_path(key).exists()

    def delete(self, key: str) -> None:
        self.local_path(key).unlink(missing_ok=True)


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        _storage = LocalStorage(get_settings().data_dir / "files")
    return _storage


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# ---- URL có chữ ký cho thiết bị tải file (hết hạn sau SIGNED_URL_TTL_SECONDS) ----

def _sig(key: str, exp: int) -> str:
    return hmac.new(get_settings().secret_key.encode(), f"{key}|{exp}".encode(), hashlib.sha256).hexdigest()


def signed_url(key: str, ttl: int | None = None, now: float | None = None) -> str:
    s = get_settings()
    exp = int((now or time.time()) + (ttl or s.signed_url_ttl_seconds))
    return f"{s.public_base_url.rstrip('/')}{s.prefix}/files/{check_key(key)}?exp={exp}&sig={_sig(key, exp)}"


def verify_signature(key: str, exp: int, sig: str, now: float | None = None) -> bool:
    if exp < (now or time.time()):
        return False
    return hmac.compare_digest(_sig(key, exp), sig)
