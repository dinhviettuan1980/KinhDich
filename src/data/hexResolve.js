// Nhận diện tên quẻ từ chuỗi người dùng gõ -> trả về quẻ trong HEXAGRAMS + tên trong sách.
// Mục tiêu: gõ kiểu nào (Càn / Kiền / Thuần Càn / Càn vi Thiên / Thủy Lôi Truân / số 1 ...) cũng ra đúng.
import { HEXAGRAMS } from './hexagrams'

// Tên quẻ theo SÁCH Ngô Tất Tố, theo thứ tự id 1..64 (để gọi /kinhdich/hexagram/:name)
export const BOOK_NAMES = [
  'Kiền', 'Khôn', 'Truân', 'Mông', 'Nhu', 'Tụng', 'Sư', 'Tỵ',
  'Tiểu Súc', 'Lý', 'Thái', 'Bĩ', 'Đồng Nhân', 'Đại Hữu', 'Khiêm', 'Dự',
  'Tùy', 'Cổ', 'Lâm', 'Quán', 'Phệ Hạp', 'Bí', 'Bác', 'Phục',
  'Vô Vọng', 'Đại Súc', 'Di', 'Đại Quá', 'Tập Khảm', 'Ly', 'Hàm', 'Hằng',
  'Độn', 'Đại Tráng', 'Tấn', 'Minh Di', 'Gia Nhân', 'Khuê', 'Kiển', 'Giải',
  'Tổn', 'Ích', 'Quải', 'Cấu', 'Tụy', 'Thăng', 'Khốn', 'Tỉnh',
  'Cách', 'Đỉnh', 'Chấn', 'Cấn', 'Tiệm', 'Qui Muội', 'Phong', 'Lữ',
  'Tốn', 'Đoái', 'Hoán', 'Tiết', 'Trung Phu', 'Tiểu Quá', 'Ký Tế', 'Vị Tế',
]

// Tên gọi khác cho 8 quẻ "thuần" (giữ dấu — vì bỏ dấu sẽ đụng Càn/Cấn, v.v.)
const ALIASES = [
  ['càn', 1], ['kiền', 1], ['càn vi thiên', 1], ['thiên vi càn', 1],
  ['khôn', 2], ['côn', 2], ['khôn vi địa', 2], ['địa vi khôn', 2],
  ['khảm', 29], ['khảm vi thủy', 29],
  ['ly', 30], ['ly vi hỏa', 30],
  ['chấn', 51], ['chấn vi lôi', 51],
  ['cấn', 52], ['cấn vi sơn', 52],
  ['tốn', 57], ['tốn vi phong', 57],
  ['đoài', 58], ['đoái', 58], ['đoài vi trạch', 58],
]

const FILLER_ND = new Set(['quẻ', 'quái', 'bát', 'thuần', 'kinh', 'dịch', 'số', 'hào'])
const FILLER_NN = new Set(['que', 'quai', 'bat', 'thuan', 'kinh', 'dich', 'so', 'hao'])

const nd = (s) => (s || '').toLowerCase().replace(/\s+/g, ' ').trim() // giữ dấu
const nn = (s) => nd(s).normalize('NFD').replace(/[̀-ͯ]/g, '')
  .replace(/đ/g, 'd').replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim() // bỏ dấu

const stripND = (s) => nd(s).split(' ').filter((w) => w && !FILLER_ND.has(w) && !/^\d+$/.test(w)).join(' ')
const stripNN = (s) => nn(s).split(' ').filter((w) => w && !FILLER_NN.has(w) && !/^\d+$/.test(w)).join(' ')

// Xây 2 bảng tra: exact (giữ dấu) và loose (bỏ dấu, chỉ dùng khi không nhập nhằng)
const exactMap = new Map()
const looseMap = new Map() // key -> Set(id)
function add(name, id) {
  const k = stripND(name)
  if (k && !exactMap.has(k)) exactMap.set(k, id)
  const kk = stripNN(name)
  if (kk) {
    if (!looseMap.has(kk)) looseMap.set(kk, new Set())
    looseMap.get(kk).add(id)
  }
}
ALIASES.forEach(([n, id]) => add(n, id))
BOOK_NAMES.forEach((n, i) => add(n, i + 1))
HEXAGRAMS.forEach((h) => add(h.name, h.id))

function scan(map, str, loose) {
  const toks = str.split(' ').filter(Boolean)
  for (let n = Math.min(4, toks.length); n >= 1; n--) {
    for (let i = 0; i + n <= toks.length; i++) {
      const key = toks.slice(i, i + n).join(' ')
      const v = map.get(key)
      if (v === undefined) continue
      if (loose) { if (v.size === 1) return [...v][0] }
      else return v
    }
  }
  return null
}

// Trả về { hex, bookName } nếu query trông như TÊN quẻ; ngược lại null (để dùng semantic search).
export function resolveHexagram(query) {
  const q = (query || '').trim()
  if (!q) return null

  // "quẻ 1", "số 29", hoặc chỉ một con số 1..64
  const numMatch = nn(q).match(/(?:^|\s)(\d{1,2})(?:\s|$)/)
  const wordsND = stripND(q).split(' ').filter(Boolean)

  let id = null
  // chỉ coi là tra-theo-tên khi câu ngắn (<=4 từ), tránh nuốt nhầm câu hỏi dài
  if (wordsND.length > 0 && wordsND.length <= 4) {
    id = scan(exactMap, stripND(q), false) || scan(looseMap, stripNN(q), true)
  }
  if (!id && numMatch) {
    const n = Number(numMatch[1])
    if (n >= 1 && n <= 64) id = n
  }
  if (!id) return null

  const hex = HEXAGRAMS.find((h) => h.id === id)
  return hex ? { hex, bookName: BOOK_NAMES[id - 1] } : null
}
