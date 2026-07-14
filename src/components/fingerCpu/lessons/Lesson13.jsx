import { useState } from 'react'
import { TIET_KHI_BY_MUA } from '../../../data/fingerCpu/tietKhi'

const MUA_COLOR = {
  Xuân: 'bg-emerald-400', Hạ: 'bg-amber-400', Thu: 'bg-orange-400', Đông: 'bg-sky-400',
}

export default function Lesson13() {
  const [active, setActive] = useState(0)

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Timeline chia đều 1 vòng quay</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Trái Đất quay quanh Mặt Trời 1 vòng ≈ 365 ngày. Người xưa chia vòng đó thành{' '}
          <strong>24 đoạn bằng nhau</strong> (~15 ngày/đoạn) — giống việc chia 1 <code className="font-mono text-xs bg-gray-100 dark:bg-dark-card px-1 rounded">for</code> loop
          thành 24 bước cố định để "lấy mẫu" thời tiết theo chu kỳ.
        </p>
      </div>

      <div className="card p-6 space-y-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500">🗓️ 4 mùa × 6 tiết</h2>
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

      <div className="card p-4 bg-gray-50 dark:bg-dark-card/50 text-center">
        <p className="text-xs text-gray-400 dark:text-gray-500 italic">
          💡 Ngày dương lịch chỉ là gần đúng (lệch 1 ngày tuỳ năm nhuận) — mục đích ở đây là thấy rõ
          cấu trúc "24 mốc cố định", không phải tính lịch chính xác tuyệt đối.
        </p>
      </div>
    </div>
  )
}
