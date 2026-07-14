import { useEffect, useRef, useState } from 'react'
import { THIEN_CAN } from '../../../data/fingerCpu/thienCan'
import { DIA_CHI } from '../../../data/fingerCpu/diaChi'
import { HOA_GIAP } from '../../../data/fingerCpu/hoaGiap'

export default function Lesson06() {
  const [i, setI] = useState(0)
  const [playing, setPlaying] = useState(false)
  const timerRef = useRef(null)

  useEffect(() => {
    if (!playing) return
    timerRef.current = setInterval(() => {
      setI((v) => {
        if (v >= 59) { setPlaying(false); return v }
        return v + 1
      })
    }, 220)
    return () => clearInterval(timerRef.current)
  }, [playing])

  const canPos = i % 10
  const chiPos = i % 12

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Hai bánh răng lệch nhau</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Thiên Can có <strong>10</strong> phần tử, Địa Chi có <strong>12</strong> phần tử. Hãy tưởng
          tượng 2 bánh răng cùng quay 1 nấc mỗi bước: bánh 10 răng và bánh 12 răng. Chúng chỉ cùng
          quay về đúng vị trí ban đầu sau <strong>bội số chung nhỏ nhất</strong> của 10 và 12.
        </p>
        <div className="mt-3 p-3 rounded-xl bg-gray-900 dark:bg-black font-mono text-xs text-emerald-400 text-center">
          LCM(10, 12) = 60 → đó là số lượng Hoa Giáp
        </div>
      </div>

      <div className="card p-6 space-y-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500">
          🎛️ Generator — sinh trực tiếp, không hardcode
        </h2>

        <GearRow title="Thiên Can (10)" items={THIEN_CAN.map((c) => c.ten)} pos={canPos} color="primary" />
        <GearRow title="Địa Chi (12)" items={DIA_CHI.map((c) => c.ten)} pos={chiPos} color="accent" />

        <div className="text-center py-2">
          <div className="font-mono text-xs text-gray-400 mb-1">HOA_GIAP[{i}] = THIEN_CAN[{canPos}] + DIA_CHI[{chiPos}]</div>
          <div className="text-2xl font-bold text-primary">{HOA_GIAP[i].ten}</div>
        </div>

        <div className="flex items-center gap-2">
          <button onClick={() => { setPlaying(false); setI((v) => Math.max(0, v - 1)) }} className="btn-secondary text-sm px-3">◀</button>
          <button
            onClick={() => setPlaying((p) => !p)}
            className="btn-primary flex-1 text-sm"
          >
            {playing ? '⏸ Tạm dừng' : i >= 59 ? '↺ Chạy lại' : '▶ Tự chạy'}
          </button>
          <button onClick={() => { setPlaying(false); setI((v) => Math.min(59, v + 1)) }} className="btn-secondary text-sm px-3">▶</button>
          <button onClick={() => { setPlaying(false); setI(0) }} className="btn-secondary text-sm px-3">Reset</button>
        </div>

        <div className="text-xs text-gray-400 dark:text-gray-500 text-center">
          Bước {i + 1}/60 {i === 59 && '— hoàn tất 1 vòng Hoa Giáp!'}
        </div>
      </div>

      <div className="card p-5 overflow-x-auto">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📋 Đã sinh ({i + 1}/60)</h2>
        <div className="flex flex-wrap gap-1.5">
          {HOA_GIAP.slice(0, i + 1).map((h) => (
            <span key={h.index} className="text-[11px] font-mono px-2 py-1 rounded-lg bg-gray-50 dark:bg-dark-card/50 text-gray-600 dark:text-gray-300">
              {h.index}:{h.ten}
            </span>
          ))}
        </div>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Code thật (không hardcode)</h2>
        <pre className="p-3 rounded-xl bg-gray-900 dark:bg-black font-mono text-[11px] text-emerald-400 overflow-x-auto">{`for (let i = 0; i < 60; i++) {
  can = THIEN_CAN[i % 10]
  chi = DIA_CHI[i % 12]
  hoaGiap[i] = can.ten + " " + chi.ten
}`}</pre>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          Toàn bộ 60 Hoa Giáp trong module này được sinh đúng bằng đoạn logic trên
          (xem <code className="font-mono">src/data/fingerCpu/hoaGiap.js</code>), không có danh sách viết tay nào cả.
        </p>
      </div>
    </div>
  )
}

function GearRow({ title, items, pos, color }) {
  const activeClass = color === 'primary' ? 'bg-primary text-white' : 'bg-accent text-white'
  return (
    <div>
      <div className="text-xs text-gray-400 dark:text-gray-500 mb-1.5">{title}</div>
      <div className="flex gap-1">
        {items.map((label, idx) => (
          <div
            key={idx}
            className={`flex-1 h-9 rounded-lg flex items-center justify-center text-[11px] font-medium transition-all duration-150 ${
              idx === pos ? `${activeClass} scale-110` : 'bg-gray-50 dark:bg-dark-card/50 text-gray-400 dark:text-gray-500'
            }`}
          >
            {label}
          </div>
        ))}
      </div>
    </div>
  )
}
