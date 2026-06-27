import { useState } from 'react'
import { Link } from 'react-router-dom'
import { searchKinhdich, fetchHexagramText } from '../api'
import { resolveHexagram } from '../data/hexResolve'

const SAMPLES = [
  'Thuần Càn',
  'làm sao biết tiến biết lui đúng lúc',
  'khi gặp hiểm nguy nên xử trí thế nào',
  'ý nghĩa đức khiêm nhường',
]

const MEANING_FIELDS = [
  ['lifeMeaning', '🌱 Đời sống'],
  ['businessMeaning', '💼 Kinh doanh'],
  ['techMeaning', '💻 Công nghệ'],
]

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [hexInfo, setHexInfo] = useState(null) // { hex, bookName, chunks }
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState({}) // semantic cards
  const [openBook, setOpenBook] = useState({}) // nguyên văn sách

  async function run(q) {
    const text = (q ?? query).trim()
    if (!text) return
    setQuery(text)
    setLoading(true)
    setError('')
    setExpanded({})
    setOpenBook({})
    setHexInfo(null)
    setResults(null)

    const resolved = resolveHexagram(text)
    try {
      // Nếu là TÊN quẻ → lấy nguyên văn sách của quẻ đó (khớp theo tên, chính xác).
      // Luôn chạy thêm semantic để gợi ý các đoạn liên quan theo ý nghĩa.
      const [chunks, hits] = await Promise.all([
        resolved ? fetchHexagramText(resolved.bookName).catch(() => []) : Promise.resolve(null),
        searchKinhdich(text, 6).catch(() => []),
      ])
      if (resolved) setHexInfo({ ...resolved, chunks: chunks || [] })
      setResults(hits)
    } catch (e) {
      setError(e.message || 'Lỗi tìm kiếm')
    } finally {
      setLoading(false)
    }
  }

  const hex = hexInfo?.hex

  return (
    <div className="max-w-2xl mx-auto px-4 py-4">
      <div className="mb-4">
        <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">🔍 Tra cứu Kinh Dịch</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Gõ <b>tên quẻ</b> (Càn, Kiền, Thuần Càn, Thủy Lôi Truân, số 1…) để xem ý nghĩa &amp; nguyên văn sách,
          hoặc hỏi bằng <b>lời tự nhiên</b> để tìm theo ý nghĩa.
        </p>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); run() }} className="flex gap-2 mb-3">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ví dụ: Thuần Càn — hoặc: làm sao để kiên nhẫn chờ thời cơ…"
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

      {!results && !hexInfo && !loading && (
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

      {error && <div className="card p-3 text-sm text-red-500 mb-3">{error}</div>}
      {loading && <div className="text-sm text-gray-400 py-6 text-center">Đang tìm…</div>}

      {/* ===== Thẻ ý nghĩa quẻ (từ trang 64 quẻ) — khi gõ đúng tên ===== */}
      {hex && (
        <div className="card p-4 mb-3 border-l-4 border-primary">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h2 className="text-lg font-display font-bold text-gray-900 dark:text-gray-100">{hex.name}</h2>
              <div className="text-xs text-gray-400 mt-0.5">
                Quẻ số {hex.id}{hexInfo.bookName && hexInfo.bookName !== hex.name ? ` · trong sách: “${hexInfo.bookName}”` : ''}
              </div>
            </div>
            <Link to={`/que/${hex.id}`} className="text-xs text-primary font-medium hover:underline flex-shrink-0 mt-1">
              Trang quẻ →
            </Link>
          </div>
          {hex.shortMeaning && (
            <p className="text-sm text-gray-700 dark:text-gray-200 mt-2 font-medium">{hex.shortMeaning}</p>
          )}
          <div className="mt-3 flex flex-col gap-2">
            {MEANING_FIELDS.map(([key, label]) =>
              hex[key] ? (
                <div key={key} className="text-sm">
                  <span className="font-semibold text-gray-600 dark:text-gray-300">{label}: </span>
                  <span className="text-gray-700 dark:text-gray-200">{hex[key]}</span>
                </div>
              ) : null
            )}
          </div>
        </div>
      )}

      {/* ===== Nguyên văn sách (Ngô Tất Tố) của đúng quẻ đó ===== */}
      {hexInfo && (
        <div className="mb-4">
          <div className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">
            📖 Nguyên văn sách {hexInfo.chunks.length ? `(${hexInfo.chunks.length} đoạn)` : ''}
          </div>
          {hexInfo.chunks.length === 0 ? (
            <div className="text-sm text-gray-400">Chưa có nguyên văn cho quẻ này.</div>
          ) : (
            <div className="flex flex-col gap-1.5">
              {hexInfo.chunks.map((c, i) => {
                const open = openBook[i]
                return (
                  <div key={c.chunk_id ?? i} className="card p-0 overflow-hidden">
                    <button
                      onClick={() => setOpenBook((e) => ({ ...e, [i]: !e[i] }))}
                      className="w-full text-left px-3 py-2 flex items-center justify-between gap-2 hover:bg-gray-50 dark:hover:bg-dark-border/50 transition-colors"
                    >
                      <span className="text-sm font-medium text-gray-800 dark:text-gray-100">{c.title}</span>
                      <span className="text-gray-400 text-xs flex-shrink-0">{open ? '▲' : '▼'}</span>
                    </button>
                    {open && (
                      <div className="px-3 pb-3 text-sm text-gray-700 dark:text-gray-200 whitespace-pre-wrap border-t border-gray-100 dark:border-dark-border pt-2">
                        {c.summary && <p className="italic text-gray-500 dark:text-gray-400 mb-1.5">{c.summary}</p>}
                        {c.content}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* ===== Kết quả semantic ===== */}
      {results && results.length > 0 && (
        <div className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">
          🔎 Liên quan theo ý nghĩa
        </div>
      )}
      {results && results.length === 0 && !hexInfo && !loading && (
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
