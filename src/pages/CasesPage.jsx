import { useEffect, useState } from 'react'
import { fetchCases, fetchCase } from '../api'

function CaseDetail({ id, onBack, onNext, hasNext }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    setLoading(true); setSelected(null); setData(null)
    fetchCase(id).then(setData).catch(() => {}).finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return <div className="py-16 flex justify-center"><div className="w-9 h-9 rounded-full border-4 border-primary border-t-transparent animate-spin" /></div>
  }
  if (!data) return null

  const revealed = selected !== null

  const optClass = (idx) => {
    const base = 'w-full text-left px-4 py-3 rounded-xl border text-sm transition-all '
    if (!revealed) return base + 'border-gray-200 dark:border-dark-border hover:border-primary hover:bg-primary/5 dark:bg-dark-card cursor-pointer'
    if (idx === data.correct) return base + 'border-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300'
    if (idx === selected) return base + 'border-red-400 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300'
    return base + 'border-gray-200 dark:border-dark-border opacity-50 dark:bg-dark-card'
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <button onClick={onBack} className="text-sm text-gray-400 hover:text-gray-700 dark:hover:text-gray-200">← Danh sách tình huống</button>

      <div className="card p-5">
        <span className="level-badge bg-primary/10 text-primary mb-3 inline-block">Tình huống {data.id}</span>
        <h2 className="text-lg font-display font-bold text-gray-900 dark:text-gray-100 mb-2">{data.title}</h2>
        <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{data.scenario}</p>
      </div>

      <div className="space-y-2">
        {data.options.map((opt, idx) => (
          <button key={idx} disabled={revealed} onClick={() => setSelected(idx)} className={optClass(idx)}>
            <span className="text-gray-400 dark:text-gray-500 mr-2 font-mono">{String.fromCharCode(65 + idx)}.</span>
            {opt}
          </button>
        ))}
      </div>

      {revealed && (
        <div className="card p-5 border-l-4 border-primary animate-slide-up">
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-sm font-bold ${selected === data.correct ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500'}`}>
              {selected === data.correct ? '✓ Chính xác!' : '✗ Chưa đúng'}
            </span>
            <span className="text-xs text-gray-400">· Khái niệm: {data.concept}</span>
          </div>
          <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">{data.explanation}</p>
        </div>
      )}

      {revealed && (
        <div className="flex gap-3">
          <button onClick={onBack} className="btn-secondary flex-1">Danh sách</button>
          {hasNext && <button onClick={onNext} className="btn-primary flex-1">Tình huống tiếp →</button>}
        </div>
      )}
    </div>
  )
}

export default function CasesPage() {
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeId, setActiveId] = useState(null)

  useEffect(() => {
    fetchCases().then(setCases).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const idx = cases.findIndex((c) => c.id === activeId)
  const nextId = idx >= 0 && idx < cases.length - 1 ? cases[idx + 1].id : null

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 animate-fade-in">
      {activeId == null ? (
        <>
          <div className="mb-5">
            <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-gray-100">🧩 Tình huống thực tế</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Đọc tình huống, chọn câu trả lời, rồi xem lời giải bằng tư duy Kinh Dịch.
            </p>
          </div>
          {loading ? (
            <div className="py-16 flex justify-center"><div className="w-9 h-9 rounded-full border-4 border-primary border-t-transparent animate-spin" /></div>
          ) : (
            <div className="space-y-2">
              {cases.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setActiveId(c.id)}
                  className="w-full text-left card p-4 hover:border-primary hover:scale-[1.01] transition-all"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xs font-mono text-gray-400 mt-0.5">{String(c.id).padStart(2, '0')}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold text-gray-800 dark:text-gray-100">{c.title}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mt-0.5">{c.scenario}</div>
                      <span className="inline-block mt-1.5 text-[10px] font-medium px-2 py-0.5 rounded-full bg-primary/10 text-primary">{c.concept}</span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </>
      ) : (
        <CaseDetail
          id={activeId}
          onBack={() => setActiveId(null)}
          onNext={() => setActiveId(nextId)}
          hasNext={!!nextId}
        />
      )}
    </div>
  )
}
