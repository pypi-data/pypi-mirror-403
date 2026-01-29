/**
 * Chat interaction utilities
 */
import { Page, expect, TestInfo } from '@playwright/test';
import { Selectors, Timeouts } from '../page-objects/selectors';
import { waitForElement, waitForAnyElement } from './wait-helpers';
import { captureScreenshot } from './screenshot';
import CONFIG from '../config';

/**
 * Enum for different response states
 */
export enum ResponseState {
  DIFF = 'DIFF',
  WAITING_FOR_USER = 'WAITING_FOR_USER',
  FINISHED = 'FINISHED'
}

export class ChatInteractor {
  /**
   * Wait for chat interface to be ready
   */
  static async waitForChatReady(page: Page): Promise<void> {
    // Wait for the chat container to be present
    const found = await waitForElement(page, Selectors.chat.container, {
      timeout: Timeouts.navigation
    });

    if (!found) {
      throw new Error('Chat container not found');
    }

    await page.waitForTimeout(Timeouts.medium);

    // Wait for the chatbox to be loaded (not in loading state)
    const chatbox = page.locator(Selectors.chat.chatbox);
    await expect(chatbox).toBeVisible({ timeout: Timeouts.selector });

    // Wait for the input section to be ready
    // Try multiple selectors since the input could be in different forms
    const inputSelectors = [
      Selectors.chat.inputContainer,
      Selectors.chat.inputRow,
      Selectors.chat.richTextInput,
      Selectors.chat.sendButton
    ];

    let inputFound = false;
    for (const selector of inputSelectors) {
      const element = page.locator(selector);
      if ((await element.count()) > 0) {
        await expect(element.first()).toBeVisible({
          timeout: Timeouts.selector
        });
        inputFound = true;
        break;
      }
    }

    if (!inputFound) {
      // Fallback: just wait for send button which should always be present
      await expect(page.locator(Selectors.chat.sendButton)).toBeVisible({
        timeout: Timeouts.selector
      });
    }

    console.log('Chat is ready for interaction');
  }

  /**
   * Send a message in the chat
   */
  static async sendMessage(page: Page, message: string): Promise<void> {
    // Find the chat input - try multiple selectors
    const inputSelectors = [
      `${Selectors.chat.container} ${Selectors.chat.richTextInput}`,
      `${Selectors.chat.container} ${Selectors.chat.inputRow} [contenteditable="true"]`,
      `${Selectors.chat.container} [contenteditable="true"]`,
      `${Selectors.chat.chatbox} [contenteditable="true"]`
    ];

    let chatInput = null;
    for (const selector of inputSelectors) {
      const element = page.locator(selector);
      if ((await element.count()) > 0) {
        chatInput = element.first();
        break;
      }
    }

    if (!chatInput) {
      throw new Error('Chat input not found');
    }

    // Find send button
    const sendButton = page.locator(Selectors.chat.sendButton).first();

    // Clear and enter message
    await chatInput.click();
    await chatInput.fill(''); // Clear
    await chatInput.fill(message);

    // Send message
    await expect(sendButton).toBeVisible();
    await sendButton.click();
  }

  /**
   * Wait for diff state to appear (CodeMirror changed lines)
   */
  static async waitForDiffState(
    page: Page,
    timeout: number = CONFIG.TEST_TIMEOUT
  ): Promise<boolean> {
    try {
      await page.waitForSelector(Selectors.codeMirror.changedLine, {
        timeout,
        state: 'visible'
      });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Wait for LLM response and determine the state
   * Uses Promise.race to check multiple conditions simultaneously
   */
  static async waitForResponse(
    page: Page,
    timeout: number = Timeouts.response
  ): Promise<ResponseState> {
    // First wait for any response message (AI or system message)
    try {
      await page.waitForSelector(
        `${Selectors.messages.aiMessage}, ${Selectors.messages.systemMessage}`,
        {
          timeout,
          state: 'visible'
        }
      );
    } catch {
      // Continue even if no message appears
    }

    // Use Promise.race to check both selectors simultaneously
    try {
      const result = await Promise.race([
        // Check for diff state
        page
          .waitForSelector(Selectors.llmState.diffState, {
            timeout,
            state: 'visible'
          })
          .then(() => ResponseState.DIFF),

        // Check for waiting for user state
        page
          .waitForSelector(Selectors.llmState.waitingForUser, {
            timeout,
            state: 'visible'
          })
          .then(() => ResponseState.WAITING_FOR_USER),

        // Also check for waiting reply container
        page
          .waitForSelector(Selectors.llmState.waitingReplyContainer, {
            timeout,
            state: 'visible'
          })
          .then(() => ResponseState.WAITING_FOR_USER),

        // Timeout fallback
        new Promise<ResponseState>(resolve =>
          setTimeout(() => resolve(ResponseState.FINISHED), timeout)
        )
      ]);

      return result;
    } catch (error) {
      console.warn(
        'waitForResponse: No expected state found, assuming finished'
      );
      return ResponseState.FINISHED;
    }
  }

  /**
   * Check if LLM is currently generating
   */
  static async waitForGeneratingState(page: Page): Promise<boolean> {
    try {
      const generatingSelectors = [
        Selectors.indicators.generating,
        Selectors.indicators.loading,
        Selectors.indicators.generatingTestId,
        Selectors.indicators.spinning,
        Selectors.indicators.loadingDots
      ];

      for (const selector of generatingSelectors) {
        if ((await page.locator(selector).count()) > 0) {
          return true;
        }
      }

      // Alternative: Check if send button is disabled
      const sendButton = page.locator(Selectors.chat.sendButton);
      const isDisabled = await sendButton.getAttribute('disabled');
      return isDisabled !== null;
    } catch {
      return false;
    }
  }

  /**
   * Check for diff approval UI elements
   */
  static async waitForDiffApprovalState(page: Page): Promise<boolean> {
    try {
      const diffSelectors = [
        '.sage-ai-diff',
        '.sage-ai-code-diff',
        '[data-testid="diff-approval"]',
        'button:has-text("Accept")',
        'button:has-text("Reject")',
        '.diff-container'
      ];

      for (const selector of diffSelectors) {
        if ((await page.locator(selector).count()) > 0) {
          return true;
        }
      }
      return false;
    } catch {
      return false;
    }
  }

  /**
   * Setup multi-diff state for testing
   * Sends a prompt that generates multiple diffs
   */
  static async setupMultiDiffState(
    page: Page,
    testName: string,
    testInfo: TestInfo
  ): Promise<ReturnType<typeof page.locator>> {
    console.log(`Setting up Multi-Diff state for ${testName}`);

    // Send multi-file diff prompt
    await ChatInteractor.sendMessage(page, CONFIG.TEST_PROMPTS.MULTI_DIFF[0]);
    await captureScreenshot(
      page,
      'generation',
      'generating',
      'multi_diff_sent',
      testName,
      testInfo
    );

    // Capture generating state
    if (await ChatInteractor.waitForGeneratingState(page)) {
      await captureScreenshot(
        page,
        'generation',
        'generating',
        'multi_file_progress',
        testName,
        testInfo
      );
    }

    // Wait for response
    await ChatInteractor.waitForResponse(page);

    // Check for multi-diff approval state
    if (await ChatInteractor.waitForDiffApprovalState(page)) {
      await captureScreenshot(
        page,
        'diff_approval',
        'multi_approval',
        'multiple_files',
        testName,
        testInfo
      );

      // Click the diff summary bar to expand the diff list
      const diffSummaryBar = page.locator(Selectors.diff.summaryBar);
      await expect(diffSummaryBar).toBeVisible();
      await diffSummaryBar.click();
      await page.waitForTimeout(Timeouts.short);

      // Look for diff list inside the LLM state display where hover actions are enabled
      const llmStateDisplay = page.locator(Selectors.llmState.display);
      await expect(llmStateDisplay).toBeVisible();
      const diffList = llmStateDisplay.locator(Selectors.diff.list);
      await expect(diffList).toBeVisible();
      // Use itemWithHover selector to get diff items that have hover actions enabled
      const diffItems = diffList.locator(Selectors.diff.itemWithHover);
      await expect(diffItems).toHaveCount(3);
      console.log('Confirmed 3 diff items in the list');

      await captureScreenshot(
        page,
        'diff_approval',
        'verified',
        'three_diffs_confirmed',
        testName,
        testInfo
      );

      return diffItems;
    }

    throw new Error('Failed to reach diff approval state');
  }

  /**
   * Handle Run All / Approve All buttons during diff workflow
   */
  static async handleRunAllButtons(
    page: Page,
    testName: string,
    loopCounter: number,
    testInfo?: TestInfo
  ): Promise<void> {
    console.log(`Handling Run All buttons in loop ${loopCounter}`);

    // Look for various Run All button selectors
    const runAllButton1 = page.locator(Selectors.diff.approveAll);
    const runAllButton2 = page.locator(Selectors.diff.navigationRunAll);
    const approveAllButton = page.locator(Selectors.diff.rejectAll);

    await captureScreenshot(
      page,
      'diff_handling',
      'before_run_all',
      `loop_${loopCounter}_before_run_all`,
      testName,
      testInfo
    );

    let buttonClicked = false;

    // Try clicking the first Run All button
    if ((await runAllButton1.count()) > 0) {
      console.log('Clicking first Run All button');
      await runAllButton1.click();
      buttonClicked = true;
      await captureScreenshot(
        page,
        'diff_handling',
        'run_all_1_clicked',
        `loop_${loopCounter}_run_all_1_clicked`,
        testName,
        testInfo
      );
    }

    await page.waitForTimeout(Timeouts.medium);

    // Try clicking the second Run All button
    if ((await runAllButton2.count()) > 0) {
      console.log('Clicking second Run All button (navigation)');
      await runAllButton2.click();
      buttonClicked = true;
      await captureScreenshot(
        page,
        'diff_handling',
        'run_all_2_clicked',
        `loop_${loopCounter}_run_all_2_clicked`,
        testName,
        testInfo
      );
    }

    // Fallback to Approve All
    if (!buttonClicked && (await approveAllButton.count()) > 0) {
      console.log('No Run All buttons found, clicking Approve All');
      await approveAllButton.click();
      buttonClicked = true;
      await captureScreenshot(
        page,
        'diff_handling',
        'approve_all_clicked',
        `loop_${loopCounter}_approve_all_clicked`,
        testName,
        testInfo
      );
    }

    // Wait for execution to complete
    await page.waitForTimeout(Timeouts.long);

    await captureScreenshot(
      page,
      'diff_handling',
      'after_run_all',
      `loop_${loopCounter}_after_run_all`,
      testName,
      testInfo
    );

    if (buttonClicked) {
      console.log('Run All/Approve All buttons handling completed');
    } else {
      console.log('No Run All or Approve All buttons found');
    }
  }
}
