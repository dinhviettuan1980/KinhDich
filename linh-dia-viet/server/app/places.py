"""Danh bạ đình chùa toàn quốc cho bản đồ.

Nguồn (được phép lưu, nhớ ghi nguồn khi hiển thị):
- OpenStreetMap qua Overpass: `amenity=place_of_worship` + các điểm tên "Chùa/Đình/Đền/Miếu…" (ODbL).
- Wikidata: các di tích có toạ độ (CC0); thêm ảnh Wikimedia Commons và link Wikipedia tiếng Việt.
- Wikipedia tiếng Việt: đoạn tóm tắt làm mô tả (CC BY-SA 4.0, lưu URL bài gốc).
KHÔNG lấy dữ liệu Places của Google để lưu (điều khoản Google Maps Platform cấm).

Hai bước, tách riêng để server production không phải gọi Overpass:
    python -m app.places build [--out FILE] [--cache DIR]   # tải + xử lý → snapshot .json.gz (commit vào repo)
    python -m app.places load [FILE]                        # nạp snapshot vào DB (seed tự gọi khi snapshot đổi)
"""
import argparse
import gzip
import json
import logging
import math
import re
import time
import unicodedata
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import BASE_DIR
from .models import CEMETERY_KINDS, PLACE_INTENTS, PLACE_KINDS, SacredPlace, Setting, Temple

log = logging.getLogger(__name__)

SNAPSHOT = BASE_DIR / "data" / "places_vn.json.gz"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
WDQS_URL = "https://query.wikidata.org/sparql"
WIKI_API = "https://vi.wikipedia.org/w/api.php"
USER_AGENT = "linh-dia-viet-import/1.0 (directory import; contact via project admin)"

_PREFIX = r"Chùa|Đình|Đền|Miếu|Miễu|Phủ|Nghè|Tịnh xá|Thiền viện|Tu viện|Niệm Phật đường|Lăng|Am|Điện"
OVERPASS_PLACES = f"""[out:json][timeout:300];
area["ISO3166-1"="VN"][admin_level=2]->.vn;
(nwr["amenity"="place_of_worship"](area.vn);
 nwr["name"~"^({_PREFIX.replace('|Lăng|Am|Điện', '')}) "][!highway][!shop][!office][!power][!railway]
    ["amenity"!="place_of_worship"](area.vn););
out center tags;"""
OVERPASS_PROVINCES = """[out:json][timeout:300];
area["ISO3166-1"="VN"][admin_level=2]->.vn;
rel(area.vn)[boundary=administrative][admin_level=4];
out geom;"""
WIKIDATA_QUERY = """SELECT ?item ?label ?coord ?article ?image WHERE {
  ?item wdt:P17 wd:Q881; wdt:P625 ?coord; rdfs:label ?label.
  FILTER(lang(?label)="vi" && REGEX(?label, "^(Chùa|Đình|Đền|Miếu|Phủ|Nghè|Tịnh xá|Thiền viện) "))
  OPTIONAL { ?article schema:about ?item; schema:isPartOf <https://vi.wikipedia.org/> }
  OPTIONAL { ?item wdt:P18 ?image }
}"""

# Danh bạ này phục vụ lễ đền chùa (Phật giáo + tín ngưỡng dân gian) → bỏ nhà thờ, thánh thất, thánh đường…
EXCLUDED_RELIGIONS = {"christian", "muslim", "hindu", "caodaism", "jewish", "sikh", "bahai", "hoahao", "mormon"}
EXCLUDED_NAME = re.compile(r"^(nhà thờ|nha tho|giáo xứ|giáo họ|giáo điểm|thánh đường|nhà nguyện|hội thánh|thánh thất|"
                           r"tin lành|masjid|mosque|điện máy|điện lực|điện biên|ubnd|ủy ban|ban trị sự|nhà bia|"
                           r"nghĩa trang|nghĩa địa|đài tưởng niệm|tượng đài|mộ |tháp mộ|nhà truyền thống|tiểu chủng viện|chủng viện|đền thánh|đức mẹ)"
                           r"|\b(church|chapel|cathedral|cao ?đài|cao dai|mosque|basilica|église|iglesia)\b", re.I)
_KIND_BY_PREFIX = [
    (r"chùa|tịnh xá|thiền viện|tu viện|niệm phật đường|am|pagoda", "chua"),
    (r"đình", "dinh"),
    (r"đền|nghè|lăng|temple", "den"),
    (r"miếu|miễu", "mieu"),
    (r"phủ|điện", "phu"),
]
_KIND_LOOSE = [
    (r"^(chua|tinh xa|thien vien)\b|\b(pagoda|tu|co tu|monastery)$", "chua"),
    (r"^dinh\b|\bdinh than\b", "dinh"),
    (r"^(den|lang ong)\b|\b(temple|shrine)$", "den"),
    (r"^mieu\b|\bmieu$|\bhoi quan\b", "mieu"),
]
_KIND_BY_RELIGION = {"buddhist": "chua", "vietnamese_folk": "den", "chinese_folk": "mieu", "taoist": "den"}


def norm(text: str) -> str:
    """Chuẩn hoá để so khớp: bỏ dấu, chữ thường, gộp khoảng trắng."""
    text = (text or "").replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def classify(name: str, religion: str = "", is_worship: bool = True) -> str | None:
    """Trả về loại địa điểm, hoặc None nếu không đưa vào danh bạ."""
    name = (name or "").strip()
    if not name or religion in EXCLUDED_RELIGIONS or EXCLUDED_NAME.search(name):
        return None
    low = name.lower()
    for pattern, kind in _KIND_BY_PREFIX:
        if re.match(rf"({pattern})\b", low):
            if not is_worship and kind == "phu" and low.startswith("điện"):
                return None  # "Điện …" không gắn tag thờ tự thường là cửa hàng/công trình điện
            if not is_worship and low.startswith(("am ", "lăng ")):
                return None
            return kind
    if not is_worship:
        return None
    # Tên không dấu / tiếng Anh / Hán Việt: "Chua Hung Long", "Tam Buu Pagoda", "An Hòa Tự", "Hải Nam Cổ Miếu"
    plain = norm(name)
    for pattern, kind in _KIND_LOOSE:
        if re.search(pattern, plain):
            return kind
    # Không nhận ra loại → bỏ: tag thờ tự trên OSM hay bị gắn nhầm (công ty, nhà văn hoá, cửa hàng…)
    return _KIND_BY_RELIGION.get(religion)


def province_name(raw: str) -> str:
    return re.sub(r"^(Tỉnh|Thành phố)\s+", "", (raw or "").strip())


class ProvinceIndex:
    """Tìm tỉnh chứa một điểm: ray casting chẵn-lẻ trên mọi đoạn biên của quan hệ ranh giới.
    Không cần ghép các way thành vòng kín: tập đoạn biên của một vùng vốn đã khép kín."""
    BAND = 20  # 1/20 độ vĩ ≈ 5,5 km mỗi dải

    def __init__(self, relations: list[dict]):
        self.items = []
        for rel in relations:
            segs = []
            for m in rel.get("members", []):
                if m.get("type") != "way" or m.get("role") not in ("outer", "inner", ""):
                    continue
                g = m.get("geometry") or []
                segs.extend((a["lon"], a["lat"], b["lon"], b["lat"]) for a, b in zip(g, g[1:]))
            if not segs:
                continue
            bands: dict[int, list] = {}
            for s in segs:
                lo, hi = sorted((s[1], s[3]))
                for k in range(math.floor(lo * self.BAND), math.floor(hi * self.BAND) + 1):
                    bands.setdefault(k, []).append(s)
            xs = [c for s in segs for c in (s[0], s[2])]
            ys = [c for s in segs for c in (s[1], s[3])]
            self.items.append((province_name(rel.get("tags", {}).get("name", "")),
                               (min(xs), min(ys), max(xs), max(ys)), bands))

    def lookup(self, lat: float, lng: float) -> str:
        for name, (x0, y0, x1, y1), bands in self.items:
            if not (x0 <= lng <= x1 and y0 <= lat <= y1):
                continue
            inside = False
            for ax, ay, bx, by in bands.get(math.floor(lat * self.BAND), ()):
                if (ay > lat) != (by > lat) and lng < ax + (lat - ay) * (bx - ax) / (by - ay):
                    inside = not inside
            if inside:
                return name
        return ""


def _osm_address(t: dict) -> str:
    parts = [" ".join(p for p in (t.get("addr:housenumber"), t.get("addr:street")) if p),
             t.get("addr:hamlet"), t.get("addr:village") or t.get("addr:quarter"), t.get("addr:subdistrict"),
             t.get("addr:district"), t.get("addr:city")]
    seen, out = set(), []
    for p in parts:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return ", ".join(out) or t.get("addr:full", "")


def _commons_thumb(url: str, width: int = 640) -> str:
    """URL Special:FilePath của Commons → ảnh thu nhỏ (Commons tự chuyển hướng tới bản đúng kích thước)."""
    if not url:
        return ""
    name = unquote(url.rsplit("/", 1)[-1])
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(name)}?width={width}"


def records_from_osm(elements: list[dict], provinces: ProvinceIndex | None) -> list[dict]:
    out = []
    for e in elements:
        t = e.get("tags") or {}
        name = (t.get("name:vi") or t.get("name") or "").strip()
        is_worship = t.get("amenity") == "place_of_worship"
        kind = classify(name, t.get("religion", ""), is_worship)
        if kind is None:
            continue
        lat, lng = (e["lat"], e["lon"]) if "lat" in e else (e.get("center", {}).get("lat"), e.get("center", {}).get("lon"))
        if lat is None:
            continue
        wp = t.get("wikipedia", "")
        out.append({
            "src": "osm", "sid": f"{e['type']}/{e['id']}", "name": name[:200], "kind": kind,
            "rel": t.get("religion", "")[:30], "lat": round(lat, 6), "lng": round(lng, 6),
            "prov": (provinces.lookup(lat, lng) if provinces else "") or province_name(t.get("addr:province", "")),
            "addr": _osm_address(t)[:300], "phone": (t.get("phone") or t.get("contact:phone") or "")[:60],
            "web": (t.get("website") or t.get("contact:website") or "")[:300],
            "wd": t.get("wikidata", ""), "wp": wp[3:] if wp.startswith("vi:") else "",
            "alt": [a.strip() for k in OSM_ALIAS_TAGS for a in (t.get(k) or "").split(";") if a.strip()],
        })
    return out


def records_from_wikidata(bindings: list[dict], provinces: ProvinceIndex | None) -> list[dict]:
    items: dict[str, dict] = {}
    for b in bindings:
        qid = b["item"]["value"].rsplit("/", 1)[-1]
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", b["coord"]["value"])
        name = b["label"]["value"].strip()
        kind = classify(name)
        if not m or kind is None or qid in items:
            continue
        lng, lat = float(m.group(1)), float(m.group(2))
        article = b.get("article", {}).get("value", "")
        items[qid] = {
            "src": "wikidata", "sid": qid, "name": name[:200], "kind": kind, "rel": "",
            "lat": round(lat, 6), "lng": round(lng, 6), "prov": provinces.lookup(lat, lng) if provinces else "",
            "addr": "", "phone": "", "web": "", "wd": qid,
            "wp": unquote(article.rsplit("/wiki/", 1)[-1]).replace("_", " ") if article else "",
            "img": _commons_thumb(b.get("image", {}).get("value", "")),
        }
    return list(items.values())


def _km(a: dict, b: dict) -> float:
    dlat = math.radians(b["lat"] - a["lat"])
    dlng = math.radians(b["lng"] - a["lng"]) * math.cos(math.radians(a["lat"]))
    return 6371 * math.hypot(dlat, dlng)


def dedupe(records: list[dict], radius_km: float = 0.3) -> list[dict]:
    """OSM hay vẽ một nơi hai lần (node + way): cùng tên (bỏ dấu) trong bán kính `radius_km` → giữ bản nhiều thông tin hơn."""
    def score(r):
        return (bool(r["wd"]), bool(r["wp"]), bool(r["addr"]), r["sid"].startswith(("way", "relation")))
    kept: list[dict] = []
    by_name: dict[str, list[dict]] = {}
    for r in sorted(records, key=score, reverse=True):
        group = by_name.setdefault(norm(r["name"]), [])
        twin = next((k for k in group if _km(k, r) <= radius_km), None)
        if twin is None:
            group.append(r)
            kept.append(r)
            continue
        for key in ("addr", "phone", "web", "wd", "wp"):
            twin[key] = twin[key] or r[key]
        _add_alt(twin, r.get("alt", []), r["name"])
    return kept


def merge(osm: list[dict], wd: list[dict], radius_km: float = 0.6) -> list[dict]:
    """Gộp Wikidata vào OSM: trùng QID, hoặc cùng tên (bỏ dấu) trong bán kính `radius_km`.
    Không trùng thì giữ bản ghi Wikidata riêng (OSM hay thiếu các di tích lớn, vd Đền Ngọc Sơn)."""
    by_qid = {r["wd"]: r for r in osm if r["wd"]}
    by_name: dict[str, list[dict]] = {}
    for r in osm:
        by_name.setdefault(norm(r["name"]), []).append(r)
    extra = []
    for w in wd:
        target = by_qid.get(w["sid"]) or next(
            (r for r in by_name.get(norm(w["name"]), []) if _km(r, w) <= radius_km), None)
        if target is None:
            extra.append(w)
            continue
        target["wd"] = target["wd"] or w["sid"]
        target["wp"] = target["wp"] or w["wp"]
        target["img"] = target.get("img") or w.get("img", "")
        _add_alt(target, w["name"])  # cùng QID nhưng Wikidata đặt tên khác (vd tên chữ Hán)
    return osm + extra


OSM_ALIAS_TAGS = ("alt_name:vi", "alt_name", "old_name:vi", "old_name", "official_name:vi", "official_name",
                  "loc_name", "short_name")
# "Đền Bảo Hà, còn được gọi là Đền Ông Hoàng Bảy, …" → "Đền Ông Hoàng Bảy"
_ALIAS_CUE = re.compile(
    r"(?:còn (?:được )?(?:gọi|biết đến|có tên(?: (?:chữ|nôm|gọi))?(?: Hán)?)(?: là| với (?:cái )?tên(?: gọi)?(?: là)?)?"
    r"|hay (?:còn )?(?:được )?gọi là|tên (?:gọi )?khác là|tên (?:chữ(?: Hán)?|nôm|dân gian|cũ) là"
    r"|(?:thường|dân gian|người dân|nhân dân) (?:vẫn |hay )?(?:được )?gọi là|quen gọi là)\s+"
    r"(.+?)(?=[,.;:()\"“”\[\]]|\s(?:là|nằm|ở|tọa|toạ|thuộc|được|có|tại|trên|do|vì|với|từ|thờ|xây)\s|$)",
    re.I)
_KIND_WORDS = ("chùa", "đền", "đình", "miếu", "phủ", "điện", "am", "nghè", "quán", "từ")


def aliases_from_text(text: str) -> list[str]:
    out = []
    for m in _ALIAS_CUE.finditer(text or ""):
        for part in re.split(r"\s+(?:hay|hoặc|và)\s+", m.group(1)):
            a = part.strip(" '\"‘’“”")
            first = a.split(" ", 1)[0]
            if not a or not 1 <= len(a.split()) <= 6:
                continue
            if first[:1].islower():  # chỉ nhận tên riêng, hoặc "chùa X"/"đền X" viết thường
                if first.lower() not in _KIND_WORDS or len(a.split()) < 2:
                    continue
                a = a[0].upper() + a[1:]
            out.append(a)
    return out


def _add_alt(rec: dict, *names) -> None:
    alt = rec.setdefault("alt", [])
    for n in names:
        alt.extend([n] if isinstance(n, str) else n)


def finalize_aliases(records: list[dict], wd_aliases: dict[str, list[str]] | None = None, limit: int = 6) -> int:
    """Gom tên gọi khác (tag OSM, alias Wikidata, tên bài Wikipedia, "còn gọi là …" trong mô tả) → `alias`
    (chuỗi "; "), bỏ trùng (không dấu) với tên chính và giữa chúng. Trả về số điểm có tên khác."""
    n = 0
    for r in records:
        cands = list(r.pop("alt", []))
        cands += (wd_aliases or {}).get(r.get("wd") or "", [])
        if r.get("wp"):
            cands.append(re.sub(r"\s*\(.*\)\s*$", "", r["wp"]))
        cands += aliases_from_text(r.get("desc", ""))
        name_key, pos, keep = norm(r["name"]), {}, []
        for a in cands:
            a = re.sub(r"\s+", " ", a).strip()[:80]
            k = norm(a)
            if len(k) < 3 or k == name_key or EXCLUDED_NAME.search(a):
                continue
            if k in pos:  # trùng: giữ bản viết hoa chuẩn ("Đền Ông Hoàng Bảy" thay "đền ông hoàng bảy")
                if keep[pos[k]] == keep[pos[k]].lower() and a != a.lower():
                    keep[pos[k]] = a
                continue
            pos[k] = len(keep)
            keep.append(a)
        r["alias"] = "; ".join(keep[:limit])
        n += bool(keep)
    return n


CURATED_FILE = BASE_DIR / "data" / "places_curated.json"
INTENT_LABELS = PLACE_INTENTS
_LEAD = re.compile(r"^(?:quan the di tich |khu di tich |den tho |den |phu |chua |mieu |dinh |dong |lang |mo |dien )+")
# phần tên quá chung (nhiều nơi trùng) → chỉ ghép khi rất gần
GENERIC_CORES = {"thuong", "ha", "trung", "mau", "cam", "co doi", "doi co", "quan giam sat", "chua ba", "co tam",
                 "thuong ngan", "tho", "lang", "hang", "ong", "ba"}
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def _core(name: str) -> str:
    """Phần riêng của tên: bỏ ngoặc và tiền tố loại ("Đền Mẫu (Cấm Sơn Linh Từ)" → "mau")."""
    return _LEAD.sub("", norm(re.sub(r"\(.*?\)|“.*?”|\".*?\"", " ", name))).strip()


def _inner_names(name: str) -> list[str]:
    """Tên trong ngoặc/ngoặc kép: "Đền Dâu (Tang Dã Linh Từ)" → ["Tang Dã Linh Từ"]."""
    return [part.strip() for groups in re.findall(r"\((.*?)\)|“(.*?)”", name) for part in groups if part.strip()]


_GENERIC_WORDS = {"den", "phu", "chua", "mieu", "dinh", "dong", "lang", "mo", "dien", "mau", "tho", "quan", "the", "di",
                  "tich", "khu", "linh", "tu", "chinh"}
_KIND_TITLE = re.compile(r"^(đền|phủ|chùa|miếu|đình|điện|lăng|động|quần thể|khu di tích|am|nghè)\b", re.I)


def _core_acc(name: str) -> str:
    """Như _core nhưng giữ dấu: "Đền Sở" → "sở" (≠ "Đình So")."""
    t = re.sub(r"\(.*?\)|“.*?”", " ", name).lower().strip()
    t = re.sub(r"^(?:(?:quần thể di tích|khu di tích|đền thờ|đền|phủ|chùa|miếu|đình|động|lăng|mộ|điện)\s+)+", "", t)
    return re.sub(r"\s+", " ", t).strip()


def _word_set(name: str) -> frozenset:
    return frozenset(w for w in norm(re.sub(r"\(.*?\)|“.*?”", " ", name)).split() if w not in _GENERIC_WORDS)


def _names_match(a: str, b: str, km: float) -> bool:
    if not a or not b:
        return False
    if a == b:  # tên ngắn ("đầm", "sở") hay chung chung → chỉ khi rất gần; tên đặc trưng → trong 30 km
        return km <= (3 if a in GENERIC_CORES or len(a) < 6 else 30)
    short = min(len(a), len(b))
    if a in b or b in a:
        if short >= 7 and min(a, b, key=len) not in GENERIC_CORES:
            return km <= 10
        return short >= 3 and km <= 1
    return False


def curated_match(c: dict, records: list[dict]) -> dict | None:
    """Điểm sẵn có (OSM/Wikidata/Wikipedia) ứng với một nơi trong danh sách biên soạn; gần nhất trong số khớp tên."""
    cnames = [c["name"], *_inner_names(c["name"])]
    best = None
    for r in records:
        # đền/phủ không ghép vào chùa, đình; miếu chỉ khi tên riêng đủ dài
        if r.get("lat") is None or r["kind"] in ("chua", "dinh", *CEMETERY_KINDS) or r.get("_cur"):
            continue
        km = _km(r, c)
        if km > 30:
            continue
        rnames = [r["name"], *r.get("alt", [])]
        ok = False
        for cn in cnames:
            for rn in rnames:
                a, b = _core(cn), _core(rn)
                if r["kind"] == "mieu" and min(len(a), len(b)) < 6:
                    continue
                if a == b and len(a) < 5 and _core_acc(cn) != _core_acc(rn):
                    continue  # "Sở" ≠ "So": tên ngắn phải khớp cả dấu
                ok = ok or _names_match(a, b, km)
        if ok and (best is None or km < best[0]):
            best = (km, r)
    return best[1] if best else None


def geocode_curated(items: list[dict], client, delay: float = 1.1) -> dict[str, dict]:
    """Nominatim (OSM) cho nơi chưa ghép được: tên + địa chỉ cũ, chỉ nhận kết quả cùng tên, cách toạ độ gốc ≤ 30 km.
    Tôn trọng giới hạn 1 yêu cầu/giây của Nominatim; kết quả cache theo tên."""
    out = {}
    for c in items:
        hits = []
        for q in (f"{c['name']}, {c['addr']}", re.sub(r"\s*\(.*?\)", "", c["name"]) + ", Việt Nam"):
            r = _retry(lambda: client.get(NOMINATIM_URL, params={"q": q, "format": "jsonv2", "countrycodes": "vn",
                                                                  "limit": 5, "accept-language": "vi"}))
            time.sleep(delay)
            if r.status_code == 200:
                hits = r.json()
            if hits:
                break
        key = f"{c['name']}@{c['lat']},{c['lng']}"
        for h in hits:
            lat, lng = float(h["lat"]), float(h["lon"])
            hname = h.get("name") or h.get("display_name", "").split(",")[0]
            km = _km({"lat": lat, "lng": lng}, c)
            if km <= 30 and any(_names_match(k, _core(hname), min(km, 2.9))
                                for k in {_core(c["name"])} | {_core(x) for x in _inner_names(c["name"])}):
                out[key] = {"lat": round(lat, 6), "lng": round(lng, 6), "name": hname, "km": round(km, 2),
                            "osm": f"{h.get('osm_type', '')}/{h.get('osm_id', '')}"}
                break
    return out


# Huyện/thị xã/thành phố cũ (trước sáp nhập 2025, vẫn dùng trong địa chỉ quen gọi) → tỉnh mới. Dùng cho điểm có toạ độ
# gần đúng: toạ độ lệch có thể rơi sang tỉnh bên cạnh, còn địa chỉ thì đúng.
OLD_DISTRICT_PROVINCE = {
    "Hà Nội": ["Thường Tín", "Ba Vì", "Sơn Tây", "Long Biên", "Tây Hồ"],
    "Lạng Sơn": ["Hữu Lũng", "Chi Lăng", "Cao Lộc", "thành phố Lạng Sơn"],
    "Ninh Bình": ["Nho Quan", "Tam Điệp", "Vụ Bản", "Ý Yên", "Mỹ Lộc", "Duy Tiên", "Lý Nhân", "thành phố Nam Định"],
    "Phú Thọ": ["Cao Phong", "Đà Bắc", "Lâm Thao", "Tam Đảo"],
    "Hưng Yên": ["Quỳnh Phụ", "Tiền Hải", "Hưng Hà", "Ân Thi", "Tiên Lữ", "thành phố Hưng Yên", "Thái Bình"],
    "Hải Phòng": ["Chí Linh", "Ninh Giang", "Vĩnh Bảo", "Đồ Sơn", "Ngô Quyền"],
    "Bắc Ninh": ["Lục Nam", "Yên Thế"],
    "Thanh Hóa": ["Hà Trung", "Hậu Lộc", "Thạch Thành", "Bỉm Sơn"],
    "Hà Tĩnh": ["Nghi Xuân", "Hồng Lĩnh"],
    "Nghệ An": ["Quỳnh Lưu", "Hoàng Mai", "Hưng Nguyên"],
    "Lào Cai": ["Bảo Yên", "Văn Bàn", "Văn Yên", "thành phố Yên Bái", "thành phố Lào Cai"],
    "Tuyên Quang": ["Yên Sơn", "Hàm Yên", "Vị Xuyên", "thành phố Hà Giang", "thành phố Tuyên Quang"],
    "Quảng Trị": ["Quảng Trạch"],
    "Thái Nguyên": ["thành phố Thái Nguyên"],
}
_DISTRICT_RX = [(prov, re.compile(r"(?:huyện|thị xã|quận|thành phố|tỉnh)?\s*" + re.escape(d) + r"\b", re.I))
                for prov, ds in OLD_DISTRICT_PROVINCE.items() for d in ds]


def province_hint(addr: str) -> str:
    """Tỉnh mới suy từ địa chỉ cũ ("…, huyện Thường Tín" → "Hà Nội"); "" nếu không nhận ra."""
    for prov, rx in _DISTRICT_RX:
        if rx.search(addr or ""):
            return prov
    return ""


def merge_curated(records: list[dict], cur: list[dict], provinces, geo: dict[str, dict]) -> dict:
    """Danh sách đền phủ tiêu biểu (places_curated.json) → bổ sung vào điểm sẵn có (giữ toạ độ OSM chính xác),
    hoặc thêm điểm mới (toạ độ Nominatim nếu tìm thấy, không thì toạ độ gốc + đánh dấu gần đúng)."""
    st = {"matched": 0, "geocoded": 0, "approx": 0}
    for c in cur:
        kind = "phu" if c["type"] == "Phủ" or norm(c["name"]).startswith("phu ") else "den"
        target = curated_match(c, records)
        if target is None:
            g = geo.get(f"{c['name']}@{c['lat']},{c['lng']}")
            lat, lng = (g["lat"], g["lng"]) if g else (c["lat"], c["lng"])
            target = {"src": "ldv", "sid": f"{norm(c['name']).replace(' ', '-')}@{c['lat']:.3f},{c['lng']:.3f}",
                      "name": c["name"], "kind": kind, "rel": "", "lat": lat, "lng": lng,
                      "prov": (not g and province_hint(c["addr"])) or (provinces.lookup(lat, lng) if provinces else ""),
                      "addr": c["addr"], "phone": "",
                      "web": "", "wd": "", "wp": "", "approx": not g}
            records.append(target)
            st["geocoded" if g else "approx"] += 1
        else:
            st["matched"] += 1
            tc = _core(target["name"])
            if target["name"] != c["name"] and (tc == _core(c["name"]) or tc in GENERIC_CORES):
                _add_alt(target, target["name"])
                target["name"] = c["name"]  # "Đền dâu"/"Đền Mẫu" (OSM) → tên chuẩn trong danh sách
            if not target.get("addr"):
                target["addr"] = c["addr"]
            _add_alt(target, c["name"])
        target["_cur"] = True
        _add_alt(target, _inner_names(c["name"]))
        target["phone"] = target.get("phone") or c["phone"]
        target.update(deity=c["deity"], groups=c["groups"], intents=c["intents"], fest=c["fest"], prio=c["prio"])
        extra = [c["deity"], *(f"thờ {g}" for g in c["groups"]), *(f"cầu {INTENT_LABELS[i].lower()}" for i in c["intents"])]
        if set(c["groups"]) & {"Mẫu", "Quan", "Chầu", "Cô", "Cậu", "Ông Hoàng"}:
            extra += ["Tứ phủ", "đạo Mẫu", "hầu đồng"]
        if target.get("addr") != c["addr"]:
            extra.append(c["addr"])  # địa chỉ cũ (huyện, tỉnh trước sáp nhập) để tìm theo thói quen
        target["kw"] = ", ".join(x for x in (target.get("kw", ""), *extra) if x)
    for r in records:
        r.pop("_cur", None)
    return st


def wiki_search_titles(queries: dict[str, str], client, delay: float = 1.0) -> dict[str, list[str]]:
    """Tìm bài vi.wikipedia cho từng nơi (khoá → câu tìm) → tối đa 3 tiêu đề/nơi."""
    out = {}
    for key, q in queries.items():
        def go():
            r = client.get(WIKI_API, params={"action": "query", "format": "json", "formatversion": "2", "list": "search",
                                             "srsearch": q, "srlimit": "3", "srnamespace": "0"})
            r.raise_for_status()
            return r.json()["query"]["search"]
        try:
            out[key] = [h["title"] for h in _retry(go, wait=10)]
        except Exception as exc:
            log.warning("Tìm Wikipedia %s: %s", q, exc)
        time.sleep(delay)
    return out


def _wiki_accept(r: dict, d: dict, place_names: list[str], hints: list[str]) -> bool:
    """Bài Wikipedia đúng là nơi này: tiêu đề là tên một nơi thờ (Đền/Phủ/…), phần tên riêng trùng khít (bỏ chữ chung
    như "Mẫu", "Phủ"), không phải trang định hướng; và toạ độ ≤ 15 km hoặc (không toạ độ) bài nhắc tỉnh/huyện."""
    title = re.sub(r"\s*\(.*\)\s*$", "", d["title"])
    if not _KIND_TITLE.match(title) or re.search(r"có thể (?:đề cập|là|chỉ)", d["desc"][:200]):
        return False
    tw = _word_set(title)
    if not tw or not any(_word_set(n) == tw for n in place_names):
        return False
    km = _km(r, d) if d.get("lat") is not None else None
    if km is not None:
        return km <= 15
    text = norm(d["desc"][:1500])
    return any(h and norm(h) in text for h in hints)


def attach_wikipedia_to_curated(records: list[dict], client, cache: Path | None) -> int:
    """Mô tả Wikipedia cho các nơi trong danh sách biên soạn chưa có mô tả."""
    todo = [r for r in records if r.get("deity") and not r.get("desc")]
    queries = {r["sid"]: f'{re.sub(r"[(“].*?[)”]", " ", r["name"]).strip()} {r["prov"]}' for r in todo}
    found = _cached_json(cache, "wiki_curated_search.json", lambda: wiki_search_titles(queries, client))
    titles = sorted({t for ts in found.values() for t in ts})
    details = {d["title"]: d for d in _cached_json(cache, "wiki_curated_pages.json",
                                                   lambda: wiki_page_details(titles, client))}
    n = 0
    for r in todo:
        names = [r["name"], *r.get("alt", []), *_inner_names(r["name"])]
        hints = [r["prov"], *re.findall(r"(?:huyện|thị xã|thành phố|quận|xã|phường)\s+([^,.]+)", r.get("addr", ""), re.I)]
        for t in found.get(r["sid"], []):
            d = details.get(t)
            if d and d["desc"] and _wiki_accept(r, d, names, hints):
                r["desc"], r["desc_src"], r["wp"] = d["desc"], d["url"], d["title"]
                r["img"] = r.get("img") or d["img"]
                r["wd"] = r.get("wd") or d["qid"]
                n += 1
                break
    return n


DEITIES_FILE = BASE_DIR / "data" / "deities.json"
TU_PHU_GROUPS = {"Mẫu", "Quan", "Chầu", "Cô", "Cậu", "Ông Hoàng"}


@lru_cache
def _deities() -> list[dict]:
    if not DEITIES_FILE.exists():
        return []
    items = json.loads(DEITIES_FILE.read_text(encoding="utf-8"))["deities"]
    return [{**d, "_keys": [norm(k) for k in d["keys"]]} for d in items]


def deity_notes(deity: str | None, groups: str | None = "", limit: int = 2) -> list[dict]:
    """Giới thiệu vị thánh được thờ (trích Wikipedia, deities.json) theo thứ tự xuất hiện trong ô "Thờ";
    không khớp vị nào mà thuộc hàng Tứ phủ → giới thiệu chung về Tứ phủ."""
    nd = f" {norm(deity)} "
    hits = []
    for d in _deities():
        pos = [nd.find(f" {k} ") for k in d["_keys"] if f" {k} " in nd]
        if pos:
            hits.append((min(pos), d))
    hits.sort(key=lambda h: h[0])
    out = [d for _, d in hits][:limit]
    if not out and {g.strip() for g in (groups or "").split(",")} & TU_PHU_GROUPS:
        out = [d for d in _deities() if d["title"] == "Tứ phủ"]
    return out


KEYWORDS_FILE = BASE_DIR / "data" / "places_keywords.json"


def apply_keywords(records: list[dict], path: Path = KEYWORDS_FILE) -> int:
    """Từ khoá soạn tay cho nơi nổi tiếng (vd Chùa Thiên Trù ← "chùa Hương"), khớp tên (bỏ dấu) + tỉnh."""
    if not path.exists():
        return 0
    idx: dict[tuple[str, str], list[dict]] = {}
    for r in records:
        idx.setdefault((norm(r["name"]), r["prov"]), []).append(r)
    n = 0
    for e in json.loads(path.read_text("utf-8"))["places"]:
        hits = idx.get((norm(e["name"]), e["prov"]), [])
        if not hits:
            log.warning("Từ khoá: không thấy %s (%s)", e["name"], e["prov"])
        for r in hits:
            r["kw"] = ", ".join(x for x in (r.get("kw", ""), e["kw"]) if x)
            n += 1
    return n


WD_ALIAS_QUERY = """SELECT ?item ?alias WHERE {
  VALUES ?item { %s }
  ?item skos:altLabel ?alias. FILTER(lang(?alias)="vi")
}"""


def fetch_wikidata_aliases(qids: list[str], client, batch: int = 200, delay: float = 1.0) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for i in range(0, len(qids), batch):
        q = WD_ALIAS_QUERY % " ".join(f"wd:{x}" for x in qids[i:i + batch])

        def go():
            r = client.post(WDQS_URL, data={"query": q}, headers={"Accept": "application/sparql-results+json"})
            r.raise_for_status()
            return r.json()
        for b in _retry(go)["results"]["bindings"]:
            out.setdefault(b["item"]["value"].rsplit("/", 1)[-1], []).append(b["alias"]["value"])
        time.sleep(delay)
    return out


def _http():
    import httpx
    return httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=httpx.Timeout(360, connect=30),
                        follow_redirects=True)


def _cached_json(cache: Path | None, name: str, fetch):
    if cache and (cache / name).exists():
        return json.loads((cache / name).read_text("utf-8"))
    data = fetch()
    if cache:
        cache.mkdir(parents=True, exist_ok=True)
        (cache / name).write_text(json.dumps(data, ensure_ascii=False), "utf-8")
    return data


def _retry(fn, tries: int = 4, wait: float = 30):
    for i in range(tries):
        try:
            return fn()
        except Exception as exc:  # 429/504 của dịch vụ công cộng: chờ rồi thử lại
            if i == tries - 1:
                raise
            log.warning("Lỗi %s, thử lại sau %ss", exc, wait * (i + 1))
            time.sleep(wait * (i + 1))


def fetch_wiki_summaries(titles: list[str], client, batch: int = 20, delay: float = 1.0) -> dict[str, dict]:
    """Đoạn mở đầu bài Wikipedia tiếng Việt (Action API, 20 bài/lần; gọi từng bài qua REST dễ bị 429)."""
    out = {}
    for i in range(0, len(titles), batch):
        chunk = titles[i:i + batch]

        def go():
            r = client.get(WIKI_API, params={"action": "query", "format": "json", "formatversion": "2",
                                             "prop": "extracts|info", "inprop": "url", "exintro": "1",
                                             "explaintext": "1", "exlimit": str(batch), "redirects": "1",
                                             "titles": "|".join(chunk)})
            r.raise_for_status()
            return r.json()["query"]
        try:
            q = _retry(go, wait=10)
        except Exception as exc:
            log.warning("Wikipedia %s…: %s", chunk[0], exc)
            continue
        alias = {x["to"]: x["from"] for key in ("normalized", "redirects") for x in q.get(key, [])}
        for page in q.get("pages", []):
            text = (page.get("extract") or "").strip()
            if not text or page.get("missing"):
                continue
            title = page["title"]
            while title in alias and title not in chunk:
                title = alias[title]
            out[title] = {"desc": text[:4000], "url": page.get("fullurl", "")}
        time.sleep(delay)
    return out


# Thể loại Wikipedia tiếng Việt → loại địa điểm (dùng khi tiêu đề bài không tự nói loại, vd "Bút Tháp")
WIKI_ROOTS = {"Thể loại:Chùa Việt Nam": "chua", "Thể loại:Đình Việt Nam": "dinh", "Thể loại:Đền Việt Nam": "den",
              "Thể loại:Đền tại Việt Nam": "den", "Thể loại:Miếu Việt Nam": "mieu"}
WIKI_SKIP_CAT = re.compile(r"hải ngoại|nước ngoài|ở nước|ấn độ giáo|tháp chăm|công giáo|nhà thờ|thánh thất|hồi giáo|"
                           r"sơ khai|nhà sư|tăng nhân|trụ trì|lễ hội|bản mẫu|hình ảnh|văn miếu|khổng", re.I)


def wiki_category_pages(client, max_depth: int = 4, delay: float = 0.5, roots: dict[str, str] | None = None) -> dict[str, str]:
    """Duyệt đệ quy các thể loại gốc → {tiêu đề bài: loại}. Bỏ thể loại hải ngoại, tháp Chăm, nhà thờ…"""
    pages: dict[str, str] = {}
    seen: set[str] = set()
    queue = [(cat, kind, 0) for cat, kind in (roots or WIKI_ROOTS).items()]
    while queue:
        cat, kind, depth = queue.pop(0)
        if cat in seen:
            continue
        seen.add(cat)
        cont: dict = {}
        while True:
            def go():
                r = client.get(WIKI_API, params={"action": "query", "format": "json", "list": "categorymembers",
                                                 "cmtitle": cat, "cmlimit": "500", "cmtype": "page|subcat", **cont})
                r.raise_for_status()
                return r.json()
            j = _retry(go, wait=10)
            for m in j["query"]["categorymembers"]:
                if m["ns"] == 14 and depth < max_depth and not WIKI_SKIP_CAT.search(m["title"]):
                    queue.append((m["title"], kind, depth + 1))
                elif m["ns"] == 0 and not m["title"].startswith("Danh sách"):
                    pages.setdefault(m["title"], kind)
            time.sleep(delay)
            if "continue" not in j:
                break
            cont = {"cmcontinue": j["continue"]["cmcontinue"]}
    return pages


def wiki_page_details(titles: list[str], client, batch: int = 20, delay: float = 1.0) -> list[dict]:
    """Toạ độ + đoạn mở đầu + QID Wikidata + ảnh (chỉ ảnh Commons) của từng bài, 20 bài/lần."""
    out = []
    for i in range(0, len(titles), batch):
        chunk = titles[i:i + batch]

        def go():
            r = client.get(WIKI_API, params={
                "action": "query", "format": "json", "formatversion": "2", "titles": "|".join(chunk),
                "prop": "coordinates|extracts|pageprops|pageimages|info", "inprop": "url", "coprimary": "primary",
                "colimit": "max", "exintro": "1", "explaintext": "1", "exlimit": str(batch), "ppprop": "wikibase_item",
                "piprop": "thumbnail", "pithumbsize": "640", "pilimit": str(batch)})
            r.raise_for_status()
            return r.json()["query"]
        try:
            q = _retry(go, wait=10)
        except Exception as exc:
            log.warning("Wikipedia %s…: %s", chunk[0], exc)
            continue
        for page in q.get("pages", []):
            co = (page.get("coordinates") or [None])[0] or {}
            if page.get("missing"):
                continue
            thumb = (page.get("thumbnail") or {}).get("source", "")
            out.append({"title": page["title"], "lat": co.get("lat"), "lng": co.get("lon"),
                        "desc": (page.get("extract") or "").strip()[:4000], "url": page.get("fullurl", ""),
                        "qid": (page.get("pageprops") or {}).get("wikibase_item", ""), "pageid": page["pageid"],
                        "img": thumb if "/wikipedia/commons/" in thumb else ""})
        time.sleep(delay)
    return out


def records_from_wikipedia(details: list[dict], kinds: dict[str, str], provinces: ProvinceIndex | None) -> list[dict]:
    out = []
    for d in details:
        name = re.sub(r"\s*\(.*\)\s*$", "", d["title"]).strip()
        if EXCLUDED_NAME.search(name):
            continue
        kind = classify(name) or kinds.get(d["title"])
        hint = re.search(r"\(([^)]*)\)\s*$", d["title"])
        if d["lat"] is None:  # bài không có toạ độ: chỉ dùng để ghép mô tả vào điểm sẵn có
            lat = lng = None
            prov = hint.group(1) if hint else ""
        else:
            lat, lng = round(d["lat"], 6), round(d["lng"], 6)
            prov = provinces.lookup(lat, lng) if provinces else ""
            if provinces and not prov:  # ngoài lãnh thổ (chùa Việt ở nước ngoài) → bỏ
                continue
        if kind is None:
            continue
        out.append({"src": "wikipedia", "sid": f"vi:{d['pageid']}", "name": name[:200], "kind": kind, "rel": "",
                    "lat": lat, "lng": lng, "prov": prov, "addr": "", "phone": "",
                    "web": "", "wd": d["qid"], "wp": d["title"], "img": d["img"],
                    "desc": d["desc"], "desc_src": d["url"]})
    return out


def merge_wikipedia(records: list[dict], wp: list[dict], radius_km: float = 1.5) -> list[dict]:
    """Bài Wikipedia trùng (QID, tiêu đề, hoặc cùng tên trong `radius_km`: toạ độ Wikipedia thường kém chính xác)
    → bổ sung mô tả/ảnh cho bản ghi sẵn có; không trùng → thêm mới."""
    by_qid = {r["wd"]: r for r in records if r["wd"]}
    by_title = {r["wp"]: r for r in records if r["wp"]}
    by_name: dict[str, list[dict]] = {}
    for r in records:
        by_name.setdefault(norm(r["name"]), []).append(r)
    extra = []
    for w in wp:
        same = by_name.get(norm(w["name"]), [])
        if w["lat"] is None:
            # không toạ độ: tên khớp duy nhất, hoặc khớp tỉnh ghi trong ngoặc ("Chùa Vĩnh Nghiêm (Bắc Ninh)")
            hint = norm(w["prov"])
            cands = [r for r in same if hint and (hint in norm(r["prov"]) or hint in norm(r["addr"]))] if hint else same
            near = cands[0] if len(cands) == 1 else None
        else:
            near = next((r for r in same if r["lat"] is not None and _km(r, w) <= radius_km), None)
        target = (by_qid.get(w["wd"]) if w["wd"] else None) or by_title.get(w["wp"]) or near
        if target is None and w["lat"] is None:
            continue
        if target is None:
            extra.append(w)
            by_name.setdefault(norm(w["name"]), []).append(w)
            continue
        for key in ("wd", "wp", "img", "desc", "desc_src"):
            if w.get(key) and not target.get(key):
                target[key] = w[key]
        _add_alt(target, w["name"])
    return records + extra


# ── Nghĩa trang, nghĩa trang liệt sĩ, đài tưởng niệm liệt sĩ ──────────────────────────────────────────────────────
# Luồng riêng (luồng thờ tự ở trên cố ý bỏ tên "Nghĩa trang…"). Lấy cả nghĩa trang không tên trên OSM: đặt tên
# "Nghĩa trang" + địa chỉ "gần <thôn/xóm/phường gần nhất>" để vẫn tìm được theo địa danh.
OVERPASS_CEMETERIES = """[out:json][timeout:300];
area["ISO3166-1"="VN"][admin_level=2]->.vn;
(nwr["landuse"="cemetery"](area.vn); nwr["amenity"="grave_yard"](area.vn);
 nwr["historic"="memorial"]["name"~"[Ll]iệt [Ss]ĩ|[Ll]iệt [Ss]ỹ"](area.vn);
 nwr["name"~"^(Nghĩa trang|Nghĩa địa|Nghĩa trủng|Đài tưởng niệm)",i][!highway](area.vn););
out center tags;"""
OVERPASS_SETTLEMENTS = """[out:json][timeout:300];
area["ISO3166-1"="VN"][admin_level=2]->.vn;
node["place"~"^(city|town|village|hamlet|suburb|quarter|neighbourhood)$"]["name"](area.vn);
out;"""
WIKI_CEMETERY_ROOTS = {"Thể loại:Nghĩa trang tại Việt Nam": "ntrang",
                       "Thể loại:Nghĩa trang và khu tưởng niệm Chiến tranh Việt Nam": "ntrang"}
_MARTYR = re.compile(r"liệt s[ĩỹi]|liet s[iy]\b|anh hùng|tử sĩ|thanh niên xung phong|\btnxp\b", re.I)
_MEMORIAL = re.compile(r"^(đài|bia|nhà bia|tượng đài|nhà tưởng niệm|khu tưởng niệm|tháp|đền thờ liệt)", re.I)
_GROUND_NAME = ("nghĩa trang", "hoa viên nghĩa trang", "nghĩa địa", "nghĩa trủng", "đất thánh", "công viên nghĩa trang", "công viên vĩnh hằng")
_TOMB = re.compile(r"^(lăng|mộ|khu mộ|lăng mộ|khu lăng mộ)\b", re.I)
CEMETERY_KW = {
    "ntls": "nghĩa trang liệt sĩ, nghĩa trang liệt sỹ, liệt sĩ, liệt sỹ, mộ liệt sĩ, viếng liệt sĩ, thắp hương liệt sĩ",
    "tuongniem": "đài tưởng niệm liệt sĩ, đài liệt sĩ, đài liệt sỹ, liệt sĩ, liệt sỹ, tri ân",
    "ntrang": "nghĩa trang, nghĩa địa, tảo mộ, thăm mộ",
    "mo": "lăng mộ, mộ, tảo mộ",
}


def classify_cemetery(name: str, t: dict) -> str | None:
    """Loại cho một đối tượng OSM nghĩa trang/đài tưởng niệm; None = bỏ (tượng đài chung, mộ lẻ không phải khu mộ…)."""
    low = (name or "").strip().lower()
    ground = t.get("landuse") == "cemetery" or t.get("amenity") == "grave_yard"
    if not low:
        return "ntrang" if ground else None
    if _MARTYR.search(low):
        return "ntls" if low.startswith(_GROUND_NAME) or (ground and not _MEMORIAL.match(low)) else "tuongniem"
    if low.startswith(_GROUND_NAME):
        return "ntrang"
    if _TOMB.match(low):
        return "mo" if ground else None
    if _MEMORIAL.match(low):
        return None
    return "ntrang" if ground else None


class SettlementIndex:
    """Thôn/xóm/phường có tên gần nhất (lưới 0,05°) → "gần thôn X" cho điểm thiếu địa chỉ."""
    CELL = 0.05

    def __init__(self, elements: list[dict]):
        self.grid: dict[tuple, list] = {}
        for e in elements:
            t = e.get("tags") or {}
            name = (t.get("name:vi") or t.get("name") or "").strip()
            if name and "lat" in e:
                self.grid.setdefault(self._cell(e["lat"], e["lon"]), []).append((e["lat"], e["lon"], name))

    def _cell(self, lat, lng):
        return (math.floor(lat / self.CELL), math.floor(lng / self.CELL))

    def near(self, lat: float, lng: float, max_km: float = 3.0) -> str:
        ci, cj = self._cell(lat, lng)
        best = None
        for i in (ci - 1, ci, ci + 1):
            for j in (cj - 1, cj, cj + 1):
                for plat, plng, name in self.grid.get((i, j), []):
                    km = _km({"lat": lat, "lng": lng}, {"lat": plat, "lng": plng})
                    if km <= max_km and (best is None or km < best[0]):
                        best = (km, name)
        return best[1] if best else ""


def records_from_cemeteries(elements: list[dict], provinces: ProvinceIndex | None,
                            settlements: SettlementIndex | None, skip_sids: set[str] = frozenset()) -> list[dict]:
    named, unnamed = [], []
    for e in elements:
        sid = f"{e['type']}/{e['id']}"
        t = e.get("tags") or {}
        name = re.sub(r"\s+", " ", (t.get("name:vi") or t.get("name") or "").strip())
        kind = classify_cemetery(name, t)
        lat, lng = (e["lat"], e["lon"]) if "lat" in e else (e.get("center", {}).get("lat"), e.get("center", {}).get("lon"))
        if kind is None or lat is None or sid in skip_sids:
            continue
        if name.isupper():  # "NGHĨA TRANG ĐỒNG RẮN" → "Nghĩa Trang Đồng Rắn"
            name = name.title()
        prov = (provinces.lookup(lat, lng) if provinces else "") or province_name(t.get("addr:province", ""))
        if provinces and not prov:
            continue
        addr = _osm_address(t)
        near = settlements.near(lat, lng) if settlements and not (addr and name) else ""
        if near and not addr:
            addr = f"gần {near}"
        if not name and near:
            name = f"Nghĩa trang gần {near}"  # mô tả vị trí, không phải tên riêng
        wp = t.get("wikipedia", "")
        rec = {"src": "osm", "sid": sid, "name": (name or "Nghĩa trang")[:200], "kind": kind,
               "rel": t.get("religion", "")[:30], "lat": round(lat, 6), "lng": round(lng, 6), "prov": prov,
               "addr": addr[:300], "phone": (t.get("phone") or t.get("contact:phone") or "")[:60],
               "web": (t.get("website") or t.get("contact:website") or "")[:300],
               "wd": t.get("wikidata", ""), "wp": wp[3:] if wp.startswith("vi:") else "",
               "alt": [a.strip() for k in OSM_ALIAS_TAGS for a in (t.get(k) or "").split(";") if a.strip()],
               "kw": CEMETERY_KW[kind]}
        (named if t.get("name") or t.get("name:vi") else unnamed).append(rec)
    named = dedupe(named)
    # nghĩa trang không tên trùng chỗ một nghĩa trang có tên (vẽ hai lần) → bỏ; không tên sát nhau → giữ một
    kept_unnamed: list[dict] = []
    for r in unnamed:
        if any(_km(r, k) <= 0.25 for k in named if abs(k["lat"] - r["lat"]) < 0.01) or \
           any(_km(r, k) <= 0.15 for k in kept_unnamed if abs(k["lat"] - r["lat"]) < 0.01):
            continue
        kept_unnamed.append(r)
    return named + kept_unnamed


def records_from_wikipedia_cemeteries(details: list[dict], provinces: ProvinceIndex | None) -> list[dict]:
    out = []
    for d in details:
        name = re.sub(r"\s*\(.*\)\s*$", "", d["title"]).strip()
        kind = classify_cemetery(name, {})  # chỉ nhận bài có tên đúng là nghĩa trang / liệt sĩ (bỏ bảo tàng, địa đạo…)
        if kind is None or d["lat"] is None:
            continue
        lat, lng = round(d["lat"], 6), round(d["lng"], 6)
        prov = provinces.lookup(lat, lng) if provinces else ""
        if provinces and not prov:
            continue
        out.append({"src": "wikipedia", "sid": f"vi:{d['pageid']}", "name": name[:200], "kind": kind, "rel": "",
                    "lat": lat, "lng": lng, "prov": prov, "addr": "", "phone": "", "web": "", "wd": d["qid"],
                    "wp": d["title"], "img": d["img"], "desc": d["desc"], "desc_src": d["url"], "kw": CEMETERY_KW[kind]})
    return out


def build(out: Path = SNAPSHOT, cache: Path | None = None) -> dict:
    with _http() as client:
        def overpass(q):
            def go():
                r = client.post(OVERPASS_URL, data={"data": q})
                r.raise_for_status()
                return r.json()
            return _retry(go)

        def wikidata():
            r = client.get(WDQS_URL, params={"query": WIKIDATA_QUERY},
                           headers={"Accept": "application/sparql-results+json"})
            r.raise_for_status()
            return r.json()

        log.info("Tải ranh giới tỉnh…")
        provs = ProvinceIndex(_cached_json(cache, "provinces.json", lambda: overpass(OVERPASS_PROVINCES))["elements"])
        log.info("Tải điểm thờ tự OSM…")
        osm = records_from_osm(_cached_json(cache, "osm.json", lambda: overpass(OVERPASS_PLACES))["elements"], provs)
        log.info("Tải Wikidata…")
        wd = records_from_wikidata(
            _cached_json(cache, "wikidata.json", lambda: _retry(wikidata))["results"]["bindings"], provs)
        records = merge(dedupe(osm), wd)
        log.info("Duyệt thể loại Wikipedia…")
        kinds = _cached_json(cache, "wiki_cats.json", lambda: wiki_category_pages(client))
        log.info("Tải %d bài Wikipedia…", len(kinds))
        details = _cached_json(cache, "wiki_pages.json", lambda: wiki_page_details(sorted(kinds), client))
        records = merge_wikipedia(records, records_from_wikipedia(details, kinds, provs))
        titles = sorted({r["wp"] for r in records if r["wp"] and not r.get("desc")})
        log.info("Tải %d tóm tắt Wikipedia…", len(titles))
        summaries = _cached_json(cache, "wiki.json", lambda: fetch_wiki_summaries(titles, client))
        qids = sorted({r["wd"] for r in records if re.fullmatch(r"Q\d+", r.get("wd") or "")})
        log.info("Tải tên gọi khác của %d mục Wikidata…", len(qids))
        wd_alias = _cached_json(cache, "wd_aliases.json", lambda: fetch_wikidata_aliases(qids, client))
        log.info("Tải nghĩa trang, đài tưởng niệm liệt sĩ…")
        settle = SettlementIndex(_cached_json(cache, "settlements.json", lambda: overpass(OVERPASS_SETTLEMENTS))["elements"])
        cem = records_from_cemeteries(_cached_json(cache, "cemetery.json", lambda: overpass(OVERPASS_CEMETERIES))["elements"],
                                      provs, settle, skip_sids={r["sid"] for r in records if r["src"] == "osm"})
        cem_kinds = _cached_json(cache, "wiki_cem_cats.json",
                                 lambda: wiki_category_pages(client, max_depth=2, roots=WIKI_CEMETERY_ROOTS))
        cem_details = _cached_json(cache, "wiki_cem_pages.json", lambda: wiki_page_details(sorted(cem_kinds), client))
        cem = merge_wikipedia(cem, records_from_wikipedia_cemeteries(cem_details, provs))
        cem_titles = sorted({r["wp"] for r in cem if r["wp"] and not r.get("desc")})
        cem_sum = _cached_json(cache, "wiki_cem.json", lambda: fetch_wiki_summaries(cem_titles, client))
        for r in cem:
            s = cem_sum.get(r["wp"])
            if s and not r.get("desc"):
                r["desc"], r["desc_src"] = s["desc"], s["url"]
        log.info("Nghĩa trang: %s", {k: sum(r["kind"] == k for r in cem) for k in CEMETERY_KINDS})
        records += cem
    for r in records:
        s = summaries.get(r["wp"])
        if s and not r.get("desc"):
            r["desc"], r["desc_src"] = s["desc"], s["url"]
    if CURATED_FILE.exists():
        cur = json.loads(CURATED_FILE.read_text("utf-8"))["places"]
        log.info("Ghép %d nơi trong danh sách biên soạn…", len(cur))
        todo = [c for c in cur if curated_match(c, records) is None]
        with _http() as client:
            geo = _cached_json(cache, "nominatim.json", lambda: geocode_curated(todo, client))
        log.info("Danh sách biên soạn: %s", merge_curated(records, cur, provs, geo))
        with _http() as client:
            log.info("Mô tả Wikipedia cho danh sách biên soạn: %d nơi",
                     attach_wikipedia_to_curated(records, client, cache))
    log.info("%d điểm có tên gọi khác", finalize_aliases(records, wd_alias))
    log.info("%d điểm có từ khoá soạn tay", apply_keywords(records))
    records.sort(key=lambda r: (r["prov"], norm(r["name"]), r["sid"]))
    snap = {"version": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
            "attribution": "© OpenStreetMap contributors (ODbL) · Wikidata (CC0) · Wikipedia (CC BY-SA 4.0)",
            "places": records}
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wt", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, separators=(",", ":"))
    return snap


def read_snapshot(path: Path = SNAPSHOT) -> dict | None:
    if not path.exists():
        return None
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def load(db: Session, snap: dict) -> dict:
    """Upsert snapshot vào DB theo (source, source_id). Bản ghi admin đã sửa tay (`edited`) giữ nguyên nội dung."""
    existing = {(p.source, p.source_id): p for p in db.scalars(select(SacredPlace))}
    added = updated = 0
    for r in snap["places"]:
        fields = dict(name=r["name"], kind=r["kind"] if r["kind"] in PLACE_KINDS else "khac", religion=r.get("rel", ""),
                      lat=r["lat"], lng=r["lng"], province=r.get("prov", ""), address=r.get("addr", ""),
                      phone=r.get("phone", ""), website=r.get("web", ""), wikidata=r.get("wd", ""),
                      description=r.get("desc", ""), description_source=r.get("desc_src", ""),
                      image_url=r.get("img", ""), aliases=r.get("alias", ""), keywords=r.get("kw", ""),
                      deity=r.get("deity", ""), deity_groups=", ".join(r.get("groups", [])),
                      intents=",".join(r.get("intents", [])), festival=r.get("fest", ""), priority=r.get("prio"),
                      approx_location=bool(r.get("approx")))
        p = existing.get((r["src"], r["sid"]))
        if p is None:
            db.add(SacredPlace(source=r["src"], source_id=r["sid"], **fields))
            added += 1
        elif not p.edited:
            for k, v in fields.items():
                setattr(p, k, v)
            updated += 1
    db.flush()
    linked = link_temples(db)
    db.merge(Setting(key="places:snapshot", value=snap["version"]))
    return {"added": added, "updated": updated, "linked": linked}


def link_temples(db: Session) -> int:
    """Gắn đền nhận đặt lễ với địa điểm cùng tên (bỏ dấu), ưu tiên cùng tỉnh. Không đụng các đền đã gắn."""
    taken = set(db.scalars(select(SacredPlace.temple_id).where(SacredPlace.temple_id.is_not(None))))
    n = 0
    for t in db.scalars(select(Temple).where(Temple.id.not_in(taken) if taken else Temple.id.is_not(None))):
        cands = [p for p in db.scalars(select(SacredPlace).where(SacredPlace.temple_id.is_(None)))
                 if norm(p.name) == norm(t.name)]
        if t.province:
            cands.sort(key=lambda p: norm(p.province) != norm(t.province))
        if cands:
            cands[0].temple_id = t.id
            n += 1
    db.flush()
    return n


def autoload(db: Session) -> dict | None:
    """Seed gọi: nạp snapshot khi DB chưa có hoặc snapshot đã đổi phiên bản."""
    snap = read_snapshot()
    if not snap:
        return None
    cur = db.get(Setting, "places:snapshot")
    if cur and cur.value == snap["version"]:
        return None
    return load(db, snap)


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(prog="app.places")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="tải OSM + Wikidata + Wikipedia → snapshot")
    b.add_argument("--out", type=Path, default=SNAPSHOT)
    b.add_argument("--cache", type=Path, default=None, help="thư mục lưu dữ liệu thô để chạy lại không phải tải")
    ld = sub.add_parser("load", help="nạp snapshot vào DB")
    ld.add_argument("file", nargs="?", type=Path, default=SNAPSHOT)
    args = ap.parse_args(argv)
    if args.cmd == "build":
        snap = build(args.out, args.cache)
        ps = snap["places"]
        print(f"{len(ps)} địa điểm · {sum(1 for p in ps if p.get('desc'))} có mô tả · "
              f"{sum(1 for p in ps if not p['prov'])} chưa rõ tỉnh → {args.out}")
        return
    from . import db as dbmod
    dbmod.init_engine()
    snap = read_snapshot(args.file)
    if not snap:
        raise SystemExit(f"Không có snapshot {args.file}")
    with dbmod.SessionLocal() as db:
        print(load(db, snap))
        db.commit()


if __name__ == "__main__":
    main()
