import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DiaChiMode from '../components/fingerCpu/simulatorModes/DiaChiMode'
import ThienCanMode from '../components/fingerCpu/simulatorModes/ThienCanMode'
import BatQuaiMode from '../components/fingerCpu/simulatorModes/BatQuaiMode'
import HoaGiapMode from '../components/fingerCpu/simulatorModes/HoaGiapMode'
import CuuCungMode from '../components/fingerCpu/simulatorModes/CuuCungMode'
import TruongSinhMode from '../components/fingerCpu/simulatorModes/TruongSinhMode'
import TietKhiMode from '../components/fingerCpu/simulatorModes/TietKhiMode'

const MODES = [
  { key: 'dia-chi', label: '12 Địa Chi', Component: DiaChiMode },
  { key: 'thien-can', label: '10 Thiên Can', Component: ThienCanMode },
  { key: 'bat-quai', label: 'Bát Quái', Component: BatQuaiMode },
  { key: 'hoa-giap', label: '60 Hoa Giáp', Component: HoaGiapMode },
  { key: 'cuu-cung', label: 'Cửu Cung', Component: CuuCungMode },
  { key: 'truong-sinh', label: 'Trường Sinh', Component: TruongSinhMode },
  { key: 'tiet-khi', label: '24 Tiết Khí', Component: TietKhiMode },
]

export default function FingerCpuSimulatorPage() {
  const navigate = useNavigate()
  const [mode, setMode] = useState('dia-chi')
  const current = MODES.find((m) => m.key === mode)
  const Mode = current.Component

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/finger-cpu')}
          className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-sm"
        >
          ← Finger CPU Lab
        </button>
      </div>

      <div>
        <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">🎛️ Finger CPU Simulator</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Chọn bảng dữ liệu để tra cứu — mỗi mode dùng đúng cấu trúc đã học ở bài tương ứng.
        </p>
      </div>

      <div className="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1">
        {MODES.map((m) => (
          <button
            key={m.key}
            onClick={() => setMode(m.key)}
            className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              mode === m.key ? 'bg-primary text-white' : 'bg-gray-50 dark:bg-dark-card/50 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-border'
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      <div className="card p-6">
        <Mode key={mode} />
      </div>
    </div>
  )
}
