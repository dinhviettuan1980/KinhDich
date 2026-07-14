// 10 Thiên Can — lookup table thứ hai, chu kỳ 10 (khác chu kỳ 12 của Địa Chi).
// Chính sự lệch chu kỳ 10 vs 12 này tạo ra 60 Hoa Giáp (xem hoaGiap.js, LCM(10,12)=60).

export const THIEN_CAN = [
  { index: 0, ten: 'Giáp', nguHanh: 'Mộc', amDuong: 'Dương', dacDiem: 'Mộc lớn, cứng cáp — như cây cổ thụ.' },
  { index: 1, ten: 'Ất', nguHanh: 'Mộc', amDuong: 'Âm', dacDiem: 'Mộc nhỏ, mềm dẻo — như dây leo, cỏ cây.' },
  { index: 2, ten: 'Bính', nguHanh: 'Hỏa', amDuong: 'Dương', dacDiem: 'Hỏa lớn, rực rỡ — như mặt trời.' },
  { index: 3, ten: 'Đinh', nguHanh: 'Hỏa', amDuong: 'Âm', dacDiem: 'Hỏa nhỏ, âm ỉ — như ngọn nến, đèn dầu.' },
  { index: 4, ten: 'Mậu', nguHanh: 'Thổ', amDuong: 'Dương', dacDiem: 'Thổ lớn, vững chắc — như núi, đê cao.' },
  { index: 5, ten: 'Kỷ', nguHanh: 'Thổ', amDuong: 'Âm', dacDiem: 'Thổ nhỏ, mềm — như đất ruộng, đất vườn.' },
  { index: 6, ten: 'Canh', nguHanh: 'Kim', amDuong: 'Dương', dacDiem: 'Kim lớn, sắc bén — như đao kiếm, kim loại thô.' },
  { index: 7, ten: 'Tân', nguHanh: 'Kim', amDuong: 'Âm', dacDiem: 'Kim nhỏ, tinh xảo — như trang sức, kim loại quý.' },
  { index: 8, ten: 'Nhâm', nguHanh: 'Thủy', amDuong: 'Dương', dacDiem: 'Thủy lớn, mạnh mẽ — như sông, biển.' },
  { index: 9, ten: 'Quý', nguHanh: 'Thủy', amDuong: 'Âm', dacDiem: 'Thủy nhỏ, mềm — như sương, mưa.' },
]

export const THIEN_CAN_BY_TEN = Object.fromEntries(THIEN_CAN.map((c) => [c.ten, c]))

export function thienCanAt(index) {
  return THIEN_CAN[((index % 10) + 10) % 10]
}
