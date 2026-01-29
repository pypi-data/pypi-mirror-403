/**
 * useInputControls Hook
 *
 * Manages input element controls like getting/setting value,
 * selection, focus, and clearing.
 */
import { useCallback, useRef, useState } from 'react';
import { RichTextInputRef } from '../RichTextInput';

export interface UseInputControlsReturn {
  richTextInputRef: React.RefObject<RichTextInputRef>;
  hasContent: boolean;
  getInputValue: () => string;
  setInputValue: (value: string) => void;
  getSelectionStart: () => number;
  setSelectionRange: (start: number, end: number) => void;
  clearInput: () => void;
  focus: () => void;
  setHasContent: (value: boolean) => void;
}

export function useInputControls(): UseInputControlsReturn {
  const richTextInputRef = useRef<RichTextInputRef>(null);
  const [hasContent, setHasContent] = useState(false);

  const getInputValue = useCallback((): string => {
    return richTextInputRef.current?.getPlainText().trim() || '';
  }, []);

  const setInputValue = useCallback((value: string): void => {
    richTextInputRef.current?.setPlainText(value);
    setHasContent(value.trim().length > 0);
  }, []);

  const getSelectionStart = useCallback((): number => {
    return richTextInputRef.current?.getSelectionStart() || 0;
  }, []);

  const setSelectionRange = useCallback((start: number, end: number): void => {
    richTextInputRef.current?.setSelectionRange(start, end);
  }, []);

  const clearInput = useCallback((): void => {
    richTextInputRef.current?.clear();
    setHasContent(false);
  }, []);

  const focus = useCallback((): void => {
    richTextInputRef.current?.focus();
  }, []);

  return {
    richTextInputRef,
    hasContent,
    getInputValue,
    setInputValue,
    getSelectionStart,
    setSelectionRange,
    clearInput,
    focus,
    setHasContent
  };
}
