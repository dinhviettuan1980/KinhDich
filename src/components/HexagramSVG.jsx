const TRIGRAMS = {
  qian: [1, 1, 1],
  kun:  [0, 0, 0],
  zhen: [1, 0, 0],
  xun:  [0, 1, 1],
  kan:  [0, 1, 0],
  li:   [1, 0, 1],
  gen:  [0, 0, 1],
  dui:  [1, 1, 0],
}

const TRIGRAM_SYMBOLS = {
  qian: '☰', kun: '☷', zhen: '☳', xun: '☴',
  kan: '☵', li: '☲', gen: '☶', dui: '☱',
}

const TRIGRAM_NAMES = {
  qian: 'Càn', kun: 'Khôn', zhen: 'Chấn', xun: 'Tốn',
  kan: 'Khảm', li: 'Ly', gen: 'Cấn', dui: 'Đoài',
}

function Line({ yang, y, width }) {
  const lineHeight = 4
  if (yang) {
    return <rect x={0} y={y} width={width} height={lineHeight} rx={2} fill="currentColor" />
  }
  const gap = width * 0.12
  const segW = (width - gap) / 2
  return (
    <>
      <rect x={0} y={y} width={segW} height={lineHeight} rx={2} fill="currentColor" />
      <rect x={segW + gap} y={y} width={segW} height={lineHeight} rx={2} fill="currentColor" />
    </>
  )
}

export function HexagramSVG({ trigram = 'qian', size = 64, showLabel = true }) {
  const lines = TRIGRAMS[trigram] || [1, 1, 1]
  const w = size
  const lineGap = size * 0.22
  const startY = size * 0.1
  const svgH = showLabel ? size + 24 : size

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={w} height={size * 0.9} viewBox={`0 0 ${w} ${size * 0.9}`} className="text-gray-800 dark:text-gray-200">
        {[...lines].reverse().map((yang, i) => (
          <Line key={i} yang={yang === 1} y={startY + i * lineGap} width={w} />
        ))}
      </svg>
      {showLabel && (
        <div className="text-center">
          <div className="text-2xl">{TRIGRAM_SYMBOLS[trigram]}</div>
          <div className="text-xs font-bold text-gray-600 dark:text-gray-400">{TRIGRAM_NAMES[trigram]}</div>
        </div>
      )}
    </div>
  )
}

export function AllTrigrams() {
  return (
    <div className="grid grid-cols-4 gap-6">
      {Object.keys(TRIGRAMS).map((t) => (
        <div key={t} className="flex flex-col items-center p-3 card rounded-xl hover:scale-105 transition-transform">
          <HexagramSVG trigram={t} size={48} showLabel={true} />
        </div>
      ))}
    </div>
  )
}
