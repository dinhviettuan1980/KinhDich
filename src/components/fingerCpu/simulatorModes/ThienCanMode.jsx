import { useState } from 'react'
import { THIEN_CAN } from '../../../data/fingerCpu/thienCan'

export default function ThienCanMode() {
  const [active, setActive] = useState(0)
  const can = THIEN_CAN[active]
  return (
    <div>
      <div className="grid grid-cols-5 gap-2 mb-4">
        {THIEN_CAN.map((c) => (
          <button
            key={c.index}
            onClick={() => setActive(c.index)}
            className={`aspect-square rounded-xl flex flex-col items-center justify-center transition-all ${
              active === c.index ? 'bg-primary text-white scale-105' : 'bg-gray-50 dark:bg-dark-card/50 hover:bg-gray-100 dark:hover:bg-dark-border'
            }`}
          >
            <span className="text-[10px] font-mono opacity-70">{c.index}</span>
            <span className="text-sm font-bold">{c.ten}</span>
          </button>
        ))}
      </div>
      <div className="p-4 rounded-xl bg-gray-50 dark:bg-dark-card/50 text-center">
        <div className="font-mono text-xs text-gray-400 mb-1">THIEN_CAN[{active}]</div>
        <div className="text-xl font-bold text-primary">{can.ten}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{can.nguHanh} · {can.amDuong}</div>
      </div>
    </div>
  )
}
