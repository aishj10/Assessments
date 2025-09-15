import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => {
          const newPath = path.replace(/^\/api/, '');
          // Add trailing slash for leads endpoint to avoid 307 redirects
          if (newPath === '/leads') {
            return '/leads/';
          }
          return newPath;
        }
      }
    }
  }
})
