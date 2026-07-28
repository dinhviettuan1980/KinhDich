import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/kinhdich/',
  plugins: [react()],
  server: {
    port: 3003,
    proxy: {
      // FE chạy local, gọi backend đã deploy (prod). Đổi về 'http://localhost:8001'
      // nếu chạy backend ngay trên máy.
      // LƯU Ý: domain đúng của kinhdichapi là kinhdichapi.tuandv.id.vn (port 8033) —
      // KHÔNG phải api.tuandv.id.vn (domain đó thực ra trỏ sang xsmbapi trên VPS).
      // Path đổi từ /kinhdich sang /api/kinhdich để không đụng route SPA khi lên
      // production (xem .claude/plans/virtual-sparking-beaver.md) — rewrite lại
      // đúng prefix /kinhdich mà backend đang expect.
      '/api/kinhdich': {
        target: 'https://kinhdichapi.tuandv.id.vn',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/kinhdich/, '/kinhdich'),
      },
    },
  },
})
