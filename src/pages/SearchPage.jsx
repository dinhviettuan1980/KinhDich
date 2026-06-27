import { useState } from 'react'
import { searchKinhdich } from '../api'

const SAMPLES = [
  'người quân tử tự cường không ngừng nghỉ',
  'làm sao biết tiến biết lui đúng lúc',
  'khi gặp hiểm nguy nên xử trí thế nào',
  'ý nghĩa đức khiêm nhường',
]

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState({})

  async function run(q) {
    const text = (q ?? query).trim()
    if (!text) return
    setQuery(text)
    setLoading(true)
    setError('')
    setExpanded({})
    try {
      const hits = await searchKinhdich(text, 6)
      setResults(hits)
    } catch (e) {
      setError(e.message || 'Lỗi tìm kiếm')
      setResults(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-4">
      <div className="mb-4">
        <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">🔍 Tra cứu Kinh Dịch</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Hỏi bằng lời tự nhiên — tìm đúng quẻ, hào, lời kinh theo ý nghĩa (không cần nhớ tên).
        </p>
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); run() }}
        className="flex gap-2 mb-3"
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ví dụ: làm sao để kiên nhẫn chờ thời cơ…"
          className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-dark-border bg-white dark:bg-dark-card text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 rounded-lg text-sm font-semibold bg-primary text-white hover:bg-primary-light transition-colors disabled:opacity-50"
        >
          {loading ? '…' : 'Tìm'}
        </button>
      </form>

      {!results && !loading && (
        <div className="flex flex-wrap gap-2 mb-4">
          {SAMPLES.map((s) => (
            <button
              key={s}
              onClick={() => run(s)}
              className="text-xs px-2.5 py-1.5 rounded-full bg-gray-100 dark:bg-dark-card text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-border transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="card p-3 text-sm text-red-500 mb-3">{error}</div>
      )}

      {loading && (
        <div className="text-sm text-gray-400 py-6 text-center">Đang tìm…</div>
      )}

      {results && results.length === 0 && !loading && (
        <div className="text-sm text-gray-400 py-6 text-center">Không tìm thấy kết quả phù hợp.</div>
      )}

      <div className="flex flex-col gap-3">
        {results?.map((r, i) => {
          const open = expanded[i]
          return (
            <div key={i} className="card p-4">
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">{r.title}</h3>
                <span className="text-[10px] font-mono text-gray-400 flex-shrink-0 mt-0.5">
                  {(r.score * 100).toFixed(0)}%
                </span>
              </div>
              {r.summary && (
                <p className="text-sm text-gray-600 dark:text-gray-300 mt-1.5 italic">{r.summary}</p>
              )}
              <div className={`text-sm text-gray-700 dark:text-gray-200 mt-2 whitespace-pre-wrap ${open ? '' : 'line-clamp-3'}`}>
                {r.content}
              </div>
              {r.content && r.content.length > 200 && (
                <button
                  onClick={() => setExpanded((e) => ({ ...e, [i]: !e[i] }))}
                  className="text-xs text-primary font-medium mt-2 hover:underline"
                >
                  {open ? 'Thu gọn' : 'Xem đầy đủ'}
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
