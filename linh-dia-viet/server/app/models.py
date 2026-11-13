from datetime import date, datetime, timezone

from sqlalchemy import false as sql_false
from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, TypeDecorator, UniqueConstraint
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
    # Tài khoản đối tác (thủ nhang / kiosk) phải được admin duyệt: approved | pending | rejected
    approval: Mapped[str] = mapped_column(String(10), default="approved", server_default="approved")
    # Thông tin tín chủ (lưu 1 lần, tự điền khi đặt lễ)
    devotee_name: Mapped[str | None] = mapped_column(String(120))
    birth_year: Mapped[int | None] = mapped_column(Integer)  # năm âm lịch (tính từ ngày sinh) — dùng trong sớ
    birth_date: Mapped[date | None] = mapped_column(Date)  # ngày sinh dương lịch
    address: Mapped[str | None] = mapped_column(String(300))
    wish: Mapped[str | None] = mapped_column(Text)
    # Thẻ thanh toán GIẢ LẬP: chỉ lưu hãng + 4 số cuối + hạn, không bao giờ lưu số thẻ đầy đủ / CVC
    card_brand: Mapped[str | None] = mapped_column(String(20))
    card_last4: Mapped[str | None] = mapped_column(String(4))
    card_exp: Mapped[str | None] = mapped_column(String(5))  # MM/YY
    card_holder: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    staff_of: Mapped[list["TempleStaff"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def devotee_complete(self) -> bool:
        return bool(self.devotee_name and self.birth_year and self.address)

    @property
    def profile_complete(self) -> bool:
        """Đủ điều kiện lập sớ: họ tên, ngày sinh, địa chỉ."""
        return bool(self.devotee_name and self.birth_date and self.address)

    @property
    def has_card(self) -> bool:
        return bool(self.card_last4)

    @property
    def card_label(self) -> str:
        return f"{self.card_brand} •••• {self.card_last4}" if self.card_last4 else ""

    @property
    def is_staff(self) -> bool:
        return self.role in ("vendor", "temple_manager") and self.approval == "approved"

    @property
    def is_partner_pending(self) -> bool:
        return self.role in ("vendor", "temple_manager") and self.approval != "approved"

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
    mqtt_hash: Mapped[str | None] = mapped_column(String(300))  # băm PBKDF2 cho file passwd của Mosquitto
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    net_type: Mapped[str | None] = mapped_column(String(10))
    version: Mapped[str | None] = mapped_column(String(40))
    test_photo_key: Mapped[str | None] = mapped_column(String(300))  # ảnh "chụp thử" gần nhất
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
    # True: đơn đã thanh toán phải được thủ nhang nhận mới xếp lịch (quá hạn tự hoàn tiền)
    require_approval: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sql_false())
    device: Mapped[Device | None] = relationship()


PLACE_INTENTS = {"binh-an": "Bình an", "tai-loc": "Tài lộc", "tinh-duyen": "Tình duyên", "suc-khoe": "Sức khỏe",
                 "cong-danh": "Công danh"}
PLACE_KINDS = {"chua": "Chùa", "den": "Đền", "dinh": "Đình", "mieu": "Miếu", "phu": "Phủ", "khac": "Nơi thờ tự",
               "ntls": "Nghĩa trang liệt sĩ", "tuongniem": "Đài tưởng niệm liệt sĩ", "ntrang": "Nghĩa trang",
               "mo": "Lăng mộ"}
CEMETERY_KINDS = ("ntls", "tuongniem", "ntrang", "mo")


class SacredPlace(Base):
    """Danh bạ đình chùa toàn quốc (chỉ để tra cứu trên bản đồ). Nhập từ OpenStreetMap (ODbL) + Wikidata (CC0),
    mô tả lấy từ Wikipedia (CC BY-SA, ghi nguồn). Gắn `temple_id` khi địa điểm là đền nhận đặt lễ."""
    __tablename__ = "sacred_places"
    __table_args__ = (UniqueConstraint("source", "source_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(20))  # osm | wikidata | manual
    source_id: Mapped[str] = mapped_column(String(40))  # vd "way/123", "Q1234"
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(10), default="khac", index=True)  # khoá của PLACE_KINDS
    religion: Mapped[str] = mapped_column(String(30), default="")
    lat: Mapped[float] = mapped_column(Float, index=True)
    lng: Mapped[float] = mapped_column(Float, index=True)
    province: Mapped[str] = mapped_column(String(100), default="", index=True)
    address: Mapped[str] = mapped_column(String(300), default="")
    phone: Mapped[str] = mapped_column(String(60), default="")
    website: Mapped[str] = mapped_column(String(300), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    description_source: Mapped[str] = mapped_column(String(300), default="")  # URL bài gốc (Wikipedia…)
    aliases: Mapped[str] = mapped_column(Text, default="")  # tên gọi khác, cách nhau "; " (vd "Đền Ông Hoàng Bảy")
    keywords: Mapped[str] = mapped_column(Text, default="")  # từ khoá tìm kiếm (data/places_keywords.json; admin sửa → `edited`, snapshot không ghi đè)
    # thông tin thờ tự (danh sách đền phủ biên soạn: data/places_curated.json; admin sửa được)
    deity: Mapped[str] = mapped_column(String(300), default="")  # thờ ai, vd "Ông Hoàng Đôi, Ông Hoàng Bảy"
    deity_groups: Mapped[str] = mapped_column(String(100), default="")  # hàng thánh: "Mẫu", "Quan", "Ông Hoàng"…
    intents: Mapped[str] = mapped_column(String(100), default="")  # mã điều cầu, cách nhau dấu phẩy: tai-loc,binh-an
    festival: Mapped[str] = mapped_column(Text, default="")  # lễ hội / ngày tiệc
    priority: Mapped[int | None] = mapped_column(Integer)  # bậc ưu tiên 1 (cao nhất) – 3; None = không thuộc danh sách
    approx_location: Mapped[bool] = mapped_column(Boolean, default=False)  # toạ độ gần đúng (chưa xác minh)
    image_url: Mapped[str] = mapped_column(String(500), default="")
    wikidata: Mapped[str] = mapped_column(String(20), default="")
    status: Mapped[str] = mapped_column(String(10), default="active")  # active | hidden
    edited: Mapped[bool] = mapped_column(Boolean, default=False)  # admin đã sửa tay → lần nhập sau không ghi đè
    temple_id: Mapped[int | None] = mapped_column(ForeignKey("temples.id", ondelete="SET NULL"), unique=True)
    temple: Mapped[Temple | None] = relationship()
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow)

    @property
    def is_cemetery(self) -> bool:
        return self.kind in CEMETERY_KINDS

    @property
    def kind_label(self) -> str:
        return PLACE_KINDS.get(self.kind, PLACE_KINDS["khac"])

    @property
    def full_address(self) -> str:
        """Địa chỉ + tỉnh, không lặp tỉnh khi địa chỉ OSM đã có sẵn (vd "…, Hà Nội")."""
        addr, prov = self.address.strip(), self.province.strip()
        if prov and prov.lower() not in addr.lower():
            addr = f"{addr}, {prov}" if addr else prov
        return addr

    @property
    def map_query(self) -> str:
        """Chuỗi Google Maps dùng để tìm/chỉ đường: toạ độ nếu chính xác; nếu gần đúng thì tên + địa chỉ
        để Google tự tìm đúng vị trí (không lưu dữ liệu của Google)."""
        if self.approx_location:
            return ", ".join(x for x in (self.name, self.address, self.province) if x)
        return f"{self.lat},{self.lng}"

    @property
    def intent_list(self) -> list[tuple[str, str]]:
        return [(k, PLACE_INTENTS[k]) for k in (self.intents or "").split(",") if k in PLACE_INTENTS]

    @property
    def alias_list(self) -> list[str]:
        return [a.strip() for a in (self.aliases or "").split(";") if a.strip()]


class OfferingPackage(Base):
    """Một món lễ vật bán lẻ (hương, hoa, gà luộc…): khách chọn số lượng từng món, không bán theo combo."""
    __tablename__ = "offering_packages"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[int] = mapped_column(Integer)  # VND cho 1 đơn vị
    unit: Mapped[str] = mapped_column(String(30), default="phần", server_default="phần")  # bó, con, đĩa…
    max_qty: Mapped[int] = mapped_column(Integer, default=10, server_default="10")
    sort: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    image_url: Mapped[str] = mapped_column(String(300), default="")
    temple_id: Mapped[int | None] = mapped_column(ForeignKey("temples.id", ondelete="CASCADE"))  # NULL = dùng chung
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)  # kiosk bán món này
    stock: Mapped[int | None] = mapped_column(Integer)  # tồn kho; NULL = không giới hạn
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    temple: Mapped[Temple | None] = relationship()
    vendor: Mapped["User | None"] = relationship(foreign_keys=[vendor_id])


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
    kind: Mapped[str] = mapped_column(String(10))  # tts | recorded | in_person (thủ nhang đọc tại đền)
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
    package_id: Mapped[int | None] = mapped_column(ForeignKey("offering_packages.id"))  # đơn cũ (combo)
    scheduled_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)  # UTC
    play_asap: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sql_false())  # phát ngay khi xếp lịch xong
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Ho_Chi_Minh")
    status: Mapped[str] = mapped_column(String(20), default="created", index=True)
    total: Mapped[int] = mapped_column(Integer)  # VND, chốt giá lúc đặt
    script_text: Mapped[str | None] = mapped_column(Text)  # văn bản sớ cuối cùng cho đền này
    audio_key: Mapped[str | None] = mapped_column(String(300))  # file sẽ phát tại đền
    audio_sha256: Mapped[str | None] = mapped_column(String(64))
    note: Mapped[str | None] = mapped_column(Text)  # lý do từ chối/hủy/lỗi
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)  # kiosk của đơn
    service_fee: Mapped[int] = mapped_column(Integer, default=0, server_default="0")  # phí thủ nhang đọc sớ (đã nằm trong total)
    read_started_at: Mapped[datetime | None] = mapped_column(UTCDateTime())  # thủ nhang bắt đầu đọc sớ tại chỗ
    read_ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    accept_by: Mapped[datetime | None] = mapped_column(UTCDateTime())  # hạn thủ nhang trả lời (NULL = không cần duyệt)
    accepted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())  # thủ nhang đã nhận đơn
    tray_ready_at: Mapped[datetime | None] = mapped_column(UTCDateTime())  # kiosk báo mâm lễ đã bày
    clip_key: Mapped[str | None] = mapped_column(String(300))  # clip xem lại (ảnh mâm + bài khấn)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(foreign_keys=[user_id])
    vendor: Mapped[User | None] = relationship(foreign_keys=[vendor_id])
    prayer: Mapped[Prayer] = relationship(back_populates="orders")
    temple: Mapped[Temple] = relationship()
    package: Mapped[OfferingPackage | None] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(order_by="OrderItem.id", cascade="all, delete-orphan")
    events: Mapped[list["OrderEvent"]] = relationship(order_by="OrderEvent.id", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="order", order_by="Payment.id")

    @property
    def needs_approval(self) -> bool:
        """Đơn đang chờ thủ nhang nhận."""
        return self.accept_by is not None and self.accepted_at is None

    @property
    def offering_text(self) -> str:
        """Lễ vật của đơn, dạng đọc được: "3 bó hương, 1 con gà luộc"."""
        if self.items:
            return offering_text((i.qty, i.unit, i.name) for i in self.items)
        return self.package.name if self.package else ""

    @property
    def photos(self) -> list["Evidence"]:
        return [e for e in self.evidence if e.kind == "photo"]

    @property
    def video(self) -> "Evidence | None":
        """Video quay tại đền lúc đọc sớ (hình mâm lễ + tiếng thu tại chỗ), nếu thiết bị có gửi."""
        return next((e for e in self.evidence if e.kind == "video"), None)


def offering_text(lines) -> str:
    """[(3, "bó", "Hương"), (1, "con", "Gà luộc")] → "3 bó hương, 1 con gà luộc"."""
    return ", ".join(f"{q} {unit} {name[:1].lower()}{name[1:]}" for q, unit, name in lines)


class OrderItem(Base):
    """Lễ vật trong đơn — chốt tên/đơn vị/giá lúc đặt (sửa danh mục sau không đổi đơn cũ)."""
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    package_id: Mapped[int | None] = mapped_column(ForeignKey("offering_packages.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(30))
    price: Mapped[int] = mapped_column(Integer)
    qty: Mapped[int] = mapped_column(Integer)


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


class DeviceJob(Base):
    """Một lần giao bài khấn của 1 đơn xuống 1 thiết bị. id (uuid hex) chính là job_id trên MQTT."""
    __tablename__ = "device_jobs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    device_id: Mapped[str | None] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"), index=True)
    state: Mapped[str] = mapped_column(String(12), default="queued", index=True)
    # queued | delivered | downloaded | playing | done | error | cancelled
    play_at: Mapped[datetime] = mapped_column(UTCDateTime())
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    delivered_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    downloaded_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    playing_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    done_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    error: Mapped[str | None] = mapped_column(Text)
    log: Mapped[list | None] = mapped_column(JSON)  # [[ts, state, detail], ...]
    order: Mapped["Order"] = relationship(back_populates="jobs")
    device: Mapped[Device | None] = relationship()


class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("device_jobs.id", ondelete="SET NULL"))
    kind: Mapped[str] = mapped_column(String(10), default="photo")
    path: Mapped[str] = mapped_column(String(300))
    captured_at: Mapped[datetime] = mapped_column(UTCDateTime())
    note: Mapped[str | None] = mapped_column(String(200))  # before | start | after
    analysis: Mapped[dict | None] = mapped_column(JSON)  # kết quả nhận diện mâm lễ (app/recognition.py)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    order: Mapped["Order"] = relationship(viewonly=True)


Order.jobs = relationship(DeviceJob, back_populates="order", order_by=DeviceJob.created_at)
Order.evidence = relationship(Evidence, order_by=Evidence.captured_at)


def tray_check(order: Order) -> tuple[Evidence, dict] | None:
    """Kết quả nhận diện dùng để hiển thị: ảnh lúc khấn (mâm đã bày xong) → sau lễ → trước lễ."""
    rank = {"start": 0, "after": 1, "before": 2}
    done = [e for e in order.evidence if e.analysis and "items" in e.analysis]
    if not done:
        return None
    ev = min(done, key=lambda e: rank.get(e.note or "", 9))
    return ev, ev.analysis
