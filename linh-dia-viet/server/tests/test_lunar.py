from datetime import date

import pytest

from app.lunar import LunarDate, can_chi_year, solar_to_lunar


@pytest.mark.parametrize("solar, year", [
    (date(1985, 1, 21), 1985),  # Việt Nam ăn Tết sớm hơn Trung Quốc 1 tháng
    (date(2000, 2, 5), 2000),
    (date(2007, 2, 17), 2007),
    (date(2020, 1, 25), 2020),
    (date(2023, 1, 22), 2023),
    (date(2024, 2, 10), 2024),
    (date(2025, 1, 29), 2025),
    (date(2026, 2, 17), 2026),
])
def test_tet_nguyen_dan(solar, year):
    assert solar_to_lunar(solar) == LunarDate(1, 1, year, False)


def test_ngay_truoc_tet_la_thang_chap_nam_cu():
    assert solar_to_lunar(date(2024, 2, 9)) == LunarDate(30, 12, 2023, False)


@pytest.mark.parametrize("solar, expected", [
    (date(2023, 3, 22), LunarDate(1, 2, 2023, True)),   # tháng 2 nhuận Quý Mão
    (date(2025, 7, 25), LunarDate(1, 6, 2025, True)),   # tháng 6 nhuận Ất Tỵ
    (date(2020, 5, 23), LunarDate(1, 4, 2020, True)),   # tháng 4 nhuận Canh Tý
    (date(2024, 9, 17), LunarDate(15, 8, 2024, False)),  # Trung thu 2024
])
def test_known_dates(solar, expected):
    assert solar_to_lunar(solar) == expected


@pytest.mark.parametrize("year, cc", [(1990, "Canh Ngọ"), (1984, "Giáp Tý"), (2000, "Canh Thìn"),
                                      (2025, "Ất Tỵ"), (2026, "Bính Ngọ"), (1975, "Ất Mão")])
def test_can_chi(year, cc):
    assert can_chi_year(year) == cc


def test_text():
    assert solar_to_lunar(date(2026, 2, 17)).text() == "mùng 1 tháng Giêng năm Bính Ngọ"
    assert solar_to_lunar(date(2025, 7, 25)).text() == "mùng 1 tháng 6 nhuận năm Ất Tỵ"
