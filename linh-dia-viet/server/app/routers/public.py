import math
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from ..config import get_settings
from ..db import get_db
from .. import deities
from ..models import PURPOSES, Deity, Device, OfferingPackage, Temple, utcnow
from ..web import render, require_user

router = APIRouter()


def device_online(device: Device | None) -> bool:
    if not device or device.revoked or not device.online or not device.last_seen_at:
        return False
    return utcnow() - device.last_seen_at < timedelta(seconds=get_settings().device_offline_after_seconds)


def packages_for(db: Session, temple_ids: list[int]) -> list[OfferingPackage]:
    """Lễ vật dùng chung + (nếu chỉ chọn 1 đền) lễ vật riêng của đền đó."""
    cond = OfferingPackage.temple_id.is_(None)
    if len(temple_ids) == 1:
        cond = or_(cond, OfferingPackage.temple_id == temple_ids[0])
    return list(db.scalars(select(OfferingPackage).where(cond, OfferingPackage.active.is_(True))
                           .order_by(OfferingPackage.sort, OfferingPackage.price, OfferingPackage.id)))


def distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Khoảng cách đường chim bay (haversine)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lng2 - lng1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def _coord(raw: str, limit: float) -> float | None:
    try:
        v = float(raw)
    except ValueError:
        return None
    return v if math.isfinite(v) and abs(v) <= limit else None


@router.get("/")
def home(request: Request, q: str = "", nhu_cau: str = "", lat: str = "", lng: str = "",
         db: Session = Depends(get_db), user=Depends(require_user)):
    stmt = select(Temple).options(joinedload(Temple.device)).where(Temple.status == "active").order_by(Temple.name)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Temple.name.ilike(like), Temple.province.ilike(like), Temple.address.ilike(like),
                              Temple.deity.ilike(like), Temple.description.ilike(like)))
    temples = list(db.scalars(stmt).unique())
    if nhu_cau in PURPOSES:
        temples = [t for t in temples if nhu_cau in t.purpose_list]
    else:
        nhu_cau = ""
    # vị trí khách (trình duyệt gửi lên khi bấm "Gần tôi"): sắp đền gần trước, đền chưa có toạ độ xuống cuối
    here = (_coord(lat, 90), _coord(lng, 180))
    dist = {}
    if None not in here:
        dist = {t.id: distance_km(*here, t.lat, t.lng) for t in temples if t.lat is not None and t.lng is not None}
        temples.sort(key=lambda t: (t.id not in dist, dist.get(t.id, 0)))
    ctx = {"temples": temples, "q": q, "nhu_cau": nhu_cau, "purposes": PURPOSES, "dist": dist,
           "lat": lat if dist else "", "lng": lng if dist else "",
           "online": {t.id: device_online(t.device) for t in temples}}
    # bấm "quay lại" từ trang đền: htmx xin lại cả trang (HX-History-Restore-Request) chứ không phải mảnh danh sách
    if request.headers.get("hx-request") and not request.headers.get("hx-history-restore-request"):
        return render(request, "public/_temple_list.html", ctx)
    return render(request, "public/home.html", ctx)


@router.get("/den/{slug}")
def temple_detail(slug: str, request: Request, lat: str = "", lng: str = "", db: Session = Depends(get_db),
                  user=Depends(require_user)):
    temple = db.scalar(select(Temple).where(Temple.slug == slug, Temple.status == "active"))
    if not temple:
        raise HTTPException(404, "Không tìm thấy đền/chùa")
    here = (_coord(lat, 90), _coord(lng, 180))
    dist = distance_km(*here, temple.lat, temple.lng) if None not in here and temple.lat is not None else None
    return render(request, "public/temple.html", {
        "temple": temple, "purposes": PURPOSES, "dist": dist, "home": here if dist is not None else None,
        "deities": deities.for_temple(db, temple), "online": device_online(temple.device), "packages": packages_for(db, [temple.id]),
    })


@router.get("/than-thanh")
def deity_list(request: Request, q: str = "", nhom: str = "", db: Session = Depends(get_db), user=Depends(require_user)):
    """Tra cứu thần thánh (chỉ mục độ tin cậy Cao / Trung bình)."""
    rows = [d for d in db.scalars(select(Deity).order_by(Deity.id)) if d.public]
    groups = {}
    for d in rows:
        groups.setdefault(d.group_code, d.group_name)
    if nhom in groups:
        rows = [d for d in rows if d.group_code == nhom]
    if q.strip():
        k = q.strip().lower()
        rows = [d for d in rows if any(k in (x or "").lower() for x in
                                       (d.name, d.aliases, d.role, d.places, d.province_old, d.province_new))]
    return render(request, "public/deities.html", {"deities": rows, "q": q, "nhom": nhom, "groups": groups})


@router.get("/may")
def phone_device(request: Request):
    """Trang biến điện thoại Android thành một thiết bị đền (loa + camera + micro của máy). Không cần đăng nhập:
    quyền nằm ở mã + token thiết bị (tạo ở Admin → Thiết bị)."""
    return render(request, "device/phone.html", {})


@router.get("/healthz")
def healthz():
    return {"ok": True}
