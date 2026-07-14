import { useParams, useNavigate } from 'react-router-dom'
import LessonShell from '../components/fingerCpu/LessonShell'
import { LESSON_BY_ID } from '../data/fingerCpu/lessons'
import { LESSON_COMPONENTS } from '../components/fingerCpu/lessons'

export default function FingerCpuLessonPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const lesson = LESSON_BY_ID[Number(id)]

  if (!lesson) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-gray-500 dark:text-gray-400">Không tìm thấy bài học này.</p>
        <button onClick={() => navigate('/finger-cpu')} className="btn-primary mt-4">← Về Finger CPU Lab</button>
      </div>
    )
  }

  const Content = LESSON_COMPONENTS[lesson.id]

  return (
    <LessonShell lesson={lesson}>
      {Content ? (
        <Content />
      ) : (
        <div className="card p-10 text-center space-y-3">
          <div className="text-4xl">🚧</div>
          <h2 className="font-semibold text-gray-700 dark:text-gray-200">Đang xây dựng</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
            Bài "{lesson.title}" nằm trong các phase tiếp theo của Finger CPU Lab — xem tiến độ trong{' '}
            <code className="font-mono text-xs">TODO.md</code> của repo.
          </p>
        </div>
      )}
    </LessonShell>
  )
}
