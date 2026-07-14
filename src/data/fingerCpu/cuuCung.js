// Cửu Cung — 9 "vùng nhớ" ghép từ Lạc Thư (số) + Hậu Thiên Bát Quái (quái/hướng).
// Đây chính là ý tưởng nền cho Memory Visualizer ở phase sau: 9 ô cố định, mỗi ô
// tra được cả số, quái, hướng, ngũ hành chỉ từ 1 vị trí (row, col).

import { LAC_THU_GRID } from './lacThu'
import { TRIGRAM_BY_PINYIN } from './trigrams'

// number (Lạc Thư) -> quái tương ứng (Hậu Thiên Bát Quái), null = trung cung (không có quái)
const TRIGRAM_BY_NUMBER = {
  1: 'kan', 2: 'kun', 3: 'zhen', 4: 'xun', 5: null, 6: 'qian', 7: 'dui', 8: 'gen', 9: 'li',
}

export const CUU_CUNG_GRID = LAC_THU_GRID.map((row) =>
  row.map((cell) => {
    const pinyin = TRIGRAM_BY_NUMBER[cell.number]
    return { ...cell, trigram: pinyin ? TRIGRAM_BY_PINYIN[pinyin] : null }
  })
)

export const CUU_CUNG_FLAT = CUU_CUNG_GRID.flat()
