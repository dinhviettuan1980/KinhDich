import { LEVEL_COLORS, LEVEL_NAMES } from '../store'
import DayCard from './DayCard'

export default function LevelSection({ level, lessons, progress, todayDay }) {
  const colors = LEVEL_COLORS[level] || LEVEL_COLORS[1]
  const completed = progress?.completedDays || []
  const scores = progress?.scores || {}

  const getStatus = (day) => {
    if (completed.includes(day)) return 'done'
    if (day === todayDay) return 'current'
    if (day < todayDay) return 'current'
    return 'locked'
  }

  const doneCount = lessons.filter((l) => completed.includes(l.day)).length

  return (
    <div className="animate-slide-up">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-3 h-3 rounded-full ${colors.dot}`} />
        <div>
          <h2 className="font-bold text-base text-gray-800 dark:text-gray-100">
            Level {level} — {LEVEL_NAMES[level]}
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {doneCount}/{lessons.length} bài hoàn thành
          </p>
        </div>
        <div className="ml-auto">
          <div className="flex gap-1">
            {lessons.map((l) => (
              <div
                key={l.day}
                className={`w-2.5 h-2.5 rounded-full transition-colors ${
                  completed.includes(l.day) ? colors.dot : 'bg-gray-200 dark:bg-dark-border'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {lessons.map((lesson) => (
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
}
