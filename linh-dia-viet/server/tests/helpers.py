import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.models import OfferingPackage, Temple
from conftest import P

VN = ZoneInfo("Asia/Ho_Chi_Minh")


def temple_id(db, slug="den-ngoc-son"):
    return db.scalar(select(Temple).where(Temple.slug == slug)).id


def shared_package(db):
    return db.scalar(select(OfferingPackage).where(OfferingPackage.temple_id.is_(None)).order_by(OfferingPackage.id))


def local_dt(minutes_from_now: float) -> str:
    return (datetime.now(VN) + timedelta(minutes=minutes_from_now)).strftime("%Y-%m-%dT%H:%M")


def booking_data(db, temples=("den-ngoc-son",), minutes=60 * 24, **over):
    data = {"den": [str(temple_id(db, s)) for s in temples], "goi": str(shared_package(db).id),
            "ho_ten": "Nguyễn Văn A", "nam_sinh": "1990", "dia_chi": "Cầu Giấy, Hà Nội",
            "nguyen_vong": "gia đình mạnh khỏe, bình an", "cach_khan": "tts", "khi_nao": "hen_gio",
            "thoi_gian": local_dt(minutes)}
    data.update(over)
    return data


def post_json(client, path, data=None, files=None):
    return client.post(f"{P}{path}", data=data, files=files, headers={"X-CSRF-Token": client.csrf})


TXN: dict[str, str] = {}  # booking_ref → mã giao dịch


def create_booking(client, db, **kw) -> str:
    r = post_json(client, "/dat-le", booking_data(db, **kw))
    assert r.status_code == 200, r.text
    TXN[r.json()["ref"]] = r.json()["txn"]
    assert r.json()["redirect"].endswith(f"/thanh-toan/{r.json()['txn']}")
    return r.json()["ref"]


def confirm_and_pay(client, ref, success=True) -> str:
    txn = TXN[ref]
    r = client.post(f"{P}/thanh-toan/{txn}/gia-lap", data={"csrf_token": client.csrf,
                                                         "ket_qua": "thanh_cong" if success else "that_bai"},
                    follow_redirects=False)
    assert r.status_code == 303
    return txn


def tone(path: Path, seconds: float = 3) -> Path:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=300:duration={seconds}",
                    str(path)], check=True)
    return path


def csrf_from(html: str) -> str:
    return re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)
