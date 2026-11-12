"""Bản đồ đình chùa toàn quốc (công khai, không cần đăng nhập): tra cứu → nơi nào nhận lễ từ xa thì đặt lễ ngay."""
import gzip
import json
import secrets

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from ..db import get_db
from ..models import PLACE_KINDS, SacredPlace, Temple, User
from ..security import check_csrf
from ..web import audit, current_user, flash, render, require_admin, u
from .public import device_online

router = APIRouter()


def bookable(temple: Temple | None) -> int:
    """2 = đặt lễ được (đền hiển thị + có thiết bị), 1 = đền đối tác chưa lắp thiết bị, 0 = chỉ là danh bạ."""
    if temple is None or temple.status != "active":
        return 0
    return 2 if temple.device_id else 1


@router.get("/ban-do")
def map_page(request: Request, db: Session = Depends(get_db), user=Depends(current_user)):
    total = db.scalar(select(func.count()).select_from(SacredPlace).where(SacredPlace.status == "active"))
    return render(request, "public/map.html", {"total": total})


@router.get("/ban-do/diem.json")
def map_points(request: Request, db: Session = Depends(get_db)):
    """Mọi điểm ở dạng mảng gọn (≈5 nghìn điểm, vài trăm KB): trình duyệt tự lọc, tìm, gom cụm, tính "gần tôi"."""
    rows = db.scalars(select(SacredPlace).options(joinedload(SacredPlace.temple))
                      .where(SacredPlace.status == "active").order_by(SacredPlace.id)).all()
    provinces = sorted({p.province for p in rows if p.province})
    pidx = {name: i for i, name in enumerate(provinces)}
    points = [[p.id, p.lat, p.lng, p.kind, p.name, pidx.get(p.province, -1), bookable(p.temple)] for p in rows]
    body = json.dumps({"kinds": PLACE_KINDS, "provinces": provinces, "points": points},
                      ensure_ascii=False, separators=(",", ":")).encode()
    headers = {"Cache-Control": "public, max-age=300", "Vary": "Accept-Encoding"}
    if "gzip" in request.headers.get("accept-encoding", ""):  # ~290 KB → ~90 KB
        body, headers["Content-Encoding"] = gzip.compress(body, 6), "gzip"
    return Response(body, media_type="application/json", headers=headers)


@router.get("/dia-diem/{place_id}")
def place_detail(place_id: int, request: Request, db: Session = Depends(get_db), user=Depends(current_user)):
    place = db.scalar(select(SacredPlace).options(joinedload(SacredPlace.temple).joinedload(Temple.device))
                      .where(SacredPlace.id == place_id))
    if place is None or (place.status != "active" and not (user and user.is_admin)):
        raise HTTPException(404, "Không tìm thấy địa điểm")
    return render(request, "public/place.html", {
        "p": place, "bookable": bookable(place.temple),
        "online": device_online(place.temple.device) if place.temple else False,
    })


# ---- Quản trị danh bạ (admin): sửa tay dữ liệu nhập tự động, ẩn điểm sai, thêm điểm còn thiếu ----
ADMIN_PAGE = 50


@router.get("/admin/dia-diem")
def admin_places(request: Request, q: str = "", prov: str = "", kind: str = "", status: str = "", page: int = 1,
                 db: Session = Depends(get_db), user: User = Depends(require_admin)):
    stmt = select(SacredPlace).options(joinedload(SacredPlace.temple))
    if q.strip():
        like = f"%{q.strip()}%"
        cond = [SacredPlace.name.ilike(like), SacredPlace.address.ilike(like)]
        if q.strip().isdigit():
            cond.append(SacredPlace.id == int(q.strip()))
        stmt = stmt.where(or_(*cond))
    if prov:
        stmt = stmt.where(SacredPlace.province == prov)
    if kind in PLACE_KINDS:
        stmt = stmt.where(SacredPlace.kind == kind)
    if status in ("active", "hidden"):
        stmt = stmt.where(SacredPlace.status == status)
    elif status == "edited":
        stmt = stmt.where(SacredPlace.edited.is_(True))
    elif status == "linked":
        stmt = stmt.where(SacredPlace.temple_id.is_not(None))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    page = max(1, page)
    rows = db.scalars(stmt.order_by(SacredPlace.province, SacredPlace.name)
                      .offset((page - 1) * ADMIN_PAGE).limit(ADMIN_PAGE)).unique().all()
    provinces = db.scalars(select(SacredPlace.province).distinct().where(SacredPlace.province != "")
                           .order_by(SacredPlace.province)).all()
    return render(request, "admin/places.html", {
        "rows": rows, "total": total, "page": page, "pages": max(1, -(-total // ADMIN_PAGE)),
        "q": q, "prov": prov, "kind": kind, "status": status, "provinces": provinces, "kinds": PLACE_KINDS})


@router.get("/admin/dia-diem/{place_id}")
def admin_place_form(place_id: str, request: Request, db: Session = Depends(get_db),
                     user: User = Depends(require_admin)):
    if place_id == "moi":
        place = SacredPlace(kind="chua", status="active", source="manual", lat=None, lng=None)
    elif not place_id.isdigit() or (place := db.get(SacredPlace, int(place_id))) is None:
        raise HTTPException(404, "Không tìm thấy địa điểm")
    return render(request, "admin/place_form.html", {"p": place, "kinds": PLACE_KINDS})


@router.post("/admin/dia-diem/{place_id}", dependencies=[Depends(check_csrf)])
def admin_place_save(place_id: str, request: Request, name: str = Form(...), kind: str = Form("chua"),
                     province: str = Form(""), address: str = Form(""), lat: float = Form(...), lng: float = Form(...),
                     phone: str = Form(""), website: str = Form(""), description: str = Form(""),
                     description_source: str = Form(""), image_url: str = Form(""), status: str = Form("active"),
                     db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if not (8.0 <= lat <= 23.5 and 102.0 <= lng <= 117.5):
        raise HTTPException(400, "Toạ độ nằm ngoài Việt Nam (vĩ độ 8–23,5; kinh độ 102–117,5)")
    if not name.strip():
        raise HTTPException(400, "Thiếu tên")
    for url in (website, description_source, image_url):
        if url.strip() and not url.strip().startswith(("https://", "http://")):
            raise HTTPException(400, "Đường dẫn phải bắt đầu bằng http:// hoặc https://")
    if place_id == "moi":
        place = SacredPlace(source="manual", source_id=secrets.token_hex(6))
        db.add(place)
    elif not place_id.isdigit() or (place := db.get(SacredPlace, int(place_id))) is None:
        raise HTTPException(404, "Không tìm thấy địa điểm")
    place.name, place.kind = name.strip()[:200], kind if kind in PLACE_KINDS else "khac"
    place.province, place.address = province.strip()[:100], address.strip()[:300]
    place.lat, place.lng = round(lat, 6), round(lng, 6)
    place.phone, place.website = phone.strip()[:60], website.strip()[:300]
    place.description, place.description_source = description.strip(), description_source.strip()[:300]
    place.image_url, place.status = image_url.strip()[:500], status if status in ("active", "hidden") else "hidden"
    place.edited = True  # lần nhập snapshot sau không ghi đè
    db.flush()
    audit(db, f"user:{user.id}", "place.save", f"place:{place.id}", name=place.name, status=place.status)
    db.commit()
    flash(request, "Đã lưu địa điểm.", "ok")
    return RedirectResponse(u(f"/admin/dia-diem/{place.id}"), 303)
