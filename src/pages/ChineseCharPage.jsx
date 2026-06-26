import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useStore } from '../store'
import {
  fetchHantuList, fetchHantu, fetchHantuQuiz,
  fetchHantuProgress, fetchHantuStats, fetchDailyHantu,
  saveHantuProgress,
} from '../api'

// ---- Progress status ----
function getStatus(score, reviewCount) {
  if (!reviewCount) return 'new'
  if (score < 40) return 'learning'
  if (score < 75) return 'familiar'
  return 'mastered'
}
const STATUS = {
  new:      { icon: '🌱', label: 'Mới học',       cls: 'text-gray-400' },
  learning: { icon: '🍃', label: 'Đang ghi nhớ',  cls: 'text-blue-500' },
  familiar: { icon: '🌳', label: 'Đã quen',        cls: 'text-emerald-500' },
  mastered: { icon: '🏆', label: 'Thành thạo',     cls: 'text-amber-500' },
}

// ---- TTS button ----
function SpeakBtn({ text, className = '' }) {
  const [active, setActive] = useState(false)
  const speak = (e) => {
    e.stopPropagation()
    if (!window.speechSynthesis) return
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'zh-CN'; u.rate = 0.8
    u.onstart = () => setActive(true)
    u.onend = () => setActive(false)
    u.onerror = () => setActive(false)
    window.speechSynthesis.speak(u)
  }
  return (
    <button onClick={speak} title="Nghe phát âm"
      className={`inline-flex items-center justify-center rounded-full transition-colors shrink-0
        ${active ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-dark-card text-gray-500 hover:bg-primary/10 hover:text-primary'}
        ${className}`}>
      <span className="text-sm">{active ? '🔊' : '🔈'}</span>
    </button>
  )
}

// ============================================================
// LEARN FLOW — the core experience for a single character
// quiz → reveal → done
// ============================================================
function LearnFlow({ charId, progress, onComplete, showIT }) {
  const [step, setStep] = useState('quiz')   // quiz | reveal
  const [quiz, setQuiz] = useState(null)
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)  // id of chosen option
  const isCorrect = selected != null && quiz && selected === quiz.correct.id

  useEffect(() => {
    setStep('quiz'); setSelected(null); setLoading(true)
    Promise.all([fetchHantuQuiz(charId), fetchHantu(charId)])
      .then(([q, d]) => { setQuiz(q); setDetail(d) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [charId])

  const answer = async (optId) => {
    if (selected != null) return
    setSelected(optId)
    const correct = optId === quiz.correct.id
    const p = progress[charId] || {}
    const newRC = (p.reviewCount || 0) + 1
    const delta = correct ? 15 : -8
    const newScore = Math.max(0, Math.min(100, (p.score || 0) + delta))
    await saveHantuProgress(charId, newScore, newRC, correct)
    onComplete(correct)          // let parent know result for stats refresh
  }

  if (loading) return <div className="py-24 text-center text-gray-400 text-sm">Đang tải...</div>
  if (!quiz || !detail) return <div className="py-24 text-center text-red-400 text-sm">Lỗi tải dữ liệu</div>

  // ---- STEP: QUIZ ----
  if (step === 'quiz') return (
    <div className="max-w-md mx-auto space-y-5">
      <div className="card p-8 text-center space-y-3">
        <p className="text-xs text-gray-400 uppercase tracking-widest">Chữ này nghĩa là gì?</p>
        <div className="flex items-center justify-center gap-3">
          <span className="text-[96px] leading-none select-none" style={{ fontFamily: 'serif' }}>{detail.char}</span>
          <SpeakBtn text={detail.char} className="w-9 h-9" />
        </div>
        <p className="text-gray-400 italic text-lg">{detail.pinyin}</p>
      </div>

      <div className="grid grid-cols-2 gap-2.5">
        {quiz.options.map((opt) => {
          let cls = 'p-4 rounded-xl border-2 text-left transition-all '
          if (selected == null) {
            cls += 'border-gray-200 dark:border-dark-border hover:border-primary hover:bg-primary/5 cursor-pointer text-gray-700 dark:text-gray-200'
          } else if (opt.id === quiz.correct.id) {
            cls += 'border-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300'
          } else if (opt.id === selected) {
            cls += 'border-red-400 bg-red-50 dark:bg-red-900/20 text-red-500 dark:text-red-300'
          } else {
            cls += 'border-gray-100 dark:border-dark-border opacity-40 text-gray-400'
          }
          return (
            <button key={opt.id} onClick={() => answer(opt.id)} className={cls}>
              <div className="font-bold text-sm">{opt.hanViet}</div>
              <div className="text-xs opacity-70 mt-1 leading-snug line-clamp-2">{opt.meaning}</div>
            </button>
          )
        })}
      </div>

      {selected != null && (
        <div className="space-y-3">
          <p className={`text-center font-semibold ${isCorrect ? 'text-emerald-600' : 'text-red-500'}`}>
            {isCorrect ? '✓ Chính xác!' : `✗ Đáp án đúng: ${quiz.correct.hanViet} — ${quiz.correct.meaning}`}
          </p>
          <button onClick={() => setStep('reveal')}
            className="w-full py-3 rounded-xl bg-primary text-white font-semibold text-sm hover:bg-primary-light transition-colors">
            {isCorrect ? 'Tìm hiểu câu chuyện →' : 'Hiểu sâu hơn →'}
          </button>
        </div>
      )}
    </div>
  )

  // ---- STEP: REVEAL ----
  return (
    <div className="max-w-2xl mx-auto space-y-4">
      {/* Hero */}
      <div className="card p-6">
        <div className="flex items-start gap-6">
          <div className="text-center shrink-0">
            <span className="text-8xl leading-none" style={{ fontFamily: 'serif' }}>{detail.char}</span>
            <div className="mt-2">
              <SpeakBtn text={detail.char} className="w-8 h-8 mx-auto" />
            </div>
          </div>
          <div className="flex-1 space-y-1 pt-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{detail.hanViet}</h2>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                STATUS[getStatus(progress[charId]?.score, progress[charId]?.reviewCount)]?.cls
              }`}>
                {STATUS[getStatus(progress[charId]?.score, progress[charId]?.reviewCount)]?.icon}{' '}
                {STATUS[getStatus(progress[charId]?.score, progress[charId]?.reviewCount)]?.label}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg italic text-gray-400">{detail.pinyin}</span>
              <SpeakBtn text={detail.pinyin} className="w-6 h-6" />
            </div>
            <p className="text-gray-700 dark:text-gray-200">{detail.meaning}</p>
          </div>
        </div>
      </div>

      {/* Story */}
      {detail.story && (
        <div className="card p-5 border-l-4 border-primary/40">
          <div className="text-[10px] font-bold uppercase tracking-widest text-primary/60 mb-3">📖 Câu chuyện</div>
          <p className="text-gray-700 dark:text-gray-200 leading-relaxed whitespace-pre-line text-sm">{detail.story}</p>
        </div>
      )}

      {/* Kinh Dịch */}
      {detail.kinhDichContext && (
        <div className="card p-5">
          <div className="text-[10px] font-bold uppercase tracking-widest text-amber-600/70 mb-3">☯ Trong Kinh Dịch</div>
          <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">{detail.kinhDichContext}</p>
        </div>
      )}

      {/* Examples */}
      <div className={`grid gap-3 ${showIT && detail.itExample ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1'}`}>
        {detail.lifeExample && (
          <div className="card p-4">
            <div className="text-[10px] font-bold uppercase tracking-widest text-emerald-600/70 mb-2">🌱 Cuộc sống</div>
            <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">{detail.lifeExample}</p>
          </div>
        )}
        {showIT && detail.itExample && (
          <div className="card p-4">
            <div className="text-[10px] font-bold uppercase tracking-widest text-blue-600/70 mb-2">💻 Kỹ thuật</div>
            <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">{detail.itExample}</p>
          </div>
        )}
      </div>

      {/* Evolution */}
      {detail.evolution && (
        <div className="card p-4">
          <div className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-3">📜 Lịch sử chữ viết</div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {[['giaCoVan','甲骨文'],['kimVan','金文'],['tieuTrien','小篆'],['khaiThu','楷書']].map(([k, label]) =>
              detail.evolution[k] ? (
                <div key={k} className="bg-gray-50 dark:bg-dark-card rounded-lg p-3 text-center">
                  <div className="text-[10px] text-gray-400 mb-1.5">{label}</div>
                  <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed">{detail.evolution[k]}</p>
                </div>
              ) : null
            )}
          </div>
        </div>
      )}

      {/* Related */}
      {detail.relatedChars?.length > 0 && (
        <div className="card p-4">
          <div className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-3">🔗 Chữ liên quan</div>
          <div className="flex flex-wrap gap-2">
            {detail.relatedChars.map((r) => (
              <button key={r.id} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-dark-border hover:border-primary text-sm transition-colors">
                <span style={{ fontFamily: 'serif' }} className="text-xl">{r.char}</span>
                <span className="text-gray-600 dark:text-gray-300">{r.hanViet}</span>
                <SpeakBtn text={r.char} className="w-5 h-5" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================
// DAILY SECTION — Today's learning queue
// ============================================================
function DailySection({ progress, onLearn, onRefresh }) {
  const [daily, setDaily] = useState(null)
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)
  const [activeIdx, setActiveIdx] = useState(null)   // which card is being learned
  const [completed, setCompleted] = useState([])     // ids completed this session

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [d, s] = await Promise.all([fetchDailyHantu(), fetchHantuStats()])
      setDaily(d); setStats(s)
    } catch { setDaily({ due: [], new: [] }) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const queue = daily ? [...(daily.due || []), ...(daily.new || [])] : []
  const remaining = queue.filter(c => !completed.includes(c.id))

  const handleComplete = async () => {
    if (activeIdx == null) return
    setCompleted(p => [...p, queue[activeIdx].id])
    await onRefresh()
    setActiveIdx(null)
  }

  if (loading) return <div className="py-20 text-center text-gray-400 text-sm">Đang tải...</div>

  return (
    <div className="space-y-5 max-w-2xl mx-auto">
      {/* Stats row */}
      {stats && (
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Đã học', value: `${stats.totalLearned}/${stats.total}`, sub: 'chữ' },
            { label: 'Độ chính xác', value: `${stats.accuracy}%`, sub: '' },
            { label: 'Chuỗi học', value: `${stats.streak}`, sub: 'ngày' },
          ].map((s) => (
            <div key={s.label} className="card p-4 text-center">
              <div className="text-2xl font-bold text-primary">{s.value}<span className="text-sm font-normal text-gray-400 ml-1">{s.sub}</span></div>
              <div className="text-xs text-gray-400 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Learn flow overlay */}
      {activeIdx != null && activeIdx < queue.length && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <button onClick={() => setActiveIdx(null)} className="text-sm text-gray-400 hover:text-primary transition-colors">
              ← Quay lại
            </button>
            <div className="flex-1 h-1.5 bg-gray-100 dark:bg-dark-border rounded-full overflow-hidden">
              <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${(completed.length / queue.length) * 100}%` }} />
            </div>
            <span className="text-xs text-gray-400">{completed.length}/{queue.length}</span>
          </div>
          <LearnFlow
            charId={queue[activeIdx].id}
            progress={progress}
            showIT={onLearn}
            onComplete={() => {}}
          />
          <button onClick={handleComplete}
            className="w-full py-3 rounded-xl bg-primary text-white font-bold text-sm hover:bg-primary-light transition-colors mt-4">
            Tôi đã hiểu — Tiếp theo →
          </button>
        </div>
      )}

      {activeIdx == null && (
        <>
          {/* Daily queue */}
          {remaining.length > 0 ? (
            <div className="space-y-3">
              <h2 className="font-semibold text-gray-700 dark:text-gray-200">
                Hôm nay cần học <span className="text-primary">{remaining.length}</span> chữ
              </h2>
              {remaining.map((c, i) => {
                const p = progress[c.id] || {}
                const st = getStatus(p.score, p.reviewCount)
                const isNew = c.type === 'new'
                return (
                  <div key={c.id} className="card p-4 flex items-center gap-4">
                    <span className="text-5xl leading-none shrink-0" style={{ fontFamily: 'serif' }}>{c.char}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-800 dark:text-gray-100">{c.hanViet}</span>
                        <SpeakBtn text={c.char} className="w-6 h-6" />
                        <span className={`text-xs ${STATUS[st]?.cls}`}>{STATUS[st]?.icon} {isNew ? 'Chữ mới' : 'Ôn tập'}</span>
                      </div>
                      <div className="text-sm text-gray-400 italic">{c.pinyin}</div>
                    </div>
                    <button onClick={() => setActiveIdx(queue.indexOf(c))}
                      className="btn-primary text-sm shrink-0">
                      {isNew ? 'Học' : 'Ôn'}
                    </button>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="card p-8 text-center space-y-3">
              <div className="text-4xl">🎉</div>
              <h2 className="font-bold text-lg text-gray-800 dark:text-gray-100">Hoàn thành hôm nay!</h2>
              <p className="text-sm text-gray-400">Quay lại ngày mai để học thêm. Não sẽ củng cố ký ức trong lúc bạn ngủ.</p>
              {stats?.hardestChar && (
                <div className="mt-4 p-3 rounded-xl bg-gray-50 dark:bg-dark-card text-sm">
                  <span className="text-gray-500">Chữ cần ôn thêm:</span>
                  <span className="ml-2 font-bold">{stats.hardestChar.char} {stats.hardestChar.hanViet}</span>
                </div>
              )}
            </div>
          )}

          {/* Best/Hardest */}
          {stats && (stats.bestChar || stats.hardestChar) && (
            <div className="grid grid-cols-2 gap-3">
              {stats.bestChar && (
                <div className="card p-4 text-center">
                  <div className="text-xs text-gray-400 mb-1">🏆 Nhớ tốt nhất</div>
                  <div className="text-4xl" style={{ fontFamily: 'serif' }}>{stats.bestChar.char}</div>
                  <div className="text-sm font-medium mt-1">{stats.bestChar.hanViet}</div>
                </div>
              )}
              {stats.hardestChar && (
                <div className="card p-4 text-center">
                  <div className="text-xs text-gray-400 mb-1">💪 Cần ôn thêm</div>
                  <div className="text-4xl" style={{ fontFamily: 'serif' }}>{stats.hardestChar.char}</div>
                  <div className="text-sm font-medium mt-1">{stats.hardestChar.hanViet}</div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

// ============================================================
// FLASHCARD — Concept-first (hint on front, char on back)
// ============================================================
function FlashcardSection({ progress, onRefresh, showIT }) {
  const [list, setList] = useState([])
  const [idx, setIdx] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [done, setDone] = useState(false)
  const [levelFilter, setLevelFilter] = useState(1)

  useEffect(() => {
    fetchHantuList({ level: levelFilter || undefined }).then(data => {
      setList(data.sort(() => Math.random() - 0.5))
      setIdx(0); setFlipped(false); setDone(false)
    })
  }, [levelFilter])

  const card = list[idx]

  const next = async (knew) => {
    if (card) {
      const p = progress[card.id] || {}
      const rc = (p.reviewCount || 0) + (knew ? 1 : 0)
      const score = Math.max(0, Math.min(100, (p.score || 0) + (knew ? 12 : -6)))
      await saveHantuProgress(card.id, score, rc, knew)
      onRefresh()
    }
    if (idx + 1 >= list.length) { setDone(true); return }
    setIdx(i => i + 1); setFlipped(false)
  }

  if (!list.length) return <div className="py-16 text-center text-gray-400">Đang tải...</div>

  if (done) return (
    <div className="py-20 text-center space-y-4 max-w-sm mx-auto">
      <div className="text-5xl">🎉</div>
      <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Hoàn thành bộ thẻ!</h2>
      <p className="text-gray-400 text-sm">{list.length} thẻ đã ôn</p>
      <button onClick={() => { setList(l => [...l].sort(() => Math.random() - 0.5)); setIdx(0); setFlipped(false); setDone(false) }}
        className="btn-primary">Ôn lại từ đầu</button>
    </div>
  )

  const hintSide = card ? (
    <div className="space-y-3 text-center">
      <p className="text-xs text-gray-400 uppercase tracking-widest">Câu gợi ý</p>
      <p className="text-gray-700 dark:text-gray-200 text-base leading-relaxed italic">
        {card.kinhDichContext || card.meaning}
      </p>
      <p className="text-sm text-gray-400">Đây là chữ Hán nào?</p>
      <div className="text-7xl text-gray-200 dark:text-gray-700 select-none" style={{ fontFamily: 'serif' }}>?</div>
    </div>
  ) : null

  const answerSide = card ? (
    <div className="space-y-3 text-center">
      <div className="flex items-center justify-center gap-3">
        <span className="text-8xl leading-none" style={{ fontFamily: 'serif' }}>{card.char}</span>
        <SpeakBtn text={card.char} className="w-9 h-9" />
      </div>
      <div>
        <div className="text-xl font-bold text-gray-900 dark:text-gray-100">{card.hanViet}</div>
        <div className="text-gray-400 italic">{card.pinyin}</div>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-300">{card.meaning}</p>
    </div>
  ) : null

  return (
    <div className="max-w-md mx-auto space-y-4">
      <div className="flex items-center gap-3">
        <select value={levelFilter} onChange={e => setLevelFilter(Number(e.target.value))}
          className="px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm outline-none">
          <option value={0}>Tất cả</option>
          <option value={1}>Cấp 1 — 40 nền tảng</option>
          <option value={2}>Cấp 2 — 40 mở rộng</option>
          <option value={3}>Cấp 3 — 40 nâng cao</option>
          <option value={4}>Cấp 4 — 80 chuyên sâu</option>
        </select>
        <div className="flex-1 h-1.5 bg-gray-100 dark:bg-dark-border rounded-full overflow-hidden">
          <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${((idx + 1) / list.length) * 100}%` }} />
        </div>
        <span className="text-xs text-gray-400 shrink-0">{idx + 1}/{list.length}</span>
      </div>

      {/* Flip card */}
      <div style={{ perspective: '1000px' }} className="cursor-pointer select-none" onClick={() => setFlipped(f => !f)}>
        <div style={{
          position: 'relative', height: '280px',
          transformStyle: 'preserve-3d',
          transition: 'transform 0.5s cubic-bezier(.4,0,.2,1)',
          transform: flipped ? 'rotateY(180deg)' : 'rotateY(0)',
        }}>
          <div style={{ position: 'absolute', inset: 0, backfaceVisibility: 'hidden' }}
            className="card flex flex-col items-center justify-center p-8 gap-4">
            {hintSide}
            <p className="text-xs text-gray-300 dark:text-gray-600 mt-2">Nhấn để lật</p>
          </div>
          <div style={{ position: 'absolute', inset: 0, backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
            className="card flex flex-col items-center justify-center p-8 gap-4 bg-primary/5">
            {answerSide}
          </div>
        </div>
      </div>

      {flipped && (
        <div className="grid grid-cols-2 gap-3">
          <button onClick={() => next(false)}
            className="py-3 rounded-xl bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-300 font-semibold hover:bg-red-100 transition-colors text-sm">
            ✗ Chưa nhớ
          </button>
          <button onClick={() => next(true)}
            className="py-3 rounded-xl bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300 font-semibold hover:bg-emerald-100 transition-colors text-sm">
            ✓ Đã nhớ
          </button>
        </div>
      )}
    </div>
  )
}

// ============================================================
// CATALOG — All 200 chars, no spoilers
// ============================================================
const TOPICS = [
  { k: '', l: 'Tất cả chủ đề' },
  { k: 'kinhDich', l: '☯ Kinh Dịch' },
  { k: 'batQua', l: '☰ Bát Quái' },
  { k: 'thienNhien', l: '🌿 Thiên Nhiên' },
  { k: 'thoiGian', l: '🕐 Thời Gian' },
  { k: 'coban', l: '🔤 Cơ Bản' },
  { k: 'conNguoi', l: '👤 Con Người' },
  { k: 'giaDinh', l: '👨‍👩‍👧 Gia Đình' },
  { k: 'sodem', l: '🔢 Số Đếm' },
  { k: 'hanhDong', l: '⚡ Hành Động' },
  { k: 'trangThai', l: '📊 Trạng Thái' },
  { k: 'nguHanh', l: '🌊 Ngũ Hành' },
  { k: 'phamChat', l: '✨ Phẩm Chất' },
  { k: 'vuTru', l: '🌌 Vũ Trụ' },
  { k: 'tenQue', l: '📖 Tên Quẻ' },
]

function CatalogSection({ progress, onSelect }) {
  const [list, setList] = useState([])
  const [loading, setLoading] = useState(true)
  const [levelFilter, setLevelFilter] = useState(0)
  const [topicFilter, setTopicFilter] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try { setList(await fetchHantuList({ level: levelFilter || undefined, topic: topicFilter || undefined, search: search || undefined })) }
    catch { setList([]) }
    finally { setLoading(false) }
  }, [levelFilter, topicFilter, search])
  useEffect(() => { load() }, [load])

  const filtered = statusFilter
    ? list.filter(h => {
        const p = progress[h.id] || {}
        return getStatus(p.score, p.reviewCount) === statusFilter
      })
    : list

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="🔍 Tìm chữ, pinyin..."
          className="flex-1 min-w-[140px] px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm outline-none focus:border-primary" />
        <select value={levelFilter} onChange={e => setLevelFilter(Number(e.target.value))}
          className="px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm outline-none">
          <option value={0}>Tất cả cấp</option>
          <option value={1}>Cấp 1</option><option value={2}>Cấp 2</option>
          <option value={3}>Cấp 3</option><option value={4}>Cấp 4</option>
        </select>
        <select value={topicFilter} onChange={e => setTopicFilter(e.target.value)}
          className="px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm outline-none">
          {TOPICS.map(t => <option key={t.k} value={t.k}>{t.l}</option>)}
        </select>
      </div>

      {/* Status filter pills */}
      <div className="flex flex-wrap gap-2">
        {['', 'new', 'learning', 'familiar', 'mastered'].map(s => (
          <button key={s} onClick={() => setStatusFilter(s)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${statusFilter === s ? 'border-primary bg-primary/10 text-primary' : 'border-gray-200 dark:border-dark-border text-gray-500 hover:border-primary/50'}`}>
            {s ? `${STATUS[s].icon} ${STATUS[s].label}` : 'Tất cả'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="py-16 text-center text-gray-400">Đang tải...</div>
      ) : (
        <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-2">
          {filtered.map(h => {
            const p = progress[h.id] || {}
            const st = getStatus(p.score, p.reviewCount)
            return (
              <button key={h.id} onClick={() => onSelect(h.id)}
                className="group relative card p-2.5 flex flex-col items-center gap-1 hover:border-primary transition-all cursor-pointer">
                <span className="text-3xl leading-none" style={{ fontFamily: 'serif' }}>{h.char}</span>
                <span className="text-[9px] text-gray-400">{h.hanViet}</span>
                <span className={`text-[10px] ${STATUS[st].cls}`}>{STATUS[st].icon}</span>
                <div onClick={e => e.stopPropagation()} className="absolute top-1 right-1 opacity-0 group-hover:opacity-100">
                  <SpeakBtn text={h.char} className="w-5 h-5" />
                </div>
              </button>
            )
          })}
          {filtered.length === 0 && <div className="col-span-full py-10 text-center text-gray-400 text-sm">Không tìm thấy chữ nào</div>}
        </div>
      )}
    </div>
  )
}

// ============================================================
// DETAIL — Full detail for a single char (accessed from catalog)
// ============================================================
function DetailSection({ charId, onBack, progress, onRefresh, showIT }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [learning, setLearning] = useState(false)

  useEffect(() => {
    setLoading(true); setLearning(false)
    fetchHantu(charId).then(setData).catch(() => setData(null)).finally(() => setLoading(false))
  }, [charId])

  if (loading) return <div className="py-20 text-center text-gray-400">Đang tải...</div>
  if (!data) return <div className="py-20 text-center text-gray-400">Không tìm thấy chữ</div>

  const p = progress[charId] || {}
  const st = getStatus(p.score, p.reviewCount)

  if (learning) return (
    <div className="space-y-4">
      <button onClick={() => setLearning(false)} className="text-sm text-gray-400 hover:text-primary transition-colors">← Chi tiết</button>
      <LearnFlow charId={charId} progress={progress} showIT={showIT} onComplete={() => onRefresh()} />
      <button onClick={() => { onRefresh(); setLearning(false) }}
        className="w-full py-3 rounded-xl bg-primary text-white font-bold text-sm hover:bg-primary-light transition-colors mt-2">
        Tôi đã hiểu →
      </button>
    </div>
  )

  return (
    <div className="space-y-4 max-w-2xl mx-auto">
      <button onClick={onBack} className="text-sm text-gray-400 hover:text-primary transition-colors">← Danh sách</button>

      {/* Hero */}
      <div className="card p-6 flex items-start gap-6">
        <div className="text-center shrink-0">
          <span className="text-8xl leading-none" style={{ fontFamily: 'serif' }}>{data.char}</span>
          <div className="mt-2"><SpeakBtn text={data.char} className="w-8 h-8 mx-auto" /></div>
        </div>
        <div className="flex-1 space-y-1.5 pt-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{data.hanViet}</h1>
            <span className={`text-xs font-medium ${STATUS[st].cls}`}>{STATUS[st].icon} {STATUS[st].label}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="italic text-gray-400 text-lg">{data.pinyin}</span>
            <SpeakBtn text={data.pinyin} className="w-6 h-6" />
          </div>
          <p className="text-gray-700 dark:text-gray-200">{data.meaning}</p>
          {p.reviewCount > 0 && (
            <div className="flex gap-3 text-xs text-gray-400">
              <span>✓ {p.correctCount || 0} đúng</span>
              <span>✗ {p.incorrectCount || 0} sai</span>
              <span>Đã ôn {p.reviewCount} lần</span>
            </div>
          )}
        </div>
      </div>

      <button onClick={() => setLearning(true)}
        className="w-full py-3 rounded-xl bg-primary text-white font-bold text-sm hover:bg-primary-light transition-colors">
        {p.reviewCount > 0 ? '🔁 Ôn lại chữ này' : '📖 Học chữ này'}
      </button>

      {data.story && (
        <div className="card p-5 border-l-4 border-primary/40">
          <div className="text-[10px] font-bold uppercase tracking-widest text-primary/60 mb-3">📖 Câu chuyện</div>
          <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed whitespace-pre-line">{data.story}</p>
        </div>
      )}
      {data.kinhDichContext && (
        <div className="card p-5">
          <div className="text-[10px] font-bold uppercase tracking-widest text-amber-600/70 mb-3">☯ Trong Kinh Dịch</div>
          <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">{data.kinhDichContext}</p>
        </div>
      )}
      <div className={`grid gap-3 ${showIT && data.itExample ? 'sm:grid-cols-2' : ''}`}>
        {data.lifeExample && (
          <div className="card p-4">
            <div className="text-[10px] font-bold uppercase tracking-widest text-emerald-600/70 mb-2">🌱 Cuộc sống</div>
            <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">{data.lifeExample}</p>
          </div>
        )}
        {showIT && data.itExample && (
          <div className="card p-4">
            <div className="text-[10px] font-bold uppercase tracking-widest text-blue-600/70 mb-2">💻 Kỹ thuật</div>
            <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">{data.itExample}</p>
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================================
// MAIN PAGE
// ============================================================
const TABS = [
  { key: 'daily', label: '📅 Hôm nay' },
  { key: 'flashcard', label: '🃏 Thẻ nhớ' },
  { key: 'catalog', label: '📚 200 chữ' },
]

export default function ChineseCharPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { lens } = useStore()
  const showIT = lens === 'tech'

  const [tab, setTab] = useState('daily')
  const [selectedId, setSelectedId] = useState(id ? Number(id) : null)
  const [progress, setProgress] = useState({})
  const [loaded, setLoaded] = useState(false)

  const loadProgress = useCallback(async () => {
    try { setProgress(await fetchHantuProgress()) } catch { setProgress({}) }
    setLoaded(true)
  }, [])

  useEffect(() => { loadProgress() }, [loadProgress])
  useEffect(() => { if (id) setSelectedId(Number(id)); else setSelectedId(null) }, [id])

  const selectChar = (cid) => { setSelectedId(cid); navigate(`/additional/chinese/${cid}`) }
  const backToList = () => { setSelectedId(null); navigate('/additional/chinese') }

  if (!loaded) return <div className="py-20 text-center text-gray-400">Đang tải...</div>

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🈶</span>
          <div>
            <h1 className="font-display font-bold text-xl text-gray-900 dark:text-gray-100">Hán Tự Kinh Dịch</h1>
            <p className="text-xs text-gray-400">Học nhận diện 200 chữ Hán cốt lõi — không cần ghi nhớ, chỉ cần gặp đủ nhiều lần</p>
          </div>
        </div>
        {!showIT && (
          <div className="text-xs text-gray-400 bg-gray-50 dark:bg-dark-card px-2 py-1 rounded-lg">
            💡 Đổi lens → <span className="font-medium text-blue-500">💻 CNTT</span> để xem ví dụ kỹ thuật
          </div>
        )}
      </div>

      {selectedId ? (
        <DetailSection
          charId={selectedId} onBack={backToList}
          progress={progress} onRefresh={loadProgress} showIT={showIT}
        />
      ) : (
        <>
          {/* Tabs */}
          <div className="flex gap-1 border-b border-gray-200 dark:border-dark-border">
            {TABS.map(t => (
              <button key={t.key} onClick={() => setTab(t.key)}
                className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
                  tab === t.key ? 'border-primary text-primary' : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                }`}>
                {t.label}
              </button>
            ))}
          </div>

          {tab === 'daily' && <DailySection progress={progress} onLearn={showIT} onRefresh={loadProgress} />}
          {tab === 'flashcard' && <FlashcardSection progress={progress} onRefresh={loadProgress} showIT={showIT} />}
          {tab === 'catalog' && <CatalogSection progress={progress} onSelect={selectChar} />}
        </>
      )}
    </div>
  )
}
