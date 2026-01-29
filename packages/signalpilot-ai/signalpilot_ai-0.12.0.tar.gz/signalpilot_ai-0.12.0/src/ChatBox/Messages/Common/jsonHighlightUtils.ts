/**
 * JSON Highlight Utilities
 *
 * This module provides utilities for parsing, cleaning, and syntax-highlighting
 * JSON data for display in the chat interface. It handles the complex task of
 * making nested JSON strings readable and visually appealing.
 *
 * Purpose:
 * When displaying tool inputs/outputs (especially from MCP tools), the data
 * often contains deeply nested JSON strings that need to be:
 * 1. Recursively parsed (JSON strings inside JSON)
 * 2. Cleaned up (removing wrapper objects like {type: "text", text: "..."})
 * 3. Syntax highlighted for readability
 *
 * Key responsibilities:
 * - Recursively parse nested JSON strings
 * - Clean parsed data by extracting meaningful content
 * - Apply syntax highlighting using highlight.js
 *
 * Real-world usage:
 * ```typescript
 * import { formatJsonWithHighlight, recursiveJsonParse } from './jsonHighlightUtils';
 *
 * // MCP tool returns nested JSON strings
 * const mcpResult = '{"content": [{"type": "text", "text": "{\\"name\\": \\"John\\"}"}]}';
 *
 * // Parse recursively to get clean object
 * const parsed = recursiveJsonParse(JSON.parse(mcpResult));
 * // Result: { content: [{ type: "text", text: { name: "John" } }] }
 *
 * // Format with syntax highlighting for display
 * const highlighted = formatJsonWithHighlight(mcpResult);
 * // Result: HTML string with <span class="hljs-..."> tags for colors
 * ```
 *
 * @module jsonHighlightUtils
 */

import hljs from 'highlight.js/lib/core';
import json from 'highlight.js/lib/languages/json';

// Register JSON language for highlight.js
hljs.registerLanguage('json', json);

/**
 * Recursively parse JSON strings within objects and arrays.
 *
 * API responses often contain JSON strings nested inside JSON objects.
 * This function recursively parses all string values that are valid JSON,
 * converting them to their parsed form for easier manipulation.
 *
 * @param data - Any data structure that may contain JSON strings
 * @returns The same structure with all JSON strings parsed
 *
 * @example
 * // Nested JSON string
 * recursiveJsonParse({ data: '{"name": "John"}' })
 * // Returns: { data: { name: "John" } }
 *
 * // Deeply nested
 * recursiveJsonParse({ outer: '{"inner": "{\\"deep\\": true}"}' })
 * // Returns: { outer: { inner: { deep: true } } }
 *
 * // Non-JSON strings are left alone
 * recursiveJsonParse({ message: "Hello world" })
 * // Returns: { message: "Hello world" }
 */
export function recursiveJsonParse(data: any): any {
  if (typeof data === 'string') {
    try {
      const parsed = JSON.parse(data);
      // Recursively parse the result in case there are nested JSON strings
      return recursiveJsonParse(parsed);
    } catch {
      // Not a JSON string, return as-is
      return data;
    }
  } else if (Array.isArray(data)) {
    return data.map(item => recursiveJsonParse(item));
  } else if (data !== null && typeof data === 'object') {
    const result: Record<string, any> = {};
    for (const key in data) {
      if (Object.prototype.hasOwnProperty.call(data, key)) {
        result[key] = recursiveJsonParse(data[key]);
      }
    }
    return result;
  }
  return data;
}

/**
 * Clean up parsed data by extracting text fields and simplifying structure.
 *
 * Many APIs wrap content in objects like `{type: "text", text: "actual content"}`.
 * This function extracts the meaningful content, making the display cleaner.
 *
 * @param data - Parsed data that may contain wrapper objects
 * @returns Cleaned data with wrapper objects simplified
 *
 * @example
 * // Single item array with type/text wrapper
 * cleanParsedData([{ type: "text", text: "Hello" }])
 * // Returns: ["Hello"]
 *
 * // Multiple items - keeps structure but extracts text
 * cleanParsedData([
 *   { type: "text", text: "Line 1" },
 *   { type: "text", text: "Line 2" }
 * ])
 * // Returns: ["Line 1", "Line 2"]
 *
 * // Non-text items are kept as-is
 * cleanParsedData([{ type: "image", url: "..." }])
 * // Returns: [{ type: "image", url: "..." }]
 */
export function cleanParsedData(data: any): any {
  if (Array.isArray(data)) {
    return data.map(item => {
      // Extract text from type/text wrapper objects
      if (
        item &&
        typeof item === 'object' &&
        item.type === 'text' &&
        item.text !== undefined
      ) {
        return item.text;
      }
      return item;
    });
  }
  return data;
}

/**
 * Format JSON with syntax highlighting using highlight.js.
 *
 * Takes JSON data (string or object), parses and cleans it, then applies
 * syntax highlighting for display in the UI. The result is an HTML string
 * with highlight.js CSS classes for coloring.
 *
 * @param json - JSON string or object to format
 * @returns HTML string with syntax highlighting spans
 *
 * @example
 * // Simple JSON
 * formatJsonWithHighlight('{"name": "John", "age": 30}')
 * // Returns HTML like:
 * // <span class="hljs-punctuation">{</span>
 * // <span class="hljs-attr">"name"</span>: <span class="hljs-string">"John"</span>, ...
 *
 * // Nested JSON strings are parsed first
 * formatJsonWithHighlight('{"data": "{\\"nested\\": true}"}')
 * // The nested JSON is expanded and highlighted
 */
export function formatJsonWithHighlight(jsonInput: string | object): string {
  try {
    // Parse if string, otherwise use directly
    const obj =
      typeof jsonInput === 'string' ? JSON.parse(jsonInput) : jsonInput;

    // Recursively parse any nested JSON strings
    const fullyParsed = recursiveJsonParse(obj);

    // Clean up by removing type wrappers and extracting text
    const cleaned = cleanParsedData(fullyParsed);

    // Pretty print
    const jsonString = JSON.stringify(cleaned, null, 2);

    // Apply syntax highlighting
    const highlighted = hljs.highlight(jsonString, {
      language: 'json',
      ignoreIllegals: true
    });

    return highlighted.value;
  } catch (e) {
    // If parsing fails, try to highlight as-is
    try {
      const highlighted = hljs.highlight(String(jsonInput), {
        language: 'json',
        ignoreIllegals: true
      });
      return highlighted.value;
    } catch {
      // If highlighting fails too, return escaped text
      return escapeHtml(String(jsonInput));
    }
  }
}

/**
 * Escape HTML special characters to prevent XSS.
 */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}
