import CodeBlock from '../CodeBlock'

export default function Lesson22() {
  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">☕ Java — kiểu tĩnh, rõ ràng từng bước</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Java buộc khai báo kiểu rõ ràng — phù hợp để thấy đúng "hình dạng" dữ liệu: mảng cố định,
          hàm nhận số nguyên, trả về chuỗi. Không có gì "ẩn" trong cú pháp.
        </p>
      </div>

      <CodeBlock title="ThienCan.java + DiaChi.java">{`public class LookupTables {
    static final String[] THIEN_CAN = {
        "Giáp","Ất","Bính","Đinh","Mậu",
        "Kỷ","Canh","Tân","Nhâm","Quý"
    };
    static final String[] DIA_CHI = {
        "Tý","Sửu","Dần","Mão","Thìn","Tỵ",
        "Ngọ","Mùi","Thân","Dậu","Tuất","Hợi"
    };
}`}</CodeBlock>

      <CodeBlock title="HoaGiap.java — sinh bằng vòng lặp, không hardcode">{`public class HoaGiap {
    public static String[] generate() {
        String[] result = new String[60];
        for (int i = 0; i < 60; i++) {
            String can = LookupTables.THIEN_CAN[i % 10];
            String chi = LookupTables.DIA_CHI[i % 12];
            result[i] = can + " " + chi;
        }
        return result;
    }

    public static void main(String[] args) {
        String[] hoaGiap = generate();
        System.out.println(hoaGiap[0]);   // Giáp Tý
        System.out.println(hoaGiap[42]);  // Bính Ngọ
    }
}`}</CodeBlock>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ Đối chiếu với bài 6</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Đây chính là <code className="font-mono text-xs bg-gray-100 dark:bg-dark-card px-1 rounded">generateHoaGiap()</code> ở
          Bài 6, viết lại bằng Java — cùng logic <code className="font-mono text-xs bg-gray-100 dark:bg-dark-card px-1 rounded">i % 10</code> /{' '}
          <code className="font-mono text-xs bg-gray-100 dark:bg-dark-card px-1 rounded">i % 12</code>, chỉ khác cú pháp.
        </p>
      </div>
    </div>
  )
}
