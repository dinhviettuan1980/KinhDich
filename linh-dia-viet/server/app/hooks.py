"""Điểm nối giữa nghiệp vụ đơn hàng và lớp thiết bị."""
from datetime import timedelta

from sqlalchemy.orm import Session

from .config import get_settings
from .models import utcnow


def on_scheduled(db: Session, order) -> None:
    """Đơn vừa được xếp lịch: tạo device job; nếu đã sát giờ thì gửi lệnh ngay."""
    from . import devices
    job = devices.create_job(db, order)
    if job.play_at <= utcnow() + timedelta(seconds=get_settings().dispatch_lead_seconds):
        devices.dispatch(db, job)


def on_cancelled(db: Session, order) -> None:
    """Đơn bị hủy/từ chối: hủy device job (gửi lệnh cancel nếu đã giao xuống thiết bị)."""
    from . import devices
    devices.cancel_jobs(db, order, "system")
