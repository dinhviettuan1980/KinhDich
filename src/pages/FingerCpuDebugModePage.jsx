import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { THIEN_CAN } from '../data/fingerCpu/thienCan'
import { DIA_CHI } from '../data/fingerCpu/diaChi'

const PHASE_LABEL = ['bắt đầu vòng lặp', 'đọc THIEN_CAN[i%10]', 'đọc DIA_CHI[i%12]', 'ghép kết quả']

export default function FingerCpuDebugModePage() {
  const navigate = useNavigate()
  const [i, setI] = useState(0)
  const [phase, setPhase] = useState(0)
  const [output, setOutput] = useState([])
  const [running, setRunning] = useState(false)
  const timerRef = useRef(null)

  const can = phase >= 1 ? THIEN_CAN[i % 10] : null
  const chi = phase >= 2 ? DIA_CHI[i % 12] : null
  const result = phase >= 3 && can && chi ? `${can.ten} ${chi.ten}` : null
  const finished = i >= 60

  const stepInto = () => {
    if (finished) return
    if (phase < 3) { setPhase((p) => p + 1); return }
    setOutput((o) => [...o, result])
    setI((v) => v + 1)
    setPhase(0)
  }

  const stepOver = () => {
    if (finished) return
    const c = THIEN_CAN[i % 10], ch = DIA_CHI[i % 12]
    setOutput((o) => [...o, `${c.ten} ${ch.ten}`])
    setI((v) => v + 1)
    setPhase(0)
  }

  const reset = () => { setRunning(false); setI(0); setPhase(0); setOutput([]) }

  useEffect(() => {
    if (!running) return
    if (i >= 60) { setRunning(false); return }
    timerRef.current = setInterval(() => stepOver(), 90)
    return () => clearInterval(timerRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running, i])

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/finger-cpu')} className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-sm">
          ← Finger CPU Lab
        </button>
      </div>

      <div>
        <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">🐞 Debug Mode</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Chạy từng bước thuật toán sinh 60 Hoa Giáp, giống debugger trong IDE.</p>
      </div>

      <div className="card p-5">
        <div className="text-[10px] font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2">Call Stack</div>
        <div className="font-mono text-xs space-y-1 text-gray-500 dark:text-gray-400">
          <div>main()</div>
          <div className="pl-3">└ generateHoaGiap()</div>
          <div className="pl-6">└ for i = {finished ? 60 : i} {'{'}</div>
          {!finished && <div className="pl-9 text-primary font-semibold">└ {PHASE_LABEL[phase]}</div>}
        </div>
      </div>

      <div className="card p-5">
        <div className="text-[10px] font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2">Watch</div>
        <div className="grid grid-cols-2 gap-2 font-mono text-xs">
          <Watch label="i" value={finished ? 60 : i} />
          <Watch label="can" value={can?.ten ?? '—'} />
          <Watch label="chi" value={chi?.ten ?? '—'} />
          <Watch label="result" value={result ?? '—'} />
        </div>
      </div>

      <div className="card p-4 flex flex-wrap gap-2">
        <button onClick={stepInto} disabled={finished} className="btn-secondary text-xs px-3 py-2 disabled:opacity-40">Step Into</button>
        <button onClick={stepOver} disabled={finished} className="btn-secondary text-xs px-3 py-2 disabled:opacity-40">Step Over</button>
        <button onClick={() => setRunning((r) => !r)} disabled={finished} className="btn-primary text-xs px-3 py-2 flex-1 disabled:opacity-40">
          {running ? '⏸ Pause' : '▶ Continue'}
        </button>
        <button onClick={reset} className="btn-secondary text-xs px-3 py-2">↺ Replay</button>
      </div>

      <div className="card p-5">
        <div className="text-[10px] font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2">
          Output ({output.length}/60){finished && ' — hoàn tất'}
        </div>
        <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto">
          {output.map((r, idx) => (
            <span key={idx} className="text-[11px] font-mono px-2 py-1 rounded-lg bg-gray-50 dark:bg-dark-card/50 text-gray-600 dark:text-gray-300">{idx}:{r}</span>
          ))}
        </div>
      </div>

      <div className="card p-4 bg-gray-50 dark:bg-dark-card/50 text-center">
        <p className="text-xs text-gray-400 dark:text-gray-500 italic">
          💡 Step Into mở từng thao tác nhỏ bên trong 1 vòng lặp. Step Over chạy trọn 1 vòng lặp rồi dừng ở vòng kế tiếp.
        </p>
      </div>
    </div>
  )
}

function Watch({ label, value }) {
  return (
    <div className="px-2.5 py-1.5 rounded-lg bg-gray-50 dark:bg-dark-card/50 flex justify-between">
      <span className="text-gray-400">{label}</span>
      <span className="text-primary font-semibold">{value}</span>
    </div>
  )
}
