"""Nhận diện mâm lễ: đối chiếu lễ vật + phiếu tên trên ảnh thiết bị gửi lên (server, không phải Pi)."""
import json

import httpx
import pytest
from sqlalchemy import select

from app import recognition
from app.config import get_settings
from app.models import Order, User
from conftest import P, login
from test_m3_devices import move_play_time, run, setup  # noqa: F401  (fixture)

ITEMS = [{"name": "Hương (nhang)", "unit": "bó", "qty": 3}, {"name": "Xôi gấc", "unit": "đĩa", "qty": 1}]


def test_name_matching():
    assert recognition.name_matches("TÍN CHỦ: NGUYỄN VĂN AN\nsinh 1985", "Nguyễn Văn An")
    assert recognition.name_matches("nguyen van an", "Nguyễn Văn An")
    assert not recognition.name_matches("Nguyễn Văn Bình", "Nguyễn Văn An")
    assert not recognition.name_matches("", "Nguyễn Văn An")


def _fake_api(monkeypatch, reply: dict, status=200):
    sent = {}

    def post(url, json=None, headers=None, timeout=None):
        sent.update(url=url, body=json, headers=headers)
        return httpx.Response(status, json={"content": [{"type": "text", "text": "Kết quả:\n" + __import__("json").dumps(reply)}]})
    monkeypatch.setattr(recognition.httpx, "post", post)
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "sk-test")
    return sent


def test_claude_counts_items_and_reads_name_card(monkeypatch):
    sent = _fake_api(monkeypatch, {"items": [{"name": "Hương (nhang)", "seen": 3, "note": ""},
                                             {"name": "Xôi gấc", "seen": 1, "note": "đĩa đỏ"}],
                                   "extra": ["chén nước"], "name_card": {"found": True, "text": "NGUYEN VAN AN", "match": False},
                                   "summary": "Mâm đủ lễ."})
    r = recognition.analyze(b"\xff\xd8jpeg", ITEMS, "Nguyễn Văn An", "claude")
    assert r["ok"] and r["items_ok"] and r["name_card"]["match"]  # khớp tên tính lại phía server (không dấu)
    assert r["items"][1]["note"] == "đĩa đỏ" and r["extra"] == ["chén nước"]
    body = sent["body"]
    assert body["model"] == get_settings().recognition_model and sent["headers"]["x-api-key"] == "sk-test"
    assert body["messages"][0]["content"][0]["source"]["media_type"] == "image/jpeg"
    assert "Hương (nhang) · bó · 3" in body["messages"][0]["content"][1]["text"]


def test_claude_missing_item_and_wrong_name(monkeypatch):
    _fake_api(monkeypatch, {"items": [{"name": "Hương (nhang)", "seen": 2}], "extra": [],
                            "name_card": {"found": True, "text": "Trần Thị B", "match": True}, "summary": ""})
    r = recognition.analyze(b"x", ITEMS, "Nguyễn Văn An", "claude")
    assert not r["ok"] and [i["ok"] for i in r["items"]] == [False, False]
    assert not r["name_card"]["match"]  # mô hình nói khớp nhưng chữ đọc được là tên khác → không khớp


def test_api_error_recorded_without_breaking_order(monkeypatch):
    _fake_api(monkeypatch, {}, status=529)
    with pytest.raises(recognition.RecognitionError):
        recognition.analyze(b"x", ITEMS, "A", "claude")


def test_provider_auto_off_without_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "")
    assert recognition.provider() == "off"
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "sk")
    assert recognition.provider() == "claude"


def test_device_photos_analyzed_and_shown(setup, db, user_client, monkeypatch):  # noqa: F811
    monkeypatch.setattr(get_settings(), "recognition_provider", "fake")
    order, agent, clock = setup
    at = move_play_time(db, order)
    run(db, agent, clock)
    run(db, agent, clock, at.timestamp() + 0.5)
    o = db.get(Order, order.id)
    assert all(e.analysis and e.analysis["ok"] for e in o.evidence)
    page = user_client.get(f"{P}/don/{o.id}").text
    assert "Kiểm tra mâm lễ" in page and "Khớp đơn" in page and "(giả lập)" in page


def test_name_card_page_permissions(setup, db, client, user_client):  # noqa: F811
    order, *_ = setup
    assert user_client.get(f"{P}/admin/don/{order.id}/phieu-ten").status_code == 403  # khách thường
    user_client.post(f"{P}/dang-xuat", data={"csrf_token": user_client.csrf})
    login(client, "admin@example.com", "admin12345")
    html = client.get(f"{P}/admin/don/{order.id}/phieu-ten").text
    assert "Nguyễn Văn A" in html and f"Đơn #{order.id}" in html and "Canh Ngọ" in html


def test_name_matching_tolerates_handwriting_typos():
    assert recognition.name_matches("Nguyen Van Ann", "Nguyễn Văn An")
    assert recognition.name_matches("Tín chủ Nguyển Vản An", "Nguyễn Văn An")
    assert not recognition.name_matches("Nguyễn Văn Bình", "Nguyễn Văn An")
