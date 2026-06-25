import { useEffect, useMemo, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useStore } from '../store'
import { getMe } from '../api'
import { lunarTodayText } from '../data/amlich'

let _cache = null
function loadVK() {
  if (!_cache) _cache = fetch('/data/van-khan.json').then((r) => r.json()).catch(() => [])
  return _cache
}

// Thay {{ten}} {{diaChi}} {{ngayAm}} bằng giá trị (in đậm) hoặc dấu chấm nếu trống
function renderFilled(text, vals) {
  const re = /\{\{(ten|diaChi|ngayAm)\}\}/g
  const out = []
  let last = 0, m, i = 0
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index))
    const v = (vals[m[1]] || '').trim()
    out.push(v
      ? <strong key={i++} className="text-primary">{v}</strong>
      : <span key={i++} className="text-gray-400">………………</span>)
    last = m.index + m[0].length
  }
  if (last < text.length) out.push(text.slice(last))
  return out
}

function Detail({ item, all }) {
  const navigate = useNavigate()
  const { user, openLogin } = useStore()
  const [me, setMe] = useState(null)
  const ngayAm = useMemo(() => lunarTodayText(), [])

  useEffect(() => {
    if (user) getMe().then(setMe).catch(() => {})
    else setMe(null)
  }, [user])

  const vals = { ten: me?.fullName || '', diaChi: me?.address || '', ngayAm }
  const filledInfo = me?.fullName || me?.address

  const idx = all.findIndex((x) => x.slug === item.slug)
  const prev = all[idx - 1], next = all[idx + 1]

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 animate-fade-in">
      <button onClick={() => navigate('/van-khan')} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-sm mb-4">← Tất cả văn khấn</button>
      <h1 className="font-display font-bold text-2xl text-gray-900 dark:text-gray-100 mb-2">{item.title}</h1>

      {/* Trạng thái tự điền */}
      <div className="text-xs rounded-lg px-3 py-2 mb-4 bg-primary/5 dark:bg-primary/10 text-gray-600 dark:text-gray-300">
        📅 Ngày khấn tự điền: <b className="text-primary">{ngayAm}</b>.{' '}
        {user
          ? (filledInfo
            ? <>Tên & địa chỉ lấy từ hồ sơ của bạn.</>
            : <>Chưa có tên/địa chỉ — <Link to="/profile" className="text-primary underline">điền hồ sơ</Link> để tự điền.</>)
          : <>Bạn <button onClick={openLogin} className="text-primary underline">đăng nhập</button> & điền hồ sơ để tự điền tên, địa chỉ.</>}
      </div>

      <div className="card p-5 space-y-2.5">
        {item.blocks.map((b, i) => b.tag === 'h3'
          ? <h3 key={i} className="font-semibold text-primary mt-4 mb-1">{b.text}</h3>
          : <p key={i} className="text-[15px] leading-relaxed text-gray-700 dark:text-gray-200">{renderFilled(b.text, vals)}</p>
        )}
        <p className="text-xs text-gray-400 pt-3 mt-2 border-t border-gray-100 dark:border-dark-border">
          Nguồn: izumi.edu.vn — lưu offline để tham khảo.
        </p>
      </div>

      <div className="flex justify-between gap-3 mt-5">
        {prev ? <Link to={`/van-khan/${prev.slug}`} className="btn-secondary flex-1 text-center text-sm truncate">← {prev.title}</Link> : <span className="flex-1" />}
        {next ? <Link to={`/van-khan/${next.slug}`} className="btn-secondary flex-1 text-center text-sm truncate">{next.title} →</Link> : <span className="flex-1" />}
      </div>
    </div>
  )
}

export default function VanKhanPage() {
  const { slug } = useParams()
  const [data, setData] = useState(null)
  const [kw, setKw] = useState('')

  useEffect(() => { loadVK().then(setData) }, [])

  const filtered = useMemo(() => {
    if (!data) return []
    const k = kw.trim().toLowerCase()
    return k ? data.filter((x) => x.title.toLowerCase().includes(k)) : data
  }, [data, kw])

  if (!data) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 flex justify-center">
        <div className="w-10 h-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
      </div>
    )
  }

  if (slug) {
    const item = data.find((x) => x.slug === slug)
    if (!item) return <div className="max-w-xl mx-auto px-4 py-16 text-center text-gray-400">Không thấy bài. <Link to="/van-khan" className="text-primary underline">Về danh sách</Link></div>
    return <Detail item={item} all={data} />
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="mb-4">
        <h1 className="font-display font-bold text-xl text-gray-900 dark:text-gray-100">🙏 Văn khấn ở đền</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{data.length} bài — tự điền tên, địa chỉ (từ hồ sơ) và ngày âm hôm nay.</p>
      </div>

      <input
        value={kw}
        onChange={(e) => setKw(e.target.value)}
        placeholder="Tìm theo tên bài khấn…"
        className="w-full mb-4 rounded-xl border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary/40"
      />

      <div className="space-y-2">
        {filtered.map((x) => (
          <Link key={x.slug} to={`/van-khan/${x.slug}`} className="card p-3.5 flex items-center gap-3 hover:border-primary/50 hover:shadow-md transition-all">
            <span className="text-2xl flex-shrink-0">🙏</span>
            <span className="font-semibold text-sm text-gray-900 dark:text-gray-100">{x.title}</span>
            <span className="ml-auto text-gray-300">›</span>
          </Link>
        ))}
        {filtered.length === 0 && <p className="text-sm text-gray-400 text-center py-6">Không tìm thấy bài khấn nào.</p>}
      </div>
    </div>
  )
}
