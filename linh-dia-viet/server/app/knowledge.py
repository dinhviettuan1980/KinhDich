"""Tab "Kiến thức": bài cơ bản theo từng dòng thờ tự (đạo Mẫu, Đức Thánh Trần, chùa, đình, nghĩa trang liệt sĩ…).

Nội dung mỗi bài là một template Jinja `templates/kien_thuc/<slug>.html` (sửa chữ ở đó). Thêm bài: thêm một mục vào
ARTICLES + tạo template cùng tên. `related()` chọn bài liên quan để gợi ý trên trang chi tiết địa điểm.
"""
from .places import norm

ARTICLES = [
    {"slug": "di-le-co-ban", "title": "Đi lễ đền, chùa, phủ: những điều cơ bản",
     "short": "Phân biệt chùa, đền, phủ, đình, miếu; lễ chay, lễ mặn; thứ tự hành lễ, thắp hương, khấn, ứng xử."},
    {"slug": "dao-mau-tu-phu", "title": "Đạo Mẫu Tứ phủ",
     "short": "Tam tòa Thánh Mẫu, bốn phủ và màu sắc, thứ bậc các vị thánh, hầu đồng, ngày giỗ Mẫu, nơi thờ tiêu biểu."},
    {"slug": "tho-duc-thanh-tran", "title": "Thờ Đức Thánh Trần (Trần triều)",
     "short": "Trần Hưng Đạo và gia quyến được thờ, các đền chính, ngày giỗ tháng Tám, khai ấn đầu năm."},
    {"slug": "di-le-chua", "title": "Đi lễ chùa",
     "short": "Chùa thờ những ai, thứ tự lễ, lễ chay, các ngày lễ Phật giáo lớn, cầu an, cầu siêu, ứng xử trong chùa."},
    {"slug": "dinh-lang-thanh-hoang", "title": "Đình làng và Thành hoàng",
     "short": "Đình thờ ai, các loại Thành hoàng, hội làng, lễ ở đình."},
    {"slug": "vieng-nghia-trang-liet-si", "title": "Viếng nghĩa trang liệt sĩ, tảo mộ",
     "short": "Ngày 27/7, thứ tự viếng, sắm lễ, ứng xử, cách hỏi tìm mộ liệt sĩ; tảo mộ tiết Thanh minh."},
]
BY_SLUG = {a["slug"]: a for a in ARTICLES}
_TU_PHU = {"mẫu", "quan", "chầu", "cô", "cậu", "ông hoàng"}


def related(place) -> list[dict]:
    """Bài nên đọc khi xem một địa điểm (theo loại, hàng thánh, vị thờ chính)."""
    deity, groups = norm(place.deity or ""), {g.strip().lower() for g in (place.deity_groups or "").split(",")}
    text = f" {deity} {norm(place.keywords or '')} {norm(place.name)} "
    slugs = []
    if " tran hung dao " in text or " duc thanh tran " in text or " tran trieu " in text:
        slugs.append("tho-duc-thanh-tran")
    if groups & _TU_PHU or " mau " in f" {deity} " or place.kind == "phu":
        slugs.append("dao-mau-tu-phu")
    slugs += {"chua": ["di-le-chua"], "dinh": ["dinh-lang-thanh-hoang"],
              "ntls": ["vieng-nghia-trang-liet-si"], "tuongniem": ["vieng-nghia-trang-liet-si"],
              "ntrang": ["vieng-nghia-trang-liet-si"]}.get(place.kind, [])
    if not place.is_cemetery:
        slugs.append("di-le-co-ban")
    return [BY_SLUG[s] for s in dict.fromkeys(slugs)]
