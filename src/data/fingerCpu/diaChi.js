// 12 Địa Chi — lookup table đầy đủ, index = vị trí trong finger[0]..finger[11].
// Đây chính là "mảng dữ liệu" mà bàn tay ánh xạ tới (xem fingerMap.js).

export const DIA_CHI = [
  { index: 0, ten: 'Tý', conGiap: 'Chuột', nguHanh: 'Thủy', amDuong: 'Dương', phuongVi: 'Chính Bắc', gio: '23h–1h', mua: 'Đông (tháng 11 âm)', dacDiem: 'Khởi đầu chu kỳ — giờ Tý là mốc 0 của đồng hồ 12 chi.' },
  { index: 1, ten: 'Sửu', conGiap: 'Trâu', nguHanh: 'Thổ', amDuong: 'Âm', phuongVi: 'Bắc Đông Bắc', gio: '1h–3h', mua: 'Đông (tháng 12 âm)', dacDiem: 'Thổ chuyển tiếp cuối mùa Đông, chuẩn bị sang Xuân.' },
  { index: 2, ten: 'Dần', conGiap: 'Hổ', nguHanh: 'Mộc', amDuong: 'Dương', phuongVi: 'Đông Bắc', gio: '3h–5h', mua: 'Xuân (tháng 1 âm)', dacDiem: 'Mộc bắt đầu vượng — tháng đầu năm âm lịch.' },
  { index: 3, ten: 'Mão', conGiap: 'Mèo', nguHanh: 'Mộc', amDuong: 'Âm', phuongVi: 'Chính Đông', gio: '5h–7h', mua: 'Xuân (tháng 2 âm)', dacDiem: 'Mộc thịnh nhất — giữa mùa Xuân.' },
  { index: 4, ten: 'Thìn', conGiap: 'Rồng', nguHanh: 'Thổ', amDuong: 'Dương', phuongVi: 'Đông Nam', gio: '7h–9h', mua: 'Xuân (tháng 3 âm)', dacDiem: 'Con giáp duy nhất không có thật ngoài đời — biểu tượng.' },
  { index: 5, ten: 'Tỵ', conGiap: 'Rắn', nguHanh: 'Hỏa', amDuong: 'Âm', phuongVi: 'Đông Nam', gio: '9h–11h', mua: 'Hạ (tháng 4 âm)', dacDiem: 'Hỏa bắt đầu vượng — mở đầu mùa Hạ.' },
  { index: 6, ten: 'Ngọ', conGiap: 'Ngựa', nguHanh: 'Hỏa', amDuong: 'Dương', phuongVi: 'Chính Nam', gio: '11h–13h', mua: 'Hạ (tháng 5 âm)', dacDiem: 'Đối xứng với Tý qua tâm vòng tròn 12 chi — giữa trưa, giữa Hạ.' },
  { index: 7, ten: 'Mùi', conGiap: 'Dê', nguHanh: 'Thổ', amDuong: 'Âm', phuongVi: 'Tây Nam', gio: '13h–15h', mua: 'Hạ (tháng 6 âm)', dacDiem: 'Thổ chuyển tiếp cuối mùa Hạ.' },
  { index: 8, ten: 'Thân', conGiap: 'Khỉ', nguHanh: 'Kim', amDuong: 'Dương', phuongVi: 'Tây Nam', gio: '15h–17h', mua: 'Thu (tháng 7 âm)', dacDiem: 'Kim bắt đầu vượng — mở đầu mùa Thu.' },
  { index: 9, ten: 'Dậu', conGiap: 'Gà', nguHanh: 'Kim', amDuong: 'Âm', phuongVi: 'Chính Tây', gio: '17h–19h', mua: 'Thu (tháng 8 âm)', dacDiem: 'Kim thịnh nhất — giữa mùa Thu.' },
  { index: 10, ten: 'Tuất', conGiap: 'Chó', nguHanh: 'Thổ', amDuong: 'Dương', phuongVi: 'Tây Bắc', gio: '19h–21h', mua: 'Thu (tháng 9 âm)', dacDiem: 'Thổ chuyển tiếp cuối mùa Thu.' },
  { index: 11, ten: 'Hợi', conGiap: 'Heo', nguHanh: 'Thủy', amDuong: 'Âm', phuongVi: 'Tây Bắc', gio: '21h–23h', mua: 'Đông (tháng 10 âm)', dacDiem: 'Cuối chu kỳ 12 chi — sau Hợi quay lại Tý (giống mảng vòng, circular array).' },
]

export const DIA_CHI_BY_TEN = Object.fromEntries(DIA_CHI.map((c) => [c.ten, c]))

export function diaChiAt(index) {
  return DIA_CHI[((index % 12) + 12) % 12]
}
