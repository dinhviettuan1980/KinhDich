import { useEffect, useRef, useState } from 'react'

// Nút đọc nội dung bằng Web Speech API (text-to-speech), giọng tiếng Việt.
// `getText` là hàm trả về chuỗi cần đọc (gọi lúc bấm để lấy nội dung mới nhất).

const synth = typeof window !== 'undefined' ? window.speechSynthesis : null

// Chọn giọng tiếng Việt nếu trình duyệt có
function pickViVoice() {
  if (!synth) return null
  const voices = synth.getVoices()
  return (
    voices.find((v) => v.lang === 'vi-VN') ||
    voices.find((v) => v.lang && v.lang.toLowerCase().startsWith('vi')) ||
    null
  )
}

// Tách thành câu để né lỗi cắt giọng khi văn bản dài (giới hạn ~15s ở vài trình duyệt)
function chunk(text) {
  return text
    .replace(/\s+/g, ' ')
    .split(/(?<=[.!?…:;\n])\s+/)
    .map((s) => s.trim())
    .filter(Boolean)
}

export default function ReadAloudButton({ getText, className = '' }) {
  const [state, setState] = useState('idle') // idle | playing | paused
  const queueRef = useRef([])
  const idxRef = useRef(0)

  // Dừng hẳn khi rời trang
  useEffect(() => () => { if (synth) synth.cancel() }, [])

  if (!synth) return null

  const speakNext = () => {
    const q = queueRef.current
    if (idxRef.current >= q.length) { setState('idle'); return }
    const u = new SpeechSynthesisUtterance(q[idxRef.current])
    u.lang = 'vi-VN'
    const voice = pickViVoice()
    if (voice) u.voice = voice
    u.rate = 0.95
    u.pitch = 1
    u.onend = () => { idxRef.current += 1; speakNext() }
    u.onerror = () => { setState('idle') }
    synth.speak(u)
  }

  const start = () => {
    synth.cancel()
    const text = (getText() || '').trim()
    if (!text) return
    queueRef.current = chunk(text)
    idxRef.current = 0
    setState('playing')
    speakNext()
  }

  const toggle = () => {
    if (state === 'idle') { start(); return }
    if (state === 'playing') { synth.pause(); setState('paused'); return }
    if (state === 'paused') { synth.resume(); setState('playing') }
  }

  const stop = () => { synth.cancel(); idxRef.current = queueRef.current.length; setState('idle') }

  const label = state === 'idle' ? '🔊 Nghe đọc' : state === 'playing' ? '⏸ Tạm dừng' : '▶ Tiếp tục'

  return (
    <div className={`inline-flex items-center gap-1 ${className}`}>
      <button
        onClick={toggle}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary/10 text-primary dark:text-primary-light text-sm font-medium hover:bg-primary/20 transition-colors"
        title="Đọc nội dung bài học"
      >
        {label}
      </button>
      {state !== 'idle' && (
        <button
          onClick={stop}
          className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 dark:bg-dark-card text-gray-500 hover:bg-gray-200 dark:hover:bg-dark-border transition-colors text-sm"
          title="Dừng"
        >
          ⏹
        </button>
      )}
    </div>
  )
}
