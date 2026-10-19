"""Luồng đặt lễ: chọn đền → gói lễ → thông tin → cách khấn → ngày giờ → xem lại → thanh toán giả lập."""
import tempfile
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import audio, orders as svc, prayer_text, tts
from ..config import get_settings
from ..db import get_db
from ..lunar import solar_to_lunar
from ..models import OfferingPackage, Order, OrderEvent, Payment, Prayer, PrayerTemplate, Temple, User, utcnow
from ..security import check_csrf, rate_limit
from ..storage import get_storage
from ..web import render, require_user, u
from .public import device_online, packages_for

router = APIRouter()
csrf = [Depends(check_csrf)]


class BookingError(ValueError):
    pass


@dataclass
class Booking:
    temples: list[Temple]
    package: OfferingPackage | None
    full_name: str
    birth_year: int | None
    address: str
    wish: str
    kind: str
    text: str | None
    recording_key: str | None
    scheduled_at: datetime | None  # UTC
    tz: str


def _form_get(form, name, default=""):
    v = form.get(name, default)
    return v if isinstance(v, str) else default


def parse_booking(db: Session, request: Request, form, *, partial: bool = False) -> Booking:
    s = get_settings()
    ids = []
    for x in form.getlist("den"):
        if str(x).isdigit() and int(x) not in ids:
            ids.append(int(x))
    if not ids:
        raise BookingError("Vui lòng chọn ít nhất một đền.")
    if len(ids) > s.max_temples_per_order:
        raise BookingError(f"Chỉ chọn tối đa {s.max_temples_per_order} đền mỗi lần.")
    temples = list(db.scalars(select(Temple).where(Temple.id.in_(ids), Temple.status == "active")))
    if len(temples) != len(ids):
        raise BookingError("Có đền không còn nhận lễ.")
    temples.sort(key=lambda t: ids.index(t.id))
    if not partial:
        missing = [t.name for t in temples if not t.device_id]
        if missing:
            raise BookingError("Chưa nhận lễ từ xa tại: " + ", ".join(missing) + " (đền chưa lắp thiết bị).")

    package = None
    pkg_id = _form_get(form, "goi")
    if pkg_id.isdigit():
        package = next((p for p in packages_for(db, ids) if p.id == int(pkg_id)), None)
    if not package and not partial:
        raise BookingError("Vui lòng chọn gói lễ phù hợp.")

    full_name = prayer_text.clean_input(_form_get(form, "ho_ten"), 120)
    address = prayer_text.clean_input(_form_get(form, "dia_chi"), 300)
    wish = prayer_text.clean_input(_form_get(form, "nguyen_vong"), 1000)
    by = _form_get(form, "nam_sinh")
    birth_year = int(by) if by.isdigit() else None
    if birth_year is not None and not (1900 <= birth_year <= date.today().year):
        raise BookingError("Năm sinh không hợp lệ.")
    if not partial and not (full_name and birth_year and address and wish):
        raise BookingError("Vui lòng điền đủ họ tên, năm sinh, địa chỉ và nguyện vọng.")

    kind = _form_get(form, "cach_khan", "tts")
    if kind not in ("tts", "recorded"):
        raise BookingError("Cách khấn không hợp lệ.")

    tz = s.default_timezone
    scheduled_at = None
    raw = _form_get(form, "thoi_gian")
    if raw:
        try:
            scheduled_at = datetime.fromisoformat(raw).replace(tzinfo=ZoneInfo(tz)).astimezone(ZoneInfo("UTC"))
        except ValueError:
            raise BookingError("Thời gian không hợp lệ.")
    if not partial:
        now = utcnow()
        if not scheduled_at or scheduled_at < now + timedelta(seconds=s.min_lead_seconds):
            raise BookingError(f"Giờ hẹn phải sau thời điểm hiện tại ít nhất {max(1, s.min_lead_seconds // 60)} phút.")
        if scheduled_at > now + timedelta(days=365):
            raise BookingError("Chỉ đặt trước tối đa 1 năm.")

    text = None
    recording_key = None
    if kind == "tts":
        edited = (_form_get(form, "van_ban") or "").replace("\r\n", "\n").strip()
        original = (_form_get(form, "van_ban_goc") or "").replace("\r\n", "\n").strip()
        if edited and edited != original:
            if len(edited) > s.max_prayer_chars:
                raise BookingError(f"Bài khấn tối đa {s.max_prayer_chars} ký tự.")
            if original and len(edited) > len(original) * 1.5 + 300:
                raise BookingError("Chỉ được sửa nhẹ bài khấn (văn bản dài hơn quá nhiều so với mẫu).")
            if prayer_text.unknown_variables(edited):
                raise BookingError("Văn bản có biến không hợp lệ trong dấu { }.")
            text = prayer_text.clean_multiline(edited, s.max_prayer_chars)
    else:
        recording_key = _form_get(form, "ghi_am")
        if not partial and recording_key not in request.session.get("rec_keys", []):
            raise BookingError("Vui lòng ghi âm hoặc tải lên bài khấn.")
    return Booking(temples, package, full_name, birth_year, address, wish, kind, text, recording_key, scheduled_at, tz)


def preview_text(db: Session, b: Booking) -> str:
    """Một đền: render đủ theo mẫu của đền. Nhiều đền: mẫu chung, giữ {ten_den}… để điền theo từng đền."""
    ceremony = (b.scheduled_at or utcnow()).astimezone(ZoneInfo(b.tz)).date()
    ctx = prayer_text.personal_context(b.full_name or "…", b.birth_year or 0, b.address or "…", b.wish or "…",
                                       b.package.name if b.package else "lễ vật", ceremony)
    if not b.birth_year:
        ctx["nam_sinh"] = ctx["can_chi"] = "…"
    if len(b.temples) == 1:
        ctx.update(prayer_text.temple_context(b.temples[0]))
        return prayer_text.render(svc.template_for(db, b.temples[0]), ctx)
    shared = db.scalar(select(PrayerTemplate).where(PrayerTemplate.temple_id.is_(None)))
    return prayer_text.render(shared.body if shared else prayer_text.DEFAULT_TEMPLATE, ctx)


# ---------------- Trang đặt lễ ----------------

@router.get("/dat-le")
def booking_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    selected = [int(x) for x in request.query_params.getlist("den") if x.isdigit()]
    prefill = {}
    src = request.query_params.get("tu_don", "")
    if src.isdigit():  # "đặt lại đơn này"
        o = db.get(Order, int(src))
        if o and o.user_id == user.id:
            p = o.prayer
            selected = [x.temple_id for x in p.orders if x.booking_ref == o.booking_ref] or [o.temple_id]
            prefill = {"goi": o.package_id, "ho_ten": p.full_name, "nam_sinh": p.birth_year, "dia_chi": p.address,
                       "nguyen_vong": p.wish, "cach_khan": p.kind, "van_ban": p.text or ""}
            if p.kind == "recorded" and p.audio_key:
                keys = request.session.setdefault("rec_keys", [])
                if p.audio_key not in keys:
                    keys.append(p.audio_key)
                prefill["ghi_am"] = p.audio_key
    temples = list(db.scalars(select(Temple).where(Temple.status == "active").order_by(Temple.name)))
    s = get_settings()
    min_dt = (utcnow() + timedelta(seconds=s.min_lead_seconds + 60)).astimezone(ZoneInfo(s.default_timezone))
    return render(request, "booking/form.html", {
        "temples": temples, "selected": selected, "online": {t.id: device_online(t.device) for t in temples},
        "packages": packages_for(db, selected), "prefill": prefill, "min_dt": min_dt.strftime("%Y-%m-%dT%H:%M"),
        "max_seconds": s.max_audio_seconds, "max_chars": s.max_prayer_chars,
    })


@router.get("/dat-le/goi-le")
def package_options(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    ids = [int(x) for x in request.query_params.getlist("den") if x.isdigit()]
    return render(request, "booking/_packages.html", {"packages": packages_for(db, ids),
                                                      "prefill": {"goi": request.query_params.get("goi")}})


@router.get("/dat-le/am-lich")
def lunar_api(ngay: str, user: User = Depends(require_user)):
    try:
        d = date.fromisoformat(ngay[:10])
    except ValueError:
        raise HTTPException(400, "Ngày không hợp lệ")
    return {"text": solar_to_lunar(d).text()}


@router.post("/dat-le/xem-truoc", dependencies=csrf)
async def preview(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    form = await request.form()
    try:
        b = parse_booking(db, request, form, partial=True)
    except BookingError as e:
        return JSONResponse({"error": str(e)}, 400)
    return {"text": preview_text(db, b), "multi": len(b.temples) > 1}


@router.post("/dat-le/nghe-thu", dependencies=csrf + [Depends(rate_limit("tts", 20, 600))])
async def tts_preview(request: Request, user: User = Depends(require_user)):
    form = await request.form()
    text = prayer_text.clean_input(str(form.get("van_ban", "")).replace("\n", " "), get_settings().max_prayer_chars)
    if len(text) < 5:
        return JSONResponse({"error": "Chưa có văn bản để nghe thử."}, 400)
    try:
        key, dur = tts.synthesize_cached(text)
    except Exception:
        return JSONResponse({"error": "Không tạo được giọng đọc, vui lòng thử lại."}, 502)
    keys = request.session.setdefault("tts_keys", [])
    if key not in keys:
        keys.append(key)
        del keys[:-10]
    return {"url": u(f"/dat-le/am-thanh/{key.split('/')[-1]}"), "seconds": round(dur, 1)}


@router.post("/dat-le/ghi-am", dependencies=csrf + [Depends(rate_limit("upload", 10, 600))])
async def upload_recording(request: Request, file: UploadFile = File(...), user: User = Depends(require_user)):
    s = get_settings()
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "in"
        size = 0
        with open(src, "wb") as f:
            while chunk := await file.read(1 << 16):
                size += len(chunk)
                if size > s.max_upload_bytes:
                    return JSONResponse({"error": f"File quá {s.max_upload_bytes // (1024 * 1024)} MB."}, 413)
                f.write(chunk)
        if not audio.sniff_audio(src.read_bytes()[:16]):
            return JSONResponse({"error": "Định dạng file không được hỗ trợ (chỉ nhận webm, ogg, m4a, mp3, wav)."}, 415)
        out = Path(d) / "out.mp3"
        try:
            dur = audio.normalize_to_mp3(src, out)
        except audio.AudioError as e:
            return JSONResponse({"error": str(e)}, 422)
        key = f"recordings/{user.id}/{uuid.uuid4().hex}.mp3"
        get_storage().put_file(out, key)
    keys = request.session.setdefault("rec_keys", [])
    keys.append(key)
    del keys[:-5]
    return {"key": key, "seconds": round(dur, 1), "url": u(f"/dat-le/am-thanh/{key.split('/')[-1]}")}


@router.get("/dat-le/am-thanh/{name}")
def session_audio(name: str, request: Request, user: User = Depends(require_user)):
    """Chỉ phát lại file TTS/ghi âm nằm trong phiên của chính người dùng."""
    for key in request.session.get("tts_keys", []) + request.session.get("rec_keys", []):
        if key.split("/")[-1] == name:
            return FileResponse(get_storage().local_path(key), media_type="audio/mpeg")
    raise HTTPException(404)


@router.post("/dat-le", dependencies=csrf)
async def submit(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    form = await request.form()
    try:
        b = parse_booking(db, request, form)
    except BookingError as e:
        return JSONResponse({"error": str(e)}, 400)
    s = get_settings()
    approved = b.kind == "tts" or s.auto_approve_recordings
    prayer = Prayer(user_id=user.id, kind=b.kind, full_name=b.full_name, birth_year=b.birth_year, address=b.address,
                    wish=b.wish, text=b.text, voice=s.tts_voice if b.kind == "tts" else None,
                    audio_key=b.recording_key, moderation="approved" if approved else "pending")
    if b.recording_key:
        prayer.audio_seconds = audio.duration_of(get_storage().local_path(b.recording_key))
    db.add(prayer)
    db.flush()
    ref = svc.new_ref()
    for t in b.temples:
        o = Order(booking_ref=ref, user_id=user.id, prayer_id=prayer.id, temple_id=t.id, package_id=b.package.id,
                  scheduled_at=b.scheduled_at, timezone=b.tz, total=b.package.price)
        db.add(o)
        db.flush()
        db.add(OrderEvent(order_id=o.id, status="created"))
    db.commit()
    return {"redirect": u(f"/dat-le/xem-lai/{ref}")}


def _booking_orders(db: Session, ref: str, user: User) -> list[Order]:
    orders = list(db.scalars(select(Order).where(Order.booking_ref == ref).order_by(Order.id)))
    if not orders or (orders[0].user_id != user.id and not user.is_admin):
        raise HTTPException(404)
    return orders


@router.get("/dat-le/xem-lai/{ref}")
def review(ref: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    orders = _booking_orders(db, ref, user)
    first = orders[0]
    return render(request, "booking/review.html", {
        "orders": orders, "ref": ref, "prayer": first.prayer, "total": sum(o.total for o in orders),
        "script": svc.script_for(db, first.prayer, first) if first.prayer.kind == "tts" else None,
    })


@router.post("/dat-le/xem-lai/{ref}", dependencies=csrf)
def confirm(ref: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    orders = _booking_orders(db, ref, user)
    if not any(o.status in ("created", "awaiting_payment") for o in orders):
        return RedirectResponse(u(f"/don/{orders[0].id}"), 303)
    txn = svc.start_payment(db, orders, f"user:{user.id}")
    db.commit()
    return RedirectResponse(u(f"/thanh-toan/{txn}"), 303)


# ---------------- Thanh toán giả lập ----------------

def _txn_payments(db: Session, txn: str, user: User) -> list[Payment]:
    pays = list(db.scalars(select(Payment).where(Payment.txn_ref == txn)))
    if not pays or (pays[0].order.user_id != user.id and not user.is_admin):
        raise HTTPException(404)
    return pays


@router.get("/thanh-toan/{txn}")
def payment_page(txn: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    pays = _txn_payments(db, txn, user)
    return render(request, "booking/payment.html", {
        "txn": txn, "payments": pays, "amount": sum(p.amount for p in pays),
        "pending": any(p.status == "pending" for p in pays), "first_order": pays[0].order})


@router.post("/thanh-toan/{txn}/gia-lap", dependencies=csrf)
async def mock_pay(txn: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    pays = _txn_payments(db, txn, user)
    ok = (await request.form()).get("ket_qua") == "thanh_cong"
    svc.payment_result(db, txn, ok, f"user:{user.id}")
    db.commit()
    if not ok:
        return RedirectResponse(u(f"/thanh-toan/{txn}"), 303)
    return RedirectResponse(u(f"/don/{pays[0].order_id}"), 303)


@router.post("/api/thanh-toan/webhook/{provider}")
async def payment_webhook(provider: str, request: Request, db: Session = Depends(get_db)):
    """Webhook cho cổng thanh toán (VietQR… sau này). Body JSON {txn_ref, status: succeeded|failed},
    header X-Signature = hex(HMAC-SHA256(PAYMENT_WEBHOOK_SECRET, body))."""
    import hashlib
    import hmac
    import json
    secret = get_settings().payment_webhook_secret
    if not secret or provider != "mock":
        raise HTTPException(404)
    body = await request.body()
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, request.headers.get("x-signature", "")):
        raise HTTPException(401, "Sai chữ ký")
    data = json.loads(body)
    svc.payment_result(db, str(data["txn_ref"]), data.get("status") == "succeeded", f"webhook:{provider}")
    db.commit()
    return {"ok": True}
