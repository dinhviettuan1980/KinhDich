import { useEffect, useMemo, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useStore } from '../store'
import { getMe, fetchVanKhanList, addVanKhanUrl, addVanKhanText, updateVanKhanText, deleteVanKhan } from '../api'
import { lunarTodayText } from '../data/amlich'

const inputCls = 'w-full px-3 py-2.5 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm text-gray-900 dark:text-gray-100 outline-none focus:border-primary'

function renderFilled(text, vals) {
  const re = /\{\{(ten|diaChi|ngayAm)\}\}/g
  const out = []
  let last = 0, m, i = 0
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index))
    const v = (vals[m[1]] || '').trim()
    out.push(v ? <strong key={i++} className="text-primary">{v}</strong> : <span key={i++} className="text-gray-400">………………</span>)
    last = m.index + m[0].length
  }
  if (last < text.length) out.push(text.slice(last))
  return out
}

// Dựng lại text để sửa (thay token bằng chỗ trống dễ đọc; backend sẽ token hoá lại khi lưu)
function blocksToText(blocks) {
  return blocks.map((b) => b.text
    .replace('{{ten}}', '[Họ và tên]')
    .replace('{{diaChi}}', '[Địa chỉ]')
    .replace('Hôm nay là {{ngayAm}}.', 'Hôm nay là ngày... tháng... năm...')).join('\n')
}

function VanKhanForm({ editItem, onClose, onSaved }) {
  const isEdit = !!editItem
  const [tab, setTab] = useState('url') // add: 'url' | 'text'
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState(editItem ? editItem.title : '')
  const [text, setText] = useState(editItem ? blocksToText(editItem.blocks) : '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault(); setError(''); setBusy(true)
    try {
      let r
      if (isEdit) r = await updateVanKhanText(editItem.id, { title, text })
      else if (tab === 'url') r = await addVanKhanUrl(url)
      else r = await addVanKhanText({ title, text })
      onSaved(r)
    } catch (err) { setError(err.message) } finally { setBusy(false) }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <form onSubmit={submit} className="relative w-full max-w-lg card p-6 z-10 max-h-[90vh] overflow-y-auto space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-display font-bold text-gray-900 dark:text-gray-100">{isEdit ? 'Sửa bài khấn' : 'Thêm bài khấn'}</h2>
          <button type="button" onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-dark-card text-gray-500 text-xl">×</button>
        </div>

        {!isEdit && (
          <div className="flex gap-2">
            <button type="button" onClick={() => setTab('url')} className={`px-3 py-1.5 rounded-lg text-sm font-medium ${tab === 'url' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-dark-card text-gray-600'}`}>Từ URL</button>
            <button type="button" onClick={() => setTab('text')} className={`px-3 py-1.5 rounded-lg text-sm font-medium ${tab === 'text' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-dark-card text-gray-600'}`}>Dán nội dung</button>
          </div>
        )}

        {!isEdit && tab === 'url' ? (
          <div>
            <label className="block text-xs text-gray-500 mb-1">URL trang văn khấn</label>
            <input className={inputCls} value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://..." />
            <p className="text-[11px] text-gray-400 mt-1">Server sẽ tải, tách nội dung & tự nhận chỗ điền tên/địa chỉ/ngày. Nếu trùng sẽ báo.</p>
          </div>
        ) : (
          <>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Tiêu đề</label>
              <input className={inputCls} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="VD: Văn khấn Thần Tài" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Nội dung (mỗi dòng 1 đoạn)</label>
              <textarea className={`${inputCls} font-mono`} rows={12} value={text} onChange={(e) => setText(e.target.value)}
                placeholder={'Nam mô A Di Đà Phật!\nTín chủ con là: [Họ và tên]\nNgụ tại: [Địa chỉ]\nHôm nay là ngày... tháng... năm...\n...'} />
              <p className="text-[11px] text-gray-400 mt-1">Tự nhận: dòng bắt đầu “Tín chủ con là:”, “Ngụ tại:”, “Hôm nay là ngày…” → thay bằng tên/địa chỉ/ngày âm.</p>
            </div>
          </>
        )}

        {error && <p className="text-sm text-red-500">{error}</p>}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-secondary">Hủy</button>
          <button type="submit" disabled={busy} className="btn-primary disabled:opacity-60">{busy ? 'Đang xử lý...' : (isEdit ? 'Lưu' : 'Thêm')}</button>
        </div>
      </form>
    </div>
  )
}

export default function VanKhanPage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { user, openLogin } = useStore()
  const [data, setData] = useState(null)
  const [kw, setKw] = useState('')
  const [me, setMe] = useState(null)
  const [adding, setAdding] = useState(false)
  const [editing, setEditing] = useState(null)
  const [speaking, setSpeaking] = useState(false)
  const ngayAm = useMemo(() => lunarTodayText(), [])

  const reload = () => fetchVanKhanList().then(setData).catch(() => setData([]))
  useEffect(() => { reload() }, [])
  useEffect(() => { if (user) getMe().then(setMe).catch(() => {}); else setMe(null) }, [user?.uid]) // eslint-disable-line
  // Nạp sẵn danh sách giọng + dừng đọc khi rời trang
  useEffect(() => { try { window.speechSynthesis.getVoices() } catch { /* noop */ } return () => { try { window.speechSynthesis.cancel() } catch { /* noop */ } } }, [])
  // Đổi bài thì dừng đọc
  useEffect(() => { try { window.speechSynthesis.cancel() } catch { /* noop */ } setSpeaking(false) }, [slug])

  if (!data) {
    return <div className="max-w-xl mx-auto px-4 py-16 flex justify-center"><div className="w-10 h-10 rounded-full border-4 border-primary border-t-transparent animate-spin" /></div>
  }

  const isAdmin = user?.isAdmin
  const vals = { ten: me?.fullName || '', diaChi: me?.address || '', ngayAm }

  const readAloud = (blocks) => {
    const synth = window.speechSynthesis
    if (!synth) return alert('Trình duyệt không hỗ trợ đọc (text-to-speech).')
    synth.cancel()
    const voice = synth.getVoices().find((v) => /vi[-_]?vn/i.test(v.lang) || /viet/i.test(v.name))
    const lines = blocks
      .map((b) => b.text
        .replace('{{ten}}', vals.ten || '')
        .replace('{{diaChi}}', vals.diaChi || '')
        .replace('Hôm nay là {{ngayAm}}.', `Hôm nay là ${vals.ngayAm}.`))
      .map((s) => s.trim()).filter(Boolean)
    setSpeaking(true)
    lines.forEach((line, i) => {
      const u = new SpeechSynthesisUtterance(line)
      u.lang = 'vi-VN'; if (voice) u.voice = voice; u.rate = 0.95
      if (i === lines.length - 1) u.onend = () => setSpeaking(false)
      synth.speak(u)
    })
  }
  const stopRead = () => { try { window.speechSynthesis.cancel() } catch { /* noop */ } setSpeaking(false) }

  const onDelete = async (item) => {
    if (!window.confirm(`Xóa bài "${item.title}"?`)) return
    try { await deleteVanKhan(item.id); await reload(); navigate('/van-khan') } catch (e) { alert(e.message) }
  }

  // ----- Chi tiết -----
  if (slug) {
    const item = data.find((x) => x.slug === slug)
    if (!item) return <div className="max-w-xl mx-auto px-4 py-16 text-center text-gray-400">Không thấy bài. <Link to="/van-khan" className="text-primary underline">Về danh sách</Link></div>
    const idx = data.findIndex((x) => x.slug === slug)
    const prev = data[idx - 1], next = data[idx + 1]
    const filledInfo = me?.fullName || me?.address
    return (
      <div className="max-w-2xl mx-auto px-4 py-6 animate-fade-in">
        <div className="flex items-center justify-between mb-4 gap-2">
          <button onClick={() => navigate('/van-khan')} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-sm flex-shrink-0">← Tất cả văn khấn</button>
          <div className="flex items-center gap-3">
            <button onClick={() => (speaking ? stopRead() : readAloud(item.blocks))}
              className={`text-xs font-semibold px-2.5 py-1 rounded-lg ${speaking ? 'bg-red-100 text-red-600 dark:bg-red-900/30' : 'bg-primary/10 text-primary hover:bg-primary/20'}`}>
              {speaking ? '⏸ Dừng đọc' : '🔊 Đọc'}
            </button>
            {isAdmin && <>
              <button onClick={() => setEditing(item)} className="text-xs text-blue-600 hover:underline">✏️ Sửa</button>
              <button onClick={() => onDelete(item)} className="text-xs text-red-500 hover:underline">🗑️ Xóa</button>
            </>}
          </div>
        </div>
        <h1 className="font-display font-bold text-2xl text-gray-900 dark:text-gray-100 mb-2">{item.title}</h1>
        <div className="text-xs rounded-lg px-3 py-2 mb-4 bg-primary/5 dark:bg-primary/10 text-gray-600 dark:text-gray-300">
          📅 Ngày khấn tự điền: <b className="text-primary">{ngayAm}</b>.{' '}
          {user ? (filledInfo ? <>Tên & địa chỉ lấy từ hồ sơ.</> : <>Chưa có tên/địa chỉ — <Link to="/profile" className="text-primary underline">điền hồ sơ</Link> để tự điền.</>)
            : <>Bạn <button onClick={openLogin} className="text-primary underline">đăng nhập</button> & điền hồ sơ để tự điền tên, địa chỉ.</>}
        </div>
        <div className="card p-5 space-y-2.5">
          {item.blocks.map((b, i) => b.tag === 'h3'
            ? <h3 key={i} className="font-semibold text-primary mt-4 mb-1">{b.text}</h3>
            : <p key={i} className="text-[15px] leading-relaxed text-gray-700 dark:text-gray-200">{renderFilled(b.text, vals)}</p>)}
          {item.source && <p className="text-xs text-gray-400 pt-3 mt-2 border-t border-gray-100 dark:border-dark-border">Nguồn: {item.source}</p>}
        </div>
        <div className="flex justify-between gap-3 mt-5">
          {prev ? <Link to={`/van-khan/${prev.slug}`} className="btn-secondary flex-1 text-center text-sm truncate">← {prev.title}</Link> : <span className="flex-1" />}
          {next ? <Link to={`/van-khan/${next.slug}`} className="btn-secondary flex-1 text-center text-sm truncate">{next.title} →</Link> : <span className="flex-1" />}
        </div>
        {editing && <VanKhanForm editItem={editing} onClose={() => setEditing(null)} onSaved={(r) => { setEditing(null); reload().then(() => { if (r.slug && r.slug !== slug) navigate(`/van-khan/${r.slug}`) }) }} />}
      </div>
    )
  }

  // ----- Danh sách -----
  const k = kw.trim().toLowerCase()
  const filtered = k ? data.filter((x) => x.title.toLowerCase().includes(k)) : data
  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-start justify-between gap-2 mb-4">
        <div>
          <h1 className="font-display font-bold text-xl text-gray-900 dark:text-gray-100">🙏 Văn khấn ở đền</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{data.length} bài — tự điền tên, địa chỉ (từ hồ sơ) và ngày âm hôm nay.</p>
        </div>
        {isAdmin && <button onClick={() => setAdding(true)} className="btn-primary text-sm px-3 py-1.5 flex-shrink-0">➕ Thêm bài</button>}
      </div>

      <input value={kw} onChange={(e) => setKw(e.target.value)} placeholder="Tìm theo tên bài khấn…"
        className="w-full mb-4 rounded-xl border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary/40" />

      <div className="space-y-2">
        {filtered.map((x) => (
          <div key={x.slug} className="card p-3.5 flex items-center gap-3 hover:border-primary/50 transition-all">
            <Link to={`/van-khan/${x.slug}`} className="flex items-center gap-3 flex-1 min-w-0">
              <span className="text-2xl flex-shrink-0">🙏</span>
              <span className="font-semibold text-sm text-gray-900 dark:text-gray-100 truncate">{x.title}</span>
            </Link>
            {isAdmin
              ? <div className="flex gap-2 flex-shrink-0">
                  <button onClick={() => setEditing(x)} className="text-xs text-blue-600 hover:underline">Sửa</button>
                  <button onClick={() => onDelete(x)} className="text-xs text-red-500 hover:underline">Xóa</button>
                </div>
              : <Link to={`/van-khan/${x.slug}`} className="text-gray-300 flex-shrink-0">›</Link>}
          </div>
        ))}
        {filtered.length === 0 && <p className="text-sm text-gray-400 text-center py-6">Không tìm thấy bài khấn nào.</p>}
      </div>

      {adding && <VanKhanForm onClose={() => setAdding(false)} onSaved={(r) => { setAdding(false); reload().then(() => r.slug && navigate(`/van-khan/${r.slug}`)) }} />}
      {editing && <VanKhanForm editItem={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); reload() }} />}
    </div>
  )
}
