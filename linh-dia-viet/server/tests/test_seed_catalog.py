"""Seed bổ sung lễ vật mới khi tăng CATALOG_VERSION: chỉ 1 lần, không hồi sinh món admin đã xoá."""
from sqlalchemy import select

from app import seed
from app.models import OfferingPackage, Setting


def _names(db):
    return set(db.scalars(select(OfferingPackage.name)))


def test_catalog_top_up_once(db):
    new = [it["name"] for it in seed.ITEMS[-5:]]
    for p in db.scalars(select(OfferingPackage).where(OfferingPackage.name.in_(new))):
        db.delete(p)  # giả lập DB production cũ (danh mục v1)
    db.merge(Setting(key="seed:catalog", value="1"))
    db.commit()
    seed.seed(db)
    db.commit()
    assert set(new) <= _names(db) and db.get(Setting, "seed:catalog").value == seed.CATALOG_VERSION
    gone = db.scalar(select(OfferingPackage).where(OfferingPackage.name == "Sữa hộp"))
    db.delete(gone)  # admin xoá món → seed lần sau không thêm lại
    db.commit()
    seed.seed(db)
    db.commit()
    assert "Sữa hộp" not in _names(db)
