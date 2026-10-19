from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """DateTime luôn đọc ra datetime có tzinfo=UTC (SQLite không lưu múi giờ)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(200), unique=True)
    phone: Mapped[str | None] = mapped_column(String(30), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    # customer: khách đặt lễ · vendor: người bán hàng kiosk tại đền (chuẩn bị mâm lễ)
    # temple_manager: người quản lý đền/chùa · admin: quản trị hệ thống
    role: Mapped[str] = mapped_column(String(20), default="customer")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    staff_of: Mapped[list["TempleStaff"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_staff(self) -> bool:
        return self.role in ("vendor", "temple_manager")

    @property
    def temple_ids(self) -> set[int]:
        return {s.temple_id for s in self.staff_of}


ROLES = {
    "customer": "Khách hàng",
    "vendor": "Người bán hàng kiosk",
    "temple_manager": "Người quản lý đền/chùa",
    "admin": "Quản trị hệ thống",
}


class TempleStaff(Base):
    """Gắn vendor / temple_manager với (các) đền họ phụ trách."""
    __tablename__ = "temple_staff"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    temple_id: Mapped[int] = mapped_column(ForeignKey("temples.id", ondelete="CASCADE"), primary_key=True)
    user: Mapped[User] = relationship(back_populates="staff_of")
    temple: Mapped["Temple"] = relationship()


class OtpCode(Base):
    __tablename__ = "otp_codes"
    id: Mapped[int] = mapped_column(primary_key=True)
    identifier: Mapped[str] = mapped_column(String(200), index=True)
    code_hash: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime())
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    token_hash: Mapped[str] = mapped_column(String(128))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    net_type: Mapped[str | None] = mapped_column(String(10))
    version: Mapped[str | None] = mapped_column(String(40))
    last_status: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class Temple(Base):
    __tablename__ = "temples"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str] = mapped_column(String(300), default="")
    province: Mapped[str] = mapped_column(String(100), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    deity: Mapped[str] = mapped_column(String(300), default="")  # danh vị thần linh chính
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | hidden
    device_id: Mapped[str | None] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"))
    device: Mapped[Device | None] = relationship()


class OfferingPackage(Base):
    __tablename__ = "offering_packages"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[int] = mapped_column(Integer)  # VND
    image_url: Mapped[str] = mapped_column(String(300), default="")
    temple_id: Mapped[int | None] = mapped_column(ForeignKey("temples.id", ondelete="CASCADE"))  # NULL = dùng chung
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    temple: Mapped[Temple | None] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    ts: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, index=True)
    actor: Mapped[str] = mapped_column(String(80))  # "user:1", "system", "device:pi-demo-01"
    action: Mapped[str] = mapped_column(String(80))
    target: Mapped[str] = mapped_column(String(120), default="")
    detail: Mapped[dict | None] = mapped_column(JSON)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class PrayerTemplate(Base):
    """Mẫu sớ. temple_id NULL = mẫu chung; mẫu riêng của đền được ưu tiên."""
    __tablename__ = "prayer_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    temple_id: Mapped[int | None] = mapped_column(ForeignKey("temples.id", ondelete="CASCADE"), unique=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow)
    temple: Mapped[Temple | None] = relationship()


class Prayer(Base):
    __tablename__ = "prayers"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(10))  # tts | recorded
    full_name: Mapped[str] = mapped_column(String(120))
    birth_year: Mapped[int] = mapped_column(Integer)
    address: Mapped[str] = mapped_column(String(300))
    wish: Mapped[str] = mapped_column(Text)
    # Văn bản khách đã sửa (NULL = dùng mẫu sớ của từng đền). Có thể chứa {ten_den}… khi đặt nhiều đền.
    text: Mapped[str | None] = mapped_column(Text)
    voice: Mapped[str | None] = mapped_column(String(60))
    audio_key: Mapped[str | None] = mapped_column(String(300))  # bản ghi âm (kind=recorded)
    audio_seconds: Mapped[float | None] = mapped_column()
    moderation: Mapped[str] = mapped_column(String(10), default="approved")  # pending | approved | rejected
    moderation_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    user: Mapped[User] = relationship()
    orders: Mapped[list["Order"]] = relationship(back_populates="prayer")


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_ref: Mapped[str] = mapped_column(String(32), index=True)  # gom các đơn của 1 lần đặt (nhiều đền)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    prayer_id: Mapped[int] = mapped_column(ForeignKey("prayers.id"))
    temple_id: Mapped[int] = mapped_column(ForeignKey("temples.id"), index=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("offering_packages.id"))
    scheduled_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)  # UTC
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Ho_Chi_Minh")
    status: Mapped[str] = mapped_column(String(20), default="created", index=True)
    total: Mapped[int] = mapped_column(Integer)  # VND, chốt giá lúc đặt
    script_text: Mapped[str | None] = mapped_column(Text)  # văn bản sớ cuối cùng cho đền này
    audio_key: Mapped[str | None] = mapped_column(String(300))  # file sẽ phát tại đền
    audio_sha256: Mapped[str | None] = mapped_column(String(64))
    note: Mapped[str | None] = mapped_column(Text)  # lý do từ chối/hủy/lỗi
    tray_ready_at: Mapped[datetime | None] = mapped_column(UTCDateTime())  # kiosk báo mâm lễ đã bày
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship()
    prayer: Mapped[Prayer] = relationship(back_populates="orders")
    temple: Mapped[Temple] = relationship()
    package: Mapped[OfferingPackage] = relationship()
    events: Mapped[list["OrderEvent"]] = relationship(order_by="OrderEvent.id", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="order", order_by="Payment.id")


class OrderEvent(Base):
    """Dòng thời gian trạng thái của đơn (hiển thị cho khách)."""
    __tablename__ = "order_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20))
    ts: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    note: Mapped[str | None] = mapped_column(Text)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    provider: Mapped[str] = mapped_column(String(20))  # mock | vietqr (sau này)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | succeeded | failed | refunded
    txn_ref: Mapped[str] = mapped_column(String(64), index=True)  # mã giao dịch (1 lần đặt có thể chung mã)
    amount: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    order: Mapped[Order] = relationship(back_populates="payments")
