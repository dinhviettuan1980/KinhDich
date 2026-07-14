import { useState } from 'react'
import FingerHandSVG from '../FingerHandSVG'

export default function Lesson02() {
  const [active, setActive] = useState(0)

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Từ bàn tay đến Array</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Bàn tay có 4 ngón (không tính ngón cái), mỗi ngón có 3 đốt → tổng cộng{' '}
          <strong>12 đốt cố định</strong>. Trong lập trình, đây chính xác là một{' '}
          <strong>mảng (Array)</strong> có độ dài 12, đánh số từ 0:
        </p>
        <div className="mt-3 p-3 rounded-xl bg-gray-900 dark:bg-black font-mono text-xs text-emerald-400 overflow-x-auto">
          finger[0], finger[1], finger[2], ..., finger[11]
        </div>
      </div>

      <div className="card p-6 flex flex-col items-center">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-4 self-start">
          🖐️ Chạm vào từng đốt để xem chỉ số
        </h2>
        <FingerHandSVG activeIndex={active} onSelect={setActive} labelAt={(i) => `đốt số ${i}`} />
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Điểm mấu chốt</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Vị trí đốt tay <strong>không đổi</strong> — giống như địa chỉ ô nhớ trong Array không đổi.
          Cái thay đổi là <em>dữ liệu gán vào mỗi ô</em>: có thể là Địa Chi, Thiên Can, hay quẻ Bát
          Quái tuỳ vào "bảng dữ liệu" bạn nạp vào. Đây gọi là <strong>tách dữ liệu khỏi cấu trúc</strong> —
          một nguyên tắc lập trình quan trọng mà người xưa đã áp dụng trực giác.
        </p>
      </div>

      <div className="card p-4 bg-gray-50 dark:bg-dark-card/50 text-center">
        <p className="text-xs text-gray-400 dark:text-gray-500 italic">
          💡 Ở các bài sau, bạn sẽ thấy cùng 12 đốt tay này được "nạp" bởi 3 bảng dữ liệu khác nhau:
          Địa Chi, rồi một phần của Thiên Can, rồi Hoa Giáp.
        </p>
      </div>
    </div>
  )
}
