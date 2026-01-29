/**
 * Context Utilities
 *
 * Helper functions for building context messages for LLM conversations.
 */

import { getCurrentWorkingDirectory, getSetupManager } from '@/stores/appStore';
import { useNotebookEventsStore } from '@/stores/notebookEventsStore';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';

/**
 * Build a context message from mention contexts for the LLM.
 * @param mentionContexts Map of context ID to mention context
 * @returns Formatted context message string
 */
export function buildContextMessage(
  mentionContexts: Map<string, IMentionContext>
): string {
  if (mentionContexts.size === 0) {
    return '';
  }

  let message = "The user's message has the following provided context:\n\n";

  for (const [_contextId, context] of mentionContexts.entries()) {
    message += `@${context.name} (ID: ${context.id}) described as: ${context.description} has the following content: \n${context.content}\n\n`;
  }

  return message.trim();
}

/**
 * Build a working directory context message for the LLM.
 * Includes Jupyter lab path, notebook path, and Python environment info.
 * @returns Formatted working directory message string
 */
export function buildWorkingDirectoryMessage(): string {
  const cwd = getCurrentWorkingDirectory();
  const notebookPath = useNotebookEventsStore.getState().getCurrentNotebook()
    ?.context.path;
  const setupManager = getSetupManager();

  const setupManagerInfo = setupManager
    ? `\nThe user's Python environment is managed with ${setupManager}. When installing packages, use ${setupManager === 'uv' ? 'uv pip install' : 'pip install'}.`
    : '';

  return `This is the jupyter lab path ${cwd}\nThe notebook path is ${notebookPath}${setupManagerInfo}`;
}
