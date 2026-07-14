// Lạc Thư — ma trận vuông kỳ diệu 3×3 (Magic Square): mọi hàng, cột, đường chéo
// đều cộng lại bằng 15. Đây là nền tảng cho Cửu Cung (bài 12).

export const LAC_THU_GRID = [
  [{ number: 4, directionVi: 'Đông Nam' }, { number: 9, directionVi: 'Nam' }, { number: 2, directionVi: 'Tây Nam' }],
  [{ number: 3, directionVi: 'Đông' }, { number: 5, directionVi: 'Trung ương' }, { number: 7, directionVi: 'Tây' }],
  [{ number: 8, directionVi: 'Đông Bắc' }, { number: 1, directionVi: 'Bắc' }, { number: 6, directionVi: 'Tây Bắc' }],
]

export const LAC_THU_FLAT = LAC_THU_GRID.flat()

export function magicSquareSums(grid = LAC_THU_GRID) {
  const rows = grid.map((row) => row.reduce((s, c) => s + c.number, 0))
  const cols = [0, 1, 2].map((c) => grid.reduce((s, row) => s + row[c].number, 0))
  const diag1 = grid[0][0].number + grid[1][1].number + grid[2][2].number
  const diag2 = grid[0][2].number + grid[1][1].number + grid[2][0].number
  return { rows, cols, diagonals: [diag1, diag2] }
}
