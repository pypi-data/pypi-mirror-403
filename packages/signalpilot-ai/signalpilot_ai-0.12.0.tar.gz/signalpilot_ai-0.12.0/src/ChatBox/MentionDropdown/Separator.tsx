/**
 * Separator Component
 *
 * Visual separator between sections matching the original ChatContextMenu styling
 */
import React from 'react';
import { SeparatorProps } from './types';

export const Separator: React.FC<SeparatorProps> = ({ text }) => {
  return <div className="sage-ai-mention-separator">{text}</div>;
};

export default Separator;
