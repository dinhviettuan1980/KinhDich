import { useEffect, useState } from 'react'
import { fetchLessons, fetchProgress } from '../api'
import { useStore, LEVEL_COLORS, LEVEL_NAMES } from '../store'
import DayCard from '../components/DayCard'

const LEVEL_ICONS = { 1: '🌱', 2: '☯', 3: '⚡', 4: '🧭', 5: '🔮', 6: '🔄', 7: '🏛' }

export default function MapPage() {
  const { progress, lessons, setProgress, setLessons } = useStore()
  const [loading, setLoading] = useState(!lessons.length)

  useEffect(() => {
    if (lessons.length) return
    Promise.all([fetchLessons(), fetchProgress()])
      .then(([ls, pr]) => { setLessons(ls); setProgress(pr) })
      .finally(() => setLoading(false))
  }, [])

  const completed = progress?.completedDays || []
  const scores = progress?.scores || {}

  const getStatus = (day) => {
    if (completed.includes(day)) return 'done'
    return 'current'
  }

  const grouped = {}
  for (const l of lessons) {
    if (!grouped[l.level]) grouped[l.level] = []
    grouped[l.level].push(l)
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 flex justify-center">
        <div className="w-10 h-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-8 animate-fade-in">
      <div>
        <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-gray-100">🗺️ Hành trình 30 ngày</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {completed.length}/30 bài hoàn thành · {Math.round((completed.length / 30) * 100)}% tiến độ
        </p>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-xs">
        {[
          { icon: '✓', label: 'Hoàn thành', cls: 'text-emerald-600 dark:text-emerald-400' },
          { icon: '▶', label: 'Đang học', cls: 'text-primary' },
          { icon: '🔒', label: 'Chưa mở', cls: 'text-gray-400' },
        ].map((l) => (
          <div key={l.label} className={`flex items-center gap-1 font-medium ${l.cls}`}>
            <span>{l.icon}</span>
            <span>{l.label}</span>
          </div>
        ))}
      </div>

      {/* Level groups */}
      {Object.keys(grouped).map((level) => {
        const colors = LEVEL_COLORS[Number(level)]
        return (
          <div key={level} className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">{LEVEL_ICONS[Number(level)]}</span>
              <h2 className="font-bold text-sm text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Level {level} — {LEVEL_NAMES[Number(level)]}
              </h2>
              <span className="text-xs text-gray-400 ml-auto">
                Ngày {grouped[level][0].day}–{grouped[level][grouped[level].length - 1].day}
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {grouped[level].map((lesson) => (
                <DayCard
                  key={lesson.day}
                  lesson={lesson}
                  status={getStatus(lesson.day)}
                  score={scores[lesson.day]}
                />
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
