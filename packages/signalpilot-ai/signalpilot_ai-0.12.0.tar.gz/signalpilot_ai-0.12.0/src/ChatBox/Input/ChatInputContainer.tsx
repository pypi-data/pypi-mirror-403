/**
 * ChatInputContainer Component
 *
 * A React component that fully replaces the ChatInputManager class.
 * Uses custom hooks to separate concerns:
 * - useInputControls: Input value, selection, focus
 * - useMessageHistory: History navigation
 * - useSendMessage: Message sending/continuation
 * - useTokenProgress: Token tracking
 *
 * DOM Structure (matches ChatInputManager exactly):
 * .sage-ai-input-container (position: relative)
 * └── .sage-ai-chatbox-wrapper
 *     ├── .sage-ai-context-row-container (ContextRow)
 *     └── .sage-ai-input-row
 *         ├── .sage-ai-rich-text-input-container (display: contents) → RichTextInput
 *         ├── .sage-ai-token-progress-container-wrapper → TokenProgressIndicator
 *         ├── .sage-ai-send-button-container → SendButton
 *         └── .sage-ai-mode-selector-container → ModeSelector
 * └── .sage-ai-mention-dropdown-container → MentionDropdown
 */
import React, {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState
} from 'react';

import {
  ChatInputContainerProps,
  ChatInputContainerRef,
  ChatInputDependencies
} from './types';
import { CellContext, ContextRow } from './ContextRow';
import { useInputControls, useMessageHistory, useSendMessage } from './hooks';
import { RichTextInput } from './RichTextInput';
import { MentionDropdown, MentionDropdownRef } from '../MentionDropdown';
import { SendButton } from './SendButton';
import { ModeSelector } from './ModeSelector';
import { TokenProgressIndicator } from './TokenProgressIndicator';
import { DemoOverlay } from '@/Components/DemoOverlay';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';
import { IChatMessage, DiffApprovalStatus } from '@/types';
import { useNotebookEventsStore } from '@/stores/notebookEventsStore';
import {
  getNotebookContextManager,
  getNotebookTools,
  getContextCellHighlighter,
  getNotebookDiffManager
} from '@/stores/servicesStore';
import { ConversationService } from '@/LLM/ConversationService';
import { checkTokenLimit, MAX_RECOMMENDED_TOKENS } from '@/utils/tokenUtils';
import { useChatInputStore } from '@/stores/chatInput/chatInputStore';
import { useChatModeStore } from '@/stores/chatModeStore';
import { usePlanStateStore } from '@/stores/planStateStore';
import { useChatMessagesStore } from '@/stores/chatMessages';
import { useChatboxStore } from '@/stores/chatboxStore';

/**
 * ChatInputContainer - Full React replacement for ChatInputManager
 */
export const ChatInputContainer = forwardRef<
  ChatInputContainerRef,
  ChatInputContainerProps
>(
  (
    {
      chatHistoryManager,
      contentManager,
      toolService,
      initialDependencies,
      onContextSelected,
      onContextRemoved,
      onResetChat,
      onModeSelected,
      onMessageSent,
      onCancel,
      placeholder:
        initialPlaceholder = 'What would you like me to generate or analyze?'
    },
    ref
  ) => {
    // ═══════════════════════════════════════════════════════════════
    // REFS
    // ═══════════════════════════════════════════════════════════════

    const containerRef = useRef<HTMLDivElement>(null);
    const mentionDropdownRef = useRef<MentionDropdownRef>(null);

    // ═══════════════════════════════════════════════════════════════
    // STATE
    // ═══════════════════════════════════════════════════════════════

    const [dependencies, setDependenciesState] =
      useState<ChatInputDependencies | null>(initialDependencies || null);
    const [activeContexts, setActiveContexts] = useState<
      Map<string, IMentionContext>
    >(new Map());
    const [inputElement, setInputElement] = useState<HTMLDivElement | null>(
      null
    );
    const [contextRowKey, setContextRowKey] = useState(0);
    const [isCompacting, setIsCompacting] = useState(false);

    // Subscribe to token count from store (updated by LLM response usage)
    const currentTokenCount = useChatInputStore(
      state => state.currentTokenCount
    );
    const [modeName, setModeName] = useState<'agent' | 'ask' | 'fast'>('agent');
    const [placeholder, setPlaceholderState] = useState(initialPlaceholder);
    const [currentMentionStart, setCurrentMentionStart] = useState(-1);

    // ═══════════════════════════════════════════════════════════════
    // HOOKS
    // ═══════════════════════════════════════════════════════════════

    // Input controls (value, selection, focus)
    const {
      richTextInputRef,
      hasContent,
      getInputValue,
      setInputValue,
      getSelectionStart,
      setSelectionRange,
      clearInput,
      focus,
      setHasContent
    } = useInputControls();

    // Message history navigation
    const {
      loadHistory: loadUserMessageHistory,
      navigateHistory,
      addToHistory
    } = useMessageHistory({ chatHistoryManager });

    // Message sending
    const {
      sendMessage: sendMessageInternal,
      continueMessage: continueMessageInternal,
      isProcessingMessage,
      setIsProcessingMessage,
      checkpointToRestore,
      setCheckpointToRestore
    } = useSendMessage({
      dependencies,
      chatHistoryManager,
      activeContexts,
      modeName,
      getInputValue,
      clearInput,
      addToHistory,
      onResetChat,
      onMessageSent
    });

    // ═══════════════════════════════════════════════════════════════
    // TOKEN PROGRESS
    // ═══════════════════════════════════════════════════════════════

    /**
     * Load token count from message history.
     * This is only called once on thread load, not on every message change.
     * Real-time updates come directly from LLM response usage via the store.
     */
    const loadTokenCountFromHistory = useCallback(
      (messages?: IChatMessage[]): void => {
        const conversationHistory =
          messages || dependencies?.messageComponent?.getMessageHistory() || [];

        let totalTokens = 0;
        let hasUsageData = false;

        for (const message of conversationHistory) {
          if (message.usage) {
            hasUsageData = true;
            totalTokens +=
              (message.usage.cache_creation_input_tokens || 0) +
              (message.usage.cache_read_input_tokens || 0) +
              (message.usage.input_tokens || 0) +
              (message.usage.output_tokens || 0);
          }
        }

        const tokenLimitCheck = checkTokenLimit(conversationHistory);
        const actualTokens = hasUsageData
          ? totalTokens
          : tokenLimitCheck.estimatedTokens;

        // Update the store's token count
        useChatInputStore.getState().setTokenCount(actualTokens);

        const percentage = Math.min(
          Math.round((actualTokens / MAX_RECOMMENDED_TOKENS) * 100),
          100
        );
        // Update NewPromptCTA visibility via store
        useChatInputStore
          .getState()
          .updateNewPromptCtaFromTokenPercentage(percentage);
      },
      [dependencies?.messageComponent]
    );

    // Alias for backward compatibility with imperative handle
    const updateTokenProgress = loadTokenCountFromHistory;

    const handleCompressHistory = useCallback(async (): Promise<void> => {
      if (
        !dependencies?.messageComponent ||
        isProcessingMessage ||
        isCompacting
      )
        return;

      setIsCompacting(true);
      try {
        const currentInput = getInputValue();
        setInputValue(
          'Please compress the chat history to reduce token usage. Keep the 10 most recent messages uncompressed.'
        );
        await sendMessageInternal(undefined, true);
        setInputValue(currentInput);
      } catch (error) {
        console.error('[ChatInputContainer] Error compressing:', error);
        dependencies?.messageComponent?.addSystemMessage(
          `Error compressing: ${error instanceof Error ? error.message : String(error)}`
        );
      } finally {
        setTimeout(() => setIsCompacting(false), 500);
      }
    }, [
      dependencies?.messageComponent,
      isProcessingMessage,
      isCompacting,
      getInputValue,
      setInputValue,
      sendMessageInternal
    ]);

    // ═══════════════════════════════════════════════════════════════
    // EVENT HANDLERS
    // ═══════════════════════════════════════════════════════════════

    const handleInput = useCallback(() => {
      const text = getInputValue();
      setHasContent(text.length > 0);

      // Mention detection
      const cursorPosition = getSelectionStart();
      const dropdownRef = mentionDropdownRef.current;
      if (!dropdownRef) return;

      if (dropdownRef.isVisible()) {
        const inputValue = richTextInputRef.current?.getPlainText() || '';
        if (
          cursorPosition < currentMentionStart ||
          !inputValue
            .substring(currentMentionStart, cursorPosition)
            .startsWith('@')
        ) {
          dropdownRef.hide();
          return;
        }
        const mentionText = inputValue.substring(
          currentMentionStart + 1,
          cursorPosition
        );
        dropdownRef.updateMentionText(mentionText);
        return;
      }

      const inputValue = richTextInputRef.current?.getPlainText() || '';
      if (inputValue.charAt(cursorPosition - 1) === '@') {
        setCurrentMentionStart(cursorPosition - 1);
        dropdownRef.show(cursorPosition - 1);
      }
    }, [
      getInputValue,
      getSelectionStart,
      currentMentionStart,
      setHasContent,
      richTextInputRef
    ]);

    const handleKeyDown = useCallback(
      (event: React.KeyboardEvent) => {
        const isDropdownVisible = mentionDropdownRef.current?.isVisible();

        if (isDropdownVisible) {
          if (event.key === 'Tab' || event.key === 'Enter') {
            event.preventDefault();
            mentionDropdownRef.current?.selectHighlighted();
            return;
          }
          if (event.key === 'ArrowDown') {
            event.preventDefault();
            mentionDropdownRef.current?.navigate('down');
            return;
          }
          if (event.key === 'ArrowUp') {
            event.preventDefault();
            mentionDropdownRef.current?.navigate('up');
            return;
          }
          if (event.key === 'Escape') {
            event.preventDefault();
            mentionDropdownRef.current?.hide();
            return;
          }
        }

        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault();
          void sendMessageInternal();
          return;
        }

        // History navigation
        if (event.key === 'ArrowUp') {
          const cursorPos = getSelectionStart();
          const inputVal = getInputValue();
          if (cursorPos === 0 || inputVal === '') {
            event.preventDefault();
            const result = navigateHistory(
              'up',
              inputVal,
              cursorPos,
              inputVal.length
            );
            if (result !== null) {
              setInputValue(result);
              setSelectionRange(result.length, result.length);
            }
          }
        } else if (event.key === 'ArrowDown') {
          const cursorPos = getSelectionStart();
          const inputVal = getInputValue();
          if (cursorPos === inputVal.length || inputVal === '') {
            event.preventDefault();
            const result = navigateHistory(
              'down',
              inputVal,
              cursorPos,
              inputVal.length
            );
            if (result !== null) {
              setInputValue(result);
              setSelectionRange(result.length, result.length);
            }
          }
        }
      },
      [
        sendMessageInternal,
        getSelectionStart,
        getInputValue,
        navigateHistory,
        setInputValue,
        setSelectionRange
      ]
    );

    const handleContextSelected = useCallback(
      (context: IMentionContext) => {
        // Create new map with the added context
        const newContexts = new Map(activeContexts);
        newContexts.set(context.id, context);

        // Update state with new map
        setActiveContexts(newContexts);

        // Update RichTextInput ref immediately with new map (not stale activeContexts)
        richTextInputRef.current?.setActiveContexts(newContexts);

        // Add context to messageComponent so it's included when sending messages
        if (dependencies?.messageComponent) {
          dependencies.messageComponent.addMentionContext(context);
        }

        onContextSelected?.(context);
      },
      [
        activeContexts,
        onContextSelected,
        richTextInputRef,
        dependencies?.messageComponent
      ]
    );

    const handleAddContext = useCallback(() => {
      focus();
      // Use React ref method instead of document.execCommand
      setTimeout(() => richTextInputRef.current?.insertText('@'), 0);
    }, [focus, richTextInputRef]);

    const handleRemoveMentionContext = useCallback(
      (contextId: string, contextName: string) => {
        if (dependencies?.messageComponent) {
          dependencies.messageComponent.removeMentionContext(contextId);
        }
        const currentInput = getInputValue();
        const escapedName = contextName.replace(
          /[-/\\^$*+?.()|[\]{}]/g,
          '\\$&'
        );
        const cleanedInput = currentInput
          .replace(new RegExp(`@\\{?${escapedName}\\}?`, 'g'), '')
          .trim();
        setInputValue(cleanedInput);
        onContextRemoved?.(contextId);
        setContextRowKey(k => k + 1);
      },
      [
        dependencies?.messageComponent,
        getInputValue,
        setInputValue,
        onContextRemoved
      ]
    );

    const handleRemoveCellContext = useCallback((cellId: string) => {
      const contextManager = getNotebookContextManager();
      const notebookId = useNotebookEventsStore.getState().currentNotebookId;
      if (contextManager && notebookId) {
        contextManager.removeCellFromContext(notebookId, cellId);
        const notebookTools = getNotebookTools();
        const currentNotebookPanel = notebookTools.getCurrentNotebook()?.widget;
        if (currentNotebookPanel) {
          const contextCellHighlighter = getContextCellHighlighter();
          contextCellHighlighter.addContextButtonsToAllCells(
            currentNotebookPanel
          );
        }
      }
      setContextRowKey(k => k + 1);
    }, []);

    const handleModeChange = useCallback(
      (newMode: 'agent' | 'ask' | 'fast') => {
        setModeName(newMode);
        // Sync with centralized chat mode store
        useChatModeStore.getState().setNotebookMode(newMode);
        onModeSelected?.(newMode);
      },
      [onModeSelected]
    );

    const handleSend = useCallback(
      () => void sendMessageInternal(),
      [sendMessageInternal]
    );

    /**
     * Handle cancel button click - actually cancels the LLM request
     */
    const handleCancel = useCallback(() => {
      console.log('[ChatInputContainer] Cancel button clicked');

      // Cancel the actual API request
      if (dependencies?.chatService) {
        dependencies.chatService.cancelRequest();
        console.log('[ChatInputContainer] Cancelled chat service request');
      }

      // Emit finished signal to unblock any stuck diff approval await
      try {
        const diffManager = getNotebookDiffManager();
        diffManager._finishedProcessingDiffs.emit(DiffApprovalStatus.APPROVED);
      } catch {
        // DiffManager not initialized - nothing to unblock
      }

      // Force-reset the conversation in-progress flag
      ConversationService.forceReset();

      // Clear processing state (this also clears useChatStore.isProcessing)
      setIsProcessingMessage(false);

      // Clear plan state loading indicator
      usePlanStateStore.getState().setLoading(false);

      // Finalize any streaming message
      if (dependencies?.messageComponent) {
        dependencies.messageComponent.finalizeStreamingMessage();
      }

      // Hide loading indicators
      if (dependencies?.uiHelper) {
        dependencies.uiHelper.hideLoadingIndicator();
      }

      // Call optional callback
      onCancel?.();
    }, [dependencies, setIsProcessingMessage, onCancel]);

    // ═══════════════════════════════════════════════════════════════
    // COMPUTED VALUES
    // ═══════════════════════════════════════════════════════════════

    const getCellContexts = useCallback((): CellContext[] => {
      const notebookId = useNotebookEventsStore.getState().currentNotebookId;
      const contextManager = getNotebookContextManager();
      return notebookId && contextManager
        ? contextManager.getContextCells(notebookId)
        : [];
    }, []);

    const getMentionContexts = useCallback((): IMentionContext[] => {
      const mentionContextsMap =
        dependencies?.messageComponent?.getMentionContexts();
      return mentionContextsMap ? Array.from(mentionContextsMap.values()) : [];
    }, [dependencies?.messageComponent]);

    // ═══════════════════════════════════════════════════════════════
    // EFFECTS
    // ═══════════════════════════════════════════════════════════════

    // Sync dependencies when initialDependencies prop changes
    // (This handles the case where services become available after initial mount)
    useEffect(() => {
      if (initialDependencies) {
        console.log(
          '[ChatInputContainer] Syncing initialDependencies to state'
        );
        setDependenciesState(initialDependencies);
      }
    }, [initialDependencies]);

    useEffect(() => {
      const element = richTextInputRef.current?.getInputElement();
      if (element) setInputElement(element);
    }, [richTextInputRef]);

    useEffect(() => {
      void loadUserMessageHistory();
    }, [loadUserMessageHistory]);

    // Sync local modeName with centralized chat mode store
    useEffect(() => {
      const unsubscribe = useChatModeStore.subscribe(
        state => state.notebookMode,
        notebookMode => {
          if (notebookMode !== modeName) {
            console.log(
              `[ChatInputContainer] Syncing modeName from store: ${notebookMode}`
            );
            setModeName(notebookMode);
          }
        }
      );
      // Also sync on mount
      const storeMode = useChatModeStore.getState().notebookMode;
      if (storeMode !== modeName) {
        setModeName(storeMode);
      }
      return unsubscribe;
    }, []); // Empty deps - only run on mount

    // Load token count from history on thread change (not on every message)
    // Real-time updates come from LLM response usage via the store
    useEffect(() => {
      const unsubscribe = useChatMessagesStore.subscribe(
        state => state.currentThreadId,
        () => {
          // When thread changes, load token count from history
          const currentHistory = useChatMessagesStore.getState().llmHistory;
          loadTokenCountFromHistory(currentHistory);
        }
      );

      // Also load on mount with current history
      const currentHistory = useChatMessagesStore.getState().llmHistory;
      if (currentHistory.length > 0) {
        loadTokenCountFromHistory(currentHistory);
      }

      return unsubscribe;
    }, [loadTokenCountFromHistory]);

    // Subscribe to context row version changes (triggered by cell add/remove from context)
    useEffect(() => {
      const unsubscribe = useChatboxStore.subscribe(
        state => state.contextRowVersion,
        () => {
          // Increment context row key to force re-render of ContextRow
          setContextRowKey(k => k + 1);
        }
      );
      return unsubscribe;
    }, []);

    // ═══════════════════════════════════════════════════════════════
    // IMPERATIVE HANDLE
    // ═══════════════════════════════════════════════════════════════

    useImperativeHandle(
      ref,
      () => ({
        sendMessage: sendMessageInternal,
        continueMessage: continueMessageInternal,
        focus,
        clearInput,
        getCurrentInputValue: getInputValue,
        setInputValue,
        loadUserMessageHistory,
        updateTokenProgress,
        renderContextRow: () => setContextRowKey(k => k + 1),
        getActiveContexts: () => activeContexts,
        setPlaceholder: (p: string) => setPlaceholderState(p),
        getIsProcessingMessage: () => isProcessingMessage,
        setIsProcessingMessage,
        getCheckpointToRestore: () => checkpointToRestore,
        setCheckpointToRestore,
        setDependencies: (deps: ChatInputDependencies) => {
          console.log('[ChatInputContainer] setDependencies called');
          setDependenciesState(deps);
        }
      }),
      [
        sendMessageInternal,
        continueMessageInternal,
        focus,
        clearInput,
        getInputValue,
        setInputValue,
        loadUserMessageHistory,
        updateTokenProgress,
        activeContexts,
        isProcessingMessage,
        setIsProcessingMessage,
        checkpointToRestore,
        setCheckpointToRestore
      ]
    );

    // ═══════════════════════════════════════════════════════════════
    // RENDER
    // ═══════════════════════════════════════════════════════════════

    return (
      <div
        ref={containerRef}
        className="sage-ai-input-container"
        style={{ position: 'relative' }}
      >
        <div
          className="sage-ai-chatbox-wrapper"
          style={{ position: 'relative' }}
        >
          {/* Demo overlay - renders when demo mode is active */}
          <DemoOverlay />

          <div className="sage-ai-context-row-container">
            <ContextRow
              key={contextRowKey}
              cellContexts={getCellContexts()}
              mentionContexts={getMentionContexts()}
              onAddContext={handleAddContext}
              onRemoveMentionContext={handleRemoveMentionContext}
              onRemoveCellContext={handleRemoveCellContext}
            />
          </div>

          <div className="sage-ai-input-row">
            <div
              className="sage-ai-rich-text-input-container"
              style={{ display: 'contents' }}
            >
              <RichTextInput
                ref={richTextInputRef}
                placeholder={placeholder}
                activeContexts={activeContexts}
                onInput={handleInput}
                onKeyDown={handleKeyDown}
                onPastedContext={handleContextSelected}
              />
            </div>

            <div className="sage-ai-token-progress-container-wrapper">
              <TokenProgressIndicator
                tokenCount={currentTokenCount}
                maxTokens={MAX_RECOMMENDED_TOKENS}
                onCompact={handleCompressHistory}
                isCompacting={isCompacting}
              />
            </div>

            <div className="sage-ai-send-button-container">
              <SendButton
                hasContent={hasContent}
                onSend={handleSend}
                onCancel={handleCancel}
              />
            </div>

            <div className="sage-ai-mode-selector-container">
              <ModeSelector onModeChange={handleModeChange} />
            </div>
          </div>
        </div>

        <div className="sage-ai-mention-dropdown-container">
          <MentionDropdown
            ref={mentionDropdownRef}
            inputElement={inputElement}
            parentElement={containerRef.current}
            onContextSelected={handleContextSelected}
            onVisibilityChange={visible => {
              if (!visible) setCurrentMentionStart(-1);
            }}
          />
        </div>
      </div>
    );
  }
);

ChatInputContainer.displayName = 'ChatInputContainer';

export default ChatInputContainer;
