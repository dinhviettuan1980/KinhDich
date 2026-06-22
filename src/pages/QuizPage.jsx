import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchLesson } from '../api'
import QuizFlow from '../components/QuizFlow'

export default function QuizPage() {
  const { day } = useParams()
  const navigate = useNavigate()
  const [lesson, setLesson] = useState(null)
  const [loading, setLoading] = useState(true)
  const [result, setResult] = useState(null)

  useEffect(() => {
    fetchLesson(day)
      .then(setLesson)
      .finally(() => setLoading(false))
  }, [day])

  if (loading) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 flex justify-center">
        <div className="w-10 h-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
      </div>
    )
  }

  if (!lesson) return null

  if (result) {
    const { score, correct, total } = result
    const isPerfect = score === 100
    return (
      <div className="max-w-xl mx-auto px-4 py-12 text-center animate-fade-in space-y-6">
        <div className="text-7xl">{isPerfect ? '🎉' : score >= 66 ? '👍' : '📚'}</div>
        <h2 className="text-2xl font-display font-bold text-gray-900 dark:text-gray-100">
          {isPerfect ? 'Xuất sắc!' : score >= 66 ? 'Tốt lắm!' : 'Cần ôn lại!'}
        </h2>
        <p className="text-gray-500 dark:text-gray-400">
          Bạn trả lời đúng <strong className="text-primary">{correct}/{total}</strong> câu
        </p>
        <div className="card p-6">
          <div className="text-5xl font-display font-bold text-primary mb-1">{score}</div>
          <div className="text-sm text-gray-400 dark:text-gray-500">điểm</div>
        </div>
        <div className="flex gap-3">
          <button onClick={() => navigate(`/learn/${day}`)} className="btn-secondary flex-1">
            ← Đọc lại bài
          </button>
          <button
            onClick={() => navigate(Number(day) < 30 ? '/' : '/')}
            className="btn-primary flex-1"
          >
            {Number(day) < 30 ? 'Về Dashboard →' : '🎓 Hoàn thành!'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-xl mx-auto px-4 py-6 space-y-5">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(`/learn/${day}`)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-sm">
          ← Bài học
        </button>
        <h1 className="font-display font-bold text-lg text-gray-900 dark:text-gray-100">
          Quiz — Ngày {day}
        </h1>
      </div>
      <QuizFlow
        questions={lesson.quiz}
        day={Number(day)}
        onDone={(score, correct, total) => setResult({ score, correct, total })}
      />
    </div>
  )
}
