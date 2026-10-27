"""Quy trình mới: đăng ký (tín chủ) → thẻ giả lập → đặt lễ → chốt (trừ thẻ) → lịch sử có ảnh + clip xem lại."""
from datetime import date

from sqlalchemy import select

from app.models import Order, User
from conftest import P, csrf_of
from helpers import booking_data, post_json, temple_id, tone


def _register(client, **over):
    tok = csrf_of(client, f"{P}/dang-ky")
    data = {"name": "Lê Văn Mới", "identifier": "moi@example.com", "password": "abcdefgh", "ngay_sinh": "1990-01-10",
            "dia_chi": "Hoàn Kiếm, Hà Nội", "csrf_token": tok}
    data.update(over)
    return client.post(f"{P}/dang-ky", data=data, follow_redirects=False)


def test_register_then_card_then_booking(client, db):
    r = _register(client)
    assert r.status_code == 303 and "/tai-khoan/the" in r.headers["location"]  # đủ hồ sơ → bước thẻ
    u = db.scalar(select(User).where(User.email == "moi@example.com"))
    # sinh 10/01/1990 dương lịch = trước Tết Canh Ngọ → năm âm 1989 (Kỷ Tỵ)
    assert u.birth_date == date(1990, 1, 10) and u.birth_year == 1989 and u.devotee_name == "Lê Văn Mới"
    tok = csrf_of(client, f"{P}/")
    # chưa có thẻ → vào trang đặt lễ bị đưa sang bước thẻ, giữ lại trang muốn tới
    r = client.get(f"{P}/dat-le?den={temple_id(db)}", follow_redirects=False)
    assert r.status_code == 303 and "/tai-khoan/the?next=" in r.headers["location"] and "dat-le" in r.headers["location"]
    # thẻ giả lập: gõ gì cũng nhận
    r = client.post(f"{P}/tai-khoan/the?next={P}/dat-le", data={"so_the": "abc 1234-5678", "het_han": "xx",
                                                                 "cvc": "", "chu_the": "", "csrf_token": tok},
                    follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == f"{P}/dat-le"
    db.expire_all()
    u = db.scalar(select(User).where(User.email == "moi@example.com"))
    assert u.card_last4 == "5678" and u.has_card
    assert client.get(f"{P}/dat-le?den={temple_id(db)}").status_code == 200
    # ô số thẻ để trống thì báo
    assert client.post(f"{P}/tai-khoan/the", data={"so_the": " ", "csrf_token": tok}).status_code == 400


def test_register_without_profile_goes_to_profile_step(client, db):
    r = _register(client, ngay_sinh="", dia_chi="")
    assert r.status_code == 303 and "/tai-khoan/ho-so" in r.headers["location"]
    assert _register(client, identifier="x2@example.com", ngay_sinh="2999-01-01").status_code == 400


def test_confirm_charges_card_and_lists_in_history(user_client, db):
    d = booking_data(db, khi_nao="ngay", thanh_toan="the")
    r = post_json(user_client, "/dat-le", d)
    assert r.status_code == 200, r.text
    ref = r.json()["ref"]
    assert r.json()["redirect"].endswith(f"/don?moi={ref}")
    [o] = db.scalars(select(Order).where(Order.booking_ref == ref)).all()
    db.refresh(o)
    assert o.status == "scheduled" and o.payments[0].provider == "card" and o.payments[0].status == "succeeded"
    html = user_client.get(f"{P}/don?moi={ref}").text
    assert "Đã chốt lễ" in html and "Visa •••• 4242" in html and "ld-hist new" in html


def test_confirm_without_card_falls_back_to_payment_page(user_client, db):
    u = db.scalar(select(User).where(User.email == "a@example.com"))
    u.card_last4 = None
    db.commit()
    r = post_json(user_client, "/dat-le", booking_data(db, thanh_toan="the"))
    assert r.status_code == 200 and "/thanh-toan/" in r.json()["redirect"]


def test_clip_built_after_completion(user_client, db, tmp_path):
    from app.models import Evidence, utcnow
    from app.storage import get_storage
    r = post_json(user_client, "/dat-le", booking_data(db, khi_nao="ngay", thanh_toan="the"))
    [o] = db.scalars(select(Order).where(Order.booking_ref == r.json()["ref"])).all()
    db.refresh(o)
    assert user_client.get(f"{P}/don/{o.id}/clip").status_code == 404  # chưa xong lễ
    from PIL import Image
    st = get_storage()
    for i, phase in enumerate(("before", "start", "after")):
        p = tmp_path / f"{phase}.jpg"
        Image.new("RGB", (640, 480), (100 + i * 50, 30, 30)).save(p)
        db.add(Evidence(order_id=o.id, path=st.put_file(p, f"evidence/{o.id}/{phase}.jpg"), captured_at=utcnow(),
                        note=phase))
    o.status = "completed"
    db.commit()
    page = user_client.get(f"{P}/don/{o.id}").text
    assert "Clip xem lại" in page
    r = user_client.get(f"{P}/don/{o.id}/clip")
    assert r.status_code == 200 and r.headers["content-type"] == "video/mp4" and r.content[4:8] == b"ftyp"
    db.refresh(o)
    assert o.clip_key == f"clips/{o.id}.mp4"
    assert "▶" in user_client.get(f"{P}/don").text
