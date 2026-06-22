import { useEffect, useState } from 'react'
import { fetchTodayObservation, fetchObservations, saveObservation } from '../api'

const FIELDS = [
  { key: 'growing', icon: '🌱', label: 'Điều gì đang tăng trưởng?', hint: 'Cái gì trong đời bạn đang lớn mạnh, đi lên?' },
  { key: 'declining', icon: '🍂', label: 'Điều gì đang suy giảm?', hint: 'Cái gì đang yếu đi, lùi lại?' },
  { key: 'transforming', icon: '🔄', label: 'Điều gì đang chuyển hóa?', hint: 'Cái gì đang biến từ trạng thái này sang trạng thái khác?' },
]

export default function ObservePage() {
  const [form, setForm] = useState({ growing: '', declining: '', transforming: '' })
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const load = () => {
    Promise.all([fetchTodayObservation(), fetchObservations()])
      .then(([today, all]) => {
        setForm({ growing: today.growing || '', declining: today.declining || '', transforming: today.transforming || '' })
        setHistory(all)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const save = async () => {
    setSaving(true)
    try { await saveObservation(form); setSaved(true); fetchObservations().then(setHistory).catch(() => {}) }
    catch { /* noop */ } finally { setSaving(false) }
  }

  const today = new Date().toLocaleDateString('en-CA')
  const past = history.filter((h) => h.observeDate !== today)
  const fmt = (d) => { try { return new Date(d).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' }) } catch { return d } }

  if (loading) {
    return <div className="max-w-2xl mx-auto px-4 py-16 flex justify-center"><div className="w-9 h-9 rounded-full border-4 border-primary border-t-transparent animate-spin" /></div>
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      <div>
        <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-gray-100">👁️ Quan sát hôm nay</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Kinh Dịch là quan sát sự biến đổi. Mỗi ngày ghi lại ba dòng chảy quanh bạn.
        </p>
      </div>

      <div className="space-y-4">
        {FIELDS.map((f) => (
          <div key={f.key} className="card p-5">
            <label className="block">
              <span className="text-sm font-semibold text-gray-800 dark:text-gray-100">{f.icon} {f.label}</span>
              <span className="block text-xs text-gray-400 dark:text-gray-500 mb-2">{f.hint}</span>
              <textarea
                value={form[f.key]}
                onChange={(e) => { setForm((s) => ({ ...s, [f.key]: e.target.value })); setSaved(false) }}
                rows={2}
                className="w-full px-3 py-2.5 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm text-gray-900 dark:text-gray-100 outline-none focus:border-primary resize-none"
              />
            </label>
          </div>
        ))}
        <div className="flex items-center gap-3">
          <button onClick={save} disabled={saving} className="btn-primary disabled:opacity-60">
            {saving ? 'Đang lưu...' : 'Lưu quan sát hôm nay'}
          </button>
          {saved && <span className="text-sm text-emerald-600 dark:text-emerald-400">✓ Đã lưu</span>}
        </div>
      </div>

      {past.length > 0 && (
        <div className="pt-2">
          <h2 className="text-sm font-bold text-gray-700 dark:text-gray-200 mb-3">Những ngày trước</h2>
          <div className="space-y-2">
            {past.map((h) => (
              <div key={h.observeDate} className="card p-4">
                <div className="text-xs font-bold text-gray-400 mb-2">{fmt(h.observeDate)}</div>
                <div className="space-y-1 text-sm">
                  {h.growing && <p className="text-gray-700 dark:text-gray-300">🌱 {h.growing}</p>}
                  {h.declining && <p className="text-gray-700 dark:text-gray-300">🍂 {h.declining}</p>}
                  {h.transforming && <p className="text-gray-700 dark:text-gray-300">🔄 {h.transforming}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
