import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchLessons, fetchProgress } from '../api'
import { useStore, LEVEL_NAMES } from '../store'
import LevelSection from '../components/LevelSection'

export default function Dashboard() {
  const navigate = useNavigate()
  const { progress, lessons, setProgress, setLessons, getTodayDay } = useStore()
  const [loading, setLoading] = useState(!lessons.length)
  const [error, setError] = useState(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [ls, pr] = await Promise.all([fetchLessons(), fetchProgress()])
        setLessons(ls)
        setProgress(pr)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const todayDay = getTodayDay()
  const completed = progress?.completedDays || []
  const percent = Math.round((completed.length / 30) * 100)
  const streak = progress?.streak || 0

  const grouped = {}
  for (const l of lessons) {
    if (!grouped[l.level]) grouped[l.level] = []
    grouped[l.level].push(l)
  }

  const todayLesson = lessons.find((l) => l.day === todayDay)

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 flex flex-col items-center gap-4">
        <div className="w-10 h-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
        <p className="text-gray-500 dark:text-gray-400">Đang tải...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="text-5xl mb-4">⚠️</div>
        <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-2">Backend chưa kết nối</h2>
        <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">{error}</p>
        <button onClick={() => window.location.reload()} className="btn-primary">
          Thử lại
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-6 animate-fade-in">
      {/* Hero stats */}
      <div className="card p-6 bg-gradient-to-br from-primary/5 to-purple-100/50 dark:from-primary/10 dark:to-purple-900/20">
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-1">
              Hành trình học Kinh Dịch
            </p>
            <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-gray-100">
              {completed.length === 0
                ? 'Bắt đầu hôm nay!'
                : `Ngày ${todayDay} / 30`}
            </h1>
          </div>
          <div className="text-right">
            {streak > 0 && (
              <div className="flex items-center gap-1 bg-accent/10 text-accent px-3 py-1.5 rounded-full font-bold">
                🔥 {streak} ngày
              </div>
            )}
          </div>
        </div>

        {/* Progress bar */}
        <div className="mb-4">
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1.5">
            <span>{completed.length} bài hoàn thành</span>
            <span className="font-bold text-primary">{percent}%</span>
          </div>
          <div className="h-2.5 bg-gray-200 dark:bg-dark-border rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary to-primary-light rounded-full transition-all duration-700"
              style={{ width: `${percent}%` }}
            />
          </div>
        </div>

        {/* CTA */}
        {todayLesson && (
          <button
            onClick={() => navigate(`/learn/${todayDay}`)}
            className="btn-primary w-full text-center"
          >
            {completed.includes(todayDay) ? `Ôn lại ngày ${todayDay}` : `▶ Học ngày ${todayDay}: ${todayLesson.title.slice(0, 40)}${todayLesson.title.length > 40 ? '...' : ''}`}
          </button>
        )}
      </div>

      {/* Quick stats row */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Đã học', value: completed.length, unit: 'bài' },
          { label: 'Còn lại', value: 30 - completed.length, unit: 'bài' },
          { label: 'Chuỗi', value: streak, unit: 'ngày 🔥' },
        ].map((s) => (
          <div key={s.label} className="card p-3 text-center">
            <div className="text-2xl font-display font-bold text-primary">{s.value}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">{s.unit}</div>
            <div className="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wide">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Levels */}
      <div className="space-y-6">
        {Object.keys(grouped).map((level) => (
          <LevelSection
            key={level}
            level={Number(level)}
            lessons={grouped[level]}
            progress={progress}
            todayDay={todayDay}
          />
        ))}
      </div>
    </div>
  )
}
