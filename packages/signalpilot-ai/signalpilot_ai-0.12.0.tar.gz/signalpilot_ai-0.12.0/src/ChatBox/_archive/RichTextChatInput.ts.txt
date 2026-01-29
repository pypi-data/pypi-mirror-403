import { IMentionContext } from './ChatContextMenu/ChatContextMenu';

/**
 * A rich text input component that supports colored @ mentions
 */
export class RichTextChatInput {
  private element!: HTMLDivElement;
  private wrapperElement!: HTMLDivElement;
  private placeholder: string = '';
  private activeContexts: Map<string, IMentionContext> = new Map();
  private availableContextsLookup:
    | ((name: string) => IMentionContext | undefined)
    | null = null;
  private onMentionResolved: ((context: IMentionContext) => void) | null = null;
  private resolvedContextIds: Set<string> = new Set();

  constructor(placeholder: string = '') {
    this.placeholder = placeholder;
    this.createElement();
  }

  private createElement(): void {
    // Create the wrapper div for the gradient border
    this.wrapperElement = document.createElement('div');
    this.wrapperElement.className = 'sage-ai-rich-chat-input-wrapper';

    // Create the actual input element
    this.element = document.createElement('div');
    this.element.className = 'sage-ai-rich-chat-input';
    this.element.contentEditable = 'true';
    this.element.setAttribute('role', 'textbox');
    this.element.setAttribute('aria-multiline', 'true');
    this.element.setAttribute('data-placeholder', this.placeholder);

    // Add the input element to the wrapper
    this.wrapperElement.appendChild(this.element);

    // Add initial placeholder styling
    this.updatePlaceholder();

    // Handle paste events to convert to plain text
    this.element.addEventListener('paste', this.handlePaste.bind(this));

    // Handle input to update placeholder and format mentions
    this.element.addEventListener('input', this.handleInput.bind(this));

    // Handle focus events to manage placeholder
    this.element.addEventListener('focus', this.handleFocus.bind(this));
    this.element.addEventListener('blur', this.handleBlur.bind(this));
  }

  private handlePaste(event: ClipboardEvent): void {
    event.preventDefault();
    const text = event.clipboardData?.getData('text/plain') || '';
    // Clear resolved IDs so pasted mentions can be re-added to context
    this.resolvedContextIds.clear();
    document.execCommand('insertText', false, text);
  }

  private handleInput(): void {
    this.updatePlaceholder();
    this.formatMentions();
  }

  private handleFocus(): void {
    if (this.isEmpty()) {
      this.element.textContent = '';
    }
  }

  private handleBlur(): void {
    this.updatePlaceholder();
  }

  setPlaceholder(placeholder: string): void {
    this.placeholder = placeholder;
    this.element.setAttribute('data-placeholder', this.placeholder);
  }

  private updatePlaceholder(): void {
    if (this.isEmpty()) {
      if (document.activeElement !== this.element) {
        this.element.classList.add('empty');
      }
    } else {
      this.element.classList.remove('empty');
    }
  }

  private isEmpty(): boolean {
    const text = this.element.textContent || '';
    return text.trim().length === 0;
  }

  /**
   * Format @ mentions with different colors based on context type
   */
  private formatMentions(): void {
    // 1. capture caret position in terms of plain-text offset
    const cursorOffset = this.getSelectionStart();

    const text = this.getPlainText();
    const mentionRegex = /@(?:\{([^}]+)\}|([a-zA-Z0-9_.-]+))/g;
    let match: RegExpExecArray | null;
    let lastIndex = 0;
    let newHTML = '';

    // build newHTML - only highlight mentions that can be resolved
    while ((match = mentionRegex.exec(text)) !== null) {
      const full = match[0];
      const name = match[1] || match[2]!;
      const start = match.index;
      const end = start + full.length;

      newHTML += this.escapeHtml(text.substring(lastIndex, start));

      const ctx = this.findContextByName(name);
      if (ctx) {
        // Only highlight if mention can be resolved to a context
        const cls = this.getContextClass(ctx.type);
        newHTML += `<span class="sage-ai-mention ${cls}" data-mention="${this.escapeHtml(name)}">${this.escapeHtml(full)}</span>`;
        // Notify that a mention was resolved (only once per context to avoid repeated callbacks)
        if (this.onMentionResolved && !this.resolvedContextIds.has(ctx.id)) {
          this.resolvedContextIds.add(ctx.id);
          this.onMentionResolved(ctx);
        }
      } else {
        // Show unresolved mentions with warning styling
        const warningIcon = `<svg class="sage-ai-mention-warning-icon" width="12" height="12" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 5.5V8.5M8 11H8.01M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
        newHTML += `<span class="sage-ai-mention sage-ai-mention-unresolved" data-mention="${this.escapeHtml(name)}" title="Context not found">${warningIcon}${this.escapeHtml(full)}</span>`;
      }

      lastIndex = end;
    }
    newHTML += this.escapeHtml(text.substring(lastIndex));

    // 2. replace innerHTML
    this.element.innerHTML = newHTML;

    // 3. restore caret by plain-text index
    this.setSelectionRange(cursorOffset, cursorOffset);
  }

  private findContextByName(name: string): IMentionContext | undefined {
    // First check active (already selected) contexts
    for (const context of this.activeContexts.values()) {
      // Match by exact name or normalized name (spaces replaced with underscores)
      const normalizedContextName = context.name.replace(/\s+/g, '_');
      if (context.name === name || normalizedContextName === name) {
        return context;
      }
    }
    // If not found in active contexts, try the available contexts lookup
    if (this.availableContextsLookup) {
      return this.availableContextsLookup(name);
    }
    return undefined;
  }

  private getContextClass(type?: string): string {
    switch (type) {
      case 'template':
        return 'sage-ai-mention-template';
      case 'data':
        return 'sage-ai-mention-data';
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

  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Get the plain text content without HTML formatting
   */
  public getPlainText(): string {
    return this.element.textContent || '';
  }

  /**
   * Set the text content
   */
  public setPlainText(text: string): void {
    this.element.textContent = text;
    this.updatePlaceholder();
    this.formatMentions();
  }

  /**
   * Clear the input
   */
  public clear(): void {
    this.element.textContent = '';
    this.resolvedContextIds.clear();
    this.updatePlaceholder();
  }

  /**
   * Focus the input
   */
  public focus(): void {
    this.element.focus();
  }

  /**
   * Get the DOM element (returns the wrapper element)
   */
  public getElement(): HTMLDivElement {
    return this.wrapperElement;
  }

  /**
   * Get the inner input element
   */
  public getInputElement(): HTMLDivElement {
    return this.element;
  }

  /**
   * Add event listener (to the wrapper element)
   */
  public addEventListener(type: string, listener: EventListener): void {
    this.wrapperElement.addEventListener(type, listener);
  }

  /**
   * Remove event listener (from the wrapper element)
   */
  public removeEventListener(type: string, listener: EventListener): void {
    this.wrapperElement.removeEventListener(type, listener);
  }

  /**
   * Add event listener to the input element (not wrapper)
   */
  public addInputEventListener(type: string, listener: EventListener): void {
    this.element.addEventListener(type, listener);
  }

  /**
   * Remove event listener from the input element
   */
  public removeInputEventListener(type: string, listener: EventListener): void {
    this.element.removeEventListener(type, listener);
  }

  /**
   * Get selection start position for cursor operations
   */
  public getSelectionStart(): number {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
      return 0;
    }

    const range = selection.getRangeAt(0);
    const preCaretRange = range.cloneRange();
    preCaretRange.selectNodeContents(this.element);
    preCaretRange.setEnd(range.startContainer, range.startOffset);

    return preCaretRange.toString().length;
  }

  /**
   * Get selection end position for cursor operations
   */
  public getSelectionEnd(): number {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
      return 0;
    }

    const range = selection.getRangeAt(0);
    const preCaretRange = range.cloneRange();
    preCaretRange.selectNodeContents(this.element);
    preCaretRange.setEnd(range.endContainer, range.endOffset);

    return preCaretRange.toString().length;
  }

  /**
   * Set cursor position
   */
  public setSelectionRange(start: number, end: number): void {
    const selection = window.getSelection();
    if (!selection) {
      return;
    }

    const range = this.createRangeFromOffsets(start, end);
    if (range) {
      selection.removeAllRanges();
      selection.addRange(range);
    }
  }

  private createRangeFromOffsets(
    startOffset: number,
    endOffset: number
  ): Range | null {
    const walker = document.createTreeWalker(
      this.element,
      NodeFilter.SHOW_TEXT
    );

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
   * Update active contexts for mention formatting
   */
  public setActiveContexts(contexts: Map<string, IMentionContext>): void {
    this.activeContexts = contexts;
    this.formatMentions();
  }

  /**
   * Set callback for when a mention is resolved during formatting (e.g., on paste)
   */
  public setOnMentionResolved(
    callback: ((context: IMentionContext) => void) | null
  ): void {
    this.onMentionResolved = callback;
  }

  /**
   * Set a lookup function for finding available contexts by name
   * This is used to resolve mentions when pasting text
   */
  public setAvailableContextsLookup(
    lookup: ((name: string) => IMentionContext | undefined) | null
  ): void {
    this.availableContextsLookup = lookup;
  }

  /**
   * Clear a resolved context ID so it can be re-added (e.g., after removal)
   */
  public clearResolvedContext(contextId: string): void {
    this.resolvedContextIds.delete(contextId);
  }

  /**
   * Get computed style height for auto-resize functionality
   */
  public getScrollHeight(): number {
    return this.element.scrollHeight;
  }

  /**
   * Set height for auto-resize functionality
   */
  public setHeight(height: string): void {
    // this.element.style.height = height;
  }

  /**
   * Set overflow style
   */
  public setOverflowY(overflow: string): void {
    this.element.style.overflowY = overflow;
  }

  /**
   * Set wrapper style properties
   */
  public setWrapperStyle(property: string, value: string): void {
    (this.wrapperElement.style as any)[property] = value;
  }
}
