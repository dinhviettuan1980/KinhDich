# KinhDich — Học tư duy biến đổi 🧭

Ứng dụng học **Kinh Dịch trong 30 ngày**, viết cho người phổ thông / kinh doanh / kỹ sư IT: giải thích bằng analogy đời sống · quản lý · lập trình, **không bói toán** — tập trung vào khung tư duy về sự biến đổi và **ứng dụng vào quyết định hằng ngày**.

- **Live:** https://kinhdich.tuandv.id.vn
- **Frontend:** repo này (Vite + React + Tailwind + Zustand + React Router)
- **Backend:** nằm trong `xsmbapi/kinhdich/` (Express + SQLite), phục vụ tại `/kinhdich` (proxy `:8001`)

---

## 1. Chức năng

### Học tập
- **30 bài học** chia 7 cấp độ; mỗi bài có giải thích sâu, **ví dụ theo 3 góc nhìn** (đời thực / kinh doanh / CNTT), câu hỏi suy ngẫm, gợi ý minh hoạ, **3 câu quiz**.
- **Quiz tương tác**: chọn đáp án → phản hồi đúng/sai ngay + giải thích → tính điểm (0–100).
- **Hexagram SVG**: vẽ quẻ Bát Quái động cho bài Level 4–5.

### 🧭 Learning Lens (góc nhìn học)
- Lần đầu chọn 1 trong 3 góc nhìn: **🌿 Cuộc sống · 📈 Quản lý & Kinh doanh · 💻 CNTT**.
- Trong bài học, ví dụ hiển thị theo góc nhìn đã chọn (mở sẵn); hai góc còn lại nằm trong accordion "Xem góc nhìn khác".
- Đổi góc nhìn bất cứ lúc nào qua nút trên thanh điều hướng. Lưu vào hồ sơ người dùng.

### 🪷 Reflection & 👁️ Daily Observation
- **Suy ngẫm cuối bài**: mỗi bài có câu hỏi gợi mở → người học viết lại quan sát của mình (lưu DB).
- **Nhật ký suy ngẫm** (`/reflection`): timeline toàn bộ suy ngẫm — để nhìn thấy chính mình thay đổi theo thời gian.
- **Quan sát hôm nay** (`/observe`): mỗi ngày ghi 3 dòng chảy — 🌱 đang tăng trưởng · 🍂 đang suy giảm · 🔄 đang chuyển hóa.

### 🧩 Case Study Mode (`/cases`)
- **30 tình huống** thực tế; chọn đáp án → xem lời giải bằng tư duy Kinh Dịch + khái niệm liên quan.

### 🤖 AI Tutor (2 chế độ)
- **💡 Giải thích**: trả lời trực tiếp. **🤔 Socrates**: đặt câu hỏi ngược để người học tự khám phá.
- Stream SSE từ Claude (`claude-haiku-4-5`). *Cần `ANTHROPIC_API_KEY` trên server để chạy.*

### Tiến độ & tài khoản
- Lưu tiến độ theo người dùng (bài hoàn thành + điểm + ngày), **streak**, **khoá/mở bài tuần tự**.
- **Journey Map** (`/map`): bản đồ 30 ngày theo 7 chặng có biểu tượng.
- Đăng nhập: **Google** (thật) · **Facebook** (cần `VITE_FB_APP_ID`) · **User/Password** (đăng ký thật, SQLite, hash SHA‑256).
- **Admin** (`admin` / `123456`): mở khoá toàn bộ 30 bài.

---

## 2. Sitemap

### Frontend (React Router)
| Route | Trang |
|-------|-------|
| `/` | Dashboard (tiến độ + widget quan sát/suy ngẫm) |
| `/learn/:day` | Bài học (theo lens + ô suy ngẫm) |
| `/quiz/:day` | Quiz + kết quả |
| `/map` | Journey Map 30 ngày |
| `/observe` | Quan sát hôm nay |
| `/cases` | Tình huống thực tế |
| `/reflection` | Nhật ký suy ngẫm |
| `/tutor` | AI Tutor (Giải thích / Socrates) |

### Backend API (prefix `/kinhdich`)
| Method | Endpoint | Mô tả |
|--------|----------|------|
| GET | `/lessons` · `/lessons/:day` | Danh sách / chi tiết bài (kèm businessExample + reflection) |
| GET · POST | `/progress/:userId` · `/progress` | Tiến độ + streak |
| GET · PUT | `/profile/:userId` | Learning Lens (kèm cờ `chosen`) |
| POST · GET | `/reflections` · `/reflections/:userId` | Suy ngẫm |
| POST · GET | `/observations` · `/observations/:userId[/today]` | Quan sát hằng ngày |
| GET | `/cases` · `/cases/:id` | Tình huống (list ẩn đáp án) |
| POST | `/register` · `/login` | Tài khoản user/pass |
| POST | `/tutor` | AI Tutor SSE (`mode`: explain/socratic) |

---

## 3. Database schema (SQLite, chung `data.sqlite`)

```sql
CREATE TABLE kinhdich_progress (
  userId TEXT, day INTEGER, score INTEGER DEFAULT 0, completedAt TEXT,
  PRIMARY KEY (userId, day)
);
CREATE TABLE kinhdich_users (
  username TEXT PRIMARY KEY, passhash TEXT, isAdmin INTEGER DEFAULT 0, createdAt TEXT
);  -- seed: admin / 123456 (isAdmin=1)

-- v2
CREATE TABLE kinhdich_profile (
  userId TEXT PRIMARY KEY, learningLens TEXT DEFAULT 'life'  -- life | business | tech
);
CREATE TABLE kinhdich_reflections (
  id INTEGER PRIMARY KEY AUTOINCREMENT, userId TEXT, day INTEGER, content TEXT, createdAt TEXT
);
CREATE TABLE kinhdich_observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT, userId TEXT, observeDate TEXT,
  growing TEXT, declining TEXT, transforming TEXT, createdAt TEXT,
  UNIQUE (userId, observeDate)
);
```

> `userId` = `google:email` | `fb:id` | `user:tên` | `<uuid khách>`.

---

## 4. Cấu trúc bài học

`lessons.js` giữ nội dung lõi; `lessons-extra.js` bổ sung `businessExample` + `reflection` cho từng ngày — router merge khi trả bài.

```js
// lessons.js
{ day, level, title, concept, explanation, realExample, techExample, imageHint,
  quiz: [{ question, options:[4], correct:0..3, explanation }] }
// lessons-extra.js
{ [day]: { businessExample, reflection } }
```

**7 cấp độ / 30 ngày:** 🌱 Nền tảng (1–5) · ☯ Âm Dương (6–10) · ⚡ Tứ Tượng (11–12) · 🧭 Bát Quái (13–17) · 🔮 64 Quẻ (18–22) · 🔄 Hào & Quẻ Biến (23–26) · 🏛 Ứng Dụng (27–30).

`cases.js`: 30 tình huống — `{ id, title, concept, scenario, options:[4], correct, explanation }`.

---

## 5. Learning flow

```
(lần đầu) Chọn Learning Lens
        │
Dashboard ──▶ LearnPage (ví dụ theo lens + accordion góc nhìn khác)
        │         │ viết Suy ngẫm (→ Nhật ký)
        │         ▼
        │     Quiz → điểm → markComplete (lưu, streak, mở bài kế)
        ▼
Hằng ngày: 👁️ Quan sát (tăng/giảm/chuyển hóa) · 🧩 Tình huống · 🤔 hỏi AI Tutor
```

- **Mở khoá:** ngày 1 luôn mở; ngày N mở khi N‑1 hoàn thành. **Admin mở hết.**
- **Điểm** lưu là cao nhất giữa các lần làm lại.

---

## 6. Roadmap

**Đã xong (v2):** Learning Lens · Reflection + lịch sử · Daily Observation · Case Study Mode · AI Socrates · Journey Map · Dashboard widgets.

**Cần cấu hình (bên ngoài, do owner):**
- [ ] Thêm origin `https://kinhdich.tuandv.id.vn` trong Google Console (bật Google login).
- [ ] Thêm `ANTHROPIC_API_KEY` trên server (bật AI Tutor — gồm chế độ Socrates).
- [ ] Tạo Facebook App → `VITE_FB_APP_ID`.

**Tiếp theo:**
- [ ] GitHub Action auto-deploy cho FE (thay scp tay).
- [ ] Hồ sơ / chứng nhận hoàn thành 30 ngày · huy hiệu theo streak.
- [ ] Ôn tập theo lịch (spaced repetition) cho quiz/case sai.
- [ ] Trang admin quản trị nội dung + thống kê người học.
- [ ] Tra cứu đầy đủ 64 quẻ.
- [ ] Bảo mật thật (JWT/session, salt) · đồng bộ đa thiết bị · PWA offline.

---

## Phát triển cục bộ

```bash
npm install
npm run dev          # http://localhost:3003
```

`vite.config.js` proxy `/kinhdich` → backend prod (`https://api.tuandv.id.vn`); đổi về `http://localhost:8001` nếu chạy backend local.

## Deploy (thủ công)

```bash
npm run build
scp -r dist/* <server>:/var/www/kinhdich/
```

Nginx vhost `kinhdich.tuandv.id.vn` serve static (`try_files … /index.html`) + proxy `/kinhdich` → `127.0.0.1:8001`. HTTPS qua certbot (tự gia hạn).
