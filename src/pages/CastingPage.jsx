import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import FullHexagramSVG from '../components/FullHexagramSVG'
import CoinAnimation from '../components/CoinAnimation'
import { computeHexagrams, TRIGRAM_SHORT, TRIGRAM_ELEMENT, getHexagramById } from '../data/hexagrams'
import { getUserId } from '../api'

// --- Coin toss logic ---
// 3 coins: heads=3, tails=2; sum → line value
function tossCoins() {
  const coins = [
    Math.random() < 0.5 ? 3 : 2,
    Math.random() < 0.5 ? 3 : 2,
    Math.random() < 0.5 ? 3 : 2,
  ]
  const sum = coins.reduce((a, b) => a + b, 0)
  // 6=âm động, 7=dương tĩnh, 8=âm tĩnh, 9=dương động
  return { coins, value: sum }
}

function lineLabel(v) {
  if (v === 6) return { symbol: '- x -', desc: 'Âm động (biến)', color: 'text-amber-500 dark:text-amber-400' }
  if (v === 7) return { symbol: '———', desc: 'Dương tĩnh', color: 'text-gray-700 dark:text-gray-200' }
  if (v === 8) return { symbol: '- -', desc: 'Âm tĩnh', color: 'text-gray-700 dark:text-gray-200' }
  if (v === 9) return { symbol: '——o', desc: 'Dương động (biến)', color: 'text-amber-500 dark:text-amber-400' }
  return { symbol: '?', desc: '', color: '' }
}

// CoinAnim đã chuyển sang CoinAnimation.jsx

// --- Steps ---
const STEPS = {
  INTRO: 'intro',
  QUESTION: 'question',
  CASTING: 'casting',
  RESULT: 'result',
  NOTE: 'note',
  DONE: 'done',
}

export default function CastingPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(STEPS.INTRO)
  const [question, setQuestion] = useState('')
  const [lines, setLines] = useState([])           // 6 values so far
  const [pendingToss, setPendingToss] = useState(null)  // coin result being animated
  const [result, setResult] = useState(null)       // computeHexagrams output
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const inputRef = useRef()

  const currentLineNum = lines.length + 1  // 1-based, which line we're about to toss

  function startCasting() {
    if (!question.trim()) return
    setStep(STEPS.CASTING)
  }

  function handleToss() {
    const r = tossCoins()
    setPendingToss(r)
  }

  function handleCoinDone() {
    const newLines = [...lines, pendingToss.value]
    setPendingToss(null)
    if (newLines.length === 6) {
      const r = computeHexagrams(newLines)
      setLines(newLines)
      setResult(r)
      setStep(STEPS.RESULT)
    } else {
      setLines(newLines)
    }
  }

  async function handleSave() {
    setSaving(true)
    try {
      const userId = getUserId()
      await fetch('/kinhdich/castings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          question: question.trim(),
          originalHexagram: result.original.id,
          changedHexagram: result.changed?.id || null,
          movingLines: JSON.stringify(result.movingLines),
          linesData: JSON.stringify(lines),
          note: note.trim(),
        }),
      })
      setStep(STEPS.DONE)
    } catch (e) {
      console.error(e)
    } finally {
      setSaving(false)
    }
  }

  function reset() {
    setStep(STEPS.INTRO)
    setQuestion('')
    setLines([])
    setPendingToss(null)
    setResult(null)
    setNote('')
  }

  // ---- Render ----
  if (step === STEPS.INTRO) return (
    <div className="max-w-xl mx-auto px-4 py-10 space-y-6 animate-fade-in">
      <div className="text-center space-y-2">
        <div className="text-5xl">☯</div>
        <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-gray-100">Gieo Quẻ Học Tập</h1>
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          Trải nghiệm thực hành tung đồng xu để hiểu <strong>cơ chế hình thành quẻ</strong> trong Kinh Dịch.
        </p>
      </div>
      <div className="card p-4 space-y-3 text-sm text-gray-600 dark:text-gray-300">
        <div className="font-semibold text-gray-800 dark:text-gray-100">Cách hoạt động:</div>
        <ul className="space-y-1.5 list-disc list-inside">
          <li>Tung 3 đồng xu 6 lần → 6 hào → 1 quẻ</li>
          <li>Đồng sấp = 2, đồng ngửa = 3</li>
          <li>Tổng 6 = Âm động · 7 = Dương tĩnh · 8 = Âm tĩnh · 9 = Dương động</li>
          <li>Hào động tạo ra <strong>quẻ biến</strong></li>
        </ul>
        <div className="pt-1 text-xs text-amber-600 dark:text-amber-400 font-medium">
          ⚠️ Đây là công cụ học Kinh Dịch — không phải bói toán
        </div>
      </div>
      <button
        className="w-full py-3 rounded-xl bg-primary text-white font-semibold text-base hover:bg-primary-light transition-colors"
        onClick={() => setStep(STEPS.QUESTION)}
      >
        Bắt đầu gieo quẻ →
      </button>
    </div>
  )

  if (step === STEPS.QUESTION) return (
    <div className="max-w-xl mx-auto px-4 py-10 space-y-6 animate-fade-in">
      <h2 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">Chủ đề suy ngẫm</h2>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Ghi lại chủ đề bạn muốn suy nghĩ khi học quẻ này (ví dụ: "Cách tiếp cận dự án mới").
      </p>
      <textarea
        ref={inputRef}
        value={question}
        onChange={e => setQuestion(e.target.value)}
        placeholder="Chủ đề suy ngẫm của bạn…"
        className="w-full rounded-xl border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-gray-800 dark:text-gray-100 p-3 text-sm resize-none h-24 focus:outline-none focus:ring-2 focus:ring-primary"
        maxLength={200}
        autoFocus
      />
      <div className="flex gap-3">
        <button onClick={() => setStep(STEPS.INTRO)} className="flex-1 py-2.5 rounded-xl border border-gray-200 dark:border-dark-border text-gray-600 dark:text-gray-300 text-sm font-medium hover:bg-gray-50 dark:hover:bg-dark-card">
          Quay lại
        </button>
        <button
          onClick={startCasting}
          disabled={!question.trim()}
          className="flex-1 py-2.5 rounded-xl bg-primary text-white font-semibold text-sm hover:bg-primary-light transition-colors disabled:opacity-40"
        >
          Tiếp tục →
        </button>
      </div>
    </div>
  )

  if (step === STEPS.CASTING) return (
    <div className="max-w-xl mx-auto px-4 py-8 space-y-6 animate-fade-in">
      <div className="text-center">
        <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Hào {currentLineNum} / 6</div>
        <h2 className="text-lg font-display font-bold text-gray-900 dark:text-gray-100 mt-1">
          {currentLineNum <= 3 ? 'Hạ quái' : 'Thượng quái'} — Hào {currentLineNum}
        </h2>
      </div>

      {/* Progress dots */}
      <div className="flex justify-center gap-2">
        {[1,2,3,4,5,6].map(n => (
          <div key={n} className={`w-2.5 h-2.5 rounded-full transition-colors ${
            n < currentLineNum ? 'bg-primary' : n === currentLineNum ? 'bg-amber-400 animate-pulse' : 'bg-gray-200 dark:bg-dark-border'
          }`} />
        ))}
      </div>

      {/* Lines so far */}
      {lines.length > 0 && (
        <div className="flex flex-col items-center gap-2">
          <div className="text-xs text-gray-400 mb-1">Các hào đã tung (từ dưới lên):</div>
          {[...lines].reverse().map((v, i) => {
            const lbl = lineLabel(v)
            const lineNum = lines.length - i
            return (
              <div key={i} className={`flex items-center gap-3 text-sm font-mono ${lbl.color}`}>
                <span className="w-4 text-xs text-gray-400">H{lineNum}</span>
                <span className="w-12 text-center tracking-widest">{lbl.symbol}</span>
                <span className="text-xs">{lbl.desc}</span>
              </div>
            )
          })}
        </div>
      )}

      {/* Coin animation or toss button */}
      {pendingToss ? (
        <CoinAnimation result={pendingToss} onDone={handleCoinDone} />
      ) : (
        <div className="flex flex-col items-center gap-4">
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
            Tập trung vào chủ đề "<em>{question}</em>", rồi nhấn để tung 3 đồng xu.
          </p>
          <button
            onClick={handleToss}
            className="px-8 py-3 rounded-full bg-amber-500 hover:bg-amber-600 text-white font-bold text-base shadow-lg transition-all active:scale-95"
          >
            Tung đồng xu
          </button>
        </div>
      )}
    </div>
  )

  if (step === STEPS.RESULT && result) {
    const { original, changed, movingLines, lines: allLines } = result
    const hasMoving = movingLines.length > 0

    // Calculate changed hexagram lines for display
    const changedLinesArr = hasMoving
      ? allLines.map(v => v === 9 ? 8 : v === 6 ? 7 : v)
      : null

    return (
      <div className="max-w-2xl mx-auto px-4 py-8 space-y-8 animate-fade-in">
        <h2 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100 text-center">Kết quả Gieo Quẻ</h2>

        {/* Hexagram display */}
        <div className={`grid gap-8 ${hasMoving ? 'grid-cols-2' : 'grid-cols-1 max-w-xs mx-auto'}`}>
          {/* Original */}
          <div className="flex flex-col items-center gap-3">
            <div className="text-xs font-bold uppercase tracking-wider text-gray-400">Quẻ chính</div>
            <FullHexagramSVG lines={allLines} movingLines={movingLines} size={1.5} />
            <div className="text-center">
              <div className="font-display font-bold text-lg text-gray-900 dark:text-gray-100">
                {original.id}. {original.name}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {TRIGRAM_ELEMENT[result.upperTrigram]} / {TRIGRAM_ELEMENT[result.lowerTrigram]}
              </div>
            </div>
          </div>

          {/* Changed */}
          {hasMoving && changed && (
            <div className="flex flex-col items-center gap-3">
              <div className="text-xs font-bold uppercase tracking-wider text-amber-500">Quẻ biến</div>
              <FullHexagramSVG lines={changedLinesArr} movingLines={[]} size={1.5} />
              <div className="text-center">
                <div className="font-display font-bold text-lg text-gray-900 dark:text-gray-100">
                  {changed.id}. {changed.name}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {TRIGRAM_SHORT[result.changedUpper]} / {TRIGRAM_SHORT[result.changedLower]}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Moving lines */}
        {hasMoving && (
          <div className="card p-4 space-y-2">
            <div className="text-sm font-semibold text-amber-600 dark:text-amber-400">Hào động (biến)</div>
            <div className="flex flex-wrap gap-2">
              {movingLines.map(n => (
                <span key={n} className="px-2.5 py-1 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 text-xs font-bold">
                  Hào {n}
                </span>
              ))}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Hào {movingLines.join(', ')} biến đổi tạo ra quẻ {changed?.name || ''}
            </p>
          </div>
        )}

        {/* Educational meaning */}
        <div className="space-y-3">
          <div className="text-sm font-semibold text-gray-700 dark:text-gray-200">Ý nghĩa giáo dục</div>
          <div className="card p-4 space-y-2">
            <div className="font-semibold text-gray-800 dark:text-gray-100 text-sm">{original.name}</div>
            <p className="text-sm text-gray-600 dark:text-gray-300">{original.shortMeaning}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">{original.lifeMeaning}</p>
          </div>
          {hasMoving && changed && (
            <div className="card p-4 space-y-2 border-l-2 border-amber-400">
              <div className="font-semibold text-gray-800 dark:text-gray-100 text-sm">{changed.name} (quẻ biến)</div>
              <p className="text-sm text-gray-600 dark:text-gray-300">{changed.shortMeaning}</p>
            </div>
          )}
        </div>

        {/* Chủ đề */}
        <div className="text-xs text-gray-400 bg-gray-50 dark:bg-dark-card rounded-lg px-3 py-2">
          Chủ đề suy ngẫm: <em>"{question}"</em>
        </div>

        {/* 6 lines breakdown */}
        <div className="space-y-2">
          <div className="text-sm font-semibold text-gray-700 dark:text-gray-200">Chi tiết 6 hào</div>
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            {allLines.map((v, i) => {
              const lbl = lineLabel(v)
              return (
                <div key={i} className={`card px-3 py-2 flex items-center gap-2 ${lbl.color}`}>
                  <span className="w-8 text-gray-400 text-xs">H{i+1}</span>
                  <span className="tracking-widest">{lbl.symbol}</span>
                  <span className="text-gray-500 dark:text-gray-400 text-[10px]">{lbl.desc}</span>
                </div>
              )
            })}
          </div>
        </div>

        <div className="flex flex-col gap-3 pt-2">
          <button
            onClick={() => setStep(STEPS.NOTE)}
            className="w-full py-3 rounded-xl bg-primary text-white font-semibold hover:bg-primary-light transition-colors"
          >
            Ghi chú & Lưu quẻ →
          </button>
          <button
            onClick={reset}
            className="w-full py-2.5 rounded-xl border border-gray-200 dark:border-dark-border text-gray-600 dark:text-gray-300 text-sm font-medium hover:bg-gray-50 dark:hover:bg-dark-card"
          >
            Gieo quẻ mới
          </button>
        </div>
      </div>
    )
  }

  if (step === STEPS.NOTE) return (
    <div className="max-w-xl mx-auto px-4 py-8 space-y-6 animate-fade-in">
      <h2 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">Ghi chú suy ngẫm</h2>
      <div className="text-xs text-gray-400">
        Quẻ: <strong>{result?.original?.name}</strong>
        {result?.changed && <> → <strong>{result.changed.name}</strong></>}
      </div>
      <textarea
        value={note}
        onChange={e => setNote(e.target.value)}
        placeholder="Điều bạn học được từ quẻ này là gì? Liên hệ thế nào với chủ đề suy ngẫm?"
        className="w-full rounded-xl border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-gray-800 dark:text-gray-100 p-3 text-sm resize-none h-32 focus:outline-none focus:ring-2 focus:ring-primary"
        maxLength={500}
        autoFocus
      />
      <div className="flex gap-3">
        <button onClick={() => setStep(STEPS.RESULT)} className="flex-1 py-2.5 rounded-xl border border-gray-200 dark:border-dark-border text-gray-600 dark:text-gray-300 text-sm font-medium hover:bg-gray-50 dark:hover:bg-dark-card">
          Xem lại
        </button>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex-1 py-2.5 rounded-xl bg-primary text-white font-semibold text-sm hover:bg-primary-light transition-colors disabled:opacity-50"
        >
          {saving ? 'Đang lưu…' : 'Lưu quẻ →'}
        </button>
      </div>
      <button onClick={() => { setStep(STEPS.DONE); setNote('') }} className="w-full text-xs text-gray-400 hover:underline">
        Bỏ qua, không lưu
      </button>
    </div>
  )

  if (step === STEPS.DONE) return (
    <div className="max-w-xl mx-auto px-4 py-16 flex flex-col items-center gap-6 animate-fade-in text-center">
      <div className="text-6xl">✨</div>
      <h2 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">Đã lưu quẻ thành công!</h2>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Quẻ <strong>{result?.original?.name}</strong> đã được ghi vào lịch sử học tập của bạn.
      </p>
      <div className="flex flex-col gap-3 w-full max-w-xs">
        <button onClick={reset} className="w-full py-3 rounded-xl bg-primary text-white font-semibold hover:bg-primary-light transition-colors">
          Gieo quẻ mới
        </button>
        <button onClick={() => navigate('/casting-history')} className="w-full py-2.5 rounded-xl border border-gray-200 dark:border-dark-border text-gray-600 dark:text-gray-300 text-sm font-medium hover:bg-gray-50 dark:hover:bg-dark-card">
          Xem lịch sử
        </button>
      </div>
    </div>
  )

  return null
}
