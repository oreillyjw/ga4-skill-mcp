# Google Analytics 4 — Claude Code Skill + MCP Server

A [Claude Code skill](https://docs.anthropic.com/en/docs/claude-code/skills) and [MCP server](https://modelcontextprotocol.io/) that lets Claude query your GA4 properties using natural language. Works with Claude Code (skill mode) and Claude Desktop / any MCP client (server mode).

## Inspiration

This skill was inspired by Anthony Lee's article [How to Set Up Google Analytics as a Claude Code Skill](https://www.linkedin.com/pulse/how-set-up-google-analytics-claude-code-skill-anthony-lee-r0n4e/) (February 2026), which walks through connecting GA4 data to Claude Code via a service account and Python query script.

## Prerequisites

- Python 3.9+
- A Google Cloud project with the **Google Analytics Data API** and **Google Analytics Admin API** enabled
- A service account with a JSON key file
- The service account added as a **Viewer** (or higher) on each GA4 property you want to query

## Installation

### 1. Copy the skill into your Claude Code skills directory

```bash
# Global (all projects)
cp -r ga4-skill-mcp ~/.claude/skills/ga4-skill-mcp

# Or project-level (single repo)
cp -r ga4-skill-mcp .claude/skills/ga4-skill-mcp
```

### 2. Set up a Python virtual environment

Create a venv (or use an existing one) and install dependencies:

```bash
# Create the venv
python3 -m venv ~/.claude/venv

# Install dependencies
~/.claude/venv/bin/pip install -r ~/.claude/skills/ga4-skill-mcp/requirements.txt
```

This installs:

- `google-analytics-data` — GA4 Data API client
- `google-analytics-admin` — GA4 Admin API client (for listing properties)

### 3. Configure environment variables

Add to `~/.claude/settings.json` (global) or `.claude/settings.local.json` (project-level):

```json
{
  "env": {
    "SKILLS_PYTHON": "/path/to/your/venv/bin/python3",
    "GA4_CREDENTIALS_PATH": "/absolute/path/to/service-account.json",
    "GA4_PROPERTY_ID": "123456789"
  }
}
```

- `SKILLS_PYTHON` — path to the venv's Python binary. Claude uses this to run the query scripts.
- `GA4_PROPERTY_ID` — optional if you always pass `--property-id` or only use the `properties` report.

## Verify It Works

Run these commands to confirm the skill is set up correctly. Each test builds on the previous one. Replace the venv path below with your actual path.

### Test 1: Check dependencies are installed

```bash
~/.claude/venv/bin/python3 -c "from google.analytics.data_v1beta import BetaAnalyticsDataClient; print('OK: google-analytics-data')"
~/.claude/venv/bin/python3 -c "from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient; print('OK: google-analytics-admin')"
```

Both should print `OK`. If not, re-run the pip install step.

### Test 2: Check credentials file exists

```bash
~/.claude/venv/bin/python3 -c "
import os, json
path = os.environ.get('GA4_CREDENTIALS_PATH', '')
assert path, 'GA4_CREDENTIALS_PATH not set'
assert os.path.exists(path), f'File not found: {path}'
with open(path) as f:
    data = json.load(f)
print(f'OK: service account = {data.get(\"client_email\", \"UNKNOWN\")}')
"
```

Should print the service account email. If it says `not set`, check your `settings.json` env block.

### Test 3: List accessible properties (no property ID needed)

```bash
~/.claude/venv/bin/python3 ~/.claude/skills/ga4-skill-mcp/ga_query.py --report properties
```

Should return a table of accounts and properties. If you see `No GA4 accounts found`, the service account doesn't have access to any GA4 properties — add it via GA4 Admin > Property Access Management.

### Test 4: Pull a real report

```bash
~/.claude/venv/bin/python3 ~/.claude/skills/ga4-skill-mcp/ga_query.py --report overview --days 7
```

Should return a summary with users, sessions, page views, etc. If you get a permissions error, confirm the service account email from Test 2 has Viewer access on the GA4 property.

### Test 5: Verify multi-property support

```bash
# Query a different property without changing env vars
~/.claude/venv/bin/python3 ~/.claude/skills/ga4-skill-mcp/ga_query.py --report overview --property-id 987654321 --days 7
```

## Usage with Claude Code

Once installed, just ask Claude naturally:

- "How many users visited in the last 30 days?"
- "Show me the top 10 pages by views this week"
- "What are my traffic sources for the last 7 days?"
- "Show me the daily trend for the past month"
- "List all my GA4 properties"
- "Compare traffic sources for property 123456789 vs 987654321"

## Available Reports

| Report | Description |
|--------|-------------|
| `properties` | List all GA4 accounts and properties the service account can access |
| `overview` | High-level summary: users, sessions, page views, bounce rate |
| `pages` | Top pages by views |
| `sources` | Traffic sources (source/medium breakdown) |
| `countries` | Geographic breakdown |
| `devices` | Device category breakdown (desktop/mobile/tablet) |
| `daily` | Day-by-day trend |
| `realtime` | Active users right now |
| `custom` | Custom query with any GA4 metrics and dimensions |

## Multi-Property Usage

Set a default property via env var, override per-query:

```bash
# Uses GA4_PROPERTY_ID from env
$SKILLS_PYTHON ga_query.py --report overview

# Override for a different property
$SKILLS_PYTHON ga_query.py --report overview --property-id 987654321
```

Or skip setting a default entirely and always pass `--property-id`.

## Output Formats

All reports support `--output table` (default), `--output json`, and `--output csv`.

## MCP Server Setup

The MCP server (`ga_mcp_server.py`) wraps the same query logic as individual tools, so any MCP-compatible client (Claude Desktop, Cursor, etc.) can call them directly.

### 1. Install the additional dependency

```bash
~/.claude/venv/bin/pip install "mcp>=1.0.0"
```

This is already included in `requirements.txt`.

### 2. Configure your MCP client

**Claude Desktop** — add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "/path/to/your/venv/bin/python3",
      "args": ["/path/to/ga4-skill-mcp/ga_mcp_server.py"],
      "env": {
        "GA4_CREDENTIALS_PATH": "/absolute/path/to/service-account.json",
        "GA4_PROPERTY_ID": "123456789"
      }
    }
  }
}
```

**Claude Code** — add to `~/.claude/settings.json` or `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "/path/to/your/venv/bin/python3",
      "args": ["/path/to/ga4-skill-mcp/ga_mcp_server.py"],
      "env": {
        "GA4_CREDENTIALS_PATH": "/absolute/path/to/service-account.json",
        "GA4_PROPERTY_ID": "123456789"
      }
    }
  }
}
```

### 3. Verify the server starts

```bash
~/.claude/venv/bin/python3 /path/to/ga4-skill-mcp/ga_mcp_server.py
```

The server runs over stdio — you should see no output (it's waiting for MCP messages). Press `Ctrl+C` to stop.

### Available MCP Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `ga_properties` | — | List all GA4 accounts and properties |
| `ga_overview` | `days`, `property_id` | High-level summary: users, sessions, page views, bounce rate |
| `ga_pages` | `days`, `limit`, `property_id` | Top pages by views |
| `ga_sources` | `days`, `limit`, `property_id` | Traffic sources (source/medium) |
| `ga_countries` | `days`, `limit`, `property_id` | Geographic breakdown |
| `ga_devices` | `days`, `property_id` | Device category breakdown |
| `ga_daily` | `days`, `property_id` | Day-by-day trend |
| `ga_realtime` | `limit`, `property_id` | Active users right now |
| `ga_custom` | `metrics`, `dimensions`, `days`, `limit`, `property_id` | Custom query with any GA4 metrics/dimensions |

All parameters are optional — defaults: `days=30`, `limit=10`.

## File Structure

```text
ga4-skill-mcp/
├── SKILL.md           # Claude Code skill definition (auto-loaded by Claude)
├── README.md          # This file
├── ga_query.py        # Query script (CLI + importable module)
├── ga_mcp_server.py   # MCP server (wraps ga_query as tools)
└── requirements.txt   # Python dependencies
```

## License

MIT
