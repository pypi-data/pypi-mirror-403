import { JupyterFrontEnd } from '@jupyterlab/application';
import { ICommandPalette } from '@jupyterlab/apputils';
import * as React from 'react';
// @ts-expect-error react-dom/client types not available in this version
import * as ReactDOM from 'react-dom/client';
import { useAppStore } from '../../stores/appStore';
import { getChatboxState } from '../../stores/chatboxStore';
import {
  getNotebookTracker,
  getFileExplorerWidget,
  getDatabaseManagerWidget
} from '../../stores/servicesStore';
import { DatabaseType } from '../../stores/databaseStore';
import {
  DatabaseType as CTADatabaseType,
  WelcomeCTAContent
} from '../../Components/WelcomeCTA';

// LocalStorage key for CTA collapsed state
const CTA_COLLAPSED_KEY = 'sage-ai-cta-collapsed';

/**
 * Register the add CTA div command for the Welcome to Your AI Data Assistant interface
 */
export function registerAddCtaDivCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const addCtaDivCommand: string = 'sage-ai:add-cta-div';

  app.commands.addCommand(addCtaDivCommand, {
    label: 'Add CTA Div to Notebook',
    isVisible: () => false,
    execute: async () => {
      try {
        // Get the current notebook tracker
        const notebookTracker = getNotebookTracker();
        const currentNotebook = notebookTracker.currentWidget;

        if (!currentNotebook) {
          console.log('No active notebook found');
          return;
        }

        // Check if CTA already exists in the current notebook
        const existingCta = currentNotebook.node.querySelector(
          '.sage-ai-data-cta-container'
        );
        if (existingCta) {
          console.log(
            '[WelcomeCTA] CTA already exists in this notebook, skipping render'
          );
          return;
        }

        // Create the main CTA container
        const ctaContainer = document.createElement('div');
        ctaContainer.className = 'sage-ai-data-cta-container';

        // Check localStorage for collapsed state
        // In demo mode, default to collapsed
        const isDemoMode = useAppStore.getState().isDemoMode;
        const initialCollapsed =
          isDemoMode || localStorage.getItem(CTA_COLLAPSED_KEY) === 'true';

        // Apply initial collapsed state
        if (initialCollapsed) {
          ctaContainer.classList.add('collapsed');
        }

        // Create a state object for React to control
        let isCollapsed = initialCollapsed;

        // Handler functions that integrate with JupyterLab services
        const handleToggleCollapse = () => {
          isCollapsed = !isCollapsed;
          if (isCollapsed) {
            ctaContainer.classList.add('collapsed');
            localStorage.setItem(CTA_COLLAPSED_KEY, 'true');
          } else {
            ctaContainer.classList.remove('collapsed');
            localStorage.setItem(CTA_COLLAPSED_KEY, 'false');
          }
          // Re-render with new state
          renderCTA();
        };

        const handleSendMessage = (message: string) => {
          const chatContainer = getChatboxState().services?.chatContainer;
          if (chatContainer?.chatWidget) {
            chatContainer.chatWidget.setInputValue(message);
            void chatContainer.chatWidget.sendMessage();
            // Collapse the CTA after sending message
            isCollapsed = true;
            ctaContainer.classList.add('collapsed');
            localStorage.setItem(CTA_COLLAPSED_KEY, 'true');
            renderCTA();
            console.log('[WelcomeCTA] Message sent to chat:', message);
          } else {
            console.warn('[WelcomeCTA] Chat input manager not available');
          }
        };

        const handleFileUpload = () => {
          const fileExplorerWidget = getFileExplorerWidget();

          if (fileExplorerWidget) {
            // Create a hidden file input element
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.multiple = true;
            fileInput.accept = '.csv,.json,.xlsx,.xls,.parquet,.txt,.tsv';
            fileInput.style.display = 'none';

            fileInput.onchange = async (e: Event) => {
              const target = e.target as HTMLInputElement;
              if (target.files && target.files.length > 0) {
                try {
                  await fileExplorerWidget.handleFileUpload(target.files);
                  console.log('[WelcomeCTA] Files uploaded successfully');
                } catch (error) {
                  console.error('[WelcomeCTA] File upload failed:', error);
                }
              }
              document.body.removeChild(fileInput);
            };

            document.body.appendChild(fileInput);
            fileInput.click();
          } else {
            console.warn('[WelcomeCTA] File explorer widget not available');
            alert('File explorer is not available. Please try again later.');
          }
        };

        const handleDatabaseClick = (dbType: CTADatabaseType) => {
          const databaseManagerWidget = getDatabaseManagerWidget();

          if (databaseManagerWidget) {
            let databaseType: DatabaseType;
            switch (dbType) {
              case 'postgresql':
                databaseType = DatabaseType.PostgreSQL;
                break;
              case 'mysql':
                databaseType = DatabaseType.MySQL;
                break;
              case 'snowflake':
                databaseType = DatabaseType.Snowflake;
                break;
              default:
                databaseType = DatabaseType.PostgreSQL;
            }

            if (!databaseManagerWidget.isVisible) {
              databaseManagerWidget.show();
            }

            app.shell.activateById(databaseManagerWidget.id);

            const widget = databaseManagerWidget as any;
            if (widget.handleAddDatabase) {
              widget.handleAddDatabase(databaseType);
            }

            console.log(
              `[WelcomeCTA] Opening database connection modal for ${dbType}`
            );
          } else {
            console.warn('[WelcomeCTA] Database manager widget not available');
            alert('Database manager is not available. Please try again later.');
          }
        };

        // Create React root and render function
        const root = ReactDOM.createRoot(ctaContainer);

        const renderCTA = () => {
          root.render(
            React.createElement(WelcomeCTAContent, {
              isCollapsed,
              onToggleCollapse: handleToggleCollapse,
              onSendMessage: handleSendMessage,
              onFileUpload: handleFileUpload,
              onDatabaseClick: handleDatabaseClick
            })
          );
        };

        // Initial render
        renderCTA();

        // Find the jp-WindowedPanel-outer div inside the notebook panel
        const notebookPanelElement = currentNotebook.node.querySelector(
          '.jp-WindowedPanel.lm-Widget.jp-Notebook.jp-mod-scrollPastEnd.jp-mod-showHiddenCellsButton.jp-NotebookPanel-notebook'
        );

        const outerPanelElement = notebookPanelElement?.querySelector(
          '.jp-WindowedPanel-outer'
        ) as HTMLElement;

        if (outerPanelElement) {
          outerPanelElement.insertBefore(
            ctaContainer,
            outerPanelElement.firstChild
          );
          console.log(
            '[WelcomeCTA] Data CTA interface added to jp-WindowedPanel-outer'
          );
        } else {
          console.warn(
            '[WelcomeCTA] Could not find jp-WindowedPanel-outer, trying fallback'
          );
          const notebookElement =
            currentNotebook.node.querySelector('.jp-Notebook');
          if (notebookElement) {
            const fallbackOuter = notebookElement.querySelector(
              '.jp-WindowedPanel-outer'
            ) as HTMLElement;
            if (fallbackOuter) {
              fallbackOuter.insertBefore(
                ctaContainer,
                fallbackOuter.firstChild
              );
              console.log('[WelcomeCTA] Data CTA interface added via fallback');
            } else {
              currentNotebook.node.appendChild(ctaContainer);
              console.log(
                '[WelcomeCTA] Data CTA interface added to notebook panel (final fallback)'
              );
            }
          } else {
            currentNotebook.node.appendChild(ctaContainer);
            console.log(
              '[WelcomeCTA] Data CTA interface added to notebook panel (final fallback)'
            );
          }
        }
      } catch (error) {
        console.error('[WelcomeCTA] Failed to add CTA div:', error);
      }
    }
  });

  // Add this command to the command palette
  palette.addItem({ command: addCtaDivCommand, category: 'AI Tools' });
}
