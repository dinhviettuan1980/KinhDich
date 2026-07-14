import { useState } from 'react'
import { FINGERS, DOTS, positionToIndex } from '../../data/fingerCpu/fingerMap'

// Chiều cao từng ngón (tổng, chia đều cho 3 đốt) — chỉ để hình minh hoạ cân đối,
// không nhằm tái hiện giải phẫu chính xác.
const FINGER_HEIGHT = { tro: 140, giua: 160, apUt: 148, ut: 116 }
const FINGER_X = { tro: 30, giua: 96, apUt: 162, ut: 220 }
const FINGER_W = { tro: 40, giua: 42, apUt: 40, ut: 34 }
const PALM_TOP = 210
const GAP = 4

/**
 * Bàn tay SVG tương tác — nền tảng trực quan của toàn bộ Finger CPU Lab.
 * 12 đốt (4 ngón × 3 đốt) = finger[0]..finger[11], xem data/fingerCpu/fingerMap.js.
 *
 * Props:
 *  activeIndex  — đốt đang được chọn (0..11 | null), viền nổi bật + tô màu accent
 *  onSelect     — (index) => void, gọi khi click 1 đốt
 *  labelAt      — (index) => string, nhãn hiển thị khi hover/chọn (vd tên Địa Chi)
 *  interactive  — cho phép click/hover (mặc định true)
 */
export default function FingerHandSVG({ activeIndex = null, onSelect, labelAt, interactive = true, size = 280 }) {
  const [hoverIndex, setHoverIndex] = useState(null)
  const shownIndex = hoverIndex ?? activeIndex

  return (
    <div className="flex flex-col items-center gap-3">
      <svg viewBox="0 0 260 260" width={size} height={size} className="select-none overflow-visible">
        {/* Lòng bàn tay */}
        <path
          d={`M 20 ${PALM_TOP} Q 20 258 60 258 L 220 258 Q 250 258 250 ${PALM_TOP} Z`}
          className="fill-primary/10 dark:fill-primary/15 stroke-primary/30"
          strokeWidth="1.5"
        />
        {/* Ngón cái — decorative, không tính vào 12 đốt */}
        <g opacity="0.55">
          <rect x="4" y="196" width="26" height="56" rx="12" className="fill-gray-200 dark:fill-dark-border stroke-gray-300 dark:stroke-dark-muted" strokeWidth="1" transform="rotate(-25 17 224)" />
          <text x="6" y="252" className="fill-gray-400 dark:fill-gray-500 text-[8px]">con trỏ</text>
        </g>

        {FINGERS.map((finger, fi) => {
          const H = FINGER_HEIGHT[finger.key]
          const x = FINGER_X[finger.key]
          const w = FINGER_W[finger.key]
          const dotH = H / 3

          return (
            <g key={finger.key}>
              {DOTS.map((dot, di) => {
                // di=0 (dưới) vẽ sát palm; di=2 (trên) vẽ xa palm nhất
                const yBottom = PALM_TOP - di * dotH
                const y = yBottom - dotH
                const idx = positionToIndex(fi, di)
                const isActive = shownIndex === idx
                return (
                  <rect
                    key={dot.key}
                    x={x}
                    y={y}
                    width={w}
                    height={dotH - GAP}
                    rx="8"
                    className={`transition-all duration-150 stroke-1 ${
                      isActive
                        ? 'fill-primary stroke-primary-dark'
                        : 'fill-white dark:fill-dark-card stroke-gray-300 dark:stroke-dark-border hover:fill-primary/20'
                    } ${interactive ? 'cursor-pointer' : ''}`}
                    onMouseEnter={() => interactive && setHoverIndex(idx)}
                    onMouseLeave={() => interactive && setHoverIndex(null)}
                    onClick={() => interactive && onSelect?.(idx)}
                  />
                )
              })}
              <text
                x={x + w / 2}
                y={PALM_TOP + 16}
                textAnchor="middle"
                className="fill-gray-400 dark:fill-gray-500 text-[9px] font-medium"
              >
                {finger.label.replace('Ngón ', '')}
              </text>
            </g>
          )
        })}
      </svg>

      {/* Nhãn đang hover/chọn */}
      <div className="h-8 flex items-center justify-center">
        {shownIndex != null ? (
          <span className="level-badge bg-primary/10 text-primary font-mono">
            finger[{shownIndex}] · {labelAt ? labelAt(shownIndex) : ''}
          </span>
        ) : (
          <span className="text-xs text-gray-400 dark:text-gray-500">
            {interactive ? 'Chạm hoặc click vào 1 đốt' : ''}
          </span>
        )}
      </div>
    </div>
  )
}
