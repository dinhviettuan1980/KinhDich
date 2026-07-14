import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { THIEN_CAN } from '../data/fingerCpu/thienCan'
import { DIA_CHI } from '../data/fingerCpu/diaChi'
import { TRIGRAMS } from '../data/fingerCpu/trigrams'

const DATASETS = [
  { key: 'dia-chi', label: 'Địa Chi', size: 12, matrix: [4, 3], table: DIA_CHI, nameOf: (x) => x.ten },
  { key: 'thien-can', label: 'Thiên Can', size: 10, matrix: [5, 2], table: THIEN_CAN, nameOf: (x) => x.ten },
  { key: 'bat-quai', label: 'Bát Quái', size: 8, matrix: [4, 2], table: TRIGRAMS, nameOf: (x) => x.quai },
]

const VIEWS = ['Array', 'HashMap', 'Matrix', 'Binary', 'Circular Array', 'Graph']

export default function FingerCpuDataStructureModePage() {
  const navigate = useNavigate()
  const [datasetKey, setDatasetKey] = useState('dia-chi')
  const [view, setView] = useState('Array')
  const dataset = DATASETS.find((d) => d.key === datasetKey)
  const items = dataset.table.map((x, i) => ({ index: i, name: dataset.nameOf(x) }))
  const bits = Math.ceil(Math.log2(dataset.size))

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/finger-cpu')} className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-sm">
          ← Finger CPU Lab
        </button>
      </div>

      <div>
        <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">🗃️ Data Structure Mode</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Cùng 1 bảng dữ liệu — 6 cách nhìn khác nhau.</p>
      </div>

      <div className="card p-4">
        <label className="text-xs text-gray-400 dark:text-gray-500 block mb-1">Bảng dữ liệu</label>
        <select
          value={datasetKey}
          onChange={(e) => setDatasetKey(e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm outline-none focus:border-primary"
        >
          {DATASETS.map((d) => <option key={d.key} value={d.key}>{d.label} ({d.size})</option>)}
        </select>
      </div>

      <div className="flex gap-1.5 overflow-x-auto pb-1">
        {VIEWS.map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              view === v ? 'bg-primary text-white' : 'bg-gray-50 dark:bg-dark-card/50 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-border'
            }`}
          >
            {v}
          </button>
        ))}
      </div>

      <div className="card p-6">
        {view === 'Array' && (
          <div className="flex flex-wrap gap-1.5 justify-center">
            {items.map((it) => (
              <div key={it.index} className="w-14 rounded-lg bg-gray-50 dark:bg-dark-card/50 text-center py-2">
                <div className="text-[9px] font-mono text-gray-400">{it.index}</div>
                <div className="text-xs font-semibold text-gray-700 dark:text-gray-200">{it.name}</div>
              </div>
            ))}
          </div>
        )}

        {view === 'HashMap' && (
          <div className="space-y-1 max-w-xs mx-auto font-mono text-xs">
            {items.map((it) => (
              <div key={it.index} className="flex justify-between px-3 py-1.5 rounded-lg bg-gray-50 dark:bg-dark-card/50">
                <span className="text-amber-500 dark:text-amber-300">"{it.name}"</span>
                <span className="text-gray-400">→</span>
                <span className="text-primary">{it.index}</span>
              </div>
            ))}
          </div>
        )}

        {view === 'Matrix' && (
          <div className="flex justify-center">
            <div className="grid gap-1.5" style={{ gridTemplateColumns: `repeat(${dataset.matrix[0]}, minmax(0, 1fr))` }}>
              {items.map((it) => (
                <div key={it.index} className="w-12 h-12 rounded-lg bg-gray-50 dark:bg-dark-card/50 flex flex-col items-center justify-center">
                  <span className="text-[9px] font-mono text-gray-400">{it.index}</span>
                  <span className="text-[11px] font-semibold text-gray-700 dark:text-gray-200">{it.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {view === 'Binary' && (
          <div className="flex flex-wrap gap-1.5 justify-center font-mono">
            {items.map((it) => (
              <div key={it.index} className="w-20 rounded-lg bg-gray-900 dark:bg-black text-center py-2">
                <div className="text-emerald-400 text-xs">{it.index.toString(2).padStart(bits, '0')}</div>
                <div className="text-[10px] text-gray-400 mt-0.5">{it.name}</div>
              </div>
            ))}
          </div>
        )}

        {(view === 'Circular Array' || view === 'Graph') && (
          <CircularView items={items} withEdges={view === 'Graph'} />
        )}
      </div>
    </div>
  )
}

function CircularView({ items, withEdges }) {
  const n = items.length
  const R = 85, CX = 105, CY = 105
  const pos = (i) => {
    const angle = (i / n) * 2 * Math.PI - Math.PI / 2
    return [CX + R * Math.cos(angle), CY + R * Math.sin(angle)]
  }
  return (
    <div className="flex justify-center">
      <svg viewBox="0 0 210 210" width={230} height={230}>
        {withEdges && items.map((it) => {
          const [x1, y1] = pos(it.index)
          const [x2, y2] = pos((it.index + 1) % n)
          return <line key={it.index} x1={x1} y1={y1} x2={x2} y2={y2} className="stroke-primary/40" strokeWidth="1.5" markerEnd="url(#arrow)" />
        })}
        <defs>
          <marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" className="fill-primary/40" />
          </marker>
        </defs>
        {items.map((it) => {
          const [x, y] = pos(it.index)
          return (
            <g key={it.index}>
              <circle cx={x} cy={y} r="14" className="fill-gray-50 dark:fill-dark-card stroke-gray-200 dark:stroke-dark-border" strokeWidth="1" />
              <text x={x} y={y + 3} textAnchor="middle" className="text-[9px] font-bold fill-gray-700 dark:fill-gray-200">{it.name}</text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
