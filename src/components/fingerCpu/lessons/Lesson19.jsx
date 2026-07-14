export default function Lesson19() {
  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Giới thiệu (không đi sâu)</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Thái Ất Thần Số theo dõi các chu kỳ rất dài (hàng chục, hàng trăm năm), đếm số "thần" di
          chuyển qua các cung theo từng mốc thời gian tích luỹ — giống một{' '}
          <strong>bộ đếm (counter)</strong> chạy song song với nhiều tầng chu kỳ modulo khác nhau
          chồng lên nhau.
        </p>
      </div>

      <div className="card p-5">
        <div className="flex items-center justify-center gap-3 text-xs font-mono text-gray-500 dark:text-gray-400">
          <span className="px-2 py-1 rounded bg-gray-50 dark:bg-dark-card/50">năm % 10</span>
          <span>+</span>
          <span className="px-2 py-1 rounded bg-gray-50 dark:bg-dark-card/50">năm % 12</span>
          <span>+</span>
          <span className="px-2 py-1 rounded bg-gray-50 dark:bg-dark-card/50">chu kỳ dài hơn...</span>
        </div>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Góc nhìn CS</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Nhiều bộ đếm modulo độ dài khác nhau chạy đồng thời — về bản chất là mở rộng ý tưởng LCM
          ở bài 6 (60 Hoa Giáp) lên nhiều tầng chu kỳ hơn, để theo dõi được các mốc thời gian rất
          lớn mà không cần lưu một bảng khổng lồ. Cách tính chi tiết nằm ngoài phạm vi module này.
        </p>
      </div>
    </div>
  )
}
