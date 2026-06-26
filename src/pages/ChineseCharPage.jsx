import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchHantuList, fetchHantu, fetchHantuQuiz, fetchHantuProgress, saveHantuProgress } from '../api'

const LEVELS = [
  { key: 0, label: 'Tất cả' },
  { key: 1, label: 'Cấp 1', desc: '40 chữ nền tảng' },
  { key: 2, label: 'Cấp 2', desc: '40 chữ mở rộng' },
  { key: 3, label: 'Cấp 3', desc: '40 chữ nâng cao' },
  { key: 4, label: 'Cấp 4', desc: '80 chữ chuyên sâu' },
]
const TOPICS = [
  { key: '', label: 'Tất cả chủ đề' },
  { key: 'kinhDich', label: '☯ Kinh Dịch' },
  { key: 'batQua', label: '☰ Bát Quái' },
  { key: 'thienNhien', label: '🌿 Thiên Nhiên' },
  { key: 'thoiGian', label: '🕐 Thời Gian' },
  { key: 'coban', label: '🔤 Cơ Bản' },
  { key: 'conNguoi', label: '👤 Con Người' },
  { key: 'giaDinh', label: '👨‍👩‍👧 Gia Đình' },
  { key: 'sodem', label: '🔢 Số Đếm' },
  { key: 'hanhDong', label: '⚡ Hành Động' },
  { key: 'trangThai', label: '📊 Trạng Thái' },
  { key: 'nguHanh', label: '🌊 Ngũ Hành' },
  { key: 'phamChat', label: '✨ Phẩm Chất' },
  { key: 'vuTru', label: '🌌 Vũ Trụ' },
  { key: 'tenQue', label: '📖 Tên Quẻ' },
]
const LEVEL_COLORS = {
  1: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
  2: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  3: 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300',
  4: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
}

function speak(text, lang = 'zh-CN') {
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const u = new SpeechSynthesisUtterance(text)
  u.lang = lang
  u.rate = 0.85
  window.speechSynthesis.speak(u)
}

function SpeakBtn({ text, className = '' }) {
  const [speaking, setSpeaking] = useState(false)
  const handleClick = (e) => {
    e.stopPropagation()
    if (!window.speechSynthesis) return
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'zh-CN'
    u.rate = 0.85
    u.onstart = () => setSpeaking(true)
    u.onend = () => setSpeaking(false)
    u.onerror = () => setSpeaking(false)
    window.speechSynthesis.speak(u)
  }
  return (
    <button
      onClick={handleClick}
      title="Nghe phát âm"
      className={`inline-flex items-center justify-center w-7 h-7 rounded-full transition-colors ${
        speaking
          ? 'bg-primary text-white'
          : 'bg-gray-100 dark:bg-dark-card text-gray-500 dark:text-gray-400 hover:bg-primary/10 hover:text-primary'
      } ${className}`}
    >
      <span className="text-sm">{speaking ? '🔊' : '🔈'}</span>
    </button>
  )
}

// ============ LIST VIEW ============
function ListView({ onSelect, progress }) {
  const [list, setList] = useState([])
  const [loading, setLoading] = useState(true)
  const [level, setLevel] = useState(0)
  const [topic, setTopic] = useState('')
  const [search, setSearch] = useState('')
  const [view, setView] = useState('grid') // grid | table

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchHantuList({ level: level || undefined, topic: topic || undefined, search: search || undefined })
      setList(data)
    } catch { setList([]) }
    finally { setLoading(false) }
  }, [level, topic, search])

  useEffect(() => { load() }, [load])

  const learned = Object.keys(progress).length
  const total = 200

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="card p-4 flex items-center gap-4">
        <div className="flex-1">
          <div className="text-sm text-gray-500 dark:text-gray-400">Tiến độ học</div>
          <div className="flex items-baseline gap-1.5 mt-0.5">
            <span className="text-2xl font-bold text-primary">{learned}</span>
            <span className="text-sm text-gray-400">/ {total} chữ</span>
          </div>
        </div>
        <div className="w-32">
          <div className="h-2 bg-gray-100 dark:bg-dark-border rounded-full overflow-hidden">
            <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${(learned / total) * 100}%` }} />
          </div>
          <div className="text-xs text-gray-400 mt-1 text-right">{Math.round((learned / total) * 100)}%</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍 Tìm chữ, nghĩa..."
          className="flex-1 min-w-[160px] px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm outline-none focus:border-primary"
        />
        <select value={level} onChange={(e) => setLevel(Number(e.target.value))}
          className="px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm outline-none focus:border-primary">
          {LEVELS.map((l) => <option key={l.key} value={l.key}>{l.label}</option>)}
        </select>
        <select value={topic} onChange={(e) => setTopic(e.target.value)}
          className="px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm outline-none focus:border-primary">
          {TOPICS.map((t) => <option key={t.key} value={t.key}>{t.label}</option>)}
        </select>
        <button onClick={() => setView(v => v === 'grid' ? 'table' : 'grid')}
          className="px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border text-sm hover:bg-gray-50 dark:hover:bg-dark-card">
          {view === 'grid' ? '☰ Bảng' : '⊞ Lưới'}
        </button>
      </div>

      {loading ? (
        <div className="py-16 text-center text-gray-400">Đang tải...</div>
      ) : list.length === 0 ? (
        <div className="py-16 text-center text-gray-400">Không tìm thấy chữ nào</div>
      ) : view === 'grid' ? (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2">
          {list.map((h) => {
            const p = progress[h.id]
            const learned = p && p.reviewCount > 0
            return (
              <button
                key={h.id}
                onClick={() => onSelect(h.id)}
                className={`relative group card p-3 flex flex-col items-center gap-1 hover:border-primary transition-all cursor-pointer text-center ${learned ? 'border-emerald-300 dark:border-emerald-700' : ''}`}
              >
                <span className="text-3xl font-hantu leading-none" style={{ fontFamily: 'serif' }}>{h.char}</span>
                <span className="text-[10px] text-gray-500 dark:text-gray-400">{h.hanViet}</span>
                <span className="text-[10px] text-gray-400">{h.pinyin}</span>
                <div className="flex items-center gap-1 mt-0.5">
                  <span className={`text-[9px] px-1 rounded ${LEVEL_COLORS[h.level]}`}>C{h.level}</span>
                  {learned && <span className="text-[9px] text-emerald-500">✓</span>}
                </div>
                <SpeakBtn text={h.char} className="absolute top-1 right-1 w-5 h-5 opacity-0 group-hover:opacity-100" />
              </button>
            )
          })}
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-dark-card border-b border-gray-200 dark:border-dark-border">
              <tr>
                <th className="text-left px-3 py-2 text-gray-500 font-medium">Chữ</th>
                <th className="text-left px-3 py-2 text-gray-500 font-medium">Hán Việt</th>
                <th className="text-left px-3 py-2 text-gray-500 font-medium hidden sm:table-cell">Pinyin</th>
                <th className="text-left px-3 py-2 text-gray-500 font-medium">Nghĩa</th>
                <th className="text-left px-3 py-2 text-gray-500 font-medium hidden md:table-cell">Cấp</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-dark-border">
              {list.map((h) => (
                <tr key={h.id} onClick={() => onSelect(h.id)} className="hover:bg-gray-50 dark:hover:bg-dark-card cursor-pointer">
                  <td className="px-3 py-2">
                    <span className="text-2xl" style={{ fontFamily: 'serif' }}>{h.char}</span>
                  </td>
                  <td className="px-3 py-2 font-medium text-gray-800 dark:text-gray-100">{h.hanViet}</td>
                  <td className="px-3 py-2 text-gray-500 hidden sm:table-cell">{h.pinyin}</td>
                  <td className="px-3 py-2 text-gray-600 dark:text-gray-300 max-w-[200px] truncate">{h.meaning}</td>
                  <td className="px-3 py-2 hidden md:table-cell">
                    <span className={`text-xs px-1.5 py-0.5 rounded ${LEVEL_COLORS[h.level]}`}>Cấp {h.level}</span>
                  </td>
                  <td className="px-3 py-2" onClick={(e) => e.stopPropagation()}>
                    <SpeakBtn text={h.char} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ============ DETAIL VIEW ============
function DetailView({ id, onBack, progress, onProgressUpdate }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    fetchHantu(id).then(setData).catch(() => setData(null)).finally(() => setLoading(false))
  }, [id])

  const markLearned = async () => {
    const p = progress[id]
    const reviewCount = (p?.reviewCount || 0) + 1
    const score = Math.min((p?.score || 0) + 10, 100)
    await saveHantuProgress(id, score, reviewCount)
    onProgressUpdate()
  }

  if (loading) return <div className="py-20 text-center text-gray-400">Đang tải...</div>
  if (!data) return <div className="py-20 text-center text-gray-400">Không tìm thấy</div>

  const p = progress[id]
  const learned = p && p.reviewCount > 0

  return (
    <div className="space-y-4 max-w-2xl mx-auto">
      <button onClick={onBack} className="flex items-center gap-1 text-sm text-gray-500 hover:text-primary transition-colors">
        ← Danh sách
      </button>

      {/* Hero */}
      <div className="card p-6">
        <div className="flex items-start gap-6">
          <div className="flex flex-col items-center gap-2">
            <span className="text-8xl leading-none" style={{ fontFamily: 'serif' }}>{data.char}</span>
            <SpeakBtn text={data.char} className="w-9 h-9" />
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{data.hanViet}</h1>
              <span className={`text-xs px-2 py-0.5 rounded-full ${LEVEL_COLORS[data.level]}`}>Cấp {data.level}</span>
              {learned && <span className="text-xs bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300 px-2 py-0.5 rounded-full">✓ Đã học</span>}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg text-gray-500 dark:text-gray-400 italic">{data.pinyin}</span>
              <SpeakBtn text={data.pinyin} />
            </div>
            <p className="text-gray-700 dark:text-gray-200 text-base mt-1">{data.meaning}</p>
          </div>
        </div>
        <button
          onClick={markLearned}
          className={`mt-4 w-full py-2.5 rounded-xl text-sm font-semibold transition-colors ${
            learned
              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-700'
              : 'bg-primary text-white hover:bg-primary-light'
          }`}
        >
          {learned ? `✓ Đã học (${p.reviewCount} lần)` : '☑ Đánh dấu đã học'}
        </button>
      </div>

      {/* Kinh Dịch context */}
      {data.kinhDichContext && (
        <div className="card p-4 space-y-1">
          <div className="text-xs font-bold uppercase tracking-wider text-primary/70 mb-2">☯ Trong Kinh Dịch</div>
          <p className="text-gray-700 dark:text-gray-200 text-sm leading-relaxed">{data.kinhDichContext}</p>
        </div>
      )}

      {/* Examples */}
      {(data.lifeExample || data.itExample) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {data.lifeExample && (
            <div className="card p-4">
              <div className="text-xs font-bold uppercase tracking-wider text-amber-600/70 mb-2">🌱 Trong cuộc sống</div>
              <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">{data.lifeExample}</p>
            </div>
          )}
          {data.itExample && (
            <div className="card p-4">
              <div className="text-xs font-bold uppercase tracking-wider text-blue-600/70 mb-2">💻 Trong kỹ thuật</div>
              <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">{data.itExample}</p>
            </div>
          )}
        </div>
      )}

      {/* Evolution */}
      {data.evolution && (
        <div className="card p-4">
          <div className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3">📜 Lịch sử tiến hóa chữ viết</div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { key: 'giaCoVan', label: '甲骨文\nGiáp Cốt Văn' },
              { key: 'kimVan', label: '金文\nKim Văn' },
              { key: 'tieuTrien', label: '小篆\nTiểu Triện' },
              { key: 'khaiThu', label: '楷書\nKhải Thư' },
            ].map(({ key, label }) => data.evolution[key] && (
              <div key={key} className="bg-gray-50 dark:bg-dark-card rounded-lg p-3 text-center">
                <div className="text-[10px] text-gray-400 whitespace-pre-line leading-tight mb-2">{label}</div>
                <div className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed">{data.evolution[key]}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Related */}
      {data.relatedChars && data.relatedChars.length > 0 && (
        <div className="card p-4">
          <div className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3">🔗 Chữ liên quan</div>
          <div className="flex flex-wrap gap-2">
            {data.relatedChars.map((r) => (
              <button key={r.id} onClick={() => window.history.replaceState(null, '', `/additional/chinese/${r.id}`) || window.dispatchEvent(new Event('charselect_' + r.id))}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-dark-border hover:border-primary text-sm transition-colors">
                <span style={{ fontFamily: 'serif' }} className="text-lg">{r.char}</span>
                <span className="text-gray-600 dark:text-gray-300">{r.hanViet}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ============ FLASHCARD VIEW ============
function FlashcardView({ progress, onProgressUpdate }) {
  const [list, setList] = useState([])
  const [idx, setIdx] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [levelFilter, setLevelFilter] = useState(1)
  const [done, setDone] = useState(false)

  useEffect(() => {
    fetchHantuList({ level: levelFilter || undefined }).then((data) => {
      setList(data.sort(() => Math.random() - 0.5))
      setIdx(0)
      setFlipped(false)
      setDone(false)
    })
  }, [levelFilter])

  if (!list.length) return <div className="py-20 text-center text-gray-400">Đang tải...</div>

  const card = list[idx]
  const total = list.length

  const next = (knew) => {
    if (card) {
      const p = progress[card.id]
      const rc = (p?.reviewCount || 0) + (knew ? 1 : 0)
      const sc = knew ? Math.min((p?.score || 0) + 10, 100) : Math.max((p?.score || 0) - 5, 0)
      saveHantuProgress(card.id, sc, rc).then(onProgressUpdate)
    }
    if (idx + 1 >= total) { setDone(true); return; }
    setIdx((i) => i + 1)
    setFlipped(false)
  }

  if (done) return (
    <div className="py-20 text-center space-y-4">
      <div className="text-5xl">🎉</div>
      <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Hoàn thành bộ thẻ!</h2>
      <p className="text-gray-500">Đã ôn {total} chữ Hán</p>
      <button onClick={() => { setIdx(0); setFlipped(false); setDone(false); setList(l => [...l].sort(() => Math.random() - 0.5)) }}
        className="btn-primary">Ôn lại</button>
    </div>
  )

  return (
    <div className="max-w-md mx-auto space-y-4">
      <div className="flex items-center gap-3">
        <select value={levelFilter} onChange={(e) => setLevelFilter(Number(e.target.value))}
          className="px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm outline-none focus:border-primary">
          {LEVELS.map((l) => <option key={l.key} value={l.key}>{l.label}</option>)}
        </select>
        <div className="flex-1 h-2 bg-gray-100 dark:bg-dark-border rounded-full overflow-hidden">
          <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${((idx + 1) / total) * 100}%` }} />
        </div>
        <span className="text-sm text-gray-400">{idx + 1}/{total}</span>
      </div>

      {/* Card */}
      <div
        className="cursor-pointer select-none"
        style={{ perspective: '1000px' }}
        onClick={() => setFlipped((f) => !f)}
      >
        <div style={{
          position: 'relative', height: '280px',
          transformStyle: 'preserve-3d',
          transition: 'transform 0.5s',
          transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
        }}>
          {/* Front */}
          <div style={{ position: 'absolute', inset: 0, backfaceVisibility: 'hidden' }}
            className="card flex flex-col items-center justify-center gap-4 p-8">
            <span className="text-9xl leading-none" style={{ fontFamily: 'serif' }}>{card.char}</span>
            <div className="flex items-center gap-2">
              <SpeakBtn text={card.char} className="w-9 h-9" />
              <span className="text-sm text-gray-400">Nhấn để xem nghĩa</span>
            </div>
          </div>
          {/* Back */}
          <div style={{ position: 'absolute', inset: 0, backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
            className="card flex flex-col items-center justify-center gap-3 p-6 text-center bg-primary/5">
            <span className="text-5xl leading-none" style={{ fontFamily: 'serif' }}>{card.char}</span>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold text-gray-900 dark:text-gray-100">{card.hanViet}</span>
              <SpeakBtn text={card.char} />
            </div>
            <span className="text-gray-500 italic">{card.pinyin}</span>
            <p className="text-sm text-gray-700 dark:text-gray-200">{card.meaning}</p>
          </div>
        </div>
      </div>

      {flipped && (
        <div className="flex gap-3">
          <button onClick={() => next(false)} className="flex-1 py-3 rounded-xl bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-300 font-semibold hover:bg-red-100 transition-colors">
            ✗ Chưa nhớ
          </button>
          <button onClick={() => next(true)} className="flex-1 py-3 rounded-xl bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300 font-semibold hover:bg-emerald-100 transition-colors">
            ✓ Đã nhớ
          </button>
        </div>
      )}
    </div>
  )
}

// ============ QUIZ VIEW ============
function QuizView({ progress, onProgressUpdate }) {
  const [list, setList] = useState([])
  const [qIdx, setQIdx] = useState(0)
  const [quiz, setQuiz] = useState(null)
  const [selected, setSelected] = useState(null)
  const [score, setScore] = useState(0)
  const [done, setDone] = useState(false)
  const [levelFilter, setLevelFilter] = useState(1)
  const TOTAL = 10

  useEffect(() => {
    fetchHantuList({ level: levelFilter || undefined }).then((data) => {
      setList(data.sort(() => Math.random() - 0.5).slice(0, TOTAL))
      setQIdx(0)
      setQuiz(null)
      setSelected(null)
      setScore(0)
      setDone(false)
    })
  }, [levelFilter])

  useEffect(() => {
    if (!list.length || qIdx >= list.length) return
    fetchHantuQuiz(list[qIdx].id).then(setQuiz)
  }, [list, qIdx])

  const answer = (opt) => {
    if (selected) return
    setSelected(opt.id)
    if (quiz && opt.id === quiz.correct.id) {
      setScore((s) => s + 1)
      const p = progress[quiz.correct.id]
      saveHantuProgress(quiz.correct.id, Math.min((p?.score || 0) + 10, 100), (p?.reviewCount || 0) + 1).then(onProgressUpdate)
    }
  }

  const next = () => {
    if (qIdx + 1 >= list.length) { setDone(true); return; }
    setQIdx((i) => i + 1)
    setSelected(null)
    setQuiz(null)
  }

  if (done) return (
    <div className="py-20 text-center space-y-4 max-w-md mx-auto">
      <div className="text-5xl">{score >= 8 ? '🏆' : score >= 5 ? '👍' : '📚'}</div>
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Kết quả: {score}/{list.length}</h2>
      <p className="text-gray-500">{score >= 8 ? 'Xuất sắc!' : score >= 5 ? 'Khá tốt!' : 'Cần ôn thêm!'}</p>
      <button onClick={() => {
        setList(l => [...l].sort(() => Math.random() - 0.5))
        setQIdx(0); setSelected(null); setQuiz(null); setScore(0); setDone(false)
      }} className="btn-primary">Làm lại</button>
    </div>
  )

  return (
    <div className="max-w-md mx-auto space-y-4">
      <div className="flex items-center gap-3">
        <select value={levelFilter} onChange={(e) => setLevelFilter(Number(e.target.value))}
          className="px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm outline-none focus:border-primary">
          {LEVELS.map((l) => <option key={l.key} value={l.key}>{l.label}</option>)}
        </select>
        <div className="text-sm text-gray-400">{qIdx + 1}/{list.length} • ✓ {score}</div>
      </div>

      {!quiz ? (
        <div className="py-16 text-center text-gray-400">Đang tải câu hỏi...</div>
      ) : (
        <div className="card p-6 space-y-5">
          <div className="text-center">
            <div className="text-xs text-gray-400 mb-2">Chữ Hán này nghĩa là gì?</div>
            <div className="flex items-center justify-center gap-3">
              <span className="text-8xl leading-none" style={{ fontFamily: 'serif' }}>{quiz.correct.char}</span>
              <SpeakBtn text={quiz.correct.char} className="w-9 h-9" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {quiz.options.map((opt) => {
              let cls = 'p-3 rounded-xl border text-sm font-medium text-left transition-all '
              if (!selected) {
                cls += 'border-gray-200 dark:border-dark-border hover:border-primary hover:bg-primary/5 cursor-pointer text-gray-700 dark:text-gray-200'
              } else if (opt.id === quiz.correct.id) {
                cls += 'border-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300'
              } else if (opt.id === selected) {
                cls += 'border-red-400 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-300'
              } else {
                cls += 'border-gray-200 dark:border-dark-border opacity-50 text-gray-500'
              }
              return (
                <button key={opt.id} onClick={() => answer(opt)} className={cls}>
                  <div className="font-bold">{opt.hanViet}</div>
                  <div className="text-xs opacity-75 mt-0.5 line-clamp-2">{opt.meaning}</div>
                </button>
              )
            })}
          </div>
          {selected && (
            <div className="space-y-2">
              <div className={`text-center text-sm font-semibold ${selected === quiz.correct.id ? 'text-emerald-600' : 'text-red-500'}`}>
                {selected === quiz.correct.id ? '✓ Chính xác!' : `✗ Sai — đáp án: ${quiz.correct.hanViet}`}
              </div>
              <button onClick={next} className="w-full py-2.5 rounded-xl bg-primary text-white font-semibold hover:bg-primary-light transition-colors text-sm">
                {qIdx + 1 >= list.length ? 'Xem kết quả' : 'Câu tiếp →'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ============ MAIN PAGE ============
const TABS = [
  { key: 'list', label: '📋 Danh sách' },
  { key: 'flashcard', label: '🃏 Thẻ ghi nhớ' },
  { key: 'quiz', label: '📝 Kiểm tra' },
]

export default function ChineseCharPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [tab, setTab] = useState('list')
  const [selectedId, setSelectedId] = useState(id ? Number(id) : null)
  const [progress, setProgress] = useState({})
  const [progressLoaded, setProgressLoaded] = useState(false)

  const loadProgress = useCallback(async () => {
    try { setProgress(await fetchHantuProgress()) }
    catch { setProgress({}) }
    setProgressLoaded(true)
  }, [])

  useEffect(() => { loadProgress() }, [loadProgress])

  useEffect(() => {
    if (id) setSelectedId(Number(id))
    else setSelectedId(null)
  }, [id])

  const selectChar = (charId) => {
    setSelectedId(charId)
    navigate(`/additional/chinese/${charId}`)
  }

  const backToList = () => {
    setSelectedId(null)
    navigate('/additional/chinese')
  }

  if (!progressLoaded) return <div className="py-20 text-center text-gray-400">Đang tải...</div>

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 space-y-4">
      <div className="flex items-center gap-3">
        <span className="text-3xl">🈶</span>
        <div>
          <h1 className="font-display font-bold text-xl text-gray-900 dark:text-gray-100">Hán Tự Kinh Dịch</h1>
          <p className="text-sm text-gray-400">200 chữ Hán cốt lõi dành cho người học Kinh Dịch</p>
        </div>
      </div>

      {/* Tabs — chỉ hiện khi không có detail */}
      {!selectedId && (
        <div className="flex gap-1 border-b border-gray-200 dark:border-dark-border">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
                tab === t.key
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      )}

      {selectedId ? (
        <DetailView id={selectedId} onBack={backToList} progress={progress} onProgressUpdate={loadProgress} />
      ) : tab === 'list' ? (
        <ListView onSelect={selectChar} progress={progress} />
      ) : tab === 'flashcard' ? (
        <FlashcardView progress={progress} onProgressUpdate={loadProgress} />
      ) : (
        <QuizView progress={progress} onProgressUpdate={loadProgress} />
      )}
    </div>
  )
}
