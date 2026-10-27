import logging
import re
import secrets
from datetime import date, timedelta
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .. import billing
from ..db import get_db
from ..lunar import solar_to_lunar
from ..models import OtpCode, User, utcnow
from ..prayer_text import clean_input
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


def onboarding_url(user: User, nxt: str) -> str | None:
    """Bước còn thiếu trước khi đặt lễ: hồ sơ tín chủ (lập sớ) → thẻ thanh toán. None = đủ rồi."""
    q = "?next=" + quote(nxt, safe="/") if nxt else ""
    if not user.profile_complete:
        return u("/tai-khoan/ho-so") + q
    if not user.has_card:
        return u("/tai-khoan/the") + q
    return None


def parse_birth_date(raw: str) -> date | None:
    """'YYYY-MM-DD' (ô date) hoặc 'DD/MM/YYYY'. Lỗi → ValueError."""
    raw = (raw or "").strip()
    if not raw:
        return None
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw)
    d = date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else date.fromisoformat(raw)
    if not date(1900, 1, 1) <= d <= date.today():
        raise ValueError
    return d


def set_profile(user: User, name: str, birth: date | None, address: str, wish: str | None = None) -> None:
    user.devotee_name = clean_input(name, 120) or None
    user.birth_date = birth
    user.birth_year = solar_to_lunar(birth).year if birth else user.birth_year  # năm âm lịch (sinh trước Tết → năm trước)
    user.address = clean_input(address, 300) or None
    if wish is not None:
        user.wish = clean_input(wish, 1000) or None


@router.get("/dang-ky")
def register_page(request: Request, user=Depends(current_user)):
    return render(request, "auth/register.html")


@router.post("/dang-ky", dependencies=[Depends(check_csrf), Depends(rate_limit("register", 5, 300))])
def register(request: Request, name: str = Form(...), identifier: str = Form(...), password: str = Form(...),
             ngay_sinh: str = Form(""), dia_chi: str = Form(""), db: Session = Depends(get_db)):
    ident = normalize_identifier(identifier)
    error, birth = None, None
    if not name.strip() or len(name) > 120:
        error = "Vui lòng nhập họ tên."
    elif not ident:
        error = "Email hoặc số điện thoại không hợp lệ."
    elif len(password) < 8:
        error = "Mật khẩu tối thiểu 8 ký tự."
    elif db.scalar(select(User).where(or_(User.email == ident[1], User.phone == ident[1]))):
        error = "Tài khoản đã tồn tại, vui lòng đăng nhập."
    else:
        try:
            birth = parse_birth_date(ngay_sinh)
        except ValueError:
            error = "Ngày sinh không hợp lệ."
    if error:
        flash(request, error, "error")
        return render(request, "auth/register.html", {"name": name, "identifier": identifier, "ngay_sinh": ngay_sinh,
                                                      "dia_chi": dia_chi}, status_code=400)
    user = User(name=name.strip(), password_hash=hash_password(password), **{ident[0]: ident[1]})
    set_profile(user, name, birth, dia_chi)
    db.add(user)
    db.commit()
    login_session(request, user)
    nxt = _next_url(request)
    return RedirectResponse(onboarding_url(user, nxt) or nxt, 303)


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


# ---------------- Hồ sơ tín chủ + thẻ (2 bước trước khi đặt lễ) ----------------

@router.get("/tai-khoan/ho-so")
def profile_page(request: Request, user=Depends(current_user)):
    if not user:
        return RedirectResponse(u("/dang-nhap?next=") + u("/tai-khoan/ho-so"), 303)
    return render(request, "auth/profile.html", {"next": request.query_params.get("next", ""),
                                                 "step": not user.profile_complete})


@router.post("/tai-khoan/ho-so", dependencies=[Depends(check_csrf)])
def profile_save(request: Request, ho_ten: str = Form(""), ngay_sinh: str = Form(""), dia_chi: str = Form(""),
                 nguyen_vong: str = Form(""), db: Session = Depends(get_db), user=Depends(current_user)):
    if not user:
        return RedirectResponse(u("/dang-nhap"), 303)
    me = db.get(User, user.id)
    ctx = {"next": request.query_params.get("next", ""), "step": not me.profile_complete}
    try:
        birth = parse_birth_date(ngay_sinh)
    except ValueError:
        flash(request, "Ngày sinh không hợp lệ.", "error")
        return render(request, "auth/profile.html", ctx, status_code=400)
    if not (ho_ten.strip() and birth and dia_chi.strip()):
        flash(request, "Vui lòng điền đủ họ tên, ngày sinh và địa chỉ để lập sớ.", "error")
        return render(request, "auth/profile.html", ctx, status_code=400)
    set_profile(me, ho_ten, birth, dia_chi, nguyen_vong)
    db.commit()
    nxt = _next_url(request, "/tai-khoan")
    flash(request, "Đã lưu thông tin tín chủ.", "ok")
    return RedirectResponse(onboarding_url(me, nxt) or nxt, 303)


@router.get("/tai-khoan/the")
def card_page(request: Request, user=Depends(current_user)):
    if not user:
        return RedirectResponse(u("/dang-nhap?next=") + u("/tai-khoan/the"), 303)
    return render(request, "auth/card.html", {"next": request.query_params.get("next", ""), "step": not user.has_card})


@router.post("/tai-khoan/the", dependencies=[Depends(check_csrf), Depends(rate_limit("card", 10, 300))])
def card_save(request: Request, so_the: str = Form(""), het_han: str = Form(""), cvc: str = Form(""),
              chu_the: str = Form(""), db: Session = Depends(get_db), user=Depends(current_user)):
    if not user:
        return RedirectResponse(u("/dang-nhap"), 303)
    me = db.get(User, user.id)
    try:
        card = billing.parse_card(so_the, het_han, cvc, chu_the)
    except billing.CardError as e:
        flash(request, str(e), "error")
        return render(request, "auth/card.html", {"next": request.query_params.get("next", ""), "step": not me.has_card,
                                                  "het_han": het_han, "chu_the": chu_the}, status_code=400)
    me.card_brand, me.card_last4, me.card_exp, me.card_holder = card["brand"], card["last4"], card["exp"], card["holder"]
    db.commit()
    flash(request, f"Đã liên kết thẻ {me.card_label}.", "ok")
    nxt = _next_url(request, "/tai-khoan")
    return RedirectResponse(onboarding_url(me, nxt) or nxt, 303)


@router.post("/tai-khoan/the/xoa", dependencies=[Depends(check_csrf)])
def card_remove(request: Request, db: Session = Depends(get_db), user=Depends(current_user)):
    if not user:
        return RedirectResponse(u("/dang-nhap"), 303)
    me = db.get(User, user.id)
    me.card_brand = me.card_last4 = me.card_exp = me.card_holder = None
    db.commit()
    flash(request, "Đã gỡ thẻ.", "ok")
    return RedirectResponse(u("/tai-khoan"), 303)
