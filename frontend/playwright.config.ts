import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './tests', outputDir: `./test-artifacts/run-${Date.now()}`, timeout: 90000, expect: { timeout: 25000 }, fullyParallel: false, workers: 1,
  reporter: [['list'], ['json', { outputFile: '../reports/gasification_reference_browser_tests.json' }]],
  use: { baseURL: 'http://127.0.0.1:28173', viewport: { width: 1536, height: 1100 }, trace: 'retain-on-failure', screenshot: 'only-on-failure', launchOptions: { channel: 'chrome', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] } },
  webServer: [
    { command: 'python -m uvicorn backend.main:app --host 127.0.0.1 --port 28100', cwd: '..', env: { WASTEWISE_CORS_ORIGINS: 'http://127.0.0.1:28173' }, url: 'http://127.0.0.1:28100/api/health', reuseExistingServer: false, timeout: 90000 },
    { command: 'npm.cmd run test:serve', env: { VITE_API_BASE_URL: 'http://127.0.0.1:28100' }, url: 'http://127.0.0.1:28173', reuseExistingServer: false, timeout: 180000 },
  ],
})
