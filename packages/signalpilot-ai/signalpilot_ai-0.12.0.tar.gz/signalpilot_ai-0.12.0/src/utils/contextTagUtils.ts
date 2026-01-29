import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';
import { useContextStore } from '../stores/contextStore';

/**
 * Utility functions for parsing and generating context tags in messages
 */

/** Warning icon SVG for unresolved mentions */
const WARNING_ICON_SVG = `<svg class="sage-ai-mention-warning-icon" width="12" height="12" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 5.5V8.5M8 11H8.01M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

export interface IParsedContextTag {
  contextId: string;
  type:
    | 'SNIPPET_CONTEXT'
    | 'DATA_CONTEXT'
    | 'VARIABLE_CONTEXT'
    | 'CELL_CONTEXT'
    | 'TABLE_CONTEXT';
  fullMatch: string;
  startIndex: number;
  endIndex: number;
}

/**
 * Regular expression to match context tags
 * Matches: <DATA_CONTEXT>#{context_id}</DATA_CONTEXT>, <SNIPPET_CONTEXT>#{context_id}</SNIPPET_CONTEXT>, etc.
 */
const CONTEXT_TAG_REGEX =
  /<(SNIPPET_CONTEXT|DATA_CONTEXT|DATABASE_CONTEXT|VARIABLE_CONTEXT|CELL_CONTEXT|TABLE_CONTEXT)>\s*#\{([^}]+)\}\s*<\/\1>/g;

/**
 * Parse context tags from a message string
 */
export function parseContextTags(message: string): IParsedContextTag[] {
  const tags: IParsedContextTag[] = [];
  let match: RegExpExecArray | null;

  // Reset regex lastIndex to ensure we start from the beginning
  CONTEXT_TAG_REGEX.lastIndex = 0;

  while ((match = CONTEXT_TAG_REGEX.exec(message)) !== null) {
    tags.push({
      contextId: match[2],
      type: match[1] as IParsedContextTag['type'],
      fullMatch: match[0],
      startIndex: match.index,
      endIndex: match.index + match[0].length
    });
  }

  return tags;
}

/**
 * Generate a context tag for a given context item
 */
export function generateContextTag(context: IMentionContext): string {
  const tagType = getContextTagType(context.type);
  return `<${tagType}>#{${context.id}}</${tagType}>`;
}

/**
 * Map context type to tag type
 */
function getContextTagType(contextType: string): string {
  switch (contextType) {
    case 'snippets':
      return 'SNIPPET_CONTEXT';
    case 'data':
      return 'DATA_CONTEXT';
    case 'database':
      return 'DATABASE_CONTEXT';
    case 'variable':
      return 'VARIABLE_CONTEXT';
    case 'cell':
      return 'CELL_CONTEXT';
    case 'table':
      return 'TABLE_CONTEXT';
    default:
      return 'SNIPPET_CONTEXT'; // Default fallback
  }
}

/**
 * Replace context tags in a message with styled mentions
 * Returns HTML string with styled mentions
 */
export function renderContextTagsAsStyled(message: string): string {
  const contextItems = useContextStore.getState().getCurrentContextItems();

  return message.replace(CONTEXT_TAG_REGEX, (fullMatch, tagType, contextId) => {
    const context = contextItems.get(contextId);

    // Always render with proper colors based on tag type, regardless of validity
    const cssClass = getContextCssClassFromTagType(tagType);

    if (context) {
      // If context exists, use its name and description
      const displayName = context.name.replace(/\s+/g, '_');
      return `<span class="sage-ai-mention ${cssClass}" title="${context.description || context.name}" data-context-id="${contextId}">@${displayName}</span>`;
    } else {
      // If context not found, still render with proper colors but use contextId as display name
      return `<span class="sage-ai-mention ${cssClass}" title="Context ID: ${contextId}" data-context-id="${contextId}">@${contextId}</span>`;
    }
  });
}

/**
 * Render unresolved @mentions with warning icon
 * @param text Text that may contain unresolved @mentions (should be pre-escaped HTML)
 * @returns HTML string with styled unresolved mentions
 */
export function renderUnresolvedMentions(text: string): string {
  // Match @mentions (both @name and @{name with spaces})
  const mentionRegex = /@(?:\{([^}]+)\}|([a-zA-Z0-9_.-]+))/g;

  return text.replace(mentionRegex, (fullMatch, bracketedName, simpleName) => {
    const mentionName = bracketedName || simpleName;
    return `<span class="sage-ai-mention sage-ai-mention-unresolved" title="Context not found: @${mentionName}">${WARNING_ICON_SVG}@${mentionName}</span>`;
  });
}

/**
 * Get CSS class directly from tag type (e.g., CELL_CONTEXT -> sage-ai-mention-cell)
 */
function getContextCssClassFromTagType(tagType: string): string {
  switch (tagType) {
    case 'SNIPPET_CONTEXT':
      return 'sage-ai-mention-template';
    case 'DATA_CONTEXT':
      return 'sage-ai-mention-data';
    case 'DATABASE_CONTEXT':
      return 'sage-ai-mention-database';
    case 'VARIABLE_CONTEXT':
      return 'sage-ai-mention-variable';
    case 'CELL_CONTEXT':
      return 'sage-ai-mention-cell';
    case 'TABLE_CONTEXT':
      return 'sage-ai-mention-table';
    default:
      return 'sage-ai-mention-default';
  }
}

/**
 * Get tag type from CSS class (reverse mapping)
 */
export function getTagTypeFromCssClass(element: Element): string {
  if (element.classList.contains('sage-ai-mention-template')) {
    return 'SNIPPET_CONTEXT';
  } else if (element.classList.contains('sage-ai-mention-data')) {
    return 'DATA_CONTEXT';
  } else if (element.classList.contains('sage-ai-mention-database')) {
    return 'DATABASE_CONTEXT';
  } else if (element.classList.contains('sage-ai-mention-variable')) {
    return 'VARIABLE_CONTEXT';
  } else if (element.classList.contains('sage-ai-mention-cell')) {
    return 'CELL_CONTEXT';
  } else if (element.classList.contains('sage-ai-mention-table')) {
    return 'TABLE_CONTEXT';
  } else {
    return 'DATA_CONTEXT'; // Default fallback
  }
}

/**
 * Result of converting mentions to context tags
 */
export interface IConvertMentionsResult {
  message: string;
  unresolvedMentions: string[];
}

/**
 * Replace @ mentions in input text with context tags
 * This is used when sending messages to convert @mentions to context tags
 * Returns both the processed message and a list of unresolved mentions
 */
export function convertMentionsToContextTags(
  message: string,
  activeContexts: Map<string, IMentionContext>
): IConvertMentionsResult {
  // Match @mentions (both @name and @{name with spaces})
  const mentionRegex = /@(?:\{([^}]+)\}|([a-zA-Z0-9_.-]+))/g;
  const unresolvedMentions: string[] = [];

  const processedMessage = message.replace(
    mentionRegex,
    (fullMatch, bracketedName, simpleName) => {
      const mentionName = bracketedName || simpleName;
      // Also create a version with underscores converted to spaces for matching
      const mentionNameWithSpaces = mentionName.replace(/_/g, ' ');

      // Find context by name
      for (const [, context] of activeContexts.entries()) {
        const normalizedContextName = context.name.replace(/\s+/g, '_');
        // Match if:
        // 1. normalizedContextName (spaces->underscores) equals mentionName, OR
        // 2. context.name equals mentionName, OR
        // 3. context.name equals mentionName with underscores converted to spaces
        if (
          normalizedContextName === mentionName ||
          context.name === mentionName ||
          context.name.toLowerCase() === mentionNameWithSpaces.toLowerCase()
        ) {
          return generateContextTag(context);
        }
      }

      // If no context found, track it and leave as is
      unresolvedMentions.push(mentionName);
      return fullMatch;
    }
  );

  return {
    message: processedMessage,
    unresolvedMentions
  };
}

/**
 * Strip context tags from message, leaving just the text content
 * Useful for getting clean text for processing
 */
export function stripContextTags(message: string): string {
  return message.replace(CONTEXT_TAG_REGEX, '');
}

/**
 * Extract context IDs from a message
 */
export function extractContextIds(message: string): string[] {
  const tags = parseContextTags(message);
  return tags.map(tag => tag.contextId);
}

/**
 * Replace context tags with plain text mentions for display in plain text contexts
 */
export function renderContextTagsAsPlainText(message: string): string {
  const contextItems = useContextStore.getState().getCurrentContextItems();

  return message.replace(CONTEXT_TAG_REGEX, (fullMatch, tagType, contextId) => {
    const context = contextItems.get(contextId);

    if (!context) {
      return `@${contextId}`;
    }

    return `@${context.name.replace(/\s+/g, '_')}`;
  });
}
