import { useState } from 'react'
import { TIET_KHI_BY_MUA } from '../../../data/fingerCpu/tietKhi'

const MUA_COLOR = { Xuân: 'bg-emerald-400', Hạ: 'bg-amber-400', Thu: 'bg-orange-400', Đông: 'bg-sky-400' }

export default function TietKhiMode() {
  const [active, setActive] = useState(0)
  return (
    <div className="space-y-3">
      {TIET_KHI_BY_MUA.map((group) => (
        <div key={group.mua}>
          <div className="flex items-center gap-1.5 mb-1.5">
            <span className={`w-2 h-2 rounded-full ${MUA_COLOR[group.mua]}`} />
            <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">{group.mua}</span>
          </div>
          <div className="grid grid-cols-3 gap-1.5">
            {group.items.map((t) => (
              <button
                key={t.index}
                onClick={() => setActive(t.index)}
                className={`text-left px-2 py-1.5 rounded-lg transition-colors ${
                  active === t.index ? 'bg-primary text-white' : 'bg-gray-50 dark:bg-dark-card/50 hover:bg-gray-100 dark:hover:bg-dark-border'
                }`}
              >
                <div className="text-xs font-medium">{t.ten}</div>
                <div className={`text-[10px] font-mono ${active === t.index ? 'opacity-80' : 'text-gray-400'}`}>{t.ngayDuongLich}</div>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
