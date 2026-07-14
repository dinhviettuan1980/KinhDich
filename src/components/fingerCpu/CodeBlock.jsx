// Khối code dùng chung cho Bài 22–24 (Java/JavaScript/Python) — không dùng thư viện
// syntax-highlight ngoài, chỉ <pre> + font-mono, đúng cách các bài trước đã làm (Bài 6, 9, 16).
export default function CodeBlock({ title, children }) {
  return (
    <div className="rounded-xl bg-gray-900 dark:bg-black overflow-hidden">
      {title && (
        <div className="px-3 py-1.5 border-b border-white/10 text-[10px] font-mono text-gray-400 uppercase tracking-wider">
          {title}
        </div>
      )}
      <pre className="p-3 font-mono text-[11px] text-emerald-400 overflow-x-auto leading-relaxed">{children}</pre>
    </div>
  )
}
