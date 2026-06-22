import { useNavigate } from 'react-router-dom'
import { LEVEL_COLORS } from '../store'

const STATUS = {
  done: { icon: '✓', label: 'Hoàn thành', cls: 'ring-2 ring-emerald-400 bg-emerald-50 dark:bg-emerald-900/20' },
  current: { icon: '▶', label: 'Học ngay', cls: 'ring-2 ring-primary bg-primary/5 dark:bg-primary/10 shadow-lg shadow-primary/20' },
  locked: { icon: '🔒', label: 'Chưa mở', cls: 'opacity-50 cursor-not-allowed' },
}

export default function DayCard({ lesson, status, score }) {
  const navigate = useNavigate()
  const s = STATUS[status]
  const colors = LEVEL_COLORS[lesson.level] || LEVEL_COLORS[1]

  const handleClick = () => {
    if (status === 'locked') return
    navigate(`/learn/${lesson.day}`)
  }

  return (
    <button
      onClick={handleClick}
      disabled={status === 'locked'}
      className={`w-full text-left p-4 rounded-2xl border transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] ${s.cls} border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${colors.bg} ${colors.text}`}>
              Ngày {lesson.day}
            </span>
            {score != null && (
              <span className="text-[10px] font-mono text-gray-500 dark:text-gray-400">{score}đ</span>
            )}
          </div>
          <p className="text-sm font-semibold text-gray-800 dark:text-gray-200 leading-snug line-clamp-2">
            {lesson.title}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-1">
            {lesson.concept}
          </p>
        </div>
        <div className={`text-lg flex-shrink-0 ${status === 'done' ? 'text-emerald-500' : status === 'current' ? 'text-primary' : 'text-gray-400'}`}>
          {s.icon}
        </div>
      </div>
    </button>
  )
}
