import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FingerHandSVG from '../components/fingerCpu/FingerHandSVG'
import { MEMORY_CONCEPTS } from '../data/fingerCpu/memoryConcepts'
import { DIA_CHI, DIA_CHI_BY_TEN } from '../data/fingerCpu/diaChi'

export default function FingerCpuMemoryVisualizerPage() {
  const navigate = useNavigate()
  const [concept, setConcept] = useState('ram')
  const [pointerIdx, setPointerIdx] = useState(0)
  const [hashInput, setHashInput] = useState('Tỵ')
  const [cacheHistory, setCacheHistory] = useState([])
  const timerRef = useRef(null)

  useEffect(() => {
    if (concept !== 'pointer') return
    timerRef.current = setInterval(() => setPointerIdx((v) => (v + 1) % 12), 500)
    return () => clearInterval(timerRef.current)
  }, [concept])

  const hashMatch = DIA_CHI_BY_TEN[hashInput.trim()]

  const handleCacheSelect = (i) => {
    setCacheHistory((h) => [i, ...h.filter((x) => x !== i)].slice(0, 3))
  }

  let activeIndex = null
  let interactive = false
  let onSelect
  if (concept === 'pointer') activeIndex = pointerIdx
  if (concept === 'array') activeIndex = null
  if (concept === 'hashmap') activeIndex = hashMatch ? hashMatch.index : null
  if (concept === 'cache') { activeIndex = cacheHistory[0] ?? null; interactive = true; onSelect = handleCacheSelect }

  const current = MEMORY_CONCEPTS.find((c) => c.key === concept)

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/finger-cpu')} className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-sm">
          ← Finger CPU Lab
        </button>
      </div>

      <div>
        <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">🧠 Memory Visualizer</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Chọn 1 khái niệm bên trái — bàn tay bên phải phản ứng tương ứng.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="card p-3 space-y-1.5 h-fit">
          {MEMORY_CONCEPTS.map((c) => (
            <button
              key={c.key}
              onClick={() => setConcept(c.key)}
              className={`w-full text-left flex items-start gap-3 px-3 py-2.5 rounded-xl transition-colors ${
                concept === c.key ? 'bg-primary/10 border border-primary/30' : 'hover:bg-gray-50 dark:hover:bg-dark-card/50'
              }`}
            >
              <span className="text-lg flex-shrink-0">{c.icon}</span>
              <div>
                <div className={`text-sm font-bold ${concept === c.key ? 'text-primary' : 'text-gray-700 dark:text-gray-200'}`}>{c.ten}</div>
                <div className="text-[11px] text-gray-400 dark:text-gray-500 leading-snug">{c.moTa}</div>
              </div>
            </button>
          ))}
        </div>

        <div className="card p-6 flex flex-col items-center justify-center">
          <FingerHandSVG
            activeIndex={activeIndex}
            interactive={interactive}
            onSelect={onSelect}
            labelAt={(i) => DIA_CHI[i].ten}
            size={230}
          />

          {concept === 'hashmap' && (
            <div className="w-full mt-3 space-y-2">
              <input
                value={hashInput}
                onChange={(e) => setHashInput(e.target.value)}
                placeholder="Nhập tên Địa Chi, vd: Tỵ"
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm outline-none focus:border-primary"
              />
              <div className="text-center text-xs text-gray-500 dark:text-gray-400">
                {hashMatch ? `HashMap["${hashInput}"] → index ${hashMatch.index}` : 'Không tìm thấy — thử "Tý", "Mão", "Ngọ"...'}
              </div>
            </div>
          )}

          {concept === 'cache' && (
            <div className="w-full mt-3">
              <div className="text-[11px] text-gray-400 dark:text-gray-500 text-center mb-1.5">Lịch sử tra gần nhất (bấm vào 1 đốt)</div>
              <div className="flex justify-center gap-1.5">
                {cacheHistory.length === 0 && <span className="text-xs text-gray-300 dark:text-gray-600">chưa có</span>}
                {cacheHistory.map((idx, i) => (
                  <span key={idx} className="text-xs px-2 py-1 rounded-lg bg-gray-50 dark:bg-dark-card/50" style={{ opacity: 1 - i * 0.3 }}>
                    {DIA_CHI[idx].ten}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="card p-4 bg-gray-50 dark:bg-dark-card/50 text-center">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          <strong>{current.ten}:</strong> {current.moTa}
        </p>
      </div>
    </div>
  )
}
