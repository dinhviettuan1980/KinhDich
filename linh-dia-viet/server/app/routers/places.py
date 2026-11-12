"""Bản đồ đình chùa toàn quốc (công khai, không cần đăng nhập): tra cứu → nơi nào nhận lễ từ xa thì đặt lễ ngay."""
import gzip
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..db import get_db
from ..models import PLACE_KINDS, SacredPlace, Temple
from ..web import current_user, render
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
