"""Sinh sớ khấn từ mẫu + chuẩn hoá văn bản để TTS đọc đúng."""
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml

from .lunar import can_chi_year, solar_text, solar_to_lunar

VARIABLES = ["ho_ten", "nam_sinh", "can_chi", "dia_chi", "ten_den", "dia_chi_den", "than_linh", "goi_le",
             "ngay_am", "ngay_duong", "nguyen_vong"]
TEMPLE_VARIABLES = ["ten_den", "dia_chi_den", "than_linh"]

# Mẫu khởi đầu — CHƯA phải văn khấn chuẩn, sẽ nhờ người am hiểu chỉnh lại (admin sửa trong trang quản trị).
DEFAULT_TEMPLATE = """Nam mô A Di Đà Phật! (3 lần)
Kính lạy {than_linh} tại {ten_den}.
Tín chủ con là {ho_ten}, sinh năm {nam_sinh} ({can_chi}), ngụ tại {dia_chi}.
Hôm nay là ngày {ngay_am} ({ngay_duong}), tín chủ con thành tâm sắm sửa {goi_le}, dâng lên trước {ten_den}, kính cẩn tâu trình.
Cúi xin chư vị soi xét, phù hộ độ trì cho {nguyen_vong}.
Chúng con lễ bạc tâm thành, kính mong được chứng giám. Nam mô A Di Đà Phật!"""

_VAR_RE = re.compile(r"\{(\w+)\}")


def clean_input(s: str, max_len: int, keep_braces: bool = False) -> str:
    """Dọn dữ liệu người dùng: bỏ ký tự điều khiển, dấu ngoặc nhọn (tránh chèn biến), cắt độ dài."""
    s = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]" if keep_braces else r"[\x00-\x08\x0b-\x1f\x7f{}]", "", s or "")
    return re.sub(r"[ \t]+", " ", s).strip()[:max_len]


def clean_multiline(s: str, max_len: int) -> str:
    """Văn bản sớ khách sửa: giữ xuống dòng và {bien} (đã kiểm tra hợp lệ trước đó)."""
    return "\n".join(clean_input(line, max_len, keep_braces=True) for line in (s or "").splitlines()).strip()[:max_len]


def render(template: str, ctx: dict[str, str]) -> str:
    """Thay {bien} có trong ctx; biến không có trong ctx giữ nguyên (để render tiếp theo từng đền)."""
    return _VAR_RE.sub(lambda m: str(ctx[m.group(1)]) if m.group(1) in ctx else m.group(0), template)


def unknown_variables(template: str) -> set[str]:
    return set(_VAR_RE.findall(template)) - set(VARIABLES)


def personal_context(full_name: str, birth_year: int, address: str, wish: str, package_name: str,
                     ceremony_date: date) -> dict[str, str]:
    lunar = solar_to_lunar(ceremony_date)
    return {
        "ho_ten": full_name, "nam_sinh": str(birth_year), "can_chi": can_chi_year(birth_year),
        "dia_chi": address, "nguyen_vong": wish, "goi_le": package_name,
        "ngay_am": lunar.text(), "ngay_duong": solar_text(ceremony_date),
    }


def temple_context(temple) -> dict[str, str]:
    return {"ten_den": temple.name, "dia_chi_den": ", ".join(x for x in (temple.address, temple.province) if x),
            "than_linh": temple.deity or "chư vị Thánh Thần"}


# ---------------- Chuẩn hoá cho TTS ----------------

DIGITS = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]


def _read_triple(n: int, full: bool) -> str:
    """Đọc số 0..999. full=True khi không phải nhóm đầu (đọc cả 'không trăm', 'linh')."""
    h, t, u = n // 100, (n // 10) % 10, n % 10
    words = []
    if h or full:
        words += [DIGITS[h], "trăm"]
    if t == 0:
        if u and (h or full):
            words.append("linh")
    elif t == 1:
        words.append("mười")
    else:
        words += [DIGITS[t], "mươi"]
    if u:
        if u == 1 and t >= 2:
            words.append("mốt")
        elif u == 5 and t >= 1:
            words.append("lăm")
        else:
            words.append(DIGITS[u])
    return " ".join(words)


def read_number(n: int) -> str:
    if n == 0:
        return "không"
    if n < 0:
        return "âm " + read_number(-n)
    groups = []
    while n:
        groups.append(n % 1000)
        n //= 1000
    names = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ"]
    parts = []
    for i in range(len(groups) - 1, -1, -1):
        g = groups[i]
        if g == 0:
            continue
        first = i == len(groups) - 1
        parts.append(_read_triple(g, full=not first))
        if names[i]:
            parts.append(names[i])
    return " ".join(parts)


@lru_cache
def pronunciation() -> dict[str, str]:
    data = yaml.safe_load((Path(__file__).parent / "data" / "pronunciation.yaml").read_text(encoding="utf-8"))
    return dict(data.get("replacements") or {})


def normalize_for_tts(text: str) -> str:
    # 1) "Câu! (3 lần)" → đọc câu đó 3 lần
    def repeat(m):
        phrase, times = m.group(1).strip(), min(int(m.group(2)), 9)
        return " ".join([phrase] * times)
    text = re.sub(r"([^.!?\n]+[.!?]?)\s*\((\d+)\s*lần\)", repeat, text)
    # 2) từ điển phát âm
    for written, spoken in sorted(pronunciation().items(), key=lambda kv: -len(kv[0])):
        text = re.sub(rf"(?<!\w){re.escape(written)}(?!\w)", spoken, text, flags=re.IGNORECASE)
    # 3) ngày tháng, giờ phút, số
    text = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
                  lambda m: f"ngày {read_number(int(m[1]))} tháng {read_number(int(m[2]))} năm {read_number(int(m[3]))}",
                  text)
    text = re.sub(r"\b(\d{1,2})[:h](\d{2})\b", lambda m: f"{read_number(int(m[1]))} giờ {read_number(int(m[2]))} phút",
                  text)
    text = re.sub(r"\d+(?:\.\d{3})+(?!\d)", lambda m: read_number(int(m[0].replace(".", ""))), text)
    text = re.sub(r"\d+", lambda m: read_number(int(m[0])), text)
    return re.sub(r"[ \t]+", " ", text).strip()
