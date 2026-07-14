import { useState } from 'react'
import { CUU_CUNG_GRID } from '../../../data/fingerCpu/cuuCung'

export default function CuuCungMode() {
  const [selected, setSelected] = useState({ r: 1, c: 1 })
  const cell = CUU_CUNG_GRID[selected.r][selected.c]
  return (
    <div>
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
      <div className="p-4 rounded-xl bg-gray-50 dark:bg-dark-card/50 text-center">
        <div className="font-mono text-xs text-gray-400 mb-1">CUU_CUNG[{selected.r}][{selected.c}]</div>
        <div className="text-lg font-bold text-primary">Cung {cell.number} · {cell.directionVi}</div>
        <div className="text-sm text-gray-600 dark:text-gray-300">
          {cell.trigram ? `${cell.trigram.quai} (${cell.trigram.hinh})` : 'Trung cung'}
        </div>
      </div>
    </div>
  )
}
