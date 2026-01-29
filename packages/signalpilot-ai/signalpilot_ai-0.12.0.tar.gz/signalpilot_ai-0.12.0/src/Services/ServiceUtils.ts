import { useAppStore } from '../stores/appStore';
import { useChatboxStore } from '../stores/chatboxStore';

/**
 * Utility functions for message formatting and processing
 */
export class ServiceUtils {
  /**
   * Parses user messages from conversation history
   * @param messages The conversation history
   * @param errorLogger Optional error logger function
   * @returns Parsed user messages
   */
  static parseUserMessages(messages: any[]): any[] {
    try {
      return messages.map(message => {
        if (this.isUserMessage(message)) {
          return {
            role: 'user',
            content: message.content
          };
        } else {
          message.usage = undefined;
        }

        return message;
      });
    } catch (error) {
      console.error('Error in parseUserMessages:', error, { messages });
      return messages;
    }
  }

  /**
   * Identifies if a message is a user message
   * @param message The message to check
   * @returns boolean indicating if the message is a user message
   */
  static isUserMessage(message: any): boolean {
    return message && message.role === 'user';
  }

  /**
   * Identifies if a message is tool-related (tool_use or tool_result)
   * @param message The message to check
   * @returns boolean indicating if the message is tool-related
   */
  static isToolRelatedMessage(message: any): boolean {
    try {
      return (
        ServiceUtils.isToolUseMessage(message) ||
        ServiceUtils.isToolResultMessage(message)
      );
    } catch (error) {
      console.error('Error in isToolRelatedMessage:', error, { message });
      // Return false as a fallback
      return false;
    }
  }

  /**
   * Checks if a message is a tool_use message (contains at least one tool_use or server_tool_use block)
   * @param message The message to check
   * @returns boolean indicating if the message is a tool_use message
   */
  static isToolUseMessage(message: any): boolean {
    return (
      message &&
      message.role === 'assistant' &&
      Array.isArray(message.content) &&
      message.content.length > 0 &&
      message.content.some(
        (block: any) =>
          block.type === 'tool_use' || block.type === 'server_tool_use'
      )
    );
  }

  /**
   * Checks if a message is a tool_result message (contains at least one tool_result block)
   * @param message The message to check
   * @returns boolean indicating if the message is a tool_result message
   */
  static isToolResultMessage(message: any): boolean {
    return (
      message &&
      message.role === 'user' &&
      Array.isArray(message.content) &&
      message.content.length > 0 &&
      message.content.some((block: any) => block.type === 'tool_result')
    );
  }

  /**
   * Gets the first tool_use or server_tool_use block from a message
   * @param message The message to extract from
   * @returns The first tool_use/server_tool_use block or undefined
   */
  static getFirstToolUseBlock(message: any): any | undefined {
    if (!message || !Array.isArray(message.content)) {
      return undefined;
    }
    return message.content.find(
      (block: any) =>
        block.type === 'tool_use' || block.type === 'server_tool_use'
    );
  }

  /**
   * Gets all tool_use IDs from a message
   * @param message The message to extract from
   * @returns Set of tool_use IDs
   */
  static getAllToolUseIds(message: any): Set<string> {
    const ids = new Set<string>();
    if (!message || !Array.isArray(message.content)) {
      return ids;
    }
    for (const block of message.content) {
      if (
        (block.type === 'tool_use' || block.type === 'server_tool_use') &&
        block.id
      ) {
        ids.add(block.id);
      }
    }
    return ids;
  }

  /**
   * Gets all tool_result IDs from a message
   * @param message The message to extract from
   * @returns Set of tool_use_ids from tool_result blocks
   */
  static getAllToolResultIds(message: any): Set<string> {
    const ids = new Set<string>();
    if (!message || !Array.isArray(message.content)) {
      return ids;
    }
    for (const block of message.content) {
      if (block.type === 'tool_result' && block.tool_use_id) {
        ids.add(block.tool_use_id);
      }
    }
    return ids;
  }

  /**
   * Gets the first tool_result block from a message
   * @param message The message to extract from
   * @returns The first tool_result block or undefined
   */
  static getFirstToolResultBlock(message: any): any | undefined {
    if (!message || !Array.isArray(message.content)) {
      return undefined;
    }
    return message.content.find((block: any) => block.type === 'tool_result');
  }

  /**
   * Checks if a message is a diff_approval message
   * @param message The message to check
   * @returns boolean indicating if the message is a diff_approval message
   */
  static isDiffApprovalMessage(message: any): boolean {
    return (
      message &&
      message.role === 'diff_approval' &&
      Array.isArray(message.content) &&
      message.content.length > 0 &&
      message.content[0].type === 'diff_approval'
    );
  }

  /**
   * Filters conversation history to keep only the last 10 tool-related message pairs
   * while preserving all non-tool messages. A pair consists of a tool_use message
   * followed by its corresponding tool_result message.
   * @param messages The conversation history
   * @param errorLogger Optional error logger function
   * @returns Filtered conversation history
   */
  static filterToolMessages(
    _messages: Array<any>,
    errorLogger?: (message: any) => Promise<void>
  ): Array<any> {
    try {
      const messages = ServiceUtils.buildCleanedConversationHistory(
        _messages,
        errorLogger
      );
      const maxToolCallLimit = useAppStore.getState().maxToolCallLimit;
      if (maxToolCallLimit) {
        let numCalls = 0;
        messages.forEach(message => {
          if (ServiceUtils.isToolRelatedMessage(message)) {
            numCalls += 1;
          }
        });
        if (numCalls > maxToolCallLimit) {
          console.log('Max tool call limit reached, cancelling llm loop');
          useChatboxStore.getState().cancelMessage();
        }
      }

      // Find all tool-related message indices
      const toolMessageIndices: number[] = [];
      const toolUseIndices: number[] = [];
      const toolResultIndices: number[] = [];

      messages.forEach((message, index) => {
        if (ServiceUtils.isToolRelatedMessage(message)) {
          toolMessageIndices.push(index);

          if (ServiceUtils.isToolUseMessage(message)) {
            toolUseIndices.push(index);
          }

          if (ServiceUtils.isToolResultMessage(message)) {
            toolResultIndices.push(index);
          }
        }
      });

      // If we have 10 or fewer tool pairs, return all messages
      if (toolUseIndices.length <= 10) {
        return [...messages];
      }

      // Find the last 10 complete tool pairs
      const lastXToolUseIndices = toolUseIndices.slice(
        toolUseIndices.length - 10
      );
      const indicesToKeep = new Set<number>();

      // For each tool_use, find its corresponding tool_result and add both to keep set
      for (const toolUseIndex of lastXToolUseIndices) {
        indicesToKeep.add(toolUseIndex);

        // Find the next tool_result after this tool_use
        const nextToolResultIndex = toolResultIndices.find(
          resultIndex => resultIndex > toolUseIndex
        );

        if (nextToolResultIndex !== undefined) {
          indicesToKeep.add(nextToolResultIndex);
        }
      }

      // Filter messages: keep non-tool messages and tool messages that are in our keep set
      return messages.filter(
        (message, index) =>
          !ServiceUtils.isToolRelatedMessage(message) ||
          indicesToKeep.has(index)
      );
    } catch (error) {
      errorLogger &&
        void errorLogger(
          `Error in filterToolMessages: ${error}, messages: ${JSON.stringify(_messages)}`
        );
      console.error('Error in filterToolMessages:', error, {
        messagesLength: _messages.length
      });
      // Return original messages as fallback
      return [..._messages];
    }
  }

  /**
   * Filters conversation history to remove all diff_approval messages,
   * preserving only non-diff_approval messages.
   * @param _messages The conversation history
   * @returns Filtered conversation history without diff_approval messages
   */
  static filterDiffApprovalMessages(_messages: Array<any>): Array<any> {
    return _messages.filter(
      message => !ServiceUtils.isDiffApprovalMessage(message)
    );
  }

  /**
   * Normalizes message content to ensure it's in the correct format for the API
   * @param messages Array of messages to normalize
   * @param errorLogger Optional error logger function
   * @returns Normalized messages
   */
  static normalizeMessageContent(
    messages: any[],
    errorLogger?: (message: any) => Promise<void>
  ): any[] {
    try {
      const normalizedMessages = messages.map(msg => {
        // Deep clone the message to avoid modifying the original
        const normalizedMsg = { ...msg };

        // Only process content if it's not a tool-related message
        if (!ServiceUtils.isToolRelatedMessage(normalizedMsg)) {
          // Handle array content
          if (Array.isArray(normalizedMsg.content)) {
            // Convert array to a single string if all elements are strings or simple types
            if (
              normalizedMsg.content.every(
                (item: any) =>
                  typeof item === 'string' ||
                  typeof item === 'number' ||
                  typeof item === 'boolean'
              )
            ) {
              normalizedMsg.content = normalizedMsg.content.join(' ');
            }
          }
        }

        return normalizedMsg;
      });

      return ServiceUtils.buildCleanedConversationHistory(
        normalizedMessages,
        errorLogger
      );
    } catch (error) {
      errorLogger &&
        void errorLogger(
          `Error in normalizeMessageContent: ${error}, messages: ${JSON.stringify(messages)}`
        );
      console.error('Error in normalizeMessageContent:', error, {
        messagesLength: messages?.length
      });
      // Return original messages as fallback
      return messages;
    }
  }

  /**
   * Removes assistant tool_use messages that are not followed by a user tool_result message.
   * Also removes user tool_result messages that are not preceded by an assistant tool_use message.
   * Also merges consecutive messages with the same role to satisfy API requirements.
   * @param initialMessages Array of messages to clean
   * @param errorLogger Optional error logger function
   * @returns Cleaned conversation history
   */
  static buildCleanedConversationHistory(
    initialMessages: any[],
    errorLogger?: (message: any) => Promise<void>
  ): any[] {
    try {
      // First: filter out server_tool_use blocks (internal API operations)
      const filteredServerToolUse =
        ServiceUtils.filterServerToolUse(initialMessages);

      // Second pass: merge consecutive messages with the same role
      const mergedMessages = ServiceUtils.mergeConsecutiveMessages(
        filteredServerToolUse
      );

      const cleanedHistory: any[] = [];
      for (let i = 0; i < mergedMessages.length; i++) {
        const currentMessage = mergedMessages[i];

        if (ServiceUtils.isToolUseMessage(currentMessage)) {
          const nextMessage = mergedMessages[i + 1];

          // Check if the next message is a user tool_result message
          const isUserToolResultNext =
            ServiceUtils.isToolResultMessage(nextMessage);
          // Keep the assistant tool_use message ONLY if it's followed by a user tool_result
          if (isUserToolResultNext) {
            cleanedHistory.push(currentMessage);
          } else {
            // If not followed by a tool_result, skip this assistant tool_use message
            console.log(
              'Removing unmatched assistant tool_use message:',
              JSON.stringify(currentMessage)
            );
          }
        } else if (ServiceUtils.isToolResultMessage(currentMessage)) {
          // Check if message has both tool_result and non-tool_result content (e.g., text)
          // This happens when a user message follows a tool_result and they get merged
          const toolResultBlocks = currentMessage.content.filter(
            (block: any) => block.type === 'tool_result'
          );
          const nonToolResultBlocks = currentMessage.content.filter(
            (block: any) => block.type !== 'tool_result'
          );

          // Look backwards through the cleaned history to find a matching tool_use
          const previousMessage = cleanedHistory[cleanedHistory.length - 1];
          const isPreviousToolUse =
            ServiceUtils.isToolUseMessage(previousMessage);
          if (isPreviousToolUse) {
            // Get ALL tool_use IDs from the previous message
            const toolUseIds = ServiceUtils.getAllToolUseIds(previousMessage);

            // Filter tool_result blocks to only those that have matching tool_use IDs
            const matchingToolResultBlocks = toolResultBlocks.filter(
              (block: any) => toolUseIds.has(block.tool_use_id)
            );
            const unmatchedToolResultBlocks = toolResultBlocks.filter(
              (block: any) => !toolUseIds.has(block.tool_use_id)
            );

            // Keep the user tool_result message if it has ANY matching tool_use
            if (matchingToolResultBlocks.length > 0) {
              const properToolFormat = {
                role: currentMessage.role,
                content: matchingToolResultBlocks.map((toolResult: any) => ({
                  tool_use_id: toolResult.tool_use_id,
                  content: toolResult.content,
                  type: toolResult.type
                }))
              };

              cleanedHistory.push(properToolFormat);

              // Log if some tool_results were unmatched (for debugging parallel calls)
              if (unmatchedToolResultBlocks.length > 0) {
                console.log(
                  `[ServiceUtils] Filtered out ${unmatchedToolResultBlocks.length} unmatched tool_results, kept ${matchingToolResultBlocks.length}`
                );
              }

              // If there were non-tool_result blocks (like text), add them as a separate message
              // This preserves user messages that were merged with tool_results
              if (nonToolResultBlocks.length > 0) {
                console.log(
                  '[ServiceUtils] Preserving non-tool_result content from merged message:',
                  nonToolResultBlocks
                );
                cleanedHistory.push({
                  role: 'user',
                  content: nonToolResultBlocks
                });
              }
            } else {
              console.log(
                'Removing unmatched user tool_result message (no matching IDs):',
                JSON.stringify(currentMessage)
              );
              // Even if tool_result doesn't match, preserve any non-tool_result content
              if (nonToolResultBlocks.length > 0) {
                console.log(
                  '[ServiceUtils] Preserving non-tool_result content despite ID mismatch:',
                  nonToolResultBlocks
                );
                cleanedHistory.push({
                  role: 'user',
                  content: nonToolResultBlocks
                });
              }
            }
          } else {
            // No preceding tool_use message found, remove this orphaned tool_result
            console.log(
              'Removing orphaned user tool_result message (no preceding tool_use):',
              JSON.stringify(currentMessage)
            );
            // Still preserve any non-tool_result content (like user text messages)
            if (nonToolResultBlocks.length > 0) {
              console.log(
                '[ServiceUtils] Preserving non-tool_result content from orphaned tool_result:',
                nonToolResultBlocks
              );
              cleanedHistory.push({
                role: 'user',
                content: nonToolResultBlocks
              });
            }
          }
        } else {
          // Keep all other messages
          cleanedHistory.push(currentMessage);
        }
      }

      // Second pass: merge consecutive same-role messages again after cleanup
      // This handles cases where removing orphaned messages creates new consecutive same-role messages
      return ServiceUtils.mergeConsecutiveMessages(cleanedHistory);
    } catch (error) {
      errorLogger &&
        void errorLogger(
          `Error in buildCleanedConversationHistory: ${error}, messages: ${JSON.stringify(initialMessages)}`
        );
      console.error('Error in buildCleanedConversationHistory:', error, {
        messagesLength: initialMessages?.length
      });
      // Return original messages as fallback
      return initialMessages;
    }
  }

  /**
   * Filters out server_tool_use blocks and their corresponding tool_result blocks.
   * server_tool_use is an internal API operation (for tool search) that should not be
   * echoed back to the API.
   * @param messages Array of messages to filter
   * @returns Messages with server_tool_use and related tool_results removed
   */
  static filterServerToolUse(messages: any[]): any[] {
    // Collect all server_tool_use IDs to filter out their corresponding tool_results
    const serverToolUseIds = new Set<string>();

    for (const msg of messages) {
      if (msg.role === 'assistant' && Array.isArray(msg.content)) {
        for (const block of msg.content) {
          if (block.type === 'server_tool_use' && block.id) {
            serverToolUseIds.add(block.id);
          }
        }
      }
    }

    if (serverToolUseIds.size === 0) {
      return messages;
    }

    console.log(
      `[ServiceUtils] Filtering out ${serverToolUseIds.size} server_tool_use blocks and their results`
    );

    // Filter out server_tool_use blocks from assistant messages
    // and their corresponding tool_result blocks from user messages
    return messages
      .map(msg => {
        if (!Array.isArray(msg.content)) {
          return msg;
        }

        if (msg.role === 'assistant') {
          // Remove server_tool_use blocks
          const filteredContent = msg.content.filter(
            (block: any) => block.type !== 'server_tool_use'
          );
          if (filteredContent.length === 0) {
            return null; // Mark for removal
          }
          if (filteredContent.length !== msg.content.length) {
            return { ...msg, content: filteredContent };
          }
        } else if (msg.role === 'user') {
          // Remove tool_result blocks that correspond to server_tool_use
          const filteredContent = msg.content.filter(
            (block: any) =>
              block.type !== 'tool_result' ||
              !serverToolUseIds.has(block.tool_use_id)
          );
          if (filteredContent.length === 0) {
            return null; // Mark for removal
          }
          if (filteredContent.length !== msg.content.length) {
            return { ...msg, content: filteredContent };
          }
        }

        return msg;
      })
      .filter(msg => msg !== null);
  }

  /**
   * Merges consecutive messages with the same role into a single message.
   * This is required because the Anthropic API requires messages to alternate between user and assistant roles.
   * @param messages Array of messages to merge
   * @returns Messages with consecutive same-role messages merged
   */
  static mergeConsecutiveMessages(messages: any[]): any[] {
    if (!messages || messages.length === 0) {
      return messages;
    }

    const merged: any[] = [];

    for (const msg of messages) {
      const last = merged[merged.length - 1];

      if (last && last.role === msg.role) {
        // Merge content into the previous message
        const lastContent = ServiceUtils.normalizeToContentArray(last.content);
        const newContent = ServiceUtils.normalizeToContentArray(msg.content);
        last.content = [...lastContent, ...newContent];
        console.log(
          `[ServiceUtils] Merged consecutive ${msg.role} messages (now ${last.content.length} content blocks)`
        );
      } else {
        // Normalize content to array format and add as new message
        const content = ServiceUtils.normalizeToContentArray(msg.content);
        merged.push({ role: msg.role, content });
      }
    }

    return merged;
  }

  /**
   * Normalizes message content to an array format.
   * Handles string content by converting to text block, and arrays by returning as-is.
   * @param content The content to normalize
   * @returns Content as an array of content blocks
   */
  private static normalizeToContentArray(content: any): any[] {
    if (Array.isArray(content)) {
      return content;
    }
    if (typeof content === 'string') {
      return [{ type: 'text', text: content }];
    }
    // For other types, wrap in a text block
    return [{ type: 'text', text: String(content) }];
  }

  /**
   * Creates a cancelled response object
   * @param errorLogger Optional error logger function
   * @param requestStatus Current request status for logging
   * @returns Cancelled response object
   */
  static async createCancelledResponse(
    errorLogger?: (message: any) => Promise<void>,
    requestStatus?: any
  ) {
    const errMsg = {
      message: 'Request was cancelled, skipping retry logic',
      requestStatus
    };
    errorLogger && (await errorLogger(JSON.stringify(errMsg)));
    return {
      cancelled: true,
      role: 'assistant',
      content: []
    };
  }
}
