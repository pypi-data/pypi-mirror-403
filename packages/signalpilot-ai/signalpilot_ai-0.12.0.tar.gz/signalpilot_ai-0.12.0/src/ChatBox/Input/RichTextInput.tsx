/**
 * RichTextInput Component
 *
 * A React contentEditable input with colored @ mention formatting.
 * Handles cursor position preservation when formatting mentions.
 *
 * Features:
 * - ContentEditable div with gradient border wrapper
 * - Placeholder text when empty
 * - @ mention formatting with type-based colors
 * - Cursor position preservation during formatting
 * - Paste handling (converts to plain text)
 * - Imperative API via ref for parent control
 * - Zustand store integration for state sharing
 *
 * Note: ContentEditable requires direct DOM manipulation for cursor handling.
 * DOM helpers are separated into contentEditableHelpers.ts for clarity.
 */
import React, {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState
} from 'react';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';
import {
  escapeHtml,
  getSelectionEndOffset,
  getSelectionStartOffset,
  insertTextAtCursor,
  setSelectionFromOffsets,
  updateHTMLPreservingCursor
} from './contentEditableHelpers';
import { useRichTextInputStore } from '@/stores/richTextInputStore';
import { useContextStore } from '@/stores/contextStore';
import { useContextCacheStore } from '@/stores/contextCacheStore';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface RichTextInputProps {
  /** Placeholder text shown when input is empty */
  placeholder?: string;
  /** Active contexts for mention color formatting */
  activeContexts?: Map<string, IMentionContext>;
  /** Callback when input content changes */
  onInput?: (event: React.FormEvent<HTMLDivElement>) => void;
  /** Callback when key is pressed */
  onKeyDown?: (event: React.KeyboardEvent<HTMLDivElement>) => void;
  /** Callback when input receives focus */
  onFocus?: (event: React.FocusEvent<HTMLDivElement>) => void;
  /** Callback when input loses focus */
  onBlur?: (event: React.FocusEvent<HTMLDivElement>) => void;
  /** Callback when content is pasted */
  onPaste?: (event: React.ClipboardEvent<HTMLDivElement>) => void;
  /** Callback when a context is detected in pasted text */
  onPastedContext?: (context: IMentionContext) => void;
  /** Additional CSS class for the wrapper */
  className?: string;
}

/** Imperative methods exposed via ref */
export interface RichTextInputRef {
  /** Get plain text content without HTML formatting */
  getPlainText: () => string;
  /** Set plain text content */
  setPlainText: (text: string) => void;
  /** Clear all content */
  clear: () => void;
  /** Focus the input */
  focus: () => void;
  /** Get cursor position as plain text offset */
  getSelectionStart: () => number;
  /** Get selection end position */
  getSelectionEnd: () => number;
  /** Set cursor position */
  setSelectionRange: (start: number, end: number) => void;
  /** Update active contexts for mention formatting */
  setActiveContexts: (contexts: Map<string, IMentionContext>) => void;
  /** Get the scroll height for auto-resize */
  getScrollHeight: () => number;
  /** Set overflow style */
  setOverflowY: (overflow: string) => void;
  /** Get the inner input element */
  getInputElement: () => HTMLDivElement | null;
  /** Get the wrapper element */
  getElement: () => HTMLDivElement | null;
  /** Insert text at current cursor position */
  insertText: (text: string) => void;
}

// ═══════════════════════════════════════════════════════════════
// MENTION FORMATTING HELPERS (React-agnostic)
// ═══════════════════════════════════════════════════════════════

/** Warning icon SVG for unresolved mentions */
const WARNING_ICON_SVG = `<svg class="sage-ai-mention-warning-icon" width="12" height="12" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 5.5V8.5M8 11H8.01M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

/** Get CSS class for mention based on context type */
function getContextClass(type?: string): string {
  switch (type) {
    case 'template':
    case 'snippets':
      return 'sage-ai-mention-template';
    case 'data':
      return 'sage-ai-mention-data';
    case 'database':
      return 'sage-ai-mention-database';
    case 'variable':
      return 'sage-ai-mention-variable';
    case 'cell':
      return 'sage-ai-mention-cell';
    case 'table':
      return 'sage-ai-mention-table';
    default:
      return 'sage-ai-mention-default';
  }
}

/** Find context by name in the active contexts map */
function findContextByName(
  name: string,
  contexts: Map<string, IMentionContext>
): IMentionContext | undefined {
  // Also create a version with underscores converted to spaces for matching
  // This allows @patreon_databricks to match "patreon databricks"
  const nameWithSpaces = name.replace(/_/g, ' ');

  for (const context of contexts.values()) {
    // Match by exact name or normalized name (spaces replaced with underscores)
    const normalizedContextName = context.name.replace(/\s+/g, '_');
    if (
      context.name === name ||
      normalizedContextName === name ||
      context.name.toLowerCase() === nameWithSpaces.toLowerCase()
    ) {
      return context;
    }
  }
  return undefined;
}

/** Find context by name in the context cache (all available contexts) */
function findContextInCache(name: string): IMentionContext | undefined {
  const cache = useContextCacheStore.getState().getCachedContexts();
  const nameWithSpaces = name.replace(/_/g, ' ');

  // Search through all categories in the cache
  for (const contexts of cache.values()) {
    for (const context of contexts) {
      const normalizedContextName = context.name.replace(/\s+/g, '_');
      if (
        context.name === name ||
        context.id === name ||
        normalizedContextName === name ||
        context.name.toLowerCase() === nameWithSpaces.toLowerCase()
      ) {
        return context;
      }
    }
  }
  return undefined;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export const RichTextInput = forwardRef<RichTextInputRef, RichTextInputProps>(
  (
    {
      placeholder = '',
      activeContexts: initialContexts,
      onInput,
      onKeyDown,
      onFocus,
      onBlur,
      onPaste,
      onPastedContext,
      className = ''
    },
    ref
  ) => {
    const wrapperRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLDivElement>(null);
    const [isEmpty, setIsEmpty] = useState(true);
    const [isFocused, setIsFocused] = useState(false);
    const activeContextsRef = useRef<Map<string, IMentionContext>>(
      initialContexts || new Map()
    );

    // ═══════════════════════════════════════════════════════════════
    // STORE INTEGRATION
    // ═══════════════════════════════════════════════════════════════

    const {
      focusRequested,
      focusCompleted,
      pendingClear,
      clearCompleted,
      pendingSetText,
      setTextCompleted,
      pendingTextInsert,
      insertCompleted,
      updateFromDOM,
      setIsFocused: setStoreFocused,
      activeContexts: storeContexts
    } = useRichTextInputStore();

    // Update contexts ref when prop or store changes
    useEffect(() => {
      if (initialContexts) {
        activeContextsRef.current = initialContexts;
      } else if (storeContexts && storeContexts.size > 0) {
        activeContextsRef.current = storeContexts;
      }
    }, [initialContexts, storeContexts]);


    /**
     * Format @ mentions with colored spans.
     * Preserves cursor position during formatting.
     * Uses contentEditableHelpers for DOM operations.
     * Checks both active contexts and context cache for resolved mentions.
     */
    const formatMentions = useCallback(() => {
      const element = inputRef.current;
      if (!element) return;

      // Capture cursor position before formatting
      const cursorOffset = getSelectionStartOffset(element);

      const text = element.textContent || '';
      const mentionRegex = /@(?:\{([^}]+)\}|([a-zA-Z0-9_.-]+))/g;
      let match: RegExpExecArray | null;
      let lastIndex = 0;
      let newHTML = '';

      // Build HTML with mention spans
      while ((match = mentionRegex.exec(text)) !== null) {
        const full = match[0];
        const name = match[1] || match[2]!;
        const start = match.index;
        const end = start + full.length;

        newHTML += escapeHtml(text.substring(lastIndex, start));

        // Try active contexts first, then fall back to cache
        let ctx = findContextByName(name, activeContextsRef.current);
        if (!ctx) {
          ctx = findContextInCache(name);
        }

        if (ctx) {
          // Resolved mention - show with appropriate color
          const cls = getContextClass(ctx.type);
          newHTML += `<span class="sage-ai-mention ${cls}" data-mention="${escapeHtml(name)}">${escapeHtml(full)}</span>`;
        } else {
          // Unresolved mention - show with warning styling and icon
          newHTML += `<span class="sage-ai-mention sage-ai-mention-unresolved" data-mention="${escapeHtml(name)}" title="Context not found">${WARNING_ICON_SVG}${escapeHtml(full)}</span>`;
        }

        lastIndex = end;
      }
      newHTML += escapeHtml(text.substring(lastIndex));

      // Update HTML and restore cursor (uses DOM helper)
      updateHTMLPreservingCursor(element, newHTML, cursorOffset);
    }, []);

    /**
     * Update empty state for placeholder styling
     */
    const updateEmptyState = useCallback(() => {
      const element = inputRef.current;
      if (!element) return;

      const text = element.textContent || '';
      setIsEmpty(text.trim().length === 0);
    }, []);

    // ═══════════════════════════════════════════════════════════════
    // STORE-DRIVEN EFFECTS
    // ═══════════════════════════════════════════════════════════════

    // Handle focus requests from store
    useEffect(() => {
      if (focusRequested && inputRef.current) {
        inputRef.current.focus();
        focusCompleted();
      }
    }, [focusRequested, focusCompleted]);

    // Handle clear requests from store
    useEffect(() => {
      if (pendingClear && inputRef.current) {
        inputRef.current.textContent = '';
        updateEmptyState();
        clearCompleted();
      }
    }, [pendingClear, clearCompleted, updateEmptyState]);

    // Handle setText requests from store
    useEffect(() => {
      if (pendingSetText !== null && inputRef.current) {
        inputRef.current.textContent = pendingSetText;
        updateEmptyState();
        formatMentions();
        setTextCompleted();
      }
    }, [pendingSetText, setTextCompleted, updateEmptyState, formatMentions]);

    // Handle insertText requests from store
    useEffect(() => {
      if (pendingTextInsert && inputRef.current) {
        inputRef.current.focus();
        insertTextAtCursor(pendingTextInsert.text);
        updateEmptyState();
        formatMentions();
        insertCompleted();
      }
    }, [pendingTextInsert, insertCompleted, updateEmptyState, formatMentions]);

    /**
     * Handle input events
     */
    const handleInput = useCallback(
      (event: React.FormEvent<HTMLDivElement>) => {
        updateEmptyState();
        formatMentions();
        // Sync to store
        const text = inputRef.current?.textContent || '';
        updateFromDOM(text);
        onInput?.(event);
      },
      [updateEmptyState, formatMentions, updateFromDOM, onInput]
    );

    /**
     * Handle paste - convert to plain text and add any @mentions to context.
     * Uses insertTextAtCursor from contentEditableHelpers.
     * Looks up mentions in both active contexts AND the context cache (all available contexts).
     * Note: This React handler is disabled - native paste handler is used instead for better contentEditable support.
     */
    const handlePaste = useCallback(
      (event: React.ClipboardEvent<HTMLDivElement>) => {
        event.preventDefault();
        const text = event.clipboardData?.getData('text/plain') || '';

        // Parse pasted text for @mentions and add them to context store
        const mentionRegex = /@(?:\{([^}]+)\}|([a-zA-Z0-9_.-]+))/g;
        let match: RegExpExecArray | null;

        while ((match = mentionRegex.exec(text)) !== null) {
          const name = match[1] || match[2]!;

          // First try active contexts, then fall back to the full cache
          let ctx = findContextByName(name, activeContextsRef.current);
          if (!ctx) {
            ctx = findContextInCache(name);
          }

          if (ctx) {
            // Add context to the store if found
            useContextStore.getState().addContext(ctx);
            // Also add to active contexts ref so formatMentions can find it
            activeContextsRef.current.set(ctx.id, ctx);
          }
        }

        insertTextAtCursor(text);
        // Re-format mentions after paste to apply proper styling
        setTimeout(() => {
          updateEmptyState();
          formatMentions();
        }, 0);
        onPaste?.(event);
      },
      [onPaste, updateEmptyState, formatMentions]
    );

    /**
     * Handle focus - clear placeholder
     */
    const handleFocus = useCallback(
      (event: React.FocusEvent<HTMLDivElement>) => {
        setIsFocused(true);
        setStoreFocused(true);
        if (isEmpty) {
          const element = inputRef.current;
          if (element) {
            element.textContent = '';
          }
        }
        onFocus?.(event);
      },
      [isEmpty, onFocus, setStoreFocused]
    );

    /**
     * Handle blur - restore placeholder
     */
    const handleBlur = useCallback(
      (event: React.FocusEvent<HTMLDivElement>) => {
        setIsFocused(false);
        setStoreFocused(false);
        updateEmptyState();
        onBlur?.(event);
      },
      [updateEmptyState, onBlur, setStoreFocused]
    );

    /**
     * Handle keydown events
     */
    const handleKeyDown = useCallback(
      (event: React.KeyboardEvent<HTMLDivElement>) => {
        onKeyDown?.(event);
      },
      [onKeyDown]
    );

    // Store callback in ref for use in native event listener
    const onPastedContextRef = useRef(onPastedContext);
    useEffect(() => {
      onPastedContextRef.current = onPastedContext;
    }, [onPastedContext]);

    // Native paste event listener (some browsers don't fire React's onPaste properly on contentEditable)
    useEffect(() => {
      const element = inputRef.current;
      if (!element) return;

      const handleNativePaste = (event: ClipboardEvent) => {
        event.preventDefault();
        const text = event.clipboardData?.getData('text/plain') || '';

        // Parse pasted text for @mentions and add them to context store
        const mentionRegex = /@(?:\{([^}]+)\}|([a-zA-Z0-9_.-]+))/g;
        let match: RegExpExecArray | null;

        while ((match = mentionRegex.exec(text)) !== null) {
          const name = match[1] || match[2]!;

          // First try active contexts, then fall back to the full cache
          let ctx = findContextByName(name, activeContextsRef.current);
          if (!ctx) {
            ctx = findContextInCache(name);
          }

          if (ctx) {
            // Notify parent component so it can update messageComponent and context row
            onPastedContextRef.current?.(ctx);
            activeContextsRef.current.set(ctx.id, ctx);
          }
        }

        insertTextAtCursor(text);
        setTimeout(() => {
          updateEmptyState();
          formatMentions();
        }, 0);
      };

      element.addEventListener('paste', handleNativePaste);
      return () => element.removeEventListener('paste', handleNativePaste);
    }, [updateEmptyState, formatMentions]);

    // Expose imperative methods via ref
    useImperativeHandle(
      ref,
      () => ({
        getPlainText: () => inputRef.current?.textContent || '',

        setPlainText: (text: string) => {
          const element = inputRef.current;
          if (element) {
            element.textContent = text;
            updateEmptyState();
            formatMentions();
          }
        },

        clear: () => {
          const element = inputRef.current;
          if (element) {
            element.textContent = '';
            updateEmptyState();
          }
        },

        focus: () => {
          inputRef.current?.focus();
        },

        getSelectionStart: () => {
          const element = inputRef.current;
          return element ? getSelectionStartOffset(element) : 0;
        },

        getSelectionEnd: () => {
          const element = inputRef.current;
          return element ? getSelectionEndOffset(element) : 0;
        },

        setSelectionRange: (start: number, end: number) => {
          const element = inputRef.current;
          if (element) {
            setSelectionFromOffsets(element, start, end);
          }
        },

        setActiveContexts: (contexts: Map<string, IMentionContext>) => {
          activeContextsRef.current = contexts;
          formatMentions();
        },

        getScrollHeight: () => inputRef.current?.scrollHeight || 0,

        setOverflowY: (overflow: string) => {
          const element = inputRef.current;
          if (element) {
            element.style.overflowY = overflow;
          }
        },

        getInputElement: () => inputRef.current,

        getElement: () => wrapperRef.current,

        insertText: (text: string) => {
          inputRef.current?.focus();
          insertTextAtCursor(text);
          updateEmptyState();
          formatMentions();
        }
      }),
      [formatMentions, updateEmptyState]
    );

    // Build class names
    const wrapperClassName =
      `sage-ai-rich-chat-input-wrapper ${className}`.trim();
    const inputClassName =
      `sage-ai-rich-chat-input ${isEmpty && !isFocused ? 'empty' : ''}`.trim();

    return (
      <div ref={wrapperRef} className={wrapperClassName}>
        <div
          ref={inputRef}
          className={inputClassName}
          contentEditable
          role="textbox"
          aria-multiline="true"
          data-placeholder={placeholder}
          onInput={handleInput}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          onBlur={handleBlur}
          /* onPaste handled by native event listener for better contentEditable support */
        />
      </div>
    );
  }
);

RichTextInput.displayName = 'RichTextInput';

export default RichTextInput;
