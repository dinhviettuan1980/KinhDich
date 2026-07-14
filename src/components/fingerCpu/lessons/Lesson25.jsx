import { useNavigate } from 'react-router-dom'

const CONCEPTS = [
  { icon: '🗂️', ten: 'Data Structure', bai: 'Bài 2, 4, 5' },
  { icon: '🔁', ten: 'Algorithm', bai: 'Bài 6, 9' },
  { icon: '🖐️', ten: 'Memory Mapping', bai: 'Bài 1, 2, 21' },
  { icon: '🔍', ten: 'Lookup Table', bai: 'Bài 3, 4, 5' },
  { icon: '➗', ten: 'Modular Arithmetic', bai: 'Bài 7, 15' },
  { icon: '🔢', ten: 'Binary', bai: 'Bài 8' },
  { icon: '▦', ten: 'Matrix', bai: 'Bài 9, 10, 12' },
  { icon: '⭕', ten: 'Finite State', bai: 'Bài 15' },
  { icon: '🧩', ten: 'Pattern Recognition', bai: 'Bài 20, 21' },
]

export default function Lesson25() {
  const navigate = useNavigate()

  return (
    <div className="space-y-4">
      <div className="card p-8 text-center space-y-3">
        <div className="text-5xl">🎓</div>
        <h2 className="text-lg font-display font-bold text-gray-900 dark:text-gray-100">
          Hoàn thành Finger CPU Lab
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
          25 bài, từ 1 bàn tay đến 3 ngôn ngữ lập trình — cùng 1 thông điệp xuyên suốt.
        </p>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">🪷 Kết luận</h2>
        <p className="text-gray-700 dark:text-gray-200 text-sm font-medium leading-relaxed">
          "Các thầy đang tính toán" — không phải "các thầy có phép thuật". Kỹ thuật bấm ngón tay là
          một hệ thống <strong>Memory Mapping</strong>, <strong>Lookup Table</strong> và{' '}
          <strong>Modulo</strong> được tinh chỉnh qua hàng nghìn năm, đủ tối ưu để chạy hoàn toàn
          bằng phần cứng sinh học — không cần điện, không cần màn hình.
        </p>
      </div>

      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📚 9 khái niệm đã học</h2>
        <div className="grid grid-cols-3 gap-2">
          {CONCEPTS.map((c) => (
            <div key={c.ten} className="p-3 rounded-xl bg-gray-50 dark:bg-dark-card/50 text-center">
              <div className="text-xl mb-1">{c.icon}</div>
              <div className="text-[11px] font-semibold text-gray-700 dark:text-gray-200 leading-tight">{c.ten}</div>
              <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">{c.bai}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-3">
        <button onClick={() => navigate('/finger-cpu/simulator')} className="btn-primary flex-1">
          🎛️ Vào Simulator
        </button>
        <button onClick={() => navigate('/finger-cpu/bai/1')} className="btn-secondary flex-1">
          ↺ Học lại từ đầu
        </button>
      </div>
    </div>
  )
}
