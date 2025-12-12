import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Determine which app to build/serve based on environment
const APP_MODE = process.env.APP_MODE || 'admin' // 'admin' or 'student'

const appConfig = {
  admin: {
    root: resolve(__dirname, 'admin/src'),
    outDir: resolve(__dirname, 'admin/dist'),
    alias: resolve(__dirname, 'admin/src'),
    inputs: {
      main: resolve(__dirname, 'admin/src/index.html'),
      login: resolve(__dirname, 'admin/src/login.html')
    }
  },
  student: {
    root: resolve(__dirname, 'student/src'),
    outDir: resolve(__dirname, 'student/dist'),
    alias: resolve(__dirname, 'student/src'),
    inputs: {
      main: resolve(__dirname, 'student/src/index.html'),
      login: resolve(__dirname, 'student/src/login.html')
    }
  }
}

const config = appConfig[APP_MODE]

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": config.alias,
    },
  },
  root: config.root,
  build: {
    outDir: config.outDir,
    emptyOutDir: true,
    rollupOptions: {
      input: config.inputs
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
