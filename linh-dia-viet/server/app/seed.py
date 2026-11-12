"""Dữ liệu mẫu: các đền (kèm nhu cầu + toạ độ), danh mục lễ vật bán lẻ, 1 thiết bị pi-demo-01, 1 admin. Chạy lại nhiều lần không sao."""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import db as dbmod
from .config import get_settings
from .models import Device, OfferingPackage, PrayerTemplate, Setting, Temple, TempleStaff, User
from .prayer_text import DEFAULT_TEMPLATE
from .security import hash_password, hash_token

log = logging.getLogger("linhdia.seed")

TEMPLES = [
    dict(slug="den-ngoc-son", name="Đền Ngọc Sơn", address="Đinh Tiên Hoàng, Hoàn Kiếm", province="Hà Nội",
         deity="Đức Thánh Trần Hưng Đạo và Văn Xương Đế Quân",
         description="Ngôi đền trên đảo Ngọc giữa hồ Hoàn Kiếm, qua cầu Thê Húc.",
         purposes="may-man,cong-danh,binh-an", lat=21.0307, lng=105.8524),
    dict(slug="chua-tran-quoc", name="Chùa Trấn Quốc", address="Thanh Niên, Tây Hồ", province="Hà Nội",
         deity="chư Phật mười phương, chư vị Bồ Tát",
         description="Ngôi chùa cổ bên Hồ Tây, có lịch sử gần 1.500 năm.",
         purposes="may-man,binh-an,giai-han", lat=21.0480, lng=105.8368),
    dict(slug="den-ba-chua-xu", name="Miếu Bà Chúa Xứ Núi Sam", address="Núi Sam, Châu Đốc", province="An Giang",
         deity="Bà Chúa Xứ Thánh Mẫu",
         description="Nơi thờ Bà Chúa Xứ dưới chân núi Sam, lễ vía lớn vào tháng Tư âm lịch.",
         purposes="may-man,tai-loc,binh-an", lat=10.6806, lng=105.0806),
    dict(slug="phu-tay-ho", name="Phủ Tây Hồ", address="Đặng Thai Mai, Tây Hồ", province="Hà Nội",
         deity="Thánh Mẫu Liễu Hạnh",
         description="Phủ thờ Mẫu trên bán đảo Hồ Tây, đông người đi lễ đầu năm cầu may.",
         purposes="may-man,tai-loc,tinh-duyen", lat=21.0572, lng=105.8195),
    dict(slug="den-ba-chua-kho", name="Đền Bà Chúa Kho", address="Cổ Mễ, Vũ Ninh", province="Bắc Ninh",
         deity="Bà Chúa Kho",
         description="Ngôi đền trên núi Kho, nơi khách thập phương đến cầu tài lộc, buôn bán thuận lợi.",
         purposes="may-man,tai-loc", lat=21.1680, lng=106.0597),
    dict(slug="den-quan-thanh", name="Đền Quán Thánh", address="Thanh Niên, Ba Đình", province="Hà Nội",
         deity="Huyền Thiên Trấn Vũ",
         description="Một trong Thăng Long tứ trấn, có tượng Huyền Thiên Trấn Vũ bằng đồng đen.",
         purposes="may-man,binh-an,suc-khoe", lat=21.0429, lng=105.8365),
    dict(slug="chua-ha", name="Chùa Hà", address="Chùa Hà, Cầu Giấy", province="Hà Nội",
         deity="chư Phật, Đức Thánh Mẫu",
         description="Ngôi chùa nổi tiếng với người trẻ đến cầu duyên.",
         purposes="tinh-duyen,binh-an", lat=21.0367, lng=105.7975),
    dict(slug="chua-phuc-khanh", name="Chùa Phúc Khánh", address="Tây Sơn, Đống Đa", province="Hà Nội",
         deity="chư Phật mười phương",
         description="Ngôi chùa đông người đến làm lễ dâng sao giải hạn đầu năm.",
         purposes="giai-han,binh-an,suc-khoe", lat=21.0122, lng=105.8236),
    dict(slug="den-tran-nam-dinh", name="Đền Trần", address="Trần Thừa, Lộc Vượng", province="Nam Định",
         deity="các vua Trần",
         description="Nơi thờ các vua Trần, nổi tiếng với lễ khai ấn đầu xuân cầu công danh.",
         purposes="may-man,cong-danh,giai-han", lat=20.4335, lng=106.1770),
    dict(slug="chua-bai-dinh", name="Chùa Bái Đính", address="Gia Sinh, Gia Viễn", province="Ninh Bình",
         deity="Phật Thích Ca Mâu Ni, Quan Thế Âm Bồ Tát",
         description="Quần thể chùa lớn trên núi Bái Đính.",
         purposes="may-man,binh-an", lat=20.2731, lng=105.8650),
    dict(slug="chua-huong", name="Chùa Hương", address="Hương Sơn, Mỹ Đức", province="Hà Nội",
         deity="Quan Thế Âm Bồ Tát",
         description="Động Hương Tích trong quần thể Hương Sơn, mùa hội từ tháng Giêng đến tháng Ba âm lịch.",
         purposes="may-man,tai-loc,tinh-duyen", lat=20.6170, lng=105.7480),
    dict(slug="van-mieu", name="Văn Miếu – Quốc Tử Giám", address="Quốc Tử Giám, Đống Đa", province="Hà Nội",
         deity="Khổng Tử, Chu Văn An",
         description="Nơi sĩ tử đến cầu đỗ đạt trước mùa thi.",
         purposes="cong-danh", lat=21.0277, lng=105.8355),
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
    # v2: món lẻ cho mâm nhỏ
    dict(name="Hoa quả", unit="quả", price=15_000, max_qty=10, description="Cam, quýt, bưởi… tính theo từng quả."),
    dict(name="Bánh giầy giò", unit="cái", price=25_000, max_qty=10, description="Bánh giầy kẹp giò lụa, lót lá chuối."),
    dict(name="Sữa hộp", unit="hộp", price=10_000, max_qty=10, description="Hộp sữa tươi nhỏ."),
    dict(name="Trà", unit="gói", price=30_000, max_qty=5, description="Gói chè/trà khô dâng lễ."),
    dict(name="Tiền giọt dầu", unit="tờ", price=10_000, max_qty=10, description="Tờ tiền lẻ đặt lên mâm, sau lễ bỏ hòm công đức."),
]
CATALOG_VERSION = "2"  # tăng khi thêm món vào ITEMS: lần seed sau bổ sung món còn thiếu (1 lần, không hồi sinh món admin đã xoá)


def seed(db: Session) -> None:
    s = get_settings()
    if not db.scalar(select(User).where(User.role == "admin")):
        db.add(User(name="Quản trị", email=s.admin_email, password_hash=hash_password(s.admin_password), role="admin"))
    if not db.get(Device, s.demo_device_id):
        db.add(Device(id=s.demo_device_id, name="Pi demo", token_hash=hash_token(s.demo_device_token)))
        db.flush()
    for i, t in enumerate(TEMPLES):
        have = db.scalar(select(Temple).where(Temple.slug == t["slug"]))
        if not have:
            db.add(Temple(**t, device_id=s.demo_device_id if i == 0 else None))
        elif not have.purposes and have.lat is None:  # đền đã có từ trước khi thêm nhu cầu + toạ độ
            have.purposes, have.lat, have.lng = t["purposes"], t["lat"], t["lng"]
    if not db.scalar(select(OfferingPackage)):
        for i, it in enumerate(ITEMS):
            db.add(OfferingPackage(**it, sort=i))
        db.merge(Setting(key="seed:catalog", value=CATALOG_VERSION))
    elif (db.get(Setting, "seed:catalog") or Setting(value="1")).value != CATALOG_VERSION:
        have = set(db.scalars(select(OfferingPackage.name).where(OfferingPackage.temple_id.is_(None))))
        top = max(db.scalars(select(OfferingPackage.sort)), default=0)
        for it in ITEMS:
            if it["name"] not in have:
                top += 1
                db.add(OfferingPackage(**it, sort=top))
                log.info("Thêm lễ vật mới vào danh mục: %s", it["name"])
        db.merge(Setting(key="seed:catalog", value=CATALOG_VERSION))
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
