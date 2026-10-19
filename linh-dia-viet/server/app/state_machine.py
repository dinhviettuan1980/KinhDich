"""Máy trạng thái đơn hàng — nơi DUY NHẤT định nghĩa chuyển trạng thái hợp lệ.

Luồng chính:
  created → awaiting_payment → paid → scheduled → delivered → playing → played → evidence_received → completed
Nhánh phụ: rejected (đền từ chối), failed (thiết bị lỗi/offline quá hạn), cancelled, refund_requested, refunded.
"""
from enum import StrEnum


class OrderStatus(StrEnum):
    CREATED = "created"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    SCHEDULED = "scheduled"
    DELIVERED = "delivered"
    PLAYING = "playing"
    PLAYED = "played"
    EVIDENCE_RECEIVED = "evidence_received"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUND_REQUESTED = "refund_requested"
    REFUNDED = "refunded"


S = OrderStatus

MAIN_LINE = [S.CREATED, S.AWAITING_PAYMENT, S.PAID, S.SCHEDULED, S.DELIVERED, S.PLAYING, S.PLAYED,
             S.EVIDENCE_RECEIVED, S.COMPLETED]

TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    S.CREATED: {S.AWAITING_PAYMENT, S.CANCELLED},
    S.AWAITING_PAYMENT: {S.PAID, S.CANCELLED},
    # paid → scheduled khi bài khấn đã được duyệt và đơn được xếp lịch cho thiết bị
    S.PAID: {S.SCHEDULED, S.CANCELLED, S.REJECTED},
    S.SCHEDULED: {S.DELIVERED, S.CANCELLED, S.REJECTED, S.FAILED},
    S.DELIVERED: {S.PLAYING, S.FAILED},
    S.PLAYING: {S.PLAYED, S.FAILED},
    # played → completed trực tiếp khi hết thời gian chờ ảnh (camera lỗi): xem DECISIONS.md
    S.PLAYED: {S.EVIDENCE_RECEIVED, S.COMPLETED},
    S.EVIDENCE_RECEIVED: {S.COMPLETED},
    S.COMPLETED: set(),
    S.REJECTED: {S.REFUND_REQUESTED},
    # failed → scheduled: admin "gửi lại job"
    S.FAILED: {S.SCHEDULED, S.REFUND_REQUESTED},
    S.CANCELLED: {S.REFUND_REQUESTED},
    S.REFUND_REQUESTED: {S.REFUNDED},
    S.REFUNDED: set(),
}

# Các trạng thái mà khách được tự hủy (trước khi lệnh được giao xuống thiết bị).
USER_CANCELLABLE = {S.CREATED, S.AWAITING_PAYMENT, S.PAID, S.SCHEDULED}
# Đã thu tiền → hủy/từ chối/lỗi thì tự chuyển sang refund_requested.
PAID_STATES = {S.PAID, S.SCHEDULED}
TERMINAL = {S.COMPLETED, S.REFUNDED} | {s for s, nxt in TRANSITIONS.items() if not nxt}
ACTIVE_DEVICE_STATES = {S.SCHEDULED, S.DELIVERED, S.PLAYING}

LABELS = {
    S.CREATED: "Đã tạo", S.AWAITING_PAYMENT: "Chờ thanh toán", S.PAID: "Đã thanh toán",
    S.SCHEDULED: "Đã xếp lịch", S.DELIVERED: "Thiết bị đã nhận lệnh", S.PLAYING: "Đang phát bài khấn",
    S.PLAYED: "Đã phát xong", S.EVIDENCE_RECEIVED: "Đã nhận ảnh mâm lễ", S.COMPLETED: "Hoàn tất",
    S.REJECTED: "Đền từ chối", S.FAILED: "Lỗi thiết bị", S.CANCELLED: "Đã hủy",
    S.REFUND_REQUESTED: "Chờ hoàn tiền", S.REFUNDED: "Đã hoàn tiền",
}


class InvalidTransition(Exception):
    def __init__(self, src, dst):
        super().__init__(f"Không thể chuyển trạng thái {src} → {dst}")
        self.src, self.dst = src, dst


def can_transition(src: str, dst: str) -> bool:
    return S(dst) in TRANSITIONS[S(src)]


def check_transition(src: str, dst: str) -> None:
    if not can_transition(src, dst):
        raise InvalidTransition(src, dst)


def path_forward(src: str, dst: str) -> list[OrderStatus]:
    """Các bước trên luồng chính để đi từ src tới dst (không gồm src).

    Dùng khi ACK từ thiết bị đến bù/lệch thứ tự (vd nhận 'done' khi đơn mới ở 'delivered').
    Trả về [] nếu dst không nằm phía sau src trên luồng chính.
    """
    src, dst = S(src), S(dst)
    if src not in MAIN_LINE or dst not in MAIN_LINE:
        return []
    i, j = MAIN_LINE.index(src), MAIN_LINE.index(dst)
    return MAIN_LINE[i + 1:j + 1] if j > i else []
