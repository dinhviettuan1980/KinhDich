// Registry của toàn bộ 25 bài học Finger CPU Lab.
// `status: 'ready'` -> có component riêng trong src/components/fingerCpu/lessons/
// `status: 'soon'`  -> chưa có nội dung, FingerCpuLessonPage hiển thị placeholder.
// Xem TODO.md để biết bài nào thuộc phase nào.

export const LESSON_GROUPS = [
  {
    key: 'nen-tang',
    title: 'Nền tảng',
    lessonIds: [1, 2, 3, 4, 5],
  },
  {
    key: 'cau-truc-du-lieu',
    title: 'Cấu trúc dữ liệu & toán học',
    lessonIds: [6, 7, 8, 9],
  },
  {
    key: 'he-thong-mo-rong',
    title: 'Các hệ thống mở rộng',
    lessonIds: [10, 11, 12, 13, 14, 15],
  },
  {
    key: 'tong-hop',
    title: 'Tổng hợp & so sánh CPU',
    lessonIds: [16, 17, 18, 19, 20, 21],
  },
  {
    key: 'code-mode',
    title: 'Code Mode',
    lessonIds: [22, 23, 24, 25],
  },
]

export const LESSONS = [
  { id: 1, slug: 'tai-sao-bam-ngon-tay', title: 'Tại sao phải bấm ngón tay?', subtitle: 'Bàn tay = RAM di động của người xưa', status: 'ready' },
  { id: 2, slug: 'ban-tay-thanh-array', title: 'Biến bàn tay thành Array', subtitle: 'finger[0] .. finger[11]', status: 'ready' },
  { id: 3, slug: 'lookup-table', title: 'Lookup Table', subtitle: 'index → tên → ý nghĩa', status: 'ready' },
  { id: 4, slug: '12-dia-chi', title: '12 Địa Chi', subtitle: 'Bảng tra cứu 12 phần tử', status: 'ready' },
  { id: 5, slug: '10-thien-can', title: '10 Thiên Can', subtitle: 'Bảng tra cứu 10 phần tử', status: 'ready' },
  { id: 6, slug: '60-hoa-giap', title: '60 Hoa Giáp', subtitle: 'LCM(10, 12) = 60', status: 'ready' },
  { id: 7, slug: 'modulo', title: 'Modulo', subtitle: '(start + offset) % 12', status: 'ready' },
  { id: 8, slug: 'bat-quai', title: 'Bát Quái', subtitle: '8 trạng thái, 3 bit', status: 'ready' },
  { id: 9, slug: '64-que', title: '64 Quẻ', subtitle: 'Ma trận 8 × 8', status: 'ready' },
  { id: 10, slug: 'lac-thu', title: 'Lạc Thư', subtitle: 'Ma trận 3×3, tổng mỗi hàng = 15', status: 'ready' },
  { id: 11, slug: 'ha-do', title: 'Hà Đồ', subtitle: 'Sơ đồ số nguyên thủy', status: 'ready' },
  { id: 12, slug: 'cuu-cung', title: 'Cửu Cung', subtitle: '9 vùng nhớ tương tác', status: 'ready' },
  { id: 13, slug: '24-tiet-khi', title: '24 Tiết Khí', subtitle: 'Timeline chu kỳ mặt trời', status: 'ready' },
  { id: 14, slug: '28-tu', title: '28 Tú', subtitle: 'Bảng tra 28 sao', status: 'ready' },
  { id: 15, slug: 'truong-sinh', title: 'Trường Sinh', subtitle: '12 giai đoạn vòng đời', status: 'ready' },
  { id: 16, slug: 'mai-hoa-dich-so', title: 'Mai Hoa Dịch Số', subtitle: 'Giải thích thuật toán', status: 'ready' },
  { id: 17, slug: 'luc-nham', title: 'Lục Nhâm', subtitle: 'Giới thiệu', status: 'ready' },
  { id: 18, slug: 'ky-mon', title: 'Kỳ Môn', subtitle: 'Giới thiệu', status: 'ready' },
  { id: 19, slug: 'thai-at', title: 'Thái Ất', subtitle: 'Giới thiệu', status: 'ready' },
  { id: 20, slug: 'data-flow', title: 'Thực sự các thầy đang làm gì?', subtitle: 'Can → Chi → Lookup → Modulo → Lookup → Quẻ', status: 'ready' },
  { id: 21, slug: 'cpu-vs-nguoi-xua', title: 'CPU vs Người xưa', subtitle: 'Register/RAM/Cache/Pointer ↔ Ngón/Đốt/Lookup/Quy tắc', status: 'ready' },
  { id: 22, slug: 'code-java', title: 'Java', subtitle: 'Cài đặt bằng Java', status: 'ready' },
  { id: 23, slug: 'code-javascript', title: 'JavaScript', subtitle: 'Cài đặt bằng JavaScript', status: 'ready' },
  { id: 24, slug: 'code-python', title: 'Python', subtitle: 'Cài đặt bằng Python', status: 'ready' },
  { id: 25, slug: 'tong-ket', title: 'Tổng kết', subtitle: 'Không phải phép thuật — là Memory Mapping', status: 'ready' },
]

export const LESSON_BY_ID = Object.fromEntries(LESSONS.map((l) => [l.id, l]))

export function lessonNeighbors(id) {
  const n = Number(id)
  return {
    prev: LESSON_BY_ID[n - 1] || null,
    next: LESSON_BY_ID[n + 1] || null,
  }
}
