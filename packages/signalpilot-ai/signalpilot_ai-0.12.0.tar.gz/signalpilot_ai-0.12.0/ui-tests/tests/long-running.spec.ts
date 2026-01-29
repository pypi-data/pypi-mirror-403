/**
 * Long-running LLM tests
 * These tests have extended timeouts and test complex workflows
 */
import {
  test,
  ChatInteractor,
  ResponseState,
  captureScreenshot,
  CONFIG,
  Timeouts,
  APIConfigurator
} from './fixtures/sage-test';
import * as path from 'path';
import * as fs from 'fs';

/**
 * Helper to download artifacts at the end of a test
 */
async function downloadTestArtifacts(
  page: ReturnType<typeof test.extend>,
  testInfo: Parameters<Parameters<typeof test>[1]>[1],
  testName: string
): Promise<void> {
  // Create output directory for this test
  const outputDir = testInfo.outputDir;
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  console.log(`Downloading test artifacts to: ${outputDir}`);

  try {
    // Download the chat thread as JSON
    console.log('Downloading thread JSON...');
    const threadPath = await APIConfigurator.downloadThreadAsJSON(
      page,
      outputDir
    );
    await testInfo.attach('Thread JSON', {
      path: threadPath,
      contentType: 'application/json'
    });
    console.log(`Thread JSON attached: ${threadPath}`);
  } catch (error) {
    console.error('Failed to download thread JSON:', error);
  }

  try {
    // Download the notebook
    console.log('Downloading notebook...');
    const notebookPath = await APIConfigurator.downloadNotebook(
      page,
      outputDir
    );
    await testInfo.attach('Notebook', {
      path: notebookPath,
      contentType: 'application/x-ipynb+json'
    });
    console.log(`Notebook attached: ${notebookPath}`);
  } catch (error) {
    console.error('Failed to download notebook:', error);
  }
}

test.describe('Long Running Tests', () => {
  test('sp500 analysis with user reply handling', async ({
    notebookWithChat: page
  }, testInfo) => {
    // Set extended timeout for this test
    testInfo.setTimeout(Timeouts.longTest);

    console.log('Testing S&P 500 Analysis with wait_for_user_reply handling');

    // Enable video recording
    page.video();

    const testName = 'sp500_test';
    let waitForUserReplyCounter = 0;
    let loopCounter = 0;
    const maxLoops = 3;

    // Send the SP_ANALYSIS prompt
    await ChatInteractor.sendMessage(page, CONFIG.TEST_PROMPTS.SP_ANALYSIS[0]);
    await captureScreenshot(
      page,
      'generation',
      'generating',
      'sp500_analysis_sent',
      testName,
      testInfo
    );

    // Capture initial generating state
    if (await ChatInteractor.waitForGeneratingState(page)) {
      await captureScreenshot(
        page,
        'generation',
        'generating',
        'sp500_initial_progress',
        testName,
        testInfo
      );
    }

    // Main loop to handle responses and user interactions
    while (loopCounter < maxLoops) {
      loopCounter++;
      console.log(`Loop iteration ${loopCounter}`);

      // Wait for response
      const responseState = await ChatInteractor.waitForResponse(page);
      console.log(`Response state detected: ${responseState}`);

      await captureScreenshot(
        page,
        'generation',
        'response',
        `loop_${loopCounter}_state_${responseState}`,
        testName,
        testInfo
      );

      // Handle different response states
      switch (responseState) {
        case ResponseState.DIFF:
          console.log(`Diff state detected in loop ${loopCounter}`);
          await captureScreenshot(
            page,
            'diff_approval',
            'diff_detected',
            `loop_${loopCounter}_diff_state`,
            testName,
            testInfo
          );

          // Handle Run All buttons
          await ChatInteractor.handleRunAllButtons(
            page,
            testName,
            loopCounter,
            testInfo
          );
          break;

        case ResponseState.WAITING_FOR_USER:
          waitForUserReplyCounter++;
          console.log(
            `Wait for user reply detected (count: ${waitForUserReplyCounter}) in loop ${loopCounter}`
          );

          await captureScreenshot(
            page,
            'user_interaction',
            'waiting_for_user',
            `loop_${loopCounter}_wait_${waitForUserReplyCounter}`,
            testName,
            testInfo
          );

          if (waitForUserReplyCounter === 1) {
            // First wait_for_user_reply - respond with "Continue"
            console.log(
              'Responding with "Continue" to first wait_for_user_reply'
            );
            await ChatInteractor.sendMessage(page, 'Continue');

            await captureScreenshot(
              page,
              'user_interaction',
              'continue_sent',
              `loop_${loopCounter}_continue_sent`,
              testName,
              testInfo
            );
          } else {
            // Second or subsequent wait_for_user_reply - exit the loop
            console.log(
              `Second wait_for_user_reply detected, ending test at loop ${loopCounter}`
            );
            await captureScreenshot(
              page,
              'completion',
              'final_wait',
              `loop_${loopCounter}_final_wait`,
              testName,
              testInfo
            );

            // Download artifacts before closing
            console.log('Downloading test artifacts...');
            await downloadTestArtifacts(page, testInfo, testName);

            console.log('Test completed successfully, saving video');
            await page.close();
            await page
              .video()
              ?.saveAs(`${CONFIG.SCREENSHOT_DIR}/${testName}_final.mp4`);
            await testInfo.attach('Final Video', {
              path: `${CONFIG.SCREENSHOT_DIR}/${testName}_final.mp4`,
              contentType: 'video/mp4'
            });
            console.log('Video saved successfully');
            return;
          }
          break;

        case ResponseState.FINISHED:
          console.log(`Finished state detected in loop ${loopCounter}`);
          await captureScreenshot(
            page,
            'completion',
            'finished',
            `loop_${loopCounter}_finished`,
            testName,
            testInfo
          );

          // Download artifacts before returning
          console.log('Downloading test artifacts...');
          await downloadTestArtifacts(page, testInfo, testName);
          return;

        default:
          console.log(
            `Unknown response state in loop ${loopCounter}: ${responseState}`
          );
          await captureScreenshot(
            page,
            'unknown',
            'unknown_state',
            `loop_${loopCounter}_unknown`,
            testName,
            testInfo
          );
      }

      // Short wait before next iteration
      await page.waitForTimeout(Timeouts.medium);
    }

    console.log(`Test reached maximum loops (${maxLoops}), ending test`);
    await captureScreenshot(
      page,
      'completion',
      'max_loops_reached',
      'final_max_loops',
      testName,
      testInfo
    );

    // Download artifacts before closing
    console.log('Downloading test artifacts...');
    await downloadTestArtifacts(page, testInfo, testName);

    console.log('Test completed, saving final video');
    await page.close();
    await page
      .video()
      ?.saveAs(`${CONFIG.SCREENSHOT_DIR}/${testName}_final.mp4`);
    await testInfo.attach('Final Video', {
      path: `${CONFIG.SCREENSHOT_DIR}/${testName}_final.mp4`,
      contentType: 'video/mp4'
    });
    console.log('Final video saved successfully');
  });
});
