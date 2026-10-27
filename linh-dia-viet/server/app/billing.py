"""Thẻ thanh toán GIẢ LẬP (chưa nối cổng thật). Giai đoạn thử nghiệm: gõ gì cũng nhận — không kiểm tra số thẻ,
hạn, CVC; trừ tiền luôn thành công. Chỉ lưu hãng (đoán theo số đầu) + 4 số cuối + hạn, không lưu số đầy đủ / CVC."""
import re


class CardError(ValueError):
    pass


def brand_of(num: str) -> str:
    if num.startswith("4"):
        return "Visa"
    if re.match(r"5[1-5]|2(2[2-9]|[3-6]\d|7[01]|720)", num):
        return "Mastercard"
    if num.startswith("35"):
        return "JCB"
    if re.match(r"3[47]", num):
        return "Amex"
    if num.startswith("9704"):
        return "Napas"
    return "Thẻ"


def parse_card(number: str, exp: str, cvc: str, holder: str) -> dict:
    """→ {"brand", "last4", "exp", "holder"}. Chỉ cần ô số thẻ không để trống."""
    if not (number or "").strip():
        raise CardError("Vui lòng nhập số thẻ (bản thử nghiệm: gõ số bất kỳ).")
    digits = re.sub(r"\D", "", number)
    last4 = (digits[-4:] if digits else "").rjust(4, "0")
    exp = re.sub(r"\s+", "", exp or "")[:5]
    holder = re.sub(r"\s+", " ", (holder or "").strip()).upper()[:120]
    return {"brand": brand_of(digits), "last4": last4, "exp": exp or "--/--", "holder": holder}


def charge(user, amount: int) -> tuple[bool, str]:
    """Trừ tiền giả lập vào thẻ đã lưu. → (thành công?, lý do nếu lỗi)."""
    if not user.card_last4:
        return False, "Chưa có thẻ thanh toán."
    if amount <= 0:
        return False, "Số tiền không hợp lệ."
    return True, ""
