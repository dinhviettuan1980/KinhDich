// 5 khái niệm CPU dùng cho Memory Visualizer — mỗi khái niệm map sang 1 hành vi tương tác
// cụ thể trên bàn tay, thay vì chỉ mô tả bằng chữ (xem MemoryVisualizerPage.jsx).
export const MEMORY_CONCEPTS = [
  { key: 'ram', ten: 'RAM', icon: '💾', moTa: 'Toàn bộ 12 đốt tay là không gian lưu trữ cố định — luôn có sẵn, không cần "cấp phát".' },
  { key: 'pointer', ten: 'Pointer', icon: '👉', moTa: 'Ngón tay cái trỏ tới đúng 1 đốt tại 1 thời điểm — luôn chỉ có 1 con trỏ đang hoạt động.' },
  { key: 'array', ten: 'Array', icon: '🗂️', moTa: '12 đốt được đánh số liên tục 0..11 — truy cập trực tiếp theo chỉ số, không cần tìm kiếm.' },
  { key: 'hashmap', ten: 'HashMap', icon: '🔑', moTa: 'Tra theo TÊN thay vì vị trí — nhập "Tỵ" để tìm ngược lại đốt số mấy.' },
  { key: 'cache', ten: 'Cache', icon: '⚡', moTa: 'Những đốt vừa tra gần nhất được "nhớ nhanh" — không cần dò lại từ đầu.' },
]
