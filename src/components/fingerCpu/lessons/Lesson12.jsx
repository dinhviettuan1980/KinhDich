import { useState } from 'react'
import { CUU_CUNG_GRID } from '../../../data/fingerCpu/cuuCung'

export default function Lesson12() {
  const [selected, setSelected] = useState({ r: 1, c: 1 })
  const cell = CUU_CUNG_GRID[selected.r][selected.c]

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 9 vùng nhớ cố định</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Cửu Cung ghép Lạc Thư (bài 10) với Bát Quái (bài 8): mỗi ô trong ma trận 3×3 vừa có 1{' '}
          <strong>số</strong>, vừa có 1 <strong>hướng</strong>, vừa có 1 <strong>quái</strong> (trừ ô
          trung tâm). Đây chính là một cấu trúc <strong>struct</strong> — nhiều trường dữ liệu gộp
          vào 1 vị trí duy nhất.
        </p>
      </div>

      <div className="card p-6">
        <div className="grid grid-cols-3 gap-2 max-w-xs mx-auto mb-4">
          {CUU_CUNG_GRID.map((row, ri) =>
            row.map((c, ci) => {
              const isSelected = selected.r === ri && selected.c === ci
              return (
                <button
                  key={`${ri}-${ci}`}
                  onClick={() => setSelected({ r: ri, c: ci })}
                  className={`aspect-square rounded-xl flex flex-col items-center justify-center transition-all duration-150 ${
                    isSelected ? 'bg-primary text-white scale-105' : 'bg-gray-50 dark:bg-dark-card/50 hover:bg-gray-100 dark:hover:bg-dark-border'
                  }`}
                >
                  <span className="text-lg">{c.trigram?.glyph || '◎'}</span>
                  <span className="text-xs font-mono font-bold">{c.number}</span>
                </button>
              )
            })
          )}
        </div>

        <div className="p-4 rounded-xl bg-gray-50 dark:bg-dark-card/50 text-center space-y-1">
          <div className="font-mono text-xs text-gray-400">CUU_CUNG[{selected.r}][{selected.c}]</div>
          <div className="text-lg font-bold text-primary">
            Cung {cell.number} · {cell.directionVi}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-300">
            {cell.trigram ? `${cell.trigram.quai} (${cell.trigram.hinh})` : 'Trung cung — không thuộc quái nào, là trục trung tâm'}
          </div>
        </div>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Struct, không phải phép thuật</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Tương đương pseudo-code: <code className="font-mono text-xs bg-gray-100 dark:bg-dark-card px-1 rounded">
          cell = {'{'} number, direction, trigram {'}'}</code>. 9 cell này sẽ quay lại ở phase
          Memory Visualizer — mô hình 9 "ô nhớ" click 1 bên sáng bên kia.
        </p>
      </div>
    </div>
  )
}
