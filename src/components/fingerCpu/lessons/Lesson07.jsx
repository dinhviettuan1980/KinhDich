import { useState } from 'react'
import FingerHandSVG from '../FingerHandSVG'
import { DIA_CHI } from '../../../data/fingerCpu/diaChi'

export default function Lesson07() {
  const [start, setStart] = useState(0)
  const [offset, setOffset] = useState(3)

  const raw = start + offset
  const result = ((raw % 12) + 12) % 12

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Modulo — phép toán "quay vòng"</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Bàn tay chỉ có 12 đốt, nhưng phép đếm có thể vượt quá 12 (đi hơn 1 vòng) hoặc âm (đi
          ngược). <strong>Modulo (%)</strong> luôn kéo kết quả về đúng phạm vi 0..11 — giống việc
          ngón tay cái tự động "quay lại từ đầu" khi đếm hết vòng.
        </p>
        <div className="mt-3 p-3 rounded-xl bg-gray-900 dark:bg-black font-mono text-xs text-emerald-400 text-center">
          index = (start + offset) % 12
        </div>
      </div>

      <div className="card p-6 space-y-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500">🎛️ Thử tự tính</h2>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-400 dark:text-gray-500 block mb-1">start (0–11)</label>
            <input
              type="number" min={0} max={11} value={start}
              onChange={(e) => setStart(Math.max(0, Math.min(11, Number(e.target.value) || 0)))}
              className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm text-gray-900 dark:text-gray-100 outline-none focus:border-primary font-mono"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 dark:text-gray-500 block mb-1">offset (số bước, có thể âm)</label>
            <input
              type="number" value={offset}
              onChange={(e) => setOffset(Number(e.target.value) || 0)}
              className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm text-gray-900 dark:text-gray-100 outline-none focus:border-primary font-mono"
            />
          </div>
        </div>

        <div className="p-3 rounded-xl bg-gray-50 dark:bg-dark-card/50 font-mono text-xs text-center text-gray-600 dark:text-gray-300 space-y-1">
          <div>({start} + {offset}) % 12</div>
          <div>= {raw} % 12</div>
          <div className="text-primary font-bold text-sm">= {result}</div>
        </div>

        <div className="flex justify-center">
          <FingerHandSVG activeIndex={result} interactive={false} labelAt={(i) => DIA_CHI[i].ten} size={220} />
        </div>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Ứng dụng thực tế</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          "Từ giờ Tý, đi thêm 15 giờ Chi là giờ gì?" → chính là bài toán{' '}
          <code className="font-mono text-xs bg-gray-100 dark:bg-dark-card px-1 rounded">(0 + 15) % 12 = 3 → Mão</code>.
          Đây là phép tính mà các thầy làm ngầm trong đầu mỗi khi lần ngón tay — không phải đoán,
          mà là modulo được thực hiện bằng chuyển động vật lý của ngón cái.
        </p>
      </div>
    </div>
  )
}
