import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { THIEN_CAN } from '../data/fingerCpu/thienCan'
import { DIA_CHI } from '../data/fingerCpu/diaChi'
import { TRIGRAMS } from '../data/fingerCpu/trigrams'

const DATASETS = [
  { key: 'dia-chi', label: 'Địa Chi', table: DIA_CHI, nameOf: (x) => x.ten },
  { key: 'thien-can', label: 'Thiên Can', table: THIEN_CAN, nameOf: (x) => x.ten },
  { key: 'bat-quai', label: 'Bát Quái', table: TRIGRAMS, nameOf: (x) => x.quai },
]

function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function generateQuestion() {
  const ds = DATASETS[Math.floor(Math.random() * DATASETS.length)]
  const correctIdx = Math.floor(Math.random() * ds.table.length)
  const correctItem = ds.table[correctIdx]
  const others = ds.table.filter((_, i) => i !== correctIdx)
  const distractors = shuffle(others).slice(0, 3)
  const choices = shuffle([correctItem, ...distractors]).map((x) => ds.nameOf(x))
  return { dataset: ds.label, index: correctIdx, answer: ds.nameOf(correctItem), choices }
}

const DURATION = 30

export default function FingerCpuGameSpeedPage() {
  const navigate = useNavigate()
  const [running, setRunning] = useState(false)
  const [timeLeft, setTimeLeft] = useState(DURATION)
  const [question, setQuestion] = useState(null)
  const [score, setScore] = useState({ correct: 0, total: 0 })
  const timerRef = useRef(null)

  useEffect(() => {
    if (!running) return
    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) { setRunning(false); return 0 }
        return t - 1
      })
    }, 1000)
    return () => clearInterval(timerRef.current)
  }, [running])

  const start = () => {
    setScore({ correct: 0, total: 0 })
    setTimeLeft(DURATION)
    setQuestion(generateQuestion())
    setRunning(true)
  }

  const answer = (choice) => {
    if (!running) return
    const isCorrect = choice === question.answer
    setScore((s) => ({ correct: s.correct + (isCorrect ? 1 : 0), total: s.total + 1 }))
    setQuestion(generateQuestion())
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/finger-cpu')} className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-sm">
          ← Finger CPU Lab
        </button>
      </div>

      <div>
        <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">⏱️ Speed Challenge</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">30 giây, trả lời càng nhiều càng tốt — trộn Địa Chi/Thiên Can/Bát Quái.</p>
      </div>

      <div className="card p-4 flex items-center justify-between">
        <span className="font-mono text-2xl font-bold text-primary">{timeLeft}s</span>
        <span className="text-sm text-gray-500 dark:text-gray-400">{score.correct}/{score.total} đúng</span>
      </div>

      {!running && timeLeft === DURATION && (
        <div className="card p-8 text-center">
          <button onClick={start} className="btn-primary">▶ Bắt đầu</button>
        </div>
      )}

      {running && question && (
        <div className="card p-6 text-center">
          <div className="text-xs text-gray-400 dark:text-gray-500 mb-1">{question.dataset}[{question.index}] = ?</div>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {question.choices.map((c) => (
              <button key={c} onClick={() => answer(c)} className="btn-secondary text-sm py-3">{c}</button>
            ))}
          </div>
        </div>
      )}

      {!running && timeLeft === 0 && (
        <div className="card p-8 text-center space-y-3">
          <div className="text-3xl">🏁</div>
          <div className="text-lg font-bold text-primary">{score.correct}/{score.total} câu đúng</div>
          <button onClick={start} className="btn-primary">↺ Chơi lại</button>
        </div>
      )}
    </div>
  )
}
