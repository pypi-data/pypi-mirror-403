/**
 * LLM State tests
 * Tests chat interactions and LLM response states
 */
import {
  test,
  expect,
  ChatInteractor,
  ResponseState,
  captureScreenshot,
  CONFIG,
  Selectors
} from './fixtures/sage-test';

test.describe('LLM States', () => {
  test('chatbox opens and is ready', async ({
    notebookWithChat: page
  }, testInfo) => {
    console.log('Testing that Chatbox Opens');

    // Capture empty interface
    await captureScreenshot(
      page,
      'idle',
      'none',
      'empty_interface',
      'chatbox_opens_and_is_ready',
      testInfo
    );

    // Verify chat input is ready but empty
    const chatInput = page.locator(Selectors.chat.input);
    await expect(chatInput).toBeVisible();
    await expect(chatInput).toBeEmpty();
  });

  test('single file diff states', async ({
    notebookWithChat: page
  }, testInfo) => {
    console.log('Testing Single File Diff States');

    // Send diff-generating prompt
    await ChatInteractor.sendMessage(page, CONFIG.TEST_PROMPTS.SINGLE_DIFF[0]);
    await captureScreenshot(
      page,
      'generation',
      'generating',
      'single_diff_sent',
      'single_file_diff_states',
      testInfo
    );

    // Capture generating state
    if (await ChatInteractor.waitForGeneratingState(page)) {
      await captureScreenshot(
        page,
        'generation',
        'generating',
        'in_progress',
        'single_file_diff_states',
        testInfo
      );
    }

    // Wait for response and potential diff
    const responseState = await ChatInteractor.waitForResponse(page);
    await ChatInteractor.waitForDiffState(page);

    // Handle different response states
    switch (responseState) {
      case ResponseState.DIFF:
        await captureScreenshot(
          page,
          'generation',
          'complete',
          'diff_state',
          'single_file_diff_states',
          testInfo
        );
        break;
      case ResponseState.WAITING_FOR_USER:
        await captureScreenshot(
          page,
          'generation',
          'complete',
          'waiting_for_user',
          'single_file_diff_states',
          testInfo
        );
        break;
      case ResponseState.FINISHED:
        await captureScreenshot(
          page,
          'generation',
          'complete',
          'finished',
          'single_file_diff_states',
          testInfo
        );
        break;
    }

    // Check for diff approval state
    if (await ChatInteractor.waitForDiffApprovalState(page)) {
      await captureScreenshot(
        page,
        'diff_approval',
        'single_approval',
        'awaiting_decision',
        'single_file_diff_states',
        testInfo
      );

      // Test accepting diff
      const acceptButton = page.locator('button:has-text("Accept")');
      if ((await acceptButton.count()) > 0) {
        await acceptButton.click();
        await captureScreenshot(
          page,
          'diff_approval',
          'single_accepted',
          'after_accept',
          'single_file_diff_states',
          testInfo
        );
      }
    }
  });
});
