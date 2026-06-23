import { useState, useEffect, useRef } from 'react'
import coinHeadsImg from '../assets/coin_yang.png'
import coinTailsImg from '../assets/coin_yin.png'

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

// ── Coin face dùng ảnh thật ──────────────────────────────────────────────────
function AncientCoinSVG({ isHeads, size = 80 }) {
  return (
    <div style={{
      width: size, height: size,
      borderRadius: '50%',
      overflow: 'hidden',
      boxShadow: '0 4px 16px rgba(0,0,0,0.5), inset 0 1px 2px rgba(255,220,100,0.3)',
    }}>
      <img
        src={isHeads ? coinHeadsImg : coinTailsImg}
        width={size}
        height={size}
        style={{ display: 'block', objectFit: 'cover', objectPosition: 'center' }}
        alt=""
        draggable={false}
      />
    </div>
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
