import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchLesson, saveReflection } from '../api'
import { useStore, LEVEL_COLORS, LEVEL_NAMES, LENS } from '../store'
import { AllTrigrams, HexagramSVG } from '../components/HexagramSVG'
import ReadAloudButton from '../components/ReadAloudButton'

const TRIGRAM_DAY = { 14: 'qian', 15: 'zhen', 16: 'kan', 17: 'gen' }
const LEVEL_TRIGRAMS = { 4: true, 5: true }

// Card hiển thị một ví dụ theo góc nhìn
function ExampleCard({ lensKey, text, accent }) {
  const l = LENS[lensKey]
  return (
    <div className={`card p-5 border-l-4 ${accent}`}>
      <h2 className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">{l.exampleLabel}</h2>
      <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">{text}</p>
    </div>
  )
}

const ACCENT = { life: 'border-emerald-400', business: 'border-amber-400', tech: 'border-primary' }

export default function LearnPage() {
  const { day } = useParams()
  const navigate = useNavigate()
  const { lens, user, openLogin } = useStore()
  const [lesson, setLesson] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showOthers, setShowOthers] = useState(false)

  // Reflection
  const [reflectionText, setReflectionText] = useState('')
  const [reflectSaved, setReflectSaved] = useState(false)
  const [reflectSaving, setReflectSaving] = useState(false)

  useEffect(() => {
    setLoading(true); setShowOthers(false); setReflectionText(''); setReflectSaved(false)
    fetchLesson(day)
      .then(setLesson)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [day])

  if (!user) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center space-y-4">
        <div className="text-5xl">🔒</div>
        <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Bài học đang khóa</h2>
        <p className="text-gray-500 dark:text-gray-400 text-sm">Đăng nhập để mở khóa toàn bộ bài học.</p>
        <div className="flex gap-3 justify-center">
          <button onClick={() => navigate('/')} className="btn-secondary">← Trang chủ</button>
          <button onClick={openLogin} className="btn-primary">Đăng nhập</button>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 flex justify-center">
        <div className="w-10 h-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
      </div>
    )
  }

  if (error || !lesson) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-gray-500 dark:text-gray-400">{error || 'Không tìm thấy bài học'}</p>
        <button onClick={() => navigate('/')} className="btn-primary mt-4">← Về trang chủ</button>
      </div>
    )
  }

  const colors = LEVEL_COLORS[lesson.level] || LEVEL_COLORS[1]
  const dayNum = Number(day)

  // Ví dụ theo lens: primary mở sẵn, hai góc còn lại trong accordion
  const exampleText = { life: lesson.realExample, business: lesson.businessExample, tech: lesson.techExample }
  const activeLens = lens || 'life'
  const others = ['life', 'business', 'tech'].filter((k) => k !== activeLens && exampleText[k])

  const handleSaveReflection = async () => {
    if (!reflectionText.trim()) return
    setReflectSaving(true)
    try { await saveReflection(dayNum, reflectionText.trim()); setReflectSaved(true) }
    catch { /* noop */ } finally { setReflectSaving(false) }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      {/* Top nav */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/')} className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-sm">
          ← Trang chủ
        </button>
        <div className="flex-1 h-1.5 bg-gray-100 dark:bg-dark-border rounded-full overflow-hidden">
          <div className="h-full bg-primary rounded-full" style={{ width: `${(dayNum / 30) * 100}%` }} />
        </div>
        <span className="text-xs text-gray-400 dark:text-gray-500 flex-shrink-0">{dayNum}/30</span>
      </div>

      {/* Level + concept badge */}
      <div className="flex flex-wrap items-center gap-2">
        <span className={`level-badge ${colors.bg} ${colors.text}`}>
          Level {lesson.level} · {LEVEL_NAMES[lesson.level]}
        </span>
        <span className="level-badge bg-gray-100 dark:bg-dark-card text-gray-600 dark:text-gray-300">
          Ngày {lesson.day}
        </span>
      </div>

      {/* Title */}
      <div>
        <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-gray-100 leading-tight mb-2">
          {lesson.title}
        </h1>
        <p className="text-gray-500 dark:text-gray-400 text-sm italic mb-3">{lesson.concept}</p>
        <ReadAloudButton getText={() => [
          lesson.title,
          lesson.concept,
          lesson.explanation,
          exampleText[activeLens],
          lesson.reflection,
        ].filter(Boolean).join('. ')} />
      </div>

      {/* Hexagram for level 4+ */}
      {LEVEL_TRIGRAMS[lesson.level] && (
        <div className="card p-6 flex justify-center">
          {lesson.level === 4 && TRIGRAM_DAY[dayNum] ? (
            <HexagramSVG trigram={TRIGRAM_DAY[dayNum]} size={80} showLabel={true} />
          ) : lesson.level === 4 ? (
            <AllTrigrams />
          ) : (
            <div className="flex gap-4">
              <HexagramSVG trigram="qian" size={56} showLabel={true} />
              <HexagramSVG trigram="kun" size={56} showLabel={true} />
            </div>
          )}
        </div>
      )}

      {/* Main explanation */}
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Giải thích</h2>
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {lesson.explanation.split('\n\n').map((para, i) => (
            <p key={i} className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3 last:mb-0">{para}</p>
          ))}
        </div>
      </div>

      {/* Ví dụ theo góc nhìn đã chọn */}
      {exampleText[activeLens] && <ExampleCard lensKey={activeLens} text={exampleText[activeLens]} accent={ACCENT[activeLens]} />}

      {/* Các góc nhìn khác (accordion) */}
      {others.length > 0 && (
        <div>
          <button
            onClick={() => setShowOthers((v) => !v)}
            className="w-full flex items-center justify-between px-4 py-2.5 rounded-xl bg-gray-50 dark:bg-dark-card text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-border transition-colors"
          >
            <span>👓 Xem góc nhìn khác ({others.map((k) => LENS[k].icon).join(' ')})</span>
            <span className={`transition-transform ${showOthers ? 'rotate-180' : ''}`}>▾</span>
          </button>
          {showOthers && (
            <div className="space-y-3 mt-3 animate-slide-up">
              {others.map((k) => <ExampleCard key={k} lensKey={k} text={exampleText[k]} accent={ACCENT[k]} />)}
            </div>
          )}
        </div>
      )}

      {/* Image hint */}
      {lesson.imageHint && (
        <div className="card p-4 bg-gray-50 dark:bg-dark-card/50 text-center">
          <p className="text-xs text-gray-400 dark:text-gray-500 italic">💡 {lesson.imageHint}</p>
        </div>
      )}

      {/* Reflection — suy ngẫm trước khi làm quiz */}
      {lesson.reflection && (
        <div className="card p-5 bg-gradient-to-br from-purple-50 to-primary/5 dark:from-purple-900/20 dark:to-primary/10 border border-primary/20">
          <h2 className="text-xs font-bold uppercase tracking-wider text-primary dark:text-primary-light mb-2">🪷 Suy ngẫm</h2>
          <p className="text-gray-700 dark:text-gray-200 text-sm font-medium mb-3">{lesson.reflection}</p>
          <textarea
            value={reflectionText}
            onChange={(e) => { setReflectionText(e.target.value); setReflectSaved(false) }}
            placeholder="Viết vài dòng quan sát của riêng bạn..."
            rows={3}
            className="w-full px-3 py-2.5 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm text-gray-900 dark:text-gray-100 outline-none focus:border-primary resize-none"
          />
          <div className="flex items-center gap-3 mt-2">
            <button
              onClick={handleSaveReflection}
              disabled={reflectSaving || !reflectionText.trim()}
              className="btn-secondary text-sm disabled:opacity-50"
            >
              {reflectSaving ? 'Đang lưu...' : 'Lưu suy ngẫm'}
            </button>
            {reflectSaved && <span className="text-xs text-emerald-600 dark:text-emerald-400">✓ Đã lưu vào nhật ký</span>}
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex gap-3 pt-2">
        {dayNum > 1 && (
          <button onClick={() => navigate(`/learn/${dayNum - 1}`)} className="btn-secondary flex-1">
            ← Ngày {dayNum - 1}
          </button>
        )}
        <button onClick={() => navigate(`/quiz/${dayNum}`)} className="btn-primary flex-1">
          Làm quiz →
        </button>
      </div>
    </div>
  )
}
