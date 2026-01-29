/**
 * Playwright configuration for Sage Agent UI tests
 * Supports running tests individually via grep patterns or projects
 */
const path = require('path');
// Load .env from ui-tests directory, fallback to parent directory
require('dotenv').config({ path: path.resolve(__dirname, '.env') });
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });

const baseConfig = require('@jupyterlab/galata/lib/playwright-config');

module.exports = {
  ...baseConfig,

  // Retry failed tests once
  retries: 1,

  // Test timeout (individual tests can override)
  timeout: 60000,

  // Global setup/teardown
  globalSetup: undefined,
  globalTeardown: undefined,

  // Test file patterns
  testDir: './tests',
  testMatch: '**/*.spec.ts',

  // Ignore patterns (add files here to exclude from tests)
  testIgnore: [],

  use: {
    ...baseConfig.use,
    headless: true,
    viewport: { width: 1920, height: 1080 },

    // Short action timeout - fail fast if elements not found (5 seconds)
    actionTimeout: 5000,

    // Capture screenshots on failure
    screenshot: 'only-on-failure',

    // Capture trace on first retry
    trace: 'on-first-retry',

    // Video recording
    video: 'on-first-retry'
  },

  // Video settings
  video: {
    size: { width: 1920, height: 1080 }
  },

  // Output directories
  outputDir: './test-results',

  // Reporters
  reporter: [
    ['html', { outputFolder: './playwright-report', open: 'never' }],
    ['json', { outputFile: './test-results/results.json' }],
    ['list']
  ],

  // Projects for different test categories
  // Run specific project with: npx playwright test --project=extension
  projects: [
    {
      name: 'extension',
      testMatch: '**/extension.spec.ts',
      use: {
        // Extension tests are quick, no special config needed
      }
    },
    {
      name: 'llm-states',
      testMatch: '**/llm-states.spec.ts',
      use: {
        // LLM state tests need more time
      }
    },
    {
      name: 'diff-interactions',
      testMatch: '**/diff-interactions.spec.ts',
      use: {
        // Diff tests need video for debugging
        video: 'on'
      }
    },
    {
      name: 'long-running',
      testMatch: '**/long-running.spec.ts',
      timeout: 600000,
      use: {
        // Long running tests always need video
        video: 'on'
      }
    },
    {
      name: 'llm-prompter',
      testMatch: '**/llm-prompter.spec.ts',
      timeout: 600000,
      use: {
        // Minimal overhead - no video/screenshots
        video: 'off',
        screenshot: 'off'
      }
    },
    {
      name: 'all',
      testMatch: '**/*.spec.ts'
    }
  ],

  // Web server configuration
  webServer: {
    command: 'jlpm start',
    url: 'http://localhost:8888/lab',
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI
  },

  // Expect configuration
  expect: {
    // Increase timeout for slow CI environments
    timeout: 10000
  }
};
