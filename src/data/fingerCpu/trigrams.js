// Cầu nối giữa 2 nguồn dữ liệu quái đã có sẵn trong app:
//  - baquai.js      → tên Việt, hình tượng (Càn/Trời...) dùng để hiển thị đẹp
//  - hexagrams.js    → khoá pinyin (qian/kun/...) dùng cho lookupHexagram (64 quẻ)
// TRIGRAMS ở đây sắp xếp theo giá trị nhị phân 0..7 (hào dưới = bit thấp nhất),
// đúng quy tắc identifyTrigram() đã dùng trong hexagrams.js — không phát minh quy ước mới.

import { BAT_QUAI } from '../baquai'

const PINYIN_BY_QUAI = {
  Khôn: 'kun', Chấn: 'zhen', Khảm: 'kan', Đoài: 'dui',
  Cấn: 'gen', Ly: 'li', Tốn: 'xun', Càn: 'qian',
}

// Thứ tự nhị phân chuẩn (Phục Hy): key = hào1 + hào2*2 + hào3*4 (0=âm, 1=dương)
const BINARY_ORDER = ['Khôn', 'Chấn', 'Khảm', 'Đoài', 'Cấn', 'Ly', 'Tốn', 'Càn']

const BY_QUAI = Object.fromEntries(BAT_QUAI.map((t) => [t.quai, t]))

export const TRIGRAMS = BINARY_ORDER.map((quaiTen, value) => {
  const base = BY_QUAI[quaiTen]
  const bits = [value & 1, (value >> 1) & 1, (value >> 2) & 1] // [hào1, hào2, hào3] từ dưới lên
  return { value, bits, pinyin: PINYIN_BY_QUAI[quaiTen], ...base }
})

export const TRIGRAM_BY_PINYIN = Object.fromEntries(TRIGRAMS.map((t) => [t.pinyin, t]))

export function trigramFromBits(bits) {
  const value = bits[0] + bits[1] * 2 + bits[2] * 4
  return TRIGRAMS[value]
}
