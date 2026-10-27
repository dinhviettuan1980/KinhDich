"""Nghiệp vụ thiết bị: giao job, gửi lệnh (có audit), xử lý ACK/status, vòng kiểm tra quá hạn."""
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import db as dbmod
from . import orders as svc
from .config import get_settings
from .device_bus import get_bus
from .models import Device, DeviceJob, Evidence, Order, Setting, utcnow
from .state_machine import OrderStatus as S, can_transition
from .storage import signed_url
from .web import audit

log = logging.getLogger("linhdia.devices")

JOB_ORDER = ["queued", "delivered", "downloaded", "playing", "done"]
ACK_TO_JOB = {"received": "delivered", "downloaded": "downloaded", "playing": "playing", "done": "done",
              "error": "error"}
ACK_TO_ORDER = {"received": S.DELIVERED, "playing": S.PLAYING, "done": S.PLAYED}


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _log(job: DeviceJob, state: str, detail: str | None = None, now: datetime | None = None) -> None:
    job.log = (job.log or []) + [[(now or utcnow()).isoformat(), state, detail]]


# ---------------- Khóa khẩn cấp (dùng ở M5) ----------------

def system_locked(db: Session) -> bool:
    s = db.get(Setting, "system_lock")
    return bool(s and s.value == "1")


# ---------------- Gửi lệnh ----------------

class CommandBlocked(RuntimeError):
    pass


def send_command(db: Session, device_id: str, payload: dict, actor: str) -> bool:
    """Mọi lệnh xuống thiết bị đều qua đây: kiểm tra khóa khẩn cấp + ghi audit log."""
    if payload.get("type") != "stop" and system_locked(db):
        audit(db, actor, "device.cmd_blocked", f"device:{device_id}", type=payload.get("type"))
        raise CommandBlocked("Hệ thống đang khóa khẩn cấp")
    ok = get_bus().send(device_id, payload)
    detail = {k: v for k, v in payload.items() if k != "audio_url"}  # không lưu URL có chữ ký vào log
    audit(db, actor, "device.cmd", f"device:{device_id}", ok=ok, **detail)
    return ok


def play_payload(job: DeviceJob) -> dict:
    s = get_settings()
    order = job.order
    return {
        "type": "play", "job_id": job.id, "audio_url": signed_url(order.audio_key), "sha256": order.audio_sha256,
        "play_at": iso(job.play_at), "volume": s.default_volume,
        "capture": {"before_s": s.capture_before_s, "at_start": True, "after_s": s.capture_after_s},
        # lễ vật của đơn để đối chiếu mâm (camera giả lập dựng ảnh mâm từ đây) — không kèm dữ liệu cá nhân
        "tray": {"items": [{"name": i.name, "unit": i.unit, "qty": i.qty} for i in order.items],
                 "temple": order.temple.name},
    }


def create_job(db: Session, order: Order, play_at: datetime | None = None) -> DeviceJob:
    job = DeviceJob(id=uuid.uuid4().hex, device_id=order.temple.device_id,
                    play_at=play_at or order.scheduled_at, log=[])
    _log(job, "queued")
    order.jobs.append(job)
    db.flush()
    return job


def current_job(order: Order) -> DeviceJob | None:
    return order.jobs[-1] if order.jobs else None


def dispatch(db: Session, job: DeviceJob, actor: str = "system", now: datetime | None = None) -> bool:
    if not job.device_id:
        return False
    try:
        ok = send_command(db, job.device_id, play_payload(job), actor)
    except CommandBlocked:
        return False
    job.sent_at = now or utcnow()
    job.attempts += 1
    _log(job, "sent", f"lần {job.attempts}", now)
    return ok


def cancel_jobs(db: Session, order: Order, actor: str) -> None:
    for job in order.jobs:
        if job.state in ("queued", "delivered", "downloaded"):
            was_sent = job.sent_at is not None
            job.state = "cancelled"
            _log(job, "cancelled")
            if was_sent and job.device_id:
                try:
                    send_command(db, job.device_id, {"type": "cancel", "job_id": job.id}, actor)
                except CommandBlocked:
                    pass


def resend(db: Session, order: Order, actor: str, now: datetime | None = None) -> DeviceJob:
    """Nút "gửi lại job" của admin.
    - Đơn lỗi (failed): tạo job mới, phát sớm nhất sau 1 phút, đơn quay lại 'scheduled'.
    - Đơn đang chờ: gửi lại cùng job_id (Pi tự chống phát trùng) kèm URL tải mới.
    """
    now = now or utcnow()
    job = current_job(order)
    if order.status == S.FAILED:
        svc.transition(db, order, S.SCHEDULED, actor, "Admin gửi lại job")
        cancel_jobs(db, order, actor)
        job = create_job(db, order, play_at=max(order.scheduled_at, now + timedelta(seconds=60)))
    elif order.status not in (S.SCHEDULED, S.DELIVERED) or job is None:
        raise ValueError("Đơn không ở trạng thái gửi lại được")
    dispatch(db, job, actor, now)
    return job


# ---------------- Nhận ACK / status ----------------

def handle_message(device_id: str, kind: str, payload: dict) -> None:
    with dbmod.SessionLocal() as db:
        if kind == "ack":
            handle_ack(db, device_id, payload)
        elif kind == "status":
            handle_status(db, device_id, payload)
        db.commit()


def handle_status(db: Session, device_id: str, payload: dict, now: datetime | None = None) -> None:
    dev = db.get(Device, device_id)
    if not dev or dev.revoked:
        return
    dev.online = bool(payload.get("online"))
    if dev.online:
        dev.last_seen_at = now or utcnow()
        dev.net_type = str(payload.get("net", ""))[:10] or None
        dev.version = str(payload.get("version", ""))[:40] or None
        dev.last_status = {k: payload.get(k) for k in
                           ("net", "rssi", "temp", "volume", "version", "uptime", "disk_free", "queue", "camera")}


def handle_ack(db: Session, device_id: str, payload: dict, now: datetime | None = None) -> None:
    now = now or utcnow()
    job = db.get(DeviceJob, str(payload.get("job_id", "")))
    state = payload.get("state")
    if not job or job.device_id != device_id or state not in ACK_TO_JOB:
        log.warning("ACK không hợp lệ từ %s: %s", device_id, payload)
        return
    dev = db.get(Device, device_id)
    if dev:
        dev.last_seen_at = now
    detail = str(payload.get("detail") or "")[:500] or None
    _log(job, f"ack:{state}", detail, now)
    if job.state == "cancelled":
        return
    new = ACK_TO_JOB[state]
    # ACK đến trễ/lệch thứ tự (hàng đợi offline của Pi) → không lùi trạng thái job
    if new != "error" and job.state in JOB_ORDER and JOB_ORDER.index(new) <= JOB_ORDER.index(job.state):
        return
    job.state = new
    setattr(job, {"delivered": "delivered_at", "downloaded": "downloaded_at", "playing": "playing_at",
                  "done": "done_at", "error": "done_at"}[new], now)
    order = job.order
    if job is not current_job(order):
        return
    actor = f"device:{device_id}"
    if new == "error":
        job.error = detail or "lỗi không rõ"
        if can_transition(order.status, S.FAILED):
            svc.transition(db, order, S.FAILED, actor, f"Thiết bị báo lỗi: {job.error}")
        return
    target = ACK_TO_ORDER.get(state)
    if not target:
        return
    if order.status == S.FAILED and state in ("playing", "done"):
        # Pi mất mạng nhưng vẫn phát đúng giờ, ACK bù đến sau khi vòng kiểm tra đã đánh dấu failed.
        svc.transition(db, order, S.SCHEDULED, actor, "Thiết bị báo bù sau khi mất kết nối")
    svc.advance_to(db, order, target, actor)
    if order.status == S.PLAYED:
        maybe_complete(db, order, actor)


def maybe_complete(db: Session, order: Order, actor: str, now: datetime | None = None, timeout: bool = False) -> None:
    """played → evidence_received → completed khi đã có ảnh 'after'; hết thời gian chờ thì hoàn tất luôn."""
    if order.status != S.PLAYED:
        return
    photos = [e for e in order.evidence if e.kind == "photo"]
    if any(e.note == "after" for e in photos) or (timeout and photos):
        svc.transition(db, order, S.EVIDENCE_RECEIVED, actor)
        svc.transition(db, order, S.COMPLETED, actor)
    elif timeout:
        svc.transition(db, order, S.COMPLETED, actor, "Không nhận được ảnh mâm lễ từ thiết bị")


# ---------------- Vòng nền ----------------

def tick(db: Session, now: datetime | None = None) -> None:
    s = get_settings()
    now = now or utcnow()
    # 1) đơn đã trả tiền nhưng chưa xếp lịch được (TTS lỗi tạm thời)
    # (bỏ qua đơn vừa thanh toán < 1 phút: tác vụ nền sau thanh toán đang lo, tránh tạo TTS 2 lần)
    for o in db.scalars(select(Order).where(Order.status == S.PAID,
                                            Order.updated_at < now - timedelta(seconds=60))).all():
        svc.try_schedule(db, o)
    # 2) gửi lệnh trước giờ phát DISPATCH_LEAD; gửi lại mỗi 5 phút nếu thiết bị chưa xác nhận
    lead = timedelta(seconds=s.dispatch_lead_seconds)
    grace = timedelta(seconds=s.play_grace_seconds)
    if not system_locked(db):
        for job in db.scalars(select(DeviceJob).where(DeviceJob.state == "queued",
                                                      DeviceJob.play_at <= now + lead,
                                                      DeviceJob.play_at > now - grace)).all():
            if job.order.status == S.SCHEDULED and (job.sent_at is None or now - job.sent_at > timedelta(minutes=5)):
                dispatch(db, job, "system", now)
    # 3) quá giờ mà chưa phát xong → failed
    max_play = timedelta(seconds=s.max_audio_seconds)
    for o in db.scalars(select(Order).where(Order.status.in_([S.SCHEDULED, S.DELIVERED, S.PLAYING]))).all():
        job = current_job(o)
        play_at = job.play_at if job else o.scheduled_at
        if now > play_at + max_play + grace:
            reason = "Thiết bị không báo phát xong đúng hạn"
            if job and not job.device_id:
                reason = "Đền chưa gắn thiết bị"
            elif job and job.state == "queued":
                reason = "Thiết bị không nhận lệnh (offline)"
            if job and job.state not in ("done", "error", "cancelled"):
                job.state, job.error = "error", reason
                _log(job, "timeout", reason, now)
            svc.transition(db, o, S.FAILED, "system", reason)
    # 4) chờ ảnh quá hạn
    ev_timeout = timedelta(seconds=s.evidence_timeout_seconds)
    for o in db.scalars(select(Order).where(Order.status == S.PLAYED)).all():
        job = current_job(o)
        if job and job.done_at and now - job.done_at > ev_timeout:
            maybe_complete(db, o, "system", now, timeout=True)
    # 5) thiết bị im lặng quá lâu → offline
    stale = now - timedelta(seconds=s.device_offline_after_seconds)
    for dev in db.scalars(select(Device).where(Device.online.is_(True))).all():
        if not dev.last_seen_at or dev.last_seen_at < stale:
            dev.online = False


def add_evidence(db: Session, job: DeviceJob, key: str, captured_at: datetime, phase: str) -> Evidence:
    ev = Evidence(order_id=job.order_id, job_id=job.id, kind="photo", path=key, captured_at=captured_at, note=phase)
    db.add(ev)
    db.flush()
    db.refresh(job.order, ["evidence"])
    maybe_complete(db, job.order, f"device:{job.device_id}")
    return ev


def set_system_lock(db: Session, locked: bool, actor: str) -> int:
    """Khóa khẩn cấp: dừng phát trên mọi thiết bị và chặn mọi lệnh mới (trừ stop). Trả về số thiết bị được gửi stop."""
    s = db.get(Setting, "system_lock") or Setting(key="system_lock", value="0")
    s.value = "1" if locked else "0"
    db.merge(s)
    audit(db, actor, "system.lock" if locked else "system.unlock", "system")
    n = 0
    if locked:
        for dev in db.scalars(select(Device).where(Device.revoked.is_(False))).all():
            send_command(db, dev.id, {"type": "stop"}, actor)
            n += 1
    return n
