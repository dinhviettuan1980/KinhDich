"""Danh mục thần thánh: nhập từ bảng tính (than_thanh_viet_nam_*.xlsx), tra cứu, và khớp với đền/địa điểm theo danh vị thờ."""
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
    return unicodedata.normalize("NFC", s).lower()


def matching(db: Session, *texts: str) -> list[Deity]:
    """Các vị (công khai) có tên/tên khác xuất hiện trong các đoạn chữ (danh vị thờ, tên đền…)."""
    text = _plain(" ".join(t or "" for t in texts))
    out = []
    for d in db.scalars(select(Deity).order_by(Deity.id)):
        if d.public and any(len(n) >= 4 and _plain(n) in text for n in d.names):
            out.append(d)
    return out
