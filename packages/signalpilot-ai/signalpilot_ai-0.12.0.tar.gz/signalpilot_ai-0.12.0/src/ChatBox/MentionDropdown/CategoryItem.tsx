/**
 * CategoryItem Component
 *
 * Renders a single category in the mention dropdown with proper SVG icons
 * Matches the original ChatContextMenu styling
 */
import React from 'react';
import { CategoryItemProps } from './types';
import { getIconForCategory } from './Icons';

export const CategoryItem: React.FC<CategoryItemProps> = ({
  category,
  isActive,
  onClick
}) => {
  const className = `sage-ai-mention-item sage-ai-mention-category-main${isActive ? ' active' : ''}`;
  const IconComponent = getIconForCategory(category.id);

  return (
    <div className={className} data-category={category.id} onClick={onClick}>
      <span className="sage-ai-mention-item-icon">
        <IconComponent />
      </span>
      <div style={{ flex: 1 }}>
        <div className="sage-ai-mention-item-text">{category.name}</div>
      </div>
    </div>
  );
};

export default CategoryItem;
