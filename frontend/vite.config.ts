import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://`${import.meta.env.VITE_API_URL}`', changeOrigin: true },
      '/ws': { target: 'ws://`${import.meta.env.VITE_API_URL}`', ws: true },
    },
  },
})
