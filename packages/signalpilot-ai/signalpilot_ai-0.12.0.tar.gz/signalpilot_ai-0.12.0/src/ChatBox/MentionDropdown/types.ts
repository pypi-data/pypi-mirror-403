/**
 * MentionDropdown Types
 *
 * Complete type definitions matching all features of the original ChatContextMenu
 */
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';

export type { IMentionContext };

export type ViewType = 'categories' | 'items';

export interface MentionCategory {
  id: string;
  name: string;
  icon: string;
  description: string;
}

export interface MentionDropdownState {
  isVisible: boolean;
  currentView: ViewType;
  selectedCategory: string | null;
  selectedIndex: number;
  searchText: string;
  currentMentionStart: number;
  currentMentionText: string;
  isLoading: boolean;
  isRefreshing: boolean;
  contextItems: Map<string, IMentionContext[]>;
}

export interface MentionDropdownProps {
  /** The input element to attach to */
  inputElement: HTMLElement | null;
  /** Parent element for positioning */
  parentElement: HTMLElement | null;
  /** Callback when a context is selected */
  onContextSelected?: (context: IMentionContext) => void;
  /** Callback when dropdown visibility changes */
  onVisibilityChange?: (isVisible: boolean) => void;
}

export interface MentionDropdownRef {
  /** Show the dropdown at the current cursor position */
  show: (mentionStart: number) => void;
  /** Hide the dropdown */
  hide: () => void;
  /** Check if dropdown is visible */
  isVisible: () => boolean;
  /** Select the currently highlighted item */
  selectHighlighted: () => void;
  /** Navigate up/down */
  navigate: (direction: 'up' | 'down') => void;
  /** Update the mention text (for filtering) */
  updateMentionText: (text: string) => void;
}

export interface CategoryItemProps {
  category: MentionCategory;
  isActive: boolean;
  onClick: () => void;
}

export interface ContextItemProps {
  item: IMentionContext;
  isActive: boolean;
  categoryLabel?: string;
  onClick: () => void;
}

export interface SearchInputProps {
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
  onKeyDown: (event: React.KeyboardEvent) => void;
  autoFocus?: boolean;
  inputRef?: React.RefObject<HTMLInputElement>;
}

export interface CategoryHeaderProps {
  categoryName: string;
  onBack: () => void;
}

export interface LoadingIndicatorProps {
  message?: string;
}

export interface SeparatorProps {
  text: string;
}
