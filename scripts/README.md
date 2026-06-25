# Script crawl 64 quẻ (dữ liệu cho trang 📖 64 Quẻ)

Crawl nội dung 64 quẻ từ kabala.vn → `public/data/que.json`. Chạy 1 lần, dùng offline.
Chỉ dùng cá nhân/học tập (mỗi quẻ ghi rõ nguồn ở UI).

## Chạy lại
```bash
npm i -D cheerio        # parser HTML (chỉ cần khi crawl)
node scripts/crawl-all.mjs   # ghi đè public/data/que.json
```

- `parse.mjs` — tách 1 trang HTML thành { so, ten, trieu, blocks[] }.
- `crawl-all.mjs` — lấy 64 slug từ trang chủ, tải từng trang (delay 0.5s), parse, ghi JSON.

> Quẻ 58 (Thuần Đoài) trên kabala thiếu phần chi tiết → đã vá thủ công bằng kinh văn cổ
> (public domain). Nếu crawl lại, nhớ vá lại quẻ 58 hoặc giữ bản hiện có.
