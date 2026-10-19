from datetime import date
from types import SimpleNamespace

import pytest

from app.prayer_text import (DEFAULT_TEMPLATE, clean_input, normalize_for_tts, personal_context, read_number,
                             render, temple_context, unknown_variables)


@pytest.mark.parametrize("n, words", [
    (0, "không"), (5, "năm"), (10, "mười"), (11, "mười một"), (15, "mười lăm"), (21, "hai mươi mốt"),
    (24, "hai mươi bốn"), (105, "một trăm linh năm"), (1990, "một nghìn chín trăm chín mươi"),
    (2026, "hai nghìn không trăm hai mươi sáu"), (250000, "hai trăm năm mươi nghìn"),
    (1000005, "một triệu không trăm linh năm"),
])
def test_read_number(n, words):
    assert read_number(n) == words


def test_render_full_template():
    ctx = personal_context("Nguyễn Văn A", 1990, "Cầu Giấy, Hà Nội", "gia đình bình an", "Lễ hoa quả",
                           date(2026, 2, 17))
    ctx.update(temple_context(SimpleNamespace(name="Đền Ngọc Sơn", address="Hoàn Kiếm", province="Hà Nội",
                                              deity="Đức Thánh Trần")))
    text = render(DEFAULT_TEMPLATE, ctx)
    assert "{" not in text
    assert "sinh năm 1990 (Canh Ngọ)" in text
    assert "ngày mùng 1 tháng Giêng năm Bính Ngọ (ngày 17 tháng 2 năm 2026)" in text
    assert "Kính lạy Đức Thánh Trần tại Đền Ngọc Sơn." in text


def test_render_keeps_missing_vars_and_no_injection():
    ctx = {"ho_ten": clean_input("A {ten_den} B", 50)}
    assert render("{ho_ten} - {ten_den}", ctx) == "A ten_den B - {ten_den}"
    assert unknown_variables("{ho_ten} {la}") == {"la"}


def test_normalize_for_tts():
    out = normalize_for_tts("Nam mô A Di Đà Phật! (3 lần)\nSinh năm 1990, ngày 17/2/2026 lúc 9:30 tại TP. Hà Nội.")
    assert out.count("Na mô A Di Đà Phật!") == 3
    assert "(3 lần)" not in out
    assert "một nghìn chín trăm chín mươi" in out
    assert "ngày mười bảy tháng hai năm hai nghìn không trăm hai mươi sáu" in out
    assert "chín giờ ba mươi phút" in out
    assert "thành phố Hà Nội" in out
    assert not any(ch.isdigit() for ch in out)
