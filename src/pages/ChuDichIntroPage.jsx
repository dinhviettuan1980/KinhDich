import { useNavigate } from 'react-router-dom'
import { CHU_DICH_REGISTRY } from '../data/chu-dich/registry'

export default function ChuDichIntroPage() {
  const navigate = useNavigate()
  const readyCount = CHU_DICH_REGISTRY.filter((h) => h.status === 'ready').length

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6 animate-fade-in">
      <div className="text-center space-y-3">
        <div className="text-5xl">📜</div>
        <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-gray-100 leading-tight">
          Chu Dịch Nguyên Tác
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto leading-relaxed">
          Đây <strong>không phải</strong> module xem bói. Đây là nơi đọc nguyên văn chữ Hán của
          Chu Dịch — có phiên âm Hán Việt, dịch nghĩa, giải thích từng chữ — để hiểu{' '}
          <em>vì sao người xưa viết như vậy</em>, không cần biết chữ Hán từ trước.
        </p>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Cam kết về nguồn</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Nguyên văn chữ Hán và bản dịch tham khảo được tra cứu từ nguồn học thuật công khai
          (Chinese Text Project, James Legge 1899, đối chiếu Wikisource) — không tự sáng tác. Nếu
          có nhiều cách dịch khác nhau, module sẽ trình bày trung lập, không khẳng định chỉ có 1
          cách hiểu đúng.
        </p>
      </div>

      <div className="card p-4 text-center">
        <span className="text-sm text-gray-500 dark:text-gray-400">
          Đã hoàn thiện <span className="font-bold text-primary">{readyCount}</span>/64 quẻ — đang triển khai dần
        </span>
      </div>

      <div>
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2 px-1">
          64 Quẻ
        </h2>
        <div className="grid grid-cols-4 gap-2">
          {CHU_DICH_REGISTRY.map((h) => (
            <button
              key={h.id}
              onClick={() => navigate(`/chu-dich/que/${h.id}`)}
              className={`p-3 rounded-xl text-center transition-all ${
                h.status === 'ready'
                  ? 'bg-primary/10 hover:bg-primary/20 text-primary'
                  : 'bg-gray-50 dark:bg-dark-card/50 text-gray-400 dark:text-gray-500 hover:bg-gray-100 dark:hover:bg-dark-border'
              }`}
            >
              <div className="text-[10px] font-mono opacity-70">{h.id}</div>
              <div className="text-xs font-semibold leading-tight mt-0.5">{h.name}</div>
              {h.status !== 'ready' && <div className="text-[9px] mt-1 opacity-60">sắp có</div>}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
