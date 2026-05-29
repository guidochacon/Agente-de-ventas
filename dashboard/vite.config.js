import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/',
  build: { outDir: 'dist' },
  server: {
    proxy: {
      '/api': process.env.VITE_API_URL || 'http://localhost:8000'
    }
  }
})
