/**
 * Diff Interactions tests
 * Tests the diff approval workflow and UI interactions
 */
import {
  test,
  expect,
  ChatInteractor,
  captureScreenshot,
  CONFIG,
  Selectors,
  Timeouts
} from './fixtures/sage-test';

test.describe('Diff Interactions', () => {
  test('inline chat diffs', async ({ notebookWithChat: page }, testInfo) => {
    const testName = 'inline_chat_diffs';
    const diffItems = await ChatInteractor.setupMultiDiffState(
      page,
      testName,
      testInfo
    );

    console.log('Testing inline chat diff hover buttons');

    // diffItems returned by setupMultiDiffState is already verified to have 3 items
    // No need to re-verify the diff list container here

    // Handle diff item 1: Click REJECT button
    console.log('Processing diff item 1: REJECT');
    const item1 = diffItems.nth(0);
    await item1.hover();
    await page.waitForTimeout(300);

    const item1RejectButton = item1.locator(Selectors.diff.rejectButton);
    await expect(item1RejectButton).toBeVisible();
    await item1RejectButton.click();
    await page.waitForTimeout(Timeouts.short);

    await captureScreenshot(
      page,
      'diff_approval',
      'item1_reject',
      'after_reject',
      testName,
      testInfo
    );

    // Handle diff item 2: Click RUN button
    console.log('Processing diff item 2: RUN');
    const item2 = diffItems.nth(1);
    await item2.hover();
    await page.waitForTimeout(300);

    const item2RunButton = item2.locator(Selectors.diff.runButton);
    await expect(item2RunButton).toBeVisible();
    await item2RunButton.click();
    await page.waitForTimeout(Timeouts.short);

    await captureScreenshot(
      page,
      'diff_approval',
      'item2_run',
      'after_run',
      testName,
      testInfo
    );

    // Handle diff item 3: Click APPROVE button
    console.log('Processing diff item 3: APPROVE');
    const item3 = diffItems.nth(2);
    await item3.hover();
    await page.waitForTimeout(300);

    const item3ApproveButton = item3.locator(Selectors.diff.approveButton);
    await expect(item3ApproveButton).toBeVisible();
    await item3ApproveButton.click();
    await page.waitForTimeout(Timeouts.short);

    await captureScreenshot(
      page,
      'diff_approval',
      'item3_approve',
      'after_approve',
      testName,
      testInfo
    );

    console.log('Inline chat diffs test completed successfully');
  });

  test('state display diffs', async ({ notebookWithChat: page }, testInfo) => {
    const testName = 'state_display_diffs';
    console.log(`Testing diff hover actions for ${testName}`);

    // Setup multi-diff state (this already clicks the summary bar to expand the diff list)
    const diffItems = await ChatInteractor.setupMultiDiffState(page, testName, testInfo);

    // Note: setupMultiDiffState already clicked the summary bar and returned diff items
    // No need to click again or re-locate the diff list

    await captureScreenshot(
      page,
      'diff_hover_actions',
      'summary_bar_clicked',
      'after_summary_bar_click',
      testName,
      testInfo
    );

    // diffItems is already returned by setupMultiDiffState with the correct locator
    const itemCount = await diffItems.count();
    console.log(`Found ${itemCount} diff items with hover actions`);

    await captureScreenshot(
      page,
      'diff_hover_actions',
      'diff_list_found',
      'diff_list_visible',
      testName,
      testInfo
    );

    // Process each diff item: Click one button per item (Reject, Run, Approve)
    const actions = ['reject', 'run', 'approve'] as const;

    for (let i = 0; i < Math.min(itemCount, 3); i++) {
      const currentItem = diffItems.nth(i);
      const action = actions[i];
      console.log(`Processing diff item ${i + 1}: ${action.toUpperCase()}`);

      // Hover over the item to reveal actions
      await currentItem.hover();
      await page.waitForTimeout(300);

      await captureScreenshot(
        page,
        'diff_hover_actions',
        `item_${i + 1}_hover`,
        'actions_revealed',
        testName,
        testInfo
      );

      // Click the appropriate button
      let buttonSelector: string;
      if (action === 'reject') {
        buttonSelector = Selectors.diff.actionReject;
      } else if (action === 'run') {
        buttonSelector = Selectors.diff.actionRun;
      } else {
        buttonSelector = Selectors.diff.actionApprove;
      }

      const button = currentItem.locator(buttonSelector);
      await expect(button).toBeVisible();
      await button.click();
      await page.waitForTimeout(Timeouts.short);

      await captureScreenshot(
        page,
        'diff_hover_actions',
        `item_${i + 1}_${action}`,
        `after_${action}_click`,
        testName,
        testInfo
      );

      console.log(`Completed ${action} action for item ${i + 1}`);
    }

    // Final screenshot
    await captureScreenshot(
      page,
      'diff_hover_actions',
      'all_items_processed',
      'final_state',
      testName,
      testInfo
    );

    console.log('All diff hover actions completed successfully');
  });

  test('navigation widget - reject all', async ({
    notebookWithChat: page
  }, testInfo) => {
    const testName = 'navigation_widget_diffs_reject_all';
    await ChatInteractor.setupMultiDiffState(page, testName, testInfo);

    console.log('Testing navigation widget Reject All button');

    // Look for the navigation button section
    const navigationButtonSection = page.locator(
      Selectors.diff.navigationSection
    );
    await expect(navigationButtonSection).toBeVisible();

    await captureScreenshot(
      page,
      'diff_approval',
      'navigation_buttons',
      'buttons_visible',
      testName,
      testInfo
    );

    // Click the Reject All button
    const rejectAllButton = navigationButtonSection.locator(
      Selectors.diff.navigationRejectAll
    );
    await expect(rejectAllButton).toBeVisible();

    // Verify the button contains the expected text and icon
    await expect(rejectAllButton.locator('span')).toContainText('Reject All');
    await expect(
      rejectAllButton.locator(Selectors.diff.rejectIcon)
    ).toBeVisible();

    console.log('Clicking Reject All button');
    await rejectAllButton.click();
    await page.waitForTimeout(Timeouts.medium);

    await captureScreenshot(
      page,
      'diff_approval',
      'reject_all',
      'after_reject_all_click',
      testName,
      testInfo
    );

    console.log('Reject All button test completed successfully');
  });

  test('navigation widget - approve all', async ({
    notebookWithChat: page
  }, testInfo) => {
    const testName = 'navigation_widget_diffs_approve_all';
    await ChatInteractor.setupMultiDiffState(page, testName, testInfo);

    console.log('Testing navigation widget Approve All button');

    // Look for the navigation button section
    const navigationButtonSection = page.locator(
      Selectors.diff.navigationSection
    );
    await expect(navigationButtonSection).toBeVisible();

    await captureScreenshot(
      page,
      'diff_approval',
      'navigation_buttons',
      'buttons_visible',
      testName,
      testInfo
    );

    // Click the Approve All button
    const approveAllButton = navigationButtonSection.locator(
      Selectors.diff.navigationApproveAll
    );
    await expect(approveAllButton).toBeVisible();

    // Verify the button contains the expected text and icon
    await expect(approveAllButton.locator('span')).toContainText('Approve All');
    await expect(
      approveAllButton.locator(Selectors.diff.approveIcon)
    ).toBeVisible();

    console.log('Clicking Approve All button');
    await approveAllButton.click();
    await page.waitForTimeout(Timeouts.medium);

    await captureScreenshot(
      page,
      'diff_approval',
      'approve_all',
      'after_approve_all_click',
      testName,
      testInfo
    );

    console.log('Approve All button test completed successfully');
  });

  test('navigation widget - run all', async ({
    notebookWithChat: page
  }, testInfo) => {
    const testName = 'navigation_widget_diffs_run_all';
    await ChatInteractor.setupMultiDiffState(page, testName, testInfo);

    console.log('Testing navigation widget Run All button');

    // Look for the navigation button section
    const navigationButtonSection = page.locator(
      Selectors.diff.navigationSection
    );
    await expect(navigationButtonSection).toBeVisible();

    await captureScreenshot(
      page,
      'diff_approval',
      'navigation_buttons',
      'buttons_visible',
      testName,
      testInfo
    );

    // Click the Run All button
    const runAllButton = navigationButtonSection.locator(
      Selectors.diff.navigationRunAll
    );
    await expect(runAllButton).toBeVisible();

    // Verify the button contains the expected text
    await expect(runAllButton.locator('span')).toContainText('Run All');

    console.log('Clicking Run All button');
    await runAllButton.click();
    await page.waitForTimeout(Timeouts.medium);

    await captureScreenshot(
      page,
      'diff_approval',
      'run_all',
      'after_run_all_click',
      testName,
      testInfo
    );

    console.log('Run All button test completed successfully');
  });

  test('inline cell diffs with codemirror', async ({
    notebookWithChat: page
  }, testInfo) => {
    // This test sends multiple prompts, so it needs more time
    test.setTimeout(120000);

    const testName = 'inline_cell_diffs';
    console.log(
      `Testing inline cell diffs with cm-chunkButtons for ${testName}`
    );

    // Setup multi-diff state using the first MULTI_DIFF prompt
    console.log('Setting up multi-diff state with first prompt');
    await ChatInteractor.sendMessage(page, CONFIG.TEST_PROMPTS.MULTI_DIFF[0]);
    await ChatInteractor.waitForResponse(page);
    await page.waitForTimeout(Timeouts.short);

    await captureScreenshot(
      page,
      'inline_cell_diffs',
      'initial_setup',
      'after_first_prompt',
      testName,
      testInfo
    );

    // Find all cm-chunkButtons components on the page
    console.log('Searching for cm-chunkButtons components');
    let chunkButtons = page.locator(Selectors.codeMirror.chunkButtons);
    const chunkButtonsCount = await chunkButtons.count();
    console.log(`Found ${chunkButtonsCount} cm-chunkButtons components`);

    // Verify we have exactly 3 components as expected
    await expect(chunkButtons).toHaveCount(3);

    await captureScreenshot(
      page,
      'inline_cell_diffs',
      'chunk_buttons_found',
      'all_buttons_visible',
      testName,
      testInfo
    );

    // Process first chunk button: REJECT
    console.log('Processing first cm-chunkButtons: REJECT');
    const firstChunkButton = chunkButtons.nth(0);
    const firstRejectButton = firstChunkButton.locator(
      Selectors.codeMirror.rejectButton
    );
    await expect(firstRejectButton).toBeVisible();
    await firstRejectButton.click();
    await page.waitForTimeout(Timeouts.short);

    await captureScreenshot(
      page,
      'inline_cell_diffs',
      'first_chunk',
      'after_reject',
      testName,
      testInfo
    );

    // Re-query chunkButtons as DOM may have changed
    chunkButtons = page.locator(Selectors.codeMirror.chunkButtons);

    // Process second chunk button: ACCEPT
    console.log('Processing second cm-chunkButtons: ACCEPT');
    const secondChunkButton = chunkButtons.nth(0);
    const secondAcceptButton = secondChunkButton.locator(
      Selectors.codeMirror.acceptButton
    );
    await expect(secondAcceptButton).toBeVisible();
    await secondAcceptButton.click();
    await page.waitForTimeout(Timeouts.short);

    await captureScreenshot(
      page,
      'inline_cell_diffs',
      'second_chunk',
      'after_accept',
      testName,
      testInfo
    );

    // Re-query chunkButtons
    chunkButtons = page.locator(Selectors.codeMirror.chunkButtons);

    // Process third chunk button: ACCEPT
    console.log('Processing third cm-chunkButtons: ACCEPT');
    const thirdChunkButton = chunkButtons.nth(0);
    const thirdAcceptButton = thirdChunkButton.locator(
      Selectors.codeMirror.acceptButton
    );
    await expect(thirdAcceptButton).toBeVisible();
    await thirdAcceptButton.click();
    await page.waitForTimeout(Timeouts.medium);

    await captureScreenshot(
      page,
      'inline_cell_diffs',
      'third_chunk',
      'after_accept',
      testName,
      testInfo
    );

    // Send the second MULTI_DIFF prompt
    console.log('Sending second MULTI_DIFF prompt');
    await ChatInteractor.sendMessage(page, CONFIG.TEST_PROMPTS.MULTI_DIFF[1]);
    await ChatInteractor.waitForResponse(page);
    await page.waitForTimeout(Timeouts.short);

    await captureScreenshot(
      page,
      'inline_cell_diffs',
      'second_prompt',
      'after_second_prompt',
      testName,
      testInfo
    );

    // Find the new cm-chunkButtons component (should be only 1)
    console.log('Searching for new cm-chunkButtons after second prompt');
    const newChunkButtons = page.locator(Selectors.codeMirror.chunkButtons);
    const newChunkButtonsCount = await newChunkButtons.count();
    console.log(
      `Found ${newChunkButtonsCount} cm-chunkButtons components after second prompt`
    );

    // There should be at least 1 new diff to accept
    await expect(newChunkButtons.first()).toBeVisible();

    // Accept the change from the second prompt
    console.log('Processing new cm-chunkButtons: ACCEPT');
    const newAcceptButton = newChunkButtons
      .first()
      .locator(Selectors.codeMirror.acceptButton);
    await expect(newAcceptButton).toBeVisible();
    await newAcceptButton.click();
    await page.waitForTimeout(Timeouts.medium);

    await captureScreenshot(
      page,
      'inline_cell_diffs',
      'final_chunk',
      'after_final_accept',
      testName,
      testInfo
    );

    // Final screenshot
    await captureScreenshot(
      page,
      'inline_cell_diffs',
      'completed',
      'final_state',
      testName,
      testInfo
    );

    console.log('Inline cell diffs test completed successfully');
  });
});
