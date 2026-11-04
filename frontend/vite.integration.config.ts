import { defineConfig } from 'vitest/config'
import config from './vite.config.ts'
export default defineConfig({ ...config, test: { ...config.test, include: ['integration/**/*.test.tsx'] } })
