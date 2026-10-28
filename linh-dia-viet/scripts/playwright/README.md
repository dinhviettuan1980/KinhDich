# Playwright: video demo và soát giao diện iPhone (chạy trên production)

```bash
cd scripts/playwright
npm install && npx playwright install chromium
node iphone.js      # đăng ký tài khoản thử → chụp các màn hình chính khổ iPhone 13 vào iphone/, báo tràn ngang
node record.js      # quay toàn bộ quy trình khách (đăng ký → thẻ → đặt lễ → chờ Pi → xem lại) vào out/
python build.py     # dựng video demo cuối: tiêu đề + quay màn hình (đoạn chờ tua ×4) + clip tại đền (cần ffmpeg, Pillow)
```

Dùng Chromium đi kèm Playwright. Chrome thật quay bị dải xám dưới đáy; Chromium không phát được H.264 nên clip được ghép vào cuối ở bước `build.py`.
Mỗi lần chạy tạo một tài khoản thử `@example.com` và một đơn thật ở Đền Ngọc Sơn: thiết bị `pi-demo-01` phải đang online.
