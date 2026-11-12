"""Tìm đền theo nhu cầu (cầu may mắn, tài lộc…) và sắp theo khoảng cách tới khách."""
import re

from sqlalchemy import select

from app.models import Temple
from app.routers.public import distance_km
from conftest import P

CAU_GIAY = {"lat": "21.0333", "lng": "105.7900"}


def _names(html: str) -> list[str]:
    return re.findall(r'<h3><a href="[^"]+">([^<]+)</a></h3>', html)


def test_filter_by_purpose(user_client, db):
    page = user_client.get(f"{P}/?nhu_cau=may-man", headers={"HX-Request": "true"}).text
    names = _names(page)
    lucky = [t.name for t in db.scalars(select(Temple)) if "may-man" in t.purpose_list]
    assert sorted(names) == sorted(lucky) and len(names) >= 6
    assert "Văn Miếu – Quốc Tử Giám" not in names  # chỉ cầu công danh
    assert f"Tìm thấy <b>{len(names)}</b> đền, chùa để cầu <b>may mắn</b>" in page


def test_unknown_purpose_ignored(user_client):
    page = user_client.get(f"{P}/?nhu_cau=xyz", headers={"HX-Request": "true"}).text
    assert "Văn Miếu" in page and "Ngọc Sơn" in page


def test_near_me_sorts_by_distance(user_client):
    page = user_client.get(f"{P}/", params={"nhu_cau": "may-man", **CAU_GIAY}, headers={"HX-Request": "true"}).text
    names = _names(page)
    assert names[-1] == "Miếu Bà Chúa Xứ Núi Sam"  # An Giang: xa nhất
    km = [float(x) for x in re.findall(r'cách ([\d.]+) km', page)]
    assert km == sorted(km) and len(km) == len(names)
    assert "maps/search/?api=1&query=21.0307,105.8524" in page  # chỉ đường tới Đền Ngọc Sơn


def test_bad_location_ignored(user_client):
    page = user_client.get(f"{P}/", params={"lat": "abc", "lng": "999"}, headers={"HX-Request": "true"}).text
    assert " km</b>" not in page and "Ngọc Sơn" in page


def test_search_matches_deity(user_client):
    names = _names(user_client.get(f"{P}/?q=Thánh Mẫu", headers={"HX-Request": "true"}).text)
    assert "Phủ Tây Hồ" in names and "Đền Ngọc Sơn" not in names


def test_distance_km():
    assert abs(distance_km(21.0307, 105.8524, 10.6806, 105.0806) - 1155) < 15  # Hà Nội → Châu Đốc
    assert distance_km(21, 105, 21, 105) == 0


def test_temple_page_shows_purposes_and_map(user_client):
    page = user_client.get(f"{P}/den/phu-tay-ho").text
    assert "Cầu may mắn" in page and "Cầu tài lộc" in page and "Xem bản đồ" in page


def test_admin_saves_purposes_and_coords(admin_client, db):
    c = admin_client
    t = db.scalar(select(Temple).where(Temple.slug == "chua-ha"))
    data = {"name": t.name, "address": t.address, "province": t.province, "deity": t.deity, "status": "active",
            "device_id": "", "slug": t.slug, "purposes": ["may-man", "tinh-duyen", "khong-co"],
            "lat": "21.04", "lng": "105.80", "csrf_token": c.csrf}
    assert c.post(f"{P}/admin/den/{t.id}", data=data, follow_redirects=False).status_code == 303
    db.expire_all()
    t = db.get(Temple, t.id)
    assert t.purposes == "may-man,tinh-duyen" and (t.lat, t.lng) == (21.04, 105.80)
    assert c.post(f"{P}/admin/den/{t.id}", data={**data, "lat": "200"}).status_code == 400
    assert c.post(f"{P}/admin/den/{t.id}", data={**data, "lat": "", "lng": ""}, follow_redirects=False).status_code == 303
    db.expire_all()
    assert db.get(Temple, t.id).lat is None


def test_serif_font_has_vietnamese_fallback():
    """Windows không có Noto Serif; Georgia vỡ dấu tiếng Việt ("Đề`n") → phải rơi về font đủ dấu."""
    from pathlib import Path
    css = (Path(__file__).resolve().parents[1] / "app" / "static" / "ld.css").read_text(encoding="utf-8")
    stacks = re.findall(r'font-family:\s*"Noto Serif",([^;]+);', css)
    assert stacks and all("Georgia" not in s and "Cambria" in s for s in stacks)
