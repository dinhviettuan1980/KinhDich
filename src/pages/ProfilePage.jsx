import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useStore } from '../store'
import { getMe, updateProfile, changePassword } from '../api'

const inputCls =
  'w-full px-3 py-2.5 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm text-gray-900 dark:text-gray-100 outline-none focus:border-primary'

export default function ProfilePage() {
  const navigate = useNavigate()
  const { user, openLogin, updateUser } = useStore()

  const [fullName, setFullName] = useState('')
  const [address, setAddress] = useState('')
  const [savingInfo, setSavingInfo] = useState(false)
  const [infoMsg, setInfoMsg] = useState({ ok: false, text: '' })

  const [oldPw, setOldPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [savingPw, setSavingPw] = useState(false)
  const [pwMsg, setPwMsg] = useState({ ok: false, text: '' })

  useEffect(() => {
    if (!user) return
    getMe()
      .then((d) => {
        setFullName(d.fullName || '')
        setAddress(d.address || '')
        updateUser({
          username: d.username,
          fullName: d.fullName || null,
          name: (d.fullName && d.fullName.trim()) || d.username,
          isAdmin: !!d.isAdmin,
        })
      })
      .catch(() => {})
  }, [user]) // eslint-disable-line

  if (!user) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center space-y-4">
        <div className="text-5xl">🔒</div>
        <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Cần đăng nhập</h2>
        <div className="flex gap-3 justify-center">
          <button onClick={() => navigate('/')} className="btn-secondary">← Trang chủ</button>
          <button onClick={openLogin} className="btn-primary">Đăng nhập</button>
        </div>
      </div>
    )
  }

  const username = user.username || user.name

  const saveInfo = async (e) => {
    e.preventDefault()
    setInfoMsg({ ok: false, text: '' })
    setSavingInfo(true)
    try {
      const d = await updateProfile({ fullName, address })
      updateUser({ fullName: d.fullName, name: (d.fullName && d.fullName.trim()) || username })
      setInfoMsg({ ok: true, text: 'Đã lưu ✓' })
    } catch (err) {
      setInfoMsg({ ok: false, text: err.message })
    } finally {
      setSavingInfo(false)
    }
  }

  const savePw = async (e) => {
    e.preventDefault()
    setPwMsg({ ok: false, text: '' })
    if (!oldPw) return setPwMsg({ ok: false, text: 'Nhập mật khẩu hiện tại' })
    if (newPw.length < 4) return setPwMsg({ ok: false, text: 'Mật khẩu mới tối thiểu 4 ký tự' })
    if (newPw !== confirmPw) return setPwMsg({ ok: false, text: 'Xác nhận mật khẩu không khớp' })
    setSavingPw(true)
    try {
      await changePassword(oldPw, newPw)
      setPwMsg({ ok: true, text: 'Đổi mật khẩu thành công ✓' })
      setOldPw(''); setNewPw(''); setConfirmPw('')
    } catch (err) {
      setPwMsg({ ok: false, text: err.message })
    } finally {
      setSavingPw(false)
    }
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-6 space-y-5">
      <div className="flex items-center gap-3">
        <span className="w-12 h-12 rounded-full bg-primary/15 text-primary flex items-center justify-center text-xl font-bold">
          {(user.name || '?').charAt(0).toUpperCase()}
        </span>
        <div>
          <h1 className="font-display font-bold text-xl text-gray-900 dark:text-gray-100">{user.name}</h1>
          <div className="text-xs text-gray-400">
            @{username}{user.isAdmin && <span className="ml-1.5 text-[10px] font-bold text-amber-600 bg-amber-100 dark:bg-amber-900/30 rounded px-1.5 py-0.5">ADMIN</span>}
          </div>
        </div>
      </div>

      {/* Thông tin cá nhân */}
      <form onSubmit={saveInfo} className="card p-5 space-y-3">
        <h2 className="font-semibold text-gray-800 dark:text-gray-100">Thông tin cá nhân</h2>
        <div>
          <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Họ và tên <span className="text-gray-300">(không bắt buộc)</span></label>
          <input className={inputCls} value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="VD: Nguyễn Văn A" />
          <p className="text-[11px] text-gray-400 mt-1">Có tên thì khi đăng nhập sẽ hiển thị tên này thay cho tên đăng nhập.</p>
        </div>
        <div>
          <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Địa chỉ <span className="text-gray-300">(không bắt buộc)</span></label>
          <input className={inputCls} value={address} onChange={(e) => setAddress(e.target.value)} placeholder="VD: Hà Nội" />
        </div>
        <div className="flex items-center gap-3">
          <button type="submit" disabled={savingInfo} className="btn-primary disabled:opacity-60">{savingInfo ? 'Đang lưu...' : 'Lưu thông tin'}</button>
          {infoMsg.text && <span className={`text-sm ${infoMsg.ok ? 'text-emerald-600' : 'text-red-500'}`}>{infoMsg.text}</span>}
        </div>
      </form>

      {/* Đổi mật khẩu */}
      <form onSubmit={savePw} className="card p-5 space-y-3">
        <h2 className="font-semibold text-gray-800 dark:text-gray-100">Đổi mật khẩu</h2>
        <input type="password" className={inputCls} value={oldPw} onChange={(e) => setOldPw(e.target.value)} placeholder="Mật khẩu hiện tại" autoComplete="current-password" />
        <input type="password" className={inputCls} value={newPw} onChange={(e) => setNewPw(e.target.value)} placeholder="Mật khẩu mới (tối thiểu 4 ký tự)" autoComplete="new-password" />
        <input type="password" className={inputCls} value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)} placeholder="Nhập lại mật khẩu mới" autoComplete="new-password" />
        <div className="flex items-center gap-3">
          <button type="submit" disabled={savingPw} className="btn-primary disabled:opacity-60">{savingPw ? 'Đang đổi...' : 'Đổi mật khẩu'}</button>
          {pwMsg.text && <span className={`text-sm ${pwMsg.ok ? 'text-emerald-600' : 'text-red-500'}`}>{pwMsg.text}</span>}
        </div>
      </form>
    </div>
  )
}
