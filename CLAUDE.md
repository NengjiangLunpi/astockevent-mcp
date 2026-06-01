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
