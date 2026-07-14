import { useEffect, useRef, useState } from 'react'
import { TRUONG_SINH, truongSinhAt } from '../../../data/fingerCpu/truongSinh'

export default function Lesson15() {
  const [i, setI] = useState(0)
  const [playing, setPlaying] = useState(false)
  const timerRef = useRef(null)
  const current = truongSinhAt(i)

  useEffect(() => {
    if (!playing) return
    timerRef.current = setInterval(() => setI((v) => (v + 1) % 12), 900)
    return () => clearInterval(timerRef.current)
  }, [playing])

  const R = 90
  const CX = 110
  const CY = 110

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Máy trạng thái hữu hạn (Finite State Machine)</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Trường Sinh mô tả 1 "vòng đời" gồm đúng 12 trạng thái cố định, luôn chuyển theo 1 chiều,
          hết trạng thái cuối (Dưỡng) thì quay lại trạng thái đầu (Trường Sinh) — không có nhánh rẽ,
          không có ngoại lệ. Đây là ví dụ sạch nhất của <strong>Finite State Machine</strong> trong
          cả module này.
        </p>
      </div>

      <div className="card p-6 flex flex-col items-center gap-4">
        <svg viewBox="0 0 220 220" width={220} height={220}>
          <circle cx={CX} cy={CY} r={R} className="fill-none stroke-gray-100 dark:stroke-dark-border" strokeWidth="1" />
          {TRUONG_SINH.map((s, idx) => {
            const angle = (idx / 12) * 2 * Math.PI - Math.PI / 2
            const x = CX + R * Math.cos(angle)
            const y = CY + R * Math.sin(angle)
            const isActive = idx === i
            return (
              <g key={s.index} onClick={() => { setPlaying(false); setI(idx) }} className="cursor-pointer">
                <circle cx={x} cy={y} r={isActive ? 14 : 11} className={`transition-all duration-200 ${isActive ? 'fill-primary' : 'fill-gray-100 dark:fill-dark-card'}`} />
                <text x={x} y={y + 3} textAnchor="middle" className={`text-[8px] font-bold ${isActive ? 'fill-white' : 'fill-gray-500 dark:fill-gray-400'}`}>
                  {idx}
                </text>
              </g>
            )
          })}
        </svg>

        <div className="text-center">
          <div className="font-mono text-xs text-gray-400 mb-1">state[{i}]</div>
          <div className="text-xl font-bold text-primary">{current.ten}</div>
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 max-w-xs">{current.moTa}</p>
        </div>

        <div className="flex items-center gap-2 w-full max-w-xs">
          <button onClick={() => { setPlaying(false); setI((v) => (v + 11) % 12) }} className="btn-secondary text-sm px-3">◀</button>
          <button onClick={() => setPlaying((p) => !p)} className="btn-primary flex-1 text-sm">
            {playing ? '⏸ Tạm dừng' : '▶ Tự chạy vòng đời'}
          </button>
          <button onClick={() => { setPlaying(false); setI((v) => (v + 1) % 12) }} className="btn-secondary text-sm px-3">▶</button>
        </div>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ next(state) = (state + 1) % 12</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Cùng công thức modulo ở bài 7 — chỉ khác đối tượng áp dụng. Đây là điểm mấu chốt của cả
          module: <strong>rất nhiều hệ thống "huyền bí" khác nhau thực chất dùng chung 1 vài công
          thức toán học</strong>, chỉ khác bảng dữ liệu được nạp vào.
        </p>
      </div>
    </div>
  )
}
