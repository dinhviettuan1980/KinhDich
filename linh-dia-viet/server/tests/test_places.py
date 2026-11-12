"""Danh bạ + bản đồ đình chùa: phân loại, gán tỉnh, gộp trùng, nạp snapshot, trang công khai, gắn với đền."""
import re

from sqlalchemy import select

from app import places
from app.models import SacredPlace, Temple
from conftest import P


def test_classify_keeps_temples_and_drops_noise():
    assert places.classify("Chùa Trấn Quốc", "buddhist") == "chua"
    assert places.classify("Đình Kim Liên") == "dinh"
    assert places.classify("Đền Ngọc Sơn") == "den"
    assert places.classify("Miếu Bà Chúa Xứ") == "mieu"
    assert places.classify("Phủ Tây Hồ") == "phu"
    assert places.classify("Tam Buu Pagoda") == "chua"
    assert places.classify("An Hòa Tự") == "chua"
    assert places.classify("Chua Hung Long") == "chua"
    # loại khỏi danh bạ
    assert places.classify("Nhà thờ Lớn Hà Nội", "christian") is None
    assert places.classify("Long Xuyen Cathedral") is None
    assert places.classify("Thánh thất Cao Đài Linh Xuân", "caodaism") is None
    assert places.classify("Công ty Kadoki") is None  # không nhận ra loại
    assert places.classify("") is None
    # điểm không gắn tag thờ tự: chỉ nhận khi tên rõ ràng, không nhận "Điện…" (cửa hàng điện máy…)
    assert places.classify("Điện máy Xanh", is_worship=False) is None
    assert places.classify("Điện Hòn Chén", is_worship=True) == "phu"
    assert places.classify("Điện Hòn Chén", is_worship=False) is None
    assert places.classify("Chùa Bửu Đà", is_worship=False) == "chua"


def _square(name, x0, y0, x1, y1):
    ring = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    # chia thành 2 way để kiểm tra không cần ghép vòng
    geo = [{"lat": y, "lon": x} for x, y in ring]
    return {"tags": {"name": name}, "members": [
        {"type": "way", "role": "outer", "geometry": geo[:3]},
        {"type": "way", "role": "outer", "geometry": geo[2:]},
    ]}


def test_province_lookup_point_in_polygon():
    idx = places.ProvinceIndex([_square("Thành phố Hà Nội", 105.0, 20.5, 106.0, 21.5),
                                _square("Tỉnh An Giang", 104.8, 10.2, 105.6, 10.9)])
    assert idx.lookup(21.03, 105.85) == "Hà Nội"
    assert idx.lookup(10.68, 105.08) == "An Giang"
    assert idx.lookup(16.0, 108.2) == ""


def _osm(id_, name, lat, lng, typ="node", **tags):
    return {"type": typ, "id": id_, "lat": lat, "lon": lng, "tags": {"amenity": "place_of_worship", "name": name, **tags}}


def test_records_dedupe_and_merge_with_wikidata():
    osm = places.records_from_osm([
        _osm(1, "Chùa Trấn Quốc", 21.0478, 105.8368, religion="buddhist"),
        _osm(2, "Chùa Trấn Quốc", 21.0480, 105.8370, typ="way", wikipedia="vi:Chùa Trấn Quốc"),
        _osm(3, "Chùa Trấn Quốc", 10.0, 106.0),  # cùng tên nhưng ở nơi khác → giữ
        _osm(4, "Nhà thờ Lớn", 21.0287, 105.8490, religion="christian"),
    ], None)
    assert len(osm) == 3
    kept = places.dedupe(osm)
    assert sorted(r["sid"] for r in kept) == ["node/3", "way/2"]
    assert next(r for r in kept if r["sid"] == "way/2")["wp"] == "Chùa Trấn Quốc"
    wd = places.records_from_wikidata([
        {"item": {"value": "http://www.wikidata.org/entity/Q1"}, "label": {"value": "Đền Ngọc Sơn"},
         "coord": {"value": "Point(105.8524 21.0307)"},
         "article": {"value": "https://vi.wikipedia.org/wiki/%C4%90%E1%BB%81n_Ng%E1%BB%8Dc_S%C6%A1n"},
         "image": {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/Ngoc%20Son.jpg"}},
        {"item": {"value": "http://www.wikidata.org/entity/Q2"}, "label": {"value": "Chùa Trấn Quốc"},
         "coord": {"value": "Point(105.8369 21.0479)"}},
    ], None)
    merged = places.merge(kept, wd)
    assert len(merged) == 3  # Trấn Quốc gộp vào OSM, Ngọc Sơn thêm mới từ Wikidata
    ngoc_son = next(r for r in merged if r["sid"] == "Q1")
    assert ngoc_son["wp"] == "Đền Ngọc Sơn" and "width=640" in ngoc_son["img"]
    assert next(r for r in merged if r["sid"] == "way/2")["wd"] == "Q2"


def _snap(version="v1", **over):
    rec = {"src": "osm", "sid": "way/2", "name": "Chùa Trấn Quốc", "kind": "chua", "rel": "buddhist",
           "lat": 21.048, "lng": 105.837, "prov": "Hà Nội", "addr": "Thanh Niên", "phone": "", "web": "",
           "wd": "Q2", "wp": "Chùa Trấn Quốc", "desc": "Ngôi chùa cổ nhất Thăng Long.",
           "desc_src": "https://vi.wikipedia.org/wiki/Ch%C3%B9a_Tr%E1%BA%A5n_Qu%E1%BB%91c"}
    rec.update(over)
    other = {"src": "osm", "sid": "node/9", "name": "Đình Kim Liên", "kind": "dinh", "lat": 21.007, "lng": 105.838,
             "prov": "Hà Nội", "addr": ""}
    return {"version": version, "places": [rec, other]}


def test_load_snapshot_upserts_links_temple_and_keeps_manual_edits(db):
    res = places.load(db, _snap())
    db.commit()
    assert res["added"] == 2
    p = db.scalar(select(SacredPlace).where(SacredPlace.source_id == "way/2"))
    tran_quoc = db.scalar(select(Temple).where(Temple.slug == "chua-tran-quoc"))
    assert p.temple_id == tran_quoc.id  # tự gắn theo tên
    p.edited, p.description = True, "Mô tả admin viết."
    db.commit()
    res = places.load(db, _snap("v2", desc="Bản mới từ Wikipedia"))
    db.commit()
    assert res["added"] == 0
    db.refresh(p)
    assert p.description == "Mô tả admin viết."


def test_map_page_and_points_are_public(client, db):
    places.load(db, _snap())
    db.commit()
    r = client.get(f"{P}/ban-do")
    assert r.status_code == 200 and "Bản đồ đình chùa" in r.text and "/static/map.js" in r.text
    assert 'key: ""' in r.text  # chưa có key → Leaflet
    j = client.get(f"{P}/ban-do/diem.json").json()
    assert j["provinces"] == ["Hà Nội"] and j["kinds"]["chua"] == "Chùa"
    by_name = {pt[4]: pt for pt in j["points"]}
    assert by_name["Chùa Trấn Quốc"][6] == 2  # đền đối tác có thiết bị (conftest gắn thiết bị cho mọi đền)
    assert by_name["Đình Kim Liên"][6] == 0


def test_place_detail_shows_booking_and_attribution(client, db):
    places.load(db, _snap())
    db.commit()
    tq = db.scalar(select(SacredPlace).where(SacredPlace.source_id == "way/2"))
    kl = db.scalar(select(SacredPlace).where(SacredPlace.source_id == "node/9"))
    html = client.get(f"{P}/dia-diem/{tq.id}").text
    assert "Sắm lễ và đặt lễ tại đây" in html and f"{P}/den/chua-tran-quoc" in html
    assert "Ngôi chùa cổ nhất Thăng Long." in html and "CC BY-SA 4.0" in html
    assert "openstreetmap.org/way/2" in html and "google.com/maps/dir/?api=1&destination=21.048,105.837" in html
    html = client.get(f"{P}/dia-diem/{kl.id}").text
    assert "chưa nhận lễ từ xa" in html and "Sắm lễ" not in html
    kl.status = "hidden"
    db.commit()
    assert client.get(f"{P}/dia-diem/{kl.id}").status_code == 404
    assert client.get(f"{P}/dia-diem/999999").status_code == 404


def test_admin_links_temple_to_place(admin_client, db):
    places.load(db, _snap())
    db.commit()
    kl = db.scalar(select(SacredPlace).where(SacredPlace.source_id == "node/9"))
    tq = db.scalar(select(SacredPlace).where(SacredPlace.source_id == "way/2"))
    ngoc_son = db.scalar(select(Temple).where(Temple.slug == "den-ngoc-son"))
    form = admin_client.get(f"{P}/admin/den/{ngoc_son.id}").text
    assert 'name="place_id"' in form
    data = {"csrf_token": admin_client.csrf, "name": ngoc_son.name, "slug": ngoc_son.slug, "status": "active",
            "device_id": ngoc_son.device_id or "", "place_id": str(kl.id)}
    r = admin_client.post(f"{P}/admin/den/{ngoc_son.id}", data=data, follow_redirects=False)
    assert r.status_code in (302, 303), r.text
    db.expire_all()
    assert db.get(SacredPlace, kl.id).temple_id == ngoc_son.id
    # địa điểm đã thuộc đền khác → 409
    r = admin_client.post(f"{P}/admin/den/{ngoc_son.id}", data={**data, "place_id": str(tq.id)}, follow_redirects=False)
    assert r.status_code == 409
    # bỏ gắn
    r = admin_client.post(f"{P}/admin/den/{ngoc_son.id}", data={**data, "place_id": ""}, follow_redirects=False)
    db.expire_all()
    assert db.get(SacredPlace, kl.id).temple_id is None
    page = admin_client.get(f"{P}/den/den-ngoc-son").text
    assert not re.search(r"Giới thiệu, vị trí", page)


def test_real_snapshot_is_sane():
    snap = places.read_snapshot()
    assert snap and len(snap["places"]) > 3000
    names = {p["name"] for p in snap["places"]}
    assert {"Đền Ngọc Sơn", "Chùa Trấn Quốc", "Miếu Bà Chúa Xứ Núi Sam"} <= names
    assert all(p["kind"] in ("chua", "den", "dinh", "mieu", "phu") for p in snap["places"])
    assert sum(1 for p in snap["places"] if not p["prov"]) < len(snap["places"]) * 0.02
