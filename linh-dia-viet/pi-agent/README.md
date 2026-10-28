# Agent Raspberry Pi – Linh Địa Việt

Agent nhận lệnh từ server qua MQTT, tải trước bài khấn, phát đúng giờ qua loa và chụp ảnh mâm lễ gửi về.

Các luật cứng nằm trên thiết bị, server không ghi đè được:
- trần âm lượng `LD_VOLUME_MAX`;
- giờ cấm phát `LD_QUIET_START`–`LD_QUIET_END` (mặc định 22:00–05:00);
- chống phát trùng: mỗi `job_id` phát nhiều nhất một lần.

Agent có hàng đợi SQLite cục bộ (`/var/lib/linh-dia-viet/agent.db`). Khi mất mạng, bài đã tải sẵn vẫn được phát đúng giờ. Có mạng lại thì agent gửi bù ACK và ảnh.

## Phần cứng đã nhắm tới

| Thành phần | Gợi ý |
|---|---|
| Máy | Raspberry Pi 4/5 (2 GB RAM trở lên) hoặc Pi 3B+ |
| Thẻ nhớ | microSD 16 GB+ loại tốt (A1/A2) |
| Loa | loa có ampli cắm jack 3.5 mm, hoặc loa/USB sound card |
| Camera | Camera Module 3 (CSI) hoặc webcam USB (UVC) |
| Mạng | Wi-Fi, hoặc USB 4G dongle (chế độ HiLink/ethernet) |
| Nguồn | adapter chính hãng; nên có UPS mini nếu điện chập chờn |

## 1. Cài Raspberry Pi OS Lite

1. Tải **Raspberry Pi Imager** và chọn *Raspberry Pi OS Lite (64-bit)*, bản Bookworm.
2. Bấm ⚙️ (Edit settings) trước khi ghi thẻ:
   - hostname: ví dụ `pi-ngoc-son-01`;
   - bật SSH, tạo user/mật khẩu (hoặc dùng SSH key);
   - **Wi-Fi**: SSID, mật khẩu, quốc gia `VN`;
   - múi giờ `Asia/Ho_Chi_Minh`.
3. Ghi thẻ, cắm vào Pi, cấp nguồn, rồi đăng nhập: `ssh <user>@pi-ngoc-son-01.local`.
4. Cập nhật hệ thống: `sudo apt update && sudo apt full-upgrade -y && sudo reboot`.

Để đổi Wi-Fi sau này: `sudo nmtui` (chọn *Activate a connection*).
Nếu dùng 4G USB, cắm dongle rồi kiểm tra `ip a` thấy `usb0`/`eth1`/`wwan0` là được. Agent tự báo `net: "4g"`.

## 2. Đồng hồ (NTP)

Agent phát theo giờ UTC trong lệnh (`play_at`), nên đồng hồ phải đúng:

```bash
timedatectl            # "System clock synchronized: yes"
sudo timedatectl set-ntp true
```

Pi không có pin RTC, nên sau khi mất điện phải đợi có mạng thì đồng hồ mới đúng lại. `install.sh` cho dịch vụ chạy sau `time-sync.target`.

## 3. Chọn thiết bị âm thanh và thử loa

```bash
aplay -l                         # liệt kê card: vd "card 0: Headphones", "card 1: Device [USB Audio]"
speaker-test -t sine -f 660 -l 1 -D plughw:0,0
alsamixer                        # F6 chọn card, kéo âm lượng tổng (Master/PCM) ~80–90%
```

Ghi cấu hình vào `/etc/linh-dia-viet/agent.env`:
- dùng mpv: `LD_PLAYER=mpv` và `LD_AUDIO_DEVICE=alsa/plughw:CARD=Headphones,DEV=0` (xem `mpv --audio-device=help`);
- dùng aplay: `LD_PLAYER=aplay` và `LD_AUDIO_DEVICE=plughw:1,0`. Âm lượng lúc này chỉnh bằng `alsamixer`, vì aplay không có tham số âm lượng.

### Card âm thanh USB (Pi Zero không có jack 3.5 mm)

Cắm card vào hub USB, nối dây AUX 3.5 mm từ lỗ tai nghe của card sang ngõ AUDIO INPUT của loa, rồi:

```bash
aplay -l                                            # vd "card 1: Device [USB Audio Device]" → tên card là Device
sudo sed -i 's|^LD_AUDIO_DEVICE=.*|LD_AUDIO_DEVICE=alsa/plughw:CARD=Device,DEV=0|' /etc/linh-dia-viet/agent.env
sudo rm -f /etc/linh-dia-viet/bt-speaker            # nếu trước đó dùng loa Bluetooth
amixer -c Device scontrols && amixer -c Device sset Speaker 90%   # tên điều khiển tuỳ card (Speaker/PCM/Headphone)
sudo systemctl restart linh-dia-viet-agent
```

Card âm thanh USB cũng có lỗ micro. Agent bỏ qua card đang dùng để phát loa và lấy micro của webcam để thu tiếng video.

### Loa Bluetooth

Bật loa ở chế độ ghép đôi (đèn nháy nhanh), đặt gần Pi, rồi:

```bash
cd pi-agent/bluetooth
sudo ./bt-pair.sh                          # quét, liệt kê thiết bị có tên (vd "联想thinkplus-K30")
sudo ./bt-pair.sh D7:DD:FE:25:50:FB 100    # ghép + kết nối, âm lượng loa 100%, chuyển agent sang loa này
```

Script đặt `LD_AUDIO_DEVICE=alsa/bluealsa:DEV=<địa chỉ>,PROFILE=a2dp` và ghi địa chỉ vào `/etc/linh-dia-viet/bt-speaker`. Timer `ld-bt-reconnect` kiểm tra mỗi 30 giây và tự kết nối lại khi loa tắt/bật hoặc Pi khởi động lại.

Âm lượng có 2 tầng. Tầng 1 là âm lượng bluealsa của loa: `sudo -u linhdia amixer -D bluealsa sset '<tên> A2DP' 80%`. Tầng 2 là âm lượng của từng lễ, do server gửi xuống và bị chặn trần bởi `LD_VOLUME_MAX`.

Quay lại cổng 3.5 mm: sửa `LD_AUDIO_DEVICE` trong `agent.env` rồi xoá `/etc/linh-dia-viet/bt-speaker`.

## 4. Thử camera

```bash
# Camera CSI (Bookworm)
rpicam-still -n -t 1500 -o /tmp/test.jpg
# Webcam USB
v4l2-ctl --list-devices          # (sudo apt install v4l-utils)
fswebcam -d /dev/video0 -r 1280x960 --no-banner /tmp/test.jpg
```

Đặt `LD_CAMERA=rpicam` (hoặc `picamera2`) cho camera CSI, `LD_CAMERA=fswebcam` (hoặc `ffmpeg`) cho webcam USB, `none` nếu không có camera.
Nên gắn camera cố định, hướng thẳng vào mâm lễ và đủ sáng.

## 5. Lấy token thiết bị

Trên server, vào **Quản lý → Thiết bị → Thêm thiết bị** (hoặc `docker compose exec api python -m app.cli add-device pi-ngoc-son-01 "Đền Ngọc Sơn"`).
Chép hai dòng `LD_DEVICE_ID` và `LD_DEVICE_TOKEN` (token chỉ hiện một lần), rồi gắn thiết bị vào đền ở trang **Đền, chùa**.

## 6. Cài dịch vụ

```bash
# Chép thư mục pi-agent lên Pi (từ máy có repo):
scp -r pi-agent <user>@pi-ngoc-son-01.local:~/
ssh <user>@pi-ngoc-son-01.local
cd ~/pi-agent && sudo ./install.sh
sudo nano /etc/linh-dia-viet/agent.env      # điền LD_SERVER_URL, LD_DEVICE_ID, LD_DEVICE_TOKEN, LD_MQTT_HOST...
sudo systemctl restart linh-dia-viet-agent
journalctl -u linh-dia-viet-agent -f        # xem log
```

Kiểm tra phần cứng bằng chính cấu hình của dịch vụ:

```bash
cd /opt/linh-dia-viet-agent
sudo -u linhdia venv/bin/python -m ld_agent --env /etc/linh-dia-viet/agent.env --test-speaker
sudo -u linhdia venv/bin/python -m ld_agent --env /etc/linh-dia-viet/agent.env --test-camera /tmp/t.jpg
sudo -u linhdia venv/bin/python -m ld_agent --env /etc/linh-dia-viet/agent.env --test-video /tmp/t.mp4  # 10s hình + tiếng
```

### Video tại đền (hình mâm lễ + tiếng thu thật)

Agent quay video trong lúc loa đọc sớ và quay thêm 3 giây sau khi đọc xong. Hình là mâm lễ, tiếng thu từ micro của webcam USB nên nghe được tiếng khấn vang tại đền cùng tiếng xung quanh. Khách xem video này ở mục **Lịch sử lễ**; video thay cho clip ghép từ ảnh.

- Cần `LD_CAMERA=fswebcam` hoặc `LD_CAMERA=ffmpeg`. Ảnh "lúc khấn" (dùng để nhận diện mâm lễ) được lấy từ một khung hình của video, vì webcam đang bận quay.
- Micro được tự chọn: card USB đầu tiên có thiết bị thu (`LD_AUDIO_IN=auto`). Muốn chỉ định thì xem `arecord -l` rồi đặt `LD_AUDIO_IN=plughw:CARD=<tên>,DEV=0`.
- Mặc định quay 1280x720, 10 hình/giây, tối đa 600 kbps và 5 phút (`LD_VIDEO_SIZE`, `LD_VIDEO_FPS`, `LD_RECORD_MAX_SECONDS`). Server nhận tối đa 24 MB.
- `LD_CAMERA=simulate`: video giả gồm ảnh mâm giả và bài khấn, có lọc tiếng cho giống tiếng thu qua micro.
- Tắt quay video: `LD_RECORD=false`.

Sau khoảng một phút, trang **Thiết bị** sẽ hiện "Online". Bấm **Phát âm thử** hoặc **Chụp thử** để kiểm tra từ xa.

Dịch vụ tự khởi động cùng máy và tự chạy lại sau 5 giây nếu bị lỗi (`Restart=always`).

## 7. Kiểm tra cuối: đơn thật hẹn sau 2 phút

1. Đặt một đơn ở đền đã gắn thiết bị, hẹn giờ sau 2–3 phút (`MIN_LEAD_SECONDS=120`), rồi thanh toán giả lập.
2. Server gửi lệnh ngay, vì giờ hẹn nằm trong 10 phút tới. Trong log Pi sẽ thấy `Nhận lệnh play`, rồi tải bài khấn, chụp ảnh "before".
3. Đúng giờ hẹn, loa phát bài khấn. Trang đơn chuyển sang "Đang phát bài khấn", rồi "Đã phát xong".
4. Khoảng 30 giây sau, ảnh "after" được gửi về và đơn chuyển sang **Hoàn tất**, có ảnh mâm lễ.

## Chạy giả lập (không cần Pi)

```bash
cd pi-agent
pip install -r requirements.txt
LD_SERVER_URL=http://localhost:8000/le-chua LD_DEVICE_ID=pi-demo-01 LD_DEVICE_TOKEN=<token> \
  python -m ld_agent --simulate --env /dev/null
```

Chế độ `--simulate` chỉ in log thay vì phát loa ("phát" trong `LD_SIMULATE_PLAY_SECONDS` giây) và tạo ảnh JPEG giả.

## Xử lý sự cố

| Hiện tượng | Kiểm tra |
|---|---|
| Trang admin báo Offline | `journalctl -u linh-dia-viet-agent`, sai token/MQTT host/cổng TLS, `ping` server |
| Báo lỗi "giờ cấm phát" | Giờ hẹn rơi vào `LD_QUIET_START`–`LD_QUIET_END` |
| Không có tiếng | `aplay -l`, `alsamixer`, sai `LD_AUDIO_DEVICE`, loa chưa bật nguồn |
| Lỗi "sai sha256" / không tải được | Mạng chập chờn (agent tự thử lại), hoặc link quá 1 giờ: bấm "gửi lại job" trên trang admin |
| Phát lệch giờ | `timedatectl` chưa đồng bộ NTP |
| Không có ảnh | `--test-camera`, quyền nhóm `video`, cáp camera CSI |
