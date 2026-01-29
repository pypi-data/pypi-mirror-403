/**
 * ContentEditable DOM Helpers
 *
 * This module contains necessary DOM manipulation utilities for contentEditable elements.
 * These operations require direct DOM access because:
 *
 * 1. ContentEditable elements don't work well with React's controlled component pattern
 * 2. Cursor position must be preserved when formatting text (e.g., adding colored mentions)
 * 3. Selection API is only available via direct DOM access
 *
 * These utilities are intentionally separated from React components to make the
 * boundary between React and imperative DOM code clear.
 *
 * @module contentEditableHelpers
 */

// ═══════════════════════════════════════════════════════════════
// HTML UTILITIES
// ═══════════════════════════════════════════════════════════════

/**
 * Escape HTML special characters to prevent XSS.
 * Uses DOM API for reliable escaping.
 */
export function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ═══════════════════════════════════════════════════════════════
// SELECTION / CURSOR UTILITIES
// ═══════════════════════════════════════════════════════════════

/**
 * Get cursor position as plain text offset from the start of the element.
 * Works with contentEditable elements that may contain HTML formatting.
 */
export function getSelectionStartOffset(element: HTMLElement): number {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    return 0;
  }

  const range = selection.getRangeAt(0);
  const preCaretRange = range.cloneRange();
  preCaretRange.selectNodeContents(element);
  preCaretRange.setEnd(range.startContainer, range.startOffset);

  return preCaretRange.toString().length;
}

/**
 * Get selection end position as plain text offset.
 */
export function getSelectionEndOffset(element: HTMLElement): number {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    return 0;
  }

  const range = selection.getRangeAt(0);
  const preCaretRange = range.cloneRange();
  preCaretRange.selectNodeContents(element);
  preCaretRange.setEnd(range.endContainer, range.endOffset);

  return preCaretRange.toString().length;
}

/**
 * Create a DOM Range from plain text offsets.
 * Uses TreeWalker to find the correct text nodes.
 */
export function createRangeFromOffsets(
  element: HTMLElement,
  startOffset: number,
  endOffset: number
): Range | null {
  const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);

  let currentOffset = 0;
  let startNode: Node | null = null;
  let startPos = 0;
  let endNode: Node | null = null;
  let endPos = 0;

  while (walker.nextNode()) {
    const node = walker.currentNode;
    const nodeLength = node.textContent?.length || 0;

    if (!startNode && currentOffset + nodeLength >= startOffset) {
      startNode = node;
      startPos = startOffset - currentOffset;
    }

    if (currentOffset + nodeLength >= endOffset) {
      endNode = node;
      endPos = endOffset - currentOffset;
      break;
    }

    currentOffset += nodeLength;
  }

  if (startNode && endNode) {
    const range = document.createRange();
    range.setStart(
      startNode,
      Math.min(startPos, startNode.textContent?.length || 0)
    );
    range.setEnd(endNode, Math.min(endPos, endNode.textContent?.length || 0));
    return range;
  }

  return null;
}

/**
 * Set cursor/selection position from plain text offsets.
 */
export function setSelectionFromOffsets(
  element: HTMLElement,
  start: number,
  end: number
): void {
  const selection = window.getSelection();
  if (!selection) {
    return;
  }

  const range = createRangeFromOffsets(element, start, end);
  if (range) {
    selection.removeAllRanges();
    selection.addRange(range);
  }
}

// ═══════════════════════════════════════════════════════════════
// CONTENT MANIPULATION
// ═══════════════════════════════════════════════════════════════

/**
 * Insert plain text at current cursor position.
 * Uses execCommand for compatibility with contentEditable undo/redo.
 *
 * Note: execCommand is deprecated but still the most reliable way to
 * insert text in contentEditable while maintaining undo history.
 */
export function insertTextAtCursor(text: string): void {
  document.execCommand('insertText', false, text);
}

/**
 * Update element innerHTML while preserving cursor position.
 * Used for formatting mentions with colored spans.
 *
 * @param element - The contentEditable element
 * @param newHTML - The new HTML content
 * @param cursorOffset - The cursor position (plain text offset) to restore
 */
export function updateHTMLPreservingCursor(
  element: HTMLElement,
  newHTML: string,
  cursorOffset: number
): void {
  element.innerHTML = newHTML;
  setSelectionFromOffsets(element, cursorOffset, cursorOffset);
}
