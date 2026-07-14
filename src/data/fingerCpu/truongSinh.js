// Trường Sinh — vòng 12 giai đoạn của một "vòng đời", lặp lại tuần hoàn.
// Đây là ví dụ giáo dục tốt nhất cho khái niệm Finite State Machine: đúng 12
// trạng thái cố định, mỗi bước chuyển sang trạng thái kế tiếp theo 1 chiều duy nhất,
// hết trạng thái cuối thì quay lại trạng thái đầu — giống hệt vòng lặp Địa Chi.

export const TRUONG_SINH = [
  { index: 0, ten: 'Trường Sinh', moTa: 'Sinh ra — khởi đầu vòng đời, năng lượng còn non nớt.' },
  { index: 1, ten: 'Mộc Dục', moTa: 'Tắm gội — được chăm sóc, còn yếu ớt, dễ tổn thương.' },
  { index: 2, ten: 'Quan Đới', moTa: 'Đội mũ trưởng thành — bắt đầu định hình bản sắc riêng.' },
  { index: 3, ten: 'Lâm Quan', moTa: 'Ra làm quan — bước vào giai đoạn cống hiến, khẳng định năng lực.' },
  { index: 4, ten: 'Đế Vượng', moTa: 'Đỉnh cao — sung mãn nhất của cả vòng đời.' },
  { index: 5, ten: 'Suy', moTa: 'Bắt đầu đi xuống — năng lượng giảm dần sau đỉnh cao.' },
  { index: 6, ten: 'Bệnh', moTa: 'Ốm yếu — suy giảm rõ rệt, cần nghỉ ngơi.' },
  { index: 7, ten: 'Tử', moTa: 'Kết thúc một hình thái — không có nghĩa là hết, mà là chuyển hoá.' },
  { index: 8, ten: 'Mộ', moTa: 'Lưu trữ — kinh nghiệm và giá trị được "cất" lại, chờ tái sinh.' },
  { index: 9, ten: 'Tuyệt', moTa: 'Điểm trống hoàn toàn — trạng thái trung tính giữa 2 vòng đời.' },
  { index: 10, ten: 'Thai', moTa: 'Thai nghén — mầm mống của chu kỳ mới bắt đầu hình thành.' },
  { index: 11, ten: 'Dưỡng', moTa: 'Nuôi dưỡng — chuẩn bị đầy đủ để bước sang Trường Sinh, khép vòng.' },
]

export function truongSinhAt(index) {
  return TRUONG_SINH[((index % 12) + 12) % 12]
}
