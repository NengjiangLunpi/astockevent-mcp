# AStockEvent MCP Server

A股公告结构化事件 Feed → AI Agent 可直接消费。

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-blue)](https://modelcontextprotocol.io/)

## 概述

AStockEvent 将 A 股上市公司公告转化为**结构化语义事件**（structured event feed），让 AI Agent（Claude、ChatGPT、VSCode Copilot 等）通过 MCP 协议直接查询、分析和追踪。

## 特性

- **5 种 Event Type** — `share_reduction`（减持）、`delisting_risk`（ST/退市）、`regulatory_letter`（监管函件）、`lockup_expiration`（限售股解禁）、`share_buyback`（股份回购）
- **3 个 MCP Tool** — `check_events`（批量查询）、`get_event_timeline`（生命周期追踪）、`get_upcoming_events`（未来事件预警）
- **结构化 Event JSON** — 每个事件包含 `structured_payload`（量化标签）、`confidence_tier`（置信度）、`ai_summary`（AI 摘要）、完整 `timeline`
- **免费使用** — 免费层 100 次/天
- **MCP 协议** — 兼容 Claude Desktop / VSCode / 任何 MCP-compatible AI Agent

## 快速开始

### 1. 安装

```bash
pip install astockevent
```

### 2. Claude Desktop 配置

在 Claude Desktop 的 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "astockevent": {
      "command": "python",
      "args": ["-m", "astockevent.mcp"],
      "env": {
        "ASTOCKEVENT_API_KEY": "dp_free_xxxx"
      }
    }
  }
}
```

### 3. 在 Claude 中使用

配置完成后，Claude 会自动识别 3 个 MCP Tool：

- **查事件**: "帮我查川润股份 002272 最近一周的减持公告"
- **看时间线**: "追踪 event_id=c8a7f9e1-d2b4-4a3c-8d5e-1f6a9b3c7d4e 的完整生命周期"
- **预警**: "未来 7 天有哪些股票的解禁股要上市？"

### 4. VSCode Copilot 配置

```json
{
  "mcp": {
    "servers": {
      "astockevent": {
        "command": "python",
        "args": ["-m", "astockevent.mcp"],
        "env": {
          "ASTOCKEVENT_API_KEY": "dp_free_xxxx"
        }
      }
    }
  }
}
```

## Event Types

| Event Type | 说明 | 常见阶段 |
|---|---|---|
| `share_reduction` | 股东减持计划、进展、完成 | plan → in_progress → completed |
| `delisting_risk` | ST 风险/退市风险警示 | warning → confirmed/解除 |
| `regulatory_letter` | 监管函/问询函/关注函 | pending_reply → replied/overdue |
| `lockup_expiration` | 限售股解禁/定增解禁 | approaching → expired |
| `share_buyback` | 股份回购计划/实施 | plan → in_progress → completed |

## API 契约

完整 REST API + MCP Tool 定义见 [docs/api-contract.md](docs/api-contract.md)。

## 项目结构

```
astockevent-mcp/
├── src/astockevent/
│   ├── mcp/              # MCP Server（完整代码）
│   │   ├── server.py     # 3 个 Tool 核心逻辑
│   │   ├── stdio_server.py  # MCP stdio 传输层
│   │   ├── __init__.py
│   │   └── __main__.py   # python -m astockevent.mcp 入口
│   ├── models/
│   │   └── schemas.py    # Event Schema（Pydantic）
│   └── db/               # 数据库层 Stub（完整实现见私有仓库）
├── web/                  # Web 看板前端（HTML/JS）
├── docs/
│   └── api-contract.md   # API 契约文档
└── README.md
```

## ⚠️ 重要说明

**本仓库是 AStockEvent 的公开子集**，包含 MCP Server + Event Schema + Web 看板 + API 文档。

MCP Server 代码依赖 `astockevent.db` 数据库层，该模块在私有仓库中有完整实现。本仓库提供了 `db/` 的 Stub 以供代码阅读参考，但**无法独立运行**。

> 完整可运行的 MCP Server 代码在私有仓库 [zhoushukai-ui/astockevent](https://github.com/zhoushukai-ui/astockevent)（PRIVATE）。  
> 完整后端代码（Extractors / Pipeline / Case Library / 部署脚本）也在此私有仓库中。

## License

MIT License — 详见 [LICENSE](LICENSE)。
