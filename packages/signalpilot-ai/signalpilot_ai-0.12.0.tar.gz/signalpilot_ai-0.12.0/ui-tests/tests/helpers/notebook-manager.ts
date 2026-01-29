/**
 * Notebook management utility
 */
import { Page } from '@playwright/test';
import { Selectors, Timeouts } from '../page-objects/selectors';
import { waitForElement } from './wait-helpers';

export class NotebookManager {
  /**
   * Create a new Python notebook from the launcher
   */
  static async createNewNotebook(page: Page): Promise<void> {
    console.log('Creating new notebook...');

    try {
      // Wait for the launcher card to be available
      const cardFound = await waitForElement(
        page,
        Selectors.jupyterlab.launcherCard,
        { timeout: Timeouts.navigation }
      );

      if (!cardFound) {
        throw new Error('Launcher card not found');
      }

      // Click on the Python 3 (ipykernel) launcher card
      await page.click(Selectors.jupyterlab.launcherCard);

      console.log('New Python notebook created');

      // Wait for the notebook to load
      await page.waitForTimeout(Timeouts.long);

      // Press Ctrl+Shift+F (format shortcut) - Use Cmd on Mac
      const isMac = process.platform === 'darwin';
      await page.keyboard.press(isMac ? 'Meta+Shift+F' : 'Control+Shift+F');
      console.log(isMac ? 'Pressed Cmd+Shift+F' : 'Pressed Ctrl+Shift+F');
    } catch (error) {
      console.error('Could not create new notebook:', error);
      throw new Error(
        'Failed to create new notebook. Ensure JupyterLab launcher is available.'
      );
    }
  }

  /**
   * Wait for notebook to be fully loaded and interactive
   */
  static async waitForNotebookReady(page: Page): Promise<void> {
    // Wait for main dock panel
    await waitForElement(page, Selectors.jupyterlab.mainDockPanel, {
      timeout: Timeouts.navigation
    });

    // Wait for notebook cells to be present
    await page.waitForTimeout(Timeouts.medium);
  }

  /**
   * Focus the first cell in the notebook
   */
  static async focusFirstCell(page: Page): Promise<void> {
    const firstCell = page.locator('.jp-Cell').first();
    if (await firstCell.isVisible()) {
      await firstCell.click();
    }
  }
}
