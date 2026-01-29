/**
 * MCP Display Utilities
 *
 * Pure utility functions for extracting data from MCP tool calls and results.
 * No DOM manipulation - all UI is handled by React components.
 *
 * @module mcpDisplayUtils
 */

/**
 * Extract input data from MCP tool call structure.
 *
 * MCP tool calls can have input in various nested locations depending
 * on how the data was structured. This function finds the actual input.
 *
 * @param toolCallData - The tool call data object
 * @returns Extracted input data
 */
export function extractMCPInput(toolCallData: any): any {
  try {
    // Check for nested structure: assistant.content[0].input
    if (toolCallData?.assistant?.content?.[0]?.input !== undefined) {
      return toolCallData.assistant.content[0].input;
    }
  } catch (e) {
    // Fall through to return original
  }

  // Return original if no nested structure found
  return toolCallData;
}

/**
 * Extract output data from MCP tool result structure.
 *
 * MCP results often wrap the actual content in various structures.
 * This function extracts the meaningful output for display.
 *
 * @param result - The tool result (may be string or object)
 * @returns Extracted output data
 */
export function extractMCPOutput(result: any): any {
  try {
    // Parse if string
    let parsed = result;
    if (typeof result === 'string') {
      try {
        parsed = JSON.parse(result);
      } catch {
        return result; // Keep as string if not valid JSON
      }
    }

    // Check for content.text
    if (parsed?.content?.text !== undefined) {
      return parsed.content.text;
    }

    // Check for content array
    if (Array.isArray(parsed?.content)) {
      // Single element with text - extract it
      if (
        parsed.content.length === 1 &&
        parsed.content[0]?.text !== undefined
      ) {
        return parsed.content[0].text;
      }
      // Multiple elements - return whole array
      return parsed.content;
    }

    // Check for direct content property
    if (parsed?.content !== undefined) {
      return parsed.content;
    }

    return parsed;
  } catch (e) {
    return result;
  }
}
