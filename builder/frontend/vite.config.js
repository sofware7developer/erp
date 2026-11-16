import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * پیکربندی Vite برای رابط کاربری سازنده ERP
 *
 * در حالت توسعه، مسیر /api به بک‌اند FastAPI پروکسی می‌شود تا نیاز به CORS
 * نباشد. در حالت تولید، خود FastAPI پوشه dist را سرو می‌کند (یک پورت).
 */
export default defineConfig(({ isSsrBuild }) => ({
  plugins: [react()],
  base: '/',
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: false,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    chunkSizeWarningLimit: 1400,
    rollupOptions: {
      output: {
        // در بیلد SSR (آزمون دود) وابستگی‌ها external هستند و manualChunks
        // باعث خطای رول‌آپ می‌شود؛ فقط برای بیلد مرورگر اعمال می‌شود.
        manualChunks: isSsrBuild
          ? undefined
          : {
              react: ['react', 'react-dom', 'react-router-dom'],
            },
      },
    },
  },
}))
