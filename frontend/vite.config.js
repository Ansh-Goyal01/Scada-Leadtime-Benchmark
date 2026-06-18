import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev server proxies /api to the Flask API (src/console_api.py on :8051),
// so the browser app and the data backend share an origin in development.
export default defineConfig({
  plugins: [react()],
  define: {
    // Build-time stamp for the footer (ISO date, computed at build, not runtime).
    __BUILD_DATE__: JSON.stringify(new Date().toISOString().slice(0, 10)),
    __APP_VERSION__: JSON.stringify('1.0'),
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8051',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
