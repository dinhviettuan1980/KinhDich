// 60 Hoa Giáp — KHÔNG hardcode danh sách, sinh trực tiếp bằng thuật toán.
// Đây là ví dụ kinh điển của LCM: chu kỳ Can (10) và chu kỳ Chi (12) chạy song song,
// mỗi bước cùng +1, và chỉ khi cả hai cùng quay về vị trí xuất phát thì một "vòng lớn"
// mới khép lại — đó chính là LCM(10, 12) = 60.

import { THIEN_CAN } from './thienCan'
import { DIA_CHI } from './diaChi'

export function generateHoaGiap() {
  const result = []
  for (let i = 0; i < 60; i++) {
    const can = THIEN_CAN[i % 10]
    const chi = DIA_CHI[i % 12]
    result.push({
      index: i,
      ten: `${can.ten} ${chi.ten}`,
      canIndex: i % 10,
      chiIndex: i % 12,
      can,
      chi,
    })
  }
  return result
}

export const HOA_GIAP = generateHoaGiap()

export function hoaGiapAt(index) {
  return HOA_GIAP[((index % 60) + 60) % 60]
}

// Tìm vị trí Hoa Giáp từ tên (vd "Giáp Tý" -> 0, "Bính Ngọ" -> 42)
export function hoaGiapIndexOf(ten) {
  return HOA_GIAP.findIndex((h) => h.ten === ten)
}
