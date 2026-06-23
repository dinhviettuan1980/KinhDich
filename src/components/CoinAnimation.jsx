import { useState, useEffect, useRef } from 'react'

// ── CSS keyframes injected once ──────────────────────────────────────────────
const STYLE_ID = 'coin-anim-css'
function ensureCSS() {
  if (document.getElementById(STYLE_ID)) return
  const el = document.createElement('style')
  el.id = STYLE_ID
  el.textContent = `
    @keyframes coinRise {
      0%   { transform: translateY(0px) scaleX(1); }
      40%  { transform: translateY(-110px) scaleX(1.04); }
      100% { transform: translateY(-110px) scaleX(1.04); }
    }
    @keyframes coinFall {
      0%   { transform: translateY(-110px) scaleX(1.04); }
      55%  { transform: translateY(6px) scaleX(0.94); }
      72%  { transform: translateY(-5px) scaleX(1.02); }
      84%  { transform: translateY(2px) scaleX(0.98); }
      92%  { transform: translateY(-1px) scaleX(1.01); }
      100% { transform: translateY(0px) scaleX(1); }
    }
    @keyframes tableShake {
      0%   { transform: translate(0,0) rotate(0deg); }
      10%  { transform: translate(-5px, 2px) rotate(-0.4deg); }
      22%  { transform: translate(5px, -2px) rotate(0.4deg); }
      34%  { transform: translate(-4px, 1px) rotate(-0.3deg); }
      46%  { transform: translate(3px, -1px) rotate(0.2deg); }
      58%  { transform: translate(-2px, 0) rotate(-0.1deg); }
      70%  { transform: translate(2px, 0); }
      82%  { transform: translate(-1px, 0); }
      91%  { transform: translate(1px, 0); }
      100% { transform: translate(0,0) rotate(0deg); }
    }
    @keyframes shadowAir {
      0%   { transform: scaleX(0.5); opacity: 0.08; }
      40%  { transform: scaleX(0.35); opacity: 0.05; }
      100% { transform: scaleX(0.35); opacity: 0.05; }
    }
    @keyframes shadowLand {
      0%   { transform: scaleX(0.35); opacity: 0.05; }
      55%  { transform: scaleX(1.2); opacity: 0.25; }
      100% { transform: scaleX(0.9); opacity: 0.18; }
    }
    @keyframes resultReveal {
      from { opacity: 0; transform: translateY(10px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes woodGrain {
      0%   { opacity: 0.06; }
      50%  { opacity: 0.1; }
      100% { opacity: 0.06; }
    }
  `
  document.head.appendChild(el)
}

// ── Ancient coin SVG ─────────────────────────────────────────────────────────
function AncientCoinSVG({ isHeads, size = 80 }) {
  const gold   = isHeads ? '#D4A535' : '#9A7C28'
  const shine  = isHeads ? '#E8C45A' : '#B09040'
  const rim    = '#5C3D0E'
  const inner  = isHeads ? '#C49225' : '#856A18'
  const hole   = '#1A0C06'

  return (
    <svg viewBox="-52 -52 104 104" width={size} height={size} style={{ display: 'block' }}>
      <defs>
        <radialGradient id={`cg${isHeads ? 'h' : 't'}`} cx="35%" cy="30%" r="60%">
          <stop offset="0%"   stopColor={shine} stopOpacity="0.9" />
          <stop offset="60%"  stopColor={gold}  stopOpacity="1" />
          <stop offset="100%" stopColor={rim}   stopOpacity="0.8" />
        </radialGradient>
      </defs>

      <circle r={48} fill={`url(#cg${isHeads ? 'h' : 't'})`} />
      <circle r={48} fill="none" stroke={rim} strokeWidth={3.5} />
      <circle r={44} fill="none" stroke={rim} strokeWidth={0.8} opacity={0.5} />

      {Array.from({ length: 24 }).map((_, i) => {
        const a = (i / 24) * Math.PI * 2
        return <circle key={i} cx={Math.cos(a) * 46} cy={Math.sin(a) * 46} r={1.4} fill={rim} />
      })}

      <circle r={22} fill={inner} />
      <circle r={22} fill="none" stroke={rim} strokeWidth={1} opacity={0.4} />
      <rect x={-10} y={-10} width={20} height={20} fill={hole} rx={1.5} />
      <rect x={-10} y={-10} width={20} height={20} fill="none" stroke={rim} strokeWidth={1} rx={1.5} />

      {isHeads ? (
        <>
          {Array.from({ length: 8 }).map((_, i) => {
            const a = (i / 8) * Math.PI * 2 + Math.PI / 8
            return (
              <line key={i}
                x1={Math.cos(a) * 13} y1={Math.sin(a) * 13}
                x2={Math.cos(a) * 20} y2={Math.sin(a) * 20}
                stroke={rim} strokeWidth={1.5} opacity={0.55} strokeLinecap="round"
              />
            )
          })}
          {[[-15,-15],[15,-15],[15,15],[-15,15]].map(([x,y],i) => (
            <circle key={i} cx={x} cy={y} r={2.2} fill={rim} opacity={0.6} />
          ))}
          <circle r={17} fill="none" stroke={rim} strokeWidth={0.6} strokeDasharray="2 3" opacity={0.4} />
        </>
      ) : (
        <>
          <circle r={17} fill="none" stroke={rim} strokeWidth={1} opacity={0.35} />
          <circle r={13} fill="none" stroke={rim} strokeWidth={0.6} opacity={0.25} />
          <line x1={-20} y1={0} x2={-12} y2={0} stroke={rim} strokeWidth={0.8} opacity={0.3} strokeLinecap="round" />
          <line x1={12}  y1={0} x2={20}  y2={0} stroke={rim} strokeWidth={0.8} opacity={0.3} strokeLinecap="round" />
          <line x1={0} y1={-20} x2={0} y2={-12} stroke={rim} strokeWidth={0.8} opacity={0.3} strokeLinecap="round" />
          <line x1={0} y1={12}  x2={0} y2={20}  stroke={rim} strokeWidth={0.8} opacity={0.3} strokeLinecap="round" />
        </>
      )}
    </svg>
  )
}

// ── Đồng xu đơn (flip animation) ────────────────────────────────────────────
function FlippingCoin({ value, delay, phase }) {
  const isHeads = value === 3
  // Quay đủ số vòng rồi dừng đúng mặt: 5 vòng + góc cuối (0=ngửa, 180=sấp)
  const finalDeg = 5 * 360 + (isHeads ? 0 : 180)

  const innerRef  = useRef()
  const rafRef    = useRef()
  const startRef  = useRef()

  const SPIN_MS   = 1000  // thời gian quay
  const EASE_MS   = 350   // ease về góc cuối

  useEffect(() => {
    if (phase !== 'spinning') return
    ensureCSS()

    const inner = innerRef.current
    if (!inner) return

    let started = false

    const timer = setTimeout(() => {
      started = true
      startRef.current = performance.now()

      const animate = (now) => {
        const elapsed = now - startRef.current
        const t = Math.min(elapsed / SPIN_MS, 1)
        // Ease-out quint
        const eased = 1 - Math.pow(1 - t, 5)
        inner.style.transform = `rotateY(${eased * finalDeg}deg)`
        if (t < 1) {
          rafRef.current = requestAnimationFrame(animate)
        } else {
          inner.style.transform = `rotateY(${finalDeg}deg)`
        }
      }
      rafRef.current = requestAnimationFrame(animate)
    }, delay)

    return () => {
      clearTimeout(timer)
      cancelAnimationFrame(rafRef.current)
    }
  }, [phase])

  const isInAir   = phase === 'spinning'
  const hasLanded = phase === 'landed' || phase === 'done'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
      {/* Bóng dưới đồng xu */}
      <div style={{ position: 'relative', width: 80 }}>
        <div
          style={{
            position: 'absolute',
            bottom: -6,
            left: '50%',
            transform: 'translateX(-50%)',
            width: 72,
            height: 10,
            background: 'radial-gradient(ellipse, rgba(0,0,0,0.35) 0%, transparent 70%)',
            borderRadius: '50%',
            animation: isInAir
              ? `shadowAir ${SPIN_MS}ms ${delay}ms ease-out both`
              : hasLanded
              ? `shadowLand 300ms ${delay}ms ease-out both`
              : 'none',
          }}
        />

        {/* Coin container — chuyển động lên/xuống */}
        <div
          style={{
            animation: isInAir
              ? `coinRise ${SPIN_MS * 0.4}ms ${delay}ms ease-out both, coinFall ${SPIN_MS * 0.6}ms ${delay + SPIN_MS * 0.4}ms cubic-bezier(0.25,0.46,0.45,0.94) both`
              : 'none',
          }}
        >
          {/* 3-D perspective wrapper */}
          <div style={{ perspective: '300px' }}>
            {/* Inner: xoay Y */}
            <div
              ref={innerRef}
              style={{
                transformStyle: 'preserve-3d',
                position: 'relative',
                width: 80,
                height: 80,
              }}
            >
              {/* Mặt ngửa */}
              <div style={{ position: 'absolute', inset: 0, backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden' }}>
                <AncientCoinSVG isHeads={true} size={80} />
              </div>
              {/* Mặt sấp */}
              <div style={{ position: 'absolute', inset: 0, backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}>
                <AncientCoinSVG isHeads={false} size={80} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Bàn gỗ SVG ──────────────────────────────────────────────────────────────
function WoodTable({ shaking }) {
  return (
    <div
      style={{
        position: 'absolute',
        bottom: -16,
        left: -32,
        right: -32,
        height: 32,
        borderRadius: '0 0 16px 16px',
        background: 'linear-gradient(to bottom, #8B5E3C, #6B4423)',
        boxShadow: '0 6px 20px rgba(0,0,0,0.4)',
        overflow: 'hidden',
        animation: shaking ? 'tableShake 420ms ease-out' : 'none',
      }}
    >
      {/* Vân gỗ */}
      {[15, 30, 50, 70, 85].map((pct, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            top: 0, bottom: 0,
            left: `${pct}%`,
            width: '1px',
            background: 'rgba(0,0,0,0.15)',
            transform: `rotate(${i % 2 === 0 ? 1 : -1}deg)`,
            animation: 'woodGrain 3s ease-in-out infinite',
            animationDelay: `${i * 0.4}s`,
          }}
        />
      ))}
    </div>
  )
}

// ── Export chính ─────────────────────────────────────────────────────────────
// props:
//   result  : { coins: [2|3, 2|3, 2|3], value: 6|7|8|9 }
//   onDone  : () => void
export default function CoinAnimation({ result, onDone }) {
  useEffect(() => { ensureCSS() }, [])

  const [phase, setPhase] = useState('idle')
  // idle → spinning → landed → done

  useEffect(() => {
    if (!result) return

    setPhase('spinning')

    // Sau khi đồng xu rơi xuống: rung bàn
    const t1 = setTimeout(() => setPhase('landed'), 1300)
    // Sau đó hiện kết quả + gọi onDone
    const t2 = setTimeout(() => { setPhase('done'); onDone() }, 2200)

    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [result])

  if (!result) return null

  const DELAYS = [0, 120, 240] // stagger 3 đồng xu

  const valueLabel = {
    6: { text: '— × —', sub: 'Âm động (biến)', color: '#F59E0B' },
    7: { text: '———',   sub: 'Dương tĩnh',      color: '#D4A535' },
    8: { text: '— —',   sub: 'Âm tĩnh',         color: '#D4A535' },
    9: { text: '——○',   sub: 'Dương động (biến)', color: '#F59E0B' },
  }[result.value] || { text: '?', sub: '', color: '#888' }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 32, paddingTop: 24, paddingBottom: 32 }}>
      {/* Vùng tung đồng xu + bàn gỗ */}
      <div style={{ position: 'relative', padding: '16px 40px 40px' }}>
        <div style={{ display: 'flex', gap: 24, alignItems: 'flex-end' }}>
          {result.coins.map((v, i) => (
            <FlippingCoin
              key={i}
              value={v}
              delay={DELAYS[i]}
              phase={phase}
            />
          ))}
        </div>

        <WoodTable shaking={phase === 'landed'} />
      </div>

      {/* Tổng kết */}
      <div
        style={{
          opacity: phase === 'landed' || phase === 'done' ? 1 : 0,
          animation: phase === 'landed' ? 'resultReveal 300ms ease-out forwards' : 'none',
          textAlign: 'center',
          transition: 'opacity 300ms',
        }}
      >
        <div style={{ fontSize: 11, color: '#9CA3AF', marginBottom: 4 }}>
          {result.coins.join(' + ')} = {result.value}
        </div>
        <div style={{ fontFamily: 'serif', fontSize: 22, fontWeight: 700, color: valueLabel.color, letterSpacing: '0.2em' }}>
          {valueLabel.text}
        </div>
        <div style={{ fontSize: 12, color: valueLabel.color, marginTop: 4, opacity: 0.8 }}>
          {valueLabel.sub}
        </div>
      </div>
    </div>
  )
}
