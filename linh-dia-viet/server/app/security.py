import hashlib
import hmac
import secrets
import threading
import time
from collections import defaultdict, deque

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import HTTPException, Request

_ph = PasswordHasher()


def hash_password(pw: str) -> str:
    return _ph.hash(pw)


def verify_password(pw: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        return _ph.verify(hashed, pw)
    except (VerifyMismatchError, InvalidHashError):
        return False


def hash_token(token: str) -> str:
    """Token thiết bị/OTP có entropy cao hoặc sống ngắn → SHA-256 là đủ, so sánh hằng thời gian."""
    return hashlib.sha256(token.encode()).hexdigest()


def token_matches(token: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_token(token), hashed)


def new_token(nbytes: int = 24) -> str:
    return secrets.token_urlsafe(nbytes)


# ---- CSRF: token gắn với phiên, gửi qua field "csrf_token" hoặc header X-CSRF-Token ----

def csrf_token(request: Request) -> str:
    tok = request.session.get("csrf")
    if not tok:
        tok = secrets.token_urlsafe(24)
        request.session["csrf"] = tok
    return tok


async def check_csrf(request: Request) -> None:
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    expected = request.session.get("csrf")
    sent = request.headers.get("x-csrf-token")
    if not sent:
        ctype = request.headers.get("content-type", "")
        if ctype.startswith(("application/x-www-form-urlencoded", "multipart/form-data")):
            form = await request.form()
            sent = form.get("csrf_token")
    if not expected or not sent or not hmac.compare_digest(str(sent), expected):
        raise HTTPException(403, "CSRF token không hợp lệ")


# ---- Rate limit đơn giản trong bộ nhớ (1 tiến trình API) ----

class RateLimiter:
    def __init__(self):
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window_s: float) -> bool:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > window_s:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True

    def reset(self):
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def client_ip(request: Request) -> str:
    # Sau reverse proxy: chạy uvicorn --proxy-headers --forwarded-allow-ips=<ip proxy>
    # thay vì tự đọc X-Forwarded-For (tránh bị giả mạo để né rate limit).
    return request.client.host if request.client else "?"


def rate_limit(name: str, limit: int, window_s: float):
    def dep(request: Request):
        if not limiter.hit(f"{name}:{client_ip(request)}", limit, window_s):
            raise HTTPException(429, "Bạn thao tác quá nhanh, vui lòng thử lại sau ít phút.")
    return dep
