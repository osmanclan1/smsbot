import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';
import { existsSync, readdirSync } from 'fs';

// Debug: Log what we can see
console.log('=== Vite Config Loading ===');
console.log('process.cwd():', process.cwd());
console.log('__dirname equivalent:', import.meta.url);

// Determine project root - Vercel uses process.cwd() as the working directory
const cwd = process.cwd();
console.log('Current working directory:', cwd);
console.log('Files in cwd:', readdirSync(cwd).join(', '));

// Check if apps/admin directory exists
if (existsSync(resolve(cwd, 'apps/admin'))) {
  console.log('apps/admin/ exists');
  console.log('Files in apps/admin/:', readdirSync(resolve(cwd, 'apps/admin')).join(', '));
  
  if (existsSync(resolve(cwd, 'apps/admin/src'))) {
    console.log('apps/admin/src/ exists');
    console.log('Files in apps/admin/src/:', readdirSync(resolve(cwd, 'apps/admin/src')).join(', '));
  }
}

// Try to find the project root
let projectRoot = cwd;
const testPath = resolve(cwd, 'apps/admin/src/index.html');

console.log('Looking for:', testPath);
console.log('Exists:', existsSync(testPath));

if (!existsSync(testPath)) {
  // Try one level up (in case Vercel is in a subdirectory)
  const parentPath = resolve(cwd, '..', 'apps/admin/src/index.html');
  console.log('Trying parent:', parentPath);
  console.log('Parent exists:', existsSync(parentPath));
  
  if (existsSync(parentPath)) {
    projectRoot = resolve(cwd, '..');
    console.log('Using parent as root:', projectRoot);
  } else {
    // Last resort: list everything
    console.error('❌ Cannot find apps/admin/src/index.html');
    console.error('Available files in root:', readdirSync(cwd));
    throw new Error(`Cannot find apps/admin/src/index.html. Current dir: ${cwd}, Files: ${readdirSync(cwd).join(', ')}`);
  }
} else {
  console.log('✅ Found project root:', projectRoot);
}

// Determine which app to build
const APP_MODE = process.env.APP_MODE || 'admin';

const adminConfig = {
  root: resolve(projectRoot, 'apps/admin/src'),
  outDir: resolve(projectRoot, 'apps/admin/dist'),
  alias: resolve(projectRoot, 'apps/admin/src'),
  inputs: {
    main: resolve(projectRoot, 'apps/admin/src/index.html'),
    login: resolve(projectRoot, 'apps/admin/src/login.html')
  }
};

const studentConfig = {
  root: resolve(projectRoot, 'apps/student/src'),
  outDir: resolve(projectRoot, 'apps/student/dist'),
  alias: resolve(projectRoot, 'apps/student/src'),
  inputs: {
    main: resolve(projectRoot, 'apps/student/src/index.html')
  }
};

// Verify inputs exist
const config = APP_MODE === 'student' ? studentConfig : adminConfig;
console.log(`${APP_MODE} config inputs:`);
Object.entries(config.inputs).forEach(([key, path]) => {
  console.log(`  ${key}: ${path} (exists: ${existsSync(path)})`);
});

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
