import { useState } from 'react'
import FingerHandSVG from '../FingerHandSVG'
import { DIA_CHI } from '../../../data/fingerCpu/diaChi'

export default function Lesson04() {
  const [active, setActive] = useState(0)
  const chi = DIA_CHI[active]

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 12 Địa Chi</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Địa Chi là bảng dữ liệu 12 phần tử — đúng bằng số đốt trên bàn tay, nên đây là bảng "vừa khít"
          nhất, không cần vòng lặp modulo phức tạp (bài sau sẽ thấy Thiên Can, chỉ có 10 phần tử,
          không khớp trực tiếp).
        </p>
      </div>

      <div className="card p-6 flex flex-col items-center">
        <FingerHandSVG activeIndex={active} onSelect={setActive} labelAt={(i) => DIA_CHI[i].ten} />
      </div>

      <div className="card p-5">
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm mb-4">
          <Field label="Tên">{chi.ten}</Field>
          <Field label="Con giáp">{chi.conGiap}</Field>
          <Field label="Ngũ hành">{chi.nguHanh}</Field>
          <Field label="Âm dương">{chi.amDuong}</Field>
          <Field label="Phương vị">{chi.phuongVi}</Field>
          <Field label="Giờ">{chi.gio}</Field>
          <Field label="Mùa">{chi.mua}</Field>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 italic border-t border-gray-100 dark:border-dark-border pt-3">
          💡 {chi.dacDiem}
        </p>
      </div>

      <div className="card p-5 overflow-x-auto">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📋 Toàn bộ bảng</h2>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-gray-400 dark:text-gray-500">
              <th className="pb-2 pr-2">#</th>
              <th className="pb-2 pr-2">Tên</th>
              <th className="pb-2 pr-2">Con giáp</th>
              <th className="pb-2 pr-2">Ngũ hành</th>
              <th className="pb-2">Giờ</th>
            </tr>
          </thead>
          <tbody>
            {DIA_CHI.map((c) => (
              <tr
                key={c.index}
                onClick={() => setActive(c.index)}
                className={`cursor-pointer border-t border-gray-50 dark:border-dark-border/50 ${
                  active === c.index ? 'bg-primary/10' : 'hover:bg-gray-50 dark:hover:bg-dark-card/50'
                }`}
              >
                <td className="py-1.5 pr-2 font-mono text-gray-400">{c.index}</td>
                <td className="py-1.5 pr-2 font-semibold text-gray-800 dark:text-gray-100">{c.ten}</td>
                <td className="py-1.5 pr-2 text-gray-600 dark:text-gray-300">{c.conGiap}</td>
                <td className="py-1.5 pr-2 text-gray-600 dark:text-gray-300">{c.nguHanh}</td>
                <td className="py-1.5 text-gray-600 dark:text-gray-300">{c.gio}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div className="flex justify-between border-b border-gray-50 dark:border-dark-border/50 py-1">
      <span className="text-gray-400 dark:text-gray-500">{label}</span>
      <span className="font-medium text-gray-800 dark:text-gray-100">{children}</span>
    </div>
  )
}
