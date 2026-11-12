"""LinhDiaViet_Data.xlsx (sheet Shrines) → app/data/places_curated.json.

Chạy: python scripts/curated_from_xlsx.py FILE.xlsx app/data/places_curated.json  (cần: pip install openpyxl)
rồi:  python -m app.places build --cache DIR  để dựng lại snapshot."""
import json, re, sys
import openpyxl

OLD_MOBILE = {"0162": "032", "0163": "033", "0164": "034", "0165": "035", "0166": "036", "0167": "037", "0168": "038",
              "0169": "039", "0120": "070", "0121": "079", "0122": "077", "0126": "076", "0128": "078", "0123": "083",
              "0124": "084", "0125": "085", "0127": "081", "0129": "082", "0186": "056", "0188": "058", "0199": "059"}
INTENTS = {"bình an": "binh-an", "tài lộc": "tai-loc", "tình duyên": "tinh-duyen", "sức khỏe": "suc-khoe",
           "sức khoẻ": "suc-khoe", "công danh": "cong-danh"}

def phone(p):
    d = re.sub(r"\D", "", p)
    if len(d) == 11 and d[:4] in OLD_MOBILE:
        d = OLD_MOBILE[d[:4]] + d[4:]
    if len(d) == 10 and d.startswith("0"):
        return f"{d[:4]} {d[4:7]} {d[7:]}" if d[1] in "35789" else f"{d[:4]} {d[4:]}"
    if len(d) == 11 and d.startswith("02"):  # máy bàn 11 số: 0xxx xxx xxxx
        return f"{d[:4]} {d[4:7]} {d[7:]}"
    return p.strip()

def clean(v):
    v = "" if v is None else str(v).strip()
    return re.sub(r"\s*-\s*null\s*$", "", v).strip()

wb = openpyxl.load_workbook(sys.argv[1], read_only=True, data_only=True)
rows = list(wb["Shrines"].iter_rows(values_only=True))
hdr = rows[0]
out = []
for r in rows[1:]:
    d = {k: clean(v) for k, v in zip(hdr, r)}
    if not d["Tên di tích"] or d["Tên di tích"].lower() == "test":
        continue
    addr, phones = d["Địa chỉ"], []
    m = re.search(r"\s*SDT:\s*(.*)$", addr, re.I)
    if m:
        addr = addr[:m.start()]
        phones = [phone(x) for x in re.split(r"\s*/\s*", m.group(1)) if re.search(r"\d{6}", re.sub(r"\D", "", x))]
    deity = d["Thần linh"]
    groups = re.findall(r"\(([^()]*)\)", deity)
    intents = [INTENTS[x.strip().lower()] for x in d["Chủ đề"].split(",") if x.strip().lower() in INTENTS]
    fest = re.sub(r"^Lễ hội/ngày (?:tiệc|hội):\s*", "", d["Lễ hội"])
    out.append({
        "name": d["Tên di tích"], "type": d["Loại hình"], "lat": round(float(d["Kinh độ (Lat)"]), 6),
        "lng": round(float(d["Vĩ độ (Lng)"]), 6), "addr": addr.strip().rstrip(".").strip(), "phone": " / ".join(phones),
        "deity": re.sub(r"\s*\([^()]*\)", "", deity).strip(), "groups": sorted(set(g.strip() for g in groups)),
        "intents": intents, "fest": fest, "prio": int(d["Bậc ưu tiên"]) if d["Bậc ưu tiên"].isdigit() else None,
    })
json.dump({"source": "LinhDiaViet_Data.xlsx (danh sách đền phủ Tứ phủ do Linh Địa Việt biên soạn)", "places": out},
          open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "nơi")
