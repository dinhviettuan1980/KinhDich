// 24 Tiết Khí — chia đều vòng quay Trái Đất quanh Mặt Trời thành 24 đoạn ~15 ngày.
// Ngày dương lịch dưới đây là GẦN ĐÚNG (lệch 1 ngày tuỳ năm do làm tròn lịch),
// mục đích minh hoạ concept "timeline chu kỳ cố định", không dùng để tính lịch chính xác.

export const TIET_KHI = [
  { index: 0, ten: 'Lập Xuân', ngayDuongLich: '4/2', mua: 'Xuân' },
  { index: 1, ten: 'Vũ Thủy', ngayDuongLich: '19/2', mua: 'Xuân' },
  { index: 2, ten: 'Kinh Trập', ngayDuongLich: '6/3', mua: 'Xuân' },
  { index: 3, ten: 'Xuân Phân', ngayDuongLich: '21/3', mua: 'Xuân' },
  { index: 4, ten: 'Thanh Minh', ngayDuongLich: '5/4', mua: 'Xuân' },
  { index: 5, ten: 'Cốc Vũ', ngayDuongLich: '20/4', mua: 'Xuân' },
  { index: 6, ten: 'Lập Hạ', ngayDuongLich: '6/5', mua: 'Hạ' },
  { index: 7, ten: 'Tiểu Mãn', ngayDuongLich: '21/5', mua: 'Hạ' },
  { index: 8, ten: 'Mang Chủng', ngayDuongLich: '6/6', mua: 'Hạ' },
  { index: 9, ten: 'Hạ Chí', ngayDuongLich: '21/6', mua: 'Hạ' },
  { index: 10, ten: 'Tiểu Thử', ngayDuongLich: '7/7', mua: 'Hạ' },
  { index: 11, ten: 'Đại Thử', ngayDuongLich: '23/7', mua: 'Hạ' },
  { index: 12, ten: 'Lập Thu', ngayDuongLich: '8/8', mua: 'Thu' },
  { index: 13, ten: 'Xử Thử', ngayDuongLich: '23/8', mua: 'Thu' },
  { index: 14, ten: 'Bạch Lộ', ngayDuongLich: '8/9', mua: 'Thu' },
  { index: 15, ten: 'Thu Phân', ngayDuongLich: '23/9', mua: 'Thu' },
  { index: 16, ten: 'Hàn Lộ', ngayDuongLich: '8/10', mua: 'Thu' },
  { index: 17, ten: 'Sương Giáng', ngayDuongLich: '23/10', mua: 'Thu' },
  { index: 18, ten: 'Lập Đông', ngayDuongLich: '7/11', mua: 'Đông' },
  { index: 19, ten: 'Tiểu Tuyết', ngayDuongLich: '22/11', mua: 'Đông' },
  { index: 20, ten: 'Đại Tuyết', ngayDuongLich: '7/12', mua: 'Đông' },
  { index: 21, ten: 'Đông Chí', ngayDuongLich: '22/12', mua: 'Đông' },
  { index: 22, ten: 'Tiểu Hàn', ngayDuongLich: '6/1', mua: 'Đông' },
  { index: 23, ten: 'Đại Hàn', ngayDuongLich: '20/1', mua: 'Đông' },
]

export const TIET_KHI_BY_MUA = ['Xuân', 'Hạ', 'Thu', 'Đông'].map((mua) => ({
  mua,
  items: TIET_KHI.filter((t) => t.mua === mua),
}))
