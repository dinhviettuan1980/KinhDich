import { useState } from 'react'
import TutorChat from '../components/TutorChat'

const TABS = [
  {
    key: 'kinhdich',
    label: '☯ Kinh Dịch',
    title: '🤖 AI Tutor Kinh Dịch',
    desc: 'Hỏi bất kỳ điều gì về Kinh Dịch — được giải thích theo góc nhìn kỹ thuật',
  },
  {
    key: 'vankhan',
    label: '🙏 Văn khấn',
    title: '🙏 Trợ lý Văn khấn',
    desc: 'Hỏi về văn khấn đền, chùa, tại nhà, cầu nguyện — cách sắm lễ, dịp dùng, xin nguyên văn',
  },
]

export default function TutorPage() {
  const [tab, setTab] = useState('kinhdich')
  const active = TABS.find((t) => t.key === tab) || TABS[0]

  return (
    <div className="max-w-2xl mx-auto px-4 py-4">
      {/* Tabs chọn chủ đề hỏi */}
      <div className="flex items-center gap-1 mb-4 p-1 rounded-xl bg-gray-100 dark:bg-dark-card w-fit">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-colors ${
              tab === t.key ? 'bg-white dark:bg-dark-bg text-primary shadow-sm' : 'text-gray-500 dark:text-gray-400'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="mb-4">
        <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">{active.title}</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{active.desc}</p>
      </div>
      <div className="card overflow-hidden">
        {/* key theo tab để reset hội thoại khi đổi chủ đề */}
        <TutorChat key={tab} topic={tab} />
      </div>
    </div>
  )
}
