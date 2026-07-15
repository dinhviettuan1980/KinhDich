# 🖐️💻 Finger CPU Lab — kế hoạch triển khai

Module giáo dục mới cho KinhDich: giải thích "bấm ngón tay của các thầy" bằng
tư duy Khoa học Máy tính (Array, HashMap, Modulo, Lookup Table, Binary...).
Không phải module xem bói — không tính vận hạn, không tra cứu cá nhân.

Quy ước kỹ thuật (theo conventions hiện có của repo, xem khảo sát ban đầu):
- Route: `/finger-cpu`, `/finger-cpu/bai/:id`, `/finger-cpu/simulator`, `/finger-cpu/game/*`
- Data: `src/data/fingerCpu/*.js` (module JS thuần, không JSON, để cho phép sinh dữ liệu bằng thuật toán thay vì hardcode — vd Hoa Giáp = Can[i%10]+Chi[i%12])
- Pages (route) nằm phẳng trong `src/pages/` giống các page khác: `FingerCpuIntroPage.jsx`, `FingerCpuLessonPage.jsx`, `FingerCpuSimulatorPage.jsx`...
- Nội dung từng bài học là component riêng trong `src/components/fingerCpu/lessons/BaiNN.jsx`, đăng ký qua registry `src/data/fingerCpu/lessons.js`
- Không thêm thư viện animation mới — dùng SVG thuần + Tailwind keyframes như `HexagramSVG.jsx`/`CoinAnimation.jsx` đã làm
- Quy ước đánh số đốt tay: 4 ngón (Trỏ, Giữa, Áp út, Út) × 3 đốt (dưới, giữa, trên) = 12 đốt = `finger[0]..finger[11]`, xem `src/data/fingerCpu/fingerMap.js`

## Phase 1 — Nền móng (đang làm)
- [x] TODO.md
- [x] Data: `thienCan.js`, `diaChi.js` (đầy đủ metadata: con giáp, ngũ hành, âm dương, phương vị, giờ, mùa, đặc điểm)
- [x] Data: `hoaGiap.js` (sinh bằng thuật toán, không hardcode)
- [x] Data: `fingerMap.js` (ánh xạ đốt ↔ ngón, dùng chung cho SVG + lesson + simulator)
- [x] Data: `lessons.js` (registry 25 bài: id, slug, tiêu đề, mô tả, trạng thái ready/coming-soon)
- [x] Component `FingerHandSVG.jsx` — bàn tay SVG tương tác (click/hover từng đốt), dùng chung toàn module
- [x] `FingerCpuIntroPage.jsx` — trang giới thiệu + danh sách 25 bài học
- [x] `FingerCpuLessonPage.jsx` — layout chung (progress bar, prev/next) + resolve bài học từ registry
- [x] Bài 1 — Tại sao phải bấm ngón tay?
- [x] Bài 2 — Biến bàn tay thành Array
- [x] Bài 3 — Lookup Table
- [x] Bài 4 — 12 Địa Chi
- [x] Bài 5 — 10 Thiên Can
- [x] Menu "🖐️ Finger CPU Lab" trong Navbar
- [x] Route trong `App.jsx`
- [x] `FingerCpuSimulatorPage.jsx` bản đầu (mode Địa Chi hoạt động đầy đủ, các mode khác "sắp có")

## Phase 2 — Toán & cấu trúc dữ liệu cốt lõi (xong)
- [x] Bài 6 — 60 Hoa Giáp (2 "bánh răng" 10 & 12 răng, generator step-by-step Play/Step/Reset, LCM)
- [x] Bài 7 — Modulo, simulator `(start + offset) % 12` với input tương tác + bàn tay minh hoạ kết quả
- [x] Bài 8 — Bát Quái (tái dùng `baquai.js` có sẵn qua cầu nối `trigrams.js`, hào toggle tương tác, nhị phân 3-bit)
- [x] Bài 9 — 64 Quẻ (ma trận 8×8 tương tác, tái dùng `hexagrams.js`/`lookupHexagram` đã có sẵn trong app thay vì tạo bảng mới)
- [x] Hoa Giáp Generator + 64 Quẻ Generator — quyết định: nhúng trực tiếp vào Bài 6 / Bài 9 dưới dạng Play/Step live-generate thay vì tách trang riêng, để giữ mạch sư phạm trực quan→thuật toán liền mạch
- [ ] (Còn nợ Phase 6) đưa Bát Quái + Hoa Giáp làm mode trong Finger CPU Simulator — data đã sẵn (`trigrams.js`, `hoaGiap.js`), chỉ cần nối UI

## Phase 3 — Các hệ thống mở rộng (Bài 10–15) — xong
- [x] Bài 10 — Lạc Thư (ma trận 3×3, bấm để kiểm tra từng hàng/cột/chéo = 15)
- [x] Bài 11 — Hà Đồ (5 cặp sinh/thành, công thức `thành = sinh + 5`)
- [x] Bài 12 — Cửu Cung (interactive, ghép Lạc Thư + Bát Quái thành 1 struct/ô)
- [x] Bài 13 — 24 Tiết Khí (timeline nhóm theo 4 mùa, ngày dương lịch ghi rõ là gần đúng)
- [x] Bài 14 — 28 Tú (interactive, nhóm theo Tứ Tượng 4×7)
- [x] Bài 15 — Trường Sinh (vòng tròn SVG, Play/Step, đóng khung rõ là Finite State Machine + modulo giống bài 7)

## Phase 4 — Tổng hợp & so sánh CPU (Bài 16–21) — xong
- [x] Bài 16 — Mai Hoa Dịch Số (đóng khung là hash function, simulator 2 số → quẻ, có caveat rút gọn so với bản gốc)
- [x] Bài 17 — Lục Nhâm (giới thiệu, 2 vòng tròn lệch pha = offset % 12)
- [x] Bài 18 — Kỳ Môn (giới thiệu, tái dùng Cửu Cung bài 12 + nhiều lớp dữ liệu song song)
- [x] Bài 19 — Thái Ất (giới thiệu, mở rộng ý tưởng LCM ở bài 6 lên nhiều tầng chu kỳ)
- [x] Bài 20 — Data Flow (pipeline Input→Can→Chi→Modulo→Quái→Quẻ, step-through, dùng lại toàn bộ hàm/data đã xây từ bài 1-9, có caveat đây là ví dụ tổng hợp không phải 1 kỹ thuật cổ cụ thể)
- [x] Bài 21 — CPU vs Người xưa (bảng so sánh 9 dòng, chốt thông điệp trước khi vào Code Mode)

## Phase 5 — Code Mode (Bài 22–25) — xong
- [x] Bài 22 — Java (LookupTables + HoaGiap.generate() bằng vòng lặp)
- [x] Bài 23 — JavaScript (gần nguyên văn code thật của chính module, không phải ví dụ giả)
- [x] Bài 24 — Python (bản list-comprehension ngắn gọn + finger_map.py)
- [x] Bài 25 — Tổng kết (recap 9 khái niệm CS ↔ bài học, CTA sang Simulator/học lại)
- [x] Component `CodeBlock` dùng chung cho 3 bài code (không cần `CodeTabs` join-3-ngôn-ngữ-1-bài — mỗi bài 1 ngôn ngữ riêng để đọc thoải mái hơn, dễ mở rộng thêm ngôn ngữ sau này)
- [ ] (Còn nợ Phase 5, để dành cho Phase 6/7) Tab "Dưới góc nhìn lập trình" xuất hiện trên MỌI bài học khi bật Developer Mode — hiện tại code mode chỉ có ở bài 22-25 riêng biệt

**25/25 bài học đã có nội dung đầy đủ — mạch bài học (Phase 1-5) hoàn tất.**

## Phase 6 — Simulator nâng cao — xong
- [x] Finger CPU Simulator: đủ 7 mode (Địa Chi, Thiên Can, Bát Quái, Hoa Giáp, Cửu Cung, Trường Sinh, Tiết Khí) — mỗi mode 1 component riêng trong `components/fingerCpu/simulatorModes/`
- [x] Simulator phép tính từng bước → gộp vào **Algorithm Visualizer** (tổng quát hơn: chọn được bảng dữ liệu bất kỳ, không chỉ 1 kịch bản cố định)
- [x] Memory Visualizer (`/finger-cpu/memory-visualizer`) — 5 khái niệm (RAM/Pointer/Array/HashMap/Cache), mỗi khái niệm có hành vi tương tác riêng trên bàn tay, không chỉ mô tả chữ
- [x] Algorithm Visualizer (`/finger-cpu/algorithm-visualizer`) — Input→Modulo→Lookup→Result, chọn được Địa Chi/Thiên Can/Bát Quái
- [x] Data Structure Mode (`/finger-cpu/data-structure-mode`) — Array/HashMap/Matrix/Binary/Circular Array/Graph cho cùng 1 dữ liệu
- [x] Debug Mode (`/finger-cpu/debug-mode`) — Step Into (mở từng thao tác trong 1 vòng lặp) / Step Over (chạy trọn 1 vòng) / Continue / Replay, có Call Stack + Watch panel giống IDE thật
- [x] Mục "🧰 Công cụ tương tác" trên trang Intro liệt kê đủ 5 công cụ trên

## Phase 7 — Chế độ & cá nhân hoá — xong
- [x] Store riêng `data/fingerCpu/store.js` (zustand + persist, key `kinhdich-finger-cpu`, tách khỏi store chính của app)
- [x] Developer Mode — toggle trên trang Intro; khi bật, mọi bài học tự hiện card "💻 Dành cho lập trình viên"
- [x] AI Explain — 2 nút "🧠 Giải thích dễ hơn" / "💻 Dành cho lập trình viên" ở `LessonShell`, nội dung viết sẵn cho cả 25 bài (`data/fingerCpu/aiExplain.js`), không gọi AI ngoài
- [x] Search — ô tìm kiếm trên trang Intro, lọc theo tiêu đề/mô tả, ẩn cả nhóm nếu không có bài nào khớp
- [x] Bookmark — nút ⭐ trên từng dòng bài học + trên `LessonShell`, có mục riêng "⭐ Đã đánh dấu" khi có ít nhất 1 bookmark
- [x] Learning Progress — đếm "đã học X/25 bài" (dựa trên `visited`, tự đánh dấu khi mở 1 bài), nhãn "đã học" trên từng dòng đã ghé qua

**Quyết định**: Learning Progress theo TỪNG CHỦ ĐỀ (Địa Chi/Thiên Can/Hoa Giáp riêng biệt) rút gọn thành theo TỪNG BÀI — vì mỗi bài đã gắn 1-1 với 1 chủ đề (bài 4 = Địa Chi, bài 5 = Thiên Can...), tách thêm 1 tầng "chủ đề" sẽ trùng lặp dữ liệu không cần thiết.

## Phase 8 — Mini game — xong
- [x] Finger Memory Trainer (`/finger-cpu/game/ghi-nho`) — "X ở đâu?", chạm đúng/sai, feedback màu xanh/đỏ, đếm điểm
- [x] Speed Challenge (`/finger-cpu/game/toc-do`) — đếm ngược 30s, trắc nghiệm trộn Địa Chi/Thiên Can/Bát Quái, sinh câu hỏi bằng thuật toán (không hardcode bộ câu hỏi)
- [x] Hexagram Builder (`/finger-cpu/game/hexagram-builder`) — 6 hào toggle, tự sinh quẻ ngay khi đổi, tái dùng `trigramFromBits` + `lookupHexagram` đã có sẵn
- [x] Binary Mode (`/finger-cpu/game/binary-mode`) — đếm nhị phân 3-bit (Bát Quái) và 6-bit (64 Quẻ) có Play/Step
- [x] Mục "🎮 Trò chơi" trên trang Intro liệt kê đủ 4 game

---
## Tổng kết

**Tất cả 8 phase đã hoàn thành.** Finger CPU Lab hiện có:
- 25/25 bài học đầy đủ nội dung, tương tác, đúng mạch sư phạm trực quan → trực giác → quy luật → thuật toán → ứng dụng
- 5 công cụ (Simulator 7-mode, Memory/Algorithm Visualizer, Data Structure Mode, Debug Mode)
- 4 mini game
- Developer Mode, AI Explain (2 lăng kính), Search, Bookmark, Learning Progress
- Toàn bộ dữ liệu tách riêng trong `src/data/fingerCpu/*.js`, phần lớn sinh bằng thuật toán (Hoa Giáp, Hà Đồ, 64 Quẻ generator) thay vì hardcode danh sách
- Kiến trúc component hoá, tái dùng tối đa dữ liệu Bát Quái/64 Quẻ đã có sẵn trong app gốc (`baquai.js`, `hexagrams.js`) thay vì tạo bản sao

**Việc còn lại nếu muốn mở rộng sau này** (không phải nợ, chỉ là hướng mở rộng tự nhiên theo đúng kiến trúc đã xây):
- Kỳ Môn/Lục Nhâm/Thái Ất mới dừng ở mức giới thiệu — muốn học sâu hơn thì thêm bài/module riêng, không cần sửa framework hiện có
- Chưa có unit test tự động cho các hàm sinh dữ liệu (generateHoaGiap, magicSquareSums...) — hiện chỉ verify thủ công + qua build

**Trạng thái:** Cả 8 phase hoàn tất — Finger CPU Lab đã sẵn sàng dùng thử toàn bộ.

=================================================

# 📜 Chu Dịch Nguyên Tác — kế hoạch triển khai

Module thứ 2, đặt sau Finger CPU Lab trong menu. Mục tiêu: giúp người học đọc được
Chu Dịch nguyên bản (chữ Hán + phiên âm Hán Việt + dịch nghĩa) và hiểu vì sao người
xưa viết như vậy — KHÔNG phải bói toán, KHÔNG cần biết chữ Hán trước.

**Ràng buộc quan trọng khác hẳn Finger CPU Lab:** phần nguyên tác (卦辭/爻辭) không được
tự sáng tác. Quy trình: dùng WebSearch/WebFetch tra cứu văn bản gốc từ nguồn học thuật
công khai (ctext.org — Chinese Text Project, có bản dịch James Legge 1899 public domain;
đối chiếu chéo với zh.wikisource.org) trước khi đưa vào data, ghi nguồn trong field
`references` của từng quẻ. Với các quẻ về sau nếu độ tin cậy trí nhớ không đủ 100%,
BẮT BUỘC phải tra cứu lại bằng WebFetch/WebSearch trước khi viết, không suy diễn.

Quy ước kỹ thuật:
- Route: `/chu-dich` (module home: lưới 64 quẻ + search + bookmark + daily quote),
  `/chu-dich/que/:id` (chi tiết 1 quẻ — gồm đủ mọi mục trong "MỖI QUẺ PHẢI CÓ")
- Data: `src/data/chu-dich/hexagram-01.json` .. `hexagram-64.json` (JSON thuần theo
  đúng yêu cầu người dùng — khác Finger CPU Lab vì đây là nội dung tham khảo tĩnh,
  không cần sinh bằng thuật toán) + `src/data/chu-dich/index.js` tổng hợp import + registry
- Pages nằm phẳng trong `src/pages/`: `ChuDichIntroPage.jsx`, `ChuDichHexagramPage.jsx`
- "Thoán Từ", "Hào Từ", "Thập Dực", "Giải mã chữ Hán", "So sánh bản dịch", "Ứng dụng
  hiện đại" trong bản gốc yêu cầu đọc là các MỤC/TAB bên trong trang chi tiết 1 quẻ
  (không phải 7 trang con riêng biệt — hợp lý hơn vì nội dung luôn gắn với 1 quẻ cụ thể)
- Liên kết chéo: mỗi quẻ trỏ được sang bài học Finger CPU (Bát Quái/64 Quẻ) và trang
  `/que/:so` (64 Quẻ hiện có) qua field `relatedLessons`

## Phase 1 — Kiến trúc + Quẻ mẫu (Càn) — xong
- [x] Tra cứu + đối chiếu chéo văn bản gốc Quẻ 1 Càn qua WebSearch/WebFetch (ctext.org + wikisource, khớp 100% với trí nhớ — độ tin cậy cao)
- [x] Schema JSON cho 1 quẻ (`id, hanzi, pinyin, hanviet, english, judgment{}, daTuong{}, meaning, computer_science, life, programming, characters[], yao[], keywords[], references[], relatedLessons[]`)
- [x] `hexagram-01.json` (Càn) — đầy đủ mọi mục theo yêu cầu
- [x] `registry.js` — danh sách 64 quẻ (tái dùng `HEXAGRAMS` có sẵn cho id/tên, tránh trùng data)
- [x] Component `HexagramCharacterCard`
- [x] `ChuDichIntroPage.jsx` — giới thiệu + cam kết nguồn + lưới 64 quẻ
- [x] `ChuDichHexagramPage.jsx` — đầy đủ Thoán Từ/Đại Tượng/giải thích/giải mã chữ/CS/đời sống/lập trình/từng hào/liên kết/nguồn tham khảo (thu gọn)
- [x] Menu "📜 Chu Dịch Nguyên Tác" trong Navbar, sau "🖐️ Finger CPU Lab"
- [x] Route trong `App.jsx`
- [x] Build (140 module) + smoke test HTTP 200

## Phase 2+ (chưa làm — sẽ báo cáo lại sau Phase 1 rồi tiếp tục)
- [ ] Batch quẻ tiếp theo: 7 quẻ thuần còn lại (Khôn, Khảm, Ly, Chấn, Tốn, Cấn, Đoài) — tái dùng cấu trúc Càn, MỖI quẻ đều cần tra cứu WebFetch riêng, không suy ra từ Càn
- [ ] Các batch 56 quẻ còn lại (chia nhóm 8, mỗi nhóm 1 phase — quy mô lớn, cần nhiều phase)
- [ ] Mở rộng "Giải mã chữ Hán" ra ngoài phạm vi 4 chữ Nguyên/Hanh/Lợi/Trinh — về sau
- [ ] "So sánh bản dịch" — cần tra cứu thêm ít nhất 1-2 nguồn dịch độc lập khác Legge trước khi làm (hiện mới có 1 nguồn đã verify)
- [ ] Sơ đồ tư duy (mindmap), Dòng thời gian, "Bản gốc" (chế độ Dark/Sepia/Paper), Nghe (audio)
- [ ] Quiz, Flashcard, Search, Bookmark, Học mỗi ngày (Daily Quote), Developer Mode, AI Explain, Animation highlight từng chữ/câu, Lịch sử — nhóm tính năng này giống hệt pattern Phase 6-8 của Finger CPU Lab, làm sau khi đủ data quẻ

**Lưu ý quy mô:** làm đúng chuẩn cho cả 64 quẻ (mỗi quẻ ~6-7 hào + giải mã chữ Hán +
đối chiếu nguồn) là khối lượng nội dung lớn hơn nhiều so với 25 bài Finger CPU Lab.
Sẽ triển khai cuốn chiếu nhiều phase, báo cáo sau mỗi phase thay vì làm 1 lần.
