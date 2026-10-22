import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'

// Slides import their numbers from '@deck', an absolute alias: a relative './data' import breaks when a browser
// tab left open from an earlier server asks for a slide module under a stale path.
export default defineConfig({
  resolve: {
    alias: {
      '@deck': fileURLToPath(new URL('./data.ts', import.meta.url)),
    },
  },
})
