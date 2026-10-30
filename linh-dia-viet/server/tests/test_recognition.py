"""Nhận diện mâm lễ: đếm lễ vật trên ảnh thiết bị gửi lên, qua HF Space OCR (/tray). Không gửi thông tin khách."""
import json

import httpx
import pytest
from sqlalchemy import select

from app import recognition
from app.config import get_settings
from app import alerts
from app.models import AuditLog, Order, Temple, TempleStaff, User
from conftest import P, login
from test_m3_devices import move_play_time, run, setup  # noqa: F401  (fixture)

ITEMS = [{"name": "Hương (nhang)", "unit": "bó", "qty": 3}, {"name": "Xôi gấc", "unit": "đĩa", "qty": 1}]


def _fake_space(monkeypatch, reply: dict, status=200):
    sent = {}

    def post(url, files=None, data=None, timeout=None):
        sent.update(url=url, files=files, data=data)
        return httpx.Response(status, json=reply)
    monkeypatch.setattr(recognition.httpx, "post", post)
    return sent


def test_hfspace_counts_items(monkeypatch):
    sent = _fake_space(monkeypatch, {"items": [{"name": "Hương (nhang)", "seen": 3, "note": ""},
                                               {"name": "Xôi gấc", "seen": 1, "note": "đĩa đỏ"}],
                                     "extra": ["Bát hương", "mâm đồng"], "summary": "Mâm đủ lễ."})
    r = recognition.analyze(b"\xff\xd8jpeg", ITEMS, "hfspace")
    assert r["ok"] and r["items"][1]["note"] == "đĩa đỏ" and r["problems"] == []
    assert r["extra"] == []  # vật cố định của ban thờ không tính là lễ vật thừa
    assert sent["url"] == get_settings().recognition_url + "/tray"
    assert json.loads(sent["data"]["items"]) == ITEMS  # chỉ gửi ảnh + lễ vật, không có tên khách
    assert set(sent["data"]) == {"items"}


def test_missing_item_flagged(monkeypatch):
    _fake_space(monkeypatch, {"items": [{"name": "Hương (nhang)", "seen": 2}, {"name": "xôi gấc", "seen": "?"}]})
    r = recognition.analyze(b"x", ITEMS, "hfspace")
    assert not r["ok"] and [(i["seen"], i["status"]) for i in r["items"]] == [(2, "thieu"), (0, "thieu")]
    assert r["problems"] == ["Thiếu 1 bó Hương (nhang)", "Thiếu 1 đĩa Xôi gấc"]


def test_extra_quantity_and_unlisted_items_flagged(monkeypatch):
    _fake_space(monkeypatch, {"items": [{"name": "Hương (nhang)", "seen": 3}, {"name": "Xôi gấc", "seen": 2}],
                              "extra": ["Gà luộc", "bát hương"]})
    r = recognition.analyze(b"x", ITEMS, "hfspace")
    assert not r["ok"] and [i["status"] for i in r["items"]] == ["du", "thua"]
    assert r["problems"] == ["Thừa 1 đĩa Xôi gấc", "Ngoài đơn: Gà luộc"]


def test_space_error_raises(monkeypatch):
    _fake_space(monkeypatch, {"detail": "Tray lỗi"}, status=500)
    with pytest.raises(recognition.RecognitionError):
        recognition.analyze(b"x", ITEMS, "hfspace")


def test_device_photos_analyzed_and_shown(setup, db, user_client, monkeypatch):  # noqa: F811
    monkeypatch.setattr(get_settings(), "recognition_provider", "fake")
    order, agent, clock = setup
    at = move_play_time(db, order)
    run(db, agent, clock)
    run(db, agent, clock, at.timestamp() + 0.5)
    o = db.get(Order, order.id)
    assert all(e.analysis and e.analysis["ok"] for e in o.evidence)
    page = user_client.get(f"{P}/don/{o.id}").text
    assert "Kiểm tra mâm lễ" in page and "Khớp đơn" in page and "(giả lập)" in page and "Phiếu tên" not in page


@pytest.fixture(autouse=True)
def no_retry_wait(monkeypatch):
    monkeypatch.setattr(recognition, "RETRY_DELAYS", (0, 0))


def test_recognition_error_does_not_break_order(setup, db, monkeypatch):  # noqa: F811
    monkeypatch.setattr(get_settings(), "recognition_provider", "hfspace")
    _fake_space(monkeypatch, {}, status=503)
    order, agent, clock = setup
    at = move_play_time(db, order)
    run(db, agent, clock)
    run(db, agent, clock, at.timestamp() + 0.5)
    o = db.get(Order, order.id)
    assert o.status == "playing" and all("error" in e.analysis for e in o.evidence)


def test_mismatch_alerts_temple_staff_only(setup, db, client, monkeypatch):  # noqa: F811
    """Mâm thiếu → bảng kiểm tra trên trang lễ của khách; cảnh báo chỉ ở trang Quản lý của nhân sự đền đó, 1 lần/đơn,
    không gửi Telegram."""
    monkeypatch.setattr(get_settings(), "recognition_provider", "hfspace")
    _fake_space(monkeypatch, {"items": [], "extra": ["rượu"]})
    sent = []
    monkeypatch.setattr(alerts, "send_telegram", lambda text: sent.append(text))
    order, agent, clock = setup
    at = move_play_time(db, order)
    run(db, agent, clock)
    run(db, agent, clock, at.timestamp() + 0.5)
    db.expire_all()
    o = db.get(Order, order.id)
    assert len(o.evidence) >= 2 and all(not e.analysis["ok"] for e in o.evidence)
    page = client.get(f"{P}/don/{o.id}").text  # khách tự xem
    assert "Chưa khớp đơn" in page and "Thiếu" in page and "Ngoài đơn" in page and "rượu" in page
    assert sum(1 for e in o.evidence if e.analysis.get("alerted")) == 1
    assert db.query(AuditLog).filter(AuditLog.action == "alert", AuditLog.target == f"order:{o.id}").count() == 1
    assert not [t for t in sent if "Mâm lễ" in t]  # không gửi Telegram
    other = db.scalar(select(Temple).where(Temple.id != o.temple_id))
    stranger = User(name="Kiosk khác", email="kiosk2@example.com", password_hash="x", role="vendor")
    stranger.staff_of.append(TempleStaff(temple_id=other.id))
    db.add(stranger)
    db.commit()
    assert alerts.active(db, stranger) == []  # nhân sự đền khác không thấy
    login(client, "kiosk@example.com", "demo12345")
    assert f"Mâm lễ chưa khớp đơn #{o.id}" in client.get(f"{P}/admin").text


def test_recognition_retries_when_space_times_out(setup, db, monkeypatch):  # noqa: F811
    """Gemini free tier quá tải → Space trả 500 timeout; server thử lại rồi có kết quả."""
    monkeypatch.setattr(get_settings(), "recognition_provider", "hfspace")
    calls = []

    def post(url, files=None, data=None, timeout=None):
        calls.append(1)
        if len(calls) % 2:
            return httpx.Response(500, json={"detail": "Tray lỗi: The read operation timed out"})
        items = json.loads(data["items"])
        return httpx.Response(200, json={"items": [{"name": i["name"], "seen": i["qty"]} for i in items], "extra": []})
    monkeypatch.setattr(recognition.httpx, "post", post)
    order, agent, clock = setup
    at = move_play_time(db, order)
    run(db, agent, clock)
    db.expire_all()
    ev = db.get(Order, order.id).evidence[0]
    assert ev.analysis["ok"] and "error" not in ev.analysis and len(calls) == 2


def test_before_photo_mismatch_alone_does_not_alert(setup, db, client, monkeypatch):  # noqa: F811
    """Ảnh trước lễ chụp lúc còn đang bày mâm: lệch cũng không báo; ảnh lúc khấn khớp → trang hiện "Khớp đơn"."""
    monkeypatch.setattr(get_settings(), "recognition_provider", "hfspace")
    calls = []

    def post(url, files=None, data=None, timeout=None):
        calls.append(1)
        items = json.loads(data["items"])
        seen = 0 if len(calls) == 1 else None  # ảnh đầu (trước lễ) thiếu hết
        return httpx.Response(200, json={"items": [{"name": i["name"], "seen": i["qty"] if seen is None else 0}
                                                   for i in items], "extra": []})
    monkeypatch.setattr(recognition.httpx, "post", post)
    order, agent, clock = setup
    at = move_play_time(db, order)
    run(db, agent, clock)
    run(db, agent, clock, at.timestamp() + 0.5)
    db.expire_all()
    o = db.get(Order, order.id)
    by = {e.note: e.analysis for e in o.photos}
    assert not by["before"]["ok"] and by["start"]["ok"]
    assert db.query(AuditLog).filter(AuditLog.action == "alert", AuditLog.target == f"order:{o.id}").count() == 0
    page = client.get(f"{P}/don/{o.id}").text
    assert "Khớp đơn" in page and "lúc khấn" in page


@pytest.mark.parametrize("thing,ignored", [
    ("Đĩa nhựa trắng", True), ("Bát hương", True), ("khay inox", True), ("Một cái đĩa sứ trắng trống", True),
    ("Đĩa xôi", False), ("Khay hoa quả", False), ("Lọ hoa", False), ("rượu", False), ("chén nước", False)])
def test_empty_containers_are_not_extra_offerings(thing, ignored):
    """Camera thật (đơn #28): AI liệt kê "Đĩa nhựa trắng" đựng hương → đồ đựng trống không tính là lễ vật ngoài đơn."""
    assert recognition._is_fixture(thing) is ignored
