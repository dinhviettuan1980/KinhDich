"""Âm lịch Việt Nam và can chi.

Thuật toán Hồ Ngọc Đức (https://www.informatik.uni-leipzig.de/~duc/amlich/), tính theo múi giờ UTC+7.
Đây là thuật toán được dùng rộng rãi ở Việt Nam (cũng là bản trong src/data/amlich.js của trang Kinh Dịch).
Không dùng thư viện âm lịch Trung Quốc (UTC+8) vì lệch với lịch Việt ở một số năm, ví dụ Tết 1985
(Việt Nam: 21/01/1985, Trung Quốc: 20/02/1985).
"""
from dataclasses import dataclass
from datetime import date
from math import floor, pi, sin

TZ = 7.0

CAN = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]
MONTH_NAMES = {1: "Giêng", 12: "Chạp"}


def _jd_from_date(dd: int, mm: int, yy: int) -> int:
    a = (14 - mm) // 12
    y = yy + 4800 - a
    m = mm + 12 * a - 3
    jd = dd + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    if jd < 2299161:
        jd = dd + (153 * m + 2) // 5 + 365 * y + y // 4 - 32083
    return jd


def _new_moon(k: int) -> float:
    T = k / 1236.85
    T2, T3 = T * T, T * T * T
    dr = pi / 180
    Jd1 = 2415020.75933 + 29.53058868 * k + 0.0001178 * T2 - 0.000000155 * T3
    Jd1 += 0.00033 * sin((166.56 + 132.87 * T - 0.009173 * T2) * dr)
    M = 359.2242 + 29.10535608 * k - 0.0000333 * T2 - 0.00000347 * T3
    Mpr = 306.0253 + 385.81691806 * k + 0.0107306 * T2 + 0.00001236 * T3
    F = 21.2964 + 390.67050646 * k - 0.0016528 * T2 - 0.00000239 * T3
    C1 = (0.1734 - 0.000393 * T) * sin(M * dr) + 0.0021 * sin(2 * dr * M)
    C1 = C1 - 0.4068 * sin(Mpr * dr) + 0.0161 * sin(dr * 2 * Mpr)
    C1 = C1 - 0.0004 * sin(dr * 3 * Mpr)
    C1 = C1 + 0.0104 * sin(dr * 2 * F) - 0.0051 * sin(dr * (M + Mpr))
    C1 = C1 - 0.0074 * sin(dr * (M - Mpr)) + 0.0004 * sin(dr * (2 * F + M))
    C1 = C1 - 0.0004 * sin(dr * (2 * F - M)) - 0.0006 * sin(dr * (2 * F + Mpr))
    C1 = C1 + 0.0010 * sin(dr * (2 * F - Mpr)) + 0.0005 * sin(dr * (2 * Mpr + M))
    if T < -11:
        deltat = 0.001 + 0.000839 * T + 0.0002261 * T2 - 0.00000845 * T3 - 0.000000081 * T * T3
    else:
        deltat = -0.000278 + 0.000265 * T + 0.000262 * T2
    return Jd1 + C1 - deltat


def _sun_longitude(jdn: float) -> float:
    T = (jdn - 2451545.0) / 36525
    T2 = T * T
    dr = pi / 180
    M = 357.52910 + 35999.05030 * T - 0.0001559 * T2 - 0.00000048 * T * T2
    L0 = 280.46645 + 36000.76983 * T + 0.0003032 * T2
    DL = (1.914600 - 0.004817 * T - 0.000014 * T2) * sin(dr * M)
    DL += (0.019993 - 0.000101 * T) * sin(dr * 2 * M) + 0.000290 * sin(dr * 3 * M)
    L = (L0 + DL) * dr
    return L - pi * 2 * floor(L / (pi * 2))


def _new_moon_day(k: int, tz: float = TZ) -> int:
    return floor(_new_moon(k) + 0.5 + tz / 24)


def _sun_long_sector(day_number: int, tz: float = TZ) -> int:
    return floor(_sun_longitude(day_number - 0.5 - tz / 24) / pi * 6)


def _lunar_month11(yy: int, tz: float = TZ) -> int:
    off = _jd_from_date(31, 12, yy) - 2415021
    k = floor(off / 29.530588853)
    nm = _new_moon_day(k, tz)
    if _sun_long_sector(nm, tz) >= 9:
        nm = _new_moon_day(k - 1, tz)
    return nm


def _leap_month_offset(a11: int, tz: float = TZ) -> int:
    k = floor((a11 - 2415021.076998695) / 29.530588853 + 0.5)
    i = 1
    arc = _sun_long_sector(_new_moon_day(k + i, tz), tz)
    while True:
        last = arc
        i += 1
        arc = _sun_long_sector(_new_moon_day(k + i, tz), tz)
        if arc == last or i >= 14:
            break
    return i - 1


@dataclass(frozen=True)
class LunarDate:
    day: int
    month: int
    year: int
    leap: bool

    @property
    def year_can_chi(self) -> str:
        return can_chi_year(self.year)

    def text(self) -> str:
        """Ví dụ: 'mùng 1 tháng Giêng năm Bính Ngọ', '15 tháng 6 nhuận năm Ất Tỵ'.
        Không có chữ 'ngày' ở đầu vì mẫu sớ viết 'Hôm nay là ngày {ngay_am}'."""
        d = f"mùng {self.day}" if self.day <= 10 else str(self.day)
        m = MONTH_NAMES.get(self.month, str(self.month))
        return f"{d} tháng {m}{' nhuận' if self.leap else ''} năm {self.year_can_chi}"

    def short(self) -> str:
        return f"{self.day}/{self.month}{' nhuận' if self.leap else ''} âm lịch"


def solar_to_lunar(d: date, tz: float = TZ) -> LunarDate:
    day_number = _jd_from_date(d.day, d.month, d.year)
    k = floor((day_number - 2415021.076998695) / 29.530588853)
    month_start = _new_moon_day(k + 1, tz)
    if month_start > day_number:
        month_start = _new_moon_day(k, tz)
    a11 = _lunar_month11(d.year, tz)
    b11 = a11
    if a11 >= month_start:
        lunar_year = d.year
        a11 = _lunar_month11(d.year - 1, tz)
    else:
        lunar_year = d.year + 1
        b11 = _lunar_month11(d.year + 1, tz)
    lunar_day = day_number - month_start + 1
    diff = floor((month_start - a11) / 29)
    leap = False
    lunar_month = diff + 11
    if b11 - a11 > 365:
        leap_diff = _leap_month_offset(a11, tz)
        if diff >= leap_diff:
            lunar_month = diff + 10
            if diff == leap_diff:
                leap = True
    if lunar_month > 12:
        lunar_month -= 12
    if lunar_month >= 11 and diff < 4:
        lunar_year -= 1
    return LunarDate(lunar_day, lunar_month, lunar_year, leap)


def can_chi_year(year: int) -> str:
    """Can chi của năm (âm lịch). 1990 → Canh Ngọ, 2026 → Bính Ngọ."""
    return f"{CAN[(year + 6) % 10]} {CHI[(year + 8) % 12]}"


def solar_text(d: date) -> str:
    return f"ngày {d.day} tháng {d.month} năm {d.year}"
