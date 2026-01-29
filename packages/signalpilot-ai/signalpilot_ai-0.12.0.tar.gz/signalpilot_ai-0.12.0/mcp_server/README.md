# Sage MCP Server

Standalone FastAPI MCP server that hosts multiple tool namespaces (terminal, schema search, files, etc.).

## Setup

1. Create the conda environment:

   ```bash
   conda env create -f environment.yml
   ```

2. Create your `.env` file:

   ```bash
   cp .env.example .env
   ```

3. Add your Anthropic API key to `.env` (optional but required for LLM summaries).

## Run

From `mcp_server`:

```bash
uvicorn main:app --reload
```

## Tools

### Terminal

The terminal namespace provides command execution and file search tools.

#### Execute Command

Endpoint:

```
POST /terminal/execute
```

Example:

```bash
curl -s http://127.0.0.1:8000/terminal/execute -H "Content-Type: application/json" -d '{"command":"echo hello","description":"print a greeting","timeout_seconds":30}'
```

Behavior:

- Returns `stdout`, `stderr`, `exit_code`.
- If total output exceeds the configured line cap, output is truncated to head/tail and a summary is added.

#### Glob (File Search)

Endpoint:

```
POST /terminal/glob
```

Request fields:

- `pattern`: glob pattern to match files (e.g., `**/*.py`, `src/*.ts`).
- `path`: base directory to search in (default: current working directory).

Example:

```bash
curl -s http://127.0.0.1:8000/terminal/glob -H "Content-Type: application/json" -d '{"pattern":"**/*.py","path":"/project"}'
```

Response:

- `files`: list of matching file paths.
- `count`: number of files found.
- `error`: error message if search failed.

#### Grep (Content Search)

Endpoint:

```
POST /terminal/grep
```

Request fields:

- `pattern`: regex pattern to search for.
- `path`: file or directory to search in (default: current working directory).
- `glob`: glob pattern to filter files (e.g., `*.py`).
- `case_insensitive`: perform case-insensitive search (default: false).
- `context_lines`: number of context lines before and after each match (default: 0, max: 10).
- `max_results`: maximum number of matches to return (default: 100, max: 1000).

Example:

```bash
curl -s http://127.0.0.1:8000/terminal/grep -H "Content-Type: application/json" -d '{"pattern":"def main","path":"/project","glob":"*.py","context_lines":2}'
```

Response:

- `matches`: list of match objects containing `file`, `line_number`, `line`, `context_before`, `context_after`.
- `count`: total number of matches found.
- `truncated`: true if results were truncated due to max_results limit.
- `error`: error message if search failed.

### Schema Search

Endpoint:

```
POST /schema-search/search
```

Request fields:

- `query`: natural language question.
- `database_id`: logical database id that maps to `DATABASE_<ID>_URL` in `.env`.
- `limit`: number of tables to return (default: 5).
- `force_reindex`: reindex schema metadata (default: false).
- `force_refresh`: bypass LLM cache (default: false).

Example:

```bash
curl -s http://127.0.0.1:8000/schema-search/search   -H "Content-Type: application/json"   -d '{"query":"where are user refunds stored?","database_id":"analytics","limit":5,"force_reindex":false}'
```

Configuration:

- Default config lives at `configs/schema_search.yml`.
- Output formatting config lives at `configs/output_formatter.yml`.
- Agent config lives at `configs/agent.yml`.
- Search strategy is set there (BM25 by default, no reranker).

### Files

The files namespace provides two services: summarization and reading with pagination.

#### File Summarization

Endpoint:

```
POST /files/summarize
```

Request fields:

- `path`: absolute or relative path to the file.
- `force_refresh`: bypass LLM cache (default: false).

Example:

```bash
curl -s http://127.0.0.1:8000/files/summarize -H "Content-Type: application/json" -d '{"path":"/path/to/data.csv"}'
```

Behavior:

- Analyzes file and returns a summary of its structure and content.
- Currently supports CSV, Excel (.xlsx), and PDF files.
- For CSV: returns total row count, columns, statistical summary, missing values, and first 5 rows.
- For Excel: returns sheet names, total rows per sheet, columns per sheet, and first 5 rows per sheet.
- For PDF: returns total page count, metadata, table of contents, and first few pages of content.

#### File Reading

Endpoint:

```
POST /files/read
```

Request fields:

- `path`: absolute or relative path to the file.
- `start`: starting line/row/page (0-indexed, default: 0).
- `end`: ending line/row/page (exclusive, default: 100).

Example:

```bash
curl -s http://127.0.0.1:8000/files/read -H "Content-Type: application/json" -d '{"path":"/path/to/data.csv","start":0,"end":100}'
```

Behavior:

- Reads specific portions of files with pagination support.
- For CSV: reads rows from `start` to `end` (0-indexed).
- For Excel: reads rows sequentially across all sheets. If Sheet1 has 100 rows and Sheet2 has 50 rows, rows 0-99 are from Sheet1, rows 100-149 are from Sheet2.
- For PDF: reads pages from `start` to `end` (0-indexed).

Configuration:

- Default config lives at `configs/files.yml`.
- Handler-specific settings (e.g., `csv.max_rows_to_read`) can be customized.

#### Adding New File Type Handlers

To support a new file type:

1. Create summarizer and reader handlers in `namespaces/files/handlers/<type>/`:
   ```python
   # namespaces/files/handlers/json/summarizer.py
   class JSONSummarizer:
       def __init__(self, config: dict[str, Any]) -> None:
           self.config = config

       def summarize(self, path: Path) -> str:
           # Your implementation
           return summary_text
   
   # namespaces/files/handlers/json/reader.py
   class JSONReader:
       def __init__(self, config: dict[str, Any]) -> None:
           self.config = config

       def read(self, path: Path, start: int, end: int) -> tuple[str, int]:
           # Your implementation
           return content, total_lines
   ```

2. Add the file type and config to `configs/files.yml`:
   ```yaml
   supported_file_types:
     - csv
     - xlsx
     - pdf
     - json
   json:
     max_depth: 3
   ```

3. Register the handlers in `namespaces/files/summarizer.py` and `namespaces/files/reader.py`:
   ```python
   from namespaces.files.handlers.json.summarizer import JSONSummarizer
   from namespaces.files.handlers.json.reader import JSONReader
   
   # In summarizer.py __init__:
   self._summarizers = {
       "csv": CSVSummarizer(config["csv"]),
       "json": JSONSummarizer(config["json"]),
   }
   
   # In reader.py __init__:
   self._readers = {
       "csv": CSVReader(config["csv"]),
       "json": JSONReader(config["json"]),
   }
   ```

## Environment Variables

- `ANTHROPIC_API_KEY`: enables LLM summaries.
- `ANTHROPIC_MODEL`: optional model override (default: `claude-haiku-4-5`).
- `DATABASE_<ID>_URL`: connection string for schema search (e.g., `DATABASE_ANALYTICS_URL`).
- `SCHEMA_SEARCH_LLM_API_KEY`, `SCHEMA_SEARCH_LLM_BASE_URL`: only needed if you enable LLM chunking in schema-search config.

## Summaries and Truncation

- Truncation defaults live in `configs/output_formatter.yml`.
- The shared `OutputProcessor` truncates large outputs and triggers LLM summarization.
- Each namespace defines its own summarization prompt in `namespaces/<tool>/prompt.md`.

## LLM Response Caching

The server implements disk-based caching for LLM summary responses to reduce API costs and improve response times:

- **Cache Location**: `/tmp/.signalpilot_cache/llm_summary/`
- **Namespace Isolation**: Each tool namespace (terminal, schema_search, files) has its own cache directory
- **Cache Size**: Configurable in `configs/output_formatter.yml` (default: 10MB per namespace)
- **Eviction Policy**: Least-recently-used (LRU) when cache is full
- **Force Refresh**: All request models include a `force_refresh` field (default: `false`) to bypass cache

Configuration (`configs/output_formatter.yml`):
```yaml
cache_dir: /tmp/.signalpilot_cache/llm_summary
cache_size_limit_mb: 10
```

Example with force refresh:
```bash
curl -s http://127.0.0.1:8000/terminal/execute \
  -H "Content-Type: application/json" \
  -d '{"command":"echo hello","force_refresh":true}'
```

Cache key includes:
- Model name and configuration
- System prompt
- Full message history
- All request parameters

This ensures cache hits only occur for truly identical requests.

## Modify or Extend

Add a new tool namespace by following the existing structure:

1. Create `namespaces/<tool>/` with:
   - `models.py` for request/response schemas.
   - `service.py` for the tool implementation.
   - `router.py` for FastAPI endpoints.
   - `prompt.md` describing how to summarize output.
2. Register the router in `main.py` with a prefix and tag.
3. Add any per-tool constants in `namespaces/<tool>/constants.py`.
4. If the tool returns large outputs, use `namespaces/base/output_processor.py` to truncate and summarize.
5. Add any config files under `configs/` and document new environment variables in `.env.example`.

## Quick Troubleshooting

- If you see summaries that just echo output, verify `ANTHROPIC_API_KEY` is set and reachable.
- If schema search fails, check the `DATABASE_<ID>_URL` entry in `.env` and confirm the DB is reachable.
