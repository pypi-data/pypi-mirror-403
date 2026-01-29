/**
 * Pure diff calculation utilities
 * Extracted from NotebookDiffTools for reusability
 * NO DOM operations - can be used anywhere
 */

export interface DiffLine {
  line: string;
  type: 'added' | 'removed' | 'unchanged';
}

/**
 * Calculate line-by-line diff between two strings
 * @param oldText The original text
 * @param newText The new text
 * @returns An array of diff objects with line content and change type
 */
export function calculateDiff(oldText: string, newText: string): DiffLine[] {
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  const result: DiffLine[] = [];

  let i = 0,
    j = 0;
  while (i < oldLines.length || j < newLines.length) {
    if (i >= oldLines.length) {
      result.push({ line: newLines[j], type: 'added' });
      j++;
    } else if (j >= newLines.length) {
      result.push({ line: oldLines[i], type: 'removed' });
      i++;
    } else if (oldLines[i] === newLines[j]) {
      result.push({ line: oldLines[i], type: 'unchanged' });
      i++;
      j++;
    } else {
      result.push({ line: oldLines[i], type: 'removed' });
      result.push({ line: newLines[j], type: 'added' });
      i++;
      j++;
    }
  }

  return result;
}

/**
 * Format diff for console output with ANSI colors
 * @param diff The diff result array
 * @returns Colored string representation of the diff
 */
export function formatDiffForConsole(diff: DiffLine[]): string {
  const RED = '\x1b[31m';
  const GREEN = '\x1b[32m';
  const RESET = '\x1b[0m';

  return diff
    .map(item => {
      if (item.type === 'added') return `${GREEN}+ ${item.line}${RESET}`;
      if (item.type === 'removed') return `${RED}- ${item.line}${RESET}`;
      return `  ${item.line}`;
    })
    .join('\n');
}

/**
 * Normalize content for consistent comparison
 * Converts Windows line endings to Unix and trims whitespace
 * @param content The content to normalize
 * @returns Normalized content
 */
export function normalizeContent(content: string): string {
  return content.replace(/\r\n/g, '\n').trim();
}

/**
 * Check if two strings are effectively equal after normalization
 * @param a First string
 * @param b Second string
 * @returns True if strings are equal after normalization
 */
export function areContentsEqual(a: string, b: string): boolean {
  return normalizeContent(a) === normalizeContent(b);
}

/**
 * Count the number of changes in a diff
 * @param diff The diff result array
 * @returns Object with counts of added, removed, and unchanged lines
 */
export function countDiffChanges(diff: DiffLine[]): {
  added: number;
  removed: number;
  unchanged: number;
} {
  return diff.reduce(
    (acc, item) => {
      acc[item.type]++;
      return acc;
    },
    { added: 0, removed: 0, unchanged: 0 }
  );
}
