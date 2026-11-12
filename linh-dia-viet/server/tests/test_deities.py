"""Danh mục thần thánh: nhập từ bảng tính, tra cứu công khai, hiện trên trang đền thờ vị đó."""
import openpyxl
import pytest
from sqlalchemy import select

from app import cli
from app.deities import DeityImportError, for_temple, import_xlsx
from app.models import AuditLog, Deity, Temple
from conftest import P

HEADER = ["ID", "Tên gọi", "Tên khác", "Mã nhóm", "Nhóm", "Vai trò", "Nơi thờ chính", "Tỉnh (cũ)", "Tỉnh mới (2025)",
          "Độ tin cậy", "Ghi chú hiệu đính"]
ROWS = [
    [4, "Thánh Mẫu Liễu Hạnh", "Mẫu Thượng Thiên", "I", "Thánh tối linh", "Đệ tứ Tứ Bất Tử", "Phủ Dầy; đền Sòng",
     "Nam Định", "Ninh Bình", "Cao", None],
    [2, "Phù Đổng Thiên Vương", "Thánh Gióng", "I", "Thánh tối linh", "Biểu tượng chống ngoại xâm", "Đền Phù Đổng",
     "Hà Nội", "Hà Nội", "Cao", None],
    [150, "Thần làng X", "", "IV", "Thành hoàng làng", "Chưa rõ thần tích", "Làng X", "Bắc Ninh", "Bắc Ninh",
     "Thấp - cần xác minh", "cần điền dã"],
]


def _xlsx(tmp_path, rows=ROWS, header=HEADER, sheet="Danh sách"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(header)
    for r in rows:
        ws.append(r)
    ws.append([None] * len(header))  # dòng trống cuối bảng
    p = tmp_path / "than_thanh.xlsx"
    wb.save(p)
    return p


def test_import_and_reimport_updates_by_id(db, tmp_path):
    assert import_xlsx(db, _xlsx(tmp_path)) == 3
    db.commit()
    d = db.get(Deity, 4)
    assert d.name == "Thánh Mẫu Liễu Hạnh" and d.province_new == "Ninh Bình" and d.public
    assert not db.get(Deity, 150).public  # độ tin cậy thấp: không công khai
    changed = [ROWS[0][:5] + ["Mẫu Thượng Thiên, Đệ tứ Tứ Bất Tử"] + ROWS[0][6:]]
    assert import_xlsx(db, _xlsx(tmp_path, changed)) == 1
    db.commit()
    assert db.scalar(select(Deity).where(Deity.id == 4)).role.startswith("Mẫu Thượng Thiên")
    assert len(db.scalars(select(Deity)).all()) == 3


def test_import_rejects_wrong_file(db, tmp_path):
    with pytest.raises(DeityImportError):
        import_xlsx(db, _xlsx(tmp_path, sheet="Khác"))
    with pytest.raises(DeityImportError):
        import_xlsx(db, _xlsx(tmp_path, header=["Tên", "Vai trò"], rows=[]))


def test_cli_import(db, tmp_path, capsys):
    cli.main(["import-deities", str(_xlsx(tmp_path))])
    assert "Đã nhập 3 vị" in capsys.readouterr().out
    db.expire_all()
    assert db.get(Deity, 2).aliases == "Thánh Gióng"
    assert db.scalar(select(AuditLog).where(AuditLog.action == "deity.import"))


def test_temple_page_shows_matching_deity(user_client, db, tmp_path):
    import_xlsx(db, _xlsx(tmp_path))
    db.commit()
    t = db.scalar(select(Temple).where(Temple.slug == "phu-tay-ho"))
    assert [d.id for d in for_temple(db, t)] == [4]
    page = user_client.get(f"{P}/den/phu-tay-ho").text
    assert "Đệ tứ Tứ Bất Tử" in page and "Mẫu Thượng Thiên" in page
    assert "Đệ tứ Tứ Bất Tử" not in user_client.get(f"{P}/den/den-ngoc-son").text


def test_deity_list_search_and_hides_unverified(user_client, db, tmp_path):
    import_xlsx(db, _xlsx(tmp_path))
    db.commit()
    page = user_client.get(f"{P}/than-thanh").text
    assert "Thánh Mẫu Liễu Hạnh" in page and "Phù Đổng Thiên Vương" in page and "Thần làng X" not in page
    page = user_client.get(f"{P}/than-thanh", params={"q": "gióng"}).text
    assert "Phù Đổng Thiên Vương" in page and "Thánh Mẫu Liễu Hạnh</h3>" not in page
    assert "Tìm đền thờ" in page
