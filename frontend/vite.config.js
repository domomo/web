import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath } from 'node:url';

const projectRoot = fileURLToPath(new URL('../', import.meta.url));

export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/static/' : '/',
  envDir: projectRoot,
  plugins: [vue()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  build: {
    outDir: '../app/static',
    emptyOutDir: true,
  },
}));
