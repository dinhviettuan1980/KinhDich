"""Khu quản trị (back-office) cho 3 nhóm: admin hệ thống, người quản lý đền, người bán hàng kiosk.

- admin: toàn quyền.
- temple_manager: sửa thông tin đền mình phụ trách + gói lễ của đền đó.
- vendor: sửa gói lễ (mâm lễ bán tại kiosk) của đền mình phụ trách.
"""
import re
import unicodedata

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ROLES, Device, OfferingPackage, Temple, TempleStaff, User
from ..security import check_csrf, hash_password
from ..web import audit, can_manage_temple, flash, render, require_admin, require_backoffice, u

router = APIRouter(prefix="/admin")
csrf = [Depends(check_csrf)]


def slugify(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "den"


def _visible_temples(db: Session, user: User) -> list[Temple]:
    stmt = select(Temple).order_by(Temple.name)
    if not user.is_admin:
        stmt = stmt.where(Temple.id.in_(user.temple_ids or {-1}))
    return list(db.scalars(stmt))


@router.get("")
def dashboard(request: Request, db: Session = Depends(get_db), user: User = Depends(require_backoffice)):
    from ..devices import system_locked
    from ..models import Prayer
    pending = db.query(Prayer).filter(Prayer.kind == "recorded", Prayer.moderation == "pending").count() \
        if user.is_admin else 0
    return render(request, "admin/index.html", {"my_temples": _visible_temples(db, user), "roles": ROLES,
                                                "locked": system_locked(db), "pending": pending})


# ---------------- Đền ----------------

@router.get("/den")
def temples(request: Request, db: Session = Depends(get_db), user: User = Depends(require_backoffice)):
    if user.role == "vendor":
        raise HTTPException(403)
    return render(request, "admin/temples.html", {"temples": _visible_temples(db, user)})


@router.get("/den/{temple_id}")
def temple_form(temple_id: str, request: Request, db: Session = Depends(get_db),
                user: User = Depends(require_backoffice)):
    if temple_id == "moi":
        if not user.is_admin:
            raise HTTPException(403)
        temple = Temple(status="active")
    else:
        temple = db.get(Temple, int(temple_id))
        if temple is None:
            raise HTTPException(404)
        if not can_manage_temple(user, temple.id, roles=("temple_manager",)):
            raise HTTPException(403)
    return render(request, "admin/temple_form.html", {
        "t": temple, "devices": db.scalars(select(Device).order_by(Device.id)).all()})


@router.post("/den/{temple_id}", dependencies=csrf)
def temple_save(temple_id: str, request: Request, name: str = Form(...), address: str = Form(""),
                province: str = Form(""), description: str = Form(""), deity: str = Form(""),
                status: str = Form("active"), device_id: str = Form(""), slug: str = Form(""),
                db: Session = Depends(get_db), user: User = Depends(require_backoffice)):
    if temple_id == "moi":
        if not user.is_admin:
            raise HTTPException(403)
        temple = Temple()
        db.add(temple)
    else:
        temple = db.get(Temple, int(temple_id))
        if temple is None:
            raise HTTPException(404)
        if not can_manage_temple(user, temple.id, roles=("temple_manager",)):
            raise HTTPException(403)
    temple.name, temple.address, temple.province = name.strip(), address.strip(), province.strip()
    temple.description, temple.deity = description.strip(), deity.strip()
    if user.is_admin:  # chỉ admin đổi thiết bị, trạng thái hiển thị, đường dẫn
        if device_id and not db.get(Device, device_id):
            raise HTTPException(400, "Thiết bị không tồn tại")
        temple.status = status if status in ("active", "hidden") else "hidden"
        temple.device_id = device_id or None
        temple.slug = slugify(slug or name)
    db.flush()
    audit(db, f"user:{user.id}", "temple.save", f"temple:{temple.id}", name=temple.name, device_id=temple.device_id)
    db.commit()
    flash(request, "Đã lưu đền.", "ok")
    return RedirectResponse(u("/admin/den" if user.is_admin else "/admin"), 303)


# ---------------- Lễ vật (bán lẻ từng món) ----------------

@router.get("/goi-le")
def packages(request: Request, db: Session = Depends(get_db), user: User = Depends(require_backoffice)):
    stmt = select(OfferingPackage).order_by(OfferingPackage.active.desc(), OfferingPackage.sort, OfferingPackage.price)
    if not user.is_admin:
        stmt = stmt.where(OfferingPackage.temple_id.in_(user.temple_ids or {-1}))
    return render(request, "admin/packages.html", {"packages": db.scalars(stmt).all()})


def _load_pkg(db: Session, pkg_id: str, user: User) -> OfferingPackage:
    if pkg_id == "moi":
        return OfferingPackage(active=True, price=0, unit="phần", max_qty=10, sort=0)
    pkg = db.get(OfferingPackage, int(pkg_id))
    if pkg is None:
        raise HTTPException(404)
    if not can_manage_temple(user, pkg.temple_id):
        raise HTTPException(403)
    return pkg


@router.get("/goi-le/{pkg_id}")
def package_form(pkg_id: str, request: Request, db: Session = Depends(get_db),
                 user: User = Depends(require_backoffice)):
    return render(request, "admin/package_form.html",
                  {"p": _load_pkg(db, pkg_id, user), "temples": _visible_temples(db, user)})


@router.post("/goi-le/{pkg_id}", dependencies=csrf)
def package_save(pkg_id: str, request: Request, name: str = Form(...), description: str = Form(""),
                 price: int = Form(...), unit: str = Form("phần"), max_qty: int = Form(10), sort: int = Form(0),
                 image_url: str = Form(""), temple_id: str = Form(""),
                 active: bool = Form(False), db: Session = Depends(get_db),
                 user: User = Depends(require_backoffice)):
    if price < 0 or not 1 <= max_qty <= 99:
        raise HTTPException(400, "Giá hoặc số lượng tối đa không hợp lệ")
    pkg = _load_pkg(db, pkg_id, user)
    new_temple_id = int(temple_id) if temple_id else None
    if not can_manage_temple(user, new_temple_id):  # nhân sự đền không tạo gói "dùng chung"
        raise HTTPException(403)
    if pkg.id is None:
        db.add(pkg)
    pkg.name, pkg.description, pkg.price = name.strip(), description.strip(), price
    pkg.image_url, pkg.active, pkg.temple_id = image_url.strip(), active, new_temple_id
    pkg.unit, pkg.max_qty, pkg.sort = unit.strip()[:30] or "phần", max_qty, sort
    db.flush()
    audit(db, f"user:{user.id}", "package.save", f"package:{pkg.id}", name=pkg.name, price=price)
    db.commit()
    flash(request, "Đã lưu lễ vật.", "ok")
    return RedirectResponse(u("/admin/goi-le"), 303)


# ---------------- Người dùng (chỉ admin) ----------------

@router.get("/nguoi-dung")
def users(request: Request, q: str = "", role: str = "", db: Session = Depends(get_db),
          admin: User = Depends(require_admin)):
    stmt = select(User).order_by(User.id.desc()).limit(200)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.name.ilike(like), User.email.ilike(like), User.phone.ilike(like)))
    if role in ROLES:
        stmt = stmt.where(User.role == role)
    return render(request, "admin/users.html", {"users": db.scalars(stmt).all(), "roles": ROLES, "q": q, "role": role})


@router.get("/nguoi-dung/{user_id}")
def user_form(user_id: str, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    target = User(role="customer", active=True) if user_id == "moi" else db.get(User, int(user_id))
    if target is None:
        raise HTTPException(404)
    return render(request, "admin/user_form.html", {
        "t": target, "roles": ROLES, "temples": db.scalars(select(Temple).order_by(Temple.name)).all(),
        "assigned": target.temple_ids if target.id else set()})


@router.post("/nguoi-dung/{user_id}", dependencies=csrf)
async def user_save(user_id: str, request: Request, db: Session = Depends(get_db),
                    admin: User = Depends(require_admin)):
    form = await request.form()
    role = form.get("role", "customer")
    if role not in ROLES:
        raise HTTPException(400, "Vai trò không hợp lệ")
    if user_id == "moi":
        from .auth import normalize_identifier
        ident = normalize_identifier(form.get("identifier", ""))
        password = form.get("password", "")
        if not ident or len(password) < 8:
            raise HTTPException(400, "Cần email/số điện thoại hợp lệ và mật khẩu ≥ 8 ký tự")
        if db.scalar(select(User).where(or_(User.email == ident[1], User.phone == ident[1]))):
            raise HTTPException(409, "Tài khoản đã tồn tại")
        target = User(password_hash=hash_password(password), **{ident[0]: ident[1]})
        db.add(target)
    else:
        target = db.get(User, int(user_id))
        if target is None:
            raise HTTPException(404)
    if target.id == admin.id and (role != "admin" or not form.get("active")):
        raise HTTPException(400, "Không thể tự hạ quyền hoặc khóa chính mình")
    target.name = (form.get("name") or target.name or "").strip()[:120] or "Người dùng"
    target.role = role
    target.active = bool(form.get("active"))
    temple_ids = {int(x) for x in form.getlist("temple_ids") if str(x).isdigit()} if role in ("vendor", "temple_manager") else set()
    target.staff_of = [s for s in target.staff_of if s.temple_id in temple_ids]  # giữ dòng cũ, tránh trùng khoá
    for tid in sorted(temple_ids - target.temple_ids):
        if db.get(Temple, tid):
            target.staff_of.append(TempleStaff(temple_id=tid))
    db.flush()
    audit(db, f"user:{admin.id}", "user.save", f"user:{target.id}", role=role, active=target.active,
          temples=sorted(temple_ids))
    db.commit()
    flash(request, "Đã lưu người dùng.", "ok")
    return RedirectResponse(u("/admin/nguoi-dung"), 303)


# ---------------- Lịch lễ của đền (admin / quản lý đền / kiosk) ----------------
# Nhân sự đền KHÔNG thấy dữ liệu cá nhân (họ tên, địa chỉ, năm sinh, nguyện vọng) — chỉ admin thấy.

@router.get("/lich-le")
def schedule(request: Request, status: str = "", db: Session = Depends(get_db),
             user: User = Depends(require_backoffice)):
    from ..models import Order
    from ..state_machine import LABELS
    stmt = select(Order).order_by(Order.scheduled_at.desc()).limit(300)
    if not user.is_admin:
        stmt = stmt.where(Order.temple_id.in_(user.temple_ids or {-1}),
                          Order.status.notin_(["created", "awaiting_payment"]))
    if status:
        stmt = stmt.where(Order.status == status)
    return render(request, "admin/schedule.html", {"orders": db.scalars(stmt).all(), "labels": LABELS,
                                                   "status": status})


def _staff_order(db: Session, order_id: int, user: User, roles):
    from ..models import Order
    o = db.get(Order, order_id)
    if o is None:
        raise HTTPException(404)
    if not can_manage_temple(user, o.temple_id, roles=roles):
        raise HTTPException(403)
    return o


@router.post("/don/{order_id}/mam-le", dependencies=csrf)
def tray_ready(order_id: int, request: Request, db: Session = Depends(get_db),
               user: User = Depends(require_backoffice)):
    from ..models import utcnow
    o = _staff_order(db, order_id, user, ("vendor", "temple_manager"))
    if o.status not in ("paid", "scheduled", "delivered"):
        raise HTTPException(409, "Đơn không ở trạng thái chuẩn bị lễ")
    o.tray_ready_at = utcnow()
    audit(db, f"user:{user.id}", "order.tray_ready", f"order:{o.id}")
    db.commit()
    flash(request, f"Đã báo mâm lễ đơn #{o.id} sẵn sàng.", "ok")
    return RedirectResponse(u("/admin/lich-le"), 303)


@router.post("/don/{order_id}/tu-choi", dependencies=csrf)
async def reject_order(order_id: int, request: Request, db: Session = Depends(get_db),
                       user: User = Depends(require_backoffice)):
    from .. import orders as svc
    from ..state_machine import InvalidTransition
    o = _staff_order(db, order_id, user, ("temple_manager",))
    reason = str((await request.form()).get("ly_do", "")).strip()[:500]
    if not reason:
        raise HTTPException(400, "Cần nêu lý do từ chối")
    try:
        svc.reject(db, o, f"user:{user.id}", reason)
    except InvalidTransition as e:
        raise HTTPException(409, str(e))
    db.commit()
    flash(request, f"Đã từ chối đơn #{o.id}.", "ok")
    return RedirectResponse(u("/admin/lich-le"), 303)


@router.post("/don/{order_id}/hoan-tien", dependencies=csrf)
def refund_order(order_id: int, request: Request, db: Session = Depends(get_db),
                 admin: User = Depends(require_admin)):
    from .. import orders as svc
    from ..models import Order
    from ..state_machine import InvalidTransition
    o = db.get(Order, order_id)
    if o is None:
        raise HTTPException(404)
    try:
        svc.mark_refunded(db, o, f"user:{admin.id}")
    except InvalidTransition as e:
        raise HTTPException(409, str(e))
    db.commit()
    flash(request, f"Đã đánh dấu hoàn tiền đơn #{o.id}.", "ok")
    return RedirectResponse(u("/admin/lich-le"), 303)


# ---------------- Mẫu sớ (admin: mọi mẫu; quản lý đền: mẫu riêng của đền mình) ----------------

@router.get("/mau-so")
def prayer_templates(request: Request, db: Session = Depends(get_db), user: User = Depends(require_backoffice)):
    from ..models import PrayerTemplate
    if user.role == "vendor":
        raise HTTPException(403)
    tpls = {t.temple_id: t for t in db.scalars(select(PrayerTemplate))}
    return render(request, "admin/prayer_templates.html",
                  {"shared": tpls.get(None), "temples": _visible_temples(db, user), "tpls": tpls})


def _tpl_scope(db: Session, scope: str, user: User):
    """scope = 'chung' (mẫu chung, chỉ admin) hoặc id đền."""
    from ..models import PrayerTemplate
    if scope == "chung":
        if not user.is_admin:
            raise HTTPException(403)
        temple_id = None
    else:
        temple_id = int(scope)
        if not db.get(Temple, temple_id):
            raise HTTPException(404)
        if not can_manage_temple(user, temple_id, roles=("temple_manager",)):
            raise HTTPException(403)
    cond = PrayerTemplate.temple_id.is_(None) if temple_id is None else PrayerTemplate.temple_id == temple_id
    return temple_id, db.scalar(select(PrayerTemplate).where(cond))


@router.get("/mau-so/{scope}")
def prayer_template_form(scope: str, request: Request, db: Session = Depends(get_db),
                         user: User = Depends(require_backoffice)):
    from ..prayer_text import DEFAULT_TEMPLATE, VARIABLES
    temple_id, tpl = _tpl_scope(db, scope, user)
    return render(request, "admin/prayer_template_form.html", {
        "scope": scope, "temple": db.get(Temple, temple_id) if temple_id else None, "tpl": tpl,
        "body": tpl.body if tpl else DEFAULT_TEMPLATE, "variables": VARIABLES})


@router.post("/mau-so/{scope}", dependencies=csrf)
async def prayer_template_save(scope: str, request: Request, db: Session = Depends(get_db),
                               user: User = Depends(require_backoffice)):
    from ..models import PrayerTemplate
    from ..prayer_text import unknown_variables
    temple_id, tpl = _tpl_scope(db, scope, user)
    form = await request.form()
    body = str(form.get("body", "")).replace("\r\n", "\n").strip()
    if form.get("xoa") and tpl and temple_id is not None:
        db.delete(tpl)
        audit(db, f"user:{user.id}", "prayer_template.delete", f"temple:{temple_id}")
        db.commit()
        flash(request, "Đã xóa mẫu riêng, đền sẽ dùng mẫu chung.", "ok")
        return RedirectResponse(u("/admin/mau-so"), 303)
    if not body or len(body) > 5000:
        raise HTTPException(400, "Mẫu sớ trống hoặc quá dài")
    bad = unknown_variables(body)
    if bad:
        raise HTTPException(400, "Biến không hợp lệ: " + ", ".join(sorted(bad)))
    if tpl is None:
        tpl = PrayerTemplate(temple_id=temple_id, name="Mẫu chung" if temple_id is None else "Mẫu riêng", body=body)
        db.add(tpl)
    tpl.body = body
    db.flush()
    audit(db, f"user:{user.id}", "prayer_template.save", f"template:{tpl.id}", temple_id=temple_id)
    db.commit()
    flash(request, "Đã lưu mẫu sớ.", "ok")
    return RedirectResponse(u("/admin/mau-so"), 303)


# ---------------- Thiết bị (chỉ admin) ----------------

@router.get("/thiet-bi")
def device_list(request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from ..models import DeviceJob
    from .public import device_online
    devs = db.scalars(select(Device).order_by(Device.id)).all()
    temples = {t.device_id: t for t in db.scalars(select(Temple).where(Temple.device_id.is_not(None)))}
    jobs = {d.id: db.scalars(select(DeviceJob).where(DeviceJob.device_id == d.id)
                             .order_by(DeviceJob.created_at.desc()).limit(5)).all() for d in devs}
    return render(request, "admin/devices.html", {
        "devices": devs, "temples": temples, "jobs": jobs, "online": {d.id: device_online(d) for d in devs},
        "new_token": request.session.pop("new_device_token", None)})


@router.post("/thiet-bi/moi", dependencies=csrf)
async def device_create(request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from ..device_admin import create_device
    form = await request.form()
    try:
        token = create_device(db, str(form.get("device_id", "")), str(form.get("name", "")))
    except ValueError as e:
        raise HTTPException(400, str(e))
    device_id = str(form.get("device_id")).strip().lower()
    audit(db, f"user:{admin.id}", "device.create", f"device:{device_id}")
    db.commit()
    request.session["new_device_token"] = [device_id, token]  # hiện đúng 1 lần
    return RedirectResponse(u("/admin/thiet-bi"), 303)


@router.post("/thiet-bi/{device_id}/token", dependencies=csrf)
async def device_token(device_id: str, request: Request, db: Session = Depends(get_db),
                       admin: User = Depends(require_admin)):
    from ..device_admin import revoke, rotate_token
    dev = db.get(Device, device_id)
    if dev is None:
        raise HTTPException(404)
    action = (await request.form()).get("action")
    if action == "revoke":
        revoke(db, dev)
        flash(request, f"Đã thu hồi token của {dev.id}.", "ok")
    elif action == "rotate":
        request.session["new_device_token"] = [dev.id, rotate_token(db, dev)]
    else:
        raise HTTPException(400)
    audit(db, f"user:{admin.id}", f"device.token_{action}", f"device:{dev.id}")
    db.commit()
    return RedirectResponse(u("/admin/thiet-bi"), 303)


@router.post("/thiet-bi/{device_id}/lenh", dependencies=csrf)
async def device_command(device_id: str, request: Request, db: Session = Depends(get_db),
                         admin: User = Depends(require_admin)):
    from .. import devices
    dev = db.get(Device, device_id)
    if dev is None:
        raise HTTPException(404)
    kind = (await request.form()).get("type")
    if kind not in ("test_tone", "capture", "stop"):
        raise HTTPException(400)
    try:
        devices.send_command(db, dev.id, {"type": kind}, f"user:{admin.id}")
        flash(request, {"test_tone": "Đã gửi lệnh phát âm thử.", "capture": "Đã gửi lệnh chụp thử, ảnh sẽ hiện sau vài giây.",
                        "stop": "Đã gửi lệnh dừng ngay."}[kind], "ok")
    except devices.CommandBlocked as e:
        flash(request, str(e), "error")
    db.commit()
    return RedirectResponse(u("/admin/thiet-bi"), 303)


@router.get("/thiet-bi/{device_id}/anh-thu")
def device_test_photo(device_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from fastapi.responses import FileResponse
    from ..storage import get_storage
    dev = db.get(Device, device_id)
    if not dev or not dev.test_photo_key:
        raise HTTPException(404)
    return FileResponse(get_storage().local_path(dev.test_photo_key), media_type="image/jpeg",
                        headers={"Cache-Control": "no-store"})


# ---------------- Kiểm duyệt ghi âm (admin) ----------------

@router.get("/kiem-duyet")
def moderation_queue(request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from ..models import Prayer
    pending = db.scalars(select(Prayer).where(Prayer.kind == "recorded", Prayer.moderation == "pending")
                         .order_by(Prayer.created_at)).all()
    return render(request, "admin/moderation.html", {"prayers": pending})


@router.get("/kiem-duyet/{prayer_id}/audio")
def moderation_audio(prayer_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from fastapi.responses import FileResponse
    from ..models import Prayer
    from ..storage import get_storage
    p = db.get(Prayer, prayer_id)
    if not p or not p.audio_key:
        raise HTTPException(404)
    return FileResponse(get_storage().local_path(p.audio_key), media_type="audio/mpeg")


@router.post("/kiem-duyet/{prayer_id}", dependencies=csrf)
async def moderation_decide(prayer_id: int, request: Request, db: Session = Depends(get_db),
                            admin: User = Depends(require_admin)):
    from .. import orders as svc
    from ..models import Prayer
    p = db.get(Prayer, prayer_id)
    if not p or p.kind != "recorded" or p.moderation != "pending":
        raise HTTPException(404)
    form = await request.form()
    approve = form.get("quyet_dinh") == "duyet"
    note = str(form.get("ly_do", "")).strip()[:500]
    if not approve and not note:
        raise HTTPException(400, "Cần nêu lý do từ chối")
    svc.moderate(db, p, approve, f"user:{admin.id}", note)
    db.commit()
    flash(request, "Đã duyệt bản ghi." if approve else "Đã từ chối bản ghi.", "ok")
    return RedirectResponse(u("/admin/kiem-duyet"), 303)


# ---------------- Khóa khẩn cấp (admin) ----------------

@router.post("/khoa-khan-cap", dependencies=csrf)
async def emergency_lock(request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from .. import devices
    lock = (await request.form()).get("khoa") == "1"
    n = devices.set_system_lock(db, lock, f"user:{admin.id}")
    db.commit()
    flash(request, f"ĐÃ KHÓA KHẨN CẤP: gửi lệnh dừng tới {n} thiết bị, chặn mọi lệnh mới." if lock
          else "Đã mở khóa hệ thống.", "error" if lock else "ok")
    return RedirectResponse(u("/admin"), 303)


# ---------------- Đơn hàng & log job (admin) ----------------

@router.get("/don/{order_id}")
def order_admin_detail(order_id: int, request: Request, db: Session = Depends(get_db),
                       admin: User = Depends(require_admin)):
    from ..models import AuditLog, Order
    from ..state_machine import LABELS
    o = db.get(Order, order_id)
    if o is None:
        raise HTTPException(404)
    logs = db.scalars(select(AuditLog).where(AuditLog.target == f"order:{o.id}").order_by(AuditLog.id)).all()
    return render(request, "admin/order_detail.html", {"o": o, "labels": LABELS, "logs": logs})


@router.post("/don/{order_id}/gui-lai", dependencies=csrf)
def order_resend(order_id: int, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from .. import devices
    from ..models import Order
    o = db.get(Order, order_id)
    if o is None:
        raise HTTPException(404)
    if devices.system_locked(db):
        raise HTTPException(409, "Hệ thống đang khóa khẩn cấp")
    try:
        devices.resend(db, o, f"user:{admin.id}")
    except ValueError as e:
        raise HTTPException(409, str(e))
    db.commit()
    flash(request, f"Đã gửi lại job cho đơn #{o.id}.", "ok")
    return RedirectResponse(u(f"/admin/don/{o.id}"), 303)
