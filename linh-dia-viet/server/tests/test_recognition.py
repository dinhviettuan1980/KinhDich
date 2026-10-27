"""Nhận diện mâm lễ: đếm lễ vật trên ảnh thiết bị gửi lên, qua HF Space OCR (/tray). Không gửi thông tin khách."""
import json

import httpx
import pytest

from app import recognition
from app.config import get_settings
from app.models import Order
from conftest import P
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
                                     "extra": ["chén nước"], "summary": "Mâm đủ lễ."})
    r = recognition.analyze(b"\xff\xd8jpeg", ITEMS, "hfspace")
    assert r["ok"] and r["items"][1]["note"] == "đĩa đỏ" and r["extra"] == ["chén nước"]
    assert sent["url"] == get_settings().recognition_url + "/tray"
    assert json.loads(sent["data"]["items"]) == ITEMS  # chỉ gửi ảnh + lễ vật, không có tên khách
    assert set(sent["data"]) == {"items"}


def test_missing_item_flagged(monkeypatch):
    _fake_space(monkeypatch, {"items": [{"name": "Hương (nhang)", "seen": 2}, {"name": "xôi gấc", "seen": "?"}]})
    r = recognition.analyze(b"x", ITEMS, "hfspace")
    assert not r["ok"] and [(i["seen"], i["ok"]) for i in r["items"]] == [(2, False), (0, False)]


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


def test_recognition_error_does_not_break_order(setup, db, monkeypatch):  # noqa: F811
    monkeypatch.setattr(get_settings(), "recognition_provider", "hfspace")
    _fake_space(monkeypatch, {}, status=503)
    order, agent, clock = setup
    at = move_play_time(db, order)
    run(db, agent, clock)
    run(db, agent, clock, at.timestamp() + 0.5)
    o = db.get(Order, order.id)
    assert o.status == "playing" and all("error" in e.analysis for e in o.evidence)
