/**
 * API Configuration utility for setting up JWT tokens and running commands
 */
import { Page, Download } from '@playwright/test';
import { Selectors, Timeouts } from '../page-objects/selectors';
import { waitForElement } from './wait-helpers';
import * as path from 'path';

export class APIConfigurator {
  /**
   * Setup JWT token via command palette test mode
   */
  static async setupJWTToken(
    page: Page,
    jwtToken: string,
    modelUrl: string,
    modelId: string
  ): Promise<void> {
    if (!jwtToken) {
      throw new Error('SAGE_JWT_TOKEN not provided in configuration');
    }

    console.log('Setting up API configuration...');

    // Wait for JupyterLab to be ready
    await waitForElement(page, Selectors.jupyterlab.mainDockPanel, {
      timeout: Timeouts.navigation
    });

    try {
      console.log('Opening command palette...');
      const isMac = process.platform === 'darwin';
      await page.keyboard.press(isMac ? 'Meta+Shift+C' : 'Control+Shift+C');

      // Wait for command palette to appear - use short timeout with 1 retry for fast failure
      const paletteFound = await waitForElement(
        page,
        Selectors.jupyterlab.commandPalette,
        {
          timeout: 5000,
          retries: 1
        }
      );
      if (!paletteFound) {
        throw new Error('Command palette did not appear within 5 seconds');
      }

      // Find the search input and enter "activate test mode"
      const searchInput = page.locator(
        Selectors.jupyterlab.commandPaletteInput
      );
      await searchInput.fill('activate test mode', { timeout: 5000 });

      console.log('Searching for "activate test mode" command...');

      // Wait for the command to appear in the results - use short timeout with 1 retry
      const contentFound = await waitForElement(
        page,
        Selectors.jupyterlab.commandPaletteContent,
        {
          timeout: 5000,
          retries: 1
        }
      );
      if (!contentFound) {
        console.log('Command palette content not found within timeout');
      }

      // Debug: Print the full command palette contents including innerHTML
      const commandPaletteHTML = await page.evaluate(() => {
        const palette = document.querySelector(
          '.lm-Widget.lm-Panel.jp-ModalCommandPalette.jp-ThemedContainer'
        );
        if (palette) {
          return {
            innerHTML: palette.innerHTML,
            outerHTML: palette.outerHTML,
            classList: Array.from(palette.classList),
            isHidden: palette.classList.contains('lm-mod-hidden'),
            childCount: palette.children.length,
            // Get the input value
            inputValue: (
              palette.querySelector('.lm-CommandPalette-input') as HTMLInputElement
            )?.value,
            // Get the content container info
            contentContainer: {
              exists: !!palette.querySelector('.lm-CommandPalette-content'),
              childCount:
                palette.querySelector('.lm-CommandPalette-content')?.children
                  .length ?? 0,
              innerHTML:
                palette.querySelector('.lm-CommandPalette-content')?.innerHTML ??
                'N/A'
            },
            // Get just the command items for easier reading
            commandItems: Array.from(
              palette.querySelectorAll('.lm-CommandPalette-item')
            ).map(item => ({
              text: item.textContent?.trim(),
              dataCommand: item.getAttribute('data-command'),
              className: item.className
            })),
            // Get all data-command attributes in the palette
            allDataCommands: Array.from(
              palette.querySelectorAll('[data-command]')
            ).map(el => el.getAttribute('data-command'))
          };
        }
        return { error: 'Palette element not found' };
      });
      console.log(
        'Command Palette Debug Info:',
        JSON.stringify(commandPaletteHTML, null, 2)
      );

      // Look for the "Activate Test Mode (Set JWT Token)" command and click it
      // Use a short 5 second timeout to fail fast if command isn't found
      const testModeCommand = page.locator(Selectors.auth.testModeCommand);
      await testModeCommand.click({ timeout: 5000 });

      console.log('Test mode activated via command palette');

      // Wait for JWT token input dialog to appear
      console.log('Waiting for JWT token input dialog...');
      await waitForElement(page, Selectors.auth.dialogInput, {
        timeout: Timeouts.selector
      });

      // Fill the JWT token into the password input field
      const jwtTokenInput = page.locator(Selectors.auth.jwtTokenInput);
      await jwtTokenInput.fill(jwtToken);
      console.log('JWT token entered');

      // Click the "Set Token" button
      const setTokenButton = page.locator(Selectors.auth.submitButton);
      await setTokenButton.click();
      console.log('"Set Token" button clicked');

      // Click the "OK" button
      await waitForElement(page, Selectors.auth.okButton, {
        timeout: Timeouts.selector
      });
      const okButton = page.locator(Selectors.auth.okButton);
      await okButton.click();
      console.log('"OK" button clicked');

      await page.waitForTimeout(Timeouts.medium);
      console.log('API configuration complete');
    } catch (error) {
      console.error('Could not access test mode via command palette');
      throw new Error(
        'Command palette or test mode command not found. Ensure the Sage AI extension is installed and enabled.'
      );
    }
  }

  /**
   * Dismiss the welcome/auth modal if present
   */
  static async dismissWelcomeModal(page: Page): Promise<boolean> {
    try {
      const dismissButton = page.locator(Selectors.auth.welcomeDismissButton);
      const isVisible = await dismissButton.isVisible().catch(() => false);

      if (isVisible) {
        await dismissButton.click();
        await page.waitForTimeout(Timeouts.short);
        console.log('Welcome modal dismissed');
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  /**
   * Handle the "Rename file" dialog that appears when saving untitled notebooks
   * Checks the "Do not ask for rename on first save" checkbox and clicks "Rename and Save"
   * @param page The Playwright page
   * @returns true if dialog was found and handled, false otherwise
   */
  static async handleRenameDialog(page: Page): Promise<boolean> {
    try {
      // Check if the rename dialog is present
      const renameDialog = page.locator(
        '.jp-Dialog-content:has(.jp-Dialog-header:text("Rename file"))'
      );

      if (
        await renameDialog
          .isVisible({ timeout: Timeouts.short })
          .catch(() => false)
      ) {
        console.log('Rename dialog detected, handling...');

        // Check the "Do not ask for rename on first save" checkbox
        const checkbox = page.locator(
          '.jp-Dialog-checkbox input[type="checkbox"]'
        );
        if (await checkbox.isVisible()) {
          await checkbox.check();
          console.log('Checked "Do not ask for rename on first save"');
        }

        // Click "Rename and Save" button
        const renameAndSaveButton = page.locator(
          '.jp-Dialog-button.jp-mod-accept'
        );
        await renameAndSaveButton.click();
        console.log('Clicked "Rename and Save"');

        await page.waitForTimeout(Timeouts.short);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  /**
   * Clean up any lingering modals
   */
  static async cleanupModals(page: Page): Promise<void> {
    await page.evaluate(() => {
      const allModals = document.querySelectorAll(
        'div[role="dialog"], .modal, .fade, .modal-backdrop'
      );
      allModals.forEach(modal => modal.remove());

      // Reset body state
      document.body.className = document.body.className.replace(
        /modal-open|fade/g,
        ''
      );
      document.body.style.cssText = '';
    });

    // Clear any lingering UI states
    await page.keyboard.press('Escape');
    await page.waitForTimeout(Timeouts.short);
  }

  /**
   * Run a command via the command palette
   * @param page The Playwright page
   * @param commandLabel The label to search for in the command palette
   * @param commandSelector Optional specific selector for the command item
   * @returns Promise that resolves when command is executed
   */
  static async runCommand(
    page: Page,
    commandLabel: string,
    commandSelector?: string
  ): Promise<void> {
    console.log(`Running command: ${commandLabel}`);

    // Open command palette
    const isMac = process.platform === 'darwin';
    await page.keyboard.press(isMac ? 'Meta+Shift+C' : 'Control+Shift+C');

    // Wait for command palette to appear
    await waitForElement(page, Selectors.jupyterlab.commandPalette, {
      timeout: Timeouts.selector
    });

    // Search for the command
    const searchInput = page.locator(Selectors.jupyterlab.commandPaletteInput);
    await searchInput.fill(commandLabel);

    // Wait for results
    await waitForElement(page, Selectors.jupyterlab.commandPaletteContent, {
      timeout: Timeouts.selector
    });

    await page.waitForTimeout(Timeouts.short);

    // Click the command - use specific selector if provided, otherwise click first result
    if (commandSelector) {
      const command = page.locator(commandSelector);
      await command.click();
    } else {
      // Click the first matching result in the command palette
      const firstResult = page
        .locator(
          `${Selectors.jupyterlab.commandPaletteContent} .lm-CommandPalette-item`
        )
        .first();
      await firstResult.click();
    }

    console.log(`Command executed: ${commandLabel}`);
    await page.waitForTimeout(Timeouts.medium);
  }

  /**
   * Download the current chat thread as JSON via command palette
   * @param page The Playwright page
   * @param outputDir Directory to save the downloaded file
   * @returns Path to the downloaded file
   */
  static async downloadThreadAsJSON(
    page: Page,
    outputDir: string
  ): Promise<string> {
    console.log('Downloading current thread as JSON...');

    // Set up download listener before triggering the download
    const downloadPromise = page.waitForEvent('download', {
      timeout: Timeouts.modal
    });

    // Run the download thread command
    await this.runCommand(
      page,
      'Download Current Thread',
      '[data-command$=":download-thread"]'
    );

    // Wait for download to start
    const download: Download = await downloadPromise;

    // Save the file to the output directory
    const filename = download.suggestedFilename() || 'thread.json';
    const outputPath = path.join(outputDir, filename);
    await download.saveAs(outputPath);

    console.log(`Thread downloaded to: ${outputPath}`);
    return outputPath;
  }

  /**
   * Download the current notebook via JupyterLab's built-in download
   * @param page The Playwright page
   * @param outputDir Directory to save the downloaded file
   * @returns Path to the downloaded file
   */
  static async downloadNotebook(
    page: Page,
    outputDir: string
  ): Promise<string> {
    console.log('Downloading current notebook...');

    // Click on the main dock panel to ensure focus is on the notebook
    const mainPanel = page.locator('#jp-main-dock-panel');
    if ((await mainPanel.count()) > 0) {
      await mainPanel.click({ position: { x: 100, y: 100 } });
      await page.waitForTimeout(Timeouts.short);
    }

    // Save the notebook first (Ctrl+S on Windows/Linux, Cmd+S on Mac)
    console.log('Saving notebook before download...');
    const isMac = process.platform === 'darwin';
    await page.keyboard.press(isMac ? 'Meta+s' : 'Control+s');

    // Wait a moment and check for rename dialog
    await page.waitForTimeout(Timeouts.medium);
    await this.handleRenameDialog(page);

    // Wait for save to complete
    await page.waitForTimeout(Timeouts.medium);

    // Set up download listener before triggering the download
    const downloadPromise = page.waitForEvent('download', {
      timeout: Timeouts.modal
    });

    // Run JupyterLab's download command via command palette
    await this.runCommand(page, 'Download');

    // Wait for download to start
    const download: Download = await downloadPromise;

    // Save the file to the output directory
    const filename = download.suggestedFilename() || 'notebook.ipynb';
    const outputPath = path.join(outputDir, filename);
    await download.saveAs(outputPath);

    console.log(`Notebook downloaded to: ${outputPath}`);
    return outputPath;
  }
}
