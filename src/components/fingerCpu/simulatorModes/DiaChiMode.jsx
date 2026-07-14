import { useState } from 'react'
import FingerHandSVG from '../FingerHandSVG'
import { DIA_CHI } from '../../../data/fingerCpu/diaChi'

export default function DiaChiMode() {
  const [active, setActive] = useState(null)
  return (
    <div className="flex flex-col items-center">
      <FingerHandSVG activeIndex={active} onSelect={setActive} labelAt={(i) => DIA_CHI[i].ten} size={260} />
      {active != null && (
        <div className="mt-4 w-full p-4 rounded-xl bg-gray-50 dark:bg-dark-card/50 text-center animate-slide-up">
          <div className="font-mono text-xs text-gray-400 mb-1">DIA_CHI[{active}]</div>
          <div className="text-xl font-bold text-primary">{DIA_CHI[active].ten}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {DIA_CHI[active].conGiap} · {DIA_CHI[active].nguHanh} · {DIA_CHI[active].amDuong} · {DIA_CHI[active].gio}
          </div>
        </div>
      )}
    </div>
  )
}
