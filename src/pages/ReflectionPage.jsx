import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchReflections } from '../api'

export default function ReflectionPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchReflections().then(setItems).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const fmt = (iso) => {
    try { return new Date(iso).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' }) }
    catch { return '' }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      <div>
        <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-gray-100">🪷 Nhật ký suy ngẫm</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Đọc lại để thấy chính mình thay đổi qua thời gian.
        </p>
      </div>

      {loading ? (
        <div className="py-16 flex justify-center">
          <div className="w-9 h-9 rounded-full border-4 border-primary border-t-transparent animate-spin" />
        </div>
      ) : items.length === 0 ? (
        <div className="card p-8 text-center">
          <div className="text-4xl mb-3">🌱</div>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">
            Chưa có suy ngẫm nào. Hãy học một bài và viết lại quan sát của bạn ở phần "Suy ngẫm".
          </p>
          <button onClick={() => navigate('/')} className="btn-primary">Bắt đầu học</button>
        </div>
      ) : (
        <div className="relative pl-6 space-y-4">
          {/* timeline line */}
          <div className="absolute left-[7px] top-2 bottom-2 w-0.5 bg-gray-200 dark:bg-dark-border" />
          {items.map((r) => (
            <div key={r.id} className="relative">
              <div className="absolute -left-[22px] top-1.5 w-3.5 h-3.5 rounded-full bg-primary ring-4 ring-white dark:ring-dark-bg" />
              <div className="card p-4">
                <div className="flex items-center justify-between mb-1.5">
                  <button
                    onClick={() => navigate(`/learn/${r.day}`)}
                    className="text-xs font-bold uppercase tracking-wider text-primary hover:underline"
                  >
                    Ngày {r.day}
                  </button>
                  <span className="text-xs text-gray-400">{fmt(r.createdAt)}</span>
                </div>
                <p className="text-gray-700 dark:text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">{r.content}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
