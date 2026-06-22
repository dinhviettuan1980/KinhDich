import { createPortal } from 'react-dom'
import { useStore, LENS } from '../store'

export default function LensOnboarding() {
  const { setLens } = useStore()

  const choose = (key) => setLens(key)

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
      <div className="relative w-full max-w-md card p-6 z-10 max-h-[90vh] overflow-y-auto animate-fade-in">
        <div className="text-center mb-5">
          <div className="text-3xl mb-2">☯</div>
          <h2 className="text-lg font-display font-bold text-gray-900 dark:text-gray-100">
            Bạn muốn học Kinh Dịch theo góc nhìn nào?
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Cùng một bài học, ví dụ sẽ được kể theo góc nhìn bạn chọn. Đổi lại bất cứ lúc nào.
          </p>
        </div>

        <div className="space-y-3">
          {Object.values(LENS).map((l) => (
            <button
              key={l.key}
              onClick={() => choose(l.key)}
              className="w-full flex items-center gap-3 p-4 rounded-2xl border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card hover:border-primary hover:bg-primary/5 dark:hover:bg-primary/10 transition-all text-left active:scale-[0.98]"
            >
              <span className="text-3xl flex-shrink-0">{l.icon}</span>
              <div>
                <div className="font-semibold text-gray-800 dark:text-gray-100">{l.label}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {l.key === 'life' && 'Ví dụ gần gũi, đời thường'}
                  {l.key === 'business' && 'Ví dụ quản lý, kinh doanh, lãnh đạo'}
                  {l.key === 'tech' && 'Ví dụ lập trình, hệ thống, dự án'}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>,
    document.body
  )
}
