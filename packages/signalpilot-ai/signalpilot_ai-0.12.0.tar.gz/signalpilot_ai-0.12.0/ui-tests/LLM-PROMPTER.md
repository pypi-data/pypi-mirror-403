# LLM Prompter Test

A configurable Playwright test for running custom prompts through the Sage AI assistant and capturing the results.

## Prerequisites

1. **Environment Setup**: Ensure you have a `.env` file in the `ui-tests/` directory with your JWT token:
   ```
   SAGE_JWT_TOKEN=your_jwt_token_here
   ```

2. **Dependencies**: Install dependencies if not already done:
   ```bash
   cd ui-tests
   yarn install
   yarn playwright install
   ```

3. **JupyterLab**: Either let the test start JupyterLab automatically, or start it manually:
   ```bash
   yarn start
   ```

## Running the Test

### Headed Mode (see the browser)
```bash
cd ui-tests
yarn playwright test --project=llm-prompter --headed --retries=0
```

### Headless Mode (background)
```bash
cd ui-tests
yarn playwright test --project=llm-prompter --retries=0
```

## Configuring the Prompt

Edit the constants at the top of `ui-tests/tests/llm-prompter.spec.ts`:

```typescript
// ============================================================
// CONFIGURE YOUR PROMPT HERE
// ============================================================
const PROMPT = 'write hello world 3 times';  // Your custom prompt
const TEST_NAME = 'llm_prompter';             // Test identifier for logs
const MAX_LOOPS = 10;                         // Max response iterations
// ============================================================
```

### Configuration Options

| Constant | Description |
|----------|-------------|
| `PROMPT` | The message sent to the AI assistant |
| `TEST_NAME` | Identifier used in logs (doesn't affect output files) |
| `MAX_LOOPS` | Maximum number of response cycles before test ends |

## Test Behavior

The test follows this flow:

1. Creates a new Jupyter notebook
2. Sets up JWT authentication
3. Sends your configured prompt to the chat
4. Handles responses in a loop:
   - **DIFF state**: Clicks "Run All" / "Approve All" buttons
   - **WAITING_FOR_USER state**:
     - First occurrence: Responds with "Continue"
     - Second occurrence: Ends test
   - **FINISHED state**: Ends test
5. Downloads artifacts (thread JSON + notebook)

## Output Files

After the test completes, artifacts are saved to:
```
ui-tests/test-results/llm-prompter-LLM-Prompter-custom-prompt-test-llm-prompter/
```

### Generated Files

| File | Description |
|------|-------------|
| `thread_<prompt_excerpt>_<date>.json` | Full conversation thread with all messages, tool calls, and responses |
| `<notebook_name>.ipynb` | The Jupyter notebook with all generated cells and outputs |

### Example Output Structure
```
test-results/
└── llm-prompter-LLM-Prompter-custom-prompt-test-llm-prompter/
    ├── thread_write_hello_world_3_times_2026-01-20.json
    └── Untitled6.ipynb
```

## Thread JSON Format

The thread JSON contains the full conversation history:

```json
{
  "threadId": "...",
  "threadName": "...",
  "messages": [
    {
      "role": "user",
      "content": "write hello world 3 times"
    },
    {
      "role": "assistant",
      "content": "...",
      "tool_calls": [...]
    }
  ],
  "createdAt": "...",
  "updatedAt": "..."
}
```

## Tips

- **Longer prompts**: Increase `MAX_LOOPS` for complex multi-step tasks
- **Quick tests**: Use simple prompts like "print hello" for fast iteration
- **Debugging**: Run with `--headed` to watch the browser interaction
- **Failed tests**: Check `test-results/` for error screenshots and context
