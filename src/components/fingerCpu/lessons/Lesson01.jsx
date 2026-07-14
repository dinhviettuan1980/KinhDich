export default function Lesson01() {
  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Vấn đề</h2>
        <div className="prose prose-sm dark:prose-invert max-w-none space-y-3 text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
          <p>
            Người xưa không có máy tính, smartphone, Excel, IDE hay calculator. Nhưng họ vẫn
            cần <strong>tra cứu nhanh</strong>, <strong>tính toán chu kỳ</strong> và <strong>ghi nhớ hàng trăm quy tắc</strong> —
            đủ để làm lịch, tính giờ, tính mùa, dự báo thời tiết nông nghiệp.
          </p>
          <p>
            Giải pháp của họ rất thực dụng: dùng chính cơ thể — cụ thể là <strong>bàn tay</strong> —
            làm một thiết bị lưu trữ và tra cứu di động, luôn mang theo bên mình, không bao giờ hết pin.
          </p>
        </div>
      </div>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-3">⚡ So sánh với máy tính</h2>
        <div className="grid grid-cols-3 gap-2 text-center text-sm">
          <div className="p-3 rounded-xl bg-gray-50 dark:bg-dark-card/50">
            <div className="text-2xl mb-1">🖐️</div>
            <div className="font-semibold text-gray-800 dark:text-gray-100">Bàn tay</div>
          </div>
          <div className="flex items-center justify-center text-gray-300 dark:text-gray-600 text-xl">↓</div>
          <div className="p-3 rounded-xl bg-primary/10">
            <div className="text-2xl mb-1">💾</div>
            <div className="font-semibold text-primary">RAM / Lookup Table</div>
          </div>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">
          12 đốt tay = 12 "ô nhớ" cố định. Mỗi ô nhớ 1 giá trị (Tý, Sửu, Dần...). Ngón tay cái
          đóng vai trò con trỏ (pointer) di chuyển tới từng ô để "đọc" giá trị — giống hệt CPU
          dùng con trỏ để truy cập một phần tử trong mảng.
        </p>
      </div>

      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">🎯 Vì sao kỹ thuật này tồn tại hàng nghìn năm</h2>
        <ul className="list-disc list-inside space-y-1.5 text-sm text-gray-700 dark:text-gray-300">
          <li><strong>Luôn sẵn có</strong> — không cần giấy bút, sách vở.</li>
          <li><strong>Tốc độ tra cứu O(1)</strong> — biết vị trí là chạm thẳng tới, không cần dò từ đầu.</li>
          <li><strong>Dễ dạy, dễ truyền</strong> — chỉ cần nhớ 1 sơ đồ cố định, không cần nhớ cả bảng.</li>
          <li><strong>Không lỗi bộ nhớ ngoài</strong> — sách có thể mất, cháy, mối mọt; bàn tay thì luôn mang theo.</li>
        </ul>
      </div>

      <div className="card p-5 bg-gradient-to-br from-purple-50 to-primary/5 dark:from-purple-900/20 dark:to-primary/10 border border-primary/20">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary dark:text-primary-light mb-2">🪷 Điều cần nhớ</h2>
        <p className="text-gray-700 dark:text-gray-200 text-sm font-medium">
          Bấm ngón tay không phải là "phép thuật". Đó là một hệ thống <strong>lưu trữ + tra cứu</strong> được
          thiết kế thông minh, chạy hoàn toàn bằng phần cứng sinh học — bàn tay của chính bạn.
        </p>
      </div>
    </div>
  )
}
