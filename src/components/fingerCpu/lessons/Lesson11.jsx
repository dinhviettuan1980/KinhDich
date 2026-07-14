import { useState } from 'react'
import { generateHaDoPairs } from '../../../data/fingerCpu/haDo'

export default function Lesson11() {
  const [active, setActive] = useState(0)
  const pairs = generateHaDoPairs()
  const p = pairs[active]

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Sơ đồ số nguyên thủy</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Hà Đồ ra đời trước Lạc Thư — chia 10 số thành 5 cặp gắn với 5 Ngũ Hành. Mỗi cặp có 1{' '}
          <strong>sinh số</strong> (1–5, tạo ra hành) và 1 <strong>thành số</strong> (6–10, hoàn
          thiện hành), theo đúng 1 công thức duy nhất:
        </p>
        <div className="mt-3 p-3 rounded-xl bg-gray-900 dark:bg-black font-mono text-xs text-emerald-400 text-center">
          thành số = sinh số + 5
        </div>
      </div>

      <div className="card p-6">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-4">🔢 5 cặp Ngũ Hành</h2>
        <div className="grid grid-cols-5 gap-2 mb-4">
          {pairs.map((pair, i) => (
            <button
              key={pair.nguHanh}
              onClick={() => setActive(i)}
              className={`p-2 rounded-xl text-center transition-all ${
                active === i ? 'bg-primary text-white scale-105' : 'bg-gray-50 dark:bg-dark-card/50 hover:bg-gray-100 dark:hover:bg-dark-border'
              }`}
            >
              <div className="text-sm font-mono font-bold">{pair.sinh}·{pair.thanh}</div>
              <div className="text-[10px]">{pair.nguHanh}</div>
            </button>
          ))}
        </div>

        <div className="p-4 rounded-xl bg-gray-50 dark:bg-dark-card/50 text-center space-y-1">
          <div className="font-mono text-xs text-gray-400">sinh {p.sinh} + 5 = thành {p.thanh}</div>
          <div className="text-lg font-bold text-primary">{p.nguHanh} — {p.phuongVi}</div>
        </div>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Sinh số vs Thành số</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Sinh số là số lẻ (dương), thành số là số chẵn (âm) — cùng công thức{' '}
          <code className="font-mono text-xs bg-gray-100 dark:bg-dark-card px-1 rounded">+5</code> áp
          dụng cho cả 5 cặp, không có ngoại lệ. Đây là một quy tắc biến đổi (transform rule) đơn
          giản, đủ để suy ra toàn bộ 10 số chỉ từ 5 con số gốc.
        </p>
      </div>
    </div>
  )
}
