export default function Lesson18() {
  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Giới thiệu (không đi sâu)</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Kỳ Môn Độn Giáp dùng lại chính lưới <strong>Cửu Cung</strong> (bài 12) — nhưng xếp chồng
          thêm nhiều lớp dữ liệu khác nhau lên cùng 9 ô: Thiên Bàn, Địa Bàn, Bát Môn (8 cửa), Cửu
          Tinh (9 sao), Bát Thần (8 thần) — tất cả đổi theo thời điểm.
        </p>
      </div>

      <div className="card p-6">
        <div className="grid grid-cols-3 gap-1.5 max-w-xs mx-auto">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="aspect-square rounded-lg bg-gray-50 dark:bg-dark-card/50 flex flex-col items-center justify-center gap-0.5 p-1">
              <span className="text-[8px] text-gray-400">Cửa</span>
              <span className="text-[8px] text-gray-400">Sao</span>
              <span className="text-[8px] text-gray-400">Thần</span>
            </div>
          ))}
        </div>
        <p className="text-[11px] text-gray-400 dark:text-gray-500 text-center mt-3">
          Mỗi ô Cửu Cung mang nhiều "trường dữ liệu" cùng lúc — như 1 struct nhiều field trên cùng 1 index.
        </p>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Góc nhìn CS</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Đây là mô hình <strong>nhiều mảng dữ liệu song song (parallel arrays)</strong> cùng chia
          sẻ 1 chỉ số (index) — mỗi ô Cửu Cung tra ra nhiều giá trị khác nhau chỉ từ 1 vị trí duy
          nhất. Toàn bộ quy tắc sắp xếp 5 lớp dữ liệu theo giờ nằm ngoài phạm vi module này.
        </p>
      </div>
    </div>
  )
}
