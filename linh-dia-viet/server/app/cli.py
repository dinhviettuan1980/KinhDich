"""Lệnh quản trị: python -m app.cli add-device <id> [tên] | rotate-token <id> | revoke <id>"""
import argparse

from . import db as dbmod
from .device_admin import create_device, revoke, rotate_token
from .models import ROLES, Device
from .web import audit


def create_user(args) -> None:
    import secrets
    from sqlalchemy import select
    from .models import Temple, TempleStaff, User
    from .security import hash_password
    pw = args.password or secrets.token_urlsafe(9)
    with dbmod.SessionLocal() as db:
        u = db.scalar(select(User).where(User.email == args.email.lower())) or User(email=args.email.lower())
        u.name = args.name or u.name or args.email.split("@")[0]
        u.role, u.active, u.password_hash = args.role, True, hash_password(pw)
        db.add(u)
        db.flush()
        for slug in args.temple:
            t = db.scalar(select(Temple).where(Temple.slug == slug))
            if not t:
                raise SystemExit(f"Không có đền {slug}")
            if t.id not in u.temple_ids:
                u.staff_of.append(TempleStaff(temple_id=t.id))
        audit(db, "cli", "user.create", f"user:{u.id}", role=args.role)
        db.commit()
    print(f"{args.email.lower()} / {pw}  ({ROLES[args.role]})")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="app.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add-device")
    a.add_argument("device_id")
    a.add_argument("name", nargs="?", default="")
    for name in ("rotate-token", "revoke"):
        sub.add_parser(name).add_argument("device_id")
    cu = sub.add_parser("create-user", help="tạo/cập nhật tài khoản (in mật khẩu nếu tự sinh)")
    cu.add_argument("email")
    cu.add_argument("--name", default="")
    cu.add_argument("--role", default="customer", choices=list(ROLES))
    cu.add_argument("--temple", action="append", default=[], help="slug đền phụ trách (vendor/temple_manager)")
    cu.add_argument("--password", default="")
    args = ap.parse_args(argv)
    dbmod.init_engine()
    if args.cmd == "create-user":
        return create_user(args)
    with dbmod.SessionLocal() as db:
        if args.cmd == "add-device":
            token = create_device(db, args.device_id, args.name)
        else:
            dev = db.get(Device, args.device_id)
            if not dev:
                raise SystemExit("Không có thiết bị này")
            token = rotate_token(db, dev) if args.cmd == "rotate-token" else revoke(db, dev)
        audit(db, "cli", f"device.{args.cmd}", f"device:{args.device_id}")
        db.commit()
    if token:
        print(f"LD_DEVICE_ID={args.device_id.lower()}\nLD_DEVICE_TOKEN={token}")
        print("# Token chỉ hiện một lần. Chép 2 dòng trên vào /etc/linh-dia-viet/agent.env trên Pi.")
    else:
        print("Đã thu hồi.")


if __name__ == "__main__":
    main()
