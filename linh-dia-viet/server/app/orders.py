"""Nghiệp vụ đơn hàng: chuyển trạng thái (qua state_machine), thanh toán, xếp lịch, hủy."""
import logging
import secrets
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from . import prayer_text, tts
from .config import get_settings
from .models import Order, OrderEvent, Payment, Prayer, PrayerTemplate, Temple, utcnow
from .state_machine import PAID_STATES, USER_CANCELLABLE, OrderStatus as S, check_transition, path_forward
from .storage import get_storage, sha256_file
from .web import audit

log = logging.getLogger("linhdia.orders")


def transition(db: Session, order: Order, dst: str, actor: str, note: str | None = None) -> None:
    src = order.status
    check_transition(src, dst)
    order.status = S(dst).value
    order.updated_at = utcnow()
    if note:
        order.note = note
    db.add(OrderEvent(order_id=order.id, status=order.status, note=note))
    audit(db, actor, "order.transition", f"order:{order.id}", src=src, dst=order.status, note=note)


def advance_to(db: Session, order: Order, target: str, actor: str) -> bool:
    """Đi tiếp trên luồng chính tới target (bù các bước bị bỏ qua). False nếu đã ở/qua target."""
    steps = path_forward(order.status, target)
    for st in steps:
        transition(db, order, st, actor)
    return bool(steps)


def new_ref() -> str:
    return secrets.token_hex(6).upper()


def template_for(db: Session, temple: Temple) -> str:
    tpl = db.scalar(select(PrayerTemplate).where(PrayerTemplate.temple_id == temple.id)) or \
        db.scalar(select(PrayerTemplate).where(PrayerTemplate.temple_id.is_(None)))
    return tpl.body if tpl else prayer_text.DEFAULT_TEMPLATE


def local_date(dt_utc: datetime, tz: str):
    return dt_utc.astimezone(ZoneInfo(tz)).date()


def script_for(db: Session, prayer: Prayer, order: Order) -> str:
    ctx = prayer_text.personal_context(prayer.full_name, prayer.birth_year, prayer.address, prayer.wish,
                                       order.offering_text, local_date(order.scheduled_at, order.timezone))
    ctx.update(prayer_text.temple_context(order.temple))
    return prayer_text.render(prayer.text or template_for(db, order.temple), ctx)


def prepare_audio(db: Session, order: Order) -> None:
    """Chốt file sẽ phát tại đền: TTS theo văn bản của đơn, hoặc bản ghi âm của khách."""
    prayer = order.prayer
    if prayer.kind == "recorded":
        key = prayer.audio_key
    else:
        order.script_text = script_for(db, prayer, order)
        key, _ = tts.synthesize_cached(order.script_text, prayer.voice)
    order.audio_key = key
    order.audio_sha256 = sha256_file(get_storage().local_path(key))


def try_schedule(db: Session, order: Order, actor: str = "system") -> bool:
    """paid → scheduled khi bài khấn đã duyệt và audio sẵn sàng."""
    if order.status != S.PAID or order.prayer.moderation != "approved":
        return False
    try:
        prepare_audio(db, order)
    except Exception as e:  # TTS lỗi mạng… → giữ 'paid', vòng nền thử lại
        log.warning("Chưa tạo được audio cho đơn %s: %s", order.id, e)
        return False
    if order.play_asap:  # "phát ngay": tính từ lúc xếp lịch (sau thanh toán / sau khi duyệt), không phải lúc đặt
        order.scheduled_at = utcnow() + timedelta(seconds=get_settings().asap_delay_seconds)
    # Giành quyền xếp lịch bằng UPDATE có điều kiện: tác vụ nền sau thanh toán và vòng nền có thể cùng chạy
    # (TTS mất vài chục giây) — chỉ một bên thắng, bên còn lại không tạo job thứ hai.
    claimed = db.execute(update(Order).where(Order.id == order.id, Order.status == S.PAID)
                         .values(status=S.SCHEDULED.value, updated_at=utcnow()))
    if claimed.rowcount != 1:
        db.expire(order)  # bỏ thay đổi chưa ghi (audio, giờ phát) của bên thua; không đụng phần còn lại của giao dịch
        return False
    order.status = S.SCHEDULED.value
    db.add(OrderEvent(order_id=order.id, status=order.status))
    audit(db, actor, "order.transition", f"order:{order.id}", src=S.PAID.value, dst=order.status)
    from . import hooks
    hooks.on_scheduled(db, order)
    return True


# ---------------- Thanh toán ----------------

def start_payment(db: Session, orders: list[Order], actor: str, provider: str = "mock") -> str:
    """Tạo giao dịch cho các đơn của 1 lần đặt (mỗi đơn 1 payment, chung txn_ref)."""
    txn = "LD" + secrets.token_hex(8).upper()
    for o in orders:
        if o.status == S.CREATED:
            transition(db, o, S.AWAITING_PAYMENT, actor)
        if o.status == S.AWAITING_PAYMENT:
            db.add(Payment(order_id=o.id, provider=provider, txn_ref=txn, amount=o.total))
    return txn


def payment_result(db: Session, txn_ref: str, success: bool, actor: str, schedule: bool = True) -> list[Order]:
    """Xử lý kết quả thanh toán (từ trang giả lập hoặc webhook nhà cung cấp). Idempotent."""
    payments = db.scalars(select(Payment).where(Payment.txn_ref == txn_ref)).all()
    paid = []
    for p in payments:
        if p.status != "pending":
            continue
        p.status = "succeeded" if success else "failed"
        audit(db, actor, "payment.result", f"payment:{p.id}", txn_ref=txn_ref, status=p.status)
        if not success:
            continue
        p.paid_at = utcnow()
        o = p.order
        if o.status == S.AWAITING_PAYMENT:
            transition(db, o, S.PAID, actor)
            paid.append(o)
        else:  # đơn đã hủy trong lúc chờ → ghi nhận tiền, chuyển hoàn tiền
            if o.status == S.CANCELLED:
                transition(db, o, S.REFUND_REQUESTED, actor, "Thanh toán sau khi đơn đã hủy")
    if schedule:
        for o in paid:
            try_schedule(db, o, actor)
    return paid


def schedule_in_background(order_ids: list[int], actor: str) -> None:
    """Tạo audio (TTS có thể mất vài chục giây) + xếp lịch sau khi đã trả response thanh toán.
    Lỗi thì vòng nền (devices.tick) sẽ thử lại các đơn còn 'paid'."""
    from . import db as dbmod
    with dbmod.SessionLocal() as db:
        for oid in order_ids:
            o = db.get(Order, oid)
            if o:
                try_schedule(db, o, actor)
                db.commit()


# ---------------- Hủy / từ chối ----------------

def can_user_cancel(order: Order, now: datetime | None = None) -> bool:
    if order.status not in USER_CANCELLABLE:
        return False
    if order.status == S.SCHEDULED:
        # chỉ hủy được trước khi lệnh được gửi xuống thiết bị
        lead = timedelta(seconds=get_settings().dispatch_lead_seconds)
        return (now or utcnow()) < order.scheduled_at - lead
    return True


def cancel(db: Session, order: Order, actor: str, reason: str = "Khách hủy") -> None:
    was_paid = order.status in PAID_STATES
    transition(db, order, S.CANCELLED, actor, reason)
    from . import hooks
    hooks.on_cancelled(db, order)
    if was_paid:
        transition(db, order, S.REFUND_REQUESTED, actor)


def reject(db: Session, order: Order, actor: str, reason: str) -> None:
    transition(db, order, S.REJECTED, actor, reason)
    from . import hooks
    hooks.on_cancelled(db, order)
    transition(db, order, S.REFUND_REQUESTED, actor)


def mark_refunded(db: Session, order: Order, actor: str) -> None:
    transition(db, order, S.REFUNDED, actor)
    for p in order.payments:
        if p.status == "succeeded":
            p.status = "refunded"


def moderate(db: Session, prayer: Prayer, approve: bool, actor: str, note: str = "") -> None:
    """Duyệt / từ chối bản ghi âm. Duyệt → xếp lịch các đơn đã trả tiền. Từ chối → đơn đã trả tiền bị
    'rejected' (→ hoàn tiền), đơn chưa trả tiền bị hủy."""
    from .state_machine import can_transition
    prayer.moderation = "approved" if approve else "rejected"
    prayer.moderation_note = note or None
    audit(db, actor, "prayer.approve" if approve else "prayer.reject", f"prayer:{prayer.id}", note=note)
    for o in prayer.orders:
        if approve:
            try_schedule(db, o, actor)
        elif o.status in (S.PAID, S.SCHEDULED):
            reject(db, o, actor, f"Bản ghi âm không được duyệt: {note}")
        elif can_transition(o.status, S.CANCELLED):
            transition(db, o, S.CANCELLED, actor, f"Bản ghi âm không được duyệt: {note}")


def prewarm_tts(order_ids: list[int]) -> None:
    """Tạo sẵn giọng đọc ngay khi đặt đơn (lúc khách còn ở trang thanh toán) → thanh toán xong phát được ngay.
    Kết quả nằm trong cache TTS nên try_schedule sau đó không phải chờ. Lỗi thì bỏ qua (try_schedule sẽ làm lại)."""
    from . import db as dbmod
    with dbmod.SessionLocal() as db:
        for oid in order_ids:
            o = db.get(Order, oid)
            if o and o.prayer.kind == "tts":
                try:
                    tts.synthesize_cached(script_for(db, o.prayer, o), o.prayer.voice)
                except Exception as e:
                    log.info("Chưa tạo sẵn được giọng đọc cho đơn %s: %s", oid, e)
