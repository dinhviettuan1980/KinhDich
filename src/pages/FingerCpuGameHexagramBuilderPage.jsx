import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { trigramFromBits } from '../data/fingerCpu/trigrams'
import { lookupHexagram, getHexagramById } from '../data/hexagrams'

function HaoBar({ on, onClick }) {
  return (
    <button onClick={onClick} className="w-full h-8 flex items-center gap-1.5 group">
      {on ? (
        <span className="h-3 flex-1 rounded bg-primary group-hover:bg-primary-dark transition-colors" />
      ) : (
        <>
          <span className="h-3 flex-1 rounded bg-gray-300 dark:bg-dark-border group-hover:bg-gray-400 transition-colors" />
          <span className="h-3 flex-1 rounded bg-gray-300 dark:bg-dark-border group-hover:bg-gray-400 transition-colors" />
        </>
      )}
    </button>
  )
}

export default function FingerCpuGameHexagramBuilderPage() {
  const navigate = useNavigate()
  const [bits, setBits] = useState([1, 1, 1, 1, 1, 1]) // index 0 = hào 1 (dưới) .. 5 = hào 6 (trên)
  const toggle = (i) => setBits((b) => b.map((v, idx) => (idx === i ? 1 - v : v)))

  const lower = trigramFromBits(bits.slice(0, 3))
  const upper = trigramFromBits(bits.slice(3, 6))
  const hex = getHexagramById(lookupHexagram(upper.pinyin, lower.pinyin))

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/finger-cpu')} className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-sm">
          ← Finger CPU Lab
        </button>
      </div>

      <div>
        <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">🧱 Hexagram Builder</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Bấm từng hào — quẻ tự sinh ngay khi đủ 6 hào.</p>
      </div>

      <div className="card p-6">
        <div className="max-w-xs mx-auto space-y-1">
          <div className="text-[10px] text-gray-400 dark:text-gray-500 text-center mb-1">Thượng quái (hào 4–6)</div>
          {[5, 4, 3].map((i) => <HaoBar key={i} on={bits[i] === 1} onClick={() => toggle(i)} />)}
          <div className="h-2" />
          <div className="text-[10px] text-gray-400 dark:text-gray-500 text-center mb-1">Hạ quái (hào 1–3)</div>
          {[2, 1, 0].map((i) => <HaoBar key={i} on={bits[i] === 1} onClick={() => toggle(i)} />)}
        </div>

        <div className="mt-5 p-4 rounded-xl bg-gray-50 dark:bg-dark-card/50 text-center">
          <div className="flex items-center justify-center gap-2 text-2xl mb-1">
            <span>{upper.glyph}</span><span>{lower.glyph}</span>
          </div>
          <div className="font-mono text-xs text-gray-400 mb-1">Quẻ số {hex.id}</div>
          <div className="text-lg font-bold text-primary">{hex.name}</div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{hex.shortMeaning}</p>
        </div>
      </div>

      <div className="card p-4 bg-gray-50 dark:bg-dark-card/50 text-center">
        <p className="text-xs text-gray-400 dark:text-gray-500 italic">
          💡 64 tổ hợp có thể — thử bấm ngẫu nhiên vài lần để thấy quẻ luôn đổi theo đúng logic Bài 9.
        </p>
      </div>
    </div>
  )
}
