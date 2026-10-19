Thư mục dùng chung giữa `api` và `mosquitto`. API ghi `devices.passwd` (dòng `device_id:<băm PBKDF2-SHA512>`)
khi admin thêm / cấp lại / thu hồi thiết bị; mosquitto tự nạp lại sau vài giây. Không commit file này.
