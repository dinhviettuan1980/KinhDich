import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import FullHexagramSVG from '../components/FullHexagramSVG'
import { getHexagramById } from '../data/hexagrams'
import { getUserId } from '../api'

function timeAgo(dateStr) {
  const d = new Date(dateStr)
  const diff = Date.now() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 2) return 'vừa xong'
  if (mins < 60) return `${mins} phút trước`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} giờ trước`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days} ngày trước`
  return d.toLocaleDateString('vi-VN')
}

function CastingCard({ item, onDeleted, onNoteUpdated }) {
  const [editing, setEditing] = useState(false)
  const [note, setNote] = useState(item.note || '')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const orig = getHexagramById(item.original_hexagram)
  const changed = item.changed_hexagram ? getHexagramById(item.changed_hexagram) : null
  const lines = item.lines_data ? JSON.parse(item.lines_data) : null
  const movingLines = item.moving_lines ? JSON.parse(item.moving_lines) : []
  const changedLines = lines ? lines.map(v => v === 9 ? 8 : v === 6 ? 7 : v) : null

  async function saveNote() {
    setSaving(true)
    try {
      await fetch(`/kinhdich/castings/${item.id}/note`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note }),
      })
      onNoteUpdated(item.id, note)
      setEditing(false)
    } catch (e) { console.error(e) } finally { setSaving(false) }
  }

  async function handleDelete() {
    if (!confirm('Xóa quẻ này khỏi lịch sử?')) return
    setDeleting(true)
    try {
      await fetch(`/kinhdich/castings/${item.id}`, { method: 'DELETE' })
      onDeleted(item.id)
    } catch (e) { console.error(e) } finally { setDeleting(false) }
  }

  return (
    <div className="card p-4 space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {lines && (
            <div className="flex-shrink-0">
              <FullHexagramSVG lines={lines} movingLines={movingLines} size={0.7} />
            </div>
          )}
          <div className="min-w-0">
            <div className="font-semibold text-gray-800 dark:text-gray-100 text-sm truncate">
              {orig.id}. {orig.name}
              {changed && <span className="text-amber-500 dark:text-amber-400"> → {changed.id}. {changed.name}</span>}
            </div>
            {movingLines.length > 0 && (
              <div className="text-xs text-amber-500 dark:text-amber-400">
                Hào động: {movingLines.map(n => `H${n}`).join(', ')}
              </div>
            )}
            <div className="text-xs text-gray-400 mt-0.5">{timeAgo(item.created_at)}</div>
          </div>
        </div>
        <button
          onClick={() => setExpanded(e => !e)}
          className="text-xs text-gray-400 hover:text-primary flex-shrink-0 mt-1"
        >
          {expanded ? '▲ Thu gọn' : '▼ Chi tiết'}
        </button>
      </div>

      {/* Question */}
      {item.question && (
        <div className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-dark-card rounded-lg px-2.5 py-2">
          Chủ đề: <em>"{item.question}"</em>
        </div>
      )}

      {/* Expanded detail */}
      {expanded && (
        <div className="space-y-3 pt-1">
          {/* Side by side if changed */}
          {lines && changed && changedLines && (
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col items-center gap-1">
                <div className="text-xs text-gray-400">Quẻ chính</div>
                <FullHexagramSVG lines={lines} movingLines={movingLines} size={1.2} />
                <div className="text-xs font-medium text-gray-700 dark:text-gray-300">{orig.name}</div>
              </div>
              <div className="flex flex-col items-center gap-1">
                <div className="text-xs text-amber-500">Quẻ biến</div>
                <FullHexagramSVG lines={changedLines} movingLines={[]} size={1.2} />
                <div className="text-xs font-medium text-gray-700 dark:text-gray-300">{changed.name}</div>
              </div>
            </div>
          )}

          {/* Meaning */}
          <div className="text-xs text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-dark-card rounded-lg p-3">
            <div className="font-semibold text-gray-700 dark:text-gray-200 mb-1">{orig.name}</div>
            {orig.shortMeaning}
          </div>
        </div>
      )}

      {/* Note */}
      {editing ? (
        <div className="space-y-2">
          <textarea
            value={note}
            onChange={e => setNote(e.target.value)}
            className="w-full rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-gray-800 dark:text-gray-100 p-2.5 text-xs resize-none h-20 focus:outline-none focus:ring-2 focus:ring-primary"
            maxLength={500}
            autoFocus
          />
          <div className="flex gap-2">
            <button onClick={() => setEditing(false)} className="flex-1 py-1.5 rounded-lg border border-gray-200 dark:border-dark-border text-gray-500 text-xs hover:bg-gray-50 dark:hover:bg-dark-card">
              Hủy
            </button>
            <button onClick={saveNote} disabled={saving} className="flex-1 py-1.5 rounded-lg bg-primary text-white text-xs font-medium hover:bg-primary-light disabled:opacity-50">
              {saving ? 'Đang lưu…' : 'Lưu ghi chú'}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex items-start gap-2">
          <div className="flex-1 text-xs text-gray-600 dark:text-gray-300 italic">
            {note ? `"${note}"` : <span className="text-gray-400">Chưa có ghi chú</span>}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <button onClick={() => setEditing(true)} className="text-xs text-primary hover:underline">
              {note ? 'Sửa' : 'Ghi chú'}
            </button>
            <button onClick={handleDelete} disabled={deleting} className="text-xs text-red-400 hover:text-red-600 disabled:opacity-50">
              {deleting ? '…' : 'Xóa'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function CastingHistoryPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const userId = getUserId()
    fetch(`/kinhdich/castings/${userId}`)
      .then(r => r.json())
      .then(data => setItems(data.castings || []))
      .catch(e => setError('Không thể tải lịch sử'))
      .finally(() => setLoading(false))
  }, [])

  function handleDeleted(id) {
    setItems(prev => prev.filter(i => i.id !== id))
  }

  function handleNoteUpdated(id, note) {
    setItems(prev => prev.map(i => i.id === id ? { ...i, note } : i))
  }

  if (loading) return (
    <div className="flex justify-center py-20">
      <div className="w-10 h-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
    </div>
  )

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-gray-100">Lịch sử Gieo Quẻ</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            {items.length > 0 ? `${items.length} lần gieo quẻ` : 'Chưa có lịch sử'}
          </p>
        </div>
        <button
          onClick={() => navigate('/casting')}
          className="px-4 py-2 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-primary-light transition-colors"
        >
          + Gieo quẻ mới
        </button>
      </div>

      {error && (
        <div className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 rounded-lg px-4 py-3">{error}</div>
      )}

      {items.length === 0 && !error && (
        <div className="text-center py-16 space-y-4">
          <div className="text-5xl">☯</div>
          <p className="text-gray-500 dark:text-gray-400 text-sm">Bạn chưa gieo quẻ lần nào.</p>
          <button onClick={() => navigate('/casting')} className="px-6 py-2.5 rounded-xl bg-primary text-white font-semibold text-sm hover:bg-primary-light transition-colors">
            Bắt đầu gieo quẻ
          </button>
        </div>
      )}

      <div className="space-y-4">
        {items.map(item => (
          <CastingCard
            key={item.id}
            item={item}
            onDeleted={handleDeleted}
            onNoteUpdated={handleNoteUpdated}
          />
        ))}
      </div>
    </div>
  )
}
