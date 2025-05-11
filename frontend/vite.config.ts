import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const port = Number(process.env.PORT) || 3000

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port,
    },
  }
})