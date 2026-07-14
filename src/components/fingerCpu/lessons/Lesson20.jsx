import { useState } from 'react'
import { THIEN_CAN } from '../../../data/fingerCpu/thienCan'
import { DIA_CHI } from '../../../data/fingerCpu/diaChi'
import { TRIGRAMS } from '../../../data/fingerCpu/trigrams'
import { lookupHexagram, getHexagramById } from '../../../data/hexagrams'

export default function Lesson20() {
  const [n, setN] = useState(23)
  const [step, setStep] = useState(5)

  const can = THIEN_CAN[n % 10]
  const chi = DIA_CHI[n % 12]
  const tren = TRIGRAMS[(n % 10) % 8]
  const duoi = TRIGRAMS[(n % 12) % 8]
  const hex = getHexagramById(lookupHexagram(tren.pinyin, duoi.pinyin))

  const STEPS = [
    { label: 'Input', detail: `n = ${n}`, sub: 'một con số bất kỳ (giờ, ngày, số ngẫu nhiên...)' },
    { label: 'Can (Lookup #1)', detail: `THIEN_CAN[${n} % 10] = ${can.ten}`, sub: 'tra bảng 10 phần tử' },
    { label: 'Chi (Lookup #2)', detail: `DIA_CHI[${n} % 12] = ${chi.ten}`, sub: 'tra bảng 12 phần tử — chu kỳ khác Can' },
    { label: 'Modulo thu gọn', detail: `(${n}%10)%8=${(n % 10) % 8} · (${n}%12)%8=${(n % 12) % 8}`, sub: 'ép cả 2 chỉ số về phạm vi 0–7 để tra quái' },
    { label: 'Quái (Lookup #3)', detail: `${tren.quai} (trên) · ${duoi.quai} (dưới)`, sub: 'tra bảng 8 quái cho từng chỉ số' },
    { label: 'Quẻ (Lookup #4)', detail: `${hex.name}`, sub: 'ghép 2 quái → tra bảng 64 quẻ' },
  ]

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Toàn bộ pipeline, 1 lượt</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Đây là ví dụ tổng hợp — ghép lại các mảnh đã học (không phải 1 kỹ thuật cổ cụ thể) để thấy
          rõ: <strong>từ 1 con số duy nhất</strong>, chỉ bằng Lookup + Modulo lặp lại nhiều lần, ta
          đi được từ Can → Chi → Quái → Quẻ.
        </p>
      </div>

      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <label className="text-xs text-gray-400 dark:text-gray-500 block mb-1">Nhập n</label>
            <input type="number" value={n} onChange={(e) => setN(Number(e.target.value) || 0)}
              className="w-28 px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm font-mono outline-none focus:border-primary" />
          </div>
          <div className="flex gap-2">
            <button onClick={() => setStep((s) => Math.max(0, s - 1))} className="btn-secondary text-sm px-3">◀</button>
            <button onClick={() => setStep((s) => Math.min(5, s + 1))} className="btn-secondary text-sm px-3">▶</button>
            <button onClick={() => setStep(0)} className="btn-secondary text-sm px-3">Reset</button>
          </div>
        </div>

        <div className="space-y-1.5">
          {STEPS.map((s, i) => (
            <div key={s.label}>
              <div className={`p-3 rounded-xl transition-all duration-200 ${i <= step ? 'bg-primary/10 border border-primary/30' : 'bg-gray-50 dark:bg-dark-card/50 opacity-40'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-gray-700 dark:text-gray-200">{s.label}</span>
                  <span className="font-mono text-xs text-primary">{i <= step ? s.detail : '…'}</span>
                </div>
                <div className="text-[11px] text-gray-400 dark:text-gray-500 mt-0.5">{s.sub}</div>
              </div>
              {i < STEPS.length - 1 && <div className="text-center text-gray-300 dark:text-gray-600 text-xs py-0.5">↓</div>}
            </div>
          ))}
        </div>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Chỉ 2 khối kỹ thuật, lặp lại nhiều lần</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Toàn bộ pipeline trên chỉ dùng <strong>Modulo</strong> và <strong>Lookup Table</strong> —
          2 công cụ đã học từ bài 3 và bài 7. "Phép thuật" của các thầy, nhìn dưới lăng kính này,
          là khả năng thực hiện chuỗi bước này bằng trí nhớ và ngón tay, nhanh và chính xác.
        </p>
      </div>
    </div>
  )
}
