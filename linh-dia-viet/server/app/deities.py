"""Danh mục thần thánh: nhập từ bảng tính (than_thanh_viet_nam_*.xlsx), tra cứu, và khớp với đền/địa điểm theo danh vị thờ."""
import re
import unicodedata
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Deity

# tiêu đề cột trong bảng tính → thuộc tính
COLUMNS = {"ID": "id", "Tên gọi": "name", "Tên khác": "aliases", "Mã nhóm": "group_code", "Nhóm": "group_name",
           "Vai trò": "role", "Nơi thờ chính": "places", "Tỉnh (cũ)": "province_old", "Tỉnh mới (2025)": "province_new",
           "Độ tin cậy": "reliability", "Ghi chú hiệu đính": "note"}


class DeityImportError(ValueError):
    pass


def import_xlsx(db: Session, path: Path, sheet: str = "Danh sách") -> int:
    """Thêm mới / cập nhật theo ID (chạy lại nhiều lần không sao). Trả số dòng đã nhập."""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if sheet not in wb.sheetnames:
        raise DeityImportError(f"Không có trang '{sheet}' trong file")
    rows = wb[sheet].iter_rows(values_only=True)
    header = [str(h or "").strip() for h in next(rows)]
    missing = [c for c in ("ID", "Tên gọi") if c not in header]
    if missing:
        raise DeityImportError(f"Thiếu cột: {', '.join(missing)}")
    idx = {COLUMNS[h]: i for i, h in enumerate(header) if h in COLUMNS}
    n = 0
    for row in rows:
        raw_id = row[idx["id"]]
        if raw_id is None or not str(raw_id).strip().isdigit() or not row[idx["name"]]:
            continue
        d = db.get(Deity, int(raw_id)) or Deity(id=int(raw_id))
        for attr, i in idx.items():
            if attr != "id":
                setattr(d, attr, str(row[i] or "").strip())
        db.add(d)
        n += 1
    db.flush()
    return n


def _plain(s: str) -> str:
    """Chữ thường, bỏ dấu câu → " a b c " để so theo nguyên từ."""
    s = unicodedata.normalize("NFC", s or "").lower()
    return " " + " ".join(re.sub(r"[^\w]+", " ", s).split()) + " "


# danh xưng đứng đầu tên: "Thánh Mẫu Liễu Hạnh" vẫn khớp "Mẫu Liễu Hạnh" / "Liễu Hạnh"
TITLES = ("thánh mẫu", "đức thánh", "đức", "thánh", "mẫu")
SHRINE_KINDS = {"đền", "phủ", "đình", "chùa", "miếu", "lăng", "điện", "quán", "nghè"}
GENERIC = {"làng", "xã", "thôn", "các", "nhiều", "thờ", "chính", "riêng"}


def _name_keys(d: Deity) -> set[str]:
    keys = set()
    for n in d.names:
        p = _plain(n)
        if len(p.strip()) >= 4:
            keys.add(p)
        for t in TITLES:
            rest = p[len(t) + 1:] if p.startswith(f" {t} ") else ""  # " liễu hạnh "
            if len(rest.split()) >= 2:
                keys.add(rest)
                break
    return keys


def _shrine_keys(d: Deity) -> set[str]:
    """Tên nơi thờ chính ("Phủ Dầy (Vụ Bản); đền Sòng (Bỉm Sơn)") → {" phủ dầy ", " đền sòng "}."""
    keys = set()
    for item in re.split(r"[;,]", re.sub(r"\([^)]*\)", "", d.places or "")):
        w = _plain(item).split()
        if len(w) >= 2 and w[0] in SHRINE_KINDS and w[1] not in GENERIC:
            keys.add(" " + " ".join(w) + " ")
    return keys


def matching(db: Session, *texts: str, names: tuple[str, ...] = ()) -> list[Deity]:
    """Các vị (công khai) có tên/tên khác xuất hiện trong các đoạn chữ (danh vị thờ, từ khoá…), hoặc có nơi thờ chính
    trùng tên địa điểm (`names`)."""
    text = _plain(" ".join(t or "" for t in texts))
    place = _plain(" ".join(n or "" for n in names))
    out = []
    for d in db.scalars(select(Deity).order_by(Deity.id)):
        if d.public and (any(k in text for k in _name_keys(d)) or any(k in place for k in _shrine_keys(d))):
            out.append(d)
    return out
