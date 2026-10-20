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

## 3. Pi giả trên máy tính (phát thật ra loa)
```bash
cd KinhDich/linh-dia-viet/pi-agent
cp .env.mac.example .env.mac      # điền LD_DEVICE_TOKEN (grep DEMO_DEVICE_TOKEN ~/KinhDich/linh-dia-viet/.env trên VPS)
./run-mac.sh start                # nhận lệnh thật, PHÁT RA LOA bằng ffplay, ảnh mâm lễ là ảnh giả
./run-mac.sh log                  # xem log;  ./run-mac.sh stop  để tắt
```
Máy tính này đóng vai `pi-demo-01` (Đền Ngọc Sơn). Đừng chạy cùng lúc với Pi thật dùng cùng mã thiết bị.

### Cách khác: Pi giả lập hoàn toàn (không phát loa)
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
