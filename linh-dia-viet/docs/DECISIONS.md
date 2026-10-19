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
