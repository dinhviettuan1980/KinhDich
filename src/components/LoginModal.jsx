import { useState } from 'react'
import { createPortal } from 'react-dom'
import { GoogleLogin } from '@react-oauth/google'
import { useStore } from '../store'
import { registerUser, loginUser } from '../api'

function decodeJwt(t) {
  try { return JSON.parse(atob(t.split('.')[1])) } catch { return null }
}

// FB App ID lấy từ env (chưa có ở dự án này); thiếu thì nút FB chỉ báo hướng dẫn.
const FB_APP_ID = import.meta.env.VITE_FB_APP_ID
function loadFbSdk(appId) {
  return new Promise((resolve) => {
    if (window.FB) return resolve(window.FB)
    window.fbAsyncInit = function () {
      window.FB.init({ appId, cookie: true, xfbml: false, version: 'v19.0' })
      resolve(window.FB)
    }
    const s = document.createElement('script')
    s.src = 'https://connect.facebook.net/en_US/sdk.js'
    s.async = true; s.defer = true
    document.body.appendChild(s)
  })
}

export default function LoginModal({ onClose }) {
  const { login } = useStore()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const onGoogle = (resp) => {
    const p = decodeJwt(resp.credential)
    if (!p) return alert('Không đọc được thông tin Google')
    login({ provider: 'google', uid: `google:${p.email || p.sub}`, name: p.name, email: p.email, avatar: p.picture })
    onClose()
  }

  const onFacebook = () => {
    if (!FB_APP_ID) {
      alert('Facebook chưa cấu hình App ID.\nThêm VITE_FB_APP_ID vào .env rồi build lại để bật đăng nhập Facebook.')
      return
    }
    loadFbSdk(FB_APP_ID).then((FB) => {
      FB.login((res) => {
        if (!res.authResponse) return
        FB.api('/me', { fields: 'name,email,picture' }, (me) => {
          login({ provider: 'facebook', uid: `fb:${me.id}`, name: me.name, email: me.email || null, avatar: me.picture?.data?.url })
          onClose()
        })
      }, { scope: 'public_profile,email' })
    })
  }

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
      await login({
        provider: 'user',
        uid: `user:${data.username}`,
        name: data.username,
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

        {/* Google */}
        <div className="flex justify-center mb-3">
          <GoogleLogin onSuccess={onGoogle} onError={() => alert('Đăng nhập Google thất bại')} width="300" />
        </div>

        {/* Facebook */}
        <button
          onClick={onFacebook}
          className="w-full flex items-center justify-center gap-2 bg-[#1877F2] hover:bg-[#166fe0] text-white rounded-lg py-2.5 text-sm font-semibold transition-colors mb-4"
        >
          <span className="text-lg">f</span> Tiếp tục với Facebook
        </button>

        {/* Divider */}
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 h-px bg-gray-200 dark:bg-dark-border" />
          <span className="text-xs text-gray-400">hoặc</span>
          <div className="flex-1 h-px bg-gray-200 dark:bg-dark-border" />
        </div>

        {/* Username/password (đăng ký + đăng nhập thật) */}
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
