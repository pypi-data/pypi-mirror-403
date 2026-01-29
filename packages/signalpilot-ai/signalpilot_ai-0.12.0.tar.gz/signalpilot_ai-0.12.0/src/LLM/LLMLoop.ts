/**
 * LLMLoop - The Main LLM Processing Loop
 *
 * This file contains the ENTIRE LLM loop from start to finish.
 * It is designed to be extremely readable and easy to understand.
 *
 * FLOW:
 * 1. Gather context (addContext)
 * 2. Send to Anthropic API
 * 3. Process streaming response
 * 4. Execute tool calls if any
 * 5. Handle pending diffs
 * 6. Recurse if tools were called
 * 7. Finalize
 */

import { LLMContextGatherer } from './LLMContext';
import { StreamingUIHandler } from './handlers/StreamingUIHandler';
import { ToolExecutionHandler } from './handlers/ToolExecutionHandler';
import { DiffApprovalHandler } from './handlers/DiffApprovalHandler';
import { AnthropicService } from './Anthropic/AnthropicService';
import { useLLMStateStore } from '../stores/llmStateStore';
import { getChatboxState } from '../stores/chatboxStore';
import { useServicesStore } from '../stores/servicesStore';
import { useSettingsStore } from '../stores/settingsStore';
import { useChatInputStore } from '../stores/chatInput/chatInputStore';
import {
  ChatMode,
  ILLMContext,
  ILLMLoopConfig,
  ILLMLoopResult,
  IToolUseEvent
} from './LLMTypes';

// ═══════════════════════════════════════════════════════════════
// MAIN CLASS
// ═══════════════════════════════════════════════════════════════

/**
 * The main LLM processing loop
 */
export class LLMLoop {
  private config: ILLMLoopConfig;
  private contextGatherer: LLMContextGatherer;
  private uiHandler: StreamingUIHandler;
  private toolHandler: ToolExecutionHandler;
  private diffHandler: DiffApprovalHandler;

  // State
  private isProcessing: boolean = false;
  private currentContext: ILLMContext | null = null;

  constructor(config: ILLMLoopConfig) {
    this.config = config;

    // Initialize context gatherer
    this.contextGatherer = new LLMContextGatherer(
      config.toolService,
      config.notebookContextManager
    );

    // Initialize streaming UI handler with tool service for real-time updates
    this.uiHandler = new StreamingUIHandler(
      config.messageComponent,
      config.toolService,
      config.diffManager,
      null // notebookId will be set per-request
    );

    // Initialize diff handler
    this.diffHandler = new DiffApprovalHandler(
      config.diffManager,
      config.messageComponent,
      config.chatHistory
    );

    // Initialize tool execution handler with all dependencies
    this.toolHandler = new ToolExecutionHandler(
      config.toolService,
      config.actionHistory,
      config.messageComponent,
      config.codeConfirmationDialog
    );

    // Connect handlers
    this.toolHandler.setStreamingHandler(this.uiHandler);
    this.toolHandler.setDiffHandler(this.diffHandler);
  }

  // ═══════════════════════════════════════════════════════════════
  // MAIN ENTRY POINT
  // ═══════════════════════════════════════════════════════════════

  /**
   * Process a conversation request.
   * This is the ONLY public method - the entire loop starts here.
   */
  async process(
    notebookId: string | null,
    mode: ChatMode,
    systemPromptMessages: string[] = []
  ): Promise<ILLMLoopResult> {
    console.log('[LLMLoop] ═══════════════════════════════════════════════');
    console.log('[LLMLoop] Starting process - Mode:', mode);
    console.log('[LLMLoop] ═══════════════════════════════════════════════');

    const perfStart = performance.now();

    if (this.isProcessing) {
      console.warn('[LLMLoop] Already processing a request');
      return {
        success: false,
        cancelled: false,
        error: new Error('Already processing')
      };
    }

    this.isProcessing = true;

    // Set notebook ID on handlers
    this.uiHandler.setNotebookId(notebookId);
    this.toolHandler.setNotebookId(notebookId);

    // Refresh notebook tool IDs
    this.config.toolService.notebookTools?.refresh_ids();

    try {
      // ─────────────────────────────────────────────────────────────
      // STEP 1: Gather all context
      // ─────────────────────────────────────────────────────────────
      console.log('[LLMLoop] Step 1: Gathering context');
      const context = await this.gatherContext(
        notebookId,
        mode,
        systemPromptMessages
      );
      this.currentContext = context;

      const perfAfterContext = performance.now();
      console.log(
        `[LLMLoop] Context gathered in ${(perfAfterContext - perfStart).toFixed(2)}ms`
      );

      // ─────────────────────────────────────────────────────────────
      // STEP 2: Run the loop
      // ─────────────────────────────────────────────────────────────
      const result = await this.runLoop(context, systemPromptMessages);

      const perfEnd = performance.now();
      console.log('[LLMLoop] ═══════════════════════════════════════════════');
      console.log(
        `[LLMLoop] Process complete in ${(perfEnd - perfStart).toFixed(2)}ms`
      );
      console.log('[LLMLoop] ═══════════════════════════════════════════════');

      return result;
    } catch (error) {
      console.error('[LLMLoop] Error:', error);
      this.uiHandler.onRequestError(error as Error);
      return { success: false, cancelled: false, error: error as Error };
    } finally {
      this.isProcessing = false;
      this.currentContext = null;
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // STEP 1: CONTEXT GATHERING
  // ═══════════════════════════════════════════════════════════════

  /**
   * Check if currently processing
   */
  isCurrentlyProcessing(): boolean {
    return this.isProcessing;
  }

  // ═══════════════════════════════════════════════════════════════
  // STEP 2: THE LOOP
  // ═══════════════════════════════════════════════════════════════

  /**
   * Get current context (for debugging)
   */
  getCurrentContext(): ILLMContext | null {
    return this.currentContext;
  }

  // ═══════════════════════════════════════════════════════════════
  // API CALL
  // ═══════════════════════════════════════════════════════════════

  /**
   * Cancel current request
   */
  cancelRequest(): void {
    this.config.anthropicService.cancelRequest();
    this.uiHandler.onRequestCancelled();
  }

  // ═══════════════════════════════════════════════════════════════
  // TOOL CONFIGURATION
  // ═══════════════════════════════════════════════════════════════

  /**
   * Gather all context needed for the LLM request.
   * Delegates to LLMContextGatherer.addContext()
   */
  private async gatherContext(
    notebookId: string | null,
    mode: ChatMode,
    systemPromptMessages: string[]
  ): Promise<ILLMContext> {
    return await this.contextGatherer.addContext(
      notebookId,
      mode,
      systemPromptMessages
    );
  }

  // ═══════════════════════════════════════════════════════════════
  // PUBLIC UTILITIES
  // ═══════════════════════════════════════════════════════════════

  /**
   * The main processing loop. Calls API, processes response, recurses if needed.
   */
  private async runLoop(
    context: ILLMContext,
    systemPromptMessages: string[]
  ): Promise<ILLMLoopResult> {
    // Reset UI handler for new iteration
    this.uiHandler.reset();

    // Start UI indicators
    this.uiHandler.onRequestStart();

    // ─────────────────────────────────────────────────────────────
    // STEP 2a: Call Anthropic API
    // ─────────────────────────────────────────────────────────────
    console.log('[LLMLoop] Step 2a: Calling Anthropic API');

    const response = await this.callAPI(context, systemPromptMessages);

    // Check for cancellation
    if (
      response?.cancelled ||
      this.config.anthropicService.isRequestCancelled()
    ) {
      console.log('[LLMLoop] Request cancelled');
      this.uiHandler.onRequestCancelled();
      return { success: true, cancelled: true };
    }

    // Check for fresh context needed (cell rejection)
    if (response?.needsFreshContext) {
      console.log('[LLMLoop] Fresh context needed');
      this.uiHandler.onRequestComplete();
      return { success: true, cancelled: false, needsFreshContext: true };
    }

    // ─────────────────────────────────────────────────────────────
    // STEP 2b: Display token debug info if enabled
    // ─────────────────────────────────────────────────────────────
    this.displayTokenDebugInfo(response);

    // ─────────────────────────────────────────────────────────────
    // STEP 2c: Finalize streaming
    // ─────────────────────────────────────────────────────────────
    console.log('[LLMLoop] Step 2b: Finalizing streaming');
    this.uiHandler.onRequestComplete();

    // ─────────────────────────────────────────────────────────────
    // STEP 2c: Process tool calls (if any)
    // ─────────────────────────────────────────────────────────────
    const hasToolCalls = this.toolHandler.hasToolCalls(response);

    if (hasToolCalls) {
      console.log('[LLMLoop] Step 2c: Processing tool calls');

      const toolResult = await this.toolHandler.processToolCalls(
        response,
        context,
        this.config.messageComponent
      );

      if (!toolResult.shouldContinue) {
        console.log('[LLMLoop] Tool processing stopped loop');
        return { success: true, cancelled: false };
      }

      // ─────────────────────────────────────────────────────────────
      // STEP 2d: Handle pending diffs before recursing
      // ─────────────────────────────────────────────────────────────
      console.log('[LLMLoop] Step 2d: Handling pending diffs');

      const diffsApproved = await this.diffHandler.handlePendingDiffs(
        context.notebookId,
        true
      );

      // Clear diffs after handling
      this.diffHandler.clearPendingDiffs(context.notebookId);

      if (!diffsApproved) {
        console.log('[LLMLoop] Diffs rejected, stopping loop');
        return { success: true, cancelled: false };
      }

      // Check if user has made approval decisions that should stop the loop
      if (this.diffHandler.checkForApprovalDecisions()) {
        console.log('[LLMLoop] Approval decisions detected, stopping loop');
        return { success: true, cancelled: false };
      }

      // ─────────────────────────────────────────────────────────────
      // STEP 2e: Recurse if tools were called
      // ─────────────────────────────────────────────────────────────
      console.log('[LLMLoop] Step 2e: Recursing after tool calls');

      // Hide diff UI before recursing
      this.diffHandler.hideDiffUI();

      // Show generating indicator
      useLLMStateStore.getState().show('Generating...');

      // Recurse with fresh context
      const freshContext = await this.gatherContext(
        context.notebookId,
        context.mode,
        systemPromptMessages
      );

      return await this.runLoop(freshContext, systemPromptMessages);
    }

    // ─────────────────────────────────────────────────────────────
    // STEP 3: Finalize (no tool calls)
    // ─────────────────────────────────────────────────────────────
    console.log('[LLMLoop] Step 3: Finalizing (no tool calls)');

    return { success: true, cancelled: false };
  }

  /**
   * Call the Anthropic API with streaming.
   * This is a thin wrapper that connects streaming callbacks to UI handler.
   */
  private async callAPI(
    context: ILLMContext,
    systemPromptMessages: string[]
  ): Promise<any> {
    const { anthropicService, toolService, notebookContextManager } =
      this.config;

    // Get tools based on mode
    const tools = this.getToolsForMode(context.mode);

    // Build notebook state for the API
    const notebookState =
      this.contextGatherer.buildNotebookStateString(context);

    // Call API with streaming callbacks routed to UI handler
    return await anthropicService.sendMessage(
      [], // New messages already added to history
      tools,
      context.mode,
      systemPromptMessages,

      // onRetry callback
      async (error, attempt) => {
        console.log(`[LLMLoop] Retry attempt ${attempt}`);
        this.uiHandler.updateLoadingIndicator(
          `Retrying... (attempt ${attempt})`
        );
      },

      // fetchNotebookState - returns context we already gathered
      async () => notebookState,

      // onTextChunk - route to UI handler
      (text: string) => {
        if (!anthropicService.isRequestCancelled()) {
          this.uiHandler.onTextChunk(text);
        }
      },

      // onToolUse - route to UI handler
      (toolUse: any) => {
        if (!anthropicService.isRequestCancelled()) {
          this.uiHandler.onToolUseEvent(toolUse as IToolUseEvent);
        }
      },

      // notebookContextManager
      notebookContextManager,

      // notebookId
      context.notebookId || undefined,

      // errorLogger (not used here)
      undefined,

      // forceRetry
      false,

      // onToolSearchResult - route to UI handler for server tools
      (toolUseId: string, result: any) => {
        if (!anthropicService.isRequestCancelled()) {
          this.uiHandler.onToolSearchResult(toolUseId, result);
        }
      }
    );
  }

  /**
   * Get tools based on mode
   */
  private getToolsForMode(mode: ChatMode): any[] {
    const { toolService } = this.config;

    switch (mode) {
      case 'ask':
        return toolService.getAskModeTools();
      case 'fast':
        return toolService.getFastModeTools();
      case 'welcome':
        return toolService.getWelcomeTools();
      default:
        return toolService.getTools();
    }
  }

  /**
   * Update token progress from LLM response usage data.
   * This updates the token count shown in the UI progress indicator.
   */
  private updateTokenProgressFromUsage(response: any): void {
    const usage = response?.usage;
    if (!usage) {
      return;
    }

    // Calculate total input tokens (context window usage)
    // This is what matters for the context limit
    const inputTokens = usage.input_tokens || 0;
    const cacheCreationTokens = usage.cache_creation_input_tokens || 0;
    const cacheReadTokens = usage.cache_read_input_tokens || 0;
    const totalInputTokens =
      inputTokens + cacheCreationTokens + cacheReadTokens;

    // Update the token count in the store
    useChatInputStore.getState().setTokenCount(totalInputTokens);

    console.log(
      '[LLMLoop] Token progress updated from usage:',
      totalInputTokens
    );
  }

  /**
   * Display token usage debug information if token debug mode is enabled
   */
  private displayTokenDebugInfo(response: any): void {
    // Always update token progress from usage (regardless of debug mode)
    this.updateTokenProgressFromUsage(response);

    // Check if token debug mode is enabled for detailed display
    const tokenMode = useSettingsStore.getState().tokenMode;
    if (!tokenMode) {
      return;
    }

    // Extract usage data from response
    const usage = response?.usage;
    if (!usage) {
      console.log('[LLMLoop] No usage data in response for token debug');
      return;
    }

    // Build the debug message (plain text)
    const inputTokens = usage.input_tokens || 0;
    const outputTokens = usage.output_tokens || 0;
    const cacheCreationTokens = usage.cache_creation_input_tokens || 0;
    const cacheReadTokens = usage.cache_read_input_tokens || 0;
    const totalInputTokens =
      inputTokens + cacheCreationTokens + cacheReadTokens;
    const totalTokens = totalInputTokens + outputTokens;

    let debugMessage = `[Token Usage]\n`;
    debugMessage += `Input tokens: ${inputTokens.toLocaleString()}\n`;
    debugMessage += `Cache creation tokens: ${cacheCreationTokens.toLocaleString()}\n`;
    debugMessage += `Cache read tokens: ${cacheReadTokens.toLocaleString()}\n`;
    debugMessage += `Output tokens: ${outputTokens.toLocaleString()}\n`;
    debugMessage += `Total: ${totalTokens.toLocaleString()}`;

    // Add model info if available
    if (response?.model) {
      debugMessage += `\nModel: ${response.model}`;
    }

    // Add stop reason if available
    if (response?.stop_reason) {
      debugMessage += `\nStop reason: ${response.stop_reason}`;
    }

    // Display as system message
    this.config.messageComponent.addSystemMessage(debugMessage);

    console.log('[LLMLoop] Token debug info displayed:', {
      inputTokens,
      outputTokens,
      cacheCreationTokens,
      cacheReadTokens,
      totalTokens,
      model: response?.model,
      stopReason: response?.stop_reason
    });
  }
}

// ═══════════════════════════════════════════════════════════════
// FACTORY FUNCTION
// ═══════════════════════════════════════════════════════════════

/**
 * Create an LLM loop instance with the current app state
 */
export function createLLMLoop(): LLMLoop | null {
  const chatboxState = getChatboxState();
  const servicesState = useServicesStore.getState();

  if (!chatboxState.services?.chatContainer?.chatWidget) {
    console.error('[LLMLoop] Chat container not available');
    return null;
  }

  const chatWidget = chatboxState.services.chatContainer.chatWidget;

  const config: ILLMLoopConfig = {
    anthropicService: chatWidget.conversationService
      .chatService as AnthropicService,
    toolService: servicesState.toolService!,
    messageComponent: chatWidget.messageComponent,
    notebookContextManager: servicesState.notebookContextManager!,
    diffManager: servicesState.notebookDiffManager || null,
    actionHistory: servicesState.actionHistory!,
    chatHistory: chatWidget.chatHistory,
    loadingManager: chatWidget.loadingManager,
    codeConfirmationDialog:
      chatWidget.conversationService.codeConfirmationDialog
  };

  return new LLMLoop(config);
}
