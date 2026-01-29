/**
 * LLMContext - Single source of truth for all context gathering
 *
 * All context is gathered through addContext() which branches into
 * simple, single-purpose methods. This file centralizes all the scattered
 * context sources into one readable location.
 */

import { useChatMessagesStore } from '../stores/chatMessages';
import { DatabaseStateService, DatabaseType } from '../stores/databaseStore';
import { useAppStore, getWorkspaceContext } from '../stores/appStore';
import {
  getDatabaseEnvVarNames,
  getEnvVarPrefix
} from '../utils/databaseEnvVars';
import { useSnippetStore } from '../stores/snippetStore';
import { KernelPreviewUtils } from '../utils/kernelPreview';
import { NotebookContextManager } from '../Notebook/NotebookContextManager';
import { ToolService } from './ToolService';
import { ConfigService } from '../Config/ConfigService';
import { ChatMode, ILLMContext } from './LLMTypes';

// ═══════════════════════════════════════════════════════════════
// MAIN CLASS
// ═══════════════════════════════════════════════════════════════

/**
 * LLMContextGatherer - Centralizes all context gathering for LLM requests
 */
export class LLMContextGatherer {
  private toolService: ToolService;
  private notebookContextManager: NotebookContextManager;

  constructor(
    toolService: ToolService,
    notebookContextManager: NotebookContextManager
  ) {
    this.toolService = toolService;
    this.notebookContextManager = notebookContextManager;
  }

  // ═══════════════════════════════════════════════════════════════
  // MAIN ENTRY POINT
  // ═══════════════════════════════════════════════════════════════

  /**
   * Gather all context needed for an LLM request.
   * This is the ONLY method external code should call.
   */
  async addContext(
    notebookId: string | null,
    mode: ChatMode,
    systemPromptMessages: string[] = []
  ): Promise<ILLMContext> {
    console.log(
      '[LLMContext] Gathering context for mode:',
      mode,
      'notebookId:',
      notebookId
    );
    const perfStart = performance.now();

    // Gather all context in parallel where possible with individual logging
    console.log('[LLMContext] Starting parallel context gathering...');
    const [
      notebookSummary,
      kernelVariables,
      workspaceContext,
      userSnippets,
      userSelectedCells
    ] = await Promise.all([
      this.getNotebookSummary(notebookId).then(r => {
        console.log('[LLMContext] notebookSummary done');
        return r;
      }),
      this.getKernelVariables().then(r => {
        console.log('[LLMContext] kernelVariables done');
        return r;
      }),
      Promise.resolve(this.getWorkspaceContext(mode)).then(r => {
        console.log('[LLMContext] workspaceContext done');
        return r;
      }),
      Promise.resolve(this.getUserSnippets()).then(r => {
        console.log('[LLMContext] userSnippets done');
        return r;
      }),
      Promise.resolve(this.getUserSelectedCells(notebookId)).then(r => {
        console.log('[LLMContext] userSelectedCells done');
        return r;
      })
    ]);
    console.log('[LLMContext] All parallel context gathered');

    console.log('[LLMContext] Getting system prompt...');
    const systemPrompt = await this.getSystemPrompt(mode, systemPromptMessages);
    console.log(
      '[LLMContext] System prompt loaded, length:',
      systemPrompt?.length || 0
    );

    const context: ILLMContext = {
      // Core context
      systemPrompt,
      conversationHistory: this.getConversationHistory(),

      // Dynamic context
      notebookSummary,
      notebookCells: '', // Included in notebookSummary
      kernelVariables,
      databaseConfigs: this.getDatabaseConfigs(),
      workspaceContext,
      userSnippets,
      userSelectedCells,

      // Metadata
      notebookId,
      mode,
      autoRun: useAppStore.getState().autoRun
    };

    const perfEnd = performance.now();
    console.log(
      `[LLMContext] Context gathered in ${(perfEnd - perfStart).toFixed(2)}ms`
    );

    return context;
  }

  // ═══════════════════════════════════════════════════════════════
  // CONTEXT ADDERS - Each does ONE thing
  // ═══════════════════════════════════════════════════════════════

  /**
   * Build the complete notebook state string for inclusion in API requests
   * This combines notebook summary and database configs
   */
  buildNotebookStateString(context: ILLMContext): string {
    let result = '';

    if (context.notebookSummary) {
      result += context.notebookSummary;
    }

    if (context.databaseConfigs) {
      result += context.databaseConfigs;
    }

    return result;
  }

  /**
   * Build the complete context string for debugging/logging
   */
  buildFullContextString(context: ILLMContext): string {
    const parts: string[] = [];

    if (context.systemPrompt) {
      parts.push('=== SYSTEM PROMPT ===\n' + context.systemPrompt);
    }

    if (context.notebookSummary) {
      parts.push(context.notebookSummary);
    }

    if (context.kernelVariables) {
      parts.push(context.kernelVariables);
    }

    if (context.databaseConfigs) {
      parts.push(context.databaseConfigs);
    }

    if (context.workspaceContext) {
      parts.push(context.workspaceContext);
    }

    if (context.userSnippets) {
      parts.push(context.userSnippets);
    }

    if (context.userSelectedCells) {
      parts.push(context.userSelectedCells);
    }

    return parts.join('\n\n');
  }

  /**
   * Get the conversation history from Zustand store
   */
  private getConversationHistory(): any[] {
    return useChatMessagesStore.getState().llmHistory || [];
  }

  /**
   * Get the system prompt based on mode
   */
  private async getSystemPrompt(
    mode: ChatMode,
    additionalMessages: string[]
  ): Promise<string> {
    try {
      const config = await ConfigService.getConfig();

      let basePrompt = '';
      switch (mode) {
        case 'ask':
          basePrompt = config.claude_ask_mode.system_prompt;
          break;
        case 'fast':
          basePrompt = config.fast_mode.system_prompt;
          break;
        case 'welcome':
          basePrompt = config.welcome_mode.system_prompt;
          break;
        default:
          basePrompt = config.claude.system_prompt;
      }

      // Append additional system prompt messages
      if (additionalMessages.length > 0) {
        basePrompt += '\n\n' + additionalMessages.join('\n\n');
      }

      return basePrompt;
    } catch (error) {
      console.error('[LLMContext] Error loading system prompt:', error);
      return 'You are a helpful AI assistant for data science and notebook development.';
    }
  }

  /**
   * Get notebook summary and cell information
   */
  private async getNotebookSummary(notebookId: string | null): Promise<string> {
    if (!notebookId) return '';

    try {
      // Ensure the tool service is using the correct notebook context
      this.toolService.setCurrentNotebookId(notebookId);

      const notebookSummary =
        await this.toolService.notebookTools?.getNotebookSummary(notebookId);

      if (!notebookSummary) return '';

      let summaryClean = '=== SUMMARY OF CELLS IN NOTEBOOK ===\n\n';

      notebookSummary.forEach((cell: any) => {
        if (cell.id === 'planning_cell') {
          summaryClean += '- SAGE PLANNING CELL -\n';
          summaryClean += `cell_index: ${cell.index}, cell_id: ${cell.id}, summary: ${cell.summary}, cell_type: ${cell.cell_type}, next_step_string: ${cell.next_step_string}, current_step_string: ${cell.current_step_string}, empty: ${cell.empty}\n`;
          summaryClean += '- END SAGE PLANNING CELL -';
        } else {
          summaryClean += `cell_id: ${cell.id}, summary: ${cell.summary}, cell_index: ${cell.index}, cell_type: ${cell.cell_type}, empty: ${cell.empty}`;
        }
        summaryClean += '\n\n';
      });

      summaryClean += '=== END SUMMARY OF CELLS IN NOTEBOOK ===\n\n';

      return summaryClean;
    } catch (error) {
      console.warn('[LLMContext] Error getting notebook summary:', error);
      return '';
    }
  }

  /**
   * Get current kernel variables and objects
   */
  private async getKernelVariables(): Promise<string> {
    try {
      const preview = await KernelPreviewUtils.getLimitedKernelPreview();
      if (!preview) return '';
      return preview;
    } catch (error) {
      console.warn('[LLMContext] Error getting kernel preview:', error);
      return '';
    }
  }

  /**
   * Get database configurations with actual environment variable names
   */
  private getDatabaseConfigs(): string {
    const dbConfigs = DatabaseStateService.getState().configurations;
    if (dbConfigs.length === 0) return '';

    let dbString = '=== DATABASE CONFIGURATIONS ===\n';

    dbConfigs.forEach(db => {
      const prefix = getEnvVarPrefix(db.name);

      dbString += `\nDatabase: ${db.name} (${db.type})\n`;
      dbString += 'ENVIRONMENT VARIABLES\n';
      dbString += '=====================\n';
      dbString +=
        'These environment variables are set in the kernel for this database:\n';

      // Get actual env var names for this specific database
      const envVarNames = getDatabaseEnvVarNames(db);
      envVarNames.forEach(varName => {
        dbString += `  ${varName}\n`;
      });

      // Add connection example using CONNECTION_URL
      dbString += '\nCONNECTION EXAMPLE\n';
      dbString += '==================\n';

      if (
        db.type === DatabaseType.PostgreSQL ||
        db.type === DatabaseType.MySQL
      ) {
        // PostgreSQL and MySQL use CONNECTION_URL directly with SQLAlchemy
        const dialect =
          db.type === DatabaseType.MySQL ? 'mysql+pymysql' : 'postgresql';
        dbString += '```python\n';
        dbString += 'import os\n';
        dbString += 'from sqlalchemy import create_engine\n\n';
        dbString += `# CONNECTION_URL is pre-built: ${dialect}://user:pass@host:port/db\n`;
        if (db.type === DatabaseType.MySQL) {
          dbString += `# Note: Replace mysql:// with mysql+pymysql:// for PyMySQL driver\n`;
          dbString += `url = os.environ['${prefix}_CONNECTION_URL'].replace('mysql://', 'mysql+pymysql://')\n`;
          dbString += 'engine = create_engine(url)\n';
        } else {
          dbString += `engine = create_engine(os.environ['${prefix}_CONNECTION_URL'])\n`;
        }
        dbString += '```\n';
      } else if (db.type === DatabaseType.Snowflake) {
        dbString += '```python\n';
        dbString += 'import os\n';
        dbString += 'import snowflake.connector\n\n';
        dbString += `conn = snowflake.connector.connect(\n`;
        dbString += `    account=os.environ['${prefix}_ACCOUNT'],\n`;
        dbString += `    user=os.environ['${prefix}_USERNAME'],\n`;
        dbString += `    password=os.environ['${prefix}_PASSWORD'],\n`;
        dbString += `    database=os.environ.get('${prefix}_DATABASE'),\n`;
        dbString += `    warehouse=os.environ.get('${prefix}_WAREHOUSE'),\n`;
        dbString += `    role=os.environ.get('${prefix}_ROLE')\n`;
        dbString += ')\n';
        dbString += '```\n';
      } else if (db.type === DatabaseType.Databricks) {
        // Get auth type to show in context
        const creds = db.credentials as any;
        const authType = creds?.authType || 'pat';

        dbString += `Auth Type: ${authType}\n`;
        dbString += '```python\n';
        dbString += 'import os\n';
        dbString += 'from databricks import sql\n\n';
        if (authType === 'service_principal') {
          dbString += '# Service Principal (OAuth M2M) authentication\n';
          dbString += 'from databricks.sdk.core import oauth_service_principal\n\n';
          dbString += 'def credential_provider():\n';
          dbString += `    return oauth_service_principal(\n`;
          dbString += `        client_id=os.environ['${prefix}_CLIENT_ID'],\n`;
          dbString += `        client_secret=os.environ['${prefix}_CLIENT_SECRET']\n`;
          dbString += '    )\n\n';
          dbString += 'conn = sql.connect(\n';
          dbString += `    server_hostname=os.environ['${prefix}_HOST'],\n`;
          dbString += `    http_path=os.environ['${prefix}_WAREHOUSE_HTTP_PATH'],\n`;
          dbString += '    credentials_provider=credential_provider\n';
          dbString += ')\n';
        } else {
          dbString += '# Personal Access Token (PAT) authentication\n';
          dbString += 'conn = sql.connect(\n';
          dbString += `    server_hostname=os.environ['${prefix}_HOST'],\n`;
          dbString += `    http_path=os.environ['${prefix}_WAREHOUSE_HTTP_PATH'],\n`;
          dbString += `    access_token=os.environ['${prefix}_ACCESS_TOKEN']\n`;
          dbString += ')\n';
        }
        dbString += '\n# Execute queries\n';
        dbString += 'cursor = conn.cursor()\n';
        dbString += "cursor.execute('SELECT * FROM my_table LIMIT 10')\n";
        dbString += 'rows = cursor.fetchall()\n\n';
        dbString += '# Or load directly into pandas\n';
        dbString += 'import pandas as pd\n';
        dbString += "df = pd.read_sql('SELECT * FROM my_table', conn)\n";
        dbString += '```\n';
      }
    });

    dbString += '\n=== END DATABASE CONFIGURATIONS ===\n';
    dbString +=
      '\nUse CONNECTION_URL or the individual environment variables to connect. They are already set in the kernel.\n';

    return dbString;
  }

  /**
   * Get workspace context (only for welcome mode)
   */
  private getWorkspaceContext(mode: ChatMode): string {
    if (mode !== 'welcome') return '';

    const context = getWorkspaceContext();
    if (!context?.welcome_context) return '';

    return `=== WORKSPACE CONTEXT ===\n\n${context.welcome_context}\n\n=== END WORKSPACE CONTEXT ===`;
  }

  // ═══════════════════════════════════════════════════════════════
  // UTILITY METHODS
  // ═══════════════════════════════════════════════════════════════

  /**
   * Get user-inserted code snippets
   */
  private getUserSnippets(): string {
    const snippets = useSnippetStore.getState().getInsertedSnippets();
    if (snippets.length === 0) return '';

    let result = '=== USER SNIPPETS ===\n\n';
    snippets.forEach(snippet => {
      result += `Title: ${snippet.title}\n${snippet.content}\n\n`;
    });
    result += '=== END USER SNIPPETS ===';

    return result;
  }

  /**
   * Get user-selected cells from NotebookContextManager
   */
  private getUserSelectedCells(notebookId: string | null): string {
    if (!notebookId) return '';
    return this.notebookContextManager.formatContextAsMessage(notebookId);
  }
}
