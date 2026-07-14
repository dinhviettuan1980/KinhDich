// Hà Đồ — sơ đồ số nguyên thủy, ra đời trước Lạc Thư. 10 số chia thành 5 cặp
// "sinh số" (1-5, dương, tạo ra hành) + "thành số" (6-10, âm, hoàn thiện hành).
// Quy tắc sinh: thành số = sinh số + 5, cùng ngũ hành, cùng phương vị.

export const HA_DO_PAIRS = [
  { sinh: 1, thanh: 6, nguHanh: 'Thủy', phuongVi: 'Bắc' },
  { sinh: 2, thanh: 7, nguHanh: 'Hỏa', phuongVi: 'Nam' },
  { sinh: 3, thanh: 8, nguHanh: 'Mộc', phuongVi: 'Đông' },
  { sinh: 4, thanh: 9, nguHanh: 'Kim', phuongVi: 'Tây' },
  { sinh: 5, thanh: 10, nguHanh: 'Thổ', phuongVi: 'Trung ương' },
]

export function generateHaDoPairs() {
  // Không hardcode phần số — chỉ hardcode ngũ hành/phương vị (dữ liệu văn hoá gốc),
  // còn "thành số" luôn suy ra bằng công thức sinh + 5.
  return HA_DO_PAIRS.map((p) => ({ ...p, thanh: p.sinh + 5 }))
}
