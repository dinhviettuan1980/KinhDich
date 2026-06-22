import { Link, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { useStore } from '../store'

export default function Navbar() {
  const { darkMode, toggleDark, progress } = useStore()
  const [menuOpen, setMenuOpen] = useState(false)
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
    </nav>
  )
}
