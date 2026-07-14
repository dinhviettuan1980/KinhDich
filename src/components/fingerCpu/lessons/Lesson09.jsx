import { useEffect, useRef, useState } from 'react'
import { TRIGRAMS } from '../../../data/fingerCpu/trigrams'
import { lookupHexagram, getHexagramById } from '../../../data/hexagrams'

const AXIS = TRIGRAMS // 8 quái, thứ tự nhị phân 0..7 — dùng chung cho hàng (thượng) và cột (hạ)

export default function Lesson09() {
  const [revealed, setRevealed] = useState(64)
  const [playing, setPlaying] = useState(false)
  const [selected, setSelected] = useState(null)
  const timerRef = useRef(null)

  useEffect(() => {
    if (!playing) return
    timerRef.current = setInterval(() => {
      setRevealed((v) => {
        if (v >= 64) { setPlaying(false); return v }
        return v + 1
      })
    }, 40)
    return () => clearInterval(timerRef.current)
  }, [playing])

  const startGenerate = () => { setRevealed(0); setPlaying(true) }

  const selectedHex = selected != null ? getHexagramById(selected.id) : null

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 8 × 8 = 64</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Mỗi Quẻ gồm 2 quái chồng lên nhau: <strong>Thượng quái</strong> (trên) và{' '}
          <strong>Hạ quái</strong> (dưới). Ghép mọi thượng quái với mọi hạ quái = một{' '}
          <strong>vòng lặp lồng nhau</strong> (nested loop) 8 × 8 = 64 tổ hợp — đúng bằng 64 Quẻ.
        </p>
        <div className="mt-3 p-3 rounded-xl bg-gray-900 dark:bg-black font-mono text-[11px] text-emerald-400 overflow-x-auto">{`for (upper of 8_quai)
  for (lower of 8_quai)
    grid[upper][lower] = lookupTenQue(upper, lower)`}</div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          Vòng lặp tạo ra <strong>tổ hợp</strong> (thuật toán) — nhưng <em>tên riêng</em> mỗi quẻ
          (theo thứ tự Văn Vương cổ) là dữ liệu lịch sử không có công thức, nên vẫn cần{' '}
          <strong>Lookup Table</strong> để tra tên. Thuật toán + bảng tra luôn đi cùng nhau.
        </p>
      </div>

      <div className="card p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500">🎛️ Ma trận 64 Quẻ</h2>
          <button onClick={startGenerate} className="btn-secondary text-xs px-3 py-1.5">
            {playing ? '⏸ đang sinh...' : '↺ Sinh lại từ đầu'}
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="border-collapse mx-auto">
            <thead>
              <tr>
                <th className="w-8 h-8" />
                {AXIS.map((lo) => (
                  <th key={lo.pinyin} className="w-8 h-8 text-center text-sm">{lo.glyph}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {AXIS.map((up, ri) => (
                <tr key={up.pinyin}>
                  <td className="w-8 h-8 text-center text-sm">{up.glyph}</td>
                  {AXIS.map((lo, ci) => {
                    const flatIndex = ri * 8 + ci
                    const isRevealed = flatIndex < revealed
                    const id = isRevealed ? lookupHexagram(up.pinyin, lo.pinyin) : null
                    const isSelected = selected && selected.upper === up.pinyin && selected.lower === lo.pinyin
                    return (
                      <td key={lo.pinyin} className="p-0.5">
                        <button
                          disabled={!isRevealed}
                          onClick={() => setSelected({ upper: up.pinyin, lower: lo.pinyin, id })}
                          className={`w-8 h-8 rounded-md text-[10px] font-mono transition-all duration-150 ${
                            !isRevealed
                              ? 'bg-transparent'
                              : isSelected
                              ? 'bg-primary text-white scale-110'
                              : 'bg-gray-50 dark:bg-dark-card/50 text-gray-500 dark:text-gray-400 hover:bg-primary/20'
                          }`}
                        >
                          {isRevealed ? id : ''}
                        </button>
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-gray-400 dark:text-gray-500 text-center mt-2">hàng = thượng quái · cột = hạ quái · số = thứ tự Văn Vương (1–64)</p>
      </div>

      {selectedHex && (
        <div className="card p-5 border-l-4 border-primary animate-slide-up">
          <div className="text-xs text-gray-400 font-mono mb-1">Quẻ số {selectedHex.id}</div>
          <div className="text-lg font-bold text-primary mb-1">{selectedHex.name}</div>
          <p className="text-sm text-gray-700 dark:text-gray-300">{selectedHex.shortMeaning}</p>
        </div>
      )}

      <div className="card p-4 bg-gray-50 dark:bg-dark-card/50 text-center">
        <p className="text-xs text-gray-400 dark:text-gray-500 italic">
          💡 Xem đầy đủ ý nghĩa & 3 góc nhìn (đời sống/kinh doanh/kỹ thuật) của cả 64 quẻ tại trang{' '}
          <strong>📖 64 Quẻ</strong> trong menu chính.
        </p>
      </div>
    </div>
  )
}
