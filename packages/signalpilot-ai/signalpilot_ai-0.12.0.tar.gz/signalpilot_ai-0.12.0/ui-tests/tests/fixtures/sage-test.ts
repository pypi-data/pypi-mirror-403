/**
 * Custom test fixtures for Sage Agent tests
 * Provides common setup/teardown for all tests
 */
import { test as base, expect } from '@jupyterlab/galata';
import { Page, TestInfo } from '@playwright/test';
import CONFIG from '../config';
import { Selectors, Timeouts } from '../page-objects/selectors';
import { APIConfigurator, NotebookManager, ChatInteractor } from '../helpers';

/**
 * Extended test type with Sage-specific fixtures
 */
export type SageTestFixtures = {
  /**
   * Page with JupyterLab loaded and extension ready
   */
  sageReady: Page;

  /**
   * Page with notebook created and chat ready
   */
  notebookWithChat: Page;
};

/**
 * Validate configuration before tests run
 */
function validateConfig(): void {
  if (CONFIG.SAGE_JWT_TOKEN === 'your-api-key-here' || !CONFIG.SAGE_JWT_TOKEN) {
    throw new Error(
      'API Key not configured! Please set SAGE_JWT_TOKEN in tests/config.ts before running tests.'
    );
  }
}

/**
 * Setup JupyterLab with extension loaded
 */
async function setupJupyterLab(
  page: Page,
  baseURL: string | undefined
): Promise<void> {
  // Setup welcome modal dismissal in parallel with navigation
  const closeWelcomeModal = async () => {
    try {
      await page.waitForSelector(Selectors.auth.welcomeDismissButton, {
        timeout: Timeouts.modal
      });
      await page.click(Selectors.auth.welcomeDismissButton);
      await page.waitForTimeout(Timeouts.short);
    } catch {
      // Modal may not appear - that's OK
    }
  };

  // Navigate to JupyterLab
  try {
    await Promise.all([closeWelcomeModal(), page.goto(`${baseURL}`)]);
  } catch (error) {
    // Ignore navigation errors if welcome modal handling throws
    console.log('Navigation completed with potential modal handling');
  }

  // Wait for JupyterLab to be ready
  await page.waitForSelector(Selectors.jupyterlab.mainDockPanel, {
    timeout: Timeouts.navigation
  });
}

/**
 * Extended test fixture for Sage Agent tests
 */
export const test = base.extend<SageTestFixtures>({
  // Disable auto-navigation - we handle it ourselves
  autoGoto: [false, { option: true }],

  /**
   * Fixture: Page with JupyterLab loaded
   */
  sageReady: async ({ page, baseURL }, use) => {
    validateConfig();
    await setupJupyterLab(page, baseURL);
    await use(page);
  },

  /**
   * Fixture: Page with notebook created and chat ready
   * This is the most commonly used fixture for tests
   */
  notebookWithChat: async ({ page, baseURL }, use) => {
    validateConfig();
    await setupJupyterLab(page, baseURL);

    // Create a new notebook
    await NotebookManager.createNewNotebook(page);

    // Setup API configuration
    await APIConfigurator.setupJWTToken(
      page,
      CONFIG.SAGE_JWT_TOKEN,
      CONFIG.CLAUDE_MODEL_URL,
      CONFIG.CLAUDE_MODEL_ID
    );

    // Cleanup any lingering modals
    await APIConfigurator.cleanupModals(page);

    // Wait for chat to be ready
    await ChatInteractor.waitForChatReady(page);

    await use(page);
  }
});

// Re-export expect for convenience
export { expect };

// Export helpers for use in tests
export { ResponseState, ChatInteractor } from '../helpers/chat-interactor';
export { NotebookManager } from '../helpers/notebook-manager';
export { APIConfigurator } from '../helpers/api-configurator';
export { captureScreenshot } from '../helpers/screenshot';
export { Selectors, Timeouts } from '../page-objects/selectors';
export { default as CONFIG } from '../config';

// Re-export types for convenience
export type { Page, TestInfo } from '@playwright/test';
