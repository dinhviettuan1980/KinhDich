import { useState } from 'react'
import { TRUONG_SINH, truongSinhAt } from '../../../data/fingerCpu/truongSinh'

export default function TruongSinhMode() {
  const [i, setI] = useState(0)
  const current = truongSinhAt(i)
  const R = 85, CX = 105, CY = 105

  return (
    <div className="flex flex-col items-center gap-4">
      <svg viewBox="0 0 210 210" width={210} height={210}>
        <circle cx={CX} cy={CY} r={R} className="fill-none stroke-gray-100 dark:stroke-dark-border" strokeWidth="1" />
        {TRUONG_SINH.map((s, idx) => {
          const angle = (idx / 12) * 2 * Math.PI - Math.PI / 2
          const x = CX + R * Math.cos(angle)
          const y = CY + R * Math.sin(angle)
          const isActive = idx === i
          return (
            <g key={s.index} onClick={() => setI(idx)} className="cursor-pointer">
              <circle cx={x} cy={y} r={isActive ? 13 : 10} className={`transition-all duration-200 ${isActive ? 'fill-primary' : 'fill-gray-100 dark:fill-dark-card'}`} />
              <text x={x} y={y + 3} textAnchor="middle" className={`text-[8px] font-bold ${isActive ? 'fill-white' : 'fill-gray-500 dark:fill-gray-400'}`}>{idx}</text>
            </g>
          )
        })}
      </svg>
      <div className="text-center">
        <div className="font-mono text-xs text-gray-400 mb-1">TRUONG_SINH[{i}]</div>
        <div className="text-lg font-bold text-primary">{current.ten}</div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-xs">{current.moTa}</p>
      </div>
    </div>
  )
}
