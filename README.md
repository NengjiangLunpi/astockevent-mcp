# AStockEvent MCP Server · A股公告事件 MCP 服务

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-blue)](https://modelcontextprotocol.io/)

**中文** | [English](#english)

---

> 把 A 股公告变成 AI Agent 能直接消费的结构化事件 Feed。

巨潮/东方财富给你公告原文。AStockEvent 给你 AI 可直接消费的结构化事件——及时、快速、不用等日终跑批。

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

- **13+ 种事件类型** — 减持、ST/退市、监管函、限售解禁、回购、重组、停复牌、质押、业绩预告、增持、分红、违规处罚、可转债
- **16 个 MCP 工具** — 按股票/类型/股东查询、事件详情/时间线、提前预警、分红/违规/重组/股东/风险/监管专用入口、可转债、基金穿透、可信度报告
- **结构化 Event JSON** — 每条事件包含 `structured_payload`（量化标签）、`confidence_tier`（verified/likely/uncertain 可信度三级）、`ai_summary`（AI 摘要）、`ai_context`（严重度/情绪）、完整 `timeline`（生命周期时间线）
- **免费额度** — 100 次/天，注册后 200 次/天。付费功能开发中，[注册获取 API Key →](https://astockevent.com/register)
- **MCP stdio 传输** — 兼容 Claude Desktop / VSCode / 任何 MCP 协议兼容的 AI Agent
- **零本地依赖** — MCP Server 是 REST API 薄代理，无需数据库、无需数据采集

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

配置完成后，Claude 会自动发现 16 个 MCP 工具：

- **按股票查询**: "帮我查一下川润股份(002272)这周有没有减持公告"
- **按类型扫描**: "最近全市场有哪些 ST/退市风险预警？"
- **事件详情**: "展示事件 c8a7f9e1-d2b4-4a3c-8d5e-1f6a9b3c7d4e 的完整数据"
- **提前预警**: "未来 7 天有哪些股票有限售股解禁？"
- **可转债**: "最近有哪些可转债触发强赎？"
- **基金穿透**: "华夏成长混合(000001)的重仓股最近有什么事件？"
- **可信度**: "这个减持事件的提取可信度如何？"

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

### Tier 1（MVP — 核心事件）

| 事件类型 | 说明 | 典型生命周期 |
|---|---|---|
| `share_reduction` | 股东减持计划、进展、完成 | plan → in_progress → completed |
| `delisting_risk` | ST/退市风险警示 | warning → confirmed / remediation |
| `regulatory_letter` | 监管函/问询函/关注函 | pending_reply → replied / overdue |
| `lockup_expiration` | 限售股/定增解禁 | approaching → expiring_soon → expired |
| `share_buyback` | 股份回购计划与实施 | plan → in_progress → completed |

### Tier 2（Phase 2 — 高频高价值）

| 事件类型 | 说明 | 典型生命周期 |
|---|---|---|
| `asset_restructuring` | 重大资产重组/并购 | plan → regulatory_review → approved / rejected / completed |
| `trading_halt_resume` | 停牌/复牌 | halted → extended → resumed |
| `pledge_risk` | 质押/补充质押/解除质押/违约处置 | new_pledge → active → released / default_disposal |
| `earnings_forecast` | 业绩预告/快报/修正 | first_forecast → revised_up/down → final_report |

### Tier 3（Phase 2 — 扩展覆盖）

| 事件类型 | 说明 | 典型生命周期 |
|---|---|---|
| `share_increase` | 大股东/董监高增持计划 | plan → in_progress → completed / terminated |
| `dividend` | 现金分红/送股/转增 | plan → approved → completed / cancelled |
| `violation_penalty` | 立案调查/行政处罚/市场禁入 | filed → investigating → final_penalty / dismissed |

## 工具参考

### 核心查询（7 个）

| 工具 | 说明 | 关键参数 |
|------|------|------|
| `search_events_by_stock` | 按股票代码查询事件 | `stock_codes`（必填） |
| `search_events_by_type` | 按事件类型全市场扫描 | `event_types`（必填） |
| `search_events_by_shareholder` | 按股东名称追踪 | `shareholder_name`（必填） |
| `search_events` | **万能入口** — 支持全部筛选器（股票/类型/严重度/情绪/可转债子类型/日期/股东） | 全部可选 |
| `get_event_detail` | 获取单条事件完整数据（含 structured_payload） | `event_id`（必填） |
| `get_event_timeline` | 获取单条事件生命周期时间线 | `event_id`（必填） |
| `get_upcoming_events` | 未来 N 天到期事件提前预警 | `days`（默认 7，最大 30） |

### 专用入口（7 个）— 预筛选的领域工具

| 工具 | 覆盖事件类型 | 用途 |
|------|------|------|
| `search_dividend_events` | `dividend` | 分红/送转公告、除权日、派息率 |
| `search_violation_events` | `violation_penalty` | 违规处罚、立案调查、行政处罚 |
| `search_restructuring_events` | `asset_restructuring` | 重大资产重组、并购、借壳 |
| `search_shareholder_events` | `share_reduction, share_increase, share_buyback, pledge_risk` | 股东行为全景（减持/增持/回购/质押） |
| `search_risk_events` | `delisting_risk, pledge_risk, trading_halt_resume, lockup_expiration` | 风险预警（ST/质押/停复牌/解禁） |
| `search_regulatory_events` | `regulatory_letter, violation_penalty` | 监管信号（问询函/关注函/处罚） |
| `search_cb_events` | `cb_event` | 可转债（强赎/回售/下修/到期） |

### 穿透 & 验证（2 个）

| 工具 | 说明 | 关键参数 |
|------|------|------|
| `search_fund_events` | 基金穿透 — 输入基金代码 → 重仓股 × 事件交叉，按 impact_score 排序 | `fund_code`（必填） |
| `get_trust_report` | 可信度报告 — 多源交叉验证、提取质量指标 | `event_id`（必填） |

> **向后兼容**: `check_events` 仍可用（已弃用，指向 `search_events`）。
> 完整参数参见 MCP 工具自身的 `inputSchema`（AI Agent 会自动读取）。

## 项目结构

```
astockevent-mcp/
├── src/astockevent/
│   ├── mcp/                 # MCP Server（完整源码）
│   │   ├── server.py        # 16 个工具核心逻辑 + dispatch
│   │   ├── stdio_server.py  # MCP stdio 传输层 + Tool 注册
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

**本仓库是 AStockEvent 的公开子集（Public Subset）**，仅包含 MCP Server + Event Schema + Web 看板 + API 文档。

### 公开 vs 私有仓库隔离

| 内容 | 公开 `astockevent-mcp` | 私有 `astockevent` |
|------|:--:|:--:|
| MCP Server 源码（`server.py`, `stdio_server.py`, `__init__.py`, `__main__.py`） | ✅ | ✅（主副本） |
| Event Schema（`schemas.py`） | ✅ | ✅（主副本） |
| Web 看板（HTML/JS） | ✅ | ✅（主副本） |
| pyproject.toml | ✅（精简 3 deps） | ✅（完整） |
| API Contract（`docs/api-contract.md`） | ✅ | ✅（主副本） |
| Extractor 引擎（`extractors/`） | ❌ | ✅ |
| 数据管线（`pipeline/`） | ❌ | ✅ |
| Case Library（`case_library.py`） | ❌ | ✅ |
| 数据库迁移（`migrations/`） | ❌ | ✅ |
| 部署脚本（`scripts/deploy.py`） | ❌ | ✅ |
| 服务器配置/密钥 | ❌ | ✅ |
| Golden Dataset（`data/golden/`） | ❌ | ✅ |

**同步规则**：
- 仅 MCP Server（`server.py`, `stdio_server.py`, `__init__.py`, `__main__.py`）、Event Schema、Web 看板、API 文档可同步
- 私有 repo MCP 文件变更时自动触发同步（Dev Agent 执行）
- `pyproject.toml` 公共版保持精简（仅 3 个依赖），与私有版不同
- 同步前自动确认无硬编码 IP/密钥/内部路径泄露

**安全红线**：
- 公开 repo 不包含任何数据库连接信息、API 密钥、服务器 IP
- 公开 repo 不包含 Extractor 引擎（核心竞争力）
- 公开 repo 不包含 Golden Dataset（护城河资产）

MCP Server 是 REST API 的薄代理层——通过 HTTP 连接 `api.astockevent.com`，不包含数据库或管线逻辑。

> 完整后端代码参见私有仓库 [NengjiangLunpi/astockevent](https://github.com/NengjiangLunpi/astockevent)（PRIVATE）。

## 联系方式

- **邮箱**: [astockevent@outlook.com](astockevent@outlook.com)
- **API 注册**: [astockevent.com/register](https://astockevent.com/register)
- **GitHub Issues**: [公开 repo](https://github.com/NengjiangLunpi/astockevent-mcp/issues)

## API 契约

完整 REST API + MCP Tool 规范见 [docs/api-contract.md](docs/api-contract.md)。

## 许可证

MIT License — 详见 [LICENSE](LICENSE)。

---

<a id="english"></a>

# English

> Transform A-share listed company announcements into structured event feeds that AI agents can directly consume.

Cninfo/Eastmoney gives you raw announcements. AStockEvent gives you AI-ready structured events — timely, fast, no batch processing needed.

AStockEvent transforms A-share listed company announcements into **structured semantic events**, enabling AI agents (Claude, ChatGPT, VSCode Copilot, etc.) to query, analyze, and track them through the MCP protocol.

---

## Features

- **13+ Event Types** — share reduction, ST/delisting risk, regulatory letters, lockup expiration, buybacks, restructuring, trading halts, pledge risk, earnings forecasts, share increase, dividends, violations, convertible bonds
- **16 MCP Tools** — query by stock/type/shareholder, event detail & timeline, early warning, 6 domain-specialized tools (dividend/violation/restructuring/shareholder/risk/regulatory), convertible bonds, fund penetration, trust reports
- **Structured Event JSON** — each event includes `structured_payload` (quantitative tags), `confidence_tier` (verified/likely/uncertain), `ai_summary`, `ai_context` (severity/sentiment), and full `timeline`
- **Free Tier** — 100 calls/day, 200 calls/day after registration. Paid plans coming soon. [Register for API Key →](https://astockevent.com/register)
- **MCP stdio transport** — compatible with Claude Desktop / VSCode / any MCP-compatible AI agent
- **Zero Local Dependencies** — MCP Server is a thin REST API proxy. No database, no data collection needed.

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

Once configured, Claude automatically discovers 16 MCP tools:

- **By stock**: "Check if 川润股份 (002272) has any share reduction announcements this week"
- **By type**: "Show me all ST/delisting risk warnings across the market"
- **Event detail**: "Show the full timeline of event c8a7f9e1-d2b4-4a3c-8d5e-1f6a9b3c7d4e"
- **Early warning**: "Which stocks have lockup shares expiring in the next 7 days?"
- **Convertible bonds**: "Any convertible bonds triggering forced redemption recently?"
- **Fund penetration**: "What events happened to 华夏成长混合 (000001)'s heavy holdings?"
- **Trust report**: "How reliable is the extraction for this share reduction event?"

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

### Tier 1 (MVP — Core Events)

| Event Type | Description | Typical Lifecycle |
|---|---|---|
| `share_reduction` | Shareholder reduction plans, progress, completion | plan → in_progress → completed |
| `delisting_risk` | ST/delisting risk warnings | warning → confirmed / remediation |
| `regulatory_letter` | Regulatory/inquiry/concern letters | pending_reply → replied / overdue |
| `lockup_expiration` | Lockup share / private placement expiration | approaching → expiring_soon → expired |
| `share_buyback` | Share buyback plans and implementation | plan → in_progress → completed |

### Tier 2 (Phase 2 — High Frequency, High Value)

| Event Type | Description | Typical Lifecycle |
|---|---|---|
| `asset_restructuring` | Major asset restructuring / M&A | plan → regulatory_review → approved / rejected / completed |
| `trading_halt_resume` | Trading halt / resumption | halted → extended → resumed |
| `pledge_risk` | Share pledge / supplementary pledge / release / default | new_pledge → active → released / default_disposal |
| `earnings_forecast` | Earnings forecast / flash report / revision | first_forecast → revised_up/down → final_report |

### Tier 3 (Phase 2 — Extended Coverage)

| Event Type | Description | Typical Lifecycle |
|---|---|---|
| `share_increase` | Major shareholder / insider increase plan | plan → in_progress → completed / terminated |
| `dividend` | Cash dividend / stock dividend / capital reserve transfer | plan → approved → completed / cancelled |
| `violation_penalty` | Regulatory investigation / administrative penalty / market ban | filed → investigating → final_penalty / dismissed |

## Tools Reference

### Core Query (7)

| Tool | Description | Key Parameter |
|------|------|------|
| `search_events_by_stock` | Query events for specific stock codes | `stock_codes` (required) |
| `search_events_by_type` | Market-wide scan by event type | `event_types` (required) |
| `search_events_by_shareholder` | Track events by shareholder name | `shareholder_name` (required) |
| `search_events` | **Universal escape hatch** — all filters (stock/type/severity/sentiment/CB sub-type/date/shareholder) | All optional |
| `get_event_detail` | Full event record with structured_payload | `event_id` (required) |
| `get_event_timeline` | Event lifecycle timeline | `event_id` (required) |
| `get_upcoming_events` | Upcoming deadlines (next N days) | `days` (default 7, max 30) |

### Domain-Specialized (7) — Pre-filtered convenience tools

| Tool | Event Types Covered | Use Case |
|------|------|------|
| `search_dividend_events` | `dividend` | Dividend/ex-rights/payout announcements |
| `search_violation_events` | `violation_penalty` | Regulatory investigations, penalties, fines |
| `search_restructuring_events` | `asset_restructuring` | M&A, asset injections, reverse mergers |
| `search_shareholder_events` | `share_reduction, share_increase, share_buyback, pledge_risk` | Insider activity panorama |
| `search_risk_events` | `delisting_risk, pledge_risk, trading_halt_resume, lockup_expiration` | Early warning signals |
| `search_regulatory_events` | `regulatory_letter, violation_penalty` | Exchange regulatory scrutiny |
| `search_cb_events` | `cb_event` | Convertible bonds (forced redemption/put-back/conversion price adjustment/maturity) |

### Penetration & Verification (2)

| Tool | Description | Key Parameter |
|------|------|------|
| `search_fund_events` | Fund penetration — fund code → holdings × events, sorted by impact_score | `fund_code` (required) |
| `get_trust_report` | Trust/verification report — cross-validation & extraction quality metrics | `event_id` (required) |

> **Backward compat**: `check_events` still works (deprecated, points to `search_events`).
> Full parameter details are in each tool's `inputSchema` (AI agents read them automatically).

## API Contract

See [docs/api-contract.md](docs/api-contract.md) for the complete REST API + MCP Tool specification.

## Project Structure

```
astockevent-mcp/
├── src/astockevent/
│   ├── mcp/                 # MCP Server (full source)
│   │   ├── server.py        # 16 Tool core logic + dispatch
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

**This repository is the public subset of AStockEvent**, containing only MCP Server + Event Schema + Web Dashboard + API documentation.

### Public vs Private Repository Separation

| Component | Public `astockevent-mcp` | Private `astockevent` |
|------|:--:|:--:|
| MCP Server source (`server.py`, `stdio_server.py`, `__init__.py`, `__main__.py`) | ✅ | ✅ (canonical) |
| Event Schema (`schemas.py`) | ✅ | ✅ (canonical) |
| Web Dashboard (HTML/JS) | ✅ | ✅ (canonical) |
| pyproject.toml | ✅ (slim, 3 deps) | ✅ (full) |
| API Contract (`docs/api-contract.md`) | ✅ | ✅ (canonical) |
| Extractor Engine (`extractors/`) | ❌ | ✅ |
| Data Pipeline (`pipeline/`) | ❌ | ✅ |
| Case Library (`case_library.py`) | ❌ | ✅ |
| DB Migrations (`migrations/`) | ❌ | ✅ |
| Deployment Scripts (`scripts/deploy.py`) | ❌ | ✅ |
| Server Config / Secrets | ❌ | ✅ |
| Golden Dataset (`data/golden/`) | ❌ | ✅ |

**Sync Rules**:
- Only MCP Server (`server.py`, `stdio_server.py`, `__init__.py`, `__main__.py`), Event Schema, Web Dashboard, and API docs may be synced to the public repo
- Sync is automated — Dev Agent executes when private repo MCP files change
- Public `pyproject.toml` is intentionally slim (3 deps only), different from private
- Pre-sync review ensures no hardcoded IPs, keys, or internal paths leak

**Security Red Lines**:
- Public repo contains NO database credentials, API keys, or server IPs
- Public repo contains NO Extractor engine (core competitive advantage)
- Public repo contains NO Golden Dataset (moat asset)

The MCP Server is a thin REST API proxy — it connects to `api.astockevent.com` via HTTP, with no database or pipeline logic included.

> Complete backend source: [NengjiangLunpi/astockevent](https://github.com/NengjiangLunpi/astockevent) (PRIVATE).

## Contact

- **Email**: [astockevent@outlook.com](mailto:astockevent@outlook.com)
- **API Registration**: [astockevent.com/register](https://astockevent.com/register)
- **GitHub Issues**: [Public Repo](https://github.com/NengjiangLunpi/astockevent-mcp/issues)

## License

MIT License — see [LICENSE](LICENSE).
