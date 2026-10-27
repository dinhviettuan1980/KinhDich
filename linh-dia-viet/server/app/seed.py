"""Dữ liệu mẫu: 3 đền, danh mục lễ vật bán lẻ, 1 thiết bị pi-demo-01, 1 admin. Chạy lại nhiều lần không sao."""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import db as dbmod
from .config import get_settings
from .models import Device, OfferingPackage, PrayerTemplate, Temple, TempleStaff, User
from .prayer_text import DEFAULT_TEMPLATE
from .security import hash_password, hash_token

log = logging.getLogger("linhdia.seed")

TEMPLES = [
    dict(slug="den-ngoc-son", name="Đền Ngọc Sơn", address="Đinh Tiên Hoàng, Hoàn Kiếm", province="Hà Nội",
         deity="Đức Thánh Trần Hưng Đạo và Văn Xương Đế Quân",
         description="Ngôi đền trên đảo Ngọc giữa hồ Hoàn Kiếm, qua cầu Thê Húc."),
    dict(slug="chua-tran-quoc", name="Chùa Trấn Quốc", address="Thanh Niên, Tây Hồ", province="Hà Nội",
         deity="chư Phật mười phương, chư vị Bồ Tát",
         description="Ngôi chùa cổ bên Hồ Tây, có lịch sử gần 1.500 năm."),
    dict(slug="den-ba-chua-xu", name="Miếu Bà Chúa Xứ Núi Sam", address="Núi Sam, Châu Đốc", province="An Giang",
         deity="Bà Chúa Xứ Thánh Mẫu",
         description="Nơi thờ Bà Chúa Xứ dưới chân núi Sam, lễ vía lớn vào tháng Tư âm lịch."),
]

ITEMS = [
    dict(name="Hương (nhang)", unit="bó", price=20_000, max_qty=10, description="Hương trầm, 1 bó khoảng 100 nén."),
    dict(name="Nến", unit="đôi", price=20_000, max_qty=10, description="Đôi nến đỏ thắp hai bên ban thờ."),
    dict(name="Hoa tươi", unit="bó", price=60_000, max_qty=5, description="Hoa cúc vàng, hoa hồng hoặc hoa sen theo mùa."),
    dict(name="Ngũ quả", unit="mâm", price=150_000, max_qty=3, description="Năm loại quả tươi bày trên đĩa."),
    dict(name="Trầu cau", unit="cơi", price=30_000, max_qty=5, description="Lá trầu têm cánh phượng và quả cau."),
    dict(name="Oản", unit="cặp", price=30_000, max_qty=5, description="Oản đường hình tháp, dùng cho lễ chay."),
    dict(name="Xôi gấc", unit="đĩa", price=60_000, max_qty=5, description="Xôi gấc đỏ (có thể đổi xôi đỗ)."),
    dict(name="Gà luộc", unit="con", price=280_000, max_qty=3, description="Gà trống luộc nguyên con, cài hoa hồng."),
    dict(name="Rượu trắng", unit="chai", price=40_000, max_qty=5, description="Rượu nếp nhỏ."),
    dict(name="Bánh kẹo", unit="gói", price=30_000, max_qty=5, description="Bánh kẹo, chè lam."),
    dict(name="Vàng mã", unit="bộ", price=50_000, max_qty=5, description="Tiền vàng, sớ giấy (đốt sau lễ)."),
    dict(name="Nước sạch", unit="chai", price=10_000, max_qty=5, description="Chai nước tinh khiết."),
]


def seed(db: Session) -> None:
    s = get_settings()
    if not db.scalar(select(User).where(User.role == "admin")):
        db.add(User(name="Quản trị", email=s.admin_email, password_hash=hash_password(s.admin_password), role="admin"))
    if not db.get(Device, s.demo_device_id):
        db.add(Device(id=s.demo_device_id, name="Pi demo", token_hash=hash_token(s.demo_device_token)))
        db.flush()
    for i, t in enumerate(TEMPLES):
        if not db.scalar(select(Temple).where(Temple.slug == t["slug"])):
            db.add(Temple(**t, device_id=s.demo_device_id if i == 0 else None))
    if not db.scalar(select(OfferingPackage)):
        for i, it in enumerate(ITEMS):
            db.add(OfferingPackage(**it, sort=i))
    if not db.scalar(select(PrayerTemplate).where(PrayerTemplate.temple_id.is_(None))):
        db.add(PrayerTemplate(name="Mẫu chung", body=DEFAULT_TEMPLATE))
    db.flush()
    if s.env in ("dev", "test") and s.demo_staff_password:
        # Tài khoản mẫu cho 2 vai trò nhân sự, gắn với đền đầu tiên (chỉ khi dev/test).
        first = db.scalar(select(Temple).where(Temple.slug == TEMPLES[0]["slug"]))
        for email, name, role in (("quanly@example.com", "Quản lý Đền Ngọc Sơn", "temple_manager"),
                                  ("kiosk@example.com", "Kiosk Đền Ngọc Sơn", "vendor")):
            if not db.scalar(select(User).where(User.email == email)):
                db.add(User(name=name, email=email, role=role, password_hash=hash_password(s.demo_staff_password),
                            staff_of=[TempleStaff(temple_id=first.id)]))
    db.commit()


if __name__ == "__main__":
    dbmod.init_engine()
    with dbmod.SessionLocal() as session:
        seed(session)
    log.info("Seed xong")
