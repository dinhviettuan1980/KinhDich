import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { CHU_DICH_REGISTRY, getHexagramDetail } from '../data/chu-dich/registry'
import HexagramCharacterCard from '../components/chuDich/HexagramCharacterCard'

function Section({ title, children }) {
  return (
    <div className="card p-5">
      <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">{title}</h2>
      {children}
    </div>
  )
}

function TextBlock({ hanzi, hanviet, translation, english }) {
  return (
    <div className="space-y-1.5">
      <div className="text-lg font-display text-gray-900 dark:text-gray-100 leading-relaxed">{hanzi}</div>
      <div className="text-sm font-semibold text-primary">{hanviet}</div>
      <div className="text-sm text-gray-700 dark:text-gray-300">{translation}</div>
      {english && <div className="text-xs text-gray-400 dark:text-gray-500 italic">{english}</div>}
    </div>
  )
}

export default function ChuDichHexagramPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [showRefs, setShowRefs] = useState(false)
  const meta = CHU_DICH_REGISTRY.find((h) => h.id === Number(id))
  const hex = getHexagramDetail(id)

  if (!meta) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-gray-500 dark:text-gray-400">Không tìm thấy quẻ này.</p>
        <button onClick={() => navigate('/chu-dich')} className="btn-primary mt-4">← Về Chu Dịch Nguyên Tác</button>
      </div>
    )
  }

  const prevId = meta.id > 1 ? meta.id - 1 : null
  const nextId = meta.id < 64 ? meta.id + 1 : null

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/chu-dich')} className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-sm">
          ← Chu Dịch Nguyên Tác
        </button>
        <span className="text-xs text-gray-400 dark:text-gray-500 ml-auto">Quẻ {meta.id}/64</span>
      </div>

      {!hex ? (
        <div className="card p-10 text-center space-y-3">
          <div className="text-4xl">🚧</div>
          <h2 className="font-semibold text-gray-700 dark:text-gray-200">"{meta.name}" đang được tra cứu và biên soạn</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
            Nguyên tác chỉ được đưa vào sau khi đã đối chiếu nguồn học thuật công khai — xem tiến độ
            trong <code className="font-mono text-xs">TODO.md</code>.
          </p>
        </div>
      ) : (
        <>
          <div className="text-center space-y-1">
            <div className="text-6xl font-display">{hex.hanzi}</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{hex.hanviet}</div>
            <div className="text-sm text-gray-400 dark:text-gray-500">{hex.pinyin} · {hex.english}</div>
          </div>

          <Section title="📖 Thoán Từ (卦辭)">
            <TextBlock {...hex.judgment} />
          </Section>

          <Section title="🌤️ Đại Tượng (大象傳) — Thập Dực">
            <TextBlock {...hex.daTuong} />
            <p className="text-[11px] text-gray-400 dark:text-gray-500 italic mt-2">{hex.daTuong.note}</p>
          </Section>

          <Section title="🧠 Giải thích dễ hiểu">
            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{hex.meaning}</p>
          </Section>

          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2 px-1">
              🈶 Giải mã từng chữ
            </h2>
            <div className="grid gap-3">
              {hex.characters.map((c) => <HexagramCharacterCard key={c.hanzi} char={c} />)}
            </div>
          </div>

          <Section title="💻 Dưới góc nhìn lập trình">
            <p className="text-sm font-mono text-primary dark:text-primary-light">{hex.computer_science}</p>
          </Section>

          <div className="grid sm:grid-cols-2 gap-3">
            <Section title="🌿 Ứng dụng đời sống">
              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{hex.life}</p>
            </Section>
            <Section title="⚙️ Ứng dụng lập trình">
              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{hex.programming}</p>
            </Section>
          </div>

          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2 px-1">
              📜 Từng hào (爻辭)
            </h2>
            <div className="space-y-3">
              {hex.yao.map((y) => (
                <div key={y.id} className="card p-4 space-y-2">
                  <div className="text-sm font-bold text-primary">{y.name}</div>
                  <TextBlock hanzi={y.hanzi} hanviet={y.hanviet} translation={y.translation} english={y.english} />
                  <p className="text-xs text-gray-500 dark:text-gray-400">{y.explain}</p>
                  <div className="grid sm:grid-cols-2 gap-2 pt-1">
                    <div className="text-xs p-2 rounded-lg bg-gray-50 dark:bg-dark-card/50">
                      <span className="font-semibold text-gray-600 dark:text-gray-300">💻 IT: </span>
                      <span className="text-gray-500 dark:text-gray-400">{y.itExample}</span>
                    </div>
                    <div className="text-xs p-2 rounded-lg bg-gray-50 dark:bg-dark-card/50">
                      <span className="font-semibold text-gray-600 dark:text-gray-300">🌿 Đời sống: </span>
                      <span className="text-gray-500 dark:text-gray-400">{y.lifeExample}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <Section title="🔗 Liên kết">
            <div className="flex flex-col gap-1.5">
              {hex.relatedLessons.map((l) => (
                <Link key={l.path} to={l.path} className="text-sm text-primary hover:underline">→ {l.label}</Link>
              ))}
            </div>
          </Section>

          <div>
            <button
              onClick={() => setShowRefs((v) => !v)}
              className="text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
            >
              {showRefs ? '▾' : '▸'} Nguồn tham khảo
            </button>
            {showRefs && (
              <div className="mt-2 space-y-1 text-[11px] text-gray-400 dark:text-gray-500">
                {hex.references.map((r) => (
                  <div key={r.url}>
                    <a href={r.url} target="_blank" rel="noreferrer" className="text-primary hover:underline">{r.source}</a> — {r.note}
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      <div className="flex gap-3 pt-2">
        {prevId && (
          <button onClick={() => navigate(`/chu-dich/que/${prevId}`)} className="btn-secondary flex-1 text-sm">
            ← Quẻ {prevId}
          </button>
        )}
        {nextId && (
          <button onClick={() => navigate(`/chu-dich/que/${nextId}`)} className="btn-primary flex-1 text-sm">
            Quẻ {nextId} →
          </button>
        )}
      </div>
    </div>
  )
}
