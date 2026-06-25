import { useEffect, useMemo, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'

// Tải 1 lần, cache ở module để chuyển trang không fetch lại
let _cache = null
function loadQue() {
  if (!_cache) _cache = fetch('/data/que.json').then((r) => r.json()).catch(() => [])
  return _cache
}
// Ký tự Unicode quẻ Kinh Dịch (theo thứ tự Văn Vương): ䷀ = quẻ 1 … ䷿ = quẻ 64
const glyph = (so) => String.fromCodePoint(0x4dc0 + (so - 1))

function Block({ b }) {
  if (b.tag === 'h2')
    return <h2 className="font-display font-bold text-lg text-gray-900 dark:text-gray-100 mt-7 mb-2 pb-1.5 border-b border-gray-200 dark:border-dark-border">{b.text}</h2>
  if (b.tag === 'h3')
    return <h3 className="font-semibold text-primary mt-4 mb-1.5">{b.text}</h3>
  if (b.tag === 'ul')
    return <ul className="list-disc pl-5 space-y-1 text-gray-700 dark:text-gray-300 text-[15px] my-2">{b.items.map((it, i) => <li key={i}>{it}</li>)}</ul>
  if (b.tag === 'table')
    return (
      <div className="overflow-x-auto my-2">
        <table className="text-sm border-collapse">
          <tbody>
            {b.rows.map((r, i) => (
              <tr key={i} className={i === 0 ? 'font-semibold text-gray-500 dark:text-gray-400' : ''}>
                {r.map((c, j) => <td key={j} className="border border-gray-200 dark:border-dark-border px-2.5 py-1">{c}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )

  const t = b.text || ''
  // Ghi chú nguồn thiếu
  if (/^⚠️/.test(t))
    return <p className="text-sm bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 rounded-lg px-3 py-2 my-2">{t}</p>
  // Tên hào: "1. Sơ Cửu (Hào 1 dương):"
  if (/^\d+\.\s.+\(Hào|^\d+\.\s.+\(Cả 6 hào/.test(t))
    return <p className="font-semibold text-gray-900 dark:text-gray-100 mt-3">{t}</p>
  // Lời kinh / Dịch âm / Dịch nghĩa / Giảng nghĩa
  const m = t.match(/^(Lời kinh|Dịch âm|Dịch nghĩa|Giảng nghĩa):\s*([\s\S]*)$/)
  if (m) {
    const [, label, rest] = m
    const han = label === 'Lời kinh'
    return (
      <p className="my-1.5 text-[15px] leading-relaxed">
        <span className="text-xs font-bold uppercase tracking-wide text-gray-400 mr-1.5">{label}</span>
        <span className={han ? 'text-lg text-primary font-medium' : 'text-gray-700 dark:text-gray-300'}>{rest}</span>
      </p>
    )
  }
  return <p className="my-1.5 text-[15px] leading-relaxed text-gray-700 dark:text-gray-300">{t}</p>
}

function Detail({ item, all }) {
  const navigate = useNavigate()
  const prev = all.find((x) => x.so === item.so - 1)
  const next = all.find((x) => x.so === item.so + 1)
  return (
    <div className="max-w-2xl mx-auto px-4 py-6 animate-fade-in">
      <button onClick={() => navigate('/que')} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-sm mb-4">← Tất cả 64 quẻ</button>

      <div className="flex items-center gap-4 mb-5">
        <div className="text-5xl text-primary leading-none">{glyph(item.so)}</div>
        <div>
          <div className="text-xs text-gray-400">Quẻ số {item.so}</div>
          <h1 className="font-display font-bold text-2xl text-gray-900 dark:text-gray-100">{item.ten}</h1>
          {item.trieu && <div className="text-sm text-accent font-medium mt-0.5">{item.trieu}</div>}
        </div>
      </div>

      <div className="card p-5">
        {item.blocks.map((b, i) => <Block key={i} b={b} />)}
        <p className="text-xs text-gray-400 mt-6 pt-3 border-t border-gray-100 dark:border-dark-border">
          Nguồn: <a href={item.url} target="_blank" rel="noreferrer" className="underline hover:text-primary">kabala.vn</a>
          {item.nguon ? ` · ${item.nguon}` : ''} — lưu offline để học cá nhân.
        </p>
      </div>

      <div className="flex justify-between gap-3 mt-5">
        {prev
          ? <Link to={`/que/${prev.so}`} className="btn-secondary flex-1 text-center text-sm">← {prev.so}. {prev.ten}</Link>
          : <span className="flex-1" />}
        {next
          ? <Link to={`/que/${next.so}`} className="btn-secondary flex-1 text-center text-sm">{next.so}. {next.ten} →</Link>
          : <span className="flex-1" />}
      </div>
    </div>
  )
}

export default function QuePage() {
  const { so } = useParams()
  const [data, setData] = useState(null)
  const [kw, setKw] = useState('')

  useEffect(() => { loadQue().then(setData) }, [])

  const filtered = useMemo(() => {
    if (!data) return []
    const k = kw.trim().toLowerCase()
    if (!k) return data
    return data.filter((x) => x.ten.toLowerCase().includes(k) || (x.trieu || '').toLowerCase().includes(k) || String(x.so) === k)
  }, [data, kw])

  if (!data)
    return (
      <div className="max-w-xl mx-auto px-4 py-16 flex justify-center">
        <div className="w-10 h-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
      </div>
    )

  if (so) {
    const item = data.find((x) => String(x.so) === String(so))
    if (!item)
      return <div className="max-w-xl mx-auto px-4 py-16 text-center text-gray-400">Không thấy quẻ. <Link to="/que" className="text-primary underline">Về danh sách</Link></div>
    return <Detail item={item} all={data} />
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <div className="mb-4">
        <h1 className="font-display font-bold text-xl text-gray-900 dark:text-gray-100">📖 64 Quẻ Kinh Dịch</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Tra cứu chi tiết từng quẻ: thoán từ, tượng, các hào, ý nghĩa chiêm bốc.</p>
      </div>

      <input
        value={kw}
        onChange={(e) => setKw(e.target.value)}
        placeholder="Tìm theo tên hoặc số quẻ…"
        className="w-full mb-4 rounded-xl border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
      />

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5">
        {filtered.map((x) => (
          <Link
            key={x.so}
            to={`/que/${x.so}`}
            className="card p-3 flex items-center gap-3 hover:border-primary/50 hover:shadow-md transition-all"
          >
            <span className="text-3xl text-primary leading-none flex-shrink-0">{glyph(x.so)}</span>
            <span className="min-w-0">
              <span className="block text-xs text-gray-400">Quẻ {x.so}</span>
              <span className="block font-semibold text-sm text-gray-900 dark:text-gray-100 truncate">{x.ten}</span>
              {x.trieu && <span className="block text-[11px] text-accent truncate">{x.trieu}</span>}
            </span>
          </Link>
        ))}
      </div>
      {filtered.length === 0 && <p className="text-sm text-gray-400 mt-6 text-center">Không tìm thấy quẻ nào.</p>}
    </div>
  )
}
