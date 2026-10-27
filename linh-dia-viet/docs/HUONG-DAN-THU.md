# Hướng dẫn thử trên production (https://tuandv.id.vn/le-chua/)

## Tài khoản thử
Mật khẩu được gửi riêng; đổi được ở menu **Tài khoản**. Tạo thêm bằng:
`python -m app.cli create-user <email> --role customer|vendor|temple_manager|admin [--temple den-ngoc-son]`

| Vai trò | Email |
|---|---|
| Quản trị | tuandv@gmail.com |
| Khách hàng | khachthu@tuandv.id.vn |
| Bán hàng kiosk (Đền Ngọc Sơn) | kiosk.ngocson@tuandv.id.vn |
| Quản lý đền (Đền Ngọc Sơn) | quanly.ngocson@tuandv.id.vn |

## 1. Khách đặt lễ và tự ghi âm
1. Vào https://tuandv.id.vn/le-chua/. Mọi trang đều cần đăng nhập; dùng tài khoản **khachthu**.
2. **Đền chùa → Đền Ngọc Sơn → Chọn gói này và đặt lễ →**. Đền và gói hiện dạng tóm tắt (nút **Đổi** nếu muốn chọn lại).
3. **Tín chủ:** lần đầu nhập họ tên, năm sinh, địa chỉ, nguyện vọng. Thông tin được lưu vào tài khoản; lần sau chỉ hiện tóm tắt,
   bấm **Sửa** khi cần (hoặc sửa ở **Tài khoản**).
4. **Bài khấn:** tờ sớ 📜 tự soạn sẵn. Chọn **Tôi tự đọc và ghi âm**, bấm **● Bắt đầu ghi**, đọc tờ sớ, bấm **■ Dừng**,
   nghe lại, rồi bấm **Dùng bản ghi này** (file lên máy chủ, chuyển thành MP3 chuẩn hoá). Hoặc để **Giọng đọc tự động**.
5. **Khi nào phát:** mặc định **Phát ngay sau khi thanh toán**. Chọn **Hẹn giờ** nếu muốn phát vào giờ khác.
6. **Đặt lễ và thanh toán** → trang thanh toán (có tóm tắt) → **Thanh toán …** (giả lập).
7. Trang đơn tự cập nhật. Với phát ngay: lệnh vào kênh MQTT ngay, Pi tải file và **phát sau khoảng 20 giây**, rồi gửi ảnh → **Hoàn tất**.

## 2. Pi nhận lệnh và phát (hoạt động thế nào)
- Pi luôn giữ kết nối MQTT tới `tuandv.id.vn:8883` (TLS) và nghe kênh riêng `ld/<mã thiết bị>/cmd`.
- **Phát ngay:** server gửi lệnh `play` vào kênh ngay khi thanh toán xong (và khi bản ghi được duyệt nếu bật kiểm duyệt),
  giờ phát = lúc đó + 20 giây. **Hẹn giờ:** gửi lệnh trước giờ khấn 10 phút. Lệnh gồm
  link tải MP3 (có chữ ký, hạn 1 giờ), mã sha256, giờ phát và âm lượng.
- Pi tải MP3 về ngay, kiểm tra sha256 rồi báo "đã tải". Nó chụp ảnh "trước", **đúng giờ thì phát ra loa**,
  chụp ảnh lúc bắt đầu, và chụp ảnh "sau" 30 giây sau khi phát xong. Ảnh được gửi về server.
- Mất mạng sau khi đã tải xong thì Pi vẫn phát đúng giờ, có mạng lại thì gửi báo cáo bù.

## 3. Pi thật
Raspberry Pi 4 (hostname `ngocson`, cắm LAN) chạy agent với mã `pi-demo-01`, gắn với **Đền Ngọc Sơn**.
- Cài: chép thư mục `pi-agent` lên Pi rồi `sudo ./install.sh`; cấu hình ở `/etc/linh-dia-viet/agent.env`
  (token thiết bị: `grep DEMO_DEVICE_TOKEN ~/KinhDich/linh-dia-viet/.env` trên VPS). Chi tiết: `pi-agent/README.md`.
- Âm thanh ra jack 3.5mm: `LD_AUDIO_DEVICE=alsa/plughw:CARD=Headphones,DEV=0`.
- Chưa có camera nên tạm đặt `LD_CAMERA=simulate` (ảnh giả). Có webcam USB thì đổi thành `LD_CAMERA=fswebcam`.
- Xem log: `journalctl -u linh-dia-viet-agent -f`. Thử loa: `sudo -u linhdia /opt/linh-dia-viet-agent/venv/bin/python -m ld_agent --env /etc/linh-dia-viet/agent.env --test-speaker`.

## 4. Quản trị
Đăng nhập **tuandv@gmail.com**, vào **Quản lý**:
- **Thiết bị:** pi-demo-01 hiện Online khi Pi đang chạy. Có các nút Phát âm thử, Chụp thử, Dừng ngay. Thêm Pi thật bằng **Thêm thiết bị**.
- **Lịch lễ & đơn hàng:** bấm số đơn để xem log từng bước của thiết bị, và **Gửi lại job** khi cần.
- **Kiểm duyệt ghi âm:** đang tắt (bản ghi được duyệt tự động). Bật bằng `AUTO_APPROVE_RECORDINGS=false` trong `.env`.
- **Mẫu sớ:** sửa bài sớ mẫu, chung cho mọi đền hoặc riêng từng đền.
- **KHÓA KHẨN CẤP:** dừng phát trên mọi thiết bị và chặn mọi lệnh mới.

Kiosk và quản lý đền đăng nhập thì thấy **Lịch lễ** của Đền Ngọc Sơn (không có thông tin cá nhân của khách).
Kiosk có nút "Mâm lễ đã bày"; quản lý đền được từ chối đơn và sửa mẫu sớ riêng của đền.
