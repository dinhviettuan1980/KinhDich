import { useState } from 'react'
import { THIEN_CAN } from '../../../data/fingerCpu/thienCan'
import { DIA_CHI } from '../../../data/fingerCpu/diaChi'
import { HOA_GIAP } from '../../../data/fingerCpu/hoaGiap'

function GearRow({ title, items, pos }) {
  return (
    <div>
      <div className="text-xs text-gray-400 dark:text-gray-500 mb-1.5">{title}</div>
      <div className="flex gap-1">
        {items.map((label, idx) => (
          <div
            key={idx}
            className={`flex-1 h-8 rounded-lg flex items-center justify-center text-[10px] font-medium transition-all duration-150 ${
              idx === pos ? 'bg-primary text-white scale-110' : 'bg-gray-50 dark:bg-dark-card/50 text-gray-400 dark:text-gray-500'
            }`}
          >
            {label}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function HoaGiapMode() {
  const [i, setI] = useState(0)
  return (
    <div className="space-y-4">
      <input
        type="range" min={0} max={59} value={i}
        onChange={(e) => setI(Number(e.target.value))}
        className="w-full accent-primary"
      />
      <GearRow title="Thiên Can (10)" items={THIEN_CAN.map((c) => c.ten)} pos={i % 10} />
      <GearRow title="Địa Chi (12)" items={DIA_CHI.map((c) => c.ten)} pos={i % 12} />
      <div className="p-4 rounded-xl bg-gray-50 dark:bg-dark-card/50 text-center">
        <div className="font-mono text-xs text-gray-400 mb-1">HOA_GIAP[{i}]</div>
        <div className="text-xl font-bold text-primary">{HOA_GIAP[i].ten}</div>
      </div>
    </div>
  )
}
