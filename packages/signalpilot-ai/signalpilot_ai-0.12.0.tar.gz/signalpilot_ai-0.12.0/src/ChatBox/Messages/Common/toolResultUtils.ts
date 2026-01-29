/**
 * Tool Result Utilities
 *
 * Pure utility functions for parsing tool execution results.
 * No DOM manipulation - all UI is handled by React components.
 *
 * @module toolResultUtils
 */

/**
 * Check if a tool result contains errors and extract error messages.
 *
 * Tool results can come in various formats:
 * 1. Single error object: `{"error": true, "errorText": "..."}`
 * 2. Array of results: `[{"error": true, "errorText": "..."}, {"error": false}]`
 * 3. Plain string (not an error)
 *
 * This function handles all these cases and returns a normalized error string
 * or `false` if no errors were found.
 *
 * @param result - The tool execution result (typically a JSON string)
 * @returns Error message string if errors found, `false` otherwise
 *
 * @example
 * // Single error
 * getResultError('{"error": true, "errorText": "Division by zero"}')
 * // Returns: "Division by zero"
 *
 * // Multiple errors in array
 * getResultError('[{"error": true, "errorText": "Error 1"}, {"error": true, "errorText": "Error 2"}]')
 * // Returns: "Error 1\nError 2"
 *
 * // No error
 * getResultError('{"success": true, "output": "42"}')
 * // Returns: false
 */
export function getResultError(result: unknown): false | string {
  try {
    if (typeof result !== 'string') {
      return false;
    }

    const obj = JSON.parse(result);

    if (Array.isArray(obj)) {
      const errors = obj.filter(item => item && item?.error === true);
      if (!errors.length) {
        return false;
      }
      return errors.map(item => item.errorText).join('\n');
    } else if (obj && obj?.error === true) {
      return obj.errorText;
    }
  } catch {
    return false;
  }

  return false;
}
