import CodeBlock from '../CodeBlock'

export default function Lesson24() {
  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-3">🐍 Python — ngắn gọn nhất trong 3 ngôn ngữ</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Python thể hiện rõ nhất phần "toán học thuần" của thuật toán, không bị cú pháp khai báo
          kiểu che khuất — chỉ còn lại đúng phần lõi: modulo + tra bảng.
        </p>
      </div>

      <CodeBlock title="hoa_giap.py">{`THIEN_CAN = ["Giáp","Ất","Bính","Đinh","Mậu",
             "Kỷ","Canh","Tân","Nhâm","Quý"]

DIA_CHI = ["Tý","Sửu","Dần","Mão","Thìn","Tỵ",
           "Ngọ","Mùi","Thân","Dậu","Tuất","Hợi"]

def generate_hoa_giap():
    return [
        f"{THIEN_CAN[i % 10]} {DIA_CHI[i % 12]}"
        for i in range(60)
    ]

hoa_giap = generate_hoa_giap()
print(hoa_giap[0])   # Giáp Tý
print(hoa_giap[42])  # Bính Ngọ
print(len(hoa_giap))  # 60 — đúng LCM(10, 12)`}</CodeBlock>

      <CodeBlock title="finger_map.py — index đốt tay">{`def index_to_position(index):
    i = index % 12
    finger_index = i // 3   # 0=trỏ 1=giữa 2=áp út 3=út
    dot_index = i % 3       # 0=dưới 1=giữa 2=trên
    return finger_index, dot_index

for i in range(12):
    print(i, index_to_position(i))`}</CodeBlock>

      <div className="card p-5 border-l-4 border-primary">
        <h2 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">⚡ 3 ngôn ngữ, 1 thuật toán</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Java, JavaScript, Python có cú pháp khác nhau hoàn toàn — nhưng cả 3 đều biểu diễn đúng
          1 ý tưởng: <code className="font-mono text-xs bg-gray-100 dark:bg-dark-card px-1 rounded">i % 10</code> và{' '}
          <code className="font-mono text-xs bg-gray-100 dark:bg-dark-card px-1 rounded">i % 12</code>. Đây
          là bằng chứng mạnh nhất rằng "bấm ngón tay" là thuật toán, không phụ thuộc công cụ diễn đạt.
        </p>
      </div>
    </div>
  )
}
