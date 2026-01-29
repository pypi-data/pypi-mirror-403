import * as React from 'react';
import { ILLMState, LLMDisplayState } from './types';
import { DiffItem } from './DiffItem';
import { useAppStore } from '@/stores/appStore';
import { getNotebookDiffManager } from '@/stores/servicesStore';
import { IPendingDiff } from '@/types';
import { MENU_CLOSE_ICON, MENU_ICON, WARNING_ICON } from './icons';
import { getToolDisplayMessage, getToolIcon } from '@/utils/toolDisplay';
import {
  subscribeToDiffChanges,
  useDiffStore,
  selectIsRunAllLoading,
  selectIsRejectAllLoading,
  selectIsAnyActionLoading
} from '@/stores/diffStore';
import { NotebookDiffTools } from '@/Notebook/NotebookDiffTools';
import { useLLMStateStore } from '@/stores/llmStateStore';
import { useChatboxStore } from '@/stores/chatboxStore';
import {
  useDemoControlStore,
  selectIsVisible as selectDemoControlVisible
} from '@/stores/demoControlStore';

/**
 * Props for LLMStateContent when used with props (legacy mode)
 */
interface ILLMStateContentProps extends ILLMState {
  /** If true, component uses Zustand store instead of props */
  useStore?: boolean;
}

/**
 * React component for displaying LLM processing state content.
 * Can be used in two modes:
 * 1. With props (legacy mode for backwards compatibility)
 * 2. With Zustand store (set useStore=true or use LLMStateDisplay component)
 */
export function LLMStateContent(
  props: ILLMStateContentProps
): JSX.Element | null {
  // If useStore is true, read from Zustand store
  const storeState = useLLMStateStore();

  // Determine which values to use - store or props
  const useStoreMode = props.useStore === true;

  const isVisible = useStoreMode ? storeState.isVisible : props.isVisible;
  const state = useStoreMode ? storeState.state : props.state;
  const text = useStoreMode ? storeState.text : props.text;
  const toolName = useStoreMode ? storeState.toolName : props.toolName;
  const diffs = useStoreMode ? storeState.diffs : props.diffs;
  const waitingForUser = useStoreMode
    ? storeState.waitingForUser
    : props.waitingForUser;
  const isRunContext = useStoreMode
    ? storeState.isRunContext
    : props.isRunContext;
  const onRunClick = useStoreMode ? storeState.onRunClick : props.onRunClick;
  const onRejectClick = useStoreMode
    ? storeState.onRejectClick
    : props.onRejectClick;
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [allDiffsResolved, setAllDiffsResolved] = React.useState(false);
  const [currentDiffs, setCurrentDiffs] = React.useState<IPendingDiff[]>(
    diffs || []
  );
  const [shouldHideForDemoMode, setShouldHideForDemoMode] =
    React.useState(false);

  // Use shared loading state from diffStore
  const isRunAllLoading = useDiffStore(selectIsRunAllLoading);
  const isRejectAllLoading = useDiffStore(selectIsRejectAllLoading);
  const isAnyActionLoading = useDiffStore(selectIsAnyActionLoading);
  const { setRunAllLoading, setRejectAllLoading } = useDiffStore.getState();

  // Refs for run buttons to enable keyboard shortcuts
  const runButtonRef = React.useRef<HTMLButtonElement>(null);
  const runAllButtonRef = React.useRef<HTMLButtonElement>(null);

  // Check if we should hide the display when in demo mode and not authenticated
  React.useEffect(() => {
    const checkDemoModeAuth = async () => {
      const isDemoMode = useAppStore.getState().isDemoMode;

      if (!isDemoMode) {
        setShouldHideForDemoMode(false);
        return;
      }

      // In demo mode, check authentication
      let isAuthenticated = false;

      // First check user profile in useAppStore
      const userProfile = useAppStore.getState().userProfile;
      if (userProfile) {
        isAuthenticated = true;
      } else {
        // If not in AppState, try to get it from JupyterAuthService
        try {
          const { JupyterAuthService } =
            await import('../../Services/JupyterAuthService');
          isAuthenticated = await JupyterAuthService.isAuthenticated();
        } catch (error) {
          console.warn(
            '[LLMStateContent] Failed to check authentication:',
            error
          );
          isAuthenticated = false;
        }
      }

      // Hide if in demo mode and not authenticated
      setShouldHideForDemoMode(isDemoMode && !isAuthenticated);
    };

    checkDemoModeAuth();
  }, []);

  // Subscribe to diff state changes from diffStore using Zustand
  React.useEffect(() => {
    const unsubscribe = subscribeToDiffChanges((pendingDiffs, notebookId) => {
      const newDiffs = Array.from(pendingDiffs.values());
      setCurrentDiffs(newDiffs);

      // Check if all diffs are resolved
      if (newDiffs.length > 0) {
        const allDecided = newDiffs.every(
          diff =>
            diff.userDecision === 'approved' ||
            diff.userDecision === 'rejected' ||
            diff.userDecision === 'run' ||
            diff.approved === true ||
            diff.approved === false
        );
        setAllDiffsResolved(allDecided);
      } else {
        setAllDiffsResolved(false);
      }
    });

    return () => unsubscribe();
  }, []);

  // Also listen for changes in the passed diffs prop for backwards compatibility
  React.useEffect(() => {
    if (diffs && diffs.length > 0) {
      setCurrentDiffs(diffs);
      // Check if all diffs have decisions (approved, rejected, or run)
      const allDecided = diffs.every(
        diff =>
          diff.userDecision === 'approved' ||
          diff.userDecision === 'rejected' ||
          diff.userDecision === 'run' ||
          diff.approved === true ||
          diff.approved === false
      );
      setAllDiffsResolved(allDecided);
    } else if (diffs && diffs.length === 0) {
      setCurrentDiffs([]);
      setAllDiffsResolved(false);
    }
  }, [diffs]);

  // Set up keyboard handler for cmd+enter / ctrl+enter
  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check for Cmd+Enter (macOS) or Ctrl+Enter (Windows/Linux)
      if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
        // Only proceed if the LLM state display is visible
        if (!isVisible) {
          return;
        }

        // For USING_TOOL state (Run/Reject buttons)
        if (state === LLMDisplayState.USING_TOOL && runButtonRef.current) {
          console.log(
            '[LLMStateContent] Cmd+Enter pressed, clicking Run button'
          );
          event.preventDefault();
          event.stopPropagation();
          runButtonRef.current.click();
          return;
        }

        // For DIFF state (Run All/Approve All button)
        if (
          state === LLMDisplayState.DIFF &&
          runAllButtonRef.current &&
          !allDiffsResolved
        ) {
          console.log(
            '[LLMStateContent] Cmd+Enter pressed, clicking Run/Approve All button'
          );
          event.preventDefault();
          event.stopPropagation();
          runAllButtonRef.current.click();
          return;
        }

        // For RUN_KERNEL state (Run all cells button)
        if (state === LLMDisplayState.RUN_KERNEL && runButtonRef.current) {
          console.log(
            '[LLMStateContent] Cmd+Enter pressed, clicking Run all cells button'
          );
          event.preventDefault();
          event.stopPropagation();
          runButtonRef.current.click();
          return;
        }
      }
    };

    // Add keyboard event listener
    document.addEventListener('keydown', handleKeyDown);

    // Cleanup
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isVisible, state, allDiffsResolved]);

  // Helper function to calculate total additions and deletions
  const calculateTotals = (diffs: IPendingDiff[]) => {
    let totalAdded = 0;
    let totalRemoved = 0;

    diffs.forEach(diff => {
      const oldLines = diff.originalContent?.split('\n') || [];
      const oldLinesCount = oldLines.length;
      const newLines = diff.newContent?.split('\n') || [];
      const newLinesCount = newLines.length;

      if (diff.type === 'add') {
        totalAdded += newLinesCount;
      } else if (diff.type === 'remove') {
        totalRemoved += oldLinesCount;
      } else if (diff.type === 'edit') {
        const diffLines = NotebookDiffTools.calculateDiff(
          diff.originalContent || '',
          diff.newContent || ''
        );
        totalAdded += diffLines.filter(line => line.type === 'added').length;
        totalRemoved += diffLines.filter(
          line => line.type === 'removed'
        ).length;
      }
    });

    return { totalAdded, totalRemoved };
  };

  // Use currentDiffs for display instead of the prop diffs
  const displayDiffs = currentDiffs.length > 0 ? currentDiffs : diffs || [];

  // Check if any diffs are runnable (add/edit type) - remove diffs can't be "run"
  const hasRunnableDiffs = displayDiffs.some(
    diff => diff.type === 'add' || diff.type === 'edit'
  );

  // Hide if in demo mode and not authenticated
  if (shouldHideForDemoMode) {
    return null;
  }

  if (!isVisible) {
    return null;
  }

  // Idle state - don't show anything
  if (state === LLMDisplayState.IDLE) {
    return null;
  }

  // Generating state - show thinking indicator
  if (state === LLMDisplayState.GENERATING) {
    // Default text fallback - never show empty while SignalPilot is active
    const displayText = text || 'SignalPilot is thinking...';

    return (
      <div
        className="sage-ai-llm-state-display sage-ai-generating"
        style={{ display: 'flex' }}
      >
        <div className="sage-ai-llm-state-content">
          {waitingForUser && <div className="sage-ai-waiting-for-user" />}
          {!waitingForUser && <div className="sage-ai-blob-loader" />}
          <span className="sage-ai-llm-state-text">{displayText}</span>
        </div>

        {!waitingForUser && (
          <button
            className="sage-ai-llm-state-stop-button"
            onClick={() => {
              useChatboxStore.getState().cancelMessage();
            }}
            title="Stop generation"
          >
            Stop
          </button>
        )}
      </div>
    );
  }

  // Using tool state - show tool usage indicator
  if (state === LLMDisplayState.USING_TOOL) {
    const toolIcon = toolName ? getToolIcon(toolName) : null;
    let toolMessage = toolName
      ? getToolDisplayMessage(toolName)
      : text || 'Using tool...';

    // Check if this is the notebook-run_cell tool that needs confirmation
    const isRunCellTool = toolName === 'notebook-run_cell';

    if (isRunCellTool) {
      toolMessage = 'Waiting to run cell...';
    }
    const isTerminalCommand = toolName === 'terminal-execute_command';
    if (isTerminalCommand) {
      toolMessage = 'Waiting to run terminal command...';
    }

    return (
      <div
        className="sage-ai-llm-state-display sage-ai-using-tool"
        style={{ display: 'flex' }}
      >
        <div className="sage-ai-llm-state-content">
          {toolIcon ? (
            <div
              className="sage-ai-tool-icon-container"
              dangerouslySetInnerHTML={{ __html: toolIcon }}
            />
          ) : (
            <div className="sage-ai-tool-loader" />
          )}
          <span
            className="sage-ai-llm-state-text"
            dangerouslySetInnerHTML={{ __html: toolMessage }}
          />
        </div>

        <div className="sage-ai-llm-state-buttons">
          {(isRunCellTool || isTerminalCommand) &&
          onRunClick &&
          onRejectClick ? (
            // Show Run/Reject buttons for notebook-run_cell and terminal-execute_command tools
            <>
              <button
                className="sage-ai-llm-state-reject-button"
                onClick={onRejectClick}
                title="Reject code execution"
              >
                Reject
              </button>
              <button
                ref={runButtonRef}
                className="sage-ai-llm-state-run-button"
                onClick={onRunClick}
                title="Run code (Cmd/Ctrl + Enter)"
              >
                Run
              </button>
            </>
          ) : (
            // Show Stop button for other tools
            <button
              className="sage-ai-llm-state-stop-button"
              onClick={() => {
                useChatboxStore.getState().cancelMessage();
              }}
              title="Stop tool execution"
            >
              Stop
            </button>
          )}
        </div>
      </div>
    );
  }

  // Diff state - show diff review interface
  if (
    state === LLMDisplayState.DIFF &&
    displayDiffs &&
    displayDiffs.length > 0
  ) {
    const { totalAdded, totalRemoved } = calculateTotals(displayDiffs);

    return (
      <div className="sage-ai-llm-state-display sage-ai-diff-state">
        <div
          className="sage-ai-diff-summary-bar"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="sage-ai-diff-summary-info">
            <span className="sage-ai-diff-icon">
              {!isExpanded ? (
                <MENU_ICON.react className="sage-ai-diff-menu-icon" />
              ) : (
                <MENU_CLOSE_ICON.react className="sage-ai-diff-menu-icon" />
              )}
            </span>
            <span className="sage-ai-diff-cell-count">
              {displayDiffs.length} cell{displayDiffs.length !== 1 ? 's' : ''}{' '}
              modified
            </span>
            <p className="sage-ai-diff-cell-count-info">
              {totalAdded > 0 && (
                <span className="sage-ai-diff-added-count">+{totalAdded}</span>
              )}
              {totalRemoved > 0 && (
                <span className="sage-ai-diff-removed-count">
                  -{totalRemoved}
                </span>
              )}
            </p>
          </div>
          <div className="sage-ai-diff-summary-actions">
            {!allDiffsResolved && (
              <>
                <button
                  className={`sage-ai-diff-btn sage-ai-diff-reject-all ${isRejectAllLoading ? 'sage-ai-btn-loading' : ''}`}
                  disabled={isAnyActionLoading}
                  onClick={async e => {
                    e.stopPropagation();
                    setRejectAllLoading(true);
                    try {
                      // Reject all diffs using diffStore
                      const { updateDiffApproval } = useDiffStore.getState();
                      for (const diff of displayDiffs) {
                        updateDiffApproval(diff.cellId, false, diff.notebookId);
                      }
                      // Also trigger the dialog action if needed
                      await getNotebookDiffManager().diffApprovalDialog.rejectAll();
                      setAllDiffsResolved(true);
                    } finally {
                      setRejectAllLoading(false);
                    }
                  }}
                  title={`Reject${diffs && diffs.length > 1 ? ' all' : ''} change${diffs && diffs.length > 1 ? 's' : ''}`}
                >
                  {isRejectAllLoading && (
                    <span className="sage-ai-btn-spinner" />
                  )}
                  <span>
                    {diffs && diffs.length > 1 ? 'Reject All' : 'Reject'}
                  </span>
                </button>
                <button
                  ref={runAllButtonRef}
                  className={`sage-ai-diff-btn sage-ai-diff-approve-all ${isRunAllLoading ? 'sage-ai-btn-loading' : ''}`}
                  disabled={isAnyActionLoading}
                  onClick={async e => {
                    e.stopPropagation();
                    setRunAllLoading(true);
                    try {
                      // Only run cells if there are runnable diffs (add/edit), otherwise just approve
                      if (isRunContext && hasRunnableDiffs) {
                        for (const diff of displayDiffs) {
                          if (!diff.userDecision) {
                            await getNotebookDiffManager().diffApprovalDialog.runCell(
                              diff.cellId
                            );
                          }
                        }
                      } else {
                        await getNotebookDiffManager().diffApprovalDialog.approveAll();
                      }
                      setAllDiffsResolved(true);
                    } finally {
                      setRunAllLoading(false);
                    }
                  }}
                  title={
                    isRunContext && hasRunnableDiffs
                      ? `Run${diffs && diffs.length > 1 ? ' all' : ''} change${diffs && diffs.length > 1 ? 's' : ''} (Cmd/Ctrl + Enter)`
                      : `Approve${diffs && diffs.length > 1 ? ' all' : ''} change${diffs && diffs.length > 1 ? 's' : ''} (Cmd/Ctrl + Enter)`
                  }
                >
                  {isRunAllLoading && <span className="sage-ai-btn-spinner" />}
                  <span>
                    {isRunContext && hasRunnableDiffs
                      ? `${diffs && diffs.length > 1 ? 'Run All' : 'Run'}`
                      : `${diffs && diffs.length > 1 ? 'Approve All' : 'Approve'}`}
                  </span>
                </button>
              </>
            )}
          </div>
        </div>
        {isExpanded && (
          <div className="sage-ai-diff-list">
            {displayDiffs.map((diff, index) => (
              <DiffItem
                key={`${diff.cellId}-${index}`}
                diff={diff}
                showActionsOnHover={true}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  if (state === LLMDisplayState.RUN_KERNEL) {
    return (
      <div className="sage-ai-llm-state-display sage-ai-run-kernel">
        <div className="sage-ai-llm-state-content">
          <WARNING_ICON.react className="sage-ai-llm-state-warning-icon" />
          <span className="sage-ai-llm-state-text">
            Kernel potentially outdated.
          </span>
        </div>
        <button
          ref={runButtonRef}
          className="sage-ai-llm-state-run-button"
          onClick={() => {
            // Access conversationService through chatbox store
            const conversationService =
              useChatboxStore.getState().services.conversationService;
            if (conversationService?.runAllCellsAfterRestore) {
              void conversationService.runAllCellsAfterRestore();
            }
          }}
          title="The kernel might be outdated due to restoring to a checkpoint (Cmd/Ctrl + Enter)"
        >
          Run all cells
        </button>
      </div>
    );
  }

  return null;
}

/**
 * Pure React component for LLM State Display that uses Zustand store.
 * This is the new preferred way to use LLMStateDisplay.
 * Just mount this component and control it via useLLMStateStore actions.
 */
export function LLMStateDisplayComponent(): JSX.Element {
  const isVisible = useLLMStateStore(state => state.isVisible);
  const displayState = useLLMStateStore(state => state.state);
  const diffs = useLLMStateStore(state => state.diffs);

  // Check if demo control panel is visible - hide LLM state when it is
  const isDemoControlVisible = useDemoControlStore(selectDemoControlVisible);

  // Determine if we should add hidden class
  const shouldHide =
    isDemoControlVisible ||
    !isVisible ||
    displayState === LLMDisplayState.IDLE ||
    (displayState === LLMDisplayState.DIFF && (!diffs || diffs.length === 0));

  return (
    <div
      className={`sage-ai-llm-state-widget ${shouldHide ? 'hidden' : ''}`}
      style={{ display: isDemoControlVisible ? 'none' : undefined }}
    >
      <LLMStateContent
        useStore={true}
        isVisible={true}
        state={LLMDisplayState.IDLE}
        text=""
      />
    </div>
  );
}
