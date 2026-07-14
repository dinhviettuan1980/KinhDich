import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FingerHandSVG from '../components/fingerCpu/FingerHandSVG'
import { LESSON_GROUPS, LESSON_BY_ID, LESSONS } from '../data/fingerCpu/lessons'
import { useFingerCpuStore } from '../data/fingerCpu/store'

export default function FingerCpuIntroPage() {
  const navigate = useNavigate()
  const [demoIndex, setDemoIndex] = useState(null)
  const [query, setQuery] = useState('')
  const { developerMode, toggleDeveloperMode, bookmarks, toggleBookmark, visited } = useFingerCpuStore()

  const q = query.trim().toLowerCase()
  const matches = (lesson) => !q || lesson.title.toLowerCase().includes(q) || lesson.subtitle.toLowerCase().includes(q)

  const filteredGroups = useMemo(
    () => LESSON_GROUPS.map((g) => ({ ...g, lessonIds: g.lessonIds.filter((id) => matches(LESSON_BY_ID[id])) })).filter((g) => g.lessonIds.length > 0),
    [q]
  )
  const bookmarkedLessons = LESSONS.filter((l) => bookmarks.includes(l.id))

  const LessonRow = ({ id }) => {
    const lesson = LESSON_BY_ID[id]
    const ready = lesson.status === 'ready'
    const isBookmarked = bookmarks.includes(id)
    return (
      <div className="w-full flex items-center gap-2 px-4 py-3 hover:bg-gray-50 dark:hover:bg-dark-card/50 transition-colors first:rounded-t-2xl last:rounded-b-2xl">
        <button
          onClick={(e) => { e.stopPropagation(); toggleBookmark(id) }}
          className="flex-shrink-0 text-base"
          aria-label="Đánh dấu yêu thích"
        >
          {isBookmarked ? '⭐' : '☆'}
        </button>
        <button onClick={() => navigate(`/finger-cpu/bai/${id}`)} className="flex-1 min-w-0 flex items-center gap-3 text-left">
          <span className="w-7 h-7 flex-shrink-0 rounded-full bg-gray-100 dark:bg-dark-card text-xs font-mono font-bold text-gray-500 dark:text-gray-400 flex items-center justify-center">
            {id}
          </span>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">{lesson.title}</div>
            <div className="text-xs text-gray-400 dark:text-gray-500 truncate">{lesson.subtitle}</div>
          </div>
          {visited.includes(id) && <span className="text-[10px] text-primary flex-shrink-0">đã học</span>}
          {!ready && <span className="text-[10px] text-gray-300 dark:text-gray-600 flex-shrink-0">sắp có</span>}
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6 animate-fade-in">
      <div className="text-center space-y-3">
        <div className="text-5xl">🖐️💻</div>
        <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-gray-100 leading-tight">
          Bàn tay của các thầy
          <br />dưới góc nhìn khoa học máy tính
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto leading-relaxed">
          Đây <strong>không phải</strong> module xem bói. Đây là Learning Lab giải thích kỹ thuật
          "bấm ngón tay" bằng Data Structure, Algorithm, Lookup Table và Modulo — để sau khi học
          xong, bạn hiểu rằng <em>"các thầy đang tính toán"</em>, không phải "các thầy có phép thuật".
        </p>
      </div>

      <div className="card p-6 flex flex-col items-center animate-slide-up">
        <FingerHandSVG activeIndex={demoIndex} onSelect={setDemoIndex} labelAt={(i) => `đốt ${i}`} size={240} />
      </div>

      <div className="card p-4 flex items-center justify-between gap-3">
        <div className="text-sm">
          <span className="font-bold text-primary">{visited.length}</span>
          <span className="text-gray-400 dark:text-gray-500">/{LESSONS.length} bài đã học</span>
        </div>
        <button
          onClick={toggleDeveloperMode}
          className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
            developerMode ? 'bg-primary text-white' : 'bg-gray-50 dark:bg-dark-card/50 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-border'
          }`}
        >
          💻 Developer Mode {developerMode ? 'ON' : 'OFF'}
        </button>
      </div>

      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="🔍 Tìm bài học (vd: modulo, hoa giáp, quẻ...)"
        className="w-full px-4 py-2.5 rounded-xl border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm outline-none focus:border-primary"
      />

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Người xưa không có...</h2>
        <div className="flex flex-wrap gap-2 mb-3">
          {['Máy tính', 'Smartphone', 'Excel', 'IDE', 'Calculator'].map((t) => (
            <span key={t} className="text-xs px-2.5 py-1 rounded-full bg-gray-100 dark:bg-dark-card text-gray-500 dark:text-gray-400 line-through decoration-red-400">
              {t}
            </span>
          ))}
        </div>
        <p className="text-sm text-gray-700 dark:text-gray-300">
          Nên họ dùng chính bàn tay làm <strong>RAM</strong>, <strong>Cache</strong> và{' '}
          <strong>Lookup Table</strong> di động — luôn mang theo, không bao giờ hết pin.
        </p>
      </div>

      <div className="flex gap-3">
        <button onClick={() => navigate('/finger-cpu/bai/1')} className="btn-primary flex-1">
          🚀 Bắt đầu học từ Bài 1
        </button>
        <button onClick={() => navigate('/finger-cpu/simulator')} className="btn-secondary flex-1">
          🎛️ Vào Simulator
        </button>
      </div>

      <div>
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2 px-1">
          🧰 Công cụ tương tác
        </h2>
        <div className="card divide-y divide-gray-50 dark:divide-dark-border/50">
          {[
            { to: '/finger-cpu/simulator', icon: '🎛️', ten: 'Finger CPU Simulator', mota: '7 mode tra cứu trên bàn tay' },
            { to: '/finger-cpu/memory-visualizer', icon: '🧠', ten: 'Memory Visualizer', mota: 'RAM/Pointer/HashMap/Cache ↔ bàn tay' },
            { to: '/finger-cpu/algorithm-visualizer', icon: '🔀', ten: 'Algorithm Visualizer', mota: 'Input → Modulo → Lookup → Result' },
            { to: '/finger-cpu/data-structure-mode', icon: '🗃️', ten: 'Data Structure Mode', mota: 'Array/HashMap/Matrix/Binary/Graph' },
            { to: '/finger-cpu/debug-mode', icon: '🐞', ten: 'Debug Mode', mota: 'Step Into/Step Over như IDE' },
          ].map((tool) => (
            <button
              key={tool.to}
              onClick={() => navigate(tool.to)}
              className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-dark-card/50 transition-colors first:rounded-t-2xl last:rounded-b-2xl"
            >
              <span className="text-xl flex-shrink-0">{tool.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-800 dark:text-gray-100">{tool.ten}</div>
                <div className="text-xs text-gray-400 dark:text-gray-500 truncate">{tool.mota}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2 px-1">
          🎮 Trò chơi
        </h2>
        <div className="card divide-y divide-gray-50 dark:divide-dark-border/50">
          {[
            { to: '/finger-cpu/game/ghi-nho', icon: '🎯', ten: 'Finger Memory Trainer', mota: '"Tỵ ở đâu?" — chạm đúng đốt tay' },
            { to: '/finger-cpu/game/toc-do', icon: '⏱️', ten: 'Speed Challenge', mota: '30 giây, trộn Địa Chi/Thiên Can/Bát Quái' },
            { to: '/finger-cpu/game/hexagram-builder', icon: '🧱', ten: 'Hexagram Builder', mota: 'Bấm 6 hào, tự sinh quẻ' },
            { to: '/finger-cpu/game/binary-mode', icon: '🔟', ten: 'Binary Mode', mota: 'Đếm nhị phân 3-bit và 6-bit' },
          ].map((game) => (
            <button
              key={game.to}
              onClick={() => navigate(game.to)}
              className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-dark-card/50 transition-colors first:rounded-t-2xl last:rounded-b-2xl"
            >
              <span className="text-xl flex-shrink-0">{game.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-800 dark:text-gray-100">{game.ten}</div>
                <div className="text-xs text-gray-400 dark:text-gray-500 truncate">{game.mota}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {bookmarkedLessons.length > 0 && !q && (
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2 px-1">
            ⭐ Đã đánh dấu
          </h2>
          <div className="card divide-y divide-gray-50 dark:divide-dark-border/50">
            {bookmarkedLessons.map((l) => <LessonRow key={l.id} id={l.id} />)}
          </div>
        </div>
      )}

      <div className="space-y-5">
        {filteredGroups.length === 0 && (
          <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-6">Không tìm thấy bài học nào khớp "{query}".</p>
        )}
        {filteredGroups.map((group) => (
          <div key={group.key}>
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2 px-1">
              {group.title}
            </h2>
            <div className="card divide-y divide-gray-50 dark:divide-dark-border/50">
              {group.lessonIds.map((id) => <LessonRow key={id} id={id} />)}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
