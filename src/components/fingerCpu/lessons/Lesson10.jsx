import { useState } from 'react'
import { LAC_THU_GRID, magicSquareSums } from '../../../data/fingerCpu/lacThu'

export default function Lesson10() {
  const [checked, setChecked] = useState([])
  const sums = magicSquareSums()
  const lines = [
    { key: 'row-0', label: 'Hàng 1', cells: [[0, 0], [0, 1], [0, 2]], sum: sums.rows[0] },
    { key: 'row-1', label: 'Hàng 2', cells: [[1, 0], [1, 1], [1, 2]], sum: sums.rows[1] },
    { key: 'row-2', label: 'Hàng 3', cells: [[2, 0], [2, 1], [2, 2]], sum: sums.rows[2] },
    { key: 'col-0', label: 'Cột 1', cells: [[0, 0], [1, 0], [2, 0]], sum: sums.cols[0] },
    { key: 'col-1', label: 'Cột 2', cells: [[0, 1], [1, 1], [2, 1]], sum: sums.cols[1] },
    { key: 'col-2', label: 'Cột 3', cells: [[0, 2], [1, 2], [2, 2]], sum: sums.cols[2] },
    { key: 'diag-0', label: 'Chéo ↘', cells: [[0, 0], [1, 1], [2, 2]], sum: sums.diagonals[0] },
    { key: 'diag-1', label: 'Chéo ↙', cells: [[0, 2], [1, 1], [2, 0]], sum: sums.diagonals[1] },
  ]
  const activeLine = lines.find((l) => checked.includes(l.key))

  const highlighted = new Set((activeLine?.cells || []).map(([r, c]) => `${r}-${c}`))

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Ma trận vuông kỳ diệu</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Lạc Thư là một <strong>ma trận 3×3</strong> chứa số 1–9, mỗi số xuất hiện đúng 1 lần, sắp
          xếp sao cho <strong>mọi hàng, cột và đường chéo</strong> cộng lại đều bằng 15. Trong lập
          trình, đây là bài toán kinh điển "Magic Square".
        </p>
      </div>

      <div className="card p-6">
        <div className="grid grid-cols-3 gap-2 max-w-xs mx-auto mb-4">
          {LAC_THU_GRID.map((row, ri) =>
            row.map((cell, ci) => (
              <div
                key={`${ri}-${ci}`}
                className={`aspect-square rounded-xl flex flex-col items-center justify-center transition-all duration-150 ${
                  highlighted.has(`${ri}-${ci}`) ? 'bg-primary text-white scale-105' : 'bg-gray-50 dark:bg-dark-card/50'
                }`}
              >
                <span className="text-xl font-bold font-mono">{cell.number}</span>
                <span className={`text-[9px] ${highlighted.has(`${ri}-${ci}`) ? 'opacity-80' : 'text-gray-400'}`}>{cell.directionVi}</span>
              </div>
            ))
          )}
        </div>

        <div className="grid grid-cols-4 gap-1.5">
          {lines.map((l) => (
            <button
              key={l.key}
              onClick={() => setChecked((c) => (c.includes(l.key) ? c.filter((k) => k !== l.key) : [...c, l.key].slice(-1)))}
              className={`text-[11px] px-2 py-1.5 rounded-lg font-mono transition-colors ${
                checked.includes(l.key) ? 'bg-primary text-white' : 'bg-gray-50 dark:bg-dark-card/50 text-gray-500 dark:text-gray-400 hover:bg-gray-100'
              }`}
            >
              {l.label}={l.sum}
            </button>
          ))}
        </div>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Vì sao điều này quan trọng</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Một ma trận có tính chất bất biến (invariant) như "mọi tổng đều = 15" rất dễ kiểm tra
          bằng máy — nhưng người xưa phát hiện và ghi nhớ nó chỉ bằng quan sát và lặp lại. Lạc Thư
          chính là nền tảng vị trí cho Cửu Cung (bài 12): mỗi số ở đây tương ứng 1 hướng, 1 quái.
        </p>
      </div>
    </div>
  )
}
