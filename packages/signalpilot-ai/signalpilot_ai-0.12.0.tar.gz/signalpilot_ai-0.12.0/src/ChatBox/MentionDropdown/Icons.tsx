/**
 * SVG Icon Components for MentionDropdown
 *
 * Uses the same SVG icons as the original ChatContextMenu
 */
import React from 'react';

// Import SVG icons as raw strings
import variableIcon from '../../../style/icons/context_menu/variable.svg';
import snippetsIcon from '../../../style/icons/context_menu/snippets.svg';
import dataIcon from '../../../style/icons/context_menu/data.svg';
import databaseIcon from '../../../style/icons/context_menu/database.svg';
import cellIcon from '../../../style/icons/context_menu/cell.svg';
import searchIcon from '../../../style/icons/context_menu/search.svg';

// Back caret SVG
const BACK_CARET_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="15" viewBox="0 0 14 15" fill="none">
  <path d="M8.75 11L5.25 7.5L8.75 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>`;

// Folder SVG
const FOLDER_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
  <path d="M2 3.5C2 2.67157 2.67157 2 3.5 2H6.79289C7.15482 2 7.50207 2.14365 7.76777 2.40934L9.70711 4.34868C9.97281 4.61438 10.32 4.75803 10.682 4.75803H12.5C13.3284 4.75803 14 5.4296 14 6.25803V12.5C14 13.3284 13.3284 14 12.5 14H3.5C2.67157 14 2 13.3284 2 12.5V3.5Z" fill="currentColor"/>
</svg>`;

// Table SVG
const TABLE_SVG = `<svg xmlns="http://www.w3.org/2000/svg" height="16px" viewBox="0 -960 960 960" width="16px" fill="currentColor"><path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-507h560v-133H200v133Zm0 214h560v-134H200v134Zm0 213h560v-133H200v133Zm40-454v-80h80v80h-80Zm0 214v-80h80v80h-80Zm0 214v-80h80v80h-80Z"/></svg>`;

interface IconProps {
  className?: string;
}

// Helper to render SVG string as React element
const SvgIcon: React.FC<{ svg: string; className?: string }> = ({
  svg,
  className
}) => <span className={className} dangerouslySetInnerHTML={{ __html: svg }} />;

export const VariableIcon: React.FC<IconProps> = ({ className }) => (
  <SvgIcon svg={variableIcon} className={className} />
);

export const SnippetsIcon: React.FC<IconProps> = ({ className }) => (
  <SvgIcon svg={snippetsIcon} className={className} />
);

export const DataIcon: React.FC<IconProps> = ({ className }) => (
  <SvgIcon svg={dataIcon} className={className} />
);

export const DatabaseIcon: React.FC<IconProps> = ({ className }) => (
  <SvgIcon svg={databaseIcon} className={className} />
);

export const CellIcon: React.FC<IconProps> = ({ className }) => (
  <SvgIcon svg={cellIcon} className={className} />
);

export const SearchIconSvg: React.FC<IconProps> = ({ className }) => (
  <SvgIcon svg={searchIcon} className={className} />
);

export const BackCaretIcon: React.FC<IconProps> = ({ className }) => (
  <SvgIcon svg={BACK_CARET_SVG} className={className} />
);

export const FolderIcon: React.FC<IconProps> = ({ className }) => (
  <SvgIcon svg={FOLDER_SVG} className={className} />
);

export const TableIcon: React.FC<IconProps> = ({ className }) => (
  <SvgIcon svg={TABLE_SVG} className={className} />
);

/**
 * Get the appropriate icon component for a context type
 */
export function getIconForType(type: string): React.FC<IconProps> {
  switch (type) {
    case 'snippets':
      return SnippetsIcon;
    case 'data':
      return DataIcon;
    case 'database':
      return DatabaseIcon;
    case 'directory':
      return FolderIcon;
    case 'variable':
      return VariableIcon;
    case 'cell':
      return CellIcon;
    case 'table':
    case 'tables':
      return TableIcon;
    default:
      return DataIcon;
  }
}

/**
 * Get the appropriate icon component for a category ID
 */
export function getIconForCategory(categoryId: string): React.FC<IconProps> {
  switch (categoryId) {
    case 'snippets':
      return SnippetsIcon;
    case 'data':
      return DataIcon;
    case 'database':
      return DatabaseIcon;
    case 'variables':
      return VariableIcon;
    case 'cells':
      return CellIcon;
    case 'tables':
      return TableIcon;
    default:
      return DataIcon;
  }
}
