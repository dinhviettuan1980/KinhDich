const ROWS = [
  { cpu: 'Register', nguoiXua: 'Ngón tay cái', giaiThich: 'Nơi giữ vị trí hiện tại đang thao tác — luôn chỉ có 1, di chuyển liên tục.' },
  { cpu: 'RAM', nguoiXua: '12 đốt tay', giaiThich: 'Không gian lưu trữ cố định, truy cập trực tiếp theo vị trí (địa chỉ).' },
  { cpu: 'Cache', nguoiXua: 'Trí nhớ đã thuộc lòng', giaiThich: 'Bảng dữ liệu tra cứu nhanh không cần "load" lại từ sách vở.' },
  { cpu: 'Pointer', nguoiXua: 'Vị trí đốt đang bấm', giaiThich: 'Trỏ tới 1 ô nhớ cụ thể để đọc giá trị tại đó.' },
  { cpu: 'Instruction', nguoiXua: 'Quy tắc bấm (thuật quyết)', giaiThich: 'Chuỗi bước cố định: xuất phát từ đâu, di chuyển thế nào, dừng ở đâu.' },
  { cpu: 'Lookup Table', nguoiXua: 'Bảng Can Chi / Bát Quái', giaiThich: 'Ánh xạ index → giá trị đã biết trước, không cần tính lại.' },
  { cpu: 'Modulo (%)', nguoiXua: 'Quay vòng ngón tay', giaiThich: 'Đưa số đếm vượt quá 12 (hoặc âm) về đúng phạm vi hợp lệ.' },
  { cpu: 'Hash Function', nguoiXua: 'Mai Hoa Dịch Số', giaiThich: '2 số đầu vào → 1 quẻ đầu ra, lặp lại luôn cho cùng kết quả.' },
  { cpu: 'Finite State Machine', nguoiXua: 'Vòng Trường Sinh', giaiThich: '12 trạng thái cố định, chuyển tiếp 1 chiều, lặp vòng.' },
]

export default function Lesson21() {
  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">📖 Cùng 1 kiến trúc, 2 cách gọi tên</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Sau 20 bài, đã đến lúc đặt song song thẳng thắn: mỗi khái niệm CPU hiện đại đều có 1 "bản
          dịch" sang ngôn ngữ của các thầy — không phải ẩn dụ gượng ép, mà là 2 cách đặt tên cho
          cùng 1 cơ chế.
        </p>
      </div>

      <div className="card p-5 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-400 dark:text-gray-500 text-xs">
              <th className="pb-2 pr-3">CPU / lập trình</th>
              <th className="pb-2 pr-3">Người xưa</th>
              <th className="pb-2">Giải thích</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((r) => (
              <tr key={r.cpu} className="border-t border-gray-50 dark:border-dark-border/50 align-top">
                <td className="py-2.5 pr-3 font-mono text-xs font-bold text-primary whitespace-nowrap">{r.cpu}</td>
                <td className="py-2.5 pr-3 font-semibold text-gray-800 dark:text-gray-100 whitespace-nowrap">{r.nguoiXua}</td>
                <td className="py-2.5 text-xs text-gray-500 dark:text-gray-400">{r.giaiThich}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card p-5 bg-gradient-to-br from-purple-50 to-primary/5 dark:from-purple-900/20 dark:to-primary/10 border border-primary/20">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary dark:text-primary-light mb-2">🪷 Kết luận tạm thời</h2>
        <p className="text-gray-700 dark:text-gray-200 text-sm font-medium">
          Người xưa không có silicon, nhưng có đủ Data Structure, Algorithm và Lookup Table để xây
          một "máy tính sinh học" chạy bằng bàn tay. 4 bài cuối sẽ hiện thực hoá điều đó bằng code
          thật — Java, JavaScript, Python.
        </p>
      </div>
    </div>
  )
}
