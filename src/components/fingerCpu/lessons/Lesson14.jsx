import { useState } from 'react'
import { TU_TUONG } from '../../../data/fingerCpu/nhiThapBatTu'

export default function Lesson14() {
  const [active, setActive] = useState({ group: 'thanh-long', i: 0 })
  const activeGroup = TU_TUONG.find((g) => g.key === active.group)
  const activeTu = activeGroup.tu[active.i]

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 28 phần tử, 4 nhóm đều nhau</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          28 Tú chia bầu trời thành 28 vùng theo các chòm sao, nhóm thành{' '}
          <strong>4 nhóm × 7 sao</strong> theo 4 hướng — mỗi nhóm mang tên 1 linh vật (Tứ Tượng).
          Đây là kỹ thuật "chunking" — chia mảng lớn khó nhớ thành các mảng con dễ nhớ hơn.
        </p>
        <div className="mt-3 p-3 rounded-xl bg-gray-900 dark:bg-black font-mono text-xs text-emerald-400 text-center">
          28 = 4 × 7
        </div>
      </div>

      <div className="card p-6 space-y-4">
        {TU_TUONG.map((group) => (
          <div key={group.key}>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-sm font-bold text-gray-700 dark:text-gray-200">{group.ten}</span>
              <span className="text-xs text-gray-400">({group.conVat} · {group.huong})</span>
            </div>
            <div className="grid grid-cols-7 gap-1">
              {group.tu.map((ten, i) => {
                const isActive = active.group === group.key && active.i === i
                return (
                  <button
                    key={ten}
                    onClick={() => setActive({ group: group.key, i })}
                    className={`aspect-square rounded-lg flex items-center justify-center text-[11px] font-medium transition-all ${
                      isActive ? 'bg-primary text-white scale-105' : 'bg-gray-50 dark:bg-dark-card/50 hover:bg-gray-100 dark:hover:bg-dark-border'
                    }`}
                  >
                    {ten}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="card p-5 border-l-4 border-primary text-center">
        <div className="font-mono text-xs text-gray-400 mb-1">
          NHI_THAP_BAT_TU[{activeGroup.tu.indexOf(activeTu) + TU_TUONG.indexOf(activeGroup) * 7}]
        </div>
        <div className="text-lg font-bold text-primary">{activeTu}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">Nhóm {activeGroup.ten} · Hướng {activeGroup.huong}</div>
      </div>
    </div>
  )
}
