import { Link, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { useStore } from '../store'
import LoginModal from './LoginModal'

export default function Navbar() {
  const { darkMode, toggleDark, progress, user, logout } = useStore()
  const [menuOpen, setMenuOpen] = useState(false)
  const [showLogin, setShowLogin] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const location = useLocation()
  const streak = progress?.streak || 0

  const links = [
    { to: '/', label: 'Trang chủ' },
    { to: '/map', label: 'Bản đồ 30 ngày' },
    { to: '/tutor', label: '🤖 AI Tutor' },
  ]

  const isActive = (to) => location.pathname === to

  return (
    <nav className="sticky top-0 z-50 bg-white/80 dark:bg-dark-bg/80 backdrop-blur-md border-b border-gray-200 dark:border-dark-border">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 flex-shrink-0">
          <span className="text-2xl">☯</span>
          <span className="font-display font-bold text-lg text-primary hidden sm:block">Kinh Dịch</span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                isActive(l.to)
                  ? 'bg-primary/10 text-primary'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-card'
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          {streak > 0 && (
            <div className="flex items-center gap-1 bg-accent/10 text-accent px-2.5 py-1 rounded-full text-sm font-bold">
              🔥 {streak}
            </div>
          )}
          <button
            onClick={toggleDark}
            className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-dark-card transition-colors text-lg"
            aria-label="Toggle dark mode"
          >
            {darkMode ? '☀️' : '🌙'}
          </button>

          {/* Auth */}
          {user ? (
            <div className="relative">
              <button
                onClick={() => setProfileOpen((v) => !v)}
                className="flex items-center gap-1.5 pl-1 pr-2 py-1 rounded-full hover:bg-gray-100 dark:hover:bg-dark-card transition-colors"
              >
                {user.avatar ? (
                  <img src={user.avatar} alt="" className="w-7 h-7 rounded-full" referrerPolicy="no-referrer" />
                ) : (
                  <span className="w-7 h-7 rounded-full bg-primary/15 text-primary flex items-center justify-center text-sm font-bold">
                    {(user.name || '?').charAt(0).toUpperCase()}
                  </span>
                )}
                <span className="hidden sm:block text-sm font-medium text-gray-700 dark:text-gray-200 max-w-[100px] truncate">{user.name}</span>
              </button>
              {profileOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setProfileOpen(false)} />
                  <div className="absolute right-0 mt-2 w-52 card p-3 z-20 shadow-lg">
                    <div className="flex items-center gap-2 pb-2 mb-2 border-b border-gray-100 dark:border-dark-border">
                      <div className="min-w-0">
                        <div className="text-sm font-semibold text-gray-800 dark:text-gray-100 truncate">{user.name}</div>
                        <div className="text-xs text-gray-400 truncate">{user.email || ({ google: 'Google', facebook: 'Facebook', user: 'Tài khoản' }[user.provider])}</div>
                      </div>
                    </div>
                    <button
                      onClick={() => { setProfileOpen(false); logout() }}
                      className="w-full text-left text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg px-2 py-1.5 transition-colors"
                    >
                      Đăng xuất
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <button
              onClick={() => setShowLogin(true)}
              className="px-3 py-1.5 rounded-lg text-sm font-semibold bg-primary text-white hover:bg-primary-light transition-colors"
            >
              Đăng nhập
            </button>
          )}

          {/* Mobile menu */}
          <button
            className="md:hidden w-9 h-9 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-dark-card"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            <span className="text-xl">{menuOpen ? '✕' : '☰'}</span>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-gray-200 dark:border-dark-border bg-white dark:bg-dark-bg px-4 py-2 flex flex-col gap-1">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              onClick={() => setMenuOpen(false)}
              className={`px-3 py-2.5 rounded-lg text-sm font-medium ${
                isActive(l.to)
                  ? 'bg-primary/10 text-primary'
                  : 'text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-dark-card'
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>
      )}

      {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
    </nav>
  )
}
