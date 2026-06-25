import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useStore } from '../store'
import { listUsers } from '../api'

function fmt(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d)) return '—'
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`
}

export default function AdminUsersPage() {
  const user = useStore((s) => s.user)
  const [users, setUsers] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!user?.isAdmin) return
    listUsers().then(setUsers).catch((e) => setError(e.message))
  }, [user])

  if (!user?.isAdmin) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center space-y-3">
        <div className="text-5xl">🚫</div>
        <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Không có quyền</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">Trang này chỉ dành cho admin.</p>
        <Link to="/" className="text-primary underline">Về trang chủ</Link>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <h1 className="font-display font-bold text-xl text-gray-900 dark:text-gray-100 mb-1">👑 Danh sách người dùng</h1>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{users ? `${users.length} tài khoản` : 'Đang tải...'}</p>

      {error && <div className="text-sm text-red-500 mb-3">⚠️ {error}</div>}

      {users && (
        <div className="overflow-x-auto card p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-dark-border">
                <th className="px-3 py-2 font-semibold">#</th>
                <th className="px-3 py-2 font-semibold">Tài khoản</th>
                <th className="px-3 py-2 font-semibold text-center">Tiến độ</th>
                <th className="px-3 py-2 font-semibold">Ngày tạo</th>
                <th className="px-3 py-2 font-semibold">Học gần nhất</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u, i) => (
                <tr key={u.username} className="border-b border-gray-100 dark:border-dark-border/50">
                  <td className="px-3 py-2 text-gray-400">{i + 1}</td>
                  <td className="px-3 py-2 font-medium text-gray-800 dark:text-gray-100">
                    {u.username}
                    {u.isAdmin && <span className="ml-1.5 text-[10px] font-bold text-amber-600 bg-amber-100 dark:bg-amber-900/30 rounded px-1.5 py-0.5">ADMIN</span>}
                  </td>
                  <td className="px-3 py-2 text-center text-gray-700 dark:text-gray-300">{u.doneDays}/30</td>
                  <td className="px-3 py-2 text-gray-500 dark:text-gray-400">{fmt(u.createdAt)}</td>
                  <td className="px-3 py-2 text-gray-500 dark:text-gray-400">{fmt(u.lastDone)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
