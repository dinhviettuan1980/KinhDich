import logging
import re
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import OtpCode, User, utcnow
from ..security import check_csrf, hash_password, hash_token, rate_limit, token_matches, verify_password
from ..web import current_user, flash, render, u

log = logging.getLogger("linhdia.auth")
router = APIRouter()

OTP_TTL = timedelta(minutes=5)


def normalize_identifier(raw: str) -> tuple[str, str] | None:
    """Trả về ('email', x) hoặc ('phone', x); None nếu không hợp lệ."""
    raw = (raw or "").strip()
    if "@" in raw:
        email = raw.lower()
        return ("email", email) if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) else None
    digits = re.sub(r"[\s.\-()]", "", raw)
    if digits.startswith("+84"):
        digits = "0" + digits[3:]
    return ("phone", digits) if re.fullmatch(r"0\d{9,10}", digits) else None


def find_user(db: Session, kind: str, value: str) -> User | None:
    col = User.email if kind == "email" else User.phone
    return db.scalar(select(User).where(col == value))


def login_session(request: Request, user: User) -> None:
    request.session.clear()  # chống session fixation
    request.session["uid"] = user.id


def _next_url(request: Request, default: str = "/") -> str:
    nxt = request.query_params.get("next") or ""
    # chỉ cho phép đường dẫn nội bộ
    return nxt if nxt.startswith("/") and not nxt.startswith("//") else u(default)


@router.get("/dang-nhap")
def login_page(request: Request, user=Depends(current_user)):
    return render(request, "auth/login.html", {"next": request.query_params.get("next", "")})


@router.post("/dang-nhap", dependencies=[Depends(check_csrf), Depends(rate_limit("login", 10, 300))])
def login(request: Request, identifier: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    ident = normalize_identifier(identifier)
    user = find_user(db, *ident) if ident else None
    if not user or not user.active or not verify_password(password, user.password_hash):
        flash(request, "Sai thông tin đăng nhập.", "error")
        return render(request, "auth/login.html", {"identifier": identifier}, status_code=400)
    login_session(request, user)
    return RedirectResponse(_next_url(request), 303)


@router.post("/otp/gui", dependencies=[Depends(check_csrf), Depends(rate_limit("otp", 5, 300))])
def otp_send(request: Request, identifier: str = Form(...), db: Session = Depends(get_db)):
    ident = normalize_identifier(identifier)
    if not ident:
        flash(request, "Email hoặc số điện thoại không hợp lệ.", "error")
        return render(request, "auth/login.html", {"identifier": identifier}, status_code=400)
    code = f"{secrets.randbelow(10**6):06d}"
    db.add(OtpCode(identifier=ident[1], code_hash=hash_token(code), expires_at=utcnow() + OTP_TTL))
    db.commit()
    # OTP giả lập: chỉ in ra log (chưa có SMS/email thật).
    log.warning("OTP giả lập cho %s: %s", ident[1], code)
    return render(request, "auth/otp.html", {"identifier": ident[1], "next": request.query_params.get("next", "")})


@router.post("/otp/xac-nhan", dependencies=[Depends(check_csrf), Depends(rate_limit("otp-verify", 10, 300))])
def otp_verify(request: Request, identifier: str = Form(...), code: str = Form(...), db: Session = Depends(get_db)):
    ident = normalize_identifier(identifier)
    otp = None
    if ident:
        otp = db.scalar(select(OtpCode).where(OtpCode.identifier == ident[1], OtpCode.used.is_(False))
                        .order_by(OtpCode.id.desc()))
    ok = bool(otp and otp.expires_at > utcnow() and otp.attempts < 5 and token_matches(code.strip(), otp.code_hash))
    if otp:
        otp.attempts += 1
        otp.used = ok or otp.attempts >= 5
        db.commit()
    if not ok:
        flash(request, "Mã OTP không đúng hoặc đã hết hạn.", "error")
        return render(request, "auth/otp.html", {"identifier": identifier}, status_code=400)
    user = find_user(db, *ident)
    if user and not user.active:
        flash(request, "Tài khoản đã bị khóa.", "error")
        return render(request, "auth/otp.html", {"identifier": identifier}, status_code=403)
    if not user:
        user = User(name=ident[1].split("@")[0], **{ident[0]: ident[1]})
        db.add(user)
        db.commit()
    login_session(request, user)
    return RedirectResponse(_next_url(request), 303)


@router.get("/dang-ky")
def register_page(request: Request, user=Depends(current_user)):
    return render(request, "auth/register.html")


@router.post("/dang-ky", dependencies=[Depends(check_csrf), Depends(rate_limit("register", 5, 300))])
def register(request: Request, name: str = Form(...), identifier: str = Form(...), password: str = Form(...),
             db: Session = Depends(get_db)):
    ident = normalize_identifier(identifier)
    error = None
    if not name.strip() or len(name) > 120:
        error = "Vui lòng nhập họ tên."
    elif not ident:
        error = "Email hoặc số điện thoại không hợp lệ."
    elif len(password) < 8:
        error = "Mật khẩu tối thiểu 8 ký tự."
    elif db.scalar(select(User).where(or_(User.email == ident[1], User.phone == ident[1]))):
        error = "Tài khoản đã tồn tại, vui lòng đăng nhập."
    if error:
        flash(request, error, "error")
        return render(request, "auth/register.html", {"name": name, "identifier": identifier}, status_code=400)
    user = User(name=name.strip(), password_hash=hash_password(password), **{ident[0]: ident[1]})
    db.add(user)
    db.commit()
    login_session(request, user)
    return RedirectResponse(u("/"), 303)


@router.post("/dang-xuat", dependencies=[Depends(check_csrf)])
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(u("/"), 303)


@router.get("/tai-khoan")
def account_page(request: Request, user=Depends(current_user)):
    if not user:
        return RedirectResponse(u("/dang-nhap?next=") + u("/tai-khoan"), 303)
    return render(request, "auth/account.html")


@router.post("/tai-khoan/mat-khau", dependencies=[Depends(check_csrf), Depends(rate_limit("passwd", 10, 300))])
def change_password(request: Request, old: str = Form(""), new: str = Form(...), db: Session = Depends(get_db),
                    user=Depends(current_user)):
    if not user:
        return RedirectResponse(u("/dang-nhap"), 303)
    user = db.get(User, user.id)
    if user.password_hash and not verify_password(old, user.password_hash):
        flash(request, "Mật khẩu hiện tại không đúng.", "error")
    elif len(new) < 8:
        flash(request, "Mật khẩu mới tối thiểu 8 ký tự.", "error")
    else:
        user.password_hash = hash_password(new)
        db.commit()
        flash(request, "Đã đổi mật khẩu.", "ok")
    return RedirectResponse(u("/tai-khoan"), 303)


@router.post("/tai-khoan/tin-chu", dependencies=[Depends(check_csrf)])
def save_devotee(request: Request, ho_ten: str = Form(""), nam_sinh: str = Form(""), dia_chi: str = Form(""),
                 nguyen_vong: str = Form(""), db: Session = Depends(get_db), user=Depends(current_user)):
    from datetime import date
    from ..prayer_text import clean_input
    if not user:
        return RedirectResponse(u("/dang-nhap"), 303)
    me = db.get(User, user.id)
    by = int(nam_sinh) if nam_sinh.isdigit() else None
    if by is not None and not (1900 <= by <= date.today().year):
        flash(request, "Năm sinh không hợp lệ.", "error")
        return RedirectResponse(u("/tai-khoan"), 303)
    me.devotee_name, me.birth_year = clean_input(ho_ten, 120) or None, by
    me.address, me.wish = clean_input(dia_chi, 300) or None, clean_input(nguyen_vong, 1000) or None
    db.commit()
    flash(request, "Đã lưu thông tin tín chủ.", "ok")
    return RedirectResponse(u("/tai-khoan"), 303)
