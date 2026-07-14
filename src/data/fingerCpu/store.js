// Store riêng cho Finger CPU Lab — tách khỏi store.js chính của app (không đụng vào
// tiến độ 30 ngày / lens / auth vốn có), lưu localStorage key riêng.
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useFingerCpuStore = create(
  persist(
    (set, get) => ({
      developerMode: false,
      toggleDeveloperMode: () => set((s) => ({ developerMode: !s.developerMode })),

      bookmarks: [],
      toggleBookmark: (id) =>
        set((s) => ({
          bookmarks: s.bookmarks.includes(id) ? s.bookmarks.filter((x) => x !== id) : [...s.bookmarks, id],
        })),
      isBookmarked: (id) => get().bookmarks.includes(id),

      visited: [],
      markVisited: (id) =>
        set((s) => (s.visited.includes(id) ? s : { visited: [...s.visited, id] })),
    }),
    { name: 'kinhdich-finger-cpu' }
  )
)
