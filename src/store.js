import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { fetchProgress, setActiveUser, clearActiveUser, fetchProfile, saveLens } from './api'

export const LENS = {
  life: { key: 'life', label: 'Cuộc sống thường ngày', icon: '🌿', field: 'realExample', exampleLabel: '🌍 Ví dụ đời thực' },
  business: { key: 'business', label: 'Quản lý & Kinh doanh', icon: '📈', field: 'businessExample', exampleLabel: '📈 Trong quản lý & kinh doanh' },
  tech: { key: 'tech', label: 'CNTT & Công nghệ', icon: '💻', field: 'techExample', exampleLabel: '💻 Trong CNTT / Công nghệ' },
}

export const LEVEL_COLORS = {
  1: { bg: 'bg-emerald-100 dark:bg-emerald-900/30', text: 'text-emerald-700 dark:text-emerald-300', border: 'border-emerald-200 dark:border-emerald-800', dot: 'bg-emerald-500' },
  2: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-300', border: 'border-blue-200 dark:border-blue-800', dot: 'bg-blue-500' },
  3: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-300', border: 'border-orange-200 dark:border-orange-800', dot: 'bg-orange-500' },
  4: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300', border: 'border-red-200 dark:border-red-800', dot: 'bg-red-500' },
  5: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-300', border: 'border-purple-200 dark:border-purple-800', dot: 'bg-purple-500' },
  6: { bg: 'bg-pink-100 dark:bg-pink-900/30', text: 'text-pink-700 dark:text-pink-300', border: 'border-pink-200 dark:border-pink-800', dot: 'bg-pink-500' },
  7: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-300', border: 'border-yellow-200 dark:border-yellow-800', dot: 'bg-yellow-500' },
}

export const LEVEL_NAMES = {
  1: 'Nền tảng',
  2: 'Âm Dương',
  3: 'Tứ Tượng',
  4: 'Bát Quái',
  5: '64 Quẻ',
  6: 'Hào & Quẻ Biến',
  7: 'Ứng Dụng',
}

export const useStore = create(
  persist(
    (set, get) => ({
      darkMode: false,
      toggleDark: () => {
        const next = !get().darkMode
        set({ darkMode: next })
        document.documentElement.classList.toggle('dark', next)
      },

      progress: null,
      lessons: [],
      setProgress: (p) => set({ progress: p }),
      setLessons: (l) => set({ lessons: l }),

      // ---- Learning Lens ----
      lens: 'life',        // 'life' | 'business' | 'tech'
      lensChosen: false,   // user đã chủ động chọn chưa (để hiện onboarding)
      lensReady: false,    // đã nạp lens từ backend chưa
      loadLens: async () => {
        try {
          const p = await fetchProfile()
          set({ lens: p.learningLens || 'life', lensChosen: !!p.chosen, lensReady: true })
        } catch { set({ lensReady: true }) }
      },
      setLens: async (lens) => {
        set({ lens, lensChosen: true })
        try { await saveLens(lens) } catch { /* noop */ }
      },

      // ---- Người dùng (chỉ để hiển thị; không cần bảo mật) ----
      // user: { provider: 'google'|'facebook'|'user', uid, name, email, avatar }
      user: null,
      login: async (user) => {
        setActiveUser(user.uid)            // tiến độ gắn theo tài khoản
        set({ user })
        try { set({ progress: await fetchProgress() }) } catch { /* noop */ }
        get().loadLens()                   // nạp góc nhìn của tài khoản
      },
      logout: async () => {
        clearActiveUser()                  // về danh tính khách
        set({ user: null })
        try { set({ progress: await fetchProgress() }) } catch { /* noop */ }
        get().loadLens()
      },

      getTodayDay: () => {
        const { progress, user } = get()
        if (user?.isAdmin) return 30 // admin: mở khoá toàn bộ
        if (!progress) return 1
        const completed = progress.completedDays || []
        if (completed.length === 0) return 1
        return Math.min(Math.max(...completed) + 1, 30)
      },

      isDayUnlocked: (day) => {
        const { progress, user } = get()
        if (user?.isAdmin) return true // admin: không khoá bài nào
        if (day === 1) return true
        if (!progress) return false
        return (progress.completedDays || []).includes(day - 1)
      },

      isDayCompleted: (day) => {
        const { progress } = get()
        if (!progress) return false
        return (progress.completedDays || []).includes(day)
      },
    }),
    {
      name: 'kinhdich-store',
      partialize: (s) => ({ darkMode: s.darkMode, user: s.user }),
      // Khi tải lại trang: nếu đã đăng nhập, đảm bảo id tiến độ khớp tài khoản
      onRehydrateStorage: () => (state) => {
        if (state?.user?.uid) setActiveUser(state.user.uid)
      },
    }
  )
)
