import hashlib
import hmac
import json

from sqlalchemy import select

from app.config import get_settings
from app.models import AuditLog, Order, Payment, Prayer, PrayerTemplate, Temple
from conftest import P, login
from helpers import booking_data, confirm_and_pay, create_booking, post_json, temple_id, tone


def orders_of(db, ref):
    db.expire_all()
    return db.scalars(select(Order).where(Order.booking_ref == ref).order_by(Order.id)).all()


def test_everything_requires_login(client):
    for path in ("/", "/den/den-ngoc-son", "/dat-le?den=1&goi=2"):
        r = client.get(f"{P}{path}", follow_redirects=False)
        assert r.status_code == 303 and "dang-nhap" in r.headers["location"]
    # sau khi đăng nhập quay lại đúng chỗ (giữ cả đền + gói đã chọn)
    assert "%3Fden%3D1%26goi%3D2" in client.get(f"{P}/dat-le?den=1&goi=2", follow_redirects=False).headers["location"]


def test_booking_page_requires_login(client):
    r = client.get(f"{P}/dat-le", follow_redirects=False)
    assert r.status_code == 303 and "dang-nhap" in r.headers["location"]


def test_booking_page_renders(user_client, db):
    r = user_client.get(f"{P}/dat-le?den={temple_id(db)}")
    assert r.status_code == 200 and "Gà luộc" in r.text and 'name="sl_' in r.text and "Ghi âm" not in r.text[:0]


def test_preview_and_lunar(user_client, db):
    r = post_json(user_client, "/dat-le/xem-truoc", booking_data(db, thoi_gian="2026-02-17T09:00"))
    assert r.status_code == 200
    text = r.json()["text"]
    assert "Đền Ngọc Sơn" in text and "Canh Ngọ" in text and "mùng 1 tháng Giêng năm Bính Ngọ" in text
    r = user_client.get(f"{P}/dat-le/am-lich?ngay=2024-09-17")
    assert r.json()["text"] == "15 tháng 8 năm Giáp Thìn"


def test_preview_multi_keeps_temple_placeholders(user_client, db):
    r = post_json(user_client, "/dat-le/xem-truoc", booking_data(db, temples=("den-ngoc-son", "chua-tran-quoc")))
    assert r.json()["multi"] and "{ten_den}" in r.json()["text"]


def test_tts_listen(user_client, db):
    r = post_json(user_client, "/dat-le/nghe-thu", {"van_ban": "Kính lạy chư vị, con xin dâng lễ."})
    assert r.status_code == 200
    a = user_client.get(r.json()["url"])
    assert a.status_code == 200 and a.headers["content-type"] == "audio/mpeg"


def test_full_tts_flow_to_scheduled(user_client, db):
    ref = create_booking(user_client, db)
    [o] = orders_of(db, ref)
    assert o.status == "awaiting_payment" and o.total == 20_000
    assert [(i.name, i.unit, i.qty, i.price) for i in o.items] == [("Hương (nhang)", "bó", 1, 20_000)]
    from helpers import TXN
    r = user_client.get(f"{P}/thanh-toan/{TXN[ref]}")
    assert "Nguyễn Văn A" in r.text and "Thanh toán 20.000 ₫" in r.text and "1 bó hương (nhang)" in r.text
    confirm_and_pay(user_client, ref)
    [o] = orders_of(db, ref)
    assert o.status == "scheduled"
    assert [e.status for e in o.events] == ["created", "awaiting_payment", "paid", "scheduled"]
    assert not o.play_asap
    assert o.script_text and "Đền Ngọc Sơn" in o.script_text and o.audio_key.startswith("tts/")
    assert len(o.audio_sha256) == 64
    assert db.scalar(select(Payment).where(Payment.order_id == o.id)).status == "succeeded"
    page = user_client.get(f"{P}/don/{o.id}")
    assert "Đã xếp lịch" in page.text and "Hủy đơn" in page.text
    assert user_client.get(f"{P}/don/{o.id}/audio").status_code == 200
    assert user_client.get(f"{P}/don/{o.id}/trang-thai").status_code == 200
    assert "Đặt lại đơn này" in user_client.get(f"{P}/don").text


def test_edited_text_is_used(user_client, db):
    d = booking_data(db)
    d["van_ban_goc"] = "Mẫu gốc dài vừa phải cho việc kiểm tra."
    d["van_ban"] = "Kính lạy chư vị tại {ten_den}. Con là {ho_ten}, xin phù hộ."
    r = post_json(user_client, "/dat-le", d)
    ref = r.json()["ref"]
    from helpers import TXN
    TXN[ref] = r.json()["txn"]
    confirm_and_pay(user_client, ref)
    [o] = orders_of(db, ref)
    assert o.script_text == "Kính lạy chư vị tại Đền Ngọc Sơn. Con là Nguyễn Văn A, xin phù hộ."


def test_edit_limits(user_client, db):
    d = booking_data(db, van_ban_goc="ngắn", van_ban="x" * 400)
    assert post_json(user_client, "/dat-le", d).status_code == 400  # sửa quá nhiều
    d = booking_data(db, van_ban_goc="ngắn", van_ban="{bien_la}")
    assert "biến" in post_json(user_client, "/dat-le", d).json()["error"]


def test_validation_errors(user_client, db):
    assert post_json(user_client, "/dat-le", booking_data(db, minutes=0)).status_code == 400  # quá sát giờ
    assert post_json(user_client, "/dat-le", booking_data(db, temples=())).status_code == 400
    assert post_json(user_client, "/dat-le", booking_data(db, ho_ten="")).status_code == 400
    assert post_json(user_client, "/dat-le", booking_data(db, nam_sinh="1800")).status_code == 400
    d = booking_data(db)
    d["den"] = [str(i) for i in range(1, 102)]
    assert "tối đa 100" in post_json(user_client, "/dat-le", d).json()["error"]


def test_multi_temple_creates_orders_per_temple(user_client, db):
    ref = create_booking(user_client, db, temples=("den-ngoc-son", "chua-tran-quoc", "den-ba-chua-xu"))
    orders = orders_of(db, ref)
    assert len(orders) == 3 and len({o.prayer_id for o in orders}) == 1
    confirm_and_pay(user_client, ref)
    orders = orders_of(db, ref)
    assert all(o.status == "scheduled" for o in orders)
    assert len({o.audio_key for o in orders}) == 3  # mỗi đền một bài (tên đền khác nhau)
    assert "Miếu Bà Chúa Xứ Núi Sam" in orders[2].script_text and "Bà Chúa Xứ Thánh Mẫu" in orders[2].script_text
    assert len(db.scalars(select(Payment).where(Payment.order_id.in_([o.id for o in orders]))).all()) == 3


def test_temple_specific_template(user_client, db):
    db.add(PrayerTemplate(name="riêng", temple_id=temple_id(db), body="Mẫu riêng Ngọc Sơn: {ho_ten} tại {ten_den}."))
    db.commit()
    r = post_json(user_client, "/dat-le/xem-truoc", booking_data(db))
    assert r.json()["text"] == "Mẫu riêng Ngọc Sơn: Nguyễn Văn A tại Đền Ngọc Sơn."


def test_payment_failure_keeps_awaiting(user_client, db):
    ref = create_booking(user_client, db)
    txn = confirm_and_pay(user_client, ref, success=False)
    [o] = orders_of(db, ref)
    assert o.status == "awaiting_payment"
    assert "Giao dịch đã xử lý" in user_client.get(f"{P}/thanh-toan/{txn}").text


def test_cancel_paid_order_requests_refund(user_client, db):
    ref = create_booking(user_client, db)
    confirm_and_pay(user_client, ref)
    [o] = orders_of(db, ref)
    r = user_client.post(f"{P}/don/{o.id}/huy", data={"csrf_token": user_client.csrf}, follow_redirects=False)
    assert r.status_code == 303
    [o] = orders_of(db, ref)
    assert o.status == "refund_requested"
    assert user_client.post(f"{P}/don/{o.id}/huy", data={"csrf_token": user_client.csrf}).status_code == 409


def test_cannot_cancel_close_to_play_time(user_client, db):
    ref = create_booking(user_client, db, minutes=5)  # < DISPATCH_LEAD (10 phút)
    confirm_and_pay(user_client, ref)
    [o] = orders_of(db, ref)
    assert o.status == "scheduled"
    assert user_client.post(f"{P}/don/{o.id}/huy", data={"csrf_token": user_client.csrf}).status_code == 409


def test_other_user_cannot_see_order(user_client, db, client):
    ref = create_booking(user_client, db)
    [o] = orders_of(db, ref)
    user_client.post(f"{P}/dang-xuat", data={"csrf_token": user_client.csrf})
    tok = login(client, "kiosk@example.com", "demo12345")  # nhân sự đền cũng không xem được dữ liệu cá nhân
    assert client.get(f"{P}/don/{o.id}").status_code == 404
    from helpers import TXN
    assert client.get(f"{P}/thanh-toan/{TXN[ref]}").status_code == 404
    assert client.get(f"{P}/don/{o.id}/audio").status_code == 404


def test_recording_upload_flow(user_client, db, tmp_path):
    wav = tone(tmp_path / "rec.wav", 3)
    r = post_json(user_client, "/dat-le/ghi-am", files={"file": ("rec.wav", wav.read_bytes(), "audio/wav")})
    assert r.status_code == 200, r.text
    key = r.json()["key"]
    assert user_client.get(r.json()["url"]).status_code == 200
    ref = create_booking(user_client, db, cach_khan="recorded", ghi_am=key)
    confirm_and_pay(user_client, ref)
    [o] = orders_of(db, ref)
    assert o.status == "scheduled" and o.audio_key == key and o.prayer.moderation == "approved"


def test_recording_pending_when_auto_approve_off(user_client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "auto_approve_recordings", False)
    key = post_json(user_client, "/dat-le/ghi-am",
                    files={"file": ("r.wav", tone(tmp_path / "r.wav").read_bytes(), "audio/wav")}).json()["key"]
    ref = create_booking(user_client, db, cach_khan="recorded", ghi_am=key)
    confirm_and_pay(user_client, ref)
    [o] = orders_of(db, ref)
    assert o.status == "paid" and o.prayer.moderation == "pending"  # chờ duyệt mới xếp lịch


def test_recording_rejects_fake_extension_and_foreign_key(user_client, db):
    r = post_json(user_client, "/dat-le/ghi-am", files={"file": ("x.mp3", b"<html>not audio</html>", "audio/mpeg")})
    assert r.status_code == 415
    r = post_json(user_client, "/dat-le", booking_data(db, cach_khan="recorded", ghi_am="recordings/999/x.mp3"))
    assert r.status_code == 400  # không dùng được file không thuộc phiên của mình


def test_reorder_prefills(user_client, db):
    ref = create_booking(user_client, db)
    [o] = orders_of(db, ref)
    r = user_client.get(f"{P}/dat-le?tu_don={o.id}")
    assert 'value="Nguyễn Văn A"' in r.text and 'value="1990"' in r.text


def test_payment_webhook_signature(user_client, db, monkeypatch):
    monkeypatch.setattr(get_settings(), "payment_webhook_secret", "whsec")
    ref = create_booking(user_client, db)
    from helpers import TXN
    txn = TXN[ref]
    body = json.dumps({"txn_ref": txn, "status": "succeeded"}).encode()
    url = f"{P}/api/thanh-toan/webhook/mock"
    assert user_client.post(url, content=body, headers={"X-Signature": "sai"}).status_code == 401
    sig = hmac.new(b"whsec", body, hashlib.sha256).hexdigest()
    assert user_client.post(url, content=body, headers={"X-Signature": sig}).status_code == 200
    assert user_client.post(url, content=body, headers={"X-Signature": sig}).status_code == 200  # idempotent
    [o] = orders_of(db, ref)
    assert o.status == "scheduled"
    assert db.scalar(select(AuditLog).where(AuditLog.actor == "webhook:mock"))


def test_preselected_temple_shows_summary_and_item_menu(user_client, db):
    tid = temple_id(db)
    from helpers import shared_package
    pkg = shared_package(db)
    html = user_client.get(f"{P}/dat-le?den={tid}&goi={pkg.id}").text  # link cũ ?goi= → món đó 1 phần
    assert "Nơi dâng lễ" in html and 'name="den" value="%d"' % tid in html and 'type="checkbox" name="den"' not in html
    assert f'name="sl_{pkg.id}" value="1"' in html and 'name="goi"' not in html
    html = user_client.get(f"{P}/dat-le").text  # chưa chọn gì → hiện danh sách để chọn
    assert 'type="checkbox" name="den"' in html


def test_devotee_info_saved_to_profile(user_client, db):
    html = user_client.get(f"{P}/dat-le?den={temple_id(db)}").text
    assert 'id="info-fields" hidden' not in html and 'id="info-summary"' not in html  # lần đầu: hiện form để nhập
    create_booking(user_client, db)
    from app.models import User
    db.expire_all()
    u = db.scalar(select(User).where(User.email == "a@example.com"))
    assert (u.devotee_name, u.birth_year, u.address) == ("Nguyễn Văn A", 1990, "Cầu Giấy, Hà Nội")
    html = user_client.get(f"{P}/dat-le?den={temple_id(db)}").text
    assert 'id="info-summary"' in html and 'id="info-fields" hidden' in html  # lần sau: thu gọn, bấm Sửa mới mở
    r = user_client.post(f"{P}/tai-khoan/tin-chu", data={"ho_ten": "Trần Thị B", "nam_sinh": "1992", "dia_chi": "HCM",
                                                       "nguyen_vong": "bình an", "csrf_token": user_client.csrf},
                         follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    assert db.scalar(select(User).where(User.email == "a@example.com")).devotee_name == "Trần Thị B"


def test_play_now_dispatches_right_after_payment(user_client, db):
    ref = create_booking(user_client, db, khi_nao="ngay", thoi_gian="")
    [o] = orders_of(db, ref)
    assert o.play_asap and o.status == "awaiting_payment"
    confirm_and_pay(user_client, ref)
    [o] = orders_of(db, ref)
    from app.models import utcnow
    from datetime import timedelta
    assert o.status == "scheduled"
    assert utcnow() < o.scheduled_at < utcnow() + timedelta(seconds=60)  # phát sau ~20 giây
    sent = [p for d, p in db.bus.sent if p.get("type") == "play"]
    assert sent and sent[-1]["job_id"] == o.jobs[-1].id  # lệnh đã vào kênh ngay, không chờ vòng nền


def test_hen_gio_requires_time(user_client, db):
    r = post_json(user_client, "/dat-le", booking_data(db, khi_nao="hen_gio", thoi_gian=""))
    assert r.status_code == 400 and "Phát ngay" in r.json()["error"]


def test_tts_prewarmed_at_booking(user_client, db, monkeypatch):
    """Giọng đọc được tạo ngay khi đặt (trước thanh toán) để 'phát ngay' không phải chờ TTS."""
    from app import tts
    from app.storage import get_storage
    ref = create_booking(user_client, db, khi_nao="ngay", thoi_gian="")
    [o] = orders_of(db, ref)
    from app import orders as svc
    key, _ = tts.synthesize_cached(svc.script_for(db, o.prayer, o), o.prayer.voice)
    assert get_storage().exists(key)
    calls = []
    monkeypatch.setattr(tts.FakeTTS, "synthesize", lambda *a: calls.append(1))
    confirm_and_pay(user_client, ref)
    assert calls == []  # lúc xếp lịch dùng cache, không gọi nhà cung cấp TTS nữa
    assert orders_of(db, ref)[0].status == "scheduled"


def _item(db, name):
    from app.models import OfferingPackage
    return db.scalar(select(OfferingPackage).where(OfferingPackage.name == name))


def test_itemized_offerings_total_script_and_tray(user_client, db):
    from helpers import shared_package
    huong, ga, xoi = shared_package(db), _item(db, "Gà luộc"), _item(db, "Xôi gấc")
    d = booking_data(db, temples=("den-ngoc-son", "chua-tran-quoc"), **{f"sl_{huong.id}": "3", f"sl_{ga.id}": "1",
                                                                        f"sl_{xoi.id}": "2", f"sl_{_item(db, 'Nến').id}": "0"})
    db.scalar(select(Temple).where(Temple.slug == "chua-tran-quoc")).device_id = "pi-demo-01"
    db.commit()
    r = post_json(user_client, "/dat-le/xem-truoc", d)
    assert "3 bó hương (nhang), 2 đĩa xôi gấc, 1 con gà luộc" in r.json()["text"]
    r = post_json(user_client, "/dat-le", d)
    assert r.status_code == 200, r.text
    orders = orders_of(db, r.json()["ref"])
    assert len(orders) == 2 and all(o.total == 3 * 20_000 + 280_000 + 2 * 60_000 for o in orders)
    assert orders[0].offering_text == "3 bó hương (nhang), 2 đĩa xôi gấc, 1 con gà luộc"
    page = user_client.get(f"{P}/thanh-toan/{r.json()['txn']}").text
    assert "Thanh toán 920.000 ₫" in page
    # sửa giá danh mục sau đó không làm đổi đơn đã đặt
    ga.price = 999_000
    db.commit()
    db.expire_all()
    assert orders_of(db, r.json()["ref"])[0].items[2].price == 280_000
    # "đặt lại đơn này" điền lại đúng số lượng
    html = user_client.get(f"{P}/dat-le?tu_don={orders[0].id}").text
    assert f'name="sl_{huong.id}" value="3"' in html and f'name="sl_{ga.id}" value="1"' in html


def test_itemized_validation(user_client, db):
    from helpers import shared_package
    huong, ga = shared_package(db), _item(db, "Gà luộc")
    r = post_json(user_client, "/dat-le", booking_data(db, **{f"sl_{huong.id}": "0"}))
    assert r.status_code == 400 and "ít nhất một lễ vật" in r.json()["error"]
    r = post_json(user_client, "/dat-le", booking_data(db, **{f"sl_{ga.id}": str(ga.max_qty + 1)}))
    assert r.status_code == 400 and "tối đa" in r.json()["error"]
    ga.active = False
    db.commit()
    r = post_json(user_client, "/dat-le", booking_data(db, **{f"sl_{huong.id}": "0", f"sl_{ga.id}": "1"}))
    assert r.status_code == 400  # món đã ngừng bán không được tính
