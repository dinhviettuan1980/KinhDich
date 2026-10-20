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
1. Đăng nhập bằng **khachthu**, rồi vào **Đền chùa → Đền Ngọc Sơn**. (Hiện chỉ Ngọc Sơn có thiết bị; hai đền còn lại chưa đặt được.)
2. Ở gói lễ muốn đặt, bấm **Chọn gói này và đặt lễ →**. Form mở ra với đền và gói đã chọn sẵn.
3. Điền họ tên, năm sinh, địa chỉ, nguyện vọng, và giờ khấn (sau thời điểm hiện tại ít nhất 2 phút).
   Khối **📜 Tờ sớ** tự soạn lại theo các thông tin này.
4. Ở mục **Cách khấn**, chọn **Tôi tự ghi âm giọng đọc**. Bấm **● Bắt đầu ghi**, đọc tờ sớ, rồi bấm **■ Dừng**.
   Nghe lại, rồi bấm **Dùng bản ghi này**: file được tải lên máy chủ và chuyển thành MP3 chuẩn hoá.
   (Hoặc chọn **Hệ thống soạn sớ…** rồi bấm **▶ Nghe thử giọng đọc**.)
5. **Xem lại đơn → Xác nhận và thanh toán → Thanh toán thành công** (thanh toán giả lập).
6. Trang đơn tự cập nhật trạng thái: Đã xếp lịch → Thiết bị đã nhận lệnh → Đang phát → Đã phát xong → Ảnh mâm lễ → Hoàn tất.

## 2. Pi nhận lệnh và phát (hoạt động thế nào)
- Pi luôn giữ kết nối MQTT tới `tuandv.id.vn:8883` (TLS) và nghe kênh riêng `ld/<mã thiết bị>/cmd`.
- **Trước giờ khấn 10 phút** (hoặc ngay lập tức nếu đặt sát giờ hơn), server gửi lệnh `play` vào kênh. Lệnh gồm
  link tải MP3 (có chữ ký, hạn 1 giờ), mã sha256, giờ phát và âm lượng.
- Pi tải MP3 về ngay, kiểm tra sha256 rồi báo "đã tải". Nó chụp ảnh "trước", **đúng giờ thì phát ra loa**,
  chụp ảnh lúc bắt đầu, và chụp ảnh "sau" 30 giây sau khi phát xong. Ảnh được gửi về server.
- Mất mạng sau khi đã tải xong thì Pi vẫn phát đúng giờ, có mạng lại thì gửi báo cáo bù.

## 3. Nếu chưa có Pi thật: chạy Pi giả lập trên máy tính
Máy cần Python 3.11+. Lấy token thiết bị demo trên VPS: `grep DEMO_DEVICE_TOKEN ~/KinhDich/linh-dia-viet/.env`.
```bash
cd KinhDich/linh-dia-viet/pi-agent && pip install -r requirements.txt
LD_SERVER_URL=https://tuandv.id.vn/le-chua LD_DEVICE_ID=pi-demo-01 LD_DEVICE_TOKEN=<token> \
LD_MQTT_HOST=tuandv.id.vn LD_MQTT_PORT=8883 LD_MQTT_TLS=true LD_DATA_DIR=/tmp/ld-pi \
python -m ld_agent --simulate --env /dev/null
```
Bỏ `--simulate` thì máy tính **phát thật ra loa** (cần `mpv` hoặc `ffplay`; đặt thêm `LD_PLAYER=ffplay LD_CAMERA=none`).
Giờ cấm phát mặc định là 22:00–05:00. Muốn thử trong khung giờ đó thì đặt `LD_QUIET_START=00:00 LD_QUIET_END=00:00`.

## 4. Quản trị
Đăng nhập **tuandv@gmail.com**, vào **Quản lý**:
- **Thiết bị:** pi-demo-01 hiện Online khi Pi đang chạy. Có các nút Phát âm thử, Chụp thử, Dừng ngay. Thêm Pi thật bằng **Thêm thiết bị**.
- **Lịch lễ & đơn hàng:** bấm số đơn để xem log từng bước của thiết bị, và **Gửi lại job** khi cần.
- **Kiểm duyệt ghi âm:** đang tắt (bản ghi được duyệt tự động). Bật bằng `AUTO_APPROVE_RECORDINGS=false` trong `.env`.
- **Mẫu sớ:** sửa bài sớ mẫu, chung cho mọi đền hoặc riêng từng đền.
- **KHÓA KHẨN CẤP:** dừng phát trên mọi thiết bị và chặn mọi lệnh mới.

Kiosk và quản lý đền đăng nhập thì thấy **Lịch lễ** của Đền Ngọc Sơn (không có thông tin cá nhân của khách).
Kiosk có nút "Mâm lễ đã bày"; quản lý đền được từ chối đơn và sửa mẫu sớ riêng của đền.
