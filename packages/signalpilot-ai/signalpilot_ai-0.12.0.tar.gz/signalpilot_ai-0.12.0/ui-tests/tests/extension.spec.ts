/**
 * Basic extension loading tests
 * Tests that the Sage Agent extension loads correctly
 * These tests do NOT require JWT token - they only verify UI presence
 */
import { test, expect } from '@jupyterlab/galata';
import { Selectors } from './page-objects/selectors';

// Don't auto-navigate - we handle it ourselves
test.use({ autoGoto: false });

test.describe('Extension Loading', () => {
  test('should load the extension', async ({ page, baseURL }) => {
    await page.goto(`${baseURL}`);
    await page.waitForSelector(Selectors.jupyterlab.mainDockPanel, {
      timeout: 30000
    });

    // Verify that JupyterLab main panel is present
    const mainPanel = page.locator(Selectors.jupyterlab.mainDockPanel);
    await expect(mainPanel).toBeVisible();
  });

  test('should have sage AI window with chat input', async ({
    page,
    baseURL
  }) => {
    await page.goto(`${baseURL}`);
    await page.waitForSelector(Selectors.jupyterlab.mainDockPanel, {
      timeout: 30000
    });

    // Wait for the sage AI chat container to be present
    await page.waitForSelector(Selectors.chat.container, { timeout: 15000 });

    // Wait for the chat input to be visible (indicates full render)
    await page.waitForSelector(Selectors.chat.input, {
      timeout: 15000,
      state: 'visible'
    });

    // Verify the sage AI chat container exists and is visible
    const chatContainer = page.locator(Selectors.chat.container);
    await expect(chatContainer).toBeVisible();

    // Check that the chat widget is present within the container
    const chatWidget = chatContainer.locator(Selectors.chat.widget);
    await expect(chatWidget).toBeVisible();

    // Verify that the chat input element is present and visible
    const chatInput = chatWidget.locator(Selectors.chat.input);
    await expect(chatInput).toBeVisible({ timeout: 15000 });

    // Verify the chat input is interactive (has contentEditable attribute)
    await expect(chatInput).toHaveAttribute('contentEditable', 'true');

    // Check that the send button is present (wait with longer timeout)
    const sendButton = chatWidget.locator(Selectors.chat.sendButton);
    await expect(sendButton).toBeVisible({ timeout: 15000 });

    // Verify toolbar exists in the DOM (may not be visible if collapsed)
    const toolbar = chatWidget.locator(Selectors.chat.toolbar);
    await expect(toolbar).toBeAttached();
  });
});
