# claude_traces_client

Extract and upload Claude Code traces to a configurable endpoint.

## Installation

```bash
pip install claude-traces-client
```

Or install from source:

```bash
cd claude_traces_client
pip install -e .
```

## Usage

```python
from claude_traces_client import traced
from claude_code_sdk import query, ClaudeCodeOptions

# Endpoint read from CLAUDE_TRACES_ENDPOINT env var (default: https://claudetraces.dev/api/trace)
async for msg in traced(query(prompt="Hello", options=opts)):
    print(msg)  # Messages flow through unchanged
# Trace is POSTed automatically after iteration completes
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `CLAUDE_TRACES_ENDPOINT` | `https://claudetraces.dev/api/trace` | URL to POST traces to |

## API

### `traced(messages, *, project_path=None, headers=None, timeout=30.0, raise_on_upload_error=False)`

Wrap a Claude SDK message iterator to upload traces after completion.

**Parameters:**
- `messages`: AsyncIterator from `query()` or `ClaudeSDKClient`
- `project_path`: Project path for trace lookup (default: cwd)
- `headers`: Optional headers for the POST request (e.g., `{"Authorization": "Bearer ..."}`)
- `timeout`: Upload timeout in seconds
- `raise_on_upload_error`: If True, raise on upload failure; if False, silently continue

**Yields:** Messages unchanged from the underlying iterator

## How It Works

1. Wraps the Claude SDK's async message iterator
2. Captures the `session_id` from the first `SystemMessage` with `subtype='init'`
3. After iteration completes, reads the trace file from `~/.claude/projects/<encoded-path>/<session_id>.jsonl`
4. POSTs the trace contents to the configured endpoint with `Content-Type: application/x-ndjson`

## Trace File Location

Claude Code writes traces to:
```
~/.claude/projects/<encoded-path>/<session_id>.jsonl
```

Where `<encoded-path>` is the project path with `/` replaced by `-` (e.g., `/Users/foo/bar` becomes `-Users-foo-bar`).
