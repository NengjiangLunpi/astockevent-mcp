# AStockEvent API 契约

> **版本**: v0.1 MVP | **对齐**: PO 裁定 §四 + CLAUDE.md §MCP Tool | **协议**: REST + MCP

---

## 一、REST API

### 1.1 公共约定

- **Base URL**: `https://api.astockevent.com/v1`
- **认证**: `Authorization: Bearer dp_api_xxxx`（API Key）
- **分页**: cursor-based（PO 裁定）
- **日期**: `YYYY-MM-DD` 格式，时区 Asia/Shanghai
- **Event ID**: UUID v4（纯 UUID，无前缀）

### 1.2 通用响应格式

```json
{
  "data": { ... },
  "meta": {
    "cursor": "a1b2c3d4...",
    "has_more": true,
    "request_id": "req_7f3a2b1c"
  },
  "error": null
}
```

### 1.3 端点

#### `GET /v1/events`

**用途**：查询 Event 列表。MVP 最高优先级参数：`since`（增量查询）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `since` | datetime | — | 增量查询起点（ISO 8601）。返回 `last_updated_at >= since` 的 Event |
| `event_type` | string | — | 枚举值。逗号分隔多个 |
| `stock_code` | string | — | 6位代码。逗号分隔多个 |
| `status` | string | — | `active` / `updating` / `closed` / `corrected` |
| `confidence_tier` | string | — | `verified` / `likely` / `uncertain` |
| `cursor` | string | — | 分页游标（上一页 `meta.cursor` 值） |
| `limit` | int | — | 每页条数，默认 50，最大 200 |

**示例**：
```
GET /v1/events?since=2026-05-30T15:00:00%2B08&event_type=share_reduction,delisting_risk&limit=50
```

**响应**：
```json
{
  "data": [
    {
      "event_id": "c8a7f9e1-d2b4-4a3c-8d5e-1f6a9b3c7d4e",
      "event_type": "share_reduction",
      "stock_code": "002272",
      "stock_name": "川润股份",
      "market": "SZ",
      "status": "active",
      "phase": "plan",
      "confidence_tier": "verified",
      "confidence_reasons": ["巨潮资讯 announcementType 代码匹配", "标题关键词匹配：减持+预披露"],
      "quantitative_tags": {
        "reduction_ratio_tier": "≥2%",
        "shareholder_type": "控股股东"
      },
      "ai_summary": "川润股份控股股东罗丽华等4人拟减持2.96%股份（集中竞价+大宗交易），合计约1.75亿元",
      "announcement_date": "2026-05-29",
      "announcement_time": "after_market",
      "last_updated_at": "2026-05-30T08:15:00+08",
      "source": {
        "primary": {"name": "cninfo", "url": "http://www.cninfo.com.cn/..."},
        "cross_validated": true,
        "cross_sources": ["akshare"]
      }
    }
  ],
  "meta": {
    "cursor": "c8a7f9e1-d2b4-4a3c-8d5e-1f6a9b3c7d4e",
    "has_more": true,
    "request_id": "req_7f3a2b1c"
  }
}
```

#### `GET /v1/events/{event_id}`

**用途**：获取单个 Event 完整信息（含 `structured_payload` + `timeline` + `related_events`）。

**响应**：与列表相同结构的单个 Event + 额外字段：

```json
{
  "data": {
    "...": "...",
    "structured_payload": {
      "shareholder_name": "罗丽华",
      "shareholder_type": "控股股东",
      "reduction_ratio": 0.0296,
      "reduction_method": "mixed",
      "reduction_period_start": "2026-06-20",
      "reduction_period_end": "2026-09-19",
      "phase": "plan"
    },
    "timeline": [
      {
        "date": "2026-05-29",
        "phase": "plan",
        "description": "罗丽华等4人预披露减持计划，拟减持2.96%",
        "source_url": "http://www.cninfo.com.cn/..."
      }
    ],
    "related_events": [],
    "merge_parent": null
  }
}
```

#### `GET /v1/events/{event_id}/timeline`

**用途**：获取单个 Event 的完整生命周期时间线。

#### `GET /v1/events/upcoming`

**用途**：未来 N 天内即将发生的事件（如解禁日、除权日、减持期截止日）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `days` | int | — | 未来天数，默认 7，最大 30 |
| `event_type` | string | — | 过滤 Event Type |

---

### 1.4 错误码

| HTTP | 错误码 | 说明 |
|------|--------|------|
| 400 | `INVALID_CURSOR` | 游标无效或已过期 |
| 400 | `INVALID_PARAM` | 参数值不在允许范围 |
| 401 | `UNAUTHORIZED` | API Key 缺失或无效 |
| 403 | `FORBIDDEN` | 实例已停用（滥用/二次分发） |
| 429 | `RATE_LIMITED` | 超出调用频率限制 |
| 500 | `INTERNAL` | 内部错误 |

---

## 二、MCP Server

### 2.1 公共约定

- **协议**: Model Context Protocol (2024-11-05 spec)
- **传输**: `stdio`（本地）或 Streamable HTTP（远程）
- **Server 名称**: `astockevent`
- **免费层**: 100 次/天（PM 裁定）

### 2.2 MCP Tool 定义

#### Tool 1: `check_events`

```
名称: check_events
描述: 检查指定股票池在指定时间段内的结构化公告事件。
      返回减持计划、ST/退市风险、监管函件、限售股解禁、股份回购等结构化 Event。
      不返回主观评级，只返回量化事实。

参数:
  - stock_codes (string): 6位股票代码列表，逗号分隔。例如 "002272,600519,300750"
  - event_types (string, 可选): 事件类型过滤，逗号分隔。默认全部 5 种
  - since (string, 可选): 起始时间 ISO 8601 datetime，如 "2026-05-30T15:00:00+08"。默认 7 天前。AI Agent 轮询用此参数做增量查询，避免重复获取已处理 Event
  - limit (int, 可选): 最大返回数，默认 50，最大 200

返回: 结构化 Event 列表（JSON 数组）
```

#### Tool 2: `get_event_timeline`

```
名称: get_event_timeline
描述: 获取单个事件的完整生命周期时间线。追踪事件从 plan→in_progress→completed/terminated 的全过程。

参数:
  - event_id (string): Event UUID，例如 "c8a7f9e1-d2b4-4a3c-8d5e-1f6a9b3c7d4e"

返回: 事件详情 + timeline 数组 + 关联事件列表
```

#### Tool 3: `get_upcoming_events`

```
名称: get_upcoming_events
描述: 获取未来N天内即将发生的事件。包括：限售股解禁日、减持计划到期日、退市整理期届满日、回购实施截止日、问询函回复截止日。

参数:
  - stock_codes (string, 可选): 6位股票代码列表，逗号分隔。不填=全市场
  - days (int, 可选): 未来天数，默认 7，最大 30
  - event_types (string, 可选): 事件类型过滤

返回: 未来事件列表（JSON 数组），每条含 event_id, event_type, stock_code, due_date, days_remaining
```

---

## 三、API Key 与速率限制

| 层级 | API Key 格式 | REST | MCP |
|------|------------|------|-----|
| 免费层 | `dp_free_xxxx` | 200 次/天 | 100 次/天 |
| 个人版 | `dp_pro_xxxx` | 500 次/天 | — |
| 专业版 | `dp_ent_xxxx` | 5000 次/天 | — |

**速率限制响应头**：
```
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 147
X-RateLimit-Reset: 1717100000
```

---

## 四、Admin API（内部，HTTP Basic Auth）

| 端点 | 认证 | 用途 |
|------|:--:|------|
| `GET /api/status` | Basic Auth | 系统实时状态：调度器/数据库/最近 10 次采集 |
| `GET /api/report` | Basic Auth | 24h Harness 报告：Event 类型分布/Confidence 分布/管线统计 |

**认证**: HTTP Basic Auth，凭据通过 `ADMIN_USERNAME` / `ADMIN_PASSWORD` 环境变量配置。

**Web 页面**: `/status` 和 `/report` 提供 HTML 可视化（同一认证）。

---

*API 契约对齐 PO 裁定 §四（cursor-based 分页、since 增量查询、corrected 状态、confidence_tier）。MCP Tool 对齐 CLAUDE.md §MCP Tool（3个）。*
