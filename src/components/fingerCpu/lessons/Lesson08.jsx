import { useState } from 'react'
import { TRIGRAMS, trigramFromBits } from '../../../data/fingerCpu/trigrams'

function HaoBar({ on, onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-full h-7 flex items-center gap-1.5 group"
    >
      {on ? (
        <span className="h-2.5 flex-1 rounded bg-primary group-hover:bg-primary-dark transition-colors" />
      ) : (
        <>
          <span className="h-2.5 flex-1 rounded bg-gray-300 dark:bg-dark-border group-hover:bg-gray-400 transition-colors" />
          <span className="h-2.5 flex-1 rounded bg-gray-300 dark:bg-dark-border group-hover:bg-gray-400 transition-colors" />
        </>
      )}
    </button>
  )
}

export default function Lesson08() {
  const [bits, setBits] = useState([1, 1, 1]) // [hào1 dưới, hào2 giữa, hào3 trên]
  const trigram = trigramFromBits(bits)

  const toggle = (i) => setBits((b) => b.map((v, idx) => (idx === i ? 1 - v : v)))

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Bát Quái = 3 bit nhị phân</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Mỗi quái gồm 3 hào, mỗi hào chỉ có 2 trạng thái: <strong>Dương (liền —)</strong> = 1, hoặc{' '}
          <strong>Âm (đứt - -)</strong> = 0. 3 hào → 2³ = <strong>8 tổ hợp</strong> → 8 quái (Bát Quái).
        </p>
      </div>

      <div className="card p-6">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-4">🎛️ Bấm để đảo hào</h2>
        <div className="flex flex-col-reverse gap-2 max-w-xs mx-auto mb-4">
          {bits.map((b, i) => (
            <HaoBar key={i} on={b === 1} onClick={() => toggle(i)} />
          ))}
        </div>
        <div className="text-center space-y-1">
          <div className="font-mono text-xs text-gray-400">
            bits = [{bits.join(', ')}] → nhị phân {[...bits].reverse().join('')} = giá trị {trigram.value}
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            <span className="text-4xl">{trigram.glyph}</span>
            <div className="text-left">
              <div className="text-lg font-bold text-primary">{trigram.quai}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">{trigram.hinh}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📋 Toàn bộ 8 quái (thứ tự nhị phân)</h2>
        <div className="grid grid-cols-4 gap-2">
          {TRIGRAMS.map((t) => (
            <button
              key={t.value}
              onClick={() => setBits(t.bits)}
              className={`p-3 rounded-xl text-center transition-all ${
                trigram.value === t.value
                  ? 'bg-primary text-white scale-105'
                  : 'bg-gray-50 dark:bg-dark-card/50 hover:bg-gray-100 dark:hover:bg-dark-border'
              }`}
            >
              <div className="text-2xl">{t.glyph}</div>
              <div className={`text-xs font-bold ${trigram.value === t.value ? '' : 'text-gray-700 dark:text-gray-200'}`}>{t.quai}</div>
              <div className={`text-[10px] font-mono ${trigram.value === t.value ? 'opacity-80' : 'text-gray-400'}`}>{t.value}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Vì sao đây là Binary thật sự</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Đây không phải phép so sánh khiên cưỡng — Bát Quái thoả mãn đúng định nghĩa toán học của
          hệ nhị phân 3-bit: 2 trạng thái/hào, 3 hào độc lập, 8 tổ hợp duy nhất, có thể đánh số 0–7
          một cách nhất quán. Bài 9 sẽ ghép 2 quái (thượng + hạ) = 6 bit = 64 tổ hợp → 64 Quẻ.
        </p>
      </div>
    </div>
  )
}
