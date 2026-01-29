/**
 * CategoryHeader Component
 *
 * Back navigation header when viewing items in a category
 * Matches the original ChatContextMenu styling
 */
import React from 'react';
import { CategoryHeaderProps } from './types';
import { BackCaretIcon } from './Icons';

export const CategoryHeader: React.FC<CategoryHeaderProps> = ({
  categoryName,
  onBack
}) => {
  return (
    <div className="sage-ai-mention-category-header" onClick={onBack}>
      <BackCaretIcon className="sage-ai-mention-back-icon" />
      <span className="sage-ai-mention-category-title">{categoryName}</span>
    </div>
  );
};

export default CategoryHeader;
