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
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import BASE_DIR
from .models import PLACE_KINDS, SacredPlace, Setting, Temple

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
    return osm + extra


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
        titles = sorted({r["wp"] for r in records if r["wp"]})
        log.info("Tải %d tóm tắt Wikipedia…", len(titles))
        summaries = _cached_json(cache, "wiki.json", lambda: fetch_wiki_summaries(titles, client))
    for r in records:
        s = summaries.get(r["wp"])
        if s:
            r["desc"], r["desc_src"] = s["desc"], s["url"]
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
                      image_url=r.get("img", ""))
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
