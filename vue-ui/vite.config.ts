import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    proxy: {
      '/download': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
    },
  },
})
