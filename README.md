# AStockEvent MCP Server · A股公告事件 MCP 服务

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-blue)](https://modelcontextprotocol.io/)

**中文** | [English](#english)

---

> 把 A 股公告变成 AI Agent 能直接消费的结构化事件 Feed。

AStockEvent 将 A 股上市公司公告转化为**结构化语义事件**，让 AI Agent（Claude、ChatGPT、VSCode Copilot 等）通过 MCP 协议直接查询、分析、追踪。

---

## 目录

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [事件类型](#事件类型)
- [工具参考](#工具参考)
- [项目结构](#项目结构)
- [重要说明](#重要说明)
- [许可证](#许可证)

---

## 功能特性

- **5 种事件类型** — `share_reduction`（股东减持）、`delisting_risk`（ST/退市风险）、`regulatory_letter`（监管函/问询函）、`lockup_expiration`（限售股解禁）、`share_buyback`（股份回购）
- **3 个 MCP 工具** — `check_events`（批量查询）、`get_event_timeline`（生命周期追踪）、`get_upcoming_events`（提前预警）
- **结构化 Event JSON** — 每条事件包含 `structured_payload`（量化标签）、`confidence_tier`（verified/likely/uncertain 可信度三级）、`ai_summary`（AI 摘要）、完整 `timeline`（生命周期时间线）
- **免费额度** — 100 次/天免费
- **MCP stdio 传输** — 兼容 Claude Desktop / VSCode / 任何 MCP 协议兼容的 AI Agent

## 快速开始

### 1. 安装

```bash
pip install astockevent
```

### 2. Claude Desktop 配置

在 `claude_desktop_config.json` 中添加：

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

### 3. 在 Claude 中使用

配置完成后，Claude 会自动发现 3 个 MCP 工具：

- **查询事件**: "帮我查一下川润股份(002272)这周有没有减持公告"
- **追踪时间线**: "展示事件 c8a7f9e1-d2b4-4a3c-8d5e-1f6a9b3c7d4e 的完整生命周期"
- **提前预警**: "未来 7 天有哪些股票有限售股解禁？"

### 4. VSCode Copilot 配置

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

## 事件类型

| 事件类型 | 说明 | 典型生命周期 |
|---|---|---|
| `share_reduction` | 股东减持计划、进展、完成 | plan → in_progress → completed |
| `delisting_risk` | ST/退市风险警示 | warning → confirmed/resolved |
| `regulatory_letter` | 监管函/问询函/关注函 | pending_reply → replied/overdue |
| `lockup_expiration` | 限售股/定增解禁 | approaching → expired |
| `share_buyback` | 股份回购计划与实施 | plan → in_progress → completed |

## 工具参考

### `check_events` — 事件查询

在时间窗口内批量查询自选股的结构化公告事件。

**适用场景**: 检查特定股票近期事件、扫描自选股、按事件类型和日期范围筛选。

**不适用**: 实时股价、交易信号、主观评级（本工具只返回公开公告的结构化事实）。

**返回**: Event 对象 JSON 数组，按时间倒序排列。

| 参数 | 类型 | 说明 |
|---|---|---|
| `stock_codes` | string | 逗号分隔的 6 位股票代码。示例: `002272,600519,300750`。留空=全市场。 |
| `event_types` | string | 逗号分隔的事件类型。可选: `share_reduction,delisting_risk,regulatory_letter,lockup_expiration,share_buyback`。留空=全部。 |
| `since` | string | 起始日期 `YYYY-MM-DD`。默认: 7 天前。 |
| `limit` | integer | 最大返回条数。默认: 50，最大: 200。 |

### `get_event_timeline` — 事件时间线

获取单个事件的完整生命周期时间线。

**适用场景**: 已有 event_id，想查看完整历史、阶段变更和相关事件。

**不适用**: 搜索或浏览事件（请用 `check_events`）。

**返回**: 单个事件对象（含 timeline 数组），或 null（未找到）。

| 参数 | 类型 | 说明 |
|---|---|---|
| `event_id` | string（必填） | 事件 UUID v4。示例: `c8a7f9e1-d2b4-4a3c-8d5e-1f6a9b3c7d4e` |

### `get_upcoming_events` — 即将发生事件

获取未来 N 天内到期的事件（提前预警）。

**适用场景**: 想知道即将发生什么——解禁到期、减持截止日、监管回复截止日。

**不适用**: 历史事件数据（请用 `check_events`）。

**返回**: 即将发生的事件 JSON 数组，按到期日期升序排列。

| 参数 | 类型 | 说明 |
|---|---|---|
| `stock_codes` | string | 逗号分隔的 6 位股票代码。留空=全市场。 |
| `days` | integer | 向前查看天数。默认: 7，最大: 30。 |
| `event_types` | string | 逗号分隔的事件类型筛选。留空=全部。 |

## 项目结构

```
astockevent-mcp/
├── src/astockevent/
│   ├── mcp/                 # MCP Server（完整源码）
│   │   ├── server.py        # 3 个工具核心逻辑
│   │   ├── stdio_server.py  # MCP stdio 传输层
│   │   ├── __init__.py
│   │   └── __main__.py      # python -m astockevent.mcp 入口
│   ├── models/
│   │   └── schemas.py       # Event Schema（Pydantic 模型）
│   └── db/                  # 数据库层桩代码（完整实现在私有仓库）
├── web/                     # Web 看板（HTML/JS）
├── docs/
│   └── api-contract.md      # API 契约文档
└── README.md
```

## 重要说明

**本仓库是 AStockEvent 的公开子集**，包含 MCP Server + Event Schema + Web 看板 + API 文档。

MCP Server 代码依赖 `astockevent.db`，该模块在私有仓库中有完整实现。本仓库提供 `db/` 桩代码供参考，但**无法独立运行**。

> 完整可运行的 MCP Server 代码参见私有仓库 [zhoushukai-ui/astockevent](https://github.com/zhoushukai-ui/astockevent)（PRIVATE）。
> 完整后端（Extractors / Pipeline / Case Library / 部署脚本）也在私有仓库中。

## API 契约

完整 REST API + MCP Tool 规范见 [docs/api-contract.md](docs/api-contract.md)。

## 许可证

MIT License — 详见 [LICENSE](LICENSE)。

---

<a id="english"></a>

# English

> Transform A-share listed company announcements into structured event feeds that AI agents can directly consume.

AStockEvent transforms A-share listed company announcements into **structured semantic events**, enabling AI agents (Claude, ChatGPT, VSCode Copilot, etc.) to query, analyze, and track them through the MCP protocol.

---

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
