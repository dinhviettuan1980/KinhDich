# Demo khấn đồng thời tại 2 nơi: Pi 4 + điện thoại Samsung (và Pi Zero)

Một lần đặt chọn 2 đền → hệ thống tạo 2 đơn **cùng giờ phát**, mỗi đền một thiết bị. Khách xem ở **Lịch sử lễ → "Lễ đồng thời"**
hai nơi cạnh nhau: giờ bắt đầu đọc sớ do chính thiết bị báo, độ lệch (giây), ảnh và video mâm lễ.

## Thiết bị

| Nơi | Thiết bị | Loa | Camera |
|---|---|---|---|
| Đền A | Pi 4 (`pi-agent`) | loa Bluetooth / jack 3.5 mm | webcam USB |
| Đền B | **Điện thoại Android** (trang `/le-chua/may`) | loa máy, Bluetooth hoặc dây 3.5 mm cắm vào điện thoại | camera sau + micro của máy |
| Đền C (sau) | Pi Zero 2 W | card âm thanh USB → dây 3.5 mm (Pi Zero không có jack) | webcam USB qua hub |

## Cài điện thoại (làm một lần)

1. Admin → **Thiết bị** → tạo thiết bị mới (vd `phone-demo-01`), sao chép token. Gắn thiết bị vào đền B (Admin → Đền).
2. Trên điện thoại mở Chrome: `https://<domain>/le-chua/may#id=phone-demo-01&token=<token>` (hoặc nhập tay).
3. Bấm **Bắt đầu nhận lệnh**, cho phép camera/micro. Cắm sạc, để màn hình sáng, **không đóng trang**, tắt tự khóa màn hình.
4. Đặt điện thoại hướng camera sau vào mâm lễ; loa đã nối với điện thoại.
5. Admin → Thiết bị: thấy điện thoại **online**; bấm "Phát âm thử" để nghe thử, "Chụp thử" để xem khung hình.

Điện thoại tự đổi giờ theo server (hiển thị "lệch giờ với server"), nên không phụ thuộc đồng hồ máy. Chrome 126+ quay MP4 trực tiếp;
bản cũ quay WebM và server tự đổi sang MP4.

## Chạy demo

1. Pi 4 và điện thoại cùng online; bấm "Phát âm thử" cho cả hai để chắc có tiếng.
2. Đăng nhập khách → chọn **2 đền** → gói lễ → "Phát ngay" (hoặc hẹn giờ) → thanh toán.
3. Cả hai loa đọc cùng một giờ (cách nhau vài chục mili-giây tới ~1 giây). Hai camera quay mâm.
4. Mở **Lịch sử lễ → Lễ đồng thời tại 2 nơi**: thấy dòng "✔ Đã khấn đồng thời tại 2 nơi, lệch x giây", hai video/ảnh cạnh nhau.

## Kết quả chạy thật

| Ngày | Lần đặt | Đền A (Pi 4, loa Bluetooth, webcam USB) | Đền B (Samsung Galaxy A5, Chrome) | Độ lệch giờ bắt đầu |
|---|---|---|---|---|
| 12/11/2026 | `60AC75716ABC` | bắt đầu 00:37:13.877, xong 00:38:00, 3 ảnh + video | bắt đầu 00:37:13.743, xong 00:38:00, 2 ảnh | **0,13 giây** |

Trang "Lễ đồng thời" hiện "✔ Đã khấn đồng thời tại 2 nơi … lệch nhau 0.1 giây"; cả hai đơn `completed`.
Môi trường: server chạy trên máy Windows (venv), điện thoại vào qua Cloudflare Tunnel (HTTPS), Mosquitto chạy trên Pi.

## Điều rút ra khi chạy thật

- **Đồng hồ server phải đồng bộ NTP.** Pi phát theo giờ NTP, điện thoại phát theo giờ server. Máy Windows chạy server từng
  nhanh 35 giây (nguồn giờ "Local CMOS Clock") → hai nơi lệch đúng 35 giây. Sửa: bật `w32time`, chỉnh giờ theo NTP.
- **Điện thoại đời cũ treo trang khi quay video** (`MediaRecorder`): lúc bắt đầu quay và lúc dừng/gửi video. Trang giờ
  phát bài khấn trước rồi mới quay, quay ở 640×480; máy vẫn yếu thì **tắt quay video từ xa** (Admin → Thiết bị →
  "🎥 Tắt quay video") — máy vẫn phát và chụp ảnh trước/trong/sau lễ, video lấy từ Pi.
- **Camera đứng hình** sau khi màn hình tắt / trang bị ẩn: ảnh chụp lặp lại y hệt. Trang kiểm tra khung hình còn chạy
  trước mỗi lần chụp/quay và tự mở lại camera.
- Điện thoại đặt trên giá ngược chiều mâm → **đổi camera trước/sau từ xa** (Admin → Thiết bị) hoặc nút "🔄 Đổi camera"
  trên trang `/may`, hoặc thêm `&cam=user` vào link.
- Không xem được màn hình điện thoại → trang gửi **bước đang làm + 20 dòng nhật ký** mỗi lần hỏi lệnh; xem ở Admin →
  Thiết bị → "Nhật ký điện thoại".
- Loa Bluetooth tự tắt khi để lâu không dùng: bật lại loa và bấm "Phát âm thử" trước mỗi buổi demo.

## Giới hạn đã biết

- Điện thoại phải giữ trang mở ở foreground; khóa màn hình hoặc Chrome bị hệ điều hành tạm dừng thì thiết bị mất kết nối (server báo offline).
- Giờ phát do thiết bị tự báo. Pi cần đồng bộ NTP; điện thoại dùng giờ server nên luôn đúng.
- Điện thoại phải truy cập server bằng HTTPS (camera và micro yêu cầu).
