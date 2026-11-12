"""Kiểm tra tĩnh file giao diện (CSS/JS) cho những lỗi đã gặp."""
import re
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "app" / "static"


def test_serif_font_has_vietnamese_fallback():
    """Windows không có Noto Serif; Georgia vỡ dấu tiếng Việt ("Đề`n") → phải rơi về font đủ dấu."""
    css = (STATIC / "ld.css").read_text(encoding="utf-8")
    stacks = re.findall(r'font-family:\s*"Noto Serif",([^;]+);', css)
    assert stacks and all("Georgia" not in s and "Cambria" in s for s in stacks)


def test_map_flies_to_selected_place_and_accepts_query():
    js = (STATIC / "map.js").read_text(encoding="utf-8")
    focus = re.findall(r"focus: function \(p\) \{(.*?)\n        \},", js, re.S)
    assert len(focus) == 2  # Google + Leaflet
    assert "flyTo(map" in focus[0] and "setZoom(16)" not in focus[0]
    assert "map.flyTo(" in focus[1]
    assert "prefers-reduced-motion" in js  # người tắt hiệu ứng chuyển động: nhảy thẳng tới nơi
    assert re.search(r"\[\?&\]q=", js)  # /ban-do?q=… từ trang Thần thánh
