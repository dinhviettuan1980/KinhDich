from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from ..config import get_settings
from ..db import get_db
from ..models import Device, OfferingPackage, Temple, utcnow
from ..web import render, require_user

router = APIRouter()


def device_online(device: Device | None) -> bool:
    if not device or device.revoked or not device.online or not device.last_seen_at:
        return False
    return utcnow() - device.last_seen_at < timedelta(seconds=get_settings().device_offline_after_seconds)


def packages_for(db: Session, temple_ids: list[int]) -> list[OfferingPackage]:
    """Gói dùng chung + (nếu chỉ chọn 1 đền) gói riêng của đền đó."""
    cond = OfferingPackage.temple_id.is_(None)
    if len(temple_ids) == 1:
        cond = or_(cond, OfferingPackage.temple_id == temple_ids[0])
    return list(db.scalars(select(OfferingPackage).where(cond, OfferingPackage.active.is_(True))
                           .order_by(OfferingPackage.price)))


@router.get("/")
def home(request: Request, q: str = "", db: Session = Depends(get_db), user=Depends(require_user)):
    stmt = select(Temple).options(joinedload(Temple.device)).where(Temple.status == "active").order_by(Temple.name)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Temple.name.ilike(like), Temple.province.ilike(like), Temple.address.ilike(like)))
    temples = list(db.scalars(stmt).unique())
    ctx = {"temples": temples, "q": q, "online": {t.id: device_online(t.device) for t in temples}}
    if request.headers.get("hx-request"):
        return render(request, "public/_temple_list.html", ctx)
    return render(request, "public/home.html", ctx)


@router.get("/den/{slug}")
def temple_detail(slug: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
    temple = db.scalar(select(Temple).where(Temple.slug == slug, Temple.status == "active"))
    if not temple:
        raise HTTPException(404, "Không tìm thấy đền/chùa")
    return render(request, "public/temple.html", {
        "temple": temple, "online": device_online(temple.device), "packages": packages_for(db, [temple.id]),
    })


@router.get("/healthz")
def healthz():
    return {"ok": True}
