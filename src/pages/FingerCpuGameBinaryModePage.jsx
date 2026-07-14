import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TRIGRAMS } from '../data/fingerCpu/trigrams'
import { lookupHexagram, getHexagramById } from '../data/hexagrams'

export default function FingerCpuGameBinaryModePage() {
  const navigate = useNavigate()
  const [mode, setMode] = useState('bat-quai') // 'bat-quai' | '64-que'
  const max = mode === 'bat-quai' ? 8 : 64
  const bitCount = mode === 'bat-quai' ? 3 : 6
  const [n, setN] = useState(0)
  const [playing, setPlaying] = useState(false)
  const timerRef = useRef(null)

  useEffect(() => { setN(0); setPlaying(false) }, [mode])

  useEffect(() => {
    if (!playing) return
    timerRef.current = setInterval(() => setN((v) => (v + 1) % max), 500)
    return () => clearInterval(timerRef.current)
  }, [playing, max])

  const binary = n.toString(2).padStart(bitCount, '0')

  let content
  if (mode === 'bat-quai') {
    const t = TRIGRAMS[n]
    content = (
      <div className="text-center">
        <div className="text-4xl mb-1">{t.glyph}</div>
        <div className="text-lg font-bold text-primary">{t.quai}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">{t.hinh}</div>
      </div>
    )
  } else {
    const lowerVal = n & 0b111
    const upperVal = (n >> 3) & 0b111
    const lower = TRIGRAMS[lowerVal]
    const upper = TRIGRAMS[upperVal]
    const hex = getHexagramById(lookupHexagram(upper.pinyin, lower.pinyin))
    content = (
      <div className="text-center">
        <div className="text-3xl mb-1">{upper.glyph}{lower.glyph}</div>
        <div className="text-lg font-bold text-primary">{hex.name}</div>
        <div className="text-xs text-gray-500 dark:text-gray-400">Quẻ số {hex.id} · {upper.quai} trên, {lower.quai} dưới</div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/finger-cpu')} className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-sm">
          ← Finger CPU Lab
        </button>
      </div>

      <div>
        <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">🔟 Binary Mode</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Bát Quái = 3 bit, 64 Quẻ = 6 bit — đếm nhị phân trực tiếp.</p>
      </div>

      <div className="flex gap-1.5">
        <button
          onClick={() => setMode('bat-quai')}
          className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${mode === 'bat-quai' ? 'bg-primary text-white' : 'bg-gray-50 dark:bg-dark-card/50 text-gray-500 dark:text-gray-400'}`}
        >
          Bát Quái (3 bit)
        </button>
        <button
          onClick={() => setMode('64-que')}
          className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${mode === '64-que' ? 'bg-primary text-white' : 'bg-gray-50 dark:bg-dark-card/50 text-gray-500 dark:text-gray-400'}`}
        >
          64 Quẻ (6 bit)
        </button>
      </div>

      <div className="card p-6 space-y-4">
        <div className="flex justify-center gap-1.5">
          {binary.split('').map((b, i) => (
            <span key={i} className={`w-9 h-9 rounded-lg flex items-center justify-center font-mono text-sm font-bold ${b === '1' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-dark-card text-gray-400'}`}>
              {b}
            </span>
          ))}
        </div>
        <div className="text-center font-mono text-xs text-gray-400">n = {n} / {max - 1}</div>

        {content}

        <div className="flex items-center gap-2">
          <button onClick={() => { setPlaying(false); setN((v) => (v - 1 + max) % max) }} className="btn-secondary text-sm px-3">◀</button>
          <button onClick={() => setPlaying((p) => !p)} className="btn-primary flex-1 text-sm">
            {playing ? '⏸ Tạm dừng' : '▶ Đếm tự động'}
          </button>
          <button onClick={() => { setPlaying(false); setN((v) => (v + 1) % max) }} className="btn-secondary text-sm px-3">▶</button>
        </div>
      </div>
    </div>
  )
}
