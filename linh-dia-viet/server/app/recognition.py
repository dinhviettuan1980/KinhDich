"""Nhận diện mâm lễ từ ảnh thiết bị gửi lên: đếm từng lễ vật của đơn (món nào có, bao nhiêu) trên ảnh.

Chạy phía server (Pi chỉ chụp ảnh). Chỉ gửi ảnh mâm + danh sách lễ vật — không gửi tên hay thông tin khách.
Nhà cung cấp qua RECOGNITION_PROVIDER:
  hfspace — HF Space OCR (tuandv80-ocr-numbers, endpoint /tray, Gemini vision free tier; key nằm ở Space) — mặc định
  fake    — chỉ dùng cho test: coi như thấy đủ
  off     — tắt
"""
import json
import logging

import httpx

from .config import get_settings
from .models import utcnow

log = logging.getLogger("linhdia.recognition")


class RecognitionError(RuntimeError):
    pass


def provider() -> str:
    p = (get_settings().recognition_provider or "").lower()
    return "hfspace" if p in ("", "auto") else p


def _call_hfspace(image: bytes, items: list[dict]) -> dict:
    url = get_settings().recognition_url.rstrip("/") + "/tray"
    try:
        r = httpx.post(url, files={"file": ("tray.jpg", image, "image/jpeg")},
                       data={"items": json.dumps(items, ensure_ascii=False)}, timeout=120)
    except httpx.HTTPError as e:
        raise RecognitionError(f"Không gọi được dịch vụ nhận diện: {e}") from e
    if r.status_code != 200:
        raise RecognitionError(f"Dịch vụ nhận diện lỗi {r.status_code}: {r.text[:200]}")
    return r.json()


def _call_fake(image: bytes, items: list[dict]) -> dict:
    return {"items": [{"name": i["name"], "seen": i["qty"], "note": ""} for i in items], "extra": [],
            "summary": "Giả lập: coi như thấy đủ."}


def analyze(image: bytes, items: list[dict], kind: str | None = None) -> dict:
    """items: [{"name","unit","qty"}]. → kết quả chuẩn hoá + đánh giá đạt/không đạt từng món."""
    kind = kind or provider()
    raw = {"hfspace": _call_hfspace, "fake": _call_fake}[kind](image, items)
    seen = {str(it.get("name", "")).strip().lower(): it for it in raw.get("items") or [] if isinstance(it, dict)}
    rows = []
    for i in items:
        r = seen.get(i["name"].strip().lower(), {})
        try:
            n = max(0, int(r.get("seen", 0)))
        except (TypeError, ValueError):
            n = 0
        rows.append({"name": i["name"], "unit": i["unit"], "expected": i["qty"], "seen": n, "ok": n >= i["qty"],
                     "note": str(r.get("note") or "")[:200]})
    return {"provider": kind, "at": utcnow().isoformat(), "items": rows, "ok": all(r["ok"] for r in rows),
            "extra": [str(x)[:80] for x in (raw.get("extra") or [])][:10], "summary": str(raw.get("summary") or "")[:300]}


def analyze_evidence(evidence_id: int) -> None:
    """Tác vụ nền sau khi thiết bị gửi ảnh mâm lễ. Lỗi thì ghi vào kết quả, không làm hỏng luồng đơn."""
    from . import db as dbmod
    from .models import Evidence
    from .storage import get_storage
    kind = provider()
    if kind == "off":
        return
    with dbmod.SessionLocal() as db:
        ev = db.get(Evidence, evidence_id)
        if not ev or ev.kind != "photo":
            return
        o = ev.order
        items = [{"name": i.name, "unit": i.unit, "qty": i.qty} for i in o.items]
        if not items:
            return
        try:
            ev.analysis = analyze(get_storage().local_path(ev.path).read_bytes(), items, kind)
        except Exception as e:
            log.warning("Nhận diện ảnh %s (đơn %s) lỗi: %s", ev.id, o.id, e)
            ev.analysis = {"provider": kind, "at": utcnow().isoformat(), "error": str(e)[:300]}
        db.commit()
