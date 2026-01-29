/**
 * Wait helper utilities for better render synchronization
 */
import { Page, Locator } from '@playwright/test';
import { Timeouts } from '../page-objects/selectors';

/**
 * Wait for an element to be visible with retry logic
 */
export async function waitForElement(
  page: Page,
  selector: string,
  options: {
    timeout?: number;
    state?: 'visible' | 'attached' | 'hidden' | 'detached';
    retries?: number;
  } = {}
): Promise<boolean> {
  const {
    timeout = Timeouts.selector,
    state = 'visible',
    retries = 3
  } = options;

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      await page.waitForSelector(selector, { timeout, state });
      return true;
    } catch (error) {
      if (attempt === retries) {
        console.warn(
          `waitForElement: ${selector} not found after ${retries} attempts`
        );
        return false;
      }
      // Small delay before retry
      await page.waitForTimeout(200);
    }
  }
  return false;
}

/**
 * Wait for any of multiple elements to appear
 * Returns the index of the first element found, or -1 if none found
 */
export async function waitForAnyElement(
  page: Page,
  selectors: string[],
  timeout: number = Timeouts.response
): Promise<{ index: number; selector: string | null }> {
  try {
    const result = await Promise.race([
      ...selectors.map((selector, index) =>
        page
          .waitForSelector(selector, { timeout, state: 'visible' })
          .then(() => ({ index, selector }))
      ),
      new Promise<{ index: number; selector: null }>(resolve =>
        setTimeout(() => resolve({ index: -1, selector: null }), timeout)
      )
    ]);
    return result;
  } catch {
    return { index: -1, selector: null };
  }
}

/**
 * Wait for an element to be hidden or removed
 */
export async function waitForElementHidden(
  page: Page,
  selector: string,
  timeout: number = Timeouts.selector
): Promise<boolean> {
  try {
    await page.waitForSelector(selector, { timeout, state: 'hidden' });
    return true;
  } catch {
    return false;
  }
}

/**
 * Wait for page to be stable (no pending network requests, animations complete)
 */
export async function waitForStableState(
  page: Page,
  options: { networkIdle?: boolean; animationComplete?: boolean } = {}
): Promise<void> {
  const { networkIdle = true, animationComplete = true } = options;

  if (networkIdle) {
    try {
      await page.waitForLoadState('networkidle', { timeout: 5000 });
    } catch {
      // Network idle timeout is acceptable - page may have long-polling
    }
  }

  if (animationComplete) {
    // Wait for CSS animations to complete
    await page.evaluate(() => {
      return new Promise<void>(resolve => {
        const animations = document.getAnimations();
        if (animations.length === 0) {
          resolve();
          return;
        }
        Promise.all(animations.map(a => a.finished)).then(() => resolve());
      });
    });
  }
}

/**
 * Retry an action until it succeeds or max retries reached
 */
export async function retryAction<T>(
  action: () => Promise<T>,
  options: {
    retries?: number;
    delay?: number;
    onRetry?: (attempt: number) => void;
  } = {}
): Promise<T> {
  const { retries = 3, delay = 500, onRetry } = options;

  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      return await action();
    } catch (error) {
      lastError = error as Error;
      if (attempt < retries) {
        onRetry?.(attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError;
}
