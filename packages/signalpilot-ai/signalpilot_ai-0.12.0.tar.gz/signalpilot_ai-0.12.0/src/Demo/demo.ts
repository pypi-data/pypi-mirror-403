import { useNotebookEventsStore } from '../stores/notebookEventsStore';
import { useAppStore } from '../stores/appStore';
import {
  useChatboxStore,
  showHistoryWidget,
  detachChatboxFromLauncher
} from '../stores/chatboxStore';
import { getToolService, getNotebookTools } from '../stores/servicesStore';
import { ChatMessages } from '@/ChatBox/services/ChatMessagesService';
import { IChatMessage, IToolCall } from '../types';
import testHistory from './test_sp.json';
import { IChatThread } from '@/ChatBox/services/ChatHistoryManager';
import { v4 as uuidv4 } from 'uuid';
import {
  executeAllCells,
  handleEditPlan,
  isEditPlanTool,
  processDemoMessages
} from './demo_cell_actions';
import { JWTAuthModalService } from '../Services/JWTAuthModalService';
import { NotebookActions } from '@jupyterlab/notebook';
import { ReplayLoadingOverlayWidget } from '../Components/ReplayLoadingOverlay/ReplayLoadingOverlayWidget';
import {
  enableTakeoverMode,
  getStoredReplayId
} from '../utils/replayIdManager';
import { posthogService } from '../Services/PostHogService';
import { useWaitingReplyStore } from '../stores/waitingReplyStore';
import { useLLMStateStore } from '../stores/llmStateStore';
import { useChatMessagesStore } from '../stores/chatMessages';
import { useDemoOverlayStore } from '../stores/demoOverlayStore';
import { useDemoControlStore } from '../stores/demoControlStore';
import { useChatUIStore } from '../stores/chatUIStore';
import {
  addJupyterLabOverlays,
  removeJupyterLabOverlays
} from '../Jupyter/DemoOverlays';

/**
 * Demo message system that directly interacts with ChatMessages
 * to add and stream messages without using the API
 *
 * CELL STREAMING CONFIGURATION:
 * To adjust the speed of cell content generation, modify CELL_STREAMING_CONFIG below:
 * - baseDelay: Higher = slower generation (in milliseconds)
 * - minChunkSize/maxChunkSize: Control characters per chunk
 * - variationFactor: Controls randomness (0-1, higher = more variation)
 */

// Global flag to control streaming vs instant mode
let isSkipToResultMode = false;
let isDemoAborted = false; // Flag to abort ongoing demo
let hasHiddenLoadingOverlay = false; // Track if we've already hidden the loading overlay
let isDemoActivelyRunning = false; // Track if demo is currently running
let appInstance: any = null; // Store app instance for activating chat panel

/**
 * Check if the demo is currently actively running
 * Used by UI components to disable interactions during demo playback
 */
export function getIsDemoActivelyRunning(): boolean {
  return isDemoActivelyRunning;
}

/**
 * Hide and disable all UI components during demo mode
 *
 * Uses Zustand store to trigger React component overlays,
 * and direct DOM manipulation for JupyterLab elements.
 */
export function hide_all_components(): void {
  console.log('[Demo] Hiding and disabling UI components');

  // Hide the LLM state widget - it's mutually exclusive with demo controls
  useLLMStateStore.getState().hide();

  // Activate React overlays via Zustand store
  // This triggers re-renders in components that subscribe to the store:
  // - ChatToolbar (renders DemoOverlay)
  // - ChatInputContainer/chatbox-wrapper (renders DemoOverlay)
  // - SendButton (shows spinner)
  useDemoOverlayStore.getState().activate();

  // Add overlays to JupyterLab (non-React) elements via DOM manipulation
  addJupyterLabOverlays();
}

/**
 * Show and re-enable all UI components after demo mode
 */
export function show_all_components(): void {
  console.log('[Demo] Showing and re-enabling UI components');

  // Deactivate React overlays via Zustand store
  useDemoOverlayStore.getState().deactivate();

  // Remove JupyterLab overlays
  removeJupyterLabOverlays();
}

export interface IDemoTextBlock {
  type: 'text';
  text: string;
}

export interface IDemoToolUseBlock {
  type: 'tool_use';
  id: string;
  name: string;
  input: any;
  result?: string; // Optional tool result content
}

export type DemoContentBlock = IDemoTextBlock | IDemoToolUseBlock;

export interface IDemoMessage {
  role: 'user' | 'assistant';
  content: string | DemoContentBlock[];
}

/**
 * Check if the chat history container is properly rendered
 */
function isChatHistoryContainerRendered(): boolean {
  const historyContainer = document.querySelector('.sage-ai-history-container');
  if (!historyContainer || !(historyContainer instanceof HTMLElement)) {
    console.warn('[Demo] Chat history container not found');
    return false;
  }

  const chatHistory = historyContainer.querySelector('.sage-ai-chat-history');
  if (!chatHistory || !(chatHistory instanceof HTMLElement)) {
    console.warn('[Demo] Chat history element not found inside container');
    return false;
  }

  // Check if the container is visible (display is not 'none')
  const containerStyle = window.getComputedStyle(historyContainer);
  if (containerStyle.display === 'none') {
    console.warn('[Demo] Chat history container display is none');
    return false;
  }

  // Check if the new chat display is shown (it should be hidden during replay)
  const newChatDisplay = document.querySelector('.sage-ai-new-chat-display');
  if (newChatDisplay instanceof HTMLElement) {
    const newChatStyle = window.getComputedStyle(newChatDisplay);
    if (newChatStyle.display !== 'none') {
      console.warn(
        '[Demo] New chat display is visible (should be hidden during replay)'
      );
      return false;
    }
  }

  return true;
}

/**
 * Ensure the chat UI is properly set up for demo
 * This handles cases where the chat might have been attached to the launcher
 * NOTE: We intentionally DON'T call loadFromThread() as it causes jarring re-renders
 */
async function ensureChatHistoryRendered(
  _demoMessages: IDemoMessage[],
  _currentMessageIndex: number
): Promise<void> {
  console.log('[Demo] Checking if chat history container is rendered...');

  if (isChatHistoryContainerRendered()) {
    console.log('[Demo] Chat history container is properly rendered');
    return;
  }

  console.warn(
    '[Demo] Chat history container is NOT rendered - ensuring proper UI state...'
  );

  const currentNotebookId = useNotebookEventsStore.getState().currentNotebookId;

  if (!currentNotebookId) {
    console.warn('[Demo] No notebook open, cannot set up chat');
    return;
  }

  // CRITICAL: Destroy any launcher-attached chat first
  const isLauncherActive = useAppStore.getState().isLauncherActive;
  if (isLauncherActive) {
    console.log(
      '[Demo] Launcher is active - disabling launcher mode and detaching from launcher'
    );
    useAppStore.getState().setLauncherActive(false);

    // Detach chatbox from launcher using the store
    detachChatboxFromLauncher();
    console.log('[Demo] Chatbox detached from launcher');
  }

  // Force show the history widget (this will hide new chat display and show history)
  // The React components will automatically render based on store state
  showHistoryWidget();
  console.log('[Demo] Called showHistoryWidget to ensure proper display state');

  // NOTE: We don't call loadFromThread() here anymore as it causes jarring re-renders
  // The messages are already being added to the store incrementally, and React will
  // automatically render them. The store state is the source of truth.

  console.log('[Demo] Chat UI state ensured for demo');
}

/**
 * Send a demo message directly to the chat interface
 * This bypasses the API and directly manipulates the ChatMessages component
 */
export async function sendDemoMessage(
  chatMessages: ChatMessages,
  message: IDemoMessage,
  streamingDelay: number = 20,
  nextMessage?: IDemoMessage,
  loadingOverlay?: ReplayLoadingOverlayWidget | null,
  demoMessages?: IDemoMessage[],
  currentMessageIndex?: number
): Promise<void> {
  // CRITICAL: Ensure the chat is ALWAYS attached to the sidebar, not the launcher
  // This must happen before every message to prevent it from staying in the launcher
  if (useChatboxStore.getState().isAttachedToLauncher()) {
    console.log('[Demo] Chat is in launcher - detaching and moving to sidebar');

    // Disable launcher mode
    useAppStore.getState().setLauncherActive(false);

    // Detach from launcher using the store
    detachChatboxFromLauncher();
    console.log('[Demo] Chat detached from launcher');
  }

  // Force show the history widget (hides new chat display, shows chat history)
  showHistoryWidget();
  console.log('[Demo] Ensured chat history widget is visible');

  // Activate the chat side panel to ensure it's open and visible (if app instance is available)
  if (appInstance && appInstance.shell) {
    try {
      appInstance.shell.activateById('sage-ai-chat-container');
      console.log('[Demo] Activated chat side panel');
    } catch (error) {
      console.warn('[Demo] Could not activate chat side panel:', error);
    }
  }

  // Check if chat history container is properly rendered
  // If not, re-initialize it with the chat history up to this point
  if (demoMessages && currentMessageIndex !== undefined) {
    await ensureChatHistoryRendered(demoMessages, currentMessageIndex);
  }

  if (message.role === 'user') {
    // Add user message directly
    await addDemoUserMessage(
      chatMessages,
      message.content as string,
      loadingOverlay
    );
  } else if (message.role === 'assistant') {
    // Stream assistant message
    await streamDemoAssistantMessage(
      chatMessages,
      message.content,
      streamingDelay,
      nextMessage
    );
  }
}

/**
 * Add a user message to the chat (demo mode)
 */
async function addDemoUserMessage(
  chatMessages: ChatMessages,
  content: string,
  loadingOverlay?: ReplayLoadingOverlayWidget | null
): Promise<void> {
  // Hide the loading overlay when the first user message is sent
  if (!hasHiddenLoadingOverlay && loadingOverlay) {
    console.log(
      '[Demo] Hiding loading overlay with fade-out - first user message sent'
    );
    loadingOverlay.hide(); // This now triggers fade-out animation
    hasHiddenLoadingOverlay = true;

    // Remove the overlay from DOM after fade animation completes
    setTimeout(() => {
      if (loadingOverlay && loadingOverlay.node.parentNode) {
        loadingOverlay.node.parentNode.removeChild(loadingOverlay.node);
      }
    }, 700); // Slightly longer than fade-out duration (600ms)
  }

  // Hide the waiting reply container since the user "responded"
  // This handles the case where wait_user_reply tool was called and now the demo
  // is replaying the user's recorded response
  useWaitingReplyStore.getState().hide();

  // Add the user message directly to the UI without saving to history
  chatMessages.addUserMessage(content, false, true); // is_demo = true

  // Small delay to simulate user input
  await delay(300);
}

/**
 * Stream an assistant message to the chat (demo mode)
 */
async function streamDemoAssistantMessage(
  chatMessages: ChatMessages,
  content: string | DemoContentBlock[],
  streamingDelay: number,
  nextMessage?: IDemoMessage
): Promise<void> {
  // Handle text content
  if (typeof content === 'string') {
    await streamDemoText(chatMessages, content, streamingDelay);
    return;
  }

  // Handle content blocks (text and tool calls)
  if (Array.isArray(content)) {
    for (const block of content) {
      if (block.type === 'text') {
        await streamDemoText(chatMessages, block.text, streamingDelay);
      } else if (block.type === 'tool_use') {
        // The tool result is now attached to the tool_use block
        await streamDemoToolUse(chatMessages, block, block.result);
      }
    }
  }
}

/**
 * Stream text content character by character
 * In skip mode, this will instantly show the full text
 */
async function streamDemoText(
  chatMessages: ChatMessages,
  text: string,
  streamingDelay: number
): Promise<void> {
  // Check if demo was aborted
  if (isDemoAborted) {
    console.log('[Demo] Aborting text streaming - demo was stopped');
    return;
  }

  // Create streaming message via store
  chatMessages.addStreamingAIMessage();

  if (isSkipToResultMode) {
    // In skip mode, add all text at once
    await chatMessages.updateStreamingMessage(text);
    await chatMessages.finalizeStreamingMessage(true);
    return;
  }

  // Normal streaming mode: Stream the text in chunks
  const chunkSize = 3; // Characters per chunk
  for (let i = 0; i < text.length; i += chunkSize) {
    // Check if demo was aborted
    if (isDemoAborted) {
      console.log('[Demo] Aborting text streaming mid-stream');
      return;
    }

    const chunk = text.slice(i, i + chunkSize);
    await chatMessages.updateStreamingMessage(chunk);
    await delay(streamingDelay);
  }

  // Finalize the streaming message (is_demo = true)
  await chatMessages.finalizeStreamingMessage(true);
}

/**
 * Configuration for cell streaming effect
 */
export const CELL_STREAMING_CONFIG = {
  // Base delay between chunks in milliseconds (adjust this to speed up/slow down)
  baseDelay: 10,
  // Minimum chunk size in characters
  minChunkSize: 4,
  // Maximum chunk size in characters
  maxChunkSize: 10,
  // Variation factor (0-1, higher = more variation)
  variationFactor: 0.3
};

/**
 * Generate random chunk size with natural variation
 */
function getRandomChunkSize(): number {
  const { minChunkSize, maxChunkSize, variationFactor } = CELL_STREAMING_CONFIG;
  const range = maxChunkSize - minChunkSize;
  const baseSize = minChunkSize + Math.floor(Math.random() * range);
  const variation = Math.floor(
    (Math.random() - 0.5) * 2 * variationFactor * range
  );
  return Math.max(minChunkSize, Math.min(maxChunkSize, baseSize + variation));
}

/**
 * Stream cell content with LLM-like generation effect
 * In skip mode, this will instantly set the full content
 */
async function streamCellContent(
  toolService: any,
  cellId: string,
  fullContent: string,
  summary: string,
  notebookPath: string,
  isAddCell: boolean = false
): Promise<void> {
  // Check if demo was aborted
  if (isDemoAborted) {
    console.log('[Demo] Aborting cell streaming - demo was stopped');
    return;
  }

  // In skip mode, just set the full content immediately
  if (isSkipToResultMode) {
    if (isAddCell) {
      toolService.notebookTools?.edit_cell({
        cell_id: cellId,
        new_source: fullContent,
        summary: summary,
        is_tracking_id: true,
        notebook_path: notebookPath
      });
    } else {
      toolService.notebookTools?.edit_cell({
        cell_id: cellId,
        new_source: fullContent,
        summary: summary,
        is_tracking_id: cellId.startsWith('cell_'),
        notebook_path: notebookPath
      });
    }
    return;
  }

  // Normal streaming mode
  let currentContent = '';
  let position = 0;

  while (position < fullContent.length) {
    // Check if demo was aborted
    if (isDemoAborted) {
      console.log('[Demo] Aborting cell streaming mid-stream');
      return;
    }

    // Get random chunk size for natural variation
    const chunkSize = getRandomChunkSize();
    const chunk = fullContent.slice(position, position + chunkSize);
    currentContent += chunk;
    position += chunkSize;

    // Update the cell with accumulated content
    if (isAddCell) {
      // For add_cell, we need to use edit_cell to update existing cell
      toolService.notebookTools?.edit_cell({
        cell_id: cellId,
        new_source: currentContent,
        summary: summary,
        is_tracking_id: true,
        notebook_path: notebookPath
      });
    } else {
      // For edit_cell, just update normally
      toolService.notebookTools?.edit_cell({
        cell_id: cellId,
        new_source: currentContent,
        summary: summary,
        is_tracking_id: cellId.startsWith('cell_'),
        notebook_path: notebookPath
      });
    }

    // Wait before next chunk with slight random variation
    const delayVariation =
      (Math.random() - 0.5) * CELL_STREAMING_CONFIG.baseDelay * 0.2;
    await delay(CELL_STREAMING_CONFIG.baseDelay + delayVariation);
  }
}

/**
 * Stream a tool use (show tool call and execute it using ToolService)
 */
async function streamDemoToolUse(
  chatMessages: ChatMessages,
  toolUse: IDemoToolUseBlock,
  toolResultContent?: string
): Promise<void> {
  // Check if demo was aborted
  if (isDemoAborted) {
    console.log('[Demo] Aborting tool use - demo was stopped');
    return;
  }

  // Skip wait_user_reply tool entirely during demo - don't even show it in UI
  // The next user message in the demo sequence will show the user's response
  if (toolUse.name === 'notebook-wait_user_reply') {
    console.log(
      '[Demo] Skipping wait_user_reply tool entirely - demo will show recorded user response'
    );
    // Hide the waiting reply box in case it was triggered by something else
    useWaitingReplyStore.getState().hide();
    return;
  }

  // Create the tool call
  const toolCall: IToolCall = {
    id: toolUse.id,
    name: toolUse.name,
    input: toolUse.input
  };

  console.log(
    '[Demo] Streaming tool use:',
    toolUse.name,
    toolUse.id,
    toolUse,
    toolResultContent
  );

  // Check if this is an edit_plan tool - handle it specially
  if (isEditPlanTool(toolUse.name) && toolResultContent) {
    // Add streaming tool call via store
    chatMessages.addStreamingToolCall(toolUse.id, toolUse.name);

    // Small delay to simulate thinking
    await delay(300);

    // Check abort again
    if (isDemoAborted) {
      return;
    }

    // Update the streaming tool call
    chatMessages.updateStreamingToolCall(toolUse.id, toolCall);

    // Wait a bit to simulate tool execution starting
    await delay(500);

    // Check abort again
    if (isDemoAborted) {
      return;
    }

    // Finalize the tool call (is_demo = true)
    chatMessages.finalizeStreamingToolCall(toolUse.id, true);

    // Execute the optimized edit_plan handler
    await delay(200);

    // Check abort again
    if (isDemoAborted) {
      return;
    }

    try {
      await handleEditPlan(toolUse, toolResultContent, chatMessages);

      // Add tool result to UI
      chatMessages.addToolResult(
        toolUse.name,
        toolUse.id,
        toolResultContent,
        {
          assistant: {
            content: [toolUse]
          }
        },
        true
      ); // is_demo = true

      const toolService = getToolService();

      if (toolService.notebookTools) {
        await delay(100); // Small delay before running
        const planCell = toolService.notebookTools.getPlanCell();
        const nb = toolService.notebookTools.getCurrentNotebook();
        if (planCell && nb) {
          await NotebookActions.runCells(
            nb.notebook,
            [planCell],
            nb.widget?.sessionContext
          );
        }
      }
    } catch (error) {
      console.error('Error executing edit_plan:', error);
      const errorContent = `Error: ${error instanceof Error ? error.message : String(error)}`;
      chatMessages.addToolResult(
        toolUse.name,
        toolUse.id,
        errorContent,
        {
          assistant: {
            content: [toolUse]
          }
        },
        true
      ); // is_demo = true
    }
    return;
  }

  // Add streaming tool call via store
  chatMessages.addStreamingToolCall(toolUse.id, toolUse.name);

  // Small delay to simulate thinking
  await delay(300);

  // Check abort again
  if (isDemoAborted) {
    return;
  }

  // Update the streaming tool call
  chatMessages.updateStreamingToolCall(toolUse.id, toolCall);

  // Wait a bit to simulate tool execution starting
  await delay(500);

  // Check abort again
  if (isDemoAborted) {
    return;
  }

  // Finalize the tool call (is_demo = true)
  chatMessages.finalizeStreamingToolCall(toolUse.id, true);

  // Check if this is an add_cell or edit_cell operation
  const isAddCell = toolUse.name === 'notebook-add_cell';
  const isEditCell = toolUse.name === 'notebook-edit_cell';
  const isRunCell = toolUse.name === 'notebook-run_cell';

  // In skip mode, skip run_cell operations (they'll be executed all at once at the end)
  if (isRunCell && isSkipToResultMode) {
    console.log('[Demo] Skip mode: Skipping run_cell, will execute all at end');
    chatMessages.addToolResult(
      toolUse.name,
      toolUse.id,
      'Cell execution skipped - will run all cells at end',
      {
        assistant: {
          content: [toolUse]
        }
      },
      true
    );
    return;
  }

  // Execute the tool using ToolService
  await delay(200);

  // Check abort again
  if (isDemoAborted) {
    return;
  }

  let resultContent: string;

  try {
    const toolService = getToolService();
    const notebookPath =
      toolUse.input.notebook_path ||
      useNotebookEventsStore.getState().getCurrentNotebook()?.context.path;
    // Handle cell operations with streaming effect
    if (isAddCell && toolUse.input.source) {
      // First, create the cell with empty content
      const cellId = toolService.notebookTools?.add_cell({
        cell_type: toolUse.input.cell_type || 'code',
        summary: toolUse.input.summary || 'Creating cell...',
        source: '', // Start with empty content
        notebook_path: notebookPath,
        position: toolUse.input.position
      });

      if (cellId) {
        // Now stream the content into the cell
        await streamCellContent(
          toolService,
          cellId,
          toolUse.input.source,
          toolUse.input.summary || 'Creating cell...',
          notebookPath,
          true // isAddCell
        );

        // Check abort before running markdown cell
        if (isDemoAborted) {
          return;
        }

        // If it's a markdown cell, run it to render the content
        const isMarkdown = toolUse.input.cell_type === 'markdown';
        const nb = toolService.notebookTools?.getCurrentNotebook();
        const { cell } =
          toolService.notebookTools?.findCellByAnyId(cellId) || {};
        if (isMarkdown && nb && cell) {
          await delay(100); // Small delay before running
          await NotebookActions.runCells(
            nb.notebook,
            [cell],
            nb.widget?.sessionContext
          );
        }

        resultContent = cellId;
      } else {
        throw new Error('Failed to create cell');
      }
    } else if (isEditCell && toolUse.input.new_source) {
      // For edit_cell, stream the new content
      await streamCellContent(
        toolService,
        toolUse.input.cell_id,
        toolUse.input.new_source,
        toolUse.input.summary || 'Editing cell...',
        notebookPath,
        false // not isAddCell
      );

      // Check abort before running markdown cell
      if (isDemoAborted) {
        return;
      }

      // If it's a markdown cell, run it to render the content
      const isMarkdown = toolUse.input.cell_type === 'markdown';
      const nb = toolService.notebookTools?.getCurrentNotebook();
      const { cell } =
        toolService.notebookTools?.findCellByAnyId(toolUse.input.cell_id) || {};
      if (isMarkdown && nb && cell) {
        await delay(100); // Small delay before running
        await NotebookActions.runCells(
          nb.notebook,
          [cell],
          nb.widget?.sessionContext
        );
      }

      resultContent = 'true';
    } else {
      // Execute other tools normally
      const result = await toolService.executeTool(toolCall);

      // Extract the content from the tool result
      if (result && result.content) {
        if (typeof result.content === 'string') {
          resultContent = result.content;
        } else if (Array.isArray(result.content)) {
          // Handle array of content blocks
          resultContent = result.content
            .map((item: any) => item.text || JSON.stringify(item))
            .join('\n');
        } else {
          resultContent = JSON.stringify(result.content);
        }
      } else {
        resultContent = JSON.stringify(result);
      }
    }
  } catch (error) {
    console.error(`Error executing tool ${toolUse.name}:`, error);
    resultContent = `Error: ${error instanceof Error ? error.message : String(error)}`;
  }

  // Check abort before adding tool result
  if (isDemoAborted) {
    return;
  }

  chatMessages.addToolResult(
    toolUse.name,
    toolUse.id,
    resultContent,
    {
      assistant: {
        content: [toolUse]
      }
    },
    true
  ); // is_demo = true
}

/**
 * Run a complete demo sequence
 * @param messages Demo messages to run
 * @param streamingDelay Delay between streaming chunks (ignored in skip mode)
 * @param showControlPanel Whether to show the control panel (default: true)
 * @param originalThreadData Optional original thread data from API (for proper history restoration)
 * @param loadingOverlay Optional loading overlay widget to hide when first message is sent
 */
export async function runDemoSequence(
  messages: IDemoMessage[],
  streamingDelay: number = 20,
  showControlPanel: boolean = true,
  originalThreadData?: any,
  loadingOverlay?: ReplayLoadingOverlayWidget | null,
  app?: any
): Promise<void> {
  // Get services from the chatbox store
  const { services, isFullyInitialized } = useChatboxStore.getState();
  const chatMessages = services.messageComponent;
  const chatHistoryManager = services.chatHistoryManager;

  if (!isFullyInitialized || !chatMessages || !chatHistoryManager) {
    console.error('[Demo] Chat services not available');
    throw new Error('Chat services not available');
  }

  // Store the app instance globally so it can be used in sendDemoMessage
  appInstance = app;
  console.log('[Demo] Stored app instance for chat panel activation');

  // Collapse left sidebar if it's expanded (only if app is provided)
  if (app && app.commands) {
    try {
      if (app.commands.isToggled('application:toggle-left-area')) {
        await app.commands.execute('application:toggle-left-area');
        console.log('[Demo] Collapsed left sidebar for demo mode');
      }
    } catch (error) {
      console.warn('[Demo] Could not collapse left sidebar:', error);
    }
  }

  chatMessages.scrollToBottom();

  // Reset skip mode and abort flag
  isSkipToResultMode = false;
  isDemoAborted = false;
  hasHiddenLoadingOverlay = false; // Reset overlay hidden flag

  // Store the messages and original thread data for later use
  const demoMessages = messages;
  let demoStarted = false;
  let newThread: any = null;
  const storedOriginalThreadData = originalThreadData;
  const storedLoadingOverlay = loadingOverlay;

  const startDemo = async (skipMode: boolean = false) => {
    if (demoStarted) {
      return;
    }
    demoStarted = true;
    isDemoActivelyRunning = true; // Mark demo as actively running

    isSkipToResultMode = skipMode;

    console.log(
      `[Demo] Starting demo in ${skipMode ? 'SKIP' : 'INTERACTIVE'} mode`
    );

    // CRITICAL: Cancel any ongoing LLM request (e.g., welcome message)
    // This prevents the welcome message from running in parallel with the demo
    console.log('[Demo] Cancelling any ongoing LLM requests');
    useChatboxStore.getState().cancelMessage();

    // Clear all chat messages to start fresh
    console.log('[Demo] Clearing chat messages');
    useChatMessagesStore.getState().clearMessages();

    // Hide the new chat display when demo starts
    useChatUIStore.getState().setShowNewChatDisplay(false);

    // Capture the load time
    posthogService.captureTimeToBeginDemo();

    // Create a new thread for tracking purposes (but don't load it - that causes re-renders)
    newThread = chatHistoryManager.createNewThread('Temporary Demo Thread');
    if (!newThread) {
      console.error('[Demo] Failed to create new thread');
      throw new Error('Failed to create new thread');
    }

    // Clear messages directly using the store - this is much smoother than loadFromThread()
    // which causes full state resets and re-renders
    useChatMessagesStore.getState().clearMessages();
    useChatMessagesStore.getState().setCurrentThreadId(newThread.id);

    console.log(
      '[Demo] Created temporary thread and cleared chat messages:',
      newThread.id
    );

    // Hide all UI components during demo
    hide_all_components();

    // Process messages for skip mode if needed
    let processedMessages = skipMode
      ? processDemoMessages(demoMessages, true)
      : demoMessages;

    console.log(
      `[Demo] Using ${processedMessages.length} messages (${skipMode ? 'filtered' : 'original'})`
    );

    // Show demo indicator
    chatMessages.addSystemMessage(
      isSkipToResultMode
        ? '⚡ Demo Mode: Fast-forwarding to result...'
        : '🎬 Demo Mode: Interactive demonstration'
    );

    // Send each message in sequence
    for (let i = 0; i < processedMessages.length; i++) {
      // Check if demo was aborted
      if (isDemoAborted) {
        console.log('[Demo] Demo aborted, stopping message sequence');
        chatMessages.addSystemMessage('⚠️ Demo stopped');
        break;
      }

      const message = processedMessages[i];
      const nextMessage =
        i < processedMessages.length - 1 ? processedMessages[i + 1] : undefined;
      console.log(
        `[Demo] Sending message ${i + 1}/${processedMessages.length}`
      );

      await sendDemoMessage(
        chatMessages,
        message,
        streamingDelay,
        nextMessage,
        storedLoadingOverlay,
        processedMessages,
        i
      );

      // Add a pause between messages (shorter in skip mode)
      if (i < processedMessages.length - 1) {
        await delay(isSkipToResultMode ? 100 : 1000);
      }
    }

    // Only proceed with completion if not aborted
    if (!isDemoAborted) {
      // If in skip mode, execute all cells at the end
      if (isSkipToResultMode) {
        console.log('[Demo] Skip mode: Executing all cells now');
        await delay(500);
        await executeAllCells();
      }

      // Hide the waiting reply container since demo is complete
      // This handles the case where the demo ends with a wait_user_reply tool call
      useWaitingReplyStore.getState().hide();

      // Show completion message
      chatMessages.addSystemMessage('✅ Demo completed!');

      console.log('[Demo] Demo sequence completed');

      // Show all UI components again
      show_all_components();

      // Mark demo as finished and update button text
      useDemoControlStore.getState().markDemoFinished();
      // Check if user is authenticated and hide panel if needed
      void updateDemoControlPanelVisibility();

      // TEMPORARILY DISABLED: Delete the temporary thread and create a new thread with the demo messages
      // This was causing React DOM errors due to message mismatch between displayed messages and original thread
      // await replaceTempThreadWithDemoThread(
      //   newThread.id,
      //   storedOriginalThreadData
      // );

      // Save the notebook after demo completes
      try {
        const currentNotebook = useNotebookEventsStore
          .getState()
          .getCurrentNotebook();
        if (currentNotebook) {
          await currentNotebook.context.save();
          console.log(
            '[Demo] Notebook saved successfully after demo completion'
          );
        } else {
          console.warn('[Demo] No current notebook found to save');
        }
      } catch (saveError) {
        console.error('[Demo] Error saving notebook:', saveError);
      }
    } else {
      console.log('[Demo] Demo was aborted, skipping completion steps');
      // Still show UI components even if aborted
      show_all_components();
    }

    // Mark demo as no longer actively running
    isDemoActivelyRunning = false;
  };

  const handleSkipToResult = async () => {
    console.log('[Demo] Skip to result clicked - switching to instant mode');

    // Mark demo as finished since user clicked Results
    useDemoControlStore.getState().markDemoFinished();
    // Check if user is authenticated and hide panel if needed
    void updateDemoControlPanelVisibility();

    // Set the flag to skip mode immediately
    isSkipToResultMode = true;

    // If demo hasn't started yet, start in skip mode
    if (!demoStarted) {
      await startDemo(true);
    } else {
      // Demo is already running - the flag change will affect ongoing operations
      console.log(
        '[Demo] Demo already running - switching to instant mode for remaining operations'
      );

      // Add a system message to indicate the mode change
      chatMessages.addSystemMessage('⚡ Fast-forwarding to result...');

      // Note: We'll execute all cells at the end when the demo completes
    }
  };

  if (showControlPanel) {
    // Show the control panel with callbacks
    showDemoControlPanel(
      async () => {
        // Try it yourself - create notebook and send first message
        hideDemoControlPanel();
        await tryItYourself(demoMessages);
      },
      handleSkipToResult // Skip to result
    );
  }
  await startDemo(false);
}

/**
 * Create a sample demo sequence from test_history.json
 * Returns both the demo messages and the original thread data
 */
export function createSampleDemoSequence(): {
  messages: IDemoMessage[];
  originalThreadData: any;
} {
  // Load the test history (should be an array with thread objects)
  if (!testHistory || testHistory.length === 0) {
    console.error('[Demo] No test history available');
    return { messages: [], originalThreadData: null };
  }

  // Get the first thread's messages
  const thread = testHistory[0];
  if (!thread || !thread.messages) {
    console.error('[Demo] Invalid thread structure');
    return { messages: [], originalThreadData: null };
  }

  const demoMessages: IDemoMessage[] = [];

  // Create a map of tool_use_id to tool_result content for easy lookup
  const toolResultMap = new Map<string, string>();

  // First pass: collect all tool results
  for (const message of thread.messages) {
    if (message.role === 'user' && Array.isArray(message.content)) {
      for (const block of message.content) {
        if (
          block.type === 'tool_result' &&
          'tool_use_id' in block &&
          'content' in block
        ) {
          toolResultMap.set(block.tool_use_id, block.content);
        }
      }
    }
  }

  // Convert each message to demo format
  for (const message of thread.messages) {
    // Skip tool_result messages (they're attached to tool_use blocks now)
    if (message.role === 'user' && Array.isArray(message.content)) {
      const hasToolResult = message.content.some(
        (block: any) => block.type === 'tool_result'
      );
      if (hasToolResult) {
        continue; // Skip tool results - they'll be accessed from toolResultMap
      }
    }

    // Skip diff_approval messages (these are internal)
    if (message.role === 'diff_approval') {
      continue;
    }

    // Convert message content to demo format
    let demoContent: string | DemoContentBlock[];

    if (typeof message.content === 'string') {
      demoContent = message.content;
    } else if (Array.isArray(message.content)) {
      // Filter and convert content blocks
      const contentArray = message.content as any[];
      const blocks: (DemoContentBlock | null)[] = contentArray
        .filter(
          (block: any) => block.type === 'text' || block.type === 'tool_use'
        )
        .map((block: any): DemoContentBlock | null => {
          if (block.type === 'text') {
            return {
              type: 'text' as const,
              text: block.text
            };
          } else if (block.type === 'tool_use') {
            // Attach the tool result content to the tool_use block
            const toolResult = toolResultMap.get(block.id);
            return {
              type: 'tool_use' as const,
              id: block.id,
              name: block.name,
              input: block.input,
              result: toolResult // Add the result to the block
            };
          }
          return null;
        });

      demoContent = blocks.filter(
        (block): block is DemoContentBlock => block !== null
      );
    } else {
      // Skip messages with unknown content format
      continue;
    }

    // Create demo message
    const demoMessage: IDemoMessage = {
      role: message.role as 'user' | 'assistant',
      content: demoContent
    };

    demoMessages.push(demoMessage);
  }

  return { messages: demoMessages, originalThreadData: testHistory };
}

/**
 * Utility function to delay execution
 * When in skip mode, returns immediately
 */
function delay(ms: number): Promise<void> {
  if (isSkipToResultMode) {
    return Promise.resolve();
  }
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Helper function to get ChatMessages instance from the store
 */
export function getChatMessages(): ChatMessages | null {
  return useChatboxStore.getState().services.messageComponent || null;
}

/**
 * Create a new thread from demo messages and switch to it
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
async function createThreadFromDemo(
  demoMessages: IDemoMessage[]
): Promise<void> {
  // Get services from the chatbox store
  const { services } = useChatboxStore.getState();
  const chatHistoryManager = services.chatHistoryManager;
  const chatMessages = services.messageComponent;

  if (!chatHistoryManager || !chatMessages) {
    console.error('[Demo] Chat services not available for thread creation');
    return;
  }

  const currentNotebookId = useNotebookEventsStore.getState().currentNotebookId;

  if (!currentNotebookId) {
    console.warn('[Demo] No notebook open, cannot create thread');
    return;
  }

  // Convert demo messages to IChatMessage format
  const threadMessages: IChatMessage[] = [];

  for (const demoMsg of demoMessages) {
    const message: IChatMessage = {
      id: uuidv4(),
      role: demoMsg.role,
      content: demoMsg.content as any
    };
    threadMessages.push(message);
  }

  // Create a new thread with these messages
  const newThread: IChatThread = {
    id: chatHistoryManager['generateThreadId'](),
    name: 'Demo: S&P 500 Analysis',
    messages: threadMessages,
    lastUpdated: Date.now(),
    contexts: new Map(),
    message_timestamps: new Map(),
    continueButtonShown: false
  };

  // Add the thread to the notebook
  const threads =
    chatHistoryManager['notebookChats'].get(currentNotebookId) || [];
  threads.unshift(newThread); // Add at the beginning
  chatHistoryManager['notebookChats'].set(currentNotebookId, threads);

  // Save to storage
  await chatHistoryManager['saveNotebookToStorage'](currentNotebookId);

  // Switch to the new thread
  chatHistoryManager['currentThreadId'] = newThread.id;
  await chatHistoryManager['storeCurrentThreadInLocalStorage'](
    currentNotebookId,
    newThread.id
  );

  // Update the store's thread ID directly instead of calling loadFromThread()
  // This prevents jarring re-renders
  useChatMessagesStore.getState().setCurrentThreadId(newThread.id);

  // Thread name display is now handled by React ChatToolbar component

  console.log('[Demo] Created and switched to new thread:', newThread.id);
}

/**
 * Replace temporary thread with a new thread using the original chat history from the endpoint/JSON
 * @param tempThreadId The temporary thread ID to replace
 * @param originalThreadData The original thread data from the API or JSON file
 */
async function replaceTempThreadWithDemoThread(
  tempThreadId: string,
  originalThreadData: any
): Promise<void> {
  // Get services from the chatbox store
  const { services } = useChatboxStore.getState();
  const chatHistoryManager = services.chatHistoryManager;
  const chatMessages = services.messageComponent;

  if (!chatHistoryManager || !chatMessages) {
    console.error('[Demo] Chat services not available for thread replacement');
    return;
  }

  const currentNotebookId = useNotebookEventsStore.getState().currentNotebookId;

  if (!currentNotebookId) {
    console.warn('[Demo] No notebook open, cannot replace thread');
    return;
  }

  // Get existing threads
  const threads =
    chatHistoryManager['notebookChats'].get(currentNotebookId) || [];

  // Remove the temporary thread
  const filteredThreads = threads.filter((t: any) => t.id !== tempThreadId);

  // Use the original thread data from the endpoint/JSON
  if (!originalThreadData) {
    console.error('[Demo] No original thread data available');
    return;
  }

  // Support both array format (like test_sp.json) and direct thread object
  let originalThread = originalThreadData;
  if (Array.isArray(originalThreadData) && originalThreadData.length > 0) {
    originalThread = originalThreadData[0];
  }

  if (!originalThread || !originalThread.messages) {
    console.error('[Demo] Invalid thread structure in original data');
    return;
  }

  // Generate thread name from first user message (same logic as ThreadManager)
  let threadName = 'Demo Chat';
  const firstUserMessage = originalThread.messages.find(
    (msg: any) => msg.role === 'user' && typeof msg.content === 'string'
  );

  if (firstUserMessage && typeof firstUserMessage.content === 'string') {
    // Use the same paraphrasing logic as ThreadManager
    const words = firstUserMessage.content.split(/\s+/);
    const selectedWords = words.slice(0, Math.min(8, words.length));
    threadName = selectedWords.join(' ');

    // Truncate if too long
    if (threadName.length > 30) {
      threadName = threadName.substring(0, 27) + '...';
    }
  }

  // Create a new thread using the original messages from the endpoint/JSON
  const newThread: IChatThread = {
    id: chatHistoryManager['generateThreadId'](),
    name: threadName,
    messages: originalThread.messages,
    lastUpdated: Date.now(),
    contexts: new Map(),
    message_timestamps: new Map(),
    continueButtonShown: false
  };

  // Add the new thread at the beginning
  filteredThreads.unshift(newThread);
  chatHistoryManager['notebookChats'].set(currentNotebookId, filteredThreads);

  // Save to storage
  await chatHistoryManager['saveNotebookToStorage'](currentNotebookId);

  // Switch to the new thread ID in both the history manager and the store
  chatHistoryManager['currentThreadId'] = newThread.id;
  await chatHistoryManager['storeCurrentThreadInLocalStorage'](
    currentNotebookId,
    newThread.id
  );

  // Update the store's thread ID directly instead of calling loadFromThread()
  // This prevents the jarring re-render that causes the chatbox to disappear
  // The messages are already in the UI from the demo, we just need to sync the thread ID
  useChatMessagesStore.getState().setCurrentThreadId(newThread.id);

  // Also sync the llmHistory with the original thread messages for persistence
  // This ensures the chat history is properly saved when the user continues chatting
  const store = useChatMessagesStore.getState();
  const currentMessages = store.messages;

  // Only update llmHistory if we have messages (don't clear if demo was interrupted)
  if (currentMessages.length > 0) {
    // The llmHistory should already be populated from the demo, but we can sync with
    // the original thread messages for completeness
    console.log('[Demo] Thread ID updated, messages already in UI from demo');
  }

  // Thread name display is now handled by React ChatToolbar component

  console.log(
    '[Demo] Replaced temporary thread with original chat history:',
    newThread.id,
    'Name:',
    threadName
  );
}

/**
 * Show the demo control panel
 * Uses Zustand store to trigger React component rendering.
 * @param onTryIt Callback for when user clicks "Takeover"
 * @param onSkip Callback for when user clicks "Results"
 */
export function showDemoControlPanel(
  onTryIt: () => void,
  onSkip: () => void
): void {
  // Hide the LLM state widget when showing demo controls - they're mutually exclusive
  useLLMStateStore.getState().hide();

  // Show the demo control panel via Zustand store
  // This triggers the DemoControlPanel React component to render
  useDemoControlStore.getState().show(onTryIt, onSkip);
}

/**
 * Check if user is authenticated and hide demo panel if needed
 * This should be called after authentication state changes
 */
export async function updateDemoControlPanelVisibility(): Promise<void> {
  // Only hide if demo is not actively running
  const isDemoMode = useAppStore.getState().isDemoMode;
  const isVisible = useDemoControlStore.getState().isVisible;

  if (!isDemoActivelyRunning && isDemoMode && isVisible) {
    // Check if user is authenticated
    const { JupyterAuthService } =
      await import('../Services/JupyterAuthService');
    const isAuthenticated = await JupyterAuthService.isAuthenticated();

    if (isAuthenticated) {
      console.log(
        '[Demo] User is authenticated and demo is not running - hiding demo panel completely'
      );
      hideDemoControlPanel(true); // Pass true to completely hide the panel
    }
  }
}

/**
 * Hide and cleanup the demo control panel
 * @param completelyHide If true, hide the entire panel. If false, just hide the skip button.
 */
export function hideDemoControlPanel(completelyHide: boolean = false): void {
  if (completelyHide) {
    // Completely hide the panel
    useDemoControlStore.getState().hide();
    // Make sure to re-enable all components when control panel is hidden
    show_all_components();
  } else {
    // Just hide the skip button
    useDemoControlStore.getState().hideSkipButton();
  }
}

/**
 * Try it yourself! - Create a new notebook and send the first prompt
 * If demo is finished, only show login modal without takeover logic
 */
async function tryItYourself(demoMessages: IDemoMessage[]): Promise<void> {
  console.log('[Takeover] Try it yourself clicked - stopping demo');

  // Check if demo is finished (via Results or natural completion)
  const isDemoFinished = useDemoControlStore.getState().isDemoFinished;

  if (isDemoFinished) {
    // Demo is finished - this is "Login to Chat" mode
    console.log('[Takeover] Demo finished - showing login modal only');

    // Check if user is already authenticated
    const { JupyterAuthService } =
      await import('../Services/JupyterAuthService');
    const isAuthenticated = await JupyterAuthService.isAuthenticated();

    if (!isAuthenticated) {
      // User is not authenticated - save current notebook path and show the JWT modal
      const currentNotebook = useNotebookEventsStore
        .getState()
        .getCurrentNotebook();
      if (currentNotebook) {
        const notebookPath = currentNotebook.context.path;
        console.log(
          '[Takeover] Storing notebook path for later:',
          notebookPath
        );

        // Save the notebook first (using notebook tracker)
        try {
          await currentNotebook.context.save();
          console.log('[Takeover] Notebook saved successfully');
        } catch (saveError) {
          console.error('[Takeover] Error saving notebook:', saveError);
        }

        // Store the notebook path in localStorage
        const { storeLastNotebookPath } =
          await import('../utils/replayIdManager');
        storeLastNotebookPath(notebookPath);
      }

      const jwtModalService = JWTAuthModalService.getInstance();
      jwtModalService.show();
    } else {
      // User is already authenticated - just hide the demo control panel completely
      console.log(
        '[Takeover] User already authenticated, hiding demo panel completely'
      );
      hideDemoControlPanel(true);
    }

    return; // Exit early - don't do takeover logic
  }

  // IMMEDIATELY stop the demo
  isDemoAborted = true;
  console.log('[Takeover] Demo stopped');

  // Show all UI components when user wants to try it themselves
  show_all_components();

  // Find the first user message to send when they return
  const firstUserMessage = demoMessages.find(msg => msg.role === 'user');
  if (!firstUserMessage || typeof firstUserMessage.content !== 'string') {
    console.error('[Takeover] No valid first user message found');
    return;
  }

  // Check if user is already authenticated
  const { JupyterAuthService } = await import('../Services/JupyterAuthService');
  const isAuthenticated = await JupyterAuthService.isAuthenticated();

  if (isAuthenticated) {
    // User is already authenticated - skip to after-login steps immediately
    console.log(
      '[Takeover] User is authenticated - proceeding with takeover immediately'
    );
    // Set takeover mode in AppState (no localStorage needed for authenticated users)
    useAppStore.getState().setTakeoverMode(true, firstUserMessage.content);
    await handleTakeoverAfterAuth(firstUserMessage.content);
  } else {
    // User is not authenticated - store takeover data in localStorage AND AppState
    console.log(
      '[Takeover] User not authenticated - storing takeover data and showing login'
    );

    const replayId = getStoredReplayId();
    if (replayId) {
      enableTakeoverMode({
        messages: firstUserMessage.content,
        replayId: replayId
      });
      // Also set in AppState for immediate use
      useAppStore.getState().setTakeoverMode(true, firstUserMessage.content);
      console.log('[Takeover] Takeover mode enabled with first message');
    }

    // Show the JWT modal for the user to sign in
    const jwtModalService = JWTAuthModalService.getInstance();
    jwtModalService.show();
  }
}

/**
 * Handle takeover after authentication
 * Creates new notebook, puts prompt in chatbox, and sends message
 */
export async function handleTakeoverAfterAuth(
  firstMessage: string
): Promise<void> {
  console.log('[Takeover] Handling takeover after authentication');

  try {
    // Add waits like how we wait for replay (500ms or reset url hits race condition)
    await new Promise(resolve => setTimeout(resolve, 500));
    console.log('[Takeover] Initial wait completed');

    // Wait for essential services to be initialized using the chatbox store
    let retries = 50;
    while (retries > 0) {
      const notebookTools = getNotebookTools();
      const chatboxReady = useChatboxStore.getState().isFullyInitialized;

      if (notebookTools && chatboxReady) {
        console.log('[Takeover] All services are ready');
        break;
      }

      await new Promise(resolve => setTimeout(resolve, 200));
      retries--;
    }

    if (retries === 0) {
      throw new Error('Timeout waiting for services to initialize');
    }

    const notebookTools = getNotebookTools();
    if (!notebookTools) {
      throw new Error('NotebookTools not available');
    }

    // Clear takeover flag and data from localStorage
    const { disableTakeoverMode } = await import('../utils/replayIdManager');
    disableTakeoverMode();
    console.log('[Takeover] Cleared takeover mode from localStorage');

    // Clear from AppState but keep the prompt for sending
    const takeoverPrompt = useAppStore.getState().takeoverPrompt;
    useAppStore.getState().setTakeoverMode(false, null);
    console.log('[Takeover] Cleared takeover mode from AppState');

    // Create a new notebook
    console.log('[Takeover] Creating new notebook with tracking');
    const timestamp = new Date()
      .toISOString()
      .replace(/[:.]/g, '-')
      .slice(0, -5);
    const notebookName = `takeover-${timestamp}.ipynb`;

    const result = await notebookTools.createNotebookWithTracking(notebookName);

    if (!result.success) {
      throw new Error('Failed to create notebook for takeover');
    }

    console.log(`[Takeover] Notebook created with ID: ${result.notebookId}`);

    // Wait for notebook to open
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Get the services from the chatbox store
    const { services } = useChatboxStore.getState();
    if (!services.threadManager) {
      throw new Error('Thread manager not available');
    }

    // Create a new chat thread for this takeover session
    console.log('[Takeover] Creating new chat thread');
    const newThread = await services.threadManager.createNewThread();
    if (!newThread) {
      console.warn('[Takeover] Failed to create new thread, continuing anyway');
    } else {
      console.log('[Takeover] Created new thread:', newThread.id);
    }

    // Wait a bit for UI to be ready
    await new Promise(resolve => setTimeout(resolve, 500));

    // Use the prompt we saved earlier (or the parameter if AppState was cleared)
    const promptToSend = takeoverPrompt || firstMessage;

    // Send the takeover prompt directly using the store
    console.log('[Takeover] Sending first message:', promptToSend);
    useChatboxStore.getState().sendPromptMessage(promptToSend);
    console.log('[Takeover] Sent first message');

    console.log('[Takeover] Takeover completed successfully');
  } catch (error) {
    console.error('[Takeover] Error during takeover after auth:', error);
    // Clear takeover mode on error
    useAppStore.getState().setTakeoverMode(false, null);
    alert(
      `Takeover failed: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}
