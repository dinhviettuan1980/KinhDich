import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3003,
    proxy: {
      // FE chạy local, gọi backend đã deploy (prod). Đổi về 'http://localhost:8001'
      // nếu chạy backend ngay trên máy.
      '/kinhdich': { target: 'https://api.tuandv.id.vn', changeOrigin: true },
    },
  },
})
