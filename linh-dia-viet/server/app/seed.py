"""Dữ liệu mẫu: 3 đền, 4 gói lễ, 1 thiết bị pi-demo-01, 1 admin. Chạy lại nhiều lần không sao."""
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

PACKAGES = [
    dict(name="Lễ chay thanh tịnh", price=150_000, description="Hương, hoa tươi, quả, nước sạch."),
    dict(name="Lễ hoa quả", price=250_000, description="Hương, hoa, mâm ngũ quả, trầu cau, nước."),
    dict(name="Lễ mặn đầy đủ", price=500_000, description="Hương, hoa, quả, xôi, gà luộc, rượu, vàng mã."),
    dict(name="Lễ dâng sao giải hạn", price=350_000, description="Hương, hoa, quả, nến, sớ dâng sao."),
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
        for p in PACKAGES:
            db.add(OfferingPackage(**p))
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
