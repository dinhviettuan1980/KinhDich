import { useState } from 'react'
import { TRIGRAMS } from '../../../data/fingerCpu/trigrams'
import { lookupHexagram, getHexagramById } from '../../../data/hexagrams'

export default function Lesson16() {
  const [n1, setN1] = useState(7)
  const [n2, setN2] = useState(13)

  const tren = TRIGRAMS[n1 % 8]
  const duoi = TRIGRAMS[n2 % 8]
  const haoDong = (n1 + n2) % 6
  const hexId = lookupHexagram(tren.pinyin, duoi.pinyin)
  const hex = getHexagramById(hexId)

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Một hàm băm (hash function) cổ</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Mai Hoa Dịch Số lấy 2 con số bất kỳ (giờ, ngày, số ngẫu nhiên...) và biến chúng thành 1
          quẻ, theo đúng cấu trúc: 2 số đầu vào → 2 phép modulo độc lập ra 2 quái → 1 phép modulo
          thứ 3 ra hào động. Về bản chất lập trình, đây là một <strong>hàm băm (hash function)</strong>:
          input cố định luôn cho ra cùng 1 output, khác input gần như chắc chắn ra output khác.
        </p>
        <div className="mt-3 p-3 rounded-xl bg-gray-900 dark:bg-black font-mono text-[11px] text-emerald-400 text-center leading-relaxed">
          quaiTren = TRIGRAMS[n1 % 8]<br />
          quaiDuoi = TRIGRAMS[n2 % 8]<br />
          haoDong = (n1 + n2) % 6
        </div>
      </div>

      <div className="card p-6 space-y-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500">🎛️ Thử với 2 số bất kỳ</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-400 dark:text-gray-500 block mb-1">n1</label>
            <input type="number" value={n1} onChange={(e) => setN1(Number(e.target.value) || 0)}
              className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm font-mono outline-none focus:border-primary" />
          </div>
          <div>
            <label className="text-xs text-gray-400 dark:text-gray-500 block mb-1">n2</label>
            <input type="number" value={n2} onChange={(e) => setN2(Number(e.target.value) || 0)}
              className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm font-mono outline-none focus:border-primary" />
          </div>
        </div>

        <div className="flex items-center justify-center gap-6 py-2">
          <div className="text-center">
            <div className="text-3xl">{tren.glyph}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">{tren.quai} (trên)</div>
          </div>
          <div className="text-center">
            <div className="text-3xl">{duoi.glyph}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">{duoi.quai} (dưới)</div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-gray-50 dark:bg-dark-card/50 text-center space-y-1">
          <div className="font-mono text-xs text-gray-400">Quẻ số {hex.id} — hào động thứ {haoDong + 1}</div>
          <div className="text-lg font-bold text-primary">{hex.name}</div>
          <p className="text-xs text-gray-500 dark:text-gray-400">{hex.shortMeaning}</p>
        </div>
      </div>

      <div className="card p-4 bg-gray-50 dark:bg-dark-card/50 text-center">
        <p className="text-xs text-gray-400 dark:text-gray-500 italic">
          💡 Bản gốc còn quy tắc chọn số theo giờ/ngày âm lịch — ở đây rút gọn để thấy rõ CẤU TRÚC
          thuật toán (2 input → hash → quẻ), không phải hướng dẫn xem quẻ đầy đủ.
        </p>
      </div>
    </div>
  )
}
