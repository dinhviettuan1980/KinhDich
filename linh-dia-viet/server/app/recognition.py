"""Nhận diện mâm lễ từ ảnh thiết bị gửi lên: đối chiếu lễ vật của đơn (món nào có, bao nhiêu) và phiếu tên tín chủ.

Chạy trên server (Pi chỉ chụp ảnh, không nhận tên khách). Nhà cung cấp qua RECOGNITION_PROVIDER:
  claude — mô hình thị giác Claude (cần ANTHROPIC_API_KEY); nhận được cả món tự do ("bó hương", "đĩa xôi") lẫn chữ viết tay
  fake   — chỉ dùng cho test: coi như thấy đủ
  off    — tắt (mặc định nếu chưa có key)
"""
import base64
import difflib
import json
import logging
import re
import unicodedata

import httpx

from .config import get_settings
from .models import utcnow

log = logging.getLogger("linhdia.recognition")

API_URL = "https://api.anthropic.com/v1/messages"

PROMPT = """Bạn là hệ thống kiểm tra mâm lễ tại đền/chùa Việt Nam. Ảnh chụp từ camera đặt phía trên/trước mâm lễ.

Đơn đặt gồm các lễ vật sau (tên · đơn vị · số lượng đặt):
{items}

Tín chủ đặt lễ: "{name}". Trên mâm có thể có một tờ giấy/phiếu ghi tên tín chủ (in hoặc viết tay).

Nhiệm vụ:
1. Với TỪNG lễ vật trong danh sách, đếm số lượng nhìn thấy trong ảnh (theo đơn vị đã cho: bó hương, đĩa xôi, con gà...).
   Nếu không chắc, ước lượng thận trọng và ghi chú ngắn. Không thấy thì seen = 0.
2. Liệt kê các vật khác đáng chú ý trên mâm không có trong danh sách (nếu có).
3. Tìm phiếu tên: chép lại nguyên văn chữ đọc được; cho biết có khớp tên tín chủ không (bỏ qua hoa/thường, dấu bị mờ).
4. Nếu ảnh không phải mâm lễ / quá tối / bị che, nói rõ trong summary.

Chỉ trả lời bằng MỘT đối tượng JSON, không kèm chữ nào khác, đúng dạng:
{{"items": [{{"name": "<tên như trong danh sách>", "seen": <số nguyên>, "note": "<ngắn, có thể rỗng>"}}],
  "extra": ["<vật khác>"],
  "name_card": {{"found": <true|false>, "text": "<chữ đọc được hoặc rỗng>", "match": <true|false>}},
  "summary": "<1 câu tiếng Việt>"}}"""


class RecognitionError(RuntimeError):
    pass


def provider() -> str:
    s = get_settings()
    p = (s.recognition_provider or "").lower()
    if p in ("", "auto"):
        return "claude" if s.anthropic_api_key else "off"
    return p


def _words(x: str) -> list[str]:
    x = unicodedata.normalize("NFD", (x or "").lower().replace("đ", "d"))
    return re.findall(r"[a-z0-9]+", "".join(c for c in x if unicodedata.category(c) != "Mn"))


def name_matches(read: str, expected: str) -> bool:
    """So tên phía server (không tin cờ "match" của mô hình): bỏ dấu, không phân biệt hoa thường. Khớp khi phiếu chứa
    đủ các chữ của tên, hoặc gần giống (chữ viết tay đọc sai 1–2 ký tự)."""
    want, got = _words(expected), _words(read)
    if not want or not got:
        return False
    if all(w in got for w in want):
        return True
    n = len(want)

    def close(a, b):
        return a == b or difflib.SequenceMatcher(None, a, b).ratio() >= 0.75

    # so từng chữ theo thứ tự (cả tên riêng ở cuối) — "Văn An" không được nhận nhầm thành "Văn Bình"
    return any(all(close(w, g) for w, g in zip(want, got[i:i + n])) for i in range(len(got) - n + 1))


def _parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise RecognitionError("Mô hình không trả JSON")
    return json.loads(m.group(0))


def _call_claude(image: bytes, items: list[dict], name: str) -> dict:
    s = get_settings()
    if not s.anthropic_api_key:
        raise RecognitionError("Chưa cấu hình ANTHROPIC_API_KEY")
    lines = "\n".join(f"- {i['name']} · {i['unit']} · {i['qty']}" for i in items) or "- (không có)"
    body = {
        "model": s.recognition_model, "max_tokens": 1024,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                         "data": base64.b64encode(image).decode()}},
            {"type": "text", "text": PROMPT.format(items=lines, name=name)},
        ]}],
    }
    r = httpx.post(API_URL, json=body, timeout=90, headers={
        "x-api-key": s.anthropic_api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    if r.status_code != 200:
        raise RecognitionError(f"API {r.status_code}: {r.text[:200]}")
    text = "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")
    return _parse_json(text)


def _call_fake(image: bytes, items: list[dict], name: str) -> dict:
    return {"items": [{"name": i["name"], "seen": i["qty"], "note": ""} for i in items], "extra": [],
            "name_card": {"found": True, "text": name, "match": True}, "summary": "Giả lập: coi như thấy đủ."}


def analyze(image: bytes, items: list[dict], name: str, kind: str | None = None) -> dict:
    """items: [{"name","unit","qty"}]. → kết quả đã chuẩn hoá + đánh giá đạt/không đạt."""
    kind = kind or provider()
    raw = {"claude": _call_claude, "fake": _call_fake}[kind](image, items, name)
    seen = {}
    for it in raw.get("items") or []:
        if isinstance(it, dict) and it.get("name"):
            seen[str(it["name"]).strip().lower()] = it
    rows = []
    for i in items:
        r = seen.get(i["name"].strip().lower(), {})
        try:
            n = max(0, int(r.get("seen", 0)))
        except (TypeError, ValueError):
            n = 0
        rows.append({"name": i["name"], "unit": i["unit"], "expected": i["qty"], "seen": n, "ok": n >= i["qty"],
                     "note": str(r.get("note") or "")[:200]})
    card = raw.get("name_card") or {}
    text = str(card.get("text") or "")[:200]
    found = bool(card.get("found")) and bool(text.strip())
    match = found and name_matches(text, name)
    items_ok = all(r["ok"] for r in rows)
    return {"provider": kind, "model": get_settings().recognition_model if kind == "claude" else kind,
            "at": utcnow().isoformat(), "items": rows, "items_ok": items_ok,
            "extra": [str(x)[:80] for x in (raw.get("extra") or [])][:10],
            "name_card": {"found": found, "text": text, "match": match},
            "ok": items_ok and match, "summary": str(raw.get("summary") or "")[:300]}


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
        try:
            image = get_storage().local_path(ev.path).read_bytes()
            ev.analysis = analyze(image, items, o.prayer.full_name, kind)
        except Exception as e:
            log.warning("Nhận diện ảnh %s (đơn %s) lỗi: %s", ev.id, o.id, e)
            ev.analysis = {"provider": kind, "at": utcnow().isoformat(), "error": str(e)[:300]}
        db.commit()
