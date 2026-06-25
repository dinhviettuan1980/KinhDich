// Bát Quái + nghĩa 64 quẻ — dùng để "giải mã" tên Hán-Việt cho dễ nhớ.

export const BAT_QUAI = [
  { glyph: '☰', quai: 'Càn', hinh: 'Trời', img: 'THIÊN' },
  { glyph: '☷', quai: 'Khôn', hinh: 'Đất', img: 'ĐỊA' },
  { glyph: '☵', quai: 'Khảm', hinh: 'Nước', img: 'THỦY' },
  { glyph: '☲', quai: 'Ly', hinh: 'Lửa', img: 'HỎA' },
  { glyph: '☶', quai: 'Cấn', hinh: 'Núi', img: 'SƠN' },
  { glyph: '☱', quai: 'Đoài', hinh: 'Đầm', img: 'TRẠCH' },
  { glyph: '☳', quai: 'Chấn', hinh: 'Sấm', img: 'LÔI' },
  { glyph: '☴', quai: 'Tốn', hinh: 'Gió', img: 'PHONG' },
]

const IMG = Object.fromEntries(BAT_QUAI.map((t) => [t.img, t]))

// Nghĩa ngắn (1 ý) của tên quẻ — phần thật sự cần nhớ
export const NGHIA = {
  1: 'sáng tạo, cương kiện', 2: 'thuận theo, nuôi dưỡng', 3: 'gian nan buổi đầu', 4: 'non trẻ, cần dạy dỗ',
  5: 'chờ đợi', 6: 'kiện cáo, tranh chấp', 7: 'quân đội, dụng binh', 8: 'gần gũi, liên kết',
  9: 'chứa nhỏ, kìm hãm nhẹ', 10: 'nề nếp, lễ độ', 11: 'hanh thông, thái hòa', 12: 'bế tắc, không thông',
  13: 'cùng người, hòa đồng', 14: 'có lớn, thịnh vượng', 15: 'khiêm nhường', 16: 'an vui, chuẩn bị',
  17: 'đi theo, tùy thuận', 18: 'chấn chỉnh việc hỏng', 19: 'tới gần, lớn lên', 20: 'quan sát, chiêm ngưỡng',
  21: 'cắn vỡ, trừng trị', 22: 'trang sức, văn vẻ', 23: 'bóc mòn, suy rụng', 24: 'trở lại, hồi phục',
  25: 'chân thật, không càn bậy', 26: 'chứa lớn, tích lũy', 27: 'nuôi dưỡng', 28: 'quá mức lớn',
  29: 'hiểm, vực sâu', 30: 'bám víu, sáng tỏ', 31: 'cảm ứng, giao cảm', 32: 'lâu bền',
  33: 'lui ẩn, rút lui', 34: 'lớn mạnh', 35: 'tiến lên', 36: 'ánh sáng bị che',
  37: 'người nhà, gia đạo', 38: 'chia lìa, trái nhau', 39: 'gian nan, trắc trở', 40: 'cởi bỏ, giải tỏa',
  41: 'bớt đi', 42: 'thêm vào, lợi ích', 43: 'quyết, dứt khoát', 44: 'gặp gỡ bất ngờ',
  45: 'tụ họp', 46: 'đi lên', 47: 'khốn cùng, bế tắc', 48: 'giếng nước, nuôi dân',
  49: 'thay đổi, cách mạng', 50: 'cái vạc, đổi mới', 51: 'chấn động (sấm)', 52: 'dừng lại, tĩnh',
  53: 'tiến dần', 54: 'gả em gái, lệch phối', 55: 'thịnh đại, sung mãn', 56: 'lữ hành, đất khách',
  57: 'thuận nhập, khiêm thuận', 58: 'vui đẹp, hòa duyệt', 59: 'ly tán, phân tán', 60: 'tiết chế, chừng mực',
  61: 'lòng thành tín', 62: 'quá mức nhỏ', 63: 'đã xong, đã thành', 64: 'chưa xong, chưa thành',
}

// Tách tên quẻ → { tren, duoi (quái), ten (tên riêng) }
export function decodeTen(ten) {
  const t = (ten || '').trim()
  if (/\sVI\s/.test(t)) {
    const w = t.split(/\s+/) // "THIÊN VI CÀN"
    const im = IMG[w[0]]
    return { tren: im, duoi: im, ten: w.slice(2).join(' '), thuan: true }
  }
  const w = t.split(/\s+/)
  return { tren: IMG[w[0]], duoi: IMG[w[1]], ten: w.slice(2).join(' '), thuan: false }
}
