# Tiếp tục làm KinhDich tại nhà

> Paste file này vào chat với Claude là làm tiếp ngay.

---

## Trạng thái hiện tại

### ✅ Đã xong — Frontend `/Users/tuandv/KinhDich`
- Đã push lên https://github.com/dinhviettuan1980/KinhDich
- Vite + React + Tailwind + Zustand + React Router
- Pages: Dashboard, LearnPage, QuizPage, TutorPage, MapPage
- Components: Navbar, DayCard, LevelSection, HexagramSVG, QuizFlow, TutorChat
- Dark mode, responsive, animations

### ✅ Đã xong — Backend `/Users/tuandv/xsmbapi/kinhdich/db.js`
- SQLite helpers: getProgress, markComplete, streak logic

### ❌ Còn thiếu (làm theo thứ tự)
1. `/Users/tuandv/xsmbapi/kinhdich/lessons.js` — nội dung 30 ngày học
2. `/Users/tuandv/xsmbapi/kinhdich/router.js` — Express routes
3. Sửa `/Users/tuandv/xsmbapi/index.js` — đăng ký router
4. Thêm `ANTHROPIC_API_KEY` vào `/Users/tuandv/xsmbapi/.env`

---

## Việc 1: Tạo `lessons.js`

File tại `/Users/tuandv/xsmbapi/kinhdich/lessons.js`

```js
module.exports = [
  {
    day: 1, level: 1,
    title: "Kinh Dịch là gì? Không phải bói toán",
    concept: "Kinh Dịch là hệ thống nhận thức về quy luật biến đổi",
    explanation: `...`,
    realExample: `...`,
    techExample: `...`,
    imageHint: `...`,
    quiz: [
      { question: "...", options: ["A","B","C","D"], correct: 0, explanation: "..." },
      { question: "...", options: ["A","B","C","D"], correct: 2, explanation: "..." },
      { question: "...", options: ["A","B","C","D"], correct: 1, explanation: "..." },
    ]
  },
  // ... 30 objects tổng cộng
]
```

30 ngày theo lịch:

| Day | Level | Title |
|-----|-------|-------|
| 1 | 1 | Kinh Dịch là gì? Không phải bói toán |
| 2 | 1 | "Kinh" và "Dịch" — ý nghĩa từng chữ |
| 3 | 1 | Biến Dịch — mọi thứ đều thay đổi |
| 4 | 1 | Bất Dịch — quy luật không thay đổi |
| 5 | 1 | Giản Dịch — đơn giản hóa phức tạp |
| 6 | 2 | Âm Dương — binary system của người xưa |
| 7 | 2 | Âm cực sinh Dương |
| 8 | 2 | Dương cực sinh Âm |
| 9 | 2 | Âm Dương trong đời sống hàng ngày |
| 10 | 2 | Âm Dương trong CNTT và quản lý dự án |
| 11 | 3 | Tứ Tượng — 4 trạng thái của vạn vật |
| 12 | 3 | Ứng dụng Tứ Tượng vào vòng đời dự án |
| 13 | 4 | Từ Tứ Tượng → Bát Quái (tại sao là 8) |
| 14 | 4 | Càn ☰ và Khôn ☷ — Trời và Đất |
| 15 | 4 | Chấn ☳ và Tốn ☴ — Sấm và Gió |
| 16 | 4 | Khảm ☵ và Ly ☲ — Nước và Lửa |
| 17 | 4 | Cấn ☶ và Đoài ☱ — Núi và Hồ |
| 18 | 5 | Tại sao 8×8 = 64 quẻ |
| 19 | 5 | Cấu tạo quẻ — Thượng quái + Hạ quái |
| 20 | 5 | Đọc tên quẻ — quy tắc đặt tên |
| 21 | 5 | Quẻ Thuần Càn — sức mạnh thuần túy |
| 22 | 5 | Quẻ Thuần Khôn — sự nhu thuận |
| 23 | 6 | Hào là gì — 6 tầng của một quẻ |
| 24 | 6 | Hào Dương và Hào Âm |
| 25 | 6 | Hào động — khi một hào thay đổi |
| 26 | 6 | Quẻ biến — đọc sự chuyển hóa |
| 27 | 7 | Ứng dụng quản trị và lãnh đạo |
| 28 | 7 | Ứng dụng kinh doanh |
| 29 | 7 | Ứng dụng CNTT (DevOps, Agile, Risk) |
| 30 | 7 | Ra quyết định theo tư duy Kinh Dịch |

**Yêu cầu nội dung:** Giải thích như người thầy nói chuyện với kỹ sư IT. Dùng analogy từ code/hệ thống. techExample phải có ví dụ cụ thể (Agile sprint, Git branching, microservice...). Quiz thách thức nhẹ, không trivial. Tiếng Việt tự nhiên.

---

## Việc 2: Tạo `router.js`

File tại `/Users/tuandv/xsmbapi/kinhdich/router.js`

```js
const express = require('express');
const router = express.Router();
const lessons = require('./lessons');
const { getProgress, markComplete } = require('./db');
const axios = require('axios');

// GET /kinhdich/lessons — metadata only (không có quiz answers)
router.get('/lessons', (req, res) => {
  res.json(lessons.map(({ day, level, title, concept }) => ({ day, level, title, concept })));
});

// GET /kinhdich/lessons/:day — full bài học
router.get('/lessons/:day', (req, res) => {
  const lesson = lessons.find(l => l.day === Number(req.params.day));
  if (!lesson) return res.status(404).json({ error: 'Không tìm thấy' });
  res.json(lesson);
});

// GET /kinhdich/progress/:userId
router.get('/progress/:userId', async (req, res) => {
  try {
    res.json(await getProgress(req.params.userId));
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// POST /kinhdich/progress — { userId, day, score }
router.post('/progress', async (req, res) => {
  const { userId, day, score } = req.body;
  try {
    res.json(await markComplete(userId, Number(day), Number(score)));
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// POST /kinhdich/tutor — { userId, message, history[] } → SSE stream
router.post('/tutor', async (req, res) => {
  const { message, history = [] } = req.body;
  const apiKey = process.env.ANTHROPIC_API_KEY;

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  if (!apiKey) {
    res.write('data: {"text":"ANTHROPIC_API_KEY chưa được cấu hình trong .env"}\n\n');
    return res.end();
  }

  try {
    const response = await axios.post(
      'https://api.anthropic.com/v1/messages',
      {
        model: 'claude-haiku-4-5',
        max_tokens: 1024,
        stream: true,
        system: `Bạn là người thầy dạy Kinh Dịch cho kỹ sư IT và người làm kỹ thuật. Giải thích đơn giản, dùng analogy từ lập trình, hệ thống, quản lý dự án. Không bói toán. Tập trung tư duy nhận thức. Trả lời ngắn gọn, như đang trò chuyện.`,
        messages: [
          ...history.map(h => ({ role: h.role, content: h.content })),
          { role: 'user', content: message }
        ]
      },
      {
        headers: {
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'content-type': 'application/json',
        },
        responseType: 'stream'
      }
    );

    response.data.on('data', chunk => {
      const lines = chunk.toString().split('\n');
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6).trim();
        if (data === '[DONE]') { res.write('data: [DONE]\n\n'); continue; }
        try {
          const parsed = JSON.parse(data);
          if (parsed.type === 'content_block_delta' && parsed.delta?.text) {
            res.write(`data: ${JSON.stringify({ text: parsed.delta.text })}\n\n`);
          }
        } catch {}
      }
    });
    response.data.on('end', () => res.end());
    response.data.on('error', () => res.end());
  } catch (e) {
    res.write(`data: ${JSON.stringify({ text: 'Lỗi kết nối AI: ' + e.message })}\n\n`);
    res.end();
  }
});

module.exports = router;
```

---

## Việc 3: Sửa `index.js`

File tại `/Users/tuandv/xsmbapi/index.js`

Tìm dòng này:
```js
const combinationRoute = require('./combination');
```

Thêm ngay bên dưới:
```js
const kinhdichRouter = require('./kinhdich/router');
```

Tìm dòng (khoảng line 25-30, chỗ `app.use` các route đầu tiên):
```js
app.use(combinationRoute);
```

Thêm ngay trước dòng đó:
```js
app.use('/kinhdich', kinhdichRouter);
```

---

## Việc 4: Thêm API key

Mở file `/Users/tuandv/xsmbapi/.env`, thêm dòng:
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
```

---

## Việc 5: Test sau khi xong

```bash
# Restart server
pm2 restart xsmbapi

# Test
curl http://localhost:8001/kinhdich/lessons | python3 -m json.tool | head -30
curl http://localhost:8001/kinhdich/progress/test-user-123
```

---

## Việc 6: Chạy frontend local

```bash
cd /Users/tuandv/KinhDich
npm run dev
# Mở http://localhost:3003
```

---

## Việc 7: Commit & push sau khi hoàn thành

```bash
# Backend
cd /Users/tuandv/xsmbapi
git add kinhdich/ index.js
git commit -m "feat: KinhDich backend complete — lessons, router, AI tutor"

# Frontend (nếu có sửa thêm)
cd /Users/tuandv/KinhDich
git add . && git commit -m "fix: ..." && git push
```

---

## Cấu trúc file cuối cùng

```
/Users/tuandv/xsmbapi/
└── kinhdich/
    ├── db.js       ✅ done
    ├── lessons.js  ❌ cần viết
    └── router.js   ❌ cần viết

/Users/tuandv/KinhDich/       ✅ done, pushed to GitHub
├── src/
│   ├── App.jsx
│   ├── api.js
│   ├── store.js
│   ├── pages/
│   │   ├── Dashboard.jsx
│   │   ├── LearnPage.jsx
│   │   ├── QuizPage.jsx
│   │   ├── TutorPage.jsx
│   │   └── MapPage.jsx
│   └── components/
│       ├── Navbar.jsx
│       ├── DayCard.jsx
│       ├── LevelSection.jsx
│       ├── HexagramSVG.jsx
│       ├── QuizFlow.jsx
│       └── TutorChat.jsx
```
