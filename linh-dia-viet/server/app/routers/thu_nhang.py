"""Thủ nhang đọc sớ tại đền: mở trang, bấm "Bắt đầu đọc" → camera tự quay → "Kết thúc" → video tự tải lên."""
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .. import audio
from .. import orders as svc
from ..db import get_db
from ..models import Evidence, Order, User, utcnow
from ..security import check_csrf
from ..storage import get_storage
from ..web import can_manage_temple, render, require_user, u

router = APIRouter(prefix="/thu-nhang")
csrf = [Depends(check_csrf)]
MAX_VIDEO_BYTES = 24 * 1024 * 1024
MAX_PHOTO_BYTES = 6 * 1024 * 1024


def _reading_order(db: Session, order_id: int, user: User) -> Order:
    o = db.get(Order, order_id)
    if o is None or o.prayer.kind != "in_person":
        raise HTTPException(404)
    if not can_manage_temple(user, o.temple_id, roles=("temple_manager",)) or not user.active:
        raise HTTPException(403, "Chỉ thủ nhang của đền này")
    if user.role == "temple_manager" and not user.is_staff:
        raise HTTPException(403, "Tài khoản chưa được duyệt")
    return o


@router.get("/doc/{order_id}")
def read_page(order_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    o = _reading_order(db, order_id, user)
    lo, hi = svc.reading_window(o)
    return render(request, "thu_nhang/doc.html", {"o": o, "window": (lo, hi), "now": utcnow(),
                                                  "script": o.script_text or ""})


@router.post("/doc/{order_id}/bat-dau", dependencies=csrf)
def start(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    o = _reading_order(db, order_id, user)
    try:
        svc.start_reading(db, o, f"user:{user.id}")
    except ValueError as e:
        return JSONResponse({"error": str(e)}, 409)
    db.commit()
    return {"ok": True, "started_at": o.read_started_at.isoformat()}


@router.post("/doc/{order_id}/ket-thuc", dependencies=csrf)
async def finish(order_id: int, video: UploadFile = File(...), anh_dau: UploadFile | None = File(None),
                 anh_cuoi: UploadFile | None = File(None), db: Session = Depends(get_db),
                 user: User = Depends(require_user)):
    o = _reading_order(db, order_id, user)
    if o.status != "playing":
        return JSONResponse({"error": "Chưa bấm bắt đầu đọc, hoặc đơn đã kết thúc"}, 409)
    data = await video.read(MAX_VIDEO_BYTES + 1)
    if len(data) > MAX_VIDEO_BYTES:
        return JSONResponse({"error": "Video quá lớn"}, 413)
    if data[:4] == b"\x1a\x45\xdf\xa3":  # WebM → MP4
        try:
            data = audio.webm_to_mp4(data)
        except audio.AudioError:
            return JSONResponse({"error": "Video hỏng"}, 415)
    if data[4:8] != b"ftyp":
        return JSONResponse({"error": "Chỉ nhận video MP4/WebM"}, 415)
    storage, now = get_storage(), utcnow()
    db.add(Evidence(order_id=o.id, kind="video", note="video", captured_at=now,
                    path=storage.put_bytes(data, f"evidence/{o.id}/video-{uuid.uuid4().hex[:10]}.mp4")))
    for up, phase in ((anh_dau, "start"), (anh_cuoi, "after")):
        if up is None:
            continue
        img = await up.read(MAX_PHOTO_BYTES + 1)
        if 0 < len(img) <= MAX_PHOTO_BYTES and img[:2] == b"\xff\xd8":  # chỉ nhận JPEG
            db.add(Evidence(order_id=o.id, kind="photo", note=phase, captured_at=now,
                            path=storage.put_bytes(img, f"evidence/{o.id}/{phase}-{uuid.uuid4().hex[:10]}.jpg")))
    svc.finish_reading(db, o, f"user:{user.id}", now)
    db.commit()
    return {"ok": True, "redirect": u("/admin/lich-le")}
