import CodeBlock from '../CodeBlock'

export default function Lesson23() {
  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">🟨 JavaScript — chính là code của trang này</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Không cần tưởng tượng — đoạn dưới đây gần như nguyên văn{' '}
          <code className="font-mono text-xs bg-gray-100 dark:bg-dark-card px-1 rounded">src/data/fingerCpu/hoaGiap.js</code> đang
          chạy thật trong module Finger CPU Lab mà bạn đang xem.
        </p>
      </div>

      <CodeBlock title="thienCan.js + diaChi.js">{`export const THIEN_CAN = [
  { index: 0, ten: 'Giáp' }, { index: 1, ten: 'Ất' },
  // ... đủ 10 phần tử
]

export const DIA_CHI = [
  { index: 0, ten: 'Tý' }, { index: 1, ten: 'Sửu' },
  // ... đủ 12 phần tử
]`}</CodeBlock>

      <CodeBlock title="hoaGiap.js — generateHoaGiap()">{`export function generateHoaGiap() {
  const result = []
  for (let i = 0; i < 60; i++) {
    const can = THIEN_CAN[i % 10]
    const chi = DIA_CHI[i % 12]
    result.push({ index: i, ten: \`\${can.ten} \${chi.ten}\` })
  }
  return result
}

export const HOA_GIAP = generateHoaGiap()`}</CodeBlock>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Bạn đã "chạy" đoạn code này rồi</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Mỗi lần bấm nút "Tự chạy" ở Bài 6, bạn đang xem đúng mảng{' '}
          <code className="font-mono text-xs bg-gray-100 dark:bg-dark-card px-1 rounded">HOA_GIAP</code> này
          được reveal dần trên UI — không có xử lý ẩn nào khác phía sau.
        </p>
      </div>
    </div>
  )
}
