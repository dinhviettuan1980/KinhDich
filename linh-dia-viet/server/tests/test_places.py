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
    js = client.get(f"{P}/static/map.js").text  # chủ quyền: nhãn hai quần đảo luôn có trên bản đồ
    assert "Quần đảo Hoàng Sa" in js and "Quần đảo Trường Sa" in js
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
    assert "openstreetmap.org/way/2" in html and "google.com/maps/dir/?api=1&destination=21.048%2C105.837" in html
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
    assert all(p["kind"] in ("chua", "den", "dinh", "mieu", "phu", *places.CEMETERY_KINDS) for p in snap["places"])
    assert sum(p["kind"] == "ntls" for p in snap["places"]) > 200 and "Nghĩa trang liệt sĩ Trường Sơn" in names
    assert sum(1 for p in snap["places"] if not p["prov"]) < len(snap["places"]) * 0.02


def test_merge_wikipedia_fills_descriptions_and_adds_new():
    base = [
        {"src": "osm", "sid": "way/1", "name": "Chùa Vĩnh Nghiêm", "kind": "chua", "lat": 21.2, "lng": 106.3,
         "prov": "Bắc Ninh", "addr": "", "wd": "", "wp": ""},
        {"src": "osm", "sid": "way/2", "name": "Chùa Vĩnh Nghiêm", "kind": "chua", "lat": 10.79, "lng": 106.68,
         "prov": "Hồ Chí Minh", "addr": "", "wd": "", "wp": ""},
        {"src": "osm", "sid": "way/3", "name": "Chùa Dâu", "kind": "chua", "lat": 21.04, "lng": 106.12,
         "prov": "Bắc Ninh", "addr": "", "wd": "", "wp": ""},
    ]
    kinds = {"Chùa Vĩnh Nghiêm (Bắc Ninh)": "chua", "Chùa Dâu": "chua", "Bút Tháp": "chua", "Chùa Xa Lạ": "chua"}
    details = [
        {"title": "Chùa Vĩnh Nghiêm (Bắc Ninh)", "lat": None, "lng": None, "desc": "Thiền phái Trúc Lâm.",
         "url": "https://vi.wikipedia.org/wiki/A", "qid": "Q10", "pageid": 10, "img": ""},
        {"title": "Chùa Dâu", "lat": None, "lng": None, "desc": "Chùa cổ nhất.", "url": "https://vi.wikipedia.org/wiki/B",
         "qid": "", "pageid": 11, "img": ""},
        {"title": "Bút Tháp", "lat": 21.07, "lng": 106.03, "desc": "Chùa Ninh Phúc.", "url": "https://vi.wikipedia.org/wiki/C",
         "qid": "Q12", "pageid": 12, "img": "https://upload.wikimedia.org/wikipedia/commons/x.jpg"},
        {"title": "Chùa Xa Lạ", "lat": None, "lng": None, "desc": "Không ghép được.", "url": "u", "qid": "", "pageid": 13, "img": ""},
    ]
    wp = places.records_from_wikipedia(details, kinds, None)
    out = places.merge_wikipedia(base, wp)
    by = {r["sid"]: r for r in out}
    assert by["way/1"]["desc"] == "Thiền phái Trúc Lâm." and by["way/1"]["wd"] == "Q10"  # khớp tỉnh trong ngoặc
    assert not by["way/2"].get("desc")
    assert by["way/3"]["desc"] == "Chùa cổ nhất."  # tên duy nhất
    assert by["vi:12"]["kind"] == "chua" and by["vi:12"]["name"] == "Bút Tháp"  # có toạ độ, không trùng → thêm mới
    assert "vi:13" not in by  # không toạ độ, không ghép được → bỏ


def test_admin_place_list_edit_hide_and_create(admin_client, client, db):
    places.load(db, _snap())
    db.commit()
    kl = db.scalar(select(SacredPlace).where(SacredPlace.source_id == "node/9"))
    page = admin_client.get(f"{P}/admin/dia-diem?q=Kim").text
    assert "Đình Kim Liên" in page and "Chùa Trấn Quốc" not in page
    assert "Danh bạ đình chùa" in admin_client.get(f"{P}/admin").text
    form = {"csrf_token": admin_client.csrf, "name": "Đình Kim Liên", "kind": "dinh", "province": "Hà Nội",
            "address": "Phương Mai", "lat": "21.0071", "lng": "105.8381", "description": "Đình thờ Cao Sơn Đại Vương.",
            "status": "hidden"}
    r = admin_client.post(f"{P}/admin/dia-diem/{kl.id}", data=form, follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    kl = db.get(SacredPlace, kl.id)
    assert kl.edited and kl.status == "hidden" and kl.address == "Phương Mai"
    j = admin_client.get(f"{P}/ban-do/diem.json").json()
    assert all(pt[4] != "Đình Kim Liên" for pt in j["points"])
    # thêm điểm mới bằng tay
    r = admin_client.post(f"{P}/admin/dia-diem/moi", data={**form, "name": "Chùa Mới", "kind": "chua", "status": "active"},
                          follow_redirects=False)
    new_id = int(r.headers["location"].rsplit("/", 1)[-1])
    assert db.get(SacredPlace, new_id).source == "manual"
    # toạ độ ngoài Việt Nam, link không hợp lệ → 400
    assert admin_client.post(f"{P}/admin/dia-diem/moi", data={**form, "lat": "48.8"}).status_code == 400
    assert admin_client.post(f"{P}/admin/dia-diem/moi", data={**form, "website": "javascript:alert(1)"}).status_code == 400


def test_admin_place_pages_require_admin(user_client, db):
    assert user_client.get(f"{P}/admin/dia-diem", follow_redirects=False).status_code == 403


def test_seo_meta_jsonld_and_sitemap(client, db):
    import json as _json
    places.load(db, _snap())
    db.commit()
    tq = db.scalar(select(SacredPlace).where(SacredPlace.source_id == "way/2"))
    kl = db.scalar(select(SacredPlace).where(SacredPlace.source_id == "node/9"))
    html = client.get(f"{P}/dia-diem/{tq.id}").text
    assert '<meta name="description" content="Ngôi chùa cổ nhất Thăng Long.">' in html
    assert f'<link rel="canonical" href="http://testserver{P}/dia-diem/{tq.id}">' in html
    ld = _json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
    assert ld["@type"] == "BuddhistTemple" and ld["geo"]["latitude"] == 21.048
    assert ld["address"]["addressRegion"] == "Hà Nội" and "https://www.wikidata.org/wiki/Q2" in ld["sameAs"]
    html = client.get(f"{P}/dia-diem/{kl.id}").text
    assert "Đình Kim Liên – Hà Nội" in html and '"PlaceOfWorship"' in html
    kl.status = "hidden"
    db.commit()
    r = client.get(f"{P}/sitemap.xml")
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/xml")
    assert f"{P}/ban-do</loc>" in r.text and f"{P}/dia-diem/{tq.id}</loc>" in r.text
    assert f"/dia-diem/{kl.id}</loc>" not in r.text


def test_aliases_and_keywords_for_search():
    assert places.aliases_from_text("Đền Bảo Hà, còn được gọi là Đền Ông Hoàng Bảy, là một ngôi đền") == ["Đền Ông Hoàng Bảy"]
    assert places.aliases_from_text("Chùa Phi Tướng, còn gọi là chùa Tướng nằm ở tổ dân phố") == ["Chùa Tướng"]
    assert places.aliases_from_text("còn gọi là núi Lạn Kha") == []  # không phải tên nơi thờ
    recs = [{"name": "Đền Bảo Hà", "prov": "Lào Cai", "wd": "Q9", "wp": "Đền Bảo Hà (Lào Cai)",
             "desc": "Đền Bảo Hà, còn được gọi là Đền Ông Hoàng Bảy, nằm bên sông Hồng.",
             "alt": ["Đền Bảo Hà", "Bảo Hà Linh Từ"]}]
    assert places.finalize_aliases(recs, {"Q9": ["đền ông hoàng bảy", "Đền Quan Hoàng Bảy"]}) == 1
    assert recs[0]["alias"] == "Bảo Hà Linh Từ; Đền Ông Hoàng Bảy; Đền Quan Hoàng Bảy"  # bỏ trùng tên chính + trùng nhau
    assert places.apply_keywords(recs) == 1 and "ông Hoàng Bảy" in recs[0]["kw"]
    # bộ từ khoá soạn tay khớp được với snapshot thật
    snap = places.read_snapshot()
    thien_tru = next(p for p in snap["places"] if p["name"] == "Chùa Thiên Trù" and p["prov"] == "Hà Nội")
    assert "chùa Hương" in thien_tru["kw"]


def test_points_carry_aliases_keywords_and_admin_edits_them(admin_client, client, db):
    places.load(db, _snap(alias="Khai Quốc tự", kw="hồ Tây"))
    db.commit()
    pt = next(x for x in client.get(f"{P}/ban-do/diem.json").json()["points"] if x[4] == "Chùa Trấn Quốc")
    assert pt[7] == "Khai Quốc tự" and pt[9] == "hồ Tây" and "chua co nhat thang long" in pt[8]
    tq = db.scalar(select(SacredPlace).where(SacredPlace.source_id == "way/2"))
    assert "Còn gọi là: <b>Khai Quốc tự</b>" in client.get(f"{P}/dia-diem/{tq.id}").text
    form = {"csrf_token": admin_client.csrf, "name": tq.name, "kind": "chua", "province": "Hà Nội", "lat": "21.048",
            "lng": "105.837", "status": "active", "aliases": "Khai Quốc tự;\nAn Quốc tự", "keywords": "hồ Tây, cổ nhất"}
    assert admin_client.post(f"{P}/admin/dia-diem/{tq.id}", data=form, follow_redirects=False).status_code == 303
    db.expire_all()
    p = db.get(SacredPlace, tq.id)
    assert p.aliases == "Khai Quốc tự; An Quốc tự" and p.keywords == "hồ Tây, cổ nhất" and p.edited
    assert "Chùa Trấn Quốc" in admin_client.get(f"{P}/admin/dia-diem", params={"q": "An Quốc"}).text


def _cur(**over):
    c = {"name": "Đền Bảo Hà", "type": "Đền", "lat": 22.1585, "lng": 104.3415, "addr": "Xã Bảo Hà, huyện Bảo Yên",
         "phone": "0214 387 9328", "deity": "Ông Hoàng Đôi, Ông Hoàng Bảy", "groups": ["Ông Hoàng"],
         "intents": ["tai-loc"], "fest": "17-7 (âm lịch) hằng năm.", "prio": 1}
    c.update(over)
    return c


def test_curated_list_merges_into_precise_points_or_adds_new():
    osm = [{"src": "osm", "sid": "way/1", "name": "Đền Bảo Hà", "kind": "den", "lat": 22.1711, "lng": 104.3516,
            "prov": "Lào Cai", "addr": "", "phone": "", "web": "", "wd": "", "wp": ""},
           {"src": "osm", "sid": "way/2", "name": "Chùa Phố", "kind": "chua", "lat": 20.6466, "lng": 106.0516,
            "prov": "Hưng Yên", "addr": "", "phone": "", "web": "", "wd": "", "wp": ""},
           {"src": "osm", "sid": "node/3", "name": "Đền Thượng", "kind": "den", "lat": 21.30, "lng": 105.30,
            "prov": "Hà Nội", "addr": "", "phone": "", "web": "", "wd": "", "wp": ""}]
    cur = [_cur(),  # lệch 1,7 km, tên đặc trưng → ghép, giữ toạ độ OSM
           _cur(name="Đền Mẫu Phố Hiến", lat=20.6465, lng=106.0515, deity="Dương Quý Phi", groups=["Mẫu"], prio=2),
           _cur(name="Đền Thượng", lat=21.0612, lng=105.3644, deity="Đức Thánh Tản Viên", groups=["Đức Thánh"]),
           _cur(name="Đền Chợ Củi", lat=18.6185, lng=105.7025, deity="Ông Hoàng Mười")]
    geo = {"Đền Chợ Củi@18.6185,105.7025": {"lat": 18.62, "lng": 105.71}}
    st = places.merge_curated(osm, cur, None, geo)
    assert st == {"matched": 1, "geocoded": 1, "approx": 2}
    bh = osm[0]
    assert (bh["lat"], bh["deity"], bh["intents"], bh["prio"], bh["phone"]) == (22.1711, cur[0]["deity"], ["tai-loc"], 1, "0214 387 9328")
    assert "thờ Ông Hoàng" in bh["kw"] and "cầu tài lộc" in bh["kw"] and "Xã Bảo Hà" in bh["addr"]
    new = {r["name"]: r for r in osm[3:]}
    assert set(new) == {"Đền Mẫu Phố Hiến", "Đền Thượng", "Đền Chợ Củi"}  # không ghép đền vào chùa / tên chung ở xa
    assert new["Đền Chợ Củi"]["lat"] == 18.62 and not new["Đền Chợ Củi"]["approx"]
    assert new["Đền Thượng"]["approx"] and new["Đền Thượng"]["sid"].startswith("den-thuong@")
    assert "Tứ phủ" in new["Đền Mẫu Phố Hiến"]["kw"]


def test_place_page_shows_worship_info_and_intent_filter(client, db):
    places.load(db, _snap(deity="Ông Hoàng Bảy", groups=["Ông Hoàng"], intents=["tai-loc", "binh-an"],
                          fest="17-7 (âm lịch)", prio=1, approx=True))
    db.commit()
    tq = db.scalar(select(SacredPlace).where(SacredPlace.source_id == "way/2"))
    html = client.get(f"{P}/dia-diem/{tq.id}").text
    assert "Ông Hoàng Bảy" in html and "Tứ phủ" in html and "17-7 (âm lịch)" in html
    assert f"{P}/ban-do?cau=tai-loc" in html and "gần đúng" in html
    j = client.get(f"{P}/ban-do/diem.json").json()
    pt = next(x for x in j["points"] if x[0] == tq.id)
    assert pt[10] == "Ông Hoàng Bảy" and pt[11] == "tai-loc,binh-an" and pt[12] == 1
    assert j["intents"]["tai-loc"] == "Tài lộc"


def test_admin_edits_worship_info(admin_client, db):
    places.load(db, _snap())
    db.commit()
    tq = db.scalar(select(SacredPlace).where(SacredPlace.source_id == "way/2"))
    assert 'name="intents"' in admin_client.get(f"{P}/admin/dia-diem/{tq.id}").text
    form = {"csrf_token": admin_client.csrf, "name": tq.name, "kind": "chua", "province": "Hà Nội", "lat": "21.048",
            "lng": "105.837", "status": "active", "deity": "Phật", "deity_groups": "Phật",
            "intents": ["binh-an", "xyz"], "festival": "Rằm tháng Giêng", "priority": "2"}
    assert admin_client.post(f"{P}/admin/dia-diem/{tq.id}", data=form, follow_redirects=False).status_code == 303
    db.expire_all()
    p = db.get(SacredPlace, tq.id)
    assert (p.deity, p.intents, p.festival, p.priority, p.approx_location) == ("Phật", "binh-an", "Rằm tháng Giêng", 2, False)


def test_province_hint_from_old_address_and_real_curated_snapshot():
    assert places.province_hint("Thôn Bằng Sở, xã Ninh Sở, huyện Thường Tín") == "Hà Nội"
    assert places.province_hint("Tổ 8, phường Trần Phú, thành phố Hà Giang") == "Tuyên Quang"
    assert places.province_hint("Phố Xích Đằng") == ""
    cur = {p["name"]: p for p in places.read_snapshot()["places"] if p.get("deity")}
    assert len(cur) >= 100
    assert cur["Đền Sở"]["prov"] == "Hà Nội" and cur["Đền Sở"]["approx"]
    assert cur["Đền Bảo Hà"]["src"] == "osm" and not cur["Đền Bảo Hà"].get("approx")  # toạ độ OSM chính xác
    assert cur["Đền Bảo Hà"]["intents"] == ["tai-loc"] and cur["Đền Bảo Hà"]["prio"] == 1


def test_deity_notes_match_order_and_tu_phu_fallback():
    from app.places import deity_notes
    titles = [d["title"] for d in deity_notes("Thánh Mẫu Thoải cung và Đức Ông Lê Thọ Vực", "Mẫu")]
    assert titles == ["Thủy cung Thánh Mẫu", "Lê Thọ Vực"]
    assert [d["title"] for d in deity_notes("Chầu Bát", "Chầu")] == ["Bát Nàn"]
    assert [d["title"] for d in deity_notes("Quan lớn Đệ Bát", "Quan")] == ["Tứ phủ"]  # không có bài riêng
    assert deity_notes("Dương Quý Phi", "") == []  # bài trùng tên (phi tần nhà Đường) cố ý không gắn
    assert deity_notes("", "") == []


def test_classify_cemetery():
    from app.places import classify_cemetery
    g = {"landuse": "cemetery"}
    assert classify_cemetery("Nghĩa trang liệt sĩ Trường Sơn", g) == "ntls"
    assert classify_cemetery("Nghĩa Trang Liệt Sỹ xã Thái Bảo", {}) == "ntls"
    assert classify_cemetery("Đài tưởng niệm các Anh hùng liệt sĩ Đông Mỹ", {"historic": "monument"}) == "tuongniem"
    assert classify_cemetery("Nghĩa trang giáo xứ Bến Gỗ", g) == "ntrang"
    assert classify_cemetery("", g) == "ntrang"
    assert classify_cemetery("Lăng Khiêm Thọ", g) == "mo"
    assert classify_cemetery("Tượng đài Lê Thái Tổ", {"historic": "monument"}) is None
    assert classify_cemetery("Bảo tàng Chiến thắng B52", {}) is None  # bài Wikipedia lẫn trong thể loại


def test_records_from_cemeteries_names_unnamed_and_drops_duplicates():
    from app.places import SettlementIndex, records_from_cemeteries
    settle = SettlementIndex([{"lat": 21.001, "lon": 105.801, "tags": {"name": "Thôn Đông"}}])
    els = [
        {"type": "way", "id": 1, "center": {"lat": 21.0, "lon": 105.8}, "tags": {"landuse": "cemetery", "name": "Nghĩa trang liệt sĩ xã A"}},
        {"type": "way", "id": 2, "center": {"lat": 21.0005, "lon": 105.8}, "tags": {"landuse": "cemetery"}},  # trùng chỗ → bỏ
        {"type": "way", "id": 3, "center": {"lat": 21.02, "lon": 105.8}, "tags": {"landuse": "cemetery"}},
        {"type": "node", "id": 4, "lat": 21.0, "lon": 105.8, "tags": {"amenity": "place_of_worship", "name": "Lăng X"}},
    ]
    out = {r["sid"]: r for r in records_from_cemeteries(els, None, settle, skip_sids={"node/4"})}
    assert set(out) == {"way/1", "way/3"}
    assert out["way/1"]["kind"] == "ntls" and out["way/1"]["addr"] == "gần Thôn Đông"
    assert "liệt sỹ" in out["way/1"]["kw"]
    assert out["way/3"]["name"] == "Nghĩa trang gần Thôn Đông"


def test_knowledge_pages_render_and_link_from_places(client, db):
    from app.knowledge import ARTICLES, related
    html = client.get(f"{P}/kien-thuc").text
    assert all(a["title"] in html for a in ARTICLES) and f"{P}/kien-thuc" in client.get(f"{P}/ban-do").text
    for a in ARTICLES:
        r = client.get(f"{P}/kien-thuc/{a['slug']}")
        assert r.status_code == 200 and a["title"] in r.text and "Wikipedia" in r.text
    art = client.get(f"{P}/kien-thuc/dao-mau-tu-phu").text
    assert f"{P}/ban-do?q=ph%E1%BB%A7%20d%E1%BA%A7y" in art  # liên kết sang bản đồ có sẵn từ khoá
    assert client.get(f"{P}/kien-thuc/khong-co").status_code == 404
    assert f"{P}/kien-thuc/vieng-nghia-trang-liet-si" in client.get(f"{P}/sitemap.xml").text

    def place(**kw):
        return SacredPlace(**{"name": "X", "kind": "den", "deity": "", "deity_groups": "", "keywords": "", **kw})
    slugs = lambda p: [a["slug"] for a in related(p)]  # noqa: E731
    assert slugs(place(deity="Đức Thánh Trần và Tứ phủ", deity_groups="Quan")) == ["tho-duc-thanh-tran", "dao-mau-tu-phu", "di-le-co-ban"]
    assert slugs(place(kind="chua")) == ["di-le-chua", "di-le-co-ban"]
    assert slugs(place(kind="ntls")) == ["vieng-nghia-trang-liet-si"]

    places.load(db, _snap())
    db.commit()
    tq = db.scalar(select(SacredPlace).where(SacredPlace.source_id == "way/2"))
    assert f"{P}/kien-thuc/di-le-chua" in client.get(f"{P}/dia-diem/{tq.id}").text
