import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath } from 'node:url';

const projectRoot = fileURLToPath(new URL('../', import.meta.url));

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, projectRoot, '');

  return {
    base: command === 'build' ? '/static/' : '/',
    envDir: projectRoot,
    define: {
      'globalThis.__API_BASE_URL__': JSON.stringify(env.VITE_API_BASE_URL || 'https://api.aiready.p-e.kr'),
    },
    plugins: [vue()],
    server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
    build: {
      outDir: '../app/static',
      emptyOutDir: true,
    },
  };
});
