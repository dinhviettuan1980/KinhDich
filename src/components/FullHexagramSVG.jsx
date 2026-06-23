// SVG renderer for a full 6-line hexagram
// lines: array of 6 values (6=yin-moving, 7=yang-static, 8=yin-static, 9=yang-moving)
// index 0 = hào 1 (bottom), index 5 = hào 6 (top)
// movingLines: array of line numbers (1-6) that are moving
// highlightMoving: whether to visually mark moving lines

const W = 80
const H = 6
const GAP = 10
const BREAK = 10 // gap in yin line
const TOTAL_HEIGHT = 6 * H + 5 * GAP

function Line({ value, y, isMoving }) {
  const isYang = value === 7 || value === 9
  const gold = '#D4A017'
  const color = isMoving ? '#F59E0B' : gold
  const opacity = isMoving ? 1 : 0.85

  if (isYang) {
    return (
      <g opacity={opacity}>
        <rect x={0} y={y} width={W} height={H} rx={2} fill={color} />
        {isMoving && (
          <circle cx={W + 10} cy={y + H / 2} r={3} fill="#F59E0B" />
        )}
      </g>
    )
  }
  // Yin: two half-bars with a break in the middle
  const halfW = (W - BREAK) / 2
  return (
    <g opacity={opacity}>
      <rect x={0} y={y} width={halfW} height={H} rx={2} fill={color} />
      <rect x={halfW + BREAK} y={y} width={halfW} height={H} rx={2} fill={color} />
      {isMoving && (
        <circle cx={W + 10} cy={y + H / 2} r={3} fill="#F59E0B" />
      )}
    </g>
  )
}

export default function FullHexagramSVG({ lines, movingLines = [], size = 1 }) {
  if (!lines || lines.length !== 6) return null
  const svgW = (W + 20) * size
  const svgH = TOTAL_HEIGHT * size

  return (
    <svg
      viewBox={`0 0 ${W + 20} ${TOTAL_HEIGHT}`}
      width={svgW}
      height={svgH}
      aria-hidden="true"
    >
      {[...lines].reverse().map((val, i) => {
        const lineNum = 6 - i // hào 6 is at top (i=0 in reversed), hào 1 at bottom
        const y = i * (H + GAP)
        const isMoving = movingLines.includes(lineNum)
        return <Line key={i} value={val} y={y} isMoving={isMoving} />
      })}
    </svg>
  )
}
