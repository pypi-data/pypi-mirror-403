/**
 * ContextItem Component
 *
 * Renders a single context item in the mention dropdown with proper SVG icons
 * Matches the original ChatContextMenu styling
 */
import React from 'react';
import { ContextItemProps } from './types';
import { getIconForType } from './Icons';

export const ContextItem: React.FC<ContextItemProps> = ({
  item,
  isActive,
  categoryLabel,
  onClick
}) => {
  const className = `sage-ai-mention-item sage-ai-mention-subcategory${isActive ? ' active' : ''}`;

  // Get the proper icon component for this item type
  const iconType = item.isDirectory ? 'directory' : item.type;
  const IconComponent = getIconForType(iconType);

  return (
    <div
      className={className}
      data-id={item.id}
      data-category={categoryLabel || item.type}
      data-type={item.isDirectory ? 'directory' : item.type}
      onClick={onClick}
    >
      <span className="sage-ai-mention-item-icon">
        <IconComponent />
      </span>
      <div style={{ flex: 1 }}>
        <div className="sage-ai-mention-item-text">{item.name}</div>
        {item.description && (
          <div className="sage-ai-mention-item-description">
            {item.description}
          </div>
        )}
      </div>
    </div>
  );
};

export default ContextItem;
