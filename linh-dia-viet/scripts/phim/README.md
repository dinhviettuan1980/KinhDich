# Phim hoạt hình demo cho nhà đầu tư

Dựng phim 4 vai (khách · thủ nhang · kiosk · quản trị) từ **app thật** chạy trên server giả lập cục bộ:
nhân vật hoạt hình nói lời thoại bên trái, màn hình app thật trong khung điện thoại bên phải; cảnh "cùng một giờ,
tại 3 nơi" là 3 ông thủ nhang hoạt hình đọc sớ cạnh mâm lễ, đồng hồ giờ thật.

Mô phỏng: 12 thiết bị tại đền (`devsim.py`, cùng giao thức HTTP với điện thoại thật), AI nhận diện mâm lễ
(`fake_space.py`: thấy đủ mọi món, trừ món thiết bị giả đánh dấu "chưa bày" — kiosk Đền Ngọc Sơn quên gà luộc).
Màn hình, xếp lịch, gửi lệnh, nhận ảnh, đối chiếu mâm lễ và cảnh báo là code thật của server.

Cần: `.venv` của repo, ffmpeg, Node + `scripts/playwright` đã `npm install`, mạng (Edge TTS, Google Maps),
file `than_thanh_viet_nam_200.xlsx`.

```bash
cd scripts/phim
export PYTHONUTF8=1 PY=../../.venv/Scripts/python      # Linux/macOS: ../../.venv/bin/python
# 1. CSDL giả lập mới + 200 thần thánh
rm -rf data dev-work && mkdir data
(cd ../../server && set -a && . ../scripts/phim/sim.env && set +a && $PY -m alembic upgrade head && $PY -m app.seed \
   && $PY -m app.cli import-deities /đường/dẫn/than_thanh_viet_nam_200.xlsx)
# 2. Ba tiến trình chạy nền (mỗi lệnh 1 cửa sổ):
$PY fake_space.py                                                         # AI giả :8199
(cd ../../server && set -a && . ../scripts/phim/sim.env && set +a \
   && export GOOGLE_MAPS_API_KEY=$(grep ^GOOGLE_MAPS_API_KEY= ../.env | cut -d= -f2-) \
   && $PY -m uvicorn app.main:app --host 127.0.0.1 --port 8100)          # server giả lập
$PY prep.py && $PY -u devsim.py                                           # dữ liệu mẫu + 12 thiết bị giả
# 3. Quay (~15 phút, chạy theo giờ thật tới lúc 3 đền khấn xong) và dựng
cd film && $PY voices.py && node record.js && $PY build.py                # → film/linh-dia-viet-phim-dau-tu.mp4
```

Sửa lời thoại: `film/lines.json` rồi chạy lại `voices.py -f`; chỉ đổi lời/nhân vật thì không cần quay lại,
chạy `build.py` là đủ (trừ khi độ dài câu thoại đổi nhiều — `record.js` chờ theo độ dài từng câu).

Tài khoản giả lập: khách `demo-an@example.com` / `demo-password`, thủ nhang `quanly@example.com`,
kiosk `kiosk@example.com` (mật khẩu `demo12345`), admin `admin@example.com` / `admin-demo-123`.
