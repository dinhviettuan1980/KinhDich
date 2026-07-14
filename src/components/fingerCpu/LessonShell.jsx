import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LESSONS, lessonNeighbors } from '../../data/fingerCpu/lessons'
import { useFingerCpuStore } from '../../data/fingerCpu/store'
import { EASY_EXPLAIN, DEV_NOTE } from '../../data/fingerCpu/aiExplain'

// Khung dùng chung cho mọi bài học Finger CPU Lab: progress bar, tiêu đề, prev/next,
// bookmark, AI Explain (2 lăng kính viết sẵn) + Developer Mode (tự hiện lăng kính lập trình viên).
// Tương tự LearnPage.jsx nhưng theo track riêng (25 bài, không dùng level/quiz của app chính).
export default function LessonShell({ lesson, children }) {
  const navigate = useNavigate()
  const { prev, next } = lessonNeighbors(lesson.id)
  const total = LESSONS.length

  const { developerMode, bookmarks, toggleBookmark, markVisited } = useFingerCpuStore()
  const bookmarked = bookmarks.includes(lesson.id)
  const [explainMode, setExplainMode] = useState(null) // null | 'easy' | 'dev'

  useEffect(() => { markVisited(lesson.id) }, [lesson.id, markVisited])
  useEffect(() => { setExplainMode(null) }, [lesson.id])

  const showDev = explainMode === 'dev' || (developerMode && explainMode !== 'easy')

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/finger-cpu')}
          className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-sm flex-shrink-0"
        >
          ← Finger CPU Lab
        </button>
        <div className="flex-1 h-1.5 bg-gray-100 dark:bg-dark-border rounded-full overflow-hidden">
          <div className="h-full bg-primary rounded-full" style={{ width: `${(lesson.id / total) * 100}%` }} />
        </div>
        <span className="text-xs text-gray-400 dark:text-gray-500 flex-shrink-0">
          Bài {lesson.id}/{total}
        </span>
      </div>

      <div>
        <div className="flex items-start justify-between gap-2">
          <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-gray-100 leading-tight mb-1">
            {lesson.title}
          </h1>
          <button
            onClick={() => toggleBookmark(lesson.id)}
            className="flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-dark-card transition-colors text-lg"
            aria-label="Đánh dấu yêu thích"
            title={bookmarked ? 'Bỏ đánh dấu' : 'Đánh dấu yêu thích'}
          >
            {bookmarked ? '⭐' : '☆'}
          </button>
        </div>
        <p className="text-gray-500 dark:text-gray-400 text-sm italic">{lesson.subtitle}</p>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => setExplainMode((m) => (m === 'easy' ? null : 'easy'))}
          className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${
            explainMode === 'easy' ? 'bg-emerald-500 text-white' : 'bg-gray-50 dark:bg-dark-card/50 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-border'
          }`}
        >
          🧠 Giải thích dễ hơn
        </button>
        <button
          onClick={() => setExplainMode((m) => (m === 'dev' ? null : 'dev'))}
          className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${
            explainMode === 'dev' ? 'bg-primary text-white' : 'bg-gray-50 dark:bg-dark-card/50 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-border'
          }`}
        >
          💻 Dành cho lập trình viên
        </button>
      </div>

      {explainMode === 'easy' && EASY_EXPLAIN[lesson.id] && (
        <div className="card p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 animate-slide-up">
          <p className="text-sm text-emerald-800 dark:text-emerald-200">🧠 {EASY_EXPLAIN[lesson.id]}</p>
        </div>
      )}
      {showDev && DEV_NOTE[lesson.id] && (
        <div className="card p-4 bg-primary/5 border border-primary/20 animate-slide-up">
          <p className="text-sm font-mono text-primary dark:text-primary-light">💻 {DEV_NOTE[lesson.id]}</p>
          {developerMode && explainMode !== 'dev' && (
            <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1.5">Tự động hiện vì Developer Mode đang bật</p>
          )}
        </div>
      )}

      {children}

      <div className="flex gap-3 pt-2">
        {prev && (
          <button onClick={() => navigate(`/finger-cpu/bai/${prev.id}`)} className="btn-secondary flex-1 text-sm">
            ← Bài {prev.id}: {prev.title}
          </button>
        )}
        {next && (
          <button onClick={() => navigate(`/finger-cpu/bai/${next.id}`)} className="btn-primary flex-1 text-sm">
            Bài {next.id}: {next.title} →
          </button>
        )}
      </div>
    </div>
  )
}
