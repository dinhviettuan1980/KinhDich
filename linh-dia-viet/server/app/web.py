"""Tiện ích dùng chung cho các router: template, phiên đăng nhập, audit log."""
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .config import BASE_DIR, get_settings
from .db import get_db
from .models import AuditLog, User
from .security import csrf_token

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def u(path: str = "/") -> str:
    """URL nội bộ có tiền tố cấu hình được (APP_PREFIX)."""
    return get_settings().prefix + (path if path.startswith("/") else "/" + path)


def fmt_vnd(n: int | None) -> str:
    return f"{(n or 0):,}".replace(",", ".") + " ₫"


def fmt_local(dt: datetime | None, tz: str | None = None, fmt: str = "%H:%M %d/%m/%Y") -> str:
    if not dt:
        return ""
    return dt.astimezone(ZoneInfo(tz or get_settings().default_timezone)).strftime(fmt)


from .models import tray_check  # noqa: E402
templates.env.globals.update(u=u, fmt_vnd=fmt_vnd, fmt_local=fmt_local, settings=get_settings, tray_check=tray_check)


class LoginRequired(Exception):
    pass


def render(request: Request, name: str, ctx: dict | None = None, status_code: int = 200):
    ctx = dict(ctx or {})
    ctx.setdefault("user", getattr(request.state, "user", None))
    ctx["csrf_token"] = csrf_token(request)
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)


def current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    uid = request.session.get("uid")
    user = db.get(User, uid) if uid else None
    if user is not None and not user.active:
        request.session.clear()
        user = None
    request.state.user = user
    return user


def require_user(user: User | None = Depends(current_user)) -> User:
    if not user:
        raise LoginRequired()
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "Chỉ dành cho quản trị viên")
    return user


def require_backoffice(user: User = Depends(require_user)) -> User:
    """admin, người quản lý đền hoặc người bán hàng kiosk."""
    if not (user.is_admin or user.is_staff) or not user.active:
        raise HTTPException(403, "Chỉ dành cho quản trị / nhân sự đền")
    return user


def can_manage_temple(user: User, temple_id: int | None, roles=("temple_manager", "vendor")) -> bool:
    if user.is_admin:
        return True
    return temple_id is not None and user.role in roles and temple_id in user.temple_ids


def audit(db: Session, actor: str, action: str, target: str = "", **detail) -> None:
    db.add(AuditLog(actor=actor, action=action, target=str(target), detail=detail or None))


def flash(request: Request, msg: str, kind: str = "info") -> None:
    request.session.setdefault("flash", []).append([kind, msg])


def pop_flash(request: Request) -> list:
    return request.session.pop("flash", [])


templates.env.globals["pop_flash"] = pop_flash
