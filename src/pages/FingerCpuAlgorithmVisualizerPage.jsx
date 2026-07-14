import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { THIEN_CAN } from '../data/fingerCpu/thienCan'
import { DIA_CHI } from '../data/fingerCpu/diaChi'
import { TRIGRAMS } from '../data/fingerCpu/trigrams'

const DATASETS = [
  { key: 'dia-chi', label: 'Địa Chi', size: 12, table: DIA_CHI, nameOf: (x) => x.ten },
  { key: 'thien-can', label: 'Thiên Can', size: 10, table: THIEN_CAN, nameOf: (x) => x.ten },
  { key: 'bat-quai', label: 'Bát Quái', size: 8, table: TRIGRAMS, nameOf: (x) => x.quai },
]

export default function FingerCpuAlgorithmVisualizerPage() {
  const navigate = useNavigate()
  const [datasetKey, setDatasetKey] = useState('dia-chi')
  const [n, setN] = useState(17)
  const [step, setStep] = useState(3)

  const dataset = DATASETS.find((d) => d.key === datasetKey)
  const index = ((n % dataset.size) + dataset.size) % dataset.size
  const result = dataset.table[index]

  const NODES = [
    { label: 'Input', detail: `n = ${n}` },
    { label: 'Modulo', detail: `${n} % ${dataset.size} = ${index}` },
    { label: 'Lookup', detail: `${dataset.label}[${index}]` },
    { label: 'Result', detail: dataset.nameOf(result) },
  ]

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/finger-cpu')} className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-sm">
          ← Finger CPU Lab
        </button>
      </div>

      <div>
        <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">🔀 Algorithm Visualizer</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Input → Modulo → Lookup → Result, với bất kỳ bảng dữ liệu nào đã học.</p>
      </div>

      <div className="card p-4 grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-gray-400 dark:text-gray-500 block mb-1">Bảng dữ liệu</label>
          <select
            value={datasetKey}
            onChange={(e) => { setDatasetKey(e.target.value); setStep(3) }}
            className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm outline-none focus:border-primary"
          >
            {DATASETS.map((d) => <option key={d.key} value={d.key}>{d.label} ({d.size})</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-400 dark:text-gray-500 block mb-1">n</label>
          <input
            type="number" value={n}
            onChange={(e) => { setN(Number(e.target.value) || 0); setStep(3) }}
            className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-sm font-mono outline-none focus:border-primary"
          />
        </div>
      </div>

      <div className="card p-6">
        <div className="flex items-center justify-end gap-2 mb-3">
          <button onClick={() => setStep(0)} className="btn-secondary text-xs px-3 py-1.5">↺ Chạy lại từ đầu</button>
        </div>
        <div className="flex flex-col items-center gap-1">
          {NODES.map((node, i) => (
            <div key={node.label} className="w-full max-w-xs">
              <button
                onClick={() => setStep(Math.max(step, i))}
                className={`w-full p-3 rounded-xl border text-center transition-all duration-200 ${
                  i <= step ? 'bg-primary/10 border-primary/30' : 'bg-gray-50 dark:bg-dark-card/50 border-transparent opacity-40'
                }`}
              >
                <div className="text-xs font-bold text-gray-600 dark:text-gray-300">{node.label}</div>
                <div className="font-mono text-sm text-primary mt-0.5">{i <= step ? node.detail : '…'}</div>
              </button>
              {i < NODES.length - 1 && <div className="text-center text-gray-300 dark:text-gray-600 text-sm py-1">↓</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
