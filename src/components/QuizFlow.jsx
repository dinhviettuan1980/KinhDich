import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { markComplete } from '../api'

export default function QuizFlow({ questions, day, onDone }) {
  const [current, setCurrent] = useState(0)
  const [selected, setSelected] = useState(null)
  const [answers, setAnswers] = useState([])
  const [saving, setSaving] = useState(false)
  const navigate = useNavigate()

  const q = questions[current]
  const totalQ = questions.length

  const handleSelect = (idx) => {
    if (selected !== null) return
    setSelected(idx)
  }

  const handleNext = async () => {
    const newAnswers = [...answers, { selected, correct: q.correct }]
    setAnswers(newAnswers)

    if (current + 1 < totalQ) {
      setCurrent(current + 1)
      setSelected(null)
    } else {
      // Done — calculate score
      const correctCount = newAnswers.filter((a) => a.selected === a.correct).length
      const score = Math.round((correctCount / totalQ) * 100)
      setSaving(true)
      try {
        await markComplete(day, score)
      } catch (e) {
        console.error(e)
      }
      setSaving(false)
      onDone(score, correctCount, totalQ)
    }
  }

  const optionClass = (idx) => {
    const base = 'w-full text-left px-4 py-3 rounded-xl border text-sm font-medium transition-all duration-200 '
    if (selected === null) {
      return base + 'border-gray-200 dark:border-dark-border hover:border-primary hover:bg-primary/5 dark:bg-dark-card dark:hover:bg-primary/10 cursor-pointer'
    }
    if (idx === q.correct) return base + 'border-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300'
    if (idx === selected && idx !== q.correct) return base + 'border-red-400 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300'
    return base + 'border-gray-200 dark:border-dark-border opacity-50 dark:bg-dark-card'
  }

  return (
    <div className="animate-fade-in space-y-6">
      {/* Progress */}
      <div className="flex items-center gap-3">
        <div className="flex gap-1.5">
          {questions.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 w-8 rounded-full transition-colors ${
                i < current ? 'bg-emerald-400' : i === current ? 'bg-primary' : 'bg-gray-200 dark:bg-dark-border'
              }`}
            />
          ))}
        </div>
        <span className="text-xs text-gray-500 dark:text-gray-400 ml-auto">Câu {current + 1}/{totalQ}</span>
      </div>

      {/* Question */}
      <div className="card p-5">
        <p className="text-base font-semibold text-gray-800 dark:text-gray-100 leading-relaxed mb-4">
          {q.question}
        </p>
        <div className="space-y-2">
          {q.options.map((opt, idx) => (
            <button key={idx} onClick={() => handleSelect(idx)} className={optionClass(idx)}>
              <span className="text-gray-400 dark:text-gray-500 mr-2 font-mono">{String.fromCharCode(65 + idx)}.</span>
              {opt}
            </button>
          ))}
        </div>
      </div>

      {/* Explanation */}
      {selected !== null && (
        <div className={`p-4 rounded-xl border text-sm animate-slide-up ${
          selected === q.correct
            ? 'border-emerald-300 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-800 dark:text-emerald-200'
            : 'border-red-300 bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200'
        }`}>
          <p className="font-bold mb-1">{selected === q.correct ? '✓ Chính xác!' : '✗ Chưa đúng'}</p>
          <p className="leading-relaxed">{q.explanation}</p>
        </div>
      )}

      {selected !== null && (
        <button onClick={handleNext} disabled={saving} className="btn-primary w-full">
          {saving ? 'Đang lưu...' : current + 1 < totalQ ? 'Câu tiếp theo →' : 'Xem kết quả'}
        </button>
      )}
    </div>
  )
}
