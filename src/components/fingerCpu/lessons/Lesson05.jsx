import { useState } from 'react'
import { THIEN_CAN } from '../../../data/fingerCpu/thienCan'

export default function Lesson05() {
  const [active, setActive] = useState(0)
  const can = THIEN_CAN[active]

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 10 Thiên Can</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Thiên Can là một bảng dữ liệu <strong>khác</strong>, chỉ có 10 phần tử — không phải 12. Đây
          là lúc "bảng dữ liệu" và "cấu trúc 12 đốt tay" tách rời nhau: cùng một bàn tay, nhưng
          Thiên Can chạy theo chu kỳ riêng, ngắn hơn Địa Chi 2 bước.
        </p>
        <div className="mt-3 p-3 rounded-xl bg-gray-900 dark:bg-black font-mono text-xs text-emerald-400 overflow-x-auto">
          can[0..9] — độ dài 10, khác độ dài 12 của chi[0..11]
        </div>
      </div>

      <div className="card p-6">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-4">
          🔢 Array Thiên Can
        </h2>
        <div className="grid grid-cols-5 gap-2">
          {THIEN_CAN.map((c) => (
            <button
              key={c.index}
              onClick={() => setActive(c.index)}
              className={`aspect-square rounded-xl flex flex-col items-center justify-center transition-all ${
                active === c.index
                  ? 'bg-primary text-white scale-105'
                  : 'bg-gray-50 dark:bg-dark-card/50 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-border'
              }`}
            >
              <span className="text-[10px] font-mono opacity-70">{c.index}</span>
              <span className="text-sm font-bold">{c.ten}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="card p-5">
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm mb-3">
          <Field label="Tên">{can.ten}</Field>
          <Field label="Ngũ hành">{can.nguHanh}</Field>
          <Field label="Âm dương">{can.amDuong}</Field>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 italic border-t border-gray-100 dark:border-dark-border pt-3">
          💡 {can.dacDiem}
        </p>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Vì sao lại là 10?</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Thiên Can được xây từ 5 Ngũ Hành (Mộc, Hỏa, Thổ, Kim, Thủy) × 2 Âm Dương = 10. Đây là một
          bảng được <strong>ghép từ 2 bảng nhỏ hơn</strong> — giống việc kết hợp 2 enum trong lập
          trình để sinh ra 1 tập giá trị lớn hơn.
        </p>
      </div>

      <div className="card p-4 bg-gray-50 dark:bg-dark-card/50 text-center">
        <p className="text-xs text-gray-400 dark:text-gray-500 italic">
          💡 Bài tiếp theo: khi 2 chu kỳ độ dài khác nhau (10 và 12) chạy song song, chuyện gì xảy ra?
          Đó chính là bài toán sinh ra 60 Hoa Giáp.
        </p>
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
