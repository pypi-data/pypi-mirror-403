/**
 * SearchInput Component
 *
 * Search input with icon matching the original ChatContextMenu styling
 */
import React, { useEffect, useRef } from 'react';
import { SearchInputProps } from './types';
import { SearchIconSvg } from './Icons';

export const SearchInput: React.FC<SearchInputProps> = ({
  value,
  placeholder,
  onChange,
  onKeyDown,
  autoFocus = false,
  inputRef: externalRef
}) => {
  const internalRef = useRef<HTMLInputElement>(null);
  const inputRef = externalRef || internalRef;

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      // Small delay to ensure the dropdown is positioned
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [autoFocus, inputRef]);

  return (
    <div className="sage-ai-mention-search-container">
      <SearchIconSvg className="sage-ai-mention-search-icon" />
      <input
        ref={inputRef}
        type="text"
        className="sage-ai-mention-search-input"
        placeholder={placeholder}
        value={value}
        onChange={e => onChange(e.target.value)}
        onKeyDown={onKeyDown}
      />
    </div>
  );
};

export default SearchInput;
