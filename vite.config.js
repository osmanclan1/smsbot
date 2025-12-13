import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';
import { existsSync, readdirSync } from 'fs';

// Determine project root - Vercel uses process.cwd(), local uses different paths
const getProjectRoot = () => {
  const cwd = process.cwd();
  
  // List of possible root directories to check
  const possibleRoots = [
    cwd, // Vercel uses this as working directory
    resolve(cwd), // Absolute path of cwd
  ];
  
  // Debug: log what we're checking
  console.log('Looking for admin/src/index.html...');
  console.log('Current working directory:', cwd);
  
  for (const root of possibleRoots) {
    const testPath = resolve(root, 'admin/src/index.html');
    console.log(`Checking: ${testPath}`);
    if (existsSync(testPath)) {
      console.log(`✅ Found project root: ${root}`);
      return root;
    }
  }
  
  // If not found, show debug info
  console.error('❌ Could not find admin/src/index.html');
  console.error('Current directory contents:', readdirSync(cwd).join(', '));
  if (existsSync(resolve(cwd, 'admin'))) {
    console.error('admin/ exists, contents:', readdirSync(resolve(cwd, 'admin')).join(', '));
  }
  if (existsSync(resolve(cwd, 'admin/src'))) {
    console.error('admin/src/ exists, contents:', readdirSync(resolve(cwd, 'admin/src')).join(', '));
  }
  
  throw new Error(`Cannot find admin/src/index.html in ${cwd}. Files available: ${readdirSync(cwd).join(', ')}`);
};

const projectRoot = getProjectRoot();

// Determine which app to build/serve based on environment
const APP_MODE = process.env.APP_MODE || 'admin';

const appConfig = {
  admin: {
    root: resolve(projectRoot, 'admin/src'),
    outDir: resolve(projectRoot, 'admin/dist'),
    alias: resolve(projectRoot, 'admin/src'),
    inputs: {
      main: resolve(projectRoot, 'admin/src/index.html'),
      login: resolve(projectRoot, 'admin/src/login.html')
    }
  },
  student: {
    root: resolve(projectRoot, 'student/src'),
    outDir: resolve(projectRoot, 'student/dist'),
    alias: resolve(projectRoot, 'student/src'),
    inputs: {
      main: resolve(projectRoot, 'student/src/index.html'),
      login: resolve(projectRoot, 'student/src/login.html')
    }
  }
};

const config = appConfig[APP_MODE];

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
  preview: {
    port: 3000,
    open: true
  },
  publicDir: false
});
