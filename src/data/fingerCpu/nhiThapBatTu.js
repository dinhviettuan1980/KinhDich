// 28 Tú (Nhị Thập Bát Tú) — 28 chòm sao dùng để chia bầu trời, nhóm theo Tứ Tượng
// (4 nhóm × 7 sao = 28) theo 4 hướng. Cấu trúc y hệt 4 nhóm bài học (LESSON_GROUPS):
// chia một tập lớn thành các nhóm đều nhau để dễ nhớ — "chunking" trong khoa học nhận thức.

export const TU_TUONG = [
  { key: 'thanh-long', ten: 'Thanh Long', conVat: 'Rồng xanh', huong: 'Đông', tu: ['Giác', 'Cang', 'Đê', 'Phòng', 'Tâm', 'Vĩ', 'Cơ'] },
  { key: 'chu-tuoc', ten: 'Chu Tước', conVat: 'Chim đỏ', huong: 'Nam', tu: ['Tỉnh', 'Quỷ', 'Liễu', 'Tinh', 'Trương', 'Dực', 'Chẩn'] },
  { key: 'bach-ho', ten: 'Bạch Hổ', conVat: 'Hổ trắng', huong: 'Tây', tu: ['Khuê', 'Lâu', 'Vị', 'Mão', 'Tất', 'Chủy', 'Sâm'] },
  { key: 'huyen-vu', ten: 'Huyền Vũ', conVat: 'Rùa-rắn đen', huong: 'Bắc', tu: ['Đẩu', 'Ngưu', 'Nữ', 'Hư', 'Nguy', 'Thất', 'Bích'] },
]

export const NHI_THAP_BAT_TU = TU_TUONG.flatMap((group, gi) =>
  group.tu.map((ten, i) => ({ index: gi * 7 + i, ten, group: group.key, groupTen: group.ten, huong: group.huong }))
)
