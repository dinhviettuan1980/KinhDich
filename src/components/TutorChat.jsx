import { useState, useRef, useEffect } from 'react'
import { streamTutor } from '../api'

const TOPIC_CFG = {
  kinhdich: {
    avatar: '☯',
    greeting: 'Xin chào! Tôi là AI Tutor Kinh Dịch. Bạn có thể hỏi tôi bất kỳ điều gì về Kinh Dịch — từ khái niệm cơ bản đến ứng dụng thực tế. 🙏',
    placeholder: 'Hỏi về Kinh Dịch...',
    showMode: true,
    suggested: [
      'Tại sao 6 hào lại cho ra 64 quẻ?',
      'Âm Dương khác gì tốt xấu?',
      'Kinh Dịch có thể áp dụng vào Agile không?',
      'Tại sao người xưa lại dùng 3 đồng xu?',
      'Bát Quái liên quan gì đến hệ nhị phân không?',
    ],
  },
  vankhan: {
    avatar: '🙏',
    greeting: 'Xin chào! Tôi là trợ lý Văn khấn. Bạn có thể hỏi về các bài văn khấn đền, chùa, tại nhà, cầu nguyện — cách sắm lễ, dịp dùng, hoặc xin nguyên văn một bài. 🪷',
    placeholder: 'Hỏi về văn khấn, đền chùa, cách cúng lễ...',
    showMode: false,
    suggested: [
      'Văn khấn ban Công Đồng đọc thế nào?',
      'Cho tôi bài văn khấn Thần Tài Thổ Địa',
      'Đi lễ chùa cầu bình an thì khấn ra sao?',
      'Văn khấn gia tiên ngày giỗ',
      'Khấn ở đền Đức Thánh Trần cần sắm lễ gì?',
    ],
  },
}

function Message({ role, content, streaming, avatar = '☯', sources }) {
  const isUser = role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-sm mr-2 flex-shrink-0 mt-1">
          {avatar}
        </div>
      )}
      <div
        className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-primary text-white rounded-br-sm'
            : 'card rounded-bl-sm text-gray-800 dark:text-gray-200'
        } ${streaming ? 'cursor-blink' : ''}`}
      >
        {content || (streaming ? '' : '...')}
        {!isUser && !streaming && sources && sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-200 dark:border-dark-border">
            <div className="text-[11px] text-gray-400 dark:text-gray-500 mb-1">📚 Nguồn tham khảo:</div>
            <div className="flex flex-wrap gap-1">
              {sources.map((s, i) => (
                <span key={i} className="text-[11px] px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function TutorChat({ topic = 'kinhdich' }) {
  const cfg = TOPIC_CFG[topic] || TOPIC_CFG.kinhdich
  const [messages, setMessages] = useState([
    { role: 'assistant', content: cfg.greeting },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState('explain') // 'explain' | 'socratic'
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return
    setInput('')

    const history = messages.slice(1).map((m) => ({ role: m.role, content: m.content }))
    setMessages((prev) => [...prev, { role: 'user', content: msg }])
    setLoading(true)

    const aiIdx = messages.length + 1
    setMessages((prev) => [...prev, { role: 'assistant', content: '', streaming: true }])

    try {
      let full = ''
      let srcs = []
      for await (const part of streamTutor(msg, history, mode, topic)) {
        if (part.text) {
          full += part.text
          setMessages((prev) =>
            prev.map((m, i) => (i === aiIdx ? { ...m, content: full } : m))
          )
        } else if (part.sources) {
          srcs = part.sources
          setMessages((prev) =>
            prev.map((m, i) => (i === aiIdx ? { ...m, sources: srcs } : m))
          )
        }
      }
      setMessages((prev) =>
        prev.map((m, i) => (i === aiIdx ? { ...m, streaming: false, sources: srcs } : m))
      )
    } catch (err) {
      setMessages((prev) =>
        prev.map((m, i) =>
          i === aiIdx
            ? { ...m, content: 'Xin lỗi, AI Tutor hiện không khả dụng. Vui lòng kiểm tra kết nối hoặc cấu hình ANTHROPIC_API_KEY.', streaming: false }
            : m
        )
      )
    }
    setLoading(false)
  }

  const showSuggested = messages.length <= 1

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-h-[700px]">
      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <Message key={i} {...m} avatar={cfg.avatar} />
        ))}
        {showSuggested && (
          <div className="space-y-2 mt-4">
            <p className="text-xs text-gray-400 dark:text-gray-500 text-center">Gợi ý câu hỏi</p>
            {cfg.suggested.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="w-full text-left text-sm px-4 py-2.5 rounded-xl border border-dashed border-gray-300 dark:border-dark-border hover:border-primary hover:bg-primary/5 dark:hover:bg-primary/10 text-gray-600 dark:text-gray-300 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 dark:border-dark-border p-4 bg-white dark:bg-dark-bg">
        {/* Mode toggle (chỉ cho Kinh Dịch) */}
        {cfg.showMode && (
          <div className="flex items-center gap-1 mb-2 p-1 rounded-xl bg-gray-100 dark:bg-dark-card w-fit">
            {[
              { key: 'explain', label: '💡 Giải thích' },
              { key: 'socratic', label: '🤔 Socrates' },
            ].map((m) => (
              <button
                key={m.key}
                onClick={() => setMode(m.key)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                  mode === m.key ? 'bg-white dark:bg-dark-bg text-primary shadow-sm' : 'text-gray-500 dark:text-gray-400'
                }`}
                title={m.key === 'socratic' ? 'AI đặt câu hỏi ngược để bạn tự khám phá' : 'AI giải thích trực tiếp'}
              >
                {m.label}
              </button>
            ))}
          </div>
        )}
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder={cfg.placeholder}
            disabled={loading}
            className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 dark:border-dark-border bg-gray-50 dark:bg-dark-card text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50"
          />
          <button
            onClick={() => send()}
            disabled={loading || !input.trim()}
            className="btn-primary px-4 rounded-xl"
          >
            {loading ? '⏳' : '→'}
          </button>
        </div>
      </div>
    </div>
  )
}
