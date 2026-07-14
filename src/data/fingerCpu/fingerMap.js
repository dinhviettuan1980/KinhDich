// Ánh xạ "đốt tay" ↔ chỉ số mảng — nền tảng của toàn bộ Finger CPU Lab.
//
// Quy ước: 4 ngón tay (không tính ngón cái — ngón cái đóng vai trò "con trỏ" bấm
// vào từng đốt) × 3 đốt mỗi ngón = 12 đốt = finger[0]..finger[11].
// Nhiều thầy có quy ước bấm khởi đầu khác nhau tuỳ trường phái; ở đây chọn MỘT
// quy ước cố định, nhất quán xuyên suốt module để dạy đúng bản chất "index cố định,
// tra bảng cố định" — không phải quy ước "chuẩn" duy nhất ngoài đời.

export const FINGERS = [
  { key: 'tro', label: 'Ngón trỏ' },
  { key: 'giua', label: 'Ngón giữa' },
  { key: 'apUt', label: 'Ngón áp út' },
  { key: 'ut', label: 'Ngón út' },
]

export const DOTS = [
  { key: 'duoi', label: 'Đốt dưới (gốc)' },
  { key: 'giua', label: 'Đốt giữa' },
  { key: 'tren', label: 'Đốt trên (đầu)' },
]

// index (0..11) -> { fingerIndex, dotIndex }
export function indexToPosition(index) {
  const i = ((index % 12) + 12) % 12
  return { fingerIndex: Math.floor(i / 3), dotIndex: i % 3 }
}

// { fingerIndex, dotIndex } -> index (0..11)
export function positionToIndex(fingerIndex, dotIndex) {
  return fingerIndex * 3 + dotIndex
}

export function fingerLabel(index) {
  const { fingerIndex, dotIndex } = indexToPosition(index)
  return `${FINGERS[fingerIndex].label} · ${DOTS[dotIndex].label}`
}
