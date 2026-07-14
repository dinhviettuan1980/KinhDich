import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FingerHandSVG from '../components/fingerCpu/FingerHandSVG'
import { DIA_CHI } from '../data/fingerCpu/diaChi'

const randomChi = () => DIA_CHI[Math.floor(Math.random() * DIA_CHI.length)]

export default function FingerCpuGameMemoryPage() {
  const navigate = useNavigate()
  const [target, setTarget] = useState(randomChi)
  const [feedback, setFeedback] = useState(null) // null | 'correct' | 'wrong'
  const [wrongIndex, setWrongIndex] = useState(null)
  const [score, setScore] = useState({ correct: 0, wrong: 0 })

  const next = () => { setTarget(randomChi()); setFeedback(null); setWrongIndex(null) }

  const handleSelect = (idx) => {
    if (feedback) return
    const isCorrect = idx === target.index
    setFeedback(isCorrect ? 'correct' : 'wrong')
    if (!isCorrect) setWrongIndex(idx)
    setScore((s) => ({ correct: s.correct + (isCorrect ? 1 : 0), wrong: s.wrong + (isCorrect ? 0 : 1) }))
    setTimeout(next, 1100)
  }

  const displayIndex = feedback === 'wrong' ? wrongIndex : feedback === 'correct' ? target.index : null

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/finger-cpu')} className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-sm">
          ← Finger CPU Lab
        </button>
      </div>

      <div>
        <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">🎯 Finger Memory Trainer</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Chạm đúng đốt tay ứng với tên được hỏi.</p>
      </div>

      <div className="flex items-center justify-center gap-4 text-sm">
        <span className="text-emerald-500 font-bold">✓ {score.correct}</span>
        <span className="text-red-500 font-bold">✕ {score.wrong}</span>
      </div>

      <div className="card p-8 text-center">
        <div className="text-xs text-gray-400 dark:text-gray-500 mb-1">Câu hỏi</div>
        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">{target.ten} ở đâu?</div>

        <FingerHandSVG
          activeIndex={displayIndex}
          interactive={!feedback}
          onSelect={handleSelect}
          labelAt={(i) => DIA_CHI[i].ten}
          size={240}
        />

        <div className="h-8 mt-3">
          {feedback === 'correct' && <span className="text-emerald-500 font-bold text-sm">✅ Chính xác!</span>}
          {feedback === 'wrong' && (
            <span className="text-red-500 font-bold text-sm">
              ❌ Sai rồi — đó là "{DIA_CHI[wrongIndex].ten}", "{target.ten}" ở finger[{target.index}]
            </span>
          )}
        </div>
      </div>

      <button onClick={() => { setScore({ correct: 0, wrong: 0 }); next() }} className="btn-secondary w-full text-sm">
        ↺ Chơi lại từ đầu
      </button>
    </div>
  )
}
