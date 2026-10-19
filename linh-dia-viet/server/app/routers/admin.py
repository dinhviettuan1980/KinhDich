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
    return render(request, "admin/index.html", {"my_temples": _visible_temples(db, user), "roles": ROLES})


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


# ---------------- Gói lễ ----------------

@router.get("/goi-le")
def packages(request: Request, db: Session = Depends(get_db), user: User = Depends(require_backoffice)):
    stmt = select(OfferingPackage).order_by(OfferingPackage.price)
    if not user.is_admin:
        stmt = stmt.where(OfferingPackage.temple_id.in_(user.temple_ids or {-1}))
    return render(request, "admin/packages.html", {"packages": db.scalars(stmt).all()})


def _load_pkg(db: Session, pkg_id: str, user: User) -> OfferingPackage:
    if pkg_id == "moi":
        return OfferingPackage(active=True, price=0)
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
                 price: int = Form(...), image_url: str = Form(""), temple_id: str = Form(""),
                 active: bool = Form(False), db: Session = Depends(get_db),
                 user: User = Depends(require_backoffice)):
    if price < 0:
        raise HTTPException(400, "Giá không hợp lệ")
    pkg = _load_pkg(db, pkg_id, user)
    new_temple_id = int(temple_id) if temple_id else None
    if not can_manage_temple(user, new_temple_id):  # nhân sự đền không tạo gói "dùng chung"
        raise HTTPException(403)
    if pkg.id is None:
        db.add(pkg)
    pkg.name, pkg.description, pkg.price = name.strip(), description.strip(), price
    pkg.image_url, pkg.active, pkg.temple_id = image_url.strip(), active, new_temple_id
    db.flush()
    audit(db, f"user:{user.id}", "package.save", f"package:{pkg.id}", name=pkg.name, price=price)
    db.commit()
    flash(request, "Đã lưu gói lễ.", "ok")
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
