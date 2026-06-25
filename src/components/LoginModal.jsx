import { useState } from 'react'
import { createPortal } from 'react-dom'
import { useStore } from '../store'
import { registerUser, loginUser } from '../api'

export default function LoginModal({ onClose }) {
  const { login } = useStore()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submitUser = async (e) => {
    e.preventDefault()
    setError('')
    const u = username.trim()
    if (!u || !password) return setError('Nhập tên đăng nhập và mật khẩu')
    setBusy(true)
    try {
      const data = mode === 'register'
        ? await registerUser(u, password)
        : await loginUser(u, password)
      if (data.token) localStorage.setItem('kd_token', data.token)
      await login({
        provider: 'user',
        uid: `user:${data.username}`,
        username: data.username,
        name: (data.fullName && data.fullName.trim()) || data.username,
        fullName: data.fullName || null,
        email: null,
        avatar: null,
        isAdmin: !!data.isAdmin,
      })
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
          <h2 className="text-lg font-display font-bold text-gray-900 dark:text-gray-100">Đăng nhập</h2>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-dark-card text-gray-500 text-xl leading-none">×</button>
        </div>
        <p className="text-xs text-gray-400 dark:text-gray-500 mb-5">Để lưu tiến độ học theo tài khoản của bạn.</p>

        <form onSubmit={submitUser} className="space-y-2">
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Tên đăng nhập"
            autoComplete="username"
            className="w-full px-3 py-2.5 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm text-gray-900 dark:text-gray-100 outline-none focus:border-primary"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Mật khẩu"
            autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
            className="w-full px-3 py-2.5 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm text-gray-900 dark:text-gray-100 outline-none focus:border-primary"
          />
          {error && <p className="text-xs text-red-500">{error}</p>}
          <button type="submit" disabled={busy} className="btn-primary w-full disabled:opacity-60">
            {busy ? 'Đang xử lý...' : mode === 'register' ? 'Đăng ký & vào học' : 'Đăng nhập'}
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 mt-3">
          {mode === 'login' ? 'Chưa có tài khoản?' : 'Đã có tài khoản?'}{' '}
          <button
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}
            className="text-primary font-semibold hover:underline"
          >
            {mode === 'login' ? 'Đăng ký' : 'Đăng nhập'}
          </button>
        </p>
      </div>
    </div>,
    document.body
  )
}
