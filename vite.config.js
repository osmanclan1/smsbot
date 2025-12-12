import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "admin/src"),
    },
  },
  root: resolve(__dirname, 'admin/src'),
  build: {
    outDir: resolve(__dirname, 'admin/dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'admin/src/index.html'),
        login: resolve(__dirname, 'admin/src/login.html')
      }
    }
  },
  server: {
    port: 3000,
    strictPort: true,
    open: true,
    host: 'localhost',
    hmr: {
      protocol: 'ws',
      host: 'localhost',
      port: 3000,
      clientPort: 3000
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    },
    watch: {
      usePolling: false
    }
  },
  // Ensure login.html is accessible
  preview: {
    port: 3000,
    open: true
  },
  publicDir: false
});
