"""Trang đơn của khách: lịch sử, theo dõi (dòng thời gian cập nhật bằng polling HTMX), hủy, nghe lại."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import orders as svc
from ..db import get_db
from ..models import Order, User
from ..security import check_csrf
from ..state_machine import LABELS, MAIN_LINE, TERMINAL, OrderStatus as S
from ..storage import get_storage
from ..web import flash, render, require_user, u

router = APIRouter(prefix="/don")


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
            "evidence": o.evidence}


@router.get("")
def history(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    orders = db.scalars(select(Order).where(Order.user_id == user.id).order_by(Order.id.desc()).limit(200)).all()
    return render(request, "orders/list.html", {"orders": orders, "labels": LABELS})


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
    ev = next((e for e in o.evidence if e.id == evidence_id), None)
    if not ev:
        raise HTTPException(404)
    return FileResponse(get_storage().local_path(ev.path), media_type="image/jpeg")
