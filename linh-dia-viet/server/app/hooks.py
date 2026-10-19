"""Điểm nối giữa nghiệp vụ đơn hàng và lớp thiết bị (được nối ở M3)."""
from sqlalchemy.orm import Session


def on_scheduled(db: Session, order) -> None:
    """Đơn vừa được xếp lịch: tạo device job."""


def on_cancelled(db: Session, order) -> None:
    """Đơn bị hủy/từ chối: hủy device job nếu có."""
