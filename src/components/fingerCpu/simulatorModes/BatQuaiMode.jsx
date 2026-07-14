import { useState } from 'react'
import { TRIGRAMS, trigramFromBits } from '../../../data/fingerCpu/trigrams'

export default function BatQuaiMode() {
  const [bits, setBits] = useState([1, 1, 1])
  const trigram = trigramFromBits(bits)
  const toggle = (i) => setBits((b) => b.map((v, idx) => (idx === i ? 1 - v : v)))

  return (
    <div>
      <div className="flex flex-col-reverse gap-2 max-w-xs mx-auto mb-4">
        {bits.map((b, i) => (
          <button key={i} onClick={() => toggle(i)} className="w-full h-7 flex items-center gap-1.5 group">
            {b === 1 ? (
              <span className="h-2.5 flex-1 rounded bg-primary group-hover:bg-primary-dark transition-colors" />
            ) : (
              <>
                <span className="h-2.5 flex-1 rounded bg-gray-300 dark:bg-dark-border group-hover:bg-gray-400 transition-colors" />
                <span className="h-2.5 flex-1 rounded bg-gray-300 dark:bg-dark-border group-hover:bg-gray-400 transition-colors" />
              </>
            )}
          </button>
        ))}
      </div>

      <div className="p-4 rounded-xl bg-gray-50 dark:bg-dark-card/50 text-center mb-4">
        <div className="flex items-center justify-center gap-3">
          <span className="text-3xl">{trigram.glyph}</span>
          <div className="text-left">
            <div className="text-lg font-bold text-primary">{trigram.quai}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">{trigram.hinh} · giá trị {trigram.value}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2">
        {TRIGRAMS.map((t) => (
          <button
            key={t.value}
            onClick={() => setBits(t.bits)}
            className={`p-2 rounded-xl text-center transition-all ${
              trigram.value === t.value ? 'bg-primary text-white scale-105' : 'bg-gray-50 dark:bg-dark-card/50 hover:bg-gray-100 dark:hover:bg-dark-border'
            }`}
          >
            <div className="text-xl">{t.glyph}</div>
            <div className="text-[10px] font-bold">{t.quai}</div>
          </button>
        ))}
      </div>
    </div>
  )
}
