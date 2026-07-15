// Thẻ giải mã 1 chữ Hán trong Thoán từ — dùng trong ChuDichHexagramPage.
export default function HexagramCharacterCard({ char }) {
  return (
    <div className="card p-4 space-y-2">
      <div className="flex items-baseline gap-3">
        <span className="text-4xl font-display">{char.hanzi}</span>
        <div>
          <div className="text-sm font-bold text-primary">{char.hanviet}</div>
          <div className="text-xs text-gray-400 dark:text-gray-500 font-mono">{char.pinyin}</div>
        </div>
      </div>
      <div className="text-sm text-gray-700 dark:text-gray-300">{char.meaning}</div>
      <div className="text-xs text-gray-500 dark:text-gray-400">
        <span className="font-semibold">Nguồn gốc:</span> {char.origin}
      </div>
      <div className="text-xs text-gray-500 dark:text-gray-400">
        <span className="font-semibold">Ví dụ:</span> {char.example}
      </div>
      <div className="pt-2 border-t border-gray-100 dark:border-dark-border flex items-center gap-2">
        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-primary/10 text-primary">
          {char.cs}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">{char.csExplain}</span>
      </div>
    </div>
  )
}
