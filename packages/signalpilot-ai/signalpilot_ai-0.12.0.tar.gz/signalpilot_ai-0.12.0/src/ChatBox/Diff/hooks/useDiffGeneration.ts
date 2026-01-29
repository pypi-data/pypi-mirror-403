/**
 * Diff generation hook and utilities
 * Provides diff HTML generation using diff2html library
 * Replaces generateHtmlDiff from NotebookDiffTools
 */

import { useMemo } from 'react';
import * as Diff2Html from 'diff2html';
import * as JsDiff from 'diff';
import { ColorSchemeType, DiffFile } from 'diff2html/lib/types';
import { useThemeDetection } from './useThemeDetection';

export interface DiffGenerationOptions {
  /** Show all lines including unchanged (default: false) */
  showAllLines?: boolean;
  /** Output format (default: 'line-by-line') */
  outputFormat?: 'line-by-line' | 'side-by-side';
  /** Draw file list header (default: false) */
  drawFileList?: boolean;
  /** Original filename (default: 'Original.py') */
  originalFileName?: string;
  /** Modified filename (default: 'Modified.py') */
  modifiedFileName?: string;
  /** Language for syntax highlighting (default: 'py') */
  language?: string;
}

export interface DiffResult {
  /** Generated HTML string */
  html: string;
  /** Parsed diff JSON structure */
  json: DiffFile[];
  /** Unified diff string */
  unified: string;
}

/**
 * Pure function for generating diff - can be used outside React
 *
 * @param oldText Original text content
 * @param newText New text content
 * @param colorScheme Theme color scheme
 * @param options Generation options
 * @returns DiffResult with html, json, and unified diff
 *
 * @example
 * ```ts
 * const result = generateDiff(oldCode, newCode, ColorSchemeType.DARK);
 * console.log(result.html);
 * ```
 */
export function generateDiff(
  oldText: string,
  newText: string,
  colorScheme: ColorSchemeType = ColorSchemeType.LIGHT,
  options?: DiffGenerationOptions
): DiffResult {
  const {
    showAllLines = false,
    outputFormat = 'line-by-line',
    drawFileList = false,
    originalFileName = 'Original.py',
    modifiedFileName = 'Modified.py',
    language = 'py'
  } = options || {};

  // Create unified diff string
  const contextOptions = showAllLines ? { context: Infinity } : {};

  const unified = JsDiff.createTwoFilesPatch(
    originalFileName,
    modifiedFileName,
    oldText,
    newText,
    '', // oldHeader
    '', // newHeader
    contextOptions
  );

  // Parse into JSON diff structure
  const json = Diff2Html.parse(unified, {
    outputFormat,
    matching: 'lines',
    colorScheme
  });

  // Set language for syntax highlighting on all blocks
  json.forEach(block => {
    block.language = language;
  });

  // Generate HTML
  const html = Diff2Html.html(json, {
    drawFileList,
    outputFormat,
    matching: 'lines',
    colorScheme
  });

  return { html, json, unified };
}

/**
 * React hook for generating diff HTML with automatic theme reactivity
 *
 * @param oldText Original text content
 * @param newText New text content
 * @param options Generation options
 * @returns DiffResult that updates when theme or content changes
 *
 * @example
 * ```tsx
 * function DiffViewer({ oldCode, newCode }) {
 *   const { html } = useDiffGeneration(oldCode, newCode);
 *   return <div dangerouslySetInnerHTML={{ __html: html }} />;
 * }
 * ```
 */
export function useDiffGeneration(
  oldText: string,
  newText: string,
  options?: DiffGenerationOptions
): DiffResult {
  const { theme } = useThemeDetection();

  return useMemo(() => {
    return generateDiff(oldText, newText, theme, options);
  }, [
    oldText,
    newText,
    theme,
    options?.showAllLines,
    options?.outputFormat,
    options?.drawFileList,
    options?.originalFileName,
    options?.modifiedFileName,
    options?.language
  ]);
}
