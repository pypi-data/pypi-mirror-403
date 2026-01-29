/**
 * ContextRow Component
 *
 * Displays the context row in the chat input area:
 * - "Add Context" button with @ icon
 * - List of active context items (cells and mention contexts)
 * - Remove functionality for each context item
 *
 * Both cell contexts and mention contexts are received as props from the parent.
 * The parent (ChatInputManager) gets mention contexts from ChatMessages.getMentionContexts()
 * which contains the user-selected contexts, NOT from the contextStore (which contains
 * available contexts loaded by ContextCacheService).
 *
 * Context items are colored based on type:
 * - snippets: purple
 * - data/database: blue
 * - variable: green
 * - cell: orange
 * - default: gray
 */
import React, { useCallback, useMemo } from 'react';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface CellContext {
  cellId: string;
  content?: string;
}

export interface ContextRowProps {
  /** Cell contexts from notebook */
  cellContexts: CellContext[];
  /** Mention contexts from ChatMessages (user-selected contexts) */
  mentionContexts: IMentionContext[];
  /** Callback when "Add Context" button is clicked */
  onAddContext: () => void;
  /** Callback when a mention context is removed */
  onRemoveMentionContext: (contextId: string, contextName: string) => void;
  /** Callback when a cell context is removed */
  onRemoveCellContext: (cellId: string) => void;
  /** Additional CSS class */
  className?: string;
}

// ═══════════════════════════════════════════════════════════════
// ICONS
// ═══════════════════════════════════════════════════════════════

/** @ icon for the Add Context button */
const AtIcon: React.FC = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="12"
    height="13"
    viewBox="0 0 12 13"
    fill="none"
  >
    <g clipPath="url(#clip0_590_6942)">
      <path
        d="M8.00001 4.5V7C8.00001 7.39783 8.15804 7.77936 8.43935 8.06066C8.72065 8.34197 9.10218 8.5 9.50001 8.5C9.89783 8.5 10.2794 8.34197 10.5607 8.06066C10.842 7.77936 11 7.39783 11 7V6.5C11 5.37366 10.6197 4.2803 9.92071 3.39709C9.22172 2.51387 8.24499 1.89254 7.14877 1.63376C6.05255 1.37498 4.90107 1.49391 3.88089 1.97128C2.86071 2.44865 2.03159 3.2565 1.52787 4.26394C1.02415 5.27137 0.875344 6.41937 1.10556 7.52194C1.33577 8.62452 1.93151 9.61706 2.79627 10.3388C3.66102 11.0605 4.74413 11.4691 5.87009 11.4983C6.99606 11.5276 8.09893 11.1758 9.00001 10.5M8 6.5C8 7.60457 7.10457 8.5 6 8.5C4.89543 8.5 4 7.60457 4 6.5C4 5.39543 4.89543 4.5 6 4.5C7.10457 4.5 8 5.39543 8 6.5Z"
        stroke="#949494"
        strokeWidth="1.3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </g>
    <defs>
      <clipPath id="clip0_590_6942">
        <rect
          width="12"
          height="12"
          fill="white"
          transform="translate(0 0.5)"
        />
      </clipPath>
    </defs>
  </svg>
);

// ═══════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════

/**
 * Get background color based on context type
 */
function getContextBackgroundColor(type: IMentionContext['type']): string {
  switch (type) {
    case 'snippets':
      return 'rgba(156, 39, 176, 0.2)'; // purple
    case 'data':
    case 'database':
      return 'rgba(33, 150, 243, 0.2)'; // blue
    case 'variable':
      return 'rgba(76, 175, 80, 0.2)'; // green
    case 'cell':
      return 'rgba(255, 152, 0, 0.2)'; // orange
    case 'directory':
    case 'table':
    default:
      return '#4a5568'; // gray
  }
}

// ═══════════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ═══════════════════════════════════════════════════════════════

interface ContextItemProps {
  id: string;
  name: string;
  title: string;
  backgroundColor?: string;
  textColor?: string;
  onRemove: () => void;
}

/** Individual context item with delete button */
const ContextItem: React.FC<ContextItemProps> = ({
  name,
  title,
  backgroundColor,
  textColor,
  onRemove
}) => {
  const handleRemove = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onRemove();
    },
    [onRemove]
  );

  const style = backgroundColor
    ? { backgroundColor, color: textColor || 'var(--jp-ui-font-color0)' }
    : undefined;

  return (
    <div
      className="sage-ai-context-cell-box-inline"
      title={title}
      style={style}
    >
      <span
        className="sage-ai-context-cell-delete"
        title="Remove from context"
        onClick={handleRemove}
      >
        ×
      </span>
      <span>{name}</span>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════

export const ContextRow: React.FC<ContextRowProps> = ({
  cellContexts,
  mentionContexts,
  onAddContext,
  onRemoveMentionContext,
  onRemoveCellContext,
  className = ''
}) => {
  // Calculate total context items
  const totalContextItems = cellContexts.length + mentionContexts.length;
  const hasContexts = totalContextItems > 0;

  // Handle "Add Context" button click
  const handleAddContextClick = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      onAddContext();
    },
    [onAddContext]
  );

  // Build class names for the row - always visible
  const rowClassName = useMemo(() => {
    const classes = ['sage-ai-context-row'];
    if (className) {
      classes.push(className);
    }
    return classes.join(' ');
  }, [className]);

  // Build class names for the display container
  // The container is always present, items are conditionally rendered inside
  const displayClassName = 'sage-ai-context-display-inline';

  return (
    <div className={rowClassName}>
      {/* Add Context Button */}
      <button
        className="sage-ai-add-context-button"
        type="button"
        title="Add context"
        onClick={handleAddContextClick}
      >
        <span className="sage-ai-at-icon">
          <AtIcon />
        </span>
        <p className="sage-ai-context-text">Add Context</p>
      </button>

      {/* Context Display */}
      <div className={displayClassName}>
        {hasContexts && (
          <div className="sage-ai-context-items-inline">
            {/* Cell Contexts */}
            {cellContexts.map(cell => (
              <ContextItem
                key={`cell-${cell.cellId}`}
                id={cell.cellId}
                name={cell.cellId}
                title={cell.content || 'Empty cell'}
                onRemove={() => onRemoveCellContext(cell.cellId)}
              />
            ))}

            {/* Mention Contexts */}
            {mentionContexts.map(context => (
              <ContextItem
                key={`mention-${context.id}`}
                id={context.id}
                name={context.name}
                title={
                  context.description ||
                  context.content ||
                  `${context.type}: ${context.name}`
                }
                backgroundColor={getContextBackgroundColor(context.type)}
                textColor="var(--jp-ui-font-color0)"
                onRemove={() =>
                  onRemoveMentionContext(context.id, context.name)
                }
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ContextRow;
