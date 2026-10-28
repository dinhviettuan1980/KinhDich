"""Trang đơn của khách: lịch sử, theo dõi (dòng thời gian cập nhật bằng polling HTMX), hủy, nghe lại."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

import logging
import threading

from .. import clips, orders as svc
from ..db import get_db
from ..models import Order, User
from ..security import check_csrf
from ..state_machine import LABELS, MAIN_LINE, TERMINAL, OrderStatus as S
from ..storage import get_storage
from ..web import flash, render, require_user, u

log = logging.getLogger("linhdia.orders")
router = APIRouter(prefix="/don")
_clip_lock = threading.Lock()  # tránh 2 request cùng dựng 1 clip (trình duyệt hay gửi nhiều Range request)


def owned_order(db: Session, order_id: int, user: User) -> Order:
    """Dữ liệu cá nhân trong đơn chỉ lộ cho chủ đơn và admin."""
    o = db.get(Order, order_id)
    if not o or (o.user_id != user.id and not user.is_admin):
        raise HTTPException(404)
    return o


def timeline(o: Order) -> list[dict]:
    reached = {e.status: e for e in o.events}
    items = [{"label": LABELS[S(e.status)], "ts": e.ts, "note": e.note, "done": True,
              "bad": e.status in ("rejected", "failed", "cancelled")} for e in o.events]
    if o.status in MAIN_LINE and o.status != S.COMPLETED:  # các bước còn lại (mờ)
        for st in MAIN_LINE[MAIN_LINE.index(S(o.status)) + 1:]:
            if st not in reached:
                items.append({"label": LABELS[st], "ts": None, "note": None, "done": False, "bad": False})
    return items


def detail_ctx(db: Session, o: Order) -> dict:
    return {"o": o, "timeline": timeline(o), "status_label": LABELS[S(o.status)], "can_cancel": svc.can_user_cancel(o),
            "final": S(o.status) in TERMINAL or o.status in ("rejected", "cancelled", "failed"),
            "evidence": o.photos, "video": o.video,
            "has_clip": bool(o.video) or bool(o.clip_key) or clips.can_build(o)}


@router.get("")
def history(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    orders = db.scalars(select(Order).where(Order.user_id == user.id).order_by(Order.id.desc()).limit(200)).all()
    cover = {}
    for o in orders:  # ảnh đại diện: ảnh sau lễ, không có thì ảnh mới nhất
        ph = sorted(o.photos, key=lambda e: (e.note == "after", e.id))
        if ph:
            cover[o.id] = ph[-1].id
    return render(request, "orders/list.html", {"orders": orders, "labels": LABELS, "cover": cover,
                                                "new_ref": request.query_params.get("moi", "")})


@router.get("/{order_id}")
def detail(order_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    o = owned_order(db, order_id, user)
    return render(request, "orders/detail.html", detail_ctx(db, o))


@router.get("/{order_id}/trang-thai")
def status_partial(order_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    o = owned_order(db, order_id, user)
    return render(request, "orders/_status.html", detail_ctx(db, o))


@router.post("/{order_id}/huy", dependencies=[Depends(check_csrf)])
def cancel(order_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    o = owned_order(db, order_id, user)
    if not svc.can_user_cancel(o):
        raise HTTPException(409, "Đơn không còn hủy được (thiết bị đã nhận lệnh hoặc đơn đã kết thúc).")
    svc.cancel(db, o, f"user:{user.id}")
    db.commit()
    flash(request, "Đã hủy đơn." + (" Yêu cầu hoàn tiền đã được ghi nhận." if o.status == "refund_requested" else ""), "ok")
    return RedirectResponse(u(f"/don/{o.id}"), 303)


@router.get("/{order_id}/audio")
def order_audio(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    o = owned_order(db, order_id, user)
    key = o.audio_key or (o.prayer.audio_key if o.prayer.kind == "recorded" else None)
    if not key:
        raise HTTPException(404, "Chưa có file âm thanh")
    return FileResponse(get_storage().local_path(key), media_type="audio/mpeg")


@router.get("/{order_id}/anh/{evidence_id}")
def evidence_photo(order_id: int, evidence_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    o = owned_order(db, order_id, user)
    ev = next((e for e in o.photos if e.id == evidence_id), None)
    if not ev:
        raise HTTPException(404)
    return FileResponse(get_storage().local_path(ev.path), media_type="image/jpeg")


@router.get("/{order_id}/clip")
def order_clip(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Clip xem lại (MP4). Có video thiết bị quay tại đền (hình + tiếng thật) thì dùng video đó;
    không thì dựng từ ảnh + bài khấn lần đầu khi mở xem, các lần sau dùng lại."""
    o = owned_order(db, order_id, user)
    if o.video:
        return FileResponse(get_storage().local_path(o.video.path), media_type="video/mp4")
    with _clip_lock:
        db.refresh(o)
        if not o.clip_key:
            if not clips.can_build(o):
                raise HTTPException(404, "Lễ chưa xong nên chưa có clip")
            try:
                o.clip_key = clips.build(o)
            except Exception as e:
                log.error("Không dựng được clip đơn %s: %s", o.id, e)
                raise HTTPException(500, "Chưa dựng được clip, vui lòng thử lại sau")
            db.commit()
    return FileResponse(get_storage().local_path(o.clip_key), media_type="video/mp4")


@router.get("/{order_id}/json")
def order_json(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Trạng thái đơn dạng JSON (cho app/script theo dõi)."""
    o = owned_order(db, order_id, user)
    return {"id": o.id, "status": o.status, "label": LABELS[S(o.status)], "note": o.note,
            "scheduled_at": o.scheduled_at.isoformat(),
            "events": [{"status": e.status, "ts": e.ts.isoformat(), "note": e.note} for e in o.events],
            "evidence": [{"id": e.id, "phase": e.note, "captured_at": e.captured_at.isoformat(),
                          "url": u(f"/don/{o.id}/anh/{e.id}")} for e in o.photos],
            "video": u(f"/don/{o.id}/clip") if o.video else None}
