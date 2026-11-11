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

1. Pi 4 và điện thoại cùng online.
2. Đăng nhập khách → chọn **2 đền** → gói lễ → "Phát ngay" (hoặc hẹn giờ) → thanh toán.
3. Cả hai loa đọc cùng một giờ (cách nhau vài chục mili-giây tới ~1 giây). Hai camera quay mâm.
4. Mở **Lịch sử lễ → Lễ đồng thời tại 2 nơi**: thấy dòng "✔ Đã khấn đồng thời tại 2 nơi, lệch x giây", hai video/ảnh cạnh nhau.

## Giới hạn đã biết

- Điện thoại phải giữ trang mở ở foreground; khóa màn hình hoặc Chrome bị hệ điều hành tạm dừng thì thiết bị mất kết nối (server báo offline).
- Giờ phát do thiết bị tự báo. Pi cần đồng bộ NTP; điện thoại dùng giờ server nên luôn đúng.
- Điện thoại phải truy cập server bằng HTTPS (camera và micro yêu cầu).
