# AStockEvent MCP Server

Structured A-share announcement event feed for AI agents — directly consumable via MCP protocol.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-blue)](https://modelcontextprotocol.io/)

AStockEvent transforms A-share listed company announcements into **structured semantic events**, enabling AI agents (Claude, ChatGPT, VSCode Copilot, etc.) to query, analyze, and track them through the MCP protocol.

> A股公告结构化事件 Feed → AI Agent 可直接消费。

## Features

- **5 Event Types** — `share_reduction`, `delisting_risk` (ST/delisting), `regulatory_letter`, `lockup_expiration`, `share_buyback`
- **3 MCP Tools** — `check_events` (batch query), `get_event_timeline` (lifecycle tracking), `get_upcoming_events` (early warning)
- **Structured Event JSON** — each event includes `structured_payload` (quantitative tags), `confidence_tier` (verified/likely/uncertain), `ai_summary`, and full `timeline`
- **Free Tier** — 100 calls/day free
- **MCP stdio transport** — compatible with Claude Desktop / VSCode / any MCP-compatible AI agent

## Quick Start

### 1. Installation

```bash
pip install astockevent
```

### 2. Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "astockevent": {
      "command": "python",
      "args": ["-m", "astockevent.mcp"],
      "env": {
        "ASTOCKEVENT_API_KEY": "your_free_api_key"
      }
    }
  }
}
```

### 3. Usage in Claude

Once configured, Claude automatically discovers 3 MCP tools:

- **Check events**: "Check if 川润股份 (002272) has any share reduction announcements this week"
- **Track timeline**: "Show the full lifecycle of event c8a7f9e1-d2b4-4a3c-8d5e-1f6a9b3c7d4e"
- **Early warning**: "Which stocks have lockup shares expiring in the next 7 days?"

### 4. VSCode Copilot Configuration

```json
{
  "mcp": {
    "servers": {
      "astockevent": {
        "command": "python",
        "args": ["-m", "astockevent.mcp"],
        "env": {
          "ASTOCKEVENT_API_KEY": "your_free_api_key"
        }
      }
    }
  }
}
```

## Event Types

| Event Type | Description | Typical Lifecycle |
|---|---|---|
| `share_reduction` | Shareholder reduction plans, progress, completion | plan → in_progress → completed |
| `delisting_risk` | ST/delisting risk warnings | warning → confirmed/resolved |
| `regulatory_letter` | Regulatory/inquiry/concern letters | pending_reply → replied/overdue |
| `lockup_expiration` | Lockup share / private placement expiration | approaching → expired |
| `share_buyback` | Share buyback plans and implementation | plan → in_progress → completed |

## Tools Reference

### `check_events`

Query structured announcement events for a watchlist of stocks within a time window.

**Use when**: you need to check recent events for specific stocks, scan a watchlist, or filter by event type and date range.

**Do NOT use when**: you need real-time stock prices, trading signals, or subjective ratings (this tool only returns structured facts from public announcements).

**Returns**: JSON array of event objects, newest first.

| Parameter | Type | Description |
|---|---|---|
| `stock_codes` | string | Comma-separated 6-digit stock codes. Example: `002272,600519,300750`. Empty = all stocks. |
| `event_types` | string | Comma-separated event types. Options: `share_reduction,delisting_risk,regulatory_letter,lockup_expiration,share_buyback`. Empty = all. |
| `since` | string | Start date `YYYY-MM-DD`. Default: 7 days ago. |
| `limit` | integer | Max results. Default: 50, Max: 200. |

### `get_event_timeline`

Get the complete lifecycle timeline for a single event.

**Use when**: you have an event_id and want to see its full history, phase transitions, and related events.

**Do NOT use when**: you want to search or browse events (use `check_events` instead).

**Returns**: single event object with timeline array, or null if not found.

| Parameter | Type | Description |
|---|---|---|
| `event_id` | string (required) | Event UUID v4. Example: `c8a7f9e1-d2b4-4a3c-8d5e-1f6a9b3c7d4e` |

### `get_upcoming_events`

Get events due within the next N days (early warning).

**Use when**: you want to know what's coming up — expirations, deadlines, regulatory responses due.

**Do NOT use when**: you need historical event data (use `check_events`).

**Returns**: JSON array of upcoming events, ordered by due_date ascending.

| Parameter | Type | Description |
|---|---|---|
| `stock_codes` | string | Comma-separated 6-digit stock codes. Empty = all stocks. |
| `days` | integer | Days to look ahead. Default: 7, Max: 30. |
| `event_types` | string | Comma-separated event types to filter. Empty = all. |

## API Contract

See [docs/api-contract.md](docs/api-contract.md) for the complete REST API + MCP Tool specification.

## Project Structure

```
astockevent-mcp/
├── src/astockevent/
│   ├── mcp/                 # MCP Server (full source)
│   │   ├── server.py        # 3 Tool core logic
│   │   ├── stdio_server.py  # MCP stdio transport layer
│   │   ├── __init__.py
│   │   └── __main__.py      # python -m astockevent.mcp entry point
│   ├── models/
│   │   └── schemas.py       # Event Schema (Pydantic)
│   └── db/                  # Database layer stub (full impl in private repo)
├── web/                     # Web dashboard (HTML/JS)
├── docs/
│   └── api-contract.md      # API contract documentation
└── README.md
```

## Important Note

**This repository is the public subset of AStockEvent**, containing MCP Server + Event Schema + Web Dashboard + API documentation.

The MCP Server code depends on `astockevent.db`, which has a complete implementation in the private repository. This repository provides a `db/` stub for code reference, but **cannot run independently**.

> Full runnable MCP Server code is in the private repository [zhoushukai-ui/astockevent](https://github.com/zhoushukai-ui/astockevent) (PRIVATE).
> Complete backend (Extractors / Pipeline / Case Library / Deployment scripts) is also in the private repository.

## License

MIT License — see [LICENSE](LICENSE).
