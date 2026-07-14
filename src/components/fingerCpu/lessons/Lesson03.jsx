import { useState } from 'react'
import FingerHandSVG from '../FingerHandSVG'
import { DIA_CHI } from '../../../data/fingerCpu/diaChi'

export default function Lesson03() {
  const [active, setActive] = useState(0)
  const chi = DIA_CHI[active]

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Lookup Table là gì?</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Một <strong>Lookup Table</strong> (bảng tra cứu) ánh xạ một <em>chỉ số (index)</em> sang
          một <em>giá trị</em> đã biết trước — không cần tính toán lại mỗi lần, chỉ cần tra bảng.
        </p>
        <div className="mt-3 flex items-center justify-center gap-3 text-sm font-mono">
          <span className="px-3 py-1.5 rounded-lg bg-gray-900 dark:bg-black text-emerald-400">index</span>
          <span className="text-gray-300 dark:text-gray-600">→</span>
          <span className="px-3 py-1.5 rounded-lg bg-gray-900 dark:bg-black text-amber-300">tên</span>
          <span className="text-gray-300 dark:text-gray-600">→</span>
          <span className="px-3 py-1.5 rounded-lg bg-gray-900 dark:bg-black text-sky-300">ý nghĩa</span>
        </div>
      </div>

      <div className="card p-6 flex flex-col items-center">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-4 self-start">
          🔍 Thử tra cứu: đốt tay → tên
        </h2>
        <FingerHandSVG activeIndex={active} onSelect={setActive} labelAt={(i) => DIA_CHI[i].ten} />
        <div className="mt-4 w-full p-4 rounded-xl bg-gray-50 dark:bg-dark-card/50 text-center">
          <div className="font-mono text-xs text-gray-400 mb-1">DIA_CHI[{active}]</div>
          <div className="text-lg font-bold text-primary">{chi.ten}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400">{chi.conGiap} · {chi.nguHanh}</div>
        </div>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Array hay HashMap?</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Vì chỉ số của bàn tay luôn là số nguyên liên tục 0..11, đây thực chất là một{' '}
          <strong>Array</strong> (tra cứu theo vị trí). Nhưng nếu tra theo chiều ngược lại — "Tý ở
          đốt nào?" — bạn cần một bảng tên → vị trí, giống một <strong>HashMap</strong> (tra cứu theo
          khoá). Người xưa dùng cả hai chiều tuỳ tình huống, dù không có khái niệm "cấu trúc dữ liệu".
        </p>
      </div>
    </div>
  )
}
