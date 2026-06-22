import TutorChat from '../components/TutorChat'

export default function TutorPage() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-4">
      <div className="mb-4">
        <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">🤖 AI Tutor Kinh Dịch</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Hỏi bất kỳ điều gì về Kinh Dịch — được giải thích theo góc nhìn kỹ thuật
        </p>
      </div>
      <div className="card overflow-hidden">
        <TutorChat />
      </div>
    </div>
  )
}
