"""API HTTP cho thiết bị: tải audio qua URL có chữ ký, upload ảnh bằng chứng bằng token thiết bị."""
import io
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy.orm import Session

from .. import devices
from ..db import get_db
from ..models import Device, DeviceJob
from ..security import token_matches
from ..storage import check_key, get_storage, verify_signature
from ..web import audit

router = APIRouter()
MAX_PHOTO_BYTES = 5 * 1024 * 1024


@router.get("/files/{key:path}")
def signed_file(key: str, exp: int, sig: str):
    try:
        check_key(key)
    except ValueError:
        raise HTTPException(404)
    if not verify_signature(key, exp, sig):
        raise HTTPException(403, "Link hết hạn hoặc sai chữ ký")
    path = get_storage().local_path(key)
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="audio/mpeg" if key.endswith(".mp3") else "application/octet-stream")


def device_auth(authorization: str = Header(""), x_device_id: str = Header(""),
                db: Session = Depends(get_db)) -> Device:
    token = authorization.removeprefix("Bearer ").strip()
    dev = db.get(Device, x_device_id) if x_device_id else None
    if not dev or dev.revoked or not token or not token_matches(token, dev.token_hash):
        raise HTTPException(401, "Thiết bị không hợp lệ")
    return dev


def read_jpeg(data: bytes) -> bytes:
    """Chỉ nhận JPEG thật (kiểm tra chữ ký + giải mã), không tin đuôi file."""
    if len(data) > MAX_PHOTO_BYTES:
        raise HTTPException(413, "Ảnh quá lớn")
    if not data.startswith(b"\xff\xd8\xff"):
        raise HTTPException(415, "Chỉ nhận ảnh JPEG")
    try:
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
            if im.format != "JPEG":
                raise ValueError
    except Exception:
        raise HTTPException(415, "Ảnh JPEG hỏng")
    return data


def _parse_ts(s: str) -> datetime:
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


@router.post("/api/device/evidence")
async def upload_evidence(job_id: str = Form(""), phase: str = Form(...), captured_at: str = Form(""),
                          file: UploadFile = File(...), dev: Device = Depends(device_auth),
                          db: Session = Depends(get_db)):
    data = read_jpeg(await file.read(MAX_PHOTO_BYTES + 1))
    storage = get_storage()
    if phase == "test":  # ảnh "chụp thử" từ trang admin
        key = storage.put_bytes(data, f"devices/{dev.id}/test-{uuid.uuid4().hex[:8]}.jpg")
        if dev.test_photo_key:
            storage.delete(dev.test_photo_key)
        dev.test_photo_key = key
        audit(db, f"device:{dev.id}", "device.test_photo", f"device:{dev.id}")
        db.commit()
        return {"ok": True}
    if phase not in ("before", "start", "after"):
        raise HTTPException(400, "phase không hợp lệ")
    job = db.get(DeviceJob, job_id)
    if not job or job.device_id != dev.id:
        raise HTTPException(404, "Job không thuộc thiết bị này")
    if any(e.job_id == job.id and e.note == phase for e in job.order.evidence):
        return {"ok": True, "duplicate": True}  # thiết bị gửi lại sau khi mất mạng
    key = storage.put_bytes(data, f"evidence/{job.order_id}/{phase}-{uuid.uuid4().hex[:10]}.jpg")
    devices.add_evidence(db, job, key, _parse_ts(captured_at), phase)
    db.commit()
    return {"ok": True}
