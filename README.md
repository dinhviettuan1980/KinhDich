# KinhDich — Học tư duy biến đổi 🧭

Ứng dụng học **Kinh Dịch trong 30 ngày**, viết cho kỹ sư IT: giải thích bằng analogy lập trình / hệ thống / quản lý dự án, **không bói toán** — tập trung vào khung tư duy về sự biến đổi.

- **Live:** https://kinhdich.tuandv.id.vn
- **Frontend:** repo này (Vite + React + Tailwind + Zustand + React Router)
- **Backend:** nằm trong `xsmbapi/kinhdich/` (Express + SQLite), phục vụ tại `/kinhdich` (proxy `:8001`)

---

## 1. Chức năng đã triển khai

### Học tập
- **30 bài học** chia 7 cấp độ; mỗi bài có giải thích sâu, ví dụ đời thực, ví dụ CNTT, gợi ý minh hoạ, **3 câu quiz**.
- **Quiz tương tác**: chọn đáp án → phản hồi đúng/sai ngay + giải thích → tính điểm (0–100).
- **Hexagram SVG**: vẽ quẻ Bát Quái động cho bài Level 4–5.
- **Bản đồ 30 ngày**: nhìn toàn cảnh lộ trình & trạng thái từng bài.

### Tiến độ & gamification
- Lưu tiến độ theo người dùng (bài hoàn thành + điểm + ngày).
- **Streak** — chuỗi ngày học liên tiếp (theo giờ VN).
- **Khoá/mở bài tuần tự**: xong bài trước mới mở bài sau.
- Thanh % hoàn thành + thống kê "đã học / còn lại / chuỗi".

### Tài khoản (đăng nhập)
- **Google** (thật — dùng chung client ID hệ sinh thái tuandv.id.vn; cần thêm origin trong Google Console).
- **Facebook** (đã wire SDK — cần `VITE_FB_APP_ID` mới chạy).
- **User/Password** (đăng ký + đăng nhập thật, lưu SQLite, hash SHA‑256).
- **Admin** (`admin` / `123456`): mở khoá toàn bộ 30 bài để xem hết.
- Tiến độ gắn theo danh tính; đăng xuất → về chế độ khách.

### AI Tutor
- Khung chat hỏi đáp Kinh Dịch, **stream SSE** từ Claude (`claude-haiku-4-5`).
- *Hiện tắt* (chưa có `ANTHROPIC_API_KEY`); bật lại chỉ cần thêm key vào `.env` server.

### Khác
- Dark mode (lưu localStorage), responsive, animation.
- Hạ tầng: FE tĩnh (nginx + HTTPS Let's Encrypt), BE chung process `xsmbapi` (pm2), proxy `/kinhdich` → `:8001`.

---

## 2. Sitemap

### Frontend (React Router)
| Route | Trang | Mô tả |
|-------|-------|------|
| `/` | Dashboard | Tổng quan tiến độ, CTA học bài hôm nay, danh sách theo level |
| `/learn/:day` | LearnPage | Nội dung bài học đầy đủ |
| `/quiz/:day` | QuizPage | Làm quiz + màn hình kết quả |
| `/tutor` | TutorPage | Chat AI Tutor |
| `/map` | MapPage | Bản đồ 30 ngày |

### Backend API (prefix `/kinhdich`)
| Method | Endpoint | Mô tả |
|--------|----------|------|
| GET | `/lessons` | Danh sách bài (metadata, **không lộ đáp án**) |
| GET | `/lessons/:day` | Bài đầy đủ (kèm quiz) |
| GET | `/progress/:userId` | Tiến độ + streak của user |
| POST | `/progress` | Đánh dấu hoàn thành `{userId, day, score}` |
| POST | `/register` | Đăng ký `{username, password}` |
| POST | `/login` | Đăng nhập `{username, password}` → `{username, isAdmin}` |
| POST | `/tutor` | Chat AI (SSE stream) — *đang tắt* |

---

## 3. Database schema (SQLite, chung `data.sqlite`)

```sql
-- Tiến độ học
CREATE TABLE kinhdich_progress (
  userId       TEXT    NOT NULL,   -- google:email | fb:id | user:tên | <uuid khách>
  day          INTEGER NOT NULL,   -- 1..30
  score        INTEGER NOT NULL DEFAULT 0,   -- 0..100, giữ điểm cao nhất
  completedAt  TEXT    NOT NULL,   -- ISO timestamp
  PRIMARY KEY (userId, day)
);

-- Tài khoản user/password
CREATE TABLE kinhdich_users (
  username   TEXT    PRIMARY KEY,  -- chữ thường, >= 3 ký tự
  passhash   TEXT    NOT NULL,     -- SHA-256(password)
  isAdmin    INTEGER NOT NULL DEFAULT 0,
  createdAt  TEXT    NOT NULL
);
-- Seed sẵn: admin / 123456 (isAdmin=1)
```

> Google/FB không tạo bản ghi `kinhdich_users` — danh tính lấy từ token, chỉ dùng làm `userId` cho tiến độ.

---

## 4. Cấu trúc một bài học (`xsmbapi/kinhdich/lessons.js`)

```js
{
  day: 1, level: 1,
  title: "Kinh Dịch là gì? Không phải bói toán",
  concept: "...",          // tóm tắt 1 câu
  explanation: `...`,      // giảng nhiều đoạn (tách bằng \n\n)
  realExample: `...`,      // ví dụ đời thực
  techExample: `...`,      // ví dụ CNTT / quản lý dự án
  imageHint: `...`,        // gợi ý minh hoạ
  quiz: [                  // đúng 3 câu
    { question, options: [4 lựa chọn], correct: 0..3, explanation }
  ]
}
```

**7 cấp độ / 30 ngày:**

| Level | Tên | Ngày |
|-------|-----|------|
| 1 | Nền tảng (3 nghĩa của Dịch) | 1–5 |
| 2 | Âm Dương | 6–10 |
| 3 | Tứ Tượng | 11–12 |
| 4 | Bát Quái | 13–17 |
| 5 | 64 Quẻ | 18–22 |
| 6 | Hào & Quẻ Biến | 23–26 |
| 7 | Ứng Dụng (lãnh đạo, kinh doanh, CNTT, ra quyết định) | 27–30 |

---

## 5. Learning flow

```
Dashboard  ──pick bài hôm nay──▶  LearnPage (/learn/:day)
   ▲                                  │  đọc: giải thích · ví dụ thực · ví dụ CNTT
   │                                  │  (quẻ SVG cho Level 4–5)
   │                                  ▼  "Làm quiz →"
   │                              QuizPage (/quiz/:day) → QuizFlow
   │                                  │  3 câu: chọn → feedback + giải thích ngay
   │                                  ▼  hết câu → score = đúng/tổng × 100
   │                          POST /progress (markComplete day, score)
   │                                  │  (lưu DB, cập nhật streak, mở bài kế)
   └────────── "Về Dashboard" ◀── Màn kết quả (🎉/👍/📚 + điểm)
```

- **Mở khoá:** ngày 1 luôn mở; ngày N mở khi ngày N‑1 hoàn thành. **Admin mở hết.**
- **Điểm** lưu là **cao nhất** giữa các lần làm lại.

---

## 6. Roadmap

**Ngắn hạn (đang dang dở):**
- [ ] Thêm origin `https://kinhdich.tuandv.id.vn` trong Google Console (bật Google login).
- [ ] Bật AI Tutor: thêm `ANTHROPIC_API_KEY` trên server.
- [ ] Tạo Facebook App → `VITE_FB_APP_ID`.
- [ ] GitHub Action auto-deploy cho FE (thay scp tay).

**Trung hạn:**
- [ ] Trang hồ sơ / giấy chứng nhận khi hoàn thành 30 ngày.
- [ ] Ôn tập theo lịch (spaced repetition) cho câu quiz sai.
- [ ] Bảng xếp hạng / huy hiệu theo streak & điểm.
- [ ] Trang admin quản trị nội dung + thống kê người học.
- [ ] Tra cứu đầy đủ 64 quẻ + công cụ gieo quẻ minh hoạ.

**Dài hạn:**
- [ ] Bảo mật thật: JWT/session, salt mật khẩu (hiện SHA‑256 trần).
- [ ] Đồng bộ tiến độ đa thiết bị (gộp dữ liệu khách khi đăng nhập).
- [ ] App mobile (Capacitor) hoặc PWA offline.
- [ ] Đa ngôn ngữ, nội dung audio/video.

---

## Phát triển cục bộ

```bash
npm install
npm run dev          # http://localhost:3003
```

`vite.config.js` proxy `/kinhdich` → backend prod (`https://api.tuandv.id.vn`) để chạy FE local không cần backend. Đổi về `http://localhost:8001` nếu chạy backend ngay trên máy.

## Deploy (thủ công, hiện tại)

```bash
npm run build
scp -r dist/* <server>:/var/www/kinhdich/
```

Nginx vhost `kinhdich.tuandv.id.vn` serve static (`try_files … /index.html`) + proxy `/kinhdich` → `127.0.0.1:8001`. HTTPS qua certbot (tự gia hạn).
