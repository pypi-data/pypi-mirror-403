/**
 * Screenshot capture utilities
 */
import { Page, TestInfo } from '@playwright/test';
import CONFIG from '../config';

/**
 * Capture a screenshot with organized naming and optional test attachment
 */
export async function captureScreenshot(
  page: Page,
  category: string,
  action: string,
  state: string,
  testName?: string,
  testInfo?: TestInfo
): Promise<string> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `${category}_${action}_${state}_${timestamp}.png`;

  // Create test-specific directory if testName is provided
  let screenshotPath: string;
  if (testName) {
    const sanitizedTestName = testName.toLowerCase().replace(/[^a-z0-9]/g, '_');
    screenshotPath = `${CONFIG.SCREENSHOT_DIR}/${sanitizedTestName}/${filename}`;
  } else {
    screenshotPath = `${CONFIG.SCREENSHOT_DIR}/${filename}`;
  }

  // Playwright will automatically create directories as needed
  await page.screenshot({
    path: screenshotPath,
    fullPage: true
  });

  // Attach to test report if testInfo provided
  if (testInfo) {
    await testInfo.attach(filename, {
      path: screenshotPath,
      contentType: 'image/png'
    });
  }

  return screenshotPath;
}

/**
 * Capture a screenshot of a specific element
 */
export async function captureElementScreenshot(
  page: Page,
  selector: string,
  name: string,
  testInfo?: TestInfo
): Promise<string | null> {
  const element = page.locator(selector);
  const count = await element.count();

  if (count === 0) {
    console.warn(`captureElementScreenshot: Element ${selector} not found`);
    return null;
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `element_${name}_${timestamp}.png`;
  const screenshotPath = `${CONFIG.SCREENSHOT_DIR}/${filename}`;

  await element.screenshot({
    path: screenshotPath
  });

  if (testInfo) {
    await testInfo.attach(filename, {
      path: screenshotPath,
      contentType: 'image/png'
    });
  }

  return screenshotPath;
}
