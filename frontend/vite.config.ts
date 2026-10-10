import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { loadEnv } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ command, mode }) => {
  if (command === 'build') {
    const value = loadEnv(mode, '.', 'VITE_').VITE_API_BASE_URL?.trim()
    let url: URL
    try {
      url = new URL(value || '')
    } catch {
      throw new Error('Set VITE_API_BASE_URL to the backend HTTP(S) origin before building.')
    }
    if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password ||
        url.search || url.hash || url.pathname !== '/') {
      throw new Error('VITE_API_BASE_URL must be an HTTP(S) origin without credentials, paths, query or fragment.')
    }
  }
  return {
    plugins: [react(), tailwindcss()],
    build: {
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('vite/preload-helper')) return 'preload'
            const modulePath = id.replace(/\\/g, '/')
            if (/\/node_modules\/(react|react-dom|scheduler)\//.test(modulePath)) return 'react'
            if (/\/node_modules\/(three|@react-three\/(fiber|drei))\//.test(modulePath)) return 'three'
          },
        },
      },
    },
  }
})


