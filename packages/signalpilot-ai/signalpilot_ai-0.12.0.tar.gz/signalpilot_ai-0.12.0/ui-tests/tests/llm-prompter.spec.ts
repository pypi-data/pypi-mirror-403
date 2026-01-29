/**
 * LLM Prompter Test
 * A configurable test for running custom prompts through the LLM
 * Change the PROMPT constant below to test different scenarios
 */
import {
  test,
  ChatInteractor,
  ResponseState,
  Timeouts,
  APIConfigurator
} from './fixtures/sage-test';
import * as fs from 'fs';

// ============================================================
// CONFIGURE YOUR PROMPT HERE
// ============================================================
const PROMPT = 'write hello world 3 times';
const TEST_NAME = 'llm_prompter';
const MAX_LOOPS = 10;
// ============================================================

/**
 * Helper to download artifacts at the end of a test
 */
async function downloadTestArtifacts(
  page: ReturnType<typeof test.extend>,
  testInfo: Parameters<Parameters<typeof test>[1]>[1],
  testName: string
): Promise<void> {
  const outputDir = testInfo.outputDir;
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  console.log(`Downloading test artifacts to: ${outputDir}`);

  try {
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

test.describe('LLM Prompter', () => {
  test('custom prompt test', async ({ notebookWithChat: page }, testInfo) => {
    testInfo.setTimeout(Timeouts.longTest);

    console.log(`Running LLM Prompter with prompt: "${PROMPT}"`);

    let waitForUserReplyCounter = 0;
    let loopCounter = 0;

    // Send the custom prompt
    await ChatInteractor.sendMessage(page, PROMPT);

    // Capture initial generating state
    await ChatInteractor.waitForGeneratingState(page);

    // Main loop to handle responses
    while (loopCounter < MAX_LOOPS) {
      loopCounter++;
      console.log(`Loop iteration ${loopCounter}`);

      const responseState = await ChatInteractor.waitForResponse(page);
      console.log(`Response state detected: ${responseState}`);

      switch (responseState) {
        case ResponseState.DIFF:
          console.log(`Diff state detected in loop ${loopCounter}`);
          await ChatInteractor.handleRunAllButtons(
            page,
            TEST_NAME,
            loopCounter
          );
          break;

        case ResponseState.WAITING_FOR_USER:
          waitForUserReplyCounter++;
          console.log(
            `Wait for user reply detected (count: ${waitForUserReplyCounter}) in loop ${loopCounter}`
          );

          if (waitForUserReplyCounter === 1) {
            console.log(
              'Responding with "Continue" to first wait_for_user_reply'
            );
            await ChatInteractor.sendMessage(page, 'Continue');
          } else {
            console.log(
              `Second wait_for_user_reply detected, ending test at loop ${loopCounter}`
            );

            console.log('Downloading test artifacts...');
            await downloadTestArtifacts(page, testInfo, TEST_NAME);

            console.log('Test completed successfully');
            return;
          }
          break;

        case ResponseState.FINISHED:
          console.log(`Finished state detected in loop ${loopCounter}`);

          console.log('Downloading test artifacts...');
          await downloadTestArtifacts(page, testInfo, TEST_NAME);
          return;

        default:
          console.log(
            `Unknown response state in loop ${loopCounter}: ${responseState}`
          );
      }

      await page.waitForTimeout(Timeouts.medium);
    }

    console.log(`Test reached maximum loops (${MAX_LOOPS}), ending test`);

    console.log('Downloading test artifacts...');
    await downloadTestArtifacts(page, testInfo, TEST_NAME);

    console.log('Test completed');
  });
});
