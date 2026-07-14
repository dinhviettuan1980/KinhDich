export default function Lesson17() {
  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Giới thiệu (không đi sâu)</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Lục Nhâm dùng một "bàn cờ vũ trụ" (thức bàn) gồm 2 vòng tròn 12 Địa Chi lồng vào nhau:{' '}
          <strong>Địa Bàn</strong> đứng yên, <strong>Thiên Bàn</strong> xoay theo giờ. Vị trí lệch
          giữa 2 vòng tại 1 thời điểm cho ra các "thần" cần tra.
        </p>
      </div>

      <div className="card p-6 flex flex-col items-center gap-4">
        <div className="relative w-48 h-48">
          <div className="absolute inset-0 rounded-full border-2 border-gray-200 dark:border-dark-border flex items-center justify-center text-[10px] text-gray-400">
            Địa Bàn (cố định)
          </div>
          <div className="absolute inset-6 rounded-full border-2 border-dashed border-primary/50 flex items-center justify-center text-[10px] text-primary animate-[spin_20s_linear_infinite]">
            Thiên Bàn (xoay)
          </div>
        </div>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Góc nhìn CS</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          2 vòng tròn cùng 12 phần tử nhưng lệch pha (phase offset) — đúng là bài toán{' '}
          <strong>offset % 12</strong> đã học ở bài 7, chỉ áp dụng cho 2 mảng vòng (circular array)
          thay vì 1. Chi tiết đầy đủ của Lục Nhâm nằm ngoài phạm vi module này.
        </p>
      </div>
    </div>
  )
}
