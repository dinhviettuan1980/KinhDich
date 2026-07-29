import { useState } from 'react'
import { createPortal } from 'react-dom'
import { useStore } from '../store'
import { linkFirebaseAccount } from '../api'

/**
 * Liên kết tài khoản Kinh Dịch cũ (username/password) với phiên đăng nhập Firebase đang
 * có (hệ sinh thái tuandv.id.vn). Bắt buộc nhập đúng mật khẩu cũ để chứng minh cùng một
 * người — xem .claude/plans/virtual-sparking-beaver.md.
 */
export default function LinkAccountModal({ onClose }) {
  const { adoptLinkedAccount, dismissFirebaseLink } = useStore()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    const u = username.trim()
    if (!u || !password) return setError('Nhập tên đăng nhập và mật khẩu tài khoản Kinh Dịch cũ')
    setBusy(true)
    try {
      await linkFirebaseAccount(u, password)
      await adoptLinkedAccount()
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-sm card p-6 z-10 max-h-[90vh] overflow-y-auto animate-fade-in">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-lg font-display font-bold text-gray-900 dark:text-gray-100">Liên kết tài khoản cũ</h2>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-dark-card text-gray-500 text-xl leading-none">×</button>
        </div>
        <p className="text-xs text-gray-400 dark:text-gray-500 mb-5">
          Nhập tên đăng nhập/mật khẩu Kinh Dịch cũ để giữ lại tiến độ học đã lưu trước đây.
        </p>

        <form onSubmit={submit} className="space-y-2">
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Tên đăng nhập cũ"
            autoComplete="username"
            className="w-full px-3 py-2.5 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm text-gray-900 dark:text-gray-100 outline-none focus:border-primary"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Mật khẩu cũ"
            autoComplete="current-password"
            className="w-full px-3 py-2.5 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm text-gray-900 dark:text-gray-100 outline-none focus:border-primary"
          />
          {error && <p className="text-xs text-red-500">{error}</p>}
          <button type="submit" disabled={busy} className="btn-primary w-full disabled:opacity-60">
            {busy ? 'Đang liên kết...' : 'Liên kết tài khoản'}
          </button>
        </form>

        <button
          onClick={() => { dismissFirebaseLink(); onClose() }}
          className="w-full text-center text-xs text-gray-400 mt-3 hover:underline"
        >
          Bỏ qua, dùng tài khoản mới
        </button>
      </div>
    </div>,
    document.body
  )
}
