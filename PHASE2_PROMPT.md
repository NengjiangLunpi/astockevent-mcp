你现在是 Dev。

这是 AStockEvent 的公开子仓库 astockevent-mcp。私有仓库在 d:\Projects\AStockEvent\。

当前状态：
- GitHub: https://github.com/zhoushukai-ui/astockevent-mcp (PUBLIC, MIT License)
- 本地: d:\Projects\astockevent-mcp\
- 已拷贝内容:
  ├─ src/astockevent/mcp/server.py      — MCP Server
  ├─ src/astockevent/mcp/stdio_server.py — MCP stdio 入口
  ├─ src/astockevent/mcp/__init__.py
  ├─ src/astockevent/mcp/__main__.py
  ├─ src/astockevent/models/schemas.py   — Event Schema
  ├─ web/                                — Web 看板前端（HTML/JS）
  └─ docs/api-contract.md                — API 契约
- 私有仓库的 extractors/pipeline/case_library 等严禁出现在此目录

你需要做：

1. 重写 README.md（公开面向）：
   - 标题：AStockEvent MCP Server
   - 一句话：A股公告结构化事件 Feed → AI Agent 可直接消费
   - 特性：5 种 Event Type、MCP 协议、免费使用
   - 快速开始：pip install + Claude Desktop 配置示例
   - 链接到 https://github.com/zhoushukai-ui/astockevent（注明"完整后端代码在此"）
   - 链接到 docs/api-contract.md

2. 创建 CLAUDE.md：
   ```
   # astockevent-mcp — Public Subset
   
   ## ⚠️ 代码隔离声明
   
   本仓库是 AStockEvent 的**公开子集**，仅包含 MCP Server + Event Schema + Web 看板 + 文档。
   
   **以下内容在本仓库中，但私有仓库中有完整实现：**
   - MCP Server（本仓库有完整代码）
   - Event Schema（本仓库有完整定义）
   
   **以下内容仅在私有仓库** `zhoushukai-ui/astockevent`（PRIVATE）**中：**
   - Extractors（公告语义提取引擎）
   - Pipeline（数据管线、调度器、采集器）
   - Case Library（判例库、Golden Dataset）
   - 数据库 Schema 实现代码
   - 部署脚本
   
   ## 对本仓库开发者的约束
   
   - ❌ 禁止在本仓库实现任何 extractor/pipeline 逻辑
   - ❌ 禁止引用私有仓库中的代码路径
   - ✅ MCP Server 依赖可以通过 PyPI 包 `astockevent` 安装（未来）
   - ✅ Web 看板和 Schema 是公开可复用的
   ```

3. 整理 MCP Server 依赖：
   - 检查 src/astockevent/mcp/server.py 的 import 是否依赖私有模块（extractors、pipeline 等）
   - 如果依赖无法解耦 → 创建 stubs 或标注 TODO
   - 目标：这个目录能独立表达"MCP Server 长什么样"
   - 如果当前无法独立运行 → 在 README 里诚实说明"完整可运行代码在私有仓库"

4. git add . + git commit + git push

完成后通知 PM（写入 d:\Projects\AStockEvent\inbox\for-pm.md）。
