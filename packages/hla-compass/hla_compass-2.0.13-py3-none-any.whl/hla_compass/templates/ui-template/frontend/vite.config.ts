import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import cssInjectedByJsPlugin from 'vite-plugin-css-injected-by-js';

const isStandalone = process.env.STANDALONE === '1';

export default defineConfig({
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  plugins: [react(), cssInjectedByJsPlugin()],
  build: {
    outDir: 'dist',
    emptyOutDir: false,
    sourcemap: isStandalone,
    lib: {
      entry: isStandalone ? 'standalone-entry.tsx' : 'index.tsx',
      name: 'ModuleUI',
      formats: ['umd'],
      fileName: () => isStandalone ? 'bundle.standalone.js' : 'bundle.js',
    },
    rollupOptions: {
      external: isStandalone ? [] : ['react', 'react-dom', 'antd'],
      output: {
        globals: isStandalone ? {} : {
          react: 'React',
          'react-dom': 'ReactDOM',
          antd: 'antd',
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: { '/api': 'http://localhost:8080' },
  },
});
