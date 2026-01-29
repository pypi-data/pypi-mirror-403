# Sage Agent UI Tests

Playwright-based UI tests for the Sage Agent JupyterLab extension.

## Directory Structure

```
tests/
├── fixtures/
│   └── sage-test.ts       # Custom test fixtures with common setup
├── helpers/
│   ├── index.ts           # Export aggregator
│   ├── api-configurator.ts # JWT token setup
│   ├── chat-interactor.ts  # Chat interaction utilities
│   ├── notebook-manager.ts # Notebook creation utilities
│   ├── screenshot.ts       # Screenshot capture utilities
│   └── wait-helpers.ts     # Element waiting utilities
├── page-objects/
│   └── selectors.ts       # Centralized UI selectors
├── config.ts              # Test configuration (JWT token, prompts)
├── extension.spec.ts      # Basic extension loading tests
├── llm-states.spec.ts     # LLM state testing
├── diff-interactions.spec.ts # Diff approval workflow tests
└── long-running.spec.ts   # Extended duration tests
```

## Setup

1. Install dependencies:
   ```bash
   cd ui-tests
   jlpm install
   ```

2. Configure your JWT token in `tests/config.ts`:
   ```typescript
   SAGE_JWT_TOKEN: 'your-jwt-token-here'
   ```

3. Ensure the extension is built:
   ```bash
   cd ..
   jlpm build
   ```

## Running Tests

### Run all tests
```bash
jlpm test
```

### Run specific test categories

```bash
# Extension loading tests (no JWT required)
jlpm test:extension

# LLM state tests
jlpm test:llm

# Diff interaction tests
jlpm test:diffs

# Long-running tests (10 min timeout)
jlpm test:long
```

### Run individual tests

```bash
# By test name pattern
jlpm playwright test --grep "should load the extension"

# By file
jlpm playwright test tests/extension.spec.ts

# By project
jlpm playwright test --project=extension
```

### Debug mode

```bash
# Interactive debug mode
jlpm test:debug

# Playwright UI mode
jlpm test:ui

# Headed mode (see browser)
jlpm test:headed
```

## Test Categories

### Extension Tests (`extension.spec.ts`)
Basic tests that verify the extension loads correctly. **No JWT token required.**

- `should load the extension` - Verifies JupyterLab loads with extension
- `should have sage AI window with chat input` - Verifies chat UI components

### LLM State Tests (`llm-states.spec.ts`)
Tests chat interactions and LLM response handling. **Requires JWT token.**

- `chatbox opens and is ready` - Verifies chat is initialized
- `single file diff states` - Tests single diff generation and approval

### Diff Interaction Tests (`diff-interactions.spec.ts`)
Tests the diff approval workflow. **Requires JWT token.**

- `inline chat diffs` - Tests hover buttons on diff items
- `state display diffs` - Tests diff summary bar interactions
- `navigation widget - reject all` - Tests "Reject All" button
- `navigation widget - approve all` - Tests "Approve All" button
- `navigation widget - run all` - Tests "Run All" button
- `inline cell diffs with codemirror` - Tests CodeMirror chunk buttons

### Long Running Tests (`long-running.spec.ts`)
Extended tests with 10-minute timeout. **Requires JWT token.**

- `sp500 analysis with user reply handling` - Complex multi-turn conversation test

## Configuration Options

### Environment Variables

- `SAGE_JWT_TOKEN` - JWT token (can also be set in config.ts)
- `CI` - Set in CI environments to disable server reuse

### Playwright Config

The `playwright.config.js` supports:
- Multiple projects for different test categories
- Screenshot on failure
- Trace recording on retry
- Video recording for debugging

## Writing New Tests

### Using Fixtures

For tests that need the full Sage setup (notebook + chat):

```typescript
import { test, expect, ChatInteractor, Selectors } from './fixtures/sage-test';

test('my test', async ({ notebookWithChat: page }) => {
  // page has notebook created and chat ready
  await ChatInteractor.sendMessage(page, 'Hello');
});
```

For basic tests without JWT:

```typescript
import { test, expect } from '@jupyterlab/galata';
import { Selectors } from './page-objects/selectors';

test('my test', async ({ page, baseURL }) => {
  await page.goto(`${baseURL}`);
  // ...
});
```

### Using Helpers

```typescript
import { ChatInteractor, ResponseState } from './helpers';

// Send message and wait for response
await ChatInteractor.sendMessage(page, 'Create a cell');
const state = await ChatInteractor.waitForResponse(page);

if (state === ResponseState.DIFF) {
  // Handle diff approval
}
```

### Using Selectors

```typescript
import { Selectors } from './page-objects/selectors';

// Use centralized selectors
await page.click(Selectors.chat.sendButton);
await page.waitForSelector(Selectors.diff.list);
```

## Debugging

### View Test Report
```bash
jlpm report
```

### View Trace
```bash
jlpm playwright show-trace test-results/[test-name]/trace.zip
```

### Screenshots
Screenshots are saved to `./screenshots/` organized by test name.

### Videos
Videos are recorded on first retry and saved to `./test-results/`.
