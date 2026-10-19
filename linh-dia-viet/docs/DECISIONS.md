# Quyết định thiết kế

Ghi lại các chỗ đặc tả còn mơ hồ và phương án (đơn giản nhất) đã chọn.

## Chung
- **Vị trí mã nguồn:** repo hiện tại là trang Kinh Dịch (Vite + React). Theo đặc tả, dự án nằm trong thư mục mới
  `linh-dia-viet/`, không sửa code Kinh Dịch có sẵn. Làm trên nhánh `feat/linh-dia-viet`.
- **Ghép với trang Kinh Dịch:** chọn "liên kết + proxy" (theo trả lời của chủ dự án). App FastAPI chạy độc lập,
  toàn bộ route dưới `APP_PREFIX` (mặc định `/le-chua`), nginx proxy cùng domain; trang Kinh Dịch chỉ thêm link.
  Header/footer là partial riêng (`_header.html`, `_footer.html`), mọi CSS nằm dưới lớp `.ld`.
- **Đăng nhập:** theo đặc tả (mật khẩu argon2 + OTP giả lập in ra log). Firebase SSO của tuandv.id.vn để sau.
- **Frontend:** Jinja2 + HTMX (đóng gói sẵn trong `static/`, không phụ thuộc CDN) + JS thuần cho ghi âm.
- **Rate limit:** bộ nhớ trong tiến trình (chỉ đúng khi chạy 1 tiến trình API). IP lấy từ `request.client`,
  sau reverse proxy thì bật `--proxy-headers --forwarded-allow-ips` của uvicorn.
- **Thời gian:** DB lưu UTC (`UTCDateTime` luôn trả datetime có múi giờ).

## Vai trò người dùng (bổ sung theo yêu cầu)
Bốn vai trò trong `users.role`:
| Vai trò | Ý nghĩa | Quyền (M1) |
|---|---|---|
| `customer` | Khách hàng đặt lễ | Đặt lễ, xem đơn của mình |
| `vendor` | Người bán hàng kiosk tại đền, chuẩn bị mâm lễ | Quản lý gói lễ (mâm lễ) của đền mình phụ trách |
| `temple_manager` | Người quản lý đền/chùa | Sửa thông tin đền mình phụ trách + gói lễ của đền |
| `admin` | Quản trị hệ thống | Toàn quyền, gán vai trò và đền cho nhân sự |

- Liên kết nhân sự ↔ đền qua bảng `temple_staff` (một người có thể phụ trách nhiều đền).
- Nhân sự đền không tạo được gói "dùng chung", không đổi thiết bị/trạng thái/đường dẫn của đền.
- Đăng ký công khai luôn là `customer`; chỉ admin nâng quyền. Tài khoản bị khóa (`active=false`) không đăng nhập được.
- Ở các mốc sau: nhân sự đền xem lịch lễ của đền mình (vendor không thấy dữ liệu cá nhân của khách),
  `temple_manager` được từ chối đơn (`rejected`).

## M2 – Đặt lễ & sớ
- **Âm lịch:** tự cài thuật toán Hồ Ngọc Đức (UTC+7) thay vì thư viện âm lịch Trung Quốc (UTC+8 lệch Tết 1985…).
  Có test với Tết 1985, 2000, 2007, 2020, 2023–2026, các tháng nhuận 2020/2023/2025 và Trung thu 2024.
  Phát hiện: `src/data/amlich.js` của trang Kinh Dịch gõ sai dấu ở công thức `newMoon` (`C -= a + b` thay vì `C = C - a + b`),
  có thể lệch ngày quanh điểm sóc. Không sửa vì nằm ngoài phạm vi; ghi lại để xử lý riêng.
- **Năm sinh** coi là năm âm lịch (can chi tính trực tiếp từ năm nhập).
- **Ngày trong sớ** (`{ngay_am}`, `{ngay_duong}`) là ngày làm lễ (giờ hẹn theo giờ Việt Nam), không phải ngày đặt.
- **Sớ khi đặt nhiều đền:** mỗi đơn có văn bản/audio riêng (`orders.script_text`, `orders.audio_key`) vì sớ chứa tên đền.
  Nếu khách không sửa → mỗi đền dùng mẫu của đền đó. Nếu sửa → văn bản sửa dùng cho mọi đền, các biến
  `{ten_den}`, `{than_linh}`, `{dia_chi_den}` được giữ lại và điền theo từng đền.
- **"Sửa nhẹ":** tối đa `MAX_PRAYER_CHARS` (3000) ký tự và không dài hơn 1,5× bản gốc + 300 ký tự; không cho biến lạ.
- **Gói lễ khi đặt nhiều đền:** chỉ chọn được gói dùng chung; gói riêng của đền chỉ hiện khi đặt 1 đền.
- **Một giờ hẹn cho mọi đền** trong một lần đặt.
- **Thanh toán:** mỗi đơn 1 `payment`, các payment của 1 lần đặt chung `txn_ref` để trả một lần. Trang giả lập gọi cùng
  hàm xử lý với webhook (`/api/thanh-toan/webhook/{provider}`, ký HMAC). Thanh toán xong mà đơn đã hủy → `refund_requested`.
- **Xếp lịch:** `paid → scheduled` ngay khi bài khấn được duyệt và audio đã tạo; TTS lỗi → giữ `paid` để thử lại.
- **Khách tự hủy** được tới trước giờ gửi lệnh xuống thiết bị (`giờ hẹn − DISPATCH_LEAD_SECONDS`). Đơn đã trả tiền
  bị hủy/từ chối tự chuyển `refund_requested`; admin bấm "Đã hoàn tiền" → `refunded`.
- **`played → completed`** được phép trực tiếp (khi hết thời gian chờ ảnh, camera lỗi) — ngoài luồng chính của đặc tả.
- **`failed → scheduled`** cho nút "gửi lại job" của admin.
- **Bảng thêm:** `order_events` (dòng thời gian), `prayer_templates` (mẫu chung + mẫu riêng từng đền).
- **Theo dõi đơn:** polling HTMX mỗi 3 giây (đơn giản hơn SSE, đủ "gần tức thì").
- **Nhân sự đền:** xem "Lịch lễ" của đền mình (giờ, gói lễ, trạng thái), không thấy dữ liệu cá nhân. Kiosk bấm
  "Mâm lễ đã bày" (`orders.tray_ready_at`, không thêm trạng thái). Quản lý đền được từ chối đơn và sửa mẫu sớ riêng.
- **TTS:** `edge` mặc định; `google` (REST + API key) và `fpt` (v5, URL bất đồng bộ) đã viết nhưng **chưa thử với tài khoản thật**.
  `fake` (âm báo) dùng cho test. Văn bản dài được cắt theo câu rồi nối bằng ffmpeg.
