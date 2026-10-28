"""Nhận diện mâm lễ từ ảnh thiết bị gửi lên: đếm từng lễ vật của đơn (món nào có, bao nhiêu) trên ảnh.

Chạy phía server (Pi chỉ chụp ảnh). Chỉ gửi ảnh mâm + danh sách lễ vật — không gửi tên hay thông tin khách.
Nhà cung cấp qua RECOGNITION_PROVIDER:
  hfspace — HF Space OCR (tuandv80-ocr-numbers, endpoint /tray, Gemini vision free tier; key nằm ở Space) — mặc định
  fake    — chỉ dùng cho test: coi như thấy đủ
  off     — tắt
"""
import json
import logging
import unicodedata

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
                       data={"items": json.dumps(items, ensure_ascii=False)}, timeout=240)  # Space tự thử lại khi Gemini quá tải
    except httpx.HTTPError as e:
        raise RecognitionError(f"Không gọi được dịch vụ nhận diện: {e}") from e
    if r.status_code != 200:
        raise RecognitionError(f"Dịch vụ nhận diện lỗi {r.status_code}: {r.text[:200]}")
    return r.json()


def _call_fake(image: bytes, items: list[dict]) -> dict:
    return {"items": [{"name": i["name"], "seen": i["qty"], "note": ""} for i in items], "extra": [],
            "summary": "Giả lập: coi như thấy đủ."}


# vật cố định của ban thờ / khung ảnh — AI hay liệt kê vào "extra" nhưng không phải lễ vật thừa
FIXTURES = ("bat huong", "lu huong", "ban tho", "mam", "khay", "tuong", "anh tho", "khan", "bai vi", "chu", "nhan",
            "anh gia lap", "khung", "bat", "chan nen", "den")


def _plain(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower().replace("đ", "d"))
    return " ".join("".join(c for c in s if unicodedata.category(c) != "Mn").split())


def _is_fixture(thing: str) -> bool:
    p = _plain(thing)
    return any(p == f or p.startswith(f + " ") for f in FIXTURES)


def problems(a: dict) -> list[str]:
    """Danh sách lệch so với đơn, vd ["Thiếu 1 con Gà luộc", "Thừa 1 đĩa Xôi gấc", "Ngoài đơn: rượu"]."""
    out = []
    for r in a.get("items") or []:
        diff = r["seen"] - r["expected"]
        if diff:
            out.append(f"{'Thiếu' if diff < 0 else 'Thừa'} {abs(diff)} {r['unit']} {r['name']}".replace("  ", " "))
    if a.get("extra"):
        out.append("Ngoài đơn: " + ", ".join(a["extra"]))
    return out


def analyze(image: bytes, items: list[dict], kind: str | None = None) -> dict:
    """items: [{"name","unit","qty"}]. → kết quả chuẩn hoá + đánh giá từng món: đủ / thiếu / thừa.
    Khớp đơn khi mọi món đúng số lượng và không có lễ vật ngoài đơn (bỏ qua vật cố định của ban thờ)."""
    kind = kind or provider()
    raw = {"hfspace": _call_hfspace, "fake": _call_fake}[kind](image, items)
    seen = {_plain(str(it.get("name", ""))): it for it in raw.get("items") or [] if isinstance(it, dict)}
    rows = []
    for i in items:
        r = seen.get(_plain(i["name"]), {})
        try:
            n = max(0, int(r.get("seen", 0)))
        except (TypeError, ValueError):
            n = 0
        status = "du" if n == i["qty"] else ("thieu" if n < i["qty"] else "thua")
        rows.append({"name": i["name"], "unit": i["unit"], "expected": i["qty"], "seen": n, "ok": status == "du",
                     "status": status, "note": str(r.get("note") or "")[:200]})
    extra = [str(x)[:80] for x in (raw.get("extra") or []) if str(x).strip() and not _is_fixture(str(x))][:10]
    a = {"provider": kind, "at": utcnow().isoformat(), "items": rows, "extra": extra,
         "summary": str(raw.get("summary") or "")[:300]}
    a["problems"] = problems(a)
    a["ok"] = not a["problems"]
    return a


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
        a = ev.analysis
        if a.get("problems") and not any((e.analysis or {}).get("alerted") for e in o.evidence if e.id != ev.id):
            _alert_mismatch(db, ev)


PHASES = {"before": "trước lễ", "start": "lúc khấn", "after": "sau lễ"}


def _alert_mismatch(db, ev) -> None:
    """Mâm lễ không khớp đơn → báo ban quản lý + kiosk của đền (trang Quản lý), 1 lần mỗi đơn. Không có thông tin khách."""
    from .alerts import tray_mismatch
    o = ev.order
    text = (f"⚠️ Mâm lễ chưa khớp đơn #{o.id} tại {o.temple.name if o.temple else '?'} "
            f"(ảnh {PHASES.get(ev.note or '', ev.note or '')}): " + "; ".join(ev.analysis["problems"]))
    ev.analysis = {**ev.analysis, "alerted": True}
    tray_mismatch(db, o, text)
    db.commit()
