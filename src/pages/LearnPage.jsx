import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchLesson } from '../api'
import { LEVEL_COLORS, LEVEL_NAMES } from '../store'
import { AllTrigrams, HexagramSVG } from '../components/HexagramSVG'

const TRIGRAM_DAY = { 14: 'qian', 15: 'zhen', 16: 'kan', 17: 'gen' }
const LEVEL_TRIGRAMS = { 4: true, 5: true }

export default function LearnPage() {
  const { day } = useParams()
  const navigate = useNavigate()
  const [lesson, setLesson] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    fetchLesson(day)
      .then(setLesson)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [day])

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 flex justify-center">
        <div className="w-10 h-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
      </div>
    )
  }

  if (error || !lesson) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-gray-500 dark:text-gray-400">{error || 'Không tìm thấy bài học'}</p>
        <button onClick={() => navigate('/')} className="btn-primary mt-4">← Về trang chủ</button>
      </div>
    )
  }

  const colors = LEVEL_COLORS[lesson.level] || LEVEL_COLORS[1]
  const dayNum = Number(day)

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      {/* Top nav */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/')} className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-sm">
          ← Trang chủ
        </button>
        <div className="flex-1 h-1.5 bg-gray-100 dark:bg-dark-border rounded-full overflow-hidden">
          <div className="h-full bg-primary rounded-full" style={{ width: `${(dayNum / 30) * 100}%` }} />
        </div>
        <span className="text-xs text-gray-400 dark:text-gray-500 flex-shrink-0">{dayNum}/30</span>
      </div>

      {/* Level + concept badge */}
      <div className="flex flex-wrap items-center gap-2">
        <span className={`level-badge ${colors.bg} ${colors.text}`}>
          Level {lesson.level} · {LEVEL_NAMES[lesson.level]}
        </span>
        <span className="level-badge bg-gray-100 dark:bg-dark-card text-gray-600 dark:text-gray-300">
          Ngày {lesson.day}
        </span>
      </div>

      {/* Title */}
      <div>
        <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-gray-100 leading-tight mb-2">
          {lesson.title}
        </h1>
        <p className="text-gray-500 dark:text-gray-400 text-sm italic">{lesson.concept}</p>
      </div>

      {/* Hexagram for level 4+ */}
      {LEVEL_TRIGRAMS[lesson.level] && (
        <div className="card p-6 flex justify-center">
          {lesson.level === 4 && TRIGRAM_DAY[dayNum] ? (
            <HexagramSVG trigram={TRIGRAM_DAY[dayNum]} size={80} showLabel={true} />
          ) : lesson.level === 4 ? (
            <AllTrigrams />
          ) : (
            <div className="flex gap-4">
              <HexagramSVG trigram="qian" size={56} showLabel={true} />
              <HexagramSVG trigram="kun" size={56} showLabel={true} />
            </div>
          )}
        </div>
      )}

      {/* Main explanation */}
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Giải thích</h2>
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {lesson.explanation.split('\n\n').map((para, i) => (
            <p key={i} className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3 last:mb-0">{para}</p>
          ))}
        </div>
      </div>

      {/* Real example */}
      <div className="card p-5 border-l-4 border-emerald-400">
        <h2 className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 mb-2">🌍 Ví dụ đời thực</h2>
        <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">{lesson.realExample}</p>
      </div>

      {/* Tech example */}
      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary dark:text-primary-light mb-2">💻 Trong CNTT / Quản lý dự án</h2>
        <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">{lesson.techExample}</p>
      </div>

      {/* Image hint */}
      {lesson.imageHint && (
        <div className="card p-4 bg-gray-50 dark:bg-dark-card/50 text-center">
          <p className="text-xs text-gray-400 dark:text-gray-500 italic">💡 {lesson.imageHint}</p>
        </div>
      )}

      {/* Navigation */}
      <div className="flex gap-3 pt-2">
        {dayNum > 1 && (
          <button onClick={() => navigate(`/learn/${dayNum - 1}`)} className="btn-secondary flex-1">
            ← Ngày {dayNum - 1}
          </button>
        )}
        <button
          onClick={() => navigate(`/quiz/${dayNum}`)}
          className="btn-primary flex-1"
        >
          Làm quiz →
        </button>
      </div>
    </div>
  )
}
