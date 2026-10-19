"""Lệnh quản trị: python -m app.cli add-device <id> [tên] | rotate-token <id> | revoke <id>"""
import argparse

from . import db as dbmod
from .device_admin import create_device, revoke, rotate_token
from .models import Device
from .web import audit


def main(argv=None):
    ap = argparse.ArgumentParser(prog="app.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add-device")
    a.add_argument("device_id")
    a.add_argument("name", nargs="?", default="")
    for name in ("rotate-token", "revoke"):
        sub.add_parser(name).add_argument("device_id")
    args = ap.parse_args(argv)
    dbmod.init_engine()
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
